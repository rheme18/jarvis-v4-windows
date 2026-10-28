from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
SETTINGS_PATH = BASE_DIR / "memory" / "jarvis_settings.json"


DEFAULT_SETTINGS: dict[str, Any] = {
    "general": {
        "startup_mode": "normal",
        "minimize_to_tray": True,
        "open_web_panel_on_start": False,
        "theme": "cyber",
    },
    "voice": {
        "voice": "Charon",
        "long_response_recovery": True,
        "interrupt_enabled": True,
        "auto_listen_after_response": True,
    },
    "proactive": {
        "enabled": True,
        "battery_warning": True,
        "battery_threshold": 20,
        "daily_brief": True,
        "daily_brief_hour": 9,
        "quiet_hours": False,
        "quiet_start": "23:00",
        "quiet_end": "08:00",
    },
    "security": {
        "approval_center": True,
        "shell_requires_approval": True,
        "file_delete_requires_approval": True,
        "pc_power_requires_approval": True,
        "admin_actions_require_confirm": True,
    },
    "integrations": {
        "discord_bot_enabled": False,
        "discord_bot_token": "",
        "discord_channel_id": "",
        "telegram_enabled": True,
        "telegram_bot_token": "",
        "web_panel_enabled": True,
        "github_enabled": True,
        "vercel_enabled": True,
        "google_enabled": True,
    },
    "file_management": {
        "allowed_roots": [],
    },
    "developer": {
        "project_index_limit": 400,
        "auto_test_command": "python -m py_compile main.py",
        "quality_score_limit": 300,
        "git_summary_limit": 80,
        "safe_refactor_requires_approval": True,
    },
    "web_panel": {
        "theme": "white",
        "remote_enabled": True,
        "mobile_remote": True,
        "live_logs": True,
        "live_system_graphs": True,
        "file_manager_enabled": True,
        "memory_editor_enabled": True,
        "workflow_builder_enabled": True,
    },
    "cyber": {
        "dns_timeout": 5,
        "http_timeout": 8,
        "ssl_timeout": 8,
        "local_network_scan_limit": 256,
        "wifi_history_enabled": True,
        "url_screenshot_enabled": False,
        "reputation_provider": "local",
    },
    "memory": {
        "editable": True,
        "max_preview_chars": 20000,
    },
    "ui": {
        "show_status_metrics": True,
        "show_plugin_badge": True,
        "compact_mode": False,
        "active_theme": "teal",
        "custom_primary": "#00d4c0",
        "reduce_motion": False,
        "visual_effect_mode": "standard",
        "sfx_enabled": True,
        "fx_volume": 0.45,
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_settings() -> dict[str, Any]:
    try:
        raw = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            return _deep_merge(DEFAULT_SETTINGS, raw)
    except Exception:
        pass
    return _deep_merge(DEFAULT_SETTINGS, {})


def save_settings(settings: dict[str, Any]) -> dict[str, Any]:
    merged = _deep_merge(DEFAULT_SETTINGS, settings or {})
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    return merged


def update_settings(section: str, updates: dict[str, Any]) -> dict[str, Any]:
    settings = load_settings()
    current = settings.setdefault(section, {})
    if isinstance(current, dict):
        current.update(updates or {})
    else:
        settings[section] = dict(updates or {})
    return save_settings(settings)


def get_setting(section: str, key: str, default: Any = None) -> Any:
    return load_settings().get(section, {}).get(key, default)


def set_setting(section: str, key: str, value: Any) -> dict[str, Any]:
    return update_settings(section, {key: value})
