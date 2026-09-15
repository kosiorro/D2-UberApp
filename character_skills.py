"""Manual, per-character skill plans, independent of character scanning."""
import json
import re
from functools import lru_cache
from contextlib import closing

from flask import jsonify, request, send_from_directory
import config
import db


def assets_dir():
    local = config.BASE_DIR / 'skille'
    return local if (local / 'skills.json').exists() else config.BUNDLE_DIR / 'skille'


@lru_cache(maxsize=1)
def catalog():
    data = json.loads((assets_dir() / 'skills.json').read_text(encoding='utf-8'))
    layout = json.loads((assets_dir() / 'skills_complete.json').read_text(encoding='utf-8'))
    records = {(s['class'].casefold(), s['name'].casefold()): s for s in layout}
    for skill in data['skills']:
        name = {'Sword Mastery': 'Blade Mastery'}.get(skill['name'], skill['name'])
        rec = records[(skill['class']['name_en'].casefold(), name.casefold())]
        skill['position'] = {'row': rec['row'], 'column': rec['column']}
        skill['game_id'] = rec['id']
        skill['prerequisites'] = rec['reqskills']
    return data


def equipment_bonuses(hero, cls, skills):
    """Only explicit +skill lines; charges, procs and mercenary items are excluded."""
    from property_parser import norm
    equipment = db.get_character_equipment(hero['name'])
    stems = {'amazon':'amazonk', 'sorceress':'czarodziejk', 'necromancer':'nekromant', 'paladin':'paladyn', 'barbarian':'barbarzync', 'druid':'druid', 'assassin':'zabojczyn', 'warlock':'czarnoksiezni'}
    common = [equipment[k] for k in ('head', 'armor', 'amulet', 'gloves', 'belt', 'boots', 'ring1', 'ring2') if equipment.get(k)] + equipment.get('charms', [])
    result = {}
    aliases = {'combat skills': ['umiejetnosci walki', 'umiejetnosci bojowych'],
               'fire spells': ['fire skills', 'zaklec ognia', 'umiejetnosci ognia'],
               'cold spells': ['cold skills', 'zaklec zimna', 'umiejetnosci zimna'],
               'lightning spells': ['lightning skills', 'zaklec blyskawic'],
               'summoning': ['summoning skills', 'przywolywania'],
               'warcries': ['okrzykow'], 'traps': ['pulapek'],
               'offensive auras': ['aur ofensywnych'], 'defensive auras': ['aur defensywnych'],
               'arts of chaos': ['umiejetnosci chaosu'],
               'eldritch weapons': ['umiejetnosci wynaturzenia'],
               'demonic binding': ['umiejetnosci demonicznych', 'umiejetnosci demonow']}
    for mode, slots in [('main', ('weapon1', 'shield1')), ('swap', ('weapon2', 'shield2'))]:
        bonuses = {s['uid']: {'value': 0, 'direct': 0, 'sources': []} for s in skills}
        for item in common + [equipment[k] for k in slots if equipment.get(k)]:
            for line in item.get('stats', []):
                text = norm(line).strip().rstrip('.')
                match = re.fullmatch(r'\+?(\d+)\s+(?:(?:do|to)\s+)?(.+)', text)
                if not match or any(x in text for x in ('chance', 'szansa', 'charges', 'ladunk', '%', 'when ', 'przy traf')):
                    continue
                amount, target = int(match[1]), match[2]
                # Respect class-only suffixes before matching a tree or individual skill.
                restrictions = re.findall(r'\(([^)]*)\)', target)
                if restrictions and not (norm(cls['name_en']) in restrictions[0] or stems[cls['slug']] in restrictions[0]):
                    continue
                target = re.sub(r'\s*\([^)]*\)', '', target).strip()
                all_skills = target in ('all skills', 'all skill levels', 'wszystkich umiejetnosci')
                class_skills = target in [f'{norm(cls["name_en"])} skill levels', f'{norm(cls["name_en"])} skills'] or bool(re.fullmatch(r'umiejetnosci ' + stems[cls['slug']] + r'[a-z]*', target))
                for skill in skills:
                    tree = skill['tree']
                    tree_names = [norm(tree['name_pl']), norm(tree['name_en'])] + aliases.get(norm(tree['name_en']), [])
                    direct = target in (norm(skill['name']), 'umiejetnosci ' + norm(skill['name']))
                    if all_skills or class_skills or target in tree_names or direct:
                        bonus = bonuses[skill['uid']]
                        bonus['value'] += amount
                        if direct:
                            bonus['direct'] += amount
                        bonus['sources'].append(f'{item.get("name", "")}: {line}')
        result[mode] = bonuses
    return result


