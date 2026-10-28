from __future__ import annotations

import json

from core.settings_store import load_settings, save_settings, set_setting


TOOL_DECLARATION = {
    "name": "settings_control",
    "description": "JARVIS ayarlarini sesli komutla okur veya degistirir.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "get | set | list"},
            "section": {"type": "STRING", "description": "general | voice | proactive | security | integrations | ui"},
            "key": {"type": "STRING", "description": "Ayar anahtari."},
            "value": {"type": "STRING", "description": "Yeni deger. true/false/sayi/metin olabilir."},
        },
    },
}

PLUGIN_META = {
    "category": "system",
    "danger": "safe",
    "ui_visible": True,
    "aliases": ["ayar degistir", "settings set", "ayar oku"],
}


def _coerce(value: str):
    text = str(value).strip()
    low = text.lower()
    if low in {"true", "evet", "ac", "aç", "on", "aktif"}:
        return True
    if low in {"false", "hayir", "hayır", "kapat", "off", "pasif"}:
        return False
    try:
        return int(text)
    except Exception:
        pass
    try:
        return float(text)
    except Exception:
        return text


def run(action: str = "list", section: str = "", key: str = "", value: str = "") -> str:
    action = (action or "list").strip().lower()
    section = (section or "").strip()
    key = (key or "").strip()
    settings = load_settings()

    if action == "list":
        if section:
            return json.dumps(settings.get(section, {}), ensure_ascii=False, indent=2)
        return "Ayar bolumleri: " + ", ".join(sorted(settings))

    if action == "get":
        if not section or not key:
            return "Ayar okumak icin section ve key gerekli."
        return f"{section}.{key} = {settings.get(section, {}).get(key)}"

    if action == "set":
        if not section or not key:
            return "Ayar degistirmek icin section ve key gerekli."
        if section not in settings:
            settings[section] = {}
        new_value = _coerce(value)
        set_setting(section, key, new_value)
        return f"{section}.{key} ayari {new_value} olarak guncellendi."

    if action == "reset":
        save_settings({})
        return "JARVIS ayarlari varsayilanlara alindi."

    return "Bilinmeyen settings_control islemi."
