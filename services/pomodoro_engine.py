import asyncio
import json
import os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
POMODORO_FILE = BASE_DIR / "pomodoro_report.json"

# Canlı durumu Web Sunucusunun ve JARVIS UI'ın anlık okuyabilmesi için global durum sözlüğü
active_session = {
    "is_active": False,
    "remaining_seconds": 0,
    "total_duration": 0,
    "type": "Work",     # "Work" veya "Break"
    "label": ""
}

def load_pomodoro_data():
    """Yerel JSON rapor dosyasını güvenli şekilde yükler."""
    if not os.path.exists(POMODORO_FILE):
        return []
    try:
        with open(POMODORO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_pomodoro_data(data):
    """Verileri yerel JSON dosyasına hatasız kaydeder."""
    try:
        with open(POMODORO_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[POMODORO ERROR] Veri yazılamadı: {e}")

def log_completed_session(session_type: str, duration_minutes: int, label: str):
    """Başarıyla biten seansı tarih ve etiketle yerel rapora işler."""
    data = load_pomodoro_data()
    log_entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": session_type,
        "duration_minutes": duration_minutes,
        "label": label
    }
    data.append(log_entry)
    save_pomodoro_data(data)

async def run_pomodoro_countdown(minutes: int, session_type: str, label: str, notification_callback=None):
    """Asenkron geri sayım motoru. Web arayüzünü canlı besler ve bitişte bildirim atar."""
    global active_session
    
    # Eğer halihazırda aktif bir seans varsa ezilmesini engelle
    if active_session["is_active"]:
        return "Patron, zaten aktif bir odaklanma seansı koşturuyorum! Önce onun bitmesini beklemeli veya iptal etmelisin."

    seconds = minutes * 60
    active_session["is_active"] = True
    active_session["remaining_seconds"] = seconds
    active_session["total_duration"] = seconds
    active_session["type"] = session_type
    active_session["label"] = label

    print(f"[POMODORO START] {minutes} dakikalık {session_type} seansı başladı ({label}).")

    try:
        while seconds > 0:
            # Dışarıdan veya UI üzerinden bir iptal sinyali gelirse döngüden çık
            if not active_session["is_active"]:
                print("[POMODORO CANCEL] Seans kullanıcı tarafından durduruldu.")
                return "Pomodoro seansı isteğin üzerine iptal edildi patron."
            
            await asyncio.sleep(1)
            seconds -= 1
            active_session["remaining_seconds"] = seconds

        # Döngü başarıyla sıfıra ulaştı
        active_session["is_active"] = False
        
        # Sadece çalışma seanslarını kalıcı rapora kaydet (Molaları istatistiğe eklemiyoruz)
        if session_type == "Work":
            log_completed_session(session_type, minutes, label)
        
        # Windows Bildirimi ve Sesli Uyarı Tetikleyici (Callback)
        if notification_callback:
            if session_type == "Work":
                msg = f"Tebrikler patron! {minutes} dakikalık {label} çalışmasını başarıyla bitirdin. Şimdi mola vakti!"
            else:
                msg = f"Mola süren bitti patron! Zihnini tazelediysen yeni bir çalışma seansına geçmeye ne dersin?"
            notification_callback(msg)
            
        return f"Tebrikler patron! {minutes} dakikalık {label} seansı başarıyla tamamlandı ve rapora işlendi."

    except Exception as e:
        active_session["is_active"] = False
        return f"Pomodoro motorunda bir iç hata oluştu patron: {str(e)}"

def stop_active_pomodoro() -> str:
    """Aktif olan seansı dışarıdan güvenle sonlandırır."""
    global active_session
    if not active_session["is_active"]:
        return "Zaten çalışan aktif bir zamanlayıcı yok patron."
    
    active_session["is_active"] = False
    active_session["remaining_seconds"] = 0
    return "Çalışan zamanlayıcı tamamen sıfırlandı ve durduruldu patron."

def get_pomodoro_stats() -> str:
    """Haftalık/Genel derin odaklanma sürelerini matematiksel ve taktiksel analiz eder."""
    data = load_pomodoro_data()
    if not data:
        return "Henüz tamamlanmış odaklanma seansın yok patron. '25 dakikalık ders başlat' diyerek ilk kaydı oluşturabiliriz!"
        
    total_work = sum(entry["duration_minutes"] for entry in data if entry["type"] == "Work")
    total_sessions = len([entry for entry in data if entry["type"] == "Work"])
    
    # Küçük bir taktiksel analiz (Mühendis-Öğretmen Bakış Açısı)
    analysis = f"📊 **JARVIS Odaklanma ve Derin Çalışma Analizi:**\n"
    analysis += f"- **Başarılı Seans Sayısı:** {total_sessions} adet Pomodoro\n"
    analysis += f"- **Toplam Saf Çalışma:** {total_work} dakika ({round(total_work/60, 1)} saat)\n\n"
    
    if total_work >= 150:
        analysis += "🔥 **Mühendis Notu:** Harika bir ivme yakaladık patron. Odaklanma eşiğin LGS ve kodlama projelerin için mükemmel seviyede!"
    else:
        analysis += "📉 **Öğretmen Notu:** Odaklanma sürelerimiz biraz düşük kalmış patron. Vitesi yavaş yavaş artırarak günlük seans sayısını 4'e çıkarmayı hedefleyelim."
        
    return analysis