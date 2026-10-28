from __future__ import annotations

import shutil
from pathlib import Path


def system_health_report(level: str = "summary") -> str:
    level = (level or "summary").strip().lower()
    lines = ["Sistem saglik raporu"]

    try:
        import psutil

        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = shutil.disk_usage("C:\\")
        lines.append(f"CPU: %{cpu:.1f}")
        lines.append(f"RAM: {mem.used / (1024**3):.1f}GB / {mem.total / (1024**3):.1f}GB (%{mem.percent:.0f})")
        lines.append(f"Disk C: {disk.used / (1024**3):.1f}GB kullanildi, {disk.free / (1024**3):.1f}GB bos")
        boot = psutil.boot_time()
        lines.append(f"Acik sure: {int((__import__('time').time() - boot) / 3600)} saat")
    except Exception as exc:
        lines.append(f"Temel metrikler alinamadi: {exc}")

    if level in {"full", "startup"}:
        startup = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        if startup.exists():
            items = [p.name for p in startup.iterdir()]
            lines.append("Baslangic klasoru: " + (", ".join(items[:10]) if items else "bos"))

    return "\n".join(lines)
