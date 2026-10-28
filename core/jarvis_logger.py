from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from core.event_bus import emit


BASE_DIR = Path(__file__).resolve().parents[1]
LOG_PATH = BASE_DIR / "memory" / "jarvis_logs.jsonl"


def log_event(level: str, category: str, message: str, **data: Any) -> dict[str, Any]:
    row = {
        "ts": dt.datetime.now().isoformat(timespec="seconds"),
        "level": (level or "INFO").upper(),
        "category": category or "general",
        "message": message or "",
        "data": data,
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    emit("log", row["message"], level=row["level"], category=row["category"], **data)
    return row


def read_logs(limit: int = 120, level: str = "", category: str = "") -> list[dict[str, Any]]:
    if not LOG_PATH.exists():
        return []
    try:
        rows = [json.loads(line) for line in LOG_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    except Exception:
        return []
    level = (level or "").upper()
    category = (category or "").lower()
    if level:
        rows = [row for row in rows if row.get("level") == level]
    if category:
        rows = [row for row in rows if str(row.get("category", "")).lower() == category]
    return rows[-max(1, int(limit or 120)):]
