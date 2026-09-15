import sqlite3
import json
import uuid
import hashlib
from pathlib import Path
import config
from config import DB_PATH

ALL_RUNES = [
    (1, "El", "low"), (2, "Eld", "low"), (3, "Tir", "low"), (4, "Nef", "low"),
    (5, "Eth", "low"), (6, "Ith", "low"), (7, "Tal", "low"), (8, "Ral", "low"),
    (9, "Ort", "low"), (10, "Thul", "low"), (11, "Amn", "low"), (12, "Sol", "low"),
    (13, "Shael", "low"), (14, "Dol", "low"), (15, "Hel", "low"), (16, "Io", "low"),
    (17, "Lum", "mid"), (18, "Ko", "mid"), (19, "Fal", "mid"), (20, "Lem", "mid"),
    (21, "Pul", "mid"), (22, "Um", "mid"), (23, "Mal", "mid"), (24, "Ist", "mid"),
    (25, "Gul", "mid"), (26, "Vex", "high"), (27, "Ohm", "high"), (28, "Lo", "high"),
    (29, "Sur", "high"), (30, "Ber", "high"), (31, "Jah", "high"), (32, "Cham", "high"),
    (33, "Zod", "high")
]

USD_TO_PLN = 4.05
PROMPT_COST_PER_M = 0.075
CANDIDATE_COST_PER_M = 0.30

def get_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with get_db() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            name_en TEXT,
            base TEXT,
            quality TEXT,
            defense INTEGER,
            damage TEXT,
            level_req INTEGER,
            req_str INTEGER,
            req_dex INTEGER,
            sockets INTEGER,
            stats_json TEXT,
            rolls_eval_json TEXT,
            requirements_json TEXT,
            catalog_id TEXT,
            preview_filename TEXT,
            screenshot_filename TEXT,
            location TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            is_duplicate INTEGER DEFAULT 0,
            duplicate_of TEXT DEFAULT '',
            image_hash TEXT DEFAULT '',
            character_name TEXT DEFAULT '',
            character_slot TEXT DEFAULT '',
            image_path TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
        """)

        cols = [r[1] for r in con.execute("PRAGMA table_info(items)").fetchall()]
        for col_name, col_type in [
            ("name_en", "TEXT"),
            ("rolls_eval_json", "TEXT"),
            ("requirements_json", "TEXT"),
            ("catalog_id", "TEXT"),
            ("location", "TEXT DEFAULT ''"),
            ("notes", "TEXT DEFAULT ''"),
            ("is_duplicate", "INTEGER DEFAULT 0"),
            ("duplicate_of", "TEXT DEFAULT ''"),
            ("image_hash", "TEXT DEFAULT ''"),
            ("character_name", "TEXT DEFAULT ''"),
            ("character_slot", "TEXT DEFAULT ''"),
            ("market_value", "TEXT DEFAULT ''"),
            ("stat_priority", "TEXT DEFAULT ''"),
            ("build_notes", "TEXT DEFAULT ''")
        ]:
            if col_name not in cols:
                con.execute(f"ALTER TABLE items ADD COLUMN {col_name} {col_type}")

        con.execute("""
        CREATE TABLE IF NOT EXISTS characters (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            class_name TEXT NOT NULL,
            level INTEGER DEFAULT 1,
            experience TEXT DEFAULT '',
            strength INTEGER DEFAULT 0,
            dexterity INTEGER DEFAULT 0,
            vitality INTEGER DEFAULT 0,
            energy INTEGER DEFAULT 0,
            defense INTEGER DEFAULT 0,
            stamina TEXT DEFAULT '',
            life TEXT DEFAULT '',
            mana TEXT DEFAULT '',
            fire_res TEXT DEFAULT '',
            light_res TEXT DEFAULT '',
            cold_res TEXT DEFAULT '',
            poison_res TEXT DEFAULT '',
            main_skill TEXT DEFAULT '',
            damage TEXT DEFAULT '',
            screenshot_filename TEXT DEFAULT '',
            updated_at TEXT DEFAULT (datetime('now', 'localtime')),
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
        """)

        con.execute("""
        CREATE TABLE IF NOT EXISTS api_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT (datetime('now', 'localtime')),
            endpoint TEXT NOT NULL,
            model TEXT NOT NULL,
            prompt_tokens INTEGER DEFAULT 0,
            candidates_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            cost_usd REAL DEFAULT 0.0,
            duration_ms INTEGER DEFAULT 0,
            status TEXT DEFAULT 'success',
            notes TEXT
        )
        """)

        con.execute("""
        CREATE TABLE IF NOT EXISTS runes (
            rune_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            tier TEXT NOT NULL,
            count INTEGER DEFAULT 0,
            updated_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
        """)

        con.execute("""
        CREATE TABLE IF NOT EXISTS trade_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
        """)
        con.execute("INSERT OR IGNORE INTO trade_lists (name) VALUES ('Główna')")

        # Bezpieczna migracja struktury trade_items
        table_sql = con.execute("SELECT sql FROM sqlite_master WHERE name = 'trade_items'").fetchone()
        if not table_sql:
            con.execute("""
            CREATE TABLE IF NOT EXISTS trade_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT NOT NULL,
                list_name TEXT DEFAULT 'Główna',
                price TEXT DEFAULT 'Czekam na ofertę',
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
                UNIQUE(item_id, list_name)
            )
            """)
        elif "UNIQUE(item_id, list_name)" not in table_sql[0]:
            con.execute("""
            CREATE TABLE IF NOT EXISTS trade_items_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT NOT NULL,
                list_name TEXT DEFAULT 'Główna',
                price TEXT DEFAULT 'Czekam na ofertę',
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
                UNIQUE(item_id, list_name)
            )
            """)
            cols = [r[1] for r in con.execute("PRAGMA table_info(trade_items)").fetchall()]
            if "list_name" in cols:
                con.execute("""
                INSERT OR IGNORE INTO trade_items_new (id, item_id, list_name, price, notes, created_at)
                SELECT id, item_id, COALESCE(NULLIF(list_name, ''), 'Główna'), price, notes, created_at FROM trade_items
                """)
            else:
                con.execute("""
                INSERT OR IGNORE INTO trade_items_new (id, item_id, list_name, price, notes, created_at)
                SELECT id, item_id, 'Główna', price, notes, created_at FROM trade_items
                """)
            con.execute("DROP TABLE trade_items")
            con.execute("ALTER TABLE trade_items_new RENAME TO trade_items")

        con.execute("""
        CREATE TABLE IF NOT EXISTS rune_scans (
            id TEXT PRIMARY KEY,
            timestamp TEXT DEFAULT (datetime('now', 'localtime')),
            total_runes INTEGER DEFAULT 0,
            runes_json TEXT,
            preview_filename TEXT
        )
        """)

        for r_id, r_name, r_tier in ALL_RUNES:
            con.execute("""
            INSERT OR IGNORE INTO runes (rune_id, name, tier, count)
            VALUES (?, ?, ?, 0)
            """, (r_id, r_name, r_tier))

        con.commit()

def calculate_file_hash(filepath: Path) -> str:
    if not filepath.exists():
        return ""
    try:
        with open(filepath, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return ""

def check_for_duplicate(name: str, quality: str, stats: list, image_hash: str) -> tuple[bool, str, str]:
    if not name:
        return False, "", ""
        
    with get_db() as con:
        if image_hash:
            row = con.execute("SELECT id, created_at FROM items WHERE image_hash = ? AND (character_name IS NULL OR character_name = '') LIMIT 1", (image_hash,)).fetchone()
            if row:
                return True, row["id"], row["created_at"]

        stats_str = json.dumps(stats or [], ensure_ascii=False)
        row = con.execute("""
            SELECT id, created_at FROM items
            WHERE LOWER(name) = LOWER(?) AND LOWER(quality) = LOWER(?) AND stats_json = ?
            AND (character_name IS NULL OR character_name = '')
            LIMIT 1
        """, (name, quality, stats_str)).fetchone()
        if row:
            return True, row["id"], row["created_at"]

    return False, "", ""

def record_api_call(endpoint: str, model: str, prompt_tokens: int, candidates_tokens: int, duration_ms: int, status="success", notes="", request_id=""):
    total_tokens = (prompt_tokens or 0) + (candidates_tokens or 0)
    cost = ((prompt_tokens or 0) * PROMPT_COST_PER_M / 1_000_000.0) +            ((candidates_tokens or 0) * CANDIDATE_COST_PER_M / 1_000_000.0)

    with get_db() as con:
        con.execute("""
        INSERT INTO api_usage (
            endpoint, model, prompt_tokens, candidates_tokens, total_tokens,
            cost_usd, duration_ms, status, notes, request_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (endpoint, model, prompt_tokens, candidates_tokens, total_tokens, cost, duration_ms, status, notes, request_id))
        con.commit()
    return cost

