# tools/ip_scanner.py
import socket
import ssl
import subprocess
import sys
import requests

def scan_ip_network_details(ip: str) -> str:
    report = [f"⚡ [IP SCANNER RAPORU] — {ip}"]
    
    # 1. IP Type Mantığı
    ip_type = "Unknown"
    if ':' in ip: ip_type = "ipv6"
    elif '.' in ip: ip_type = "ipv4"
    report.append(f" 🔹 IP Type: {ip_type}")
    
    # 2. Ping Mantığı
    try:
        ping_cmd = ['ping', '-n', '1', ip] if sys.platform.startswith("win") else ['ping', '-c', '1', '-W', '1', ip]
        res = subprocess.run(ping_cmd, capture_output=True, text=True, timeout=2)
        if res.returncode == 0:
            report.append(" 🔹 Ping Status: 🟢 Success")
        else:
            report.append(" 🔹 Ping Status: 🔴 Failed")
    except:
        report.append(" 🔹 Ping Status: ⚠️ Error execution")

    # 3. Host / ISP / ASN Bilgisi (Orijinal Kod API'si)
    try:
        api = requests.get(f"https://ipapi.co/{ip}/json/", timeout=3).json()
        if not api.get('error'):
            if api.get('org'): report.append(f" 🔹 Host Name: {api.get('org', 'None')}")
            if api.get('org'): report.append(f" 🔹 Host ISP: {api.get('org', 'None')}")
            if api.get('asn'): report.append(f" 🔹 Host AS: {api.get('asn', 'None')}")
    except: pass

    # 4. SSL Sertifika Kontrol Mantığı (Port 443)
    try:
        with socket.create_connection((ip, 443), timeout=2) as sock:
            context = ssl.create_default_context()
            with context.wrap_socket(sock, server_hostname=ip) as ssock:
                cert = ssock.getpeercert()
                report.append(f" 🔹 SSL Certificate: ✅ {str(cert)[:100]}...")
    except Exception as e:
        report.append(f" 🔹 SSL Certificate Check Failed: {str(e)}")
        
    return "\n".join(report)