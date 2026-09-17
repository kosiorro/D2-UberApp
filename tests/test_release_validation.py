import json
from pathlib import Path
import tempfile
import unittest
from release_validation import validate_package


class ReleaseValidationTests(unittest.TestCase):
    def test_private_files_block_build(self):
        for name in ('data/stash.sqlite', '_internal/data/stash.sqlite-wal',
                     'data/previews/old.png', 'data/screenshots/old.json', '.env'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b'private')
                with self.assertRaises(ValueError):
                    validate_package(root)

    def test_personal_settings_block_build(self):
        for key in ('api_key', 'api_key_protected', 'character', 'location'):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root/'companion-settings.json').write_text(json.dumps({key:'private'}))
                with self.assertRaises(ValueError):
                    validate_package(root)

    def test_default_configuration_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'companion-settings.json').write_text(json.dumps({'mode':'stash', 'api_key':''}))
            validate_package(root)
