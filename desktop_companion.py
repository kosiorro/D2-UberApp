import os
import ctypes
import subprocess
import threading
import time
import webbrowser
import config
from preferences import save
from capture import capture_service as service
from uber_features import select_character

try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('d2uberapp.companion.1.0')
except Exception:
    pass


show_requested = threading.Event()
creator_requested = threading.Event()
_creator_window = None

def free_port(port):
    try:
        import os
        my_pid = os.getpid()
        out = subprocess.check_output('netstat -ano -p tcp', shell=True, text=True)
        for line in out.splitlines():
            parts = line.strip().split()
            if len(parts) >= 5 and f':{port}' in parts[1] and 'LISTENING' in parts[3]:
                pid = int(parts[4])
                if pid > 4 and pid != my_pid:
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
        time.sleep(0.3)
    except Exception:
        pass

def persist(**updates):
    data = dict(config.COMPANION_SETTINGS)
    data.update(
        api_key=config.GEMINI_API_KEY,
        model=config.GEMINI_MODEL,
        hotkey=config.HOTKEY_NAME,
        mode_hotkeys=getattr(config, 'MODE_HOTKEYS', {}),
        sound=config.SOUND_ENABLED,
        autostart=config.CAPTURE_AUTOSTART,
        character=service.current_character,
        mode=service.scan_mode,
        swap=service.is_swap,
        location=service.current_location
    )
    data.update(updates)
    from db import save_stash_location
    save_stash_location(str(data.get('location') or '').strip())
    save(data)
    config.COMPANION_SETTINGS = data

_active_window = None

def exclude_window_from_capture(window=None):
    try:
        user32 = ctypes.windll.user32
        WDA_EXCLUDEFROMCAPTURE = 0x00000011
        import os
        pid = os.getpid()

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        def child_cb(chwnd, _):
            user32.SetWindowDisplayAffinity(chwnd, WDA_EXCLUDEFROMCAPTURE)
            return True
        child_proc = WNDENUMPROC(child_cb)

        def top_cb(hwnd, _):
            wpid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(wpid))
            if wpid.value == pid:
                user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
                user32.EnumChildWindows(hwnd, child_proc, 0)
            return True
        top_proc = WNDENUMPROC(top_cb)

        user32.EnumWindows(top_proc, 0)
    except Exception:
        pass

def set_window_opacity(window, opacity):
    if not window:
        return
    # 1. WinForms native.Opacity
    try:
        if hasattr(window, 'native') and window.native:
            native = window.native
            val = float(opacity)
            if hasattr(native, 'InvokeRequired') and native.InvokeRequired:
                import System
                native.Invoke(System.Action(lambda: setattr(native, 'Opacity', val)))
            elif hasattr(native, 'Opacity'):
                native.Opacity = val
    except Exception:
        pass

    # 2. Win32 SetLayeredWindowAttributes on all windows of our process
    try:
        user32 = ctypes.windll.user32
        import os
        pid = os.getpid()
        WS_EX_LAYERED = 0x00080000
        GWL_EXSTYLE = -20
        LWA_ALPHA = 0x00000002
        GetWindowLongPtr = getattr(user32, 'GetWindowLongPtrW', user32.GetWindowLongW)
        SetWindowLongPtr = getattr(user32, 'SetWindowLongPtrW', user32.SetWindowLongW)
        GetWindowLongPtr.restype = ctypes.c_void_p
        SetWindowLongPtr.restype = ctypes.c_void_p

        alpha = max(30, min(255, int(255 * opacity)))

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        def apply_hwnd(hwnd):
            style = GetWindowLongPtr(hwnd, GWL_EXSTYLE)
            cur = style if isinstance(style, int) else (style or 0)
            if opacity < 0.99:
                SetWindowLongPtr(hwnd, GWL_EXSTYLE, ctypes.c_void_p(cur | WS_EX_LAYERED))
                user32.SetLayeredWindowAttributes(hwnd, 0, alpha, LWA_ALPHA)
            else:
                user32.SetLayeredWindowAttributes(hwnd, 0, 255, LWA_ALPHA)
                SetWindowLongPtr(hwnd, GWL_EXSTYLE, ctypes.c_void_p(cur & ~WS_EX_LAYERED))

        def top_cb(hwnd, _):
            wpid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(wpid))
            if wpid.value == pid:
                apply_hwnd(hwnd)
            return True

        user32.EnumWindows(WNDENUMPROC(top_cb), 0)
    except Exception:
        pass

def set_window_topmost(topmost: bool):
    try:
        user32 = ctypes.windll.user32
        import os
        pid = os.getpid()
        HWND_TOPMOST = -1
        HWND_NOTOPMOST = -2
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_NOACTIVATE = 0x0010
        SWP_SHOWWINDOW = 0x0040

        target = HWND_TOPMOST if topmost else HWND_NOTOPMOST
        flags = SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        def top_cb(hwnd, _):
            wpid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(wpid))
            if wpid.value == pid:
                user32.SetWindowPos(hwnd, target, 0, 0, 0, 0, flags)
            return True

        user32.EnumWindows(WNDENUMPROC(top_cb), 0)
    except Exception:
        pass

