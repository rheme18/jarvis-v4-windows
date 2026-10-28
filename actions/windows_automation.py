"""
JARVIS Windows — Windows 10/11 Derin Sistem Otomasyonu
Pencere yönetimi, pycaw uygulama ses kontrolü, parlaklık, toast bildirimleri ve güç durumu.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import os
import sys
import psutil
from typing import Any, Dict, List, Optional

# ── Windows API Sabitleri ─────────────────────────────────────────────────────
SW_RESTORE = 9
SW_MINIMIZE = 6
SW_MAXIMIZE = 3
WM_CLOSE = 0x0010


def list_desktop_windows() -> List[Dict[str, Any]]:
    """Görünür tüm Windows pencerelerini listeler."""
    windows = []
    user32 = ctypes.windll.user32

    def enum_proc(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value.strip()
                # Windows kabuk/görünmez pencerelerini filtrele
                if title and title not in ("Default IME", "MSCTFIME UI", "Program Manager", "Settings"):
                    pid = ctypes.wintypes.DWORD()
                    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                    rect = ctypes.wintypes.RECT()
                    user32.GetWindowRect(hwnd, ctypes.byref(rect))
                    w = rect.right - rect.left
                    h = rect.bottom - rect.top
                    if w > 100 and h > 100:
                        windows.append({
                            "hwnd": hwnd,
                            "title": title,
                            "pid": pid.value,
                            "width": w,
                            "height": h,
                        })
        return True

    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    user32.EnumWindows(EnumWindowsProc(enum_proc), 0)
    return windows


def focus_window_by_title(query: str) -> str:
    """Başlığında sorgu geçen pencereyi öne getirir ve odaklar."""
    user32 = ctypes.windll.user32
    target_q = query.lower().strip()
    windows = list_desktop_windows()
    match = None
    for w in windows:
        if target_q in w["title"].lower():
            match = w
            break

    if not match:
        return f"'{query}' başlıklı açık bir pencere bulunamadı Patron."

    hwnd = match["hwnd"]
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetForegroundWindow(hwnd)
    return f"'{match['title']}' penceresi öne getirildi ve odaklandı Patron."


def close_window_by_title(query: str) -> str:
    """Başlığında sorgu geçen pencereyi güvenle kapatır."""
    user32 = ctypes.windll.user32
    target_q = query.lower().strip()
    windows = list_desktop_windows()
    match = None
    for w in windows:
        if target_q in w["title"].lower():
            match = w
            break

    if not match:
        return f"Kapatılacak '{query}' başlıklı pencere bulunamadı Patron."

    user32.PostMessageW(match["hwnd"], WM_CLOSE, 0, 0)
    return f"'{match['title']}' penceresine kapatma sinyali gönderildi Patron."


# ── PyCaw Ses Yönetimi ───────────────────────────────────────────────────────
def get_audio_info() -> Dict[str, Any]:
    """Sistem ana sesini ve aktif uygulama ses oturumlarını listeler."""
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL
        
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
        master_vol = int(round(volume.GetMasterVolumeLevelScalar() * 100))
        is_muted = bool(volume.GetMute())

        app_sessions = []
        sessions = AudioUtilities.GetAllSessions()
        for s in sessions:
            if s.Process:
                p_name = s.Process.name()
                s_vol = s.SimpleAudioVolume
                vol_pct = int(round(s_vol.GetMasterVolume() * 100))
                s_muted = bool(s_vol.GetMute())
                app_sessions.append({
                    "app": p_name,
                    "volume": vol_pct,
                    "muted": s_muted,
                })

        return {
            "master_volume": master_vol,
            "master_muted": is_muted,
            "apps": app_sessions,
        }
    except Exception as exc:
        return {"error": str(exc)}


def set_system_or_app_volume(target: str = "master", level: int = 50) -> str:
    """
    Ana sistem sesini veya belirli bir uygulamanın (örn: Spotify, Chrome) sesini ayarlar.
    level: 0 - 100 arası tamsayı.
    """
    level = max(0, min(100, int(level)))
    scalar = level / 100.0
    target_clean = str(target or "master").lower().strip()

    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL

        if target_clean in ("master", "system", "sistem", "ana"):
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(scalar, None)
            return f"Ana sistem ses düzeyi %{level} yapıldı Patron."

        # Uygulama bazlı ses ayarı
        sessions = AudioUtilities.GetAllSessions()
        matched = []
        for s in sessions:
            if s.Process:
                p_name = s.Process.name().lower()
                if target_clean in p_name:
                    s.SimpleAudioVolume.SetMasterVolume(scalar, None)
                    matched.append(s.Process.name())

        if matched:
            return f"Uygulama ({', '.join(matched)}) ses seviyesi %{level} yapıldı Patron."
        return f"'{target}' adında ses çalan aktif bir uygulama oturumu bulunamadı Patron."
    except Exception as exc:
        return f"Ses ayarı hatası: {exc}"


def toggle_audio_mute(target: str = "master", mute: Optional[bool] = None) -> str:
    """Ana sesi veya belirli bir uygulamayı sessize alır / sesi açar."""
    target_clean = str(target or "master").lower().strip()
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL

        if target_clean in ("master", "system", "sistem", "ana"):
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
            cur = bool(volume.GetMute())
            new_state = (not cur) if mute is None else bool(mute)
            volume.SetMute(int(new_state), None)
            state_str = "sessize alındı" if new_state else "sesi açıldı"
            return f"Ana sistem {state_str} Patron."

        sessions = AudioUtilities.GetAllSessions()
        matched = []
        for s in sessions:
            if s.Process and target_clean in s.Process.name().lower():
                cur = bool(s.SimpleAudioVolume.GetMute())
                new_state = (not cur) if mute is None else bool(mute)
                s.SimpleAudioVolume.SetMute(int(new_state), None)
                matched.append((s.Process.name(), new_state))

        if matched:
            rep = [f"{app}: {'sessiz' if st else 'ses açık'}" for app, st in matched]
            return f"Uygulama ses durumu güncellendi: {', '.join(rep)} Patron."
        return f"'{target}' oturumu bulunamadı."
    except Exception as exc:
        return f"Mute hatası: {exc}"


# ── Ekran Parlaklığı Kontrolü ────────────────────────────────────────────────
def set_display_brightness(level: int) -> str:
    """Ekran parlaklığını ayarlar (0 - 100)."""
    level = max(0, min(100, int(level)))
    try:
        import screen_brightness_control as sbc
        sbc.set_brightness(level)
        return f"Ekran parlaklığı %{level} yapıldı Patron."
    except Exception as exc:
        return f"Parlaklık ayarlanamadı: {exc}"


def get_display_brightness() -> str:
    """Mevcut ekran parlaklığını döndürür."""
    try:
        import screen_brightness_control as sbc
        b = sbc.get_brightness()
        val = b[0] if isinstance(b, list) else b
        return f"Mevcut ekran parlaklığı: %{val} Patron."
    except Exception as exc:
        return f"Parlaklık bilgisi alınamadı: {exc}"


# ── Windows 10/11 Toast Bildirimi ───────────────────────────────────────────
def show_toast_notification(title: str, message: str) -> str:
    """Windows 10/11 sağ alt köşe Toast bildirimi gösterir."""
    try:
        from plyer import notification
        notification.notify(
            title=title or "J.A.R.V.I.S.",
            message=message or "Sistem bildirimi",
            app_name="JARVIS Core",
            timeout=5,
        )
        return f"Bildirim gönderildi: '{title} - {message}'"
    except Exception as exc:
        return f"Bildirim gönderilemedi: {exc}"


# ── Pil ve Güç Durumu ───────────────────────────────────────────────────────
def get_power_status() -> str:
    """Detaylı batarya, şarj ve güç kaynağı raporu."""
    try:
        battery = psutil.sensors_battery()
        if not battery:
            return "Sistem masaüstü güç kaynağına bağlı (Batarya bulunmuyor) Patron."

        percent = battery.percent
        plugged = "Prize takılı (Şarj oluyor)" if battery.power_plugged else "Pilde çalışıyor"
        seconds_left = battery.secsleft
        time_str = ""
        if seconds_left != psutil.POWER_TIME_UNLIMITED and seconds_left > 0:
            hrs = seconds_left // 3600
            mins = (seconds_left % 3600) // 60
            time_str = f" · Tahmini kalan süre: {hrs} saat {mins} dk"

        return f"[PIL DURUMU] %{percent:.0f} · {plugged}{time_str} Patron."
    except Exception as exc:
        return f"Güç bilgisi alınamadı: {exc}"


def snap_window(query: str, side: str = "left") -> str:
    """Pencereyi ekranın sol veya sağ yarısına Windows Snap mantığıyla yerleştirir."""
    wins = list_desktop_windows()
    target = None
    for w in wins:
        if query.lower() in w["title"].lower():
            target = w
            break

    if not target:
        return f"'{query}' başlıklı pencere bulunamadı Patron."

    hwnd = target["hwnd"]
    user32 = ctypes.windll.user32
    # SW_RESTORE (9)
    user32.ShowWindow(hwnd, 9)
    user32.SetForegroundWindow(hwnd)

    # Ekran boyutları
    sw = user32.GetSystemMetrics(0) # SM_CXSCREEN
    sh = user32.GetSystemMetrics(1) # SM_CYSCREEN

    half_w = sw // 2
    x = 0 if side == "left" else half_w
    # SetWindowPos(hwnd, 0, x, y, cx, cy, SWP_NOZORDER | SWP_SHOWWINDOW)
    user32.SetWindowPos(hwnd, 0, x, 0, half_w, sh - 40, 0x0040)
    return f"'{target['title']}' penceresi ekranın {side.upper()} yarısına hizalandı Patron."


def split_screen_dual(left_app: str, right_app: str) -> str:
    """Sol ve sağ uygulamaları aynı anda ikiye bölüp tam çalışma düzeni oluşturur."""
    res_l = snap_window(left_app, "left")
    res_r = snap_window(right_app, "right")
    return f"Ekran düzenlendi Patron:\n• {res_l}\n• {res_r}"


def minimize_all_windows() -> str:
    """Tüm pencereleri küçültüp temiz masaüstünü gösterir."""
    try:
        import win32gui, win32con
        win32gui.PostMessage(win32gui.FindWindow("Shell_TrayWnd", None), win32con.WM_COMMAND, 419, 0)
        return "Tüm pencereler simge durumuna küçültüldü, masaüstü hazır Patron."
    except Exception:
        # Fallback PowerShell
        import subprocess
        subprocess.Popen(["powershell", "-NoProfile", "-Command", "(New-Object -ComObject Shell.Application).MinimizeAll()"])
        return "Masaüstü gösterildi Patron."


def windows_system_control(action: str, **kwargs: Any) -> str:
    """
    Ana Windows derin sistem otomasyon yönlendiricisi.
    action:
      - list_windows
      - focus_window (query)
      - close_window (query)
      - snap_window (query, side='left'/'right')
      - split_screen (left_app, right_app)
      - minimize_all
      - set_volume (level, target='master'/'spotify'/vb.)
      - get_volume
      - mute (target, mute=True/False/None)
      - set_brightness (level)
      - get_brightness
      - toast (title, message)
      - power_status
    """
    act = str(action or "").lower().strip()

    if act == "snap_window":
        q = str(kwargs.get("query") or kwargs.get("title") or "")
        side = str(kwargs.get("side") or "left")
        return snap_window(q, side)

    elif act == "split_screen":
        l_app = str(kwargs.get("left_app") or kwargs.get("left") or "")
        r_app = str(kwargs.get("right_app") or kwargs.get("right") or "")
        return split_screen_dual(l_app, r_app)

    elif act == "minimize_all":
        return minimize_all_windows()

    if act == "list_windows":
        wins = list_desktop_windows()
        if not wins:
            return "Şu an açık görünür pencere bulunamadı Patron."
        lines = [f"🖥️ AÇIK PENCERELER ({len(wins)} Adet):"]
        for w in wins[:12]:
            lines.append(f" • [{w['pid']}] {w['title'][:50]}")
        return "\n".join(lines)

    elif act == "focus_window":
        q = str(kwargs.get("query") or kwargs.get("title") or "")
        return focus_window_by_title(q)

    elif act == "close_window":
        q = str(kwargs.get("query") or kwargs.get("title") or "")
        return close_window_by_title(q)

    elif act == "set_volume":
        target = str(kwargs.get("target") or "master")
        level = kwargs.get("level", 50)
        return set_system_or_app_volume(target, int(level))

    elif act == "get_volume":
        data = get_audio_info()
        if "error" in data:
            return f"Ses bilgisi alınamadı: {data['error']}"
        lines = [f"🔊 Ana Ses: %{data['master_volume']} ({'Sessiz' if data['master_muted'] else 'Açık'})"]
        if data.get("apps"):
            lines.append("Aktif Uygulama Sesleri:")
            for a in data["apps"]:
                lines.append(f" • {a['app']}: %{a['volume']} ({'Mute' if a['muted'] else 'Aktif'})")
        return "\n".join(lines)

    elif act == "mute":
        target = str(kwargs.get("target") or "master")
        mute_val = kwargs.get("mute")
        return toggle_audio_mute(target, mute_val)

    elif act == "set_brightness":
        level = kwargs.get("level", 70)
        return set_display_brightness(int(level))

    elif act == "get_brightness":
        return get_display_brightness()

    elif act == "toast":
        title = str(kwargs.get("title") or "J.A.R.V.I.S.")
        message = str(kwargs.get("message") or "")
        return show_toast_notification(title, message)

    elif act == "power_status":
        return get_power_status()

    return f"Bilinmeyen Windows sistem eylemi: '{action}'. Desteklenenler: list_windows, focus_window, close_window, set_volume, get_volume, mute, set_brightness, get_brightness, toast, power_status."
