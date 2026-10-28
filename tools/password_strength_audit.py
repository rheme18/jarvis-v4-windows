from __future__ import annotations

import re


COMMON = {"password", "123456", "qwerty", "admin", "jarvis", "emir", "turkiye", "istanbul"}


def password_strength_audit(password: str) -> str:
    value = password or ""
    score = 0
    notes = []
    if len(value) >= 12:
        score += 2
    elif len(value) >= 8:
        score += 1
    else:
        notes.append("En az 12 karakter daha guvenli olur.")
    checks = [
        (r"[a-z]", "kucuk harf"),
        (r"[A-Z]", "buyuk harf"),
        (r"\d", "rakam"),
        (r"[^A-Za-z0-9]", "sembol"),
    ]
    for pattern, label in checks:
        if re.search(pattern, value):
            score += 1
        else:
            notes.append(f"{label} eklenebilir.")
    lower = value.lower()
    if any(item in lower for item in COMMON):
        score -= 2
        notes.append("Yaygin kelime veya tahmin edilebilir ifade iceriyor.")
    if re.search(r"(.)\1{2,}", value):
        score -= 1
        notes.append("Tekrarlayan karakter var.")
    score = max(0, min(score, 6))
    level = "zayif" if score <= 2 else "orta" if score <= 4 else "guclu"
    return "\n".join([
        "PAROLA GUC DENETIMI",
        f"Seviye: {level} ({score}/6)",
        "Notlar: " + ("; ".join(notes) if notes else "Temel kontroller iyi gorunuyor."),
    ])
