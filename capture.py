import time
import uuid
import ctypes
import threading
import winsound
from ctypes import wintypes
from pathlib import Path
from PIL import Image
import numpy as np

from config import SCREENSHOTS_DIR, PREVIEWS_DIR
import config
from db import insert_item, check_for_duplicate, calculate_file_hash, get_character_equipment
from ai_processor import process_image

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

HOTKEY_ID = 200
MOD_NOREPEAT = 0x4000

MODE_MAP = {
    'stash': 211,
    'character': 212,
    'merc': 213,
    'runes': 214,
    'stat_screen': 215,
}
ID_TO_MODE = {v: k for k, v in MODE_MAP.items()}


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ('biSize', wintypes.DWORD), ('biWidth', wintypes.LONG), ('biHeight', wintypes.LONG),
        ('biPlanes', wintypes.WORD), ('biBitCount', wintypes.WORD), ('biCompression', wintypes.DWORD),
        ('biSizeImage', wintypes.DWORD), ('biXPelsPerMeter', wintypes.LONG), ('biYPelsPerMeter', wintypes.LONG),
        ('biClrUsed', wintypes.DWORD), ('biClrImportant', wintypes.DWORD)
    ]

def exclude_companion_from_capture():
    try:
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

def capture_screen() -> Image.Image:
    exclude_companion_from_capture()
    width = user32.GetSystemMetrics(0)
    height = user32.GetSystemMetrics(1)
    
    hdc_screen = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
    hbmp = gdi32.CreateCompatibleBitmap(hdc_screen, width, height)
    gdi32.SelectObject(hdc_mem, hbmp)
    
    gdi32.BitBlt(hdc_mem, 0, 0, width, height, hdc_screen, 0, 0, 0x00CC0020)
    
    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = width
    bmi.biHeight = -height
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0
    
    buffer = ctypes.create_string_buffer(width * height * 4)
    gdi32.GetDIBits(hdc_mem, hbmp, 0, height, buffer, ctypes.byref(bmi), 0)
    image = Image.frombuffer('RGBA', (width, height), buffer, 'raw', 'BGRA', 0, 1)
    
    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(0, hdc_screen)
    return image

def _detect_text_cluster_tooltip(arr, mode='normal'):
    h, w, _ = arr.shape
    is_bright = (np.max(arr, axis=2) >= 70) & (np.min(arr, axis=2) >= 8)
    is_bright[:45, :] = False
    is_bright[h-80:, :] = False
    is_bright[:, :40] = False
    is_bright[:, w-40:] = False

    lines = []
    for y in range(45, h - 80):
        cols = np.where(is_bright[y])[0]
        if len(cols) >= 12:
            diffs = np.diff(cols)
            splits = np.where(diffs > 35)[0] + 1
            for g in np.split(cols, splits):
                if len(g) >= 12 and (g[-1] - g[0]) >= 40:
                    lines.append((y, g[0], g[-1], (g[0] + g[-1]) / 2, g[-1] - g[0]))

    if not lines:
        return None

    clusters = []
    for l in lines:
        y, x0, x1, xc, width = l
        matched = False
        for c in clusters:
            last_l = c[-1]
            gap = y - last_l[0]
            if 1 <= gap <= 32 and abs(xc - c[0][3]) <= 40:
                c.append(l)
                matched = True
                break
        if not matched:
            clusters.append([l])

    best_cluster_crop = None
    best_cluster_score = 0
    for c in clusters:
        rows = sorted(set(l[0] for l in c))
        if len(rows) >= 28:
            ymin = min(rows)
            ymax = max(rows)
            height = ymax - ymin
            if 45 <= height <= int(h * 0.70):
                xmin = min(l[1] for l in c)
                xmax = max(l[2] for l in c)
                width = xmax - xmin
                if 80 <= width <= int(w * 0.70):
                    pad_x = 35
                    pad_y = 25
                    bx = max(0, xmin - pad_x)
                    by = max(0, ymin - pad_y)
                    bw = min(w - bx, width + 2 * pad_x)
                    bh = min(h - by, height + 2 * pad_y)
                    sub = arr[by:by+bh, bx:bx+bw]
                    dark_ratio = np.mean(np.max(sub, axis=2) <= 30)
                    text_ratio = np.mean(np.max(sub, axis=2) >= 70)
                    if dark_ratio >= 0.35 and 0.01 <= text_ratio <= 0.35:
                        score = len(rows) * width
                        if score > best_cluster_score:
                            best_cluster_score = score
                            best_cluster_crop = (int(bx), int(by), int(bw), int(bh))

    return best_cluster_crop


