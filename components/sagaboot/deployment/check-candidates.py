#!/usr/bin/env python3
from pathlib import Path
import subprocess as s, hashlib, json, os, re
os.umask(0o077)
w=Path(__file__).resolve().parent
r=w.parent.parent/'releases/SagaBoot-v1.0'
results={}
for variant in ['fixed','recovery']:
    root=w/f'{variant}-tree'
    def rp(path):
        todo=[p for p in Path(path).parts if p not in ('/','')]; done=[]; seen=0
        while todo:
            p=todo.pop(0)
            if p=='.':continue
            if p=='..':
                assert done;done.pop();continue
            q=root.joinpath(*done,p)
            if q.is_symlink():
                seen+=1;assert seen<100
                link=os.readlink(q)
                if link.startswith('/'):done=[]
                todo=[x for x in link.split('/') if x]+todo
            else:done.append(p)
        q=root.joinpath(*done);assert q.exists(),str(q);return q
    checked=set()
    def elf(p):
        q=rp(p)
        if str(q) in checked:return
        checked.add(str(q))
        if q.read_bytes()[:4]!=b'\x7fELF':return
        out=s.check_output(['readelf','-l','-d',str(q)],text=True)
        for dep in re.findall(r'Shared library: \[(.*?)\]',out):
            found=None
            for d in ['/usr/lib/','/lib/','/lib64/']:
                try:found=rp(d+dep);break
                except AssertionError:pass
            assert found,dep
            elf('/'+str(found.relative_to(root)))
        for interp in re.findall(r'Requesting program interpreter: (.*?)\]',out):elf(interp)
    for p in ['/usr/bin/cryptsetup','/usr/bin/btrfs']+(['/usr/bin/fc-match','/usr/lib/plymouth/label-freetype.so'] if variant=='fixed' else []):elf(p)
    assert (root/'hooks/encrypt').read_bytes()==Path('/usr/lib/initcpio/hooks/encrypt').read_bytes()
    assert (root/'init').read_bytes()==Path('/usr/lib/initcpio/init').read_bytes()
    modules=[str(p.relative_to(root)) for p in root.rglob('*.ko.zst')]
    builtin=Path('/usr/lib/modules/7.2.8-9-omarchy/modules.builtin').read_text().splitlines()
    drivers={}
    for name in ['nvme','nvme-core','i915','atkbd','i8042','xhci-pci','btrfs','dm-crypt','overlay']:
        if any(Path(p).name==name+'.ko.zst' for p in modules):drivers[name]='initramfs module'
        elif any(Path(p).name==name+'.ko' for p in builtin):drivers[name]='built into installed kernel'
        else:raise AssertionError(name)
    row={'elf_closure_files_checked':len(checked),'runtime_encrypt_unchanged':True,'init_unchanged':True,'hardware_drivers':drivers}
    if variant=='fixed':
        assert (root/'hooks/plymouth').read_bytes()==Path('/usr/lib/initcpio/hooks/plymouth').read_bytes()
        assert (root/'etc/fonts/fonts.conf').read_bytes()==(w/'patch/plymouth-fallback-fonts.conf').read_bytes()
        rows=[]
        env=os.environ|{'FONTCONFIG_SYSROOT':str(root),'FONTCONFIG_FILE':'/etc/fonts/fonts.conf'}
        for request in ['monospace','monospace:weight=bold','Sans','Cantarell 11']:
            out=s.check_output([str(root/'usr/lib/ld-linux-x86-64.so.2'),'--inhibit-cache','--library-path',str(root/'usr/lib'),str(root/'usr/bin/fc-match'),'-f','%{file}\n',request],env=env,text=True).strip()
            assert out.startswith('/usr/share/fonts/plymouth-fallback/'),out
            p=rp(out);assert p.is_file(),out
            rows.append({'request':request,'font':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        row['fc_match_executed_with_staged_loader_and_libraries']=rows
    else:
        for p in ['hooks/plymouth','usr/bin/plymouth','usr/bin/plymouthd','usr/share/plymouth']:assert not (root/p).exists()
        row['plymouth_and_theme_absent']=True
    results[variant]=row
addon=r/'staged/SagaBoot-v1.0.addon.efi'
assert hashlib.sha256(addon.read_bytes()).hexdigest()=='0812f2425a531264416005554b6e0169a5a4222403c09e0546e5027510bb5d66'
# Extract directly, without objcopy's implicit in-place PE rewrite.
import struct
data=addon.read_bytes(); pe=struct.unpack_from('<I',data,60)[0]
n=struct.unpack_from('<H',data,pe+6)[0]; opt=struct.unpack_from('<H',data,pe+20)[0]
for i in range(n):
    off=pe+24+opt+40*i
    if data[off:off+8].rstrip(b'\0')==b'.initrd':
        vs,_,rs,ptr=struct.unpack_from('<IIII',data,off+8)
        assert vs<=rs
        (w/'original-addon.initrd').write_bytes(data[ptr:ptr+vs])
        break
else:raise AssertionError('Missing addon initrd')
members=s.check_output(['bsdtar','-tf',str(w/'original-addon.initrd')],text=True).splitlines()
assert all(not p.startswith('/') and '..' not in Path(p).parts for p in members)
assert all(p in ['etc','etc/plymouth','usr','usr/share','usr/share/fonts','usr/share/plymouth','usr/share/plymouth/themes'] or p.startswith(('etc/plymouth/','usr/share/fonts/','usr/share/plymouth/themes/')) for p in members)
assert not any(p.startswith(('hooks/','usr/bin/','etc/fonts/')) for p in members)
results['addon']={'sha256':hashlib.sha256(addon.read_bytes()).hexdigest(),'member_count':len(members),'no_runtime_hooks_binaries_or_fontconfig_override':True}
(w/'candidate-content-checks.json').write_text(json.dumps(results,indent=2))
print('PASS: staged ELF closure, fallback font selection, hardware drivers, console independence, original addon scope.')
