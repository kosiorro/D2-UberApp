"""GitHub release updater. Checks are read-only; installation is explicitly requested."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import urllib.request
import zipfile

from app_version import VERSION
from release_validation import CATALOG_FILES

REPO = 'kosiorro/D2-UberApp'
API = f'https://api.github.com/repos/{REPO}/releases/latest'
ASSET = 'D2UberApp_Windows_x64.zip'
MAX_DOWNLOAD = 500 * 1024 * 1024
MAX_UNPACKED = 2 * 1024 * 1024 * 1024
_lock = threading.Lock()
_state = dict(status='idle', current=VERSION)
_release = None


def version_tuple(value):
    if not isinstance(value, str) or not re.fullmatch(r'v?\d+\.\d+\.\d+', value):
        raise ValueError('Unsupported release version')
    return tuple(map(int, value.lstrip('v').split('.')))


def select_release(data):
    if data.get('draft') or data.get('prerelease'):
        return None
    tag = data.get('tag_name')
    if version_tuple(tag) <= version_tuple(VERSION):
        return None
    for asset in data.get('assets', []):
        expected = f'https://github.com/{REPO}/releases/download/{tag}/{ASSET}'
        if asset.get('name') == ASSET and asset.get('browser_download_url') == expected:
            digest = asset.get('digest') or ''
            if not re.fullmatch(r'sha256:[a-fA-F0-9]{64}', digest):
                raise ValueError('Missing SHA-256')
            if not isinstance(asset.get('size'), int) or not 0 < asset['size'] <= MAX_DOWNLOAD:
                raise ValueError('Invalid package size')
            return dict(version=tag.lstrip('v'), url=expected, size=asset['size'], sha256=digest[7:].lower())
    raise ValueError('No Windows portable asset')


def snapshot():
    with _lock:
        return {**{k: v for k, v in _state.items() if k != 'folder'},
                'supported': bool(getattr(sys, 'frozen', False) and os.name == 'nt')}


def _set(**values):
    with _lock:
        _state.update(values)


def check():
    with _lock:
        if _state['status'] in ('checking', 'downloading', 'ready', 'installing'):
            return
        _state.update(status='checking')
    threading.Thread(target=_check, daemon=True).start()


def _check():
    global _release
    try:
        req = urllib.request.Request(API, headers={'Accept': 'application/vnd.github+json',
                                                  'User-Agent': 'D2UberApp/' + VERSION})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read(2 * 1024 * 1024))
        release = select_release(data)
        with _lock:
            _release = release
            _state.update(status='available' if release else 'current', latest=release['version'] if release else VERSION)
    except Exception:
        _set(status='check_error')


def extract_package(archive, folder):
    """Validate every member before writing. Only official application files may update."""
    allowed = {'D2UberApp.exe', '_internal', 'templates', 'static', 'skille',
               'README.md', 'LICENSE', 'ExocetReaper-Medium.woff2',
               'Launch_D2_UberApp.bat', 'start.bat', 'Uruchom_D2_UberApp.bat'}
    seen = set()
    entries = []
    with zipfile.ZipFile(archive) as package:
        if sum(i.file_size for i in package.infolist()) > MAX_UNPACKED:
            raise ValueError('Package too large')
        for member in package.infolist():
            name = member.filename
            parts = PurePosixPath(name).parts
            if ('\\' in name or ':' in name or not parts or parts[0] != 'D2UberApp'
                    or any(p in ('..', '.') or p.endswith((' ', '.')) for p in parts)
                    or stat.S_ISLNK(member.external_attr >> 16)):
                raise ValueError('Unsafe archive path')
            if member.is_dir():
                continue
            key = name.casefold()
            if key in seen:
                raise ValueError('Duplicate archive path')
            seen.add(key)
            relative = parts[1:]
            if not relative:
                raise ValueError('Invalid package root')
            if relative[0] == 'data':
                # Keep all user settings, databases and scans. Refresh only shipped catalogs.
                if len(relative) != 2 or relative[1] not in CATALOG_FILES:
                    continue
            elif relative[0] not in allowed:
                raise ValueError('Unexpected application file')
            entries.append((member, Path(*relative)))
        names = {str(rel).replace('\\', '/') for _, rel in entries}
        if 'D2UberApp.exe' not in names or not any(re.fullmatch(r'_internal/python3\d+\.dll', name) for name in names):
            raise ValueError('Incomplete Windows package')
        for member, relative in entries:
            target = folder / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with package.open(member) as source, target.open('wb') as dest:
                shutil.copyfileobj(source, dest)
    return sorted({str(rel.parts[0]) if rel.parts[0] != 'data' else str(rel) for _, rel in entries})


def download_package(release, folder):
    archive = folder / 'update.zip'
    digest = hashlib.sha256()
    total = 0
    req = urllib.request.Request(release['url'], headers={'User-Agent': 'D2UberApp/' + VERSION})
    with urllib.request.urlopen(req, timeout=30) as response, archive.open('wb') as output:
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            total += len(block)
            if total > release['size']:
                raise ValueError('Download size mismatch')
            digest.update(block)
            output.write(block)
    if total != release['size'] or digest.hexdigest() != release['sha256']:
        raise ValueError('Download checksum mismatch')
    return extract_package(archive, folder / 'package')


# All file operations stay in PowerShell, with canonical path checks before moves/deletes.
HELPER = r'''param([string]$Plan)
$ErrorActionPreference = 'Stop'
$p = Get-Content -LiteralPath $Plan -Raw -Encoding UTF8 | ConvertFrom-Json
function ChildPath($root, $relative) {
    $base = [IO.Path]::GetFullPath($root).TrimEnd('\')
    $target = [IO.Path]::GetFullPath((Join-Path $base $relative))
    if (-not $target.StartsWith($base + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe path' }
    return $target
}
$changed = @()
try {
    $process = Get-Process -Id $p.pid -ErrorAction SilentlyContinue
    if ($process) { $process | Wait-Process -Timeout 120 }
} catch {
    'Application is still running. Update cancelled.' | Set-Content -LiteralPath $p.result
    exit 1
}
try {
    foreach ($entry in $p.entries) {
        $source = ChildPath $p.package $entry
        $target = ChildPath $p.target $entry
        $backup = ChildPath $p.backup $entry
        if (Test-Path -LiteralPath $target) {
            if ((Get-Item -LiteralPath $target).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked target' }
            New-Item -ItemType Directory -Force -Path (Split-Path $backup) | Out-Null
            Move-Item -LiteralPath $target -Destination $backup
        }
        $changed += $entry
        New-Item -ItemType Directory -Force -Path (Split-Path $target) | Out-Null
        Move-Item -LiteralPath $source -Destination $target
    }
    'success' | Set-Content -LiteralPath $p.result
} catch {
    $failure = $_.Exception.Message
    [array]::Reverse($changed)
    foreach ($entry in $changed) {
        $target = ChildPath $p.target $entry
        $backup = ChildPath $p.backup $entry
        if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Recurse -Force }
        if (Test-Path -LiteralPath $backup) { Move-Item -LiteralPath $backup -Destination $target }
    }
    $failure | Set-Content -LiteralPath $p.result
}
Start-Process -FilePath (ChildPath $p.target 'D2UberApp.exe') -WorkingDirectory $p.target -WindowStyle Hidden
'''


def prepare():
    with _lock:
        if _state['status'] != 'available' or not _release:
            raise ValueError('No update available')
        if not getattr(sys, 'frozen', False) or os.name != 'nt':
            raise ValueError('Use the installed Windows application')
        release = dict(_release)
        _state.update(status='downloading')
    threading.Thread(target=_prepare, args=(release,), daemon=True).start()


def _prepare(release):
    try:
        import config
        cache = config.BASE_DIR / '.updates'
        cache.mkdir(exist_ok=True)
        folder = Path(tempfile.mkdtemp(prefix='update-', dir=cache)).resolve()
        entries = download_package(release, folder)
        plan = dict(pid=os.getpid(), target=str(config.BASE_DIR.resolve()),
                    package=str(folder / 'package'), backup=str(folder / 'backup'),
                    result=str(cache / 'last-result.txt'), entries=entries)
        for entry in entries:
            target = config.BASE_DIR / entry
            for path in (target, *target.parents):
                if path.is_symlink() or (path.exists() and path.stat().st_file_attributes & 1024):
                    raise ValueError('Linked installation path')
                if path == config.BASE_DIR:
                    break
        (folder / 'plan.json').write_text(json.dumps(plan), encoding='utf-8')
        (folder / 'apply.ps1').write_text(HELPER, encoding='utf-8-sig')
        _set(status='ready', folder=str(folder))
    except Exception:
        _set(status='download_error')


def launch():
    with _lock:
        if _state['status'] != 'ready':
            raise ValueError('Update is not ready')
        folder = Path(_state['folder'])
        subprocess.Popen(['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                          '-File', str(folder / 'apply.ps1'), '-Plan', str(folder / 'plan.json')],
                         creationflags=subprocess.CREATE_NO_WINDOW)
        _state.update(status='installing')