class Bridge:
    exiting = False

    def reset_hotkeys(self):
        if service.queue_count or service.processing_lock.locked():
            return {'error': 'Poczekaj na zakończenie skanu.'}
        running = service.is_running
        service.stop()
        try:
            config.HOTKEY_MODIFIERS, config.HOTKEY_VK, config.HOTKEY_NAME = config.parse_hotkey('F10')
            config.MODE_HOTKEYS = dict(config.DEFAULT_MODE_HOTKEYS)
            persist()
            return {'success': True, 'hotkey': config.HOTKEY_NAME, 'mode_hotkeys': config.MODE_HOTKEYS}
        finally:
            if running:
                service.start()

    def open_creator(self):
        creator_requested.set()
        return {'success': True}

    def settings(self):
        return dict(
            hotkey=config.HOTKEY_NAME,
            mode_hotkeys=getattr(config, 'MODE_HOTKEYS', {}),
            model=config.GEMINI_MODEL,
            has_key=bool(config.GEMINI_API_KEY),
            sound=config.SOUND_ENABLED,
            autostart=config.CAPTURE_AUTOSTART,
            location=service.current_location,
            topmost=config.COMPANION_SETTINGS.get('topmost', False),
            lang=config.COMPANION_SETTINGS.get('lang', 'pl'),
            
            regions=config.COMPANION_SETTINGS.get('regions', {'stat_screen': [0, 0, .58, 1], 'runes': [0, 0, .65, .95]})
        )

    def save_settings(self, data):
        if service.queue_count or service.processing_lock.locked():
            return {'error': 'Poczekaj na zakończenie skanu.'}
        key = str(data.get('key', '')).strip() or config.GEMINI_API_KEY
        model = str(data.get('model', '')).strip()
        hotkey = str(data.get('hotkey', '')).strip()
        parsed_hk = config.parse_hotkey(hotkey)
        if not key or not model or not parsed_hk:
            return {'error': 'Sprawdź model, klucz i skrót przechwytywania.'}
        hotkey_mods, hotkey_vk, hotkey_name = parsed_hk

        regions = data.get('regions', {})
        for name in ('stat_screen', 'runes'):
            region = regions.get(name)
            if not isinstance(region, list) or len(region) != 4 or not all(isinstance(x, (int, float)) for x in region):
                return {'error': 'Obszary wymagają czterech liczb: X, Y, szerokość, wysokość.'}
            x, y, w, h = region
            if min(x, y) < 0 or min(w, h) <= 0 or x + w > 1.001 or y + h > 1.001 or w * h >= .99:
                return {'error': 'Obszar musi być wycinkiem ekranu, o współrzędnych od 0 do 1.'}

        raw_mode_hotkeys = data.get('mode_hotkeys', {})
        new_mode_hotkeys = {}
        for m in ('stash', 'character', 'merc', 'runes', 'stat_screen', 'skill_screen', 'gems', 'materials', 'swap', 'toggle_listener', 'toggle_mini'):
            k = str(raw_mode_hotkeys.get(m, '')).strip()
            if not k or k.lower() in ('brak', 'none', ''):
                new_mode_hotkeys[m] = ''
            else:
                parsed_m = config.parse_hotkey(k)
                if not parsed_m:
                    return {'error': f'Nieprawidłowy skrót dla trybu {m}: {k}'}
                new_mode_hotkeys[m] = parsed_m[2]

        running = service.is_running
        service.stop()
        try:
            if service.queue_count or service.processing_lock.locked():
                raise ValueError('Skan właśnie się rozpoczął. Poczekaj na wynik.')
            persist(
                api_key=key,
                model=model,
                hotkey=hotkey_name,
                mode_hotkeys=new_mode_hotkeys,
                sound=bool(data.get('sound')),
                autostart=bool(data.get('autostart')),
                location=str(data.get('location', '')),
                regions=regions
            )
            config.GEMINI_API_KEY = key
            config.GEMINI_MODEL = model
            config.HOTKEY_NAME = hotkey_name
            config.HOTKEY_MODIFIERS = hotkey_mods
            config.HOTKEY_VK = hotkey_vk
            config.MODE_HOTKEYS = new_mode_hotkeys
            config.SOUND_ENABLED = bool(data.get('sound'))
            config.CAPTURE_AUTOSTART = bool(data.get('autostart'))
            service.current_location = str(data.get('location', ''))
            return {'success': True}
        except Exception as error:
            return {'error': str(error)}
        finally:
            if running:
                service.start()

    def appearance(self, topmost, transparent=False):
        try:
            topmost = bool(topmost)
            transparent = bool(transparent)
            persist(topmost=topmost)
            if _active_window:
                try:
                    _active_window.on_top = topmost
                except Exception:
                    pass
                set_window_topmost(topmost)
                opacity = 1.0
                set_window_opacity(_active_window, opacity)
                exclude_window_from_capture(_active_window)

            return {'success': True}
        except Exception as error:
            return {'error': str(error)}

    def set_mini_mode(self, is_mini):
        if _active_window:
            try:
                if is_mini:
                    _active_window.resize(370, 290)
                else:
                    _active_window.resize(430, 730)
            except Exception:
                pass
        return {'success': True}

    def open_web(self, tab='items'):
        if tab not in ('items', 'character', 'runes', 'gems', 'materials', 'trade', 'costs'):
            tab = 'items'
        webbrowser.open(f'http://127.0.0.1:{config.FLASK_PORT}/?tab={tab}')

    def minimize(self):
        if _active_window:
            _active_window.minimize()

    def quit(self):
        if service.queue_count or service.processing_lock.locked():
            return {'error': 'Poczekaj na zakończenie analizy.'}
        service.stop()
        self.exiting = True
        if _active_window:
            _active_window.destroy()
        return {'success': True}

