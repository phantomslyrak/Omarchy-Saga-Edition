import QtQuick
import Quickshell.Io
import "TelemetryModel.js" as Model

Item {
    id: stats
    visible: false
    property bool polling: true
    property real cpu: -1
    property real ram: -1
    property real disk: -1
    property string ramText: "—"
    property int battery: -1
    property string batteryStatus: ""
    property var history: []
    property var previousCpu: null
    property double lastPoll: 0

    function resetCpu() { previousCpu = null; cpu = -1; history = [] }
    function refreshSlow() {
        memFile.reload(); batteryFile.reload(); batteryStatusFile.reload()
        if (!diskProc.running) diskProc.running = true
    }
    function pollCpu() {
        const now = Date.now()
        if (lastPoll && (now - lastPoll > 6500 || now < lastPoll)) { resetCpu(); refreshSlow() }
        lastPoll = now
        cpuFile.reload()
    }
    FileView {
        id: cpuFile
        path: "/proc/stat"
        printErrors: false
        onLoadFailed: stats.resetCpu()
        onLoaded: {
            const result = Model.cpuSample(stats.previousCpu, Model.cpuCounters(text()), Date.now())
            stats.cpu = result.cpu
            stats.previousCpu = result.previous
            if (result.reset) stats.history = []
            if (result.cpu >= 0) stats.history = stats.history.concat([result.cpu]).slice(-48)
        }
    }
    FileView {
        id: memFile
        path: "/proc/meminfo"
        printErrors: false
        onLoadFailed: { stats.ram = -1; stats.ramText = "—" }
        onLoaded: {
            const value = Model.memory(text())
            stats.ram = value ? value.ratio : -1
            stats.ramText = value ? value.text : "—"
        }
    }
    FileView {
        id: batteryFile
        path: "/sys/class/power_supply/BAT0/capacity"
        printErrors: false
        onLoadFailed: stats.battery = -1
        onLoaded: stats.battery = Model.battery(text())
    }
    FileView {
        id: batteryStatusFile
        path: "/sys/class/power_supply/BAT0/status"
        printErrors: false
        onLoadFailed: stats.batteryStatus = ""
        onLoaded: stats.batteryStatus = Model.batteryStatus(text())
    }
    Process {
        id: diskProc
        command: ["timeout", "--kill-after=1s", "4s", "df", "--output=size,used", "-B1", "/"]
        stdout: StdioCollector { id: diskOut; waitForEnd: true }
        onExited: function(code) { stats.disk = Model.disk(diskOut.text, code) }
    }
    Timer { interval: 2000; running: stats.polling; repeat: true; onTriggered: stats.pollCpu() }
    Timer { interval: 5000; running: stats.polling; repeat: true; onTriggered: memFile.reload() }
    Timer {
        interval: 30000; running: stats.polling; repeat: true
        onTriggered: { batteryFile.reload(); batteryStatusFile.reload() }
    }
    Timer { interval: 60000; running: stats.polling; repeat: true; onTriggered: if (!diskProc.running) diskProc.running = true }
    onPollingChanged: {
        resetCpu(); lastPoll = 0
        if (polling) { pollCpu(); refreshSlow() }
    }
    Component.onCompleted: if (polling) { pollCpu(); refreshSlow() }
}
