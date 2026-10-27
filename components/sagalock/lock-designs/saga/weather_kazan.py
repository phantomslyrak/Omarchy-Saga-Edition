"""Small on-demand SagaLock adapter. Fixed Kazan only; no geolocation or service."""
import datetime as dt
import fcntl
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from zoneinfo import ZoneInfo

LAT, LON = 55.78874, 49.12214
ZONE = 'Europe/Moscow'
TZ = ZoneInfo(ZONE)
INTERVAL, RETRY, MAX_AGE, CAP = 1200, 300, 21600, 65536
URL = ('https://api.open-meteo.com/v1/forecast?latitude=55.78874&longitude=49.12214'
       '&current=temperature_2m,apparent_temperature,weather_code,is_day'
       '&daily=temperature_2m_max,temperature_2m_min&timezone=Europe%2FMoscow&forecast_days=2')
IDENTITY = {'version': 1, 'latitude': LAT, 'longitude': LON, 'timezone': ZONE, 'source': 'Open-Meteo'}
REVISION = 'kazan-weather-2'
CODES = {0: ('Clear', 'sun'), 1: ('Mostly clear', 'cloud'), 2: ('Partly cloudy', 'cloud'),
         3: ('Overcast', 'cloud'), 45: ('Fog', 'fog'), 48: ('Freezing fog', 'fog'),
         51: ('Light drizzle', 'rain'), 53: ('Drizzle', 'rain'), 55: ('Heavy drizzle', 'rain'),
         56: ('Freezing drizzle', 'rain'), 57: ('Freezing drizzle', 'rain'),
         61: ('Light rain', 'rain'), 63: ('Rain', 'rain'), 65: ('Heavy rain', 'rain'),
         66: ('Freezing rain', 'rain'), 67: ('Freezing rain', 'rain'),
         71: ('Light snow', 'snow'), 73: ('Snow', 'snow'), 75: ('Heavy snow', 'snow'),
         77: ('Snow grains', 'snow'), 80: ('Rain showers', 'rain'), 81: ('Rain showers', 'rain'),
         82: ('Heavy showers', 'rain'), 85: ('Snow showers', 'snow'), 86: ('Heavy snow', 'snow'),
         95: ('Thunderstorm', 'storm'), 96: ('Storm with hail', 'storm'), 99: ('Storm with hail', 'storm')}


def number(value, low, high):
    if type(value) not in (float, int) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError('Invalid weather number')
    return value


def parse_report(data, now):
    if data.get('timezone') != ZONE or data.get('utc_offset_seconds') != 10800:
        raise ValueError('Wrong weather timezone')
    if abs(number(data.get('latitude'), -90, 90) - LAT) > .15 or abs(number(data.get('longitude'), -180, 180) - LON) > .15:
        raise ValueError('Weather response is outside Kazan')
    current, daily = data['current'], data['daily']
    if any(data['current_units'].get(k) != '°C' for k in ('temperature_2m', 'apparent_temperature')):
        raise ValueError('Wrong temperature units')
    if any(data['daily_units'].get(k) != '°C' for k in ('temperature_2m_max', 'temperature_2m_min')):
        raise ValueError('Wrong daily units')
    stamp = dt.datetime.fromisoformat(current['time'])
    if stamp.tzinfo is not None:
        raise ValueError('Expected timezone-local API timestamp')
    observed = stamp.replace(tzinfo=TZ).timestamp()
    if not -1800 <= now - observed <= MAX_AGE:
        raise ValueError('Outdated/future observation')
    code = current['weather_code']
    if type(code) is not int or code not in CODES or type(current['is_day']) is not int or current['is_day'] not in (0, 1):
        raise ValueError('Invalid weather code')
    condition, glyph = CODES[code]
    if code == 0 and current['is_day'] == 0:
        glyph = 'moon'
    today = dt.datetime.fromtimestamp(now, TZ).date().isoformat()
    days = daily['time']
    if not isinstance(days, list) or len(days) != len(daily['temperature_2m_max']) or len(days) != len(daily['temperature_2m_min']):
        raise ValueError('Invalid daily forecast')
    high = low = None
    if today in days:
        index = days.index(today)
        high = number(daily['temperature_2m_max'][index], -100, 70)
        low = number(daily['temperature_2m_min'][index], -100, 70)
        if low > high:
            raise ValueError('Invalid min/max')
    return {'available': True, 'place': 'KAZAN', 'tempC': number(current['temperature_2m'], -100, 70),
            'feelsC': number(current['apparent_temperature'], -120, 90), 'condition': condition,
            'glyph': glyph, 'maxC': high, 'minC': low, 'today': today, 'observedAt': observed}


