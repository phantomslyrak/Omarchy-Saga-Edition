pragma ComponentBehavior: Bound
// Decorative length/caret numbers only. No input, password, lock service or processes.
import QtQuick
import QtQuick.Shapes

Item {
    id: mask
    objectName: "sagaRuneMask"
    // Authentication failure hides and clears the visual layer immediately.
    property bool resetImmediately: false
    onResetImmediatelyChanged: if (resetImmediately) {
        clearTimer.stop(); slots.clear(); previousLength = 0; clearing = false
    }
    enabled: false // Entire ornament subtree is transparent to keyboard/pointer input.
    property int count: 0
    property int caret: 0
    property real unit: 1
    property bool reducedMotion: false
    property bool focused: false
    property bool healthy: false
    property bool clearing: false
    property int previousLength: 0
    readonly property int capacity: Math.max(1, Math.min(24, Math.floor(width / (17 * unit))))
    readonly property int visibleCount: slots.count
    readonly property int viewportStart: Math.max(0, Math.min(Math.max(0, count - capacity), Math.max(0, caret - capacity + 1)))
    readonly property bool settledEmpty: count === 0 && !clearing
    readonly property real caretX: Math.max(0, Math.min(width - 2, (caret - viewportStart) * 17 * unit + 2 * unit))
    clip: true

    function sync() {
        try {
            const total = resetImmediately ? 0 : Math.max(0, count)
            const start = viewportStart
            const end = Math.min(total, start + capacity)
            while (slots.count && slots.get(0).ordinal < start) slots.remove(0)
            while (slots.count && slots.get(slots.count - 1).ordinal >= end) slots.remove(slots.count - 1)
            if (slots.count) {
                for (let n = slots.get(0).ordinal - 1; n >= start; n--)
                    slots.insert(0, { ordinal: n, animateBirth: false })
            }
            const next = slots.count ? slots.get(slots.count - 1).ordinal + 1 : start
            for (let n = next; n < end; n++) slots.append({ ordinal: n, animateBirth: n >= previousLength })
            clearing = total === 0 && previousLength > 0 && !reducedMotion
            if (clearing) clearTimer.restart()
            else clearTimer.stop()
            previousLength = total
            // Apply queued ListModel removals before the next password edit.
            strip.forceLayout()
            healthy = true
        } catch (error) { healthy = false; console.warn("SAGA_RUNES_MASK_FAILED", String(error)) }
    }
    onCountChanged: Qt.callLater(sync)
    onCaretChanged: Qt.callLater(sync)
    onCapacityChanged: Qt.callLater(sync)
    onReducedMotionChanged: if (reducedMotion) { clearing = false; clearTimer.stop() }
    Component.onCompleted: sync()
    Timer { id: clearTimer; interval: 170; onTriggered: mask.clearing = false }
    ListModel { id: slots }
    ListView {
        id: strip
        objectName: "runeStrip"
        anchors.fill: parent
        orientation: ListView.Horizontal
        model: slots
        interactive: false
        keyNavigationEnabled: false
        focus: false
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        delegate: Item {
            id: mark
            required property int ordinal
            required property bool animateBirth
            readonly property int variant: ordinal % 6
            property real morph: 0
            width: 17 * mask.unit
            height: strip.height
            opacity: 0
            scale: 0.45
            transformOrigin: Item.Center
            ListView.onRemove: birth.stop()
            Component.onCompleted: {
                if (mask.reducedMotion || !animateBirth) { opacity = 1; scale = 1; morph = 1 }
                else birth.start()
            }
            Connections {
                target: mask
                function onResetImmediatelyChanged() {
                    if (mask.resetImmediately) { birth.stop(); mark.opacity = 0 }
                }
                function onReducedMotionChanged() {
                    if (mask.reducedMotion) { birth.stop(); mark.opacity = 1; mark.scale = 1; mark.morph = 1 }
                }
            }
            SequentialAnimation {
                id: birth
                ParallelAnimation {
                    NumberAnimation { target: mark; property: "opacity"; from: 0; to: 1; duration: 140; easing.type: Easing.OutCubic }
                    NumberAnimation { target: mark; property: "scale"; from: 0.45; to: 1; duration: 140; easing.type: Easing.OutCubic }
                }
                NumberAnimation { target: mark; property: "morph"; from: 0; to: 1; duration: 210; easing.type: Easing.InOutCubic }
            }
            Rectangle {
                anchors.centerIn: parent
                width: 3 * mask.unit; height: width; radius: width / 2
                color: "#ead6bc"
                opacity: 1 - mark.morph
            }
            Shape {
                anchors.centerIn: parent
                width: 14; height: 14
                scale: mask.unit * (0.35 + 0.65 * mark.morph)
                opacity: mark.morph
                ShapePath {
                    strokeColor: "#ead6bc"
                    strokeWidth: 1.15
                    fillColor: mark.variant === 1 || mark.variant === 3 || mark.variant === 4 ? "transparent" : "#28d9c2a0"
                    joinStyle: ShapePath.MiterJoin
                    PathSvg {
                        path: [
                            "M7 2 L12 7 L7 12 L2 7 Z",
                            "M7 2 A5 5 0 1 1 6.99 2 M7 6 L7 8",
                            "M7 0 L10 5 L9 11 L7 14 L4 9 L4 4 Z M7 2 L7 12",
                            "M7 1 L7 13 M7 5 L3 2 M7 9 L11 6 M5 12 L9 12",
                            "M7 0 L7 4 M7 10 L7 14 M0 7 L4 7 M10 7 L14 7 M7 4 L10 7 L7 10 L4 7 Z",
                            "M4 2 L10 3 L12 8 L8 12 L2 9 Z M4 2 L6 7 L2 9 M6 7 L10 3"
                        ][mark.variant]
                    }
                }
            }
        }
        remove: Transition {
            ParallelAnimation {
                NumberAnimation { property: "opacity"; to: 0; duration: mask.reducedMotion || mask.resetImmediately ? 0 : 150; easing.type: Easing.OutCubic }
                NumberAnimation { property: "scale"; to: 0.65; duration: mask.reducedMotion || mask.resetImmediately ? 0 : 150; easing.type: Easing.OutCubic }
            }
        }
    }
    Rectangle {
        x: mask.caretX
        anchors.verticalCenter: parent.verticalCenter
        width: 1
        height: 15 * mask.unit
        color: "#b4d8c3a6"
        visible: mask.focused && mask.count > 0 && !mask.clearing
    }
}
