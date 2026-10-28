from __future__ import annotations

from core.skill_library import get_skill, list_skills, search_skills


TOOL_DECLARATION = {
    "name": "skill_library",
    "description": (
        "JARVIS'e entegre edilen skills klasorunu listeler, arar veya ilgili SKILL.md "
        "icerigini okur. Belge, PDF, PPTX, XLSX, frontend, Claude API, MCP veya test "
        "gorevlerinde once bu araci kullan."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "list | search | read"},
            "query": {"type": "STRING", "description": "Aranacak skill veya konu."},
            "name": {"type": "STRING", "description": "Okunacak skill adi."},
            "limit": {"type": "NUMBER", "description": "Maksimum sonuc sayisi."},
            "include_body": {"type": "BOOLEAN", "description": "read icin SKILL.md metnini de dondur."},
        },
        "required": ["action"],
    },
}

PLUGIN_META = {"category": "skills", "danger": "safe", "ui_visible": True}


def run(
    action: str = "list",
    query: str = "",
    name: str = "",
    limit: int = 12,
    include_body: bool = False,
) -> str:
    action = (action or "list").strip().lower()
    limit = max(1, min(int(limit or 12), 40))
    if action == "list":
        rows = list_skills(limit)
        if not rows:
            return "Entegre skill bulunamadi."
        return "\n".join(f"- {item.name}: {item.description[:260]}" for item in rows)
    if action == "search":
        rows = search_skills(query, limit)
        if not rows:
            return f"'{query}' icin skill bulunamadi."
        return "\n".join(f"- {item.name}: {item.description[:320]}" for item in rows)
    if action == "read":
        data = get_skill(name or query, include_body=include_body, max_chars=12000)
        if "error" in data:
            return data["error"]
        lines = [f"Skill: {data['name']}", f"Path: {data['path']}", f"Description: {data['description']}"]
        if include_body and data.get("body"):
            lines.append("\n--- SKILL.md ---\n" + data["body"])
        return "\n".join(lines)
    return "Gecersiz action. list, search veya read kullan."
