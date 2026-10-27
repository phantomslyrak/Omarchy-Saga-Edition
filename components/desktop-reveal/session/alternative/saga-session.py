#!/usr/bin/python3
"""Saga session entry, guarded compositor child and persistent recovery controls."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parent
BINARY = ROOT.parent / 'bin/Hyprland-saga-reveal'
STATE = Path.home() / '.local/state/omarchy-saga-session'
MANIFEST = ROOT / 'compatibility.json'
CONTROL = ROOT.parent / 'tools/control'
GUARD = ROOT / 'saga-compositor'
STOCK = '/usr/bin/Hyprland'

def digest(path):
    with open(path, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name(path.name + '.' + str(os.getpid()))
    tmp.write_text(data)
    os.replace(tmp, path)

def log(message):
    print('Saga: ' + message, file=sys.stderr, flush=True)
    atomic(STATE / 'last-event', time.strftime('%Y-%m-%d %H:%M:%S ') + message + '\n')

def compatible():
    try:
        if not BINARY.is_file() or not os.access(BINARY, os.X_OK):
            return False, 'Saga binary missing or not executable'
        baseline = json.loads(MANIFEST.read_text())
        for name, expected in baseline['files'].items():
            if digest(name) != expected:
                return False, 'changed file: ' + name
        installed = subprocess.check_output(['/usr/bin/pacman', '-Q', *baseline['packages']], text=True)
        if installed != baseline['package_versions']:
            return False, 'Hyprland/session/dependency package versions changed'
        return True, 'compatible with recorded tested build'
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        return False, str(error)

def runtime():
    path = Path('/run/user') / str(os.getuid())
    st = path.stat()
    if st.st_uid != os.getuid() or st.st_mode & 0o022:
        raise RuntimeError('unsafe runtime directory')
    return path

def reveal(enabled):
    subprocess.run([str(CONTROL), 'enable' if enabled else 'disable', '--ms', '700'], check=True)

def selection():
    ok, reason = compatible()
    if (STATE / 'stock-primary').exists():
        return STOCK, 'stock selected by user'
    if (STATE / 'quarantined').exists():
        return STOCK, 'Saga quarantined; inspect last-event, adapt patch after updates, then rearm'
    return (str(BINARY), reason) if ok else (STOCK, 'Saga blocked: ' + reason + '; patch adaptation/revalidation required, no automatic rebuild')

def command():
    # Keep start-hyprland as the UWSM executable ID: loads its Hyprland quirks.
    return ['/usr/bin/uwsm', 'start', '-g', '-1', '-e', '-U', 'run', '-F', '-D', 'Hyprland', '--',
            '/usr/bin/start-hyprland', '--path', str(GUARD), '--', '--saga-token', uuid.uuid4().hex]

def child(arguments):
    if len(arguments) < 2 or arguments[0] != '--saga-token':
        # start-hyprland prepends watchdog/safe-mode arguments, so locate our pair.
        index = arguments.index('--saga-token')
    else:
        index = 0
    token = arguments[index + 1]
    if len(token) != 32 or any(c not in '0123456789abcdef' for c in token):
        raise ValueError('invalid session token')
    arguments = arguments[:index] + arguments[index + 2:]
    fd_index = arguments.index('--watchdog-fd')
    watchdog_fd = int(arguments[fd_index + 1])
    ledger = runtime() / ('saga-session-' + token)
    attempt = int(ledger.read_text()) + 1 if ledger.exists() else 1
    atomic(ledger, str(attempt))
    if attempt > 2:
        atomic(STATE / 'quarantined', 'restart budget exhausted\n')
        log('Restart budget exhausted; returning to login screen. Use stock session or TTY recovery.')
        os.write(watchdog_fd, b'end\n')
        return 1
    executable, reason = selection()
    if attempt > 1:
        atomic(STATE / 'quarantined', 'watchdog restarted compositor\n')
        executable, reason = STOCK, 'watchdog restart: fallback to stock, retaining safe-mode/locked arguments'
    log(reason)
    reveal(executable == str(BINARY) and not (STATE / 'reveal-disabled').exists())
    atomic(STATE / 'last-launch.json', json.dumps({'executable': executable, 'attempt': attempt, 'duration_ms': 700, 'reason': reason}, indent=2))
    parent = os.getpid()
    def child_setup():
        # Preserve watchdog semantics if the wrapper is forcibly killed.
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(1, signal.SIGKILL, 0, 0, 0) != 0 or os.getppid() != parent:
            os._exit(125)
    process = subprocess.Popen([executable, *arguments], pass_fds=(watchdog_fd,), preexec_fn=child_setup)
    def forward(signum, frame):
        try:
            process.send_signal(signum)
        except ProcessLookupError:
            pass
    signal.signal(signal.SIGTERM, forward)
    signal.signal(signal.SIGINT, forward)
    code = process.wait()
    if code != 0:
        atomic(STATE / 'quarantined', 'compositor failed with ' + str(code) + '\n')
        log('Compositor failed; subsequent Saga logins use stock until explicit rearm.')
    return code if code >= 0 else 128 - code

def watchdog_matches(proc):
    argv = (proc / 'cmdline').read_bytes().split(b'\0')
    prefix = [b'/usr/bin/start-hyprland', b'--path', os.fsencode(GUARD), b'--', b'--saga-token']
    return (proc.stat().st_uid == os.getuid()
            and os.readlink(proc / 'exe') == '/usr/bin/start-hyprland'
            and argv[:5] == prefix and len(argv) == 7 and argv[-1] == b''
            and len(argv[5]) == 32 and all(c in b'0123456789abcdef' for c in argv[5]))

def terminate_watchdog():
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        fd = None
        try:
            fd = os.pidfd_open(int(proc.name))
            if watchdog_matches(proc):
                signal.pidfd_send_signal(fd, signal.SIGTERM)
                print('Sent SIGTERM to Saga watchdog:', proc.name)
        except (OSError, ProcessLookupError):
            continue
        finally:
            if fd is not None:
                os.close(fd)

def main():
    if Path(sys.argv[0]).name == 'saga-compositor':
        return child(sys.argv[1:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['launch', 'check', 'status', 'disable-reveal', 'enable-reveal', 'stock-primary', 'saga-primary', 'rearm', 'recover'])
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--terminate', action='store_true', help='recover only: terminate the exact Saga watchdog, for manual TTY recovery')
    args = parser.parse_args()
    if args.terminate and args.action != 'recover':
        parser.error('--terminate is only supported with recover')
    if args.action == 'launch':
        cmd = command()
        if args.dry_run:
            import shlex
            print(shlex.join(cmd))
            print('Selection:', *selection())
            return 0
        if os.environ.get('WAYLAND_DISPLAY') or os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):
            parser.error('launch only from login manager or an idle TTY')
        os.environ['OMARCHY_PATH'] = '/usr/share/omarchy'
        os.execv(cmd[0], cmd)
    elif args.action in ('check', 'status'):
        ok, reason = compatible()
        print('Compatibility:', ok, reason)
        print('Next Saga entry:', *selection())
        print('Reveal:', 'disabled persistently' if (STATE / 'reveal-disabled').exists() else '700 ms at each Saga start')
        if (STATE / 'last-launch.json').exists():
            print('Last launch:', (STATE / 'last-launch.json').read_text())
        print('Visible compositor processes (run status in a host terminal for the real session):')
        for proc in Path('/proc').iterdir():
            try:
                exe = (proc / 'exe').resolve(strict=True)
                if proc.stat().st_uid == os.getuid() and str(exe) in (str(BINARY), STOCK):
                    print(proc.name, exe)
            except (OSError, ValueError):
                pass
        return 0 if args.action == 'status' or ok else 1
    elif args.action in ('disable-reveal', 'recover', 'stock-primary'):
        if args.dry_run:
            print('Would persist stock/reveal preferences; recover --terminate targets only exact same-user Saga watchdog argv.')
            return 0
        atomic(STATE / 'reveal-disabled', 'disabled by user\n')
        if args.action != 'disable-reveal':
            atomic(STATE / 'stock-primary', 'use stock at next login\n')
        reveal(False)
        if args.terminate:
            terminate_watchdog()
        print('Reveal disabled persistently.' + (' Next Saga login launches stock; no current process stopped.' if args.action != 'disable-reveal' else ''))
    elif args.action == 'enable-reveal':
        (STATE / 'reveal-disabled').unlink(missing_ok=True)
        reveal(True)
    else:
        ok, reason = compatible()
        if not ok:
            parser.error('refusing to rearm: ' + reason + '; adapt and revalidate patch, do not refresh baseline blindly')
        (STATE / 'quarantined').unlink(missing_ok=True)
        if args.action == 'saga-primary':
            (STATE / 'stock-primary').unlink(missing_ok=True)
        print('Saga rearmed for next login. Reveal preference preserved.')
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print('Saga session refused: ' + str(error), file=sys.stderr)
        sys.exit(1)