def get_api_summary():
    with get_db() as con:
        row = con.execute("""
        SELECT 
            COUNT(*) as total_calls,
            SUM(prompt_tokens) as total_prompt_tokens,
            SUM(candidates_tokens) as total_candidates_tokens,
            SUM(total_tokens) as total_tokens,
            SUM(cost_usd) as total_cost_usd,
            AVG(duration_ms) as avg_duration_ms
        FROM api_usage
        """).fetchone()
        
        summary = dict(row) if row else {}
        summary["total_cost_pln"] = round((summary.get("total_cost_usd") or 0.0) * USD_TO_PLN, 4)
        summary["total_cost_usd"] = round(summary.get("total_cost_usd") or 0.0, 5)
        summary["avg_duration_ms"] = int(round(summary.get("avg_duration_ms") or 0))

        recent_rows = con.execute("""
        SELECT * FROM api_usage ORDER BY id DESC LIMIT 25
        """).fetchall()
        summary["recent_calls"] = [dict(r) for r in recent_rows]
        return summary

def update_runes(runes_dict: dict, preview_filename: str = None) -> dict:
    total_count = 0
    with get_db() as con:
        for r_id, r_name, _ in ALL_RUNES:
            cnt = int(runes_dict.get(r_name, 0))
            con.execute("""
            UPDATE runes 
            SET count = ?, updated_at = datetime('now', 'localtime')
            WHERE name = ?
            """, (cnt, r_name))
            total_count += cnt
            
        scan_id = uuid.uuid4().hex
        con.execute("""
        INSERT INTO rune_scans (id, total_runes, runes_json, preview_filename)
        VALUES (?, ?, ?, ?)
        """, (scan_id, total_count, json.dumps(runes_dict, ensure_ascii=False), preview_filename or ""))
        con.commit()

    return {"total_runes": total_count, "scan_id": scan_id}

def get_runes():
    with get_db() as con:
        rows = con.execute("SELECT * FROM runes ORDER BY rune_id ASC").fetchall()
        runes_list = [dict(r) for r in rows]
        
        for r in runes_list:
            r_num = r["rune_id"]
            r_name = r["name"]
            r["icon"] = f"/static/images/runes/runa-{r_name.lower()}--r{r_num:02d}.png"

        low_count = sum(r["count"] for r in runes_list if r["tier"] == "low")
        mid_count = sum(r["count"] for r in runes_list if r["tier"] == "mid")
        high_count = sum(r["count"] for r in runes_list if r["tier"] == "high")
        total_count = low_count + mid_count + high_count
        
        return {
            "runes": runes_list,
            "total_count": total_count,
            "low_count": low_count,
            "mid_count": mid_count,
            "high_count": high_count
        }


CATALOG_DB_PATH = config.DATA_DIR / 'catalog.sqlite'
if not CATALOG_DB_PATH.exists() and hasattr(config, 'BUNDLE_DIR'):
    CATALOG_DB_PATH = config.BUNDLE_DIR / 'data' / 'catalog.sqlite'

