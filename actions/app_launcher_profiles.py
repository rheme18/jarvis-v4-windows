from __future__ import annotations

import webbrowser

from actions.open_app import open_app


PROFILES = {
    "code": {
        "apps": ["Visual Studio Code", "Terminal"],
        "urls": [],
        "description": "Kodlama profili",
    },
    "study": {
        "apps": ["Chrome"],
        "urls": ["https://calendar.google.com", "https://tasks.google.com"],
        "description": "Ders ve odak profili",
    },
    "media": {
        "apps": ["Spotify", "Chrome"],
        "urls": ["https://music.youtube.com"],
        "description": "Medya profili",
    },
    "meeting": {
        "apps": ["WhatsApp", "Chrome"],
        "urls": ["https://meet.google.com", "https://calendar.google.com"],
        "description": "Toplantı ve takvim profili",
    },
    "writing": {
        "apps": ["Notion", "Chrome"],
        "urls": ["https://docs.google.com"],
        "description": "Yazı ve belge profili",
    },
    "planning": {
        "apps": [],
        "urls": [
            "https://calendar.google.com",
            "https://tasks.google.com",
            "https://mail.google.com",
            "https://drive.google.com",
        ],
        "description": "Takvim, görev, e-posta ve Drive profili",
    },
    "creative": {
        "apps": [],
        "urls": [
            "https://www.figma.com",
            "https://www.canva.com",
            "https://drive.google.com",
        ],
        "description": "Tasarım ve yaratıcı çalışma profili",
    },
    "creator": {
        "apps": [],
        "urls": [
            "https://studio.youtube.com",
            "https://docs.google.com",
            "https://www.canva.com",
        ],
        "description": "YouTube içerik ve yayın hazırlık profili",
    },
    "devops": {
        "apps": ["Visual Studio Code", "Terminal"],
        "urls": ["https://github.com", "https://vercel.com/dashboard"],
        "description": "Geliştirme, GitHub ve Vercel profili",
    },
}


def launch_app_profile(profile: str = "code", apps: str = "", urls: str = "") -> str:
    key = (profile or "code").strip().lower()
    selected = dict(PROFILES.get(key, {}))
    app_list = [a.strip() for a in apps.split(",") if a.strip()] if apps else selected.get("apps", [])
    url_list = [u.strip() for u in urls.split(",") if u.strip()] if urls else selected.get("urls", [])

    if not app_list and not url_list:
        known = ", ".join(sorted(PROFILES))
        return f"Profil bulunamadi. Bilinen profiller: {known}"

    results = []
    for app_name in app_list:
        try:
            results.append(open_app(app_name) or f"{app_name} acildi.")
        except Exception as exc:
            results.append(f"{app_name} acilamadi: {exc}")

    for url in url_list:
        try:
            webbrowser.open(url)
            results.append(f"URL acildi: {url}")
        except Exception as exc:
            results.append(f"URL acilamadi ({url}): {exc}")

    return f"{selected.get('description', key)} hazirlandi.\n" + "\n".join(results)
