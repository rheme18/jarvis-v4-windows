#!/usr/bin/env python3
"""
JARVIS Windows — Gelişmiş GUI Otomasyon ve Görsel Kontrol Modülü
Emir Aras Koç tarafından yapılmıştır
"""

import pyautogui
import time
import os
from pathlib import Path

# GÜVENLİK KİLİDİ: Fareyi ekranın sol üst köşesine (0,0) hızla çekersen otomasyon anında çöker ve sistemi kurtarır.
pyautogui.FAILSAFE = True
# İşlemler arası çok hafif insan taklidi boşluğu (hızı stabil tutar)
pyautogui.PAUSE = 0.1

def _focus_window_safe(title: str) -> str:
    """Windows API ile bağımlılıksız pencere öne getirme."""
    try:
        from actions.windows_automation import focus_window_by_title
        res = focus_window_by_title(title)
        if "bulunamadı" not in res.lower():
            return res
    except Exception:
        pass

    try:
        import pywinauto
        app = pywinauto.Application().connect(title_re=f".*{title}.*", timeout=4)
        window = app.top_window()
        if window.is_minimized():
            window.restore()
        window.set_focus()
        return f"'{title}' başlıklı pencere başarıyla yakalandı ve odağa alındı."
    except Exception as exc:
        return f"Pencere odaklanamadı: {exc}"

def handle_gui_action(action, **kwargs):
    """
    Jarvis'in ekran, fare ve klavye üzerindeki tam yetkili manuel kontrol merkezi.
    """
    action = str(action).strip().lower()
    
    try:
        # ──────── 1. TIKLAMA VE FARE HAREKETLERİ ────────
        if action == "click":
            x = kwargs.get("x")
            y = kwargs.get("y")
            clicks = int(kwargs.get("clicks", 1))
            button = str(kwargs.get("button", "left")).lower()
            
            if x is not None and y is not None:
                pyautogui.click(x=int(x), y=int(y), clicks=clicks, button=button)
                return f"Başarıyla ({x}, {y}) koordinatına {clicks} kez {button} tıklandı."
            return "Hata: 'click' aksiyonu için x ve y koordinatları eksik."

        # ──────── 2. GÖRSEL EŞLEŞTİRME (RESMİ GÖRÜP TIKLAMA) ────────
        elif action == "click_image":
            image_name = kwargs.get("image_name")
            confidence = float(kwargs.get("confidence", 0.8)) # Varsayılan %80 benzerlik
            clicks = int(kwargs.get("clicks", 1))
            
            if not image_name:
                return "Hata: 'click_image' için 'image_name' belirtilmedi."
                
            # assets/ klasörünü veya ana dizini kontrol et
            possible_paths = [
                Path("assets") / f"{image_name}.png",
                Path("actions") / "assets" / f"{image_name}.png",
                Path(f"{image_name}.png")
            ]
            
            image_path = None
            for p in possible_paths:
                if p.exists():
                    image_path = str(p)
                    break
                    
            if not image_path:
                return f"Hata: '{image_name}.png' görseli hiçbir assets dizininde bulunamadı patron."
                
            # Ekranda resmi ara (OpenCV bağımlılığı vardır)
            try:
                location = pyautogui.locateOnScreen(image_path, confidence=confidence)
                if location:
                    center_point = pyautogui.center(location)
                    pyautogui.click(center_point.x, center_point.y, clicks=clicks)
                    return f"'{image_name}' görseli ekranda bulundu ve ({center_point.x}, {center_point.y}) noktasına tıklandı."
                else:
                    return f"Görsel bulunamadı: '{image_name}' şu an ekranda görünmüyor veya benzerlik oranı düşük."
            except Exception as cv_err:
                return f"Görsel arama hatası (opencv-python kurulmamış olabilir): {str(cv_err)}"

        # ──────── 3. METİN GİRİŞİ (YAZI YAZMA) ────────
        elif action == "type_text":
            text = kwargs.get("text", "")
            press_enter = bool(kwargs.get("press_enter", False))
            
            if text:
                # interval ile harfler arası bekleme atıp insan gibi yazdırıyoruz patron
                pyautogui.write(text, interval=0.04)
                if press_enter:
                    pyautogui.press("enter")
                    return f"'{text}' metni yazıldı ve Enter tuşuna basıldı."
                return f"'{text}' metni başarıyla yazıldı."
            return "Hata: 'type_text' için 'text' parametresi boş."

        # ──────── 4. KISAYOL TUŞ KOMBİNASYONU (HOTKEY) ────────
        elif action == "hotkey":
            keys = kwargs.get("keys", []) # Örn: ["ctrl", "alt", "t"] veya ["win", "d"]
            if keys:
                # Listeyi unzip edip hotkey'e pasla
                pyautogui.hotkey(*keys)
                return f"{keys} tuş kombinasyonu başarıyla yürütüldü."
            return "Hata: 'hotkey' için tuş listesi ('keys') belirtilmedi."

        # ──────── 5. EKRAN KAYDIRMA (SCROLL) ────────
        elif action == "scroll":
            clicks = int(kwargs.get("clicks", 3)) # Pozitif yukarı, negatif aşağı kaydırır
            pyautogui.scroll(clicks * 100)
            direction = "yukarı" if clicks > 0 else "aşağı"
            return f"Ekran {abs(clicks)} birim {direction} kaydırıldı."

        # ──────── 6. PENCERE ODAKLAMA ────────
        elif action == "focus_window":
            title = kwargs.get("title", "")
            if title:
                return _focus_window_safe(title)
            return "Hata: 'focus_window' için pencere başlığı ('title') eksik."

        return f"Hata: '{action}' adında bir GUI aksiyonu tanımlanmamış."

    except Exception as e:
        return f"GUI Kritik Modül Hatası Kök Nedeni: {str(e)}"
