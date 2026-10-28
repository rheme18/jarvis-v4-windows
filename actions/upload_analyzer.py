from __future__ import annotations

import mimetypes
import time
from pathlib import Path

from google import genai
from google.genai import errors, types

from app_config import get_app_config_value


TOOL_DECLARATION = {
    "name": "uploaded_file_analyzer",
    "description": "Web panel veya dosya yolu uzerinden gorsel, PDF ve metin dosyalarini analiz eder.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "file_path": {"type": "STRING", "description": "Analiz edilecek dosyanin tam yolu."},
            "prompt": {"type": "STRING", "description": "Kullanici analizi istegi."},
        },
        "required": ["file_path"],
    },
}

PLUGIN_META = {
    "category": "web",
    "danger": "safe",
    "ui_visible": True,
    "aliases": ["dosya analiz", "gorsel analiz", "pdf analiz"],
}


TEXT_EXTS = {".txt", ".md", ".py", ".json", ".csv", ".log", ".html", ".css", ".js", ".xml", ".yaml", ".yml"}
INLINE_LIMIT = 18_000_000
TEXT_LIMIT = 80_000
MODELS = ("models/gemini-2.0-flash", "models/gemini-2.5-flash-lite", "models/gemini-2.5-flash")


def _response_text(response) -> str:
    text = str(getattr(response, "text", "") or "").strip()
    if text:
        return text
    chunks: list[str] = []
    for candidate in getattr(response, "candidates", None) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", None) or []:
            part_text = str(getattr(part, "text", "") or "").strip()
            if part_text:
                chunks.append(part_text)
    return "\n".join(chunks).strip()


def _transient(exc: Exception) -> bool:
    message = str(exc).lower()
    markers = ("503", "429", "timeout", "deadline", "unavailable", "overloaded", "resource exhausted")
    return isinstance(exc, (errors.ServerError, TimeoutError)) or any(item in message for item in markers)


def _mime(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(str(path))
    if guessed:
        return guessed
    if path.suffix.lower() == ".pdf":
        return "application/pdf"
    return "application/octet-stream"


def _prompt(path: Path, user_prompt: str) -> str:
    ask = (user_prompt or "Bu dosyayi analiz et, ozetle ve dikkat edilmesi gereken noktaları soyle.").strip()
    return (
        "Sen JARVIS web panelinden yuklenen dosyalari analiz eden dikkatli bir asistansin.\n"
        f"Dosya adi: {path.name}\n"
        f"Dosya turu: {_mime(path)}\n"
        "Yaniti Turkce ver. Uydurma yapma; dosyada gormedigin bilgiyi varmis gibi yazma.\n"
        "Gerekirse once kisa ozet, sonra bulgular ve oneriler ver.\n\n"
        f"Kullanici istegi: {ask}"
    )


def _text_analysis(client: genai.Client, path: Path, prompt: str) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")[:TEXT_LIMIT]
    content = f"{_prompt(path, prompt)}\n\nDOSYA ICERIGI:\n{text}"
    response = client.models.generate_content(
        model="models/gemini-2.0-flash",
        contents=[types.Part.from_text(text=content)],
        config=types.GenerateContentConfig(temperature=0.2),
    )
    return _response_text(response) or "Dosya okundu fakat model bos yanit verdi."


def _binary_analysis(client: genai.Client, path: Path, prompt: str) -> str:
    data = path.read_bytes()
    if len(data) > INLINE_LIMIT:
        return f"Dosya cok buyuk ({len(data) / (1024 * 1024):.1f} MB). 18 MB altindaki gorsel/PDF dosyalarini analiz edebilirim."
    part = types.Part.from_bytes(data=data, mime_type=_mime(path))
    last_error: Exception | None = None
    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=[types.Part.from_text(text=_prompt(path, prompt)), part],
                config=types.GenerateContentConfig(temperature=0.2),
            )
            return _response_text(response) or "Dosya yollandı fakat model bos yanit verdi."
        except Exception as exc:
            last_error = exc
            if _transient(exc):
                time.sleep(1.0)
                continue
            break
    return f"Dosya analizi basarisiz oldu: {last_error}"


def uploaded_file_analyzer(file_path: str, prompt: str = "") -> str:
    path = Path(file_path).expanduser()
    if not path.exists() or not path.is_file():
        return f"Dosya bulunamadi: {file_path}"

    api_key = str(get_app_config_value("gemini_api_key", "") or "").strip()
    if not api_key:
        return "Gemini API anahtari eksik oldugu icin dosya analizi yapilamadi."

    client = genai.Client(api_key=api_key)
    if path.suffix.lower() in TEXT_EXTS:
        return _text_analysis(client, path, prompt)
    return _binary_analysis(client, path, prompt)


def run(file_path: str, prompt: str = "") -> str:
    return uploaded_file_analyzer(file_path, prompt)
