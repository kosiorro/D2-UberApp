"""Trade Jargon and 500 Popular Items Catalog Integration.

Provides colloquial item names, shorthand mechanics abbreviations, roll formatting,
and export generation for Diablo 2 Resurrected trading (nazwy zwyczajowe / Traderie style).
"""
import json
import re
from pathlib import Path

import config
BASE_DIR = config.BASE_DIR
CATALOG_FILE = config.DATA_DIR / "trade_catalog_500.json"
if not CATALOG_FILE.exists() and hasattr(config, 'BUNDLE_DIR'):
    CATALOG_FILE = config.BUNDLE_DIR / "data" / "trade_catalog_500.json"

_CATALOG_DATA = []
_CATALOG_BY_CLEAN_NAME = {}
_CATALOG_BY_ID = {}

def _clean_str(s: str) -> str:
    if not s:
        return ""
    return re.sub(r"[^a-z0-9]", "", s.lower())

def _load_catalog():
    global _CATALOG_DATA, _CATALOG_BY_CLEAN_NAME, _CATALOG_BY_ID
    if _CATALOG_DATA:
        return
    if not CATALOG_FILE.exists():
        return
    try:
        with open(CATALOG_FILE, "r", encoding="utf-8") as f:
            _CATALOG_DATA = json.load(f)
        for entry in _CATALOG_DATA:
            _CATALOG_ID = entry.get("id")
            if _CATALOG_ID:
                _CATALOG_BY_ID[_CATALOG_ID] = entry
            name = entry.get("name", "")
            clean_name = _clean_str(name)
            if clean_name:
                _CATALOG_BY_CLEAN_NAME[clean_name] = entry
            no_prefix = re.sub(r"^(base|craft|rare|set|rune|magicjewel|magic)\s*:\s*", "", name, flags=re.IGNORECASE)
            clean_no_prefix = _clean_str(no_prefix)
            if clean_no_prefix:
                _CATALOG_BY_CLEAN_NAME[clean_no_prefix] = entry
    except Exception as e:
        print(f"[trade_jargon] Failed to load catalog: {e}")

_load_catalog()

