from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4


BASE_DIR = Path(__file__).resolve().parent.parent
NOTES_FILE = BASE_DIR / "memory" / "quick_notes.json"


def _load_notes() -> list[dict]:
    try:
        data = json.loads(NOTES_FILE.read_text(encoding="utf-8"))
        return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []
    except Exception:
        return []


def _save_notes(notes: list[dict]) -> None:
    NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = NOTES_FILE.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(notes, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(NOTES_FILE)


def quick_note(action: str, text: str = "", query: str = "", note_id: str = "", limit: int = 10) -> str:
    action = (action or "list").strip().lower()
    text = (text or "").strip()
    query = (query or "").strip().lower()
    note_id = (note_id or "").strip()
    notes = _load_notes()

    if action in {"add", "save", "note"}:
        if not text:
            return "Not almak icin metin gerekli."
        item = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S") + "-" + uuid4().hex[:6],
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "text": text,
        }
        notes.insert(0, item)
        _save_notes(notes)
        return f"Not kaydedildi. ID: {item['id']}"

    if action in {"update", "edit"}:
        if not note_id:
            return "Düzenlemek için note_id gerekli."
        if not text:
            return "Not metni boş bırakılamaz."
        for item in notes:
            if str(item.get("id", "")) == note_id:
                item["text"] = text
                item["updated_at"] = datetime.now().isoformat(timespec="seconds")
                _save_notes(notes)
                return f"Not güncellendi. ID: {note_id}"
        return "Güncellenecek not bulunamadı."

    if action in {"list", "latest", "recent"}:
        if not notes:
            return "Kayitli hizli not yok."
        limit = max(1, min(int(limit or 10), 25))
        lines = ["Son hizli notlar:"]
        for item in notes[:limit]:
            lines.append(f"- {item.get('id')}: {item.get('text', '')}")
        return "\n".join(lines)

    if action == "search":
        if not query:
            return "Aranacak not metni gerekli."
        matched = [n for n in notes if query in str(n.get("text", "")).lower()]
        if not matched:
            return f"'{query}' icin not bulunamadi."
        lines = [f"'{query}' ile eslesen notlar:"]
        for item in matched[:10]:
            lines.append(f"- {item.get('id')}: {item.get('text', '')}")
        return "\n".join(lines)

    if action == "delete":
        if not note_id and not query:
            return "Silmek icin note_id veya query gerekli."
        kept = []
        removed = []
        for item in notes:
            is_match = note_id and item.get("id") == note_id
            if not is_match and query:
                is_match = query in str(item.get("text", "")).lower()
            if is_match:
                removed.append(item)
            else:
                kept.append(item)
        if not removed:
            return "Silinecek not bulunamadi."
        _save_notes(kept)
        return f"{len(removed)} not silindi."

    return f"Bilinmeyen hizli not eylemi: {action}"
