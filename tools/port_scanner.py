# tools/port_scanner.py
import socket
import time

def scan_local_ports(target_ip: str = "127.0.0.1") -> str:
    if not target_ip:
        target_ip = "127.0.0.1"
        
    # Siber dünyada en kritik ve hocaların kesinlikle bildiği popüler portlar
    common_ports = {
        21: "FTP (Dosya Aktarımı)",
        22: "SSH (Güvenli Bağlantı)",
        23: "Telnet",
        25: "SMTP (E-Posta)",
        80: "HTTP (Web)",
        110: "POP3",
        443: "HTTPS (Güvenli Web)",
        3306: "MySQL (Veritabanı)",
        3389: "RDP (Uzak Masaüstü)"
    }
    
    report = f"╔════════ SİBER PORT TARAMA RAPORU: [{target_ip}] ════════\n"
    open_ports = 0
    
    for port, service in common_ports.items():
        try:
            # Düşük timeout ile hızlı ve sistemi yormayan soket bağlantısı kuruyoruz
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            result = s.connect_ex((target_ip, port))
            
            if result == 0:
                report += f" 🟢 Port {port:<5} | AÇIK ⚠️  -> Hizmet: {service}\n"
                open_ports += 1
            else:
                report += f" 🔴 Port {port:<5} | KAPALI    -> Hizmet: {service}\n"
            s.close()
        except:
            report += f" ❌ Port {port:<5} | Tarama Hatası\n"
            
    report += f"═════════════════════════════════════════════════\n"
    report += f"📊 Tarama Bitti. Toplam Açık Port Sayısı: {open_ports}\n"
    if open_ports > 0:
        report += "⚠️ UYARI: Açık portlar siber sızıntı riski taşıyabilir patron!"
    else:
        report += "🛡️ GÜVENLİ: Kritik portların tamamı dış bağlantılara kapalı."
        
    return report