COMMON_ALIASES = {
    "harlequin crest": "Shako",
    "czapka arlekina": "Shako",
    "heart of the oak": "Hoto",
    "serce debu": "Hoto",
    "serce dębu": "Hoto",
    "call to arms": "CTA",
    "wezwanie do broni": "CTA",
    "skin of the vipermagi": "Vmagi",
    "skora zmijomaga": "Vmagi",
    "skóra żmijomaga": "Vmagi",
    "arachnid mesh": "Arach",
    "siatka arachnidow": "Arach",
    "siatka arachnidów": "Arach",
    "war traveler": "War Trav",
    "podroze wojenne": "War Trav",
    "podróże wojenne": "War Trav",
    "waterwalk": "Waterwalk",
    "chodzacy po wodzie": "Waterwalk",
    "chodzący po wodzie": "Waterwalk",
    "gore rider": "Gore",
    "jezdzcy rzezi": "Gore",
    "jeźdźcy rzezi": "Gore",
    "magefist": "Magefist",
    "piesci maga": "Magefist",
    "pięści maga": "Magefist",
    "dracul's grasp": "Dracs",
    "uscisk drakuli": "Dracs",
    "uścisk drakuli": "Dracs",
    "the stone of jordan": "SOJ",
    "kamien jordana": "SOJ",
    "kamień jordana": "SOJ",
    "bul-kathos' wedding band": "BK Ring",
    "obraczka bul-kathosa": "BK Ring",
    "obrączka bul-kathosa": "BK Ring",
    "mara's kaleidoscope": "Mara",
    "kalejdoskop mary": "Mara",
    "griffon's eye": "Griffon",
    "oko gryfa": "Griffon",
    "crown of ages": "CoA",
    "korona wiekow": "CoA",
    "korona wieków": "CoA",
    "andariel's visage": "Andy",
    "oblicze andariel": "Andy",
    "vampire gaze": "Vamp Gaze",
    "spojrzenie wampira": "Vamp Gaze",
    "herald of zakarum": "HoZ",
    "herold zakarum": "HoZ",
    "homunculus": "Homu",
    "stormshield": "Stormshield",
    "tarcza burzy": "Stormshield",
    "thunderstroke": "Tstroke",
    "uderzenie gromu": "Tstroke",
    "titan's revenge": "Titans",
    "zemsta tytanow": "Titans",
    "zemsta tytanów": "Titans",
    "the oculus": "Oculus",
    "death's fathom": "Fathom",
    "glebia smierci": "Fathom",
    "głębia śmierci": "Fathom",
    "eschuta's temper": "Eschuta",
    "tomb reaver": "Tombreaver",
    "grobowy grabiezca": "Tombreaver",
    "reaper's toll": "Reaper",
    "zniwiarz": "Reaper",
    "żniwiarz": "Reaper",
    "windforce": "Windforce",
    "sila wiatru": "Windforce",
    "siła wiatru": "Windforce",
    "guillaume's face": "Gface",
    "twarz guillaume'a": "Gface",
    "tal rasha's guardianship": "Tal Armor",
    "straz tal rashy": "Tal Armor",
    "straż tal rashy": "Tal Armor",
    "tal rasha's adjudicator": "Tal Amulet",
    "tal rasha's lidless eye": "Tal Orb",
    "tal rasha's fine-spun cloth": "Tal Belt",
    "tal rasha's horadric crest": "Tal Mask",
    "hellfire torch": "Torch",
    "pochodnia piekielnego ognia": "Torch",
    "annihilus": "Anni",
    "gheed's fortune": "Gheed",
    "fortuna gheeda": "Gheed",
    "grand charm": "GC",
    "wielki talizman": "GC",
    "small charm": "SC",
    "maly talizman": "SC",
    "mały talizman": "SC",
    "large charm": "LC",
    "duzy talizman": "LC",
    "duży talizman": "LC",
    "enigma": "Enigma",
    "infinity": "Infinity",
    "nieskonczonosc": "Infinity",
    "nieskończoność": "Infinity",
    "grief": "Grief",
    "zal": "Grief",
    "żal": "Grief",
    "fortitude": "Fort",
    "hart": "Fort",
    "spirit": "Spirit",
    "duch": "Spirit",
    "insight": "Insight",
    "olsnienie": "Insight",
    "olśnienie": "Insight",
    "faith": "Faith",
    "wiara": "Faith",
    "beast": "Beast",
    "bestia": "Beast",
    "bramble": "Bramble",
    "ciernie": "Bramble",
    "chains of honor": "CoH",
    "lancuch honoru": "CoH",
    "łańcuch honoru": "CoH",
    "death": "Death",
    "smierc": "Death",
    "śmierć": "Death",
    "last wish": "Last Wish",
    "ostatnie zyczenie": "Last Wish",
    "ostatnie życzenie": "Last Wish",
    "mosaic": "Mosaic",
    "mozaika": "Mosaic",
    "phoenix": "Phoenix",
    "feniks": "Phoenix",
    "pride": "Pride",
    "duma": "Pride",
    "exile": "Exile",
    "wygnanie": "Exile",
    "flickering flame": "Flickering Flame",
    "migoczacy plomien": "Flickering Flame",
    "migoczący płomień": "Flickering Flame",
    "hustle": "Hustle",
    "cure": "Cure",
    "lekarstwo": "Cure",
    "metamorphosis": "Metamorphosis",
    "metamorfoza": "Metamorfoza",
    "obsidian": "Obsidian",
    "mist": "Mist",
    "mgla": "Mist",
    "mgła": "Mist",
    "plague": "Plague",
    "plaga": "Plague",
    "unbending will": "Unbending Will",
    "nieugieta wola": "Unbending Will",
    "nieugięta wola": "Unbending Will",
    "wisdom": "Wisdom",
    "madrosc": "Wisdom",
    "mądrość": "Wisdom",
    "lawbringer": "Lawbringer",
    "dawca prawa": "Lawbringer",
    "treachery": "Treachery",
    "zdrada": "Treachery",
    "smoke": "Smoke",
    "dym": "Smoke",
    "stealth": "Stealth",
    "skradanie sie": "Stealth",
    "skradanie się": "Stealth",
    "lore": "Lore",
    "wiedza": "Lore",
    "rhyme": "Rhyme",
    "rym": "Rhyme",
    "white": "White",
    "biel": "White",
}

