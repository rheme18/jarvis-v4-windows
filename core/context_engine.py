from __future__ import annotations

import datetime as dt
import os
import platform
from pathlib import Path
from typing import Iterable

from core.error_boundary import log_root_cause
from core.claude_plugin_adapter import format_plugin_context
from core.skill_library import format_skill_context


BASE_DIR = Path(__file__).resolve().parents[1]
EXTRA_RULES_PATH = BASE_DIR / "core" / "tool_rules_extra.txt"


PRIVATE_REASONING_POLICY = """
[INTERNAL QUALITY PIPELINE]
- Cevap vermeden once gizli bir scratchpad mantigiyla hedefi, varsayimlari, tool parametrelerini ve hata risklerini kontrol et.
- Zincirleme dusunceni veya gizli scratchpad'i kullaniciya aciklama; sadece gerekli kisa gerekce, karar ve sonucu ver.
- Bir tool sonucu hatali, eksik veya tutarsiz gorunurse ayni turn icinde once kok nedeni degerlendir, guvenli alternatif veya graceful fallback sec.
- Yikici islemlerde onay merkezini ve confirm alanlarini kullan; kullanici acik onay vermediyse uyguluyormus gibi yapma.
""".strip()


TOOL_ORCHESTRATION_POLICY = """
[TOOL ORCHESTRATION]
- Parametreleri eksik veya belirsiz tool cagirma; once mevcut contextten tamamla, hala riskliyse netlestir.
- Donanim, ekran, siber guvenlik ve dosya islemlerinde en dusuk riskli araci once kullan: rapor/scan -> plan -> onayli eylem.
- CPU/RAM yuksekse uzun tarama, kamera, ekran analizi ve network islemlerini kisa limitlerle calistir.
- Ag kesintisinde internet gerektiren entegrasyonlar yerine yerel fallback ve acik hata nedeni sun.
""".strip()


class DynamicContextManager:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or BASE_DIR

    def system_snapshot(self) -> str:
        try:
            import psutil

            cpu = psutil.cpu_percent(interval=0.05)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage(str(self.base_dir))
            battery = psutil.sensors_battery()
            net_up = any(stat.isup for stat in psutil.net_if_stats().values())
            lines = [
                "[LIVE SYSTEM SNAPSHOT]",
                f"os={platform.system()} {platform.release()}",
                f"cwd={self.base_dir}",
                f"cpu_percent={cpu:.1f}",
                f"ram_percent={ram.percent:.1f}",
                f"disk_percent={disk.percent:.1f}",
                f"network_link={'up' if net_up else 'down'}",
            ]
            if battery:
                plugged = "plugged" if battery.power_plugged else "battery"
                lines.append(f"battery_percent={battery.percent:.0f} mode={plugged}")
            if cpu >= 85 or ram.percent >= 90:
                lines.append("load_policy=high_load: prefer short bounded tool calls")
            return "\n".join(lines)
        except Exception as exc:
            log_root_cause("context", "System snapshot alinamadi", exc)
            return "[LIVE SYSTEM SNAPSHOT]\nstatus=unavailable"

    def recent_activity(self, limit: int = 6) -> str:
        chunks: list[str] = []
        try:
            from core.event_bus import recent_events

            events = recent_events(limit)
            if events:
                chunks.append("[RECENT EVENTS]")
                for item in events[-limit:]:
                    chunks.append(f"- {item.get('ts', '')} {item.get('type', '')}: {item.get('message', '')}")
        except Exception:
            pass
        try:
            from actions.intent_history import _load_history

            rows = _load_history(limit)
            if rows:
                chunks.append("[RECENT TOOL USE]")
                for item in rows[-limit:]:
                    chunks.append(f"- {item.get('tool', '')}: {item.get('status', '')}")
        except Exception:
            pass
        return "\n".join(chunks)

    def extra_rules(self) -> str:
        try:
            if EXTRA_RULES_PATH.exists():
                return EXTRA_RULES_PATH.read_text(encoding="utf-8", errors="replace").strip()
        except Exception as exc:
            log_root_cause("context", "Tool rules okunamadi", exc)
        return ""

    def tool_inventory(self, tool_names: Iterable[str] | None = None, max_names: int = 120) -> str:
        names = sorted({str(name) for name in (tool_names or []) if name})
        if not names:
            return ""
        clipped = names[: max(1, int(max_names or 120))]
        suffix = "" if len(names) == len(clipped) else f"\n... {len(names) - len(clipped)} tool daha var."
        return "[AVAILABLE TOOL NAMES]\n" + ", ".join(clipped) + suffix

    def build(
        self,
        base_prompt: str,
        memory_prompt: str = "",
        tool_names: Iterable[str] | None = None,
        user_hint: str = "",
    ) -> str:
        now = dt.datetime.now().astimezone()
        parts = [
            f"[CURRENT TIME]\n{now.strftime('%A, %d %B %Y - %H:%M %Z')}",
            self.system_snapshot(),
        ]
        if memory_prompt:
            parts.append(memory_prompt.strip())
        activity = self.recent_activity()
        if activity:
            parts.append(activity)
        skill_context = format_skill_context(user_hint, limit=8)
        if skill_context:
            parts.append(skill_context)
        plugin_context = format_plugin_context(user_hint, limit=8)
        if plugin_context:
            parts.append(plugin_context)
        inventory = self.tool_inventory(tool_names)
        if inventory:
            parts.append(inventory)
        rules = self.extra_rules()
        if rules:
            parts.append(rules)
        parts.extend([PRIVATE_REASONING_POLICY, TOOL_ORCHESTRATION_POLICY, base_prompt.strip()])
        return "\n\n".join(part for part in parts if part)


def load_base_prompt(prompt_path: Path) -> str:
    try:
        return prompt_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return (
            "Sen JARVIS'sin. Windows'ta calisan kisisel AI asistanisin. "
            "Turkce konus, kisa ve net yanit ver, araclari gercekten kullan."
        )