# Kanoniczna baza grafik Diablo 2 dla gwarantowanego dopasowania bez klucza
CANONICAL_SPRITES = {
    # Klejnoty (Jewels)
    "klejnot": "/static/images/database/gem/klejnot--jew.png",
    "klejnoty": "/static/images/database/gem/klejnot--jew.png",
    "jewel": "/static/images/database/gem/klejnot--jew.png",
    "jewels": "/static/images/database/gem/klejnot--jew.png",
    "widok teczy": "/static/images/database/gem/klejnot--jew.png",
    "widok tęczy": "/static/images/database/gem/klejnot--jew.png",
    "rainbow facet": "/static/images/database/gem/klejnot--jew.png",

    # Buty (Boots)
    "lekkie płytowe buty": "/static/images/database/armor/nl-lekkie-p-ytowe-buty--tbt.png",
    "lekkie plytowe buty": "/static/images/database/armor/nl-lekkie-p-ytowe-buty--tbt.png",
    "light plate boots": "/static/images/database/armor/nl-lekkie-p-ytowe-buty--tbt.png",
    "light plated boots": "/static/images/database/armor/nl-lekkie-p-ytowe-buty--tbt.png",
    "bitewne buty": "/static/images/database/armor/nl-lekkie-p-ytowe-buty--tbt.png",
    "battle boots": "/static/images/database/armor/nl-lekkie-p-ytowe-buty--tbt.png",
    "lustrzane buty": "/static/images/database/armor/nl-lekkie-p-ytowe-buty--tbt.png",
    "mirrored boots": "/static/images/database/armor/nl-lekkie-p-ytowe-buty--tbt.png",
    "buty": "/static/images/database/armor/nl-buty--lbt.png",
    "boots": "/static/images/database/armor/nl-buty--lbt.png",
    "skórzane buty": "/static/images/database/armor/nl-buty--lbt.png",
    "skorzane buty": "/static/images/database/armor/nl-buty--lbt.png",
    "leather boots": "/static/images/database/armor/nl-buty--lbt.png",
    "demoniczne buty": "/static/images/database/armor/nl-buty--lbt.png",
    "demonhide boots": "/static/images/database/armor/nl-buty--lbt.png",
    "gadzie buty": "/static/images/database/armor/nl-buty--lbt.png",
    "wyrmhide boots": "/static/images/database/armor/nl-buty--lbt.png",
    "ciężkie buty": "/static/images/database/armor/nl-ci-kie-buty--vbt.png",
    "ciezkie buty": "/static/images/database/armor/nl-ci-kie-buty--vbt.png",
    "heavy boots": "/static/images/database/armor/nl-ci-kie-buty--vbt.png",
    "rekinie buty": "/static/images/database/armor/nl-ci-kie-buty--vbt.png",
    "sharkskin boots": "/static/images/database/armor/nl-ci-kie-buty--vbt.png",
    "skarabeuszowe buty": "/static/images/database/armor/nl-ci-kie-buty--vbt.png",
    "scarabshell boots": "/static/images/database/armor/nl-ci-kie-buty--vbt.png",
    "kolczugowe buty": "/static/images/database/armor/nl-kolczugowe-buty--mbt.png",
    "chain boots": "/static/images/database/armor/nl-kolczugowe-buty--mbt.png",
    "kolcze buty": "/static/images/database/armor/nl-kolczugowe-buty--mbt.png",
    "mesh boots": "/static/images/database/armor/nl-kolczugowe-buty--mbt.png",
    "kościane buty": "/static/images/database/armor/nl-kolczugowe-buty--mbt.png",
    "kosciane buty": "/static/images/database/armor/nl-kolczugowe-buty--mbt.png",
    "boneweave boots": "/static/images/database/armor/nl-kolczugowe-buty--mbt.png",
    "nagolenice": "/static/images/database/armor/nl-nagolenice--hbt.png",
    "greaves": "/static/images/database/armor/nl-nagolenice--hbt.png",
    "bojowe buty": "/static/images/database/armor/nl-nagolenice--hbt.png",
    "war boots": "/static/images/database/armor/nl-nagolenice--hbt.png",
    "myrmidońskie nagolenice": "/static/images/database/armor/nl-nagolenice--hbt.png",
    "myrmidonskie nagolenice": "/static/images/database/armor/nl-nagolenice--hbt.png",
    "myrmidon greaves": "/static/images/database/armor/nl-nagolenice--hbt.png",

    # Tarcze (Shields)
    "święta rondela": "/static/images/database/armor/fs-rodela--pa2.png",
    "swieta rondela": "/static/images/database/armor/fs-rodela--pa2.png",
    "święta rõdela": "/static/images/database/armor/fs-rodela--pa2.png",
    "sacred rondache": "/static/images/database/armor/fs-rodela--pa2.png",
    "rodela": "/static/images/database/armor/fs-rodela--pa2.png",
    "rondela": "/static/images/database/armor/fs-rodela--pa2.png",
    "rondache": "/static/images/database/armor/fs-rodela--pa2.png",
    "aerinowa tarcza": "/static/images/database/armor/fs-aerinowa-tarcza--pa4.png",
    "aerin shield": "/static/images/database/armor/fs-aerinowa-tarcza--pa4.png",
    "heraldyczna tarcza": "/static/images/database/armor/fs-heraldyczna-tarcza--pa3.png",
    "heraldic shield": "/static/images/database/armor/fs-heraldyczna-tarcza--pa3.png",
    "koronowa tarcza": "/static/images/database/armor/fs-koronowa-tarcza--pa5.png",
    "crown shield": "/static/images/database/armor/fs-koronowa-tarcza--pa5.png",
    "zakarum": "/static/images/database/armor/fs-koronowa-tarcza--pa5.png",
    "kurast": "/static/images/database/armor/fs-heraldyczna-tarcza--pa3.png",
    "targi": "/static/images/database/armor/fs-aerinowa-tarcza--pa4.png",
    "targe": "/static/images/database/armor/fs-aerinowa-tarcza--pa4.png",
    "święte targi": "/static/images/database/armor/fs-aerinowa-tarcza--pa4.png",
    "swiete targi": "/static/images/database/armor/fs-aerinowa-tarcza--pa4.png",
    "sacred targe": "/static/images/database/armor/fs-aerinowa-tarcza--pa4.png",
    "monarch": "/static/images/database/armor/fs-tr-jk-tna-tarcza--kit.png",
    "monarcha": "/static/images/database/armor/fs-tr-jk-tna-tarcza--kit.png",
    "duża tarcza": "/static/images/database/armor/fs-du-a-tarcza--lrg.png",
    "duza tarcza": "/static/images/database/armor/fs-du-a-tarcza--lrg.png",
    "large shield": "/static/images/database/armor/fs-du-a-tarcza--lrg.png",
    "mała tarcza": "/static/images/database/armor/fs-ma-a-tarcza--sml.png",
    "mala tarcza": "/static/images/database/armor/fs-ma-a-tarcza--sml.png",
    "small shield": "/static/images/database/armor/fs-ma-a-tarcza--sml.png",
    "puklerz": "/static/images/database/armor/fs-ma-a-tarcza--sml.png",
    "buckler": "/static/images/database/armor/fs-ma-a-tarcza--sml.png",
    "ciężka tarcza": "/static/images/database/armor/fs-ci-ka-tarcza--tow.png",
    "ciezka tarcza": "/static/images/database/armor/fs-ci-ka-tarcza--tow.png",
    "tower shield": "/static/images/database/armor/fs-ci-ka-tarcza--tow.png",
    "gotycka tarcza": "/static/images/database/armor/fs-gotycka-tarcza--gts.png",
    "gothic shield": "/static/images/database/armor/fs-gotycka-tarcza--gts.png",
    "pavise": "/static/images/database/armor/fs-gotycka-tarcza--gts.png",
    "kościana tarcza": "/static/images/database/armor/fs-ko-ciana-tarcza--bsh.png",
    "kosciana tarcza": "/static/images/database/armor/fs-ko-ciana-tarcza--bsh.png",
    "bone shield": "/static/images/database/armor/fs-ko-ciana-tarcza--bsh.png",
    "kolczasta tarcza": "/static/images/database/armor/fs-kolczasta-tarcza--spk.png",
    "trójkątna tarcza": "/static/images/database/armor/fs-tr-jk-tna-tarcza--kit.png",
    "trojkatna tarcza": "/static/images/database/armor/fs-tr-jk-tna-tarcza--kit.png",
    "kite shield": "/static/images/database/armor/fs-tr-jk-tna-tarcza--kit.png",

    # Rękawice (Gloves)
    "lekkie rękawice": "/static/images/database/armor/nl-lekkie-r-kawice--tgl.png",
    "lekkie rekawice": "/static/images/database/armor/nl-lekkie-r-kawice--tgl.png",
    "light gauntlets": "/static/images/database/armor/nl-lekkie-r-kawice--tgl.png",
    "pięści maga": "/static/images/database/armor/nl-lekkie-r-kawice--tgl.png",
    "piesci maga": "/static/images/database/armor/nl-lekkie-r-kawice--tgl.png",
    "magefist": "/static/images/database/armor/nl-lekkie-r-kawice--tgl.png",

    # Pasy (Belts)
    "szarfa": "/static/images/database/armor/fs-szarfa--lbl.png",
    "sash": "/static/images/database/armor/fs-szarfa--lbl.png",
    "siatka arachnidów": "/static/images/database/armor/fs-szarfa--lbl.png",
    "siatka arachnidow": "/static/images/database/armor/fs-szarfa--lbl.png",
    "pajęcza szarfa": "/static/images/database/armor/fs-szarfa--lbl.png",
    "pajecza szarfa": "/static/images/database/armor/fs-szarfa--lbl.png",
    "spiderweb sash": "/static/images/database/armor/fs-szarfa--lbl.png",
    "arachnid mesh": "/static/images/database/armor/fs-szarfa--lbl.png",

    # Hełmy (Helms)
    "czapka arlekina": "/static/images/database/armor/ms-kaptur--cap.png",
    "harlequin crest": "/static/images/database/armor/ms-kaptur--cap.png",
    "czako": "/static/images/database/armor/ms-kaptur--cap.png",
    "shako": "/static/images/database/armor/ms-kaptur--cap.png",
    "kaptur": "/static/images/database/armor/ms-kaptur--cap.png",
    "cap": "/static/images/database/armor/ms-kaptur--cap.png",
    "korona": "/static/images/database/armor/fs-korona--crn.png",
    "crown": "/static/images/database/armor/fs-korona--crn.png",
    "koronetka": "/static/images/database/armor/fs-koronetka--ci1.png",
    "coronet": "/static/images/database/armor/fs-koronetka--ci1.png",
    "diadem": "/static/images/database/armor/fs-koronetka--ci1.png",
    "tiara": "/static/images/database/armor/fs-koronetka--ci1.png",
    "obręcz": "/static/images/database/armor/fs-obr-cz--ci0.png",
    "obrec": "/static/images/database/armor/fs-obr-cz--ci0.png",
    "circlet": "/static/images/database/armor/fs-obr-cz--ci0.png",
    "maska": "/static/images/database/armor/fs-maska--msk.png",
    "mask": "/static/images/database/armor/fs-maska--msk.png",

    # Zbroje (Armor)
    "skóra zmijomaga": "/static/images/database/armor/fs-sk-rzana-zbroja--lea.png",
    "skora zmijomaga": "/static/images/database/armor/fs-sk-rzana-zbroja--lea.png",
    "skin of the vipermagi": "/static/images/database/armor/fs-sk-rzana-zbroja--lea.png",
    "skórzana zbroja": "/static/images/database/armor/fs-sk-rzana-zbroja--lea.png",
    "skorzana zbroja": "/static/images/database/armor/fs-sk-rzana-zbroja--lea.png",
    "gadzia skóra": "/static/images/database/armor/fs-sk-rzana-zbroja--lea.png",
    "gadzia skora": "/static/images/database/armor/fs-sk-rzana-zbroja--lea.png",
    "wyrmhide": "/static/images/database/armor/fs-sk-rzana-zbroja--lea.png",
    "dusk shroud": "/static/images/database/armor/fs-sk-rzana-zbroja--lea.png",
    "archon plate": "/static/images/database/armor/fs-pe-na-zbroja-p-ytowa--ful.png",
    "pancerz archonta": "/static/images/database/armor/fs-pe-na-zbroja-p-ytowa--ful.png",

    # Bronie (Weapons)
    "korbacz": "/static/images/database/weapon/ms-korbacz--fla.png",
    "flail": "/static/images/database/weapon/ms-korbacz--fla.png",
    "serce dębu": "/static/images/database/weapon/ms-korbacz--fla.png",
    "serce debu": "/static/images/database/weapon/ms-korbacz--fla.png",
    "heart of the oak": "/static/images/database/weapon/ms-korbacz--fla.png",
    "kryształowy miecz": "/static/images/database/weapon/ms-kryszta-owy-miecz--crs.png",
    "krysztalowy miecz": "/static/images/database/weapon/ms-kryszta-owy-miecz--crs.png",
    "crystal sword": "/static/images/database/weapon/ms-kryszta-owy-miecz--crs.png",
    "wezwanie do broni": "/static/images/database/weapon/ms-kryszta-owy-miecz--crs.png",
    "call to arms": "/static/images/database/weapon/ms-kryszta-owy-miecz--crs.png",

    # Talizmany (cm1: 1x1, cm2: 1x2, cm3: 1x3)
    "annihilus": "/static/images/database/charm/ms-mniejszy-talizman--cm1.png",
    "mniejszy talizman": "/static/images/database/charm/ms-mniejszy-talizman--cm1.png",
    "small charm": "/static/images/database/charm/ms-mniejszy-talizman--cm1.png",
    "pochodnia piekielnego ognia": "/static/images/database/charm/ms-du-y-talizman--cm2.png",
    "hellfire torch": "/static/images/database/charm/ms-du-y-talizman--cm2.png",
    "duży talizman": "/static/images/database/charm/ms-du-y-talizman--cm2.png",
    "duzy talizman": "/static/images/database/charm/ms-du-y-talizman--cm2.png",
    "large charm": "/static/images/database/charm/ms-du-y-talizman--cm2.png",
    "wielki talizman": "/static/images/database/charm/ms-wielki-talizman--cm3.png",
    "grand charm": "/static/images/database/charm/ms-wielki-talizman--cm3.png",
    "lwi wielki talizman": "/static/images/database/charm/ms-wielki-talizman--cm3.png",
    "odnowione niebiańskie pęknięcie": "/static/images/database/charm/ms-wielki-talizman--cm3.png",
    "odnowione niebiaskie pknicie": "/static/images/database/charm/ms-wielki-talizman--cm3.png",
    "gheed": "/static/images/database/charm/ms-wielki-talizman--cm3.png",
}

