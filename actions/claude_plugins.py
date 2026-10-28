from __future__ import annotations

from core.claude_plugin_adapter import (
    export_mcp_config,
    get_plugin,
    list_plugins,
    read_component,
    search_plugins,
)


TOOL_DECLARATION = {
    "name": "claude_plugin_adapter",
    "description": (
        "Jarvis'e entegre edilen Claude official/external plugin paketlerini listeler, arar, "
        "command/skill/agent/MCP dosyalarini okur ve external MCP config disari aktarir."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "list | search | detail | read | export_mcp"},
            "query": {"type": "STRING", "description": "Arama metni."},
            "name": {"type": "STRING", "description": "Plugin adi."},
            "source": {"type": "STRING", "description": "all | official | external"},
            "kind": {"type": "STRING", "description": "command | skill | agent | hook | mcp | readme"},
            "component": {"type": "STRING", "description": "Okunacak component adi."},
            "limit": {"type": "NUMBER", "description": "Maksimum sonuc."},
            "max_chars": {"type": "NUMBER", "description": "Okuma limiti."},
        },
        "required": ["action"],
    },
}

PLUGIN_META = {"category": "plugins", "danger": "safe", "ui_visible": True}


def run(
    action: str = "list",
    query: str = "",
    name: str = "",
    source: str = "all",
    kind: str = "",
    component: str = "",
    limit: int = 12,
    max_chars: int = 18_000,
) -> str:
    action = (action or "list").strip().lower()
    limit = max(1, min(int(limit or 12), 80))
    if action == "list":
        rows = list_plugins(source)
        if not rows:
            return "Claude plugin bulunamadi."
        lines = [f"Claude pluginleri ({len(rows)}):"]
        for plugin in rows[:limit]:
            kinds = ", ".join(sorted({item.kind for item in plugin.components})) or "metadata"
            lines.append(f"- {plugin.source}/{plugin.name}: {plugin.description[:220]} [{kinds}]")
        return "\n".join(lines)
    if action == "search":
        rows = search_plugins(query, source, limit)
        if not rows:
            return f"'{query}' icin Claude plugin bulunamadi."
        return "\n".join(f"- {p.source}/{p.name}: {p.description[:260]}" for p in rows)
    if action == "detail":
        plugin = get_plugin(name or query, source)
        if not plugin:
            return f"Plugin bulunamadi: {name or query}"
        data = plugin.as_dict()
        lines = [
            f"Plugin: {data['source']}/{data['name']}",
            f"Root: {data['root']}",
            f"Description: {data['description']}",
            "Components:",
        ]
        lines.extend(f"- {c['kind']}: {c['name']} -> {c['path']}" for c in data["components"])
        return "\n".join(lines)
    if action == "read":
        data = read_component(name or query, component, kind, max_chars)
        if "error" in data:
            return data["error"]
        return (
            f"Plugin: {data['plugin']}\n"
            f"Component: {data['kind']}/{data['component']}\n"
            f"Path: {data['path']}\n\n"
            f"{data['content']}"
        )
    if action == "export_mcp":
        data = export_mcp_config()
        return f"MCP config yazildi: {data['path']}\nSunucu sayisi: {data['count']}\n" + "\n".join(f"- {s}" for s in data["servers"])
    return "Gecersiz action. list, search, detail, read veya export_mcp kullan."
