from __future__ import annotations

import random
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


TOOL_DECLARATION = {
    "name": "open_plugin_panel",
    "description": "JARVIS plugin yonetim panelini modern cyber temali ayri bir UI penceresinde acar.",
    "parameters": {"type": "OBJECT", "properties": {}, "required": []},
}

PLUGIN_META = {
    "category": "system",
    "danger": "safe",
    "ui_visible": True,
    "aliases": ["plugin paneli", "plugin panelini ac", "eklenti paneli"],
}


C_BG = "#02070a"
C_PANEL = "#041014"
C_PANEL_2 = "#061820"
C_CARD = "#07151b"
C_LINE = "#0b3d48"
C_PRI = "#00e5ff"
C_SEC = "#9b5cff"
C_TEXT = "#d9fbff"
C_MUTED = "#5e8f9a"
C_DIM = "#16343d"
C_GREEN = "#00ff9d"
C_GOLD = "#ffd166"
C_ORANGE = "#ff8a3d"
C_RED = "#ff3b5c"
C_BLUE = "#4ea1ff"

FONT_BODY = "Grift"
FONT_DISPLAY = "Grift Extra Bold"
DANGERS = ["safe", "confirm_required", "admin", "blocked"]


def font_body(size: int, weight: str = "normal"):
    return (FONT_BODY, size, weight)


def font_display(size: int):
    return (FONT_DISPLAY, size)


def _load_rows() -> list[dict]:
    from actions.plugin_manager import _registry
    from core.plugin_control import plugin_rows

    return plugin_rows(_registry())


def _set_enabled(name: str, enabled: bool) -> str:
    from actions.plugin_manager import run as plugin_manager

    return plugin_manager("enable" if enabled else "disable", name=name)


def _set_danger(name: str, danger: str) -> str:
    from actions.plugin_manager import run as plugin_manager

    return plugin_manager("set_danger", name=name, danger=danger)


class CyberButton(tk.Canvas):
    def __init__(self, master, text: str, command, height: int = 40, active: bool = False, accent: str = C_PRI, **kwargs):
        super().__init__(master, height=height, bg=kwargs.get("bg", C_PANEL), highlightthickness=0, bd=0)
        self.text = text
        self.command = command
        self.active = active
        self.accent = accent
        self.hover = False
        self.bind("<Button-1>", lambda _event: self.command())
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<Configure>", lambda _event: self.draw())
        self.draw()

    def set_text(self, text: str):
        self.text = text
        self.draw()

    def set_active(self, active: bool):
        self.active = active
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
        fill = "#09222a" if self.hover else C_CARD
        outline = self.accent if self.active or self.hover else C_LINE
        self.create_rectangle(0, 0, w - 1, h - 1, fill=fill, outline=outline, width=1)
        self.create_line(0, 0, min(62, w), 0, fill=self.accent, width=2)
        self.create_text(14, h / 2, text=self.text, anchor="w", fill=C_TEXT, font=font_body(10, "bold"))
        if self.active:
            self.create_oval(w - 20, h / 2 - 4, w - 12, h / 2 + 4, fill=self.accent, outline="")


class PluginPanelApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S // Plugin Control")
        self.root.geometry("1240x780")
        self.root.minsize(1040, 660)
        self.root.configure(bg=C_BG)

        self.rows: list[dict] = []
        self.filtered: list[dict] = []
        self.selected: dict | None = None
        self.search_var = tk.StringVar()
        self.category_var = tk.StringVar(value="All")
        self.danger_var = tk.StringVar(value="All")
        self.tick = 0
        self.buttons: list[CyberButton] = []
        self.particles = [
            {
                "x": random.randint(0, 1240),
                "y": random.randint(0, 780),
                "r": random.choice((1, 1, 2)),
                "s": random.uniform(0.15, 0.85),
                "a": random.choice((C_PRI, C_SEC, C_BLUE, C_GREEN)),
            }
            for _ in range(95)
        ]

        self._build_layout()
        self._load()
        self._animate()

    def _build_layout(self):
        self.bg = tk.Canvas(self.root, bg=C_BG, highlightthickness=0, bd=0)
        self.bg.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.sidebar = tk.Frame(self.root, bg=C_PANEL, highlightbackground=C_LINE, highlightthickness=1)
        self.sidebar.place(x=18, y=18, width=286, relheight=1, height=-36)

        self.header = tk.Frame(self.root, bg=C_BG)
        self.header.place(x=324, y=18, relwidth=1, width=-342, height=112)

        self.list_panel = tk.Frame(self.root, bg=C_PANEL, highlightbackground=C_LINE, highlightthickness=1)
        self.list_panel.place(x=324, y=146, width=386, relheight=1, height=-164)

        self.detail = tk.Frame(self.root, bg=C_PANEL, highlightbackground=C_LINE, highlightthickness=1)
        self.detail.place(x=728, y=146, relwidth=1, width=-746, relheight=1, height=-164)

        self._build_sidebar()
        self._build_header()

    def _build_sidebar(self):
        brand = tk.Frame(self.sidebar, bg=C_PANEL)
        brand.pack(fill="x", padx=18, pady=(20, 16))
        self.orb = tk.Canvas(brand, width=58, height=58, bg=C_PANEL, highlightthickness=0)
        self.orb.pack(side="left")

        title = tk.Frame(brand, bg=C_PANEL)
        title.pack(side="left", padx=12)
        tk.Label(title, text="J.A.R.V.I.S", bg=C_PANEL, fg=C_PRI, font=font_display(18)).pack(anchor="w")
        tk.Label(title, text="PLUGIN CONTROL", bg=C_PANEL, fg=C_MUTED, font=font_body(9, "bold")).pack(anchor="w")

        self.status = tk.Label(self.sidebar, text="● SYNCING", bg=C_PANEL, fg=C_GOLD, font=font_body(10, "bold"), anchor="w")
        self.status.pack(fill="x", padx=18, pady=(0, 14))

        self.stats = tk.Label(self.sidebar, text="", bg=C_PANEL, fg=C_TEXT, justify="left", font=font_body(10), anchor="w")
        self.stats.pack(fill="x", padx=18, pady=(0, 18))

        tk.Label(self.sidebar, text="FILTERS", bg=C_PANEL, fg=C_MUTED, font=font_body(9, "bold")).pack(anchor="w", padx=18, pady=(6, 8))
        self.category_box = tk.OptionMenu(self.sidebar, self.category_var, "All")
        self._style_option(self.category_box)
        self.category_box.pack(fill="x", padx=18, pady=(0, 8))
        self.category_var.trace_add("write", lambda *_args: self._render_list())

        self.danger_box = tk.OptionMenu(self.sidebar, self.danger_var, "All", *DANGERS)
        self._style_option(self.danger_box)
        self.danger_box.pack(fill="x", padx=18, pady=(0, 12))
        self.danger_var.trace_add("write", lambda *_args: self._render_list())

        CyberButton(self.sidebar, "REFRESH PLUGINS", self._load, bg=C_PANEL, accent=C_GREEN).pack(fill="x", padx=14, pady=4)
        CyberButton(self.sidebar, "PLUGIN AUDIT PLAN", lambda: self._quick_workflow("plugin_audit"), bg=C_PANEL, accent=C_SEC).pack(fill="x", padx=14, pady=4)
        CyberButton(self.sidebar, "PROJECT SCAN PLAN", lambda: self._quick_workflow("project_scan"), bg=C_PANEL, accent=C_BLUE).pack(fill="x", padx=14, pady=4)

        foot = tk.Frame(self.sidebar, bg=C_PANEL)
        foot.pack(side="bottom", fill="x", padx=18, pady=18)
        tk.Label(foot, text="VOICE TRIGGER", bg=C_PANEL, fg=C_MUTED, font=font_body(8, "bold")).pack(anchor="w")
        tk.Label(foot, text="'Jarvis, plugin panelini ac'", bg=C_PANEL, fg=C_TEXT, wraplength=230, justify="left", font=font_body(10)).pack(anchor="w", pady=(5, 0))

    def _build_header(self):
        tk.Label(self.header, text="PLUGIN CONTROL", bg=C_BG, fg=C_PRI, font=font_display(26)).pack(anchor="w")
        tk.Label(
            self.header,
            text="Enable modules, tune risk levels and inspect the living extension layer.",
            bg=C_BG,
            fg=C_MUTED,
            font=font_body(11),
        ).pack(anchor="w", pady=(4, 12))

        row = tk.Frame(self.header, bg=C_BG)
        row.pack(fill="x")
        tk.Label(row, text="SEARCH", bg=C_BG, fg=C_MUTED, font=font_body(8, "bold")).pack(side="left", padx=(0, 8))
        search = tk.Entry(row, textvariable=self.search_var, bg="#03151b", fg=C_TEXT, insertbackground=C_PRI, relief="flat", font=font_body(11))
        search.pack(side="left", fill="x", expand=True, ipady=7)
        self.search_var.trace_add("write", lambda *_args: self._render_list())

    def _style_option(self, widget):
        widget.configure(bg=C_CARD, fg=C_TEXT, activebackground="#09222a", activeforeground=C_PRI, relief="flat", highlightthickness=1, highlightbackground=C_LINE, font=font_body(10, "bold"))
        widget["menu"].configure(bg=C_CARD, fg=C_TEXT, activebackground=C_PRI, activeforeground=C_BG, relief="flat", font=font_body(10))

    def _load(self):
        try:
            self.rows = _load_rows()
            self.status.configure(text="● ONLINE", fg=C_GREEN)
            self._refresh_categories()
            self._render_list()
        except Exception as exc:
            self.status.configure(text="● ERROR", fg=C_RED)
            self._show_detail_error(str(exc))

    def _refresh_categories(self):
        categories = ["All"] + sorted({str(row.get("category") or "general") for row in self.rows})
        menu = self.category_box["menu"]
        menu.delete(0, "end")
        for category in categories:
            menu.add_command(label=category, command=lambda value=category: self.category_var.set(value))
        if self.category_var.get() not in categories:
            self.category_var.set("All")

    def _passes(self, row: dict) -> bool:
        category = self.category_var.get()
        danger = self.danger_var.get()
        if category != "All" and row.get("category") != category:
            return False
        if danger != "All" and row.get("danger") != danger:
            return False
        needle = self.search_var.get().strip().lower()
        if not needle:
            return True
        blob = f"{row.get('name', '')} {row.get('category', '')} {row.get('source', '')} {row.get('description', '')}".lower()
        return needle in blob

    def _render_list(self):
        self.filtered = [row for row in self.rows if self._passes(row)]
        for child in self.list_panel.winfo_children():
            child.destroy()
        self.buttons = []

        head = tk.Frame(self.list_panel, bg=C_PANEL)
        head.pack(fill="x", padx=14, pady=(14, 8))
        tk.Label(head, text="PLUGIN REGISTRY", bg=C_PANEL, fg=C_PRI, font=font_body(10, "bold")).pack(anchor="w")
        tk.Label(head, text=f"{len(self.filtered)} visible / {len(self.rows)} total", bg=C_PANEL, fg=C_MUTED, font=font_body(9)).pack(anchor="w", pady=(2, 0))

        shell = tk.Frame(self.list_panel, bg=C_PANEL)
        shell.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        canvas = tk.Canvas(shell, bg=C_PANEL, highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(shell, orient="vertical", command=canvas.yview)
        body = tk.Frame(canvas, bg=C_PANEL)
        window_id = canvas.create_window((0, 0), window=body, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        body.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window_id, width=event.width))
        canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))

        for row in self.filtered:
            danger_color = self._danger_color(row.get("danger", "safe"))
            state = "ON" if row.get("enabled", True) else "OFF"
            label = f"{row['name']}\n{state}  //  {row.get('danger', 'safe')}  //  {row.get('category', 'general')}"
            btn = CyberButton(body, label, lambda item=row: self._select(item), height=62, active=self.selected and self.selected.get("name") == row.get("name"), accent=danger_color, bg=C_PANEL)
            btn.pack(fill="x", pady=4)
            self.buttons.append(btn)

        self._update_stats()
        if self.filtered and (not self.selected or self.selected not in self.filtered):
            self._select(self.filtered[0])
        elif not self.filtered:
            self._empty_detail("No plugins matched the current filter.")

    def _select(self, row: dict):
        self.selected = row
        for btn in self.buttons:
            btn.set_active(btn.text.startswith(row["name"] + "\n"))
        self._render_detail(row)

    def _render_detail(self, row: dict):
        for child in self.detail.winfo_children():
            child.destroy()

        danger = row.get("danger", "safe")
        accent = self._danger_color(danger)
        top = tk.Frame(self.detail, bg=C_PANEL)
        top.pack(fill="x", padx=22, pady=(22, 16))
        tk.Label(top, text=row["name"], bg=C_PANEL, fg=C_PRI, font=font_display(23)).pack(anchor="w")
        tk.Label(top, text=row.get("description") or "No description.", bg=C_PANEL, fg=C_MUTED, wraplength=450, justify="left", font=font_body(11)).pack(anchor="w", pady=(6, 0))

        meta = tk.Frame(self.detail, bg=C_PANEL_2, highlightbackground=C_LINE, highlightthickness=1)
        meta.pack(fill="x", padx=22, pady=(0, 16))
        self._kv(meta, "STATE", "ENABLED" if row.get("enabled", True) else "DISABLED", C_GREEN if row.get("enabled", True) else C_RED)
        self._kv(meta, "RISK", danger.upper(), accent)
        self._kv(meta, "CATEGORY", str(row.get("category", "general")).upper(), C_BLUE)
        self._kv(meta, "SOURCE", str(row.get("source", "plugin")), C_TEXT)

        actions = tk.Frame(self.detail, bg=C_PANEL)
        actions.pack(fill="x", padx=22, pady=(0, 14))
        toggle_text = "DISABLE PLUGIN" if row.get("enabled", True) else "ENABLE PLUGIN"
        toggle_color = C_RED if row.get("enabled", True) else C_GREEN
        CyberButton(actions, toggle_text, lambda: self._toggle_selected(), accent=toggle_color, bg=C_PANEL).pack(fill="x", pady=4)

        tk.Label(actions, text="RISK LEVEL", bg=C_PANEL, fg=C_MUTED, font=font_body(8, "bold")).pack(anchor="w", pady=(16, 6))
        risk_grid = tk.Frame(actions, bg=C_PANEL)
        risk_grid.pack(fill="x")
        for level in DANGERS:
            btn = CyberButton(risk_grid, level.upper(), lambda value=level: self._set_selected_danger(value), active=level == danger, accent=self._danger_color(level), bg=C_PANEL, height=38)
            btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        log_box = tk.Frame(self.detail, bg="#031116", highlightbackground=C_LINE, highlightthickness=1)
        log_box.pack(fill="both", expand=True, padx=22, pady=(8, 22))
        tk.Label(log_box, text="POLICY NOTES", bg="#031116", fg=C_PRI, font=font_body(9, "bold")).pack(anchor="w", padx=14, pady=(12, 4))
        text = self._policy_text(row)
        tk.Label(log_box, text=text, bg="#031116", fg=C_TEXT, justify="left", wraplength=460, font=font_body(10)).pack(anchor="nw", padx=14, pady=(0, 12))

    def _kv(self, master, key: str, value: str, color: str):
        row = tk.Frame(master, bg=C_PANEL_2)
        row.pack(fill="x", padx=14, pady=7)
        tk.Label(row, text=key, bg=C_PANEL_2, fg=C_MUTED, font=font_body(8, "bold"), width=12, anchor="w").pack(side="left")
        tk.Label(row, text=value, bg=C_PANEL_2, fg=color, font=font_body(10, "bold"), anchor="w").pack(side="left", fill="x", expand=True)

    def _policy_text(self, row: dict) -> str:
        danger = row.get("danger", "safe")
        if not row.get("enabled", True):
            return "This plugin is disabled. It will not be exposed to the model after restart."
        if danger == "safe":
            return "Safe plugin. It can run directly through Jarvis voice, panel or workflow calls."
        if danger == "confirm_required":
            return "Confirmation required. Calls need confirm=true or explicit approval semantics."
        if danger == "admin":
            return "Admin-level plugin. Keep this for powerful local operations and require explicit confirmation."
        return "Blocked plugin. It stays visible in the panel but execution is denied."

    def _toggle_selected(self):
        if not self.selected:
            return
        name = self.selected["name"]
        enabled = not bool(self.selected.get("enabled", True))
        try:
            result = _set_enabled(name, enabled)
            self._toast(result)
            self._load()
        except Exception as exc:
            messagebox.showerror("Plugin Control", str(exc))

    def _set_selected_danger(self, danger: str):
        if not self.selected:
            return
        try:
            result = _set_danger(self.selected["name"], danger)
            self._toast(result)
            self._load()
        except Exception as exc:
            messagebox.showerror("Plugin Control", str(exc))

    def _quick_workflow(self, workflow: str):
        from actions.workflow_runner import run as workflow_runner

        self._show_output(workflow_runner(workflow, "plan"))

    def _show_output(self, output: str):
        for child in self.detail.winfo_children():
            child.destroy()
        tk.Label(self.detail, text="WORKFLOW PREVIEW", bg=C_PANEL, fg=C_PRI, font=font_display(22)).pack(anchor="w", padx=22, pady=(22, 12))
        box = tk.Text(self.detail, bg="#031116", fg=C_TEXT, insertbackground=C_PRI, relief="flat", font=font_body(10), wrap="word")
        box.pack(fill="both", expand=True, padx=22, pady=(0, 22))
        box.insert("1.0", output)
        box.configure(state="disabled")

    def _show_detail_error(self, text: str):
        for child in self.detail.winfo_children():
            child.destroy()
        tk.Label(self.detail, text="PANEL ERROR", bg=C_PANEL, fg=C_RED, font=font_display(22)).pack(anchor="w", padx=22, pady=(22, 12))
        tk.Label(self.detail, text=text, bg=C_PANEL, fg=C_TEXT, wraplength=480, justify="left", font=font_body(11)).pack(anchor="nw", padx=22)

    def _empty_detail(self, text: str):
        for child in self.detail.winfo_children():
            child.destroy()
        tk.Label(self.detail, text=text, bg=C_PANEL, fg=C_MUTED, font=font_body(13, "bold")).pack(anchor="center", expand=True)

    def _update_stats(self):
        total = len(self.rows)
        enabled = sum(1 for row in self.rows if row.get("enabled", True))
        risky = sum(1 for row in self.rows if row.get("danger") != "safe")
        self.stats.configure(text=f"Plugins: {total}\nEnabled: {enabled}\nPolicy tuned: {risky}")

    def _toast(self, text: str):
        self.status.configure(text="● UPDATED", fg=C_GREEN)
        self.root.after(1800, lambda: self.status.configure(text="● ONLINE", fg=C_GREEN))
        print(f"[JARVIS-PLUGIN-PANEL] {text}")

    @staticmethod
    def _danger_color(danger: str) -> str:
        return {
            "safe": C_GREEN,
            "confirm_required": C_GOLD,
            "admin": C_ORANGE,
            "blocked": C_RED,
        }.get(danger, C_PRI)

    def _animate(self):
        self.tick += 1
        self._draw_background()
        self._draw_orb()
        self.root.after(33, self._animate)

    def _draw_background(self):
        self.bg.delete("all")
        w = max(1, self.bg.winfo_width())
        h = max(1, self.bg.winfo_height())
        step = 42
        offset = self.tick % step
        for x in range(-step, w + step, step):
            self.bg.create_line(x + offset, 0, x + offset - 80, h, fill="#03151b")
        for y in range(-step, h + step, step):
            self.bg.create_line(0, y + offset, w, y + offset, fill="#031017")
        for p in self.particles:
            p["y"] += p["s"]
            if p["y"] > h + 10:
                p["y"] = -10
                p["x"] = random.randint(0, max(1, w))
            self.bg.create_oval(p["x"], p["y"], p["x"] + p["r"], p["y"] + p["r"], fill=p["a"], outline="")
        scan_y = (self.tick * 3) % max(1, h)
        self.bg.create_rectangle(0, scan_y, w, scan_y + 2, fill="#07323b", outline="")

    def _draw_orb(self):
        self.orb.delete("all")
        r = 20 + (self.tick % 24) / 8
        self.orb.create_oval(29 - r, 29 - r, 29 + r, 29 + r, outline=C_PRI, width=2)
        self.orb.create_oval(19, 19, 39, 39, fill="#062932", outline=C_SEC, width=1)
        self.orb.create_arc(11, 11, 47, 47, start=self.tick * 5, extent=90, outline=C_GREEN, width=2, style="arc")

    def run(self):
        self.root.mainloop()


def start_plugin_panel():
    app = PluginPanelApp()
    app.run()


def run() -> str:
    import subprocess
    import sys
    base_file = Path(__file__).resolve()
    subprocess.Popen(
        [sys.executable, str(base_file)],
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
    )
    return "Plugin paneli bağımsız pencere olarak açılıyor Patron."


if __name__ == "__main__":
    start_plugin_panel()
