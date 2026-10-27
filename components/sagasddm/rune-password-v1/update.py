import datetime,hashlib,json,os,pathlib,shutil,stat,subprocess,sys,tempfile
P=pathlib.Path
base=P(__file__).resolve().parent
root=P('/usr/share/sddm/themes/saga-sddm')
state=P('/var/lib/saga-sddm/rune-password-v1')
names=('Main.qml','RuneMask.qml')
if os.geteuid()!=0:raise SystemExit('Run with sudo from your host terminal.')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def safe(p):
    for q in (p,*p.parents):
        if q.exists() or q.is_symlink():
            st=q.lstat()
            if q.is_symlink() or st.st_uid!=0 or st.st_mode&0o022:raise SystemExit('Unsafe system path: '+str(q))
def write(p,data,mode=0o644):
    fd,tmp=tempfile.mkstemp(prefix='.saga-runes-',dir=p.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(data)
        os.chmod(tmp,mode);os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
for p in (root,state):safe(p)
if sys.argv[1:] == ['apply']:
    expected=json.loads((base/'original-theme-sha256.json').read_text())
    for path,sha in expected.items():
        safe(P(path))
        if digest(P(path))!=sha:raise SystemExit('Installed theme changed since backup: '+path)
    if (root/'RuneMask.qml').exists():raise SystemExit('RuneMask.qml already installed; refusing overwrite.')
    candidate=base.parent/'saga-sddm'
    approved=json.loads((base/'update-sha256.json').read_text())
    for name in names:
        if digest(candidate/name)!=approved[name]:raise SystemExit('Update changed since verification: '+name)
    if (state/'active-backup').exists():raise SystemExit('An update already exists; restore it before reapplying.')
    stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup=state/stamp;backup.mkdir(parents=True,mode=0o700);os.chmod(state,0o700)
    shutil.copytree(root,backup/'theme')
    manifest={'installed':approved,'original':expected}
    (backup/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    previous=(root/'Main.qml').read_bytes()
    try:
        # Install the component before Main.qml starts referencing it.
        for name in ('RuneMask.qml','Main.qml'):
            write(root/name,(candidate/name).read_bytes())
            subprocess.run(['runuser','-u','sddm','--','test','-r',str(root/name)],check=True)
            assert (root/name).stat().st_uid==0 and stat.S_IMODE((root/name).stat().st_mode)==0o644
        for path,sha in expected.items():
            if P(path)!=root/'Main.qml':assert digest(P(path))==sha,path
        write(state/'active-backup',(str(backup)+'\n').encode(),0o600)
    except BaseException:
        write(root/'Main.qml',previous)
        if (root/'RuneMask.qml').exists():(root/'RuneMask.qml').unlink()
        raise
    print('Updated only Main.qml and RuneMask.qml. No restart. Backup: '+str(backup))
elif sys.argv[1:] in (['rollback'],['check-rollback']):
    backup=P((state/'active-backup').read_text().strip())
    if backup.parent!=state:raise SystemExit('Invalid backup path')
    safe(backup)
    manifest=json.loads((backup/'manifest.json').read_text())
    for name,sha in manifest['installed'].items():
        safe(root/name)
        if digest(root/name)!=sha:raise SystemExit('Updated file changed; refusing rollback: '+name)
    original=backup/'theme/Main.qml'
    if digest(original)!=manifest['original'][str(root/'Main.qml')]:raise SystemExit('Backup checksum failed')
    if sys.argv[1]=='check-rollback':
        print('Rollback checks passed; no changes made.');raise SystemExit(0)
    write(root/'Main.qml',original.read_bytes())
    (root/'RuneMask.qml').unlink()
    for path,sha in manifest['original'].items():assert digest(P(path))==sha,path
    (state/'active-backup').unlink()
    print('Previous working theme restored. No restart.')
else:raise SystemExit('Usage: update.py apply|rollback|check-rollback')
