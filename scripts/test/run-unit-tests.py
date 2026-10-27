#!/usr/bin/env python3
"""Run isolated existing unit tests. Writes only below repository .local/."""
from pathlib import Path
import os, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
work=ROOT/'.local';tmp=work/'tmp';tmp.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(tmp),PYTHONDONTWRITEBYTECODE='1')
def run(args):subprocess.run(args,cwd=ROOT,env=env,check=True)
run([sys.executable,'-B','scripts/test/check-sources.py'])
run([sys.executable,'-B','components/sagalock/tests/test_weather.py'])
run(['node','components/sagalock/tests/telemetry.test.cjs'])
run([sys.executable,'-B','components/sagaboot/tests/native_test.py'])
run(['g++','-std=c++23','-Wall','-Wextra','-Werror','components/desktop-reveal/tests/policy.cpp','-o',str(work/'policy-tests')])
run([str(work/'policy-tests')])
# The installed start-hyprland test and graphical-launch test need external runtime
# or a linked compositor. Only pure identity/command/mocked-signal cases run here.
suite='components.desktop-reveal.tests.test_session'
for name in ['test_command','test_recovery_identity','test_preferred_default','test_recovery_stops_supervisor_and_legacy_only']:
    run([sys.executable,'-B','-m','unittest',suite+'.SessionTests.'+name])
qt=Path('/usr/lib/qt6/bin/qmllint')
if qt.exists():
    run([str(qt),'components/sagasddm/saga-sddm/RuneMask.qml','components/sagasddm/saga-sddm/NorthernFrame.qml','components/sagalock/lock-designs/saga-runes-v1/RuneMask.qml','components/sagalock/lock-designs/saga-runes-v1/NorthernFrame.qml'])
else:print('SKIP Qt6 qmllint: not installed')
print('PASS isolated unit tests; no compositor, locker, service, boot image or installation launched')
