from __future__ import annotations

from typing import Any

import requests

from app_config import get_app_config_value


TOOL_DECLARATION = {
    "name": "claude_code_assistant",
    "description": (
        "Opsiyonel Anthropic Claude API koprusu. Kod yazma, code review, refactor onerisi, "
        "hata aciklama ve feature planlama icin Claude modelinden yardim alir."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "write_code | review_code | explain_code | plan_feature | refactor_advice | general",
            },
            "prompt": {"type": "STRING", "description": "Claude'a gonderilecek gorev."},
            "code": {"type": "STRING", "description": "Opsiyonel kod parcasi."},
            "language": {"type": "STRING", "description": "Opsiyonel programlama dili."},
            "max_tokens": {"type": "NUMBER", "description": "Maksimum cikti token sayisi. Varsayilan 1800."},
        },
        "required": ["action", "prompt"],
    },
}

PLUGIN_META = {"category": "ai_provider", "danger": "network", "ui_visible": True}


SYSTEM_BY_ACTION = {
    "write_code": "You are Claude acting as a senior software engineer. Produce correct, maintainable code and concise implementation notes.",
    "review_code": "You are Claude acting as a rigorous code reviewer. Prioritize bugs, security, regressions, and missing tests.",
    "explain_code": "You are Claude acting as a patient code explainer. Explain behavior, edge cases, and risks clearly.",
    "plan_feature": "You are Claude acting as a product-minded architect. Produce a practical implementation plan with risks and tests.",
    "refactor_advice": "You are Claude acting as a refactoring specialist. Preserve behavior and reduce complexity.",
    "general": "You are Claude helping Jarvis with coding and software engineering tasks.",
}


def _config() -> tuple[str, str]:
    key = str(get_app_config_value("claude_api_key", "") or get_app_config_value("ANTHROPIC_API_KEY", "") or "").strip()
    model = str(get_app_config_value("claude_model", "claude-sonnet-4-5-20250929") or "claude-sonnet-4-5-20250929").strip()
    return key, model


def _limit(value: Any) -> int:
    try:
        return max(256, min(8000, int(value or 1800)))
    except Exception:
        return 1800


def run(
    action: str = "general",
    prompt: str = "",
    code: str = "",
    language: str = "",
    max_tokens: int = 1800,
) -> str:
    action = (action or "general").strip().lower()
    prompt = str(prompt or "").strip()
    code = str(code or "")
    language = str(language or "").strip()
    if not prompt:
        return "Claude gorevi icin prompt gerekli."

    api_key, model = _config()
    if not api_key:
        return "Claude API bagli degil. config/.env icine CLAUDE_API_KEY ekle. Model icin opsiyonel CLAUDE_MODEL kullan."

    system = SYSTEM_BY_ACTION.get(action, SYSTEM_BY_ACTION["general"])
    user_parts = [f"Task type: {action}", prompt]
    if language:
        user_parts.append(f"Language: {language}")
    if code:
        user_parts.append("Code:\n```" + (language or "") + "\n" + code[:80_000] + "\n```")

    payload = {
        "model": model,
        "max_tokens": _limit(max_tokens),
        "system": system,
        "messages": [{"role": "user", "content": "\n\n".join(user_parts)}],
    }

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
            timeout=60,
        )
    except requests.RequestException as exc:
        return f"Claude API ag hatasi: {type(exc).__name__}: {exc}"

    if response.status_code >= 400:
        detail = ""
        try:
            data = response.json()
            if isinstance(data, dict):
                detail = str((data.get("error") or {}).get("message") or data.get("message") or "")
        except Exception:
            detail = response.text[:300]
        return f"Claude API hatasi ({response.status_code}): {detail or 'detay yok'}"

    try:
        data = response.json()
        blocks = data.get("content", [])
        texts = [block.get("text", "") for block in blocks if isinstance(block, dict) and block.get("type") == "text"]
        answer = "\n".join(texts).strip()
        return answer or "Claude API bos yanit verdi."
    except Exception as exc:
        return f"Claude API yaniti okunamadi: {type(exc).__name__}: {exc}"
