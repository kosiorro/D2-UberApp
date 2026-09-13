import json
import time
from pathlib import Path
from PIL import Image
from google import genai
from google.genai import types

import config
from db import record_api_call, update_runes
from catalog_matcher import catalog_matcher

_client = None
_client_key = None

def get_client():
    global _client, _client_key
    if _client is None or _client_key != config.GEMINI_API_KEY:
        _client = genai.Client(api_key=config.GEMINI_API_KEY)
        _client_key = config.GEMINI_API_KEY
    return _client

UNIFIED_PROMPT = """Przeanalizuj ten zrzut ekranu z gry Diablo 2 Resurrected.
Zrzut może przedstawiać:
A) Opis przedmiotu (tooltip)
B) Zakładkę "RUNY" w skrytce (stash) ze stałą siatką 33 run (od El do Zod).

JEŚLI TO ZAKŁADKA RUN ("RUNY"):
Plansza ma stałą siatkę o wymiarach 9 kolumn x 5 wierszy dla 33 run:
Wiersz 1 (kolumny 1-9): 1:El, 2:Eld, 3:Tir, 4:Nef, 5:Eth, 6:Ith, 7:Tal, 8:Ral, 9:Ort
Wiersz 2 (kolumny 1-9): 1:Thul, 2:Amn, 3:Sol, 4:Shael, 5:Dol, 6:Hel, 7:Io, 8:Lum, 9:Ko
Wiersz 3 (kolumny 1-9): 1:Fal, 2:Lem, 3:Pul, 4:Um, 5:Mal, 6:Ist, 7:Gul, 8:Vex, 9:Ohm
Wiersz 4: Kolumna 1:Lo, Kolumna 2:Sur (środek pusty) Kolumna 8:Ber, Kolumna 9:Jah
Wiersz 5: Kolumna 1:Cham (środek pusty) Kolumna 9:Zod

INSTRUKCJA DLA RUN:
- Zbadaj każdą kolumnę wiersza. Sloty ciemne/szare oznaczają 0 sztuk.
- Sloty podświetlone mają białą cyfrę w prawym dolnym rogu.
- Zwróć tylko te runy, których ilość > 0.
Format odpowiedzi dla run:
{
  "type": "rune_stash",
  "runes": {
    "El": 1,
    "Eld": 6,
    ...
  }
}

JEŚLI TO OPIS PRZEDMIOTU (TOOLTIP):
Zwróć:
{
  "type": "item",
  "name": "nazwa po polsku",
  "name_en": "oficjalna nazwa po angielsku (np. The Oculus, Skin of the Vipermagi, Thunderstroke, Harlequin Crest itp.)",
  "base": "nazwa bazy",
  "slot": "head|armor|shield|weapon|gloves|belt|boots|amulet|ring|charm|misc (wybierz dokładnie jedno)",
  "quality": "unikalny|zestaw|runeword|rzadki|magiczny|normalny",
  "level_req": null lub liczba,
  "req_str": null lub liczba,
  "req_dex": null lub liczba,
  "defense": null lub liczba,
  "damage": null lub "zakres",
  "sockets": null lub liczba,
  "socket_contents": ["wyłącznie widoczne nazwy osadzonych run, klejnotów lub kamieni; pusta lista gdy nie wiadomo"],
  "stats": ["linia statystyki 1", "linia 2..."],
  "rolls": {
    "dmg%": null lub liczba (zwiększone obrażenia ED),
    "res-all": null lub liczba (wszystkie odporności),
    "lifesteal": null lub liczba,
    "manasteal": null lub liczba,
    "red-mag": null lub liczba (redukcja obrażeń od magii),
    "ac%": null lub liczba (zwiększona obrona ED),
    "mag%": null lub liczba (MF)
  }
}

Zwróć WYŁĄCZNIE czysty JSON bez formatowania markdown."""

