import QtQuick
import Quickshell.Io

Item {
    id: weather
    visible: false
    property bool active: true
    property var report: ({ available: false, stale: false })
    property double checkedAt: Date.now()
    readonly property bool available: report.available === true && typeof report.tempC === "number" && isFinite(report.tempC)
        && typeof report.fetchedAt === "number" && checkedAt >= report.fetchedAt * 1000
        && checkedAt - report.fetchedAt * 1000 <= 21600000
    readonly property bool stale: available && (report.stale === true || checkedAt - report.fetchedAt * 1000 >= 1200000)
    readonly property string place: "KAZAN"
    readonly property string condition: available ? String(report.condition) : "Weather unavailable"
    readonly property string glyph: available ? String(report.glyph) : "cloud"
    readonly property string tempC: available ? Math.round(report.tempC) + "°C" : "—"
    readonly property string kazanDay: new Date(checkedAt + 10800000).toISOString().slice(0, 10)
    readonly property string extremes: available && report.today === kazanDay && report.maxC !== null && report.minC !== null
        ? "↑ " + Math.round(report.maxC) + "°   ↓ " + Math.round(report.minC) + "°" : ""
    readonly property string revision: "weather-link-2"
    readonly property string helperPath: decodeURIComponent(Qt.resolvedUrl("weather_kazan.py").toString().replace(/^file:\/\//, ""))
    property string lastError: ""
    property string lastStderr: ""
    property int lastExitCode: -1
    property bool stdoutFinished: false
    property bool stderrFinished: false
    function refresh() {
        checkedAt = Date.now()
        if (active && !fetchProc.running) {
            stdoutFinished = false; stderrFinished = false; lastExitCode = -1
            fetchProc.running = true
        }
    }
    function finish() {
        if (!stdoutFinished || !stderrFinished || lastExitCode < 0) return
        try {
            if (lastExitCode !== 0) throw new Error("Helper exit " + lastExitCode + ": " + lastStderr)
            const value = JSON.parse(output.text)
            if (value.revision !== "kazan-weather-2" || value.place !== "KAZAN" || typeof value.available !== "boolean")
                throw new Error("Invalid/old weather helper result")
            weather.checkedAt = Date.now()
            weather.report = value
            const detail = value.error ? JSON.stringify(value.error) : ""
            if (detail && detail !== lastError) console.warn("SAGA_WEATHER_FETCH", detail)
            lastError = detail
        } catch (error) {
            lastError = String(error)
            console.warn("SAGA_WEATHER_LINK", lastError)
            weather.report = Object.assign({}, weather.report, { stale: true })
        }
    }
    Process {
        id: fetchProc
        command: ["/usr/bin/python3", "-B", weather.helperPath]
        stdout: StdioCollector { id: output; waitForEnd: true; onStreamFinished: { weather.stdoutFinished = true; weather.finish() } }
        stderr: StdioCollector { waitForEnd: true; onStreamFinished: { weather.lastStderr = text; weather.stderrFinished = true; weather.finish() } }
        onExited: function(code) { weather.lastExitCode = code; weather.finish() }
    }
    // Minute heartbeat updates age/resume state; helper enforces 20min success/5min failure TTL.
    Timer { interval: 60000; running: weather.active; repeat: true; onTriggered: weather.refresh() }
    onActiveChanged: if (active) refresh()
    Component.onCompleted: { console.info("SAGA_WEATHER_LOADED", revision, helperPath); refresh() }
}