def character_class(hero):
    name = (hero.get('class_name') or '').strip().casefold()
    if name in ('czarnoksiężnik', 'czarnoksieznik'):
        name = 'warlock'
    return next((c for c in catalog()['classes'] if name in
                 [c[k].casefold() for k in ('slug', 'code', 'name_pl', 'name_en')]), None)


def view(hero):
    cls = character_class(hero) if hero else None
    if not cls:
        return None
    with closing(db.get_db()) as con, con:
        row = con.execute('SELECT points, overrides FROM character_skill_plans WHERE character_id=? AND class_slug=?',
                          (hero['id'], cls['slug'])).fetchone()
    skills = [s for s in catalog()['skills'] if s['class']['slug'] == cls['slug']]
    return {'character': hero['name'], 'level': hero.get('level', 1), 'class': cls,
            'skills': skills, 'bonuses': equipment_bonuses(hero, cls, skills),
            'points': json.loads(row['points']) if row else {},
            'overrides': json.loads(row['overrides']) if row else {}}


def register(app):
    with closing(db.get_db()) as con, con:
        con.execute('''CREATE TABLE IF NOT EXISTS character_skill_plans (
            character_id TEXT NOT NULL, class_slug TEXT NOT NULL, points TEXT NOT NULL,
            PRIMARY KEY (character_id, class_slug))''')
        if 'overrides' not in {r['name'] for r in con.execute('PRAGMA table_info(character_skill_plans)')}:
            con.execute("ALTER TABLE character_skill_plans ADD COLUMN overrides TEXT NOT NULL DEFAULT '{}'")
        con.execute('''CREATE TRIGGER IF NOT EXISTS delete_character_skill_plans
            AFTER DELETE ON characters BEGIN
            DELETE FROM character_skill_plans WHERE character_id=OLD.id; END''')

    @app.get('/skill-assets/<path:filename>')
    def skill_asset(filename):
        return send_from_directory(assets_dir() / 'images', filename)

    @app.post('/api/character/skills')
    def save_character_skills():
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or not isinstance(data.get('character'), str):
            return jsonify(error='Invalid character'), 400
        hero = db.get_character(data['character'])
        if not hero:
            return jsonify(error='Character not found'), 404
        cls = character_class(hero)
        if not cls or data.get('class_slug') != cls['slug']:
            return jsonify(error='Character class changed; reload the page'), 409
        allowed = {s['uid']: s['max_hard_points'] for s in catalog()['skills']
                   if s['class']['slug'] == cls['slug']}
        points = data.get('points')
        overrides = data.get('overrides', {})
        if not isinstance(overrides, dict) or any(
                mode not in ('main', 'swap') or not isinstance(values, dict) or any(
                    uid not in allowed or type(value) is not int or not 0 <= value <= 99
                    for uid, value in values.items()) for mode, values in overrides.items()):
            return jsonify(error='Invalid item bonuses'), 400
        if not isinstance(points, dict) or any(
                key not in allowed or type(value) is not int or not 0 <= value <= allowed[key]
                for key, value in points.items()):
            return jsonify(error='Invalid skill points'), 400
        with closing(db.get_db()) as con, con:
            con.execute('INSERT OR REPLACE INTO character_skill_plans (character_id, class_slug, points, overrides) VALUES (?, ?, ?, ?)',
                        (hero['id'], cls['slug'], json.dumps(points), json.dumps(overrides)))
        return jsonify(status='ok')

    @app.get('/api/character/skills')
    def get_character_skills():
        hero = db.get_character(request.args.get('character', ''))
        plan = view(hero)
        if not plan:
            return jsonify(error='Nie znaleziono postaci lub klasy.'), 404
        return jsonify(plan)
