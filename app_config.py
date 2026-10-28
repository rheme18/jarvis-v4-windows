# Jarvis application configuration.
from __future__ import annotations

import json
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config"
CONFIG_PATH = CONFIG_DIR / "api_keys.json"
ENV_PATH = CONFIG_DIR / ".env"
ROOT_ENV_PATH = BASE_DIR / ".env"


DEFAULT_CONFIG = {
    "gemini_api_key": "",
    "voice": "Charon",
    "youtube_api_key": "",
    "youtube_channel_handle": "",
    "telegram_bot_token": "",
    "claude_api_key": "",
    "claude_model": "claude-sonnet-4-5-20250929",
    "github_token": "",
    "github_owner": "",
    "vercel_token": "",
    "vercel_team_id": "",
    "google_credentials_file": "config/google_credentials.json",
    "google_token_file": "config/google_token.json",
    "gmail_user_id": "me",
}

ENV_KEY_ALIASES = {
    "gemini_api_key": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    "youtube_api_key": ("YOUTUBE_API_KEY",),
    "youtube_channel_handle": ("YOUTUBE_CHANNEL_HANDLE",),
    "telegram_bot_token": ("TELEGRAM_BOT_TOKEN",),
    "claude_api_key": ("CLAUDE_API_KEY", "ANTHROPIC_API_KEY"),
    "claude_model": ("CLAUDE_MODEL", "ANTHROPIC_MODEL"),
    "discord_bot_token": ("DISCORD_BOT_TOKEN",),
    "discord_channel_id": ("DISCORD_CHANNEL_ID",),
    "github_token": ("GITHUB_TOKEN", "GITHUB_PERSONAL_ACCESS_TOKEN"),
    "GITHUB_TOKEN": ("GITHUB_TOKEN", "GITHUB_PERSONAL_ACCESS_TOKEN"),
    "github_owner": ("GITHUB_OWNER",),
    "vercel_token": ("VERCEL_TOKEN",),
    "VERCEL_TOKEN": ("VERCEL_TOKEN",),
    "vercel_team_id": ("VERCEL_TEAM_ID",),
    "google_credentials_file": ("GOOGLE_CREDENTIALS_FILE",),
    "google_token_file": ("GOOGLE_TOKEN_FILE",),
    "gmail_user_id": ("GMAIL_USER_ID",),
}

PRIMARY_ENV_KEYS = {
    "gemini_api_key": "GEMINI_API_KEY",
    "youtube_api_key": "YOUTUBE_API_KEY",
    "youtube_channel_handle": "YOUTUBE_CHANNEL_HANDLE",
    "telegram_bot_token": "TELEGRAM_BOT_TOKEN",
    "claude_api_key": "CLAUDE_API_KEY",
    "claude_model": "CLAUDE_MODEL",
    "discord_bot_token": "DISCORD_BOT_TOKEN",
    "discord_channel_id": "DISCORD_CHANNEL_ID",
    "github_token": "GITHUB_TOKEN",
    "github_owner": "GITHUB_OWNER",
    "vercel_token": "VERCEL_TOKEN",
    "vercel_team_id": "VERCEL_TEAM_ID",
    "google_credentials_file": "GOOGLE_CREDENTIALS_FILE",
    "google_token_file": "GOOGLE_TOKEN_FILE",
    "gmail_user_id": "GMAIL_USER_ID",
}


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        if not path.exists():
            return values
        for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                values[key] = value
    except Exception:
        return {}
    return values


def load_env_config() -> dict[str, str]:
    env_values: dict[str, str] = {}
    env_values.update(_parse_env_file(ROOT_ENV_PATH))
    env_values.update(_parse_env_file(ENV_PATH))
    for key, value in env_values.items():
        os.environ.setdefault(key, value)
    return env_values


def _quote_env_value(value: object) -> str:
    text = str(value if value is not None else "")
    if not text or any(ch.isspace() for ch in text) or any(ch in text for ch in ['"', "'", "#", "="]):
        return json.dumps(text, ensure_ascii=False)
    return text


def save_env_config(updates: dict) -> None:
    if not updates:
        return
    env_updates: dict[str, str] = {}
    for key, value in updates.items():
        env_key = PRIMARY_ENV_KEYS.get(str(key))
        if env_key is not None and value is not None:
            env_updates[env_key] = str(value)
    if not env_updates:
        return

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    existing = _parse_env_file(ENV_PATH)
    existing.update(env_updates)

    ordered_keys = list(PRIMARY_ENV_KEYS.values())
    lines = [
        "# Jarvis local API configuration.",
        "# Keep this file private. Empty values are ignored.",
    ]
    for key in ordered_keys:
        lines.append(f"{key}={_quote_env_value(existing.get(key, ''))}")
    for key in sorted(k for k in existing if k not in set(ordered_keys)):
        lines.append(f"{key}={_quote_env_value(existing[key])}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_app_config() -> dict:
    config = dict(DEFAULT_CONFIG)
    env_values = load_env_config()
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            config.update(raw)
    except Exception:
        pass
    for key, aliases in ENV_KEY_ALIASES.items():
        normalized_key = key.lower() if key.isupper() else key
        for env_key in aliases:
            value = os.getenv(env_key) or env_values.get(env_key)
            if value:
                config[normalized_key] = value
                break
    return config


def save_app_config(updates: dict) -> dict:
    config = load_app_config()
    for key, value in (updates or {}).items():
        if value is None:
            continue
        config[key] = value
    save_env_config(updates or {})
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(config, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )
    return config


def get_app_config_value(key: str, default=None):
    config = load_app_config()
    if key in config:
        return config.get(key, default)
    return config.get(key.lower(), default)


def has_gemini_api_key() -> bool:
    value = str(get_app_config_value("gemini_api_key", "") or "").strip()
    return bool(value)
