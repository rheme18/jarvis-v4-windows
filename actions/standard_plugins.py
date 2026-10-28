from __future__ import annotations

from actions.app_launcher_profiles import launch_app_profile as _launch_app_profile
from actions.app_usage import app_usage as _app_usage
from actions.backup_manager import backup_manager as _backup_manager
from actions.browser import browser_control as _browser_control
from actions.calendar import add_calendar_event as _add_calendar_event
from actions.calendar import delete_calendar_event as _delete_calendar_event
from actions.calendar import get_calendar_events as _get_calendar_events
from actions.clipboard_notes import clipboard_notes as _clipboard_notes
from actions.code_map import code_map as _code_map
from actions.daily_brief import daily_brief as _daily_brief
from actions.downloads_cleaner import downloads_cleaner as _downloads_cleaner
from actions.focus_guard import focus_guard as _focus_guard
from actions.health import get_health_data as _get_health_data
from actions.intent_history import intent_history as _intent_history
from actions.media import play_media as _play_media
from actions.open_app import open_app as _open_app
from actions.project_assistant import project_assistant as _project_assistant
from actions.project_snapshot import project_snapshot as _project_snapshot
from actions.quick_notes import quick_note as _quick_note
from actions.reminders import add_reminder as _add_reminder
from actions.reminders import delete_reminder as _delete_reminder
from actions.reminders import get_reminders as _get_reminders
from actions.safe_cleaner import safe_cleaner as _safe_cleaner
from actions.smart_todo import smart_todo as _smart_todo
from actions.study_timer import get_timer_status as _get_timer_status
from actions.study_timer import start_study_timer as _start_study_timer
from actions.system_health_report import system_health_report as _system_health_report
from actions.text_tools import text_tools as _text_tools
from actions.voice_commands_help import voice_commands_help as _voice_commands_help
from actions.window_snap import window_snap as _window_snap
from actions.youtube_stats import get_youtube_channel_report as _get_youtube_channel_report


PLUGIN_META = {
    "category": "standard_actions",
    "source_type": "main_migration",
}


def _decl(name: str, description: str, properties: dict | None = None, required: list[str] | None = None) -> dict:
    return {
        "name": name,
        "description": description,
        "parameters": {
            "type": "OBJECT",
            "properties": properties or {},
            "required": required or [],
        },
    }


