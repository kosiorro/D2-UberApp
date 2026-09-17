import config
import numpy as np

MODE_LABELS = {
    'stash': '📦 Skrzynia',
    'character': '♜ Postać',
    'merc': '🛡 Najemnik',
    'runes': '💎 Runy',
    'stat_screen': '📜 Statystyki',
    'normal': '📦 Skrzynia'
}

def _check_rune_grid_presence(screen):
    width, height = screen.size
    arr = np.asarray(screen.convert('RGB'))
    if width == 1920 and height == 1080:
        # A single grey row is common in equipment panels and game scenery.
        # Require repeated grid separators and textured cell contents instead.
        for top in (207, 236):
            rows = [arr[top + step * 52, 175:643, :3] for step in range(6)]
            if all(np.abs(row.mean(axis=1) - 58).mean() < 15 for row in rows):
                interior = arr[top + 2:top + 50, 177:641, :3]
                if interior.std() > 15:
                    return True
    return False

def resolve_scan_mode(screen, mode):
    """Choose a locally recognizable target without any model request."""
    from tooltip_detection import find_tooltip_crop
    if mode not in ('normal', 'stash', 'character', 'merc', 'runes', 'gems', 'materials', 'stat_screen'):
        return mode
    box = find_tooltip_crop(screen, mode='stash', cursor=screen.info.get('cursor'))
    if box:
        return mode if mode in ('stash', 'character', 'merc') else 'stash'
    # An ambiguous comparison must never become a stash-grid scan.
    if find_tooltip_crop(screen, strict=True):
        return mode
    if mode in ('normal', 'stash', 'character', 'merc') and _check_rune_grid_presence(screen):
        return 'runes'
    return mode


def crop_for_ai(screen, mode):
    from tooltip_detection import find_tooltip_crop
    width, height = screen.size
    mode_name = MODE_LABELS.get(mode, mode)
    if mode in ('gems', 'materials'):
        # Crop to the stash window area for high-resolution, uncompressed AI recognition.
        # Panel bounds at standard 1920x1080: X=90..730, Y=70..820 (includes title, tabs, and complete grid)
        if width == 1920 and height == 1080:
            box = (90, 70, 730, 820)
            return screen.crop(box), box
        elif width > 1400 and height > 800:
            scale_x = width / 1920.0
            scale_y = height / 1080.0
            box = (int(90 * scale_x), int(70 * scale_y), int(730 * scale_x), int(820 * scale_y))
            return screen.crop(box), box
        return screen.copy(), (0, 0, width, height)

    # 1. RUNES MODE
    if mode == 'runes':
        # Reject if user hovered over an item tooltip
        item_box = find_tooltip_crop(screen, strict=True)
        if item_box:
            raise ValueError(
                "Odrzucono: Wykryto opis przedmiotu (tooltip), a masz włączony tryb '💎 Runy'! "
                "Kliknij przycisk '📦 Skrzynia' lub '♜ Postać', aby dodać ten przedmiot."
            )
        # Check if rune grid is actually present
        if width == 1920 and height == 1080:
            if not _check_rune_grid_presence(screen):
                raise ValueError(
                    "Odrzucono: Nie wykryto otwartej zakładki run w grze. "
                    "Otwórz skrzynię w grze i przejdź do zakładki z runami, a następnie naciśnij skrót."
                )
        try:
            from rune_processor import detect_and_crop_rune_grid
            return detect_and_crop_rune_grid(screen)
        except Exception:
            defaults = [0, 0, .65, .95]
            region = config.COMPANION_SETTINGS.get('regions', {}).get('runes', defaults)
            x, y, w, h = region
            box = (int(x * width), int(y * height), int((x + w) * width), int((y + h) * height))
            return screen.crop(box), box

    if mode == 'skill_screen':
        # The skill panel can be on either side depending on game layout.
        return screen.copy(), (0, 0, width, height)

    # 2. STAT SCREEN (CHARACTER CREATOR / STATS) MODE
    if mode == 'stat_screen':
        defaults = [0, 0, .58, 1]
        region = config.COMPANION_SETTINGS.get('regions', {}).get('stat_screen', defaults)
        x, y, w, h = region
        box = (int(x * width), int(y * height), int((x + w) * width), int((y + h) * height))
        return screen.crop(box), box

    # 3. ITEM MODES (stash, character, merc)
    # An item can be hovered above the rune tab. Identify the item before
    # applying the grid check. Ambiguous comparisons also take priority.
    box = find_tooltip_crop(screen, mode=mode, cursor=screen.info.get('cursor'))
    if not box and not find_tooltip_crop(screen, strict=True) and _check_rune_grid_presence(screen):
        raise ValueError(
            f"Odrzucono: Wykryto układ przypominający zakładkę run, a masz wybrany tryb '{mode_name}'. "
            "Kliknij przycisk '💎 Runy', aby zapisać stan run."
        )

    if not box:
        raise ValueError(
            f"Odrzucono: Nie znaleziono jednego czytelnego opisu przedmiotu dla trybu '{mode_name}'. "
            "Pokaż cały opis, zamknij porównanie przedmiotów i ponownie naciśnij skrót."
        )

    x, y, w, h = box
    scale = max(.5, min(width / 1920, height / 1080))
    if w < 75 * scale or h < 45 * scale or w > width or h > height or w * h > width * height * .95:
        raise ValueError(
            "Odrzucono: Niepewny wycinek przedmiotu. "
            "Upewnij się, że kursor wskazuje przedmiot i cały opis jest widoczny na ekranie."
        )

    # The detector already includes a small glyph-safe margin. Adding another
    # one here would bring action hints and unrelated interface back into view.
    bounds = (x, y, x + w, y + h)
    return screen.crop(bounds), bounds
