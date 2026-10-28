import threading
import time

# Geçici olarak aktif seansı hafızada tutar
study_session = {"remaining": 0, "active": False}

def start_study_timer(duration_minutes: int, task_name: str = "Çalışma") -> str:
    """
    Belirtilen süre kadar bir çalışma seansı başlatır.
    """
    global study_session
    study_session["remaining"] = duration_minutes * 60
    study_session["active"] = True
    
    def timer_thread():
        while study_session["active"] and study_session["remaining"] > 0:
            time.sleep(1)
            study_session["remaining"] -= 1
        
        if study_session["active"]:
            study_session["active"] = False
            # Burada JARVIS'in sesli bildirim tetikleyicisi devreye girer
            print(f"⏰ SEANS BİTTİ: {task_name}")

    threading.Thread(target=timer_thread, daemon=True).start()
    return f"✅ '{task_name}' için {duration_minutes} dakikalık çalışma seansı başlatıldı patron."

def get_timer_status() -> str:
    """Kalan süreyi raporlar."""
    if not study_session["active"]:
        return "Şu an aktif bir çalışma seansı yok patron."
    mins = study_session["remaining"] // 60
    secs = study_session["remaining"] % 60
    return f"Çalışma seansına kalan süre: {mins} dakika {secs} saniye."