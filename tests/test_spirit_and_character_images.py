import unittest
import db

class TestSpiritAndCharacterImages(unittest.TestCase):
    def test_spirit_sacred_rondache_image(self):
        img1 = db.resolve_item_image('Duch', 'Spirit', 'Święta Rødela', 'shield2', 'runeword')
        self.assertEqual(img1, '/static/images/database/armor/fs-rodela--pa2.png')

        img2 = db.resolve_item_image('Duch', 'Spirit', 'Święta Ródela', 'shield1', 'runeword')
        self.assertEqual(img2, '/static/images/database/armor/fs-rodela--pa2.png')

        img3 = db.resolve_item_image('Duch', 'Spirit', 'Święta Rodela', '', 'runeword')
        self.assertEqual(img3, '/static/images/database/armor/fs-rodela--pa2.png')

        img4 = db.resolve_item_image('Spirit', 'Spirit', 'Sacred Rondache', 'shield', 'runeword')
        self.assertEqual(img4, '/static/images/database/armor/fs-rodela--pa2.png')

    def test_shield_slot_never_returns_weapon(self):
        img = db.resolve_item_image('Duch', 'Spirit', 'Święta Rødela', 'shield2', 'runeword')
        self.assertNotIn('/weapon/', img)
        self.assertIn('/armor/', img)

    def test_spirit_monarch_is_shield(self):
        img = db.resolve_item_image('Duch', 'Spirit', 'Monarch', 'shield1', 'runeword')
        self.assertEqual(img, '/static/images/database/armor/fs-tr-jk-tna-tarcza--kit.png')

    def test_spirit_sword_is_weapon(self):
        img = db.resolve_item_image('Duch', 'Spirit', 'Kryształowy Miecz', 'weapon1', 'runeword')
        self.assertEqual(img, '/static/images/database/weapon/ms-kryszta-owy-miecz--crs.png')

    def test_kosior_equipment_shield2(self):
        eq = db.get_character_equipment('KΘSIΘR')
        shield2 = eq.get('shield2')
        self.assertIsNotNone(shield2)
        self.assertEqual(shield2.get('name'), 'Duch')
        self.assertEqual(shield2.get('image_path'), '/static/images/database/armor/fs-rodela--pa2.png')

if __name__ == '__main__':
    unittest.main()
