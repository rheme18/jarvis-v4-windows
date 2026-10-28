from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
USAGE_FILE = BASE_DIR / "memory" / "app_usage.jsonl"


def _active_window() -> tuple[str, str]:
    try:
        import win32gui
        import win32process
        import psutil

        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd) or "Bilinmeyen pencere"
        _tid, pid = win32process.GetWindowThreadProcessId(hwnd)
        proc = psutil.Process(pid)
        return proc.name(), title
    except Exception:
        return "unknown", "Aktif pencere alinamadi"


def _append(proc_name: str, title: str) -> None:
    USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    item = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "process": proc_name,
        "title": title[:200],
    }
    with USAGE_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=False) + "\n")


def _load(limit: int = 500) -> list[dict]:
    if not USAGE_FILE.exists():
        return []
    rows = []
    for line in USAGE_FILE.read_text(encoding="utf-8").splitlines()[-max(1, limit):]:
        try:
            item = json.loads(line)
            if isinstance(item, dict):
                rows.append(item)
        except Exception:
            continue
    return rows


def app_usage(action: str = "snapshot", limit: int = 20) -> str:
    action = (action or "snapshot").strip().lower()
    limit = max(1, min(int(limit or 20), 80))

    if action in {"snapshot", "log"}:
        proc_name, title = _active_window()
        _append(proc_name, title)
        return f"Aktif uygulama kaydedildi: {proc_name} | {title}"

    rows = _load(1000)
    if action in {"report", "summary"}:
        if not rows:
            return "Henuz uygulama kullanim kaydi yok. snapshot eylemiyle kayit alinabilir."
        counts: dict[str, int] = {}
        for item in rows:
            proc = str(item.get("process") or "unknown")
            counts[proc] = counts.get(proc, 0) + 1
        top = sorted(counts.items(), key=lambda pair: pair[1], reverse=True)[:limit]
        lines = [f"Uygulama kullanim ozeti: {len(rows)} pencere kaydi."]
        lines.extend(f"- {proc}: {count} kayit" for proc, count in top)
        return "\n".join(lines)

    if action in {"list", "latest"}:
        if not rows:
            return "Henuz uygulama kullanim kaydi yok."
        lines = ["Son uygulama kayitlari:"]
        for item in rows[-limit:][::-1]:
            lines.append(f"- {item.get('ts')} | {item.get('process')} | {item.get('title')}")
        return "\n".join(lines)

    if action == "clear":
        USAGE_FILE.write_text("", encoding="utf-8")
        return "Uygulama kullanim kayitlari temizlendi."

    return f"Bilinmeyen uygulama kullanim eylemi: {action}"
