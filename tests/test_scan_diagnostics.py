import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image
from scan_diagnostics import save_diagnostics, DETECTOR_VERSION


class ScanDiagnosticsTests(unittest.TestCase):
    def test_reproduction_metadata_without_configuration_or_keys(self):
        screen = Image.new('RGB', (1280, 720))
        screen.info['cursor'] = (400, 300)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'scan.json'
            save_diagnostics(path, screen=screen, requested_mode='runes',
                             effective_mode='stash', bounds=(10, 20, 200, 300),
                             state='success', message='OK', request_id='test')
            data = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(data, dict(detector_version=DETECTOR_VERSION,
                                   resolution=[1280, 720], cursor=[400, 300],
                                   requested_mode='runes', effective_mode='stash',
                                   crop_bounds=[10, 20, 200, 300], state='success',
                                   message='OK', request_id='test'))
