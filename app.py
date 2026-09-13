from flask import Flask, render_template, request, jsonify, send_from_directory
from pathlib import Path
import uuid
import config
import json
import time

from config import PREVIEWS_DIR, SCREENSHOTS_DIR, FLASK_PORT
from db import (
    get_trade_items, add_to_trade, remove_from_trade, update_trade_item, get_trade_count, is_in_trade,
    init_db, get_all_items, delete_item, insert_item,
    get_runes, get_api_summary, update_item_meta,
    get_distinct_locations, check_for_duplicate, calculate_file_hash,
    get_potential_duplicates, separate_duplicate, equip_item, unequip_item,
    get_character_equipment, get_all_characters, create_or_update_character,
    get_character, get_all_characters_detailed, delete_character
)
from capture import capture_service
from ai_processor import process_image, process_character_stat_screen
from runeword_calc import calculate_runewords_crafting
from translations import get_t, get_item_title

app = Flask(__name__)

CLASS_ICONS = {
    "paladyn": "/static/images/classes/paladin.jpg",
    "paladin": "/static/images/classes/paladin.jpg",
    "czarodziejka": "/static/images/classes/sorceress.jpg",
    "sorceress": "/static/images/classes/sorceress.jpg",
    "barbarzyńca": "/static/images/classes/barbarian.jpg",
    "barbarian": "/static/images/classes/barbarian.jpg",
    "nekromanta": "/static/images/classes/necromancer.jpg",
    "necromancer": "/static/images/classes/necromancer.jpg",
    "amazonka": "/static/images/classes/amazon.jpg",
    "amazon": "/static/images/classes/amazon.jpg",
    "druid": "/static/images/classes/druid.jpg",
    "zabójczyni": "/static/images/classes/assassin.jpg",
    "assassin": "/static/images/classes/assassin.jpg",
    "czarnoksiężnik": "/static/images/classes/warlock.jpg",
    "warlock": "/static/images/classes/warlock.jpg",
}


init_db()
from uber_features import init_features, character_report, trade_line, trade_details, save_trade_details, select_character
init_features()
from scan_history import init_history, calls
init_history()
from companion_routes import register
register(app)

def get_current_lang():
    lang = request.args.get('lang')
    if lang in ('pl', 'en'):
        return lang
    lang = request.cookies.get('app_lang')
    if lang in ('pl', 'en'):
        return lang
    try:
        from preferences import load as load_pref
        pref = load_pref()
        if pref.get('lang') in ('pl', 'en'):
            return pref.get('lang')
    except Exception:
        pass
    return 'pl'

@app.context_processor
def inject_translations():
    lang = get_current_lang()
    return {
        'lang': lang,
        't': get_t(lang),
        'item_title': lambda it: get_item_title(it, lang)
    }

@app.route("/api/set_language", methods=["GET", "POST"])
def api_set_language():
    data = request.get_json(silent=True) or {}
    new_lang = request.args.get("lang") or data.get("lang") or "pl"
    if new_lang not in ("pl", "en"):
        new_lang = "pl"
    try:
        from preferences import load as load_pref, save as save_pref
        pref = load_pref()
        pref["lang"] = new_lang
        save_pref(pref)
    except Exception:
        pass
    resp = jsonify({"success": True, "lang": new_lang})
    resp.set_cookie("app_lang", new_lang, max_age=365*24*3600)
    return resp

