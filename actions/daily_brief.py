from __future__ import annotations

import datetime as dt


def _safe(label: str, func) -> str:
    try:
        value = func()
        return value or f"{label}: bilgi yok."
    except Exception as exc:
        return f"{label}: alinamadi ({exc})."


def daily_brief(sections: str = "all") -> str:
    wanted = {s.strip().lower() for s in (sections or "all").split(",") if s.strip()}
    all_sections = "all" in wanted
    lines = [f"Gunluk ozet - {dt.datetime.now().strftime('%d.%m.%Y %H:%M')}"]

    if all_sections or "system" in wanted:
        from actions.sys_info import sys_info

        lines.append(_safe("Sistem", lambda: sys_info("battery ram disk network")))

    if all_sections or "weather" in wanted:
        from actions.weather import get_weather_summary

        lines.append(_safe("Hava", lambda: get_weather_summary(None)))

    if all_sections or "calendar" in wanted:
        from actions.calendar import get_calendar_events

        lines.append(_safe("Takvim", lambda: get_calendar_events("today", 5)))

    if all_sections or "reminders" in wanted:
        from actions.reminders import get_reminders

        lines.append(_safe("Hatirlaticilar", lambda: get_reminders("upcoming", 5, "")))

    if all_sections or "email" in wanted:
        from services.google_manager import get_latest_email

        lines.append(_safe("E-posta", get_latest_email))

    return "\n\n".join(lines)
