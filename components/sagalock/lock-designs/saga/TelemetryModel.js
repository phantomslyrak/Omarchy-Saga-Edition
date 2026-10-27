// Pure parsers shared with isolated tests. Fractions are 0..1; null means unavailable.
function cpuCounters(raw) {
    const fields = String(raw).split('\n')[0].trim().split(/\s+/)
    if (fields.shift() !== 'cpu' || fields.length < 8) return null
    const values = fields.slice(0, 8).map(Number) // guest/guest_nice already included in user/nice
    if (values.some(v => !Number.isSafeInteger(v) || v < 0)) return null
    return { total: values.reduce((a, b) => a + b, 0), idle: values[3] + values[4] }
}
function cpuSample(previous, counters, now) {
    if (!counters) return { cpu: -1, previous: null, reset: true }
    const next = { total: counters.total, idle: counters.idle, at: now }
    if (!previous || now <= previous.at || now - previous.at > 6500)
        return { cpu: -1, previous: next, reset: true }
    const total = counters.total - previous.total, idle = counters.idle - previous.idle
    if (total <= 0 || idle < 0 || idle > total) return { cpu: -1, previous: next, reset: true }
    return { cpu: 1 - idle / total, previous: next, reset: false }
}
function memory(raw) {
    const total = String(raw).match(/^MemTotal:\s+(\d+)\s+kB/m)
    const available = String(raw).match(/^MemAvailable:\s+(\d+)\s+kB/m)
    if (!total || !available) return null
    const t = Number(total[1]), a = Number(available[1])
    if (!Number.isSafeInteger(t) || !Number.isSafeInteger(a) || t <= 0 || a < 0 || a > t) return null
    return { ratio: (t - a) / t, text: ((t - a) / 1048576).toFixed(1) + ' / ' + (t / 1048576).toFixed(1) + ' GiB' }
}
function disk(raw, code) {
    const rows = String(raw).trim().split('\n')
    if (code !== 0 || rows.length !== 2) return -1
    const values = rows[1].trim().split(/\s+/).map(Number)
    if (values.length !== 2 || values.some(v => !Number.isSafeInteger(v)) || values[0] <= 0 || values[1] < 0 || values[1] > values[0]) return -1
    return values[1] / values[0]
}
function battery(raw) {
    const text = String(raw).trim()
    if (!/^\d{1,3}$/.test(text)) return -1
    const value = Number(text)
    return value <= 100 ? value : -1
}
function batteryStatus(raw) {
    const status = String(raw).trim()
    return ['Charging', 'Discharging', 'Full', 'Not charging'].indexOf(status) >= 0 ? status : ''
}
