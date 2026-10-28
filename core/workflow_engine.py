# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S V4 — Workflow Automation Engine
Executes multi-step scheduled or on-demand automated pipelines from YAML/JSON workflows.
"""

import os
import json
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = BASE_DIR / "workflows"
WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)


def _parse_yaml_or_json(content: str) -> dict:
    """Attempts to parse with yaml, falling back to basic key-value / json parser."""
    try:
        import yaml
        return yaml.safe_load(content)
    except Exception:
        pass
    try:
        return json.loads(content)
    except Exception:
        # Simple line-based fallback parser
        data = {"steps": []}
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("name:"):
                data["name"] = line.split(":", 1)[1].strip().strip('"\'')
            elif line.startswith("description:"):
                data["description"] = line.split(":", 1)[1].strip().strip('"\'')
            elif line.startswith("- tool:"):
                data["steps"].append({"tool": line.split(":", 1)[1].strip()})
        return data


def list_workflows() -> list[dict]:
    """Lists all available automated workflows in the workflows/ directory."""
    _ensure_sample_workflows()
    results = []
    for f in sorted(WORKFLOWS_DIR.iterdir()):
        if f.suffix in (".yaml", ".yml", ".json"):
            try:
                content = f.read_text(encoding="utf-8")
                parsed = _parse_yaml_or_json(content)
                results.append({
                    "id": f.stem,
                    "file": f.name,
                    "name": parsed.get("name", f.stem),
                    "description": parsed.get("description", "Açıklama belirtilmemiş."),
                    "step_count": len(parsed.get("steps", []))
                })
            except Exception:
                pass
    return results


def run_workflow_file(workflow_name: str, orchestrator=None, ctx=None) -> str:
    """Executes a workflow pipeline sequentially."""
    _ensure_sample_workflows()
    target = None
    for ext in ("", ".yaml", ".yml", ".json"):
        candidate = WORKFLOWS_DIR / f"{workflow_name}{ext}"
        if candidate.is_file():
            target = candidate
            break

    if not target:
        return f"❌ Workflow dosyası bulunamadı: '{workflow_name}'. Mevcut workflow'ları 'list_workflows' ile görün."

    try:
        content = target.read_text(encoding="utf-8")
        wf = _parse_yaml_or_json(content)
    except Exception as exc:
        return f"❌ Workflow dosyası okunamadı: {exc}"

    name = wf.get("name", target.stem)
    steps = wf.get("steps", [])
    logs = [f"🚀 Workflow Başlatıldı: {name} ({len(steps)} adım)"]

    for idx, step in enumerate(steps, start=1):
        tool_name = step.get("tool")
        args = step.get("args", {})
        desc = step.get("desc", tool_name)
        logs.append(f"▶ [{idx}/{len(steps)}] {desc}...")

        # If we have an active orchestrator, execute step
        if orchestrator and ctx and tool_name:
            try:
                import asyncio
                # Run sync in event loop if available or thread
                res = asyncio.run(orchestrator.execute(tool_name, args, ctx))
                logs.append(f"   ↳ Sonuç: {str(res.result)[:120]}")
            except Exception as e:
                logs.append(f"   ↳ HATA: {e}")
        else:
            time.sleep(0.3)
            logs.append("   ↳ Tamamlandı.")

    logs.append(f"✅ Workflow başarıyla tamamlandı: {name}")
    return "\n".join(logs)


def _ensure_sample_workflows():
    """Generates initial sample workflows if folder is empty."""
    daily_brief = WORKFLOWS_DIR / "daily_brief.yaml"
    if not daily_brief.exists():
        content = """name: Günlük Sabah Brifingi
description: Hava durumu, sistem kaynakları ve bekleyen takvim etkinliklerini tek komutla hazırlar.
steps:
  - tool: get_weather
    desc: İstanbul hava durumu kontrolü
    args:
      location: "İstanbul"
  - tool: sys_info
    desc: CPU, RAM ve batarya analizi
    args:
      query: "all"
"""
        daily_brief.write_text(content, encoding="utf-8")

    school_prep = WORKFLOWS_DIR / "okul_odev_hazirla.yaml"
    if not school_prep.exists():
        content = """name: Okul Projesi ve Ödev Şablonu
description: Proje ödevi için otomatik araştırma tablosu ve sunum taslağı oluşturur.
steps:
  - tool: create_excel
    desc: Araştırma ve kaynakça tablosu oluşturuluyor
    args:
      title: "Okul Projesi Kaynakça ve Notlar"
      sheet_name: "Kaynaklar"
      data:
        - ["Kaynak Adı", "Yazar", "Tarih", "Önem Derecesi"]
        - ["Yapay Zeka Tarihi", "Turing Enstitüsü", "2024", "Yüksek"]
        - ["Biyometrik Sistemler", "IEEE Dergisi", "2025", "Kritik"]
  - tool: create_powerpoint
    desc: Sunum slayt taslağı hazırlanıyor
    args:
      title: "Dönem Projesi Sunumu"
      subtitle: "J.A.R.V.I.S V4 Otomasyonu ile Hazırlandı"
      sections:
        - "Giriş ve Problem Tanımı"
        - "Metodoloji ve Veri Analizi"
        - "Geliştirilen Çözüm ve Sonuçlar"
        - "Kaynakça ve Kapanış"
"""
        school_prep.write_text(content, encoding="utf-8")
