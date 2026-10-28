"""
JARVIS — Gemini Live araç (tool) tanımları
Windows masaüstü çekirdeği (main.py) kullanır.
"""

TOOL_DECLARATIONS = [
{
        "name": "db_save",
        "description": "Kullanıcının sesli veya yazılı söylediği günlük notlarını, kişisel bilgilerini, hatırlatmalarını, rehber kişilerini ve proje detaylarını SQLite veritabanına kaydeder.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "category": {
                    "type": "STRING",
                    "description": "Kayıt kategorisi: 'journal' (günlük), 'note' (not), 'contact' (kişi rehberi), 'project' (proje detayları)."
                },
                "content": {
                    "type": "STRING",
                    "description": "Kaydedilecek metin, not veya günlük içeriği."
                },
                "title": {
                    "type": "STRING",
                    "description": "Kayıt için kısa bir başlık veya konu adı."
                },
                "tags": {
                    "type": "STRING",
                    "description": "Virgülle ayrılmış arama etiketleri (örn: 'okul, lgs, matematik')."
                }
            },
            "required": ["category", "content"]
        }
    },
    {
        "name": "db_search",
        "description": "Kişisel veritabanında geçmiş günlük kayıtlarını, notları, kişileri veya projeleri arar.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "Aranacak kelime, konu veya isim."
                },
                "category": {
                    "type": "STRING",
                    "description": "İsteğe bağlı kategori filtresi: 'journal', 'note', 'contact', 'project'."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "db_add_person",
        "description": "Veritabanına yeni kişi bilgileri ekler veya mevcut kişiyi günceller.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "name": {"type": "STRING", "description": "Kişinin tam adı (Örn: 'Ahmet Yılmaz')"},
                "role": {"type": "STRING", "description": "Unvanı veya rolu (Örn: 'Yazılım Geliştirici', 'Kardeş')"},
                "phone": {"type": "STRING", "description": "Telefon numarası"},
                "email": {"type": "STRING", "description": "E-posta adresi"},
                "tags": {"type": "STRING", "description": "Etiketler (Örn: 'Aile, İş, VIP')"},
                "notes": {"type": "STRING", "description": "Kişi hakkında ek notlar"},
                "photo_name": {"type": "STRING", "description": "database/pngs/ klasöründeki fotoğraf adı (Örn: 'ahmet.png')"}
            },
            "required": ["name"]
        }
    },
    {
        "name": "db_show_person",
        "description": "Veritabanından belirli bir kişinin bilgilerini çeker ve Cyberpunk temalı J.A.R.V.I.S özel UI kartını açar.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "name": {"type": "STRING", "description": "Aranacak veya kartı açılacak kişinin adı"}
            },
            "required": ["name"]
        }
    },
    {
        "name": "db_list_people",
        "description": "Veritabanındaki tüm kayıtlı kişilerin listesini Cyberpunk UI üzerinde gösterir.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "db_delete",
        "description": "Veritabanından belirli bir ID'ye sahip kaydı siler.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "record_id": {
                    "type": "INTEGER",
                    "description": "Silinecek kaydın benzersiz ID numarası."
                }
            },
            "required": ["record_id"]
        }
    },
    {
        "name": "open_app",
        "description": "Windows'ta herhangi bir uygulamayı açar. Spotify, Chrome, Terminal, Dosya Gezgini, VS Code vb.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "app_name": {
                    "type": "STRING",
                    "description": "Uygulama adı (örn. 'Spotify', 'Chrome', 'Terminal')"
                }
            },
            "required": ["app_name"]
        }
    },
    {
        "name": "sys_info",
        "description": "Sistem bilgisi alır: pil durumu, CPU, RAM, disk, saat, tarih, ağ bağlantısı.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "battery | cpu | ram | disk | time | date | network | all"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_weather",
        "description": (
            "Anlik hava durumunu ozetler. Varsayilan konum Istanbul'dur. "
            "Kullanici hava durumunu, sicakligi veya yagmur durumunu sordugunda kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "location": {
                    "type": "STRING",
                    "description": "Sehir veya konum. Bos birakilirsa Istanbul kullanilir."
                }
            }
        }
    },
    {
        "name": "get_calendar_events",
        "description": (
            "Takvim (Google Calendar) etkinliklerini okur. "
            "Bugun, yarin, siradaki etkinlik veya yaklasan ajandayi ozetler. "
            "Kullanici toplanti, takvim, ajanda, etkinlik veya gunluk programini sordugunda kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": (
                        "today | tomorrow | next | agenda | week veya dogal dilde "
                        "'onumuzdeki 30 gun', '2 hafta', 'bu ay', 'gelecek ay'"
                    )
                },
                "limit": {
                    "type": "NUMBER",
                    "description": "Maksimum etkinlik sayisi"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "add_calendar_event",
        "description": (
            "Takvim (Google Calendar) servisine yeni etkinlik ekler. "
            "Kullanici toplanti, randevu, takvime ekleme veya etkinlik olusturma isterse kullan. "
            "Baslangic tarihini gercek tarih/saat olarak ver; bitis verilmezse varsayilan sure kullanilir."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "title": {
                    "type": "STRING",
                    "description": "Etkinlik basligi. Ornek: 'Disci Randevusu'"
                },
                "start_iso": {
                    "type": "STRING",
                    "description": "Baslangic tarih/saat. ISO veya yyyy-MM-dd HH:mm formatinda."
                },
                "end_iso": {
                    "type": "STRING",
                    "description": "Bitis tarih/saat. Opsiyonel."
                },
                "location": {
                    "type": "STRING",
                    "description": "Etkinlik konumu. Opsiyonel."
                },
                "notes": {
                    "type": "STRING",
                    "description": "Etkinlik notlari. Opsiyonel."
                },
                "calendar_name": {
                    "type": "STRING",
                    "description": "Eklenecek takvim adi. Opsiyonel."
                },
                "all_day": {
                    "type": "BOOLEAN",
                    "description": "true ise tum gun etkinligi olusturur."
                }
            },
            "required": ["title", "start_iso"]
        }
    },
    {
        "name": "delete_calendar_event",
        "description": (
            "Takvim (Google Calendar) servisinden etkinlik siler. "
            "Kullanici bir toplantiyi, randevuyu veya takvim kaydini silmek istediginde kullan. "
            "Ayni ada birden fazla etkinlik varsa dogru kaydi bulmak icin baslangic tarihini gercek tarih/saat olarak ver."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "title": {
                    "type": "STRING",
                    "description": "Silinecek etkinlik basligi. Ornek: 'Disci Randevusu'"
                },
                "start_iso": {
                    "type": "STRING",
                    "description": "Opsiyonel tarih/saat. Ayni isimli birden fazla etkinligi ayirt etmek icin kullan."
                },
                "calendar_name": {
                    "type": "STRING",
                    "description": "Opsiyonel takvim adi"
                },
                "delete_all_matches": {
                    "type": "BOOLEAN",
                    "description": "true ise eslesen tum etkinlikleri siler"
                }
            },
            "required": ["title"]
        }
    },
    {
        "name": "get_reminders",
        "description": (
            "Hatırlatıcılar (Microsoft To-Do) listesini okur. "
            "Bugunku, yaklasan, geciken veya tum acik animsaticilari ozetler. "
            "Kullanici hatirlatma, animsatici, reminder veya yapilacaklar listesini sordugunda kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "today | upcoming | overdue | all | next"
                },
                "limit": {
                    "type": "NUMBER",
                    "description": "Maksimum animsatici sayisi"
                },
                "list_name": {
                    "type": "STRING",
                    "description": "Istenirse belirli bir animsatici listesi adi"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "add_reminder",
        "description": (
            "Hatırlatıcılar (Microsoft To-Do) uygulamasina yeni bir animsatici ekler. "
            "Kullanici 'hatirlat', 'animsatici ekle', 'reminder kur' dediginde kullan. "
            "Goreli zaman ifadelerini bugunku tarih baglamina gore due_iso alanina ISO formatinda cevir."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "title": {
                    "type": "STRING",
                    "description": "Animsatici basligi"
                },
                "due_iso": {
                    "type": "STRING",
                    "description": "Opsiyonel tarih/saat. Ornek: 2026-04-13T09:00 veya tum gun icin 2026-04-13"
                },
                "notes": {
                    "type": "STRING",
                    "description": "Opsiyonel not"
                },
                "list_name": {
                    "type": "STRING",
                    "description": "Opsiyonel animsatici listesi"
                },
                "priority": {
                    "type": "STRING",
                    "description": "low | medium | high"
                },
                "all_day": {
                    "type": "BOOLEAN",
                    "description": "Tum gun animsatici ise true"
                }
            },
            "required": ["title"]
        }
    },
    {
        "name": "browser_control",
        "description": "Tarayıcıda URL açar, Google'da arama yapar veya YouTube'da ilk sonucu doğrudan oynatır.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "open_url | search | play_youtube"},
                "url":    {"type": "STRING", "description": "Açılacak URL (open_url için)"},
                "query":  {"type": "STRING", "description": "Arama sorgusu (search veya play_youtube için)"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "shell_run",
        "description": "Windows komut satırı (cmd.exe) komutu çalıştırır. Dosya işlemleri, sistem yönetimi.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "command": {
                    "type": "STRING",
                    "description": "Çalıştırılacak komut"
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "toggle_webcam",
        "description": (
            "Gerçek zamanlı webcam akışını başlatır veya durdurur. "
            "Akış aktifken model sürekli kamera görüntüsü alır — 'bak', 'gör', 'göster', "
            "'kameraya bak', 'önümdekileri anlat', 'ne görüyorsun' gibi komutlarda 'start' kullan. "
            "'kamerayı kapat', 'artık bakma' gibi durumlarda 'stop' kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING",
                    "description": "start — akışı başlat  |  stop — akışı durdur"
                }
            },
            "required": ["action"]
        }
    },
    {
        "name": "play_media",
        "description": (
            "YouTube veya Spotify'da şarkı, müzik veya video açar. "
            "Kullanıcı belirli bir platform söylerse onu kullan. "
            "Belirtmezse uygun olanı dene. "
            "Kullanıcı 'çal', 'oynat', 'aç' diyorsa autoplay=true kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "Şarkı, sanatçı, albüm veya video arama ifadesi"
                },
                "provider": {
                    "type": "STRING",
                    "description": "auto | youtube | spotify"
                },
                "autoplay": {
                    "type": "BOOLEAN",
                    "description": "true ise mümkünse doğrudan oynatır"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_youtube_channel_report",
        "description": (
            "YouTube kanalinin public istatistiklerini ve son videolarin performansini raporlar. "
            "Kullanici kanal istatistiklerini, abone sayisini, son videolarini, buyume hizini "
            "veya YouTube analizini sordugunda kullan. Bu arac Studio yerine public YouTube Data API verisini kullanir."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": (
                        "Dogal dilde analiz istegi. Ornek: "
                        "'YouTube istatistiklerim nasil', 'son videolarimi analiz et', "
                        "'kanal buyumemi ozetle'"
                    )
                },
                "handle": {
                    "type": "STRING",
                    "description": (
                        "Opsiyonel kanal handle'i, kanal linki veya kanal ID'si. "
                        "Bos birakilirsa ayarlardaki youtube_channel_handle kullanilir."
                    )
                },
                "video_limit": {
                    "type": "NUMBER",
                    "description": "Analize dahil edilecek son video sayisi. Varsayilan 6."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "analyze_screen",
        "description": (
            "Aktif pencerenin ekran goruntusunu alip Gemini vision ile analiz eder. "
            "Kullanici ekranda ne oldugunu, bir hatayi, gorunen metni, butonlari veya pencere icerigini sordugunda kullan. "
            "Bu surum yalnizca aktif pencereyi destekler."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "Kullanicinin ekranla ilgili sorusu. Ornek: 'Bu hatayi oku', 'Ekranda ne var?'"
                },
                "target": {
                    "type": "STRING",
                    "description": "Su an sadece active_window desteklenir."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "save_memory",
        "description": "Kullanıcı hakkında önemli bilgiyi kalıcı belleğe kaydeder. İsim, tercihler, projeler vb. duyunca sessizce çağır.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "category": {
                    "type": "STRING",
                    "description": "identity | preferences | projects | notes"
                },
                "key":   {"type": "STRING", "description": "Kısa anahtar (örn. 'name')"},
                "value": {"type": "STRING", "description": "Değer (İngilizce)"}
            },
            "required": ["category", "key", "value"]
        }
    },
    {
        "name": "delete_memory",
        "description": (
            "Kalici hafizadaki bir kaydi siler. "
            "Kullanici 'bunu hafizandan kaldir', 'unut', 'sil' gibi bir sey derse kullan. "
            "Mumkunse category ve key ile sil; emin degilsen match_text ile ilgili kaydi bulup kaldir."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "category": {
                    "type": "STRING",
                    "description": "Kaydin kategorisi. Ornek: notes | identity | preferences | projects"
                },
                "key": {
                    "type": "STRING",
                    "description": "Silinecek anahtar. Ornek: claude_limit_refresh"
                },
                "match_text": {
                    "type": "STRING",
                    "description": "Kaydi bulmak icin kullanilacak dogal dil parcasi. Ornek: 'claude ai limit yenilenmesi'"
                }
            }
        }
    },
    {
        "name": "send_whatsapp_message",
        "description": (
            "WhatsApp Desktop veya WhatsApp Web üzerinden mesaj taslağı açar veya mesajı gönderir. "
            "Kişi adı veya telefon numarasıyla çalışabilir. "
            "Telefon numarası verilmemişse kişi adını önce kayıtlı WhatsApp kişileri ve içe aktarılan telefon rehberinde ara. "
            "Kullanıcı 'gönder', 'yolla', 'ile', 'hemen gönder' gibi açık bir gönderme niyeti söylüyorsa "
            "ekstra onay istemeden send_now=true kullan. "
            "Yalnızca 'hazırla', 'taslak aç', 'yaz ama gönderme' diyorsa send_now=false kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "recipient_name": {
                    "type": "STRING",
                    "description": "Kişi adı. Örn: 'Anne', 'Ahmet', 'Ece'"
                },
                "phone_number": {
                    "type": "STRING",
                    "description": "Uluslararası telefon numarası. Örn: +905551112233"
                },
                "message": {
                    "type": "STRING",
                    "description": "Gönderilecek mesaj içeriği"
                },
                "app_target": {
                    "type": "STRING",
                    "description": "desktop | web | auto. Varsayılan auto, tercihen desktop."
                },
                "send_now": {
                    "type": "BOOLEAN",
                    "description": "true ise sohbet açıldıktan sonra mesajı otomatik gönderir"
                }
            },
            "required": ["message"]
        }
    },
    {
        "name": "save_whatsapp_contact",
        "description": (
            "Sık kullanılan bir WhatsApp kişisini adı ve telefon numarasıyla kalıcı belleğe kaydeder. "
            "Kullanıcı bir kişiyi 'annem', 'Ahmet', 'iş ortağım' gibi tekrar kullanılacak şekilde tanımladığında kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "display_name": {
                    "type": "STRING",
                    "description": "Kaydedilecek kişi adı. Örn: 'Annem', 'Ahmet'"
                },
                "phone_number": {
                    "type": "STRING",
                    "description": "Uluslararası telefon numarası. Örn: +905551112233"
                },
                "aliases": {
                    "type": "STRING",
                    "description": "Virgülle ayrılmış alternatif hitaplar. Örn: 'anne, annem, mom'"
                }
            },
            "required": ["display_name", "phone_number"]
        }
    }
]


