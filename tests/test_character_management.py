import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import config
import db
from db import (
    init_db, create_or_update_character, get_character, delete_character,
    touch_character, insert_item, get_item, get_character_equipment,
    update_item_full, find_character_equipped_item, get_all_items
)
from scan_history import init_history


class CharacterManagementTests(unittest.TestCase):
    def setUp(self):
        # These tests exercise persistence with mocked recognition, not API setup or image detection.
        for target, kwargs in [('api_setup.has_api_key', {'return_value': True}),
                               ('scan_diagnostics.save_diagnostics', {}),
                               ('capture_regions.resolve_scan_mode', {'side_effect': lambda screen, mode: mode})]:
            mock = patch(target, **kwargs)
            mock.start()
            self.addCleanup(mock.stop)
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.test_db_path = Path(self.temp_dir.name) / 'test_stash.sqlite'
        self.patch_config = patch.object(config, 'DB_PATH', self.test_db_path)
        self.patch_db = patch.object(db, 'DB_PATH', self.test_db_path)
        self.patch_config.start()
        self.patch_db.start()
        init_db()
        init_history()

    def tearDown(self):
        self.patch_config.stop()
        self.patch_db.stop()
        self.temp_dir.cleanup()

    def test_create_and_delete_character_unlinks_items_to_stash(self):
        char = create_or_update_character({
            "name": "TestHammer",
            "class_name": "Paladyn",
            "level": 85,
            "strength": 120
        })
        self.assertIsNotNone(char)
        self.assertEqual(char["name"], "TestHammer")

        # Equip an item on TestHammer
        item = {
            "id": "item123",
            "name": "Shako",
            "base": "Czako",
            "quality": "unikalny",
            "character_name": "TestHammer",
            "character_slot": "head",
            "location": "Postać: TestHammer"
        }
        insert_item(item)
        eq = get_character_equipment("TestHammer")
        self.assertIsNotNone(eq.get("head"))
        self.assertEqual(eq["head"]["id"], "item123")

        # Delete character
        delete_character("TestHammer")
        self.assertIsNone(get_character("TestHammer"))

        # Check that equipped item returned to stash with location = 'Skrzynia'
        stored = get_item("item123")
        self.assertEqual(stored["character_name"], "")
        self.assertEqual(stored["character_slot"], "")
        self.assertEqual(stored["location"], "Skrzynia")

    def test_touch_character_updates_timestamp(self):
        char = create_or_update_character({
            "name": "SorceressTest",
            "class_name": "Czarodziejka",
            "level": 70
        })
        initial_time = char.get("updated_at")
        touch_character("SorceressTest")
        updated = get_character("SorceressTest")
        self.assertIsNotNone(updated.get("updated_at"))

    def test_find_and_update_equipped_item(self):
        char = create_or_update_character({
            "name": "BarbTest",
            "class_name": "Barbarzyńca",
            "level": 90
        })
        item = {
            "id": "grief123",
            "name": "Grief",
            "base": "Ostrze Fazowe",
            "quality": "runiczne",
            "damage": "35-40",
            "character_name": "BarbTest",
            "character_slot": "weapon1",
            "location": "Postać: BarbTest"
        }
        insert_item(item)

        # Find equipped item by slot
        found = find_character_equipped_item("BarbTest", slot="weapon1")
        self.assertIsNotNone(found)
        self.assertEqual(found["id"], "grief123")

        # Find equipped item by name
        found_name = find_character_equipped_item("BarbTest", name="Grief")
        self.assertIsNotNone(found_name)
        self.assertEqual(found_name["id"], "grief123")

        # Update equipped item in place
        update_item_full("grief123", {
            "name": "Grief",
            "damage": "400",
            "stats": ["+400 do obrażeń"]
        })
        stored = get_item("grief123")
        self.assertEqual(stored["damage"], "400")
        self.assertIn("+400 do obrażeń", stored["stats_json"])
        self.assertEqual(stored["character_name"], "BarbTest")
        self.assertEqual(stored["character_slot"], "weapon1")

    def test_scan_pipeline_stat_screen_updates_existing_character(self):
        create_or_update_character({
            "name": "Javazon",
            "class_name": "Amazonka",
            "level": 80,
            "strength": 100
        })

        import scan_pipeline

        mock_service = MagicMock()
        mock_service.scan_mode = "stat_screen"
        mock_service.current_character = "Javazon"
        mock_service.is_swap = False
        mock_service.current_location = "Skrzynia"
        mock_service.wizard_active = True

        fake_scan_result = {
            "status": "success",
            "type": "character",
            "data": {
                "name": "Javazon",
                "class_name": "Amazonka",
                "level": 81,
                "strength": 105,
                "vitality": 200
            },
            "raw": {"test": 1}
        }

        with patch('capture.capture_screen'), \
             patch('capture_regions.crop_for_ai', return_value=(MagicMock(), (0, 0, 100, 100))), \
             patch('scan_pipeline.process_image', return_value=fake_scan_result), \
             patch('capture.play_sound'):
            scan_pipeline.run_capture(mock_service)

        updated = get_character("Javazon")
        self.assertEqual(updated["level"], 81)
        self.assertEqual(updated["strength"], 105)
        self.assertEqual(updated["vitality"], 200)
        self.assertFalse(mock_service.wizard_active)
        self.assertEqual(mock_service.current_character, "Javazon")

    def test_scan_pipeline_equipment_scan_updates_equipped_item(self):
        create_or_update_character({
            "name": "PalaGear",
            "class_name": "Paladyn",
            "level": 90
        })

        item = {
            "id": "herald1",
            "name": "Herald of Zakarum",
            "base": "Pozłacana Tarcza",
            "quality": "unikalny",
            "defense": 450,
            "character_name": "PalaGear",
            "character_slot": "shield1",
            "location": "Postać: PalaGear"
        }
        insert_item(item)

        import scan_pipeline

        mock_service = MagicMock()
        mock_service.scan_mode = "character"
        mock_service.current_character = "PalaGear"
        mock_service.is_swap = False
        mock_service.current_location = ""
        mock_service.wizard_active = False

        fake_item_scan = {
            "status": "success",
            "type": "item",
            "data": {
                "name": "Herald of Zakarum",
                "base": "Pozłacana Tarcza",
                "quality": "unikalny",
                "slot": "shield",
                "defense": 500,
                "stats": ["+200% Enhanced Defense"]
            },
            "raw": {"test": 2}
        }

        with patch('capture.capture_screen'), \
             patch('capture_regions.crop_for_ai', return_value=(MagicMock(), (0, 0, 100, 100))), \
             patch('scan_pipeline.process_image', return_value=fake_item_scan), \
             patch('capture.play_sound'):
            scan_pipeline.run_capture(mock_service)

        updated_item = get_item("herald1")
        self.assertEqual(updated_item["defense"], 500)
        self.assertEqual(updated_item["character_name"], "PalaGear")
        self.assertEqual(updated_item["character_slot"], "shield1")


    def test_save_settings_all_mode_and_action_hotkeys(self):
        import desktop_companion
        bridge = desktop_companion.Bridge()
        test_settings = {
            'hotkey': 'F10',
            'model': 'gemini-3.5-flash-lite',
            'key': '',
            'location': 'TestLoc',
            'sound': True,
            'autostart': True,
            'mode_hotkeys': {
                'stash': 'F1',
                'character': 'F2',
                'merc': 'F3',
                'runes': 'F4',
                'stat_screen': 'F5',
                'gems': 'F6',
                'materials': 'F7',
                'swap': 'F8',
                'toggle_listener': 'F9',
                'toggle_mini': 'F11'
            },
            'regions': {
                'stat_screen': [0, 0, 0.58, 1],
                'runes': [0, 0, 0.65, 0.95]
            }
        }
        res = bridge.save_settings(test_settings)
        self.assertEqual(res, {'success': True})
        self.assertEqual(config.MODE_HOTKEYS['gems'], 'F6')
        self.assertEqual(config.MODE_HOTKEYS['materials'], 'F7')
        self.assertEqual(config.MODE_HOTKEYS['swap'], 'F8')
        self.assertEqual(config.MODE_HOTKEYS['toggle_listener'], 'F9')
        self.assertEqual(config.MODE_HOTKEYS['toggle_mini'], 'F11')


    def test_scan_pipeline_stash_mode_never_hijacks_character_gear(self):
        create_or_update_character({
            "name": "StashPala",
            "class_name": "Paladyn",
            "level": 90
        })

        equipped = {
            "id": "belt1",
            "name": "Sznur Verdungo",
            "base": "Pas z pajęczej siatki",
            "quality": "unikalny",
            "character_name": "StashPala",
            "character_slot": "belt",
            "location": "Postać: StashPala"
        }
        insert_item(equipped)

        import scan_pipeline

        mock_service = MagicMock()
        mock_service.scan_mode = "stash"
        mock_service.current_character = "StashPala"
        mock_service.is_swap = False
        mock_service.current_location = "Muł Zbroje"
        mock_service.wizard_active = False

        fake_scan = {
            "status": "success",
            "type": "item",
            "data": {
                "name": "Sznur Verdungo",
                "base": "Pas z pajęczej siatki",
                "quality": "unikalny",
                "slot": "belt",
                "stats": ["+40 do żywotności", "Zmniejsza obrażenia o 15%"]
            },
            "raw": {}
        }

        with patch('capture.capture_screen'), \
             patch('capture_regions.crop_for_ai', return_value=(MagicMock(), (0, 0, 100, 100))), \
             patch('scan_pipeline.process_image', return_value=fake_scan), \
             patch('capture.play_sound'):
            scan_pipeline.run_capture(mock_service)

        # 1. Equipped item on StashPala should NOT be overwritten or touched
        orig_equipped = get_item("belt1")
        self.assertEqual(orig_equipped["character_name"], "StashPala")
        self.assertEqual(orig_equipped["character_slot"], "belt")

        # 2. A new item must be saved in stash with location = "Muł Zbroje"
        stash_items = get_all_items(location_filter="Muł Zbroje", exclude_character_gear=True)
        self.assertEqual(len(stash_items), 1)
        self.assertEqual(stash_items[0]["name"], "Sznur Verdungo")
        self.assertEqual(stash_items[0]["location"], "Muł Zbroje")
        self.assertEqual(stash_items[0]["character_name"], "")

if __name__ == '__main__':
    unittest.main()