def detect_item_slot(name: str = "", name_en: str = "", base: str = "", current_slot: str = "", quality: str = "") -> str:
    combined = f"{name} {name_en} {base}".lower()
    base_lower = (base or "").lower()

    shield_keys = ["rondel", "rondache", "rodel", "rodela", "ródela", "tarcz", "shield", "puklerz", "pelta", "egid", "aegis", 
                   "kuria", "herald", "targi", "targe", "tarża", "aerin", "kurast", "zakarum", "vortex", "ward", 
                   "pavise", "scutum", "monarch", "monarcha", "głowa", "glowa", "trofeum", "trophy", "kanty"]
    for k in shield_keys:
        if k in base_lower:
            return "shield"

    boots_keys = ["buty", "boot", "greave", "nagolenic", "trzewik", "chodak", "tread", "spur"]
    for k in boots_keys:
        if k in base_lower:
            return "boots"

    gloves_keys = ["rekawic", "rękawic", "glove", "mitt", "gauntlet", "karwasz", "pięści", "piesci", "łapy", "lapy"]
    for k in gloves_keys:
        if k in base_lower:
            return "gloves"

    belt_keys = ["pas", "belt", "sash", "girdle", "szarf"]
    for k in belt_keys:
        if k in base_lower:
            return "belt"

    armor_keys = ["zbroj", "armor", "armour", "plate", "płytow", "plytow", "kolczug", "hauberk", "cuirass", "pancerz", "kolczan", "zbroja"]
    for k in armor_keys:
        if k in base_lower:
            return "armor"

    head_keys = ["helm", "hełm", "cap", "czap", "czako", "shako", "crown", "koron", "mask", "diadem", "tiar", "szyszak", "kapalin", "sallet", "basinet", "armet", "casque", "przyłbica", "przylbica", "morion"]
    for k in head_keys:
        if k in base_lower:
            return "head"

    weapon_keys = ["miecz", "sword", "topor", "topór", "axe", "bulaw", "buław", "mace", "kostur", "staff", "rozdzka", "różdżka", "wand", "luk", "łuk", "bow", "kusz", "kusza", "crossbow", "sztylet", "dagger", "berlo", "berło", "scepter", "flail", "korbacz", "kosa", "scythe", "polearm", "drzewc", "spear", "wloczni", "włóczni", "pike", "pika", "halberd", "partizan", "thresher"]
    for k in weapon_keys:
        if k in base_lower:
            return "weapon"

    for k in shield_keys:
        if k in combined:
            return "shield"
    for k in boots_keys:
        if k in combined:
            return "boots"
    for k in gloves_keys:
        if k in combined:
            return "gloves"
    for k in belt_keys:
        if k in combined:
            return "belt"
    for k in ["amulet"]:
        if k in combined:
            return "amulet"
    for k in ["pierscien", "pierścień", "ring"]:
        if k in combined:
            return "ring"
    for k in ["talizman", "charm"]:
        if k in combined:
            return "charm"

    valid_slots = ("head", "armor", "shield", "weapon", "gloves", "belt", "boots", "amulet", "ring", "charm")
    if current_slot and current_slot.lower() in valid_slots:
        return current_slot.lower()

    for k in head_keys:
        if k in combined:
            return "head"
    for k in armor_keys:
        if k in combined:
            return "armor"
    for k in weapon_keys:
        if k in combined:
            return "weapon"

    return current_slot or "misc"

