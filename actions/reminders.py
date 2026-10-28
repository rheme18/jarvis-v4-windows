from __future__ import annotations

import datetime as dt
import json
import uuid
from pathlib import Path
from typing import Any

from core.error_boundary import log_root_cause


BASE_DIR = Path(__file__).resolve().parent.parent
LOCAL_REMINDERS_FILE = BASE_DIR / "memory" / "reminders.json"
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"
SCOPES = ["https://www.googleapis.com/auth/tasks"]


def _load_local() -> list[dict[str, Any]]:
    try:
        data = json.loads(LOCAL_REMINDERS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_local(rows: list[dict[str, Any]]) -> None:
    LOCAL_REMINDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_REMINDERS_FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def _google_available() -> bool:
    return CREDENTIALS_FILE.exists()


def _get_tasks_service():
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except Exception as exc:
        raise RuntimeError(
            "Google Tasks paketleri eksik. Local reminder fallback kullaniliyor."
        ) from exc

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError("credentials.json bulunamadi")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return build("tasks", "v1", credentials=creds)


def _get_or_create_jarvis_list(service) -> str:
    lists_result = service.tasklists().list().execute()
    tasklists = lists_result.get("items", [])
    for task_list in tasklists:
        if task_list.get("title") == "JARVIS_Tasks":
            return task_list["id"]
    created = service.tasklists().insert(body={"title": "JARVIS_Tasks"}).execute()
    return created["id"]


def _local_due_sort(item: dict[str, Any]) -> str:
    return str(item.get("due_iso") or "9999-12-31")


def _format_local(rows: list[dict[str, Any]], limit: int) -> str:
    if not rows:
        return "Yerel hatirlatici listen bos."
    lines = ["Yerel hatirlaticilar:"]
    for item in sorted(rows, key=_local_due_sort)[:limit]:
        due = f" | {item.get('due_iso')}" if item.get("due_iso") else ""
        priority = f" | {item.get('priority')}" if item.get("priority") else ""
        lines.append(f"- {item.get('title', 'Adsiz')}{due}{priority}")
    return "\n".join(lines)


def _query_local(query: str, limit: int) -> str:
    query_l = (query or "upcoming").strip().lower()
    rows = [item for item in _load_local() if item.get("status", "open") == "open"]
    today = dt.date.today().isoformat()
    if query_l in {"today", "bugun"}:
        rows = [item for item in rows if str(item.get("due_iso", "")).startswith(today)]
    elif query_l in {"overdue", "gecmis"}:
        rows = [item for item in rows if item.get("due_iso") and str(item["due_iso"])[:10] < today]
    elif query_l not in {"all", "upcoming", "next"}:
        rows = [item for item in rows if query_l in str(item.get("title", "")).lower()]
    return _format_local(rows, limit)


def _add_local(title: str, due_iso: str = "", notes: str = "", priority: str = "") -> str:
    rows = _load_local()
    item = {
        "id": uuid.uuid4().hex[:10],
        "title": title.strip(),
        "due_iso": due_iso.strip(),
        "notes": notes.strip(),
        "priority": priority.strip() or "medium",
        "status": "open",
        "created_at": dt.datetime.now().isoformat(timespec="seconds"),
    }
    rows.append(item)
    _save_local(rows)
    due = f" ({due_iso})" if due_iso else ""
    return f"Yerel hatirlatici eklendi: {title}{due}"


def _delete_local(title: str) -> str:
    rows = _load_local()
    needle = (title or "").strip().lower()
    for item in rows:
        if needle and needle in str(item.get("title", "")).lower() and item.get("status", "open") == "open":
            item["status"] = "deleted"
            item["deleted_at"] = dt.datetime.now().isoformat(timespec="seconds")
            _save_local(rows)
            return f"Yerel hatirlatici silindi: {item.get('title')}"
    return f"'{title}' icin acik hatirlatici bulunamadi."


def get_reminders(query: str = "upcoming", limit: int = 8, list_name: str = "") -> str:
    limit = max(1, min(int(limit or 8), 50))
    if not _google_available():
        return _query_local(query, limit)
    try:
        service = _get_tasks_service()
        list_id = _get_or_create_jarvis_list(service)
        result = service.tasks().list(tasklist=list_id, showCompleted=False, maxResults=limit).execute()
        items = result.get("items", [])
        if not items:
            return "Google Tasks listenizde acik hatirlatici yok."
        lines = ["Google Tasks hatirlaticilari:"]
        for item in items:
            due = f" | {item['due'].split('T')[0]}" if item.get("due") else ""
            lines.append(f"- {item.get('title', 'Adsiz')}{due}")
        return "\n".join(lines)
    except Exception as exc:
        log_root_cause("reminders", "Google Tasks okunamadi, local fallback kullanildi", exc)
        return _query_local(query, limit)


def add_reminder(
    title: str,
    due_iso: str = "",
    notes: str = "",
    list_name: str = "",
    priority: str = "",
    all_day: bool = False,
) -> str:
    if not title or not title.strip():
        return "Hatirlatici basligi bos olamaz."
    if not _google_available():
        return _add_local(title, due_iso, notes, priority)
    try:
        service = _get_tasks_service()
        list_id = _get_or_create_jarvis_list(service)
        body: dict[str, Any] = {"title": title.strip(), "notes": notes or "JARVIS tarafindan eklendi."}
        if due_iso:
            clean_date = due_iso.split("T")[0]
            body["due"] = f"{clean_date}T00:00:00Z"
        service.tasks().insert(tasklist=list_id, body=body).execute()
        return f"Google Tasks hatirlaticisi eklendi: {title}"
    except Exception as exc:
        log_root_cause("reminders", "Google Tasks ekleme basarisiz, local fallback kullanildi", exc)
        return _add_local(title, due_iso, notes, priority)


def delete_reminder(title: str, list_name: str = "") -> str:
    if not title or not title.strip():
        return "Silinecek hatirlatici basligi bos olamaz."
    if not _google_available():
        return _delete_local(title)
    try:
        service = _get_tasks_service()
        list_id = _get_or_create_jarvis_list(service)
        result = service.tasks().list(tasklist=list_id, showCompleted=False).execute()
        for item in result.get("items", []):
            if title.lower() in item.get("title", "").lower():
                service.tasks().delete(tasklist=list_id, task=item["id"]).execute()
                return f"Google Tasks hatirlaticisi silindi: {item.get('title')}"
        return f"Google Tasks icinde '{title}' bulunamadi."
    except Exception as exc:
        log_root_cause("reminders", "Google Tasks silme basarisiz, local fallback kullanildi", exc)
        return _delete_local(title)
