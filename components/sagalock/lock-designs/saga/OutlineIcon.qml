import QtQuick

Canvas {
    id: icon
    property string kind: ""
    property color stroke: "#d7c4aa"
    property real strokeWidth: 1.15
    width: 24; height: 24
    onKindChanged: requestPaint()
    onStrokeChanged: requestPaint()
    onStrokeWidthChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onPaint: {
        const c = getContext("2d")
        c.reset(); c.scale(width / 24, height / 24)
        c.strokeStyle = stroke; c.lineWidth = strokeWidth; c.lineCap = "round"; c.lineJoin = "round"
        function line(x, y, xx, yy) { c.moveTo(x,y); c.lineTo(xx,yy) }
        c.beginPath()
        if (["cloud", "rain", "snow", "storm"].indexOf(kind) >= 0) {
            c.moveTo(6,18); c.bezierCurveTo(0,18,0,10,6,10)
            c.bezierCurveTo(6,1,18,1,18,10); c.bezierCurveTo(25,9,25,18,19,18); c.closePath()
            if (kind === "rain") { line(7,20,5,23); line(14,20,12,23); line(21,20,19,23) }
            if (kind === "snow") { line(7,21,11,21); line(9,19,9,23); line(16,21,20,21); line(18,19,18,23) }
            if (kind === "storm") { line(13,16,10,21); line(10,21,15,20); line(15,20,12,24) }
        } else if (kind === "sun") {
            c.arc(12,12,5,0,Math.PI*2)
            for (let i=0; i<8; i++) { const a=i*Math.PI/4; line(12+8*Math.cos(a),12+8*Math.sin(a),12+11*Math.cos(a),12+11*Math.sin(a)) }
        } else if (kind === "fog") { for (let y=6; y<=18; y+=6) line(3,y,21,y) }
        else if (kind === "cpu") {
            c.rect(5,5,14,14); c.rect(9,9,6,6)
            for (let i=8; i<=16; i+=4) { line(i,2,i,5); line(i,19,i,22); line(2,i,5,i); line(19,i,22,i) }
        } else if (kind === "ram") {
            c.ellipse(4,3,16,5)
            for (let y=8; y<=18; y+=5) { c.moveTo(4,y); c.bezierCurveTo(4,y+5,20,y+5,20,y) }
            line(4,5,4,18); line(20,5,20,18)
        } else if (kind === "disk") {
            c.moveTo(5,4); c.lineTo(19,4); c.lineTo(22,20); c.lineTo(2,20); c.closePath()
            line(3,15,21,15); line(6,18,8,18); line(17,18,18,18)
        } else if (kind === "battery") {
            c.rect(2,6,18,12); c.rect(20,10,2,4); c.rect(4,8,12,8)
        } else if (kind === "bolt") {
            c.moveTo(14,2); c.lineTo(5,14); c.lineTo(12,14); c.lineTo(10,22); c.lineTo(19,10); c.lineTo(12,10); c.closePath()
        } else if (kind === "previous" || kind === "next") {
            if (kind === "next") { c.translate(24,0); c.scale(-1,1) }
            line(4,5,4,19); c.moveTo(18,5); c.lineTo(7,12); c.lineTo(18,19); c.closePath()
        } else if (kind === "pause") { line(8,5,8,19); line(16,5,16,19) }
        else if (kind === "play") { c.moveTo(7,4); c.lineTo(20,12); c.lineTo(7,20); c.closePath() }
        else if (kind === "power") {
            c.arc(12,13,8,-Math.PI*0.32,Math.PI*1.32); line(12,2,12,12)
        } else if (kind === "reboot") {
            c.arc(12,12,8,-0.8,Math.PI*1.6); line(18,3,18,8); line(18,8,22,7)
        } else if (kind === "moon") {
            c.moveTo(17,3); c.bezierCurveTo(4,-1,-2,15,9,21); c.bezierCurveTo(16,25,22,19,22,15)
            c.bezierCurveTo(9,20,5,7,17,3)
        } else if (kind === "lock") {
            c.rect(5,10,14,11); c.moveTo(8,10); c.lineTo(8,6); c.bezierCurveTo(8,0,16,0,16,6); c.lineTo(16,10); line(12,14,12,17)
        } else if (kind === "arrow") { line(4,12,20,12); line(14,6,20,12); line(20,12,14,18) }
        else if (kind === "music") {
            line(9,17,9,5); line(9,5,20,3); line(20,3,20,15); c.ellipse(3,16,6,4); c.ellipse(14,14,6,4)
        }
        c.stroke()
    }
}