@app.route("/")
def index():
    tab = request.args.get("tab", "items").strip() # 'items', 'character', 'runes', 'duplicates', 'summary'
    view = request.args.get("view", "grid").strip() # 'grid' lub 'table'
    q = request.args.get("q", "").strip()
    quality = request.args.get("quality", "").strip()
    location = request.args.get("location", "").strip()
    
    # Lista postaci
    all_characters = get_all_characters_detailed()
    char_name = (request.args.get("name") or request.args.get("char") or "").strip()
    if not char_name and all_characters:
        char_name = select_character(capture_service.current_character)
    elif not char_name:
        char_name = capture_service.current_character or "Moja Postać"

    active_character = get_character(char_name)
    character_doll = get_character_equipment(char_name)

    for c in all_characters:
        cl = (c.get("class_name") or "paladyn").lower()
        c["class_icon"] = CLASS_ICONS.get(cl, "/static/images/database/armor/fs-korona--crn.png")

    if active_character:
        cl = (active_character.get("class_name") or "paladyn").lower()
        active_character["class_icon"] = CLASS_ICONS.get(cl, "/static/images/database/armor/fs-korona--crn.png")

    # Przedmioty w skrzyni (przedmioty nieschowane na postaciach!)
    stash_items = get_all_items(
        quality_filter=quality,
        search_query=q,
        location_filter=location,
        include_duplicates=False,
        exclude_character_gear=True
    )
    
    # Grupy duplikatów
    potential_duplicates = get_potential_duplicates()
    
    # Statystyki jakości przedmiotów w skrzyni
    item_stats = {
        "total": len(stash_items),
        "unique": sum(1 for it in stash_items if "unik" in (it.get("quality") or "").lower()),
        "set": sum(1 for it in stash_items if "zest" in (it.get("quality") or "").lower()),
        "runeword": sum(1 for it in stash_items if "rune" in (it.get("quality") or "").lower() or "słowo" in (it.get("quality") or "").lower()),
        "rare": sum(1 for it in stash_items if "rzad" in (it.get("quality") or "").lower() or "rare" in (it.get("quality") or "").lower()),
        "magic": sum(1 for it in stash_items if "mag" in (it.get("quality") or "").lower()),
        "duplicates": len(potential_duplicates),
    }
    
    # Runy i kalkulator słów
    runes_data = get_runes()
    runewords_calc = calculate_runewords_crafting()
    
    # Podsumowanie API i lokalizacje
    api_summary = get_api_summary()
    trade_items = get_trade_items()
    trade_count = len(trade_items)
    locations = get_distinct_locations()

    return render_template(
        "index.html",
        active_tab=tab,
        active_view=view,
        view_mode=view,
        items=stash_items,
        total=len(stash_items),
        item_stats=item_stats,
        potential_duplicates=potential_duplicates,
        duplicates_groups=potential_duplicates,
        dup_count=len(potential_duplicates),
        api_calls=calls(max(1,request.args.get('page',1,type=int))) if tab=='costs' else [],
        report=character_report(char_name),
        character_doll=character_doll,
        doll=character_doll,
        active_character=active_character,
        selected_character=active_character,
        current_char_name=char_name,
        all_characters=all_characters,
        runes_data=runes_data,
        runewords_calc=runewords_calc,
        runewords_crafting=runewords_calc,
        api_summary=api_summary,
        locations=locations,
        distinct_locations=locations,
        current_location=capture_service.current_location,
        scan_mode=capture_service.scan_mode,
        is_character_scanning=(capture_service.scan_mode == "character"),
        active_scan_character=capture_service.current_character,
        is_swap=capture_service.is_swap,
        q=q,
        search_query=q,
        quality=quality,
        quality_filter=quality,
        location=location,
        location_filter=location,
        hotkey_name=config.HOTKEY_NAME,
        ai_model=config.GEMINI_MODEL,
        service_running=capture_service.is_running,
        service_status=capture_service.last_status,
        trade_items=trade_items,
        trade_count=trade_count
    )

@app.route("/previews/<path:filename>")
def serve_preview(filename):
    return send_from_directory(PREVIEWS_DIR, filename)

@app.route("/screenshots/<path:filename>")
def serve_screenshot(filename):
    return send_from_directory(SCREENSHOTS_DIR, filename)


@app.route("/api/live_activity", methods=["GET"])
def api_live_activity():
    activity = getattr(capture_service, "last_activity", {
        "state": "idle",
        "message": "Gotowy. Oczekiwanie na klawisz F10 w grze...",
        "item_name": "",
        "timestamp": time.time(),
        "queue_count": 0
    })
    logs = getattr(capture_service, "activity_log", [])
    queue_count = getattr(capture_service, "queue_count", 0)
    return jsonify({
        "activity": activity,
        "logs": logs,
        "queue_count": queue_count,
        "is_running": capture_service.is_running,
        "status_text": capture_service.last_status,
        "scan_mode": capture_service.scan_mode,
        "character": capture_service.current_character,
        "is_swap": capture_service.is_swap,
        "total_captured": capture_service.total_captured, "hotkey": config.HOTKEY_NAME
    })

