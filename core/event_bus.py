from __future__ import annotations

import datetime as dt
import json
import threading
from collections import deque
from pathlib import Path
from typing import Any, Callable


BASE_DIR = Path(__file__).resolve().parents[1]
EVENT_LOG_PATH = BASE_DIR / "memory" / "events.jsonl"
MAX_EVENTS = 600
Subscriber = Callable[[dict[str, Any]], None]

_events: deque[dict[str, Any]] = deque(maxlen=MAX_EVENTS)
_subscribers: list[Subscriber] = []
_lock = threading.RLock()


def emit(event_type: str, message: str = "", **data: Any) -> dict[str, Any]:
    event = {
        "ts": dt.datetime.now().isoformat(timespec="seconds"),
        "type": event_type,
        "message": message,
        "data": data,
    }
    with _lock:
        _events.append(event)
        EVENT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with EVENT_LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
        subscribers = list(_subscribers)
    for subscriber in subscribers:
        try:
            subscriber(event)
        except Exception:
            pass
    return event


def subscribe(callback: Subscriber) -> None:
    with _lock:
        if callback not in _subscribers:
            _subscribers.append(callback)


def recent_events(limit: int = 80, event_type: str = "") -> list[dict[str, Any]]:
    event_type = (event_type or "").strip()
    with _lock:
        rows = list(_events)
    if not rows and EVENT_LOG_PATH.exists():
        try:
            lines = EVENT_LOG_PATH.read_text(encoding="utf-8").splitlines()[-MAX_EVENTS:]
            rows = [json.loads(line) for line in lines if line.strip()]
        except Exception:
            rows = []
    if event_type:
        rows = [row for row in rows if row.get("type") == event_type]
    return rows[-max(1, int(limit or 80)):]
