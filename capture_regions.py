import config
import numpy as np
from rune_processor import detect_and_crop_rune_grid

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
    arr = np.array(screen)
    if width == 1920 and height == 1080:
        score_236 = np.abs(arr[236, 175:175+468, :3].mean(axis=1) - 58).mean()
        score_207 = np.abs(arr[207, 175:175+468, :3].mean(axis=1) - 58).mean()
        return min(score_236, score_207) < 8.0
    return False

def crop_for_ai(screen, mode):
    from capture import find_tooltip_crop
    width, height = screen.size
    mode_name = MODE_LABELS.get(mode, mode)

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
        arr = np.array(screen)
        if width == 1920 and height == 1080:
            score_236 = np.abs(arr[236, 175:175+468, :3].mean(axis=1) - 58).mean()
            score_207 = np.abs(arr[207, 175:175+468, :3].mean(axis=1) - 58).mean()
            if min(score_236, score_207) > 18.0:
                raise ValueError(
                    "Odrzucono: Nie wykryto otwartej zakładki run w grze. "
                    "Otwórz skrzynię w grze i przejdź do zakładki z runami, a następnie naciśnij skrót."
                )
        try:
            return detect_and_crop_rune_grid(screen)
        except Exception:
            defaults = [0, 0, .65, .95]
            region = config.COMPANION_SETTINGS.get('regions', {}).get('runes', defaults)
            x, y, w, h = region
            box = (int(x * width), int(y * height), int((x + w) * width), int((y + h) * height))
            return screen.crop(box), box

    # 2. STAT SCREEN (CHARACTER CREATOR / STATS) MODE
    if mode == 'stat_screen':
        defaults = [0, 0, .58, 1]
        region = config.COMPANION_SETTINGS.get('regions', {}).get('stat_screen', defaults)
        x, y, w, h = region
        box = (int(x * width), int(y * height), int((x + w) * width), int((y + h) * height))
        return screen.crop(box), box

    # 3. ITEM MODES (stash, character, merc)
    # Check if user accidentally snapped the rune tab
    if _check_rune_grid_presence(screen):
        raise ValueError(
            f"Odrzucono: Na ekranie znajduje się zakładka RUN, a masz wybrany tryb '{mode_name}'. "
            "Kliknij przycisk '💎 Runy', aby zapisać stan run."
        )

    box = find_tooltip_crop(screen)
    if not box:
        raise ValueError(
            f"Odrzucono: Nie wykryto opisu przedmiotu (ramki tooltip) dla trybu '{mode_name}'. "
            "Najedź kursorem myszy na przedmiot w grze, aby wyświetlić jego opis, a następnie naciśnij skrót."
        )

    x, y, w, h = box
    if w < 90 or h < 55 or w > width * .85 or w * h > width * height * .75:
        raise ValueError(
            "Odrzucono: Niepewny wycinek przedmiotu. "
            "Upewnij się, że kursor wskazuje przedmiot i cały opis jest widoczny na ekranie."
        )

    margin = 8
    bounds = (max(0, x - margin), max(0, y - margin), min(width, x + w + margin), min(height, y + h + margin))
    return screen.crop(bounds), bounds
