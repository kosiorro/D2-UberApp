import sqlite3
import json
import re
import unicodedata
import difflib
from pathlib import Path
from item_names import clean_item_name

import config
CATALOG_PATH = config.DATA_DIR / "catalog.sqlite"
BASES_PATH = config.DATA_DIR / "item_bases.json"

RUNE_REQ_LEVELS = {
    "r01": 11, "r02": 11, "r03": 13, "r04": 13, "r05": 15,
    "r06": 15, "r07": 17, "r08": 19, "r09": 21, "r10": 23,
    "r11": 25, "r12": 27, "r13": 29, "r14": 31, "r15": 0,
    "r16": 35, "r17": 37, "r18": 39, "r19": 41, "r20": 43,
    "r21": 45, "r22": 47, "r23": 49, "r24": 51, "r25": 53,
    "r26": 55, "r27": 57, "r28": 59, "r29": 61, "r30": 63,
    "r31": 65, "r32": 67, "r33": 69
}

IGNORED_PROPERTIES = {
    "charged", "hit-skill", "gethit-skill", "att-skill",
    "dmg-norm", "dmg-ltng", "dmg-fire", "dmg-cold", "dmg-pois",
    "pois-min", "pois-max", "pois-len", "rep-quant", "light",
    "stupidity", "freeze"
}

PROP_NAMES_PL = {
    "dmg%": "Zwiększone Obrażenia (ED)",
    "dmg": "Dodatkowe Obrażenia",
    "res-all": "Wszystkie Odporności",
    "all-stats": "Wszystkie Atrybuty",
    "randclassskill": "Klasa Postaci (+3 do Umiejętności)",
    "res-fire": "Odporność na Ogień",
    "res-ltng": "Odporność na Błyskawice",
    "res-cold": "Odporność na Zimno",
    "res-pois": "Odporność na Trucizny",
    "ac%": "Zwiększona Obrona (ED)",
    "ac": "Obrona",
    "lifesteal": "Wyssanie Życia (LL)",
    "manasteal": "Wyssanie Many (ML)",
    "mag%": "Lepsza Szansa na MF",
    "gold%": "Więcej Złota",
    "cheap": "Niższe Ceny u Kupców",
    "cast2": "Szybsze Rzucanie Czarów (FCR)",
    "cast3": "Szybsze Rzucanie Czarów (FCR)",
    "swing2": "Szybkość Ataku (IAS)",
    "swing3": "Szybkość Ataku (IAS)",
    "balance2": "Szybsze Odzyskiwanie Równowagi (FHR)",
    "balance3": "Szybsze Odzyskiwanie Równowagi (FHR)",
    "red-mag": "Redukcja Obrażeń od Magii",
    "red-dmg%": "Redukcja Obrażeń Fizycznych (%)",
    "extra-ltng": "Obrażenia od Błyskawic (%)",
    "pierce-ltng": "Obniżenie Odp. na Błyskawice (%)",
    "extra-cold": "Obrażenia od Zimna (%)",
    "pierce-cold": "Obniżenie Odp. na Zimno (%)",
    "pierce-pois": "Obniżenie Odp. na Trucizny (%)",
    "str": "Siła",
    "dex": "Zręczność",
    "vit": "Żywotność",
    "enr": "Energia",
    "allskills": "Wszystkie Umiejętności",
    "skilltab": "Drzewko Umiejętności",
    "move2": "Szybkość Biegania/Chodzenia (FRW)",
    "block": "Szansa na Blok",
    "hp": "Życie",
    "mana": "Mana",
    "abs-mag": "Absorpcja Magii",
    "abs-fire": "Absorpcja Ognia",
    "abs-ltng": "Absorpcja Błyskawic",
    "addxp": "Więcej Doświadczenia (%)",
    "sock": "Liczba Gniazd",
    "oskill": "Umiejętność (Oskill)",
}