def _detect_dark_tooltip_rectangle(arr):
    h, w, _ = arr.shape
    is_dark = np.max(arr, axis=2) <= 24
    row_runs = []
    min_w = int(w * 0.10)
    
    # Exclude title bar (y < 45) and bottom HUD (y > h - 80)
    for y in range(45, h - 80):
        row = is_dark[y]
        diff = np.diff(np.pad(row.astype(np.int8), (1, 1)))
        starts = np.where(diff == 1)[0]
        ends = np.where(diff == -1)[0]
        
        merged = []
        for s, e in zip(starts, ends):
            if not merged:
                merged.append([s, e])
            else:
                if s - merged[-1][1] <= 24: # text gap
                    merged[-1][1] = e
                else:
                    merged.append([s, e])
        for s, e in merged:
            if (e - s) >= min_w:
                row_runs.append((y, s, e))
                
    if not row_runs:
        return None
        
    from collections import defaultdict
    by_start = defaultdict(list)
    for y, s, e in row_runs:
        s_bin = round(s / 20) * 20
        by_start[s_bin].append((y, s, e))
        
    best_candidate = None
    best_score = 0
    
    for s_bin, runs in by_start.items():
        if s_bin <= 20: # Exclude extreme screen bezels
            continue
        if len(runs) >= 35:
            runs_y = [r[0] for r in runs]
            ymin = min(runs_y)
            ymax = max(runs_y)
            height = ymax - ymin
            if 55 <= height <= int(h * 0.70) and len(runs) / height >= 0.50:
                s_val = int(np.median([r[1] for r in runs]))
                e_val = int(np.median([r[2] for r in runs]))
                width = e_val - s_val
                
                # Exclude edge bezels
                if s_val >= int(w * 0.82) or width < 200:
                    continue
                
                sub = arr[ymin:ymax, s_val:e_val]
                text_mask = np.max(sub, axis=2) >= 70
                text_ratio = np.mean(text_mask)
                dark_ratio = np.mean(np.max(sub, axis=2) <= 26)
                
                if 0.01 <= text_ratio <= 0.35 and dark_ratio >= 0.35:
                    score = width * height
                    if score > best_score:
                        best_score = score
                        best_candidate = (s_val, ymin, width, height)
                        
    return best_candidate


