from __future__ import annotations

import subprocess


DISTRACTION_PROCESSES = {
    "chrome.exe": "Chrome",
    "msedge.exe": "Edge",
    "firefox.exe": "Firefox",
    "discord.exe": "Discord",
    "spotify.exe": "Spotify",
    "steam.exe": "Steam",
    "epicgameslauncher.exe": "Epic Games",
    "telegram.exe": "Telegram",
    "whatsapp.exe": "WhatsApp",
}


def _running_distractions() -> list[tuple[str, str]]:
    try:
        import psutil
    except Exception:
        return []
    hits: list[tuple[str, str]] = []
    for proc in psutil.process_iter(["name"]):
        try:
            name = str(proc.info.get("name") or "").lower()
        except Exception:
            continue
        if name in DISTRACTION_PROCESSES:
            label = DISTRACTION_PROCESSES[name]
            if (name, label) not in hits:
                hits.append((name, label))
    return sorted(hits, key=lambda item: item[1].lower())


def focus_guard(action: str = "report", apps: str = "", confirm: bool = False) -> str:
    action = (action or "report").strip().lower()
    custom_apps = [item.strip().lower() for item in (apps or "").split(",") if item.strip()]
    running = _running_distractions()

    if action in {"report", "scan"}:
        if not running:
            return "Odak kontrolu: dikkat dagitici uygulama gorunmuyor."
        lines = ["Odak kontrolu: su uygulamalar acik gorunuyor:"]
        lines.extend(f"- {label} ({exe})" for exe, label in running)
        lines.append("Kapatmak icin close eylemi ve confirm=true gerekli.")
        return "\n".join(lines)

    if action in {"close", "block"}:
        targets = custom_apps or [exe for exe, _label in running]
        if not targets:
            return "Kapatilacak dikkat dagitici uygulama bulunamadi."
        if not confirm:
            return "Odak uygulamalarini kapatmak icin confirm=true gerekli. Once report ile listeyi kontrol et."
        closed = []
        for target in targets:
            exe = target if target.endswith(".exe") else f"{target}.exe"
            try:
                result = subprocess.run(
                    ["taskkill", "/F", "/IM", exe],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                if result.returncode == 0:
                    closed.append(exe)
            except Exception:
                continue
        if not closed:
            return "Odak uygulamalari kapatilamadi veya zaten kapali."
        return "Kapatilan odak dagiticilar: " + ", ".join(closed)

    return f"Bilinmeyen odak korumasi eylemi: {action}"