@app.route("/api/items", methods=["GET"])
def api_get_items():
    from db import get_all_items, get_db
    items = get_all_items(include_duplicates=False)
    with get_db() as con:
        trade_ids = {r["item_id"] for r in con.execute("SELECT item_id FROM trade_items").fetchall()}
    for it in items:
        it["is_in_trade"] = it["id"] in trade_ids
    return jsonify({"status": "success", "count": len(items), "items": items})

@app.route("/api/items/<item_id>", methods=["GET"])
def api_get_single_item(item_id):
    from db import get_item
    it = get_item(item_id)
    if not it:
        return jsonify({"error": "Przedmiot nie istnieje"}), 404
    return jsonify({"item": it})

@app.route("/api/status")
def api_status():
    items = get_all_items(include_duplicates=False, exclude_character_gear=True)
    runes_data = get_runes()
    api_summary = get_api_summary()
    dups = get_potential_duplicates()
    chars = get_all_characters_detailed()
    return jsonify({
        "is_running": capture_service.is_running,
        "status_text": capture_service.last_status,
        "current_location": capture_service.current_location,
        "scan_mode": capture_service.scan_mode,
        "current_character": capture_service.current_character,
        "is_swap": capture_service.is_swap,
        "total_items": len(items),
        "total_duplicates": len(dups),
        "total_characters": len(chars),
        "total_runes": runes_data["total_count"],
        "total_cost_usd": api_summary["total_cost_usd"],
        "total_cost_pln": api_summary["total_cost_pln"],
        "total_api_calls": api_summary["total_calls"]
    })

@app.route("/api/session/settings", methods=["GET", "POST"])
def api_session_settings():
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        if "location" in payload:
            capture_service.set_location(payload.get("location", ""))
        if "scan_mode" in payload:
            capture_service.set_scan_mode(payload.get("scan_mode", "normal"))
        if "character" in payload:
            capture_service.set_character(payload.get("character", "Moja Postać"))
        if "is_swap" in payload:
            capture_service.set_swap(payload.get("is_swap", False))

    return jsonify({
        "location": capture_service.current_location,
        "scan_mode": capture_service.scan_mode,
        "character": capture_service.current_character,
        "is_swap": capture_service.is_swap
    })

# Endpoints: kreator postaci i statystyki

