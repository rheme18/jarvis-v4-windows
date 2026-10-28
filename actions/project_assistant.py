from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_NAMES = {".env", "credentials.json", "token.json", "jarvis_google_token.json", "api_keys.json"}
IMPORTANT_FILES = ["README.md", "requirements.txt", ".gitignore"]


def _resolve_project(path: str = "") -> Path:
    candidate = Path(path).expanduser() if path else BASE_DIR
    if not candidate.is_absolute():
        candidate = BASE_DIR / candidate
    return candidate.resolve()


def project_assistant(action: str = "report", path: str = "") -> str:
    action = (action or "report").strip().lower()
    project = _resolve_project(path)
    if not project.exists() or not project.is_dir():
        return f"Proje klasoru bulunamadi: {project}"

    py_files = list(project.rglob("*.py"))
    total_size = 0
    big_files = []
    secret_hits = []
    for root, dirs, files in os.walk(project):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", "node_modules", ".venv", "venv"}]
        for filename in files:
            file_path = Path(root) / filename
            try:
                size = file_path.stat().st_size
            except OSError:
                continue
            total_size += size
            if size > 5 * 1024 * 1024:
                big_files.append(file_path)
            if filename in SECRET_NAMES:
                secret_hits.append(file_path)

    if action in {"report", "scan"}:
        missing = [name for name in IMPORTANT_FILES if not (project / name).exists()]
        lines = [
            f"Proje raporu: {project}",
            f"Python dosyasi: {len(py_files)}",
            f"Yaklasik boyut: {total_size / (1024 * 1024):.1f} MB",
        ]
        if missing:
            lines.append("Eksik temel dosyalar: " + ", ".join(missing))
        if big_files:
            lines.append("Buyuk dosyalar:")
            lines.extend(f"- {p}" for p in big_files[:10])
        if secret_hits:
            lines.append("Dikkat: gizli/kimlik dosyasi olabilecek dosyalar bulundu:")
            lines.extend(f"- {p.name}" for p in secret_hits[:10])
        return "\n".join(lines)

    if action == "tree":
        lines = [f"Proje agaci: {project}"]
        for child in sorted(project.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            if child.name in {".git", "__pycache__"}:
                continue
            kind = "dir" if child.is_dir() else "file"
            lines.append(f"- [{kind}] {child.name}")
        return "\n".join(lines)

    return f"Bilinmeyen proje asistani eylemi: {action}"
