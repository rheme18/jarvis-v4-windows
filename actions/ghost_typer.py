# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S V4 — Ghost Typer Engine (Hayalet Yazıcı)
Aktif penceredeki imlecin olduğu yere (Notepad, Word, Discord, Browser, IDE vb.)
Türkçe karakterleri bozmadan akıcı bir şekilde doğrudan metin yazar.
"""

import time
import threading
import tkinter as tk
from tkinter import messagebox
import pyautogui

try:
    import pyperclip
except ImportError:
    pyperclip = None


def ghost_type_text(text: str, delay_start: float = 0.5, speed_mode: str = "smooth") -> str:
    """
    Hedef pencereye odaklanıp metni imlecin olduğu yere yazar.
    speed_mode: 'instant' (panoyla yapıştır) veya 'smooth' (daktilo gibi harf harf akıt)
    """
    clean_text = str(text or "").strip()
    if not clean_text:
        return "Yazılacak metin bulunamadı Patron."

    # Kullanıcının önceki pencereye geçmesi için kısa bekleme
    if delay_start > 0:
        time.sleep(delay_start)

    try:
        # Türkçe özel karakterler (ç, ğ, ı, ö, ş, ü, İ vb.) için panolu güvenli simülasyon
        if speed_mode == "instant" or len(clean_text) > 120 or pyperclip is not None:
            if pyperclip:
                old_clipboard = pyperclip.paste()
                pyperclip.copy(clean_text)
                pyautogui.hotkey("ctrl", "v")
                time.sleep(0.1)
                try:
                    pyperclip.copy(old_clipboard)
                except Exception:
                    pass
                return f"Metin hedef pencereye anında yazıldı Patron ({len(clean_text)} karakter)."

        # Harf harf daktilo modu
        for char in clean_text:
            try:
                pyautogui.write(char)
            except Exception:
                # Özel karakterse panoyla yapıştır
                if pyperclip:
                    pyperclip.copy(char)
                    pyautogui.hotkey("ctrl", "v")
            time.sleep(0.015)

        return f"Metin başarıyla yazıldı Patron ({len(clean_text)} karakter)."

    except Exception as exc:
        return f"Hayalet yazıcı hatası: {exc}"


class GhostTyperPopup:
    """Kısayolla açılan modern siber hayalet yazıcı paneli."""

    def __init__(self, callback_type_func=None):
        self.root = tk.Toplevel()
        self.root.title("J.A.R.V.I.S · GHOST TYPER")
        self.root.geometry("520x340")
        self.root.configure(bg="#050a0f")
        self.root.attributes("-topmost", True)

        tk.Label(self.root, text="⌨️ J.A.R.V.I.S GHOST TYPER (HAYALET YAZICI)",
                 font=("Consolas", 12, "bold"), fg="#00f0ff", bg="#050a0f").pack(pady=(12, 6))

        tk.Label(self.root, text="Yazılmasını istediğiniz metni girin veya bir şablon seçin.\n'Yazdır' butonuna bastıktan 1 saniye sonra aktif pencereye yazılır.",
                 font=("Consolas", 9), fg="#7a9ba6", bg="#050a0f", justify="center").pack(pady=(0, 8))

        self.txt = tk.Text(self.root, height=7, bg="#02060a", fg="#7dfff6",
                           insertbackground="#00f0ff", font=("Consolas", 10), bd=1, relief="solid")
        self.txt.pack(fill="both", expand=True, padx=16, pady=6)
        self.txt.focus_set()

        btn_bar = tk.Frame(self.root, bg="#050a0f")
        btn_bar.pack(fill="x", padx=16, pady=(4, 14))

        tk.Button(btn_bar, text="⚡ İMLECE YAZDIR", command=self._start_typing,
                  bg="#042e2b", fg="#00ff88", font=("Consolas", 10, "bold"), padx=14, pady=6, relief="flat", cursor="hand2").pack(side="left")

        tk.Button(btn_bar, text="KAPAT", command=self.root.destroy,
                  bg="#2a0810", fg="#ff3344", font=("Consolas", 10), padx=12, pady=6, relief="flat", cursor="hand2").pack(side="right")

    def _start_typing(self):
        text = self.txt.get("1.0", tk.END).strip()
        if not text:
            return
        self.root.withdraw()
        # 0.8 saniye sonra yazmaya başla (kullanıcı önceki pencereye odaklansın)
        threading.Thread(target=lambda: (ghost_type_text(text, delay_start=0.8), self.root.destroy()), daemon=True).start()


if __name__ == "__main__":
    print(ghost_type_text("JARVIS V4 Ghost Typer Testi: Başarılı!", delay_start=0))
