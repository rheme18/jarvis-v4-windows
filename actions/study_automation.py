# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S V4 — School, Study & Homework Automation Suite
- WhatsApp ve Mesaj ödev tarayıcısı: "Grupta ödev paylaşmışlar mı?" analizi
- Otomatik Ödev ve Proje Üreticisi (Word, Excel, PPTX, PDF)
- Akıllı Sınav ve Çalışma Planlayıcısı (Spaced Repetition & Pomodoro)
- Tarayıcısız E-Posta Okuma ve Yanıt Taslağı Hazırlama
"""

import os
import re
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = Path(os.path.expanduser(r"~\Desktop"))
HOMEWORK_DB = BASE_DIR / "memory" / "homework_tracker.json"
HOMEWORK_DB.parent.mkdir(parents=True, exist_ok=True)


def _load_homework_db() -> dict:
    if HOMEWORK_DB.exists():
        try:
            return json.loads(HOMEWORK_DB.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"tasks": [], "last_scan": None, "archived": []}


def _save_homework_db(data: dict):
    try:
        HOMEWORK_DB.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def scan_messages_for_homework(message_text: str = "", source: str = "WhatsApp / Mail") -> str:
    """
    Mesaj veya grup sohbeti metnini analiz ederek ödev, proje ve sınav duyurularını otomatik ayıklar.
    """
    if not message_text.strip():
        # Veritabanındaki mevcut ödevleri listele
        db = _load_homework_db()
        active = [t for t in db.get("tasks", []) if not t.get("completed", False)]
        if not active:
            return "📋 Şu anda kayıtlı veya tespit edilmiş bekleyen bir ödev bulunmuyor Patron."
        
        lines = [f"📚 AKTİF ÖDEVLER VE PROJELER ({len(active)} Adet):"]
        for idx, t in enumerate(active, 1):
            deadline = t.get("deadline", "Belirtilmedi")
            lines.append(f"{idx}. 📌 [{t.get('course', 'Genel')}] {t.get('title')}")
            lines.append(f"   ⏳ Teslim: {deadline} | Kaynak: {t.get('source', 'Sistem')}")
            if t.get("details"):
                lines.append(f"   📝 Detay: {t.get('details')}")
        return "\n".join(lines)

    # Doğal dil metninden ödevleri ayıkla
    db = _load_homework_db()
    lines = message_text.split("\n")
    found_count = 0
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")

    # Basit anahtar kelime ve pattern taraması
    keywords = ["ödev", "odev", "proje", "teslim", "sayfa", "soru", "sunum", "sınav", "sinav", "quiz"]
    detected_items = []

    for l in lines:
        line_clean = l.strip()
        if not line_clean:
            continue
        low = line_clean.lower()
        if any(k in low for k in keywords):
            # Ders tespiti
            course = "Genel"
            for c_name in ["Matematik", "Fizik", "Kimya", "Biyoloji", "Tarih", "Edebiyat", "İngilizce", "Geometri", "Bilgisayar", "Yazılım"]:
                if c_name.lower() in low:
                    course = c_name
                    break

            # Tarih tespiti
            deadline = "Yakın zamanda"
            days = ["pazartesi", "salı", "çarşamba", "perşembe", "cuma", "cumartesi", "pazar", "haftaya", "yarın"]
            for d in days:
                if d in low:
                    deadline = d.capitalize()
                    break

            task_obj = {
                "id": int(time.time() * 1000) + found_count,
                "course": course,
                "title": line_clean[:90],
                "details": line_clean,
                "deadline": deadline,
                "source": source,
                "created_at": now_str,
                "completed": False
            }
            db["tasks"].append(task_obj)
            detected_items.append(task_obj)
            found_count += 1

    db["last_scan"] = now_str
    _save_homework_db(db)

    if found_count == 0:
        return "🔍 İncelenen mesajlarda yeni bir ödev veya proje uyarısı bulunamadı Patron."

    res = [f"✅ Grup mesajlarından {found_count} adet yeni ödev/görev çıkarıldı ve takip listesine eklendi:"]
    for item in detected_items:
        res.append(f"• 📌 [{item['course']}] {item['title']} (Teslim: {item['deadline']})")
    return "\n".join(res)


def create_full_homework_package(topic: str, course: str = "Genel", doc_type: str = "all") -> str:
    """
    Belirtilen konu için eksiksiz ödev paketi oluşturur (Word dokümanı, Sunum veya Rapor).
    """
    results = []
    clean_topic = topic.replace(" ", "_").strip()
    
    # 1. Word Raporu Oluştur
    if doc_type in ("all", "word", "docx"):
        from actions.skill_executor import create_docx_from_skill
        word_content = f"""# {topic.upper()} - ARAŞTIRMA VE ÖDEV RAPORU

