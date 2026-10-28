from __future__ import annotations


TOOL_DECLARATION = {
    "name": "plugin_system_status",
    "description": "Otomatik plugin sistemi hakkinda kisa durum ve plugin yazma rehberi verir.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "detail": {
                "type": "STRING",
                "description": "summary | guide. Varsayilan summary.",
            }
        },
    },
}

PLUGIN_META = {
    "category": "system",
    "danger": "safe",
    "ui_visible": True,
    "aliases": ["plugin sistemi", "otomatik plugin", "plugin durumu"],
}


def run(detail: str = "summary") -> str:
    detail = (detail or "summary").strip().lower()
    if detail == "guide":
        return "\n".join(
            [
                "Otomatik plugin formati:",
                "1. actions/ veya tools/ altina yeni .py dosyasi ekle.",
                "2. TOOL_DECLARATION sozlugu tanimla.",
                "3. run(**args) veya execute(**args) fonksiyonu yaz.",
                "4. JARVIS yeniden baslayinca araci otomatik tanir.",
            ]
        )
    return "Otomatik plugin sistemi aktif. TOOL_DECLARATION ve run/execute bulunan yeni moduller otomatik yuklenir."