PROP_NAMES_EN = {
    "dmg%": "Enhanced Damage (ED)",
    "dmg": "Added Damage",
    "res-all": "All Resistances",
    "all-stats": "All Attributes",
    "randclassskill": "Character Class (+3 Skills)",
    "res-fire": "Fire Resistance",
    "res-ltng": "Lightning Resistance",
    "res-cold": "Cold Resistance",
    "res-pois": "Poison Resistance",
    "ac%": "Enhanced Defense (ED)",
    "ac": "Defense",
    "lifesteal": "Life Stolen per Hit (LL)",
    "manasteal": "Mana Stolen per Hit (ML)",
    "mag%": "Magic Find (MF)",
    "gold%": "Extra Gold from Monsters",
    "cheap": "Reduces Vendor Prices",
    "cast2": "Faster Cast Rate (FCR)",
    "cast3": "Faster Cast Rate (FCR)",
    "swing2": "Increased Attack Speed (IAS)",
    "swing3": "Increased Attack Speed (IAS)",
    "balance2": "Faster Hit Recovery (FHR)",
    "balance3": "Faster Hit Recovery (FHR)",
    "red-mag": "Magic Damage Reduced",
    "red-dmg%": "Damage Reduced by (%)",
    "extra-ltng": "Lightning Skill Damage (%)",
    "pierce-ltng": "Enemy Lightning Resistance (%)",
    "extra-cold": "Cold Skill Damage (%)",
    "pierce-cold": "Enemy Cold Resistance (%)",
    "pierce-pois": "Enemy Poison Resistance (%)",
    "str": "Strength",
    "dex": "Dexterity",
    "vit": "Vitality",
    "enr": "Energy",
    "allskills": "All Skills",
    "skilltab": "Skill Tree",
    "move2": "Faster Run/Walk (FRW)",
    "block": "Chance to Block",
    "hp": "Life",
    "mana": "Mana",
    "abs-mag": "Magic Absorb",
    "abs-fire": "Fire Absorb",
    "abs-ltng": "Lightning Absorb",
    "addxp": "Extra Experience (%)",
    "sock": "Sockets",
    "oskill": "Skill (Oskill)",
}

CLASS_NAMES_PL = {
    "paladyn": "Paladyn", "paladyna": "Paladyn", "paladin": "Paladyn",
    "czarodziejk": "Czarodziejka", "czarodziejki": "Czarodziejka", "sorceress": "Czarodziejka",
    "barbarzyc": "Barbarzyńca", "barbarzycy": "Barbarzyńca", "barbarian": "Barbarzyńca",
    "amazonk": "Amazonka", "amazonki": "Amazonka", "amazon": "Amazonka",
    "zabjczyn": "Zabójczyni", "zabójczyn": "Zabójczyni", "assassin": "Zabójczyni",
    "nekromant": "Nekromanta", "nekromanty": "Nekromanta", "necromancer": "Nekromanta",
    "druid": "Druid", "druida": "Druid"
}

def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\[.*?\]', '', text)
    text = text.replace('\ufffd', '')
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    # Zachowujemy litery, cyfry oraz znaki +, -, % kluczowe dla statystyk
    text = re.sub(r'[^a-zA-Z0-9+\-%/.\s]', ' ', text)
    return " ".join(text.lower().split())

def clean_prop_name(prop: str, param: str = "") -> str:
    if prop == "oskill" and param:
        return f"{param} (Oskill)"
    return PROP_NAMES_PL.get(prop, prop)

def clean_prop_name_en(prop: str, param: str = "") -> str:
    if prop == "oskill" and param:
        return f"{param} (Oskill)"
    return PROP_NAMES_EN.get(prop, clean_prop_name(prop, param))

