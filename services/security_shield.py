import win32evtlog
import win32evtlogutil
import win32security
from datetime import datetime

def check_failed_logins(limit: int = 5) -> list:
    """Windows Güvenlik Günlüklerini tarayarak son başarısız giriş denemelerini (Event ID 4625) bulur."""
    server = 'localhost'
    log_type = 'Security'
    
    failed_attempts = []
    
    try:
        # Güvenlik günlüğünü aç
        hand = win32evtlog.OpenEventLog(server, log_type)
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        
        total = 0
        while True:
            events = win32evtlog.ReadEventLog(hand, flags, 0)
            if not events:
                break
                
            for event in events:
                # Event ID 4625 = Başarısız Oturum Açma Denemesi
                if event.EventID & 0xFFFF == 4625:
                    # Olayın gerçekleştiği zaman
                    time_generated = event.TimeGenerated.Format('%Y-%m-%d %H:%M:%S')
                    
                    # Giriş yapmaya çalışan kullanıcı adı verisini ayıkla
                    strings = event.StringInserts
                    target_user = strings[5] if strings and len(strings) > 5 else "Bilinmeyen Kullanıcı"
                    workstation = strings[13] if strings and len(strings) > 13 else "Bilinmeyen Cihaz"
                    
                    failed_attempts.append({
                        "time": time_generated,
                        "user": target_user,
                        "device": workstation
                    })
                    
                    total += 1
                    if total >= limit:
                        return failed_attempts
                        
            if total >= limit:
                break
                
        return failed_attempts
    except Exception as e:
        print(f"[SECURITY SHIELD ERROR] Günlükler okunamadı: {e}")
        # Eğer yetki hatası alınırsa (Terminal Administrator olarak açılmadıysa) boş liste döner
        return []

def get_security_report_text() -> str:
    """JARVIS'in siber istihbarat raporu sunması için temiz çıktı üretir."""
    # Son 3 başarısız denemeyi kontrol et
    logs = check_failed_logins(3)
    
    report = "🛡️ **JARVIS Siber Güvenlik İstihbarat Raporu:**\n"
    
    if not logs:
        report += "✅ Sistem temiz patron! Yakın zamanda herhangi bir başarısız şifre denemesi veya şüpheli sızıntı izine rastlamadım. Bilgisayarın güvende."
        return report
        
    report += f"⚠️ **ALARM:** Sistemde yakın zamanda **{len(logs)} adet başarısız şifre denemesi** tespit ettim patron!\n\n"
    for idx, log in enumerate(logs, 1):
        report += f"{idx}. 🗓️ Zaman: `{log['time']}` | 👤 Denenen Hesap: `{log['user']}` | 💻 Kaynak Cihaz: `{log['device']}`\n"
        
    report += "\n🔒 **Taktiksel Tavsiye:** Eğer bu denemeleri sen yapmadıysan, biri sen yokken bilgisayarının şifresini zorlamış olabilir. Tetikte olmakta fayda var!"
    return report