BASE_ABBREVIATIONS = {
    "monarch": "Mon",
    "monarcha": "Mon",
    "sacred targe": "ST",
    "swieta tarcza": "ST",
    "święta tarcza": "ST",
    "sacred rondache": "SR",
    "swieta rondela": "SR",
    "święta rondela": "SR",
    "swieta rodela": "SR",
    "święta rodela": "SR",
    "kurast shield": "Kurast",
    "zakarum shield": "Zakarum",
    "vortex shield": "Vortex",
    "mage plate": "MP",
    "plyta maga": "MP",
    "płyta maga": "MP",
    "archon plate": "AP",
    "plyta archonta": "AP",
    "płyta archonta": "AP",
    "dusk shroud": "Dusk",
    "calun zmierzchu": "Dusk",
    "całun zmierzchu": "Dusk",
    "wyrmhide": "Wyrm",
    "skora wyrma": "Wyrm",
    "scarab husk": "Scarab",
    "wire fleece": "Wire",
    "great hauberk": "GH",
    "phase blade": "PB",
    "ostrze fazowe": "PB",
    "crystal sword": "CS",
    "krysztalowy miecz": "CS",
    "kryształowy miecz": "CS",
    "colossus blade": "CB",
    "ostrze kolosa": "CB",
    "colossus sword": "CSword",
    "miecz kolosa": "CSword",
    "berserker axe": "BA",
    "topor berserkera": "BA",
    "topór berserkera": "BA",
    "colossus voulge": "CV",
    "wulga kolosa": "CV",
    "thresher": "Thresh",
    "mlocarnia": "Thresh",
    "młocarnia": "Thresh",
    "giant thresher": "GT",
    "wielka mlocarnia": "GT",
    "wielka młocarnia": "GT",
    "cryptic axe": "CA",
    "tajemniczy topor": "CA",
    "tajemniczy topór": "CA",
    "great poleaxe": "GPA",
    "flail": "Flail",
    "korbacz": "Flail",
    "grand matron bow": "GMB",
    "matriarchal bow": "Mat Bow",
    "shako": "Shako",
    "czako": "Shako",
    "bone visage": "Bone Visage",
    "demonhead": "Demonhead",
    "tiara": "Tiara",
    "diadem": "Diadem",
    "coronet": "Coronet",
    "circlet": "Circlet",
}

def strip_diacritics(s: str) -> str:
    if not s:
        return ""
    mapping = {'ą':'a', 'ć':'c', 'ę':'e', 'ł':'l', 'ń':'n', 'ó':'o', 'ś':'s', 'ź':'z', 'ż':'z'}
    res = s.lower()
    for k, v in mapping.items():
        res = res.replace(k, v)
    return res

