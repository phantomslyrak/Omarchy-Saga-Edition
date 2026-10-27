#!/usr/bin/env python3
"""Assemble outside ESP only. Candidates require comparison with original UKI."""
from pathlib import Path
import os, struct, subprocess as sp, hashlib, json
os.umask(0o077)
w = Path(__file__).resolve().parent
stub = Path('/usr/lib/systemd/boot/efi/linuxx64.efi.stub')
kernel = Path('/usr/lib/modules/7.2.8-9-omarchy/vmlinuz')
def sections(path):
    b = path.read_bytes(); pe = struct.unpack_from('<I', b, 60)[0]
    assert b[pe:pe+4] == b'PE\0\0'
    n = struct.unpack_from('<H', b, pe+6)[0]
    opt = struct.unpack_from('<H', b, pe+20)[0]
    base = struct.unpack_from('<Q', b, pe+48)[0]
    rows = []
    for i in range(n):
        off = pe+24+opt+i*40
        name = b[off:off+8].rstrip(b'\0').decode()
        vs, va, rs, ptr = struct.unpack_from('<IIII', b, off+8)
        rows.append((name, vs, va, rs, ptr))
    return b, base, rows
results = {}
for variant in ('fixed','recovery'):
    target = w / ('sagaboot-fixed-candidate.efi' if variant == 'fixed' else 'sagaboot-console-candidate.efi')
    assert not target.exists(), 'Refuse overwrite'
    _, base, old = sections(stub)
    addr = (max(va+max(vs,rs) for _,vs,va,rs,_ in old)+4095)&~4095
    payloads = {'.osrel':Path('/etc/os-release'), '.uname':w/'kernel-version',
                '.cmdline':w/f'{variant}.cmdline', '.linux':kernel,
                '.initrd':w/f'{variant}.initramfs.img'}
    (w/'kernel-version').write_text('7.2.8-9-omarchy\n')
    args=['objcopy']
    for name, path in payloads.items():
        args += ['--add-section',f'{name}={path}','--change-section-vma',f'{name}=0x{base+addr:x}',
                 '--set-section-flags',f'{name}=contents,alloc,load,readonly,data']
        addr = (addr+path.stat().st_size+4095)&~4095
    sp.run(args+[str(stub),str(target)],check=True)
    data,_,rows = sections(target)
    for name,path in payloads.items():
        _,vs,_,rs,ptr = next(r for r in rows if r[0]==name)
        assert vs <= rs and data[ptr:ptr+vs] == path.read_bytes()
    results[variant]={'file':target.name,'sha256':hashlib.sha256(data).hexdigest(),
                      'sections':[dict(zip(('name','virtual_size','rva','raw_size','raw_offset'),r)) for r in rows],
                      'status':'CANDIDATE: original UKI/TPM comparison pending; hardware boot not tested'}
(w/'candidate-pe-checks.json').write_text(json.dumps(results,indent=2))
print('Two candidate UKIs assembled outside ESP; PE payloads verified byte for byte.')
