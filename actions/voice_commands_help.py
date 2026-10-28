from __future__ import annotations


CATEGORIES = {
    "system": [
        "Sistem durumunu soyle",
        "Sesi yuzde 30 yap",
        "Mikrofonu kapat",
        "Bilgisayari kilitle",
        "Genel sistem saglik raporu ver",
    ],
    "productivity": [
        "Bugunku gorevlerimi goster",
        "Bunu not al",
        "Panodaki metni ozetle",
        "Gunluk brifing hazirla",
        "25 dakikalik odak seansi baslat",
    ],
    "project": [
        "Proje anlik goruntusu al",
        "Kod haritasini cikar",
        "Projedeki buyuk dosyalari goster",
        "Guvenli temizlik taramasi yap",
        "Proje yedek plani hazirla",
    ],
    "web": [
        "Chrome'u ac",
        "Google'da Python ara",
        "YouTube'da muzik ac",
        "Vercel projelerim ne durumda",
        "GitHub bildirimlerimi kontrol et",
    ],
    "personal": [
        "Bugun takvimimde ne var",
        "Yarin icin hatirlatici ekle",
        "WhatsApp mesaji hazirla",
        "Saglik ozetimi ver",
        "Hava durumu nasil",
    ],
    "plugin": [
        "Plugin panelini ac",
        "Pluginleri listele",
        "Plugin sistemi durumunu goster",
        "Proje tarama workflow plani hazirla",
        "Bakim workflow plani hazirla",
        "Workflow builder ac",
        "Settings ac",
        "Discord bot ayarlarini ac",
    ],
    "settings": [
        "Ayarlar panelini ac",
        "Proaktif modu kapat",
        "Web panel temasini cyber yap",
        "Onay merkezini ac",
        "Discord botu kapat",
        "Gunluk brifing saatini 9 yap",
    ],
    "developer": [
        "Projeyi indeksle",
        "Kodda process_message sembolunu ara",
        "Otomatik test calistir",
        "Git diff ozetini ver",
        "Kod kalite puanini hesapla",
        "Commit aciklamasi hazirla",
        "Yerel changelog uret",
    ],
    "cyber": [
        "Subdomain finder calistir",
        "HTTP security headers audit yap",
        "SSL TLS detayli rapor hazirla",
        "DNS propagation kontrol et",
        "Local network inventory cikar",
        "Acik port risk raporu ver",
        "Wi-Fi sinyal gecmisini goster",
    ],
}


def voice_commands_help(category: str = "all", query: str = "", limit: int = 30) -> str:
    category = (category or "all").strip().lower()
    query = (query or "").strip().lower()
    limit = max(5, min(int(limit or 30), 80))

    if query:
        matches = []
        for cat, commands in CATEGORIES.items():
            for command in commands:
                if query in command.lower() or query in cat:
                    matches.append((cat, command))
        if not matches:
            return f"'{query}' icin komut onerisi bulunamadi."
        lines = [f"'{query}' komut onerileri:"]
        lines.extend(f"- [{cat}] {command}" for cat, command in matches[:limit])
        return "\n".join(lines)

    selected = CATEGORIES if category == "all" else {category: CATEGORIES.get(category, [])}
    if not any(selected.values()):
        return "Kategori bulunamadi. Kategoriler: " + ", ".join(sorted(CATEGORIES))

    lines = ["Jarvis sesli komut rehberi:"]
    count = 0
    for cat, commands in selected.items():
        lines.append(f"{cat}:")
        for command in commands:
            if count >= limit:
                break
            lines.append(f"- {command}")
            count += 1
    return "\n".join(lines)
