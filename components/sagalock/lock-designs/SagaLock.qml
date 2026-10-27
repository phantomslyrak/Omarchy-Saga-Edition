// Saga Edition: interactive UI over the cleaned original concept illustration.
// Never selects itself. Auth remains Lock Screen Explorer's PasswordField/LockInput.
pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import "../plugins/io.github.sirjul1337.lock-explorer/designs"
import "saga"

DesignBase {
    id: saga
    inputItem: field.input
    showMediaStrip: false
    showPasswordToggle: false
    property bool sagaRunesEnabled: true
    readonly property var sagaMotionHost: parentWithMotion(saga.parent)
    readonly property bool runesReducedMotion: sagaMotionHost ? sagaMotionHost.holdStill === true : false
    readonly property var runeMask: runeMaskLoader.item
    readonly property bool runeMaskInUse: sagaRunesEnabled && runeMaskLoader.status === Loader.Ready
        && runeMask !== null && runeMask.healthy === true && !field.revealed && !saga.fido2Active
        && !saga.authenticatingPassword && !saga.errorState && !saga.inputBlocked && !saga.snapshotMode

    readonly property real u: Math.min(width / 1536, height / 1024)
    readonly property color ivory: "#ead6bc"
    readonly property color muted: "#d1c2ac"
    readonly property color rule: "#789b9789"
    readonly property string scenicPath: Quickshell.env("HOME") + "/.local/share/omarchy-saga-edition/assets/lock/fjord-clean-no-logo-v1.png"
    readonly property var media: mediaLoader.item || emptyMedia
    readonly property var player: media.player
    readonly property var weather: weatherLoader.item || emptyWeather
    readonly property bool weatherReady: weather.available === true
    readonly property real trackPosition: media.position
    Component.onCompleted: console.info("SAGA_DESIGN_READY", "v1.0-20261026")

    function parentWithMotion(node) {
        while (node) {
            if (node.holdStill !== undefined) return node
            node = node.parent
        }
        return null
    }
    function configureRuneMask(component) {
        component.count = Qt.binding(function() { return field.input.length })
        component.caret = Qt.binding(function() { return field.input.cursorPosition })
        component.unit = Qt.binding(function() { return saga.u })
        component.reducedMotion = Qt.binding(function() { return saga.runesReducedMotion || !saga.animating })
        component.focused = Qt.binding(function() { return field.input.activeFocus && field.input.enabled && !field.input.inert })
    }
    function configureNorthernFrame(component) {
        component.unit = Qt.binding(function() { return saga.u })
        component.focused = Qt.binding(function() { return field.input.activeFocus })
        component.failed = Qt.binding(function() { return saga.errorState })
        component.reducedMotion = Qt.binding(function() { return saga.runesReducedMotion || !saga.animating })
    }

    function duration(seconds) {
        if (!isFinite(seconds) || seconds < 0) return "—"
        return Math.floor(seconds / 60) + ":" + String(Math.floor(seconds % 60)).padStart(2, "0")
    }
    function configureMedia(component) {
        component.active = Qt.binding(function() { return saga.loadBackground && !saga.inputBlocked })
    }
    function configureWeather(component) {
        component.active = Qt.binding(function() { return saga.loadBackground && !saga.inputBlocked })
    }
    // A newly added directory type can be absent from a running QQmlEngine's
    // import cache. An explicit URL bypasses that catalogue and isolates failure.
    QtObject {
        id: emptyWeather
        readonly property bool available: false
        readonly property bool stale: false
        readonly property string glyph: "cloud"
        readonly property string tempC: "—"
        readonly property string condition: "Weather unavailable"
        readonly property string extremes: ""
    }
    Loader {
        id: weatherLoader
        objectName: "sagaWeatherLoader"
        active: saga.loadBackground
        source: Qt.resolvedUrl("saga-weather/WeatherPanel.qml")
        onLoaded: saga.configureWeather(item)
        onStatusChanged: if (status === Loader.Error) console.warn("SAGA_WEATHER_COMPONENT_FAILED", source)
    }
    Telemetry { id: stats; objectName: "sagaTelemetry"; polling: saga.loadBackground && !saga.inputBlocked }
    Connections {
        target: stats
        function onHistoryChanged() { cpuGraph.requestPaint() }
    }
    QtObject {
        id: emptyMedia
        readonly property var player: null
        readonly property bool hasMedia: false
        readonly property bool playing: false
        readonly property string title: ""
        readonly property string artist: ""
        readonly property string artUrl: ""
        readonly property real position: 0
        readonly property real duration: 0
        readonly property bool positionKnown: false
        readonly property real progress: -1
    }
    Loader {
        id: mediaLoader
        objectName: "sagaMediaLoader"
        active: saga.loadBackground
        source: Qt.resolvedUrl("saga-media-v1/MediaPanel.qml")
        onLoaded: saga.configureMedia(item)
        onStatusChanged: if (status === Loader.Error) console.warn("SAGA_MEDIA_COMPONENT_FAILED")
    }

    Rectangle { anchors.fill: parent; color: "#0d171b" }
    Image {
        id: scenery
        objectName: "sagaScenery"
        anchors.fill: parent
        source: saga.loadBackground ? saga.fileUrl(saga.scenicPath) : ""
        fillMode: Image.Stretch
        asynchronous: true
        sourceSize.width: Math.ceil(width * 1.25)
        sourceSize.height: Math.ceil(height * 1.25)
    }
    Rectangle {
        anchors.fill: parent
        opacity: 0.25
        gradient: Gradient {
            GradientStop { position: 0; color: "#38081113" }
            GradientStop { position: 0.52; color: "#160b1315" }
            GradientStop { position: 1; color: "#60080c0e" }
        }
    }
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        onClicked: { saga.wakeRequested(); saga.forcePasswordFocus() }
        onPositionChanged: saga.wakeRequested()
    }
    component Serif: Text {
        textFormat: Text.PlainText
        color: saga.ivory
        font.family: "Liberation Serif"
        font.pixelSize: 20 * saga.u
    }
    component Sans: Text {
        textFormat: Text.PlainText
        color: saga.ivory
        font.family: "Noto Sans"
        font.weight: Font.Normal
        font.pixelSize: 14 * saga.u
    }
    component Rule: Rectangle { height: 1; color: saga.rule }
    component LineIcon: OutlineIcon {
        stroke: saga.ivory
        width: 24 * saga.u
        height: width
    }
    component Meter: Rectangle {
        id: meter
        property real value: -1
        height: 4 * saga.u
        radius: height / 2
        color: "#997a807b"
        Rectangle {
            width: meter.value >= 0 ? meter.width * Math.max(0, Math.min(1, meter.value)) : 0
            height: parent.height; radius: parent.radius; color: saga.ivory
            Behavior on width { NumberAnimation { duration: 350 } }
        }
    }

    // Reference: left=60/1536, top=49/1024. The original serif has generous thin strokes.
    Item {
        x: parent.width * 0.041; y: parent.height * 0.047
        width: parent.width * 0.30; height: parent.height * 0.23
        Serif {
            id: clockText
            objectName: "sagaClock"
            y: -19 * saga.u
            text: saga.clock("HH:mm")
            font.family: "Noto Serif"
            font.pixelSize: 99 * saga.u
            font.weight: Font.Light
            font.letterSpacing: -2 * saga.u
        }
        Serif {
            y: parent.height * 0.45
            text: saga.date("dddd, d MMMM")
            font.pixelSize: 25 * saga.u
        }
        Rule { y: parent.height * 0.66; width: 216 * saga.u }
        Serif {
            y: parent.height * 0.74
            text: "A CALMER MIND\nA STRONGER TOMORROW"
            font.pixelSize: 12 * saga.u; font.letterSpacing: 2.4 * saga.u; lineHeight: 1.7
        }
        Rule { y: parent.height * 0.98; width: 68 * saga.u }
    }

    // Right column keeps reference positions even when a data source is absent.
    Item {
        id: rail
        x: parent.width * 0.7822; y: parent.height * 0.049
        width: parent.width * 0.1865; height: parent.height * 0.49
        Item {
            width: parent.width; height: 75 * saga.u
            LineIcon { x: 0; y: 5 * saga.u; kind: saga.weather.glyph; width: 54 * saga.u; opacity: saga.weatherReady ? 1 : 0.85 }
            Serif { x: 79 * saga.u; text: saga.weatherReady ? saga.weather.tempC : "—"; font.pixelSize: 40 * saga.u }
            Sans { x: 80 * saga.u; y: 43 * saga.u; text: (saga.weather.stale ? "Stale · " : "") + saga.weather.condition; width: parent.width - x; elide: Text.ElideRight; font.pixelSize: 12 * saga.u; color: saga.muted }
            Sans {
                anchors.right: parent.right; y: 9 * saga.u
                text: "KAZAN"
                font.pixelSize: 12 * saga.u; color: saga.muted
            }
            Sans {
                anchors.right: parent.right; y: 40 * saga.u
                text: saga.weather.extremes
                font.pixelSize: 11 * saga.u; color: saga.muted
            }
        }
        Rule { y: 82 * saga.u; width: parent.width }
        Item {
            y: 101 * saga.u; width: parent.width; height: 126 * saga.u
            Rectangle {
                id: coverFrame
                width: 91 * saga.u; height: width; radius: 9 * saga.u
                color: "#251b272a"; border.width: 1; border.color: saga.rule; clip: true
                Image { id: albumArt; anchors.fill: parent; source: saga.media.artUrl; fillMode: Image.PreserveAspectCrop; asynchronous: true }
                LineIcon { anchors.centerIn: parent; visible: albumArt.status !== Image.Ready; kind: "music"; opacity: 0.35 }
            }
            Sans {
                x: 109 * saga.u; y: 2 * saga.u; width: parent.width - x
                text: saga.media.hasMedia ? saga.media.title : "Nothing playing"
                elide: Text.ElideRight; font.pixelSize: 16 * saga.u
            }
            Sans {
                x: 109 * saga.u; y: 27 * saga.u; width: parent.width - x
                text: saga.media.hasMedia ? saga.media.artist : ""
                elide: Text.ElideRight; font.pixelSize: 12 * saga.u; color: saga.muted
            }
            Meter {
                x: 109 * saga.u; y: 61 * saga.u; width: parent.width - x
                value: saga.media.progress
            }
            Sans {
                anchors.right: parent.right; y: 73 * saga.u
                text: saga.media.positionKnown ? saga.duration(saga.trackPosition) + " / " + saga.duration(saga.media.duration) : ""
                font.pixelSize: 10 * saga.u; color: saga.muted
            }
            Row {
                anchors.right: parent.right; y: 90 * saga.u; spacing: 27 * saga.u
                Repeater {
                    model: ["previous", "toggle", "next"]
                    delegate: Item {
                        id: transport
                        required property string modelData
                        readonly property bool available: saga.mediaControls && saga.player !== null && saga.player === saga.lockMedia.player && (modelData === "previous" ? saga.player.canGoPrevious : modelData === "next" ? saga.player.canGoNext : saga.player.canTogglePlaying)
                        width: 32 * saga.u; height: 30 * saga.u
                        LineIcon { anchors.centerIn: parent; kind: transport.modelData === "previous" ? "previous" : transport.modelData === "next" ? "next" : saga.media.playing ? "pause" : "play"; opacity: transport.available ? 1 : 0.4 }
                        MouseArea { anchors.fill: parent; enabled: transport.available; onClicked: saga.mediaAct(transport.modelData) }
                    }
                }
            }
        }
        Rule { y: 243 * saga.u; width: parent.width }

        component StatLine: Item {
            id: statLine
            property string title
            property string valueText
            property string glyph
            property real fill: -1
            width: rail.width; height: 56 * saga.u
            Rectangle {
                width: 42 * saga.u; height: width; radius: width / 2
                color: "transparent"; border.width: 1; border.color: saga.rule
                LineIcon { anchors.centerIn: parent; kind: statLine.glyph }
            }
            Sans { x: 59 * saga.u; y: 0; text: statLine.title; font.pixelSize: 14 * saga.u }
            Sans { x: 59 * saga.u; y: 20 * saga.u; text: statLine.valueText; font.pixelSize: 14 * saga.u }
            Meter { visible: statLine.title !== "CPU"; x: statLine.width * 0.535; y: 27 * saga.u; width: statLine.width * 0.465; value: statLine.fill }
        }
        StatLine {
            y: 265 * saga.u; title: "CPU"; valueText: stats.cpu >= 0 ? Math.round(stats.cpu * 100) + "%" : "—"; glyph: "cpu"
            Canvas {
                id: cpuGraph
                visible: stats.cpu >= 0
                x: parent.width * 0.56; y: 6 * saga.u; width: parent.width * 0.44; height: 27 * saga.u
                onPaint: {
                    const ctx = getContext("2d"); ctx.clearRect(0, 0, width, height)
                    const values = stats.history; if (!values.length) return
                    ctx.beginPath(); ctx.moveTo(0, height)
                    const start = 48 - values.length
                    ctx.moveTo(width * start / 47, height)
                    for (let i = 0; i < values.length; i++) ctx.lineTo(width * (start + i) / 47, height * (1 - values[i]))
                    ctx.strokeStyle = "#aaad9c84"; ctx.lineWidth = 1; ctx.stroke()
                    ctx.lineTo(width, height); ctx.closePath()
                    ctx.fillStyle = "#389d9b88"; ctx.fill()
                }
            }
        }
        Rule { y: 318 * saga.u; width: parent.width }
        StatLine { y: 329 * saga.u; title: "RAM"; valueText: stats.ramText; glyph: "ram"; fill: stats.ram }
        Rule { y: 382 * saga.u; width: parent.width }
        StatLine { y: 393 * saga.u; title: "SSD"; valueText: stats.disk >= 0 ? Math.round(stats.disk * 100) + "%" : "—"; glyph: "disk"; fill: stats.disk }
        Rule { y: 456 * saga.u; width: parent.width }
        LineIcon { y: 476 * saga.u; kind: "battery"; width: 31 * saga.u; opacity: stats.battery >= 0 ? 1 : 0.4 }
        Sans { x: 59 * saga.u; y: 478 * saga.u; text: stats.battery >= 0 ? stats.battery + "%" : "—"; font.pixelSize: 16 * saga.u }
        LineIcon { x: 132 * saga.u; y: 476 * saga.u; kind: stats.batteryStatus === "Charging" ? "bolt" : "" }
        Sans { anchors.right: parent.right; y: 479 * saga.u; text: stats.battery >= 0 ? (stats.batteryStatus === "Charging" ? "Charging…" : stats.batteryStatus || "—") : "—"; font.pixelSize: 13 * saga.u; color: saga.muted }
        Rule { y: 520 * saga.u; width: parent.width }
    }

    Item {
        x: parent.width * 0.0456; y: parent.height * 0.854
        width: parent.width * 0.26; height: parent.height * 0.082
        Rectangle { width: 1; height: parent.height; color: saga.rule }
        Serif { x: 23 * saga.u; text: "You have no enemies.\nNo one does."; font.italic: true; font.pixelSize: 21 * saga.u; lineHeight: 1.3 }
        Serif { x: 23 * saga.u; y: 67 * saga.u; text: "— THORFINN"; font.pixelSize: 12 * saga.u; font.letterSpacing: 2 * saga.u }
    }

    PasswordField {
        id: field
        objectName: "sagaPassword"
        lock: saga
        anchors.horizontalCenter: parent.horizontalCenter
        y: parent.height * 0.774
        width: parent.width * 0.26
        height: 56 * saga.u
        radius: height / 2
        placeholder: ""
        textAlignment: TextInput.AlignLeft
        fontScale: saga.u * 0.94
        sidePadding: 62 * saga.u
        outlineThickness: 1
        outlineColor: "#dfc9aa"
        outlineErrorColor: saga.sagaRunesEnabled ? "#c3846d" : field.errorColor
        shakeOnFail: !saga.sagaRunesEnabled && !saga.runesReducedMotion
        textColor: saga.ivory; mutedColor: saga.muted; accentColor: saga.ivory
        color: "#dc242725"
        // Reserve the native input's right side for submit, without changing auth.
        showLockGlyph: false
        input.anchors.leftMargin: field.borderLeft + field.sidePadding + field.glyphReserve
        input.anchors.rightMargin: field.borderRight + 51 * saga.u + field.fingerprintReserve
        input.color: saga.runeMaskInUse ? "transparent" : saga.ivory
        input.cursorVisible: !saga.runeMaskInUse && field.input.activeFocus && field.input.length > 0 && !field.authenticating && !field.errorState
        input.font.family: "Noto Sans"
        Loader {
            id: runeMaskLoader
            objectName: "sagaRuneMaskLoader"
            anchors.fill: field.input
            active: saga.sagaRunesEnabled && !saga.snapshotMode
            visible: saga.runeMaskInUse
            source: Qt.resolvedUrl("saga-runes-v1/RuneMask.qml")
            onLoaded: saga.configureRuneMask(item)
            onStatusChanged: if (status === Loader.Error) console.warn("SAGA_RUNES_MASK_UNAVAILABLE")
        }
        Sans {
            anchors.fill: field.input
            text: saga.tr("Enter your password")
            visible: field.input.text.length === 0 && !saga.authenticatingPassword && !saga.errorState && !saga.fido2Active && !saga.snapshotMode
                && (!saga.runeMaskInUse || saga.runeMask.settledEmpty)
            verticalAlignment: Text.AlignVCenter
            font.pixelSize: 17 * saga.u
            color: saga.ivory
            elide: Text.ElideRight
        }
        Rectangle {
            x: 9 * saga.u; anchors.verticalCenter: parent.verticalCenter
            width: 40 * saga.u; height: width; radius: width / 2
            color: "transparent"; border.width: 1; border.color: saga.ivory
            visible: !saga.snapshotMode
            LineIcon { anchors.centerIn: parent; kind: "lock"; width: 22 * saga.u }
        }
        Rectangle {
            width: 27 * saga.u; height: width; radius: width / 2
            anchors.right: parent.right; anchors.rightMargin: 14 * saga.u
            anchors.verticalCenter: parent.verticalCenter
            color: saga.ivory; opacity: submitArea.containsMouse ? 1 : 0.9
            LineIcon { anchors.centerIn: parent; kind: "arrow"; stroke: "#273032"; width: 20 * saga.u }
            MouseArea {
                id: submitArea
                anchors.fill: parent; hoverEnabled: true
                enabled: field.input.enabled && !field.input.inert
                onClicked: { saga.wakeRequested(); field.input.accepted(); saga.forcePasswordFocus() }
            }
        }
    }
    Loader {
        id: northernFrameLoader
        objectName: "sagaNorthernFrameLoader"
        x: field.x - 6 * saga.u; y: field.y - 6 * saga.u
        width: field.width + 12 * saga.u; height: field.height + 12 * saga.u
        z: field.z + 1
        active: saga.sagaRunesEnabled && !saga.snapshotMode
        source: Qt.resolvedUrl("saga-runes-v1/NorthernFrame.qml")
        onLoaded: saga.configureNorthernFrame(item)
        onStatusChanged: if (status === Loader.Error) console.warn("SAGA_NORTHERN_FRAME_UNAVAILABLE")
    }
    // Power remains disabled by the existing service settings. No direct commands.
    Row {
        objectName: "sagaPowerStudy"
        enabled: false
        visible: !saga.powerActions
        anchors.horizontalCenter: parent.horizontalCenter
        y: parent.height * 0.879
        spacing: 42 * saga.u
        Repeater {
            model: ["power", "reboot", "moon"]
            Item {
                id: powerStudy
                required property string modelData
                // Keep the existing slot size, centers and spacing unchanged.
                width: 28 * saga.u
                height: width
                Rectangle {
                    anchors.centerIn: parent
                    width: powerIcon.width + 14
                    height: width
                    radius: width / 2
                    color: "#78141b1c"
                    border.width: 1
                    border.color: "#65d8c3a6"
                }
                LineIcon {
                    id: powerIcon
                    anchors.centerIn: parent
                    kind: powerStudy.modelData
                    width: Math.max(24, Math.min(28, 24 * saga.u))
                    stroke: "#ead6bc"
                    strokeWidth: 2
                    opacity: 0.85
                }
            }
        }
    }
    Item {
        x: parent.width * 0.865; y: parent.height * 0.865
        width: parent.width * 0.105; height: parent.height * 0.062
        Serif {
            anchors.right: parent.right
            width: parent.width
            text: "FAR LANDS\nQUIET SEAS\nCLEAR THOUGHTS"
            horizontalAlignment: Text.AlignLeft
            font.pixelSize: 12 * saga.u; font.letterSpacing: 2 * saga.u; lineHeight: 1.8
        }
        Rectangle { anchors.left: parent.left; anchors.leftMargin: -16 * saga.u; width: 1; height: parent.height; color: saga.rule }
    }
}
