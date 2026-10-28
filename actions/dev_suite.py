from __future__ import annotations

import ast
import datetime as dt
import json
import os
import subprocess
from pathlib import Path

from core.settings_store import get_setting


BASE_DIR = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", ".mypy_cache", ".pytest_cache"}


def _decl(name: str, description: str, props: dict | None = None, required: list[str] | None = None) -> dict:
    return {
        "name": name,
        "description": description,
        "parameters": {"type": "OBJECT", "properties": props or {}, "required": required or []},
    }


TOOL_DECLARATIONS = [
    _decl("project_indexer", "Proje dosyalarini indeksler ve ozet envanter cikarir.", {"path": {"type": "STRING"}, "limit": {"type": "NUMBER"}}),
    _decl("code_symbol_search", "Kod sembol haritasi ve arama yapar.", {"query": {"type": "STRING"}, "path": {"type": "STRING"}, "limit": {"type": "NUMBER"}}),
    _decl("auto_test_runner", "Projede otomatik test/compile komutu calistirir.", {"command": {"type": "STRING"}, "timeout": {"type": "NUMBER"}}),
    _decl("stack_trace_explainer", "Python stack trace veya hata metnini aciklar.", {"trace": {"type": "STRING"}}, ["trace"]),
    _decl("git_diff_summary", "Git diff/status ozetini verir.", {"limit": {"type": "NUMBER"}}),
    _decl("pr_description_generator", "Git diff'e gore commit/PR aciklamasi uretir.", {"title": {"type": "STRING"}}),
    _decl("safe_refactor_workflow", "Dosyayi bozmadan refactor icin guvenli plan uretir.", {"file_path": {"type": "STRING"}, "goal": {"type": "STRING"}}, ["file_path"]),
    _decl("local_changelog_generator", "Yerel git degisikliklerinden changelog taslagi uretir.", {"since": {"type": "STRING"}}),
    _decl("release_notes_generator", "Versiyon notu taslagi uretir.", {"version": {"type": "STRING"}}),
    _decl("code_quality_score", "Python kod kalitesi icin basit puan ve bulgu raporu verir.", {"path": {"type": "STRING"}, "limit": {"type": "NUMBER"}}),
]

PLUGIN_META = {"category": "developer", "danger": "safe", "ui_visible": True}


def _root(path: str = "") -> Path:
    p = Path(path).expanduser() if path else BASE_DIR
    if not p.is_absolute():
        p = BASE_DIR / p
    return p.resolve()


def _iter_files(root: Path, suffixes=(".py", ".md", ".txt", ".json"), limit: int = 400):
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            p = Path(dirpath) / name
            if suffixes and p.suffix.lower() not in suffixes:
                continue
            yield p
            count += 1
            if count >= limit:
                return


def _run(cmd: list[str], timeout: int = 30) -> str:
    try:
        cp = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True, timeout=timeout, shell=False)
        out = (cp.stdout or "") + ("\n" + cp.stderr if cp.stderr else "")
        return f"exit={cp.returncode}\n{out.strip()[:6000]}"
    except Exception as exc:
        return f"Komut hatasi: {exc}"


def project_indexer(path: str = "", limit: int = 0) -> str:
    root = _root(path)
    limit = int(limit or get_setting("developer", "project_index_limit", 400) or 400)
    by_ext: dict[str, int] = {}
    total_size = 0
    files = []
    for p in _iter_files(root, suffixes=(), limit=limit):
        try:
            size = p.stat().st_size
        except Exception:
            size = 0
        total_size += size
        by_ext[p.suffix.lower() or "<none>"] = by_ext.get(p.suffix.lower() or "<none>", 0) + 1
        files.append(str(p.relative_to(root)))
    return "\n".join([
        f"Proje indeksi: {root}",
        f"Dosya sayisi: {len(files)}",
        f"Toplam boyut: {total_size/1024:.1f} KB",
        "Uzanti dagilimi: " + json.dumps(by_ext, ensure_ascii=False),
        "Ornek dosyalar:",
        *[f"- {item}" for item in files[:40]],
    ])


def code_symbol_search(query: str = "", path: str = "", limit: int = 50) -> str:
    root = _root(path)
    query_l = (query or "").lower()
    hits = []
    for p in _iter_files(root, suffixes=(".py",), limit=500):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = node.name
                if not query_l or query_l in name.lower() or query_l in str(p).lower():
                    hits.append(f"{p.relative_to(root)}:{node.lineno} - {type(node).__name__} {name}")
                    if len(hits) >= int(limit or 50):
                        return "\n".join(hits)
    return "\n".join(hits) if hits else "Sembol bulunamadi."


