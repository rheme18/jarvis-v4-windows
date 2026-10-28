from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app_config import BASE_DIR, get_app_config_value


SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]


def _log_root(area: str, exc: Exception, **data: Any) -> None:
    try:
        from core.error_boundary import log_root_cause

        log_root_cause("google", f"Google manager failed: {area}", exc, **data)
    except Exception:
        pass


def _resolve_path(value: str, fallback: str) -> Path:
    raw = str(value or fallback).strip()
    path = Path(raw)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path


def _google_paths() -> tuple[Path, Path]:
    credentials = _resolve_path(
        str(get_app_config_value("google_credentials_file", "") or ""),
        "config/google_credentials.json",
    )
    token = _resolve_path(
        str(get_app_config_value("google_token_file", "") or ""),
        "config/google_token.json",
    )
    return credentials, token


def _user_id() -> str:
    return str(get_app_config_value("gmail_user_id", "me") or "me").strip() or "me"


def _dependency_error(exc: Exception) -> str:
    return (
        "Google API kutuphaneleri yuklu degil. requirements.txt icindeki "
        f"google paketlerini kur: {type(exc).__name__}: {exc}"
    )


def get_google_service(service_name: str, version: str):
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except Exception as exc:
        return _dependency_error(exc)

    credentials_file, token_file = _google_paths()
    creds = None

    try:
        if token_file.exists():
            creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_file.parent.mkdir(parents=True, exist_ok=True)
            token_file.write_text(creds.to_json(), encoding="utf-8")

        if not creds or not creds.valid:
            if not credentials_file.exists():
                return (
                    "Google kimlik dosyasi bulunamadi. config/.env icinde "
                    "GOOGLE_CREDENTIALS_FILE=config/google_credentials.json ayarla ve dosyayi ekle."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), SCOPES)
            creds = flow.run_local_server(port=0)
            token_file.parent.mkdir(parents=True, exist_ok=True)
            token_file.write_text(creds.to_json(), encoding="utf-8")

        return build(service_name, version, credentials=creds, cache_discovery=False)
    except Exception as exc:
        _log_root("auth", exc, service=service_name, version=version)
        return f"Google kimlik dogrulama hatasi: {type(exc).__name__}: {exc}"


def _service_or_message(service_name: str, version: str):
    service = get_google_service(service_name, version)
    if isinstance(service, str):
        return None, service
    if service is None:
        return None, "Google servisi baslatilamadi."
    return service, None


def _header_value(headers: list[dict[str, str]], name: str) -> str:
    target = name.lower()
    for item in headers:
        if str(item.get("name", "")).lower() == target:
            return str(item.get("value", "") or "")
    return ""


def gmail_search(query: str = "", limit: int = 5) -> str:
    try:
        service, error = _service_or_message("gmail", "v1")
        if error:
            return error
        limit = max(1, min(20, int(limit or 5)))
        result = service.users().messages().list(userId=_user_id(), q=str(query or ""), maxResults=limit).execute()
        messages = result.get("messages", [])
        if not messages:
            return "Gmail aramasinda e-posta bulunamadi."

        lines = ["Gmail sonuclari:"]
        for item in messages[:limit]:
            msg = (
                service.users()
                .messages()
                .get(
                    userId=_user_id(),
                    id=item["id"],
                    format="metadata",
                    metadataHeaders=["Subject", "From", "Date"],
                )
                .execute()
            )
            headers = msg.get("payload", {}).get("headers", [])
            subject = _header_value(headers, "Subject") or "Baslik yok"
            sender = _header_value(headers, "From") or "Bilinmeyen gonderen"
            date = _header_value(headers, "Date") or "Tarih yok"
            snippet = str(msg.get("snippet", "") or "").replace("\n", " ")[:180]
            lines.append(f"- {subject} | {sender} | {date}\n  {snippet}")
        return "\n".join(lines)
    except Exception as exc:
        _log_root("gmail_search", exc, query=query)
        return f"Gmail arama hatasi: {type(exc).__name__}: {exc}"


def gmail_labels() -> str:
    try:
        service, error = _service_or_message("gmail", "v1")
        if error:
            return error
        result = service.users().labels().list(userId=_user_id()).execute()
        labels = result.get("labels", [])
        if not labels:
            return "Gmail etiketi bulunamadi."
        return "Gmail etiketleri:\n" + "\n".join(f"- {item.get('name')} ({item.get('id')})" for item in labels)
    except Exception as exc:
        _log_root("gmail_labels", exc)
        return f"Gmail etiket hatasi: {type(exc).__name__}: {exc}"


def get_latest_email() -> str:
    return gmail_search("", 1).replace("Gmail sonuclari:", "Son e-posta:", 1)


def _drive_literal(value: str) -> str:
    return str(value or "").replace("\\", "\\\\").replace("'", "\\'")


def drive_search_logic(query: str, limit: int = 5) -> str:
    try:
        service, error = _service_or_message("drive", "v3")
        if error:
            return error
        text = _drive_literal(query)
        limit = max(1, min(20, int(limit or 5)))
        result = (
            service.files()
            .list(
                q=f"name contains '{text}' and trashed = false",
                pageSize=limit,
                fields="files(id, name, mimeType, webViewLink, modifiedTime)",
                orderBy="modifiedTime desc",
            )
            .execute()
        )
        files = result.get("files", [])
        if not files:
            return f"Drive icinde '{query}' ile ilgili dosya bulunamadi."
        lines = ["Google Drive sonuclari:"]
        for item in files:
            lines.append(f"- {item.get('name')} ({item.get('modifiedTime', '')[:10]}) {item.get('webViewLink', '')}")
        return "\n".join(lines)
    except Exception as exc:
        _log_root("drive_search", exc, query=query)
        return f"Drive arama hatasi: {type(exc).__name__}: {exc}"


def _calendar_window(query: str) -> tuple[datetime, datetime | None]:
    now = datetime.now(timezone.utc)
    q = str(query or "today").lower()
    if "tomorrow" in q or "yarin" in q:
        start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return start, start + timedelta(days=1)
    if "week" in q or "hafta" in q:
        return now, now + timedelta(days=7)
    if "month" in q or "ay" in q:
        return now, now + timedelta(days=31)
    if "next" in q or "upcoming" in q or "siradaki" in q or "yaklasan" in q:
        return now, None
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=1)


def calendar_events(query: str = "today", limit: int = 8) -> str:
    try:
        service, error = _service_or_message("calendar", "v3")
        if error:
            return error
        limit = max(1, min(30, int(limit or 8)))
        start, end = _calendar_window(query)
        params: dict[str, Any] = {
            "calendarId": "primary",
            "timeMin": start.isoformat(),
            "maxResults": limit,
            "singleEvents": True,
            "orderBy": "startTime",
        }
        if end:
            params["timeMax"] = end.isoformat()
        result = service.events().list(**params).execute()
        events = result.get("items", [])
        if not events:
            return "Google Calendar icinde eslesen etkinlik bulunamadi."
        lines = ["Google Calendar etkinlikleri:"]
        for event in events[:limit]:
            start_info = event.get("start", {})
            when = start_info.get("dateTime") or start_info.get("date") or "tarih yok"
            location = f" @ {event.get('location')}" if event.get("location") else ""
            lines.append(f"- {when}: {event.get('summary', 'Baslik yok')}{location}")
        return "\n".join(lines)
    except Exception as exc:
        _log_root("calendar_events", exc, query=query)
        return f"Calendar hatasi: {type(exc).__name__}: {exc}"
