"""UberApp character reports and persistent trading vocabulary."""
import json
import re
import unicodedata
from collections import defaultdict
from db import get_db, get_character, get_character_equipment, create_or_update_character

SLOTS = {'head':'Hełm','armor':'Pancerz','weapon1':'Broń I','shield1':'Off-hand I',
         'weapon2':'Broń II','shield2':'Off-hand II','amulet':'Amulet','gloves':'Rękawice',
         'belt':'Pas','boots':'Buty','ring1':'Pierścień I','ring2':'Pierścień II',
         'merc_head':'Hełm najemnika','merc_armor':'Pancerz najemnika',
         'merc_weapon':'Broń najemnika','merc_offhand':'Off-hand najemnika','charms':'Talizmany'}

def init_features():
    with get_db() as con:
        con.execute('CREATE TABLE IF NOT EXISTS uber_aliases (kind TEXT, source TEXT, alias TEXT NOT NULL, PRIMARY KEY(kind,source))')
        con.execute('CREATE TABLE IF NOT EXISTS uber_item_details (item_id TEXT PRIMARY KEY, socket_contents TEXT DEFAULT "", trade_stats TEXT DEFAULT "")')

def select_character(saved=''):
    with get_db() as con:
        rows = con.execute('SELECT name FROM characters ORDER BY updated_at DESC, rowid DESC').fetchall()
    names = [r['name'] for r in rows]
    return saved if saved in names else (names[0] if names else '')

def edit_character(original, updates):
    current = get_character(original) if original else {}
    name = str(updates.get('name') or '').strip()
    if not name:
        raise ValueError('Podaj nazwę postaci.')
    level = int(updates.get('level') or 1)
    if not 1 <= level <= 99:
        raise ValueError('Poziom musi mieścić się w zakresie 1–99.')
    if name.casefold() != (original or '').casefold() and get_character(name):
        raise ValueError('Postać o tej nazwie już istnieje.')
    data = dict(current or {})
    data.update(updates, name=name, level=level)
    if current and name != original:
        with get_db() as con:
            con.execute('UPDATE characters SET name=? WHERE id=?', (name, current['id']))
            con.execute('UPDATE items SET character_name=?, location=REPLACE(location, ?, ?) WHERE LOWER(character_name)=LOWER(?)', (name, original, name, original))
    return create_or_update_character(data)

def normal(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text.casefold().replace('ł','l')) if not unicodedata.combining(c))

# Only explicitly additive, unambiguous global bonuses. Local/conditional properties stay in the complete source list.
RULES = [
    ('Wszystkie umiejętności', '', r'(?:do )?(?:wszystkich umiejetnosci|all skills)'),
    ('Siła', '', r'(?:do )?(?:sily|sila|strength)'),
    ('Zręczność', '', r'(?:do )?(?:zrecznosci|zrecznosc|dexterity)'),
    ('Żywotność', '', r'(?:do )?(?:zywotnosci|zywotnosc|vitality)'),
    ('Energia', '', r'(?:do )?(?:energii|energia|energy)'),
    ('Życie', '', r'(?:do )?(?:zycia|zycie|zdrowia|life)'),
    ('Mana', '', r'(?:do )?(?:many|mana)'),
    ('Wszystkie atrybuty', '', r'(?:do )?(?:wszystkich atrybutow|all attributes)'),
    ('FCR · szybkość rzucania czarów', '%', r'(?:(?:do )?szyb?k?osci rzucania czarow|szybsze rzucanie czarow|szybszego rzucania czarow|faster cast rate|fcr)'),
    ('FHR · odzyskiwanie równowagi', '%', r'(?:(?:do )?szyb?k?osci odzyskiwania rownowagi|szybsze odzyskiwanie rownowagi|szybszego odzyskiwania rownowagi|faster hit recovery|fhr)'),
    ('FRW · bieg / chód', '%', r'(?:szybsze bieganie[ /]chodzenie|szybsze bieganie i chodzenie|(?:do )?szyb?k?osci poruszania sie|faster run/walk|frw)'),
    ('IAS · szybkość ataku', '%', r'(?:(?:do )?szyb?k?osci ataku|zwiekszona szybk?osc ataku|zwiekszonej szybk?osci ataku|increased attack speed|ias)'),
    ('MF · magiczne przedmioty', '%', r'(?:(?:do )?szansy na zdobycie magicznych przedmiotow|wieksza szansa na znalezienie magicznych przedmiotow|lepsza szansa na znalezienie magicznych przedmiotow|better chance of getting magic items)'),
    ('Kradzież życia', '%', r'(?:(?:zycia|zdrowia) wykrad(?:ane|zione) za kazde trafienie|(?:zycia|zdrowia) za kazde trafienie|life stolen per hit)'),
    ('Kradzież many', '%', r'(?:many wykrad(?:ane|zione) za kazde trafienie|many za kazde trafienie|mana stolen per hit)'),
    ('Regeneracja many', '%', r'(?:do )?regeneracji many|regenerate mana'),
    ('EG · złoto z potworów', '%', r'(?:dodatkowego zlota od potworow|wiecej zlota od potworow|extra gold from monsters|extra gold)'),
    ('Odporność na ogień', '%', r'(?:(?:do )?odpornosci na ogien|odpornosc na ogien|fire resist)'),
    ('Odporność na zimno', '%', r'(?:(?:do )?odpornosci na zimno|odpornosc na zimno|cold resist)'),
    ('Odporność na błyskawice', '%', r'(?:(?:do )?odpornosci na blyskawice|odpornosc na blyskawice|lightning resist)'),
    ('Odporność na truciznę', '%', r'(?:(?:do )?odpornosci na trucizn[ey]|odpornosc na trucizne|poison resist)'),
    ('Wszystkie odporności', '%', r'(?:(?:do )?wszystkich odpornosci|wszystkie odpornosci|all resistances)'),
]

