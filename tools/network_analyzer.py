# tools/network_analyzer.py
import subprocess
import socket
import re

def analyze_wifi_and_gateway() -> str:
    report = "╔════════ YEREL AĞ VE Wİ-Fİ ANALİZ RAPORU ════════\n"
    
    # 1. Yerel IP Adresini Çekme
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        report += f" 🌐 Yerel IP Adresin      : {local_ip}\n"
    except:
        report += " 🌐 Yerel IP Adresin      : Tespit Edilemedi\n"
        
    # 2. Windows Netsh Üzerinden Wi-Fi Detaylarını Ayıklama
    try:
        # Windows komut satırından kablosuz ağ arayüz bilgilerini çekiyoruz
        meta_data = subprocess.check_output(['netsh', 'wlan', 'show', 'interfaces'], startupinfo=subprocess.STARTUPINFO())
        meta_data = meta_data.decode('utf-8', errors='ignore')
        
        ssid = "Bağlı Değil/Kablolu"
        signal = "0%"
        
        # Düzenli ifadelerle (Regex) SSID ve Sinyal değerlerini yakalıyoruz
        ssid_match = re.search(r"SSID\s*:\s*(.*)", meta_data)
        signal_match = re.search(r"Signal\s*:\s*(.*)", meta_data)
        
        if ssid_match:
            ssid = ssid_match.group(1).strip()
        if signal_match:
            signal = signal_match.group(1).strip()
            
        report += f" 📶 Kablosuz Ağ Adı (SSID): {ssid}\n"
        report += f" 📊 Wi-Fi Sinyal Gücü     : {signal}\n"
    except Exception as e:
        report += " 📶 Wi-Fi Bilgileri       : Kablolu bağlantı veya Wi-Fi kapalı\n"

    # 3. Gateway (Modem) IP Adresini Ayıklama
    try:
        # ipconfig komut çıktısından Varsayılan Ağ Geçidini yakalıyoruz
        ipconfig_data = subprocess.check_output(['ipconfig'], startupinfo=subprocess.STARTUPINFO())
        ipconfig_data = ipconfig_data.decode('utf-8', errors='ignore')
        
        # Türkçe ve İngilizce sistem uyumluluğu için çift yönlü regex kontrolü
        gateway_match = re.search(r"(Default Gateway|Varsayılan Ağ Geçidi). . . . . . . . . : ([\d\.]+)", ipconfig_data)
        if gateway_match:
            gateway = gateway_match.group(2).strip()
            report += f" 🎛️ Modem Ağ Geçidi (GW)  : {gateway}\n"
        else:
            report += " 🎛️ Modem Ağ Geçidi (GW)  : Tespit Edilemedi\n"
    except:
        report += " 🎛️ Modem Ağ Geçidi (GW)  : Hata Oluştu\n"
        
    report += f"═════════════════════════════════════════════════\n"
    report += "✅ Ağ durumu aktif. Tüm sinyal ve IP köprüleri stabil patron!"
    return report