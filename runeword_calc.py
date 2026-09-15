import sqlite3
import json
from pathlib import Path
from collections import Counter

import config
CATALOG_PATH = config.DATA_DIR / "catalog.sqlite"
STASH_PATH = config.DB_PATH

R_CODE_TO_NUM = {f"r{i:02d}": i for i in range(1, 34)}

RUNE_NAMES = [
    "", "El", "Eld", "Tir", "Nef", "Eth", "Ith", "Tal", "Ral", "Ort", "Thul",
    "Amn", "Sol", "Shael", "Dol", "Hel", "Io", "Lum", "Ko", "Fal", "Lem",
    "Pul", "Um", "Mal", "Ist", "Gul", "Vex", "Ohm", "Lo", "Sur", "Ber",
    "Jah", "Cham", "Zod"
]

R_CODE_TO_NAME = {f"r{i:02d}": RUNE_NAMES[i] for i in range(1, 34)}
NAME_TO_R_CODE = {RUNE_NAMES[i]: f"r{i:02d}" for i in range(1, 34)}

RUNE_FILENAMES = {
    f"r{i:02d}": f"runa-{RUNE_NAMES[i].lower()}--r{i:02d}.png" for i in range(1, 34)
}

RUNE_REQ_LEVELS = {
    "r01": 11, "r02": 11, "r03": 13, "r04": 13, "r05": 15,
    "r06": 15, "r07": 17, "r08": 19, "r09": 21, "r10": 23,
    "r11": 25, "r12": 27, "r13": 29, "r14": 31, "r15": 0,
    "r16": 35, "r17": 37, "r18": 39, "r19": 41, "r20": 43,
    "r21": 45, "r22": 47, "r23": 49, "r24": 51, "r25": 53,
    "r26": 55, "r27": 57, "r28": 59, "r29": 61, "r30": 63,
    "r31": 65, "r32": 67, "r33": 69
}

BASE_TYPE_TRANSLATIONS = {
    "shld": "Tarcze", "tors": "Zbroje", "helm": "Hełmy",
    "swor": "Miecze", "pole": "Drzewcowa", "spea": "Włócznie",
    "mace": "Buławy", "axe": "Topory", "bow": "Łuki",
    "xbow": "Kusze", "wand": "Różdżki", "staf": "Laski",
    "scep": "Berła", "clau": "Szpony", "club": "Maczugi",
    "hamm": "Młoty", "knif": "Sztylety", "pelt": "Pelt Druida",
    "phlm": "Hełm Barbarzyńcy", "ashd": "Tarcze Paladyna",
    "head": "Głowy Nekromanty", "abow": "Łuki Amazonki",
    "aspe": "Włócznie Amazonki", "ajav": "Oszczepy Amazonki",
    "weap": "Dowolna Broń", "mele": "Broń do Walki Wręcz",
    "miss": "Broń Dystansowa"
}

BASE_CATEGORY_MAP = {
    "tors": "Zbroja",
    "shld": "Tarcza",
    "ashd": "Tarcza",
    "head": "Tarcza",
    "helm": "Hełm",
    "phlm": "Hełm",
    "pelt": "Hełm",
    "circ": "Hełm"
}

