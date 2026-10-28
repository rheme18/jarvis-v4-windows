# tools/ip_lookup.py
import requests

def lookup_ip_address(ip: str) -> str:
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        api = response.json()
        
        status = "Valid" if api.get('status') == "success" else "Invalid"
        if status == "Invalid":
            return f"❌ {ip} geçersiz bir IP adresi patron."
            
        report = [
            f"🌐 [IP LOOKUP RAPORU] — {ip}",
            f" 🔹 Status    : {status}",
            f" 🔹 Country   : {api.get('country', 'None')} ({api.get('countryCode', 'None')})",
            f" 🔹 Region    : {api.get('regionName', 'None')} ({api.get('region', 'None')})",
            f" 🔹 Zip       : {api.get('zip', 'None')}",
            f" 🔹 City      : {api.get('city', 'None')}",
            f" 🔹 Latitude  : {api.get('lat', 'None')}",
            f" 🔹 Longitude : {api.get('lon', 'None')}",
            f" 🔹 Timezone  : {api.get('timezone', 'None')}",
            f" 🔹 Isp       : {api.get('isp', 'None')}",
            f" 🔹 Org       : {api.get('org', 'None')}",
            f" 🔹 As        : {api.get('as', 'None')}"
        ]
        return "\n".join(report)
    except Exception as e:
        return f"❌ IP API sorgulama hatası: {str(e)}"