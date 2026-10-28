from __future__ import annotations

import json

from core.plugin_control import (
    set_plugin_danger,
    set_plugin_enabled,
    plugin_rows,
    VALID_DANGER_LEVELS,
)
from core.plugin_loader import load_plugins


TOOL_DECLARATION = {
    "name": "plugin_manager",
    "description": "JARVIS pluginlerini listeler, acar/kapatir ve risk seviyesini yonetir.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "list | enable | disable | set_danger | status",
            },
            "name": {"type": "STRING", "description": "Plugin/tool adi."},
            "danger": {
                "type": "STRING",
                "description": "safe | confirm_required | admin | blocked",
            },
            "detail": {"type": "STRING", "description": "summary | json"},
        },
    },
}

PLUGIN_META = {
    "category": "system",
    "danger": "safe",
    "ui_visible": True,
    "aliases": ["plugin manager", "plugin yonetimi", "eklenti yonetimi"],
}


def _registry():
    return load_plugins(["actions", "tools"], reserved_names=set(), include_disabled=True)


def _format_rows(rows: list[dict], limit: int = 60) -> str:
    if not rows:
        return "Plugin bulunamadi."
    lines = [f"Plugin yonetimi: {len(rows)} plugin bulundu."]
    for row in rows[:limit]:
        state = "acik" if row["enabled"] else "kapali"
        lines.append(
            f"- {row['name']} [{state}, {row['danger']}, {row['category']}] - {row['description'][:90]}"
        )
    if len(rows) > limit:
        lines.append(f"... {len(rows) - limit} plugin daha var.")
    return "\n".join(lines)


def run(action: str = "list", name: str = "", danger: str = "", detail: str = "summary") -> str:
    action = (action or "list").strip().lower()
    name = (name or "").strip()
    detail = (detail or "summary").strip().lower()

    if action == "enable":
        if not name:
            return "Acmak icin plugin adi gerekli."
        set_plugin_enabled(name, True)
        return f"{name} plugini acildi. Degisikligin model tool listesine yansimasi icin Jarvis'i yeniden baslatmak en temiz yoldur."

    if action == "disable":
        if not name:
            return "Kapatmak icin plugin adi gerekli."
        if name == "plugin_manager":
            return "plugin_manager kendini kapatamaz; yonetim kapisi acik kalmali."
        set_plugin_enabled(name, False)
        return f"{name} plugini kapatildi. Jarvis yeniden baslayinca modele gosterilmeyecek."

    if action == "set_danger":
        if not name:
            return "Risk seviyesi icin plugin adi gerekli."
        danger = (danger or "").strip().lower()
        if danger not in VALID_DANGER_LEVELS:
            return "Gecersiz risk seviyesi. Kullan: safe, confirm_required, admin, blocked."
        set_plugin_danger(name, danger)
        return f"{name} risk seviyesi {danger} olarak ayarlandi."

    registry = _registry()
    rows = plugin_rows(registry)
    if name:
        rows = [row for row in rows if row["name"] == name or name.lower() in row["name"].lower()]

    payload = {
        "count": len(rows),
        "errors": registry.errors,
        "plugins": rows,
    }
    if detail == "json":
        return json.dumps(payload, ensure_ascii=False)
    if action == "status":
        enabled = sum(1 for row in rows if row["enabled"])
        risky = sum(1 for row in rows if row["danger"] != "safe")
        return f"Plugin sistemi aktif. {enabled}/{len(rows)} plugin acik, {risky} plugin ozel risk seviyesinde."
    return _format_rows(rows)
