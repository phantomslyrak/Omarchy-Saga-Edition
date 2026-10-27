#!/usr/bin/env python3
"""Session-launch checks without a compositor, UWSM start, or live signals."""
import contextlib
import io
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
with patch.object(sys, 'argv', ['test-session', 'status']), contextlib.redirect_stdout(io.StringIO()):
    SESSION = runpy.run_path(str(ROOT / 'tools/test-session'))


class SessionTests(unittest.TestCase):
    def test_command(self):
        self.assertEqual(SESSION['command'], ['uwsm', 'start', '-U', 'run', '-F', '-D',
                         'Hyprland', '--', '/usr/bin/start-hyprland', '--path', str(ROOT / 'bin/Hyprland-saga-reveal')])

    def test_recovery_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            process = Path(directory)
            (process / 'exe').symlink_to('/usr/bin/start-hyprland')
            argv = SESSION['launcher_args']
            (process / 'cmdline').write_bytes(b'\0'.join(os.fsencode(a) for a in argv) + b'\0')
            self.assertTrue(SESSION['is_test_watchdog'](process))
            for wrong in [argv[:1], [argv[0], '--path', '/usr/bin/Hyprland'], argv + ['--', '--safe-mode']]:
                (process / 'cmdline').write_bytes(b'\0'.join(os.fsencode(a) for a in wrong) + b'\0')
                self.assertFalse(SESSION['is_test_watchdog'](process))
            (process / 'cmdline').write_bytes(b'\0'.join(os.fsencode(a) for a in argv) + b'\0')
            with patch.object(os, 'getuid', return_value=os.getuid() + 1):
                self.assertFalse(SESSION['is_test_watchdog'](process))

    def test_graphical_launch_guard(self):
        env = dict(os.environ, WAYLAND_DISPLAY='test-do-not-launch')
        result = subprocess.run([str(ROOT / 'tools/test-session'), 'launch'], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('launch only from a logged-in TTY', result.stderr)

    def test_preferred_default(self):
        with patch.object(sys, 'argv', ['control', 'status']), contextlib.redirect_stdout(io.StringIO()):
            control = runpy.run_path(str(ROOT / 'tools/control'))
        self.assertEqual(control['args'].ms, 700)

    def test_recovery_stops_supervisor_and_legacy_only(self):
        with tempfile.TemporaryDirectory() as directory:
            proc = Path(directory)
            for pid, exe, parent in [(1101, SESSION['launcher'], 1),
                                     (1102, SESSION['binary'], 1101),
                                     (1103, Path('/usr/bin/Hyprland'), 1),
                                     (1104, SESSION['binary'], 1103)]:
                process = proc / str(pid)
                process.mkdir()
                (process / 'exe').symlink_to(exe)
                (process / 'stat').write_text(f'{pid} (name with spaces) S {parent} 0')
                (process / 'cmdline').write_bytes(b'\0'.join(os.fsencode(a) for a in SESSION['launcher_args']) + b'\0')
            original_path = Path
            def mapped_path(value):
                return proc if str(value) == '/proc' else original_path(value)
            globals_ = SESSION['terminate_test_session'].__globals__
            with patch.dict(globals_, Path=mapped_path), \
                    patch.object(os, 'pidfd_open', side_effect=lambda pid: pid), \
                    patch.object(os, 'close'), \
                    patch.object(SESSION['signal'], 'pidfd_send_signal') as send, \
                    contextlib.redirect_stdout(io.StringIO()):
                SESSION['terminate_test_session']()
            self.assertEqual([call.args[0] for call in send.call_args_list], [1101, 1104])

    def test_installed_launcher_watchdog(self):
        # A protocol stub, never a compositor: it opens no display/DRM/input.
        # Simulate an initialized, locked child exiting, then a clean safe restart.
        with tempfile.TemporaryDirectory() as directory:
            stub = Path(directory) / 'protocol-stub'
            stub.write_text('''#!/usr/bin/env python3
import os, sys
args = sys.argv[1:]
assert args[0] == '--watchdog-fd', args
fd = int(args[1])
if '--safe-mode' not in args:
    os.write(fd, b'vax\\nlock\\n')
    os.close(fd)
    sys.exit(1)
assert '--locked' in args, args
os.write(fd, b'vax\\nend\\n')
os.close(fd)
print('stub: safe-mode and locked restart verified')
''')
            stub.chmod(0o700)
            result = subprocess.run(['/usr/bin/start-hyprland', '--path', str(stub)], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('stub: safe-mode and locked restart verified', result.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