RUNE_BONUSES = {
    "El": [("+50 Do Skuteczności Ataku", "weap"), ("+1 Do Promienia Światła", "all")],
    "Eld": [("+75% Obrażeń Przeciwko Nieumarłym", "weap"), ("+7% Zwiększona Szansa na Blok", "shld"), ("15% Wolniejsze Zużycie Wytrzymałości", "helm")],
    "Tir": [("+2 Do Many Po Każdym Zabiciu", "all")],
    "Nef": [("Odepchnięcie (Knockback)", "weap"), ("+30 Do Obrony Przed Pociskami", "helm")],
    "Eth": [("-25% Do Obrony Celu", "weap"), ("Regeneracja Many 15%", "helm")],
    "Ith": [("+9 Do Maksymalnych Obrażeń", "weap"), ("15% Otrzymanych Obrażeń Przechodzi na Manę", "helm")],
    "Tal": [("+75 Do Obrażeń Od Trucizn (5 sek.)", "weap"), ("Odporność na Trucizny 35%", "shld"), ("Odporność na Trucizny 30%", "helm")],
    "Ral": [("Dodaje 5-30 Obrażeń Od Ognia", "weap"), ("Odporność na Ogień 35%", "shld"), ("Odporność na Ogień 30%", "helm")],
    "Ort": [("Dodaje 1-50 Obrażeń Od Błyskawic", "weap"), ("Odporność na Błyskawice 35%", "shld"), ("Odporność na Błyskawice 30%", "helm")],
    "Thul": [("Dodaje 3-14 Obrażeń Od Zimna", "weap"), ("Odporność na Zimno 35%", "shld"), ("Odporność na Zimno 30%", "helm")],
    "Amn": [("7% Wyssanie Życia", "weap"), ("Odwet: 14 Obrażeń", "helm")],
    "Sol": [("+9 Do Minimalnych Obrażeń", "weap"), ("Redukcja Obrażeń o 7", "helm")],
    "Shael": [("+20% Zwiększona Szybkość Ataku (IAS)", "weap"), ("+20% Szybsze Odzyskiwanie Równowagi (FHR)", "helm"), ("+20% Szybszy Blok", "shld")],
    "Dol": [("25% Szansa na Ucieczkę Potwora", "weap"), ("Regeneracja Życia +7", "helm")],
    "Hel": [("Wymagania -20%", "weap"), ("Wymagania -15%", "helm")],
    "Io": [("+10 Do Żywotności", "all")],
    "Lum": [("+10 Do Energii", "all")],
    "Ko": [("+10 Do Zręczności", "all")],
    "Fal": [("+10 Do Siły", "all")],
    "Lem": [("75% Więcej Złota", "weap"), ("50% Więcej Złota", "helm")],
    "Pul": [("+75% Obrażeń Przeciwko Demonom", "weap"), ("+30% Zwiększona Obrona", "helm")],
    "Um": [("25% Szansa na Otwarte Rany", "weap"), ("Wszystkie Odporności +15", "helm"), ("Wszystkie Odporności +22", "shld")],
    "Mal": [("Zapobiega Leczeniu Potworów", "weap"), ("Redukcja Obrażeń od Magii o 7", "helm")],
    "Ist": [("30% Lepsza Szansa na Znalezienie Magicznych Przedmiotów", "weap"), ("25% Lepsza Szansa na Znalezienie Magicznych Przedmiotów", "helm")],
    "Gul": [("20% Bonus Do Skuteczności Ataku", "weap"), ("+5% Do Maksymalnej Odp. na Trucizny", "helm")],
    "Vex": [("7% Wyssanie Many", "weap"), ("+5% Do Maksymalnej Odp. na Ogień", "helm")],
    "Ohm": [("+50% Zwiększone Obrażenia (ED)", "weap"), ("+5% Do Maksymalnej Odp. na Zimno", "helm")],
    "Lo": [("20% Szansa na Śmiertelne Uderzenie (Deadly Strike)", "weap"), ("+5% Do Maksymalnej Odp. na Błyskawice", "helm")],
    "Sur": [("Oślepia Cel", "weap"), ("Maksimum Many 5%", "helm")],
    "Ber": [("20% Szansa na Druzgocące Uderzenie (Crushing Blow)", "weap"), ("Redukcja Obrażeń Fizycznych o 8%", "helm")],
    "Jah": [("Ignoruje Obronę Celu", "weap"), ("Maksimum Życia 5%", "helm")],
    "Cham": [("Zamraża Cel +3", "weap"), ("Nie Może Zostać Zamrożony", "helm")],
    "Zod": [("Niezniszczalny", "all")]
}

