from __future__ import annotations


TOOL_DECLARATION = {
    "name": "open_settings_panel",
    "description": "JARVIS modern cyber settings panelini acar; Discord bot, ses, proaktif kurallar, guvenlik ve entegrasyonlari yonetir.",
    "parameters": {"type": "OBJECT", "properties": {}, "required": []},
}

PLUGIN_META = {
    "category": "system",
    "danger": "safe",
    "ui_visible": True,
    "aliases": ["settings", "ayarlar", "ayar paneli", "discord ayarlari"],
}


def run() -> str:
    import subprocess
    import sys
    from pathlib import Path

    base_dir = Path(__file__).resolve().parents[1]
    settings_py = base_dir / "settings.py"
    subprocess.Popen(
        [sys.executable, str(settings_py)],
        cwd=str(base_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
    )
    return "Settings panel aciliyor."
