import os
import ctypes
import comtypes
import subprocess

from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import screen_brightness_control as sbc

def pc_master_control(action, value=None):
    """
    JARVIS Windows PC Kontrol Modülü
    Geliştirilmiş Sürüm: Ses, Parlaklık, Kilit, Uyku, Mikrofon Kapatma, Uygulama Kapatma ve Güç Yönetimi.
    """
    try:
        comtypes.CoInitialize()
        action = str(action).lower().strip()

        # =========================
        # 🔊 SES KONTROLÜ
        # =========================
        if action == "volume":
            if value is None:
                return "Ses seviyesi belirtilmedi patron."

            device = AudioUtilities.GetSpeakers()
            interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))

            vol_val = max(0.0, min(1.0, float(value) / 100.0))
            volume.SetMasterVolumeLevelScalar(vol_val, None)
            return f"Ses seviyesi %{int(value)} olarak ayarlandı."

        # =========================
        # 🎤 MİKROFON SESSİZE ALMA (MUTE/UNMUTE)
        # =========================
        elif action == "mute_mic":
            # Windows Giriş (Mikrofon) Cihazını yakala
            try:
                device = AudioUtilities.GetMicrophone()
                if not device:
                    return "Sistemde aktif bir mikrofon giriş cihazı bulunamadı patron."
                
                interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                mic_volume = cast(interface, POINTER(IAudioEndpointVolume))
                
                # value: True/1 veya "on" ise sessize al, False/0 veya "off" ise sesi aç
                # Eğer value boş geldiyse toggle (tersine çevir) yapalım
                if value is None:
                    current_mute = mic_volume.GetMute()
                    target_mute = not current_mute
                else:
                    target_mute = True if str(value).lower() in ['true', '1', 'on', 'mute'] else False

                mic_volume.SetMute(target_mute, None)
                state_str = "sessize alındı" if target_mute else "sesi açıldı"
                return f"Mikrofon başarıyla {state_str}, patron."
            except Exception as mic_err:
                return f"Mikrofon kontrolü başarısız oldu: {str(mic_err)}"

        # =========================
        # 💡 PARLAKLIK
        # =========================
        elif action == "brightness":
            if value is None:
                return "Parlaklık değeri belirtilmedi patron."

            val = max(0, min(100, int(value)))
            sbc.set_brightness(val)
            return f"Ekran parlaklığı %{val} olarak ayarlandı."

        # =========================
        # 🔒 KİLİT
        # =========================
        elif action == "lock":
            ctypes.windll.user32.LockWorkStation()
            return "Bilgisayar kilitlendi."

        # =========================
        # 😴 UYKU
        # =========================
        elif action == "sleep":
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], check=False)
            return "Sistem uyku moduna alınıyor."

        # =========================
        # ❌ UYGULAMA KAPATMA (CLOSE APP)
        # =========================
        elif action == "close_app":
            if value is None:
                return "Kapatılacak uygulamanın adını belirtmediniz patron."
            
            app_target = str(value).lower().strip()
            
            # Popüler uygulamalar için takma ad (alias) haritası
            app_map = {
                "chrome": "chrome.exe",
                "spotify": "Spotify.exe",
                "discord": "Discord.exe",
                "vs code": "code.exe",
                "vscode": "code.exe",
                "notepad": "notepad.exe",
                "not defteri": "notepad.exe",
                "tarayıcı": "chrome.exe",
                "terminal": "cmd.exe",
                "powershell": "powershell.exe"
            }
            
            exe_name = app_map.get(app_target, app_target if app_target.endswith(".exe") else f"{app_target}.exe")
            
            # Windows taskkill komutunu arka planda güvenle çalıştıralım (/F: Zorla, /IM: Görsel İmaj Adı)
            try:
                creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                result = subprocess.run(
                    ["taskkill", "/F", "/IM", exe_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=creation_flags
                )
                if result.returncode == 0:
                    return f"{exe_name} uygulaması başarıyla sonlandırıldı, patron."
                else:
                    return f"{exe_name} kapatılamadı. Muhtemelen şu an çalışmıyor."
            except Exception as e:
                return f"Uygulama kapatılırken bir hata oluştu: {str(e)}"

        # =========================
        # 📉 TÜM PENCERELERİ SİMGE DURUMUNA GETİR (MASAÜSTÜNÜ GÖSTER)
        # =========================
        elif action == "minimize_all":
            # Windows + D işlevi görür
            ctypes.windll.user32.Keybd_event(0x5B, 0, 0, 0) # Sol Windows Tuşu Basıldı
            ctypes.windll.user32.Keybd_event(0x44, 0, 0, 0) # 'D' Tuşu Basıldı
            ctypes.windll.user32.Keybd_event(0x44, 0, 2, 0) # 'D' Tuşu Bırakıldı
            ctypes.windll.user32.Keybd_event(0x5B, 0, 2, 0) # Sol Windows Tuşu Bırakıldı
            return "Masaüstü gösteriliyor, tüm pencereler simge durumuna küçültüldü."

        # =========================
        # 🛑 SİSTEMİ KAPATMA / YENİDEN BAŞLATMA
        # =========================
        elif action == "shutdown":
            subprocess.run(["shutdown", "/s", "/t", "60"], check=False)
            return "Sistem 1 dakika içinde kapatılacak şekilde zamanlandı, patron."
            
        elif action == "reboot":
            subprocess.run(["shutdown", "/r", "/t", "60"], check=False)
            return "Sistem 1 dakika içinde yeniden başlatılacak şekilde zamanlandı, patron."

        else:
            return f"Tanınmayan işlem katmanı: {action}"

    except Exception as e:
        error_msg = f"PC Kontrol Hatası: {type(e).__name__} - {str(e)}"
        print(f"[JARVIS-ERROR] ❌ {error_msg}")
        return error_msg

    finally:
        try:
            comtypes.CoUninitialize()
        except:
            pass