def _clean_str(s: str) -> str:
    if not s:
        return ""
    import re
    res = re.sub(r'\[.*?\]', '', s).lower()
    charmap = {'ą':'a','ć':'c','ę':'e','ł':'l','ń':'n','ó':'o','ś':'s','ź':'z','ż':'z'}
    for k, v in charmap.items():
        res = res.replace(k, v)
    res = re.sub(r'[^a-z0-9\s]', ' ', res)
    res = re.sub(r'\brondel[aei]?\b', 'rodela', res)
    res = re.sub(r'\bobledniczy\b', 'oblezniczy', res)
    return ' '.join(res.split())

_HAC_CACHE = None

def _get_hac_items():
    global _HAC_CACHE
    if _HAC_CACHE is not None:
        return _HAC_CACHE
    items = []
    try:
        import sqlite3
        conn = sqlite3.connect(CATALOG_DB_PATH)
        c = conn.cursor()
        c.execute('SELECT kind, quality, category, name, name_en, base_name, image, market_value, stat_priority, build_notes FROM items')
        for kind, qual, cat, name, name_en, base_name, img, mval, spri, bnot in c.fetchall():
            items.append({
                'kind': kind,
                'quality': qual,
                'category': cat,
                'name': name,
                'name_en': name_en,
                'base_name': base_name,
                'image': f"/static/images/database/{img[7:]}" if img and img.startswith("images/") else (img or ""),
                'market_value': mval or "",
                'stat_priority': spri or "",
                'build_notes': bnot or "",
                'norm_name': _clean_str(name),
                'norm_en': _clean_str(name_en),
                'norm_base': _clean_str(base_name)
            })
        # Load valuable magic items
        try:
            c.execute('SELECT name, item_type, quality, market_value, stat_priority, build_notes, image FROM valuable_magic_items')
            for m_name, m_type, m_qual, m_val, m_pri, m_not, m_img in c.fetchall():
                items.append({
                    'kind': 'magic',
                    'quality': m_qual or 'magiczny',
                    'category': m_type or '',
                    'name': m_name,
                    'name_en': m_name,
                    'base_name': '',
                    'image': m_img or '',
                    'market_value': m_val or '',
                    'stat_priority': m_pri or '',
                    'build_notes': m_not or '',
                    'norm_name': _clean_str(m_name),
                    'norm_en': _clean_str(m_name),
                    'norm_base': ''
                })
        except Exception:
            pass
        # Load runewords
        try:
            c.execute('SELECT name, name_en, market_value, stat_priority, build_notes FROM runewords')
            for rw_name, rw_en, rw_val, rw_pri, rw_not in c.fetchall():
                items.append({
                    'kind': 'runeword',
                    'quality': 'runiczne',
                    'category': 'runeword',
                    'name': rw_name,
                    'name_en': rw_en,
                    'base_name': '',
                    'image': '',
                    'market_value': rw_val or '',
                    'stat_priority': rw_pri or '',
                    'build_notes': rw_not or '',
                    'norm_name': _clean_str(rw_name),
                    'norm_en': _clean_str(rw_en),
                    'norm_base': ''
                })
        except Exception:
            pass
        conn.close()
    except Exception:
        pass
    _HAC_CACHE = items
    return _HAC_CACHE

_BASE_IMAGES_CACHE = None

def _init_base_images():
    global _BASE_IMAGES_CACHE
    if _BASE_IMAGES_CACHE is not None:
        return _BASE_IMAGES_CACHE
    cache = {}
    aliases = {
        'monarch': 'monarcha',
        'phase blade': 'fazowe ostrze',
        'crystal sword': 'krysztalowy miecz',
        'archon plate': 'archoncka zbroja plytowa',
        'mage plate': 'lekka zbroja plytowa',
        'dusk shroud': 'wieczorny calun',
        'flail': 'korbacz',
        'thresher': 'rozdzieracz',
        'colossus blade': 'kolosalne ostrze',
        'colossus sword': 'kolosalny miecz',
        'berserker axe': 'topor berserkera',
        'sacred targe': 'swieta tarza',
        'vortex shield': 'wirotarcza',
        'kurast shield': 'kurastowa tarcza',
        'zakarum shield': 'zakarymska tarcza',
        'shako': 'czako',
        'czapka': 'kaptur',
        'cap': 'kaptur',
        'tiara': 'tiara',
        'diadem': 'diadem',
        'grand charm': 'wielki talizman',
        'small charm': 'mniejszy talizman',
        'large charm': 'duzy talizman',
        'ring': 'pierscien',
        'amulet': 'amulet',
        'jewel': 'klejnot',
    }
    try:
        import sqlite3
        conn = sqlite3.connect(CATALOG_DB_PATH)
        c = conn.cursor()
        rows = c.execute("SELECT name, name_en, image FROM items WHERE kind='base'").fetchall()
        for name, name_en, img in rows:
            if not img:
                continue
            img_path = f"/static/images/database/{img[7:]}" if img.startswith("images/") else img
            cn = _clean_str(name)
            ce = _clean_str(name_en)
            if cn:
                cache[cn] = img_path
            if ce:
                cache[ce] = img_path
        conn.close()
    except Exception:
        pass
    
    for ak, av in aliases.items():
        if av in cache and ak not in cache:
            cache[ak] = cache[av]

    _BASE_IMAGES_CACHE = cache
    return _BASE_IMAGES_CACHE

def get_base_image(base_name):
    if not base_name:
        return None
    cache = _init_base_images()
    cb = _clean_str(base_name)
    if not cb:
        return None
    if cb in cache:
        return cache[cb]
    # Substring match
    for k, v in cache.items():
        if len(k) >= 3 and (k == cb or k in cb or cb in k):
            return v
    # Word overlap
    words_b = set(cb.split())
    best = None
    best_score = 0
    for k, v in cache.items():
        k_words = set(k.split())
        score = len(words_b & k_words)
        if score > best_score:
            best_score = score
            best = v
    if best and best_score >= 1:
        return best
    return None

