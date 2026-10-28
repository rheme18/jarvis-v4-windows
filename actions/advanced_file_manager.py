from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
HOME = Path.home()
DEFAULT_ROOTS = [
    BASE_DIR,
    HOME,
    HOME / "Desktop",
    HOME / "Documents",
    HOME / "Downloads",
]
SKIP_DIRS = {".git", "__pycache__", "venv", ".venv", "node_modules", ".mypy_cache", ".pytest_cache"}
TEXT_EXTS = {".txt", ".md", ".py", ".json", ".csv", ".log", ".yaml", ".yml", ".html", ".css", ".js", ".ts", ".tsx", ".xml"}


TOOL_DECLARATION = {
    "name": "advanced_file_manager",
    "description": (
        "Windows dosya sisteminde gelismis ve guvenli dosya yonetimi yapar: listeleme, agac, okuma, yazma, "
        "arama, kopyalama, tasima, silme, hash ve metadata. Riskli islemler icin confirm=true gerekir."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "roots | list | tree | read | write | append | mkdir | search | copy | move | delete | stat | hash"},
            "path": {"type": "STRING", "description": "Hedef dosya veya klasor yolu."},
            "destination": {"type": "STRING", "description": "copy/move icin hedef yol."},
            "content": {"type": "STRING", "description": "write/append icin icerik."},
            "query": {"type": "STRING", "description": "search icin dosya adi veya icerik aramasi."},
            "glob": {"type": "STRING", "description": "Dosya filtre paterni. Ornek: *.py"},
            "depth": {"type": "NUMBER", "description": "tree derinligi."},
            "limit": {"type": "NUMBER", "description": "Maksimum sonuc."},
            "max_chars": {"type": "NUMBER", "description": "read/search icerik limiti."},
            "content_search": {"type": "BOOLEAN", "description": "search icinde dosya iceriginde de ara."},
            "confirm": {"type": "BOOLEAN", "description": "delete/move/overwrite gibi riskli islemler icin acik onay."},
        },
        "required": ["action"],
    },
}

PLUGIN_META = {"category": "files", "danger": "confirm_required", "ui_visible": True}


def _allowed_roots() -> list[Path]:
    roots = []
    try:
        from core.settings_store import load_settings

        configured = load_settings().get("file_management", {}).get("allowed_roots", [])
        for item in configured:
            if item:
                roots.append(Path(str(item)).expanduser())
    except Exception:
        pass
    roots.extend(DEFAULT_ROOTS)
    unique: list[Path] = []
    for root in roots:
        try:
            resolved = root.resolve()
        except Exception:
            continue
        if resolved not in unique:
            unique.append(resolved)
    return unique


def _resolve(raw_path: str = "") -> Path:
    candidate = Path(os.path.expandvars(raw_path or ".")).expanduser()
    if not candidate.is_absolute():
        candidate = BASE_DIR / candidate
    resolved = candidate.resolve()
    for root in _allowed_roots():
        if resolved == root:
            return resolved
        try:
            resolved.relative_to(root)
            return resolved
        except ValueError:
            continue
    raise PermissionError(f"Yol izinli koklerin disinda: {resolved}")


