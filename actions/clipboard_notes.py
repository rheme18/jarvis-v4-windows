from __future__ import annotations

from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
CLIPBOARD_LOG = BASE_DIR / "memory" / "clipboard_notes.md"


def _read_clipboard() -> str:
    try:
        import pyperclip

        return str(pyperclip.paste() or "")
    except Exception as exc:
        return f"[clipboard_error] {exc}"


def _simple_summary(text: str, max_chars: int = 500) -> str:
    clean = " ".join((text or "").split())
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 3].rstrip() + "..."


def clipboard_notes(action: str, text: str = "", title: str = "") -> str:
    action = (action or "read").strip().lower()
    content = text if text else _read_clipboard()
    title = (title or "Clipboard note").strip()

    if content.startswith("[clipboard_error]"):
        return f"Pano okunamadi: {content}"

    if action in {"read", "show"}:
        if not content.strip():
            return "Pano bos gorunuyor."
        return "Panodaki metin:\n" + _simple_summary(content, 1500)

    if action in {"summary", "summarize"}:
        if not content.strip():
            return "Ozetlenecek pano metni yok."
        return "Pano ozeti:\n" + _simple_summary(content, 600)

    if action in {"save", "append"}:
        if not content.strip():
            return "Kaydedilecek pano metni yok."
        CLIPBOARD_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = [
            f"## {title} - {datetime.now().isoformat(timespec='seconds')}",
            "",
            content.strip(),
            "",
        ]
        with CLIPBOARD_LOG.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(entry))
        return f"Pano notu kaydedildi: {CLIPBOARD_LOG.name}"

    return f"Bilinmeyen pano eylemi: {action}"
