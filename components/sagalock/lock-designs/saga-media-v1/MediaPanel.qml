import QtQuick
import Quickshell.Services.Mpris
import "../../plugins/io.github.sirjul1337.lock-explorer/designs" as Native

// Display only. Selection and polling never invoke MPRIS control methods.
Item {
    id: media
    visible: false
    property bool active: true
    property var candidates: Mpris.players ? Mpris.players.values : []
    readonly property var player: {
        const list = candidates.filter(p => p && String(p.trackTitle || "").trim().length > 0
            && (p.playbackState === MprisPlaybackState.Playing || p.playbackState === MprisPlaybackState.Paused))
        list.sort(function(a, b) {
            const ar = a.playbackState === MprisPlaybackState.Playing ? 0 : 1
            const br = b.playbackState === MprisPlaybackState.Playing ? 0 : 1
            if (ar !== br) return ar - br
            const ak = String(a.dbusName || ""), bk = String(b.dbusName || "")
            return ak < bk ? -1 : ak > bk ? 1 : 0
        })
        return list.length ? list[0] : null
    }
    readonly property bool hasMedia: player !== null
    readonly property bool playing: player !== null && player.playbackState === MprisPlaybackState.Playing
    readonly property string title: player !== null ? String(player.trackTitle || "").slice(0, 200) : ""
    readonly property string artist: player !== null ? String(player.trackArtist || "").slice(0, 200) : ""
    readonly property string trackIdentity: player !== null ? String(player.dbusName) + "|" + String(player.uniqueId || "") + "|" + title : ""
    readonly property real duration: player !== null && player.lengthSupported && isFinite(player.length) && player.length > 0 ? player.length : 0
    property real position: 0
    readonly property bool positionKnown: player !== null && player.positionSupported && duration > 0
    readonly property real progress: positionKnown ? Math.max(0, Math.min(1, position / duration)) : -1
    // Reuse Explorer's bounded subprocess decoder. Do not show the old cover
    // while the replacement is being decoded, or fetch any unrelated artwork.
    readonly property string artUrl: hasMedia && cover.loaded === cover.wanted ? cover.source : ""
    Native.CoverArt { id: cover; url: media.player !== null ? String(media.player.trackArtUrl || "") : "" }
    function samplePosition() {
        const value = player !== null && player.positionSupported ? player.position : 0
        position = isFinite(value) && value >= 0 ? (duration > 0 ? Math.min(value, duration) : value) : 0
    }
    onPlayerChanged: samplePosition()
    onTrackIdentityChanged: samplePosition()
    onDurationChanged: samplePosition()
    onPlayingChanged: samplePosition()
    onActiveChanged: if (active) samplePosition()
    Connections {
        target: media.player
        function onPositionChanged() { media.samplePosition() }
    }
    Timer { interval: 1000; repeat: true; running: media.active && media.hasMedia; triggeredOnStart: true; onTriggered: media.samplePosition() }
}
