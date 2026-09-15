"""Offline regression tests. No model calls and no application database writes."""
from pathlib import Path
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw, ImageFont

from tooltip_detection import find_tooltip_crop


ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS = ROOT / 'data' / 'screenshots'
NEGATIVE_IDS = {'17eb069c', '232e2d3f', '238c64c2', 'a4cd3972',
                '3cef0c2b', '1e60a003', '41ac6e5e'}
ITEM_IDS = {'cc8ae732', '53b9b54b', 'b422d671', 'b8f41677', 'd3070412',
            '94f927a0', '6f831a29', 'd27cf75c', 'cda92622', 'f914850d',
            'd99dd069', '86bcceb0', '73853a4d', '9e642f6b', '6f8d2b63',
            '4183ffe9', '4741aca1', 'ad9283d8', 'a1393791', '01360410',
            'aa8c3d2e', 'b15897f7', '70f12ddb', 'a7c5cd31', 'b72bda79',
            '29f90ded', '9c984bb1', '0db2b926', '237190df'}


def example_tooltip(position=(600, 300), framed=True, plain=False):
    image = Image.new('RGB', (1920, 1080), (48, 39, 33))
    x, y = position
    draw = ImageDraw.Draw(image)
    draw.rectangle((x, y, x + 560, y + 270), fill=(8, 8, 8),
                   outline=(80, 80, 80) if framed else None)
    rows = [
        ('SOCKETED CRYSTAL SWORD' if plain else 'ANCIENT WARRIOR BLADE', (105, 105, 105) if plain else (199, 179, 119)),
        ('ONE HAND DAMAGE: 15 - 50', (255, 255, 255)),
        ('REQUIRED STRENGTH: 120', (255, 255, 255)),
        ('REQUIRED LEVEL: 65', (255, 255, 255)),
        ('+120 PERCENT ENHANCED DAMAGE', (255, 255, 255) if plain else (110, 110, 255)),
        ('FIRE RESISTANCE +35 PERCENT', (255, 255, 255) if plain else (255, 77, 77)),
        ('SOCKETED (4)', (255, 255, 255) if plain else (110, 110, 255)),
        ('SHIFT + CLICK TO EQUIP', (144, 144, 144)),
    ]
    font = ImageFont.load_default()
    text_bounds = []
    for i, (text, colour) in enumerate(rows):
        a, b, r, bottom = draw.textbbox((0, 0), text, font=font)
        line = Image.new('RGB', (r - a, bottom - b), (8, 8, 8))
        ImageDraw.Draw(line).text((-a, -b), text, font=font, fill=colour)
        line = line.resize((line.width * 2, line.height * 2), Image.Resampling.NEAREST)
        px, py = x + (560 - line.width) // 2, y + 12 + i * 30
        image.paste(line, (px, py))
        text_bounds.append((px, py, px + line.width, py + line.height))
    return image, text_bounds


