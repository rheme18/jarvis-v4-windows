from __future__ import annotations

import ast
import os
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "backups"}


def _iter_py_files(root: Path):
    for current, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
        for filename in files:
            if filename.endswith(".py"):
                yield Path(current) / filename


def _functions(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return []
    names = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.append(node.name)
    return names


def _tool_names() -> list[str]:
    main_path = BASE_DIR / "main.py"
    try:
        text = main_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    return sorted(set(re.findall(r'"name"\s*:\s*"([^"]+)"', text)))


def code_map(action: str = "overview", path: str = "", query: str = "", limit: int = 30) -> str:
    action = (action or "overview").strip().lower()
    root = Path(path).expanduser() if path else BASE_DIR
    if not root.is_absolute():
        root = BASE_DIR / root
    root = root.resolve()
    query = (query or "").strip().lower()
    limit = max(5, min(int(limit or 30), 80))
    if not root.exists():
        return f"Kod haritasi icin klasor bulunamadi: {root}"

    py_files = list(_iter_py_files(root))

    if action in {"overview", "summary"}:
        action_files = sorted((BASE_DIR / "actions").glob("*.py"))
        service_files = sorted((BASE_DIR / "services").glob("*.py"))
        tools = _tool_names()
        lines = [
            f"Kod haritasi: {root}",
            f"Python dosyasi: {len(py_files)}",
            f"Action modulu: {len(action_files)} | Service modulu: {len(service_files)} | Tool declaration: {len(tools)}",
            "Kayitli tool isimleri:",
        ]
        lines.extend(f"- {name}" for name in tools[:limit])
        return "\n".join(lines)

    if action == "actions":
        lines = ["Action modulleri:"]
        for path_obj in sorted((BASE_DIR / "actions").glob("*.py"))[:limit]:
            funcs = ", ".join(_functions(path_obj)[:8]) or "fonksiyon yok"
            lines.append(f"- {path_obj.name}: {funcs}")
        return "\n".join(lines)

    if action == "search":
        if not query:
            return "Kod haritasinda aramak icin query gerekli."
        matches = []
        for path_obj in py_files:
            funcs = [name for name in _functions(path_obj) if query in name.lower() or query in path_obj.name.lower()]
            if funcs or query in path_obj.name.lower():
                matches.append((path_obj, funcs))
        if not matches:
            return f"'{query}' icin kod haritasi eslesmesi yok."
        lines = [f"'{query}' kod haritasi eslesmeleri:"]
        for path_obj, funcs in matches[:limit]:
            suffix = f" -> {', '.join(funcs[:8])}" if funcs else ""
            lines.append(f"- {path_obj.relative_to(root) if root in path_obj.parents else path_obj}{suffix}")
        return "\n".join(lines)

    return f"Bilinmeyen kod haritasi eylemi: {action}"