def parse_bonus(line):
    text = normal(str(line)).strip().rstrip('.')
    text = re.sub(r'\s+', ' ', text)
    for label, unit, pattern in RULES:
        number = r'([+-]?\d+(?:[.,]\d+)?)'
        # Require a full match: effects per level, charges, ranges and conditions are not summed.
        suffix = (r'\s*%?' if 'odporności' in label.casefold() or label.startswith('Odporność') else r'\s*%') if unit else ''
        match = re.fullmatch(number + suffix + r'\s*' + pattern, text)
        if not match:
            match = re.fullmatch(pattern + r'\s*:?\s*' + number + suffix, text)
        if match:
            return label, unit, float(match.group(1).replace(',','.'))
    from property_parser import extended_bonus
    return extended_bonus(line)

def group_report(items):
    totals, units, sources = defaultdict(float), {}, defaultdict(list)
    details = []
    unaggregated = {}
    for item in items:
        lines = [str(s) for s in item.get('stats', [])]
        details.append(dict(item, slot_label=SLOTS.get(item.get('character_slot'),'Talizman')))
        for line in lines:
            bonus = parse_bonus(line)
            if bonus:
                label, unit, value = bonus
                totals[label] += value
                units[label] = unit
                sources[label].append(f"{item['name']}: {value:g}{unit}")
            else:
                unaggregated.setdefault(line, []).append(item['name'])
    all_res = totals.get('Wszystkie odporności', 0)
    if all_res:
        for label in ['Odporność na ogień','Odporność na zimno','Odporność na błyskawice','Odporność na truciznę']:
            totals[label] += all_res
            units[label] = '%'
            sources[label] += sources['Wszystkie odporności']
    attrs = totals.get('Wszystkie atrybuty', 0)
    if attrs:
        for label in ['Siła','Zręczność','Żywotność','Energia']:
            totals[label] += attrs
            units[label] = ''
            sources[label] += sources['Wszystkie atrybuty']
    # Keep direct bonuses visible and add effective skill/tree totals as separate rows.
    for label in list(totals):
        if label.startswith(('Drzewko:', 'Umiejętność:', 'Umiejętności klasy:')):
            extra = totals.get('Wszystkie umiejętności', 0)
            inherited = list(sources.get('Wszystkie umiejętności', []))
            if not label.startswith('Umiejętności klasy:'):
                for class_label in list(totals):
                    if class_label.startswith('Umiejętności klasy:') and class_label.split(': ',1)[1] in label:
                        extra += totals[class_label]
                        inherited += sources[class_label]
            effective = label + ' · łącznie'
            totals[effective] = totals[label] + extra
            units[effective] = ''
            sources[effective] = sources[label] + inherited
    return {'items': details, 'unaggregated':[dict(text=text,sources=names) for text,names in unaggregated.items()], 'totals':[dict(label=k,value=f'{v:g}',unit=units[k],sources=sources[k]) for k,v in totals.items() if k not in ('Wszystkie odporności','Wszystkie atrybuty')]}

def character_report(name):
    doll = get_character_equipment(name)
    common = [doll[k] for k in ['head','armor','amulet','gloves','belt','boots','ring1','ring2'] if doll.get(k)] + doll.get('charms',[])
    groups = {'main':group_report(common+[doll[k] for k in ['weapon1','shield1'] if doll.get(k)]),
              'swap':group_report(common+[doll[k] for k in ['weapon2','shield2'] if doll.get(k)]),
              'merc':group_report([doll[k] for k in ['merc_head','merc_armor','merc_weapon','merc_offhand'] if doll.get(k)])}
    return {'character':get_character(name), 'equipment':doll, 'groups':groups}

def alias_key(item):
    return (item.get('name_en') or item.get('name') or '').strip().casefold()

def _ensure_uber_columns(con):
    cols = [c[1] for c in con.execute('PRAGMA table_info(uber_item_details)').fetchall()]
    if 'selected_rolls' not in cols:
        try:
            con.execute('ALTER TABLE uber_item_details ADD COLUMN selected_rolls TEXT DEFAULT ""')
        except Exception:
            pass

