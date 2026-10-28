from __future__ import annotations

import copy
import random
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from app_config import CONFIG_PATH, load_app_config, save_app_config
from core.approval_center import decide, pending
from core.event_bus import recent_events
from core.jarvis_logger import read_logs
from core.settings_store import load_settings, save_settings

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))

C_BG = "#02070a"
C_PANEL = "#041014"
C_CARD = "#07151b"
C_CARD_2 = "#0a2028"
C_LINE = "#0d3d47"
C_PRI = "#00e5ff"
C_SEC = "#9b5cff"
C_TEXT = "#d9fbff"
C_MUTED = "#6c99a5"
C_GREEN = "#00ff9d"
C_GOLD = "#ffd166"
C_RED = "#ff3b5c"
C_BLUE = "#4ea1ff"

FONT_BODY = "Segoe UI Variable"
FONT_DISPLAY = "Segoe UI Semibold"


def font_body(size: int, weight: str = "normal"):
    return (FONT_BODY, size, weight)


def font_display(size: int):
    return (FONT_DISPLAY, size)


class CyberButton(tk.Canvas):
    def __init__(self, master, text: str, command, active: bool = False, height: int = 42, accent: str = C_PRI, **kwargs):
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
        fill = "#09222a" if self.hover or self.active else C_CARD
        outline = self.accent if self.hover or self.active else C_LINE
        self.create_rectangle(0, 0, w - 1, h - 1, fill=fill, outline=outline, width=1)
        self.create_line(0, 0, min(70, w), 0, fill=self.accent, width=2)
        self.create_text(14, h / 2, text=self.text, anchor="w", fill=C_TEXT, font=font_body(10, "bold"))


class SettingsApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S // Settings Core")
        self.root.geometry("1220x760")
        self.root.minsize(1040, 640)
        self.root.configure(bg=C_BG)

        self.settings = load_settings()
        self.api_config = load_app_config()

        # Sekmeler arası veri kaybını önlemek için taslak yapıları
        self.draft_settings = copy.deepcopy(self.settings)
        self.draft_api = copy.deepcopy(self.api_config)

        self.tab = "general"
        self.tab_buttons: dict[str, CyberButton] = {}
        self.vars: dict[str, tk.Variable] = {}
        self.tick = 0
        self.particles = [
            {"x": random.randint(0, 1220), "y": random.randint(0, 760), "s": random.uniform(0.2, 0.8), "c": random.choice((C_PRI, C_SEC, C_BLUE, C_GREEN))}
            for _ in range(90)
        ]
        self._build()
        self._render()
        self._animate()

    def _build(self):
        self.bg = tk.Canvas(self.root, bg=C_BG, highlightthickness=0, bd=0)
        self.bg.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.sidebar = tk.Frame(self.root, bg=C_PANEL, highlightbackground=C_LINE, highlightthickness=1)
        self.sidebar.place(x=18, y=18, width=286, relheight=1, height=-36)
        self.header = tk.Frame(self.root, bg=C_BG)
        self.header.place(x=324, y=18, relwidth=1, width=-342, height=96)
        self.content = tk.Frame(self.root, bg=C_PANEL, highlightbackground=C_LINE, highlightthickness=1)
        self.content.place(x=324, y=130, relwidth=1, width=-342, relheight=1, height=-148)

        brand = tk.Frame(self.sidebar, bg=C_PANEL)
        brand.pack(fill="x", padx=18, pady=(20, 18))
        self.orb = tk.Canvas(brand, width=58, height=58, bg=C_PANEL, highlightthickness=0)
        self.orb.pack(side="left")
        title = tk.Frame(brand, bg=C_PANEL)
        title.pack(side="left", padx=12)
        tk.Label(title, text="J.A.R.V.I.S", bg=C_PANEL, fg=C_PRI, font=font_display(18)).pack(anchor="w")
        tk.Label(title, text="SETTINGS CORE", bg=C_PANEL, fg=C_MUTED, font=font_body(9, "bold")).pack(anchor="w")

        for key, label in [
            ("general", "GENERAL"),
            ("voice", "VOICE"),
            ("integrations", "INTEGRATIONS"),
            ("developer", "DEVELOPER"),
            ("web_panel", "WEB PANEL"),
            ("cyber", "CYBER"),
            ("memory", "MEMORY"),
            ("proactive", "PROACTIVE"),
            ("security", "SECURITY"),
            ("logs", "LOGS"),
            ("approvals", "APPROVALS"),
        ]:
            btn = CyberButton(self.sidebar, label, lambda name=key: self._set_tab(name), active=key == self.tab, bg=C_PANEL)
            btn.pack(fill="x", padx=14, pady=4)
            self.tab_buttons[key] = btn

        CyberButton(self.sidebar, "SAVE SETTINGS", self._save, accent=C_GREEN, bg=C_PANEL).pack(side="bottom", fill="x", padx=14, pady=(4, 18))

        tk.Label(self.header, text="SETTINGS CORE", bg=C_BG, fg=C_PRI, font=font_display(27)).pack(anchor="w")
        tk.Label(
            self.header,
            text="Voice, integrations, proactive behavior, approvals and system diagnostics.",
            bg=C_BG,
            fg=C_MUTED,
            font=font_body(11),
        ).pack(anchor="w", pady=(4, 0))

    def _set_tab(self, tab: str):
        self.tab = tab
        for key, btn in self.tab_buttons.items():
            btn.set_active(key == tab)
        self._render()

    def _render(self):
        for child in self.content.winfo_children():
            child.destroy()
        self.vars.clear()

        if self.tab == "general":
            self._render_general()
        elif self.tab == "voice":
            self._render_voice()
        elif self.tab == "integrations":
            self._render_integrations()
        elif self.tab == "developer":
            self._render_developer()
        elif self.tab == "web_panel":
            self._render_web_panel()
        elif self.tab == "cyber":
            self._render_cyber()
        elif self.tab == "memory":
            self._render_memory()
        elif self.tab == "proactive":
            self._render_proactive()
        elif self.tab == "security":
            self._render_security()
        elif self.tab == "logs":
            self._render_logs()
        else:
            self._render_approvals()

    def _section(self, title: str, subtitle: str = ""):
        frame = tk.Frame(self.content, bg=C_PANEL)
        frame.pack(fill="both", expand=True, padx=24, pady=22)
        tk.Label(frame, text=title, bg=C_PANEL, fg=C_PRI, font=font_display(22)).pack(anchor="w")
        if subtitle:
            tk.Label(frame, text=subtitle, bg=C_PANEL, fg=C_MUTED, font=font_body(10), wraplength=760, justify="left").pack(anchor="w", pady=(4, 18))
        return frame

    def _update_draft(self, key: str, value: Any):
        """Kullanıcının girdiği her değeri anında taslak objesine kaydeder."""
        if key.startswith("api."):
            api_key_name = key.split(".", 1)[1]
            self.draft_api[api_key_name] = value
        else:
            section, name = key.split(".", 1)
            self.draft_settings.setdefault(section, {})[name] = value

    def _row(self, parent, label: str, key: str, value="", secret: bool = False):
        wrap = tk.Frame(parent, bg=C_PANEL)
        wrap.pack(fill="x", pady=7)
        tk.Label(wrap, text=label, bg=C_PANEL, fg=C_MUTED, font=font_body(9, "bold"), width=24, anchor="w").pack(side="left")
        
        var = tk.StringVar(value=str(value or ""))
        ent = tk.Entry(wrap, textvariable=var, show="*" if secret else "", bg="#03151b", fg=C_TEXT, insertbackground=C_PRI, relief="flat", font=font_body(11))
        ent.pack(side="left", fill="x", expand=True, ipady=7)
        
        # Değer her değiştiğinde taslağı güncelle
        var.trace_add("write", lambda *_: self._update_draft(key, var.get()))
        self.vars[key] = var
        return var

    def _check(self, parent, label: str, key: str, value: bool):
        var = tk.BooleanVar(value=bool(value))
        cb = tk.Checkbutton(
            parent,
            text=label,
            variable=var,
            bg=C_PANEL,
            fg=C_TEXT,
            selectcolor=C_CARD_2,
            activebackground=C_PANEL,
            activeforeground=C_PRI,
            font=font_body(10),
            command=lambda: self._update_draft(key, var.get()),
        )
        cb.pack(anchor="w", pady=5)
        self.vars[key] = var
        return var

    def _get_val(self, section: str, key: str, default: Any) -> Any:
        return self.draft_settings.get(section, {}).get(key, default)

    def _get_api_val(self, key: str, default: Any) -> Any:
        return self.draft_api.get(key, default)

    def _render_general(self):
        sec = self._section("General", "Window behavior, tray mode and UI preferences.")
        self._check(sec, "Minimize to tray when X is clicked", "general.minimize_to_tray", self._get_val("general", "minimize_to_tray", True))
        self._check(sec, "Open web panel on start", "general.open_web_panel_on_start", self._get_val("general", "open_web_panel_on_start", False))
        self._check(sec, "Show status metrics", "ui.show_status_metrics", self._get_val("ui", "show_status_metrics", True))
        self._check(sec, "Compact UI mode", "ui.compact_mode", self._get_val("ui", "compact_mode", False))

    def _render_voice(self):
        sec = self._section("Voice", "Realtime voice behavior and long response stability.")
        self._row(sec, "Voice name", "voice.voice", self._get_api_val("voice", self._get_val("voice", "voice", "Charon")))
        self._check(sec, "Long response recovery", "voice.long_response_recovery", self._get_val("voice", "long_response_recovery", True))
        self._check(sec, "Interrupt enabled", "voice.interrupt_enabled", self._get_val("voice", "interrupt_enabled", True))
        self._check(sec, "Auto listen after response", "voice.auto_listen_after_response", self._get_val("voice", "auto_listen_after_response", True))

    def _render_integrations(self):
        sec = self._section("Integrations", f"Discord, Telegram, GitHub, Vercel and API keys. API config: {CONFIG_PATH}")
        self._row(sec, "Gemini API key", "api.gemini_api_key", self._get_api_val("gemini_api_key", ""), secret=True)
        self._row(sec, "Claude API key", "api.claude_api_key", self._get_api_val("claude_api_key", ""), secret=True)
        self._row(sec, "Claude model", "api.claude_model", self._get_api_val("claude_model", "claude-sonnet-4-5-20250929"))
        self._row(sec, "YouTube API key", "api.youtube_api_key", self._get_api_val("youtube_api_key", ""), secret=True)
        self._row(sec, "YouTube handle", "api.youtube_channel_handle", self._get_api_val("youtube_channel_handle", ""))
        self._check(sec, "GitHub enabled", "integrations.github_enabled", self._get_val("integrations", "github_enabled", True))
        self._row(sec, "GitHub token", "api.github_token", self._get_api_val("github_token", ""), secret=True)
        self._row(sec, "GitHub owner", "api.github_owner", self._get_api_val("github_owner", ""))
        self._check(sec, "Vercel enabled", "integrations.vercel_enabled", self._get_val("integrations", "vercel_enabled", True))
        self._row(sec, "Vercel token", "api.vercel_token", self._get_api_val("vercel_token", ""), secret=True)
        self._row(sec, "Vercel team ID", "api.vercel_team_id", self._get_api_val("vercel_team_id", ""))
        self._check(sec, "Google/Gmail enabled", "integrations.google_enabled", self._get_val("integrations", "google_enabled", True))
        self._row(sec, "Google credentials file", "api.google_credentials_file", self._get_api_val("google_credentials_file", "config/google_credentials.json"))
        self._row(sec, "Google token file", "api.google_token_file", self._get_api_val("google_token_file", "config/google_token.json"))
        self._row(sec, "Gmail user ID", "api.gmail_user_id", self._get_api_val("gmail_user_id", "me"))
        self._check(sec, "Discord bot enabled", "integrations.discord_bot_enabled", self._get_val("integrations", "discord_bot_enabled", False))
        self._row(sec, "Discord bot token", "integrations.discord_bot_token", self._get_val("integrations", "discord_bot_token", ""), secret=True)
        self._row(sec, "Discord channel ID", "integrations.discord_channel_id", self._get_val("integrations", "discord_channel_id", ""))
        self._check(sec, "Telegram enabled", "integrations.telegram_enabled", self._get_val("integrations", "telegram_enabled", True))
        self._row(sec, "Telegram bot token", "integrations.telegram_bot_token", self._get_val("integrations", "telegram_bot_token", ""), secret=True)
        self._check(sec, "Web panel enabled", "integrations.web_panel_enabled", self._get_val("integrations", "web_panel_enabled", True))

    def _render_developer(self):
        sec = self._section("Developer Tools", "Project indexing, tests, git summaries and code quality defaults.")
        self._row(sec, "Project index limit", "developer.project_index_limit", self._get_val("developer", "project_index_limit", 400))
        self._row(sec, "Auto test command", "developer.auto_test_command", self._get_val("developer", "auto_test_command", "python -m py_compile main.py"))
        self._row(sec, "Quality scan limit", "developer.quality_score_limit", self._get_val("developer", "quality_score_limit", 300))
        self._row(sec, "Git summary limit", "developer.git_summary_limit", self._get_val("developer", "git_summary_limit", 80))
        self._check(sec, "Safe refactor requires approval", "developer.safe_refactor_requires_approval", self._get_val("developer", "safe_refactor_requires_approval", True))

    def _render_web_panel(self):
        sec = self._section("Web Panel", "Remote command center, live logs, themes and management screens.")
        self._row(sec, "Theme", "web_panel.theme", self._get_val("web_panel", "theme", "white"))
        self._check(sec, "Remote commands enabled", "web_panel.remote_enabled", self._get_val("web_panel", "remote_enabled", True))
        self._check(sec, "Mobile remote enabled", "web_panel.mobile_remote", self._get_val("web_panel", "mobile_remote", True))
        self._check(sec, "Live logs enabled", "web_panel.live_logs", self._get_val("web_panel", "live_logs", True))
        self._check(sec, "Live system graphs", "web_panel.live_system_graphs", self._get_val("web_panel", "live_system_graphs", True))
        self._check(sec, "File manager enabled", "web_panel.file_manager_enabled", self._get_val("web_panel", "file_manager_enabled", True))
        self._check(sec, "Memory editor enabled", "web_panel.memory_editor_enabled", self._get_val("web_panel", "memory_editor_enabled", True))
        self._check(sec, "Workflow builder enabled", "web_panel.workflow_builder_enabled", self._get_val("web_panel", "workflow_builder_enabled", True))

    def _render_cyber(self):
        sec = self._section("Cyber Tools", "Network, DNS, SSL, reputation and Wi-Fi tool defaults.")
        self._row(sec, "DNS timeout", "cyber.dns_timeout", self._get_val("cyber", "dns_timeout", 5))
        self._row(sec, "HTTP timeout", "cyber.http_timeout", self._get_val("cyber", "http_timeout", 8))
        self._row(sec, "SSL timeout", "cyber.ssl_timeout", self._get_val("cyber", "ssl_timeout", 8))
        self._row(sec, "Local network scan limit", "cyber.local_network_scan_limit", self._get_val("cyber", "local_network_scan_limit", 256))
        self._check(sec, "Wi-Fi history enabled", "cyber.wifi_history_enabled", self._get_val("cyber", "wifi_history_enabled", True))
        self._check(sec, "URL screenshot enabled", "cyber.url_screenshot_enabled", self._get_val("cyber", "url_screenshot_enabled", False))
        self._row(sec, "Reputation provider", "cyber.reputation_provider", self._get_val("cyber", "reputation_provider", "local"))

    def _render_memory(self):
        sec = self._section("Memory", "Memory edit controls and preview limits used by the web panel.")
        self._check(sec, "Memory editor enabled", "memory.editable", self._get_val("memory", "editable", True))
        self._row(sec, "Max preview chars", "memory.max_preview_chars", self._get_val("memory", "max_preview_chars", 20000))

    def _render_proactive(self):
        sec = self._section("Proactive Jarvis", "Controls what Jarvis can do before you explicitly ask.")
        self._check(sec, "Enable proactive engine", "proactive.enabled", self._get_val("proactive", "enabled", True))
        self._check(sec, "Battery warning", "proactive.battery_warning", self._get_val("proactive", "battery_warning", True))
        self._row(sec, "Battery threshold", "proactive.battery_threshold", self._get_val("proactive", "battery_threshold", 20))
        self._check(sec, "Daily brief reminder", "proactive.daily_brief", self._get_val("proactive", "daily_brief", True))
        self._row(sec, "Daily brief hour", "proactive.daily_brief_hour", self._get_val("proactive", "daily_brief_hour", 9))
        self._check(sec, "Quiet hours", "proactive.quiet_hours", self._get_val("proactive", "quiet_hours", False))
        self._row(sec, "Quiet start", "proactive.quiet_start", self._get_val("proactive", "quiet_start", "23:00"))
        self._row(sec, "Quiet end", "proactive.quiet_end", self._get_val("proactive", "quiet_end", "08:00"))

    def _render_security(self):
        sec = self._section("Security", "Approval center and risky action gates.")
        self._check(sec, "Approval center enabled", "security.approval_center", self._get_val("security", "approval_center", True))
        self._check(sec, "Shell requires approval", "security.shell_requires_approval", self._get_val("security", "shell_requires_approval", True))
        self._check(sec, "File delete requires approval", "security.file_delete_requires_approval", self._get_val("security", "file_delete_requires_approval", True))
        self._check(sec, "PC power actions require approval", "security.pc_power_requires_approval", self._get_val("security", "pc_power_requires_approval", True))
        self._check(sec, "Admin actions require confirm", "security.admin_actions_require_confirm", self._get_val("security", "admin_actions_require_confirm", True))

    def _render_logs(self):
        sec = self._section("Logs & Events", "Recent local logs and event bus activity.")
        box = tk.Text(sec, bg="#031116", fg=C_TEXT, insertbackground=C_PRI, relief="flat", font=font_body(10), wrap="word")
        box.pack(fill="both", expand=True)
        lines = ["RECENT LOGS:"]
        lines.extend(f"[{r.get('level')}] {r.get('category')}: {r.get('message')}" for r in read_logs(80))
        lines.append("\nRECENT EVENTS:")
        lines.extend(f"[{r.get('type')}] {r.get('message')}" for r in recent_events(80))
        box.insert("1.0", "\n".join(lines))
        box.configure(state="disabled")

    def _render_approvals(self):
        sec = self._section("Approval Center", "Risky operations waiting for approval.")
        rows = pending(80)
        if not rows:
            tk.Label(sec, text="No pending approvals.", bg=C_PANEL, fg=C_MUTED, font=font_body(13, "bold")).pack(anchor="w", pady=20)
            return
        for row in rows:
            card = tk.Frame(sec, bg=C_CARD_2, highlightbackground=C_LINE, highlightthickness=1)
            card.pack(fill="x", pady=6)
            tk.Label(card, text=f"{row['tool']}  /  {row['id']}", bg=C_CARD_2, fg=C_TEXT, font=font_body(11, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
            tk.Label(card, text=row.get("reason", ""), bg=C_CARD_2, fg=C_MUTED, font=font_body(9), wraplength=720, justify="left").pack(anchor="w", padx=12)
            ops = tk.Frame(card, bg=C_CARD_2)
            ops.pack(anchor="e", padx=10, pady=10)
            tk.Button(ops, text="APPROVE", command=lambda item=row: self._decide(item["id"], True), bg=C_GREEN, fg=C_BG, relief="flat").pack(side="left", padx=4)
            tk.Button(ops, text="REJECT", command=lambda item=row: self._decide(item["id"], False), bg=C_RED, fg="white", relief="flat").pack(side="left", padx=4)

    def _decide(self, approval_id: str, approved: bool):
        decide(approval_id, approved)
        self._render()

    def _save(self):
        # Sayısal alanların veri tipini güvenli bir şekilde integer'a çevirelim
        for section, values in self.draft_settings.items():
            if isinstance(values, dict):
                for k, v in values.items():
                    if k.endswith(("threshold", "hour", "limit", "timeout", "chars")):
                        try:
                            values[k] = int(v)
                        except (ValueError, TypeError):
                            pass

        self.settings = save_settings(self.draft_settings)
        self.api_config = save_app_config(self.draft_api)
        messagebox.showinfo("JARVIS Settings", "All settings saved successfully.")

    def _animate(self):
        self.tick += 1
        self.bg.delete("all")
        w = max(1, self.bg.winfo_width())
        h = max(1, self.bg.winfo_height())
        for x in range(-48, w + 48, 48):
            self.bg.create_line(x + self.tick % 48, 0, x - 130, h, fill="#06131b")
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


def start_settings_panel():
    SettingsApp().run()


def open_settings_panel() -> str:
    base_dir = Path(__file__).resolve().parent
    subprocess.Popen(
        [sys.executable, str(base_dir / "settings.py")],
        cwd=str(base_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
    )
    return "Settings panel aciliyor."


if __name__ == "__main__":
    start_settings_panel()