pragma ComponentBehavior: Bound
// Pointer-transparent ornaments. No input or authentication object is passed here.
import QtQuick
import QtQuick.Shapes

Item {
    id: frame
    enabled: false
    property real unit: 1
    property bool focused: false
    property bool failed: false
    property bool reducedMotion: false
    property real focusAmount: focused ? 1 : 0
    property real errorPulse: 0
    readonly property color edgeColor: Qt.rgba((234 - 30 * errorPulse) / 255, (214 - 80 * errorPulse) / 255, (188 - 73 * errorPulse) / 255, 0.52 + focusAmount * 0.25)
    Behavior on focusAmount { NumberAnimation { duration: frame.reducedMotion ? 0 : 240; easing.type: Easing.OutCubic } }
    onFailedChanged: if (failed) {
        if (reducedMotion) errorPulse = 0.6
        else errorAnimation.restart()
    } else { errorAnimation.stop(); errorPulse = 0 }
    onReducedMotionChanged: if (reducedMotion) { errorAnimation.stop(); errorPulse = failed ? 0.6 : 0 }
    NumberAnimation { id: errorAnimation; target: frame; property: "errorPulse"; from: 1; to: 0.35; duration: 800; easing.type: Easing.OutCubic }

    Rectangle {
        anchors.fill: parent
        radius: height / 2
        color: "#0b111a1c"
        border.width: 1
        border.color: frame.edgeColor
    }
    Rectangle {
        anchors.fill: parent; anchors.margins: 4 * frame.unit
        radius: height / 2
        color: "transparent"
        border.width: 1
        border.color: Qt.rgba(0.88,0.82,0.72,0.13 + 0.13 * frame.focusAmount)
    }
    Rectangle {
        anchors.fill: parent; anchors.margins: 7 * frame.unit
        radius: height / 2
        color: "transparent"
        border.width: 1
        border.color: Qt.rgba(0.94,0.85,0.69,0.025 + 0.035 * frame.focusAmount)
    }
    Repeater {
        model: [false, true]
        Item {
            id: end
            required property bool modelData
            x: modelData ? frame.width - width : 0
            width: 44 * frame.unit; height: frame.height
            transform: Scale { origin.x: end.width / 2; xScale: end.modelData ? -1 : 1 }
            Shape {
                width: 44; height: 68
                scale: frame.unit
                transformOrigin: Item.TopLeft
                opacity: 0.55 + 0.25 * frame.focusAmount
                ShapePath {
                    strokeColor: frame.edgeColor; strokeWidth: 0.8; fillColor: "#43202b2e"
                    PathSvg { path: "M6 28 L11 23 L16 27 L17 37 L11 44 L6 39 Z M11 25 L11 41 M7 31 L15 34" }
                }
                ShapePath {
                    strokeColor: frame.edgeColor; strokeWidth: 0.75; fillColor: "transparent"
                    PathSvg { path: "M22 9 L29 6 L38 6 M19 13 L24 11 M22 59 L29 62 L38 62 M19 55 L24 57 M29 17 L29 24 M27 19 L31 22 M29 44 L29 51 M27 48 L31 45" }
                }
            }
        }
    }
    // Engraved ice: three restrained, unequal tips away from the text baseline.
    Repeater {
        model: [{at:0.27,depth:8},{at:0.64,depth:11},{at:0.76,depth:6}]
        Shape {
            id: ice
            required property var modelData
            x: frame.width * modelData.at
            y: 3 * frame.unit
            width: 7; height: 14
            scale: frame.unit
            transformOrigin: Item.TopLeft
            opacity: 0.38 + 0.17 * frame.focusAmount
            ShapePath {
                strokeColor: frame.edgeColor; strokeWidth: 0.6; fillColor: "#199dafa9"
                PathSvg { path: "M0 0 L6 0 L3 " + ice.modelData.depth + " Z M3 1 L3 " + (ice.modelData.depth - 2) }
            }
        }
    }
    Shape {
        anchors.horizontalCenter: parent.horizontalCenter
        y: -3 * frame.unit
        width: 44; height: 10
        scale: frame.unit
        opacity: 0.5 + 0.2 * frame.focusAmount
        ShapePath {
            strokeColor: frame.edgeColor; strokeWidth: 0.7; fillColor: "#262f3836"
            PathSvg { path: "M0 5 L15 5 M22 1 L27 5 L22 9 L17 5 Z M29 5 L44 5" }
        }
    }
}
