from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_ROOT = BASE_DIR / "backups"
ALLOWED_ROOTS = [BASE_DIR, Path.home() / "Desktop", Path.home() / "Documents"]


def _safe_source(path: Path) -> bool:
    try:
        resolved = path.resolve()
        return any(resolved == root.resolve() or root.resolve() in resolved.parents for root in ALLOWED_ROOTS)
    except Exception:
        return False


def backup_manager(action: str = "plan", source: str = "", destination: str = "", confirm: bool = False) -> str:
    action = (action or "plan").strip().lower()
    src = Path(source).expanduser() if source else BASE_DIR
    if not src.is_absolute():
        src = (BASE_DIR / src).resolve()

    if not src.exists():
        return f"Yedeklenecek kaynak bulunamadi: {src}"
    if not _safe_source(src):
        return "Guvenlik: sadece proje, Masaustu veya Belgeler altindaki kaynaklar yedeklenebilir."

    dest_root = Path(destination).expanduser() if destination else BACKUP_ROOT
    if not dest_root.is_absolute():
        dest_root = (BASE_DIR / dest_root).resolve()
    if not (dest_root == BACKUP_ROOT or BACKUP_ROOT in dest_root.parents):
        return "Guvenlik: yedek hedefi proje icindeki backups klasoru altinda olmali."

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = dest_root / f"{src.name}_{stamp}"

    if action in {"plan", "preview"}:
        if src.is_file():
            size = src.stat().st_size / (1024 * 1024)
            return f"Yedek plani: {src} -> {target}{src.suffix} ({size:.2f} MB). Calistirmak icin confirm=true."
        count = sum(1 for p in src.rglob("*") if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts)
        return f"Yedek plani: {src} -> {target} ({count} dosya). Calistirmak icin confirm=true."

    if action == "backup":
        if not confirm:
            return "Yedek almak icin confirm=true gerekli. Once plan ile hedefi kontrol et."
        dest_root.mkdir(parents=True, exist_ok=True)
        if src.is_file():
            final = target.with_suffix(src.suffix)
            shutil.copy2(src, final)
        else:
            ignore = shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "backups")
            shutil.copytree(src, target, ignore=ignore)
            final = target
        return f"Yedek tamamlandi: {final}"

    return f"Bilinmeyen yedek eylemi: {action}"