def process_image(image_path: Path, scan_mode="normal") -> dict:
    """
    Analizuje zrzut ekranu (tooltip przedmiotu lub zakładkę run) za pomocą Gemini Flash Lite.
    Rejestruje zużycie tokenów, czas wykonania i koszty w bazie danych.
    """
    client = get_client()
    t0 = time.time()
    
    try:
        img = Image.open(image_path)
    except Exception as e:
        return {"status": "error", "message": f"Błąd otwarcia pliku graficznego: {e}"}

    try:
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=[img, UNIFIED_PROMPT + '\n' + {
                'runes':'Odczytuj wyłącznie zakładkę run. Inny obraz: type=error, message.',
                'stash':'Odczytuj wyłącznie opis przedmiotu. Inny obraz: type=error, message.',
                'character':'Odczytuj wyłącznie opis przedmiotu. Inny obraz: type=error, message.',
                'merc':'Odczytuj wyłącznie opis przedmiotu. Inny obraz: type=error, message.'
            }.get(scan_mode, 'Rozpoznaj automatycznie: przedmiot, runy lub statystyki postaci.')],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0
            )
        )
        duration_ms = int((time.time() - t0) * 1000)
        
        prompt_tokens = 0
        candidates_tokens = 0
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            prompt_tokens = response.usage_metadata.prompt_token_count or 0
            candidates_tokens = response.usage_metadata.candidates_token_count or 0

        raw_text = response.text.strip()
        data = json.loads(raw_text)
        res_type = data.get("type", "item")

        # Rejestracja w bazie kosztów
        cost = record_api_call(
            endpoint=res_type,
            model=config.GEMINI_MODEL,
            prompt_tokens=prompt_tokens,
            candidates_tokens=candidates_tokens,
            duration_ms=duration_ms,
            status="success",
            notes=data.get("name") or ("Rune scan" if res_type == "rune_stash" else "")
        )

        if res_type == 'error':
            return dict(status='error',message=data.get('message','Obraz nie pasuje do wybranego trybu.'))
        expected = 'rune_stash' if scan_mode=='runes' else ('item' if scan_mode in ('stash','character','merc') else None)
        if expected and res_type != expected:
            return dict(status='error',message='Obraz nie pasuje do wybranego trybu skanowania.')
        if res_type == 'character':
            if not data.get('character',{}).get('name'):
                return dict(status='error',message='Nie rozpoznano nazwy postaci.')
            return dict(status='success',type='character',data=data['character'])

        # Obsługa zakładki run
        if res_type == "rune_stash":
            runes_dict = data.get("runes", {})
            update_res = update_runes(runes_dict, preview_filename=image_path.name)
            return {
                "status": "success",
                "type": "rune_stash",
                "runes": runes_dict,
                "summary": update_res,
                "tokens": {"prompt": prompt_tokens, "candidates": candidates_tokens},
                "cost_usd": cost,
                "duration_ms": duration_ms
            }

        # Obsługa przedmiotu
        rolls_eval = []
        catalog_id = None
        reqs = {
            "level_req": data.get("level_req"),
            "req_str": data.get("req_str"),
            "req_dex": data.get("req_dex")
        }

        cat_item = catalog_matcher.find_item(data.get("name", ""), data.get("name_en"))
        inferred_slot = data.get("slot") or ""
        if cat_item:
            catalog_id = cat_item.get("id")
            cat_slot = cat_item.get("slot", "misc")
            inferred_slot = cat_slot
            # Uzupełnienie wymagań z oficjalnego katalogu jeśli na tooltipie nie było
            if reqs["level_req"] is None and cat_item.get("level_req"):
                reqs["level_req"] = cat_item["level_req"]
            if reqs["req_str"] is None and cat_item.get("req_str"):
                reqs["req_str"] = cat_item["req_str"]
            if reqs["req_dex"] is None and cat_item.get("req_dex"):
                reqs["req_dex"] = cat_item["req_dex"]

            # Obliczenie widełek dla zmiennych statystyk
            rolls_eval = catalog_matcher.evaluate_item_rolls(
                cat_item,
                data.get("stats", []),
                data.get("rolls", {})
            )

        # Wymuszenie poprawnego slotu na podstawie bazy i słów kluczowych
        final_slot = detect_item_slot(
            name=data.get("name", ""),
            name_en=data.get("name_en", ""),
            base=data.get("base", ""),
            current_slot=inferred_slot,
            quality=data.get("quality", "")
        )
        data["slot"] = final_slot
        data["rolls_eval"] = rolls_eval
        data["requirements"] = reqs
        data["catalog_id"] = catalog_id

        return {
            "status": "success",
            "type": "item",
            "data": data,
            "tokens": {"prompt": prompt_tokens, "candidates": candidates_tokens},
            "cost_usd": cost,
            "duration_ms": duration_ms
        }

    except Exception as e:
        duration_ms = int((time.time() - t0) * 1000)
        record_api_call(
            endpoint="unknown",
            model=config.GEMINI_MODEL,
            prompt_tokens=0,
            candidates_tokens=0,
            duration_ms=duration_ms,
            status="error",
            notes=str(e)[:200]
        )
        return {
            "status": "error",
            "message": str(e),
            "duration_ms": duration_ms
        }