def resolve_item_image(name, name_en, base, slot, quality=""):
    name = (name or '').strip()
    name_en = (name_en or '').strip()
    base = (base or '').strip()
    slot = (slot or '').strip().lower()
    quality = (quality or '').strip().lower()

    clean_name = _clean_str(name)
    clean_base = _clean_str(base)
    clean_en = _clean_str(name_en)

    hac_items = _get_hac_items()

    # 1. Sprawdź najpierw unikatowe lub zestawowe przedmioty (specjalna grafika .webp)
    if quality in ('unikalny', 'unique', 'zestaw', 'set') or not quality:
        for h in hac_items:
            if h['kind'] in ('unique', 'set') and h.get('image'):
                if clean_name and clean_name == h['norm_name']:
                    return h['image']
                if clean_en and clean_en == h['norm_en']:
                    return h['image']

    # 2. "jak nie masz grafiki do itemu to daj grafikę bazy itemu"
    # A) Jeśli mamy podaną bazę przedmiotu (np. Monarch, Crystal Sword, Archon Plate)
    if base:
        b_img = get_base_image(base)
        if b_img:
            return b_img

    # B) Jeśli unikat/zestaw nie ma własnej grafiki, pobierz grafikę jego bazy z katalogu
    for h in hac_items:
        if (clean_name and clean_name == h['norm_name']) or (clean_en and clean_en == h['norm_en']):
            if h.get('base_name'):
                b_img = get_base_image(h['base_name'])
                if b_img:
                    return b_img

    # C) Sprawdź czy nazwa lub name_en zawiera bazę (np. "Bursztynowy Mały Talizman", "Ring of the Zodiac")
    for target in [clean_base, clean_name, clean_en]:
        if target:
            b_img = get_base_image(target)
            if b_img:
                return b_img

    # D) Sprawdź kanoniczną bazę bezpośrednio po nazwie, bazie lub name_en
    for target in [clean_name, clean_base, clean_en]:
        if target and target in CANONICAL_SPRITES:
            return CANONICAL_SPRITES[target]

    for key, sprite_path in CANONICAL_SPRITES.items():
        if len(key) >= 4 and (key in clean_base or key in clean_name or key in clean_en):
            return sprite_path

    # Wykrywanie slotu na podstawie słów kluczowych jeśli slot pusty
    if not slot or slot in ("misc", ""):
        if any(k in clean_base or k in clean_name for k in ["buty", "boot", "greave", "nagolenic", "trzewik"]):
            slot = "boots"
        elif any(k in clean_base or k in clean_name for k in ["rondel", "rodel", "rodache", "tarcz", "shield", "puklerz", "pelta", "egid", "herald", "aerin", "monarch", "kurast", "zakarum", "glowa", "trofeum"]):
            slot = "shield"
        elif any(k in clean_base or k in clean_name for k in ["rekawic", "glove", "mitt", "gauntlet", "piesci"]):
            slot = "gloves"
        elif any(k in clean_base or k in clean_name for k in ["pas", "belt", "sash", "girdle", "szarf"]):
            slot = "belt"
        elif any(k in clean_base or k in clean_name for k in ["amulet"]):
            slot = "amulet"
        elif any(k in clean_base or k in clean_name for k in ["pierscien", "ring"]):
            slot = "ring"
        elif any(k in clean_base or k in clean_name for k in ["talizman", "charm"]):
            slot = "charm"
        elif any(k in clean_base or k in clean_name for k in ["klejnot", "jewel"]):
            slot = "jewel"
        elif any(k in clean_base or k in clean_name for k in ["helm", "cap", "czap", "czako", "shako", "crown", "koron", "mask", "diadem", "tiar", "szyszak"]):
            slot = "head"
        elif any(k in clean_base or k in clean_name for k in ["zbroj", "armor", "armour", "plate", "plytow", "kolczug", "pancerz", "kolczan"]):
            slot = "armor"
        elif any(k in clean_base or k in clean_name for k in ["miecz", "sword", "topor", "axe", "bulaw", "mace", "kostur", "staff", "rozdzka", "wand", "luk", "bow", "kusz", "flail", "korbacz", "kosa", "wloczni", "drzewc"]):
            slot = "weapon"

    is_bow = any(k in clean_base or k in clean_name or k in clean_en for k in ["luk", "bow", "kusz", "crossbow"])
    if is_bow:
        return '/static/images/database/weapon/ms-kr-tki-uk--sbw.png'

    fallbacks = {
        'head': '/static/images/database/armor/ms-kaptur--cap.png',
        'armor': '/static/images/database/armor/fs-sk-rzana-zbroja--lea.png',
        'shield1': '/static/images/database/armor/fs-rodela--pa2.png',
        'shield2': '/static/images/database/armor/fs-du-a-tarcza--lrg.png',
        'shield': '/static/images/database/armor/fs-rodela--pa2.png',
        'weapon1': '/static/images/database/weapon/ms-korbacz--fla.png',
        'weapon2': '/static/images/database/weapon/ms-kryszta-owy-miecz--crs.png',
        'weapon': '/static/images/database/weapon/ms-kryszta-owy-miecz--crs.png',
        'gloves': '/static/images/database/armor/nl-lekkie-r-kawice--tgl.png',
        'boots': '/static/images/database/armor/nl-lekkie-p-ytowe-buty--tbt.png',
        'belt': '/static/images/database/armor/fs-szarfa--lbl.png',
        'amulet': '/static/images/database/amulet/ms-amulet--amu.png',
        'ring1': '/static/images/database/ring/ms-pier-cie--rin.png',
        'ring2': '/static/images/database/ring/ms-pier-cie--rin.png',
        'ring': '/static/images/database/ring/ms-pier-cie--rin.png',
        'charms': '/static/images/database/charm/ms-du-y-talizman--cm2.png',
        'charm': '/static/images/database/charm/ms-du-y-talizman--cm2.png',
    }
    return fallbacks.get(slot, '/static/images/database/armor/ms-kaptur--cap.png')