def _decl(name: str, description: str, properties: dict | None = None, required: list[str] | None = None) -> dict:
    return {
        "name": name,
        "description": description,
        "parameters": {
            "type": "OBJECT",
            "properties": properties or {},
            "required": required or [],
        },
    }


CORE_EXTRA_DECLARATIONS = [
    _decl(
        "delete_reminder",
        "Kayitli bir hatirlaticiyi siler. Google Tasks hazir degilse yerel hatirlatici deposunu kullanir.",
        {
            "title": {"type": "STRING", "description": "Silinecek hatirlatici basligi."},
            "list_name": {"type": "STRING", "description": "Opsiyonel liste adi."},
        },
        ["title"],
    ),
    _decl(
        "manage_file",
        "Masaustu veya Belgeler klasorundeki dosya/klasorleri guvenli sinirlarla yonetir.",
        {
            "action": {"type": "STRING", "description": "write | read | delete | create_dir | list_dir | search"},
            "filename": {"type": "STRING", "description": "Hedef dosya veya klasor adi/yolu."},
            "content": {"type": "STRING", "description": "write icin icerik."},
            "new_filename": {"type": "STRING", "description": "Gelecek rename islemleri icin yeni ad."},
            "confirm": {"type": "BOOLEAN", "description": "Riskli islemler icin acik onay."},
        },
        ["action", "filename"],
    ),
    _decl(
        "gui_automation",
        "Windows ekraninda fare, klavye, hotkey, scroll ve pencere odaklama otomasyonu yapar.",
        {
            "action": {"type": "STRING", "description": "click | click_image | type_text | hotkey | scroll | focus_window"},
            "x": {"type": "NUMBER", "description": "click icin X koordinati."},
            "y": {"type": "NUMBER", "description": "click icin Y koordinati."},
            "clicks": {"type": "NUMBER", "description": "Tiklama veya scroll miktari."},
            "button": {"type": "STRING", "description": "left | right | middle"},
            "image_name": {"type": "STRING", "description": "assets altinda aranacak PNG adi."},
            "confidence": {"type": "NUMBER", "description": "Gorsel eslesme guveni."},
            "text": {"type": "STRING", "description": "Yazilacak metin."},
            "press_enter": {"type": "BOOLEAN", "description": "Yazma sonrasi Enter bas."},
            "keys": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Hotkey tus listesi."},
            "title": {"type": "STRING", "description": "Odaklanacak pencere basligi."},
        },
        ["action"],
    ),
    _decl(
        "pc_control",
        "Ses, parlaklik, mikrofon, kilit, uyku, uygulama kapatma ve guc islemlerini yonetir.",
        {
            "action": {"type": "STRING", "description": "volume | brightness | mute_mic | lock | sleep | close_app | minimize_all | shutdown | reboot"},
            "value": {"type": "STRING", "description": "Yuzde veya hedef uygulama adi."},
        },
        ["action"],
    ),
    _decl(
        "secure_vault_access",
        "Yuz dogrulamasi ile guvenli kasa veya kritik sistem dosyalari erisimini yonetir.",
        {"action": {"type": "STRING", "description": "open_vault | system_files"}},
    ),
    _decl("capture_camera_vision", "Kameradan tek kare alip model ile analiz eder.", {}),
    _decl("check_email", "Google/Gmail entegrasyonundan son e-posta ozetini getirir.", {}),
    _decl(
        "gmail_search",
        "Gmail icinde e-posta arar ve konu/gonderen/snippet ozetini getirir.",
        {
            "query": {"type": "STRING", "description": "Gmail arama sorgusu. Bos birakilirsa en yeni e-postalar gelir."},
            "limit": {"type": "NUMBER", "description": "Maksimum e-posta sayisi. Varsayilan 5."},
        },
    ),
    _decl("gmail_labels", "Gmail etiketlerini listeler.", {}),
    _decl(
        "drive_search",
        "Google Drive icinde dosya arar.",
        {
            "query": {"type": "STRING", "description": "Drive arama sorgusu."},
            "limit": {"type": "NUMBER", "description": "Maksimum dosya sayisi. Varsayilan 5."},
        },
        ["query"],
    ),
    _decl(
        "git_push",
        "Yerel projeyi git add/commit/push akisiyle gonderir; riskli oldugu icin onay ister.",
        {"commit_message": {"type": "STRING", "description": "Commit mesaji veya auto."}},
    ),
    _decl("scan_network", "Yerel ag ARP tablosunu tarayip cihaz raporu uretir.", {}),
    _decl("check_security", "Windows guvenlik olaylari ve sistem kalkan ozetini getirir.", {}),
    _decl(
        "add_lgs_exam",
        "LGS deneme sonucunu kaydeder.",
        {
            "exam_name": {"type": "STRING", "description": "Deneme adi."},
            "results": {"type": "OBJECT", "description": "Ders bazli net/dogru/yanlis verileri."},
        },
    ),
    _decl("get_lgs_report", "LGS gelisim ozetini ve hedef raporunu getirir.", {}),
    _decl(
        "vercel_control",
        "Vercel proje, deployment ve domain durumlarini API uzerinden yonetir.",
        {
            "action": {"type": "STRING", "description": "list_projects | project_summary | check_deployment | list_deployments | list_domains"},
            "project_name": {"type": "STRING", "description": "Kontrol edilecek proje adi."},
            "team_id": {"type": "STRING", "description": "Opsiyonel Vercel team id. Bos ise config/.env VERCEL_TEAM_ID kullanilir."},
            "limit": {"type": "NUMBER", "description": "Maksimum sonuc sayisi."},
        },
        ["action"],
    ),
    _decl(
        "github_control",
        "GitHub bildirimleri, repolari, issue/PR listelerini ve workflow durumlarini API uzerinden yonetir.",
        {
            "action": {"type": "STRING", "description": "whoami | check_notifications | list_repos | repo_summary | list_issues | list_prs | workflow_runs | search_repos | create_issue"},
            "repo_name": {"type": "STRING", "description": "Repo adi. owner/repo veya sadece repo adi."},
            "owner": {"type": "STRING", "description": "Opsiyonel repo sahibi. Bos ise config/.env GITHUB_OWNER kullanilir."},
            "state": {"type": "STRING", "description": "Issue/PR state: open | closed | all."},
            "query": {"type": "STRING", "description": "search_repos icin arama sorgusu."},
            "title": {"type": "STRING", "description": "create_issue icin issue basligi."},
            "body": {"type": "STRING", "description": "create_issue icin issue aciklamasi."},
            "confirm": {"type": "BOOLEAN", "description": "Yazma islemleri icin acik onay."},
            "limit": {"type": "NUMBER", "description": "Maksimum sonuc sayisi."},
        },
        ["action"],
    ),
    _decl(
        "get_health_data",
        "Yerel saglik, uyku, adim, nabiz veya kalori verilerini ozetler.",
        {"query": {"type": "STRING", "description": "all | steps | sleep | heart | calories"}},
    ),
    _decl(
        "windows_automation",
        "Windows 10/11 derin sistem kontrolü: pencereleri listeleme/odaklama/kapatma, pycaw uygulama ses ayarları, ekran parlaklığı, yerel bildirimler ve güç durumu.",
        {
            "action": {
                "type": "STRING",
                "description": "list_windows | focus_window | close_window | set_volume | get_volume | mute | set_brightness | get_brightness | toast | power_status"
            },
            "query": {"type": "STRING", "description": "focus_window veya close_window için pencere başlığı/arama metni."},
            "target": {"type": "STRING", "description": "Ses için hedef: 'master' veya uygulama adı (spotify, chrome vb.)."},
            "level": {"type": "NUMBER", "description": "Ses veya parlaklık için 0-100 arası seviye."},
            "mute": {"type": "BOOLEAN", "description": "Sessize alma durumu (True=Sessiz, False=Açık)."},
            "title": {"type": "STRING", "description": "Toast bildirimi başlığı."},
            "message": {"type": "STRING", "description": "Toast bildirimi mesajı."}
        },
        ["action"],
    ),
    _decl(
        "semantic_memory_search",
        "Jarvis'in yerel vektör veri tabanında (RAG) anlamsal hafıza, not, kişi ve doküman araması yapar.",
        {
            "query": {"type": "STRING", "description": "Aranacak kavram, soru veya konu."},
            "limit": {"type": "NUMBER", "description": "Maksimum sonuç sayısı. Varsayılan 4."},
            "category": {"type": "STRING", "description": "Filtrelenecek kategori (isteğe bağlı)."}
        },
        ["query"],
    ),
    _decl(
        "autonomous_task_executor",
        "Kullanıcının karmaşık çok adımlı hedeflerini otonom olarak planlar, araç zincirini sırayla çalıştırır ve nihai rapor üretir.",
        {
            "goal": {"type": "STRING", "description": "Tamamlanması istenen üst düzey hedef."},
            "context": {"type": "STRING", "description": "İsteğe bağlı ek bağlam veya kısıtlamalar."}
        },
        ["goal"],
    ),
    _decl(
        "take_photo",
        "Kullanıcı veya ortam fotoğrafı çeker. Web kamerasını açar, deklanşör sesi çalar, fotoğrafı Pictures/Jarvis_Photos klasörüne kaydeder ve kullanıcıya gösterir.",
        {"caption": {"type": "STRING", "description": "Opsiyonel fotoğraf etiketi veya açıklaması."}},
    ),
    _decl(
        "ghost_typer",
        "Kullanıcının dikte ettiği veya belirttiği metni doğrudan o an aktif/odaklı olan Windows penceresine (Notepad, Word, browser, chat vb.) yazar veya yapıştırır.",
        {
            "text": {"type": "STRING", "description": "Aktif pencereye yazılacak metin."},
            "mode": {"type": "STRING", "description": "type | paste | open_popup"}
        },
        ["text"],
    ),
    _decl(
        "self_healing",
        "PC Kendi Kendini Onarma ve İyileştirme Motoru. DNS önbelleğini temizler, takılan Windows Gezgini (explorer.exe) ve Ses Hizmetlerini (audiosrv) yeniden başlatır, geçici şişkinlikleri (%TEMP%) temizler ve RAM çalışma kümelerini optimize eder.",
        {"action": {"type": "STRING", "description": "full | network | audio | memory | temp_clean"}},
    ),
    _decl(
        "paranoid_mode_control",
        "Paranoid Güvenlik Modu Kontrolü. Kullanıcı bilgisayar başından ayrıldığında izinsiz girişleri tespit eder, ekranı karartır (0 parlaklık), sessizce davetsiz misafir fotoğrafı çeker ve raporlar.",
        {
            "action": {"type": "STRING", "description": "enable | disable | status | configure"},
            "dim_screen": {"type": "BOOLEAN", "description": "Ekranı 0 parlaklığa düşür."},
            "take_photo": {"type": "BOOLEAN", "description": "Davetsiz misafir fotoğrafı çek."}
        },
        ["action"],
    ),
    _decl(
        "air_gestures_control",
        "Kamera ile Temassız El Hareketi Kontrolü (Air Gestures). Açık el -> İşaret parmağı ile durdur/oynat, yumruk ile ses artır/azalt, barış işareti ile sonraki parça. Fütüristik siber iskelet HUD efekti.",
        {
            "action": {"type": "STRING", "description": "start | stop | toggle | status"},
            "preview": {"type": "BOOLEAN", "description": "İskelet HUD önizleme penceresini aç/kapat."}
        },
        ["action"],
    ),
    _decl(
        "create_excel",
        "Profesyonel Excel tablosu (.xlsx) oluşturur ve Masaüstüne kaydeder. Başlıklar, satırlar, zebra renklendirme ve otomatik toplam satırı destekler.",
        {
            "title": {"type": "STRING", "description": "Tablo ana başlığı."},
            "headers": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Sütun başlıkları listesi."},
            "rows": {"type": "ARRAY", "items": {"type": "ARRAY", "items": {"type": "STRING"}}, "description": "Veri satırları matrisi."},
            "filename": {"type": "STRING", "description": "Opsiyonel dosya adı (varsayılan: başlık.xlsx)."},
            "include_summary": {"type": "BOOLEAN", "description": "Sayısal sütunların altına otomatik toplam satırı ekle."}
        },
        ["title", "headers", "rows"],
    ),
    _decl(
        "create_powerpoint",
        "Modern koyu siber temalı PowerPoint slayt gösterisi (.pptx) hazırlar ve Masaüstüne kaydeder.",
        {
            "title": {"type": "STRING", "description": "Sunum ana başlığı."},
            "subtitle": {"type": "STRING", "description": "Sunum alt başlığı veya açıklama."},
            "slides": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING", "description": "Slayt başlığı."},
                        "bullets": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Maddeler."}
                    },
                    "required": ["title", "bullets"]
                },
                "description": "Slayt listesi (her slayt için başlık ve maddeler)."
            },
            "filename": {"type": "STRING", "description": "Opsiyonel dosya adı (varsayılan: başlık.pptx)."}
        },
        ["title", "slides"],
    ),
    _decl(
        "send_email",
        "Belirtilen adrese doğrudan SMTP ile e-posta gönderir.",
        {
            "to": {"type": "STRING", "description": "Alıcı e-posta adresi."},
            "subject": {"type": "STRING", "description": "E-posta konusu."},
            "body": {"type": "STRING", "description": "E-posta metin içeriği."}
        },
        ["to", "subject", "body"],
    ),
    _decl(
        "read_emails",
        "Tarayıcı açmadan son gelen e-postaları IMAP üzerinden okur. Ödev, proje veya belirli bir kelime için arama yapabilir.",
        {
            "count": {"type": "NUMBER", "description": "Okunacak e-posta sayısı (varsayılan: 5)."},
            "search_query": {"type": "STRING", "description": "Aranacak anahtar kelime (örn: ödev, proje, üniversite)."}
        },
    ),
    _decl(
        "read_whatsapp",
        "Windows Bildirim Merkezi üzerinden WhatsApp mesajlarını tarayıcı veya pencere açmadan okur. Grupta veya sohbetlerde ödev/proje/duyuru paylaşılmış mı arar ve özetler.",
        {
            "count": {"type": "NUMBER", "description": "İncelenecek maksimum bildirim sayısı (varsayılan: 15)."},
            "keyword": {"type": "STRING", "description": "Filtrelenecek anahtar kelime (örn: ödev, sınav, proje, link)."}
        },
    ),
    _decl(
        "setup_owner_face",
        "Kullanıcının yüzünü detaylı tarayıp LBPH biyometrik yapay zeka modelini eğiten yüz kayıt protokolünü canlı kamerayla açar.",
        {},
    ),
]