@app.route("/api/character/scan_stat_screen", methods=["POST"])
def api_scan_stat_screen():
    if "file" not in request.files:
        return jsonify({"error": "Brak pliku ze zrzutem ekranu"}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Pusty plik"}), 400

    uid = uuid.uuid4().hex
    filename = f"char_stat_{uid}.png"
    target_path = PREVIEWS_DIR / filename
    file.save(target_path)

    res = process_character_stat_screen(target_path)
    if res.get("status") == "success":
        res["screenshot_filename"] = filename
    return jsonify(res)

@app.route("/api/character/save", methods=["POST"])
def api_save_character():
    payload = request.get_json(silent=True) or {}
    if not payload.get("name"):
        return jsonify({"error": "Brak nazwy postaci"}), 400
    saved = create_or_update_character(payload)
    capture_service.set_character(saved["name"])
    return jsonify({"success": True, "character": saved})

@app.route("/api/character/<name>", methods=["GET"])
def api_get_character_info(name):
    char = get_character(name)
    doll = get_character_equipment(name)
    return jsonify({"character": char, "doll": doll})

@app.route("/api/character/<name>", methods=["DELETE"])
def api_delete_character(name):
    delete_character(name)
    return jsonify({"success": True})

@app.route("/api/characters/all", methods=["GET"])
def api_get_all_characters():
    return jsonify(get_all_characters_detailed())

@app.route("/api/character/wizard_listen", methods=["POST"])
def api_wizard_listen():
    capture_service.set_scan_mode("stat_screen")
    capture_service.last_stat_scan = None
    if not capture_service.is_running:
        capture_service.start()
    return jsonify({"success": True, "status": "listening", "service_status": capture_service.last_status})

@app.route("/api/character/wizard_poll", methods=["GET"])
def api_wizard_poll():
    ready = capture_service.last_stat_scan is not None
    return jsonify({
        "ready": ready,
        "data": capture_service.last_stat_scan,
        "scan_mode": capture_service.scan_mode,
        "service_running": capture_service.is_running
    })

@app.route("/api/character/stop_gear_scan", methods=["POST"])
def api_stop_gear_scan():
    capture_service.set_scan_mode("normal")
    return jsonify({"success": True, "scan_mode": "normal"})

@app.route("/api/character/start_gear_scan", methods=["POST"])
def api_start_gear_scan():
    payload = request.get_json(silent=True) or {}
    char_name = payload.get("character_name", "").strip()
    if not char_name:
        return jsonify({"error": "Brak nazwy postaci"}), 400
    capture_service.set_scan_mode("character")
    capture_service.set_character(char_name)
    return jsonify({"success": True, "character": char_name, "scan_mode": "character"})

# Endpoints: duplikaty i skrzynia

@app.route("/api/duplicates", methods=["GET"])
def api_get_duplicates():
    return jsonify(get_potential_duplicates())

@app.route("/api/duplicates/<item_id>/separate", methods=["POST"])
def api_separate_duplicate(item_id):
    separate_duplicate(item_id)
    return jsonify({"success": True})

@app.route("/api/character/equip", methods=["POST"])
def api_equip_item():
    payload = request.get_json(silent=True) or {}
    item_id = payload.get("item_id")
    char_name = payload.get("character_name")
    slot = payload.get("slot")
    if item_id and char_name and slot:
        equip_item(item_id, char_name, slot)
        return jsonify({"success": True})
    return jsonify({"error": "Brakujące parametry"}), 400

@app.route("/api/character/unequip", methods=["POST"])
def api_unequip_item():
    payload = request.get_json(silent=True) or {}
    item_id = payload.get("item_id")
    if item_id:
        unequip_item(item_id)
        return jsonify({"success": True})
    return jsonify({"error": "Brakujące parametry"}), 400

@app.route("/api/items/<item_id>/meta", methods=["POST"])
def api_update_item_meta(item_id):
    payload = request.get_json(silent=True) or {}
    location = payload.get("location")
    notes = payload.get("notes")
    is_duplicate = payload.get("is_duplicate")
    char_name = payload.get("character_name")
    char_slot = payload.get("character_slot")
    update_item_meta(item_id, location=location, notes=notes, is_duplicate=is_duplicate, character_name=char_name, character_slot=char_slot)
    return jsonify({"success": True})

@app.route("/api/runewords/calc")
def api_runewords_calc():
    return jsonify(calculate_runewords_crafting())

@app.route("/api/service/start", methods=["POST"])
def api_start_service():
    capture_service.start()
    return jsonify({"success": True, "status": capture_service.last_status})

@app.route("/api/service/stop", methods=["POST"])
def api_stop_service():
    capture_service.stop()
    return jsonify({"success": True, "status": capture_service.last_status})

@app.route("/api/items/<item_id>", methods=["DELETE"])
def api_delete_item(item_id):
    delete_item(item_id)
    return jsonify({"success": True})

@app.route("/api/upload", methods=["POST"])
def api_upload_image():
    if "file" not in request.files:
        return jsonify({"error": "Brak pliku w żądaniu"}), 400
        
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Pusta nazwa pliku"}), 400

    target_loc = request.form.get("location", capture_service.current_location).strip()
    is_char_mode = request.form.get("scan_mode", capture_service.scan_mode) == "character"
    char_name = request.form.get("character", capture_service.current_character).strip()
    is_swap = request.form.get("is_swap", "0") in ("1", "true", "True")

    uid = uuid.uuid4().hex
    preview_name = f"upload_{uid}.png"
    target_path = PREVIEWS_DIR / preview_name
    file.save(target_path)

    img_hash = calculate_file_hash(target_path)
    res = process_image(target_path)
    
    if res.get("status") == "success":
        res_type = res.get("type", "item")
        if res_type == "item":
            data = res.get("data", {})
            reqs = data.get("requirements") or {}
            name = data.get("name", "Nieznany")
            quality = data.get("quality", "normalny")
            stats = data.get("stats", [])
            detected_slot = data.get("slot") or "misc"

            if is_char_mode and char_name:
                if detected_slot == "weapon":
                    assigned_slot = "weapon2" if is_swap else "weapon1"
                elif detected_slot == "shield":
                    assigned_slot = "shield2" if is_swap else "shield1"
                elif detected_slot == "ring":
                    eq = get_character_equipment(char_name)
                    assigned_slot = "ring2" if eq.get("ring1") else "ring1"
                elif detected_slot in ("head", "armor", "gloves", "belt", "boots", "amulet"):
                    assigned_slot = detected_slot
                elif detected_slot == "charm":
                    assigned_slot = "charms"
                else:
                    assigned_slot = "charms"

                final_char = char_name
                final_slot = assigned_slot
                final_loc = f"Postać: {char_name}"
                is_dup = 0
                dup_of_id = ""
            else:
                final_char = ""
                final_slot = ""
                final_loc = target_loc
                is_dup, dup_of_id, orig_date = check_for_duplicate(name, quality, stats, img_hash)

            item_record = {
                "id": uid,
                "name": name,
                "name_en": data.get("name_en", ""),
                "base": data.get("base", ""),
                "quality": quality,
                "defense": data.get("defense"),
                "damage": data.get("damage"),
                "level_req": reqs.get("level_req") or data.get("level_req"),
                "req_str": reqs.get("req_str") or data.get("req_str"),
                "req_dex": reqs.get("req_dex") or data.get("req_dex"),
                "sockets": data.get("sockets"),
                "stats": stats,
                "rolls_eval": data.get("rolls_eval", []),
                "requirements": reqs,
                "catalog_id": data.get("catalog_id", ""),
                "preview_filename": preview_name,
                "screenshot_filename": "",
                "location": final_loc,
                "notes": "",
                "is_duplicate": 1 if is_dup else 0,
                "duplicate_of": dup_of_id,
                "image_hash": img_hash,
                "character_name": final_char,
                "character_slot": final_slot
            }
            insert_item(item_record)
            res["item_id"] = uid
            res["is_duplicate"] = is_dup
    return jsonify(res)


def generate_trade_export_text(trade_items: list[dict], lang: str = "pl", include_rolls: bool = True, include_base: bool = True, include_sockets: bool = True, include_price: bool = True, include_notes: bool = True) -> str:
    """Generuje sformatowany tekst listy sprzedaży (dla Discorda, forum, handlu itp.)."""
    is_pl = (lang.lower() == "pl")
    
    header = "=== LISTA PRZEDMIOTÓW NA SPRZEDAŻ (D2R) ===" if is_pl else "=== D2R TRADE / SALE LIST ==="
    lines = [header, ""]
    
    if not trade_items:
        lines.append("Brak przedmiotów na liście sprzedaży." if is_pl else "No items on the trade list.")
        return "\n".join(lines)
        
    for i, it in enumerate(trade_items, 1):
        name_pl = it.get("name") or "Przedmiot"
        name_en = it.get("name_en") or ""
        quality = (it.get("quality") or "").lower()
        
        # Nazwa w wybranym języku
        if is_pl:
            title = name_pl
            if name_en and name_en.lower() != name_pl.lower():
                title += f" / {name_en}"
        else:
            title = name_en or name_pl
            if name_pl and name_pl.lower() != (name_en or "").lower():
                title += f" ({name_pl})"
                
        # Typ jakości
        q_tag = ""
        if "rune" in quality or "słowo" in quality:
            q_tag = " [Słowo runiczne]" if is_pl else " [Runeword]"
        elif "unik" in quality:
            q_tag = " [Unikalny]" if is_pl else " [Unique]"
        elif "zest" in quality or "set" in quality:
            q_tag = " [Zestaw]" if is_pl else " [Set]"
        elif "rzad" in quality or "rare" in quality:
            q_tag = " [Rzadki]" if is_pl else " [Rare]"
        elif "mag" in quality:
            q_tag = " [Magiczny]" if is_pl else " [Magic]"
            
        lines.append(f"{i}. {title}{q_tag}")
        
        # Baza (zwłaszcza dla słów runicznych lub gdy różna od nazwy)
        base = it.get("base") or ""
        is_runeword = ("rune" in quality or "słowo" in quality)
        if base and (is_runeword or include_base):
            label_base = "Baza" if is_pl else "Base"
            lines.append(f"   • {label_base}: {base}")
            
        # Obrona / Obrażenia jeśli istotne
        def_val = it.get("defense")
        dmg_val = it.get("damage")
        if def_val:
            label_def = "Obrona" if is_pl else "Defense"
            lines.append(f"   • {label_def}: {def_val}")
        if dmg_val:
            label_dmg = "Obrażenia" if is_pl else "Damage"
            lines.append(f"   • {label_dmg}: {dmg_val}")
            
        # Gniazda (sockets)
        sockets = it.get("sockets")
        if include_sockets and sockets:
            label_soc = f"{sockets} gniazda" if is_pl else f"{sockets} sockets"
            lines.append(f"   • Gniazda: {label_soc}" if is_pl else f"   • Sockets: {label_soc}")
            
        # Zmienne statystyki (rolls)
        if include_rolls:
            rolls = it.get("rolls_eval") or []
            if rolls:
                roll_texts = []
                for r in rolls:
                    lbl = r.get("label") or r.get("property")
                    act = r.get("actual")
                    mi = r.get("min")
                    ma = r.get("max")
                    rat = r.get("rating") or ""
                    rat_suffix = f" ({rat})" if rat else ""
                    if mi is not None and ma is not None and mi != ma:
                        roll_texts.append(f"{lbl}: {act} (zakres: {mi}-{ma}){rat_suffix}")
                    else:
                        roll_texts.append(f"{lbl}: {act}{rat_suffix}")
                label_rolls = "Zmienne" if is_pl else "Rolls"
                lines.append(f"   • {label_rolls}: {', '.join(roll_texts)}")
            elif it.get("stats"):
                # Jeśli brak eval, wypisz kluczowe statystyki
                key_stats = [s for s in it.get("stats", [])[:4]]
                if key_stats:
                    label_stats = "Statystyki" if is_pl else "Key Stats"
                    lines.append(f"   • {label_stats}: {'; '.join(key_stats)}")
                    
        # Cena
        if include_price:
            price = it.get("trade_price") or ("Czekam na ofertę" if is_pl else "Offer")
            label_price = "Cena" if is_pl else "Price"
            lines.append(f"   • {label_price}: {price}")
            
        # Notatka własna
        if include_notes and it.get("trade_notes"):
            label_notes = "Notatka" if is_pl else "Note"
            lines.append(f"   • {label_notes}: {it.get('trade_notes')}")
            
        lines.append("") # Pusta linia odstępu
        
    return "\n".join(lines).strip()

@app.route("/api/trade/list", methods=["GET"])
def api_trade_list():
    items = get_trade_items()
    return jsonify({"status": "success", "count": len(items), "items": items})

@app.route("/api/trade/add", methods=["POST"])
def api_trade_add():
    data = request.get_json(force=True, silent=True) or {}
    item_id = data.get("item_id")
    price = data.get("price") or "Czekam na ofertę"
    notes = data.get("notes") or ""
    if not item_id:
        return jsonify({"status": "error", "message": "Brak item_id"}), 400
    add_to_trade(item_id, price, notes)
    return jsonify({"status": "success", "trade_count": get_trade_count()})

@app.route("/api/trade/remove", methods=["POST"])
def api_trade_remove():
    data = request.get_json(force=True, silent=True) or {}
    item_id = data.get("item_id")
    if not item_id:
        return jsonify({"status": "error", "message": "Brak item_id"}), 400
    remove_from_trade(item_id)
    return jsonify({"status": "success", "trade_count": get_trade_count()})

@app.route("/api/trade/update", methods=["POST"])
def api_trade_update():
    data = request.get_json(force=True, silent=True) or {}
    item_id = data.get("item_id")
    price = data.get("price")
    notes = data.get("notes")
    if not item_id:
        return jsonify({"status": "error", "message": "Brak item_id"}), 400
    update_trade_item(item_id, price, notes)
    return jsonify({"status": "success"})

@app.route("/api/trade/export", methods=["POST", "GET"])
def api_trade_export():
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
    else:
        data = request.args.to_dict()
        
    lang = data.get("lang", "pl").lower()
    include_rolls = str(data.get("include_rolls", "true")).lower() in ("true", "1", "yes")
    include_base = str(data.get("include_base", "true")).lower() in ("true", "1", "yes")
    include_sockets = str(data.get("include_sockets", "true")).lower() in ("true", "1", "yes")
    include_price = str(data.get("include_price", "true")).lower() in ("true", "1", "yes")
    include_notes = str(data.get("include_notes", "true")).lower() in ("true", "1", "yes")
    use_shorthand = str(data.get("use_shorthand", "false")).lower() in ("true", "1", "yes")

    items = get_trade_items()
    text = '\n'.join(trade_line(it, lang, include_rolls, include_base, include_sockets, include_price, include_notes, use_shorthand=use_shorthand) for it in items)
    return jsonify({"status": "success", "text": text, "count": len(items)})

@app.route("/api/trade/online_sync", methods=["POST"])
def api_trade_online_sync():
    import urllib.request
    import urllib.error
    data = request.get_json(force=True, silent=True) or {}
    server_url = (data.get("server_url") or "http://localhost:5050").rstrip("/")
    api_token = data.get("api_token") or ""
    username = data.get("username") or ""
    password = data.get("password") or ""
    realm_sc_hc = data.get("realm_sc_hc") or "sc"
    realm_ladder = data.get("realm_ladder") or "ladder"
    realm_expansion = data.get("realm_expansion") or "lod"
    item_ids = set(data.get("item_ids") or [])

    from db import get_trade_items
    all_trade = get_trade_items()
    selected_items = [it for it in all_trade if it["id"] in item_ids] if item_ids else all_trade

    if not selected_items:
        return jsonify({"status": "error", "error": "Brak zaznaczonych przedmiotów do opublikowania."}), 400

    payload = {
        "api_token": api_token,
        "username": username,
        "password": password,
        "realm_sc_hc": realm_sc_hc,
        "realm_ladder": realm_ladder,
        "realm_expansion": realm_expansion,
        "items": selected_items
    }

    try:
        req = urllib.request.Request(
            f"{server_url}/api/marketplace/publish",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "X-API-Key": api_token},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            resp_data["server_url"] = server_url
            return jsonify(resp_data)
    except urllib.error.HTTPError as he:
        try:
            err_msg = json.loads(he.read().decode("utf-8")).get("error", str(he))
        except Exception:
            err_msg = str(he)
        return jsonify({"status": "error", "error": f"Błąd serwera giełdy ({he.code}): {err_msg}"}), 400
    except Exception as e:
        return jsonify({"status": "error", "error": f"Nie udało się połączyć z giełdą online ({server_url}): {e}"}), 500

@app.route('/api/companion/open', methods=['POST'])
def open_companion():
    if not request.is_json or (request.headers.get('Origin') and request.headers['Origin'] != request.host_url.rstrip('/')):
        return jsonify(error='Niedozwolone żądanie'), 403
    if not app.config.get('COMPANION_AVAILABLE'):
        return jsonify(error='Uruchom start.bat, aby otworzyć aplikację towarzyszącą.'), 503
    from desktop_companion import show_requested
    show_requested.set()
    return jsonify(success=True)

@app.route('/api/trade/details/<item_id>', methods=['GET','POST'])
def uber_trade_details(item_id):
    from db import get_item
    item = get_item(item_id)
    if not item:
        return jsonify(error='Nie znaleziono przedmiotu'), 404
    if request.method == 'POST':
        if not request.is_json:
            return jsonify(error='Wymagany JSON'), 400
        save_trade_details(item, request.get_json())
    return jsonify(trade_details(item))

if __name__ == "__main__":
    from desktop_companion import run
    run(app)