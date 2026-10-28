# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S V4 — Smart Clipboard Manager
Pano Geçmişi, Hızlı Arama, Otomatik İzleme ve Tek Tıkla Geri Yükleme
"""

import time
import tkinter as tk
from tkinter import messagebox

BG = "#04090c"
PANEL = "#09141c"
CYAN = "#00F0FF"
PINK = "#FF0055"
GOLD = "#FFCC00"
GREEN = "#00FF88"
TEXT = "#D9E7EF"
DIM = "#13313d"


class ClipboardManagerUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S V4 · AKILLI PANO YÖNETİCİSİ (CLIPBOARD)")
        self.root.geometry("680x560")
        self.root.minsize(560, 440)
        self.root.configure(bg=BG)

        self.history = []
        self.last_clip = ""
        self._setup_ui()
        self._poll_clipboard()
        self.root.mainloop()

    def _setup_ui(self):
        hdr = tk.Frame(self.root, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(14, 8))
        tk.Label(hdr, text="📋 J.A.R.V.I.S V4 · PANO GEÇMİŞİ & ASİSTANI",
                 font=("Consolas", 13, "bold"), fg=CYAN, bg=BG).pack(side="left")

        # Arama Çubuğu
        search_box = tk.Frame(self.root, bg=BG)
        search_box.pack(fill="x", padx=16, pady=4)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh_list())
        tk.Label(search_box, text="ARA:", font=("Consolas", 10, "bold"), fg=GOLD, bg=BG).pack(side="left", padx=(0, 6))
        s_entry = tk.Entry(search_box, textvariable=self.search_var, font=("Consolas", 10),
                           bg=PANEL, fg=TEXT, insertbackground=CYAN, relief="flat")
        s_entry.pack(side="left", fill="x", expand=True, ipady=4)

        # Liste
        list_frame = tk.Frame(self.root, bg=PANEL, highlightbackground=DIM, highlightthickness=1)
        list_frame.pack(fill="both", expand=True, padx=16, pady=8)

        self.listbox = tk.Listbox(list_frame, bg="#02080d", fg=TEXT, selectbackground=DIM,
                                  selectforeground=CYAN, font=("Consolas", 10), relief="flat", bd=0)
        self.listbox.pack(fill="both", expand=True, padx=8, pady=8)
        self.listbox.bind("<Double-Button-1>", self._on_item_double_click)

        # Alt Butonlar
        bar = tk.Frame(self.root, bg=BG)
        bar.pack(fill="x", padx=16, pady=(0, 14))

        tk.Button(bar, text="📋 SEÇİLİYİ PANOLARA KOPYALA", command=self._copy_selected,
                  bg="#042e2b", fg=GREEN, font=("Consolas", 10, "bold"), relief="flat", padx=12, pady=6, cursor="hand2").pack(side="left", padx=(0, 8))

        tk.Button(bar, text="🗑️ GEÇMİŞİ TEMİZLE", command=self._clear_history,
                  bg="#2a0810", fg=PINK, font=("Consolas", 10), relief="flat", padx=10, pady=6, cursor="hand2").pack(side="left")

        tk.Label(bar, text="* Çift tıklayarak doğrudan kopyalayabilirsiniz", font=("Consolas", 8), fg="#6b8e99", bg=BG).pack(side="right")

    def _poll_clipboard(self):
        try:
            current = self.root.clipboard_get()
            if current and current.strip() and current != self.last_clip:
                self.last_clip = current
                stamp = time.strftime("%H:%M:%S")
                # Önceden varsa en üste al
                self.history = [item for item in self.history if item["text"] != current]
                self.history.insert(0, {"time": stamp, "text": current})
                if len(self.history) > 40:
                    self.history.pop()
                self._refresh_list()
        except Exception:
            pass
        self.root.after(800, self._poll_clipboard)

    def _refresh_list(self):
        q = self.search_var.get().strip().casefold()
        self.listbox.delete(0, tk.END)
        self.visible_items = [it for it in self.history if q in it["text"].casefold()]
        for it in self.visible_items:
            clean = " ".join(it["text"].split())[:75]
            self.listbox.insert(tk.END, f" [{it['time']}]  {clean}")

    def _copy_selected(self):
        sel = self.listbox.curselection()
        if sel and sel[0] < len(self.visible_items):
            item = self.visible_items[sel[0]]
            self.root.clipboard_clear()
            self.root.clipboard_append(item["text"])
            self.last_clip = item["text"]
            messagebox.showinfo("Başarılı", "Seçilen metin panoya kopyalandı!")

    def _on_item_double_click(self, _event):
        self._copy_selected()

    def _clear_history(self):
        self.history.clear()
        self._refresh_list()


if __name__ == "__main__":
    ClipboardManagerUI()