def insert_item(item_dict: dict):
    with get_db() as con:
        if item_dict.get('character_name') and item_dict.get('character_slot') not in ('', 'charms', 'charm', None):
            con.execute("UPDATE items SET character_name='', character_slot='', location='Skrzynia' WHERE LOWER(character_name)=LOWER(?) AND character_slot=?", (item_dict['character_name'],item_dict['character_slot']))
        img_path = item_dict.get("image_path")
        if not img_path:
            img_path = resolve_item_image(
                item_dict.get("name"),
                item_dict.get("name_en"),
                item_dict.get("base"),
                item_dict.get("character_slot"),
                item_dict.get("quality")
            )

        con.execute("""
        INSERT INTO items (
            id, name, name_en, base, quality, defense, damage, level_req,
            req_str, req_dex, sockets, stats_json, rolls_eval_json, requirements_json,
            catalog_id, preview_filename, screenshot_filename, location, notes,
            is_duplicate, duplicate_of, image_hash, character_name, character_slot, image_path,
            market_value, stat_priority, build_notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item_dict["id"],
            item_dict.get("name", "Nieznany"),
            item_dict.get("name_en", ""),
            item_dict.get("base", ""),
            item_dict.get("quality", "normalny"),
            item_dict.get("defense"),
            item_dict.get("damage"),
            item_dict.get("level_req"),
            item_dict.get("req_str"),
            item_dict.get("req_dex"),
            item_dict.get("sockets"),
            json.dumps(item_dict.get("stats", []), ensure_ascii=False),
            json.dumps(item_dict.get("rolls_eval", []), ensure_ascii=False),
            json.dumps(item_dict.get("requirements", {}), ensure_ascii=False),
            item_dict.get("catalog_id", ""),
            item_dict.get("preview_filename", ""),
            item_dict.get("screenshot_filename", ""),
            item_dict.get("location", ""),
            item_dict.get("notes", ""),
            item_dict.get("is_duplicate", 0),
            item_dict.get("duplicate_of", ""),
            item_dict.get("image_hash", ""),
            item_dict.get("character_name", ""),
            item_dict.get("character_slot", ""),
            img_path,
            item_dict.get("market_value", ""),
            item_dict.get("stat_priority", ""),
            item_dict.get("build_notes", "")
        ))
        con.commit()

def update_item_meta(item_id: str, location: str = None, notes: str = None, is_duplicate: int = None, character_name: str = None, character_slot: str = None):
    with get_db() as con:
        updates = []
        params = []
        if location is not None:
            updates.append("location = ?")
            params.append(location)
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)
        if is_duplicate is not None:
            updates.append("is_duplicate = ?")
            params.append(is_duplicate)
        if character_name is not None:
            updates.append("character_name = ?")
            params.append(character_name)
        if character_slot is not None:
            updates.append("character_slot = ?")
            params.append(character_slot)
        if updates:
            params.append(item_id)
            con.execute(f"UPDATE items SET {', '.join(updates)} WHERE id = ?", params)
            con.commit()

def get_distinct_locations() -> list[str]:
    with get_db() as con:
        rows = con.execute("SELECT DISTINCT location FROM items WHERE location IS NOT NULL AND location != '' AND (character_name IS NULL OR character_name = '') ORDER BY location ASC").fetchall()
        return [r[0] for r in rows]

def _parse_item_row(r, con=None) -> dict:
    it = dict(r)
    img = it.get("image_path")
    name_clean = (it.get("name") or "").lower()
    name_en_clean = (it.get("name_en") or "").lower()
    base_clean = (it.get("base") or "").lower()
    is_actual_crown = any("koron" in s or "crown" in s for s in [name_clean, name_en_clean, base_clean])

    resolved_img = resolve_item_image(
        it.get("name"),
        it.get("name_en"),
        it.get("base"),
        it.get("character_slot"),
        it.get("quality")
    )
    if resolved_img:
        it["image_path"] = resolved_img
    it["base_image_path"] = get_base_image(it.get("base")) or get_base_image(it.get("name")) or ""

    # Auto-enrich market value, stat priority, build notes from catalog if empty
    if not it.get("market_value"):
        for h in _get_hac_items():
            if (it.get("name") and _clean_str(it["name"]) == h["norm_name"]) or \
               (it.get("name_en") and _clean_str(it["name_en"]) == h["norm_en"]):
                if h.get("market_value"):
                    it["market_value"] = h["market_value"]
                    if not it.get("stat_priority"):
                        it["stat_priority"] = h.get("stat_priority", "")
                    if not it.get("build_notes"):
                        it["build_notes"] = h.get("build_notes", "")
                break
    try:
        it["stats"] = json.loads(it.get("stats_json") or "[]")
    except Exception:
        it["stats"] = []
    try:
        it["rolls_eval"] = json.loads(it.get("rolls_eval_json") or "[]")
    except Exception:
        it["rolls_eval"] = []
    try:
        it["requirements"] = json.loads(it.get("requirements_json") or "{}")
    except Exception:
        it["requirements"] = {}

    # Oblicz display_name: dla białych, niebieskich i rzadkich pokazuj bazę
    qual = (it.get("quality") or "").lower()
    base = it.get("base") or ""
    name = it.get("name") or ""
    en_to_pl_bases = {
        "small charm": "Mniejszy Talizman",
        "large charm": "Duży Talizman",
        "grand charm": "Wielki Talizman",
        "light plate boots": "Lekkie Płytowe Buty",
        "ring": "Pierścień",
        "amulet": "Amulet",
        "jewel": "Klejnot"
    }
    clean_base_display = en_to_pl_bases.get(base.lower(), base) if base else name

    if qual in ("normalny", "normal", "superior", "magiczny", "magic", "rzadki", "rare"):
        it["display_name"] = clean_base_display
    else:
        it["display_name"] = name or clean_base_display

    try:
        import trade_jargon
        it["colloquial_name"] = trade_jargon.get_colloquial_name(it, use_shorthand=True)
        it["base_shorthand"] = trade_jargon.abbreviate_base(it.get("base") or "")
        for r in it["rolls_eval"]:
            r["shorthand"] = trade_jargon.format_roll_shorthand(r)
    except Exception:
        it["colloquial_name"] = it.get("name_en") or it.get("name") or "Przedmiot"
        it["base_shorthand"] = it.get("base") or ""

    it["is_in_trade"] = bool(it.get("trade_id"))
    it["trade_price"] = it.get("trade_price") or "Czekam na ofertę"
    it["trade_notes"] = it.get("trade_notes") or ""
    return it

def update_item_full(item_id: str, item_dict: dict):
    img_path = item_dict.get("image_path")
    if not img_path:
        img_path = resolve_item_image(
            item_dict.get("name"),
            item_dict.get("name_en"),
            item_dict.get("base"),
            item_dict.get("character_slot"),
            item_dict.get("quality")
        )
    with get_db() as con:
        con.execute("""
        UPDATE items SET
            name = ?, name_en = ?, base = ?, quality = ?, defense = ?, damage = ?,
            level_req = ?, req_str = ?, req_dex = ?, sockets = ?, stats_json = ?,
            rolls_eval_json = ?, requirements_json = ?, preview_filename = ?,
            screenshot_filename = ?, image_hash = ?, image_path = ?,
            location = COALESCE(NULLIF(?, ''), location),
            character_name = COALESCE(NULLIF(?, ''), character_name),
            character_slot = COALESCE(NULLIF(?, ''), character_slot)
        WHERE id = ?
        """, (
            item_dict.get("name", "Nieznany"),
            item_dict.get("name_en", ""),
            item_dict.get("base", ""),
            item_dict.get("quality", "normalny"),
            item_dict.get("defense"),
            item_dict.get("damage"),
            item_dict.get("level_req"),
            item_dict.get("req_str"),
            item_dict.get("req_dex"),
            item_dict.get("sockets"),
            json.dumps(item_dict.get("stats", []), ensure_ascii=False),
            json.dumps(item_dict.get("rolls_eval", []), ensure_ascii=False),
            json.dumps(item_dict.get("requirements", {}), ensure_ascii=False),
            item_dict.get("preview_filename", ""),
            item_dict.get("screenshot_filename", ""),
            item_dict.get("image_hash", ""),
            img_path,
            item_dict.get("location", ""),
            item_dict.get("character_name", ""),
            item_dict.get("character_slot", ""),
            item_id
        ))
        con.commit()

def find_character_equipped_item(character_name: str, name: str = "", quality: str = "", stats: list = None, image_hash: str = "", slot: str = "") -> dict | None:
    if not character_name:
        return None
    with get_db() as con:
        if image_hash:
            row = con.execute("SELECT * FROM items WHERE LOWER(character_name) = LOWER(?) AND image_hash = ? LIMIT 1", (character_name, image_hash)).fetchone()
            if row:
                return _parse_item_row(row, con)
        if slot and slot not in ("", "charms", "charm"):
            row = con.execute("SELECT * FROM items WHERE LOWER(character_name) = LOWER(?) AND character_slot = ? LIMIT 1", (character_name, slot)).fetchone()
            if row:
                it = _parse_item_row(row, con)
                if not name or it.get("name", "").lower() == (name or "").lower() or it.get("base", "").lower() == (name or "").lower():
                    return it
        if name:
            if stats:
                stats_str = json.dumps(stats, ensure_ascii=False)
                row = con.execute("SELECT * FROM items WHERE LOWER(character_name) = LOWER(?) AND LOWER(name) = LOWER(?) AND stats_json = ? LIMIT 1", (character_name, name, stats_str)).fetchone()
                if row:
                    return _parse_item_row(row, con)
            row = con.execute("SELECT * FROM items WHERE LOWER(character_name) = LOWER(?) AND LOWER(name) = LOWER(?) LIMIT 1", (character_name, name)).fetchone()
            if row:
                return _parse_item_row(row, con)
    return None

def get_all_items(quality_filter=None, search_query=None, location_filter=None, include_duplicates=False, character_filter=None, exclude_character_gear=False):
    with get_db() as con:
        where = []
        params = []
        
        if not include_duplicates:
            where.append("(items.is_duplicate = 0 OR items.is_duplicate IS NULL)")
            
        if exclude_character_gear:
            where.append("(items.character_name IS NULL OR items.character_name = '')")
        elif character_filter:
            where.append("items.character_name = ?")
            params.append(character_filter)

        if quality_filter:
            where.append("items.quality LIKE ?")
            params.append(f"%{quality_filter}%")
        if location_filter:
            where.append("items.location = ?")
            params.append(location_filter)
        if search_query:
            needle = f"%{search_query}%"
            where.append("(items.name LIKE ? OR items.name_en LIKE ? OR items.base LIKE ? OR items.stats_json LIKE ? OR items.location LIKE ? OR items.notes LIKE ? OR items.character_name LIKE ?)")
            params.extend([needle, needle, needle, needle, needle, needle, needle])
            
        sql = """
            SELECT items.*, t.id as trade_id, t.price as trade_price, t.notes as trade_notes
            FROM items
            LEFT JOIN (
                SELECT item_id, id, price, notes FROM trade_items GROUP BY item_id
            ) t ON items.id = t.item_id
        """
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY items.created_at DESC"
        
        rows = con.execute(sql, params).fetchall()
        return [_parse_item_row(r) for r in rows]

def get_potential_duplicates() -> list[dict]:
    with get_db() as con:
        dup_rows = con.execute("SELECT * FROM items WHERE is_duplicate = 1").fetchall()
        if not dup_rows:
            return []

        groups = {}
        for dr in dup_rows:
            dup_item = _parse_item_row(dr)
            orig_id = dup_item.get("duplicate_of") or ""
            
            if not orig_id:
                orig_id = dup_item["id"]

            if orig_id not in groups:
                orig_row = con.execute("SELECT * FROM items WHERE id = ?", (orig_id,)).fetchone()
                if orig_row:
                    orig_item = _parse_item_row(orig_row)
                else:
                    orig_item = dup_item
                groups[orig_id] = {
                    "group_id": orig_id,
                    "name": orig_item["name"],
                    "name_en": orig_item.get("name_en", ""),
                    "quality": orig_item.get("quality", ""),
                    "base": orig_item.get("base", ""),
                    "primary_item": orig_item,
                    "duplicates": []
                }
            
            if dup_item["id"] != orig_id:
                groups[orig_id]["duplicates"].append(dup_item)

        return list(groups.values())

def separate_duplicate(item_id: str):
    with get_db() as con:
        con.execute("UPDATE items SET is_duplicate = 0, duplicate_of = '' WHERE id = ?", (item_id,))
        con.commit()


def get_item(item_id: str) -> dict | None:
    with get_db() as con:
        row = con.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        return _parse_item_row(row) if row else None

def delete_item(item_id: str):
    with get_db() as con:
        con.execute("DELETE FROM items WHERE id = ?", (item_id,))
        con.commit()

def equip_item(item_id: str, character_name: str, slot: str):
    with get_db() as con:
        if slot not in ('charms', 'charm'):
            con.execute("UPDATE items SET character_name='', character_slot='', location='' WHERE LOWER(character_name)=LOWER(?) AND character_slot=? AND id<>?",(character_name,slot,item_id))
        con.execute("""
        UPDATE items
        SET character_name = ?, character_slot = ?, location = ?, is_duplicate = 0, duplicate_of = ''
        WHERE id = ?
        """, (character_name, slot, f"Postać: {character_name}", item_id))
        con.commit()

def unequip_item(item_id: str):
    with get_db() as con:
        con.execute("""
        UPDATE items
        SET character_name = '', character_slot = '', location = ''
        WHERE id = ?
        """, (item_id,))
        con.commit()

# =========================================================================
# CHARACTER CRUD & EQUIPMENT
# =========================================================================

def create_or_update_character(data: dict) -> dict:
    char_id = data.get("id") or uuid.uuid4().hex
    name = (data.get("name") or "Bohater").strip()
    class_name = (data.get("class_name") or "Paladyn").strip()
    level = int(data.get("level") or 1)

    with get_db() as con:
        existing = con.execute("SELECT id FROM characters WHERE LOWER(name) = LOWER(?)", (name,)).fetchone()
        if existing:
            char_id = existing["id"]
            con.execute("""
            UPDATE characters SET
                class_name = ?, level = ?, experience = ?, strength = ?, dexterity = ?,
                vitality = ?, energy = ?, defense = ?, stamina = ?, life = ?, mana = ?,
                fire_res = ?, light_res = ?, cold_res = ?, poison_res = ?, main_skill = ?,
                damage = ?, screenshot_filename = ?, updated_at = datetime('now', 'localtime')
            WHERE id = ?
            """, (
                class_name, level, data.get("experience", ""), data.get("strength") or 0,
                data.get("dexterity") or 0, data.get("vitality") or 0, data.get("energy") or 0,
                data.get("defense") or 0, data.get("stamina", ""), data.get("life", ""),
                data.get("mana", ""), data.get("fire_res", ""), data.get("light_res", ""),
                data.get("cold_res", ""), data.get("poison_res", ""), data.get("main_skill", ""),
                data.get("damage", ""), data.get("screenshot_filename", ""), char_id
            ))
        else:
            con.execute("""
            INSERT INTO characters (
                id, name, class_name, level, experience, strength, dexterity,
                vitality, energy, defense, stamina, life, mana, fire_res, light_res,
                cold_res, poison_res, main_skill, damage, screenshot_filename
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                char_id, name, class_name, level, data.get("experience", ""),
                data.get("strength") or 0, data.get("dexterity") or 0, data.get("vitality") or 0,
                data.get("energy") or 0, data.get("defense") or 0, data.get("stamina", ""),
                data.get("life", ""), data.get("mana", ""), data.get("fire_res", ""),
                data.get("light_res", ""), data.get("cold_res", ""), data.get("poison_res", ""),
                data.get("main_skill", ""), data.get("damage", ""), data.get("screenshot_filename", "")
            ))
        con.commit()

    return get_character(name)

