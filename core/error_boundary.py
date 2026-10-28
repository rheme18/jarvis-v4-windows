from __future__ import annotations

import traceback
from typing import Any


def root_cause(exc: BaseException) -> BaseException:
    current: BaseException = exc
    seen: set[int] = set()
    while True:
        marker = id(current)
        if marker in seen:
            return current
        seen.add(marker)
        next_exc = current.__cause__ or current.__context__
        if not next_exc:
            return current
        current = next_exc


def compact_exception(exc: BaseException, limit: int = 2200) -> str:
    cause = root_cause(exc)
    stack = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    text = (
        f"{type(exc).__name__}: {exc}\n"
        f"root_cause={type(cause).__name__}: {cause}\n"
        f"{stack}"
    )
    return text[: max(200, int(limit or 2200))]


def log_root_cause(category: str, message: str, exc: BaseException | None = None, **context: Any) -> None:
    payload: dict[str, Any] = dict(context)
    if exc is not None:
        cause = root_cause(exc)
        payload.update(
            {
                "error_type": type(exc).__name__,
                "error": str(exc),
                "root_cause_type": type(cause).__name__,
                "root_cause": str(cause),
                "traceback": compact_exception(exc),
            }
        )

    try:
        from core.jarvis_logger import log_event

        log_event("ERROR" if exc else "INFO", category, message, **payload)
    except Exception:
        pass

    try:
        from core.event_bus import emit

        emit("error" if exc else "event", message, category=category, **payload)
    except Exception:
        pass


def graceful_error(tool_name: str, exc: BaseException) -> str:
    cause = root_cause(exc)
    return (
        f"{tool_name} araci calisirken hata olustu. "
        f"Kok neden: {type(cause).__name__}: {cause}"
    )
