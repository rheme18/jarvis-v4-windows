from __future__ import annotations

import math
import random
import sys
import threading
import time
import tkinter as tk
from pathlib import Path


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


C_BG = "#020c0c"
C_PANEL = "#030f0f"
C_PANEL_2 = "#061818"
C_CARD = "#041313"
C_LINE = "#0a3935"
C_PRI = "#00d4c0"
C_TEXT = "#7dfff6"
C_DIM = "#236962"
C_DIMMER = "#08211f"
C_GREEN = "#00ff88"
C_BLUE = "#4488ff"
C_GOLD = "#ffcc00"
C_ORANGE = "#ff7a00"
C_RED = "#ff3344"

FONT_BODY = "Grift"
FONT_DISPLAY = "Grift Extra Bold"


def font_body(size: int, weight: str = "normal"):
    return (FONT_BODY, size, weight)


def font_display(size: int):
    return (FONT_DISPLAY, size)


TOOL_SPECS = [
    ("Domain", "Domain Report", "domain_whois_lookup", [("domain", "example.com")]),
    ("Domain", "DNS Health", "dns_health_check", [("domain", "example.com")]),
    ("Domain", "SSL Audit", "ssl_certificate_audit", [("hostname", "example.com"), ("port", "443")]),
    ("Security", "URL Reputation", "url_reputation_check", [("url", "example.com")]),
    ("Security", "Password Strength", "password_strength_audit", [("password", "")]),
    ("Security", "Process Risk Scan", "process_risk_scanner", [("limit", "20")]),
    ("File", "File Hash", "file_hash_checker", [("file_path", ""), ("algorithm", "sha256")]),
    ("Network", "Port Scan", "scan_local_ports", [("target_ip", "127.0.0.1")]),
    ("Network", "Wi-Fi Analyzer", "analyze_wifi_and_gateway", []),
    ("Network", "Speed Test", "wifi_speed_test", [("test_url", "")]),
    ("OSINT", "IP Lookup", "lookup_ip_address", [("ip", "8.8.8.8")]),
    ("OSINT", "Phone Lookup", "lookup_phone_number_details", [("phone_number", "+905XXXXXXXXX")]),
    ("OSINT", "Username OSINT", "track_username_osint", [("username", "")]),
    ("OSINT", "Instagram OSINT", "get_instagram_profile_osint", [("username", "")]),
    ("Web", "Website Link Scan", "scan_website_secret_urls", [("url", "example.com")]),
    ("Crypto", "Encrypt Text", "encrypt_message_aes", [("message", "")]),
    ("Crypto", "Decrypt Text", "decrypt_message_aes", [("cipher_text", ""), ("secret_key", "")]),
    ("Market", "Market Report", "track_stock_market_live", []),
]

CATEGORIES = ["All", "Domain", "Security", "File", "Network", "OSINT", "Web", "Crypto", "Market"]


class CyberButton(tk.Canvas):
    def __init__(self, master, text: str, command, active=False, height=42, spec=None, **kwargs):
        super().__init__(master, height=height, bg=kwargs.get("bg", C_PANEL), highlightthickness=0, bd=0)
        self.text = text
        self.command = command
        self.active = active
        self.spec = spec
        self.hover = False
        self.bind("<Button-1>", lambda _event: self.command())
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<Configure>", lambda _event: self.draw())
        self.draw()

    def set_active(self, value: bool):
        self.active = value
        self.draw()

    def _enter(self, _event):
        self.hover = True
        self.draw()

    def _leave(self, _event):
        self.hover = False
        self.draw()

    def draw(self):
        self.delete("all")
        w = max(1, self.winfo_width())
        h = max(1, self.winfo_height())
        fill = "#052522" if self.hover else C_CARD
        outline = C_PRI if self.active else "#0c4944" if self.hover else C_LINE
        text_col = C_PRI if self.active else C_TEXT
        if self.active:
            fill = "#062b28"
        self.create_rectangle(0, 0, w - 1, h - 1, fill=fill, outline=outline, width=1)
        self.create_line(0, 0, min(54, w), 0, fill=C_PRI if self.active else C_DIM, width=2)
        self.create_text(14, h / 2, text=self.text, anchor="w", fill=text_col, font=font_body(10, "bold"))
        if self.active:
            self.create_oval(w - 20, h / 2 - 4, w - 12, h / 2 + 4, fill=C_GREEN, outline="")


class ToolsMenuApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S // Tools Matrix")
        self.root.geometry("1180x760")
        self.root.minsize(980, 640)
        self.root.configure(bg=C_BG)
        self.selected_category = "All"
        self.selected_tool = None
        self.inputs: dict[str, tk.Entry] = {}
        self.category_buttons: dict[str, CyberButton] = {}
        self.tool_buttons: list[CyberButton] = []
        self.search_var = tk.StringVar()
        self.tick = 0
        self.particles = [
            {
                "x": random.randint(0, 1180),
                "y": random.randint(0, 760),
                "r": random.choice((1, 1, 2)),
                "s": random.uniform(0.15, 0.75),
                "a": random.randint(35, 120),
            }
            for _ in range(80)
        ]
        self._build_layout()
        self._render_tools()
        self._animate()

    def _build_layout(self):
        self.bg = tk.Canvas(self.root, bg=C_BG, highlightthickness=0, bd=0)
        self.bg.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.sidebar = tk.Frame(self.root, bg=C_PANEL, highlightbackground=C_LINE, highlightthickness=1)
        self.sidebar.place(x=18, y=18, width=272, relheight=1, height=-36)

        self.header = tk.Frame(self.root, bg=C_BG)
        self.header.place(x=310, y=18, relwidth=1, width=-328, height=94)

        self.list_panel = tk.Frame(self.root, bg=C_PANEL, highlightbackground=C_LINE, highlightthickness=1)
        self.list_panel.place(x=310, y=126, width=326, relheight=1, height=-144)

        self.detail = tk.Frame(self.root, bg=C_PANEL, highlightbackground=C_LINE, highlightthickness=1)
        self.detail.place(x=654, y=126, relwidth=1, width=-672, relheight=1, height=-144)

        self._build_sidebar()
        self._build_header()

    def _build_sidebar(self):
        brand = tk.Frame(self.sidebar, bg=C_PANEL)
        brand.pack(fill="x", padx=18, pady=(20, 16))
        self.orb = tk.Canvas(brand, width=54, height=54, bg=C_PANEL, highlightthickness=0)
        self.orb.pack(side="left")
        box = tk.Frame(brand, bg=C_PANEL)
        box.pack(side="left", padx=12)
        tk.Label(box, text="J.A.R.V.I.S", bg=C_PANEL, fg=C_PRI, font=font_display(17)).pack(anchor="w")
        tk.Label(box, text="TOOLS MATRIX", bg=C_PANEL, fg=C_DIM, font=font_body(9, "bold")).pack(anchor="w")

        self.status = tk.Label(
            self.sidebar,
            text="● READY",
            bg=C_PANEL,
            fg=C_GREEN,
            font=font_body(10, "bold"),
            anchor="w",
        )
        self.status.pack(fill="x", padx=18, pady=(0, 14))

        tk.Label(self.sidebar, text="CATEGORIES", bg=C_PANEL, fg=C_DIM, font=font_body(9, "bold")).pack(anchor="w", padx=18, pady=(6, 8))
        for category in CATEGORIES:
            btn = CyberButton(self.sidebar, category.upper(), lambda c=category: self._select_category(c), active=category == self.selected_category, bg=C_PANEL)
            btn.pack(fill="x", padx=14, pady=3)
            self.category_buttons[category] = btn

        foot = tk.Frame(self.sidebar, bg=C_PANEL)
        foot.pack(side="bottom", fill="x", padx=18, pady=18)
        tk.Label(foot, text="VOICE TRIGGER", bg=C_PANEL, fg=C_DIM, font=font_body(8, "bold")).pack(anchor="w")
        tk.Label(
            foot,
            text="'Jarvis, araclar menusunu ac'",
            bg=C_PANEL,
            fg=C_TEXT,
            wraplength=220,
            justify="left",
            font=font_body(10),
        ).pack(anchor="w", pady=(5, 0))

    def _build_header(self):
        tk.Label(self.header, text="TOOLS MATRIX", bg=C_BG, fg=C_PRI, font=font_display(25)).pack(anchor="w")
        tk.Label(
            self.header,
            text="Local cyber tools, OSINT utilities, crypto helpers and diagnostics.",
            bg=C_BG,
            fg=C_DIM,
            font=font_body(11),
        ).pack(anchor="w", pady=(4, 10))

        search_wrap = tk.Frame(self.header, bg=C_BG)
        search_wrap.pack(fill="x")
        tk.Label(search_wrap, text="SEARCH", bg=C_BG, fg=C_DIM, font=font_body(8, "bold")).pack(side="left", padx=(0, 8))
        self.search = tk.Entry(
            search_wrap,
            textvariable=self.search_var,
            bg="#001112",
            fg=C_TEXT,
            insertbackground=C_PRI,
            relief="flat",
            font=font_body(11),
        )
        self.search.pack(side="left", fill="x", expand=True, ipady=6)
        self.search_var.trace_add("write", lambda *_args: self._render_tools())

    def _select_category(self, category: str):
        self.selected_category = category
        for name, btn in self.category_buttons.items():
            btn.set_active(name == category)
        self._render_tools()

    def _matches(self, spec) -> bool:
        category, label, func_name, _fields = spec
        if self.selected_category != "All" and category != self.selected_category:
            return False
        needle = self.search_var.get().strip().lower()
        if not needle:
            return True
        return needle in f"{category} {label} {func_name}".lower()

    def _render_tools(self):
        for child in self.list_panel.winfo_children():
            child.destroy()
        self.tool_buttons = []

        top = tk.Frame(self.list_panel, bg=C_PANEL)
        top.pack(fill="x", padx=14, pady=(14, 8))
        tk.Label(top, text="AVAILABLE TOOLS", bg=C_PANEL, fg=C_PRI, font=font_body(10, "bold")).pack(anchor="w")
        tk.Label(top, text=f"{self.selected_category} channel", bg=C_PANEL, fg=C_DIM, font=font_body(9)).pack(anchor="w", pady=(2, 0))

        specs = [item for item in TOOL_SPECS if self._matches(item)]
        list_body = tk.Frame(self.list_panel, bg=C_PANEL)
        list_body.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        for spec in specs:
            label = f"{spec[1]}\n{spec[2]}"
            btn = CyberButton(list_body, label, lambda s=spec: self._select_tool(s), active=self.selected_tool == spec, height=58, spec=spec, bg=C_PANEL)
            btn.pack(fill="x", pady=4)
            self.tool_buttons.append(btn)

        if specs and (self.selected_tool not in specs):
            self._select_tool(specs[0])
        elif not specs:
            self._empty_detail("No tools matched the current filter.")

    def _empty_detail(self, text: str):
        for child in self.detail.winfo_children():
            child.destroy()
        tk.Label(self.detail, text=text, bg=C_PANEL, fg=C_DIM, font=font_body(13, "bold")).pack(anchor="center", expand=True)

    def _select_tool(self, spec):
        self.selected_tool = spec
        for btn in self.tool_buttons:
            btn.set_active(btn.spec == spec)
        for child in self.detail.winfo_children():
            child.destroy()
        self.inputs.clear()

        category, label, func_name, fields = spec
        head = tk.Frame(self.detail, bg=C_PANEL)
        head.pack(fill="x", padx=20, pady=(18, 12))
        tk.Label(head, text=label.upper(), bg=C_PANEL, fg=C_PRI, font=font_display(20)).pack(anchor="w")
        tk.Label(head, text=f"{category} // {func_name}", bg=C_PANEL, fg=C_DIM, font=font_body(10, "bold")).pack(anchor="w", pady=(4, 0))

        form = tk.Frame(self.detail, bg=C_PANEL)
        form.pack(fill="x", padx=20)
        if not fields:
            tk.Label(form, text="No parameters required.", bg=C_PANEL, fg=C_DIM, font=font_body(11)).pack(anchor="w", pady=(8, 10))

        for name, placeholder in fields:
            tk.Label(form, text=name.upper(), bg=C_PANEL, fg=C_DIM, font=font_body(8, "bold")).pack(anchor="w", pady=(8, 4))
            entry = tk.Entry(
                form,
                bg="#001112",
                fg=C_TEXT,
                insertbackground=C_PRI,
                relief="flat",
                font=font_body(11),
            )
            entry.insert(0, placeholder)
            entry.pack(fill="x", ipady=8)
            self.inputs[name] = entry

        actions = tk.Frame(self.detail, bg=C_PANEL)
        actions.pack(fill="x", padx=20, pady=16)
        self.run_btn = CyberButton(actions, "RUN TOOL", self._run_selected, active=True, height=44, bg=C_PANEL)
        self.run_btn.pack(side="left", fill="x", expand=True)
        clear_btn = CyberButton(actions, "CLEAR OUTPUT", self._clear_output, height=44, bg=C_PANEL)
        clear_btn.pack(side="left", fill="x", expand=True, padx=(10, 0))

        output_wrap = tk.Frame(self.detail, bg=C_BG, highlightbackground=C_LINE, highlightthickness=1)
        output_wrap.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        tk.Label(output_wrap, text="TERMINAL OUTPUT", bg=C_BG, fg=C_DIM, font=font_body(8, "bold")).pack(anchor="w", padx=12, pady=(10, 0))
        self.output = tk.Text(
            output_wrap,
            wrap="word",
            bg=C_BG,
            fg=C_TEXT,
            insertbackground=C_PRI,
            relief="flat",
            font=("Consolas", 10),
            padx=12,
            pady=10,
        )
        self.output.pack(fill="both", expand=True, padx=0, pady=(4, 0))
        self.output.insert("end", "Awaiting execution...\n")

    def _run_selected(self):
        if not self.selected_tool:
            return
        _category, label, func_name, _fields = self.selected_tool
        payload = {name: entry.get().strip() for name, entry in self.inputs.items()}
        self.status.configure(text="● RUNNING", fg=C_GOLD)
        self.output.delete("1.0", "end")
        self.output.insert("end", f"> {label} started\n> dispatch: {func_name}\n\n")
        threading.Thread(target=self._run_worker, args=(func_name, payload), daemon=True).start()

    def _run_worker(self, func_name: str, payload: dict):
        started = time.time()
        try:
            from tools import _get_custom_tool

            func = _get_custom_tool(func_name)
            if not func:
                result = f"Tool not found: {func_name}"
            else:
                clean_payload = {}
                for key, value in payload.items():
                    if value == "":
                        continue
                    if key in {"port", "limit"}:
                        try:
                            clean_payload[key] = int(value)
                        except ValueError:
                            clean_payload[key] = value
                    else:
                        clean_payload[key] = value
                result = func(**clean_payload)
        except Exception as exc:
            result = f"ERROR: {exc}"
        elapsed = time.time() - started
        self.root.after(0, lambda: self._write_output(str(result), elapsed))

    def _write_output(self, text: str, elapsed: float):
        self.output.insert("end", text)
        self.output.insert("end", f"\n\n> completed in {elapsed:.2f}s")
        self.status.configure(text="● READY", fg=C_GREEN)

    def _clear_output(self):
        if hasattr(self, "output"):
            self.output.delete("1.0", "end")
            self.output.insert("end", "Output cleared.\n")

    def _animate(self):
        self.tick += 1
        self._draw_background()
        self._draw_orb()
        self.root.after(33, self._animate)

    def _draw_background(self):
        self.bg.delete("all")
        w = max(1, self.root.winfo_width())
        h = max(1, self.root.winfo_height())
        step = 44
        for x in range(0, w, step):
            self.bg.create_line(x, 0, x, h, fill=C_DIMMER)
        for y in range(0, h, step):
            self.bg.create_line(0, y, w, y, fill=C_DIMMER)
        scan_y = (self.tick * 2) % (h + 80) - 40
        self.bg.create_line(0, scan_y, w, scan_y + 42, fill="#083a36", width=1)
        for p in self.particles:
            p["y"] += p["s"]
            if p["y"] > h + 6:
                p["y"] = -6
                p["x"] = random.randint(0, w)
            col = self._alpha_color(0, 212, 192, p["a"])
            self.bg.create_oval(p["x"] - p["r"], p["y"] - p["r"], p["x"] + p["r"], p["y"] + p["r"], fill=col, outline="")

    def _draw_orb(self):
        self.orb.delete("all")
        cx, cy = 27, 27
        pulse = 1 + math.sin(self.tick * 0.08) * 0.08
        for r, col in ((24, C_DIM), (19, C_LINE), (13, C_PRI)):
            rr = r * pulse
            self.orb.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, outline=col, width=1)
        angle = self.tick * 4
        self.orb.create_arc(4, 4, 50, 50, start=angle, extent=84, outline=C_GREEN, width=2, style="arc")
        self.orb.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill=C_PRI, outline="")

    @staticmethod
    def _alpha_color(r: int, g: int, b: int, a: int) -> str:
        # Tk has no alpha colors; blend against the dark background.
        bg = (2, 12, 12)
        t = max(0, min(255, a)) / 255
        rr = int(bg[0] + (r - bg[0]) * t)
        gg = int(bg[1] + (g - bg[1]) * t)
        bb = int(bg[2] + (b - bg[2]) * t)
        return f"#{rr:02x}{gg:02x}{bb:02x}"

    def run(self):
        self.root.mainloop()


def start_tools_menu():
    app = ToolsMenuApp()
    app.run()


if __name__ == "__main__":
    start_tools_menu()
