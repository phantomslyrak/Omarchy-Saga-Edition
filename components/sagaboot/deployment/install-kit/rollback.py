#!/usr/bin/env python3
"""Live USB rollback: only Linux ESP; root filesystem/LUKS not needed."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess as sp,sys
def sha(b):return hashlib.sha256(b).hexdigest()
def verified(p,h):
    assert p.is_file() and not p.is_symlink(),f'Missing/unsafe file: {p.name}'
    b=p.read_bytes();assert sha(b)==h,f'Checksum mismatch: {p.name}';return b
def replace(p,b):
    assert not p.is_symlink()
    t=p.with_name('.'+p.name+'.sagaboot-rollback.tmp')
    with t.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
    verified(t,sha(b));os.replace(t,p);verified(p,sha(b))
def rollback(esp,spec,restore_original=False):
    recovery=esp/'EFI/SagaBoot-v1.0-recovery'
    saved=verified(recovery/'limine.conf.original',spec['original_limine_sha256'])
    original=verified(recovery/'original.efi',spec['original_uki_sha256'])
    menu=esp/'limine.conf';uki=esp/'EFI/Linux/omarchy_linux-omarchy.efi'
    assert menu.exists() and sha(menu.read_bytes()) in (spec['original_limine_sha256'],spec['bundle_hashes']['payload/limine.conf.prepared']), 'Limine config changed since install; manual merge required'
    need_original=not uki.exists() or sha(uki.read_bytes())!=spec['original_uki_sha256']
    assert not need_original or restore_original,'Original UKI differs/missing: inspect first, then explicitly use --restore-original if appropriate'
    for rel,name in spec['writes'].items():
        if rel=='limine.conf':continue
        target=esp/rel
        if target.exists():verified(target,spec['bundle_hashes'][name])
    # Restore a working original path and menu BEFORE removing any added image.
    if need_original:replace(uki,original)
    if sha(menu.read_bytes())!=spec['original_limine_sha256']:replace(menu,saved)
    verified(uki,spec['original_uki_sha256']);verified(menu,spec['original_limine_sha256']);os.sync()
    for rel in reversed(list(spec['writes'])):
        if rel=='limine.conf':continue
        target=esp/rel
        if target.exists():target.unlink()
    # deployment.json is the last retained recovery artifact, unlisted to avoid a self-hash cycle.
    manifest=recovery/'deployment.json'
    if manifest.exists():manifest.unlink()
    for d in [esp/'EFI/Linux/omarchy-sagaboot-v1.efi.extra.d',recovery]:
        if d.exists():d.rmdir()
    os.sync()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--esp',type=Path,required=True);p.add_argument('--apply',action='store_true',required=True);p.add_argument('--restore-original',action='store_true');a=p.parse_args()
    assert os.geteuid()==0,'Root required in Live USB'
    esp=a.esp.resolve(strict=True)
    m=json.loads(sp.check_output(['findmnt','-J','-M',str(esp),'-o','SOURCE,FSTYPE,OPTIONS'],text=True))['filesystems'][0]
    assert m['source']=='/dev/nvme0n1p3' and m['fstype']=='vfat' and 'rw' in m['options'].split(','),'Only read-write Linux ESP nvme0n1p3 allowed'
    spec=json.loads((esp/'EFI/SagaBoot-v1.0-recovery/deployment.json').read_text())
    rollback(esp,spec,a.restore_original)
    print('Original UKI/menu verified; only installed SagaBoot additions removed. No Windows/LUKS/TPM writes or reboot.')
if __name__=='__main__':
    try:main()
    except (AssertionError,OSError,ValueError,sp.CalledProcessError) as e:print('STOP:',str(e),file=sys.stderr);sys.exit(1)
