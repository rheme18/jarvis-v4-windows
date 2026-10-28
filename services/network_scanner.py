import asyncio
import re
import subprocess
import platform

# Canlı cihaz bilgisini web sunucusunun çekebilmesi için global değişken
detected_devices = []

async def scan_local_network() -> list:
    """Windows ARP tablosunu asenkron tarayarak bağlı cihazların IP ve MAC adreslerini ayıklar."""
    global detected_devices
    devices = []
    
    try:
        # İşletim sistemi kontrolü (Yalnızca Windows destekliyoruz)
        if platform.system().lower() != "windows":
            return []

        # Windows 'arp -a' komutunu arka planda kilitlenmeden asenkron çalıştır
        proc = await asyncio.create_subprocess_exec(
            'arp', '-a',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode('cp857', errors='ignore') # Türkçe karakter uyumu için

        # IP ve MAC adreslerini yakalamak için Regex (Düzenli İfade)
        # Örn: 192.168.1.1       1a-2b-3c-4d-5e-6f     dinamik
        pattern = re.compile(r'(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+(?P<mac>[0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2})')

        for line in output.splitlines():
            match = pattern.search(line)
            if match:
                ip = match.group('ip')
                mac = match.group('mac').upper().replace(':', '-')
                
                # Gereksiz broadcast veya multicast IP'lerini filtrele
                if ip.startswith("224.") or ip.startswith("239.") or ip.endswith(".255"):
                    continue
                    
                devices.append({"ip": ip, "mac": mac})

        detected_devices = devices
        return devices

    except Exception as e:
        print(f"[NETWORK SCANNER ERROR] Tarama başarısız: {e}")
        return []

def get_network_report_text() -> str:
    """JARVIS'in sesli veya metinsel rapor vermesi için temiz çıktı üretir."""
    global detected_devices
    if not detected_devices:
        return "Şu an ağda etkin bir harici cihaz tespit edemedim patron. Tarayıcıyı tetiklememizi ister misin?"
        
    report = f"🛰️ **Yerel Ağ Tarama Raporu:**\nEvdeki Wi-Fi ağına şu an bağlı toplam **{len(detected_devices)}** cihaz tespit ettim patron:\n"
    for idx, dev in enumerate(detected_devices, 1):
        report += f"{idx}. IP: `{dev['ip']}` | MAC: `{dev['mac']}`\n"
        
    if len(detected_devices) > 5: # Örnek bir eşik değer
        report += "\n⚠️ **Güvenlik Notu:** Ağdaki cihaz sayısı normalden biraz fazla görünüyor patron, yabancı bir sızıntı olup olmadığını kontrol etmek isteyebilirsin."
        
    return report