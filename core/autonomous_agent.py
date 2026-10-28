"""
JARVIS V4 Windows — Otonom Görev Yürütücü (Autonomous Task Agent)
Kullanıcının karmaşık çok adımlı hedeflerini planlar, araçları sırayla yürütür,
sonuçları değerlendirir ve kapsamlı bir özet rapor sunar.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from google import genai
from core.error_boundary import log_root_cause

BASE_DIR = Path(__file__).resolve().parent.parent


def _get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        try:
            from app_config import get_app_config_value
            api_key = str(get_app_config_value("gemini_api_key", "") or "")
        except Exception:
            pass
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


class AutonomousTaskExecutor:
    def __init__(self, orchestrator: Any = None, max_steps: int = 7):
        self.orchestrator = orchestrator
        self.max_steps = max_steps

    async def execute_goal(self, goal: str, context: Optional[str] = None) -> str:
        """
        Kullanıcının hedefini planlar ve otonom olarak adım adım yürütür.
        """
        if not goal or not goal.strip():
            return "Hata: Yürütülecek otonom görev hedefi belirtilmedi Patron."

        client = _get_gemini_client()
        if not client:
            return "Hata: Gemini API istemcisi başlatılamadı. API anahtarınızı kontrol edin."

        print(f"[AUTONOMOUS AGENT] 🎯 Hedef başlatıldı: '{goal}'")
        
        # 1. Aşama: Adım Planlaması
        planning_prompt = f"""Sen JARVIS'in Otonom Görev Planlayıcısısın.
Kullanıcının şu hedefini incele ve bunu sırayla çalıştırılabilecek mantıklı 2 ila {self.max_steps} adıma böl.

HEDEF: {goal}
EK BAĞLAM: {context or 'Yok'}

KULLANILABİLİR ARAÇLAR:
- windows_automation: (action='list_windows'|'set_volume'|'get_volume'|'set_brightness'|'toast'|'power_status')
- sys_info: (query='cpu'|'memory'|'disk'|'all')
- manage_file: (action='write'|'read'|'list_dir'|'search', filename='...', content='...')
- get_weather: (location='...')
- browser_control: (action='search'|'open_url', query='...', url='...')
- db_save: (category='note'|'journal', content='...', title='...')
- db_search: (query='...')
- semantic_memory_search: (query='...')
- scan_network: ()
- check_security: ()

Yanıtını SADECE geçerli bir JSON dizisi olarak ver. Örnek:
[
  {{"step": 1, "tool": "sys_info", "args": {{"query": "all"}}, "reason": "Sistem durumunu al"}},
  {{"step": 2, "tool": "manage_file", "args": {{"action": "write", "filename": "sistem_raporu.txt", "content": "..."}}, "reason": "Raporu dosyaya kaydet"}}
]
"""
        try:
            plan_response = await asyncio.to_thread(
                lambda: client.models.generate_content(
                    model="models/gemini-2.5-flash",
                    contents=planning_prompt
                )
            )
            raw_plan = plan_response.text.strip()
            # JSON bloğunu ayıkla
            if "```json" in raw_plan:
                raw_plan = raw_plan.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_plan:
                raw_plan = raw_plan.split("```")[1].split("```")[0].strip()
            
            steps = json.loads(raw_plan)
            if not isinstance(steps, list) or not steps:
                return f"Görev planı oluşturulamadı: {raw_plan[:200]}"

        except Exception as exc:
            log_root_cause("autonomous", "Planlama hatası", exc)
            return f"Otonom görev planlaması başarısız: {exc}"

        # 2. Aşama: Adımların Sırayla Yürütülmesi
        from core.tool_orchestrator import ToolContext, ToolOrchestrator
        from tool_defs import PLUGIN_REGISTRY
        
        orch = self.orchestrator or ToolOrchestrator(PLUGIN_REGISTRY)
        ctx = ToolContext(base_dir=BASE_DIR)

        step_logs = []
        for item in steps[:self.max_steps]:
            s_num = item.get("step", len(step_logs) + 1)
            t_name = item.get("tool", "")
            t_args = item.get("args", {})
            reason = item.get("reason", "")

            print(f"[AUTONOMOUS AGENT] ▶️ Adım {s_num}: {t_name} ({reason})")
            exec_res = await orch.execute(t_name, t_args, ctx)
            step_logs.append({
                "step": s_num,
                "tool": t_name,
                "reason": reason,
                "status": exec_res.status,
                "result": exec_res.result[:500],
            })

            if exec_res.status == "approval_required":
                return f"Otonom görev '{t_name}' adımında durduruldu: Kullanıcı onayı gerekiyor (ID: {exec_res.result})."

        # 3. Aşama: Nihai Sonuç Özeti ve Sentezi
        summary_prompt = f"""Aşağıdaki otonom görev yürütme adımlarını incele ve kullanıcıya şık, profesyonel bir J.A.R.V.I.S. görev tamamlama raporu hazırla.

ANA HEDEF: {goal}
YÜRÜTÜLEN ADIMLAR VE SONUÇLAR:
{json.dumps(step_logs, ensure_ascii=False, indent=2)}

Kısa, net ve Türkçe yanıt ver."""

        try:
            final_res = await asyncio.to_thread(
                lambda: client.models.generate_content(
                    model="models/gemini-2.5-flash",
                    contents=summary_prompt
                )
            )
            return final_res.text.strip()
        except Exception:
            # Fallback format
            out = [f"✅ OTONOM GÖREV TAMAMLANDI: '{goal}'\n"]
            for s in step_logs:
                out.append(f"• Adım {s['step']} ({s['tool']}): {s['result'][:120]}")
            return "\n".join(out)


_default_executor = AutonomousTaskExecutor()


async def run_autonomous_task(goal: str, context: str = "") -> str:
    """Otonom görev yürütücüsünü çalıştırır."""
    return await _default_executor.execute_goal(goal, context)
