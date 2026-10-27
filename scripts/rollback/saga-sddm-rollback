#!/usr/bin/env bash
set -euo pipefail
[[ $EUID == 0 ]] || { echo 'Run with sudo.' >&2; exit 1; }
exec /usr/bin/python3 - "$@" <<'PY'
import configparser, hashlib, json, os, pathlib, sys, tempfile
P=pathlib.Path
backup=P(P('/var/lib/saga-sddm/active-backup').read_text().strip())
if backup.parent != P('/var/lib/saga-sddm/backups') or backup.is_symlink():
    raise SystemExit('Invalid backup path')
m=json.loads((backup/'manifest.json').read_text())
for path,digest in m['installed'].items():
    p=P(path)
    if p.is_symlink() or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
        raise SystemExit('Installed file changed; refusing rollback: '+path)
original=(backup/'omarchy-saga.desktop').read_bytes()
if hashlib.sha256(original).hexdigest()!=m['original_session_sha256']:
    raise SystemExit('Session backup checksum failed')
if sys.argv[1:]==['--check']:
    print('Rollback preflight OK; backup and installed files verified. No changes made.')
    raise SystemExit(0)
if len(sys.argv)>1: raise SystemExit('Usage: saga-sddm-rollback [--check]')
p=P('/usr/share/wayland-sessions/omarchy-saga.desktop')
fd,tmp=tempfile.mkstemp(prefix='.saga-restore-',dir=p.parent)
with os.fdopen(fd,'wb') as f:f.write(original)
os.chmod(tmp,m['original_session_mode']);os.chown(tmp,m['original_session_uid'],m['original_session_gid']);os.replace(tmp,p)
P('/etc/sddm.conf.d/zzzzz-saga-sddm-theme.conf').unlink()
# Restore the previous launch route. Theme assets remain available for inspection.
P('/usr/local/libexec/saga-session-launcher').unlink()
c=configparser.ConfigParser(strict=False,interpolation=None)
files=[]
for d in ('/usr/lib/sddm/sddm.conf.d','/etc/sddm.conf.d'):files.extend(sorted(P(d).glob('*.conf')))
if P('/etc/sddm.conf').exists():files.append(P('/etc/sddm.conf'))
c.read(files)
assert c.get('Theme','Current',fallback='')==m['previous_theme']
assert c.get('Autologin','Session',fallback='')==m['autologin_session']
print('Restored Theme.Current='+m['previous_theme']+' and original session entry. Autologin unchanged. No restart.')
PY
