# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S V4 — Otomatik Kişisel Profilleyici & Hafıza Grafiği
Sohbet esnasında kullanıcının zevklerini, tercihlerini, planlarını ve alışkanlıklarını
otomatik olarak öğrenip sessizce kaydeden uzun vadeli bellek mekanizması.
"""

import json
import re
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
FACTS_FILE = BASE_DIR / "memory" / "user_facts.json"


class UserProfiler:
    def __init__(self):
        self.facts = self.load_facts()

    def load_facts(self) -> list:
        if FACTS_FILE.exists():
            try:
                data = json.loads(FACTS_FILE.read_text(encoding="utf-8"))
                return data if isinstance(data, list) else []
            except Exception:
                return []
        return []

    def save_facts(self):
        try:
            FACTS_FILE.parent.mkdir(parents=True, exist_ok=True)
            FACTS_FILE.write_text(json.dumps(self.facts, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def analyze_user_text(self, text: str):
        """Kullanıcının cümlesinde kalıcı bir bilgi/tercih var mı tespit eder."""
        txt = str(text or "").strip()
        if len(txt) < 8:
            return

        patterns = [
            (r"(?:benim|ben)\s+(?:adım|ismim)\s+([A-Za-zÇĞİÖŞÜçğiöşü\s]+)", "İsim"),
            (r"(?:en çok|genelde|asla)?\s*(.+?)\s+(?:severim|hoşlanırım|tercih ederim)", "Tercih/Sevilen"),
            (r"(.+?)\s+(?:sevmem|nefret ederim|istemem)", "Sevilmeyen"),
            (r"(?:yarın|gelecek hafta|pazartesi|salı|çarşamba|perşembe|cuma|cumartesi|pazar)\s+(.+?)\s+(?:var|yapacağım|gideceğim)", "Gelecek Planı"),
            (r"(?:çalışıyorum|öğrenciyim|mesleğim)\s+(.+)", "Meslek/Uğraş"),
        ]

        for pat, category in patterns:
            m = re.search(pat, txt, re.IGNORECASE)
            if m:
                fact_str = txt.rstrip(".!?")
                # Zaten kayıtlı mı kontrol et
                existing = [f["fact"] for f in self.facts]
                if fact_str not in existing:
                    stamp = time.strftime("%Y-%m-%d %H:%M")
                    self.facts.append({
                        "category": category,
                        "fact": fact_str,
                        "timestamp": stamp
                    })
                    self.save_facts()
                    # Vektör hafızaya da indeksle
                    try:
                        from memory.vector_memory import _vector_store
                        _vector_store.add_memory("user_profile", fact_str, {"category": category})
                    except Exception:
                        pass
                    print(f"[JARVIS Profiler] 💡 Yeni kullanıcı gerçeği öğrenildi: [{category}] {fact_str}")
                    break

    def get_facts_summary(self, limit: int = 5) -> str:
        """Prompt enjeksiyonu için bilinen gerçekleri döndürür."""
        if not self.facts:
            return ""
        lines = ["[PATRON HAKKINDA BİLİNEN ÖZEL BİLGİLER & TERCİHLER]"]
        for f in self.facts[-limit:]:
            lines.append(f"• {f['fact']}")
        return "\n".join(lines)


_profiler_instance = None

def get_user_profiler():
    global _profiler_instance
    if _profiler_instance is None:
        _profiler_instance = UserProfiler()
    return _profiler_instance
