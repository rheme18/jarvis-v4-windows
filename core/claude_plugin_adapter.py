from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = BASE_DIR / "integrations" / "claude_plugins"
OFFICIAL_ROOT = PLUGIN_ROOT / "official"
EXTERNAL_ROOT = PLUGIN_ROOT / "external"
MCP_EXPORT_PATH = BASE_DIR / "config" / "claude_mcp_servers.json"


@dataclass(frozen=True)
class PluginComponent:
    kind: str
    name: str
    path: Path

    def as_dict(self) -> dict[str, str]:
        return {"kind": self.kind, "name": self.name, "path": str(self.path)}


@dataclass
class ClaudePlugin:
    name: str
    source: str
    root: Path
    description: str = ""
    author: str = ""
    components: list[PluginComponent] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "source": self.source,
            "root": str(self.root),
            "description": self.description,
            "author": self.author,
            "components": [item.as_dict() for item in self.components],
        }


def _frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    raw = text[3:end].strip()
    body = text[end + 4 :].lstrip()
    data: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data, body


def _read_text(path: Path, max_chars: int = 20_000) -> str:
    return path.read_text(encoding="utf-8", errors="replace")[: max(1000, int(max_chars or 20_000))]


def _manifest(root: Path) -> dict[str, Any]:
    path = root / ".claude-plugin" / "plugin.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _readme_description(root: Path) -> str:
    readme = root / "README.md"
    if not readme.exists():
        return ""
    try:
        text = _read_text(readme, 6000)
    except Exception:
        return ""
    lines = [line.strip(" #") for line in text.splitlines() if line.strip()]
    for line in lines:
        if not line.lower().startswith(("install", "usage", "overview")):
            return line[:500]
    return lines[0][:500] if lines else ""


def _components(root: Path) -> list[PluginComponent]:
    components: list[PluginComponent] = []
    patterns = [
        ("command", "commands/*.md"),
        ("skill", "skills/*/SKILL.md"),
        ("agent", "agents/*.md"),
        ("hook", "hooks/hooks.json"),
        ("mcp", ".mcp.json"),
        ("readme", "README.md"),
    ]
    for kind, pattern in patterns:
        for path in sorted(root.glob(pattern), key=lambda item: str(item).lower()):
            name = path.parent.name if path.name == "SKILL.md" else path.stem
            components.append(PluginComponent(kind=kind, name=name, path=path))
    return components


def list_plugins(source: str = "all") -> list[ClaudePlugin]:
    roots: list[tuple[str, Path]] = []
    source = (source or "all").strip().lower()
    if source in {"all", "official"}:
        roots.append(("official", OFFICIAL_ROOT))
    if source in {"all", "external"}:
        roots.append(("external", EXTERNAL_ROOT))

    plugins: list[ClaudePlugin] = []
    for source_name, root in roots:
        if not root.exists():
            continue
        for child in sorted(root.iterdir(), key=lambda item: item.name.lower()):
            if not child.is_dir():
                continue
            manifest = _manifest(child)
            author = manifest.get("author", "")
            if isinstance(author, dict):
                author = str(author.get("name", ""))
            plugin = ClaudePlugin(
                name=str(manifest.get("name") or child.name),
                source=source_name,
                root=child,
                description=str(manifest.get("description") or _readme_description(child)),
                author=str(author or ""),
                components=_components(child),
            )
            plugins.append(plugin)
    return plugins


def _score(query: str, plugin: ClaudePlugin) -> int:
    query = re.sub(r"\s+", " ", (query or "").casefold()).strip()
    if not query:
        return 1
    haystack = " ".join(
        [
            plugin.name,
            plugin.source,
            plugin.description,
            " ".join(f"{c.kind}:{c.name}" for c in plugin.components),
        ]
    ).casefold()
    score = 0
    for token in query.split():
        if token == plugin.name.casefold():
            score += 90
        elif token in plugin.name.casefold():
            score += 45
        elif token in haystack:
            score += 12
    if query in haystack:
        score += 50
    return score


