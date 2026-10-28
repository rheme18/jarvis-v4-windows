from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
HISTORY_FILE = BASE_DIR / "memory" / "intent_history.jsonl"


def _shorten(value, limit: int = 500):
    text = value if isinstance(value, str) else repr(value)
    if len(text) > limit:
        return text[:limit] + "..."
    return text


def record_tool_use(tool_name: str, args: dict | None = None, result=None, status: str = "ok") -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    item = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "tool": str(tool_name or ""),
        "status": str(status or "ok"),
        "args": {str(k): _shorten(v, 240) for k, v in (args or {}).items()},
        "result": _shorten(result, 500),
    }
    with HISTORY_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=False) + "\n")


def _load_history(limit: int = 200) -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    rows: list[dict] = []
    try:
        for line in HISTORY_FILE.read_text(encoding="utf-8").splitlines()[-max(1, limit):]:
            try:
                item = json.loads(line)
                if isinstance(item, dict):
                    rows.append(item)
            except Exception:
                continue
    except Exception:
        return []
    return rows


def intent_history(action: str = "report", query: str = "", limit: int = 15) -> str:
    action = (action or "report").strip().lower()
    query = (query or "").strip().lower()
    limit = max(1, min(int(limit or 15), 50))
    rows = _load_history(500)

    if action in {"report", "summary"}:
        if not rows:
            return "Henuz kayitli Jarvis arac gecmisi yok."
        counts: dict[str, int] = {}
        errors = 0
        for item in rows:
            tool = str(item.get("tool", "unknown"))
            counts[tool] = counts.get(tool, 0) + 1
            if item.get("status") != "ok":
                errors += 1
        top = sorted(counts.items(), key=lambda pair: pair[1], reverse=True)[:8]
        lines = [
            f"Jarvis arac gecmisi: son {len(rows)} kayit.",
            f"Hata gorunen kayit: {errors}",
            "En cok kullanilan araclar:",
        ]
        lines.extend(f"- {name}: {count}" for name, count in top)
        return "\n".join(lines)

    if action in {"list", "latest"}:
        if not rows:
            return "Henuz kayitli arac gecmisi yok."
        lines = ["Son Jarvis araclari:"]
        for item in rows[-limit:][::-1]:
            lines.append(f"- {item.get('ts')} | {item.get('tool')} | {item.get('status')}")
        return "\n".join(lines)

    if action == "search":
        if not query:
            return "Gecmiste aramak icin query gerekli."
        matched = [item for item in rows if query in json.dumps(item, ensure_ascii=False).lower()]
        if not matched:
            return f"'{query}' icin arac gecmisi bulunamadi."
        lines = [f"'{query}' ile eslesen son kayitlar:"]
        for item in matched[-limit:][::-1]:
            lines.append(f"- {item.get('ts')} | {item.get('tool')} | {item.get('status')}")
        return "\n".join(lines)

    if action == "clear":
        HISTORY_FILE.write_text("", encoding="utf-8")
        return "Jarvis arac gecmisi temizlendi."

    return f"Bilinmeyen gecmis eylemi: {action}"
