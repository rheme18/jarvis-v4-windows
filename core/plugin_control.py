from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = BASE_DIR / "memory" / "plugin_config.json"

SAFE = "safe"
CONFIRM_REQUIRED = "confirm_required"
ADMIN = "admin"
BLOCKED = "blocked"
VALID_DANGER_LEVELS = {SAFE, CONFIRM_REQUIRED, ADMIN, BLOCKED}


def _default_config() -> dict[str, Any]:
    return {"plugins": {}}


def load_plugin_config() -> dict[str, Any]:
    try:
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data.setdefault("plugins", {})
                return data
    except Exception:
        pass
    return _default_config()


def save_plugin_config(config: dict[str, Any]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _entry(config: dict[str, Any], name: str) -> dict[str, Any]:
    plugins = config.setdefault("plugins", {})
    current = plugins.setdefault(name, {})
    if not isinstance(current, dict):
        current = {}
        plugins[name] = current
    return current


def get_plugin_config(name: str) -> dict[str, Any]:
    return dict(load_plugin_config().get("plugins", {}).get(name, {}) or {})


def is_plugin_enabled(name: str) -> bool:
    entry = get_plugin_config(name)
    return bool(entry.get("enabled", True))


def set_plugin_enabled(name: str, enabled: bool) -> None:
    config = load_plugin_config()
    _entry(config, name)["enabled"] = bool(enabled)
    save_plugin_config(config)


def set_plugin_danger(name: str, danger: str) -> None:
    danger = (danger or SAFE).strip().lower()
    if danger not in VALID_DANGER_LEVELS:
        raise ValueError(f"Gecersiz risk seviyesi: {danger}")
    config = load_plugin_config()
    _entry(config, name)["danger"] = danger
    save_plugin_config(config)


def danger_for(name: str, meta: dict[str, Any] | None = None) -> str:
    meta = meta or {}
    configured = get_plugin_config(name).get("danger")
    if configured in VALID_DANGER_LEVELS:
        return configured
    declared = str(meta.get("danger", "") or "").strip().lower()
    if declared in VALID_DANGER_LEVELS:
        return declared
    return SAFE


def _has_confirmation(args: dict[str, Any]) -> bool:
    return bool(
        args.get("confirm") is True
        or args.get("_confirm") is True
        or str(args.get("confirm", "")).strip().lower() in {"true", "evet", "onay", "yes"}
    )


def check_plugin_policy(name: str, args: dict[str, Any] | None, meta: dict[str, Any] | None = None) -> tuple[bool, str]:
    args = args or {}
    if not is_plugin_enabled(name):
        return False, f"Plugin kapali: {name}. Plugin manager ile tekrar acabilirsin."

    danger = danger_for(name, meta)
    if danger == BLOCKED:
        return False, f"Plugin engelli: {name}."
    if danger in {CONFIRM_REQUIRED, ADMIN} and not _has_confirmation(args):
        return (
            False,
            f"{name} icin {danger} yetkisi gerekiyor. Eminsen komutu onayli calistir.",
        )
    return True, "ok"


def plugin_rows(registry, include_config: bool = True) -> list[dict[str, Any]]:
    config = load_plugin_config() if include_config else {"plugins": {}}
    rows: list[dict[str, Any]] = []
    for name in registry.names():
        meta = registry.meta.get(name, {}) or {}
        declaration = next((item for item in registry.declarations if item.get("name") == name), {})
        local = config.get("plugins", {}).get(name, {}) or {}
        rows.append(
            {
                "name": name,
                "enabled": bool(local.get("enabled", True)),
                "danger": danger_for(name, meta),
                "category": meta.get("category", "general"),
                "source": meta.get("source", "plugin"),
                "description": declaration.get("description", ""),
            }
        )
    return rows
