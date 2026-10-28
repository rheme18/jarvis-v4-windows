# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S V4 — Quick Tools Hub
QR Kod, Şifre Üretici, Renk Çevirici, JSON Düzenleyici, Hash ve Base64 Araçları
"""

import hashlib
import base64
import json
import random
import string
import tkinter as tk
from tkinter import ttk, messagebox

BG = "#04090c"
PANEL = "#09141c"
CYAN = "#00F0FF"
PINK = "#FF0055"
GOLD = "#FFCC00"
GREEN = "#00FF88"
TEXT = "#D9E7EF"
DIM = "#13313d"


class QuickToolsUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S V4 · HIZLI ARAÇLAR (QUICK TOOLS)")
        self.root.geometry("820x620")
        self.root.minsize(740, 540)
        self.root.configure(bg=BG)

        self._setup_ui()
        self.root.mainloop()

    def _setup_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(14, 8))
        tk.Label(hdr, text="⚡ J.A.R.V.I.S V4 · HIZLI ARAÇLAR & YARDIMCILAR ⚡",
                 font=("Consolas", 14, "bold"), fg=CYAN, bg=BG).pack(side="left")

        # Main Layout: Sol Menü + Sağ İçerik Alanı
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        nav = tk.Frame(body, bg=PANEL, width=200, highlightbackground=DIM, highlightthickness=1)
        nav.pack(side="left", fill="y", padx=(0, 12))
        nav.pack_propagate(False)

        self.content_area = tk.Frame(body, bg=PANEL, highlightbackground=DIM, highlightthickness=1)
        self.content_area.pack(side="right", fill="both", expand=True)

        tabs = [
            ("🔐 ŞİFRE ÜRETİCİ", self._tab_password),
            ("🎨 RENK ÇEVİRİCİ", self._tab_colors),
            ("📦 BASE64 ÇEVİRİCİ", self._tab_base64),
            ("⚙️ HASH HESAPLA", self._tab_hash),
            ("📄 JSON FORMATTER", self._tab_json),
            ("📊 METİN SAYACI", self._tab_word_counter),
        ]

        self.nav_buttons = []
        for name, callback in tabs:
            btn = tk.Button(
                nav, text=name, command=callback, bg=PANEL, fg=TEXT,
                activebackground=DIM, activeforeground=CYAN,
                font=("Consolas", 10, "bold"), relief="flat", anchor="w", padx=12, pady=10, cursor="hand2"
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons.append(btn)

        self._tab_password()

    def _clear_content(self):
        for w in self.content_area.winfo_children():
            w.destroy()

    # ── 1. ŞİFRE ÜRETİCİ ─────────────────────────────────────────────────────
    def _tab_password(self):
        self._clear_content()
        tk.Label(self.content_area, text="GÜVENLİ ŞİFRE & TOKEN ÜRETİCİ", font=("Consolas", 12, "bold"), fg=CYAN, bg=PANEL).pack(anchor="w", padx=16, pady=14)

        opt_frame = tk.Frame(self.content_area, bg=PANEL)
        opt_frame.pack(fill="x", padx=16, pady=6)

        tk.Label(opt_frame, text="Uzunluk:", font=("Consolas", 10), fg=TEXT, bg=PANEL).pack(side="left")
        self.pwd_len = tk.IntVar(value=16)
        len_slider = tk.Scale(opt_frame, from_=6, to=64, orient="horizontal", variable=self.pwd_len,
                              bg=PANEL, fg=TEXT, highlightthickness=0, troughcolor=BG)
        len_slider.pack(side="left", padx=10)

        # Seçenekler
        self.use_upper = tk.BooleanVar(value=True)
        self.use_lower = tk.BooleanVar(value=True)
        self.use_digits = tk.BooleanVar(value=True)
        self.use_symbols = tk.BooleanVar(value=True)

        cb_frame = tk.Frame(self.content_area, bg=PANEL)
        cb_frame.pack(fill="x", padx=16, pady=6)
        for label, var in (("A-Z", self.use_upper), ("a-z", self.use_lower), ("0-9", self.use_digits), ("!@#$", self.use_symbols)):
            tk.Checkbutton(cb_frame, text=label, variable=var, bg=PANEL, fg=CYAN, selectcolor=BG,
                           activebackground=PANEL, activeforeground=CYAN, font=("Consolas", 10)).pack(side="left", padx=8)

        # Üretilen Şifre Kutusu
        self.pwd_res_var = tk.StringVar()
        pwd_entry = tk.Entry(self.content_area, textvariable=self.pwd_res_var, font=("Consolas", 13, "bold"),
                             bg="#02080d", fg=GREEN, insertbackground=CYAN, relief="flat")
        pwd_entry.pack(fill="x", padx=16, pady=14, ipady=8)

        # Butonlar
        btn_bar = tk.Frame(self.content_area, bg=PANEL)
        btn_bar.pack(fill="x", padx=16, pady=6)

        def _generate():
            pool = ""
            if self.use_upper.get(): pool += string.ascii_uppercase
            if self.use_lower.get(): pool += string.ascii_lowercase
            if self.use_digits.get(): pool += string.digits
            if self.use_symbols.get(): pool += "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not pool: pool = string.ascii_letters
            res = "".join(random.choice(pool) for _ in range(self.pwd_len.get()))
            self.pwd_res_var.set(res)

        def _copy():
            text = self.pwd_res_var.get()
            if text:
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                messagebox.showinfo("Kopyalandı", "Şifre panoya kopyalandı!")

        tk.Button(btn_bar, text="⚡ ŞİFRE ÜRET", command=_generate, bg="#042e2b", fg=GREEN,
                  font=("Consolas", 10, "bold"), relief="flat", padx=14, pady=6, cursor="hand2").pack(side="left", padx=(0, 8))
        tk.Button(btn_bar, text="📋 PANOYA KOPYALA", command=_copy, bg=DIM, fg=TEXT,
                  font=("Consolas", 10), relief="flat", padx=14, pady=6, cursor="hand2").pack(side="left")

        _generate()

    # ── 2. RENK ÇEVİRİCİ ─────────────────────────────────────────────────────
    def _tab_colors(self):
        self._clear_content()
        tk.Label(self.content_area, text="HEX ↔ RGB RENK ÇEVİRİCİ & ÖNİZLEME", font=("Consolas", 12, "bold"), fg=CYAN, bg=PANEL).pack(anchor="w", padx=16, pady=14)

        box = tk.Frame(self.content_area, bg=PANEL)
        box.pack(fill="x", padx=16, pady=6)

        tk.Label(box, text="HEX Kodu (Örn: #00F0FF):", font=("Consolas", 10), fg=TEXT, bg=PANEL).pack(anchor="w")
        self.hex_var = tk.StringVar(value="#00F0FF")
        e_hex = tk.Entry(box, textvariable=self.hex_var, font=("Consolas", 11), bg="#02080d", fg=CYAN, relief="flat")
        e_hex.pack(fill="x", pady=4, ipady=6)

        self.color_preview = tk.Canvas(self.content_area, width=120, height=60, bg="#00F0FF", highlightthickness=1, highlightbackground=TEXT)
        self.color_preview.pack(anchor="w", padx=16, pady=10)

        self.rgb_res_lbl = tk.Label(self.content_area, text="RGB: (0, 240, 255)", font=("Consolas", 11, "bold"), fg=GOLD, bg=PANEL)
        self.rgb_res_lbl.pack(anchor="w", padx=16, pady=4)

        def _update_color(*_):
            h = self.hex_var.get().strip()
            if not h.startswith("#"): h = "#" + h
            if len(h) == 7:
                try:
                    r = int(h[1:3], 16)
                    g = int(h[3:5], 16)
                    b = int(h[5:7], 16)
                    self.color_preview.configure(bg=h)
                    self.rgb_res_lbl.configure(text=f"RGB: ({r}, {g}, {b})  |  CSS: rgb({r}, {g}, {b})")
                except ValueError:
                    pass

        self.hex_var.trace_add("write", _update_color)

    # ── 3. BASE64 ────────────────────────────────────────────────────────────
    def _tab_base64(self):
        self._clear_content()
        tk.Label(self.content_area, text="BASE64 METİN KODLAYICI / ÇÖZÜCÜ", font=("Consolas", 12, "bold"), fg=CYAN, bg=PANEL).pack(anchor="w", padx=16, pady=14)

        txt_in = tk.Text(self.content_area, height=8, bg="#02080d", fg=TEXT, font=("Consolas", 10), insertbackground=CYAN)
        txt_in.pack(fill="x", padx=16, pady=4)
        txt_in.insert("1.0", "J.A.R.V.I.S V4 Online")

        btn_box = tk.Frame(self.content_area, bg=PANEL)
        btn_box.pack(fill="x", padx=16, pady=8)

        txt_out = tk.Text(self.content_area, height=8, bg="#02080d", fg=GREEN, font=("Consolas", 10), insertbackground=CYAN)
        txt_out.pack(fill="x", padx=16, pady=4)

        def _encode():
            raw = txt_in.get("1.0", tk.END).strip()
            res = base64.b64encode(raw.encode("utf-8")).decode("utf-8")
            txt_out.delete("1.0", tk.END)
            txt_out.insert("1.0", res)

        def _decode():
            raw = txt_in.get("1.0", tk.END).strip()
            try:
                res = base64.b64decode(raw.encode("utf-8")).decode("utf-8")
                txt_out.delete("1.0", tk.END)
                txt_out.insert("1.0", res)
            except Exception as e:
                messagebox.showerror("Hata", f"Geçersiz Base64: {e}")

        tk.Button(btn_box, text="🔒 ENCODE (Base64'e Çevir)", command=_encode, bg=DIM, fg=CYAN, font=("Consolas", 10), padx=10, pady=4).pack(side="left", padx=(0, 8))
        tk.Button(btn_box, text="🔓 DECODE (Metne Çöz)", command=_decode, bg=DIM, fg=GOLD, font=("Consolas", 10), padx=10, pady=4).pack(side="left")

    # ── 4. HASH HESAPLA ──────────────────────────────────────────────────────
    def _tab_hash(self):
        self._clear_content()
        tk.Label(self.content_area, text="HASH OLUŞTURUCU (MD5 / SHA-256 / SHA-512)", font=("Consolas", 12, "bold"), fg=CYAN, bg=PANEL).pack(anchor="w", padx=16, pady=14)

        tk.Label(self.content_area, text="Girdi Metni:", font=("Consolas", 10), fg=TEXT, bg=PANEL).pack(anchor="w", padx=16)
        in_entry = tk.Entry(self.content_area, font=("Consolas", 11), bg="#02080d", fg=TEXT, relief="flat")
        in_entry.pack(fill="x", padx=16, pady=4, ipady=6)
        in_entry.insert(0, "Jarvis")

        res_box = tk.Frame(self.content_area, bg=PANEL)
        res_box.pack(fill="both", expand=True, padx=16, pady=10)

        hashes = {}
        for algo in ("MD5", "SHA-1", "SHA-256", "SHA-512"):
            tk.Label(res_box, text=f"{algo}:", font=("Consolas", 9, "bold"), fg=CYAN, bg=PANEL).pack(anchor="w", pady=(4, 0))
            e = tk.Entry(res_box, font=("Consolas", 9), bg="#02080d", fg=GREEN, relief="flat")
            e.pack(fill="x", pady=(0, 4), ipady=4)
            hashes[algo] = e

        def _calc(*_):
            txt = in_entry.get().encode("utf-8")
            hashes["MD5"].delete(0, tk.END); hashes["MD5"].insert(0, hashlib.md5(txt).hexdigest())
            hashes["SHA-1"].delete(0, tk.END); hashes["SHA-1"].insert(0, hashlib.sha1(txt).hexdigest())
            hashes["SHA-256"].delete(0, tk.END); hashes["SHA-256"].insert(0, hashlib.sha256(txt).hexdigest())
            hashes["SHA-512"].delete(0, tk.END); hashes["SHA-512"].insert(0, hashlib.sha512(txt).hexdigest())

        in_entry.bind("<KeyRelease>", _calc)
        _calc()

    # ── 5. JSON FORMATTER ────────────────────────────────────────────────────
    def _tab_json(self):
        self._clear_content()
        tk.Label(self.content_area, text="JSON FORMATLAYICI & VALİDATÖR", font=("Consolas", 12, "bold"), fg=CYAN, bg=PANEL).pack(anchor="w", padx=16, pady=14)

        txt = tk.Text(self.content_area, height=18, bg="#02080d", fg=TEXT, font=("Consolas", 10), insertbackground=CYAN)
        txt.pack(fill="both", expand=True, padx=16, pady=4)
        txt.insert("1.0", '{"jarvis": "v4", "modules": ["voice", "arcade", "vision"], "active": true}')

        btn_bar = tk.Frame(self.content_area, bg=PANEL)
        btn_bar.pack(fill="x", padx=16, pady=8)

        def _prettify():
            raw = txt.get("1.0", tk.END).strip()
            try:
                data = json.loads(raw)
                txt.delete("1.0", tk.END)
                txt.insert("1.0", json.dumps(data, indent=2, ensure_ascii=False))
            except Exception as e:
                messagebox.showerror("Geçersiz JSON", str(e))

        def _minify():
            raw = txt.get("1.0", tk.END).strip()
            try:
                data = json.loads(raw)
                txt.delete("1.0", tk.END)
                txt.insert("1.0", json.dumps(data, separators=(',', ':'), ensure_ascii=False))
            except Exception as e:
                messagebox.showerror("Geçersiz JSON", str(e))

        tk.Button(btn_bar, text="✨ FORMATLA (Beautify)", command=_prettify, bg=DIM, fg=GREEN, font=("Consolas", 10), padx=10, pady=4).pack(side="left", padx=(0, 8))
        tk.Button(btn_bar, text="📦 SIKIŞTIR (Minify)", command=_minify, bg=DIM, fg=CYAN, font=("Consolas", 10), padx=10, pady=4).pack(side="left")

    # ── 6. METİN VE KELİME SAYACI ───────────────────────────────────────────
    def _tab_word_counter(self):
        self._clear_content()
        tk.Label(self.content_area, text="CANLI METİN & KARAKTER ANALİZİ", font=("Consolas", 12, "bold"), fg=CYAN, bg=PANEL).pack(anchor="w", padx=16, pady=14)

        lbl_stats = tk.Label(self.content_area, text="Karakter: 0  |  Boşluksuz: 0  |  Kelime: 0  |  Satır: 0",
                             font=("Consolas", 11, "bold"), fg=GOLD, bg=PANEL)
        lbl_stats.pack(anchor="w", padx=16, pady=4)

        txt = tk.Text(self.content_area, height=18, bg="#02080d", fg=TEXT, font=("Consolas", 10), insertbackground=CYAN)
        txt.pack(fill="both", expand=True, padx=16, pady=8)

        def _update(*_):
            content = txt.get("1.0", tk.END).rstrip("\n")
            chars = len(content)
            chars_no_space = len(content.replace(" ", "").replace("\n", "").replace("\t", ""))
            words = len(content.split())
            lines = len(content.splitlines()) if content else 0
            lbl_stats.configure(text=f"Karakter: {chars}  |  Boşluksuz: {chars_no_space}  |  Kelime: {words}  |  Satır: {lines}")

        txt.bind("<KeyRelease>", _update)


if __name__ == "__main__":
    QuickToolsUI()