def get_rune_icon_path(rune_name: str) -> str:
    r_code = NAME_TO_R_CODE.get(rune_name)
    if r_code and r_code in RUNE_FILENAMES:
        return f"/static/images/runes/{RUNE_FILENAMES[r_code]}"
    return ""

def format_property_display(prop: str, param: str, min_v: str, max_v: str) -> dict:
    val_str = f"{min_v}-{max_v}" if min_v and max_v and min_v != max_v else (min_v or max_v or "")
    is_aura = False

    if prop == "aura":
        is_aura = True
        text = f"Poziom {val_str} Aura {param} Kiedy Założony"
    elif prop == "allskills":
        text = f"+{val_str} Do Wszystkich Umiejętności"
    elif prop == "oskill":
        text = f"+{val_str} Do {param}"
    elif prop == "dmg%":
        text = f"+{val_str}% Zwiększone Obrażenia (ED)"
    elif prop == "ac%":
        text = f"+{val_str}% Zwiększona Obrona (ED)"
    elif prop == "ac":
        text = f"+{val_str} Do Obrony"
    elif prop == "res-all":
        text = f"Wszystkie Odporności +{val_str}"
    elif prop == "res-fire":
        text = f"Odporność na Ogień +{val_str}%"
    elif prop == "res-ltng":
        text = f"Odporność na Błyskawice +{val_str}%"
    elif prop == "res-cold":
        text = f"Odporność na Zimno +{val_str}%"
    elif prop == "res-pois":
        text = f"Odporność na Trucizny +{val_str}%"
    elif prop == "lifesteal":
        text = f"{val_str}% Wyssanie Życia na Trafienie"
    elif prop == "manasteal":
        text = f"{val_str}% Wyssanie Many na Trafienie"
    elif prop in ("cast2", "cast3"):
        text = f"+{val_str}% Szybsze Rzucanie Czarów (FCR)"
    elif prop in ("balance2", "balance3"):
        text = f"+{val_str}% Szybsze Odzyskiwanie Równowagi (FHR)"
    elif prop in ("swing2", "swing3"):
        text = f"+{val_str}% Szybkość Ataku (IAS)"
    elif prop in ("move2", "move3"):
        text = f"+{val_str}% Szybkość Biegania/Chodzenia (FRW)"
    elif prop == "str":
        text = f"+{val_str} Do Siły"
    elif prop == "dex":
        text = f"+{val_str} Do Zręczności"
    elif prop == "vit":
        text = f"+{val_str} Do Żywotności"
    elif prop == "enr":
        text = f"+{val_str} Do Energii"
    elif prop == "hp":
        text = f"+{val_str} Do Życia"
    elif prop == "mana":
        text = f"+{val_str} Do Many"
    elif prop == "red-dmg%":
        text = f"Redukcja Obrażeń Fizycznych o {val_str}%"
    elif prop == "red-mag":
        text = f"Redukcja Obrażeń od Magii o {val_str}"
    elif prop == "mag%":
        text = f"{val_str}% Lepsza Szansa na Magiczne Przedmioty (MF)"
    elif prop == "gold%":
        text = f"{val_str}% Więcej Złota od Potworów"
    elif prop == "openwounds":
        text = f"{val_str}% Szansa na Otwarte Rany"
    elif prop == "crush":
        text = f"{val_str}% Szansa na Druzgocące Uderzenie (CB)"
    elif prop == "deadly":
        text = f"{val_str}% Szansa na Śmiertelne Uderzenie (DS)"
    elif prop == "pierce-ltng":
        text = f"-{val_str}% Do Odp. Przeciwnika na Błyskawice"
    elif prop == "pierce-fire":
        text = f"-{val_str}% Do Odp. Przeciwnika na Ogień"
    elif prop == "pierce-cold":
        text = f"-{val_str}% Do Odp. Przeciwnika na Zimno"
    elif prop == "pierce-pois":
        text = f"-{val_str}% Do Odp. Przeciwnika na Trucizny"
    elif prop == "regen":
        text = f"Regeneracja Życia +{val_str}"
    elif prop == "nofreeze":
        text = "Nie Może Zostać Zamrożony"
    elif prop == "ignore-ac":
        text = "Ignoruje Obronę Celu"
    elif prop == "prevent-heal":
        text = "Zapobiega Leczeniu Potworów"
    elif prop == "knock":
        text = "Odepchnięcie (Knockback)"
    elif prop == "charged":
        text = f"Poziom {max_v} {param} ({min_v} Ładunków)"
    elif prop == "str/lvl":
        factor = (float(param) / 8.0) if param and param.isdigit() else 0.75
        text = f"+{factor:.2f} Do Siły (W Zależności od Poziomu Postaci)"
    elif prop == "vit/lvl":
        factor = (float(param) / 8.0) if param and param.isdigit() else 0.5
        text = f"+{factor:.2f} Do Żywotności (W Zależności od Poziomu Postaci)"
    elif prop == "mag%/lvl":
        factor = (float(param) / 8.0) if param and param.isdigit() else 1.0
        text = f"+{factor:.2f}% Lepsza Szansa na Magiki (W Zależności od Poziomu)"
    elif prop in ("cast1", "cast2", "cast3"):
        text = f"+{val_str}% Szybsze Rzucanie Czarów (FCR)"
    elif prop in ("hit1", "hit2", "hit3"):
        text = f"+{val_str}% Szybsze Odzyskiwanie Równowagi (FHR)"
    elif prop in ("block1", "block2", "block3"):
        text = f"+{val_str}% Szybsze Blokowanie (FBR)"
    elif prop in ("all-stats", "allstats"):
        text = f"+{val_str} Do Wszystkich Atrybutów"
    elif prop in ("extra-mag", "mag-dmg"):
        text = f"+{val_str}% Do Obrażeń od Magii"
    elif prop == "heal-kill":
        text = f"+{val_str} Życia Za Każde Zabójstwo"
    elif prop == "mana-kill":
        text = f"+{val_str} Many Za Każde Zabójstwo"
    elif prop in ("res-all", "all_res"):
        text = f"+{val_str} Do Wszystkich Odporności"
    elif prop == "res-all-max":
        text = f"+{val_str}% Do Maksymalnych Odporności"
    elif prop == "gethit-skill":
        text = f"{min_v}% Szansa na rzucenie Poziomu {max_v} {param} po otrzymaniu ciosu"
    elif prop == "hit-skill":
        text = f"{min_v}% Szansa na rzucenie Poziomu {max_v} {param} przy trafieniu"
    elif prop == "kill-skill":
        text = f"{min_v}% Szansa na rzucenie Poziomu {max_v} {param} po zabiciu wroga"
    elif prop == "att-skill":
        text = f"{min_v}% Szansa na rzucenie Poziomu {max_v} {param} przy ataku"

    elif prop in ("cast1", "cast2", "cast3"):
        text = f"+{val_str}% Szybsze Rzucanie Czarów (FCR)"
    elif prop in ("hit1", "hit2", "hit3"):
        text = f"+{val_str}% Szybsze Odzyskiwanie Równowagi (FHR)"
    elif prop in ("block1", "block2", "block3"):
        text = f"+{val_str}% Szybsze Blokowanie (FBR)"
    elif prop in ("all-stats", "allstats"):
        text = f"+{val_str} Do Wszystkich Atrybutów"
    elif prop in ("extra-mag", "mag-dmg"):
        text = f"+{val_str}% Do Obrażeń od Magii"
    elif prop == "heal-kill":
        text = f"+{val_str} Życia Za Każde Zabójstwo"
    elif prop == "mana-kill":
        text = f"+{val_str} Many Za Każde Zabójstwo"
    elif prop in ("res-all", "all_res"):
        text = f"+{val_str} Do Wszystkich Odporności"
    elif prop == "res-all-max":
        text = f"+{val_str}% Do Maksymalnych Odporności"
    elif prop == "gethit-skill":
        text = f"{min_v}% Szansa na rzucenie Poziomu {max_v} {param} po otrzymaniu ciosu"
    elif prop == "hit-skill":
        text = f"{min_v}% Szansa na rzucenie Poziomu {max_v} {param} przy trafieniu"
    elif prop == "kill-skill":
        text = f"{min_v}% Szansa na rzucenie Poziomu {max_v} {param} po zabiciu wroga"
    elif prop == "att-skill":
        text = f"{min_v}% Szansa na rzucenie Poziomu {max_v} {param} przy ataku"

    else:
        text = f"{prop}: +{val_str} {param}".strip()

    return {
        "text": text,
        "is_aura": is_aura
    }