def find_tooltip_crop(img: Image.Image, strict=False, mode='normal') -> tuple[int, int, int, int] | None:
    arr = np.array(img.convert("RGB"))
    h, w, _ = arr.shape
    
    # 1. Framed tooltip detector (horizontal edge lines with gray border)
    edges = []
    min_len = int(w * 0.10)
    
    # Exclude title bar (y < 45) and bottom HUD (y > h - 80)
    for y in range(45, h - 80):
        row = arr[y]
        diffs = np.max(np.abs(np.diff(row.astype(int), axis=0)), axis=1)
        run_mask = diffs <= 2
        diff = np.diff(np.pad(run_mask.astype(np.int8), (1, 1)))
        starts = np.where(diff == 1)[0]
        ends = np.where(diff == -1)[0]
        for s, e in zip(starts, ends):
            length = e - s
            if length >= min_len and s >= 15 and s + length <= w - 15:
                pix = row[s + length // 2]
                r, g, b = int(pix[0]), int(pix[1]), int(pix[2])
                if 20 <= r <= 130 and abs(r - g) <= 20 and abs(g - b) <= 20:
                    edges.append((y, s, length))
                    
    best = None
    best_area = 0
    for i, (y1, s1, l1) in enumerate(edges):
        for y2, s2, l2 in edges[i+1:]:
            height = y2 - y1
            if 65 <= height <= int(h * 0.70):
                if abs(s1 - s2) <= 12 and abs(l1 - l2) <= 18:
                    area = min(l1, l2) * height
                    if area > best_area:
                        bx, by, bw, bh = (int(min(s1, s2)), int(y1), int(min(l1, l2)), int(height))
                        sub = arr[by+5:by+bh-5, bx+5:bx+bw-5]
                        if sub.size > 0:
                            dark_ratio = np.mean(np.max(sub, axis=2) < 32)
                            text_ratio = np.mean(np.max(sub, axis=2) >= 70)
                            if dark_ratio > 0.40 and 0.01 <= text_ratio <= 0.35:
                                best_area = area
                                best = (bx, by, bw, bh)
                        
    if best:
        return best

    if strict or mode == 'stash':
        return None

    # 2. Text cluster detector for equipped / borderless items (character & mercenary)
    cluster_box = _detect_text_cluster_tooltip(arr, mode=mode)
    if cluster_box:
        return cluster_box

    # 3. Dark / borderless tooltip rectangle detector
    dark_box = _detect_dark_tooltip_rectangle(arr)
    if dark_box:
        return dark_box
            
    return None

SFX_DIR = Path(__file__).parent / "static" / "sfx"

def play_sound(sound_type="gem"):
    if not config.SOUND_ENABLED:
        return
    try:
        if sound_type in ("error", "fail", "rejected"):
            wav = SFX_DIR / "error.wav"
            if wav.exists():
                winsound.PlaySound(str(wav), winsound.SND_FILENAME | winsound.SND_ASYNC)
                return
            else:
                winsound.Beep(330, 180)
                winsound.Beep(260, 260)
                return
        elif sound_type in ("pickup", "success"):
            wav = SFX_DIR / "pickup.wav"
        elif sound_type in ("drop", "item"):
            wav = SFX_DIR / "drop.wav"
        elif sound_type == "rune":
            wav = SFX_DIR / "rune.wav"
        elif sound_type == "armor":
            wav = SFX_DIR / "armor.wav"
        elif sound_type == "ring":
            wav = SFX_DIR / "ring.wav"
        elif sound_type == "gem":
            wav = SFX_DIR / "gem.wav"
        elif sound_type == "duplicate":
            wav = SFX_DIR / "ring.wav"
        else:
            wav = SFX_DIR / "drop.wav"

        if wav.exists():
            winsound.PlaySound(str(wav), winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            winsound.Beep(1200, 100)
    except Exception:
        pass



class CaptureService:
    def __init__(self):
        self.is_running = False
        self.thread = None
        self.processing_lock = threading.Lock()
        self.offhand = False
        self.last_status = "Zatrzymany"
        self.total_captured = 0
        self.current_location = config.COMPANION_SETTINGS.get("location", "")
        self.scan_mode = config.COMPANION_SETTINGS.get("mode", "stash")
        if self.scan_mode == "normal":
            self.scan_mode = "stash"
        self.current_character = config.COMPANION_SETTINGS.get("character", "Moja Postać")
        self.is_swap = config.COMPANION_SETTINGS.get("swap", False)
        self.last_stat_scan = None
        self.wizard_active = False
        self.queue_count = 0
        self.activity_log = []
        self.last_activity = {
            "state": "idle",
            "message": f"Gotowy. Oczekiwanie na klawisz {config.HOTKEY_NAME} w grze...",
            "item_name": "",
            "timestamp": time.time(),
            "queue_count": 0
        }

    def _add_log(self, text: str, status: str = "OK"):
        now_str = time.strftime("%H:%M:%S")
        self.activity_log.insert(0, {"time": now_str, "text": text, "status": status})
        if len(self.activity_log) > 12:
            self.activity_log.pop()

    def set_location(self, loc: str):
        self.current_location = (loc or "").strip()
        print(f"[Serwis] Ustawiono aktywną lokalizację na: '{self.current_location}'")

    def set_scan_mode(self, mode: str):
        if mode in ("character", "stat_screen", "runes", "stash", "merc"):
            self.scan_mode = mode
        else:
            self.scan_mode = "stash"
        print(f"[Serwis] Ustawiono tryb skanowania na: '{self.scan_mode}'")

    def set_character(self, char_name: str):
        if char_name and char_name.strip():
            self.current_character = char_name.strip()
            print(f"[Serwis] Ustawiono aktywną postać na: '{self.current_character}'")

    def set_swap(self, is_swap: bool):
        self.is_swap = bool(is_swap)
        print(f"[Serwis] Swap broni/tarczy: {'SWAP II' if self.is_swap else 'GŁÓWNY I'}")

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.last_status = "Uruchamianie nasłuchu..."
        self.thread.start()

    def stop(self):
        self.is_running = False
        if self.thread and self.thread is not threading.current_thread():
            self.thread.join()
        self.last_status = "Zatrzymany"

    def _process_screen(self):
        from scan_pipeline import run_capture
        run_capture(self)

    def _safe_process_screen(self):
        if not self.processing_lock.acquire(blocking=False):
            return
        if self.queue_count:
            self._add_log("Poczekaj na zakończenie poprzedniego skanu.", "Zajęty")
            self.processing_lock.release()
            return
        try:
            self._process_screen()
        except Exception as e:
            print(f"[BŁĄD F10] {e}")
            import traceback
            traceback.print_exc()
            self.queue_count = max(0, self.queue_count - 1)
            self.last_activity = {
                "state": "error",
                "message": f"Błąd przechwytywania: {str(e)[:40]}",
                "item_name": "Błąd",
                "timestamp": time.time(),
                "queue_count": self.queue_count
            }
            self._add_log(f"Błąd zrzutu: {str(e)[:30]}", "Błąd")

        finally:
            self.processing_lock.release()

    def _run_loop(self):
        registered_ids = []
        hk_mods = getattr(config, 'HOTKEY_MODIFIERS', MOD_NOREPEAT)
        hk_vk = getattr(config, 'HOTKEY_VK', 0x79)
        hk_name = getattr(config, 'HOTKEY_NAME', 'F10')

        if not user32.RegisterHotKey(None, HOTKEY_ID, hk_mods, hk_vk):
            self.last_status = f"Błąd rejestracji {hk_name} (skrót zajęty)"
            self.is_running = False
            return
        registered_ids.append(HOTKEY_ID)

        mode_hotkeys = getattr(config, 'MODE_HOTKEYS', {})
        for mode, hk_id in MODE_MAP.items():
            key_name = str(mode_hotkeys.get(mode, '')).strip()
            if key_name:
                parsed = config.parse_hotkey(key_name)
                if parsed:
                    m_mods, m_vk, _ = parsed
                    if (m_mods, m_vk) != (hk_mods, hk_vk):
                        if user32.RegisterHotKey(None, hk_id, m_mods, m_vk):
                            registered_ids.append(hk_id)

        self.last_status = f"Aktywny (Skrót: {hk_name})"
        print(f"[Serwis F10] Nasłuch aktywny. Naciśnij {hk_name} w grze.")
        msg = wintypes.MSG()
        try:
            while self.is_running:
                if user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                    if msg.message == 0x0312:
                        if msg.wParam == HOTKEY_ID:
                            # Dzwiek potwierdzenia
                            try:
                                play_sound("gem")
                            except Exception:
                                pass
                            # Asynchroniczne przetwarzanie zrzutu ekranu
                            threading.Thread(target=self._safe_process_screen, daemon=True).start()
                        elif msg.wParam in ID_TO_MODE:
                            target_mode = ID_TO_MODE[msg.wParam]
                            self.set_scan_mode(target_mode)
                            mode_labels = {
                                'stash': 'Skrzynia',
                                'character': 'Postać',
                                'merc': 'Najemnik',
                                'runes': 'Runy',
                                'stat_screen': 'Statystyki'
                            }
                            label = mode_labels.get(target_mode, target_mode)
                            self._add_log(f"Skrót: Tryb {label}", "Tryb")
                            try:
                                play_sound("gem")
                            except Exception:
                                pass
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))
                else:
                    time.sleep(0.01)
        finally:
            for hid in registered_ids:
                try:
                    user32.UnregisterHotKey(None, hid)
                except Exception:
                    pass
            print(f"[Serwis F10] Skróty zwolnione.")


capture_service = CaptureService()
