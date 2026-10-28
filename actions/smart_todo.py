from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
TODO_FILE = BASE_DIR / "memory" / "smart_todo.json"


def _load() -> list[dict]:
    try:
        data = json.loads(TODO_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(items: list[dict]) -> None:
    TODO_FILE.parent.mkdir(parents=True, exist_ok=True)
    TODO_FILE.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")


def _match(item: dict, text: str) -> bool:
    blob = " ".join(str(item.get(key, "")) for key in ("id", "title", "notes", "priority", "due"))
    return text.lower() in blob.lower()


def smart_todo(
    action: str = "list",
    title: str = "",
    notes: str = "",
    priority: str = "medium",
    due: str = "",
    todo_id: str = "",
    query: str = "",
    limit: int = 12,
) -> str:
    action = (action or "list").strip().lower()
    title = (title or "").strip()
    notes = (notes or "").strip()
    priority = (priority or "medium").strip().lower()
    due = (due or "").strip()
    todo_id = (todo_id or "").strip()
    query = (query or "").strip()
    limit = max(1, min(int(limit or 12), 50))
    items = _load()

    if action in {"add", "create"}:
        if not title:
            return "Gorev eklemek icin title gerekli."
        item = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "done": False,
            "title": title,
            "notes": notes,
            "priority": priority if priority in {"low", "medium", "high"} else "medium",
            "due": due,
        }
        items.insert(0, item)
        _save(items)
        return f"Gorev eklendi. ID: {item['id']} | {item['title']}"

    if action in {"list", "today", "open"}:
        open_items = [item for item in items if not item.get("done")]
        if action == "today":
            today = datetime.now().date().isoformat()
            open_items = [item for item in open_items if str(item.get("due", "")).startswith(today)]
        if not open_items:
            return "Acik gorev yok."
        rank = {"high": 0, "medium": 1, "low": 2}
        open_items.sort(key=lambda item: (rank.get(str(item.get("priority")), 3), str(item.get("due", ""))))
        lines = ["Acik gorevler:"]
        for item in open_items[:limit]:
            due_text = f" | son: {item.get('due')}" if item.get("due") else ""
            lines.append(f"- {item.get('id')} [{item.get('priority')}] {item.get('title')}{due_text}")
        return "\n".join(lines)

    if action in {"done", "complete"}:
        target = todo_id or query or title
        if not target:
            return "Tamamlamak icin todo_id, query veya title gerekli."
        changed = 0
        for item in items:
            if str(item.get("id")) == target or _match(item, target):
                item["done"] = True
                item["completed_at"] = datetime.now().isoformat(timespec="seconds")
                changed += 1
                break
        if not changed:
            return "Tamamlanacak gorev bulunamadi."
        _save(items)
        return "Gorev tamamlandi."

    if action == "search":
        if not query:
            return "Arama icin query gerekli."
        matched = [item for item in items if _match(item, query)]
        if not matched:
            return f"'{query}' icin gorev bulunamadi."
        lines = [f"'{query}' ile eslesen gorevler:"]
        for item in matched[:limit]:
            state = "tamam" if item.get("done") else "acik"
            lines.append(f"- {item.get('id')} [{state}] {item.get('title')}")
        return "\n".join(lines)

    if action == "delete":
        target = todo_id or query or title
        if not target:
            return "Silmek icin todo_id, query veya title gerekli."
        kept = [item for item in items if not (str(item.get("id")) == target or _match(item, target))]
        removed = len(items) - len(kept)
        if not removed:
            return "Silinecek gorev bulunamadi."
        _save(kept)
        return f"{removed} gorev silindi."

    if action == "stats":
        open_count = sum(1 for item in items if not item.get("done"))
        done_count = len(items) - open_count
        high_count = sum(1 for item in items if not item.get("done") and item.get("priority") == "high")
        return f"Gorev ozeti: {open_count} acik, {done_count} tamamlanmis, {high_count} yuksek oncelik."

    return f"Bilinmeyen gorev eylemi: {action}"
