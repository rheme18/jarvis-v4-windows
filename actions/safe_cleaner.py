from __future__ import annotations

import shutil
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
REVIEW_DIR = BASE_DIR / "backups" / "safe_cleaner_review"
PATTERNS = {
    "__pycache__": "Python cache klasoru",
    "*.pyc": "Python bytecode",
    "*.pyo": "Python optimized bytecode",
    "*.log": "Log dosyasi",
    ".pytest_cache": "Pytest cache",
}


def _candidates(scope: str = "project") -> list[Path]:
    root = BASE_DIR if scope != "actions" else BASE_DIR / "actions"
    hits: list[Path] = []
    for pattern in PATTERNS:
        hits.extend(root.rglob(pattern))
    return sorted(set(hits), key=lambda p: str(p).lower())


def _safe(path: Path) -> bool:
    try:
        resolved = path.resolve()
        return resolved == BASE_DIR or BASE_DIR in resolved.parents
    except Exception:
        return False


def safe_cleaner(action: str = "scan", scope: str = "project", confirm: bool = False, mode: str = "review") -> str:
    action = (action or "scan").strip().lower()
    scope = (scope or "project").strip().lower()
    mode = (mode or "review").strip().lower()
    candidates = [path for path in _candidates(scope) if _safe(path)]

    if action in {"scan", "report"}:
        if not candidates:
            return "Guvenli temizlik taramasi: temizlenecek cache/log adayi yok."
        lines = [f"Guvenli temizlik taramasi: {len(candidates)} aday bulundu."]
        for path in candidates[:40]:
            kind = "klasor" if path.is_dir() else "dosya"
            lines.append(f"- [{kind}] {path.relative_to(BASE_DIR)}")
        lines.append("Temizlemek icin clean eylemi ve confirm=true gerekli.")
        return "\n".join(lines)

    if action == "clean":
        if not confirm:
            return "Temizlik icin confirm=true gerekli. Once scan ile adaylari kontrol et."
        if not candidates:
            return "Temizlenecek aday bulunamadi."
        moved = 0
        deleted = 0
        REVIEW_DIR.mkdir(parents=True, exist_ok=True)
        for path in candidates:
            try:
                if mode == "delete":
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                    deleted += 1
                else:
                    target = REVIEW_DIR / path.name
                    if target.exists():
                        target = REVIEW_DIR / f"{path.stem}_{moved}{path.suffix}"
                    shutil.move(str(path), str(target))
                    moved += 1
            except Exception:
                continue
        if mode == "delete":
            return f"Guvenli temizlik tamamlandi: {deleted} aday silindi."
        return f"Guvenli temizlik tamamlandi: {moved} aday inceleme klasorune tasindi: {REVIEW_DIR}"

    return f"Bilinmeyen temizlik eylemi: {action}"
