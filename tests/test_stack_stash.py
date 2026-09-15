import sqlite3
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from stack_stash import validate_snapshot, save_snapshot, get_snapshot, MATERIAL_CODES, GEM_CODES
from scan_validation import RejectedScan


class StackStashTests(unittest.TestCase):
    def test_invalid_scans_are_rejected(self):
        valid_gems = dict(tab='gems', complete=True, items=[{'code': c, 'count': 0} for c in GEM_CODES])
        valid_gems['items'][0]['count'] = 4
        self.assertEqual(validate_snapshot(valid_gems, 'gems')[0]['count'], 4)

        for data in [dict(valid_gems, tab='materials'), dict(valid_gems, complete=False), dict(valid_gems, items=[]),
                     dict(valid_gems, items=valid_gems['items'] * 2)]:
            with self.assertRaises(RejectedScan):
                validate_snapshot(data, 'gems')

        for count in [True, -1, 1.5, '4', None, 1000000]:
            with self.assertRaises(RejectedScan):
                broken = [dict(x) for x in valid_gems['items']]
                broken[0]['count'] = count
                validate_snapshot(dict(valid_gems, items=broken), 'gems')

    def test_snapshot_replacement_and_tab_isolation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.sqlite'
            fake_db = types.SimpleNamespace(get_db=lambda: sqlite3.connect(path))
            with patch.dict(sys.modules, db=fake_db):
                gems_items = [{'code': c, 'count': (4 if i == 0 else 0)} for i, c in enumerate(GEM_CODES)]
                mat_items = [{'code': c, 'count': (7 if i == 0 else 0)} for i, c in enumerate(MATERIAL_CODES)]

                save_snapshot('gems', gems_items)
                save_snapshot('materials', mat_items)
                self.assertEqual(get_snapshot('gems')['total'], 4)
                self.assertEqual(get_snapshot('materials')['total'], 7)

                gems_items[0]['count'] = 2
                save_snapshot('gems', gems_items)
                self.assertEqual(get_snapshot('gems')['total'], 2)
                self.assertEqual(get_snapshot('materials')['total'], 7)

                with self.assertRaises(RejectedScan):
                    broken = [dict(x) for x in gems_items]
                    broken[0]['count'] = -1
                    save_snapshot('gems', broken)
                self.assertEqual(get_snapshot('gems')['total'], 2)

                empty_gems = [{'code': c, 'count': 0} for c in GEM_CODES]
                save_snapshot('gems', empty_gems)
                self.assertEqual(get_snapshot('gems')['total'], 0)
                self.assertIsNotNone(get_snapshot('gems')['updated_at'])


if __name__ == '__main__':
    unittest.main()
