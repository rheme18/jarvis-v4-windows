from __future__ import annotations

import asyncio
import json
import random
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


BASE_DIR = Path(__file__).resolve().parents[1]
WORKFLOWS_PATH = BASE_DIR / "memory" / "workflows.json"

TOOL_DECLARATION = {
    "name": "open_workflow_builder",
    "description": "JARVIS workflow builder UI penceresini acar; pluginlerden gorev zinciri olusturur.",
    "parameters": {"type": "OBJECT", "properties": {}, "required": []},
}

PLUGIN_META = {
    "category": "workflow",
    "danger": "safe",
    "ui_visible": True,
    "aliases": ["workflow builder", "gorev zinciri paneli", "akis olusturucu"],
}


C_BG = "#03070d"
C_PANEL = "#061019"
C_CARD = "#081723"
C_CARD_2 = "#0b1e2c"
C_LINE = "#12384a"
C_PRI = "#00e5ff"
C_SEC = "#a855f7"
C_TEXT = "#e2fbff"
C_MUTED = "#6d93a3"
C_GREEN = "#00ff9d"
C_GOLD = "#ffd166"
C_RED = "#ff3b5c"
C_BLUE = "#4ea1ff"

FONT_BODY = "Grift"
FONT_DISPLAY = "Grift Extra Bold"


def font_body(size: int, weight: str = "normal"):
    return (FONT_BODY, size, weight)


def font_display(size: int):
    return (FONT_DISPLAY, size)


def _load_plugins() -> list[dict]:
    from actions.plugin_manager import _registry
    from core.plugin_control import plugin_rows

    rows = plugin_rows(_registry())
    return [row for row in rows if row.get("enabled", True)]