def trade_details(item):
    import json, trade_jargon
    with get_db() as con:
        _ensure_uber_columns(con)
        aliases = {(r['kind'], r['source']):r['alias'] for r in con.execute('SELECT * FROM uber_aliases')}
        extra = con.execute('SELECT * FROM uber_item_details WHERE item_id=?',(item['id'],)).fetchone()
    sel_rolls = []
    if extra and extra['selected_rolls']:
        try:
            sel_rolls = json.loads(extra['selected_rolls'])
        except Exception:
            sel_rolls = [s.strip() for s in extra['selected_rolls'].split(',') if s.strip()]
    catalog_info = trade_jargon.find_catalog_entry(item)
    colloquial = trade_jargon.get_colloquial_name(item, use_shorthand=True)
    return {
        'item_alias': aliases.get(('item',alias_key(item)),''),
        'base_alias': aliases.get(('base',(item.get('base') or '').strip().casefold()),''),
        'socket_contents': extra['socket_contents'] if extra else '',
        'trade_stats': extra['trade_stats'] if extra else '',
        'selected_rolls': sel_rolls,
        'rolls_eval': item.get('rolls_eval') or [],
        'colloquial_suggestion': colloquial,
        'catalog_shorthand': catalog_info.get('shorthand','') if catalog_info else '',
        'catalog_variables': catalog_info.get('variables','') if catalog_info else '',
    }

def save_trade_details(item, data):
    import json
    with get_db() as con:
        _ensure_uber_columns(con)
        for kind, key in [('item',alias_key(item)),('base',(item.get('base') or '').strip().casefold())]:
            value = str(data.get(kind+'_alias','')).strip()[:120]
            if key:
                con.execute('INSERT INTO uber_aliases(kind,source,alias) VALUES(?,?,?) ON CONFLICT(kind,source) DO UPDATE SET alias=excluded.alias',(kind,key,value))
        sel_rolls_val = data.get('selected_rolls')
        if isinstance(sel_rolls_val, list):
            sel_rolls_str = json.dumps(sel_rolls_val, ensure_ascii=False)
        else:
            sel_rolls_str = str(sel_rolls_val or '').strip()
        con.execute('INSERT INTO uber_item_details(item_id,socket_contents,trade_stats,selected_rolls) VALUES(?,?,?,?) ON CONFLICT(item_id) DO UPDATE SET socket_contents=excluded.socket_contents,trade_stats=excluded.trade_stats,selected_rolls=excluded.selected_rolls',
                    (item['id'],str(data.get('socket_contents','')).strip()[:500],str(data.get('trade_stats','')).strip()[:2000],sel_rolls_str))

def trade_line(item, lang='pl', include_rolls=True, include_base=True, include_sockets=True, include_price=True, include_notes=True, use_shorthand=False):
    import trade_jargon
    extra = trade_details(item)
    sel_rolls = extra.get('selected_rolls') or None
    if use_shorthand:
        return trade_jargon.format_trade_line(
            item,
            use_shorthand=True,
            selected_rolls=sel_rolls if include_rolls else [],
            include_base=include_base,
            include_sockets=include_sockets,
            include_price=include_price,
            include_notes=include_notes,
            lang=lang
        )
    name = extra['item_alias'] or (item.get('name_en') if lang=='en' else item.get('name')) or item.get('name','')
    quality = normal(item.get('quality',''))
    runeword = any(x in quality for x in ['runeword','runiczne','slowo'])
    parts = [name]
    if include_rolls:
        if extra['trade_stats']:
            parts.append(extra['trade_stats'])
        elif runeword:
            parts.extend(str(x) for x in item.get('stats',[]))
        else:
            rolls = []
            for r in item.get('rolls_eval',[]):
                prop_key = r.get('property') or r.get('property_pl') or r.get('label') or ''
                if sel_rolls and prop_key not in sel_rolls and r.get('label') not in sel_rolls:
                    continue
                if r.get('min') is not None and r.get('max') is not None and r['min'] != r['max']:
                    value = r.get('actual',r.get('roll'))
                    if value is not None:
                        rolls.append(f"{r.get('label') or r.get('property_pl') or r.get('property')}: {value}")
            parts.extend(rolls if item.get('rolls_eval') else [str(x) for x in item.get('stats',[])])
    if include_base and (runeword or quality in ('normalny','normal','superior')) and item.get('base'):
        parts.append(extra['base_alias'] or item['base'])
    if include_sockets and item.get('sockets'):
        parts.append(f"{item['sockets']}os" + (f" [{extra['socket_contents']}]" if extra['socket_contents'] else ''))
    if include_price:
        parts.append(item.get('trade_price') or 'Oferty')
    if include_notes and item.get('trade_notes'):
        parts.append(item['trade_notes'])
    return ' | '.join(parts)
