from __future__ import annotations

import re
from urllib.parse import urlparse

import requests


SUSPICIOUS_WORDS = ("login", "verify", "free", "gift", "bonus", "update-account", "secure-check")


def url_reputation_check(url: str) -> str:
    target = (url or "").strip()
    if not target:
        return "URL risk kontrolu icin URL gerekli."
    if not target.startswith(("http://", "https://")):
        target = "https://" + target
    parsed = urlparse(target)
    host = parsed.netloc.lower()
    score = 0
    notes = []
    if parsed.scheme != "https":
        score += 2
        notes.append("HTTPS kullanmiyor.")
    if re.match(r"^\d+\.\d+\.\d+\.\d+", host):
        score += 2
        notes.append("Domain yerine IP adresi kullaniliyor.")
    if host.count("-") >= 3:
        score += 1
        notes.append("Domain cok fazla tire iceriyor.")
    if any(word in target.lower() for word in SUSPICIOUS_WORDS):
        score += 1
        notes.append("Phishing kampanyalarinda sik gorulen kelimeler var.")
    try:
        response = requests.get(target, timeout=6, allow_redirects=True, headers={"User-Agent": "JARVIS"})
        notes.append(f"HTTP durum: {response.status_code}")
        if len(response.history) > 2:
            score += 1
            notes.append("Coklu yonlendirme var.")
        final_host = urlparse(response.url).netloc.lower()
        if final_host and final_host != host:
            notes.append(f"Son hedef: {final_host}")
    except Exception as exc:
        score += 1
        notes.append(f"Erisim hatasi: {exc}")
    level = "dusuk" if score <= 1 else "orta" if score <= 3 else "yuksek"
    return "\n".join([
        "URL RISK KONTROLU",
        f"Hedef: {target}",
        f"Risk: {level} ({score})",
        "Bulgular: " + ("; ".join(notes) if notes else "Belirgin risk sinyali yok."),
    ])