def _load_workflows() -> dict:
    try:
        if WORKFLOWS_PATH.exists():
            data = json.loads(WORKFLOWS_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def _save_workflows(data: dict) -> None:
    WORKFLOWS_PATH.parent.mkdir(parents=True, exist_ok=True)
    WORKFLOWS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class CyberButton(tk.Canvas):
    def __init__(self, master, text: str, command, height: int = 42, accent: str = C_PRI, active: bool = False, **kwargs):
        super().__init__(master, height=height, bg=kwargs.get("bg", C_PANEL), highlightthickness=0, bd=0)
        self.text = text
        self.command = command
        self.accent = accent
        self.active = active
        self.hover = False
        self.bind("<Button-1>", lambda _event: self.command())
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<Configure>", lambda _event: self.draw())
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
        fill = "#0c2432" if self.hover or self.active else C_CARD
        self.create_rectangle(0, 0, w - 1, h - 1, fill=fill, outline=self.accent if self.hover or self.active else C_LINE, width=1)
        self.create_line(0, 0, min(74, w), 0, fill=self.accent, width=2)
        self.create_text(14, h / 2, text=self.text, anchor="w", fill=C_TEXT, font=font_body(10, "bold"))


class WorkflowBuilderApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S // Workflow Builder")
        self.root.geometry("1260x780")
        self.root.minsize(1060, 660)
        self.root.configure(bg=C_BG)

        self.plugins: list[dict] = []
        self.steps: list[dict] = []
        self.search_var = tk.StringVar()
        self.workflow_name = tk.StringVar(value="my_workflow")
        self.tick = 0
        self.particles = [
            {"x": random.randint(0, 1260), "y": random.randint(0, 780), "s": random.uniform(.2, .9), "c": random.choice((C_PRI, C_SEC, C_BLUE))}
            for _ in range(80)
        ]
        self._build()
        self._refresh_plugins()
        self._render_steps()
        self._animate()

    def _build(self):
        self.bg = tk.Canvas(self.root, bg=C_BG, highlightthickness=0, bd=0)
        self.bg.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.sidebar = tk.Frame(self.root, bg=C_PANEL, highlightbackground=C_LINE, highlightthickness=1)
        self.sidebar.place(x=18, y=18, width=292, relheight=1, height=-36)

        self.header = tk.Frame(self.root, bg=C_BG)
        self.header.place(x=330, y=18, relwidth=1, width=-348, height=110)

        self.plugin_panel = tk.Frame(self.root, bg=C_PANEL, highlightbackground=C_LINE, highlightthickness=1)
        self.plugin_panel.place(x=330, y=146, width=374, relheight=1, height=-164)

        self.flow_panel = tk.Frame(self.root, bg=C_PANEL, highlightbackground=C_LINE, highlightthickness=1)
        self.flow_panel.place(x=722, y=146, relwidth=1, width=-740, relheight=1, height=-164)

        self._build_sidebar()
        self._build_header()

    def _build_sidebar(self):
        brand = tk.Frame(self.sidebar, bg=C_PANEL)
        brand.pack(fill="x", padx=18, pady=(20, 16))
        self.orb = tk.Canvas(brand, width=58, height=58, bg=C_PANEL, highlightthickness=0)
        self.orb.pack(side="left")
        box = tk.Frame(brand, bg=C_PANEL)
        box.pack(side="left", padx=12)
        tk.Label(box, text="J.A.R.V.I.S", bg=C_PANEL, fg=C_PRI, font=font_display(18)).pack(anchor="w")
        tk.Label(box, text="WORKFLOW BUILDER", bg=C_PANEL, fg=C_MUTED, font=font_body(9, "bold")).pack(anchor="w")

        tk.Label(self.sidebar, text="WORKFLOW NAME", bg=C_PANEL, fg=C_MUTED, font=font_body(8, "bold")).pack(anchor="w", padx=18, pady=(10, 6))
        tk.Entry(self.sidebar, textvariable=self.workflow_name, bg="#051722", fg=C_TEXT, insertbackground=C_PRI, relief="flat", font=font_body(11)).pack(fill="x", padx=18, ipady=7)

        CyberButton(self.sidebar, "SAVE WORKFLOW", self._save_current, accent=C_GREEN, bg=C_PANEL).pack(fill="x", padx=14, pady=(18, 4))
        CyberButton(self.sidebar, "LOAD WORKFLOW", self._load_named, accent=C_BLUE, bg=C_PANEL).pack(fill="x", padx=14, pady=4)
        CyberButton(self.sidebar, "RUN CHAIN", self._run_chain_threaded, accent=C_SEC, bg=C_PANEL).pack(fill="x", padx=14, pady=4)
        CyberButton(self.sidebar, "CLEAR CHAIN", self._clear_steps, accent=C_RED, bg=C_PANEL).pack(fill="x", padx=14, pady=4)

        self.status = tk.Label(self.sidebar, text="● READY", bg=C_PANEL, fg=C_GREEN, font=font_body(10, "bold"), anchor="w")
        self.status.pack(fill="x", padx=18, pady=(20, 8))
        tk.Label(
            self.sidebar,
            text="Soldan plugin sec, zincire ekle, sirayi duzenle ve calistir. Parametre isteyen pluginler simdilik varsayilan argumanla calisir.",
            bg=C_PANEL,
            fg=C_MUTED,
            wraplength=230,
            justify="left",
            font=font_body(10),
        ).pack(anchor="w", padx=18, pady=(0, 12))

    def _build_header(self):
        tk.Label(self.header, text="WORKFLOW BUILDER", bg=C_BG, fg=C_PRI, font=font_display(27)).pack(anchor="w")
        tk.Label(self.header, text="Compose plugin chains and turn Jarvis abilities into repeatable routines.", bg=C_BG, fg=C_MUTED, font=font_body(11)).pack(anchor="w", pady=(4, 12))
        row = tk.Frame(self.header, bg=C_BG)
        row.pack(fill="x")
        tk.Label(row, text="SEARCH PLUGINS", bg=C_BG, fg=C_MUTED, font=font_body(8, "bold")).pack(side="left", padx=(0, 8))
        tk.Entry(row, textvariable=self.search_var, bg="#051722", fg=C_TEXT, insertbackground=C_PRI, relief="flat", font=font_body(11)).pack(side="left", fill="x", expand=True, ipady=7)
        self.search_var.trace_add("write", lambda *_args: self._render_plugins())

    def _scroll_body(self, parent):
        shell = tk.Frame(parent, bg=C_PANEL)
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
        canvas.bind("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))
        body.bind("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))
        return body

    def _refresh_plugins(self):
        self.plugins = _load_plugins()
        self._render_plugins()

    def _render_plugins(self):
        for child in self.plugin_panel.winfo_children():
            child.destroy()
        head = tk.Frame(self.plugin_panel, bg=C_PANEL)
        head.pack(fill="x", padx=14, pady=(14, 8))
        tk.Label(head, text="AVAILABLE PLUGINS", bg=C_PANEL, fg=C_PRI, font=font_body(10, "bold")).pack(anchor="w")
        tk.Label(head, text=f"{len(self.plugins)} active modules", bg=C_PANEL, fg=C_MUTED, font=font_body(9)).pack(anchor="w", pady=(2, 0))
        body = self._scroll_body(self.plugin_panel)
        needle = self.search_var.get().strip().lower()
        for row in self.plugins:
            blob = f"{row.get('name','')} {row.get('category','')} {row.get('description','')}".lower()
            if needle and needle not in blob:
                continue
            label = f"{row['name']}\n{row.get('category', 'general')} // {row.get('danger', 'safe')}"
            CyberButton(body, label, lambda item=row: self._add_step(item), height=62, accent=self._danger_color(row.get("danger", "safe")), bg=C_PANEL).pack(fill="x", pady=4)

    def _render_steps(self):
        for child in self.flow_panel.winfo_children():
            child.destroy()
        head = tk.Frame(self.flow_panel, bg=C_PANEL)
        head.pack(fill="x", padx=18, pady=(16, 10))
        tk.Label(head, text="CHAIN", bg=C_PANEL, fg=C_PRI, font=font_display(21)).pack(anchor="w")
        tk.Label(head, text=f"{len(self.steps)} steps", bg=C_PANEL, fg=C_MUTED, font=font_body(10)).pack(anchor="w", pady=(2, 0))
        body = self._scroll_body(self.flow_panel)
        if not self.steps:
            tk.Label(body, text="No steps yet. Select plugins from the left.", bg=C_PANEL, fg=C_MUTED, font=font_body(13, "bold")).pack(anchor="center", expand=True, pady=80)
            return
        for idx, step in enumerate(self.steps):
            card = tk.Frame(body, bg=C_CARD_2, highlightbackground=C_LINE, highlightthickness=1)
            card.pack(fill="x", pady=6)
            tk.Label(card, text=f"{idx + 1:02d}", bg=C_CARD_2, fg=C_SEC, font=font_display(18), width=4).pack(side="left", padx=(10, 4), pady=12)
            info = tk.Frame(card, bg=C_CARD_2)
            info.pack(side="left", fill="x", expand=True, pady=10)
            tk.Label(info, text=step["name"], bg=C_CARD_2, fg=C_TEXT, font=font_body(11, "bold")).pack(anchor="w")
            tk.Label(info, text=step.get("description", "")[:110], bg=C_CARD_2, fg=C_MUTED, font=font_body(9), wraplength=420, justify="left").pack(anchor="w", pady=(3, 0))
            ops = tk.Frame(card, bg=C_CARD_2)
            ops.pack(side="right", padx=8)
            tk.Button(ops, text="↑", command=lambda i=idx: self._move(i, -1), bg=C_CARD, fg=C_TEXT, relief="flat", width=3).pack(side="left", padx=2)
            tk.Button(ops, text="↓", command=lambda i=idx: self._move(i, 1), bg=C_CARD, fg=C_TEXT, relief="flat", width=3).pack(side="left", padx=2)
            tk.Button(ops, text="×", command=lambda i=idx: self._remove(i), bg=C_RED, fg="white", relief="flat", width=3).pack(side="left", padx=2)

    def _add_step(self, row: dict):
        self.steps.append({"name": row["name"], "description": row.get("description", ""), "args": {}})
        self.status.configure(text="● STEP ADDED", fg=C_GREEN)
        self._render_steps()

    def _move(self, index: int, delta: int):
        target = index + delta
        if target < 0 or target >= len(self.steps):
            return
        self.steps[index], self.steps[target] = self.steps[target], self.steps[index]
        self._render_steps()

    def _remove(self, index: int):
        self.steps.pop(index)
        self._render_steps()

    def _clear_steps(self):
        self.steps = []
        self._render_steps()

    def _save_current(self):
        name = self.workflow_name.get().strip() or "my_workflow"
        data = _load_workflows()
        data[name] = {"steps": self.steps}
        _save_workflows(data)
        self.status.configure(text="● SAVED", fg=C_GREEN)

    def _load_named(self):
        data = _load_workflows()
        if not data:
            messagebox.showinfo("Workflow Builder", "Kayitli workflow yok.")
            return
        name = simpledialog.askstring("Workflow Builder", "Workflow adi:", initialvalue=next(iter(data)))
        if not name:
            return
        if name not in data:
            messagebox.showerror("Workflow Builder", "Workflow bulunamadi.")
            return
        self.workflow_name.set(name)
        self.steps = list(data[name].get("steps", []))
        self._render_steps()

    def _run_chain_threaded(self):
        threading.Thread(target=self._run_chain, daemon=True).start()

    def _run_chain(self):
        if not self.steps:
            self.status.configure(text="● EMPTY", fg=C_GOLD)
            return
        self.status.configure(text="● RUNNING", fg=C_GOLD)
        try:
            from core.plugin_loader import execute_plugin, load_plugins

            registry = load_plugins(["actions", "tools"], reserved_names=set())
            outputs = []
            for idx, step in enumerate(self.steps, 1):
                name = step["name"]
                if name not in registry.tools:
                    outputs.append(f"{idx}. {name}: plugin bulunamadi veya kapali.")
                    continue
                result = asyncio.run(execute_plugin(registry, name, step.get("args", {})))
                outputs.append(f"{idx}. {name}: {result[:600]}")
            self.root.after(0, lambda: self._show_output("\n\n".join(outputs)))
        except Exception as exc:
            self.root.after(0, lambda: messagebox.showerror("Workflow Builder", str(exc)))
        finally:
            self.root.after(0, lambda: self.status.configure(text="● READY", fg=C_GREEN))

    def _show_output(self, text: str):
        win = tk.Toplevel(self.root)
        win.title("Workflow Output")
        win.geometry("820x520")
        win.configure(bg=C_BG)
        box = tk.Text(win, bg="#051722", fg=C_TEXT, insertbackground=C_PRI, relief="flat", font=font_body(10), wrap="word")
        box.pack(fill="both", expand=True, padx=16, pady=16)
        box.insert("1.0", text)
        box.configure(state="disabled")

    @staticmethod
    def _danger_color(danger: str) -> str:
        return {"safe": C_GREEN, "confirm_required": C_GOLD, "admin": "#ff8a3d", "blocked": C_RED}.get(danger, C_PRI)

    def _animate(self):
        self.tick += 1
        self.bg.delete("all")
        w = max(1, self.bg.winfo_width())
        h = max(1, self.bg.winfo_height())
        for x in range(-50, w + 50, 50):
            self.bg.create_line(x + self.tick % 50, 0, x - 120, h, fill="#06111d")
        for p in self.particles:
            p["y"] += p["s"]
            if p["y"] > h + 8:
                p["y"] = -8
                p["x"] = random.randint(0, max(1, w))
            self.bg.create_oval(p["x"], p["y"], p["x"] + 2, p["y"] + 2, fill=p["c"], outline="")
        scan = (self.tick * 3) % max(1, h)
        self.bg.create_rectangle(0, scan, w, scan + 2, fill="#0a2535", outline="")
        self._draw_orb()
        self.root.after(33, self._animate)

    def _draw_orb(self):
        self.orb.delete("all")
        r = 19 + (self.tick % 26) / 7
        self.orb.create_oval(29 - r, 29 - r, 29 + r, 29 + r, outline=C_PRI, width=2)
        self.orb.create_oval(19, 19, 39, 39, fill="#071b28", outline=C_SEC, width=1)
        self.orb.create_arc(10, 10, 48, 48, start=self.tick * 5, extent=100, outline=C_GREEN, width=2, style="arc")

    def run(self):
        self.root.mainloop()


def start_workflow_builder():
    app = WorkflowBuilderApp()
    app.run()


def run() -> str:
    import subprocess
    import sys
    from pathlib import Path
    base_file = Path(__file__).resolve()
    subprocess.Popen(
        [sys.executable, str(base_file)],
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
    )
    return "Workflow builder bağımsız pencere olarak açılıyor Patron."


if __name__ == "__main__":
    start_workflow_builder()
