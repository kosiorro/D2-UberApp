"""Reject release packages containing local application data."""
import json
from pathlib import Path
import sqlite3

CATALOG_FILES = ('armor_bases.json', 'item_bases.json', 'catalog.sqlite', 'stack_catalog.json',
                 'trade_catalog_500.json', 'companion-settings.default.json')


def validate_package(root):
    root = Path(root)
    for path in root.rglob('*'):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        parts = [p.lower() for p in relative.parts]
        if (path.name.lower().startswith(('stash.sqlite', '.env')) or
                any(p in ('screenshots', 'previews') for p in parts) and path.name != '.gitkeep'):
            raise ValueError(f'Private user data in package: {relative}')
        if path.name in ('companion-settings.json', 'companion-settings.default.json'):
            settings = json.loads(path.read_text(encoding='utf-8'))
            if settings.get('api_key') or settings.get('api_key_protected') or settings.get('character') or settings.get('location'):
                raise ValueError(f'Personal settings in package: {relative}')
        if path.name == 'catalog.sqlite':
            with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as db:
                if db.execute("SELECT name FROM sqlite_master WHERE name='user_inventory'").fetchone():
                    if db.execute('SELECT COUNT(*) FROM user_inventory').fetchone()[0]:
                        raise ValueError(f'Personal catalog inventory in package: {relative}')
