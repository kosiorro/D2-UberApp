import tempfile
import gc
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask, render_template
import db
import character_skills as skills


class CharacterSkillsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.patch = patch.object(db, 'DB_PATH', Path(self.temp.name) / 'test.sqlite')
        self.patch.start()
        db.init_db()
        self.app = Flask(__name__, template_folder=str(Path(__file__).resolve().parents[1] / 'templates'))
        skills.register(self.app)
        self.client = self.app.test_client()
        self.hero = db.create_or_update_character({'name': 'One', 'class_name': 'Amazonka'})
        db.create_or_update_character({'name': 'Two', 'class_name': 'Amazonka'})

    def tearDown(self):
        self.patch.stop()
        gc.collect()
        self.temp.cleanup()

    def save(self, points, **changes):
        payload = dict(character='One', class_slug='amazon', points=points)
        payload.update(changes)
        return self.client.post('/api/character/skills', json=payload)

    def test_saved_points_are_isolated_and_survive_scan_update(self):
        self.assertEqual(self.save({'amazon.magic-arrow': 7}).status_code, 200)
        db.create_or_update_character({'name': 'One', 'class_name': 'Amazonka', 'level': 50})
        self.assertEqual(skills.view(db.get_character('One'))['points'], {'amazon.magic-arrow': 7})
        self.assertEqual(skills.view(db.get_character('Two'))['points'], {})
        db.delete_character('One')
        with db.get_db() as con:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM character_skill_plans').fetchone()[0], 0)

    def test_validation(self):
        for points in ({'amazon.magic-arrow': -1}, {'amazon.magic-arrow': 21},
                       {'amazon.magic-arrow': True}, {'amazon.magic-arrow': 1.5},
                       {'paladin.smite': 1}, [], None):
            self.assertEqual(self.save(points).status_code, 400)
        self.assertEqual(self.save({}, class_slug='paladin').status_code, 409)
        self.assertEqual(self.save({}, character='Missing').status_code, 404)
        self.assertEqual(self.save({}).status_code, 200)

    def test_bonuses_separate_sets_and_exclude_mercenary_and_procs(self):
        catalog = skills.catalog()
        cls = next(c for c in catalog['classes'] if c['slug'] == 'paladin')
        selected = [s for s in catalog['skills'] if s['class']['slug'] == 'paladin']
        equipment = {'head': {'name':'Hat', 'stats':['+2 to All Skills']},
                     'amulet': {'name':'Amulet', 'stats':['+2 do umiejętności Paladyna']},
                     'weapon1': {'name':'Weapon', 'stats':['+3 to Blessed Hammer (Paladin Only)', '+1 to Combat Skills (Paladin Only)', '5% Chance to cast level 10 Blessed Hammer']},
                     'weapon2': {'name':'Swap', 'stats':['+1 to All Skills']},
                     'merc_head': {'name':'Merc', 'stats':['+9 to All Skills']},
                     'charms': [{'name':'Charm', 'stats':['+1 to Combat Skills (Paladin Only)']}]}
        with patch.object(db, 'get_character_equipment', return_value=equipment):
            bonuses = skills.equipment_bonuses({'name':'Test'}, cls, selected)
        self.assertEqual(bonuses['main']['paladin.blessed-hammer']['value'], 9)
        self.assertEqual(bonuses['main']['paladin.blessed-hammer']['direct'], 3)
        self.assertEqual(bonuses['swap']['paladin.blessed-hammer']['value'], 6)
        self.assertEqual(bonuses['main']['paladin.might']['value'], 4)

    def test_catalog_and_template_for_all_classes(self):
        data = skills.catalog()
        self.assertEqual(len(data['skills']), 240)
        for cls in data['classes']:
            hero = db.create_or_update_character({'name': cls['slug'], 'class_name': cls['name_pl']})
            plan = skills.view(hero)
            self.assertEqual(len(plan['skills']), 30)
            self.assertEqual(len({(s['tree']['page'], s['position']['row'], s['position']['column']) for s in plan['skills']}), 30)
            with self.app.test_request_context():
                html = render_template('uber-skills.html', skill_plan=plan, lang='pl')
            self.assertEqual(html.count('class="skill-node"'), 30)
            for skill in plan['skills']:
                self.assertTrue((skills.assets_dir() / skill['icon']).is_file())
        with self.client.get('/skill-assets/skills/amazon/magic-arrow.png') as response:
            self.assertEqual(response.status_code, 200)

    def test_html_market_export_template_and_read_only_specs(self):
        hero = db.create_or_update_character({'name': 'Pal', 'class_name': 'Paladyn'})
        plan = skills.view(hero)
        with self.app.test_request_context():
            html = render_template('uber-skills.html', skill_plan=plan, lang='pl')

        # 1. Verify JSON export button is removed
        self.assertNotIn('id="skill-market-export"', html)

        # 2. Verify HTML export to Market button & modal exist
        self.assertIn('id="skill-market-api-export"', html)
        self.assertIn('id="buildMarketModal"', html)
        self.assertIn('id="buildMarketServerUrl"', html)

        # 3. Verify character-skills.js contains read-only cleaning and styling
        js_path = Path(__file__).resolve().parents[1] / 'static' / 'character-skills.js'
        self.assertTrue(js_path.is_file())
        js_content = js_path.read_text(encoding='utf-8')
        self.assertIn('window.SKILL_EXPORT', js_content)
        self.assertIn('.skill-counter button, [data-delta]', js_content)
        self.assertIn('.skill-edit-values', js_content)
        self.assertIn('isExport', js_content)


if __name__ == '__main__':
    unittest.main()
