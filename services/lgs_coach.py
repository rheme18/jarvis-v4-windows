import json
import os
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "lgs_report.json"

# LGS Soru Sayıları Standartları
LGS_STRUCTURE = {
    "Turkce": 20,
    "Matematik": 20,
    "Fen": 20,
    "Inkilap": 10,
    "Din": 10,
    "Ingilizce": 10
}

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_safe_ascii=False, indent=4)

def add_exam_result(exam_name: str, results: dict) -> str:
    """
    results formatı: 
    {
       "Turkce": {"dogru": 18, "yanlis": 2, "bos_konu": "Paragrafta Anlam"},
       "Matematik": {"dogru": 15, "yanlis": 4, "bos_konu": "Köklü İfadeler"}
       ...
    }
    """
    data = load_data()
    
    # Yeni deneme kaydı oluşturma
    entry = {"exam_name": exam_name, "scores": {}}
    toplam_net = 0
    
    for ders, limit in LGS_STRUCTURE.items():
        res = results.get(ders, {"dogru": 0, "yanlis": 0, "bos_konu": "Yok"})
        dogru = int(res.get("dogru", 0))
        yanlis = int(res.get("yanlis", 0))
        bos_konu = res.get("bos_konu", "Yok")
        
        # Mantıksal Doğruluk Kontrolü
        if dogru + yanlis > limit:
            return f"Hata: {ders} dersi için girdiğin doğru ve yanlış toplamı ({dogru+yanlis}), LGS limiti olan {limit} değerini aşamaz patron!"
            
        net = dogru - (yanlis / 3)
        toplam_net += net
        
        entry["scores"][ders] = {
            "dogru": dogru,
            "yanlis": yanlis,
            "net": round(net, 2),
            "kritik_konu": bos_konu
        }
        
    entry["toplam_net"] = round(toplam_net, 2)
    data.append(entry)
    save_data(data)
    
    # Anlık analiz üretimi
    return generate_feedback(entry, data)

def generate_feedback(current_exam: dict, all_data: list) -> str:
    """Mühendislik ve öğretmen bakış açısıyla öğrenciye özel taktiksel geri bildirim üretir."""
    feedback = f"🎯 **{current_exam['exam_name']} Sonuçları Sisteme İşlendi, Patron!**\n"
    feedback += f"📊 **Bu Denemedeki Toplam Netin:** {current_exam['toplam_net']} / 90.00\n\n"
    
    df_list = []
    for exam in all_data:
        row = {"exam_name": exam["exam_name"], "toplam_net": exam["toplam_net"]}
        for ders in LGS_STRUCTURE.keys():
            row[f"{ders}_net"] = exam["scores"][ders]["net"]
        df_list.append(row)
        
    df = pd.DataFrame(df_list)
    
    feedback += "🔍 **Ders Bazlı Kritik Odak Noktaları:**\n"
    alarm_konular = []
    
    for ders in LGS_STRUCTURE.keys():
        current_score = current_exam["scores"][ders]
        feedback += f"- **{ders}:** {current_score['dogru']}D {current_score['yanlis']}Y ({current_score['net']} Net) "
        
        if current_score['yanlis'] > 0 and current_score['kritik_konu'] != "Yok":
            alarm_konular.append(f"{ders} -> {current_score['kritik_konu']}")
            feedback += f"⚠️ *Zayıf Halka: {current_score['kritik_konu']}*\n"
        else:
            feedback += "✅ *Harika!*\n"
            
    # Gelişim/Performans Trend Analizi (Uzun Vadeli Değerlendirme)
    if len(df) > 1:
        feedback += "\n📈 **Genel Trend Analizi:**\n"
        previous_net = df.iloc[-2]["toplam_net"]
        diff = current_exam["toplam_net"] - previous_net
        
        if diff > 0:
            feedback += f"🚀 Muazzam! Bir önceki denemeye göre netini **{round(diff, 2)}** artırmışsın. Performansın yükseliyor, aynen devam!\n"
        elif diff < 0:
            feedback += f"📉 Patron bu denemede bir önceki maça göre **{round(abs(diff), 2)}** net kaybımız var. Moral bozmak yok, eksikleri kapatacağız.\n"
        else:
            feedback += "📊 Netlerin bir önceki denemeyle tamamen stabil kalmış. Sıçrama yapmak için vites artırmalıyız.\n"
            
    # Stratejik Tavsiye (Kök Neden Analizi)
    if alarm_konular:
        feedback += "\n🛠️ **JARVIS Stratejik Eylem Planı:**\n"
        feedback += "Bir sonraki çalışma seanslarında öncelikli olarak şu konuların üzerine gitmeliyiz:\n"
        for alarm in alarm_konular[:2]: # En kritik 2 konuyu öne çıkar
            feedback += f"👉 *{alarm}* konusundan hap özetler oku ve soru çözümü izle.\n"
            
    return feedback

def get_lgs_summary() -> str:
    """Tüm denemelerin genel özetini ve gelişim grafiği metnini getirir."""
    data = load_data()
    if not data:
        return "Henüz sisteme kayıtlı LGS deneme sınavı bulamadım patron. İlk denemeni ekleyerek başlayabiliriz!"
        
    df_list = []
    for exam in data:
        df_list.append({"Deneme": exam["exam_name"], "Net": exam["toplam_net"]})
    df = pd.DataFrame(df_list)
    
    summary = "📉 **LGS Genel Başarı Tablon:**\n```\n"
    summary += df.to_string(index=False)
    summary += "\n```\n"
    summary += f"🏆 **En Yüksek Netin:** {df['Net'].max()}\n"
    summary += f"🎯 **Ortalama Netin:** {round(df['Net'].mean(), 2)}\n"
    return summary