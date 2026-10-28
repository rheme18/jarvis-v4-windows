from __future__ import annotations

from actions.code_map import code_map
from actions.project_assistant import project_assistant
from actions.project_snapshot import project_snapshot
from actions.quick_notes import quick_note
from actions.safe_cleaner import safe_cleaner
from actions.system_health_report import system_health_report
from actions.voice_commands_help import voice_commands_help


TOOL_DECLARATION = {
    "name": "workflow_runner",
    "description": "Cok adimli Jarvis gorev zincirlerini planlar veya calistirir.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "workflow": {
                "type": "STRING",
                "description": "project_scan | daily_start | plugin_audit | maintenance_review",
            },
            "mode": {"type": "STRING", "description": "plan | run"},
            "path": {"type": "STRING", "description": "Proje yolu. Bos ise mevcut proje."},
            "confirm": {"type": "BOOLEAN", "description": "Temizlik gibi hassas adimlari calistirma onayi."},
        },
    },
}

PLUGIN_META = {
    "category": "workflow",
    "danger": "safe",
    "ui_visible": True,
    "aliases": ["gorev zinciri", "workflow", "akilli akis"],
}


WORKFLOWS = {
    "project_scan": [
        "Proje ozetini cikar",
        "Kod haritasini uret",
        "Proje asistan raporunu hazirla",
        "Guvenli temizlik adaylarini tara",
    ],
    "daily_start": [
        "Sistem saglik ozetini al",
        "Sesli komut rehberinden kisa komut listesi ver",
        "Hizli notlara gunluk baslangic notu ekle",
    ],
    "plugin_audit": [
        "Plugin durumunu ozetle",
        "Kullanilabilir komut kategorilerini listele",
    ],
    "maintenance_review": [
        "Sistem sagligini denetle",
        "Proje temizlenebilir dosyalarini tara",
        "Onay varsa guvenli temizlik inceleme modunu calistir",
    ],
}


def _plan(workflow: str) -> str:
    steps = WORKFLOWS.get(workflow)
    if not steps:
        return "Bilinmeyen workflow. Kullan: " + ", ".join(sorted(WORKFLOWS))
    lines = [f"Workflow planı: {workflow}"]
    lines.extend(f"{idx}. {step}" for idx, step in enumerate(steps, 1))
    return "\n".join(lines)


def run(workflow: str = "project_scan", mode: str = "plan", path: str = "", confirm: bool = False) -> str:
    workflow = (workflow or "project_scan").strip().lower()
    mode = (mode or "plan").strip().lower()

    if mode != "run":
        return _plan(workflow)

    results: list[str] = [f"Workflow calisti: {workflow}"]

    if workflow == "project_scan":
        results.append(project_snapshot("summary", path, 10))
        results.append(code_map("overview", path, "", 25))
        results.append(project_assistant("report", path))
        results.append(safe_cleaner("scan", "project", False, "review"))
    elif workflow == "daily_start":
        results.append(system_health_report("summary"))
        results.append(voice_commands_help("all", "", 12))
        results.append(quick_note("add", "Gunluk baslangic workflow'u calistirildi.", "", "", 10))
    elif workflow == "plugin_audit":
        from actions.plugin_manager import run as plugin_manager

        results.append(plugin_manager("status"))
        results.append(voice_commands_help("all", "plugin", 12))
    elif workflow == "maintenance_review":
        results.append(system_health_report("summary"))
        results.append(safe_cleaner("scan", "project", False, "review"))
        if confirm:
            results.append(safe_cleaner("clean", "project", True, "review"))
        else:
            results.append("Temizlik calistirilmadi; sadece tarama yapildi. Temizlik icin confirm=true gerekir.")
    else:
        return _plan(workflow)

    return "\n\n---\n\n".join(str(item) for item in results if item)
