#!/usr/bin/env python3
"""SagaBoot additive installer. --check is read-only; --apply needs separate approval."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess as sp, sys
if not __debug__:
    raise SystemExit('STOP: Python optimization disables safety checks; use plain python3')

def sha(data): return hashlib.sha256(data).hexdigest()
def read_verified(path, expected):
    assert path.is_file() and not path.is_symlink(), f'Not a regular file: {path.name}'
    data=path.read_bytes(); assert sha(data)==expected, f'Checksum mismatch: {path.name}'
    return data
def load_bundle(bundle):
    spec=json.loads((bundle/'deployment.json').read_text())
    data={n:read_verified(bundle/n,h) for n,h in spec['bundle_hashes'].items()}
    assert data['payload/limine.conf.prepared'].startswith(data['payload/limine.conf.original'])
    return spec,data
def mount_info(path):
    return json.loads(sp.check_output(['findmnt','-J','-T',str(path),'-o','SOURCE,TARGET,FSTYPE,OPTIONS'],text=True))['filesystems'][0]
def host_preflight(esp,spec):
    m=mount_info(esp)
    assert m['target']==str(esp) and m['source']=='/dev/nvme0n1p3' and m['fstype']=='vfat', 'Unexpected Linux ESP'
    for n,h in spec['host_input_hashes'].items():read_verified(Path(n),h)
    assert sorted(str(p) for p in Path('/etc/mkinitcpio.conf.d').glob('*.conf'))==spec['mkinitcpio_dropins'], 'mkinitcpio drop-in set changed'
    assert os.uname().release=='7.2.8-9-omarchy', 'Running kernel changed'
    read_verified(esp/'EFI/limine/limine_x64.efi',spec['limine_loader_sha256'])
    for p in [esp/'loader/addons',esp/'loader/credentials',esp/'loader/extensions',
              esp/'EFI/Linux/omarchy_linux-omarchy.efi.extra.d',
              esp/'EFI/Linux/omarchy-sagaboot-console.efi.extra.d']:
        assert not p.exists(), f'Unexpected global/companion directory: {p}'
    secure=list(Path('/sys/firmware/efi/efivars').glob('SecureBoot-*'))
    assert len(secure)==1 and secure[0].read_bytes()[4:5]==b'\x00', 'Secure Boot must still be disabled'
    meta=json.loads(sp.check_output(['/usr/bin/cryptsetup','luksDump','--dump-json-metadata','/dev/nvme0n1p4'],stderr=sp.DEVNULL,text=True))
    assert len(meta.get('keyslots',{}))==1 and not meta.get('tokens'), 'LUKS enrollment changed; stop'
    assert next(iter(meta['keyslots'].values())).get('type')=='luks2', 'Unexpected keyslot type'
    del meta
    return m
def destination_preflight(esp,spec,data):
    read_verified(esp/'EFI/Linux/omarchy_linux-omarchy.efi',spec['original_uki_sha256'])
    read_verified(esp/'limine.conf',spec['original_limine_sha256'])
    for rel in spec['writes']:
        assert rel=='limine.conf' or not (esp/rel).exists(), f'Target already exists: {rel}'
        parent=(esp/rel).parent
        while parent!=esp:
            assert not parent.is_symlink(), f'Symlink parent: {parent}'
            parent=parent.parent
        assert not (esp/rel).is_symlink(), f'Symlink target: {rel}'
        assert not (esp/rel).with_name('.'+Path(rel).name+'.sagaboot-v1.tmp').exists(), 'Leftover temporary file; inspect first'
    for rel in ['EFI/SagaBoot-v1.0-recovery','EFI/Linux/omarchy-sagaboot-v1.efi.extra.d']:
        assert not (esp/rel).exists(), f'Directory already exists: {rel}'
    need=sum(len(data[n]) for n in spec['writes'].values())+64*1024*1024
    stat=os.statvfs(esp);assert stat.f_bavail*stat.f_frsize>need*2, 'Insufficient ESP free space'
def atomic_write(path,data,expected_before=None):
    if expected_before is None: assert not path.exists(), f'Target exists: {path.name}'
    else:read_verified(path,expected_before)
    tmp=path.with_name('.'+path.name+'.sagaboot-v1.tmp')
    assert not tmp.exists()
    try:
        with tmp.open('xb') as f:
            f.write(data);f.flush();os.fsync(f.fileno())
        assert sha(tmp.read_bytes())==sha(data)
        if expected_before is None:assert not path.exists()
        else:read_verified(path,expected_before)
        os.replace(tmp,path)
    finally:
        if tmp.exists():tmp.unlink()
    read_verified(path,sha(data))
def transact(esp,spec,data):
    created=[];directories=[];config_switched=False
    try:
        # Publish the boot menu only after all images and recovery files are durable.
        for rel,name in spec['writes'].items():
            if rel=='limine.conf':continue
            path=esp/rel;missing=[];p=path.parent
            while not p.exists():missing.append(p);p=p.parent
            for d in reversed(missing):d.mkdir();directories.append(d)
            # Record intent before the write, so failures after rename are reversible.
            created.append((path,sha(data[name])))
            atomic_write(path,data[name])
        os.sync()
        read_verified(esp/'EFI/Linux/omarchy_linux-omarchy.efi',spec['original_uki_sha256'])
        atomic_write(esp/'limine.conf',data['payload/limine.conf.prepared'],spec['original_limine_sha256'])
        config_switched=True
        os.sync()
        for rel,name in spec['writes'].items():read_verified(esp/rel,sha(data[name]))
        read_verified(esp/'EFI/Linux/omarchy_linux-omarchy.efi',spec['original_uki_sha256'])
    except BaseException:
        current=esp/'limine.conf'
        # Handles an error after menu rename but before atomic_write returned.
        if current.exists() and sha(current.read_bytes())==sha(data['payload/limine.conf.prepared']):
            atomic_write(current,data['payload/limine.conf.original'],sha(data['payload/limine.conf.prepared']))
            config_switched=False
        if not current.exists() or sha(current.read_bytes())!=spec['original_limine_sha256']:
            raise RuntimeError('Menu changed unexpectedly. Recovery files retained; use Live USB rollback.')
        for path,h in reversed(created):
            if path.exists():
                read_verified(path,h);path.unlink()
        for d in reversed(directories):d.rmdir()
        os.sync()
        raise
def independent_backup(path,spec,data):
    path=path.resolve(strict=True);assert path.is_dir()
    m=mount_info(path)
    assert m['fstype'] in ('ext4','btrfs','xfs'), 'Private external Linux filesystem required; no installer FAT'
    ancestry=sp.check_output(['lsblk','-s','-n','-o','NAME,TYPE',m['source'].split('[')[0]],text=True)
    assert 'nvme0n1' not in ancestry and ' disk' in ancestry, 'Backup must be on another physical disk'
    dst=path/'SagaBoot-v1.0-preinstall-20261027'
    assert not dst.exists(), 'External backup target exists; do not overwrite'
    required=['payload/original.efi','payload/limine.conf.original','payload/limine_x64.efi.original']
    size=sum(len(data[n]) for n in required)+1024*1024
    st=os.statvfs(path);assert st.f_bavail*st.f_frsize>size*2
    dst.mkdir(mode=0o700)
    hashes=[]
    for n in required:
        target=dst/Path(n).name
        with target.open('xb') as f:f.write(data[n]);f.flush();os.fsync(f.fileno())
        target.chmod(0o600);read_verified(target,sha(data[n]));hashes.append(f'{sha(data[n])}  {target.name}\n')
    (dst/'SHA256SUMS').write_text(''.join(hashes));(dst/'SHA256SUMS').chmod(0o600)
    os.sync()
    for n in required:read_verified(dst/Path(n).name,sha(data[n]))
    return dst
def verify_local_backup(bundle,spec):
    backup=Path(spec['local_backup_directory'])
    assert backup.is_dir() and not backup.is_symlink(), 'Private local backup is missing/unsafe'
    assert backup.stat().st_mode & 0o077 == 0, 'Local backup directory must be private'
    for rel,expected in {
        'EFI/Linux/omarchy_linux-omarchy.efi':spec['original_uki_sha256'],
        'limine.conf':spec['original_limine_sha256'],
        'EFI/limine/limine_x64.efi':spec['limine_loader_sha256'],
    }.items():
        path=backup/rel
        read_verified(path,expected)
        assert path.stat().st_mode & 0o077 == 0, 'Local backup files must be private'
    return backup
def confirm_no_independent_backup():
    assert sys.stdin.isatty(), 'Risk acceptance requires an interactive terminal; redirected input is not allowed'
    phrase='ПРИНИМАЮ РИСК БЕЗ ВНЕШНЕЙ КОПИИ'
    print('ВНИМАНИЕ: независимого внешнего backup нет. Локальная копия и копия на ESP находятся на том же SSD.')
    print('Повреждение ESP или SSD может лишить доступа к Linux и Windows. Откат через Live USB не гарантирован при отказе SSD.')
    print('Для тестовой установки введите точно: '+phrase)
    assert input('Подтверждение риска: ')==phrase, 'Risk not accepted; nothing written to ESP'
def main():
    os.umask(0o077)
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--check',action='store_true');g.add_argument('--apply',action='store_true')
    p.add_argument('--independent-backup',type=Path)
    p.add_argument('--windows-recovery-confirmed',action='store_true')
    a=p.parse_args();assert os.geteuid()==0,'Run from a normal terminal with sudo'
    bundle=Path(__file__).resolve().parent;esp=Path('/boot')
    spec,data=load_bundle(bundle);local_backup=verify_local_backup(bundle,spec)
    m=host_preflight(esp,spec);destination_preflight(esp,spec,data)
    if a.check:
        print('PASS: original UKI/config, hardware build inputs, LUKS metadata, Secure Boot, addon isolation, destinations and space.')
        print('Local backup verified. Without external backup, --apply requires explicit interactive risk acceptance; Windows recovery availability must be confirmed locally.')
        return
    assert a.windows_recovery_confirmed,'Confirm Windows recovery information locally; never send the key here'
    assert 'rw' in m['options'].split(','),'Linux ESP must already be mounted read-write; no automatic remount'
    backup=None
    if a.independent_backup:
        backup=independent_backup(a.independent_backup,spec,data)
    else:
        confirm_no_independent_backup()
    # Recheck package, local backup and destinations after the interactive pause,
    # immediately before the first ESP write. No previously loaded bytes are trusted alone.
    current_spec,current_data=load_bundle(bundle)
    assert current_spec==spec and current_data==data, 'Installation kit changed during confirmation'
    verify_local_backup(bundle,spec)
    host_preflight(esp,spec);destination_preflight(esp,spec,data)
    transact(esp,spec,data)
    print('Installed additive SagaBoot and console entries; original UKI/default/Windows entries preserved. No reboot performed.')
    print('Independent backup:',backup if backup else 'NONE: risk explicitly accepted in terminal')
    print('Verified local backup:',local_backup)
if __name__=='__main__':
    try:main()
    except (AssertionError,RuntimeError,OSError,sp.CalledProcessError,ValueError) as e:
        print('STOP:',str(e),file=sys.stderr);sys.exit(1)
