import os
import shutil
import subprocess
import sys
from pathlib import Path

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

    dist_dir = BASE_DIR / 'dist'
    build_dir = BASE_DIR / 'build'
    
    # 2. Argumenty PyInstaller
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--noconfirm',
        '--onedir',
        '--name', 'D2UberApp',
        '--add-data', f'{BASE_DIR / "templates"}{os.pathsep}templates',
        '--add-data', f'{BASE_DIR / "static"}{os.pathsep}static',
        '--add-data', f'{BASE_DIR / "data"}{os.pathsep}data',
        '--hidden-import', 'sqlite3',
        '--hidden-import', 'PIL',
        '--hidden-import', 'PIL.Image',
        '--hidden-import', 'PIL.ImageOps',
        '--hidden-import', 'google.genai',
        '--hidden-import', 'flask',
        '--hidden-import', 'jinja2',
        str(BASE_DIR / 'app.py')
    ]

    print('Uruchamianie kompilacji PyInstaller...')
    subprocess.check_call(cmd, cwd=str(BASE_DIR))

    # 3. Kopiuj pomocnicze skrypty startowe i baze do dist/D2UberApp
    target_app_dir = dist_dir / 'D2UberApp'
    if (BASE_DIR / 'start.bat').exists():
        shutil.copy2(BASE_DIR / 'start.bat', target_app_dir)
    if (BASE_DIR / 'README.md').exists():
        shutil.copy2(BASE_DIR / 'README.md', target_app_dir)

    print('\n[SUKCES] Aplikacja skompilowana do folderu:', target_app_dir)
    print('Aby uruchomic na dowolnym Windowsie: dist/D2UberApp/D2UberApp.exe')

    # 4. Spakuj do ZIP
    zip_target = BASE_DIR / 'D2UberApp_Windows_x64'
    print(f'Tworzenie archiwum ZIP: {zip_target}.zip...')
    shutil.make_archive(str(zip_target), 'zip', str(dist_dir), 'D2UberApp')
    print(f'[GOTOWE] Gotowa paczka: {zip_target}.zip')

if __name__ == '__main__':
    build()
