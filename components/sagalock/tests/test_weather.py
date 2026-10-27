"""Synthetic weather data is confined to tests; production fetch URL is fixed."""
import copy
import datetime as dt
import fcntl
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / 'lock-designs/saga/weather_kazan.py'
spec = importlib.util.spec_from_file_location('weather', PATH)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
NOW = dt.datetime(2026, 10, 26, 0, 15, tzinfo=m.TZ).timestamp()


def report():
    return dict(timezone=m.ZONE, utc_offset_seconds=10800, latitude=55.79, longitude=49.125,
        current_units={'temperature_2m': '°C', 'apparent_temperature': '°C'},
        daily_units={'temperature_2m_max': '°C', 'temperature_2m_min': '°C'},
        current={'time': '2026-10-26T00:00', 'temperature_2m': 4.2, 'apparent_temperature': 2.1, 'weather_code': 3, 'is_day': 0},
        daily={'time': ['2026-10-25', '2026-10-26'], 'temperature_2m_max': [10, 8], 'temperature_2m_min': [3, 1]})


class Weather(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.cache = Path(self.temp.name) / 'kazan.json'

    def test_fixed_url_and_no_location_argument(self):
        self.assertIn('latitude=55.78874&longitude=49.12214', m.URL)
        self.assertIn('timezone=Europe%2FMoscow', m.URL)
        with patch.object(m.sys, 'argv', ['weather_kazan.py', 'London']), patch.object(m, 'fetch') as fetch:
            self.assertEqual(m.main(), 2); fetch.assert_not_called()

    def test_success_and_twenty_minute_cache(self):
        with patch.object(m, 'fetch', return_value=report()) as fetch:
            first = m.update(self.cache, NOW); second = m.update(self.cache, NOW+60)
            self.assertEqual(fetch.call_count, 1)
        self.assertTrue(first['available']); self.assertFalse(first['stale'])
        self.assertEqual(first['place'], 'KAZAN'); self.assertEqual(first['tempC'], 4.2)
        self.assertEqual(second['tempC'], first['tempC'])

    def test_kazan_day_differs_from_utc_and_laptop_date(self):
        # NOW is October 25 UTC, but October 26 in Kazan.
        self.assertEqual(dt.datetime.fromtimestamp(NOW, dt.timezone.utc).day, 25)
        result = m.parse_report(report(), NOW)
        self.assertEqual(result['today'], '2026-10-26'); self.assertEqual(result['maxC'], 8)
        self.assertEqual(result['minC'], 1)

    def test_offline_cache_is_stale_and_failure_is_throttled(self):
        with patch.object(m, 'fetch', return_value=report()): m.update(self.cache, NOW)
        with patch.object(m, 'fetch', side_effect=OSError('offline')) as fetch:
            result = m.update(self.cache, NOW+1201); m.update(self.cache, NOW+1260)
            self.assertEqual(fetch.call_count, 1)
        self.assertTrue(result['available']); self.assertTrue(result['stale'])

    def test_offline_without_cache_is_unavailable(self):
        with patch.object(m, 'fetch', side_effect=OSError('offline')):
            result = m.update(self.cache, NOW)
        self.assertFalse(result['available']); self.assertEqual(result['place'], 'KAZAN')

    def test_http_timeout_and_malformed_response(self):
        failures = [subprocess.CalledProcessError(22, 'curl'), subprocess.TimeoutExpired('curl', 15),
                    ValueError('not JSON')]
        for failure in failures:
            with self.subTest(failure=failure), patch.object(m, 'fetch', side_effect=failure):
                if self.cache.exists(): self.cache.unlink()
                self.assertFalse(m.update(self.cache, NOW)['available'])

    def test_invalid_data_and_wrong_city_refused(self):
        for field, value in [('latitude', 51.5), ('longitude', 0), ('timezone', 'Europe/London'),
                             ('utc_offset_seconds', 0), ('current', {})]:
            data = report(); data[field] = value
            with patch.object(m, 'fetch', return_value=data):
                if self.cache.exists(): self.cache.unlink()
                self.assertFalse(m.update(self.cache, NOW)['available'])
        for field, value in [('temperature_2m', None), ('temperature_2m', float('nan')),
                             ('weather_code', 999), ('time', 'garbage')]:
            data = report(); data['current'][field] = value
            with self.assertRaises((ValueError, KeyError, TypeError)): m.parse_report(data, NOW)

    def test_units_and_daily_bounds_refused(self):
        data = report(); data['current_units']['temperature_2m'] = '°F'
        with self.assertRaises(ValueError): m.parse_report(data, NOW)
        data = report(); data['daily']['temperature_2m_min'][1] = 50
        with self.assertRaises(ValueError): m.parse_report(data, NOW)

    def test_stale_cache_expires(self):
        with patch.object(m, 'fetch', return_value=report()): m.update(self.cache, NOW)
        cache = m.read_cache(self.cache)
        self.assertFalse(m.present(cache, NOW+m.MAX_AGE+1)['available'])

    def test_previous_day_extrema_are_not_reused(self):
        data = report(); data['daily']['time'] = ['2026-10-24', '2026-10-25']
        result = m.parse_report(data, NOW)
        self.assertIsNone(result['maxC']); self.assertIsNone(result['minC'])

    def test_external_ip_and_network_env_cannot_change_url(self):
        with patch.dict(m.os.environ, {'CITY': 'London', 'TZ': 'Pacific/Honolulu', 'LOCATION': 'Paris'}):
            with patch.object(m.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, json.dumps(report()).encode())) as run:
                m.fetch()
                self.assertEqual(run.call_args.args[0][-1], m.URL)
                self.assertNotIn('wttr.in', m.URL)

    def test_corrupt_or_other_city_cache_ignored(self):
        for raw in ('{', '[]', 'null'):
            self.cache.write_text(raw)
            self.assertEqual(m.read_cache(self.cache), {})
        self.cache.write_text(json.dumps({'identity': {'city': 'Kyiv'}}))
        self.assertEqual(m.read_cache(self.cache), {})

    def test_contention_does_not_fetch_twice(self):
        lock = open(str(self.cache)+'.lock', 'a')
        self.addCleanup(lock.close); fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with patch.object(m, 'fetch') as fetch:
            self.assertFalse(m.update(self.cache, NOW)['available']); fetch.assert_not_called()

    def test_fetch_size_and_deadline(self):
        with patch.object(m.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, b'x' * m.CAP)) as run:
            with self.assertRaises(ValueError): m.fetch()
            self.assertEqual(run.call_args.kwargs['timeout'], 15)
            self.assertIn('--max-time', run.call_args.args[0])

    def test_current_observation_future_or_too_old_refused(self):
        for timestamp in ('2026-10-27T00:00', '2026-10-24T00:00'):
            data=report();data['current']['time']=timestamp
            with self.assertRaises(ValueError): m.parse_report(data,NOW)

    def test_all_battery_independent_weather_codes_and_night(self):
        for code in m.CODES:
            data=report();data['current']['weather_code']=code
            self.assertTrue(m.parse_report(data,NOW)['glyph'])
        data=report();data['current']['weather_code']=0
        self.assertEqual(m.parse_report(data,NOW)['glyph'],'moon')


if __name__ == '__main__': unittest.main()