class TooltipDetectionTests(unittest.TestCase):
    def assert_contains(self, box, content):
        self.assertIsNotNone(box)
        x, y, w, h = box
        left, top, right, bottom = content
        self.assertLessEqual(x, left)
        self.assertLessEqual(y, top)
        self.assertGreaterEqual(x + w, right)
        self.assertGreaterEqual(y + h, bottom)

    def test_edges_and_borderless_items_keep_all_properties(self):
        for position, framed in [((0, 0), True), ((1360, 810), True),
                                 ((0, 810), False), ((1360, 0), False)]:
            with self.subTest(position=position, framed=framed):
                image, rows = example_tooltip(position, framed)
                box = find_tooltip_crop(image, mode='stash')
                for row in rows[:-1]:
                    self.assert_contains(box, row)
                # PIL crop bounds are exclusive on the right and bottom.
                self.assertLessEqual(box[1] + box[3], rows[-1][1])

    def test_plain_item_keeps_grey_name(self):
        image, rows = example_tooltip(plain=True)
        box = find_tooltip_crop(image)
        for row in rows[:-1]:
            self.assert_contains(box, row)

    def test_resolutions(self):
        original, rows = example_tooltip()
        for size in [(1280, 720), (2560, 1440), (3840, 2160)]:
            with self.subTest(size=size):
                image = original.resize(size, Image.Resampling.LANCZOS)
                box = find_tooltip_crop(image)
                factor = size[0] / original.width
                for row in rows[:-1]:
                    self.assert_contains(box, tuple(round(v * factor) for v in row))

    def test_empty_images_are_not_tooltips(self):
        for colour in ['black', 'white', '#505050']:
            self.assertIsNone(find_tooltip_crop(Image.new('RGB', (640, 480), colour)))

    def test_ambiguous_comparison_does_not_choose_largest(self):
        boxes = [(0, 200, 400, 300), (900, 200, 700, 600)]
        with patch('tooltip_detection.tooltip_candidates', return_value=boxes):
            self.assertIsNone(find_tooltip_crop(None))
            self.assertEqual(find_tooltip_crop(None, cursor=(410, 350)), boxes[0])
            self.assertIsNotNone(find_tooltip_crop(None, strict=True))

    def test_two_visible_tooltips_need_unambiguous_cursor(self):
        left, _ = example_tooltip((0, 0))
        right, _ = example_tooltip((1300, 600))
        left.paste(right.crop((1300, 600, 1861, 871)), (1300, 600))
        self.assertIsNone(find_tooltip_crop(left))
        box = find_tooltip_crop(left, cursor=(560, 150))
        self.assertIsNotNone(box)
        self.assertLess(box[0] + box[2], 600)

    def test_item_crop_is_exact_and_takes_priority_over_rune_row(self):
        from capture_regions import crop_for_ai
        image, rows = example_tooltip()
        with patch('capture_regions._check_rune_grid_presence', return_value=True):
            cropped, bounds = crop_for_ai(image, 'stash')
        self.assertEqual(cropped.tobytes(), image.crop(bounds).tobytes())
        self.assertLessEqual(bounds[3], rows[-1][1])
        self.assertLess(cropped.width * cropped.height, image.width * image.height / 4)

    def test_rune_mode_rejects_item_before_calling_ai(self):
        from capture_regions import crop_for_ai
        image, _ = example_tooltip()
        with self.assertRaisesRegex(ValueError, 'opis przedmiotu'):
            crop_for_ai(image, 'runes')

    def test_failed_item_detection_never_returns_full_screen(self):
        from capture_regions import crop_for_ai
        with self.assertRaises(ValueError):
            crop_for_ai(Image.new('RGB', (1280, 720), 'black'), 'stash')

    def test_local_screenshot_corpus(self):
        paths = [p for p in SCREENSHOTS.glob('*.png') if p.stem[-8:] in ITEM_IDS | NEGATIVE_IDS]
        if not paths:
            self.skipTest('Private screenshot corpus is not checked into git')
        for path in paths:
            with self.subTest(screenshot=path.name), Image.open(path) as image:
                box = find_tooltip_crop(image, mode='stash')
                if path.stem[-8:] in NEGATIVE_IDS:
                    self.assertIsNone(box)
                else:
                    self.assertIsNotNone(box)

    def test_known_regressions_keep_full_text_and_drop_controls(self):
        # Bounds were read from the source screenshots, not from the detector.
        cases = {
            '237190df': ((16, 322, 1111, 634), 658),  # Dracul, long left-edge line
            '0db2b926': ((16, 525, 647, 972), 997),   # Griswold, red set lines
            '4741aca1': ((853, 426, 1801, 981), 1080),  # Borderless equipped Grief
        }
        for uid, (content, controls_top) in cases.items():
            matches = list(SCREENSHOTS.glob('*_' + uid + '.png'))
            if not matches:
                continue
            with self.subTest(item=uid), Image.open(matches[0]) as image:
                box = find_tooltip_crop(image)
                self.assert_contains(box, content)
                self.assertLess(box[1] + box[3], controls_top)
                self.assertLess(box[2] * box[3], image.width * image.height * .3)

    def test_local_items_at_other_resolutions(self):
        cases = {'237190df': (16, 322, 1111, 634),
                 '0db2b926': (16, 525, 647, 972),
                 '4741aca1': (853, 426, 1801, 981)}
        for uid, content in cases.items():
            paths = list(SCREENSHOTS.glob('*_' + uid + '.png'))
            if not paths:
                continue
            with Image.open(paths[0]) as original:
                for size in [(1280, 720), (2560, 1440)]:
                    with self.subTest(item=uid, size=size):
                        image = original.resize(size, Image.Resampling.LANCZOS)
                        scale = size[0] / original.width
                        self.assert_contains(find_tooltip_crop(image), tuple(round(v * scale) for v in content))


if __name__ == '__main__':
    unittest.main()