CHARACTER_PROMPT = """
Jesteś ekspertem Diablo II: Resurrected. Na przesłanym zrzucie ekranu znajduje się okno statystyk postaci ("POSTAĆ").
Przeanalizuj zrzut i zwróć DOKŁADNY obiekt JSON o strukturze:
{
  "name": "Nazwa postaci (np. KOSIOR)",
  "class_name": "Klasa postaci (Paladyn, Czarodziejka, Barbarzyńca, Amazonka, Zabójczyni, Nekromanta, Druid)",
  "level": 85,
  "experience": "np. 1.050.337.625 z 1.145.236.814",
  "strength": 109,
  "dexterity": 120,
  "vitality": 422,
  "energy": 46,
  "defense": 1358,
  "stamina": "800 / 800",
  "life": "1725 / 1725",
  "mana": "548 / 548",
  "fire_res": "76%",
  "light_res": "76%",
  "cold_res": "75%",
  "poison_res": "75%",
  "main_skill": "Pięść Niebios",
  "damage": "4188 - 4308"
}
Jeżeli jakieś pole jest niewidoczne, wstaw null.
Zwróć WYŁĄCZNIE czysty JSON.
"""

def process_character_stat_screen(image_path: Path) -> dict:
    client = get_client()
    t0 = time.time()
    try:
        img = Image.open(image_path)
    except Exception as e:
        return {"status": "error", "message": f"Błąd otwarcia pliku: {e}"}

    try:
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=[img, CHARACTER_PROMPT],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0
            )
        )
        duration_ms = int((time.time() - t0) * 1000)
        prompt_tokens = response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') and response.usage_metadata else 0
        candidates_tokens = response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') and response.usage_metadata else 0

        data = json.loads(response.text.strip())
        char_name = data.get("name")
        if not char_name or str(char_name).strip().lower() in ("none", "null", ""):
            duration_ms = int((time.time() - t0) * 1000)
            record_api_call(
                endpoint="character_screen",
                model=config.GEMINI_MODEL,
                prompt_tokens=prompt_tokens,
                candidates_tokens=candidates_tokens,
                duration_ms=duration_ms,
                status="error",
                notes="Nie wykryto nazwy postaci"
            )
            return {
                "status": "error",
                "message": "Nie wykryto okna postaci na zrzucie ekranu. Upewnij się, że w grze jest otwarte okno postaci (klawisz 'A' lub 'C') i spróbuj ponownie.",
                "duration_ms": duration_ms
            }

        cost = record_api_call(
            endpoint="character_screen",
            model=config.GEMINI_MODEL,
            prompt_tokens=prompt_tokens,
            candidates_tokens=candidates_tokens,
            duration_ms=duration_ms,
            status="success",
            notes=f"Postać: {data.get('name')} ({data.get('class_name')} Lvl {data.get('level')})"
        )
        return {
            "status": "success",
            "character": data,
            "data": data,
            "tokens": {"prompt": prompt_tokens, "candidates": candidates_tokens},
            "cost_usd": cost,
            "duration_ms": duration_ms
        }
    except Exception as e:
        duration_ms = int((time.time() - t0) * 1000)
        record_api_call(
            endpoint="character_screen",
            model=config.GEMINI_MODEL,
            prompt_tokens=0,
            candidates_tokens=0,
            duration_ms=duration_ms,
            status="error",
            notes=str(e)[:200]
        )
        return {"status": "error", "message": str(e), "duration_ms": duration_ms}


# Automatic recognition uses one model request, with the same character schema.
UNIFIED_PROMPT += '\nJEŚLI TO OKNO STATYSTYK POSTACI: zwróć {"type":"character","character":{...}}. Wewnątrz character zastosuj schemat:\n' + CHARACTER_PROMPT
