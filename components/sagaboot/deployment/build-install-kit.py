#!/usr/bin/env python3
from pathlib import Path
import os,json,subprocess as s,struct,hashlib,shutil
os.umask(0o077)
w=Path(__file__).resolve().parent
r=json.loads((w/'readiness-readonly.json').read_text())
original=w/r['backup_local']/'EFI/Linux/omarchy_linux-omarchy.efi'
bundle=w/'install-kit';bundle.mkdir(mode=0o700,exist_ok=True)
(bundle/'payload').mkdir(mode=0o700,exist_ok=True)
def sections(p):
    b=p.read_bytes();pe=struct.unpack_from('<I',b,60)[0];n=struct.unpack_from('<H',b,pe+6)[0];opt=struct.unpack_from('<H',b,pe+20)[0]
    base=struct.unpack_from('<Q',b,pe+48)[0];out={};ranges=[];vmas={}
    for i in range(n):
        o=pe+24+opt+40*i;name=b[o:o+8].rstrip(b'\0').decode();vs,va,rs,ptr=struct.unpack_from('<IIII',b,o+8)
        assert ptr+rs<=len(b) and vs<=rs
        out[name]=b[ptr:ptr+vs];ranges.append((va,va+max(vs,rs)));vmas[name]=base+va
    for a,z in zip(sorted(ranges),sorted(ranges)[1:]):assert a[1]<=z[0]
    assert struct.unpack_from('<I',b,pe+80)[0]>=max(x[1] for x in ranges)
    return out,vmas
old,vmas=sections(original)
for variant,name in [('fixed','omarchy-sagaboot-v1.efi'),('recovery','omarchy-sagaboot-console.efi')]:
    target=bundle/'payload'/name
    # Re-add changed sections: --update-section alone retains old VirtualSize and
    # SizeOfImage with this objcopy, which would truncate the larger initramfs.
    replacements={'.initrd':w/f'{variant}.initramfs.img'}
    if variant=='recovery':replacements['.cmdline']=w/'recovery.cmdline'
    args=['objcopy']
    for sec,path in replacements.items():
        args+=['--remove-section',sec,'--add-section',f'{sec}={path}',
               '--change-section-vma',f'{sec}=0x{vmas[sec]:x}',
               '--set-section-flags',f'{sec}=contents,alloc,load,readonly,data']
    s.run(args+[str(original),str(target)],check=True)
    new,_=sections(target)
    assert old.keys()==new.keys()
    assert all(old[k]==new[k] for k in old if k not in replacements)
    assert all(new[k]==p.read_bytes() for k,p in replacements.items())
for src,name in [(w.parent.parent/'releases/SagaBoot-v1.0/staged/SagaBoot-v1.0.addon.efi','sagaboot-v1.addon.efi'),(original,'original.efi'),(w/r['backup_local']/'limine.conf','limine.conf.original')]:
    shutil.copyfile(src,bundle/'payload'/name)
origconf=(bundle/'payload/limine.conf.original').read_bytes()
newconf=origconf+b'\n# SagaBoot v1.0 additive entries; original entries and default preserved.\n/Omarchy SagaBoot v1.0\n    protocol: efi\n    path: boot():/EFI/Linux/omarchy-sagaboot-v1.efi\n\n/Omarchy Console Recovery\n    protocol: efi\n    path: boot():/EFI/Linux/omarchy-sagaboot-console.efi\n'
(bundle/'payload/limine.conf.prepared').write_bytes(newconf)
assert newconf.startswith(origconf)
(w/'final-image-checks.json').write_text(json.dumps({'source_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'fixed_only_changed_payload_section':'.initrd','console_only_changed_payload_sections':['.initrd','.cmdline'],'all_other_sections_byte_identical':True,'pe_bounds_nonoverlap_and_virtual_size':'PASS','limine_original_bytes_preserved_as_prefix':True,'default_and_windows_entries_unchanged':True,'capture_time':r['capture_time'],'metadata_has_tpm_tokens':False,'independent_backup':False},indent=2))
print('PASS: final PE images derived from actual original; unchanged section payloads match; appended Limine configuration ready.')
