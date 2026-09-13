"""Local preferences. The API key is encrypted for the current Windows user."""
import base64
import ctypes
from ctypes import wintypes
import json
from pathlib import Path

PATH = Path(__file__).resolve().parent / 'data' / 'companion-settings.json'

class Blob(ctypes.Structure):
    _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]

def protect(value, decrypt=False):
    raw = base64.b64decode(value) if decrypt else value.encode('utf-8')
    buffer = ctypes.create_string_buffer(raw)
    source = Blob(len(raw), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    target = Blob()
    api = ctypes.windll.crypt32.CryptUnprotectData if decrypt else ctypes.windll.crypt32.CryptProtectData
    if not api(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise OSError('Windows nie może odczytać lub zabezpieczyć klucza API.')
    try:
        result = ctypes.string_at(target.data, target.size)
        return result.decode('utf-8') if decrypt else base64.b64encode(result).decode('ascii')
    finally:
        ctypes.windll.kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        ctypes.windll.kernel32.LocalFree(target.data)

def load():
    if not PATH.exists():
        return {}
    data = json.loads(PATH.read_text(encoding='utf-8'))
    if 'api_key_protected' in data:
        data['api_key'] = protect(data.pop('api_key_protected'), decrypt=True)
    return data

def save(data):
    stored = dict(data)
    stored['api_key_protected'] = protect(stored.pop('api_key'))
    PATH.parent.mkdir(parents=True, exist_ok=True)
    temp = PATH.with_suffix('.tmp')
    temp.write_text(json.dumps(stored, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(PATH)