def search_plugins(query: str = "", source: str = "all", limit: int = 12) -> list[ClaudePlugin]:
    ranked = [(plugin, _score(query, plugin)) for plugin in list_plugins(source)]
    ranked = [item for item in ranked if item[1] > 0]
    ranked.sort(key=lambda item: (-item[1], item[0].source, item[0].name))
    return [plugin for plugin, _ in ranked[: max(1, int(limit or 12))]]


def get_plugin(name: str, source: str = "all") -> ClaudePlugin | None:
    needle = (name or "").casefold().strip()
    plugins = list_plugins(source)
    selected = next((plugin for plugin in plugins if plugin.name.casefold() == needle), None)
    if selected:
        return selected
    selected = next((plugin for plugin in plugins if needle and needle in plugin.name.casefold()), None)
    if selected:
        return selected
    hits = search_plugins(name, source, 1)
    return hits[0] if hits else None


def read_component(plugin_name: str, component: str = "", kind: str = "", max_chars: int = 18_000) -> dict[str, str]:
    plugin = get_plugin(plugin_name)
    if not plugin:
        return {"error": f"Plugin bulunamadi: {plugin_name}"}
    kind = (kind or "").strip().lower()
    needle = (component or "").casefold().strip()
    candidates = plugin.components
    if kind:
        candidates = [item for item in candidates if item.kind == kind]
    selected = None
    if needle:
        selected = next((item for item in candidates if item.name.casefold() == needle), None)
        if selected is None:
            selected = next((item for item in candidates if needle in item.name.casefold()), None)
    if selected is None and candidates:
        selected = candidates[0]
    if selected is None:
        return {"error": f"{plugin.name} icinde component bulunamadi."}
    try:
        text = _read_text(selected.path, max_chars)
    except Exception as exc:
        return {"error": f"Component okunamadi: {exc}"}
    meta, body = _frontmatter(text)
    return {
        "plugin": plugin.name,
        "kind": selected.kind,
        "component": selected.name,
        "path": str(selected.path),
        "frontmatter": json.dumps(meta, ensure_ascii=False),
        "content": body if meta else text,
    }


def export_mcp_config(target_path: Path | None = None) -> dict[str, Any]:
    target = target_path or MCP_EXPORT_PATH
    merged: dict[str, Any] = {}
    for plugin in list_plugins("external"):
        mcp_path = plugin.root / ".mcp.json"
        if not mcp_path.exists():
            continue
        try:
            data = json.loads(mcp_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        data = _replace_plugin_root(data, plugin.root)
        if "mcpServers" in data and isinstance(data["mcpServers"], dict):
            merged.update(data["mcpServers"])
        elif isinstance(data, dict):
            merged.update(data)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"mcpServers": merged}, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"path": str(target), "count": len(merged), "servers": sorted(merged)}


def _replace_plugin_root(value: Any, root: Path) -> Any:
    if isinstance(value, str):
        return value.replace("${CLAUDE_PLUGIN_ROOT}", str(root))
    if isinstance(value, list):
        return [_replace_plugin_root(item, root) for item in value]
    if isinstance(value, dict):
        return {key: _replace_plugin_root(item, root) for key, item in value.items()}
    return value


def format_plugin_context(query: str = "", limit: int = 8) -> str:
    rows = search_plugins(query, "all", limit)
    if not rows:
        return ""
    lines = [
        "[CLAUDE PLUGIN LIBRARY]",
        "Gorev uygun oldugunda claude_plugin_adapter ile plugin command/skill/agent/MCP detayini oku.",
    ]
    for plugin in rows:
        kinds = sorted({component.kind for component in plugin.components})
        lines.append(f"- {plugin.source}/{plugin.name}: {plugin.description[:260]} ({', '.join(kinds)})")
    return "\n".join(lines)
