from __future__ import annotations

import shutil
from datetime import datetime, timedelta
from pathlib import Path


HOME = Path.home()
SCAN_DIRS = [HOME / "Downloads", HOME / "Desktop"]
REVIEW_DIR = HOME / "Desktop" / "Jarvis_Review_Cleanup"


def _iter_files() -> list[Path]:
    files: list[Path] = []
    for folder in SCAN_DIRS:
        if folder.exists():
            files.extend(path for path in folder.rglob("*") if path.is_file())
    return files


def downloads_cleaner(action: str = "report", days: int = 30, min_size_mb: int = 100, confirm: bool = False) -> str:
    action = (action or "report").strip().lower()
    cutoff = datetime.now() - timedelta(days=max(1, int(days or 30)))
    min_bytes = max(1, int(min_size_mb or 100)) * 1024 * 1024
    files = _iter_files()

    old_files = [p for p in files if datetime.fromtimestamp(p.stat().st_mtime) < cutoff]
    large_files = [p for p in files if p.stat().st_size >= min_bytes]
    candidates = sorted(set(old_files + large_files), key=lambda p: p.stat().st_size, reverse=True)

    if action in {"report", "scan"}:
        if not candidates:
            return "Indirilenler ve Masaustu temiz gorunuyor; esiklere takilan dosya yok."
        lines = [
            f"Temizlik raporu: {len(candidates)} aday dosya bulundu.",
            f"Esikler: {days} gunden eski veya {min_size_mb} MB ustu.",
        ]
        for path in candidates[:20]:
            size_mb = path.stat().st_size / (1024 * 1024)
            lines.append(f"- {path} ({size_mb:.1f} MB)")
        return "\n".join(lines)

    if action in {"stage", "move"}:
        if not confirm:
            return "Dosyalari inceleme klasorune tasimak icin confirm=true gerekli. Once report ile listeyi kontrol et."
        REVIEW_DIR.mkdir(parents=True, exist_ok=True)
        moved = 0
        for path in candidates[:50]:
            try:
                target = REVIEW_DIR / path.name
                if target.exists():
                    target = REVIEW_DIR / f"{path.stem}_{int(datetime.now().timestamp())}{path.suffix}"
                shutil.move(str(path), str(target))
                moved += 1
            except Exception:
                continue
        return f"{moved} dosya silinmeden inceleme klasorune tasindi: {REVIEW_DIR}"

    return f"Bilinmeyen temizlik eylemi: {action}"