def auto_test_runner(command: str = "", timeout: int = 60) -> str:
    command = (command or get_setting("developer", "auto_test_command", "python -m py_compile main.py")).strip()
    if command.startswith("python -m py_compile"):
        return _run(command.split(), int(timeout or 60))
    if command in {"pytest", "python -m pytest"}:
        return _run(command.split(), int(timeout or 60))
    return "Guvenlik icin sadece 'python -m py_compile ...' veya 'pytest' komutlari desteklenir."


def stack_trace_explainer(trace: str) -> str:
    lines = [line.rstrip() for line in (trace or "").splitlines() if line.strip()]
    error = next((line for line in reversed(lines) if "Error" in line or "Exception" in line or "SyntaxError" in line), lines[-1] if lines else "")
    files = [line.strip() for line in lines if line.strip().startswith('File "')]
    tips = ["Hata ozeti: " + (error or "Belirgin hata satiri yok.")]
    if files:
        tips.append("Son dosya izi: " + files[-1])
    if "SyntaxError" in error:
        tips.append("Muhtemel neden: eksik parantez, tirnak, iki nokta veya hatali indentation.")
    if "ModuleNotFoundError" in error:
        tips.append("Muhtemel neden: eksik pip paketi veya yanlis Python ortami.")
    if "PermissionError" in error:
        tips.append("Muhtemel neden: dosya/klasor izinleri veya calisan uygulama kilidi.")
    return "\n".join(tips)


def git_diff_summary(limit: int = 0) -> str:
    limit = int(limit or get_setting("developer", "git_summary_limit", 80) or 80)
    status = _run(["git", "status", "--short"], 20)
    diff = _run(["git", "diff", "--stat"], 20)
    names = _run(["git", "diff", "--name-only"], 20)
    return f"GIT STATUS\n{status}\n\nDIFF STAT\n{diff}\n\nFILES\n" + "\n".join(names.splitlines()[: int(limit or 80)])


def pr_description_generator(title: str = "Jarvis update") -> str:
    stat = _run(["git", "diff", "--stat"], 20)
    names = _run(["git", "diff", "--name-only"], 20)
    return f"""# {title}

## Summary
- Updated Jarvis project modules.
- Changed files: {len([x for x in names.splitlines() if x.strip()])}

## Files
{names}

## Diff Stat
{stat}

## Tests
- Run local compile/test command before merge.
"""


def safe_refactor_workflow(file_path: str, goal: str = "Improve safely") -> str:
    p = _root(file_path)
    return "\n".join([
        f"Safe refactor workflow: {p}",
        "1. Dosyayi oku ve mevcut davranisi ozetle.",
        "2. Sadece hedefle ilgili en kucuk degisikligi planla.",
        "3. Public fonksiyon imzalarini koru.",
        "4. Degisikligi patch olarak uygula.",
        "5. py_compile/test calistir.",
        "6. Git diff ozetini kontrol et.",
        f"Hedef: {goal}",
    ])


def local_changelog_generator(since: str = "") -> str:
    cmd = ["git", "log", "--oneline", "--decorate", "-n", "20"] if not since else ["git", "log", "--oneline", f"{since}..HEAD"]
    log = _run(cmd, 20)
    stat = _run(["git", "diff", "--stat"], 20)
    return f"Yerel changelog taslagi\n\nCommits:\n{log}\n\nUncommitted:\n{stat}"


def release_notes_generator(version: str = "next") -> str:
    return f"""Release Notes - {version}

Highlights:
- Plugin, workflow, settings and automation improvements.

Changes:
{git_diff_summary(40)}

Upgrade Notes:
- Restart Jarvis after plugin/settings changes.
"""


def code_quality_score(path: str = "", limit: int = 0) -> str:
    root = _root(path)
    limit = int(limit or get_setting("developer", "quality_score_limit", 300) or 300)
    files = list(_iter_files(root, suffixes=(".py",), limit=limit))
    issues = []
    total_lines = 0
    for p in files:
        text = p.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()
        total_lines += len(lines)
        if len(lines) > 900:
            issues.append(f"{p.relative_to(root)}: dosya cok uzun ({len(lines)} satir)")
        for i, line in enumerate(lines, 1):
            if len(line) > 140:
                issues.append(f"{p.relative_to(root)}:{i}: uzun satir")
                break
        try:
            ast.parse(text)
        except SyntaxError as exc:
            issues.append(f"{p.relative_to(root)}:{exc.lineno}: syntax error")
    score = max(0, 100 - len(issues) * 4)
    return "\n".join([
        f"Kod kalite puani: {score}/100",
        f"Python dosyasi: {len(files)}",
        f"Toplam satir: {total_lines}",
        "Bulgular:",
        *(f"- {item}" for item in issues[:40]),
    ])
