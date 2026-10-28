# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S V4 — Granular Tool Permission & Safety Gate
Enforces confirmation rules for sensitive operations (email sending, terminal commands, file deletion, system controls).
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PERMS_FILE = BASE_DIR / "config" / "permissions.json"

DEFAULT_PERMS = {
    "send_email": True,
    "create_excel": True,
    "create_powerpoint": True,
    "create_word_doc": True,
    "create_pdf": True,
    "read_emails": True,
    "read_whatsapp": True,
    "safe_cleaner": False,
    "shell_exec": False,
}


def load_permissions() -> dict:
    if PERMS_FILE.is_file():
        try:
            return json.loads(PERMS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return dict(DEFAULT_PERMS)


def save_permissions(perms: dict):
    PERMS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PERMS_FILE.write_text(json.dumps(perms, indent=2, ensure_ascii=False), encoding="utf-8")


def check_tool_permission(tool_name: str) -> bool:
    """Returns True if the tool is allowed to run automatically without blocking."""
    perms = load_permissions()
    return perms.get(tool_name, True)


def set_tool_permission(tool_name: str, allowed: bool):
    perms = load_permissions()
    perms[tool_name] = allowed
    save_permissions(perms)