PROPERTY_ABBREVIATIONS = [
    (r"(?:szybsze rzucanie czarow|szybkosci rzucania czarow|szyb?k?osci rzucania czarow|faster cast rate|fcr)", "FCR", "%"),
    (r"(?:zwiekszona szybkosc ataku|szybkosci ataku|increased attack speed|ias)", "IAS", "%"),
    (r"(?:szybsze odzyskiwanie rownowagi|odzyskiwania rownowagi|faster hit recovery|fhr)", "FHR", "%"),
    (r"(?:szybsze bieganie[ /]chodzenie|poruszania sie|faster run/walk|frw)", "FRW", "%"),
    (r"(?:zwiekszone obrazenia|zwiekszonych obrazen|enhanced damage)", "ED", "%"),
    (r"(?:zwiekszona obrona|zwiekszonej obrony|enhanced defense)", "ED", "%"),
    (r"(?:skutecznosc ataku|skutecznosci ataku|attack rating)", "AR", ""),
    (r"(?:druzgocace uderzenie|druzgocacego uderzenia|crushing blow)", "CB", "%"),
    (r"(?:smiertelne uderzenie|smiertelnego uderzenia|deadly strike)", "DS", "%"),
    (r"(?:otwarte rany|otwartych ran|open wounds)", "OW", "%"),
    (r"(?:kradziez zycia|zycia za kazde trafienie|zycia wykradane|life stolen per hit|life leech)", "LL", "%"),
    (r"(?:kradziez many|many za kazde trafienie|many wykradana|mana stolen per hit|mana leech)", "ML", "%"),
    (r"(?:pochlanianie magii|pochlaniania magii|magic absorb)", "Absorb", ""),
    (r"(?:redukcja obrazen od magii|magic damage reduced|mdr)", "MDR", ""),
    (r"(?:redukcja obrazen|obrazenia zredukowane|damage reduced|\bdr\b)", "DR", "%"),
    (r"(?:wszystkie odpornosci|odpornosci na wszystkie|all resistances|all res)", "@res", ""),
    (r"(?:odpornosc na ogien|odpornosci na ogien|fire resist|fr)", "FR", "%"),
    (r"(?:odpornosc na zimno|odpornosci na zimno|cold resist|cr)", "CR", "%"),
    (r"(?:odpornosc na blyskawice|odpornosci na blyskawice|lightning resist|lr)", "LR", "%"),
    (r"(?:odpornosc na trucizne|odpornosci na trucizne|poison resist|pr)", "PR", "%"),
    (r"(?:szansa na znalezienie magicznych|magic find|mf)", "MF", "%"),
    (r"(?:wiecej zlota od potworow|extra gold|eg)", "EG", "%"),
    (r"(?:wszystkie atrybuty|all attributes|stats)", "Stats", ""),
    (r"(?:drzewko umiejetnosci|umiejetnosci|umiejetnosc|all skills|skills)", "Skills", ""),
    (r"(?:do sily|sila|strength|str)", "Str", ""),
    (r"(?:do zrecznosci|zrecznosc|dexterity|dex)", "Dex", ""),
    (r"(?:do zywotnosci|zywotnosc|vitality|vit)", "Vit", ""),
    (r"(?:do energii|energia|energy|ene)", "Ene", ""),
    (r"(?:do zycia|zycie|life)", "Life", ""),
    (r"(?:do many|mana)", "Mana", ""),
    (r"(?:obrona|defense)", "Def", ""),
]

def find_catalog_entry(item: dict) -> dict | None:
    _load_catalog()
    name_en = item.get("name_en") or ""
    name_pl = item.get("name") or ""
    base = item.get("base") or ""
    for n in (name_en, name_pl):
        c = _clean_str(n)
        if c in _CATALOG_BY_CLEAN_NAME:
            return _CATALOG_BY_CLEAN_NAME[c]
    if "spirit" in name_en.lower() or "duch" in name_pl.lower():
        clean_b = base.lower().replace("ø", "o").replace("õ", "o").replace("ó", "o")
        is_shield = any(k in clean_b for k in ["shield", "tarcza", "monarch", "rondela", "rodela", "rondache", "targe", "targi", "tarza", "tarża", "kurast", "zakarum", "aerin", "puklerz", "pelta", "egid", "aegis", "ward", "pavise", "scutum"])
        key = "spiritshield" if is_shield else "spiritsword"
        if key in _CATALOG_BY_CLEAN_NAME:
            return _CATALOG_BY_CLEAN_NAME[key]
    if "torch" in name_en.lower() or "piekielnego ognia" in name_pl.lower():
        if "hellfiretorch" in _CATALOG_BY_CLEAN_NAME:
            return _CATALOG_BY_CLEAN_NAME["hellfiretorch"]
    if "annihilus" in name_en.lower() or "annihilus" in name_pl.lower():
        if "annihilus" in _CATALOG_BY_CLEAN_NAME:
            return _CATALOG_BY_CLEAN_NAME["annihilus"]
    return None