def get_character(name: str) -> dict | None:
    if not name:
        return None
    with get_db() as con:
        row = con.execute("SELECT * FROM characters WHERE LOWER(name) = LOWER(?)", (name,)).fetchone()
        return dict(row) if row else None

def get_all_characters_detailed() -> list[dict]:
    with get_db() as con:
        rows = con.execute("SELECT * FROM characters ORDER BY COALESCE(updated_at, created_at) DESC, level DESC, name ASC").fetchall()
        chars = [dict(r) for r in rows]
        for c in chars:
            eq = get_character_equipment(c["name"])
            c["equipped_count"] = sum(1 for k in ["head", "armor", "amulet", "weapon1", "shield1", "gloves", "belt", "boots", "ring1", "ring2"] if eq.get(k))
            c["charms_count"] = len(eq.get("charms") or [])
        return chars

def delete_character(name: str):
    with get_db() as con:
        con.execute("DELETE FROM characters WHERE LOWER(name) = LOWER(?)", (name,))
        con.execute("UPDATE items SET character_name = '', character_slot = '', location = 'Skrzynia' WHERE LOWER(character_name) = LOWER(?)", (name,))
        con.commit()

def touch_character(name: str):
    if not name:
        return
    with get_db() as con:
        con.execute("UPDATE characters SET updated_at = datetime('now', 'localtime') WHERE LOWER(name) = LOWER(?)", (name,))
        con.commit()


def layout_charms_inventory(charms: list[dict]) -> list[dict]:
    """
    Rozmieszcza talizmany w siatce inwentarza 10 kolumn x 4 wiersze z zachowaniem autentycznych wymiarów D2:
    - Wielki Talizman (Grand Charm, Skillery): 1x3
    - Duży Talizman / Pochodnia (Large Charm, Torch): 1x2
    - Mniejszy Talizman / Annihilus (Small Charm): 1x1
    """
    if not charms:
        return []

    for c in charms:
        name_l = (c.get("name") or "").lower()
        base_l = (c.get("base") or "").lower()
        en_l = (c.get("name_en") or "").lower()
        comb = f"{name_l} {base_l} {en_l}"

        if any(k in comb for k in ["wielki", "grand", "gheed", "skiller"]):
            h = 3
            img = "/static/images/database/charm/ms-wielki-talizman--cm3.png"
            type_lbl = "Wielki Talizman (1x3)"
        elif any(k in comb for k in ["duży", "duzy", "large", "pochodnia", "torch"]):
            h = 2
            img = "/static/images/database/charm/ms-du-y-talizman--cm2.png"
            type_lbl = "Duży Talizman (1x2)"
        else:
            h = 1
            img = "/static/images/database/charm/ms-mniejszy-talizman--cm1.png"
            type_lbl = "Mniejszy Talizman (1x1)"

        c["grid_height"] = h
        c["grid_width"] = 1
        c["image_path"] = img
        c["charm_type_label"] = type_lbl

    # Sortuj od największych do najmniejszych dla optymalnego upakowania
    sorted_charms = sorted(charms, key=lambda x: x.get("grid_height", 1), reverse=True)

    # Siatka zajętości 10 kolumn x 4 wiersze
    grid = [[False for _ in range(4)] for _ in range(10)]

    for c in sorted_charms:
        h = c.get("grid_height", 1)
        placed = False
        for col in range(10):
            for row in range(5 - h):
                if all(not grid[col][row + r] for r in range(h)):
                    for r in range(h):
                        grid[col][row + r] = True
                    c["grid_col"] = col + 1
                    c["grid_row"] = row + 1
                    placed = True
                    break
            if placed:
                break
        if not placed:
            c["grid_col"] = 1
            c["grid_row"] = 1

    return sorted_charms

