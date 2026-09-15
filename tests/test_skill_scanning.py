import unittest
from unittest.mock import patch

import db
import character_skills
from skill_scanning import validate_tree, save_tree
from scan_validation import RejectedScan
import test_character_skills as fixtures


class SkillScanTests(unittest.TestCase):
    setUp = fixtures.CharacterSkillsTests.setUp
    tearDown = fixtures.CharacterSkillsTests.tearDown
    save = fixtures.CharacterSkillsTests.save
    def plan(self):
        result = character_skills.view(self.hero)
        result.update(character_id=self.hero['id'], gear_mode='main')
        return result

    def raw(self, plan, page=1):
        return dict(type='skill_tree', complete=True, confidence=.99, class_slug='amazon', page=page,
                    levels={s['uid']: 0 for s in plan['skills'] if s['tree']['page'] == page})

    def test_subtracts_bonus_and_preserves_other_trees(self):
        self.save({'amazon.inner-sight': 4})
        plan = self.plan()
        plan['bonuses']['main']['amazon.magic-arrow']['value'] = 3
        raw = self.raw(plan)
        raw['levels']['amazon.magic-arrow'] = 6
        with patch.object(character_skills, 'equipment_bonuses', return_value=plan['bonuses']):
            page, split = save_tree(raw, plan)
        self.assertEqual(split['amazon.magic-arrow'], dict(displayed=6, items=3, hard=3))
        saved = self.plan()['points']
        self.assertEqual(saved['amazon.magic-arrow'], 3)
        self.assertEqual(saved['amazon.inner-sight'], 4)

    def test_incomplete_wrong_class_and_impossible_values_rejected(self):
        plan = self.plan()
        for key, value in [('complete', False), ('class_slug', 'paladin'), ('confidence', .5), ('page', True)]:
            raw = self.raw(plan)
            raw[key] = value
            with self.assertRaises(RejectedScan): validate_tree(raw, plan)
        for value in [None, True, -1, 100, 1.5]:
            raw = self.raw(plan)
            raw['levels']['amazon.magic-arrow'] = value
            with self.assertRaises(RejectedScan): validate_tree(raw, plan)
        raw = self.raw(plan)
        del raw['levels']['amazon.magic-arrow']
        with self.assertRaises(RejectedScan): validate_tree(raw, plan)
        self.assertEqual(self.plan()['points'], {})

    def test_does_not_overwrite_concurrent_manual_edit(self):
        plan = self.plan()
        self.save({'amazon.magic-arrow': 4})
        with self.assertRaises(RejectedScan): save_tree(self.raw(plan), plan)
        self.assertEqual(self.plan()['points']['amazon.magic-arrow'], 4)

    def test_swap_bonus_and_unlearned_skills(self):
        plan = self.plan()
        plan['gear_mode'] = 'swap'
        plan['bonuses']['main']['amazon.magic-arrow']['value'] = 5
        plan['bonuses']['swap']['amazon.magic-arrow']['value'] = 2
        raw = self.raw(plan)
        raw['levels']['amazon.magic-arrow'] = 6
        self.assertEqual(validate_tree(raw, plan)[1]['amazon.magic-arrow'], 4)
        raw['levels']['amazon.magic-arrow'] = 0
        self.assertEqual(validate_tree(raw, plan)[1]['amazon.magic-arrow'], 0)
        raw['levels']['amazon.magic-arrow'] = 1
        self.assertEqual(validate_tree(raw, plan)[2]['amazon.magic-arrow'], dict(displayed=1, items=1, hard=0))

    def test_mismatch_is_saved_with_exact_screen_total_and_editable_bonus(self):
        plan = self.plan()
        plan['bonuses']['main']['amazon.magic-arrow']['value'] = 9
        raw = self.raw(plan)
        raw['levels']['amazon.magic-arrow'] = 6
        save_tree(raw, plan)
        saved = self.plan()
        self.assertEqual(saved['points']['amazon.magic-arrow'], 0)
        self.assertEqual(saved['overrides']['main']['amazon.magic-arrow'], 6)
        response = self.save({'amazon.magic-arrow': 3}, overrides={'main': {'amazon.magic-arrow': 3}})
        self.assertEqual(response.status_code, 200)
        edited = self.plan()
        self.assertEqual(edited['points']['amazon.magic-arrow'] + edited['overrides']['main']['amazon.magic-arrow'], 6)
        raw = self.raw(edited)
        raw['levels']['amazon.magic-arrow'] = 35
        _, _, breakdown = validate_tree(raw, edited)
        self.assertEqual(breakdown['amazon.magic-arrow'], dict(displayed=35, items=15, hard=20))
