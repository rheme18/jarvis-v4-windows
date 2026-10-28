from __future__ import annotations

import re
import unicodedata


TR_FIXES = {
    "Ä±": "ı",
    "Ä°": "İ",
    "ÅŸ": "ş",
    "Å": "Ş",
    "ÄŸ": "ğ",
    "Äž": "Ğ",
    "Ã¼": "ü",
    "Ãœ": "Ü",
    "Ã¶": "ö",
    "Ã–": "Ö",
    "Ã§": "ç",
    "Ã‡": "Ç",
}


def _slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "metin"


def text_tools(action: str, text: str = "", max_chars: int = 600) -> str:
    action = (action or "clean").strip().lower()
    text = text or ""

    if action in {"clean", "normalize"}:
        return " ".join(text.split())

    if action in {"fix_turkish", "fix_encoding"}:
        fixed = text
        for bad, good in TR_FIXES.items():
            fixed = fixed.replace(bad, good)
        return fixed

    if action in {"summary", "summarize"}:
        clean = " ".join(text.split())
        max_chars = max(80, int(max_chars or 600))
        return clean if len(clean) <= max_chars else clean[: max_chars - 3].rstrip() + "..."

    if action == "slug":
        return _slugify(text)

    if action in {"count", "stats"}:
        words = [w for w in re.split(r"\s+", text.strip()) if w]
        return f"Karakter: {len(text)}, kelime: {len(words)}, satir: {len(text.splitlines())}"

    return f"Bilinmeyen metin araci eylemi: {action}"