def get_colloquial_name(item: dict, use_shorthand: bool = True) -> str:
    quality = (item.get("quality") or "").lower().strip()
    is_non_named = quality in ("normalny", "normal", "superior", "magiczny", "magic", "rzadki", "rare")
    base = item.get("base") or ""

    if is_non_named and base:
        b_clean = base.lower().strip()
        if use_shorthand:
            if b_clean in COMMON_ALIASES:
                return COMMON_ALIASES[b_clean]
            if b_clean in BASE_ABBREVIATIONS:
                return BASE_ABBREVIATIONS[b_clean]
        return item.get("display_name") or base

    if not use_shorthand:
        return item.get("name_en") or item.get("name") or "Przedmiot"
    name_en = (item.get("name_en") or "").lower().strip()
    name_pl = (item.get("name") or "").lower().strip()
    for key in (name_en, name_pl):
        if key in COMMON_ALIASES:
            return COMMON_ALIASES[key]
    entry = find_catalog_entry(item)
    if entry and entry.get("shorthand"):
        sh = entry["shorthand"].split("/")[0].strip()
        words = sh.split()
        if words:
            candidate = words[0].capitalize()
            if len(candidate) > 1:
                return candidate
    return item.get("name_en") or item.get("name") or "Przedmiot"

def abbreviate_base(base: str) -> str:
    if not base:
        return ""
    b_clean = base.lower().strip()
    return BASE_ABBREVIATIONS.get(b_clean, base)

def abbreviate_property_name(prop: str) -> tuple[str, str]:
    """Returns (abbreviation, unit) for a given property string."""
    clean = strip_diacritics(prop)
    for pattern, abbr, unit in PROPERTY_ABBREVIATIONS:
        if re.search(pattern, clean):
            return abbr, unit
    return prop, ""

def format_roll_shorthand(roll_dict: dict) -> str:
    prop = roll_dict.get("label") or roll_dict.get("property_pl") or roll_dict.get("property") or ""
    actual = roll_dict.get("actual", roll_dict.get("roll"))
    if actual is None:
        return prop
    abbr, unit = abbreviate_property_name(prop)
    if abbr == "@res":
        return f"{actual}@"
    if abbr in ("FCR", "IAS", "FHR", "FRW", "CB", "DS", "OW", "LL", "ML", "ED", "MF", "EG"):
        return f"{actual}% {abbr}" if unit == "%" and not str(actual).endswith("%") else f"{actual} {abbr}"
    if abbr in ("FR", "CR", "LR", "PR"):
        return f"{actual}% {abbr}"
    if abbr in ("Str", "Dex", "Vit", "Ene", "Life", "Mana", "Def", "AR"):
        return f"+{actual} {abbr}" if isinstance(actual, (int, float)) and actual > 0 else f"{actual} {abbr}"
    return f"{abbr}: {actual}"