def read_cache(path):
    try:
        if path.is_symlink() or path.stat().st_size >= CAP:
            return {}
        data = json.loads(path.read_text())
        if data.get('identity') != IDENTITY:
            return {}
        return data
    except (OSError, ValueError, TypeError, AttributeError):
        return {}


def fresh_report(data, now):
    parsed = parse_report(data, now)
    if now - parsed['observedAt'] > 7200 or parsed['maxC'] is None:
        raise ValueError('No fresh observation or Kazan-day forecast')
    return parsed


def present(cache, now):
    metadata = {'revision': REVISION, 'source': 'Open-Meteo', 'error': cache.get('error'),
                'lastAttemptAt': cache.get('attempt_at')}
    empty = dict(metadata, available=False, place='KAZAN', stale=False,
                 condition='Weather unavailable', glyph='cloud')
    try:
        fetched = number(cache['fetched_at'], 0, now + 1)
        if now - fetched > MAX_AGE:
            return empty
        result = parse_report(cache['report'], now)
        result.update(fetchedAt=fetched, stale=bool(cache.get('error')) or now - fetched >= INTERVAL
                      or now - result['observedAt'] > 3600)
        result.update(metadata)
        return result
    except (KeyError, ValueError, TypeError, AttributeError, OverflowError):
        return empty


def fetch():
    response = subprocess.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--proto', '=https',
                               '--connect-timeout', '5', '--max-time', '12', '--max-filesize', str(CAP), URL],
                              capture_output=True, timeout=15, check=True)
    if not response.stdout or len(response.stdout) >= CAP:
        raise ValueError('Empty/oversized weather response')
    return json.loads(response.stdout)


def error_detail(error):
    detail = {'type': type(error).__name__, 'message': str(error)[:600]}
    if isinstance(error, subprocess.CalledProcessError):
        detail['curlExit'] = error.returncode
        raw = error.stderr or b''
        detail['stderr'] = (raw.decode('utf-8', errors='replace') if isinstance(raw, bytes) else str(raw))[:600]
    return detail


def write_cache(path, data):
    descriptor, name = tempfile.mkstemp(prefix='.kazan-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w') as output:
            json.dump(data, output)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def update(path, now=None):
    now = time.time() if now is None else now
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Serialize screens/thumbnails. Contention returns cached data, never another request.
    fd = os.open(str(path) + '.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'a') as guard:
        try:
            fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return present(read_cache(path), now)
        cache = read_cache(path)
        last = cache.get('attempt_at', 0)
        interval = RETRY if cache.get('error') else INTERVAL
        if type(last) in (int, float) and math.isfinite(last) and 0 <= now - last < interval:
            return present(cache, now)
        try:
            data = fetch()
            fresh_report(data, now)
            cache = {'identity': IDENTITY, 'report': data, 'fetched_at': now}
        except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError, AttributeError, OverflowError) as error:
            cache.update(identity=IDENTITY, error=error_detail(error))
        cache['attempt_at'] = now
        write_cache(path, cache)
        return present(cache, now)


def main():
    if sys.argv[1:] not in ([], ['--diagnose']):
        return 2  # No configurable location, URL or IP fallback.
    cache_root = Path(os.environ.get('XDG_CACHE_HOME') or Path.home() / '.cache')
    if not cache_root.is_absolute():
        cache_root = Path.home() / '.cache'
    path = cache_root / 'omarchy-saga-edition' / 'weather-kazan-v1.json'
    if sys.argv[1:] == ['--diagnose']:
        # Explicit read-only probe bypasses cache TTL but never modifies cache/locks.
        now = time.time()
        diagnostic = {'revision': REVISION, 'url': URL, 'python': sys.executable,
                      'script': str(Path(__file__).resolve()), 'now': now,
                      'kazanNow': dt.datetime.fromtimestamp(now, TZ).isoformat(),
                      'cachePath': str(path), 'cached': present(read_cache(path), now)}
        try:
            raw = fetch()
            diagnostic['api'] = raw
            diagnostic['parsed'] = fresh_report(raw, time.time())
            diagnostic['ok'] = True
        except Exception as error:
            diagnostic.update(ok=False, error=error_detail(error))
        print(json.dumps(diagnostic, ensure_ascii=False))
        return 0 if diagnostic['ok'] else 1
    os.umask(0o077)
    try:
        result = update(path)
    except OSError as error:
        result = present({}, time.time())
        result['error'] = error_detail(error)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