def get_character_equipment(character_name: str) -> dict:
    doll = {
        "character_name": character_name,
        "head": None,
        "amulet": None,
        "armor": None,
        "weapon1": None,
        "shield1": None,
        "weapon2": None,
        "shield2": None,
        "gloves": None,
        "belt": None,
        "boots": None,
        "ring1": None,
        "ring2": None,
        "merc_head": None, "merc_armor": None, "merc_weapon": None, "merc_offhand": None,
        "charms": []
    }
    if not character_name:
        return doll

    with get_db() as con:
        rows = con.execute("SELECT * FROM items WHERE LOWER(character_name) = LOWER(?) ORDER BY created_at ASC, rowid ASC", (character_name,)).fetchall()
        for r in rows:
            it = _parse_item_row(r)
            slot = it.get("character_slot")
            if slot in doll and slot != "charms":
                doll[slot] = it
            elif slot == "charms" or slot == "charm":
                doll["charms"].append(it)
        doll["charms"] = layout_charms_inventory(doll["charms"])
    return doll

def get_all_characters() -> list[str]:
    with get_db() as con:
        names_from_chars = [r[0] for r in con.execute("SELECT name FROM characters ORDER BY name ASC").fetchall()]
        names_from_items = [r[0] for r in con.execute("SELECT DISTINCT character_name FROM items WHERE character_name IS NOT NULL AND character_name != '' ORDER BY character_name ASC").fetchall()]
        combined = list(dict.fromkeys(names_from_chars + names_from_items))
        return combined


# ==========================================
# MODUŁ LISTY SPRZEDAŻY (TRADE LISTS)
# ==========================================

def get_trade_lists() -> list[dict]:
    """Pobiera wszystkie listy sprzedaży wraz z liczbą przypisanych ofert."""
    with get_db() as con:
        con.execute("INSERT OR IGNORE INTO trade_lists (name) VALUES ('Główna')")
        rows = con.execute("""
            SELECT tl.id, tl.name, tl.description, tl.created_at,
                   COUNT(ti.id) as item_count
            FROM trade_lists tl
            LEFT JOIN trade_items ti ON tl.name = ti.list_name
            GROUP BY tl.id, tl.name
            ORDER BY tl.id ASC
        """).fetchall()
        return [dict(r) for r in rows]

def create_trade_list(name: str, description: str = "") -> dict:
    """Tworzy nową listę sprzedaży."""
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Nazwa listy nie może być pusta.")
    with get_db() as con:
        con.execute(
            "INSERT INTO trade_lists (name, description) VALUES (?, ?)",
            (clean_name, description.strip())
        )
        con.commit()
        row = con.execute("SELECT * FROM trade_lists WHERE name = ?", (clean_name,)).fetchone()
        return dict(row)

def rename_trade_list(old_name: str, new_name: str) -> bool:
    """Zmienia nazwę listy sprzedaży oraz aktualizuje przypisane przedmioty."""
    clean_old = old_name.strip()
    clean_new = new_name.strip()
    if not clean_old or not clean_new:
        raise ValueError("Nazwy nie mogą być puste.")
    if clean_old == clean_new:
        return True
    with get_db() as con:
        con.execute("UPDATE trade_lists SET name = ? WHERE name = ?", (clean_new, clean_old))
        con.execute("UPDATE trade_items SET list_name = ? WHERE list_name = ?", (clean_new, clean_old))
        con.commit()
        return True

def delete_trade_list(name: str) -> bool:
    """Usuwa listę sprzedaży i przypisane do niej przedmioty (nie pozwala usunąć ostatniej listy)."""
    clean_name = name.strip()
    with get_db() as con:
        count = con.execute("SELECT COUNT(*) FROM trade_lists").fetchone()[0]
        if count <= 1:
            raise ValueError("Nie można usunąć jedynej istniejącej listy sprzedaży.")
        con.execute("DELETE FROM trade_items WHERE list_name = ?", (clean_name,))
        con.execute("DELETE FROM trade_lists WHERE name = ?", (clean_name,))
        con.commit()
        return True

def get_trade_items(list_name: str = None) -> list[dict]:
    """Pobiera przedmioty wystawione na liście sprzedaży z pełnymi informacjami o przedmiocie."""
    with get_db() as con:
        target_list = list_name.strip() if list_name and list_name.strip() else None
        if not target_list:
            first_list = con.execute("SELECT name FROM trade_lists ORDER BY id ASC LIMIT 1").fetchone()
            target_list = first_list[0] if first_list else "Główna"

        rows = con.execute("""
            SELECT t.id as trade_id, t.list_name, t.price as trade_price, t.notes as trade_notes, t.created_at as trade_created_at,
                   i.*
            FROM trade_items t
            JOIN items i ON t.item_id = i.id
            WHERE t.list_name = ?
            ORDER BY t.created_at DESC
        """, (target_list,)).fetchall()

        result = []
        for r in rows:
            it = _parse_item_row(r)
            it["trade_id"] = r["trade_id"]
            it["trade_list_name"] = r["list_name"] or "Główna"
            it["trade_price"] = r["trade_price"] or "Czekam na ofertę"
            it["trade_notes"] = r["trade_notes"] or ""
            it["trade_created_at"] = r["trade_created_at"]
            it["is_in_trade"] = True
            result.append(it)
        return result

def add_to_trade(item_id: str, price: str = "Czekam na ofertę", notes: str = "", list_name: str = None) -> bool:
    """Dodaje przedmiot do wybranej listy sprzedaży lub aktualizuje jego cenę."""
    with get_db() as con:
        target_list = list_name.strip() if list_name and list_name.strip() else None
        if not target_list:
            first = con.execute("SELECT name FROM trade_lists ORDER BY id ASC LIMIT 1").fetchone()
            target_list = first[0] if first else "Główna"
        
        con.execute("INSERT OR IGNORE INTO trade_lists (name) VALUES (?)", (target_list,))
        con.execute("""
            INSERT INTO trade_items (item_id, list_name, price, notes)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(item_id, list_name) DO UPDATE SET price = excluded.price, notes = excluded.notes
        """, (item_id, target_list, price.strip() or "Czekam na ofertę", notes.strip()))
        con.commit()
        return True

def remove_from_trade(item_id: str, list_name: str = None) -> bool:
    """Usuwa przedmiot z listy sprzedaży (lub ze wszystkich list, jeśli list_name nie podano)."""
    with get_db() as con:
        if list_name:
            con.execute("DELETE FROM trade_items WHERE item_id = ? AND list_name = ?", (item_id, list_name.strip()))
        else:
            con.execute("DELETE FROM trade_items WHERE item_id = ?", (item_id,))
        con.commit()
        return True

def update_trade_item(item_id: str, price: str = None, notes: str = None, list_name: str = None) -> bool:
    """Aktualizuje cenę lub notatkę przedmiotu na liście sprzedaży."""
    with get_db() as con:
        updates = []
        params = []
        if price is not None:
            updates.append("price = ?")
            params.append(price.strip() or "Czekam na ofertę")
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes.strip())
        if updates:
            where_clause = "WHERE item_id = ?"
            params.append(item_id)
            if list_name:
                where_clause += " AND list_name = ?"
                params.append(list_name.strip())
            con.execute(f"UPDATE trade_items SET {', '.join(updates)} {where_clause}", params)
            con.commit()
            return True
        return False

def is_in_trade(item_id: str, list_name: str = None) -> bool:
    """Sprawdza czy przedmiot znajduje się na liście sprzedaży."""
    with get_db() as con:
        if list_name:
            row = con.execute("SELECT 1 FROM trade_items WHERE item_id = ? AND list_name = ? LIMIT 1", (item_id, list_name.strip())).fetchone()
        else:
            row = con.execute("SELECT 1 FROM trade_items WHERE item_id = ? LIMIT 1", (item_id,)).fetchone()
        return bool(row)

def get_trade_count(list_name: str = None) -> int:
    """Zwraca liczbę przedmiotów na liście sprzedaży."""
    with get_db() as con:
        if list_name:
            row = con.execute("SELECT COUNT(*) FROM trade_items WHERE list_name = ?", (list_name.strip(),)).fetchone()
        else:
            row = con.execute("SELECT COUNT(*) FROM trade_items").fetchone()
        return row[0] if row else 0
