from __future__ import annotations

from typing import Any


TOOL_DECLARATION = {
    "name": "jarvis_inventory",
    "description": (
        "Jarvis'in aktif skill, Claude plugin, MCP ve tool envanterini listeler; "
        "ozellikle Claude kod yazma/code review workflowlarini aciklar."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "summary | skills | plugins | coding | mcp | tools | detail",
            },
            "query": {"type": "STRING", "description": "Arama veya detay istenecek ad."},
            "source": {"type": "STRING", "description": "Plugin kaynagi: all | official | external"},
            "limit": {"type": "NUMBER", "description": "Maksimum sonuc sayisi."},
        },
        "required": ["action"],
    },
}

PLUGIN_META = {"category": "system", "danger": "safe", "ui_visible": True}


CODING_TERMS = (
    "code",
    "coding",
    "review",
    "feature",
    "frontend",
    "plugin",
    "mcp",
    "lsp",
    "modernization",
    "simplifier",
    "security",
    "typescript",
    "pyright",
    "rust",
    "kotlin",
    "java",
    "csharp",
    "php",
    "ruby",
    "go",
)


def _limit(value: Any, default: int = 20, maximum: int = 80) -> int:
    try:
        return max(1, min(maximum, int(value or default)))
    except Exception:
        return default


def _plugin_line(plugin) -> str:
    kinds = ", ".join(sorted({component.kind for component in plugin.components})) or "metadata"
    desc = (plugin.description or "").strip() or "Aciklama yok."
    return f"- {plugin.source}/{plugin.name} [{kinds}]: {desc[:260]}"


def _skill_line(skill) -> str:
    desc = (skill.description or "").strip() or "Aciklama yok."
    return f"- {skill.name}: {desc[:260]}"


def _is_coding_plugin(plugin) -> bool:
    haystack = " ".join(
        [
            plugin.name,
            plugin.description or "",
            " ".join(component.name for component in plugin.components),
        ]
    ).casefold()
    return any(term in haystack for term in CODING_TERMS)


def _is_coding_skill(skill) -> bool:
    haystack = f"{skill.name} {skill.description}".casefold()
    return any(term in haystack for term in CODING_TERMS)


def run(action: str = "summary", query: str = "", source: str = "all", limit: int = 20) -> str:
    from core.claude_plugin_adapter import get_plugin, list_plugins, read_component, search_plugins
    from core.skill_library import get_skill, list_skills, search_skills

    action = (action or "summary").strip().lower()
    source = (source or "all").strip().lower()
    limit = _limit(limit)

    if action == "summary":
        skills = list_skills()
        plugins = list_plugins("all")
        official = [plugin for plugin in plugins if plugin.source == "official"]
        external = [plugin for plugin in plugins if plugin.source == "external"]
        mcp_count = sum(1 for plugin in plugins for component in plugin.components if component.kind == "mcp")
        coding_count = sum(1 for plugin in plugins if _is_coding_plugin(plugin))
        return (
            "Jarvis aktif envanteri:\n"
            f"- Skill: {len(skills)}\n"
            f"- Claude plugin: {len(plugins)} ({len(official)} official, {len(external)} external)\n"
            f"- MCP config tasiyan plugin: {mcp_count}\n"
            f"- Kodlama/code-review odakli plugin: {coding_count}\n"
            "- Detay icin action=skills, plugins, coding, mcp veya detail kullan."
        )

    if action == "skills":
        rows = search_skills(query, limit) if query else list_skills()[:limit]
        if not rows:
            return "Eslesen skill bulunamadi."
        return "Jarvis skill listesi:\n" + "\n".join(_skill_line(skill) for skill in rows)

    if action == "plugins":
        rows = search_plugins(query, source, limit) if query else list_plugins(source)[:limit]
        if not rows:
            return "Eslesen Claude plugin bulunamadi."
        return "Claude plugin listesi:\n" + "\n".join(_plugin_line(plugin) for plugin in rows)

    if action == "coding":
        plugins = [plugin for plugin in list_plugins(source) if _is_coding_plugin(plugin)]
        skills = [skill for skill in list_skills() if _is_coding_skill(skill)]
        if query:
            plugins = search_plugins(query, source, limit)
            skills = search_skills(query, limit)
        lines = [
            "Claude/Jarvis kodlama yetenekleri:",
            "Pluginler:",
            *(_plugin_line(plugin) for plugin in plugins[:limit]),
            "Skill'ler:",
            *(_skill_line(skill) for skill in skills[: min(limit, 12)]),
            "Not: Bunlar Jarvis'in okuyup uygulayabildigi workflow/talimat ve MCP entegrasyonlaridir; Claude model API'si ayrica CLAUDE_API_KEY ile baglanabilir.",
        ]
        return "\n".join(lines)

    if action == "mcp":
        plugins = [
            plugin
            for plugin in list_plugins(source)
            if any(component.kind == "mcp" for component in plugin.components)
        ]
        if query:
            plugins = [plugin for plugin in plugins if query.casefold() in plugin.name.casefold() or query.casefold() in (plugin.description or "").casefold()]
        if not plugins:
            return "MCP bileseni olan plugin bulunamadi."
        return "MCP pluginleri:\n" + "\n".join(_plugin_line(plugin) for plugin in plugins[:limit])

    if action == "tools":
        try:
            import tool_defs

            names = sorted({item.get("name", "") for item in tool_defs.TOOL_DECLARATIONS if item.get("name")})
            if query:
                names = [name for name in names if query.casefold() in name.casefold()]
            return f"Jarvis tool listesi ({len(names)}):\n" + "\n".join(f"- {name}" for name in names[:limit])
        except Exception as exc:
            return f"Tool envanteri okunamadi: {type(exc).__name__}: {exc}"

    if action == "detail":
        name = (query or "").strip()
        if not name:
            return "Detay icin query alanina skill veya plugin adi ver."
        skill = get_skill(name)
        if skill:
            return f"Skill: {skill.name}\nPath: {skill.path}\n\n{skill.content[:6000]}"
        plugin = get_plugin(name, source)
        if plugin:
            lines = [_plugin_line(plugin), "Components:"]
            lines.extend(f"- {component.kind}: {component.name}" for component in plugin.components)
            readable = next((component for component in plugin.components if component.kind in {"skill", "command", "readme"}), None)
            if readable:
                data = read_component(plugin.name, readable.name, readable.kind, 5000)
                if "content" in data:
                    lines.append("\nIlk okunabilir bilesen:\n" + data["content"][:5000])
            return "\n".join(lines)
        return f"Skill/plugin bulunamadi: {name}"

    return "Gecersiz action. summary, skills, plugins, coding, mcp, tools veya detail kullan."