TOOL_DECLARATIONS = [
    _decl(
        "open_app",
        "Windows'ta uygulama acar.",
        {"app_name": {"type": "STRING", "description": "Acilacak uygulama adi."}},
        ["app_name"],
    ),
    _decl(
        "start_study_timer",
        "Odaklanma/calisma zamanlayicisi baslatir.",
        {
            "duration_minutes": {"type": "NUMBER", "description": "Sure, dakika cinsinden."},
            "task_name": {"type": "STRING", "description": "Calisma veya gorev adi."},
        },
    ),
    _decl("get_timer_status", "Odaklanma zamanlayicisi durumunu ve istatistiklerini getirir."),
    _decl(
        "get_calendar_events",
        "Takvim etkinliklerini listeler.",
        {
            "query": {"type": "STRING", "description": "today | tomorrow | upcoming veya metin sorgu."},
            "limit": {"type": "NUMBER", "description": "Maksimum etkinlik sayisi."},
        },
    ),
    _decl(
        "add_calendar_event",
        "Takvime etkinlik ekler.",
        {
            "title": {"type": "STRING", "description": "Etkinlik basligi."},
            "start_iso": {"type": "STRING", "description": "Baslangic ISO zamani."},
            "end_iso": {"type": "STRING", "description": "Bitis ISO zamani."},
            "notes": {"type": "STRING", "description": "Notlar."},
            "location": {"type": "STRING", "description": "Konum."},
            "calendar_name": {"type": "STRING", "description": "Takvim adi."},
            "all_day": {"type": "BOOLEAN", "description": "Tum gun etkinligi."},
        },
        ["title", "start_iso", "end_iso"],
    ),
    _decl(
        "delete_calendar_event",
        "Takvim etkinligi siler.",
        {
            "title": {"type": "STRING", "description": "Silinecek etkinlik basligi."},
            "start_iso": {"type": "STRING", "description": "Opsiyonel baslangic zamani."},
            "calendar_name": {"type": "STRING", "description": "Takvim adi."},
            "delete_all_matches": {"type": "BOOLEAN", "description": "Tum eslesenleri sil."},
        },
        ["title"],
    ),
    _decl(
        "get_reminders",
        "Animsaticilari listeler.",
        {
            "query": {"type": "STRING", "description": "upcoming | today | all veya metin sorgu."},
            "limit": {"type": "NUMBER", "description": "Maksimum animsatici sayisi."},
            "list_name": {"type": "STRING", "description": "Liste adi."},
        },
    ),
    _decl(
        "add_reminder",
        "Yeni animsatici ekler.",
        {
            "title": {"type": "STRING", "description": "Animsatici basligi."},
            "due_iso": {"type": "STRING", "description": "Vade ISO zamani."},
            "notes": {"type": "STRING", "description": "Notlar."},
            "list_name": {"type": "STRING", "description": "Liste adi."},
            "priority": {"type": "STRING", "description": "Oncelik."},
            "all_day": {"type": "BOOLEAN", "description": "Tum gun."},
        },
        ["title"],
    ),
    _decl(
        "delete_reminder",
        "Animsatici siler.",
        {
            "title": {"type": "STRING", "description": "Silinecek animsatici basligi."},
            "list_name": {"type": "STRING", "description": "Liste adi."},
        },
        ["title"],
    ),
    _decl(
        "browser_control",
        "Tarayici acma, URL veya arama islemleri yapar.",
        {
            "action": {"type": "STRING", "description": "open_url | search | youtube_search vb."},
            "url": {"type": "STRING", "description": "Acilacak URL."},
            "query": {"type": "STRING", "description": "Arama metni."},
        },
    ),
    _decl(
        "play_media",
        "YouTube/Spotify gibi kaynaklarda medya oynatir.",
        {
            "query": {"type": "STRING", "description": "Calinacak medya aramasi."},
            "provider": {"type": "STRING", "description": "auto | youtube | spotify."},
            "autoplay": {"type": "BOOLEAN", "description": "Otomatik oynatma."},
        },
    ),
    _decl(
        "get_youtube_channel_report",
        "YouTube kanali icin ozet ve son video raporu verir.",
        {
            "query": {"type": "STRING", "description": "overview veya analiz istegi."},
            "handle": {"type": "STRING", "description": "Kanal handle/URL/ID."},
            "video_limit": {"type": "NUMBER", "description": "Video limiti."},
        },
    ),
    _decl(
        "get_health_data",
        "Yerel saglik verilerini ozetler.",
        {"query": {"type": "STRING", "description": "all | steps | sleep | heart vb."}},
    ),
    _decl(
        "quick_note",
        "Hizli not ekler, arar, listeler veya siler.",
        {
            "action": {"type": "STRING", "description": "add | list | search | delete."},
            "text": {"type": "STRING", "description": "Not metni."},
            "query": {"type": "STRING", "description": "Arama metni."},
            "note_id": {"type": "STRING", "description": "Not kimligi."},
            "limit": {"type": "NUMBER", "description": "Liste limiti."},
        },
    ),
    _decl(
        "clipboard_notes",
        "Pano metnini okur, ozetler veya notlastirir.",
        {
            "action": {"type": "STRING", "description": "read | summarize | save."},
            "text": {"type": "STRING", "description": "Opsiyonel metin."},
            "title": {"type": "STRING", "description": "Not basligi."},
        },
    ),
    _decl("daily_brief", "Gunluk ozet raporu hazirlar.", {"sections": {"type": "STRING", "description": "all veya bolum listesi."}}),
    _decl(
        "launch_app_profile",
        "Uygulama/URL profil seti acar.",
        {
            "profile": {"type": "STRING", "description": "code | study | media | meeting | writing | planning | creative | creator | devops."},
            "apps": {"type": "STRING", "description": "Ek uygulamalar."},
            "urls": {"type": "STRING", "description": "Ek URL'ler."},
        },
    ),
    _decl(
        "downloads_cleaner",
        "Indirilenler klasorunu raporlar veya onayla temizler.",
        {
            "action": {"type": "STRING", "description": "report | clean."},
            "days": {"type": "NUMBER", "description": "Yas filtresi."},
            "min_size_mb": {"type": "NUMBER", "description": "Minimum boyut."},
            "confirm": {"type": "BOOLEAN", "description": "Temizlik onayi."},
        },
    ),
    _decl(
        "project_assistant",
        "Proje icin rapor, komut ve yardim uretir.",
        {
            "action": {"type": "STRING", "description": "report | commands | files."},
            "path": {"type": "STRING", "description": "Proje yolu."},
        },
    ),
    _decl(
        "window_snap",
        "Pencereyi ekranda hizalar.",
        {
            "action": {"type": "STRING", "description": "left | right | maximize | center."},
            "title": {"type": "STRING", "description": "Pencere basligi filtresi."},
        },
    ),
    _decl("system_health_report", "Sistem saglik raporu verir.", {"level": {"type": "STRING", "description": "summary | detail."}}),
    _decl(
        "text_tools",
        "Metin temizleme, ozetleme ve donusturme araci.",
        {
            "action": {"type": "STRING", "description": "clean | summarize | slug | bullets."},
            "text": {"type": "STRING", "description": "Islenecek metin."},
            "max_chars": {"type": "NUMBER", "description": "Maksimum karakter."},
        },
    ),
    _decl(
        "backup_manager",
        "Yedekleme planlar veya onayla yedek alir.",
        {
            "action": {"type": "STRING", "description": "plan | backup."},
            "source": {"type": "STRING", "description": "Kaynak yol."},
            "destination": {"type": "STRING", "description": "Hedef yol."},
            "confirm": {"type": "BOOLEAN", "description": "Calistirma onayi."},
        },
    ),
    _decl(
        "intent_history",
        "Jarvis arac kullanim gecmisini raporlar.",
        {
            "action": {"type": "STRING", "description": "report | search."},
            "query": {"type": "STRING", "description": "Arama metni."},
            "limit": {"type": "NUMBER", "description": "Kayit limiti."},
        },
    ),
    _decl(
        "smart_todo",
        "Akilli gorev listesi yonetir.",
        {
            "action": {"type": "STRING", "description": "add | list | done | delete | search."},
            "title": {"type": "STRING", "description": "Gorev basligi."},
            "notes": {"type": "STRING", "description": "Notlar."},
            "priority": {"type": "STRING", "description": "low | medium | high."},
            "due": {"type": "STRING", "description": "Vade."},
            "todo_id": {"type": "STRING", "description": "Gorev kimligi."},
            "query": {"type": "STRING", "description": "Arama metni."},
            "limit": {"type": "NUMBER", "description": "Liste limiti."},
        },
    ),
    _decl(
        "focus_guard",
        "Dikkat dagitan uygulamalari raporlar veya onayla kapatir.",
        {
            "action": {"type": "STRING", "description": "report | close."},
            "apps": {"type": "STRING", "description": "Uygulama listesi."},
            "confirm": {"type": "BOOLEAN", "description": "Kapatma onayi."},
        },
    ),
    _decl(
        "project_snapshot",
        "Proje dosyalari ve git durumundan ozet cikarir.",
        {
            "action": {"type": "STRING", "description": "summary | files."},
            "path": {"type": "STRING", "description": "Proje yolu."},
            "max_files": {"type": "NUMBER", "description": "Maksimum dosya."},
        },
    ),
    _decl(
        "code_map",
        "Python kod haritasi ve fonksiyon listesi uretir.",
        {
            "action": {"type": "STRING", "description": "overview | search."},
            "path": {"type": "STRING", "description": "Proje yolu."},
            "query": {"type": "STRING", "description": "Arama metni."},
            "limit": {"type": "NUMBER", "description": "Limit."},
        },
    ),
    _decl(
        "app_usage",
        "Aktif uygulama kullanimini kaydeder veya raporlar.",
        {
            "action": {"type": "STRING", "description": "snapshot | report | list | clear."},
            "limit": {"type": "NUMBER", "description": "Limit."},
        },
    ),
    _decl(
        "safe_cleaner",
        "Projedeki cache/pyc/log adaylarini guvenli sekilde tarar veya temizler.",
        {
            "action": {"type": "STRING", "description": "scan | clean."},
            "scope": {"type": "STRING", "description": "project | actions."},
            "confirm": {"type": "BOOLEAN", "description": "Temizlik onayi."},
            "mode": {"type": "STRING", "description": "review | delete."},
        },
    ),
    _decl(
        "voice_commands_help",
        "Kullanilabilir sesli komutlari listeler.",
        {
            "category": {"type": "STRING", "description": "all | system | productivity | project | web | personal."},
            "query": {"type": "STRING", "description": "Arama metni."},
            "limit": {"type": "NUMBER", "description": "Limit."},
        },
    ),
]


