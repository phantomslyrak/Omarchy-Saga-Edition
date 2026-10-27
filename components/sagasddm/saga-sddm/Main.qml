pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic as Controls

Rectangle {
    id: root
    objectName: "sagaRoot"
    width: 2048; height: 1280
    color: "#0d171b"
    readonly property real u: Math.min(width / 1536, height / 1024)
    readonly property color ivory: "#ead6bc"
    property int sessionIndex: -1
    property bool busy: false
    property bool failed: false
    property string message: ""
    property date now: new Date()

    FontLoader { id: serif; source: "assets/NotoSerif-Regular.ttf" }
    FontLoader { id: sans; source: "assets/NotoSans-Regular.ttf" }
    Timer { interval: 1000; running: true; repeat: true; onTriggered: root.now = new Date() }

    // Match the desktop filename exactly; never fall back to an unrelated UWSM session.
    Repeater {
        model: sessionModel
        delegate: Item {
            required property string file
            required property int index
            Component.onCompleted: {
                if (file.split("/").pop() === "omarchy-saga.desktop") {
                    root.sessionIndex = index
                    console.info("SagaSDDM: selected omarchy-saga.desktop at index", index)
                }
            }
        }
    }

    function submit() {
        if (busy) return
        if (sessionIndex < 0) {
            message = "Session omarchy-saga.desktop is unavailable"
            password.forceActiveFocus()
            return
        }
        if (!users.currentValue) {
            message = "Select a user"
            users.forceActiveFocus()
            return
        }
        failed = false
        message = "Signing in…"
        busy = true
        sddm.login(users.currentValue, password.text, sessionIndex)
    }
    Connections {
        target: sddm
        function onLoginFailed() {
            root.busy = false
            root.failed = true
            root.message = "Authentication failed. Try again."
            password.clear()
            password.forceActiveFocus()
        }
        function onLoginSucceeded() { password.clear(); root.message = "Welcome home" }
        function onInformationMessage(message) { root.message = message }
    }

    Image {
        anchors.fill: parent
        source: "assets/fjord-clean-no-logo-v1.png"
        fillMode: Image.PreserveAspectCrop
        horizontalAlignment: Image.AlignHCenter
        verticalAlignment: Image.AlignVCenter
    }
    // The original scenic image stays visible; only the lower input area is shaded.
    Rectangle {
        anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
        height: parent.height * 0.35
        gradient: Gradient {
            GradientStop { position: 0; color: "#0010191b" }
            GradientStop { position: 0.58; color: "#5010191b" }
            GradientStop { position: 1; color: "#6010191b" }
        }
    }
    MouseArea { anchors.fill: parent; onClicked: password.forceActiveFocus() }

    Column {
        x: root.width * 0.041; y: root.height * 0.035
        spacing: 7 * root.u
        Text {
            text: Qt.formatTime(root.now, "HH:mm")
            font.family: serif.name; font.pixelSize: 99 * root.u
            font.letterSpacing: -2 * root.u
            color: root.ivory
        }
        Text {
            text: Qt.formatDate(root.now, "dddd, d MMMM")
            font.family: serif.name; font.pixelSize: 25 * root.u
            color: root.ivory
        }
        Rectangle { width: 216 * root.u; height: 1; color: "#789b9789" }
        Text {
            text: "A CALMER MIND\nA STRONGER TOMORROW"
            font.family: serif.name; font.pixelSize: 12 * root.u
            font.letterSpacing: 2.4 * root.u; lineHeight: 1.7
            color: root.ivory
        }
    }

    Controls.ComboBox {
        id: users
        objectName: "sagaUsers"
        anchors.horizontalCenter: parent.horizontalCenter
        y: field.y - height - 18 * root.u
        width: field.width * 0.8; height: 34 * root.u
        model: userModel
        textRole: "name"; valueRole: "name"
        enabled: !root.busy
        font.family: sans.name; font.pixelSize: 14 * root.u
        Accessible.name: "User"
        Component.onCompleted: {
            const last = indexOfValue(userModel.lastUser)
            currentIndex = last >= 0 ? last : (count > 0 ? 0 : -1)
        }
        onActivated: {
            password.clear(); root.failed = false; root.message = ""
            password.forceActiveFocus()
        }
        KeyNavigation.tab: password
        KeyNavigation.backtab: submitButton
        contentItem: Text {
            text: users.displayText + (users.count > 1 ? "  ▾" : "")
            font: users.font; color: root.ivory
            verticalAlignment: Text.AlignVCenter; horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
        }
        indicator: Item {}
        background: Rectangle {
            color: "#88141d20"; radius: height / 2
            border.width: users.activeFocus ? 1 : 0; border.color: root.ivory
        }
        delegate: Controls.ItemDelegate {
            id: userEntry
            required property string name
            required property int index
            width: users.width
            text: name
            font: users.font
            contentItem: Text { text: userEntry.text; color: root.ivory; font: users.font; verticalAlignment: Text.AlignVCenter }
            background: Rectangle { color: userEntry.highlighted ? "#524c47" : "#202a2c" }
            highlighted: users.highlightedIndex === index
        }
        popup: Controls.Popup {
            y: users.height + 4
            width: users.width
            implicitHeight: Math.min(contentItem.implicitHeight + 8, root.height * 0.3)
            padding: 4
            contentItem: ListView {
                clip: true; implicitHeight: contentHeight
                model: users.popup.visible ? users.delegateModel : null
                currentIndex: users.highlightedIndex
            }
            background: Rectangle { color: "#202a2c"; border.color: "#789b9789"; radius: 8 }
        }
    }

    Item {
        id: field
        anchors.horizontalCenter: parent.horizontalCenter
        y: parent.height * 0.774
        width: Math.min(root.width * 0.6, 430 * root.u)
        height: 56 * root.u
        Rectangle {
            anchors.fill: parent; radius: height / 2
            color: "#dc242725"
            border.width: 1; border.color: root.failed ? "#c3846d" : "#dfc9aa"
        }
        NorthernFrame {
            anchors.fill: parent; anchors.margins: -6 * root.u
            unit: root.u; focused: password.activeFocus; failed: root.failed
            reducedMotion: true
        }
        Text {
            x: 21 * root.u; anchors.verticalCenter: parent.verticalCenter
            text: "ᛉ"; font.family: serif.name; font.pixelSize: 24 * root.u
            color: root.ivory
        }
        TextInput {
            id: password
            objectName: "sagaPassword"
            anchors.fill: parent
            anchors.leftMargin: 58 * root.u; anchors.rightMargin: 57 * root.u
            verticalAlignment: TextInput.AlignVCenter
            font.family: sans.name; font.pixelSize: 19 * root.u
            color: "transparent"; selectionColor: "transparent"; selectedTextColor: "transparent"
            cursorVisible: false
            cursorDelegate: Item { objectName: "sagaHiddenCursor"; visible: false }
            // Match hidden native mask advance to the decorative rune cells for pointer editing.
            font.letterSpacing: 17 * root.u - passwordMetrics.advanceWidth("•")
            echoMode: TextInput.Password; passwordCharacter: "•"; passwordMaskDelay: 0
            clip: true; focus: true; enabled: !root.busy
            inputMethodHints: Qt.ImhSensitiveData | Qt.ImhNoPredictiveText | Qt.ImhHiddenText
            Accessible.name: "Password"
            KeyNavigation.tab: submitButton
            KeyNavigation.backtab: users
            onAccepted: root.submit()
            Keys.onEscapePressed: { clear(); root.failed = false; root.message = "" }
            onTextEdited: { root.failed = false; root.message = "" }
        }
        FontMetrics {
            id: passwordMetrics
            font.family: sans.name
            font.pixelSize: 19 * root.u
        }
        RuneMask {
            id: runeMask
            anchors.fill: password
            count: password.length
            caret: password.cursorPosition
            unit: root.u
            focused: password.activeFocus && password.enabled
            resetImmediately: root.failed
            visible: !root.failed
        }
        Text {
            anchors.fill: password
            verticalAlignment: Text.AlignVCenter
            text: root.busy ? "Signing in…" : "Enter your password"
            visible: password.length === 0 && runeMask.settledEmpty
            font.family: sans.name; font.pixelSize: 17 * root.u
            color: root.ivory
        }
        Controls.Button {
            id: submitButton
            anchors.right: parent.right; anchors.rightMargin: 13 * root.u
            anchors.verticalCenter: parent.verticalCenter
            width: 30 * root.u; height: width
            enabled: !root.busy && root.sessionIndex >= 0
            Accessible.name: "Sign in"
            KeyNavigation.tab: users
            KeyNavigation.backtab: password
            background: Rectangle {
                radius: height / 2
                color: submitButton.hovered || submitButton.activeFocus ? "#f6e5cc" : root.ivory
                border.width: submitButton.activeFocus ? 2 : 0; border.color: "#a88e6a"
            }
            contentItem: Text {
                text: "→"; color: "#273032"; font.pixelSize: 24 * root.u
                horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
            }
            onClicked: root.submit()
        }
    }
    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        y: field.y + field.height + 18 * root.u
        width: parent.width * 0.8
        text: root.sessionIndex < 0 ? "Session omarchy-saga.desktop is unavailable" : root.message
        horizontalAlignment: Text.AlignHCenter; wrapMode: Text.WordWrap
        font.family: sans.name; font.pixelSize: 13 * root.u
        color: root.failed ? "#e4ad96" : root.ivory
    }
    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        y: parent.height * 0.93
        text: "A TRUE WARRIOR NEEDS NO SWORD"
        font.family: serif.name; font.pixelSize: 12 * root.u; font.letterSpacing: 2.4 * root.u
        color: root.ivory
    }
    Component.onCompleted: password.forceActiveFocus()
}