## 1. Giriş ve Konunun Önemi
Bu çalışma, {topic} konusunun temel kavramlarını, tarihsel gelişimini ve modern bilimdeki yerini incelemek amacıyla hazırlanmıştır.

## 2. Temel Kavramlar ve Kuramsal Altyapı
- **Tanım ve Kapsam:** {topic} alanının temel dinamikleri ve literatürdeki yeri.
- **Kritik İlkeler:** Konuyu şekillendiren temel faktörler ve hipotezler.
- **Uygulama Alanları:** Günümüz teknolojisinde ve bilimsel araştırmalardaki karşılığı.

## 3. Bulgular ve Analiz
Konu üzerinde yapılan detaylı incelemeler ve akademik referanslar, bu alanın gelecekte daha büyük inovasyonlara zemin hazırlayacağını göstermektedir.

## 4. Sonuç ve Değerlendirme
Elde edilen bulgular doğrultusunda {topic} konusunun hem teorik hem de pratik yönden kritik öneme sahip olduğu tespit edilmiştir.

### Kaynakça
1. Akademik Araştırmalar Veritabanı (2024).
2. Temel Bilimler ve İnovasyon Enstitüsü Yayınları.
3. J.A.R.V.I.S V4 Bilişsel Veri Tabanı.
"""
        w_res = create_docx_from_skill(f"{topic} Ödevi", word_content, f"{clean_topic}_Odevi.docx")
        results.append(w_res)

    # 2. PowerPoint Sunumu Oluştur
    if doc_type in ("all", "pptx", "presentation"):
        from actions.skill_executor import create_pptx_from_skill
        slides = [
            {"title": "Giriş ve Genel Bakış", "points": [f"{topic} kavramının ortaya çıkışı", "Çalışmanın temel amacı ve hedefleri", "Konunun güncel önemi"]},
            {"title": "Temel Prensipler", "points": ["Anahtar formüller ve kurallar", "Sistemik işleyiş mekanizması", "Örnek vakalar ve durum analizleri"]},
            {"title": "Gelecek Perspektifi & Sonuç", "points": ["Teknolojik entegrasyon fırsatları", "Araştırma sonuçlarının özeti", "Soru ve Cevap oturumu"]}
        ]
        p_res = create_pptx_from_skill(topic, slides, subtitle=f"{course} Dersi Ödev Sunumu", output_name=f"{clean_topic}_Sunumu.pptx")
        results.append(p_res)

    return "\n\n".join(results)


def generate_study_plan(exam_name: str, available_hours_daily: float = 3.0) -> str:
    """
    Spaced repetition ve Pomodoro tekniği ile optimize edilmiş çalışma planı oluşturur.
    """
    days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    plan = [
        f"🎯 {exam_name.upper()} İÇİN HAFTALIK OPTİMİZE ÇALIŞMA PLANI",
        f"⏱️ Günlük Hedef: {available_hours_daily} Saat (4 x 40 dk Pomodoro + 10 dk Mola)",
        "────────────────────────────────────────────────"
    ]
    
    stages = [
        ("Konu Anlatımı & Zihin Haritası Çıkarma", "40 dk Odak"),
        ("Soru Çözümü & Zorlu Örnekler", "40 dk Odak"),
        ("Hatalı Soruların Analizi (Active Recall)", "40 dk Odak"),
        ("Spaced Repetition & Günlük Tekrar", "30 dk Hafıza Pekiştirme")
    ]

    for d in days:
        plan.append(f"\n📅 {d}:")
        for s_idx, (stage, duration) in enumerate(stages, 1):
            plan.append(f"   [{s_idx}] {stage} ➔ {duration}")

    plan.append("\n💡 JARVIS Tavsiyesi: Her 2 bloktan sonra 15 dakika ekran molası verin Patron.")
    return "\n".join(plan)