def calculate_runewords_crafting() -> dict:
    if not CATALOG_PATH.exists() or not STASH_PATH.exists():
        return {"ready": [], "missing_one": [], "all": [], "total_runes": 0, "ready_count": 0, "missing_one_count": 0}

    owned_runes = {}
    with sqlite3.connect(STASH_PATH) as con:
        rows = con.execute("SELECT name, count FROM runes").fetchall()
        for name, count in rows:
            owned_runes[name] = count

    total_owned = sum(owned_runes.values())

    rw_properties = {}
    with sqlite3.connect(CATALOG_PATH) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("""
            SELECT item_id, property, param, min_value, max_value
            FROM item_properties
            WHERE item_id LIKE 'runeword:%'
            ORDER BY slot ASC
        """)
        for r in cur.fetchall():
            iid = r["item_id"]
            if iid not in rw_properties:
                rw_properties[iid] = []
            rw_properties[iid].append(dict(r))

        cur.execute("""
            SELECT id, name, name_en, complete, runes_json, include_types_json, raw_json
            FROM runewords
            WHERE complete = 1
        """)
        runewords = cur.fetchall()

        ready_list = []
        missing_one_list = []
        missing_two_list = []
        missing_three_list = []
        all_list = []

        for rw in runewords:
            r_codes = json.loads(rw["runes_json"] or "[]")
            if not r_codes:
                continue

            rune_names = [R_CODE_TO_NAME.get(c, c) for c in r_codes]
            req_counts = Counter(rune_names)

            req_lvl = max([RUNE_REQ_LEVELS.get(c, 0) for c in r_codes] or [0])

            # Bazy
            include_types = json.loads(rw["include_types_json"] or "[]")
            bases = [BASE_TYPE_TRANSLATIONS.get(t, t.upper()) for t in include_types if t]
            bases_str = ", ".join(bases) if bases else "Różne bazy"

            primary_cat = "Broń"
            for t in include_types:
                if t in BASE_CATEGORY_MAP:
                    primary_cat = BASE_CATEGORY_MAP[t]
                    break

            raw_data = json.loads(rw["raw_json"] or "{}")
            patch_raw = str(raw_data.get("*Patch Release") or raw_data.get("version") or "")
            patch = "1.10"
            if "109" in patch_raw:
                patch = "1.09"
            elif "111" in patch_raw:
                patch = "1.11"
            elif "2.4" in patch_raw:
                patch = "2.4"
            elif "2.6" in patch_raw:
                patch = "2.6"
            elif "110" in patch_raw or "ladder" in patch_raw.lower():
                patch = "1.10"

            needed_diff = 0
            missing_runes = []
            runes_details = []

            for r_name in rune_names:
                cnt_needed = req_counts[r_name]
                cnt_owned = owned_runes.get(r_name, 0)
                has_enough = cnt_owned >= cnt_needed
                
                if not has_enough:
                    diff = cnt_needed - cnt_owned
                    if r_name not in missing_runes:
                        needed_diff += diff
                        missing_runes.append(r_name)

                r_code = NAME_TO_R_CODE.get(r_name, "")
                r_num = R_CODE_TO_NUM.get(r_code, 0)
                tier = "low" if r_num <= 16 else ("mid" if r_num <= 25 else "high")
                runes_details.append({
                    "name": r_name,
                    "code": r_code,
                    "icon": get_rune_icon_path(r_name),
                    "owned": cnt_owned,
                    "needed": cnt_needed,
                    "has": cnt_owned >= 1,
                    "tier": tier
                })

            stats_list = []
            raw_props = rw_properties.get(rw["id"], [])
            for p in raw_props:
                fmt = format_property_display(p["property"], p["param"], p["min_value"], p["max_value"])
                stats_list.append({
                    "text": fmt["text"],
                    "is_aura": fmt["is_aura"],
                    "rune_icon": None,
                    "rune_name": None
                })

            for r_name in rune_names:
                bonuses = RUNE_BONUSES.get(r_name, [])
                for b_text, b_type in bonuses:
                    if b_type == "all" or (primary_cat == "Broń" and b_type == "weap") or (primary_cat == "Tarcza" and b_type == "shld") or (primary_cat in ("Zbroja", "Hełm") and b_type == "helm"):
                        if not any(b_text[:12].lower() in s["text"].lower() for s in stats_list):
                            stats_list.append({
                                "text": b_text,
                                "is_aura": False,
                                "rune_icon": get_rune_icon_path(r_name),
                                "rune_name": r_name
                            })

            BASE_ICONS = {
                "Zbroja": "/static/images/database/armor/fs-sk-rzana-zbroja--lea.png",
                "Hełm": "/static/images/database/armor/ms-kaptur--cap.png",
                "Tarcza": "/static/images/database/armor/fs-rodela--pa2.png",
                "Broń": "/static/images/database/weapon/ms-kryszta-owy-miecz--crs.png",
            }
            base_ico = BASE_ICONS.get(primary_cat, "/static/images/database/weapon/ms-korbacz--fla.png")
            if "łuk" in bases_str.lower() or "kusz" in bases_str.lower():
                base_ico = "/static/images/database/weapon/fs-ci-ka-kusza--hxb.png"
            elif "drzewc" in bases_str.lower() or "kosa" in bases_str.lower():
                base_ico = "/static/images/database/weapon/fs-bojowa-kosa--wsc.png"
            elif "korbacz" in bases_str.lower() or "buław" in bases_str.lower():
                base_ico = "/static/images/database/weapon/ms-korbacz--fla.png"

            item_data = {
                "id": rw["id"],
                "name": rw["name"].replace("[ms]", "").replace("[fs]", "").strip(),
                "name_en": rw["name_en"],
                "patch": patch,
                "category": primary_cat,
                "base_icon": base_ico,
                "level_req": req_lvl,
                "sockets": len(rune_names),
                "bases": bases_str,
                "runes": runes_details,
                "runes_str": " + ".join(rune_names),
                "stats": stats_list,
                "ready": needed_diff == 0,
                "missing_count": needed_diff,
                "missing_runes": missing_runes
            }

            all_list.append(item_data)
            if needed_diff == 0:
                ready_list.append(item_data)
            elif needed_diff == 1:
                missing_one_list.append(item_data)
            elif needed_diff == 2:
                missing_two_list.append(item_data)
            elif needed_diff == 3:
                missing_three_list.append(item_data)
            elif needed_diff == 2:
                missing_two_list.append(item_data)
            elif needed_diff == 3:
                missing_three_list.append(item_data)

    ready_list.sort(key=lambda x: x["level_req"], reverse=True)
    missing_one_list.sort(key=lambda x: x["level_req"], reverse=True)
    missing_two_list.sort(key=lambda x: x["level_req"], reverse=True)
    missing_three_list.sort(key=lambda x: x["level_req"], reverse=True)
    all_list.sort(key=lambda x: x["level_req"], reverse=True)

    return {
        "ready": ready_list,
        "missing_one": missing_one_list,
        "missing_two": missing_two_list,
        "missing_three": missing_three_list,
        "all": all_list,
        "total_runes": total_owned,
        "ready_count": len(ready_list),
        "missing_one_count": len(missing_one_list),
        "missing_two_count": len(missing_two_list),
        "missing_three_count": len(missing_three_list)
    }
