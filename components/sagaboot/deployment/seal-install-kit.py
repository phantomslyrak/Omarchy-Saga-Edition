#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,shutil,os
os.umask(0o077)
w=Path(__file__).resolve().parent;k=w/'install-kit';r=json.loads((w/'readiness-readonly.json').read_text());b=w/r['backup_local']
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
shutil.copyfile(b/'EFI/limine/limine_x64.efi',k/'payload/limine_x64.efi.original')
inputs=json.loads((w/'config-input-hashes.json').read_text())
for name in ['/usr/lib/modules/7.2.8-9-omarchy/vmlinuz','/usr/lib/initcpio/hooks/encrypt','/usr/lib/initcpio/hooks/plymouth','/etc/vconsole.conf']:
    inputs[name]=h(Path(name))
writes={
    'EFI/SagaBoot-v1.0-recovery/original.efi':'payload/original.efi',
    'EFI/SagaBoot-v1.0-recovery/limine.conf.original':'payload/limine.conf.original',
    'EFI/SagaBoot-v1.0-recovery/rollback.sh':'rollback.sh',
    'EFI/Linux/omarchy-sagaboot-console.efi':'payload/omarchy-sagaboot-console.efi',
    'EFI/Linux/omarchy-sagaboot-v1.efi':'payload/omarchy-sagaboot-v1.efi',
    'EFI/Linux/omarchy-sagaboot-v1.efi.extra.d/sagaboot-v1.addon.efi':'payload/sagaboot-v1.addon.efi',
    'limine.conf':'payload/limine.conf.prepared'}
manifest={'original_uki_sha256':h(k/'payload/original.efi'),'original_limine_sha256':h(k/'payload/limine.conf.original'),
          'installed_menu_sha256':h(k/'payload/limine.conf.prepared'),
          'added_images':{p:h(k/n) for p,n in writes.items() if p.startswith('EFI/Linux/')}}
(k/'rollback-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
replacements={'@ORIGINAL_UKI@':manifest['original_uki_sha256'],'@ORIGINAL_MENU@':manifest['original_limine_sha256'],
              '@INSTALLED_MENU@':manifest['installed_menu_sha256'],'@MANIFEST_HASH@':h(k/'rollback-manifest.json'),
              '@ADDED_IMAGE_HASHES@':'\n'.join(f'{digest} {path}' for path,digest in manifest['added_images'].items())}
script=(w/'rollback-template.sh').read_text()
for old,new in replacements.items():script=script.replace(old,new)
assert '@' not in script.replace('"$@"','')
(k/'rollback.sh').write_text(script)
spec={'version':'SagaBoot v1.0 additive installation 20261027','original_uki_sha256':manifest['original_uki_sha256'],
      'local_backup_directory':str(b),
      'original_limine_sha256':manifest['original_limine_sha256'],'limine_loader_sha256':h(k/'payload/limine_x64.efi.original'),
      'host_input_hashes':inputs,'mkinitcpio_dropins':sorted(str(p) for p in Path('/etc/mkinitcpio.conf.d').glob('*.conf')),
      'bundle_hashes':{str(p.relative_to(k)):h(p) for p in sorted(k.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name not in ['deployment.json','SHA256SUMS','INSTALL.md']},
      'writes':{'EFI/SagaBoot-v1.0-recovery/deployment.json':'rollback-manifest.json',**writes}}
(k/'deployment.json').write_text(json.dumps(spec,indent=2)+'\n')
for p in k.rglob('*'):
    if p.is_file():p.chmod(0o600)
print('Sealed bundle; eight exact ESP writes; shell rollback requires no Python in Live USB.')
