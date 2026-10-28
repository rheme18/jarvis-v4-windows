from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "backups"}
SECRET_FILE_NAMES = {".env", "credentials.json", "token.json", "api_keys.json", "jarvis_google_token.json"}
SECRET_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"ghp_[0-9A-Za-z_]{20,}"),
    re.compile(r"xox[baprs]-[0-9A-Za-z-]{20,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"][^'\"]{12,}['\"]"),
]


def _resolve(path: str = "") -> Path:
    candidate = Path(path).expanduser() if path else BASE_DIR
    if not candidate.is_absolute():
        candidate = BASE_DIR / candidate
    return candidate.resolve()


def _git_status(project: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(project),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=8,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.returncode != 0:
            return ["Git durumu alinamadi."]
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        return lines[:30] or ["Git calisma agaci temiz gorunuyor."]
    except Exception as exc:
        return [f"Git durumu alinamadi: {exc}"]


def _iter_files(project: Path):
    for root, dirs, files in os.walk(project):
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
        for filename in files:
            yield Path(root) / filename


def project_snapshot(action: str = "summary", path: str = "", max_files: int = 12) -> str:
    action = (action or "summary").strip().lower()
    project = _resolve(path)
    max_files = max(3, min(int(max_files or 12), 40))
    if not project.exists() or not project.is_dir():
        return f"Proje klasoru bulunamadi: {project}"

    files = list(_iter_files(project))
    py_files = [p for p in files if p.suffix.lower() == ".py"]
    total_size = sum((p.stat().st_size for p in files if p.exists()), 0)
    newest = sorted(files, key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)[:max_files]
    big_files = sorted(files, key=lambda p: p.stat().st_size if p.exists() else 0, reverse=True)[:max_files]

    secret_hits = []
    for path_obj in files:
        if path_obj.name in SECRET_FILE_NAMES:
            secret_hits.append(f"{path_obj.relative_to(project)} (dosya adi)")
            continue
        if path_obj.suffix.lower() not in {".py", ".txt", ".json", ".env", ".bat", ".md"}:
            continue
        try:
            text = path_obj.read_text(encoding="utf-8", errors="ignore")[:25000]
        except Exception:
            continue
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            secret_hits.append(f"{path_obj.relative_to(project)} (icerik riski)")

    if action in {"summary", "report", "scan"}:
        lines = [
            f"Proje anlik goruntusu: {project}",
            f"Dosya: {len(files)} | Python: {len(py_files)} | Boyut: {total_size / (1024 * 1024):.1f} MB",
            f"Rapor zamani: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            "Git durumu:",
        ]
        lines.extend(f"- {line}" for line in _git_status(project)[:max_files])
        if secret_hits:
            lines.append("Dikkat: gizli bilgi riski olabilecek izler:")
            lines.extend(f"- {item}" for item in secret_hits[:max_files])
        else:
            lines.append("Gizli bilgi dosya/icerik riski: belirgin bulgu yok.")
        return "\n".join(lines)

    if action == "recent":
        lines = ["Son degisen dosyalar:"]
        for item in newest:
            stamp = datetime.fromtimestamp(item.stat().st_mtime).strftime("%d.%m %H:%M")
            lines.append(f"- {item.relative_to(project)} | {stamp}")
        return "\n".join(lines)

    if action == "big":
        lines = ["En buyuk dosyalar:"]
        for item in big_files:
            lines.append(f"- {item.relative_to(project)} | {item.stat().st_size / (1024 * 1024):.1f} MB")
        return "\n".join(lines)

    return f"Bilinmeyen proje goruntusu eylemi: {action}"
