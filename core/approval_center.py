from __future__ import annotations

import datetime as dt
import json
import uuid
from pathlib import Path
from typing import Any

from core.event_bus import emit
from core.settings_store import get_setting


BASE_DIR = Path(__file__).resolve().parents[1]
APPROVALS_PATH = BASE_DIR / "memory" / "approvals.json"

RISKY_TOOLS = {
    "shell_run",
    "manage_file",
    "pc_control",
    "git_push",
    "safe_cleaner",
    "backup_manager",
}


def _load() -> list[dict[str, Any]]:
    try:
        data = json.loads(APPROVALS_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(rows: list[dict[str, Any]]) -> None:
    APPROVALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    APPROVALS_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def needs_approval(tool_name: str, args: dict[str, Any] | None = None) -> bool:
    if not get_setting("security", "approval_center", True):
        return False
    args = args or {}
    # Sadece UI veya Telegram doğrulanmış onay token'ı (_approved: True) onayı baypas edebilir.
    # Modelin kendi kendine 'confirm: True' argümanı üretmesi insan onayını atlatamaz!
    if args.get("_approved") is True or args.get("_user_confirmed") is True:
        return False
    name = (tool_name or "").strip()
    if name == "shell_run" and get_setting("security", "shell_requires_approval", True):
        return True
    if name == "pc_control" and get_setting("security", "pc_power_requires_approval", True):
        action = str(args.get("action", "")).lower()
        return action in {"shutdown", "reboot", "sleep", "lock", "close_app"}
    if name == "manage_file" and get_setting("security", "file_delete_requires_approval", True):
        return str(args.get("action", "")).lower() in {"delete", "remove", "rmdir"}
    return name in RISKY_TOOLS


def request_approval(tool_name: str, args: dict[str, Any] | None = None, reason: str = "") -> dict[str, Any]:
    rows = _load()
    item = {
        "id": uuid.uuid4().hex[:12],
        "ts": dt.datetime.now().isoformat(timespec="seconds"),
        "tool": tool_name,
        "args": args or {},
        "reason": reason or "Riskli islem onay bekliyor.",
        "status": "pending",
    }
    rows.append(item)
    _save(rows)
    emit("approval_pending", f"{tool_name} onay bekliyor", approval_id=item["id"], tool=tool_name)
    return item


def decide(approval_id: str, approved: bool) -> str:
    rows = _load()
    for row in rows:
        if row.get("id") == approval_id:
            row["status"] = "approved" if approved else "rejected"
            row["decided_at"] = dt.datetime.now().isoformat(timespec="seconds")
            _save(rows)
            emit("approval_decided", f"{approval_id} {'approved' if approved else 'rejected'}", approval_id=approval_id)
            return row["status"]
    return "not_found"


def pending(limit: int = 50) -> list[dict[str, Any]]:
    rows = [row for row in _load() if row.get("status") == "pending"]
    return rows[-max(1, int(limit or 50)):]