def format_trade_line(
    item: dict,
    use_shorthand: bool = False,
    selected_rolls: list[str] | None = None,
    include_base: bool = True,
    include_sockets: bool = True,
    include_price: bool = True,
    include_notes: bool = True,
    lang: str = "pl"
) -> str:
    quality = (item.get("quality") or "").lower()
    is_runeword = any(k in quality for k in ("runeword", "runiczne", "slowo", "słowo"))
    if use_shorthand:
        name = get_colloquial_name(item, use_shorthand=True)
    else:
        name = (item.get("name_en") if lang == "en" else item.get("name")) or item.get("name") or "Przedmiot"
    parts = [name]
    base = item.get("base") or ""
    if include_base and base:
        if is_runeword or quality in ("normalny", "normal", "superior"):
            parts.append(abbreviate_base(base) if use_shorthand else base)
    rolls = list(item.get("rolls_eval") or [])
    formatted_rolls = []
    cname = (item.get("name_en") or item.get("name") or "").lower()
    if use_shorthand and ("call to arms" in cname or "wezwanie do broni" in cname):
        bc = next((r.get("actual") for r in rolls if "command" in (r.get("property") or "").lower()), None)
        bo = next((r.get("actual") for r in rolls if "orders" in (r.get("property") or "").lower()), None)
        bcry = next((r.get("actual") for r in rolls if "cry" in (r.get("property") or "").lower()), None)
        if bc is not None and bo is not None and bcry is not None:
            formatted_rolls.append(f"{bc}/{bo}/{bcry}")
            rolls = []
    elif use_shorthand and ("grief" in cname or "zal" in cname or "żal" in cname):
        ias = next((r.get("actual") for r in rolls if "ias" in (r.get("property") or "").lower() or "speed" in (r.get("property") or "").lower()), None)
        dmg = next((r.get("actual") for r in rolls if "damage" in (r.get("property") or "").lower()), None)
        if ias is not None and dmg is not None:
            formatted_rolls.append(f"{ias}/{dmg}")
            rolls = []
    if rolls:
        for r in rolls:
            prop_key = r.get("property") or r.get("property_pl") or r.get("label") or ""
            if selected_rolls is not None and len(selected_rolls) > 0:
                if prop_key not in selected_rolls and r.get("label") not in selected_rolls:
                    continue
            if use_shorthand:
                formatted_rolls.append(format_roll_shorthand(r))
            else:
                lbl = r.get("label") or r.get("property_pl") or r.get("property") or ""
                act = r.get("actual", r.get("roll"))
                mi = r.get("min")
                ma = r.get("max")
                range_str = f" [{mi}-{ma}]" if mi is not None and ma is not None and mi != ma else ""
                formatted_rolls.append(f"{lbl}: {act}{range_str}")
    if formatted_rolls:
        parts.append(", ".join(formatted_rolls))
    elif not rolls and item.get("stats"):
        top_stats = item.get("stats", [])[:3]
        if top_stats:
            if use_shorthand:
                sh_stats = []
                for s in top_stats:
                    abbr, unit = abbreviate_property_name(str(s))
                    nums = re.findall(r"[+-]?\d+", str(s))
                    val = nums[0] if nums else ""
                    if abbr != str(s):
                        if abbr == "@res":
                            sh_stats.append(f"{val}@")
                        elif unit == "%":
                            sh_stats.append(f"{val}% {abbr}")
                        else:
                            sh_stats.append(f"{val} {abbr}")
                    else:
                        sh_stats.append(str(s))
                parts.append(", ".join(sh_stats))
            else:
                parts.append("; ".join(str(s) for s in top_stats))
    sockets = item.get("sockets")
    if include_sockets and sockets:
        soc_str = f"{sockets}os" if use_shorthand else (f"{sockets} gniazda" if lang == "pl" else f"{sockets} sockets")
        parts.append(soc_str)
    if item.get("ethereal"):
        parts.append("eth" if use_shorthand else ("Eteryczny" if lang == "pl" else "Ethereal"))
    if include_price:
        price = item.get("trade_price") or ("Oferty" if lang == "pl" else "Offer")
        parts.append(price)
    if include_notes and item.get("trade_notes"):
        parts.append(f"({item['trade_notes']})")
    return " | ".join(parts)
