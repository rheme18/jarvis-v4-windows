# tools/__init__.py
from .declarations import TOOL_DECLARATIONS
import threading

def _get_custom_tool(name: str):
    if name == "track_email_accounts":
        from .email_tracker import track_email_accounts
        return track_email_accounts
    elif name == "get_instagram_profile_osint":
        from .instagram_osint import get_instagram_profile_osint
        return get_instagram_profile_osint
    elif name == "lookup_ip_address":
        from .ip_lookup import lookup_ip_address
        return lookup_ip_address
    elif name == "scan_ip_network_details":
        from .ip_scanner import scan_ip_network_details
        return scan_ip_network_details
    elif name == "lookup_phone_number_details":
        from .phone_lookup import lookup_phone_number_details
        return lookup_phone_number_details
    elif name == "scan_website_secret_urls":
        from .website_scanner import scan_website_secret_urls
        return scan_website_secret_urls
    elif name == "track_username_osint":
        from .username_tracker import track_username_osint
        return track_username_osint
    elif name == "scan_local_ports":
        from .port_scanner import scan_local_ports
        return scan_local_ports
    elif name == "analyze_wifi_and_gateway":
        from .network_analyzer import analyze_wifi_and_gateway
        return analyze_wifi_and_gateway
    elif name == "encrypt_message_aes":
        from .crypter import encrypt_message_aes
        return encrypt_message_aes
    elif name == "decrypt_message_aes":
        from .crypter import decrypt_message_aes
        return decrypt_message_aes
    elif name == "track_stock_market_live":  # <--- BORSA ARACI TAM OLARAK BURADA OLMALI PATRON!
        from .market_tracker import track_stock_market_live
        return track_stock_market_live
    elif name == "domain_whois_lookup":
        from .domain_whois_lookup import domain_whois_lookup
        return domain_whois_lookup
    elif name == "dns_health_check":
        from .dns_health_check import dns_health_check
        return dns_health_check
    elif name == "ssl_certificate_audit":
        from .ssl_certificate_audit import ssl_certificate_audit
        return ssl_certificate_audit
    elif name == "password_strength_audit":
        from .password_strength_audit import password_strength_audit
        return password_strength_audit
    elif name == "file_hash_checker":
        from .file_hash_checker import file_hash_checker
        return file_hash_checker
    elif name == "url_reputation_check":
        from .url_reputation_check import url_reputation_check
        return url_reputation_check
    elif name == "wifi_speed_test":
        from .wifi_speed_test import wifi_speed_test
        return wifi_speed_test
    elif name == "process_risk_scanner":
        from .process_risk_scanner import process_risk_scanner
        return process_risk_scanner
    return None

async def execute_custom_tool(name: str, clean_payload: dict, loop) -> str:
    if name == "open_virus_builder_gui":
        return (
            "Bu kurulumda zararli yazilim uretici araclar guvenlik nedeniyle calistirilmaz. "
            "Savunma, analiz ve risk denetimi icin open_tools_menu veya cyber audit araclarini kullanabilirim."
        )

    if name == "open_tools_menu":
        try:
            from .tools_menu import start_tools_menu
            t = threading.Thread(target=start_tools_menu, daemon=True)
            t.start()
            return "Araçlar menüsü ayrı pencerede açıldı patron."
        except Exception as e:
            return f"Araçlar menüsü başlatılamadı: {str(e)}"

    if name == "open_defense_simulator_gui":
        try:
            from .malware_analyzer_gui import start_defense_gui
            t = threading.Thread(target=start_defense_gui, daemon=True)
            t.start()
            return "☣️ Siber Savunma Laboratuvarı ayrı bir güvenli pencerede başarıyla başlatıldı patron!"
        except Exception as e:
            return f"Hata: Arayüz başlatılamadı: {str(e)}"

    func = _get_custom_tool(name)
    if not func: 
        return f"Hata: {name} aracı siber dizinde bulunamadı patron."
        
    try:
        # Borsa dahil tüm senkron araçlar burada asenkron havuzda (executor) güvenle çalıştırılır
        result = await loop.run_in_executor(None, lambda: func(**clean_payload))
        return result
    except Exception as e:
        return f"Siber araç yürütme hatası [{name}]: {str(e)}"