def _is_text(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTS


def _format_path(path: Path) -> str:
    try:
        return str(path.relative_to(BASE_DIR))
    except Exception:
        return str(path)


def _iter_files(root: Path, glob_pattern: str = "*", limit: int = 2000):
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
        for filename in filenames:
            if glob_pattern and not fnmatch.fnmatch(filename.lower(), glob_pattern.lower()):
                continue
            path = Path(dirpath) / filename
            yield path
            count += 1
            if count >= limit:
                return


def _tree(root: Path, depth: int, limit: int) -> str:
    rows: list[str] = [f"{_format_path(root)}/"]
    base_depth = len(root.parts)
    for current, dirnames, filenames in os.walk(root):
        current_path = Path(current)
        level = len(current_path.parts) - base_depth
        if level >= depth:
            dirnames[:] = []
        dirnames[:] = [name for name in sorted(dirnames) if name not in SKIP_DIRS]
        entries = [*(name + "/" for name in dirnames), *sorted(filenames)]
        for entry in entries:
            rows.append("  " * (level + 1) + entry)
            if len(rows) >= limit:
                rows.append("... limit doldu")
                return "\n".join(rows)
    return "\n".join(rows)


def run(
    action: str = "list",
    path: str = "",
    destination: str = "",
    content: str = "",
    query: str = "",
    glob: str = "*",
    depth: int = 2,
    limit: int = 50,
    max_chars: int = 20_000,
    content_search: bool = False,
    confirm: bool = False,
) -> str:
    action = (action or "list").strip().lower()
    limit = max(1, min(int(limit or 50), 500))
    max_chars = max(100, min(int(max_chars or 20_000), 200_000))

    try:
        if action == "roots":
            return "Izinli kokler:\n" + "\n".join(f"- {root}" for root in _allowed_roots())

        target = _resolve(path)

        if action == "list":
            if not target.exists() or not target.is_dir():
                return f"Klasor bulunamadi: {target}"
            rows = []
            for item in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))[:limit]:
                suffix = "/" if item.is_dir() else ""
                size = "" if item.is_dir() else f" {item.stat().st_size} byte"
                rows.append(f"- {item.name}{suffix}{size}")
            return "\n".join(rows) if rows else "Klasor bos."

        if action == "tree":
            if not target.exists() or not target.is_dir():
                return f"Klasor bulunamadi: {target}"
            return _tree(target, max(1, min(int(depth or 2), 6)), limit)

        if action == "read":
            if not target.exists() or not target.is_file():
                return f"Dosya bulunamadi: {target}"
            if not _is_text(target):
                return f"Bu dosya metin olarak okunmadi. Hash/stat kullan: {target.suffix}"
            return target.read_text(encoding="utf-8", errors="replace")[:max_chars]

        if action == "write":
            if target.exists() and not confirm:
                return "Dosya zaten var. Uzerine yazmak icin confirm=true gerekli."
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content or "", encoding="utf-8")
            return f"Yazildi: {_format_path(target)}"

        if action == "append":
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("a", encoding="utf-8") as handle:
                handle.write(content or "")
            return f"Eklendi: {_format_path(target)}"

        if action == "mkdir":
            target.mkdir(parents=True, exist_ok=True)
            return f"Klasor hazir: {_format_path(target)}"

        if action == "search":
            root = target if target.is_dir() else target.parent
            needle = (query or "").lower()
            rows: list[str] = []
            for item in _iter_files(root, glob or "*", limit=5000):
                matched = needle in item.name.lower() if needle else True
                if content_search and needle and _is_text(item):
                    try:
                        sample = item.read_text(encoding="utf-8", errors="replace")[:max_chars].lower()
                        matched = matched or needle in sample
                    except Exception:
                        pass
                if matched:
                    rows.append(f"- {_format_path(item)}")
                    if len(rows) >= limit:
                        break
            return "\n".join(rows) if rows else "Eslesen dosya bulunamadi."

        if action == "copy":
            dest = _resolve(destination)
            if not target.exists():
                return f"Kaynak bulunamadi: {target}"
            if dest.exists() and not confirm:
                return "Hedef zaten var. Uzerine yazmak icin confirm=true gerekli."
            dest.parent.mkdir(parents=True, exist_ok=True)
            if target.is_dir():
                shutil.copytree(target, dest, dirs_exist_ok=confirm)
            else:
                shutil.copy2(target, dest)
            return f"Kopyalandi: {_format_path(target)} -> {_format_path(dest)}"

        if action == "move":
            if not confirm:
                return "Tasima islemi icin confirm=true gerekli."
            dest = _resolve(destination)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(target), str(dest))
            return f"Tasindi: {_format_path(target)} -> {_format_path(dest)}"

        if action == "delete":
            if not confirm:
                return "Silme islemi icin confirm=true gerekli."
            if not target.exists():
                return f"Silinecek hedef bulunamadi: {target}"
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            return f"Silindi: {_format_path(target)}"

        if action == "stat":
            if not target.exists():
                return f"Hedef bulunamadi: {target}"
            stat = target.stat()
            return json.dumps(
                {
                    "path": str(target),
                    "is_dir": target.is_dir(),
                    "is_file": target.is_file(),
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "created": stat.st_ctime,
                },
                ensure_ascii=False,
                indent=2,
            )

        if action == "hash":
            if not target.exists() or not target.is_file():
                return f"Dosya bulunamadi: {target}"
            digest = hashlib.sha256()
            with target.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            return f"sha256 {_format_path(target)} = {digest.hexdigest()}"

        return f"Gecersiz action: {action}"
    except Exception as exc:
        return f"advanced_file_manager hatasi: {type(exc).__name__}: {exc}"
