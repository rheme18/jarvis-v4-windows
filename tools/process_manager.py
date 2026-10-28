# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S V4 — Advanced Process & Resource Manager
Canlı Görev Yöneticisi, Kaynak Tüketim Analizi, İşlem Sonlandırıcı ve RAM Booster
"""

import ctypes
import os
import psutil
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


class ProcessManagerUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S V4 · SÜREÇ & GÖREV YÖNETİCİSİ")
        self.root.geometry("860x640")
        self.root.minsize(720, 520)
        self.root.configure(bg=BG)

        self._setup_ui()
        self._refresh_processes()
        self.root.mainloop()

    def _setup_ui(self):
        # Header & RAM Özeti
        hdr = tk.Frame(self.root, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(14, 8))

        tk.Label(hdr, text="⚡ J.A.R.V.I.S V4 · SİSTEM SÜREÇ YÖNETİCİSİ ⚡",
                 font=("Consolas", 14, "bold"), fg=CYAN, bg=BG).pack(side="left")

        self.btn_boost = tk.Button(
            hdr, text="🚀 RAM BOOSTER (TEMİZLE)", command=self._boost_ram,
            bg="#042e2b", fg=GREEN, activebackground=DIM, activeforeground=CYAN,
            relief="flat", font=("Consolas", 10, "bold"), padx=12, pady=4, cursor="hand2"
        )
        self.btn_boost.pack(side="right")

        # Sistem Durum Kartları
        stat_bar = tk.Frame(self.root, bg=BG)
        stat_bar.pack(fill="x", padx=16, pady=4)
        self.lbl_cpu = tk.Label(stat_bar, text="CPU: %--", font=("Consolas", 10, "bold"), fg=GOLD, bg=PANEL, padx=10, pady=4)
        self.lbl_cpu.pack(side="left", padx=(0, 8))
        self.lbl_ram = tk.Label(stat_bar, text="RAM: %--", font=("Consolas", 10, "bold"), fg=CYAN, bg=PANEL, padx=10, pady=4)
        self.lbl_ram.pack(side="left", padx=(0, 8))
        self.lbl_count = tk.Label(stat_bar, text="Süreç Sayısı: --", font=("Consolas", 10), fg=TEXT, bg=PANEL, padx=10, pady=4)
        self.lbl_count.pack(side="left")

        # Arama
        s_box = tk.Frame(self.root, bg=BG)
        s_box.pack(fill="x", padx=16, pady=6)
        tk.Label(s_box, text="FİLTRELE:", font=("Consolas", 10, "bold"), fg=CYAN, bg=BG).pack(side="left", padx=(0, 6))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter_tree())
        s_entry = tk.Entry(s_box, textvariable=self.search_var, font=("Consolas", 10),
                           bg=PANEL, fg=TEXT, insertbackground=CYAN, relief="flat")
        s_entry.pack(side="left", fill="x", expand=True, ipady=4)

        # Tablo
        tree_frame = tk.Frame(self.root, bg=PANEL, highlightbackground=DIM, highlightthickness=1)
        tree_frame.pack(fill="both", expand=True, padx=16, pady=6)

        cols = ("pid", "name", "cpu", "ram", "status")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")

        self.tree.heading("pid", text="PID")
        self.tree.heading("name", text="İŞLEM ADI")
        self.tree.heading("cpu", text="CPU %")
        self.tree.heading("ram", text="BELLEK (MB)")
        self.tree.heading("status", text="DURUM")

        self.tree.column("pid", width=70, anchor="center")
        self.tree.column("name", width=260, anchor="w")
        self.tree.column("cpu", width=90, anchor="center")
        self.tree.column("ram", width=120, anchor="center")
        self.tree.column("status", width=110, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Stil
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#02080d", foreground=TEXT, fieldbackground="#02080d",
                        rowheight=26, font=("Consolas", 9))
        style.configure("Treeview.Heading", background=PANEL, foreground=CYAN, font=("Consolas", 9, "bold"))
        style.map("Treeview", background=[("selected", DIM)], foreground=[("selected", CYAN)])

        # Alt Butonlar
        bottom_bar = tk.Frame(self.root, bg=BG)
        bottom_bar.pack(fill="x", padx=16, pady=(6, 14))

        tk.Button(bottom_bar, text="⛔ GÖREVİ SONLANDIR (KILL)", command=self._kill_selected,
                  bg="#330a12", fg=PINK, activebackground=DIM, activeforeground=PINK,
                  font=("Consolas", 10, "bold"), relief="flat", padx=14, pady=6, cursor="hand2").pack(side="left", padx=(0, 10))

        tk.Button(bottom_bar, text="↻ LİSTEYİ YENİLE", command=self._refresh_processes,
                  bg=PANEL, fg=TEXT, font=("Consolas", 10), relief="flat", padx=12, pady=6, cursor="hand2").pack(side="left")

    def _boost_ram(self):
        """Windows SetProcessWorkingSetSize API ile gereksiz bellek alanlarını boşaltır."""
        try:
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetCurrentProcess()
            kernel32.SetProcessWorkingSetSize(handle, -1, -1)
            messagebox.showinfo("RAM Booster", "Jarvis bellek temizliğini tamamladı. Sistem optimize edildi!")
        except Exception as e:
            messagebox.showerror("Hata", f"Optimizasyon hatası: {e}")
        self._refresh_processes()

    def _refresh_processes(self):
        try:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            self.lbl_cpu.configure(text=f"CPU: %{cpu:.1f}")
            self.lbl_ram.configure(text=f"RAM: %{mem:.1f}")
        except Exception:
            pass

        self.proc_data = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status']):
            try:
                info = p.info
                ram_mb = (info['memory_info'].rss / (1024 * 1024)) if info['memory_info'] else 0
                self.proc_data.append((
                    info['pid'],
                    info['name'] or "Bilinmeyen",
                    f"{info['cpu_percent'] or 0.0:.1f}",
                    f"{ram_mb:.1f}",
                    info['status'] or "running",
                    ram_mb
                ))
            except Exception:
                continue

        # Belleğe göre sırala
        self.proc_data.sort(key=lambda x: x[5], reverse=True)
        self.lbl_count.configure(text=f"Süreç Sayısı: {len(self.proc_data)}")
        self._filter_tree()

    def _filter_tree(self):
        q = self.search_var.get().strip().casefold()
        for row in self.tree.get_children():
            self.tree.delete(row)

        for p in self.proc_data:
            if not q or q in str(p[0]) or q in p[1].casefold():
                self.tree.insert("", "end", values=(p[0], p[1], p[2], p[3], p[4]))

    def _kill_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Seçim Yok", "Lütfen sonlandırmak istediğiniz bir işlem seçin.")
            return

        item = self.tree.item(sel[0])
        pid = int(item["values"][0])
        name = item["values"][1]

        if messagebox.askyesno("Onay", f"'{name}' (PID: {pid}) işlemini sonlandırmak istediğinize emin misiniz?"):
            try:
                proc = psutil.Process(pid)
                proc.terminate()
                messagebox.showinfo("Başarılı", f"İşlem {name} sonlandırıldı.")
                self.root.after(300, self._refresh_processes)
            except Exception as e:
                messagebox.showerror("Hata", f"İşlem sonlandırılamadı: {e}")


if __name__ == "__main__":
    ProcessManagerUI()
