import hashlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import zipfile
import json
import os
import subprocess
import app_updater as updater


class UpdaterTests(unittest.TestCase):
    def release(self, version='9.0.0'):
        return dict(tag_name='v'+version, draft=False, prerelease=False, assets=[dict(
            name=updater.ASSET, browser_download_url=f'https://github.com/{updater.REPO}/releases/download/v{version}/{updater.ASSET}',
            size=123, digest='sha256:'+'a'*64)])

    def test_version_order_and_skip_old_or_prerelease(self):
        self.assertGreater(updater.version_tuple('v1.10.0'), updater.version_tuple('1.9.9'))
        self.assertIsNone(updater.select_release(self.release('1.0.0')))
        self.assertIsNone(updater.select_release(dict(self.release(), prerelease=True)))
        self.assertEqual(updater.select_release(self.release())['version'], '9.0.0')

    def test_reject_untrusted_url_or_missing_digest(self):
        for field, value in [('browser_download_url', 'https://example.com/app.zip'), ('digest', None), ('size', -1)]:
            release = self.release()
            release['assets'][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                updater.select_release(release)

    def archive(self, folder, extra=None):
        path = folder / 'app.zip'
        with zipfile.ZipFile(path, 'w') as package:
            package.writestr('D2UberApp/D2UberApp.exe', b'app')
            package.writestr('D2UberApp/_internal/python311.dll', b'runtime')
            for name, value in (extra or {}).items():
                package.writestr(name, value)
        return path

    def test_never_stages_user_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = self.archive(root, {'D2UberApp/data/stash.sqlite':'private',
                                         'D2UberApp/data/companion-settings.json':'secret',
                                         'D2UberApp/data/catalog.sqlite':'catalog'})
            entries = updater.extract_package(archive, root / 'package')
            self.assertFalse((root / 'package/data/stash.sqlite').exists())
            self.assertFalse((root / 'package/data/companion-settings.json').exists())
            self.assertIn(str(Path('data/catalog.sqlite')), entries)

    def test_archive_traversal_rejected_before_any_extraction(self):
        for name in ('D2UberApp/../escape.txt', '/D2UberApp/absolute', 'D2UberApp/C:/bad',
                     'D2UberApp\\bad', 'D2UberApp/.env', 'D2UberApp/static/foo. '):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                archive = self.archive(root, {name:'bad'})
                with self.assertRaises(ValueError):
                    updater.extract_package(archive, root / 'package')
                self.assertFalse((root / 'package/D2UberApp.exe').exists())

    def test_corrupt_download_is_not_extracted(self):
        with tempfile.TemporaryDirectory() as tmp:
            release = dict(url='https://github.com/test', size=3, sha256=hashlib.sha256(b'yes').hexdigest())
            with patch('urllib.request.urlopen', return_value=io.BytesIO(b'bad')), \
                    patch.object(updater, 'extract_package') as extract:
                with self.assertRaisesRegex(ValueError, 'checksum'):
                    updater.download_package(release, Path(tmp))
                extract.assert_not_called()

    def test_network_error_does_not_escape_background_check(self):
        with patch('urllib.request.urlopen', side_effect=OSError('offline')), patch.dict(updater._state):
            updater._check()
            self.assertEqual(updater.snapshot()['status'], 'check_error')

    @unittest.skipUnless(os.name == 'nt', 'Windows update helper')
    def test_windows_apply_and_rollback_preserve_user_data(self):
        for fail in (False, True):
            with self.subTest(rollback=fail), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                target, package = root/'installed', root/'package'
                target.mkdir(); package.mkdir()
                (target/'D2UberApp.exe').write_text('old')
                (target/'data').mkdir()
                (target/'data/stash.sqlite').write_text('user data')
                (target/'.env').write_text('user key')
                (package/'D2UberApp.exe').write_text('new')
                plan = dict(pid=2147483647, target=str(target), package=str(package),
                            backup=str(root/'backup'), result=str(root/'result.txt'),
                            entries=['D2UberApp.exe'] + (['missing.txt'] if fail else []))
                (root/'plan.json').write_text(json.dumps(plan))
                (root/'apply.ps1').write_text(updater.HELPER, encoding='utf-8-sig')
                # Replace only process launch in the harness; production file operations run unchanged.
                (root/'test.ps1').write_text('function Start-Process { param($FilePath, $WorkingDirectory, $WindowStyle) }\n& "$PSScriptRoot/apply.ps1" -Plan "$PSScriptRoot/plan.json"', encoding='utf-8-sig')
                result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                                         '-File', str(root/'test.ps1')], capture_output=True, text=True, timeout=20)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual((target/'D2UberApp.exe').read_text(), 'old' if fail else 'new')
                self.assertEqual((target/'data/stash.sqlite').read_text(), 'user data')
                self.assertEqual((target/'.env').read_text(), 'user key')


if __name__ == '__main__':
    unittest.main()
