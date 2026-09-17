import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from release_validation import CATALOG_FILES, validate_package

BASE_DIR = Path(__file__).resolve().parent

def build():
    print('=============================================')
    print('   D2 UberApp - Budowanie Paczki Wydania')
    print('=============================================')

    # 1. Sprawdz pyinstaller
    try:
        import PyInstaller
    except ImportError:
        print('Instalowanie PyInstaller...')
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])

    dist_root = BASE_DIR / 'dist'
    dist_root.mkdir(exist_ok=True)
    # Never reuse a directory where a previous executable may have saved scans.
    dist_dir = Path(tempfile.mkdtemp(prefix='release-', dir=dist_root))
    build_dir = BASE_DIR / 'build'
    build_dir.mkdir(exist_ok=True)
    # Bundle only static catalogs and defaults, never the developer's live data.
    package_data = Path(tempfile.mkdtemp(prefix='release-data-', dir=build_dir))
    for name in CATALOG_FILES:
        shutil.copy2(BASE_DIR / 'data' / name, package_data / name)
    import sqlite3
    with sqlite3.connect(package_data / 'catalog.sqlite') as catalog:
        catalog.execute('DELETE FROM user_inventory')
        catalog.commit()
        catalog.execute('VACUUM')
    validate_package(package_data)

    icon_path = BASE_DIR / 'static' / 'images' / 'uberapp.ico'

    # 2. Argumenty PyInstaller
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--noconfirm',
        '--onedir',
        '--name', 'D2UberApp',
        '--distpath', str(dist_dir),
        '--add-data', f'{BASE_DIR / "templates"}{os.pathsep}templates',
        '--add-data', f'{BASE_DIR / "static"}{os.pathsep}static',
        '--add-data', f'{package_data}{os.pathsep}data',
        '--add-data', f'{BASE_DIR / "skille"}{os.pathsep}skille',
        '--add-data', f'{BASE_DIR / "ExocetReaper-Medium.woff2"}{os.pathsep}.',
        '--collect-all', 'webview',
        '--collect-all', 'google.genai',
        '--hidden-import', 'sqlite3',
        '--hidden-import', 'PIL',
        '--hidden-import', 'PIL.Image',
        '--hidden-import', 'PIL.ImageOps',
        '--hidden-import', 'google.genai',
        '--hidden-import', 'flask',
        '--hidden-import', 'jinja2',
        '--hidden-import', 'werkzeug',
        '--hidden-import', 'clr',
        '--hidden-import', 'pythonnet',
        '--hidden-import', 'webview',
        '--hidden-import', 'bottle',
        '--hidden-import', 'stack_stash',
        '--hidden-import', 'item_names',
        '--hidden-import', 'translations',
        str(BASE_DIR / 'app.py')
    ]

    if icon_path.exists():
        cmd.extend(['--icon', str(icon_path)])

    print('Uruchamianie kompilacji PyInstaller...')
    subprocess.check_call(cmd, cwd=str(BASE_DIR))

    target_app_dir = dist_dir / 'D2UberApp'

    # 3. Zapewnij dostępność zasobów w głównym katalogu dist/D2UberApp (PyInstaller 6 umieszcza je w _internal)
    for folder in ['templates', 'static', 'data', 'skille']:
        src = package_data if folder == 'data' else BASE_DIR / folder
        dst = target_app_dir / folder
        if src.exists():
            if not dst.exists():
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns('*.tmp', '*.sqlite-shm', '*.sqlite-wal', 'stash.sqlite*'))
            else:
                for item in src.iterdir():
                    target_item = dst / item.name
                    if not target_item.exists() and not item.name.startswith('stash.sqlite') and not item.suffix in ('.tmp', '.shm', '.wal'):
                        if item.is_dir():
                            shutil.copytree(item, target_item)
                        else:
                            shutil.copy2(item, target_item)

    # Inicjalizuj domyślne ustawienia jeśli brak
    dist_data_dir = target_app_dir / 'data'
    dist_data_dir.mkdir(parents=True, exist_ok=True)
    (dist_data_dir / 'screenshots').mkdir(parents=True, exist_ok=True)
    (dist_data_dir / 'previews').mkdir(parents=True, exist_ok=True)

    default_settings = dist_data_dir / 'companion-settings.default.json'
    active_settings = dist_data_dir / 'companion-settings.json'
    if default_settings.exists() and not active_settings.exists():
        shutil.copy2(default_settings, active_settings)

    # 4. Kopiuj pomocnicze skrypty startowe i dokumentację
    for launcher_name in ['Launch_D2_UberApp.bat', 'start.bat', 'Uruchom_D2_UberApp.bat', 'README.md', 'LICENSE', 'ExocetReaper-Medium.woff2']:
        fpath = BASE_DIR / launcher_name
        if fpath.exists():
            shutil.copy2(fpath, target_app_dir)

    validate_package(target_app_dir)
    (build_dir / 'release-package.txt').write_text(str(target_app_dir), encoding='utf-8')
    print('\n[SUKCES] Aplikacja skompilowana do folderu:', target_app_dir)
    print('Aby uruchomic na dowolnym Windowsie: dist/D2UberApp/D2UberApp.exe')

    # 5. Spakuj do ZIP (Wersja Portable)
    zip_target = BASE_DIR / 'D2UberApp_Windows_x64'
    print(f'Tworzenie archiwum ZIP: {zip_target}.zip...')
    shutil.make_archive(str(zip_target), 'zip', str(dist_dir), 'D2UberApp')
    print(f'[GOTOWE] Gotowa paczka: {zip_target}.zip')

if __name__ == '__main__':
    build()
