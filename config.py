import os
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).resolve().parent
    BUNDLE_DIR = Path(getattr(sys, '_MEIPASS', BASE_DIR)).resolve()
else:
    BASE_DIR = Path(__file__).resolve().parent
    BUNDLE_DIR = BASE_DIR

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-3.5-flash-lite')

DATA_DIR = BASE_DIR / 'data'
SCREENSHOTS_DIR = DATA_DIR / 'screenshots'
PREVIEWS_DIR = DATA_DIR / 'previews'
DB_PATH = DATA_DIR / 'stash.sqlite'

try:
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

# When running bundled exe, ensure essential data files exist in writeable DATA_DIR
if getattr(sys, 'frozen', False) and BUNDLE_DIR != BASE_DIR:
    try:
        import shutil
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        bundle_data = BUNDLE_DIR / 'data'
        if bundle_data.exists():
            for f in bundle_data.iterdir():
                target_f = DATA_DIR / f.name
                if not target_f.exists() and f.is_file():
                    shutil.copy2(f, target_f)
    except Exception:
        pass

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

KEY_MAP = {
    **{f'F{i}': 0x70 + i - 1 for i in range(1, 13)},
    **{str(i): 0x30 + i for i in range(10)},
    **{chr(c): c for c in range(ord('A'), ord('Z') + 1)},
    'INSERT': 0x2D,
    'DELETE': 0x2E,
    'HOME': 0x24,
    'END': 0x23,
    'PAGEUP': 0x21,
    'PAGEDOWN': 0x22,
    'TILDE': 0xC0,
    'PAUSE': 0x13,
    'SCROLLLOCK': 0x91,
}

def parse_hotkey(hotkey_str: str) -> tuple[int, int, str] | None:
    if not hotkey_str or not isinstance(hotkey_str, str):
        return None
    raw = hotkey_str.strip()
    if not raw or raw.lower() in ('brak', 'none', ''):
        return None
    parts = [p.strip() for p in raw.replace('-', '+').split('+') if p.strip()]
    if not parts:
        return None
    mods = MOD_NOREPEAT
    mod_names = []
    key_part = None
    for p in parts:
        pl = p.lower()
        if pl == 'alt':
            mods |= MOD_ALT
            mod_names.append('Alt')
        elif pl in ('ctrl', 'control'):
            mods |= MOD_CONTROL
            mod_names.append('Ctrl')
        elif pl == 'shift':
            mods |= MOD_SHIFT
            mod_names.append('Shift')
        else:
            if key_part is not None:
                return None
            key_part = p.upper()
    if not key_part or key_part not in KEY_MAP:
        return None
    vk = KEY_MAP[key_part]
    canonical_name = '+'.join(mod_names + [key_part])
    return mods, vk, canonical_name

HOTKEY_MODIFIERS = MOD_NOREPEAT
HOTKEY_VK = 0x79  # F10
HOTKEY_NAME = 'F10'
FLASK_PORT = 5005

from preferences import load as load_preferences
try:
    COMPANION_SETTINGS = load_preferences()
except Exception:
    COMPANION_SETTINGS = {}

GEMINI_API_KEY = COMPANION_SETTINGS.get('api_key', GEMINI_API_KEY)
GEMINI_MODEL = COMPANION_SETTINGS.get('model', GEMINI_MODEL)

raw_hotkey = COMPANION_SETTINGS.get('hotkey', 'F10')
parsed = parse_hotkey(raw_hotkey)
if parsed:
    HOTKEY_MODIFIERS, HOTKEY_VK, HOTKEY_NAME = parsed
else:
    HOTKEY_MODIFIERS, HOTKEY_VK, HOTKEY_NAME = MOD_NOREPEAT, 0x79, 'F10'

SOUND_ENABLED = COMPANION_SETTINGS.get('sound', True)
CAPTURE_AUTOSTART = COMPANION_SETTINGS.get('autostart', True)

DEFAULT_MODE_HOTKEYS = {
    'stash': 'Ctrl+F9',
    'runes': 'Ctrl+F10',
    'gems': 'Ctrl+F11',
    'materials': 'Ctrl+F12',
    'character': 'Alt+F9',
    'stat_screen': 'Alt+F10',
    'merc': 'Alt+F11',
    'skill_screen': 'Alt+F12',
    'swap': 'F8',
    'toggle_listener': '',
    'toggle_mini': ''
}
saved_mode_hotkeys = COMPANION_SETTINGS.get('mode_hotkeys', {})
MODE_HOTKEYS = {}
for m, default_k in DEFAULT_MODE_HOTKEYS.items():
    raw_val = saved_mode_hotkeys.get(m, default_k)
    parsed_m = parse_hotkey(raw_val)
    if parsed_m:
        MODE_HOTKEYS[m] = parsed_m[2]
    else:
        MODE_HOTKEYS[m] = '' if str(raw_val).strip().lower() in ('brak', 'none', '') else default_k