def open_app(app_name: str) -> str:
    return _open_app(app_name) or f"{app_name} acildi."


def start_study_timer(duration_minutes: int = 25, task_name: str = "Calisma") -> str:
    return _start_study_timer(int(duration_minutes or 25), task_name or "Calisma")


def get_timer_status() -> str:
    return _get_timer_status()


def get_calendar_events(query: str = "today", limit: int = 6) -> str:
    return _get_calendar_events(query, int(limit or 6))


def add_calendar_event(
    title: str,
    start_iso: str,
    end_iso: str,
    notes: str = "",
    location: str = "",
    calendar_name: str = "",
    all_day: bool = False,
) -> str:
    return _add_calendar_event(title, start_iso, end_iso, notes, location, calendar_name, bool(all_day))


def delete_calendar_event(
    title: str,
    start_iso: str = "",
    calendar_name: str = "",
    delete_all_matches: bool = False,
) -> str:
    return _delete_calendar_event(title, start_iso, calendar_name, bool(delete_all_matches))


def get_reminders(query: str = "upcoming", limit: int = 8, list_name: str = "") -> str:
    return _get_reminders(query, int(limit or 8), list_name)


def add_reminder(
    title: str,
    due_iso: str = "",
    notes: str = "",
    list_name: str = "",
    priority: str = "",
    all_day: bool = False,
) -> str:
    return _add_reminder(title, due_iso, notes, list_name, priority, bool(all_day))