ITEM_ALIASES = {
    # Polish OCR misreads & abbreviations
    "olsinienie": "olśnienie",
    "olsnienie": "olśnienie",
    "insight": "olśnienie",
    "czako": "czapka arlekina",
    "shako": "harlequin crest",
    "hoto": "serce dębu",
    "serce debu": "serce dębu",
    "cta": "wezwanie do broni",
    "call to arms": "wezwanie do broni",
    "wezwanie": "wezwanie do broni",
    "soj": "kamień jordana",
    "kamien jordana": "kamień jordana",
    "stone of jordan": "kamień jordana",
    "mara": "kalejdoskop mary",
    "kalejdoskop": "kalejdoskop mary",
    "griffon": "oko gryfa",
    "griffons eye": "oko gryfa",
    "oko gryfa": "oko gryfa",
    "arach": "siatka arachnidów",
    "arachnid": "siatka arachnidów",
    "siatka arachnidow": "siatka arachnidów",
    "eni": "enigma",
    "enigma": "enigma",
    "forti": "hart",
    "fortitude": "hart",
    "hart": "hart",
    "infa": "nieskończoność",
    "infinity": "nieskończoność",
    "nieskonczonosc": "nieskończoność",
    "grief": "żal",
    "zal": "żal",
    "anni": "annihilus",
    "annihilus": "annihilus",
    "torch": "pochodnia piekielnego ognia",
    "pochodnia": "pochodnia piekielnego ognia",
    "jmod": "jeweler's monarch of deflection",
    "coa": "korona wieków",
    "crown of ages": "korona wieków",
    "korona wiekow": "korona wieków",
    "dweb": "pajęczyna śmierci",
    "deaths web": "pajęczyna śmierci",
    "pajeczyna smierci": "pajęczyna śmierci",
    "dfathom": "głębia śmierci",
    "deaths fathom": "głębia śmierci",
    "glebia smierci": "głębia śmierci",
    "andy": "oblicze andariel",
    "andariels visage": "oblicze andariel",
    "oblicze andariel": "oblicze andariel",
    "zaka": "herald zakarum",
    "herald of zakarum": "herald zakarum",
    "herald zakarum": "herald zakarum",
    "gheed": "talizman gheeda",
    "gheeda": "talizman gheeda",
    "tal rasha": "tal rasha",
}

