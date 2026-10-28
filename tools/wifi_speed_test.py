from __future__ import annotations

import time

import requests


def wifi_speed_test(test_url: str = "https://speed.cloudflare.com/__down?bytes=1000000") -> str:
    url = (test_url or "https://speed.cloudflare.com/__down?bytes=1000000").strip()
    started = time.perf_counter()
    try:
        response = requests.get(url, timeout=12, stream=True, headers={"User-Agent": "JARVIS"})
        response.raise_for_status()
        total = 0
        for chunk in response.iter_content(chunk_size=64 * 1024):
            total += len(chunk)
        elapsed = max(time.perf_counter() - started, 0.001)
        mbps = (total * 8) / elapsed / 1_000_000
        return "\n".join([
            "BAGLANTI HIZ TESTI",
            f"Indirilen veri: {total / 1024 / 1024:.2f} MB",
            f"Sure: {elapsed:.2f} sn",
            f"Tahmini hiz: {mbps:.2f} Mbps",
        ])
    except Exception as exc:
        return f"Hiz testi basarisiz: {exc}"
