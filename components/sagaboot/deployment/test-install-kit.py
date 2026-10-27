#!/usr/bin/env python3
"""Real temporary-file transaction tests; never calls host preflight or touches ESP."""
from pathlib import Path
import importlib.util,json,tempfile,unittest,subprocess,io
from unittest.mock import patch
w=Path(__file__).resolve().parent;k=w/'install-kit'
def module(name):
    spec=importlib.util.spec_from_file_location(name,k/f'{name}.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
install=module('install');rollback=module('rollback')
class Transactions(unittest.TestCase):
    def test_no_external_backup_requires_interactive_exact_acceptance(self):
        phrase='ПРИНИМАЮ РИСК БЕЗ ВНЕШНЕЙ КОПИИ'
        with patch.object(install.sys.stdout,'write'):
            with patch.object(install.sys.stdin,'isatty',return_value=False),patch('builtins.input') as prompt:
                with self.assertRaises(AssertionError):install.confirm_no_independent_backup()
                prompt.assert_not_called()
            with patch.object(install.sys.stdin,'isatty',return_value=True):
                for reply in ['', 'yes', 'ДА', phrase+' ']:
                    with self.subTest(reply=reply),patch('builtins.input',return_value=reply):
                        with self.assertRaises(AssertionError):install.confirm_no_independent_backup()
                with patch('builtins.input',return_value=phrase):install.confirm_no_independent_backup()
    def test_local_backup_corruption_blocks_installation(self):
        with tempfile.TemporaryDirectory() as t:
            backup=Path(t);(backup/'EFI/Linux').mkdir(parents=True);(backup/'EFI/limine').mkdir()
            values={'EFI/Linux/omarchy_linux-omarchy.efi':b'original uki','limine.conf':b'original menu','EFI/limine/limine_x64.efi':b'original loader'}
            for rel,data in values.items():
                (backup/rel).write_bytes(data);(backup/rel).chmod(0o600)
            spec={'local_backup_directory':str(backup),'original_uki_sha256':install.sha(values['EFI/Linux/omarchy_linux-omarchy.efi']),
                  'original_limine_sha256':install.sha(values['limine.conf']),'limine_loader_sha256':install.sha(values['EFI/limine/limine_x64.efi'])}
            self.assertEqual(install.verify_local_backup(k,spec),backup)
            (backup/'limine.conf').write_bytes(b'damaged')
            with self.assertRaises(AssertionError):install.verify_local_backup(k,spec)
    def fixture(self,esp):
        real=json.loads((k/'deployment.json').read_text())
        data={n:(n+' test payload\n').encode() for n in real['bundle_hashes']}
        data['payload/limine.conf.original']=b'timeout: no\ndefault_entry: 2\n/Original\n/Windows\n'
        data['payload/limine.conf.prepared']=data['payload/limine.conf.original']+b'/SagaBoot\n/Console\n'
        spec=real|{'bundle_hashes':{n:install.sha(b) for n,b in data.items()},'original_uki_sha256':install.sha(data['payload/original.efi']),'original_limine_sha256':install.sha(data['payload/limine.conf.original'])}
        # A separate rollback manifest deliberately excludes its own file/hash.
        rspec=spec|{'writes':{p:n for p,n in spec['writes'].items() if n!='rollback-manifest.json'}}
        data['rollback-manifest.json']=json.dumps(rspec).encode();spec['bundle_hashes']['rollback-manifest.json']=install.sha(data['rollback-manifest.json'])
        (esp/'EFI/Linux').mkdir(parents=True)
        (esp/'EFI/Linux/omarchy_linux-omarchy.efi').write_bytes(data['payload/original.efi'])
        (esp/'limine.conf').write_bytes(data['payload/limine.conf.original'])
        return spec,rspec,data
    def test_exact_bundle_integrity(self):
        spec,data=install.load_bundle(k)
        self.assertEqual(len(spec['writes']),8)
        self.assertEqual(install.sha(data['payload/sagaboot-v1.addon.efi']),'0812f2425a531264416005554b6e0169a5a4222403c09e0546e5027510bb5d66')
    @patch.object(install.os,'sync')
    def test_success_and_live_rollback(self,_):
        with tempfile.TemporaryDirectory() as t:
            esp=Path(t);spec,rspec,data=self.fixture(esp)
            install.transact(esp,spec,data)
            self.assertEqual((esp/'limine.conf').read_bytes(),data['payload/limine.conf.prepared'])
            self.assertEqual((esp/'EFI/Linux/omarchy_linux-omarchy.efi').read_bytes(),data['payload/original.efi'])
            rollback.rollback(esp,rspec)
            self.assertEqual((esp/'limine.conf').read_bytes(),data['payload/limine.conf.original'])
            self.assertEqual(sorted(str(p.relative_to(esp)) for p in esp.rglob('*') if p.is_file()),['EFI/Linux/omarchy_linux-omarchy.efi','limine.conf'])
    @patch.object(install.os,'sync')
    def test_failure_after_each_publication_restores_original(self,_):
        real_write=install.atomic_write
        for step in range(1,9):
            with self.subTest(step=step),tempfile.TemporaryDirectory() as t:
                esp=Path(t);spec,rspec,data=self.fixture(esp);calls=0
                def fail_after(path,content,expected_before=None):
                    nonlocal calls
                    real_write(path,content,expected_before);calls+=1
                    if calls==step:raise OSError('Simulated error after rename')
                with patch.object(install,'atomic_write',side_effect=fail_after):
                    with self.assertRaises(OSError):install.transact(esp,spec,data)
                self.assertEqual((esp/'limine.conf').read_bytes(),data['payload/limine.conf.original'])
                self.assertEqual(sorted(str(p.relative_to(esp)) for p in esp.rglob('*') if p.is_file()),['EFI/Linux/omarchy_linux-omarchy.efi','limine.conf'])
    @patch.object(install.os,'sync')
    def test_foreign_changes_refused_before_rollback_writes(self,_):
        for target in ['limine.conf','EFI/Linux/omarchy-sagaboot-v1.efi']:
            with self.subTest(target=target),tempfile.TemporaryDirectory() as t:
                esp=Path(t);spec,rspec,data=self.fixture(esp);install.transact(esp,spec,data)
                (esp/target).write_bytes(b'foreign change')
                before={str(p):p.read_bytes() for p in esp.rglob('*') if p.is_file()}
                with self.assertRaises(AssertionError):rollback.rollback(esp,rspec)
                self.assertEqual(before,{str(p):p.read_bytes() for p in esp.rglob('*') if p.is_file()})
    @patch.object(install.os,'sync')
    def test_original_restore_requires_explicit_flag(self,_):
        with tempfile.TemporaryDirectory() as t:
            esp=Path(t);spec,rspec,data=self.fixture(esp);install.transact(esp,spec,data)
            original=esp/'EFI/Linux/omarchy_linux-omarchy.efi';original.unlink()
            with self.assertRaises(AssertionError):rollback.rollback(esp,rspec)
            rollback.rollback(esp,rspec,restore_original=True)
            self.assertEqual(original.read_bytes(),data['payload/original.efi'])
    def test_temporary_write_failure_preserves_target(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/'limine.conf';path.write_bytes(b'original')
            with patch.object(install.os,'replace',side_effect=OSError('rename failed')):
                with self.assertRaises(OSError):install.atomic_write(path,b'new',install.sha(b'original'))
            self.assertEqual(path.read_bytes(),b'original')
            self.assertEqual(list(Path(t).iterdir()),[path])
    @patch.object(install.os,'sync')
    def test_real_shell_rollback_with_final_payloads(self,_):
        spec,data=install.load_bundle(k)
        with tempfile.TemporaryDirectory() as t:
            esp=Path(t);(esp/'EFI/Linux').mkdir(parents=True)
            original=esp/'EFI/Linux/omarchy_linux-omarchy.efi'
            original.write_bytes(data['payload/original.efi'])
            (esp/'limine.conf').write_bytes(data['payload/limine.conf.original'])
            install.transact(esp,spec,data)
            # Source the library in a user-owned temporary directory; never run
            # the privileged mount-validation entry point during this test.
            script=k/'rollback.sh'
            original.unlink()
            proc=subprocess.run(['bash','-c','source "$1"; rollback_files "$2"', 'test',str(script),str(esp)],capture_output=True,text=True)
            self.assertNotEqual(proc.returncode,0)
            self.assertTrue((esp/'EFI/Linux/omarchy-sagaboot-v1.efi').exists())
            subprocess.run(['bash','-c','source "$1"; rollback_files "$2" yes','test',str(script),str(esp)],check=True,capture_output=True,text=True)
            self.assertEqual(original.read_bytes(),data['payload/original.efi'])
            self.assertEqual((esp/'limine.conf').read_bytes(),data['payload/limine.conf.original'])
            self.assertEqual(sorted(str(p.relative_to(esp)) for p in esp.rglob('*') if p.is_file()),['EFI/Linux/omarchy_linux-omarchy.efi','limine.conf'])
if __name__=='__main__':unittest.main(verbosity=2)
