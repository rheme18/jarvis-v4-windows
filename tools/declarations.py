# tools/declarations.py

TOOL_DECLARATIONS = [
    {
        "name": "track_email_accounts",
        "description": "Belirtilen e-posta adresinin populer platformlarda kayit izi olup olmadigini OSINT mantigiyla sorgular.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "email": {"type": "STRING", "description": "Sorgulanacak e-posta adresi."}
            },
            "required": ["email"],
        },
    },
    {
        "name": "get_instagram_profile_osint",
        "description": "Belirtilen Instagram kullanici adinin herkese acik profil verilerini analiz eder.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "username": {"type": "STRING", "description": "Sorgulanacak Instagram kullanici adi."}
            },
            "required": ["username"],
        },
    },
    {
        "name": "lookup_ip_address",
        "description": "Belirtilen IP adresinin konum, ISP ve organizasyon bilgilerini sorgular.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "ip": {"type": "STRING", "description": "Sorgulanacak IPv4 veya IPv6 adresi."}
            },
            "required": ["ip"],
        },
    },
    {
        "name": "scan_ip_network_details",
        "description": "Belirtilen IP adresine ping atar, IP tipi ve SSL gibi ag detaylarini tarar.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "ip": {"type": "STRING", "description": "Taranacak hedef IP adresi."}
            },
            "required": ["ip"],
        },
    },
    {
        "name": "lookup_phone_number_details",
        "description": "Uluslararasi formattaki telefon numarasinin gecerlilik, operator, ulke ve bolge bilgisini sorgular.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "phone_number": {"type": "STRING", "description": "Sorgulanacak telefon numarasi. Ornek: +905XXXXXXXXX"}
            },
            "required": ["phone_number"],
        },
    },
    {
        "name": "scan_website_secret_urls",
        "description": "Hedef web sitesinin kaynak kodundan acik dahili/harici URL baglantilarini listeler.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "url": {"type": "STRING", "description": "Taranacak web sitesi URL'si. Ornek: example.com"}
            },
            "required": ["url"],
        },
    },
    {
        "name": "track_username_osint",
        "description": "Hedef kullanici adinin Jarvis OSINT araclarindaki platform izlerini tarar.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "username": {"type": "STRING", "description": "Sorgulanacak kullanici adi."}
            },
            "required": ["username"],
        },
    },
    {
        "name": "open_virus_builder_gui",
        "description": "Guvenlik nedeniyle zararli yazilim uretimini reddeder ve savunma/analiz araclarina yonlendirir.",
        "parameters": {"type": "OBJECT", "properties": {}, "required": []},
    },
    {
        "name": "scan_local_ports",
        "description": "Belirtilen IP veya localhost uzerindeki kritik portlari tarar.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "target_ip": {"type": "STRING", "description": "Taranacak hedef IP adresi. Varsayilan: 127.0.0.1"}
            },
            "required": ["target_ip"],
        },
    },
    {
        "name": "analyze_wifi_and_gateway",
        "description": "Bagli olunan Wi-Fi aginin SSID, sinyal, yerel IP ve gateway detaylarini analiz eder.",
        "parameters": {"type": "OBJECT", "properties": {}, "required": []},
    },
    {
        "name": "encrypt_message_aes",
        "description": "Belirtilen hassas metni AES/Fernet ile sifreler ve gizli anahtar uretir.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "message": {"type": "STRING", "description": "Sifrelenecek metin veya mesaj."}
            },
            "required": ["message"],
        },
    },
    {
        "name": "decrypt_message_aes",
        "description": "AES/Fernet ile sifrelenmis metni dogru gizli anahtar ile cozer.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "cipher_text": {"type": "STRING", "description": "Cozulecek sifreli metin."},
                "secret_key": {"type": "STRING", "description": "Sifreyi cozmek icin gereken gizli anahtar."},
            },
            "required": ["cipher_text", "secret_key"],
        },
    },
    {
        "name": "track_stock_market_live",
        "description": "BIST, doviz, altin ve populer hisseler icin canli piyasa ozeti verir.",
        "parameters": {"type": "OBJECT", "properties": {}, "required": []},
    },
    {
        "name": "domain_whois_lookup",
        "description": "Domain icin DNS cozumu ve temel SSL kimlik bilgilerini raporlar.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "domain": {"type": "STRING", "description": "Sorgulanacak domain. Ornek: example.com"}
            },
            "required": ["domain"],
        },
    },
    {
        "name": "dns_health_check",
        "description": "Domain icin A/AAAA, MX, NS ve TXT DNS kayitlarini kontrol eder.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "domain": {"type": "STRING", "description": "DNS kayitlari kontrol edilecek domain."}
            },
            "required": ["domain"],
        },
    },
    {
        "name": "ssl_certificate_audit",
        "description": "Bir hostun SSL/TLS sertifika suresini, verenini ve TLS bilgilerini denetler.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "hostname": {"type": "STRING", "description": "SSL denetimi yapilacak host."},
                "port": {"type": "NUMBER", "description": "Port. Varsayilan 443."},
            },
            "required": ["hostname"],
        },
    },
    {
        "name": "password_strength_audit",
        "description": "Parolanin gucunu yerel olarak analiz eder; parola dis servise gonderilmez.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "password": {"type": "STRING", "description": "Analiz edilecek parola."}
            },
            "required": ["password"],
        },
    },
    {
        "name": "file_hash_checker",
        "description": "Bir dosyanin SHA256/MD5 gibi hash degerini hesaplar.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "file_path": {"type": "STRING", "description": "Hash alinacak dosya yolu."},
                "algorithm": {"type": "STRING", "description": "sha256 | md5 | sha1 vb. Varsayilan sha256."},
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "url_reputation_check",
        "description": "URL icin basit phishing/risk sinyallerini ve HTTP durumunu kontrol eder.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "url": {"type": "STRING", "description": "Kontrol edilecek URL."}
            },
            "required": ["url"],
        },
    },
    {
        "name": "wifi_speed_test",
        "description": "Kucuk bir indirme testiyle yaklasik internet hizini olcer.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "test_url": {"type": "STRING", "description": "Opsiyonel test dosyasi URL'si."}
            },
        },
    },
    {
        "name": "process_risk_scanner",
        "description": "Calisan Windows surecleri icin basit risk sinyalleri taramasi yapar.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "limit": {"type": "NUMBER", "description": "Listelenecek maksimum bulgu sayisi."}
            },
        },
    },
    {
        "name": "open_tools_menu",
        "description": "JARVIS araclar menusu UI penceresini acar. Kullanici 'araclar menusu', 'tool menusu' veya 'tools menu ac' dediginde kullan.",
        "parameters": {"type": "OBJECT", "properties": {}, "required": []},
    },
]
