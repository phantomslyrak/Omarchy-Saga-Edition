#!/usr/bin/env python3
"""Check the exact upstream blobs and patch roundtrip in a repository-local copy."""
from pathlib import Path
import argparse, hashlib, json, subprocess, tempfile
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
blobs=json.loads((ROOT/'components/desktop-reveal/upstream-blobs.json').read_text())
base={}
for name,want in blobs.items():
    data=(a.source/name).read_bytes()
    got=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    if got!=want:p.error('wrong upstream Git blob: '+name)
    base[name]=data
parent=ROOT/'.local/tmp';parent.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='patch-',dir=parent) as tmp:
    target=Path(tmp)
    for name,data in base.items():
        f=target/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(data)
    subprocess.run(['git','init','-q',str(target)],check=True)
    patch=ROOT/'components/desktop-reveal/saga-desktop-reveal.patch'
    for args in [ ['--check'], [] ]:
        subprocess.run(['git','-C',str(target),'apply',*args,str(patch)],check=True)
    changed=[*base,'src/render/SagaRevealPolicy.hpp']
    for name in changed:
        if (target/name).read_bytes()!=(ROOT/'components/desktop-reveal/source'/name).read_bytes():
            raise SystemExit('patched source mismatch: '+name)
    for args in [['--reverse','--check'],['--reverse']]:
        subprocess.run(['git','-C',str(target),'apply',*args,str(patch)],check=True)
    for name,data in base.items():assert (target/name).read_bytes()==data,name
    assert not (target/'src/render/SagaRevealPolicy.hpp').exists()
print('PASS: exact upstream blobs, forward/reverse patch, four matching patched sources')