def delete_reminder(title: str, list_name: str = "") -> str:
    return _delete_reminder(title, list_name)


def browser_control(action: str = "", url: str = "", query: str = "") -> str:
    return _browser_control(action, url, query) or "Tamam."


def play_media(query: str = "", provider: str = "auto", autoplay: bool = True) -> str:
    return _play_media(query, provider, bool(autoplay)) or "Medya oynatma baslatildi."


def get_youtube_channel_report(query: str = "overview", handle: str = "", video_limit: int = 6) -> str:
    return _get_youtube_channel_report(query, handle, int(video_limit or 6))


def get_health_data(query: str = "all") -> str:
    return _get_health_data(query)


def quick_note(action: str = "list", text: str = "", query: str = "", note_id: str = "", limit: int = 10) -> str:
    return _quick_note(action, text, query, note_id, int(limit or 10))


def clipboard_notes(action: str = "read", text: str = "", title: str = "") -> str:
    return _clipboard_notes(action, text, title)


def daily_brief(sections: str = "all") -> str:
    return _daily_brief(sections)


def launch_app_profile(profile: str = "code", apps: str = "", urls: str = "") -> str:
    return _launch_app_profile(profile, apps, urls)


def downloads_cleaner(action: str = "report", days: int = 30, min_size_mb: int = 100, confirm: bool = False) -> str:
    return _downloads_cleaner(action, int(days or 30), int(min_size_mb or 100), bool(confirm))


def project_assistant(action: str = "report", path: str = "") -> str:
    return _project_assistant(action, path)


def window_snap(action: str = "left", title: str = "") -> str:
    return _window_snap(action, title)


def system_health_report(level: str = "summary") -> str:
    return _system_health_report(level)


def text_tools(action: str = "clean", text: str = "", max_chars: int = 600) -> str:
    return _text_tools(action, text, int(max_chars or 600))


def backup_manager(action: str = "plan", source: str = "", destination: str = "", confirm: bool = False) -> str:
    return _backup_manager(action, source, destination, bool(confirm))


def intent_history(action: str = "report", query: str = "", limit: int = 15) -> str:
    return _intent_history(action, query, int(limit or 15))


def smart_todo(
    action: str = "list",
    title: str = "",
    notes: str = "",
    priority: str = "medium",
    due: str = "",
    todo_id: str = "",
    query: str = "",
    limit: int = 12,
) -> str:
    return _smart_todo(action, title, notes, priority, due, todo_id, query, int(limit or 12))


def focus_guard(action: str = "report", apps: str = "", confirm: bool = False) -> str:
    return _focus_guard(action, apps, bool(confirm))


def project_snapshot(action: str = "summary", path: str = "", max_files: int = 12) -> str:
    return _project_snapshot(action, path, int(max_files or 12))


def code_map(action: str = "overview", path: str = "", query: str = "", limit: int = 30) -> str:
    return _code_map(action, path, query, int(limit or 30))


def app_usage(action: str = "snapshot", limit: int = 20) -> str:
    return _app_usage(action, int(limit or 20))


def safe_cleaner(action: str = "scan", scope: str = "project", confirm: bool = False, mode: str = "review") -> str:
    return _safe_cleaner(action, scope, bool(confirm), mode)


def voice_commands_help(category: str = "all", query: str = "", limit: int = 30) -> str:
    return _voice_commands_help(category, query, int(limit or 30))