class CatalogMatcher:
    def __init__(self, db_path=CATALOG_PATH):
        self.db_path = Path(db_path)
        self._cache_loaded = False
        self._items_cache = []
        self._runewords_cache = []
        self._item_bases = {}
        self._load_cache()

    def _get_con(self):
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con

    def _load_cache(self):
        if not self.db_path.exists():
            return
        try:
            if BASES_PATH.exists():
                with open(BASES_PATH, "r", encoding="utf-8") as f:
                    self._item_bases = json.load(f)

            with self._get_con() as con:
                items = con.execute("""
                    SELECT id, name, name_en, quality, category, base_code, level_req, req_str, req_dex,
                           image, market_value, stat_priority, build_notes, subcategory
                    FROM items
                """).fetchall()
                self._items_cache = [dict(r) for r in items]
                for it in self._items_cache:
                    it["name"] = clean_item_name(it["name"])
                    it["norm_pl"] = normalize_text(it["name"])
                    it["norm_en"] = normalize_text(it["name_en"])
                    b_code = it.get("base_code")
                    base_info = self._item_bases.get(b_code, {})
                    slot = base_info.get("slot")
                    if not slot:
                        n_lower = it["name_en"].lower()
                        if any(c in n_lower for c in ["torch", "annihilus", "gheed", "charm"]):
                            slot = "charm"
                        elif it.get("category") == "armor":
                            slot = "armor"
                        elif it.get("category") == "weapons":
                            slot = "weapon"
                        else:
                            slot = "misc"
                    it["slot"] = slot

                # Załaduj wartościowe przedmioty magiczne (charms, jewels, circlets itp.)
                try:
                    magics = con.execute("""
                        SELECT id, name, name_en, 'magiczny' as quality, category, subcategory,
                               market_value, stat_priority, build_notes, image
                        FROM valuable_magic_items
                    """).fetchall()
                    for m in magics:
                        md = dict(m)
                        md["name"] = clean_item_name(md["name"])
                        md["norm_pl"] = normalize_text(md["name"])
                        md["norm_en"] = normalize_text(md["name_en"])
                        md["level_req"] = None
                        md["req_str"] = None
                        md["req_dex"] = None
                        cat_l = (md.get("category") or "").lower()
                        md["slot"] = "charm" if "charm" in cat_l else ("ring" if "ring" in cat_l else ("amulet" if "amulet" in cat_l else "misc"))
                        self._items_cache.append(md)
                except Exception:
                    pass

                rws = con.execute("""
                    SELECT id, name, name_en, runes_json, include_types_json,
                           market_value, stat_priority, build_notes
                    FROM runewords WHERE complete = 1
                """).fetchall()
                self._runewords_cache = [dict(r) for r in rws]
                for rw in self._runewords_cache:
                    rw["name"] = clean_item_name(rw["name"])
                    rw["norm_pl"] = normalize_text(rw["name"])
                    rw["norm_en"] = normalize_text(rw["name_en"])
                    rw["quality"] = "runeword"
                    rw["base_code"] = None
                    try:
                        r_codes = json.loads(rw["runes_json"] or "[]")
                        rw["level_req"] = max([RUNE_REQ_LEVELS.get(c, 0) for c in r_codes] or [0])
                    except Exception:
                        rw["level_req"] = None
                    rw["req_str"] = None
                    rw["req_dex"] = None
                    inc_types = json.loads(rw["include_types_json"] or "[]")
                    if any(t in inc_types for t in ["tors"]):
                        rw["slot"] = "armor"
                    elif any(t in inc_types for t in ["shld", "ashd", "head"]):
                        rw["slot"] = "shield"
                    elif any(t in inc_types for t in ["helm", "phlm", "pelt", "circ"]):
                        rw["slot"] = "head"
                    else:
                        rw["slot"] = "weapon"

                self._cache_loaded = True
        except Exception as e:
            print(f"[CatalogMatcher] Błąd ładowania cache: {e}")

    def find_item(self, name: str, name_en: str = None, quality: str = None) -> dict | None:
        if not self._cache_loaded:
            self._load_cache()

        norm_input_en = normalize_text(name_en)
        norm_input_pl = normalize_text(name)

        is_runeword_hint = quality and ("rune" in quality.lower() or "słowo" in quality.lower())
        is_unique_hint = quality and ("unik" in quality.lower() or "uniq" in quality.lower())
        is_set_hint = quality and ("zest" in quality.lower() or "set" in quality.lower())

        alias_target = ""
        for inp in [norm_input_pl, norm_input_en]:
            if inp and inp in ITEM_ALIASES:
                alias_target = normalize_text(ITEM_ALIASES[inp])
                break

        phonetic_pl = norm_input_pl.replace("si", "s") if "si" in norm_input_pl else ""

        all_inputs = [x for x in [alias_target, norm_input_en, norm_input_pl, phonetic_pl] if x]

        found_item = None
        is_runeword = False

        if is_runeword_hint:
            search_pools = [
                (self._runewords_cache, True),
                (self._items_cache, False)
            ]
        elif is_unique_hint:
            uniques = [x for x in self._items_cache if x.get("quality") == "unique"]
            others = [x for x in self._items_cache if x.get("quality") != "unique"]
            search_pools = [
                (uniques, False),
                (others, False),
                (self._runewords_cache, True)
            ]
        elif is_set_hint:
            sets = [x for x in self._items_cache if x.get("quality") == "set"]
            others = [x for x in self._items_cache if x.get("quality") != "set"]
            search_pools = [
                (sets, False),
                (others, False),
                (self._runewords_cache, True)
            ]
        else:
            search_pools = [
                (self._items_cache, False),
                (self._runewords_cache, True)
            ]

        # 1. Dokładne dopasowanie (PL, EN, Alias, Fonetyczne)
        for pool, rw_flag in search_pools:
            for inp in all_inputs:
                for candidate in pool:
                    if candidate["norm_en"] == inp or candidate["norm_pl"] == inp:
                        found_item = candidate
                        is_runeword = rw_flag
                        break
                if found_item:
                    break
            if found_item:
                break

            # 2. Dopasowanie prefiksu / podciągu (dla nazw >= 4 znaki)
            for inp in all_inputs:
                if len(inp) >= 4:
                    for candidate in pool:
                        if inp in candidate["norm_en"] or inp in candidate["norm_pl"]:
                            found_item = candidate
                            is_runeword = rw_flag
                            break
                    if found_item:
                        break
            if found_item:
                break

        # 3. Dopasowanie rozmyte (Fuzzy Matching z difflib)
        if not found_item:
            best_score = 0.0
            best_cand = None
            best_is_rw = False

            for pool, rw_flag in [
                (self._runewords_cache, True) if is_runeword_hint else (self._items_cache, False),
                (self._items_cache, False) if is_runeword_hint else (self._runewords_cache, True)
            ]:
                for candidate in pool:
                    score = 0.0
                    for inp in all_inputs:
                        if candidate["norm_en"]:
                            score = max(score, difflib.SequenceMatcher(None, inp, candidate["norm_en"]).ratio())
                        if candidate["norm_pl"]:
                            score = max(score, difflib.SequenceMatcher(None, inp, candidate["norm_pl"]).ratio())
                    
                    if score > best_score:
                        best_score = score
                        best_cand = candidate
                        best_is_rw = rw_flag

            if best_score >= 0.68:
                found_item = best_cand
                is_runeword = best_is_rw

        if not found_item:
            return None

        item_id = found_item["id"]
        result = dict(found_item)

        with self._get_con() as con:
            cur = con.cursor()
            cur.execute("""
                SELECT property, param, min_value, max_value, prop_group
                FROM item_properties
                WHERE item_id = ?
                ORDER BY slot ASC
            """, (item_id,))
            props = [dict(p) for p in cur.fetchall()]
            result["properties"] = props

            variable_props = []
            for p in props:
                prop_key = p.get("property", "")
                min_v = p.get("min_value")
                max_v = p.get("max_value")
                param = p.get("param", "")

                if prop_key in IGNORED_PROPERTIES:
                    continue

                if min_v is not None and max_v is not None and min_v != max_v:
                    try:
                        v_min = float(min_v)
                        v_max = float(max_v)
                        if v_min <= v_max:
                            variable_props.append({
                                "property": prop_key,
                                "label": clean_prop_name(prop_key, param),
                                "label_en": clean_prop_name_en(prop_key, param),
                                "min": int(v_min) if v_min.is_integer() else v_min,
                                "max": int(v_max) if v_max.is_integer() else v_max,
                                "param": param
                            })
                    except ValueError:
                        pass

            # Sprawdzenie bazowej obrony dla zbroi/hełmów/tarcz bez cechy ac% (np. Czapka Arlekina / Shako)
            has_ed = any(p.get("property") == "ac%" for p in props)
            b_code = found_item.get("base_code")
            base_info = self._item_bases.get(b_code, {})
            min_base_ac = base_info.get("minac", 0)
            max_base_ac = base_info.get("maxac", 0)

            if not has_ed and max_base_ac > min_base_ac and result.get("slot") in ("head", "armor", "shield", "gloves", "belt", "boots"):
                flat_ac = next((p for p in props if p.get("property") == "ac"), None)
                flat_min = int(flat_ac["min_value"]) if flat_ac and flat_ac.get("min_value") else 0
                flat_max = int(flat_ac["max_value"]) if flat_ac and flat_ac.get("max_value") else 0
                def_min = min_base_ac + flat_min
                def_max = max_base_ac + flat_max
                variable_props.insert(0, {
                    "property": "base_defense",
                    "label": "Obrona (Wartość Bazy)",
                    "label_en": "Defense (Base Value)",
                    "min": def_min,
                    "max": def_max,
                    "param": ""
                })

            result["variable_props"] = variable_props
            result["has_variable_rolls"] = len(variable_props) > 0
            return result

    def evaluate_item_rolls(self, catalog_item: dict, detected_stats: list[str], detected_rolls: dict = None) -> list[dict]:
        if not catalog_item or not catalog_item.get("variable_props"):
            return []

        rolls = {k.lower().replace("_", "").replace("-", ""): v for k, v in (detected_rolls or {}).items() if v is not None}
        raw_stats_text = " \n ".join(detected_stats)
        stats_text = normalize_text(raw_stats_text)
        evaluations = []

        for prop in catalog_item["variable_props"]:
            p_key = prop["property"]
            p_min = prop["min"]
            p_max = prop["max"]
            label = prop["label"]
            param = prop.get("param", "")
            
            val = None

            # Obsluga cechy randclassskill (Pochodnia Piekielnego Ognia)
            if p_key == "randclassskill":
                m_cls = re.search(r'\+?3\s*do\s*umiej[^\s]*\s*([a-zA-Z-]+)', stats_text)
                if not m_cls:
                    m_cls = re.search(r'\+?3\s*to\s*([a-zA-Z-]+)\s*skill', stats_text)
                
                class_name = "Nieznana"
                if m_cls:
                    raw_cls = m_cls.group(1).lower()
                    for k_pat, v_name in CLASS_NAMES_PL.items():
                        if k_pat in raw_cls:
                            class_name = v_name
                            break
                    if class_name == "Nieznana":
                        class_name = m_cls.group(1).capitalize()

                evaluations.append({
                    "property": p_key,
                    "label": "Klasa Postaci",
                    "label_en": "Character Class",
                    "min": "1 z 7",
                    "max": "Klasa",
                    "actual": class_name,
                    "percent": 100,
                    "rating": class_name,
                    "badge_class": "high"
                })
                continue

            # Obsluga cechy oskill (Call to Arms itp.)
            if p_key == "oskill" and param:
                param_norm = normalize_text(param)
                m_osk = re.search(rf'\+?(\d+)\s*do\s*(?:[^\n]*?{param_norm}|{param_norm})', stats_text)
                if not m_osk:
                    m_osk = re.search(rf'\+?(\d+)\s*to\s*(?:[^\n]*?{param_norm}|{param_norm})', stats_text)
                if m_osk:
                    try:
                        val = float(m_osk.group(1))
                    except ValueError:
                        pass

            # Weryfikacja obrony bazowej
            if p_key == "base_defense":
                for k_def in ["defense", "obrona", "ac", "basedefense"]:
                    if k_def in rolls:
                        try:
                            val = float(rolls[k_def])
                            break
                        except (ValueError, TypeError):
                            pass
                if val is None:
                    m_def = re.search(r'(?:obrona|defense)\s*:?\s*(\d+)', stats_text)
                    if not m_def:
                        m_def = re.search(r'(\d+)\s*(?:obrony|defense)', stats_text)
                    if m_def:
                        try:
                            val = float(m_def.group(1))
                        except ValueError:
                            pass

            # 1. Sprawdzenie w słowniku rolls
            if val is None:
                key_candidates = [
                    p_key.lower().replace("_", "").replace("-", ""),
                    p_key.replace("%", "").replace("-", ""),
                ]
                if p_key == "dmg%":
                    key_candidates.extend(["ed", "enhanceddamage", "damage%"])
                elif p_key == "res-all":
                    key_candidates.extend(["allres", "resall", "allresistances"])
                elif p_key == "all-stats":
                    key_candidates.extend(["allstats", "attributes", "stats"])
                elif p_key == "lifesteal":
                    key_candidates.extend(["ll", "lifesteal"])
                elif p_key == "manasteal":
                    key_candidates.extend(["ml", "manasteal"])
                elif p_key == "red-mag":
                    key_candidates.extend(["redmag", "magicdmgeduced", "mdr"])
                elif p_key == "ac%":
                    key_candidates.extend(["ac", "enhanceddefense"])
                elif p_key == "skilltab":
                    key_candidates.extend(["skilltab", "skills", "plusskills"])
                elif p_key in ("cast2", "cast3"):
                    key_candidates.extend(["fcr", "cast", "fastercastrate"])

                for cand in key_candidates:
                    if cand in rolls:
                        try:
                            val = float(rolls[cand])
                            break
                        except (ValueError, TypeError):
                            pass

            # 2. Sprawdzenie wyrażeń regularnych w liniach statystyk
            if val is None:
                patterns = []
                if p_key == "dmg%":
                    patterns = [
                        r'\+?(\d+)%\s*(?:do\s*obrazen|zwiekszone\s*obrazenia|enhanced\s*damage)',
                        r'(\d+)%\s*(?:ed|dmg|obrazen)'
                    ]
                elif p_key == "res-all":
                    patterns = [
                        r'\+?(\d+)\s*do\s*wszystkich\s*odporno',
                        r'(?:wszystkie\s*odporno[^\n]*?)\+?(\d+)',
                        r'to\s*all\s*resistances\s*\+?(\d+)',
                        r'all\s*resistances\s*\+?(\d+)'
                    ]
                elif p_key == "all-stats":
                    patterns = [
                        r'\+?(\d+)\s*do\s*wszystkich\s*atrybut',
                        r'\+?(\d+)\s*do\s*wszystkich\s*cech',
                        r'\+?(\d+)\s*to\s*all\s*attributes'
                    ]
                elif p_key == "lifesteal":
                    patterns = [
                        r'(\d+)%\s*(?:wyssanie|skradzione|kradnie|stolen).*zyci',
                        r'(\d+)%\s*life\s*stolen\s*per\s*hit'
                    ]
                elif p_key == "manasteal":
                    patterns = [
                        r'(\d+)%\s*(?:wyssanie|skradzione|kradnie|stolen).*man',
                        r'(\d+)%\s*mana\s*stolen\s*per\s*hit'
                    ]
                elif p_key == "red-mag":
                    patterns = [
                        r'(?:redukcja|zmniejsza|zmniejszenie)[^\n]*?obrazen[^\n]*?magii\s*(?:o\s*)?(\d+)',
                        r'magic\s*damage\s*reduced\s*(?:by\s*)?(\d+)'
                    ]
                elif p_key == "red-dmg%":
                    patterns = [
                        r'redukcja\s*obrazen\s*(?:fizycznych)?\s*(?:o\s*)?(\d+)%',
                        r'damage\s*reduced\s*by\s*(\d+)%'
                    ]
                elif p_key == "mag%":
                    patterns = [r'(\d+)%\s*(?:lepsza\s*szansa|szansa\s*na\s*znalezienie\s*magicznych|better\s*chance)']
                elif p_key == "gold%":
                    patterns = [r'(\d+)%\s*(?:wiecej\s*zlota|extra\s*gold)']
                elif p_key == "ac%":
                    patterns = [r'\+?(\d+)%\s*(?:do\s*obrony|zwiekszona\s*obrona|enhanced\s*defense)']
                elif p_key == "skilltab":
                    patterns = [
                        r'\+?(\d+)\s*do\s*umiejetnosci',
                        r'\+?(\d+)\s*to\s*[a-zA-Z\s]+skills'
                    ]
                elif p_key == "str":
                    patterns = [
                        r'\+?(\d+)\s*do\s*sily', r'sila\s*\+?(\d+)',
                        r'\+?(\d+)\s*to\s*strength', r'strength\s*\+?(\d+)'
                    ]
                elif p_key == "dex":
                    patterns = [
                        r'\+?(\d+)\s*do\s*zrecznosci', r'zrecznosc\s*\+?(\d+)',
                        r'\+?(\d+)\s*to\s*dexterity', r'dexterity\s*\+?(\d+)'
                    ]
                elif p_key == "vit":
                    patterns = [
                        r'\+?(\d+)\s*do\s*zywotnosci', r'zywotnosc\s*\+?(\d+)',
                        r'\+?(\d+)\s*to\s*vitality', r'vitality\s*\+?(\d+)'
                    ]
                elif p_key == "enr":
                    patterns = [
                        r'\+?(\d+)\s*do\s*energii', r'energia\s*\+?(\d+)',
                        r'\+?(\d+)\s*to\s*energy', r'energy\s*\+?(\d+)'
                    ]
                elif p_key in ("cast2", "cast3"):
                    patterns = [
                        r'\+?(\d+)%\s*do\s*szybkosci\s*rzucania', r'(\d+)%\s*(?:fcr|cast)',
                        r'(\d+)%\s*faster\s*cast\s*rate'
                    ]
                elif p_key in ("swing2", "swing3"):
                    patterns = [
                        r'\+?(\d+)%\s*do\s*szybkosci\s*ataku', r'(\d+)%\s*(?:ias|attack\s*speed)',
                        r'(\d+)%\s*increased\s*attack\s*speed'
                    ]
                elif p_key == "dmg":
                    patterns = [
                        r'\+?(\d+)\s*(?:do\s*obrazen|obrazen)', r'dodaje\s*(\d+)\s*obrazen',
                        r'\+?(\d+)\s*to\s*damage'
                    ]
                elif p_key == "abs-mag":
                    patterns = [r'\+?(\d+)\s*do\s*absorpcji\s*magii', r'(?:absorpcja\s*magii|magic\s*absorb)[^\n]*?\+?(\d+)%?']
                elif p_key == "abs-fire":
                    patterns = [r'\+?(\d+)\s*do\s*absorpcji\s*ognia', r'(?:absorpcja\s*ognia|fire\s*absorb)[^\n]*?\+?(\d+)%?']
                elif p_key == "abs-ltng":
                    patterns = [
                        r'\+?(\d+)\s*do\s*absorpcji\s*blyskawic',
                        r'(?:absorpcja\s*blyskawic|lightning\s*absorb)[^\n]*?\+?(\d+)%?'
                    ]
                elif p_key == "mana":
                    patterns = [r'\+?(\d+)\s*do\s*many', r'mana\s*\+?(\d+)', r'\+?(\d+)\s*to\s*mana']
                elif p_key == "addxp":
                    patterns = [r'\+?(\d+)%\s*(?:wiecej\s*doswiadczenia|to\s*experience)']
                elif p_key == "sock":
                    patterns = [r'gniazd[a-z]*:\s*(\d+)', r'sockets?:\s*(\d+)']

                for pat in patterns:
                    m = re.search(pat, stats_text)
                    if m:
                        try:
                            val = float(m.group(1))
                            break
                        except ValueError:
                            pass

            if val is not None:
                if p_max == p_min:
                    pct = 100.0
                else:
                    pct = max(0.0, min(100.0, (val - p_min) / (p_max - p_min) * 100.0))
                
                pct_int = int(round(pct))
                if val >= p_max:
                    rating = "PERF"
                    badge_class = "perf"
                elif pct_int >= 75:
                    rating = "HIGH"
                    badge_class = "high"
                elif pct_int >= 40:
                    rating = "MID"
                    badge_class = "mid"
                elif val <= p_min:
                    rating = "MIN"
                    badge_class = "min"
                else:
                    rating = "LOW"
                    badge_class = "low"

                evaluations.append({
                    "property": p_key,
                    "label": label,
                    "label_en": prop.get("label_en") or clean_prop_name_en(p_key, param),
                    "min": p_min,
                    "max": p_max,
                    "actual": int(val) if val.is_integer() else val,
                    "percent": pct_int,
                    "rating": rating,
                    "badge_class": badge_class
                })

        return evaluations

catalog_matcher = CatalogMatcher()