CORE_EXTRA_DECLARATIONS.extend([
    _decl(
        "create_word_doc",
        "Word (.docx) belgesi oluşturur ve kaydeder. Okul ödevleri, raporlar ve makaleler için başlıklar, alt başlıklar ve maddeler içerir.",
        {
            "title": {"type": "STRING", "description": "Belge ana başlığı."},
            "content": {"type": "STRING", "description": "Belge metni veya markdown biçimli içeriği."},
            "output_name": {"type": "STRING", "description": "Opsiyonel dosya adı (.docx)."}
        },
        ["title", "content"],
    ),
    _decl(
        "create_pdf",
        "PDF belgesi oluşturur. Başlık ve içerik metnini doğrudan PDF olarak kaydeder.",
        {
            "title": {"type": "STRING", "description": "PDF başlığı."},
            "content": {"type": "STRING", "description": "PDF içeriği metni."},
            "output_name": {"type": "STRING", "description": "Opsiyonel dosya adı (.pdf)."}
        },
        ["title", "content"],
    ),
    _decl(
        "list_skills",
        "JARVIS sistemine entegre 17 Claude beceri paketini (xlsx, pptx, docx, pdf, react, test vb.) listeler.",
        {},
    ),
    _decl(
        "list_workflows",
        "Kayıtlı tüm otomatik iş akışlarını (workflows/ klasöründeki YAML dosyaları) listeler.",
        {},
    ),
    _decl(
        "run_workflow",
        "Belirtilen otomatik iş akışını (YAML/JSON workflow) adım adım çalıştırır.",
        {
            "workflow_name": {"type": "STRING", "description": "Çalıştırılacak workflow dosya adı veya ID'si (örn: daily_brief, okul_odev_hazirla)."}
        },
        ["workflow_name"],
    ),
    _decl(
        "scan_homework",
        "Mesajları veya okul gruplarını tarayarak ödevleri, sınavları ve teslim tarihlerini listeler veya yeni ödevleri kaydeder.",
        {
            "message_text": {"type": "STRING", "description": "İncelenecek sohbet/mesaj metni (boş bırakılırsa mevcut kayıtlı ödevleri listeler)."},
            "source": {"type": "STRING", "description": "Kaynağın adı (örn: WhatsApp Sınıf Grubu, Mail)."}
        },
    ),
    _decl(
        "create_homework",
        "Belirtilen okul ödevi/projesi konusu için tam paket (Word araştırma raporu ve PowerPoint sunumu) oluşturur.",
        {
            "topic": {"type": "STRING", "description": "Ödev konusu veya araştırma başlığı."},
            "course": {"type": "STRING", "description": "Dersin adı (Matematik, Fizik, Tarih vb.)."},
            "doc_type": {"type": "STRING", "description": "Belge türü: 'all' (Word + PPTX), 'word', veya 'pptx'."}
        },
        ["topic"],
    ),
    _decl(
        "create_study_plan",
        "Sınav veya ders için Pomodoro ve Spaced Repetition destekli haftalık akıllı çalışma planı oluşturur.",
        {
            "exam_name": {"type": "STRING", "description": "Sınav veya hedef konu adı (örn: Üniversite Sınavı, Biyoloji Vize)."},
            "available_hours_daily": {"type": "NUMBER", "description": "Günlük ayrılacak çalışma saati (örn: 3.0)."}
        },
        ["exam_name"],
    ),
])