def run(app):
    from werkzeug.serving import make_server
    free_port(config.FLASK_PORT)
    server = make_server('127.0.0.1', config.FLASK_PORT, app, threaded=True)

    threading.Thread(target=server.serve_forever, daemon=True).start()
    app.config['COMPANION_AVAILABLE'] = True

    # Automatically open the web browser to the main UberApp interface
    def _open_browser():
        time.sleep(1.0)
        webbrowser.open(f'http://127.0.0.1:{config.FLASK_PORT}/?tab=items')
    threading.Thread(target=_open_browser, daemon=True).start()

    service.current_character = select_character(config.COMPANION_SETTINGS.get('character', ''))
    service.wizard_active = False

    if config.CAPTURE_AUTOSTART:
        service.start()

    try:
        import webview
        global _active_window
        bridge = Bridge()
        window = webview.create_window(
            'D2 UberApp · Panel',
            f'http://127.0.0.1:{config.FLASK_PORT}/companion',
            js_api=bridge,
            width=430,
            height=730,
            min_size=(320, 200),
            background_color='#0c100d',
            on_top=bool(config.COMPANION_SETTINGS.get('topmost', False)),
            text_select=True
        )
        _active_window = window

        def on_closing():
            bridge.exiting = True
            if _creator_window:
                _creator_window.destroy()
        window.events.closing += on_closing

        def watcher():
            global _creator_window
            key_down = {}
            icon_path = str(config.BASE_DIR / 'static' / 'images' / 'uberapp.ico')
            icon_applied = False
            affinity_applied = False
            while not bridge.exiting:
                if creator_requested.is_set():
                    creator_requested.clear()
                    if _creator_window is None:
                        _creator_window = webview.create_window(
                            'D2 UberApp · Kreator postaci',
                            f'http://127.0.0.1:{config.FLASK_PORT}/character-creator',
                            width=740, height=820, min_size=(520, 500),
                            background_color='#080d09', on_top=True, js_api=bridge)
                        def creator_closed():
                            global _creator_window
                            _creator_window = None
                            from character_creator import close_creator
                            close_creator()
                        _creator_window.events.closed += creator_closed
                        _creator_window.events.loaded += lambda: exclude_window_from_capture()
                    else:
                        _creator_window.on_top = True
                        _creator_window.restore()
                        _creator_window.show()
                context = getattr(service, 'creator_context', None)
                if _creator_window and context:
                    for key in ('I', 'W', 'T'):
                        down = bool(ctypes.windll.user32.GetAsyncKeyState(ord(key)) & 0x8000)
                        if down and not key_down.get(key):
                            service.creator_key = dict(key=key, stage=context['stage'], timestamp=time.time())
                        key_down[key] = down
                if not affinity_applied:
                    exclude_window_from_capture(window)
                    if config.COMPANION_SETTINGS.get('transparent'):
                        set_window_opacity(window, 0.82)
                    affinity_applied = True
                if not icon_applied and os.path.exists(icon_path):
                    try:
                        hwnd = None
                        if hasattr(window, 'native') and hasattr(window.native, 'Handle'):
                            hwnd = int(window.native.Handle)
                        if not hwnd:
                            hwnd = ctypes.windll.user32.FindWindowW(None, 'D2 UberApp · Panel')
                        if hwnd:
                            WM_SETICON = 0x0080
                            ICON_SMALL = 0
                            ICON_BIG = 1
                            IMAGE_ICON = 1
                            LR_LOADFROMFILE = 0x00000010
                            hicon_sm = ctypes.windll.user32.LoadImageW(None, icon_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
                            hicon_lg = ctypes.windll.user32.LoadImageW(None, icon_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE)
                            if hicon_sm:
                                ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_sm)
                            if hicon_lg:
                                ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_lg)
                            icon_applied = True
                    except Exception:
                        pass

                if show_requested.wait(0.05):
                    show_requested.clear()
                    try:
                        window.restore()
                        window.show()
                    except Exception:
                        pass

        webview.start(watcher, icon=str(config.BASE_DIR / 'static/images/uberapp.ico'), debug=False)
    except Exception as e:
        print(f"[UberApp] Okno companion zakonczone: {e}. Serwer WWW dziala pod adresem http://127.0.0.1:{config.FLASK_PORT}")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    finally:
        service.stop()
        server.shutdown()
        app.config['COMPANION_AVAILABLE'] = False
