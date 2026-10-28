from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from core.error_boundary import graceful_error, log_root_cause
from database import db_save, db_search, db_delete


@dataclass
class ToolContext:
    base_dir: Path
    ui: Any = None
    webcam_streamer: Any = None
    get_api_key: Callable[[], str] | None = None
    focus_tool: Callable[[str, dict[str, Any]], None] | None = None
    vision_model: str = "gemini-2.5-flash"


@dataclass
class ToolExecutionResult:
    name: str
    result: str
    status: str
    elapsed_ms: int


class ToolOrchestrator:
    def __init__(self, plugin_registry: Any = None, default_timeout: float = 90.0) -> None:
        self.plugin_registry = plugin_registry
        self.default_timeout = default_timeout
        self._cyber_names = self._load_cyber_names()

    @staticmethod
    def _load_cyber_names() -> set[str]:
        try:
            from tools.declarations import TOOL_DECLARATIONS as cyber_declarations

            return {item.get("name", "") for item in cyber_declarations if item.get("name")}
        except Exception:
            return set()

    async def _to_thread(self, func: Callable[[], Any], timeout: float | None = None) -> str:
        value = await asyncio.wait_for(asyncio.to_thread(func), timeout=timeout or self.default_timeout)
        return str(value) if value is not None else "Tamam."

    def _emit(self, event_type: str, message: str, **data: Any) -> None:
        try:
            from core.event_bus import emit

            emit(event_type, message, **data)
        except Exception:
            pass

    def _log(self, level: str, category: str, message: str, **data: Any) -> None:
        try:
            from core.jarvis_logger import log_event

            log_event(level, category, message, **data)
        except Exception:
            pass

    @staticmethod
    def _launch_person_profile(person: dict[str, Any] | None = None) -> str:
        """Start the contact UI and detect startup crashes before reporting success."""
        base_dir = Path(__file__).resolve().parent.parent
        ui_path = base_dir / "ui" / "person_profile_ui.py"
        if not ui_path.is_file():
            return f"Kişi veritabanı arayüzü bulunamadı: {ui_path}"

        command = [sys.executable, str(ui_path)]
        if person:
            command.append(json.dumps(person, ensure_ascii=False))
        creationflags = (getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                         | getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            process = subprocess.Popen(
                command, cwd=str(base_dir), stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
                creationflags=creationflags,
            )
            try:
                process.wait(timeout=1.5)
            except subprocess.TimeoutExpired:
                return f"Kişi veritabanı arayüzü açıldı (işlem {process.pid})."
            details = process.stdout.read().strip() if process.stdout else ""
            details = details[-1400:] if details else "Başlangıç sırasında pencere kapandı."
            return f"Kişi veritabanı açılamadı (çıkış kodu {process.returncode}): {details}"
        except Exception as exc:
            return f"Kişi veritabanı arayüzü başlatılamadı: {exc}"

    async def execute(self, name: str, args: dict[str, Any] | None, ctx: ToolContext) -> ToolExecutionResult:
        started = time.perf_counter()
        name = str(name or "").strip()
        clean_args = dict(args or {})
        self._emit("tool_call", name, args=clean_args)
        self._log("INFO", "tool", f"Tool call: {name}", args=clean_args)

        try:
            from core.approval_center import needs_approval, request_approval

            if needs_approval(name, clean_args):
                approval = request_approval(name, clean_args, "JARVIS riskli bir islem icin onay bekliyor.")
                result = (
                    f"{name} icin onay gerekiyor. Settings > Approvals panelinde "
                    f"onay bekliyor. ID: {approval['id']}"
                )
                return self._finish(name, result, "approval_required", started, clean_args)
        except Exception as exc:
            log_root_cause("approval", "Approval kontrolu basarisiz, tool guvenli hata ile durduruldu", exc, tool=name)
            return self._finish(name, graceful_error(name, exc), "error", started, clean_args)

        try:
            if name in CORE_TOOL_NAMES:
                result = await self._execute_core(name, clean_args, ctx)
            elif name in self._cyber_names:
                result = await self._execute_cyber(name, clean_args)
            elif self.plugin_registry and name in getattr(self.plugin_registry, "tools", {}):
                from core.plugin_loader import execute_plugin

                result = await asyncio.wait_for(
                    execute_plugin(self.plugin_registry, name, clean_args),
                    timeout=self.default_timeout,
                )
            else:
                result = f"Bilinmeyen arac: {name}"

            status = "error" if _looks_like_error(result) else "ok"
            return self._finish(name, result, status, started, clean_args)
        except Exception as exc:
            log_root_cause("tool", "Tool root-cause exception", exc, tool=name, args=clean_args)
            return self._finish(name, graceful_error(name, exc), "error", started, clean_args)

    def _finish(
        self,
        name: str,
        result: Any,
        status: str,
        started: float,
        args: dict[str, Any],
    ) -> ToolExecutionResult:
        text = str(result) if result is not None else "Tamam."
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        self._emit("tool_result", name, result=text[:1500], status=status, elapsed_ms=elapsed_ms)
        self._log("ERROR" if status == "error" else "INFO", "tool", f"Tool result: {name}", result=text[:1500], elapsed_ms=elapsed_ms)
        try:
            from actions.intent_history import record_tool_use

            if name != "intent_history":
                record_tool_use(name, args, text, "error" if status == "error" else "ok")
        except Exception as exc:
            log_root_cause("history", "Tool history yazilamadi", exc, tool=name)
        return ToolExecutionResult(name=name, result=text, status=status, elapsed_ms=elapsed_ms)

    async def _execute_cyber(self, name: str, args: dict[str, Any]) -> str:
        from tools import execute_custom_tool

        loop = asyncio.get_running_loop()
        return await execute_custom_tool(name, args, loop)

    async def _execute_core(self, name: str, args: dict[str, Any], ctx: ToolContext) -> str:
        if name == "save_memory":
            from memory.memory_manager import update_memory

            cat = args.get("category", "notes")
            key = args.get("key", "")
            val = args.get("value", "")
            if key and val:
                update_memory({cat: {key: {"value": val}}})
                return "ok"
            return "Hata: save_memory icin key ve value gerekli."

        if name == "delete_memory":
            from memory.memory_manager import delete_memory

            return delete_memory(args.get("category", ""), args.get("key", ""), args.get("match_text", ""))

        if name == "db_save":
            return await self._to_thread(
                lambda: db_save(
                    category=args.get("category", "note"),
                    content=args.get("content", ""),
                    title=args.get("title", ""),
                    tags=args.get("tags", "")
                )
            )

        if name == "db_search":
            return await self._to_thread(
                lambda: db_search(
                    query=args.get("query", ""),
                    category=args.get("category", None)
                )
            )

        if name == "db_delete":
            return await self._to_thread(
                lambda: db_delete(
                    record_id=int(args.get("record_id", 0))
                )
            )

        if name == "open_app":
            from actions.open_app import open_app

            return await self._to_thread(lambda: open_app(args.get("app_name", "")))

        if name == "sys_info":
            if ctx.focus_tool:
                ctx.focus_tool(name, args)
            from actions.sys_info import sys_info

            return await self._to_thread(lambda: sys_info(args.get("query", "all")))

        if name == "get_weather":
            if ctx.focus_tool:
                ctx.focus_tool(name, args)
            from actions.weather import get_weather_summary

            return await self._to_thread(lambda: get_weather_summary(args.get("location") or None))

        if name == "get_calendar_events":
            from actions.calendar import get_calendar_events

            return await self._to_thread(lambda: get_calendar_events(args.get("query", "today"), int(args.get("limit", 6) or 6)))

        if name == "add_calendar_event":
            from actions.calendar import add_calendar_event

            return await self._to_thread(
                lambda: add_calendar_event(
                    args.get("title", ""),
                    args.get("start_iso", ""),
                    args.get("end_iso", ""),
                    args.get("notes", ""),
                    args.get("location", ""),
                    args.get("calendar_name", ""),
                    bool(args.get("all_day", False)),
                )
            )

        if name == "delete_calendar_event":
            from actions.calendar import delete_calendar_event

            return await self._to_thread(
                lambda: delete_calendar_event(
                    args.get("title", ""),
                    args.get("start_iso", ""),
                    args.get("calendar_name", ""),
                    bool(args.get("delete_all_matches", False)),
                )
            )

        if name == "get_reminders":
            from actions.reminders import get_reminders

            return await self._to_thread(lambda: get_reminders(args.get("query", "upcoming"), int(args.get("limit", 8) or 8), args.get("list_name", "")))

        if name == "add_reminder":
            from actions.reminders import add_reminder

            return await self._to_thread(
                lambda: add_reminder(
                    args.get("title", ""),
                    args.get("due_iso", ""),
                    args.get("notes", ""),
                    args.get("list_name", ""),
                    args.get("priority", ""),
                    bool(args.get("all_day", False)),
                )
            )

        if name == "delete_reminder":
            from actions.reminders import delete_reminder

            return await self._to_thread(lambda: delete_reminder(args.get("title", ""), args.get("list_name", "")))

        if name == "browser_control":
            from actions.browser import browser_control

            return await self._to_thread(lambda: browser_control(args.get("action"), args.get("url"), args.get("query")))

        if name == "shell_run":
            from actions.shell import shell_run

            return await self._to_thread(lambda: shell_run(args.get("command", "")), timeout=60)

        if name == "toggle_webcam":
            return self._toggle_webcam(args, ctx)

        if name == "play_media":
            from actions.media import play_media

            return await self._to_thread(lambda: play_media(args.get("query", ""), args.get("provider", "auto"), bool(args.get("autoplay", True))))

        if name == "get_youtube_channel_report":
            from actions.youtube_stats import get_youtube_channel_report

            return await self._to_thread(
                lambda: get_youtube_channel_report(
                    args.get("query", "overview"),
                    args.get("handle", ""),
                    int(args.get("video_limit", 6) or 6),
                )
            )

        if name == "analyze_screen":
            from actions.screen_vision import analyze_screen

            return await self._to_thread(lambda: analyze_screen(args.get("query", "Ekranda ne var?"), args.get("target", "active_window")))

        if name == "send_whatsapp_message":
            from actions.whatsapp import send_whatsapp_message

            return await self._to_thread(
                lambda: send_whatsapp_message(
                    args.get("message", ""),
                    args.get("phone_number", ""),
                    args.get("recipient_name", ""),
                    bool(args.get("send_now", False)),
                    args.get("app_target", "auto"),
                ),
                timeout=130,
            )

        if name == "save_whatsapp_contact":
            from actions.whatsapp import save_whatsapp_contact

            return await self._to_thread(lambda: save_whatsapp_contact(args.get("display_name", ""), args.get("phone_number", ""), args.get("aliases", "")))

        if name == "manage_file":
            from actions.file_manager import manage_file

            return await self._to_thread(
                lambda: manage_file(
                    action=args.get("action", ""),
                    filename=args.get("filename", ""),
                    content=args.get("content", ""),
                    new_filename=args.get("new_filename", ""),
                    confirm=bool(args.get("confirm", False)),
                )
            )

        if name == "gui_automation":
            from actions.gui_control import handle_gui_action

            return await self._to_thread(lambda: handle_gui_action(args.get("action", ""), **args), timeout=45)

        if name == "db_add_person":
            from core.person_manager import add_person

            def _add():
                person = add_person(
                    name=args.get("name", ""),
                    role=args.get("role", "Kayıtlı Kişi"),
                    phone=args.get("phone", ""),
                    email=args.get("email", ""),
                    tags=args.get("tags", "Genel"),
                    notes=args.get("notes", ""),
                    photo_name=args.get("photo_name", "")
                )
                return f"'{person['name']}' veritabanına başarıyla kaydedildi Patron. Fotoğrafı için 'database/pngs/' klasörünü kullanabilirsin."

            return await self._to_thread(_add)

        if name == "db_show_person":
            from core.person_manager import get_person

            def _show():
                query = args.get("name", "") or args.get("query", "")
                person = get_person(query)

                if not person:
                    return f"Veritabanında '{query}' adında bir kayıt bulunamadı Patron."

                if ctx.ui is not None and hasattr(ctx.ui, "open_people_database"):
                    ctx.ui.open_people_database(person)
                    return f"{person['name']} kişi kartı JARVIS veritabanı penceresinde açılıyor."

                return self._launch_person_profile(person)

            return await self._to_thread(_show)
            
        if name == "db_list_people":
            def _list_ui():
                if ctx.ui is not None and hasattr(ctx.ui, "open_people_database"):
                    ctx.ui.open_people_database()
                    return "Kişi veritabanı JARVIS penceresinde açılıyor."
                return self._launch_person_profile()

            return await self._to_thread(_list_ui)    

        if name == "pc_control":
            from actions.pc_control import pc_master_control

            return await self._to_thread(lambda: pc_master_control(args.get("action", ""), args.get("value", None)), timeout=45)

        if name == "secure_vault_access":
            from actions.face_auth import manage_secure_vault, verify_user

            verified = await asyncio.wait_for(asyncio.to_thread(lambda: verify_user(timeout=15)), timeout=25)
            if not verified:
                return "Yuz dogrulama basarisiz. Yetkisiz erisim engellendi."
            action = str(args.get("action", "open_vault")).lower()
            if action == "system_files":
                subprocess.Popen(["explorer", r"C:\Windows\System32"])
                return "Yuz dogrulandi. Sistem dosyalari acildi."
            return await self._to_thread(lambda: manage_secure_vault(str(ctx.base_dir), action="open"), timeout=35)

        if name == "capture_camera_vision":
            from google import genai
            from actions.camera_vision import capture_and_analyze_shot

            api_key = ctx.get_api_key() if ctx.get_api_key else ""
            client = genai.Client(api_key=api_key, http_options={"api_version": "v1alpha"})
            return await self._to_thread(lambda: capture_and_analyze_shot(client, ctx.vision_model), timeout=80)

        if name == "check_email":
            from services.google_manager import get_latest_email

            return await self._to_thread(get_latest_email)

        if name == "gmail_search":
            from services.google_manager import gmail_search

            return await self._to_thread(lambda: gmail_search(args.get("query", ""), int(args.get("limit", 5) or 5)))

        if name == "gmail_labels":
            from services.google_manager import gmail_labels

            return await self._to_thread(gmail_labels)

        if name == "drive_search":
            from services.google_manager import drive_search_logic

            return await self._to_thread(lambda: drive_search_logic(args.get("query", ""), int(args.get("limit", 5) or 5)))

        if name == "git_push":
            from services.git_manager import jarvis_git_push

            return await self._to_thread(lambda: jarvis_git_push(args.get("commit_message", "auto")), timeout=120)

        if name == "scan_network":
            from services.network_scanner import get_network_report_text, scan_local_network

            await asyncio.wait_for(scan_local_network(), timeout=35)
            return get_network_report_text()

        if name == "check_security":
            from services.security_shield import get_security_report_text

            return await self._to_thread(get_security_report_text, timeout=70)

        if name == "add_lgs_exam":
            from services.lgs_coach import add_exam_result

            return await self._to_thread(lambda: add_exam_result(args.get("exam_name", "Genel Deneme"), args.get("results", {})))

        if name == "get_lgs_report":
            from services.lgs_coach import get_lgs_summary

            return await self._to_thread(get_lgs_summary)

        if name == "vercel_control":
            from actions.vercel_control import vercel_master_control

            return await self._to_thread(lambda: vercel_master_control(**args))

        if name == "github_control":
            from actions.github_control import github_master_control

            return await self._to_thread(lambda: github_master_control(**args))

        if name == "get_health_data":
            from actions.health import get_health_data

            return await self._to_thread(lambda: get_health_data(args.get("query", "all")))

        if name == "windows_automation":
            from actions.windows_automation import windows_system_control

            return await self._to_thread(lambda: windows_system_control(**args))

        if name == "semantic_memory_search":
            from memory.vector_memory import semantic_memory_search

            return await self._to_thread(lambda: semantic_memory_search(args.get("query", ""), int(args.get("limit", 4) or 4), args.get("category")))

        if name == "autonomous_task_executor":
            from core.autonomous_agent import run_autonomous_task

            return await run_autonomous_task(args.get("goal", ""), args.get("context", ""))

        if name == "take_photo":
            from actions.photo_capture import capture_user_photo
            return await self._to_thread(lambda: capture_user_photo(args.get("caption", "")))

        if name == "ghost_typer":
            from actions.ghost_typer import ghost_type_text
            return await self._to_thread(lambda: ghost_type_text(args.get("text", ""), mode=args.get("mode", "type")))

        if name == "self_healing":
            from actions.self_healing import run_full_self_healing
            return await self._to_thread(lambda: run_full_self_healing(args.get("action", "full")))

        if name == "paranoid_mode_control":
            from actions.paranoid_mode import get_paranoid_sentinel
            sentinel = get_paranoid_sentinel()
            action = str(args.get("action", "status")).strip().lower()
            if action in ("enable", "start"):
                sentinel.configure(dim_screen=args.get("dim_screen", True), take_photo=args.get("take_photo", True))
                res = sentinel.start()
                return f"Paranoid Güvenlik Modu AKTİF edildi. {res}"
            elif action in ("disable", "stop"):
                res = sentinel.stop()
                return f"Paranoid Güvenlik Modu devre dışı bırakıldı. {res}"
            elif action == "status":
                st = sentinel.get_status()
                return f"Paranoid Mod Durumu: {'AKTİF' if st.get('is_active') else 'KAPALI'}, Yapılandırma: {st.get('config')}"
            elif action == "configure":
                sentinel.configure(dim_screen=args.get("dim_screen", True), take_photo=args.get("take_photo", True))
                return "Paranoid Mod ayarları başarıyla güncellendi."
            return f"Bilinmeyen eylem: {action}"

        if name == "air_gestures_control":
            from actions.air_gestures import get_air_gesture_controller
            controller = get_air_gesture_controller()
            action = str(args.get("action", "status")).strip().lower()
            if action in ("start", "enable"):
                res = controller.start(preview=args.get("preview", True))
                return res
            elif action in ("stop", "disable"):
                res = controller.stop()
                return res
            elif action == "toggle":
                if controller.is_running():
                    return controller.stop()
                return controller.start(preview=args.get("preview", True))
            elif action == "status":
                return f"Air Gestures Durumu: {'AKTİF' if controller.is_running() else 'KAPALI'}"
            return f"Bilinmeyen eylem: {action}"

        if name == "create_excel":
            from actions.office_automation import create_excel_document
            title = args.get("title", "Jarvis_Tablo")
            headers = args.get("headers", [])
            rows = args.get("rows", [])
            filename = args.get("filename")
            include_summary = bool(args.get("include_summary", False))
            res = await self._to_thread(lambda: create_excel_document(title, headers, rows, filename=filename, include_summary=include_summary))
            return res.get("message", str(res))

        if name == "create_powerpoint":
            from actions.office_automation import create_powerpoint_presentation
            title = args.get("title", "Sunum")
            subtitle = args.get("subtitle", "")
            slides = args.get("slides", [])
            filename = args.get("filename")
            res = await self._to_thread(lambda: create_powerpoint_presentation(title, subtitle, slides, filename=filename))
            return res.get("message", str(res))

        if name == "send_email":
            from actions.email_sender import send_email_message
            to = args.get("to", "")
            subject = args.get("subject", "")
            body = args.get("body", "")
            res = await self._to_thread(lambda: send_email_message(to, subject, body))
            return res.get("message", str(res))

        if name == "read_emails":
            from actions.email_sender import read_recent_emails
            count = int(args.get("count", 5))
            sq = args.get("search_query")
            res = await self._to_thread(lambda: read_recent_emails(count=count, search_query=sq))
            return res.get("summary", str(res))

        if name == "read_whatsapp":
            from actions.whatsapp_reader import read_whatsapp_messages
            count = int(args.get("count", 15))
            kw = args.get("keyword")
            res = await self._to_thread(lambda: read_whatsapp_messages(count=count, filter_keyword=kw))
            return res.get("summary", str(res))

        if name == "setup_owner_face":
            from utils.face_setup import setup_face
            success = await self._to_thread(setup_face)
            if success:
                return "Patron yüz tarama protokolü tamamlandı ve biyometrik model kaydedildi. Paranoid Mod artık yüzünüzü tanıyacaktır."
            return "Yüz kayıt işlemi iptal edildi veya kamera açılamadı."

        if name == "create_word_doc":
            from actions.skill_executor import create_docx_from_skill
            title = args.get("title", "Ödev Raporu")
            content = args.get("content", "")
            out_name = args.get("output_name")
            return await self._to_thread(lambda: create_docx_from_skill(title, content, out_name))

        if name == "create_pdf":
            from actions.skill_executor import create_pdf_from_skill
            title = args.get("title", "Belge")
            content = args.get("content", "")
            out_name = args.get("output_name")
            return await self._to_thread(lambda: create_pdf_from_skill(title, content, out_name))

        if name == "list_skills":
            from actions.skill_executor import list_skills
            skills = list_skills()
            summary = [f"📚 Entegre Claude Becerileri ({len(skills)} Adet):"]
            for s in skills:
                summary.append(f"• {s['name']} ({s['id']}): {s['description'][:70]}...")
            return "\n".join(summary)

        if name == "list_workflows":
            from core.workflow_engine import list_workflows
            wfs = list_workflows()
            if not wfs:
                return "Kayıtlı otomatik workflow bulunamadı."
            summary = [f"⚡ Kayıtlı İş Akışları ({len(wfs)} Adet):"]
            for w in wfs:
                summary.append(f"• {w['name']} [{w['file']}] — {w['step_count']} Adım: {w['description']}")
            return "\n".join(summary)

        if name == "run_workflow":
            from core.workflow_engine import run_workflow_file
            wf_name = args.get("workflow_name", "")
            return await self._to_thread(lambda: run_workflow_file(wf_name, orchestrator=self, ctx=ctx))

        if name == "scan_homework":
            from actions.study_automation import scan_messages_for_homework
            text = args.get("message_text", "")
            source = args.get("source", "WhatsApp / Mail")
            return await self._to_thread(lambda: scan_messages_for_homework(text, source=source))

        if name == "create_homework":
            from actions.study_automation import create_full_homework_package
            topic = args.get("topic", "Genel Araştırma")
            course = args.get("course", "Genel")
            doc_type = args.get("doc_type", "all")
            return await self._to_thread(lambda: create_full_homework_package(topic, course=course, doc_type=doc_type))

        if name == "create_study_plan":
            from actions.study_automation import generate_study_plan
            exam = args.get("exam_name", "Genel Sınav")
            hrs = float(args.get("available_hours_daily", 3.0))
            return await self._to_thread(lambda: generate_study_plan(exam, available_hours_daily=hrs))

        return f"Bilinmeyen core araci: {name}"

    def _toggle_webcam(self, args: dict[str, Any], ctx: ToolContext) -> str:
        streamer = ctx.webcam_streamer
        if not streamer:
            return "Webcam stream katmani hazir degil."
        action = str(args.get("action", "start")).strip().lower()
        if action == "start":
            status = streamer.start()
            if ctx.ui:
                ctx.ui.set_webcam_active(status in {"ok", "already_active"})
            if status == "ok":
                return "Webcam akisi baslatildi."
            if status == "already_active":
                return "Webcam zaten acik."
            return "Webcam baslatilamadi."
        streamer.stop()
        if ctx.ui:
            ctx.ui.set_webcam_active(False)
        return "Webcam akisi durduruldu."


CORE_TOOL_NAMES = {
    "save_memory",
    "delete_memory",
    "open_app",
    "db_add_person",
    "db_show_person",
    "db_list_people",
    "sys_info",
    "get_weather",
    "get_calendar_events",
    "add_calendar_event",
    "delete_calendar_event",
    "get_reminders",
    "add_reminder",
    "delete_reminder",
    "browser_control",
    "shell_run",
    "toggle_webcam",
    "play_media",
    "get_youtube_channel_report",
    "analyze_screen",
    "send_whatsapp_message",
    "save_whatsapp_contact",
    "manage_file",
    "gui_automation",
    "pc_control",
    "secure_vault_access",
    "capture_camera_vision",
    "check_email",
    "gmail_search",
    "gmail_labels",
    "drive_search",
    "git_push",
    "scan_network",
    "check_security",
    "add_lgs_exam",
    "get_lgs_report",
    "vercel_control",
    "github_control",
    "get_health_data",
    "db_save",
    "db_search",
    "db_delete",
    "windows_automation",
    "semantic_memory_search",
    "autonomous_task_executor",
    "take_photo",
    "ghost_typer",
    "self_healing",
    "paranoid_mode_control",
    "air_gestures_control",
    "create_excel",
    "create_powerpoint",
    "send_email",
    "read_emails",
    "read_whatsapp",
    "setup_owner_face",
    "create_word_doc",
    "create_pdf",
    "list_skills",
    "list_workflows",
    "run_workflow",
    "scan_homework",
    "create_homework",
    "create_study_plan",
}


def _looks_like_error(result: Any) -> bool:
    text = str(result or "").strip().lower()
    if not text:
        return False
    markers = (
        "hata",
        "error",
        "exception",
        "root-cause",
        "kok neden",
        "bulunamadi",
        "bulunamad",
        "acilamadi",
        "basarisiz",
        "izin",
        "onay gerekiyor",
        "gecersiz",
    )
    return any(marker in text for marker in markers)