def _dedupe_declarations(items: list[dict]) -> list[dict]:
    merged: list[dict] = []
    seen: set[str] = set()
    for item in items:
        name = item.get("name") if isinstance(item, dict) else None
        if not name or name in seen:
            continue
        seen.add(str(name))
        merged.append(item)
    return merged


def _load_declaration_extras() -> tuple[list[dict], object | None, list[str]]:
    extras: list[dict] = []
    errors: list[str] = []
    plugin_registry = None

    try:
        from tools.declarations import TOOL_DECLARATIONS as cyber_declarations

        extras.extend(cyber_declarations)
    except Exception as exc:
        errors.append(f"cyber declarations: {exc}")

    reserved = {item.get("name") for item in TOOL_DECLARATIONS + CORE_EXTRA_DECLARATIONS + extras if item.get("name")}
    try:
        from core.plugin_loader import load_plugins

        plugin_registry = load_plugins(["actions", "tools"], reserved_names=set(reserved))
        extras.extend(plugin_registry.declarations)
        errors.extend(getattr(plugin_registry, "errors", []))
    except Exception as exc:
        errors.append(f"plugin loader: {exc}")

    return extras, plugin_registry, errors


_EXTRA_DECLARATIONS, PLUGIN_REGISTRY, PLUGIN_LOAD_ERRORS = _load_declaration_extras()
TOOL_DECLARATIONS = _dedupe_declarations(TOOL_DECLARATIONS + CORE_EXTRA_DECLARATIONS + _EXTRA_DECLARATIONS)
