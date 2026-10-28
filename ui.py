"""
JARVIS V4 Windows — Main HUD
Concentric teal rings · Segmented arcs
"""

import os, time, math, random, threading, json, queue
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog, ttk, colorchooser
from collections import deque
from pathlib import Path
import psutil

from PIL import Image, ImageTk, ImageDraw, ImageFont
from app_config import has_gemini_api_key, load_app_config, save_app_config
from actions.weather import get_weather_summary

BASE_DIR = Path(__file__).resolve().parent

SYSTEM_NAME = "J.A.R.V.I.S V4"
MODEL_BADGE = "VOICE CORE · WINDOWS"

# ── Renk paleti ──────────────────────────────────────────────────────────────
C_BG      = "#020c0c"
C_PRI     = "#00d4c0"
C_ORG     = "#ff6600"
C_ORG2    = "#ff9900"
C_MID     = "#006a62"
C_DIM     = "#0a2a28"
C_DIMMER  = "#061414"
C_TEXT    = "#7dfff6"
C_PANEL   = "#030f0f"
C_GREEN   = "#00ff88"
C_RED     = "#ff3344"
C_MUTED   = "#cc2255"
C_BLUE    = "#4488ff"
C_GOLD    = "#ffcc00"
C_CYAN    = "#00ffff"
C_WHITE   = "#ffffff"

# Orb durum renkleri
ORB_COLORS = {
    "LISTENING":    (0, 255, 136),
    "SPEAKING":     (68, 136, 255),
    "THINKING":     (255, 204, 0),
    "MUTED":        (200, 30, 80),
    "PAUSED":       (30, 60, 55),
    "ERROR":        (255, 51, 68),
    "INITIALISING": (255, 51, 68),
}

# ── Dinamik Tema Paletleri ───────────────────────────────────────────────────
THEME_PALETTES = {
    "teal": {
        "name": "CYBER TEAL (Varsayılan)",
        "pri": "#00d4c0",
        "mid": "#006a62",
        "dim": "#0a2a28",
        "text": "#7dfff6",
        "accent": "#00ff88",
        "orb": (0, 255, 136),
    },
    "ironman": {
        "name": "IRON MAN ARC (Altın / Kızıl)",
        "pri": "#ffcc00",
        "mid": "#8f1d1d",
        "dim": "#3d0a0a",
        "text": "#ffe082",
        "accent": "#ff3344",
        "orb": (255, 204, 0),
    },
    "matrix": {
        "name": "MATRIX NEON (Siber Yeşil)",
        "pri": "#00ff66",
        "mid": "#005522",
        "dim": "#031a0b",
        "text": "#80ffaa",
        "accent": "#00ff88",
        "orb": (0, 255, 102),
    },
    "violet": {
        "name": "DEEP SPACE (Kozmik Mor)",
        "pri": "#c084fc",
        "mid": "#581c87",
        "dim": "#1e0b36",
        "text": "#e9d5ff",
        "accent": "#38bdf8",
        "orb": (192, 132, 252),
    },
    "amber": {
        "name": "AMBER CYBER (Kehribar)",
        "pri": "#ff9900",
        "mid": "#7c3500",
        "dim": "#261000",
        "text": "#ffd180",
        "accent": "#ff6600",
        "orb": (255, 153, 0),
    },
}


def _custom_palette(color: str) -> dict:
    """Build a readable HUD palette from a user-selected accent color."""
    clean = str(color or "").strip().lstrip("#")
    if len(clean) != 6 or any(ch not in "0123456789abcdefABCDEF" for ch in clean):
        clean = "00d4c0"
    rgb = tuple(int(clean[index:index + 2], 16) for index in (0, 2, 4))

    def shade(factor: float) -> str:
        return "#" + "".join(f"{max(0, min(255, round(channel * factor))):02x}" for channel in rgb)

    light = "#" + "".join(f"{max(0, min(255, round(channel + (255 - channel) * .45))):02x}" for channel in rgb)
    return {"name": "KİŞİSEL NEON", "pri": f"#{clean.lower()}", "mid": shade(.38),
            "dim": shade(.14), "text": light, "accent": f"#{clean.lower()}", "orb": rgb}

# ── Boyutlar ─────────────────────────────────────────────────────────────────
W_TARGET = 1540
H_TARGET = 940
LEFT_W_T = 310
RIGHT_W_T = 340
HDR_H    = 72
FOOTER_H = 26
INPUT_H  = 34
CONTROL_H = 126

VOICES = ["Charon", "Puck", "Aoede", "Kore", "Fenrir", "Leda", "Orus", "Zephyr"]

# ── Font sistemi ─────────────────────────────────────────────────────────────
# Grift fontu kullanıcının sisteminde yüklü. Basliklarda daha sert bir vurgu
# icin ayri extra bold aile adini kullaniyoruz.
FONT_BODY_FAMILY = "Grift"
FONT_DISPLAY_FAMILY = "Grift Extra Bold"


def font_body(size: int):
    return (FONT_BODY_FAMILY, size)


def font_body_bold(size: int):
    return (FONT_BODY_FAMILY, size, "bold")


def font_display(size: int):
    return (FONT_DISPLAY_FAMILY, size)


STATE_HEX_COLORS = {
    "LISTENING": C_GREEN,
    "SPEAKING": C_BLUE,
    "THINKING": C_GOLD,
    "INITIALISING": C_RED,
    "ERROR": C_RED,
}


# ── SoundManager ─────────────────────────────────────────────────────────────
import subprocess as _sp

def _resolve_sfx_dir() -> Path:
    return BASE_DIR / "SFX"


_SFX_DIR = _resolve_sfx_dir()
_HUD_FILE = _SFX_DIR / "HUD.mp3"
_START_FILE = _SFX_DIR / "Start.mp3"
_THINK_FILE = _SFX_DIR / "Think.mp3"
_DONE_FILE = _SFX_DIR / "Done.mp3"
_ERROR_FILE = _SFX_DIR / "Error.mp3"

_CREATE_NO_WINDOW = getattr(_sp, "CREATE_NO_WINDOW", 0)


def _play_audio_file(path: Path, volume: float):
    """
    Windows'ta MP3'u PowerShell System.Windows.Media.MediaPlayer ile asenkron calar.
    macOS'taki 'afplay -v <vol>' davranisinin karsiligi: dosya bitince surec sonlanir,
    boylece dongusel sesler (HUD/Think) sorunsuz tekrar eder. Bir Popen nesnesi doner;
    durdurmak icin _sp.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], stdout=_sp.DEVNULL, stderr=_sp.DEVNULL, creationflags=_CREATE_NO_WINDOW); proc.terminate() yeterlidir (PowerShell olunce ses de durur).
    """
    vol = max(0.0, min(1.0, float(volume)))
    uri = str(path).replace("\\", "/")  # Windows yolu URI icin / ile
    script = (
        "Add-Type -AssemblyName presentationCore;"
        "$ErrorActionPreference='SilentlyContinue';"
        "$p=New-Object System.Windows.Media.MediaPlayer;"
        f"$p.Open([System.Uri]'{uri}');"
        f"$p.Volume={vol:.2f};"
        "$p.Play();"
        "$n=0; while(-not $p.NaturalDuration.HasTimeSpan -and $n -lt 40){Start-Sleep -Milliseconds 50; $n++};"
        "if($p.NaturalDuration.HasTimeSpan)"
        "{Start-Sleep -Milliseconds ([int]$p.NaturalDuration.TimeSpan.TotalMilliseconds + 150)}"
        "else{Start-Sleep -Seconds 5}"
    )
    return _sp.Popen(
        ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", script],
        stdout=_sp.DEVNULL,
        stderr=_sp.DEVNULL,
        creationflags=_CREATE_NO_WINDOW,
    )


class SoundManager:
    def __init__(self):
        self._enabled = True
        self._ambient_proc = None
        self._volume = 0.20
        self._ambient_stop = None
        self._ambient_thread = None
        self._foreground_proc = None
        self._foreground_stop = None
        self._foreground_thread = None
        self._foreground_tag = ""
        self._lock = threading.Lock()

    @staticmethod
    def _terminate_process(proc):
        if not proc or proc.poll() is not None:
            return
        try:
            _sp.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], stdout=_sp.DEVNULL, stderr=_sp.DEVNULL, creationflags=_CREATE_NO_WINDOW); proc.terminate()
            proc.wait(timeout=1.0)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    def start_ambient(self):
        if not _HUD_FILE.exists():
            return
        with self._lock:
            if not self._enabled:
                return
            if self._foreground_proc and self._foreground_proc.poll() is None:
                return
            if self._ambient_thread and self._ambient_thread.is_alive():
                return
            stop_event = threading.Event()
            worker = threading.Thread(
                target=self._loop_ambient,
                args=(stop_event,),
                daemon=True,
            )
            self._ambient_stop = stop_event
            self._ambient_thread = worker
        worker.start()

    def _loop_ambient(self, stop_event: threading.Event):
        while not stop_event.is_set():
            with self._lock:
                if not self._enabled or self._ambient_stop is not stop_event:
                    break
                volume = self._volume
            try:
                proc = _play_audio_file(_HUD_FILE, volume)
            except Exception:
                break

            with self._lock:
                if self._ambient_stop is not stop_event or not self._enabled:
                    self._terminate_process(proc)
                    break
                self._ambient_proc = proc

            while proc.poll() is None and not stop_event.wait(0.2):
                pass

            if stop_event.is_set():
                self._terminate_process(proc)

            with self._lock:
                if self._ambient_proc is proc:
                    self._ambient_proc = None

            if stop_event.is_set():
                break
            time.sleep(0.2)

        with self._lock:
            if self._ambient_stop is stop_event:
                self._ambient_stop = None
            if self._ambient_thread and self._ambient_thread.ident == threading.get_ident():
                self._ambient_thread = None

    def _stop_ambient(self):
        with self._lock:
            stop_event = self._ambient_stop
            proc = self._ambient_proc
            self._ambient_stop = None
            self._ambient_thread = None
            self._ambient_proc = None
        if stop_event:
            stop_event.set()
        self._terminate_process(proc)

    def _stop_foreground(self):
        with self._lock:
            stop_event = self._foreground_stop
            proc = self._foreground_proc
            self._foreground_stop = None
            self._foreground_thread = None
            self._foreground_proc = None
            self._foreground_tag = ""
        if stop_event:
            stop_event.set()
        self._terminate_process(proc)

    def _play_foreground(
        self,
        path: Path,
        tag: str,
        loop: bool = False,
        volume_factor: float = 1.0,
        pause_ambient: bool = True,
    ):
        if not path.exists():
            return
        with self._lock:
            if not self._enabled:
                return
            if loop and self._foreground_tag == tag and self._foreground_thread and self._foreground_thread.is_alive():
                return
            base_volume = self._volume
        if pause_ambient:
            self._stop_ambient()
        self._stop_foreground(); [p.kill() for p in psutil.process_iter(['name','cmdline']) if p.info.get('name') and 'powershell' in p.info['name'].lower() and 'MediaPlayer' in ' '.join(p.info.get('cmdline') or [])]

        stop_event = threading.Event()
        worker = threading.Thread(
            target=self._foreground_worker,
            args=(
                path,
                tag,
                stop_event,
                loop,
                max(0.0, min(1.0, base_volume * volume_factor)),
                pause_ambient,
            ),
            daemon=True,
        )
        with self._lock:
            self._foreground_stop = stop_event
            self._foreground_thread = worker
            self._foreground_tag = tag
        worker.start()

    def _foreground_worker(
        self,
        path: Path,
        tag: str,
        stop_event: threading.Event,
        loop: bool,
        volume: float,
        resume_ambient: bool,
    ):
        while not stop_event.is_set():
            try:
                proc = _play_audio_file(path, volume)
            except Exception:
                break

            with self._lock:
                if self._foreground_stop is not stop_event or not self._enabled:
                    self._terminate_process(proc)
                    break
                self._foreground_proc = proc

            while proc.poll() is None and not stop_event.wait(0.12):
                pass

            if stop_event.is_set():
                self._terminate_process(proc)

            with self._lock:
                if self._foreground_proc is proc:
                    self._foreground_proc = None

            if not loop or stop_event.is_set():
                break
            time.sleep(0.08)

        with self._lock:
            if self._foreground_stop is stop_event:
                self._foreground_stop = None
                self._foreground_thread = None
                self._foreground_tag = ""
            should_restart = resume_ambient and self._enabled and self._foreground_stop is None
        if should_restart:
            self.start_ambient()

    def play_startup(self):
        self._play_foreground(_START_FILE, tag="start", loop=False, volume_factor=0.95)

    def play_success(self):
        self._play_foreground(
            _DONE_FILE,
            tag="done",
            loop=False,
            volume_factor=0.68,
            pause_ambient=False,
        )

    def play_error(self):
        self._play_foreground(_ERROR_FILE, tag="error", loop=False, volume_factor=0.95)

    def start_thinking(self):
        self._play_foreground(
            _THINK_FILE,
            tag="think",
            loop=True,
            volume_factor=0.82,
            pause_ambient=False,
        )

    def stop_thinking(self):
        with self._lock:
            is_thinking = self._foreground_tag == "think"
        if is_thinking:
            self._stop_foreground(); [p.kill() for p in psutil.process_iter(['name','cmdline']) if p.info.get('name') and 'powershell' in p.info['name'].lower() and 'MediaPlayer' in ' '.join(p.info.get('cmdline') or [])]

    def toggle(self) -> bool:
        self.set_enabled(not self._enabled)
        return self._enabled

    def set_enabled(self, enabled: bool):
        enabled = bool(enabled)
        with self._lock:
            self._enabled = enabled
        if enabled:
            self.start_ambient()
        else:
            self._stop_ambient()
            self._stop_foreground(); [p.kill() for p in psutil.process_iter(['name','cmdline']) if p.info.get('name') and 'powershell' in p.info['name'].lower() and 'MediaPlayer' in ' '.join(p.info.get('cmdline') or [])]

    def set_volume(self, volume: float):
        with self._lock:
            self._volume = max(0.0, min(1.0, float(volume)))
            fg_tag = self._foreground_tag
            can_restart_ambient = self._enabled and not fg_tag
        if fg_tag == "think":
            self._stop_foreground(); [p.kill() for p in psutil.process_iter(['name','cmdline']) if p.info.get('name') and 'powershell' in p.info['name'].lower() and 'MediaPlayer' in ' '.join(p.info.get('cmdline') or [])]
            self.start_thinking()
        elif can_restart_ambient:
            self._stop_ambient()
            self.start_ambient()

    def stop_all(self):
        with self._lock:
            self._enabled = False
        self._stop_ambient()
        self._stop_foreground(); [p.kill() for p in psutil.process_iter(['name','cmdline']) if p.info.get('name') and 'powershell' in p.info['name'].lower() and 'MediaPlayer' in ' '.join(p.info.get('cmdline') or [])]

    def get_volume(self) -> float:
        return self._volume


# ─────────────────────────────────────────────────────────────────────────────

class JarvisUI:
    def __init__(self):
        global C_PRI, C_MID, C_TEXT, C_DIM, C_GREEN, C_BLUE, C_BG
        try:
            from core.settings_store import get_setting
            __import__("ctypes").windll.shell32.SetCurrentProcessExplicitAppUserModelID("jarvis.voice.v4") if os.name == "nt" else None; saved_theme = str(get_setting("ui", "active_theme", "teal"))
            saved_reduce_motion = bool(get_setting("ui", "reduce_motion", False))
            saved_effect_mode = str(get_setting("ui", "visual_effect_mode", "standard"))
            saved_sfx = bool(get_setting("ui", "sfx_enabled", True))
            saved_fx_volume = max(0.0, min(1.0, float(get_setting("ui", "fx_volume", 0.45))))
        except Exception:
            saved_theme = "teal"
            saved_reduce_motion = False
            saved_effect_mode = "standard"
            saved_sfx = True
            saved_fx_volume = 0.45
        if saved_theme not in THEME_PALETTES and saved_theme != "custom":
            saved_theme = "teal"
        palette = (_custom_palette(get_setting("ui", "custom_primary", "#00d4c0"))
                   if saved_theme == "custom" else THEME_PALETTES[saved_theme])
        C_PRI, C_MID, C_TEXT, C_DIM = palette["pri"], palette["mid"], palette["text"], palette["dim"]
        C_GREEN, C_BG = palette["accent"], "#020c0c"
        C_BLUE = palette.get("pri", C_BLUE)
        ORB_COLORS["LISTENING"] = palette.get("orb", (0, 255, 136))
        STATE_HEX_COLORS["LISTENING"] = C_GREEN
        STATE_HEX_COLORS["SPEAKING"] = C_BLUE
        self.root = tk.Tk()
        self._tk_thread_id = threading.get_ident()
        self._ui_request_queue = queue.Queue()
        self.root.withdraw()  # Tam render olana kadar gizle — siyah flash önlenir
        self.root.title("J.A.R.V.I.S V4 · Windows Edition")
        self.root.resizable(False, False)  # Tam ekran dışında boyutlandırma kapalı

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.W = min(sw - 48, W_TARGET)
        self.H = min(sh - 84, H_TARGET)
        _geo = f"{self.W}x{self.H}+{(sw-self.W)//2}+{(sh-self.H)//2}"
        self.root.geometry(_geo)
        self.root.configure(bg=C_BG)
        self.current_theme = saved_theme
        self._reduce_motion = saved_reduce_motion
        self._visual_effect_mode = saved_effect_mode if saved_effect_mode in {"calm", "standard", "cinematic"} else "standard"
        self._sfx_preference = saved_sfx
        self._fx_volume_preference = saved_fx_volume

        self._window_geometry = _geo
        self._normal_size = (self.W, self.H)
        self._fullscreen = False
        self._resize_job = None

        self._set_layout_metrics(self.W, self.H)

        # ── State ────────────────────────────────────────────────────────────
        self.speaking        = False
        self.user_speaking   = False
        self.muted           = False
        self.paused          = False
        self.scale           = 1.0
        self.target_scale    = 1.0
        self.halo_a          = 55.0
        self.target_halo     = 55.0
        self.last_t          = time.time()
        self.tick            = 0
        self.rings_spin      = [0.0, 45.0, 90.0, 200.0]  # 4 ayrı halka
        self.pulse_r         = []
        self.status_blink    = True
        self._jarvis_state   = "INITIALISING"
        self._user_speaking_until = 0.0

        # ── Webcam ───────────────────────────────────────────────────────────
        self._webcam_active        = False
        self._webcam_photo         = None
        self._webcam_queue_lock    = threading.Lock()
        self._pending_webcam_frame = None
        self._webcam_frame_queued  = False
        self._cam_label: "tk.Label | None" = None
        self._cam_orb_shift        = 0.0   # orb'un anlık kayması (animasyonlu)
        self._cam_orb_shift_target = 0.0   # hedef kayma
        self._cam_orb_face         = 0.0   # orb'un anlık face boyutu (0 → FACE kullan)
        self._cam_orb_face_target  = 0.0   # hedef face boyutu
        self._weather_card = {
            "city": "Adana",
            "primary": "--",
            "details": ["Hava durumu yükleniyor..."],
        }
        self._panel_focus = ""
        self._panel_focus_until = 0.0
        self._brief_refresh_busy = False
        self._started_at = time.time()
        self._error_hold_until = 0.0
        self._settings_open = False
        self._settings_tab = "settings"
        self._debug_entries = deque(maxlen=160)
        self._startup_sfx_played = False
        self._settings_geometry = {
            "btn_x": 14,
            "btn_y": 12,
            "btn_w": 250,
            "btn_h": 46,
            "panel_x": 14,
            "panel_y": HDR_H + 10,
            "panel_w": 380,
            "panel_h": 580,
        }
        self._in_background_mode = False
        self._visual_tick = 0
        self.setup_frame = None
        self.api_entry = None
        self.youtube_api_entry = None
        self.youtube_handle_entry = None

        # ── Callbacks ────────────────────────────────────────────────────────
        self.on_text_command = None
        self.on_pause_toggle = None
        self.on_stop_command = None
        self.on_voice_change = None
        self.on_effects_state_change = None
        self.on_webcam_toggle = None

        # ── Voice ────────────────────────────────────────────────────────────
        self._current_voice = self._load_voice()

        # ── Sound ────────────────────────────────────────────────────────────
        self.sound = SoundManager()
        self.sound.set_volume(self._fx_volume_preference)

        # ── Stats ────────────────────────────────────────────────────────────
        self._stats      = {'cpu': 0.0, 'ram': 0.0, 'disk': 0.0,
                            'battery': 100.0, 'net_up': 0.0, 'net_down': 0.0}
        self._cpu_hist   = [0.0] * 24
        self._last_net   = psutil.net_io_counters()
        self._last_net_t = time.time()
        self._wave_jarvis = [random.randint(4, 26) for _ in range(18)]
        self._wave_user   = [random.randint(2, 10) for _ in range(18)]

        # ── Typing ───────────────────────────────────────────────────────────
        self.typing_queue = deque()
        self.is_typing    = False

        # ── Partiküller (arka plan, az sayıda) ───────────────────────────────
        self.particles = [
            {
                'x':  random.uniform(0, self.W),
                'y':  random.uniform(0, self.H),
                'vx': random.uniform(-0.15, 0.15),
                'vy': random.uniform(-0.15, 0.15),
                'r':  random.uniform(0.5, 1.8),
                'a':  random.randint(15, 70),
            }
            for _ in range(48)
        ]

        self.orb_particles = [
            {
                'angle': random.uniform(0, math.tau),
                'orbit': random.uniform(0.06, 0.98),
                'speed': random.uniform(-0.030, 0.030),
                'size': random.uniform(0.8, 2.8),
                'phase': random.uniform(0, math.tau),
                'wobble': random.uniform(0.010, 0.040),
                'depth': random.uniform(0.30, 1.00),
            }
            for _ in range(260)
        ]
        self.orb_shell_particles = [
            {
                'angle': random.uniform(0, math.tau),
                'speed': random.uniform(-0.020, 0.020),
                'size': random.uniform(1.4, 3.8),
                'phase': random.uniform(0, math.tau),
                'glow': random.uniform(0.4, 1.0),
            }
            for _ in range(112)
        ]

        # ── Matrix Yağmuru ve Siber Efektler (Sıfır Kasma için Pasif) ─────────
        self._matrix_rain_enabled = False
        self._matrix_chars = ""
        self._matrix_columns = []

        # ── Canvas ───────────────────────────────────────────────────────────
        self.bg = tk.Canvas(self.root, width=self.W, height=self.H,
                            bg=C_BG, highlightthickness=0)
        self.bg.place(x=0, y=0)

        # ── Log ──────────────────────────────────────────────────────────────
        self.log_frame = tk.Frame(self.root, bg="#030e0e",
                                  highlightbackground=C_MID,
                                  highlightthickness=1)
        self.log_frame.place(x=self.CHAT_X, y=self.CHAT_Y,
                             width=self.CHAT_W, height=self.CHAT_H)
        self.log_text = tk.Text(
            self.log_frame, fg=C_TEXT, bg="#030e0e",
            insertbackground=C_TEXT, borderwidth=0,
            wrap="word", font=font_body(12), padx=12, pady=8)
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")
        self.log_text.tag_config("you", foreground="#d0f0ee")
        self.log_text.tag_config("ai",  foreground=C_PRI)
        self.log_text.tag_config("sys", foreground=C_GOLD)
        self.log_text.tag_config("err", foreground=C_RED)
        self._bind_smooth_scroll(self.log_text)

        self._build_input_bar(self.CHAT_W)
        self._build_mute_button()
        self._build_pause_button()
        self._build_webcam_button()
        self._build_shutdown_button()
        self._build_social_bar()
        self._build_settings_panel()
        self._build_voice_selector(self._settings_body)
        self._build_sfx_button(self._settings_body)
        self._build_api_button(self._settings_body)
        self._build_fx_slider(self._settings_body)
        self._build_autostart_button(self._settings_body)
        self._build_shortcut_button(self._settings_body)
        self._build_motion_button(self._settings_body)
        self._build_effects_mode_button(self._settings_body)
        self._build_paranoid_button(self._settings_body)
        self._build_air_gestures_button(self._settings_body)
        self._build_self_healing_button(self._settings_body)
        self._build_ghost_typer_button(self._settings_body)
        self._build_terminate_button(self._settings_body)
        self._layout_settings_controls()
        self._place_layout_widgets()

        # Orb tıklama = pause/resume
        self.bg.bind("<Button-1>", self._on_canvas_click)

        self.root.bind("<F4>",        lambda e: self._toggle_mute())
        self.root.bind("<Control-m>", lambda e: self._toggle_mute())
        self.root.bind("<Escape>",    lambda e: self._esc_action())
        self.root.bind("<F5>",        lambda e: self._toggle_pause())
        self.root.bind("<F6>",        lambda e: self._toggle_webcam_ui())
        self.root.bind("<F11>",       lambda e: self._toggle_fullscreen())
        self.root.bind("<Control-f>", lambda e: self._toggle_fullscreen())
        self.root.bind("<Control-k>", lambda e: self._open_command_palette())
        self.root.bind("<F8>", lambda e: self._toggle_floating_island())
        self.root.bind("<Control-Shift-J>", lambda e: self._toggle_floating_island())
        self.root.bind("<Control-Shift-G>", lambda e: self._open_ghost_typer_popup())
        self.root.bind("<Control-Shift-g>", lambda e: self._open_ghost_typer_popup())
        self.root.bind("<Control-Alt-s>",   lambda e: self._quick_screen_analyze())

        # Global Hotkeys (Windows genelinde aktif - Jarvis arkaplandayken de F8 ve Ctrl+Shift+G dinler)
        self._global_f8_registered = False
        try:
            import keyboard
            keyboard.add_hotkey('f8', lambda: self._dispatch_ui(self._toggle_floating_island))
            self._global_f8_registered = True
            keyboard.add_hotkey('ctrl+shift+g', lambda: self._dispatch_ui(self._open_ghost_typer_popup))
        except Exception as _hotkey_err:
            print(f"[Hotkey] Global hotkey başlatılamadı: {_hotkey_err}")
        if not self._global_f8_registered and os.name == "nt":
            threading.Thread(target=self._win_f8_poller, daemon=True).start()

        self._api_key_ready = has_gemini_api_key()
        if not self._api_key_ready:
            self._show_setup_ui()

        self.root.bind("<Configure>", self._on_configure)

        self._effects_active = None
        self._sync_sound_state()
        self._kick_brief_refresh()
        self.root.after(80, self._drain_ui_requests)
        # İlk render — deiconify sonrası _draw() zorunlu, macOS cached content'i atmıyor
        self.root.update_idletasks()
        self._draw()
        self.root.update()
        self._animate()
        self.root.deiconify(); (self._enter_fullscreen() if getattr(self, "_fullscreen", False) else None)
        self.root.update()
        self._draw()   # pencere görünür olduktan sonra zorla çiz — siyah flash önlenir
        # Tam ekran başlat
        self._fullscreen = True
        self._enter_fullscreen()
        self.root.protocol("WM_DELETE_WINDOW", self._shutdown)

    # ── Layout & Fullscreen ───────────────────────────────────────────────────
    def _on_configure(self, event):
        if event.widget is not self.root:
            return
        w, h = event.width, event.height
        if getattr(self, "_fullscreen", False):
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            w = max(w, sw)
            h = max(h, sh)
        if w == self.W and h == self.H:
            return
        if not hasattr(self, "bg"):
            return
        if self._resize_job:
            self.root.after_cancel(self._resize_job)
        self._resize_job = self.root.after(30, lambda: self._resize_surface(w, h))

    def _set_layout_metrics(self, width: int, height: int):
        self.W = max(320, int(width))
        self.H = max(320, int(height))

        left_w = min(LEFT_W_T, max(180, int(self.W * 0.22)))
        right_w = min(RIGHT_W_T, max(220, int(self.W * 0.24)))
        min_center_w = 520
        overflow = left_w + right_w + min_center_w - self.W
        if overflow > 0:
            left_share = min(overflow // 2, max(0, left_w - 170))
            left_w -= left_share
            overflow -= left_share
            right_w -= min(overflow, max(0, right_w - 210))
        self.LEFT_W = max(170, left_w)
        self.RIGHT_W = max(210, right_w)

        center_w = max(360, self.W - self.LEFT_W - self.RIGHT_W)
        control_h = min(CONTROL_H, max(78, int(self.H * 0.16)))
        is_fs = getattr(self, "_fullscreen", False)
        eff_footer = 0 if is_fs else FOOTER_H
        usable_center_h = max(240, self.H - HDR_H - eff_footer - (0 if is_fs else 8))
        orb_area_h = max(170, usable_center_h - control_h)
        self.FCX = self.LEFT_W + center_w // 2
        self.FCY = HDR_H + orb_area_h // 2 + 6
        self.FACE = max(130, min(int(orb_area_h * 0.82), int(center_w * 0.70), 520))
        self.CENTER_X0 = self.LEFT_W
        self.CENTER_X1 = self.W - self.RIGHT_W
        self.CTRL_X = self.LEFT_W + 18
        self.CTRL_Y = HDR_H + orb_area_h + (8 if is_fs else 2)
        self.CHAT_PANEL_X = self.W - self.RIGHT_W + 8
        self.CHAT_PANEL_Y = HDR_H + 8
        self.CHAT_PANEL_W = max(200, self.RIGHT_W - 14)
        # Tam ekranda alt boşluğu tamamen sıfırla, ekrana tam oturt
        self.CHAT_PANEL_H = max(180, self.H - HDR_H - eff_footer - (10 if is_fs else 12))
        self.CHAT_X = self.CHAT_PANEL_X + 10
        self.CHAT_Y = self.CHAT_PANEL_Y + 34
        self.CHAT_W = max(170, self.CHAT_PANEL_W - 20)
        self.CHAT_H = max(80, self.CHAT_PANEL_H - INPUT_H - 52)
        self.CHAT_INPUT_Y = self.CHAT_PANEL_Y + self.CHAT_PANEL_H - INPUT_H - 10

        if hasattr(self, "_settings_geometry"):
            eff_footer = 0 if getattr(self, "_fullscreen", False) else FOOTER_H
            panel_w = min(400, max(310, min(self.LEFT_W + 70, self.W - 28)))
            panel_h = min(680, max(460, self.H - HDR_H - eff_footer - 16))
            self._settings_geometry.update(
                {
                    "btn_w": min(260, max(200, panel_w)),
                    "panel_w": panel_w,
                    "panel_h": panel_h,
                    "panel_y": HDR_H + 10,
                }
            )

    def _enter_fullscreen(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.resizable(True, True)
        self.root.attributes("-fullscreen", True)
        # Windows/Tk sometimes keeps the previous client height after the
        # fullscreen attribute changes. Explicit geometry removes the taskbar
        # sized strip; the follow-up reads back the actual client dimensions.
        self.root.geometry(f"{sw}x{sh}+0+0")
        self._resize_surface(sw, sh)
        self.root.update_idletasks()
        self.root.after(50, self._resize_to_actual_window)

    def _resize_to_actual_window(self):
        try:
            self.root.update_idletasks()
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            if self._fullscreen:
                sw = self.root.winfo_screenwidth()
                sh = self.root.winfo_screenheight()
                width = max(width, sw)
                height = max(height, sh)
            if width > 1 and height > 1:
                self._resize_surface(width, height)
        except Exception:
            pass

    def _toggle_fullscreen(self):
        self._fullscreen = not self._fullscreen
        if self._fullscreen:
            self._enter_fullscreen()
        else:
            self.root.attributes("-fullscreen", False)
            self.root.resizable(False, False)    # pencere modunda kilitle
            self.root.geometry(self._window_geometry)
            self._resize_surface(*self._normal_size)

    def _esc_action(self):
        """Tam ekrandaysa çık, pencere modundaysa kapat."""
        if self._fullscreen:
            self._fullscreen = False
            self.root.attributes("-fullscreen", False)
            self.root.resizable(False, False)
            self.root.geometry(self._window_geometry)
            self._resize_surface(*self._normal_size)
        else:
            self._shutdown()

    def _resize_surface(self, width: int, height: int):
        if getattr(self, "_fullscreen", False):
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            width = max(width, sw)
            height = max(height, sh)
        self._set_layout_metrics(width, height)
        self.bg.configure(width=self.W, height=self.H)
        self.bg.place(x=0, y=0, width=self.W, height=self.H)
        if hasattr(self, "_settings_body"):
            self._layout_settings_controls()
        self._place_layout_widgets()
        eff_footer = 0 if getattr(self, "_fullscreen", False) else FOOTER_H
        if hasattr(self, "_social_bar"):
            self._social_bar.place(x=14, y=max(HDR_H + 4, self.H - eff_footer - 48))
        for p in getattr(self, "particles", []):
            p["x"] %= self.W
            p["y"] %= self.H
        self._draw()
        # Kamera açıksa layout değiştiğinde hedefleri ve label konumunu güncelle
        if self._webcam_active:
            cam_w, cam_h, cam_x, cam_y, shift, face = self._calc_cam_layout()
            self._cam_orb_shift_target = float(shift)
            self._cam_orb_face_target  = float(face)
            if self._cam_label is not None:
                self._cam_label.place(x=cam_x, y=cam_y,
                                      width=cam_w, height=cam_h)

    # ── Modern Yuvarlatılmış / Beveled Şık Çizim Fonksiyonu ────────────────────
    @staticmethod
    def _draw_smooth_rounded_rect(canvas, x1, y1, x2, y2, radius=8, **kwargs):
        """Kenarları yumuşak kavisli lüks cyber panel ve buton çizer."""
        r = max(2, min(radius, (x2 - x1) // 2, (y2 - y1) // 2))
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1
        ]
        return canvas.create_polygon(points, smooth=True, **kwargs)

    def _bind_smooth_scroll(self, widget):
        """Binds silky smooth 60fps momentum scroll to a Tkinter widget (Canvas or Text)."""
        target = [0.0]
        active = [False]

        def _step():
            try:
                curr = widget.yview()[0]
                diff = target[0] - curr
                if abs(diff) > 0.001:
                    widget.yview_moveto(curr + diff * 0.35)
                    self.root.after(16, _step)
                else:
                    widget.yview_moveto(target[0])
                    active[0] = False
            except Exception:
                active[0] = False

        def _on_wheel(e):
            try:
                bounds = widget.yview()
                vh = bounds[1] - bounds[0]
                if vh >= 1.0:
                    return "break"
                step = (vh * 0.16) * (-1 if e.delta > 0 else 1)
                target[0] = max(0.0, min(1.0 - vh, target[0] + step))
                if not active[0]:
                    active[0] = True
                    _step()
            except Exception:
                pass
            return "break"

        widget.bind("<MouseWheel>", _on_wheel)

    # ── Voice ─────────────────────────────────────────────────────────────────
    def _load_voice(self) -> str:
        try:
            return str(load_app_config().get("voice", "Charon") or "Charon")
        except Exception:
            return "Charon"

    # ── Social bar ───────────────────────────────────────────────────────────
    def _build_social_bar(self):
        bar = tk.Frame(self.root, bg=C_BG)
        self._social_bar = bar

        name_lbl = tk.Label(
            bar, text="RHEME18",
            fg="#3a8a82", bg=C_BG,
            font=font_display(14),
            justify="left",
        )
        name_lbl.pack(side="left", padx=(0, 10))

    # ── Shutdown button (sağ alt, büyük) ────────────────────────────────────
    def _build_shutdown_button(self):
        BW, BH = 140, 36
        self._shutdown_canvas = tk.Canvas(
            self.root, width=BW, height=BH,
            bg=C_BG, highlightthickness=0, cursor="hand2")
        self._shutdown_canvas.bind("<Button-1>", lambda e: self.minimize_to_background())
        self._draw_shutdown_button()

    def _draw_shutdown_button(self):
        c = self._shutdown_canvas
        BW, BH = 140, 36
        c.delete("all")
        # Diğer butonlarla tam uyumlu şık siber mavi / cam stil
        col, bg_col = C_BLUE, "#051322"
        self._draw_smooth_rounded_rect(c, 2, 2, BW - 2, BH - 2, radius=10,
                                       fill=bg_col, outline=col, width=1)
        c.create_text(BW//2, BH//2, text="⏻  ARKA PLAN",
                      fill=col, font=font_body_bold(10))

    def _build_settings_panel(self):
        geo = self._settings_geometry
        self._settings_btn_canvas = tk.Canvas(
            self.root,
            width=geo["btn_w"],
            height=geo["btn_h"],
            bg=C_BG,
            highlightthickness=0,
            cursor="hand2",
        )
        self._settings_btn_canvas.place(x=geo["btn_x"], y=geo["btn_y"])
        self._settings_btn_canvas.bind("<Button-1>", lambda e: self._toggle_settings_panel())
        self._draw_settings_button()

        self._settings_panel = tk.Frame(
            self.root,
            bg="#041111",
            highlightbackground=C_MID,
            highlightthickness=1,
        )
        self._settings_panel.place_forget()

        self._settings_title = tk.Label(
            self._settings_panel,
            text="SETTINGS",
            fg=C_PRI,
            bg="#041111",
            font=font_display(11),
        )
        self._settings_tab_settings = tk.Canvas(
            self._settings_panel,
            width=80,
            height=28,
            bg="#041111",
            highlightthickness=0,
            cursor="hand2",
        )
        self._settings_tab_settings.bind("<Button-1>", lambda e: self._set_settings_tab("settings"))

        self._settings_tab_apps = tk.Canvas(
            self._settings_panel,
            width=80,
            height=28,
            bg="#041111",
            highlightthickness=0,
            cursor="hand2",
        )
        self._settings_tab_apps.bind("<Button-1>", lambda e: self._set_settings_tab("apps"))

        self._settings_tab_themes = tk.Canvas(
            self._settings_panel,
            width=76,
            height=28,
            bg="#041111",
            highlightthickness=0,
            cursor="hand2",
        )
        self._settings_tab_themes.bind("<Button-1>", lambda e: self._set_settings_tab("themes"))

        self._settings_tab_debug = tk.Canvas(
            self._settings_panel,
            width=76,
            height=28,
            bg="#041111",
            highlightthickness=0,
            cursor="hand2",
        )
        self._settings_tab_debug.bind("<Button-1>", lambda e: self._set_settings_tab("debug"))

        self._settings_body = tk.Frame(self._settings_panel, bg="#041111")
        self._apps_body = tk.Frame(self._settings_panel, bg="#041111")
        self._themes_body = tk.Frame(self._settings_panel, bg="#041111")
        self._debug_body = tk.Frame(self._settings_panel, bg="#041111")
        self._settings_rules = [tk.Frame(self._settings_body, height=1, bg="#173130") for _ in range(2)]
        self._settings_security_rule = tk.Frame(self._settings_body, height=1, bg="#173130")
        self._settings_security_label = tk.Label(
            self._settings_body,
            text="GÜVENLİK & OTONOM MODLAR",
            fg=C_PRI,
            bg="#041111",
            font=font_body_bold(9),
        )

        self._build_apps_menu(self._apps_body)
        self._build_themes_menu(self._themes_body)
        self._settings_sfx_label = tk.Label(
            self._settings_body,
            text="SES & SESLENDİRME",
            fg=C_PRI,
            bg="#041111",
            font=font_body_bold(9),
        )
        self._settings_visual_label = tk.Label(
            self._settings_body,
            text="GÖRÜNÜM & BAŞLANGIÇ",
            fg=C_PRI,
            bg="#041111",
            font=font_body_bold(9),
        )
        self._settings_status_primary = tk.Label(
            self._settings_body,
            text="",
            fg=C_TEXT,
            bg="#041111",
            font=font_body_bold(9),
            anchor="w",
            justify="left",
        )
        self._settings_status_secondary = tk.Label(
            self._settings_body,
            text="",
            fg=C_MID,
            bg="#041111",
            font=font_body(9),
            anchor="w",
            justify="left",
        )
        self._debug_text = tk.Text(
            self._debug_body,
            fg=C_TEXT,
            bg="#020a0a",
            insertbackground=C_TEXT,
            borderwidth=0,
            wrap="word",
            font=font_body(10),
            padx=10,
            pady=10,
            highlightthickness=1,
            highlightbackground=C_DIM,
        )
        self._debug_text.tag_config("info", foreground=C_TEXT)
        self._debug_text.tag_config("warn", foreground=C_GOLD)
        self._debug_text.tag_config("err", foreground=C_RED)
        self._debug_text.configure(state="disabled"); self._bind_smooth_scroll(self._debug_text)
        self._draw_settings_tabs()
        self._render_debug_logs()
        self._refresh_settings_status()

    def _draw_settings_button(self):
        c = self._settings_btn_canvas
        bw = int(c["width"])
        bh = int(c["height"])
        c.delete("all")
        accent = C_BLUE if self._settings_open else C_PRI
        inner = "#052020" if self._settings_open else "#021212"
        self._draw_smooth_rounded_rect(c, 2, 2, bw - 2, bh - 2, radius=11, fill=inner, outline=accent, width=1)
        c.create_text(14, 15, text="⚙  SYSTEM & APPS", fill=C_PRI, font=font_display(10), anchor="w")
        c.create_text(14, 33, text="CONTROL CENTER · JARVIS V4", fill="#5ca69e", font=font_body(9), anchor="w")
        c.create_text(bw - 16, bh // 2, text="▾" if self._settings_open else "▸",
                      fill=accent, font=font_display(13), anchor="e")

    def _toggle_settings_panel(self):
        self._settings_open = not self._settings_open
        self._draw_settings_button()
        self._place_layout_widgets()

    def _draw_settings_tabs(self):
        tabs = [
            ("settings", self._settings_tab_settings, "AYARLAR"),
            ("apps", self._settings_tab_apps, "MENÜLER"),
            ("themes", self._settings_tab_themes, "TEMA"),
            ("debug", self._settings_tab_debug, "LOG"),
        ]
        for key, canvas, label in tabs:
            active = self._settings_tab == key
            bw = int(canvas["width"])
            bh = int(canvas["height"])
            canvas.delete("all")
            outline = C_PRI if active else C_DIM
            fill = "#082020" if active else "#041111"
            text_col = C_PRI if active else "#5ea7a0"
            canvas.create_rectangle(0, 0, bw, bh, fill=fill, outline="")
            self._draw_smooth_rounded_rect(canvas, 1, 1, bw - 1, bh - 1, radius=6, fill=fill, outline=outline, width=1); canvas.create_text(bw // 2, bh // 2, text=label, fill=text_col, font=font_body_bold(8)); continue
            for bx, by, sx, sy in [(0, 0, 1, 1), (bw, 0, -1, 1), (0, bh, 1, -1), (bw, bh, -1, -1)]:
                canvas.create_line(bx, by, bx + sx * bl, by, fill=outline, width=1)
                canvas.create_line(bx, by, bx, by + sy * bl, fill=outline, width=1)
            canvas.create_text(bw // 2, bh // 2, text=label, fill=text_col, font=font_body_bold(8))

    def _set_settings_tab(self, tab: str):
        self._settings_tab = tab
        self._draw_settings_tabs()
        self._place_layout_widgets()

    def _open_command_palette(self):
        commands = [
            ("App Hub", "Favoriler ve çalışma profilleri", self._open_app_hub),
            ("Odak Zamanlayıcı", "Pomodoro ve mola sayacı", self._open_focus_timer),
            ("Günlük Brifing", "Takvim, hava ve sistem özeti", self._open_daily_brief),
            ("Kişi Kartları", "Kişi veritabanını aç", self._launch_people_cards),
            ("Hızlı Notlar", "Not oluştur, ara veya düzenle", self._open_quick_notes),
            ("Pano Asistanı", "Panoyu isteğe bağlı incele", self._open_clipboard_panel),
            ("Sistem Panosu", "Canlı donanım ve süreç görünümü", self._open_system_dashboard),
            ("Windows Araçları", "Pencere, ses ve ekran kontrolleri", self._open_windows_tools),
            ("Yedek Merkezi", "Yerel dosya yedeği oluştur", self._open_backup_center),
            ("JARVIS Arcade", "Snake ve Tetris oyunları", self._launch_arcade),
            ("Plugin Manager", "Eklentileri yönet", self._launch_plugin_panel),
            ("Workflow Builder", "Çok adımlı iş akışı oluştur", self._launch_workflow_builder),
            ("Siber Güvenlik", "Güvenlik araçlarını aç", self._launch_tools_menu),
        ]
        window = tk.Toplevel(self.root)
        window.title("JARVIS V4 · Komut Paleti")
        window.configure(bg="#071111")
        window.transient(self.root)
        window.geometry("560x500")
        window.minsize(460, 390)
        tk.Label(window, text="HIZLI KOMUT PALETİ", bg="#071111", fg=C_PRI,
                 font=font_display(14)).pack(anchor="w", padx=16, pady=(14, 8))
        query = tk.StringVar()
        search = tk.Entry(window, textvariable=query, bg="#030909", fg=C_TEXT,
                          insertbackground=C_PRI, relief="flat", font=font_body(11))
        search.pack(fill="x", padx=16, pady=(0, 9), ipady=8)
        listing = tk.Listbox(window, bg="#030909", fg=C_TEXT, selectbackground=C_MID,
                             selectforeground="#FFFFFF", relief="flat", bd=0,
                             font=font_body(10), activestyle="none")
        listing.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        visible = []

        def refresh(*_args):
            needle = query.get().strip().casefold()
            visible[:] = [item for item in commands
                          if needle in item[0].casefold() or needle in item[1].casefold()]
            listing.delete(0, tk.END)
            for title, description, _callback in visible:
                listing.insert(tk.END, f"  {title}    ·    {description}")
            if visible:
                listing.selection_set(0)
                listing.activate(0)

        def run_selected(_event=None):
            choice = listing.curselection()
            if not choice or choice[0] >= len(visible):
                return "break"
            callback = visible[choice[0]][2]
            window.destroy()
            callback()
            return "break"

        query.trace_add("write", refresh)
        listing.bind("<Return>", run_selected)
        listing.bind("<Double-Button-1>", run_selected)
        window.bind("<Escape>", lambda _event: window.destroy())
        tk.Label(window, text="↑ ↓ ile seç · Enter ile aç · Esc ile kapat · Ctrl+K", bg="#071111",
                 fg=C_MID, font=font_body(8)).pack(anchor="w", padx=18, pady=(0, 12))
        refresh()
        search.focus_set()

    def _open_system_dashboard(self):
        current = getattr(self, "_system_dashboard_window", None)
        if current is not None:
            try:
                if current.winfo_exists():
                    current.deiconify()
                    current.lift()
                    return
            except tk.TclError:
                pass

        window = tk.Toplevel(self.root)
        self._system_dashboard_window = window
        window.title("JARVIS V4 · Sistem Panosu")
        window.configure(bg="#071111")
        window.geometry("720x560")
        window.minsize(620, 480)
        tk.Label(window, text="CANLI SİSTEM PANOSU", bg="#071111", fg=C_PRI,
                 font=font_display(16)).pack(anchor="w", padx=18, pady=(15, 3))
        tk.Label(window, text="Donanım durumu ve en çok bellek kullanan süreçler", bg="#071111",
                 fg=C_MID, font=font_body(9)).pack(anchor="w", padx=18, pady=(0, 12))

        cards = tk.Frame(window, bg="#071111")
        cards.pack(fill="x", padx=14, pady=(0, 10))
        stats = {}
        for index, (key, title) in enumerate((
            ("cpu", "İŞLEMCİ"), ("ram", "BELLEK"), ("disk", "DİSK"),
            ("battery", "PİL"), ("network", "AĞ"),
        )):
            card = tk.Frame(cards, bg="#0a171b", highlightbackground="#173b43", highlightthickness=1)
            card.grid(row=index // 3, column=index % 3, sticky="ew", padx=4, pady=4)
            tk.Label(card, text=title, bg="#0a171b", fg=C_MID,
                     font=font_body_bold(8)).pack(anchor="w", padx=9, pady=(7, 0))
            value = tk.Label(card, text="--", bg="#0a171b", fg=C_TEXT,
                             font=font_body_bold(13), anchor="w")
            value.pack(anchor="w", padx=9, pady=(1, 7))
            stats[key] = value
        for column in range(3):
            cards.columnconfigure(column, weight=1)

        graph = tk.Canvas(window, height=102, bg="#030909", highlightthickness=1,
                          highlightbackground="#123238")
        graph.pack(fill="x", padx=18, pady=(0, 10))
        process_frame = tk.Frame(window, bg="#071111")
        process_frame.pack(fill="both", expand=True, padx=18, pady=(0, 10))
        tk.Label(process_frame, text="BELLEK KULLANIMINA GÖRE SÜREÇLER", bg="#071111", fg=C_TEXT,
                 font=font_body_bold(9)).pack(anchor="w", pady=(0, 5))
        process_list = tk.Listbox(process_frame, height=8, bg="#030909", fg="#cde3e1",
                                  selectbackground=C_MID, selectforeground="#FFFFFF",
                                  relief="flat", bd=0, font=font_body(9), activestyle="none")
        process_list.pack(fill="both", expand=True)
        history = {"cpu": [], "ram": []}
        previous = {"network": None, "time": time.monotonic()}
        job = {"id": None}

        def update_dashboard():
            if job["id"]:
                try:
                    window.after_cancel(job["id"])
                except tk.TclError:
                    pass
                job["id"] = None
            try:
                cpu = psutil.cpu_percent(interval=None)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage(str(BASE_DIR.anchor or BASE_DIR))
                battery = psutil.sensors_battery()
                network = psutil.net_io_counters()
                now = time.monotonic()
                last, last_time = previous["network"], previous["time"]
                rate_text = "—"
                if last is not None:
                    elapsed = max(.1, now - last_time)
                    down = max(0, network.bytes_recv - last.bytes_recv) / elapsed
                    up = max(0, network.bytes_sent - last.bytes_sent) / elapsed
                    rate_text = f"↓ {down / 1024:.0f} ↑ {up / 1024:.0f} KB/s"
                previous.update(network=network, time=now)
                stats["cpu"].configure(text=f"{cpu:.0f}%")
                stats["ram"].configure(text=f"{memory.percent:.0f}% · {memory.used / 1024**3:.1f} GB")
                stats["disk"].configure(text=f"{disk.percent:.0f}% dolu")
                stats["battery"].configure(text=f"%{battery.percent:.0f}" if battery else "AC güç")
                stats["network"].configure(text=rate_text)

                for key, value in (("cpu", cpu), ("ram", memory.percent)):
                    history[key].append(float(value))
                    del history[key][:-48]
                graph.delete("all")
                width = max(100, graph.winfo_width())
                height = int(graph["height"])
                graph.create_text(10, 13, text="CPU", anchor="w", fill=C_PRI, font=font_body_bold(8))
                graph.create_text(10, 31, text="RAM", anchor="w", fill=C_GREEN, font=font_body_bold(8))
                for key, color, baseline in (("cpu", C_PRI, 24), ("ram", C_GREEN, 42)):
                    values = history[key]
                    points = []
                    for idx, value in enumerate(values):
                        x = 65 + idx * max(1, (width - 80) / 47)
                        y = baseline + 12 - (value / 100.0) * 12
                        points.extend((x, y))
                    if len(points) >= 4:
                        graph.create_line(*points, fill=color, width=2, smooth=True)
                graph.create_line(60, height - 15, width - 10, height - 15, fill="#123238")

                processes = []
                for proc in psutil.process_iter(["pid", "name", "memory_info"]):
                    try:
                        info = proc.info
                        mem = info.get("memory_info")
                        if mem:
                            processes.append((mem.rss, int(info.get("pid") or 0), str(info.get("name") or "Süreç")))
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
                process_list.delete(0, tk.END)
                for used, pid, name in sorted(processes, reverse=True)[:10]:
                    process_list.insert(tk.END, f"{name[:32]:32}  PID {pid:<7}  {used / 1024**2:6.0f} MB")
                job["id"] = window.after(1300, update_dashboard)
            except (psutil.Error, OSError, tk.TclError) as exc:
                try:
                    stats["cpu"].configure(text="Veri alınamadı")
                    self.write_log(f"ERR: Sistem panosu güncellenemedi: {exc}")
                    job["id"] = window.after(2500, update_dashboard)
                except tk.TclError:
                    pass

        controls = tk.Frame(window, bg="#071111")
        controls.pack(fill="x", padx=18, pady=(0, 14))
        self._quick_action_button(controls, "YENİLE", update_dashboard).pack(side="left", padx=(0, 6))
        self._quick_action_button(controls, "WINDOWS ARAÇLARI", self._open_windows_tools).pack(side="left", padx=6)

        def close_dashboard():
            if job["id"]:
                try:
                    window.after_cancel(job["id"])
                except tk.TclError:
                    pass
            window.destroy()
            self._system_dashboard_window = None

        window.protocol("WM_DELETE_WINDOW", close_dashboard)
        update_dashboard()

    def _build_apps_menu(self, parent):
        items = [
            ("🛡️  PARANOİD GÜVENLİK MODU", self._open_paranoid_panel, "İzinsiz giriş tespiti, otomatik karartma & gizli fotoğraf"),
            ("🖐️  AIR GESTURES (TEMASSIZ HAREKET)", self._toggle_air_gestures_ui, "Kamera ile el hareketleri & siber iskelet HUD"),
            ("⌨️  GHOST TYPER (HAYALET YAZICI)", self._open_ghost_typer_popup, "Ctrl+Shift+G · Odaklı pencereye akıcı metin yazımı"),
            ("🛠️  PC SELF-HEALING (SİSTEMİ ONAR)", self._run_self_healing_ui, "DNS, Gezgin, Ses, Temp & RAM tek tıkla onarımı"),
            ("📷  KAMERADAN FOTOĞRAF ÇEK", self._capture_photo_ui, "Webcam ile yüksek çözünürlüklü fotoğraf çek ve kaydet"),
            ("⌕  HIZLI KOMUT PALETİ", self._open_command_palette, "Ctrl+K · Ara, seç, çalıştır"),
            ("📊  SİSTEM PANOSU", self._open_system_dashboard, "Canlı CPU, bellek, disk, pil ve süreçler"),
            ("🚀  APP HUB", self._open_app_hub, "Uygulamalar, favoriler ve çalışma profilleri"),
            ("⏱  ODAK ZAMANLAYICI", self._open_focus_timer, "Pomodoro, mola ve dikkat kontrolü"),
            ("🌅  GÜNLÜK BRİFİNG", self._open_daily_brief, "Sistem, hava, takvim ve hatırlatıcı özeti"),
            ("📋  PANO ASİSTANI", self._open_clipboard_panel, "Panoyu incele, özetle veya yerel nota kaydet"),
            ("💾  YEDEK MERKEZİ", self._open_backup_center, "Yerel yedek planla ve oluştur"),
            ("🏝️  YÜZEN ADA (FLOATING HUD)", self._enter_floating_island, "F8 · Sürüklenebilir şeffaf dinamik ada"),
            ("👁️  CANLI EKRAN ANALİZİ", self._quick_screen_analyze, "Ctrl+Alt+S · Ekrandaki kodu, metni ve içeriği incele"),
            ("🛠️  HIZLI ARAÇLAR", self._launch_quick_tools, "Şifre, QR, Renk, Hash, Base64 & JSON"),
            ("📋  PANO YÖNETİCİSİ", self._launch_clipboard_manager, "Geçmiş panolar, arama & tek tıkla kopyala"),
            ("⚡  SÜREÇ & RAM BOOSTER", self._launch_process_manager, "Canlı görev yöneticisi & bellek temizleyici"),
            ("🎮  CYBER ARCADE", self._launch_arcade, "Tetris, Snake, AI Pong, Refleks & Trivia"),
            ("🔌  PLUGIN MANAGER", self._launch_plugin_panel, "Eklentileri ve araçları yönet"),
            ("⚡  WORKFLOW BUILDER", self._launch_workflow_builder, "Çok adımlı görev zinciri tasarla"),
            ("🛡️  SİBER GÜVENLİK", self._launch_tools_menu, "OSINT, port tarama ve şifreleme"),
            ("👤  KİŞİ KARTLARI", self._launch_people_cards, "Kayıtlı kişi profilleri ve kartlar"),
            ("🧠  VEKTÖR HAFIZA EŞİTLE", self._sync_vector_memory, "Yerel RAG hafızasını güncelle"),
            ("📝  HIZLI NOTLAR", self._open_quick_notes, "Not al, ara ve notlarını yönet"),
            ("🖥️  WINDOWS ARAÇLARI", self._open_windows_tools, "Pencere düzeni, ses, parlaklık"),
        ]
        canvas = tk.Canvas(parent, bg="#041111", highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        cards = tk.Frame(canvas, bg="#041111")
        window_id = canvas.create_window((0, 0), window=cards, anchor="nw")
        cards.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window_id, width=event.width))
        self._bind_smooth_scroll(canvas)
        for i, (label, cmd, desc) in enumerate(items):
            box = tk.Frame(cards, bg="#031616", highlightbackground=C_MID, highlightthickness=1)
            box.pack(fill="x", padx=1, pady=3, ipady=2)
            lbl = tk.Label(box, text=label, fg=C_PRI, bg="#031616", font=font_body_bold(9), anchor="w")
            lbl.pack(fill="x", padx=9, pady=(4, 0))
            desc_lbl = tk.Label(box, text=desc, fg="#5ea7a0", bg="#031616", font=font_body(8), anchor="w")
            desc_lbl.pack(fill="x", padx=9, pady=(0, 4))
            for w in (box, lbl, desc_lbl):
                w.bind("<Button-1>", lambda e, func=cmd: func())
                w.bind("<MouseWheel>", lambda event: canvas.event_generate("<MouseWheel>", delta=event.delta))
                w.configure(cursor="hand2")

    def _build_themes_menu(self, parent):
        lbl = tk.Label(parent, text="HUD RENK PALETİ SEÇİMİ", fg=C_PRI, bg="#041111", font=font_display(9))
        lbl.place(x=0, y=4)
        y = 28
        for key, t in THEME_PALETTES.items():
            box = tk.Frame(parent, bg="#031616", highlightbackground=t["pri"], highlightthickness=1)
            box.place(x=0, y=y, relwidth=1.0, height=42)
            dot = tk.Canvas(box, width=16, height=16, bg="#031616", highlightthickness=0)
            dot.place(x=10, y=13)
            dot.create_oval(2, 2, 14, 14, fill=t["pri"], outline=t["accent"], width=1)
            name_lbl = tk.Label(box, text=t["name"], fg=t["pri"], bg="#031616", font=font_body_bold(9))
            name_lbl.place(x=34, y=11)
            for w in (box, dot, name_lbl):
                w.bind("<Button-1>", lambda e, tk_name=key: self.apply_theme(tk_name))
                w.configure(cursor="hand2")
            y += 48
        custom = tk.Button(self._themes_body, text="✦  ÖZEL NEON RENGİ SEÇ",
                           command=self._choose_custom_theme, bg="#0a171b", fg=C_PRI,
                           activebackground="#153739", activeforeground="#ffffff",
                           relief="flat", bd=0, cursor="hand2", font=font_body_bold(9))
        custom.place(x=0, y=y + 2, relwidth=1.0, height=36)

    def _choose_custom_theme(self):
        selected = colorchooser.askcolor(color=C_PRI, title="JARVIS vurgu rengini seç", parent=self.root)
        color = selected[1] if selected else None
        if not color:
            return
        try:
            from core.settings_store import set_setting
            set_setting("ui", "custom_primary", color)
        except Exception as exc:
            self.write_log(f"ERR: Özel tema kaydedilemedi: {exc}")
        self.apply_theme("custom")

    def _launch_child_ui(self, relative_path: str, label: str):
        import subprocess, sys
        path = BASE_DIR / relative_path
        if not path.is_file():
            message = f"{label} arayüz dosyası bulunamadı: {path}"
            self.write_log(f"ERR: {message}")
            messagebox.showerror(label, message, parent=self.root)
            return
        try:
            subprocess.Popen(
                [sys.executable, str(path)], cwd=str(BASE_DIR),
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
            self.write_log(f"SYS: {label} ayrı pencerede açılıyor.")
        except Exception as exc:
            self.write_log(f"ERR: {label} açılamadı: {exc}")
            messagebox.showerror(label, f"Pencere açılamadı:\n{exc}", parent=self.root)

    def _launch_plugin_panel(self):
        self._launch_child_ui("actions/plugin_panel.py", "Plugin Manager")

    def _launch_workflow_builder(self):
        self._launch_child_ui("actions/workflow_builder.py", "Workflow Builder")

    def _launch_tools_menu(self):
        self._launch_child_ui("tools/tools_menu.py", "Siber Güvenlik Araçları")

    def _launch_people_cards(self):
        self.open_people_database()

    def open_people_database(self, person=None):
        # Tk widgets are only touched by the thread that owns the Tcl event loop.
        # Tool calls run in asyncio worker threads, so enqueue their UI request.
        self._dispatch_ui(self._show_people_database, person)

    def _dispatch_ui(self, callback, *args):
        if threading.get_ident() == self._tk_thread_id:
            callback(*args)
        else:
            self._ui_request_queue.put(("callback", (callback, args)))

    def _drain_ui_requests(self):
        try:
            while True:
                action, payload = self._ui_request_queue.get_nowait()
                if action == "callback":
                    callback, args = payload
                    callback(*args)
                elif action == "webcam_frame":
                    with self._webcam_queue_lock:
                        frame = self._pending_webcam_frame
                        self._pending_webcam_frame = None
                        self._webcam_frame_queued = False
                    if frame is not None:
                        self._show_webcam_preview(frame)
        except queue.Empty:
            pass
        except Exception as exc:
            self.write_log(f"ERR: Arayüz isteği tamamlanamadı: {exc}")
        try:
            if self.root.winfo_exists():
                self.root.after(80, self._drain_ui_requests)
        except tk.TclError:
            pass

    def _show_people_database(self, person=None):
        try:
            current = getattr(self, "_people_database_ui", None)
            current_open = False
            if current is not None:
                try:
                    current_open = bool(current.root.winfo_exists())
                except tk.TclError:
                    current_open = False
            if current_open:
                current.show_person(person)
            else:
                import importlib.util
                import sys
                module_name = "_jarvis_person_profile_ui"
                profile_module = sys.modules.get(module_name)
                if profile_module is None:
                    profile_path = BASE_DIR / "ui" / "person_profile_ui.py"
                    spec = importlib.util.spec_from_file_location(module_name, profile_path)
                    if spec is None or spec.loader is None:
                        raise ImportError(f"Kişi kartı arayüzü yüklenemedi: {profile_path}")
                    profile_module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = profile_module
                    try:
                        spec.loader.exec_module(profile_module)
                    except Exception:
                        sys.modules.pop(module_name, None)
                        raise
                self._people_database_ui = profile_module.CyberpersonUI(
                    target_person=person, parent=self.root,
                )
            if person:
                self.write_log(f"SYS: {person.get('name', 'Kişi')} kartı veritabanında açıldı.")
            else:
                self.write_log("SYS: Kişi Kartları veritabanı açıldı.")
        except Exception as exc:
            self.write_log(f"ERR: Kişi Kartları açılamadı: {exc}")

    def _launch_quick_tools(self):
        self._launch_child_ui("tools/quick_tools.py", "Hızlı Araçlar")

    def _launch_clipboard_manager(self):
        self._launch_child_ui("tools/clipboard_manager.py", "Pano Yöneticisi")

    def _launch_process_manager(self):
        self._launch_child_ui("tools/process_manager.py", "Süreç Yöneticisi")

    # ── Floating Dynamic Island HUD Modu ─────────────────────────────────────
    def _quick_screen_analyze(self):
        def _run():
            try:
                self.write_log("SYS: Ekran taranıyor ve analiz ediliyor...")
                from actions.screen_vision import analyze_screen
                result = analyze_screen("Ekrandaki mevcut içeriği, açık olan pencereyi ve önemli detayları özetle.")
                self.write_log(f"JARVIS [EKRAN ANALİZİ]: {result}")
            except Exception as exc:
                self.write_log(f"ERR: Ekran analizi başarısız: {exc}")

        import threading
        threading.Thread(target=_run, daemon=True).start()

    def _win_f8_poller(self):
        if os.name != "nt":
            return
        import ctypes
        last = False
        while True:
            try:
                st = bool(ctypes.windll.user32.GetAsyncKeyState(0x77) & 0x8000)
                if st and not last:
                    self._dispatch_ui(self._toggle_floating_island)
                last = st
            except Exception:
                pass
            time.sleep(0.04)

    def _toggle_floating_island(self):
        now = time.time()
        if now - getattr(self, "_last_island_toggle_time", 0.0) < 0.65:
            return
        self._last_island_toggle_time = now

        if getattr(self, "_floating_island", None) and getattr(self._floating_island, "root", None):
            try:
                if self._floating_island.root.winfo_exists():
                    self._floating_island.restore_main_ui()
                    return
            except Exception:
                pass
        self._enter_floating_island()

    def _enter_floating_island(self):
        try:
            import importlib.util
            island_path = BASE_DIR / "ui" / "floating_island.py"
            spec = importlib.util.spec_from_file_location("_floating_island_mod", island_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            try:
                self.sound.stop_all()
            except Exception:
                pass

            self.root.withdraw()
            self._in_background_mode = True
            self._floating_island = mod.FloatingIsland(
                jarvis_ui=self,
                on_restore_callback=self._restore_from_floating_island
            )
            self.write_log("SYS: ✦ Yüzen Ada (Dynamic Island) moduna geçildi. (F8 ile geri dön)")
        except Exception as exc:
            self.write_log(f"ERR: Yüzen Ada başlatılamadı: {exc}")
            self._in_background_mode = False
            self.root.deiconify()
            if getattr(self, "_fullscreen", False):
                self._enter_fullscreen()

    def _restore_from_floating_island(self):
        self._floating_island = None
        self._in_background_mode = False
        try:
            self.root.deiconify()
            if getattr(self, "_fullscreen", False):
                self._enter_fullscreen()
            self.root.lift()
            self.root.focus_force()
            self.write_log("SYS: ✦ Ana kontrol paneline geri dönüldü.")
        except Exception:
            pass
        try:
            if getattr(self, "_sfx_preference", True):
                self.sound.set_enabled(True)
                self.sound.start_ambient()
        except Exception:
            pass

    def _launch_arcade(self):
        self._launch_child_ui("games/arcade.py", "JARVIS Arcade")

    def _open_app_hub(self):
        preferences_path = BASE_DIR / "memory" / "ui_preferences.json"
        defaults = ["Chrome", "Spotify", "VS Code", "WhatsApp", "Notion", "Calculator"]

        def load_preferences():
            try:
                data = json.loads(preferences_path.read_text(encoding="utf-8"))
                if isinstance(data, dict) and isinstance(data.get("favorite_apps"), list):
                    return [str(item).strip() for item in data["favorite_apps"] if str(item).strip()]
            except (OSError, json.JSONDecodeError):
                pass
            return list(defaults)

        def save_preferences(items):
            try:
                preferences_path.parent.mkdir(parents=True, exist_ok=True)
                preferences_path.write_text(
                    json.dumps({"favorite_apps": items}, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                return True
            except OSError as exc:
                messagebox.showerror("App Hub", f"Favoriler kaydedilemedi:\n{exc}", parent=window)
                return False

        window = tk.Toplevel(self.root)
        window.title("JARVIS V4 · App Hub")
        window.configure(bg="#071111")
        window.geometry("760x640")
        window.minsize(620, 520)
        tk.Label(window, text="APP HUB", bg="#071111", fg=C_PRI,
                 font=font_display(18)).pack(anchor="w", padx=18, pady=(15, 2))
        tk.Label(window, text="Uygulamalarını, web servislerini ve çalışma ortamlarını tek yerden aç.",
                 bg="#071111", fg=C_MID, font=font_body(9)).pack(anchor="w", padx=18, pady=(0, 14))

        profiles = tk.Frame(window, bg="#071111")
        profiles.pack(fill="x", padx=14, pady=(0, 12))
        profile_cards = [
            ("KODLAMA", "code", "VS Code + Terminal"),
            ("DERS & ODAK", "study", "Chrome + Calendar + Tasks"),
            ("MEDYA", "media", "Spotify + YouTube Music"),
            ("TOPLANTI", "meeting", "WhatsApp + Meet"),
            ("YAZI & BELGE", "writing", "Notion + Google Docs"),
            ("PLANLAMA", "planning", "Calendar + Tasks + Gmail + Drive"),
            ("TASARIM", "creative", "Figma + Canva + Drive"),
            ("İÇERİK ÜRETİMİ", "creator", "YouTube Studio + Docs + Canva"),
            ("GELİŞTİRME / DEVOPS", "devops", "VS Code + GitHub + Vercel"),
        ]
        for idx, (title, key, summary) in enumerate(profile_cards):
            card = tk.Frame(profiles, bg="#0b1b21", highlightbackground="#173b43", highlightthickness=1)
            card.grid(row=idx // 2, column=idx % 2, sticky="ew", padx=4, pady=4)
            tk.Label(card, text=title, bg="#0b1b21", fg=C_PRI,
                     font=font_body_bold(10)).pack(anchor="w", padx=10, pady=(8, 1))
            tk.Label(card, text=summary, bg="#0b1b21", fg="#82aaa8",
                     font=font_body(8)).pack(anchor="w", padx=10)
            self._quick_action_button(card, "AÇ", lambda profile=key: self._launch_app_profile(profile)).pack(
                anchor="e", padx=8, pady=(3, 8)
            )
        profiles.columnconfigure(0, weight=1)
        profiles.columnconfigure(1, weight=1)

        section = tk.Frame(window, bg="#071111")
        section.pack(fill="both", expand=True, padx=18, pady=(2, 8))
        header = tk.Frame(section, bg="#071111")
        header.pack(fill="x", pady=(0, 7))
        tk.Label(header, text="FAVORİ UYGULAMALAR", bg="#071111", fg=C_TEXT,
                 font=font_body_bold(10)).pack(side="left")
        apps_frame = tk.Frame(section, bg="#071111")
        apps_frame.pack(fill="both", expand=True)
        favorites = load_preferences()

        def render_favorites():
            for child in apps_frame.winfo_children():
                child.destroy()
            for index, app_name in enumerate(favorites):
                row = tk.Frame(apps_frame, bg="#0a171b", highlightbackground="#123238", highlightthickness=1)
                row.grid(row=index // 3, column=index % 3, sticky="ew", padx=4, pady=4)
                tk.Label(row, text=app_name, bg="#0a171b", fg=C_TEXT,
                         font=font_body_bold(9)).pack(fill="x", padx=8, pady=(8, 3))
                controls = tk.Frame(row, bg="#0a171b")
                controls.pack(fill="x", padx=5, pady=(0, 5))
                self._quick_action_button(controls, "BAŞLAT", lambda app=app_name: self._launch_favorite_app(app)).pack(
                    side="left", fill="x", expand=True, padx=2
                )
                tk.Button(controls, text="×", command=lambda app=app_name: remove_favorite(app),
                          bg="#30151b", fg="#ff7289", relief="flat", bd=0, width=3,
                          font=font_body_bold(9)).pack(side="right", padx=2)
            for column in range(3):
                apps_frame.columnconfigure(column, weight=1)

        def add_favorite():
            app_name = simpledialog.askstring("Favori Ekle", "Windows uygulaması veya uygulama adı:", parent=window)
            app_name = (app_name or "").strip()
            if not app_name:
                return
            if any(item.casefold() == app_name.casefold() for item in favorites):
                messagebox.showinfo("App Hub", "Bu uygulama zaten favorilerde.", parent=window)
                return
            candidate = favorites + [app_name]
            if save_preferences(candidate):
                favorites[:] = candidate
                render_favorites()

        def remove_favorite(app_name):
            if app_name in favorites:
                candidate = [item for item in favorites if item != app_name]
                if save_preferences(candidate):
                    favorites[:] = candidate
                    render_favorites()

        self._quick_action_button(header, "+ UYGULAMA EKLE", add_favorite).pack(side="right")
        render_favorites()

    def _launch_favorite_app(self, app_name):
        try:
            from actions.open_app import open_app
            result = open_app(app_name)
            self.write_log(f"SYS: {result}")
            if "açılamadı" in result.lower() or "bulunamadı" in result.lower():
                messagebox.showwarning("App Hub", result, parent=self.root)
        except Exception as exc:
            self.write_log(f"ERR: {app_name} açılamadı: {exc}")

    def _launch_app_profile(self, profile):
        try:
            from actions.app_launcher_profiles import launch_app_profile
            result = launch_app_profile(profile)
            self.write_log(f"SYS: {result}")
        except Exception as exc:
            self.write_log(f"ERR: {profile} profili başlatılamadı: {exc}")

    def _open_focus_timer(self):
        existing = getattr(self, "_focus_timer_window", None)
        if existing is not None:
            try:
                if existing.winfo_exists():
                    existing.deiconify()
                    existing.lift()
                    return
            except tk.TclError:
                pass

        window = tk.Toplevel(self.root)
        self._focus_timer_window = window
        window.title("JARVIS V4 · Odak Zamanlayıcı")
        window.configure(bg="#071111")
        window.geometry("510x570")
        window.resizable(False, False)
        minutes = tk.IntVar(value=25)
        always_on_top = tk.BooleanVar(value=False)
        remaining = {"seconds": 25 * 60, "deadline": None, "job": None, "running": False}
        mode_label = tk.StringVar(value="ODAK SEANSI")
        status_label = tk.StringVar(value="Hazır olduğunda başlat.")

        def selected_minutes():
            try:
                value = max(1, min(120, int(minutes.get())))
            except (tk.TclError, TypeError, ValueError):
                value = 25
                minutes.set(value)
            return value

        tk.Label(window, text="FOCUS MODE", bg="#071111", fg=C_PRI,
                 font=font_display(18)).pack(pady=(18, 0))
        tk.Label(window, textvariable=mode_label, bg="#071111", fg=C_GREEN,
                 font=font_body_bold(10)).pack(pady=(3, 5))
        dial = tk.Canvas(window, width=300, height=270, bg="#071111", highlightthickness=0)
        dial.pack(pady=2)
        display = tk.Label(window, textvariable=status_label, bg="#071111", fg="#82aaa8",
                           font=font_body(9))
        display.pack(pady=(0, 12))

        def format_time(seconds):
            return f"{max(0, seconds) // 60:02d}:{max(0, seconds) % 60:02d}"

        def draw_timer():
            dial.delete("all")
            dial.create_oval(28, 18, 272, 262, outline="#173b43", width=8)
            total = selected_minutes() * 60
            fraction = max(0.0, min(1.0, remaining["seconds"] / total))
            dial.create_arc(28, 18, 272, 262, start=90, extent=-359.9 * fraction,
                            style="arc", outline=C_PRI, width=8)
            dial.create_text(150, 120, text=format_time(remaining["seconds"]),
                             fill=C_TEXT, font=("Consolas", 38, "bold"))
            dial.create_text(150, 162, text="DAKİKA : SANİYE", fill=C_MID,
                             font=font_body_bold(9))

        def stop_job():
            job = remaining.get("job")
            if job:
                try:
                    window.after_cancel(job)
                except tk.TclError:
                    pass
                remaining["job"] = None

        def finish_session():
            remaining["running"] = False
            remaining["deadline"] = None
            status_label.set("Seans tamamlandı. Mola zamanı!")
            draw_timer()
            self.write_log("SYS: Odak seansı tamamlandı.")
            try:
                self.sound.play_success()
            except Exception:
                pass
            try:
                from actions.windows_automation import show_toast_notification
                show_toast_notification("JARVIS V4 · Odak", "Odak seansı tamamlandı. Kısa mola verebilirsin.")
            except Exception:
                pass

        def tick():
            remaining["job"] = None
            if not remaining["running"] or remaining["deadline"] is None:
                return
            remaining["seconds"] = max(0, math.ceil(remaining["deadline"] - time.monotonic()))
            draw_timer()
            if remaining["seconds"] <= 0:
                finish_session()
            else:
                remaining["job"] = window.after(250, tick)

        def start_timer():
            if remaining["running"]:
                return
            if remaining["seconds"] <= 0:
                remaining["seconds"] = selected_minutes() * 60
            remaining["running"] = True
            remaining["deadline"] = time.monotonic() + remaining["seconds"]
            status_label.set("Odak açık · JARVIS seansı takip ediyor.")
            tick()

        def pause_timer():
            if not remaining["running"]:
                return
            remaining["seconds"] = max(0, math.ceil(remaining["deadline"] - time.monotonic()))
            remaining["running"] = False
            remaining["deadline"] = None
            stop_job()
            status_label.set("Duraklatıldı.")
            draw_timer()

        def reset_timer():
            remaining["running"] = False
            remaining["deadline"] = None
            stop_job()
            remaining["seconds"] = selected_minutes() * 60
            status_label.set("Hazır olduğunda başlat.")
            draw_timer()

        def set_preset(value, label):
            if remaining["running"]:
                pause_timer()
            minutes.set(value)
            remaining["seconds"] = value * 60
            mode_label.set(label)
            status_label.set("Hazır olduğunda başlat.")
            draw_timer()

        presets = tk.Frame(window, bg="#071111")
        presets.pack(fill="x", padx=24, pady=(0, 9))
        for label, value, mode in (("ODAK 25", 25, "ODAK SEANSI"),
                                   ("KISA MOLA 5", 5, "KISA MOLA"),
                                   ("UZUN MOLA 15", 15, "UZUN MOLA")):
            self._quick_action_button(presets, label,
                                      lambda v=value, m=mode: set_preset(v, m)).pack(
                side="left", fill="x", expand=True, padx=3
            )

        controls = tk.Frame(window, bg="#071111")
        controls.pack(fill="x", padx=24, pady=(0, 8))
        tk.Label(controls, text="ÖZEL DAKİKA", bg="#071111", fg=C_MID,
                 font=font_body_bold(8)).pack(side="left")
        spin = tk.Spinbox(controls, from_=1, to=120, width=5, textvariable=minutes,
                          bg="#0a171b", fg=C_TEXT, buttonbackground="#0a171b",
                          insertbackground=C_PRI, relief="flat", font=font_body(10))
        spin.pack(side="left", padx=8)
        spin.bind("<FocusOut>", lambda _event: reset_timer())
        self._quick_action_button(controls, "UYGULA", reset_timer).pack(side="left", padx=3)
        tk.Checkbutton(controls, text="Üstte tut", variable=always_on_top,
                       command=lambda: window.attributes("-topmost", always_on_top.get()),
                       bg="#071111", fg="#91b5b2", activebackground="#071111",
                       activeforeground=C_PRI, selectcolor="#0a171b", font=font_body(8)).pack(side="right")

        actions = tk.Frame(window, bg="#071111")
        actions.pack(fill="x", padx=24, pady=(0, 10))
        self._quick_action_button(actions, "BAŞLAT / DEVAM", start_timer).pack(side="left", fill="x", expand=True, padx=3)
        self._quick_action_button(actions, "DURAKLAT", pause_timer).pack(side="left", fill="x", expand=True, padx=3)
        self._quick_action_button(actions, "SIFIRLA", reset_timer).pack(side="left", fill="x", expand=True, padx=3)

        report = tk.Text(window, height=4, bg="#030909", fg="#82aaa8", relief="flat",
                         font=font_body(8), wrap="word", padx=9, pady=7)
        report.pack(fill="x", padx=24, pady=(0, 12))
        report.insert("1.0", "Dikkat dağıtıcıları kapatmadan önce listele. Kapatma işlemi kullanıcı onayı olmadan yapılmaz.")
        report.configure(state="disabled")

        def scan_distractions():
            try:
                from actions.focus_guard import focus_guard
                result = focus_guard("report")
                report.configure(state="normal")
                report.delete("1.0", tk.END)
                report.insert("1.0", result)
                report.configure(state="disabled")
                self.write_log("SYS: Odak kontrolü tamamlandı.")
            except Exception as exc:
                self.write_log(f"ERR: Odak kontrolü çalışmadı: {exc}")

        self._quick_action_button(window, "DİKKAT DAĞITICILARI TARA", scan_distractions).pack(
            fill="x", padx=24, pady=(0, 16)
        )
        draw_timer()

        def close_timer():
            stop_job()
            remaining["running"] = False
            window.destroy()
            self._focus_timer_window = None

        window.protocol("WM_DELETE_WINDOW", close_timer)


    def _open_daily_brief(self):
        window = tk.Toplevel(self.root)
        window.title("JARVIS V4 · Günlük Brifing")
        window.configure(bg="#071111")
        window.geometry("740x560")
        window.minsize(620, 440)
        tk.Label(window, text="GÜNLÜK BRİFİNG", bg="#071111", fg=C_PRI,
                 font=font_display(16)).pack(anchor="w", padx=18, pady=(15, 3))
        tk.Label(window, text="İstediğin bölümleri seç; JARVIS bilgileri arka planda toplasın.",
                 bg="#071111", fg=C_MID, font=font_body(9)).pack(anchor="w", padx=18, pady=(0, 10))
        section_frame = tk.Frame(window, bg="#071111")
        section_frame.pack(fill="x", padx=14, pady=(0, 8))
        options = [("system", "Sistem"), ("weather", "Hava"), ("calendar", "Takvim"),
                   ("reminders", "Hatırlatıcılar"), ("email", "E-posta")]
        selected = {key: tk.BooleanVar(value=True) for key, _label in options}
        for index, (key, label) in enumerate(options):
            tk.Checkbutton(section_frame, text=label, variable=selected[key], bg="#071111", fg=C_TEXT,
                           activebackground="#071111", activeforeground=C_PRI,
                           selectcolor="#0a171b", font=font_body(9)).grid(row=0, column=index, padx=5, sticky="w")
        output = tk.Text(window, bg="#030909", fg="#cde3e1", insertbackground=C_PRI,
                         relief="flat", wrap="word", font=font_body(10), padx=12, pady=10)
        output.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        output.insert("1.0", "Brifingi oluşturmak için bölümleri seçip düğmeye bas.")
        output.configure(state="disabled")
        status = tk.StringVar(value="Hazır")
        tk.Label(window, textvariable=status, bg="#071111", fg=C_MID,
                 font=font_body(8)).pack(anchor="w", padx=18, pady=(0, 4))

        def collect():
            sections = [key for key, _label in options if selected[key].get()]
            if not sections:
                messagebox.showinfo("Günlük Brifing", "En az bir bölüm seç.", parent=window)
                return
            status.set("Bilgiler toplanıyor…")
            run_button.configure(state="disabled", text="TOPLANIYOR…")

            def worker():
                try:
                    from actions.daily_brief import daily_brief
                    result = daily_brief(",".join(sections))
                except Exception as exc:
                    result = f"Brifing hazırlanamadı: {exc}"

                def display():
                    try:
                        if not window.winfo_exists():
                            return
                    except tk.TclError:
                        return
                    output.configure(state="normal")
                    output.delete("1.0", tk.END)
                    output.insert("1.0", result)
                    output.configure(state="disabled")
                    status.set("Güncellendi")
                    run_button.configure(state="normal", text="BRİFİNGİ OLUŞTUR")
                    self.write_log("SYS: Günlük brifing hazır.")
                self._dispatch_ui(display)

            threading.Thread(target=worker, daemon=True).start()

        run_row = tk.Frame(window, bg="#071111")
        run_row.pack(fill="x", padx=16, pady=(0, 15))
        run_button = self._quick_action_button(run_row, "BRİFİNGİ OLUŞTUR", collect)
        run_button.pack(side="left")

    def _open_clipboard_panel(self):
        window = tk.Toplevel(self.root)
        window.title("JARVIS V4 · Pano Asistanı")
        window.configure(bg="#071111")
        window.geometry("700x500")
        window.minsize(560, 380)
        tk.Label(window, text="PANO ASİSTANI", bg="#071111", fg=C_PRI,
                 font=font_display(16)).pack(anchor="w", padx=18, pady=(15, 8))
        title_var = tk.StringVar(value="Pano notu")
        tk.Entry(window, textvariable=title_var, bg="#030909", fg=C_TEXT,
                 insertbackground=C_PRI, relief="flat", font=font_body(10)).pack(
            fill="x", padx=18, pady=(0, 9), ipady=6
        )
        output = tk.Text(window, bg="#030909", fg="#cde3e1", insertbackground=C_PRI,
                         relief="flat", wrap="word", font=font_body(10), padx=12, pady=10)
        output.pack(fill="both", expand=True, padx=18, pady=(0, 10))

        def run(action):
            try:
                from actions.clipboard_notes import clipboard_notes
                result = clipboard_notes(action, title=title_var.get().strip() or "Pano notu")
                output.delete("1.0", tk.END)
                output.insert("1.0", result)
                self.write_log("SYS: Pano asistanı " + ("notu yerel dosyaya kaydetti." if action == "save" else "panoyu okudu."))
            except Exception as exc:
                output.delete("1.0", tk.END)
                output.insert("1.0", f"Pano işlemi başarısız: {exc}")

        actions = tk.Frame(window, bg="#071111")
        actions.pack(fill="x", padx=18, pady=(0, 15))
        self._quick_action_button(actions, "PANODA NE VAR?", lambda: run("read")).pack(side="left", padx=(0, 7))
        self._quick_action_button(actions, "ÖZETLE", lambda: run("summary")).pack(side="left", padx=7)
        self._quick_action_button(actions, "YEREL NOTA KAYDET", lambda: run("save")).pack(side="right")
        output.insert("1.0", "Pano içeriği otomatik okunmaz. Görmek için ‘Panoda ne var?’ düğmesine bas.")

    def _open_backup_center(self):
        window = tk.Toplevel(self.root)
        window.title("JARVIS V4 · Yedek Merkezi")
        window.configure(bg="#071111")
        window.geometry("720x430")
        window.resizable(False, False)
        tk.Label(window, text="YEREL YEDEK MERKEZİ", bg="#071111", fg=C_PRI,
                 font=font_display(16)).pack(anchor="w", padx=18, pady=(15, 4))
        tk.Label(window, text="Kaynak yalnızca bu bilgisayarda, proje içindeki backups klasörüne kopyalanır.",
                 bg="#071111", fg=C_MID, font=font_body(9)).pack(anchor="w", padx=18, pady=(0, 12))
        default_source = BASE_DIR / "memory"
        source_var = tk.StringVar(value=str(default_source))
        tk.Label(window, text="YEDEK KAYNAĞI", bg="#071111", fg=C_TEXT,
                 font=font_body_bold(9)).pack(anchor="w", padx=18, pady=(3, 4))
        path_row = tk.Frame(window, bg="#071111")
        path_row.pack(fill="x", padx=18)
        tk.Entry(path_row, textvariable=source_var, bg="#030909", fg=C_TEXT,
                 insertbackground=C_PRI, relief="flat", font=font_body(9)).pack(side="left", fill="x", expand=True, ipady=7)

        def choose_source():
            chosen = filedialog.askdirectory(parent=window, title="Yedeklenecek klasörü seç")
            if chosen:
                source_var.set(chosen)

        self._quick_action_button(path_row, "SEÇ", choose_source).pack(side="left", padx=(7, 0))
        output = tk.Text(window, height=9, bg="#030909", fg="#cde3e1", relief="flat",
                         wrap="word", font=font_body(9), padx=10, pady=8)
        output.pack(fill="both", expand=True, padx=18, pady=12)

        def show_result(result):
            try:
                if not window.winfo_exists():
                    return
                output.delete("1.0", tk.END)
                output.insert("1.0", result)
            except tk.TclError:
                pass

        def plan_backup():
            source = source_var.get().strip()
            show_result("Yedek planı hazırlanıyor…")

            def worker():
                try:
                    from actions.backup_manager import backup_manager
                    result = backup_manager("plan", source=source)
                except Exception as exc:
                    result = f"Yedek planı oluşturulamadı: {exc}"
                self._dispatch_ui(show_result, result)

            threading.Thread(target=worker, daemon=True).start()

        def run_backup():
            source = source_var.get().strip()
            if not source:
                messagebox.showwarning("Yedek Merkezi", "Önce kaynak klasörü seç.", parent=window)
                return
            if not messagebox.askyesno("Yerel Yedek", f"Bu klasörü proje içindeki backups klasörüne kopyalayayım mı?\n\n{source}", parent=window):
                return
            show_result("Yedek hazırlanıyor…")

            def worker():
                try:
                    from actions.backup_manager import backup_manager
                    result = backup_manager("backup", source=source, confirm=True)
                except Exception as exc:
                    result = f"Yedek alınamadı: {exc}"
                self._dispatch_ui(show_result, result)
            threading.Thread(target=worker, daemon=True).start()

        footer = tk.Frame(window, bg="#071111")
        footer.pack(fill="x", padx=18, pady=(0, 15))
        self._quick_action_button(footer, "PLANI GÖR", plan_backup).pack(side="left")
        self._quick_action_button(footer, "YEDEK AL", run_backup).pack(side="right")

    def _open_quick_notes(self):
        notes_path = BASE_DIR / "memory" / "quick_notes.json"
        window = tk.Toplevel(self.root)
        window.title("JARVIS V4 · Hızlı Notlar")
        window.configure(bg="#071111")
        window.geometry("680x430")
        window.minsize(560, 360)
        selected_id = {"value": ""}
        visible_rows = []
        filter_var = tk.StringVar()

        tk.Label(window, text="HIZLI NOTLAR", bg="#071111", fg=C_PRI,
                 font=font_display(16)).pack(anchor="w", padx=16, pady=(14, 8))
        search_entry = tk.Entry(window, textvariable=filter_var, bg="#030909", fg=C_TEXT,
                                insertbackground=C_PRI, relief="flat", font=font_body(10))
        search_entry.pack(fill="x", padx=16, pady=(0, 9), ipady=6)
        body = tk.Frame(window, bg="#071111")
        body.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        listing = tk.Listbox(body, width=27, bg="#030909", fg=C_TEXT, selectbackground=C_MID,
                             selectforeground="#FFFFFF", relief="flat", font=font_body(9))
        listing.pack(side="left", fill="y", padx=(0, 10))
        editor = tk.Text(body, bg="#030909", fg="#d8e8e6", insertbackground=C_PRI,
                         relief="flat", wrap="word", font=font_body(11), padx=10, pady=8)
        editor.pack(side="left", fill="both", expand=True)

        def read_notes():
            try:
                rows = json.loads(notes_path.read_text(encoding="utf-8"))
                return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
            except (OSError, json.JSONDecodeError):
                return []

        def refresh():
            listing.delete(0, tk.END)
            query = filter_var.get().strip().casefold()
            visible_rows[:] = [row for row in read_notes()
                               if query in str(row.get("text", "")).casefold()]
            for row in visible_rows:
                text = " ".join(str(row.get("text", "")).split())
                listing.insert(tk.END, text[:42] or "Boş not")

        def select_note(_event=None):
            selection = listing.curselection()
            if not selection or selection[0] >= len(visible_rows):
                return
            row = visible_rows[selection[0]]
            selected_id["value"] = str(row.get("id", ""))
            editor.delete("1.0", tk.END)
            editor.insert("1.0", str(row.get("text", "")))

        def save_note():
            text = editor.get("1.0", "end-1c").strip()
            if not text:
                messagebox.showinfo("Hızlı Notlar", "Önce not metnini yaz.", parent=window)
                return
            try:
                from actions.quick_notes import quick_note
                note_id = selected_id["value"]
                result = quick_note("update" if note_id else "add", text=text, note_id=note_id)
                if not note_id:
                    editor.delete("1.0", tk.END)
                refresh()
                self.write_log(f"SYS: {result}")
            except Exception as exc:
                messagebox.showerror("Hızlı Notlar", str(exc), parent=window)

        def delete_note():
            note_id = selected_id["value"]
            if not note_id:
                return
            if not messagebox.askyesno("Notu Sil", "Seçili not silinsin mi?", parent=window):
                return
            try:
                from actions.quick_notes import quick_note
                result = quick_note("delete", note_id=note_id)
                selected_id["value"] = ""
                editor.delete("1.0", tk.END)
                refresh()
                self.write_log(f"SYS: {result}")
            except Exception as exc:
                messagebox.showerror("Not silinemedi", str(exc), parent=window)

        listing.bind("<<ListboxSelect>>", select_note)
        filter_var.trace_add("write", lambda *_: refresh())
        footer = tk.Frame(window, bg="#071111")
        footer.pack(fill="x", padx=16, pady=(0, 14))
        self._quick_action_button(footer, "YENİ NOT", lambda: (selected_id.update(value=""), editor.delete("1.0", tk.END))).pack(side="left", padx=(0, 6))
        self._quick_action_button(footer, "KAYDET", save_note).pack(side="left", padx=6)
        self._quick_action_button(footer, "SEÇİLİ NOTU SİL", delete_note).pack(side="left", padx=6)
        self._quick_action_button(footer, "YENİLE", refresh).pack(side="right")
        refresh()

    def _open_windows_tools(self):
        window = tk.Toplevel(self.root)
        window.title("JARVIS V4 · Windows Araçları")
        window.configure(bg="#071111")
        window.geometry("600x590")
        window.minsize(540, 500)
        tk.Label(window, text="WINDOWS KONTROL MERKEZİ", bg="#071111", fg=C_PRI,
                 font=font_display(14)).pack(anchor="w", padx=18, pady=(16, 4))
        tk.Label(window, text="Pencere, ses ve ekran araçları", bg="#071111", fg=C_MID,
                 font=font_body(9)).pack(anchor="w", padx=18, pady=(0, 12))
        grid = tk.Frame(window, bg="#071111")
        grid.pack(fill="both", expand=True, padx=14, pady=4)

        def run_action(label, action):
            try:
                result = action()
                if result is None:
                    return
                self.write_log(f"SYS: {result}")
                messagebox.showinfo(label, result, parent=window)
            except Exception as exc:
                self.write_log(f"ERR: {label}: {exc}")
                messagebox.showerror(label, str(exc), parent=window)

        def snap(action):
            from actions.window_snap import window_snap
            return window_snap(action)

        def ask_volume():
            level = simpledialog.askinteger("Ana Ses", "Ses düzeyi (0–100):", parent=window,
                                            minvalue=0, maxvalue=100)
            if level is not None:
                from actions.windows_automation import windows_system_control
                return windows_system_control("set_volume", level=level)

        def ask_brightness():
            level = simpledialog.askinteger("Ekran Parlaklığı", "Parlaklık (0–100):", parent=window,
                                            minvalue=0, maxvalue=100)
            if level is not None:
                from actions.windows_automation import windows_system_control
                return windows_system_control("set_brightness", level=level)

        def ask_focus():
            title = simpledialog.askstring("Pencereyi Öne Getir", "Pencere başlığında geçen metin:", parent=window)
            if title:
                from actions.windows_automation import windows_system_control
                return windows_system_control("focus_window", query=title)

        def ask_close_window():
            title = simpledialog.askstring("Pencereyi Kapat", "Kapatılacak pencere başlığında geçen metin:", parent=window)
            if not title:
                return None
            if not messagebox.askyesno("Pencereyi Kapat", f"‘{title}’ eşleşen pencereye kapatma isteği gönderilsin mi?", parent=window):
                return None
            return control("close_window", query=title)

        def open_windows_settings():
            if os.name != "nt":
                raise OSError("Windows Ayarları yalnızca Windows üzerinde açılabilir.")
            os.startfile("ms-settings:")
            return "Windows Ayarları açıldı."

        def lock_workstation():
            if os.name != "nt":
                raise OSError("Ekran kilidi yalnızca Windows üzerinde kullanılabilir.")
            import ctypes
            if not ctypes.windll.user32.LockWorkStation():
                raise OSError("Windows oturumu kilitlenemedi.")
            return "Windows oturumu kilitlendi."

        def control(action, **kwargs):
            from actions.windows_automation import windows_system_control
            return windows_system_control(action, **kwargs)

        actions = [
            ("AÇIK PENCERELER", lambda: __import__("actions.windows_automation", fromlist=["windows_system_control"]).windows_system_control("list_windows")),
            ("PENCEREYİ ÖNE GETİR", ask_focus),
            ("PENCEREYİ KAPAT…", ask_close_window),
            ("SOL YARIM EKRAN", lambda: snap("left")),
            ("SAĞ YARIM EKRAN", lambda: snap("right")),
            ("AKTİF PENCEREYİ KÜÇÜLT", lambda: snap("minimize")),
            ("MASAÜSTÜNÜ GÖSTER", lambda: snap("desktop")),
            ("AKTİF PENCEREYİ BÜYÜT", lambda: snap("maximize")),
            ("ANA SESİ AYARLA", ask_volume),
            ("SESİ SESSİZE AL / AÇ", lambda: control("mute")),
            ("SES DURUMU", lambda: control("get_volume")),
            ("PARLAKLIĞI AYARLA", ask_brightness),
            ("PARLAKLIK DURUMU", lambda: control("get_brightness")),
            ("PİL VE GÜÇ DURUMU", lambda: control("power_status")),
            ("WINDOWS AYARLARI", open_windows_settings),
            ("BİLGİSAYARI KİLİTLE", lock_workstation),
        ]
        for index, (label, action) in enumerate(actions):
            btn = self._quick_action_button(grid, label, lambda name=label, fn=action: run_action(name, fn))
            btn.grid(row=index // 2, column=index % 2, sticky="ew", padx=4, pady=4, ipady=12)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

    def _quick_action_button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, bg="#0d2022", fg=C_PRI,
                         activebackground="#153739", activeforeground="#ffffff",
                         relief="flat", bd=1, cursor="hand2", font=font_body_bold(9), padx=10, pady=8)

    def _sync_vector_memory(self):
        try:
            from memory.vector_memory import _vector_store
            msg = _vector_store.index_all_sources()
            self.write_log(f"SYS: {msg}")
        except Exception as exc:
            self.write_log(f"ERR: Vektör senkronizasyon hatası: {exc}")

    def apply_theme(self, theme_key: str):
        if theme_key == "custom":
            try:
                from core.settings_store import get_setting
                t = _custom_palette(get_setting("ui", "custom_primary", "#00d4c0"))
            except Exception:
                t = _custom_palette("#00d4c0")
        elif theme_key in THEME_PALETTES:
            t = THEME_PALETTES[theme_key]
        else:
            return
        self.current_theme = theme_key
        global C_PRI, C_MID, C_TEXT, C_DIM, C_GREEN, C_BLUE, C_BG
        C_PRI = t["pri"]
        C_MID = t["mid"]
        C_TEXT = t["text"]
        C_DIM = t["dim"]
        C_GREEN = t["accent"]
        C_BLUE = t.get("pri", C_BLUE)
        STATE_HEX_COLORS["LISTENING"] = C_GREEN
        STATE_HEX_COLORS["SPEAKING"] = C_BLUE
        ORB_COLORS["LISTENING"] = t.get("orb", (0, 255, 136))
        for name in ("_settings_sfx_label", "_settings_visual_label"):
            label = getattr(self, name, None)
            if label is not None:
                label.configure(fg=C_PRI)
        try:
            from core.settings_store import set_setting
            set_setting("ui", "active_theme", theme_key)
        except Exception:
            pass
        self._draw_settings_button()
        self._draw_settings_tabs()
        for canvas_name, draw_name in (
            ("_api_canvas", "_draw_api_button"),
            ("_sfx_canvas", "_draw_sfx_button"),
            ("_autostart_canvas", "_draw_autostart_button"),
            ("_shortcut_canvas", "_draw_shortcut_button"),
            ("_motion_canvas", "_draw_motion_button"),
            ("_effects_mode_canvas", "_draw_effects_mode_button"),
            ("_paranoid_canvas", "_draw_paranoid_button"),
            ("_air_gestures_canvas", "_draw_air_gestures_button"),
            ("_self_healing_canvas", "_draw_self_healing_button"),
            ("_ghost_typer_canvas", "_draw_ghost_typer_button"),
            ("_terminate_canvas", "_draw_terminate_button"),
        ):
            if hasattr(self, canvas_name):
                try:
                    getattr(self, draw_name)()
                except Exception:
                    pass
        for label_name, color in (("_settings_status_primary", C_TEXT),
                                  ("_settings_status_secondary", C_MID),
                                  ("_settings_sfx_label", C_PRI),
                                  ("_settings_visual_label", C_PRI),
                                  ("_volume_label", C_PRI), ("_voice_label", C_MID)):
            label = getattr(self, label_name, None)
            if label is not None:
                label.configure(fg=color)
        if hasattr(self, "_volume_scale"):
            self._volume_scale.configure(fg=C_TEXT, activebackground=C_PRI)
        if hasattr(self, "_voice_menu"):
            self._voice_menu.configure(fg=C_PRI, activebackground=C_PRI)
            self._voice_menu["menu"].configure(fg=C_PRI, activebackground=C_PRI)
        self._draw()
        self.write_log(f"SYS: Arayüz teması güncellendi: {t['name']}")

    def _layout_settings_controls(self):
        inner_w = self._settings_geometry["panel_w"] - 24
        self._api_canvas.place(x=0, y=2)
        self._sfx_canvas.place(x=inner_w - int(self._sfx_canvas["width"]) - 4, y=0)
        self._settings_status_primary.place(x=0, y=36, width=inner_w)
        self._settings_status_secondary.place(x=0, y=54, width=inner_w)
        for rule, y in zip(self._settings_rules, (78, 186)):
            rule.place(x=0, y=y, width=inner_w)
        self._settings_sfx_label.place(x=0, y=82)
        self._volume_label.place(x=0, y=102)
        self._volume_scale.place(x=0, y=122, width=inner_w, height=24)
        self._voice_label.place(x=0, y=156)
        self._voice_menu.place(x=88, y=152, width=inner_w - 88, height=26)
        self._settings_visual_label.place(x=0, y=192)
        self._autostart_canvas.place(x=0, y=214, width=inner_w, height=26)
        self._shortcut_canvas.place(x=0, y=244, width=inner_w, height=26)
        self._motion_canvas.place(x=0, y=274, width=inner_w, height=26)
        self._effects_mode_canvas.place(x=0, y=304, width=inner_w, height=24)

        if hasattr(self, "_settings_security_rule"):
            self._settings_security_rule.place(x=0, y=334, width=inner_w)
        if hasattr(self, "_settings_security_label"):
            self._settings_security_label.place(x=0, y=340)

        half_w = (inner_w - 6) // 2
        if hasattr(self, "_paranoid_canvas"):
            self._paranoid_canvas.configure(width=half_w, height=28); self._paranoid_canvas.place(x=0, y=362, width=half_w, height=28); self._draw_paranoid_button()
        if hasattr(self, "_air_gestures_canvas"):
            self._air_gestures_canvas.configure(width=half_w, height=28); self._air_gestures_canvas.place(x=half_w + 6, y=362, width=half_w, height=28); self._draw_air_gestures_button()

        if hasattr(self, "_face_setup_canvas"):
            self._face_setup_canvas.place(x=0, y=392, width=inner_w, height=26)
            next_y = 422
        else:
            next_y = 398

        if hasattr(self, "_self_healing_canvas"):
            self._self_healing_canvas.configure(width=inner_w, height=28); self._self_healing_canvas.place(x=0, y=next_y, width=inner_w, height=28); self._draw_self_healing_button()
            next_y += 34
        if hasattr(self, "_ghost_typer_canvas"):
            self._ghost_typer_canvas.configure(width=inner_w, height=28); self._ghost_typer_canvas.place(x=0, y=next_y, width=inner_w, height=28); self._draw_ghost_typer_button()
            next_y += 34
        if hasattr(self, "_terminate_canvas"):
            self._terminate_canvas.configure(width=inner_w, height=28); self._terminate_canvas.place(x=0, y=next_y, width=inner_w, height=28); self._draw_terminate_button()

    def _refresh_settings_status(self):
        if not hasattr(self, "_settings_status_primary"):
            return
        cfg = load_app_config()
        gemini_ready = bool(str(cfg.get("gemini_api_key", "") or "").strip())
        primary = "Gemini hazir" if gemini_ready else "Gemini API eksik"
        self._settings_status_primary.configure(text=primary)
        youtube_ready = bool(str(cfg.get("youtube_api_key", "") or "").strip())
        self._settings_status_secondary.configure(
            text="YouTube API hazır" if youtube_ready else "YouTube API isteğe bağlı"
        )

    def write_debug(self, text: str, level: str = "INFO"):
        if threading.get_ident() != self._tk_thread_id:
            self._dispatch_ui(self.write_debug, text, level)
            return
        clean = " ".join(str(text or "").split())
        if not clean:
            return
        self.root.after(0, self._append_debug_entry, clean, level)

    def _append_debug_entry(self, text: str, level: str = "INFO"):
        stamp = time.strftime("%H:%M:%S")
        lvl = (level or "INFO").upper()
        self._debug_entries.append((lvl, f"[{stamp}] {lvl}: {text}"))
        self._render_debug_logs()

    def _render_debug_logs(self):
        if not hasattr(self, "_debug_text"):
            return
        self._debug_text.configure(state="normal")
        self._debug_text.delete("1.0", tk.END)
        if not self._debug_entries:
            self._debug_text.insert(tk.END, "Henüz not edilebilir hata yok.\n", "info")
        else:
            for level, line in self._debug_entries:
                tag = "err" if level == "ERROR" else "warn" if level == "WARN" else "info"
                self._debug_text.insert(tk.END, line + "\n", tag)
        self._debug_text.see(tk.END)
        self._debug_text.configure(state="disabled"); self._bind_smooth_scroll(self._debug_text)

    def _build_api_button(self, parent=None):
        parent = parent or self.root
        bw, bh = 154, 28
        self._api_canvas = tk.Canvas(
            parent, width=bw, height=bh,
            bg=parent.cget("bg"), highlightthickness=0, cursor="hand2")
        self._api_canvas.bind("<Button-1>", lambda e: self._open_api_settings())
        self._draw_api_button()

    def _draw_api_button(self):
        c = self._api_canvas
        bw = int(c["width"])
        bh = int(c["height"])
        c.delete("all")
        self._draw_smooth_rounded_rect(c, 2, 2, bw - 2, bh - 2, radius=8, fill="#04121a", outline=C_BLUE, width=1); c.create_text(bw // 2, bh // 2, text="⚙ API SETTINGS", fill=C_BLUE, font=font_body_bold(9)); return
        for bx, by, sx, sy in [(0, 0, 1, 1), (bw, 0, -1, 1), (0, bh, 1, -1), (bw, bh, -1, -1)]:
            c.create_line(bx, by, bx + sx * bl, by, fill=C_BLUE, width=1)
            c.create_line(bx, by, bx, by + sy * bl, fill=C_BLUE, width=1)
        c.create_text(bw // 2, bh // 2, text="⚙ API SETTINGS",
                      fill=C_BLUE, font=font_body_bold(10))

    def _build_fx_slider(self, parent=None):
        parent = parent or self.root
        slider_w = 280
        self._volume_label = tk.Label(
            parent,
            text=f"FX LEVEL  {int(self.sound.get_volume() * 100)}%",
            fg=C_PRI,
            bg=parent.cget("bg"),
            font=font_body_bold(10),
        )
        self._volume_scale = tk.Scale(
            parent,
            from_=0,
            to=100,
            orient="horizontal",
            length=slider_w,
            showvalue=False,
            resolution=1,
            troughcolor="#071818",
            bg=parent.cget("bg"),
            fg=C_TEXT,
            activebackground=C_PRI,
            highlightthickness=0,
            borderwidth=0,
            sliderlength=18,
            width=10,
            command=self._on_volume_change,
        )
        self._volume_scale.set(int(self.sound.get_volume() * 100))

    def _on_volume_change(self, value):
        try:
            volume = max(0, min(100, int(float(value))))
        except (TypeError, ValueError):
            return
        self._volume_label.configure(text=f"FX LEVEL  {volume}%")
        self.sound.set_volume(volume / 100.0)
        self._fx_volume_preference = volume / 100.0
        job = getattr(self, "_volume_save_job", None)
        if job:
            try:
                self.root.after_cancel(job)
            except tk.TclError:
                pass
        self._volume_save_job = self.root.after(350, self._persist_fx_volume)

    def _persist_fx_volume(self):
        self._volume_save_job = None
        try:
            from core.settings_store import set_setting
            set_setting("ui", "fx_volume", self._fx_volume_preference)
        except Exception as exc:
            self.write_log(f"ERR: Ses düzeyi tercihi kaydedilemedi: {exc}")

    # ── Autostart toggle ─────────────────────────────────────────────────────
    def _autostart_plist_dst(self) -> Path:
        # Windows: Başlangıç klasöründeki kısayol (macOS LaunchAgent karşılığı)
        from make_shortcut import startup_shortcut_path
        return startup_shortcut_path()

    def _build_autostart_plist(self) -> str:
        """LaunchAgent plist'ini bu makineye göre DİNAMİK üretir.
        Sabit kullanıcı yolu (örn. /Users/...) gömmez; her bilgisayarda çalışır."""
        import sys
        python_exe = sys.executable or "/usr/bin/python3"
        py_dir     = str(Path(python_exe).parent)
        main_py    = BASE_DIR / "main.py"
        out_log    = BASE_DIR / "jarvis.log"
        err_log    = BASE_DIR / "jarvis_error.log"
        home       = Path.home()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.alp.jarvis</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_exe}</string>
        <string>{main_py}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{BASE_DIR}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>{out_log}</string>
    <key>StandardErrorPath</key>
    <string>{err_log}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>{py_dir}:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>HOME</key>
        <string>{home}</string>
    </dict>
</dict>
</plist>
"""

    def _is_autostart_installed(self) -> bool:
        return self._autostart_plist_dst().exists()

    def _build_autostart_button(self, parent=None):
        parent = parent or self.root
        self._autostart_canvas = tk.Canvas(
            parent, height=30,
            bg=parent.cget("bg"), highlightthickness=0, cursor="hand2"
        )
        self._autostart_canvas.bind("<Button-1>", lambda e: self._toggle_autostart())
        self._draw_autostart_button()

    def _draw_autostart_button(self):
        c = self._autostart_canvas
        bw = int(c["width"]) if int(c["width"]) > 1 else 296
        bh = int(c["height"])
        c.delete("all")
        on = self._is_autostart_installed()
        col  = C_GREEN if on else C_MID
        icon = "◉" if on else "○"
        text = f"{icon}  AÇILIŞTA BAŞLAT  {'[AÇIK]' if on else '[KAPALI]'}"; bg_col = "#041a14" if on else "#021212"; self._draw_smooth_rounded_rect(c, 2, 2, bw - 2, bh - 2, radius=8, fill=bg_col, outline=col, width=1); c.create_text(bw // 2, bh // 2, text=text, fill=col, font=font_body_bold(9)); return
        bg_col = "#041a14" if state == "ok" else "#1a080a" if state == "err" else "#021212"; self._draw_smooth_rounded_rect(c, 2, 2, bw - 2, bh - 2, radius=8, fill=bg_col, outline=col, width=1); c.create_text(bw // 2, bh // 2, text=f"{icon}  {label}", fill=col, font=font_body_bold(9)); return
        for bx, by, sx, sy in [(0, 0, 1, 1), (bw, 0, -1, 1),
                                (0, bh, 1, -1), (bw, bh, -1, -1)]:
            c.create_line(bx, by, bx+sx*bl, by, fill=col, width=2)
            c.create_line(bx, by, bx, by+sy*bl, fill=col, width=2)
        c.create_text(bw//2, bh//2, text=text, fill=col, font=font_body_bold(10))

    def _toggle_autostart(self):
        try:
            from make_shortcut import create_startup_shortcut, remove_startup_shortcut
            if self._is_autostart_installed():
                remove_startup_shortcut()
                self.write_log("SYS: Otomatik başlatma kapatıldı.")
            else:
                create_startup_shortcut()
                self.write_log("SYS: Otomatik başlatma açıldı. Windows açılışında JARVIS başlar.")
        except Exception as exc:
            self.write_log(f"SYS: Autostart hatası — {exc}")
        finally:
            self.root.after(0, self._draw_autostart_button)

    # ── Desktop shortcut button ──────────────────────────────────────────────
    def _build_shortcut_button(self, parent=None):
        parent = parent or self.root
        self._shortcut_canvas = tk.Canvas(
            parent, height=30,
            bg=parent.cget("bg"), highlightthickness=0, cursor="hand2"
        )
        self._shortcut_canvas.bind("<Button-1>", lambda e: self._create_desktop_shortcut())
        self._draw_shortcut_button()

    def _draw_shortcut_button(self, state: str = "idle"):
        c = self._shortcut_canvas
        bw = int(c["width"]) if int(c["width"]) > 1 else 296
        bh = int(c["height"])
        c.delete("all")
        if state == "ok":
            col, icon, label = C_GREEN, "✓", "MASAÜSTÜ KISAYOLU OLUŞTURULDU"
        elif state == "err":
            col, icon, label = C_RED,   "✕", "HATA — KISAYOL OLUŞTURULAMADI"
        else:
            col, icon, label = C_MID,   "⊞", "MASAÜSTÜNE KISAYOL EKLE"
        bg_col = "#041a14" if state == "ok" else "#1a080a" if state == "err" else "#021212"; self._draw_smooth_rounded_rect(c, 2, 2, bw - 2, bh - 2, radius=8, fill=bg_col, outline=col, width=1); c.create_text(bw // 2, bh // 2, text=f"{icon}  {label}", fill=col, font=font_body_bold(9)); return
        for bx, by, sx, sy in [(0, 0, 1, 1), (bw, 0, -1, 1),
                                (0, bh, 1, -1), (bw, bh, -1, -1)]:
            c.create_line(bx, by, bx+sx*bl, by, fill=col, width=2)
            c.create_line(bx, by, bx, by+sy*bl, fill=col, width=2)
        c.create_text(bw//2, bh//2, text=f"{icon}  {label}",
                      fill=col, font=font_body_bold(10))

    def _create_desktop_shortcut(self):
        def _run():
            try:
                from make_shortcut import create_desktop_shortcut
                create_desktop_shortcut()
                self.write_log("SYS: Masaüstü kısayolu oluşturuldu → JARVIS.lnk")
                state = "ok"
            except Exception as exc:
                self.write_log(f"SYS: Kısayol hatası — {exc}")
                state = "err"

            def show_state():
                try:
                    if not self.root.winfo_exists():
                        return
                    self._draw_shortcut_button(state)
                    self.root.after(3000, self._draw_shortcut_button, "idle")
                except tk.TclError:
                    pass
            self._dispatch_ui(show_state)

        threading.Thread(target=_run, daemon=True).start()

    def _play_startup_sfx_once(self):
        if self._startup_sfx_played:
            return
        self._startup_sfx_played = True
        if self._effects_active:
            self.sound.play_startup()

    def _sync_sound_state(self):
        enabled = self._sfx_on and not self.paused
        self.sound.set_enabled(enabled)
        if enabled and self._jarvis_state == "THINKING":
            self.sound.start_thinking()
        if enabled != self._effects_active:
            self._effects_active = enabled
            if self.on_effects_state_change:
                threading.Thread(
                    target=self.on_effects_state_change,
                    args=(enabled,),
                    daemon=True,
                ).start()

    def _open_api_settings(self):
        self._show_setup_ui(edit_mode=self._api_key_ready)

    def _close_setup_ui(self):
        if self.setup_frame and self.setup_frame.winfo_exists():
            self.setup_frame.destroy()
        self.setup_frame = None
        self.api_entry = None
        self.youtube_api_entry = None
        self.youtube_handle_entry = None

    # ── SFX toggle ───────────────────────────────────────────────────────────
    def _build_sfx_button(self, parent=None):
        parent = parent or self.root
        BW, BH = 98, 36
        self._sfx_canvas = tk.Canvas(parent, width=BW, height=BH,
                                     bg=parent.cget("bg"), highlightthickness=0, cursor="hand2")
        self._sfx_canvas.bind("<Button-1>", lambda e: self._toggle_sfx())
        self._sfx_on = self._sfx_preference
        self._draw_sfx_button()

    def _draw_sfx_button(self):
        c = self._sfx_canvas
        BW = int(c["width"])
        BH = int(c["height"])
        c.delete("all")
        col  = C_PRI if self._sfx_on else C_MID
        text = "♪ SFX ON" if self._sfx_on else "♪ SFX OFF"; bg_col = "#041a18" if self._sfx_on else "#021212"; self._draw_smooth_rounded_rect(c, 2, 2, BW - 2, BH - 2, radius=8, fill=bg_col, outline=col, width=1); c.create_text(BW // 2, BH // 2, text=text, fill=col, font=font_body_bold(9)); return
        self._draw_smooth_rounded_rect(c, 2, 2, bw - 2, bh - 2, radius=8, fill="#04121a", outline=C_BLUE, width=1); c.create_text(bw // 2, bh // 2, text="⚙ API SETTINGS", fill=C_BLUE, font=font_body_bold(9)); return
        for bx, by, sx, sy in [(0, 0, 1, 1), (BW, 0, -1, 1),
                                (0, BH, 1, -1), (BW, BH, -1, -1)]:
            c.create_line(bx, by, bx+sx*bl, by, fill=col, width=1)
            c.create_line(bx, by, bx, by+sy*bl, fill=col, width=1)
        c.create_text(BW//2, BH//2, text=text, fill=col, font=font_body_bold(9))

    def _toggle_sfx(self):
        self._sfx_on = not self._sfx_on
        self._sfx_preference = self._sfx_on
        try:
            from core.settings_store import set_setting
            set_setting("ui", "sfx_enabled", self._sfx_on)
        except Exception as exc:
            self.write_log(f"ERR: Ses tercihi kaydedilemedi: {exc}")
        self._draw_sfx_button()
        self._sync_sound_state()

    def _build_motion_button(self, parent=None):
        parent = parent or self.root
        self._motion_canvas = tk.Canvas(parent, height=30, bg=parent.cget("bg"),
                                        highlightthickness=0, cursor="hand2")
        self._motion_canvas.bind("<Button-1>", lambda _event: self._toggle_reduce_motion())
        self._draw_motion_button()

    def _draw_motion_button(self):
        canvas = self._motion_canvas
        width, height = int(canvas["width"]), int(canvas["height"])
        if width < 2:
            width = self._settings_geometry["panel_w"] - 24
        canvas.delete("all")
        color = C_GREEN if self._reduce_motion else C_MID; bg_col = "#041a14" if self._reduce_motion else "#021212"; self._draw_smooth_rounded_rect(canvas, 2, 2, width - 2, height - 2, radius=8, fill=bg_col, outline=color, width=1); canvas.create_text(width // 2, height // 2, text=("◉  HAREKET AZALT  [AÇIK]" if self._reduce_motion else "○  HAREKET AZALT  [KAPALI]"), fill=color, font=font_body_bold(9)); return
        label = "◉  HAREKET AZALT  [AÇIK]" if self._reduce_motion else "○  HAREKET AZALT  [KAPALI]"
        for x, y, sx, sy in ((0, 0, 1, 1), (width, 0, -1, 1), (0, height, 1, -1), (width, height, -1, -1)):
            canvas.create_line(x, y, x + sx * 5, y, fill=color, width=1)
            canvas.create_line(x, y, x, y + sy * 5, fill=color, width=1)
        canvas.create_text(width // 2, height // 2, text=label, fill=color, font=font_body_bold(9))

    def _toggle_reduce_motion(self):
        self._reduce_motion = not self._reduce_motion
        try:
            from core.settings_store import set_setting
            set_setting("ui", "reduce_motion", self._reduce_motion)
        except Exception as exc:
            self.write_log(f"ERR: Görsel tercih kaydedilemedi: {exc}")
        self._draw_motion_button()
        self.write_log("SYS: Hareket azaltma " + ("açıldı." if self._reduce_motion else "kapatıldı."))

    def _build_effects_mode_button(self, parent=None):
        parent = parent or self.root
        self._effects_mode_canvas = tk.Canvas(parent, height=28, bg=parent.cget("bg"),
                                              highlightthickness=0, cursor="hand2")
        self._effects_mode_canvas.bind("<Button-1>", lambda _event: self._cycle_visual_effect_mode())
        self._draw_effects_mode_button()

    def _draw_effects_mode_button(self):
        canvas = self._effects_mode_canvas
        width, height = int(canvas["width"]), int(canvas["height"])
        if width < 2:
            width = self._settings_geometry["panel_w"] - 24
        labels = {"calm": "CALM", "standard": "STANDARD", "cinematic": "CINEMATIC"}
        label = labels.get(self._visual_effect_mode, "STANDARD")
        color = C_GREEN if self._visual_effect_mode == "cinematic" else C_PRI; bg_col = "#041a14" if self._visual_effect_mode == "cinematic" else "#031718"; canvas.delete("all"); self._draw_smooth_rounded_rect(canvas, 2, 2, width - 2, height - 2, radius=8, fill=bg_col, outline=color, width=1); canvas.create_text(width // 2, height // 2, text=f"✦  HUD EFEKT KİPİ  ·  {label}  ↻", fill=color, font=font_body_bold(8)); return
        canvas.delete("all")
        for x, y, sx, sy in ((0, 0, 1, 1), (width, 0, -1, 1), (0, height, 1, -1), (width, height, -1, -1)):
            canvas.create_line(x, y, x + sx * 5, y, fill=color, width=1)
            canvas.create_line(x, y, x, y + sy * 5, fill=color, width=1)
        canvas.create_text(width // 2, height // 2, text=f"✦  HUD EFEKT KİPİ  ·  {label}  ↻",
                           fill=color, font=font_body_bold(8))

    def _cycle_visual_effect_mode(self):
        modes = ("calm", "standard", "cinematic")
        self._visual_effect_mode = modes[(modes.index(self._visual_effect_mode) + 1) % len(modes)]
        try:
            from core.settings_store import set_setting
            set_setting("ui", "visual_effect_mode", self._visual_effect_mode)
        except Exception as exc:
            self.write_log(f"ERR: HUD efekti tercihi kaydedilemedi: {exc}")
        self._draw_effects_mode_button()
        self.write_log(f"SYS: HUD efekti: {self._visual_effect_mode.upper()}")

    # ── Voice selector ───────────────────────────────────────────────────────
    def _build_voice_selector(self, parent=None):
        parent = parent or self.root
        self._voice_var = tk.StringVar(value=self._current_voice)
        self._voice_label = tk.Label(parent, text="VOICE", fg=C_MID, bg=parent.cget("bg"),
                                     font=font_body_bold(8))

        self._voice_menu = tk.OptionMenu(parent, self._voice_var, *VOICES,
                                         command=self._on_voice_select)
        self._voice_menu.config(
            fg=C_PRI, bg=C_PANEL, activeforeground=C_BG,
            activebackground=C_PRI, font=font_body(10),
            borderwidth=0, highlightthickness=1,
            highlightbackground=C_MID, width=12)
        self._voice_menu["menu"].config(
            fg=C_PRI, bg=C_PANEL, font=font_body(10),
            activeforeground=C_BG, activebackground=C_PRI)

    def _on_voice_select(self, voice: str):
        self._current_voice = voice
        save_app_config({"voice": voice})
        if self.on_voice_change:
            threading.Thread(target=self.on_voice_change, args=(voice,), daemon=True).start()

    # ── Mute button ──────────────────────────────────────────────────────────
    def _build_mute_button(self):
        self._mute_canvas = tk.Canvas(self.root, width=126, height=36,
                                      bg=C_BG, highlightthickness=0, cursor="hand2")
        self._mute_canvas.bind("<Button-1>", lambda e: self._toggle_mute())
        self._draw_mute_button()

    def _draw_mute_button(self):
        c = self._mute_canvas
        bw = int(c["width"])
        bh = int(c["height"])
        c.delete("all")
        if self.muted:
            col, icon, lbl = C_MUTED, "🔇", " MUTED"
            bg_col = "#1a080d"
        else:
            col, icon, lbl = C_GREEN, "🎙", " LIVE"
            bg_col = "#031713"
        self._draw_smooth_rounded_rect(c, 2, 2, bw - 2, bh - 2, radius=10, fill=bg_col, outline=col, width=1)
        c.create_text(bw//2, bh//2, text=f"{icon}{lbl}",
                      fill=col, font=font_body_bold(10))

    def _build_pause_button(self):
        self._pause_canvas = tk.Canvas(self.root, width=126, height=36,
                                       bg=C_BG, highlightthickness=0, cursor="hand2")
        self._pause_canvas.bind("<Button-1>", lambda e: self._toggle_pause())
        self._draw_pause_button()

    def _draw_pause_button(self):
        c = self._pause_canvas
        bw = int(c["width"])
        bh = int(c["height"])
        c.delete("all")
        if self.paused:
            col, text, bg_col = C_GOLD, "▶ RESUME", "#1c1604"
        else:
            col, text, bg_col = C_BLUE, "⏸ PAUSE", "#051322"
        self._draw_smooth_rounded_rect(c, 2, 2, bw - 2, bh - 2, radius=10, fill=bg_col, outline=col, width=1)
        c.create_text(bw//2, bh//2, text=text, fill=col, font=font_body_bold(10))

    # ── Webcam toggle button ─────────────────────────────────────────────────
    def _build_webcam_button(self):
        self._cam_canvas = tk.Canvas(self.root, width=110, height=36,
                                     bg=C_BG, highlightthickness=0, cursor="hand2")
        self._cam_canvas.bind("<Button-1>", lambda e: self._toggle_webcam_ui())
        self._draw_webcam_button()

    def _draw_webcam_button(self):
        c = self._cam_canvas
        bw, bh = int(c["width"]), int(c["height"])
        c.delete("all")
        if self._webcam_active:
            col, text, bg_col = C_RED, "◉  CAM ON", "#1f090c"
        else:
            col, text, bg_col = C_MID, "◎  CAM", "#041414"
        self._draw_smooth_rounded_rect(c, 2, 2, bw - 2, bh - 2, radius=10, fill=bg_col, outline=col, width=1)
        c.create_text(bw//2, bh//2, text=text, fill=col, font=font_body_bold(10))

    def _toggle_webcam_ui(self):
        if self.on_webcam_toggle:
            self.on_webcam_toggle(not self._webcam_active)

    def _toggle_mute(self):
        self.muted = not self.muted
        self._draw_mute_button()
        if self.muted:
            self.write_log("SYS: Mikrofon kapatıldı.")
        else:
            self.write_log("SYS: Mikrofon açık.")
        self._sync_sound_state()

    # ── Orb tıklama = pause ──────────────────────────────────────────────────
    def _on_canvas_click(self, event):
        dx = event.x - self.FCX
        dy = event.y - self.FCY
        if dx*dx + dy*dy <= (self.FACE * 0.40)**2:
            self._toggle_pause()

    def _toggle_pause(self):
        self.paused = not self.paused
        self._draw_pause_button()
        if self.paused:
            self.set_state("PAUSED")
            self.write_log("SYS: JARVIS duraklatıldı.")
        else:
            self.set_state("THINKING")
            self.write_log("SYS: JARVIS devam ediyor...")
        self._sync_sound_state()
        if self.on_pause_toggle:
            threading.Thread(target=self.on_pause_toggle, args=(self.paused,), daemon=True).start()

    # ── Yeni Güvenlik & Otonom Kontroller ─────────────────────────────────────
    def _build_paranoid_button(self, parent=None):
        parent = parent or self.root
        self._paranoid_canvas = tk.Canvas(parent, height=30, bg=parent.cget("bg"), highlightthickness=0, cursor="hand2")
        self._paranoid_canvas.bind("<Button-1>", lambda e: self._open_paranoid_panel())
        self._draw_paranoid_button()

    def _draw_paranoid_button(self):
        c = self._paranoid_canvas
        w = c.winfo_width() if c.winfo_width() > 20 else (int(c["width"]) if int(c["width"]) > 1 else 150)
        h = int(c["height"])
        c.delete("all")
        try:
            from actions.paranoid_mode import get_paranoid_sentinel
            is_active = get_paranoid_sentinel().is_active
        except Exception:
            is_active = False
        col = C_GREEN if is_active else C_MID
        bg_col = "#041a14" if is_active else "#021212"
        self._draw_smooth_rounded_rect(c, 2, 2, w - 2, h - 2, radius=8, fill=bg_col, outline=col, width=1)
        txt = "🛡️ PARANOID [ON]" if is_active else "🛡️ PARANOID [OFF]"
        c.create_text(w // 2, h // 2, text=txt, fill=col, font=font_body_bold(8))

    def _build_air_gestures_button(self, parent=None):
        parent = parent or self.root
        self._air_gestures_canvas = tk.Canvas(parent, height=30, bg=parent.cget("bg"), highlightthickness=0, cursor="hand2")
        self._air_gestures_canvas.bind("<Button-1>", lambda e: self._toggle_air_gestures_ui())
        self._draw_air_gestures_button()

    def _draw_air_gestures_button(self):
        c = self._air_gestures_canvas
        w = c.winfo_width() if c.winfo_width() > 20 else (int(c["width"]) if int(c["width"]) > 1 else 150)
        h = int(c["height"])
        c.delete("all")
        try:
            from actions.air_gestures import get_air_gesture_controller
            is_active = get_air_gesture_controller().is_running()
        except Exception:
            is_active = False
        col = C_GREEN if is_active else C_MID
        bg_col = "#041a14" if is_active else "#021212"
        self._draw_smooth_rounded_rect(c, 2, 2, w - 2, h - 2, radius=8, fill=bg_col, outline=col, width=1)
        txt = "🖐️ GESTURES [ON]" if is_active else "🖐️ GESTURES [OFF]"
        c.create_text(w // 2, h // 2, text=txt, fill=col, font=font_body_bold(8))

    def _build_self_healing_button(self, parent=None):
        parent = parent or self.root
        self._self_healing_canvas = tk.Canvas(parent, height=28, bg=parent.cget("bg"), highlightthickness=0, cursor="hand2")
        self._self_healing_canvas.bind("<Button-1>", lambda e: self._run_self_healing_ui())
        self._draw_self_healing_button()

    def _draw_self_healing_button(self):
        c = self._self_healing_canvas
        w = int(c["width"]) if int(c["width"]) > 1 else 350
        h = int(c["height"])
        c.delete("all")
        self._draw_smooth_rounded_rect(c, 2, 2, w - 2, h - 2, radius=8, fill="#021417", outline=C_PRI, width=1)
        c.create_text(w // 2, h // 2, text="🛠️ SİSTEMİ ONAR (SELF-HEALING · RAM & DNS)", fill=C_PRI, font=font_body_bold(8))

    def _build_ghost_typer_button(self, parent=None):
        parent = parent or self.root
        self._ghost_typer_canvas = tk.Canvas(parent, height=28, bg=parent.cget("bg"), highlightthickness=0, cursor="hand2")
        self._ghost_typer_canvas.bind("<Button-1>", lambda e: self._open_ghost_typer_popup())
        self._draw_ghost_typer_button()

    def _draw_ghost_typer_button(self):
        c = self._ghost_typer_canvas
        w = int(c["width"]) if int(c["width"]) > 1 else 350
        h = int(c["height"])
        c.delete("all")
        self._draw_smooth_rounded_rect(c, 2, 2, w - 2, h - 2, radius=8, fill="#04121a", outline=C_BLUE, width=1)
        c.create_text(w // 2, h // 2, text="⌨️ GHOST TYPER HUD (CTRL+SHIFT+G)", fill=C_BLUE, font=font_body_bold(8))

    def _build_terminate_button(self, parent=None):
        parent = parent or self.root
        self._terminate_canvas = tk.Canvas(parent, height=28, bg=parent.cget("bg"), highlightthickness=0, cursor="hand2")
        self._terminate_canvas.bind("<Button-1>", lambda e: self.terminate_app())
        self._draw_terminate_button()

    def _draw_terminate_button(self):
        c = self._terminate_canvas
        w = int(c["width"]) if int(c["width"]) > 1 else 350
        h = int(c["height"])
        c.delete("all")
        self._draw_smooth_rounded_rect(c, 2, 2, w - 2, h - 2, radius=8, fill="#1c0608", outline=C_RED, width=1)
        c.create_text(w // 2, h // 2, text="✕  JARVIS'İ TAMAMEN KAPAT (SİSTEMDEN ÇIK)", fill=C_RED, font=font_body_bold(8))

    def _open_paranoid_panel(self):
        try:
            from actions.paranoid_mode import get_paranoid_sentinel
            sentinel = get_paranoid_sentinel()
            st = sentinel.get_status()
            cfg = st.get("config", {})

            win = tk.Toplevel(self.root)
            win.title("🛡️ Paranoid Güvenlik Modu")
            win.geometry("460x440")
            win.configure(bg="#051010")
            win.resizable(False, False)

            tk.Label(win, text="🛡️ PARANOID GÜVENLİK MERKEZİ", fg=C_PRI, bg="#051010", font=font_display(12)).pack(pady=(14, 4))
            tk.Label(win, text="Kullanıcı bilgisayar başında yokken biyometrik oda/alan savunması", fg="#5ea7a0", bg="#051010", font=font_body(9)).pack(pady=(0, 10))

            status_var = tk.StringVar(value=f"DURUM: {'🟢 AKTİF' if st.get('is_active') else '⚪ KAPALI'}")
            status_lbl = tk.Label(win, textvariable=status_var, fg=C_GREEN if st.get('is_active') else C_MID, bg="#051010", font=font_body_bold(11))
            status_lbl.pack(pady=2)

            has_bio = bool(st.get("has_biometric_model", False))
            bio_lbl = tk.Label(win, text=f"BİYOMETRİK YÜZ TANIMA: {'✓ AKTİF (Patron Kayıtlı)' if has_bio else '⚠️ MODEL YOK (Tüm Yüzler Yabancı)'}",
                               fg=C_GREEN if has_bio else C_GOLD, bg="#051010", font=font_body(9))
            bio_lbl.pack(pady=2)

            def _start_face_enroll():
                self.write_log("SYS: Patron Yüz Kayıt Protokolü başlatılıyor... Canlı kamera açılıyor.")
                def _worker():
                    from utils.face_setup import setup_face
                    res = setup_face()
                    if res:
                        self.write_log("SYS: ✓ Patron biyometrik yüz modeli başarıyla kilitlendi!")
                        try:
                            bio_lbl.configure(text="BİYOMETRİK YÜZ TANIMA: ✓ AKTİF (Patron Kayıtlı)", fg=C_GREEN)
                        except Exception:
                            pass
                    else:
                        self.write_log("WARN: Yüz tarama işlemi tamamlanamadı.")
                threading.Thread(target=_worker, daemon=True).start()

            tk.Button(win, text="📸 Patron Yüzünü Kaydet / Güncelle", command=_start_face_enroll,
                      fg=C_BG, bg=C_CYAN, font=font_body_bold(9), padx=10, pady=4, relief="flat", cursor="hand2").pack(pady=4)

            dim_var = tk.BooleanVar(value=cfg.get("dim_screen", True))
            photo_var = tk.BooleanVar(value=cfg.get("take_photo", True))

            def _toggle_mode():
                if sentinel.is_active:
                    sentinel.stop()
                    status_var.set("DURUM: ⚪ KAPALI")
                    status_lbl.configure(fg=C_MID)
                    self.write_log("SYS: Paranoid Güvenlik Modu KAPATILDI.")
                else:
                    sentinel.configure(dim_screen=dim_var.get(), take_photo=photo_var.get())
                    res = sentinel.start()
                    status_var.set("DURUM: 🟢 AKTİF")
                    status_lbl.configure(fg=C_GREEN)
                    self.write_log(f"SYS: Paranoid Güvenlik Modu AKTİFLEŞTİRİLDİ. ({res})")
                self._draw_paranoid_button()

            def _update_cfg():
                sentinel.configure(dim_screen=dim_var.get(), take_photo=photo_var.get())

            btn_toggle = tk.Button(win, text="MODU AÇ / KAPAT", command=_toggle_mode, fg=C_BG, bg=C_PRI, font=font_body_bold(10), padx=14, pady=6, relief="flat", cursor="hand2")
            btn_toggle.pack(pady=10)

            chk_frame = tk.Frame(win, bg="#051010")
            chk_frame.pack(pady=6)
            tk.Checkbutton(chk_frame, text="İzinsiz girişte ekranı 0 parlaklığa karart", variable=dim_var, command=_update_cfg, fg=C_TEXT, bg="#051010", selectcolor="#020a0a", activebackground="#051010", activeforeground=C_TEXT, font=font_body(9)).pack(anchor="w", pady=2)
            tk.Checkbutton(chk_frame, text="Davetsiz misafir fotoğrafı çek (database/intruders)", variable=photo_var, command=_update_cfg, fg=C_TEXT, bg="#051010", selectcolor="#020a0a", activebackground="#051010", activeforeground=C_TEXT, font=font_body(9)).pack(anchor="w", pady=2)

            def _open_folder():
                from actions.paranoid_mode import INTRUDER_DIR
                INTRUDER_DIR.mkdir(parents=True, exist_ok=True)
                os.startfile(str(INTRUDER_DIR))

            tk.Button(win, text="📁 Fotoğraf Klasörünü Aç", command=_open_folder, fg=C_TEXT, bg="#031f1e", font=font_body(9), relief="flat", cursor="hand2").pack(pady=12)

        except Exception as exc:
            self.write_log(f"ERR: Paranoid paneli açılamadı: {exc}")

    def _toggle_air_gestures_ui(self):
        try:
            from actions.air_gestures import get_air_gesture_controller
            controller = get_air_gesture_controller()
            if controller.is_running():
                controller.stop()
                self.write_log("SYS: Air Gestures (Temassız El Hareketleri) durduruldu.")
            else:
                res = controller.start(preview=True)
                self.write_log(f"SYS: {res}")
            self._draw_air_gestures_button()
        except Exception as exc:
            self.write_log(f"ERR: Air Gestures başlatılamadı: {exc}")

    def _open_ghost_typer_popup(self):
        try:
            from actions.ghost_typer import GhostTyperPopup
            GhostTyperPopup(self.root)
            self.write_log("SYS: Ghost Typer (Hayalet Yazıcı) açıldı. (Global kısayol: Ctrl+Shift+G)")
        except Exception as exc:
            self.write_log(f"ERR: Ghost Typer açılamadı: {exc}")

    def _run_self_healing_ui(self):
        self.write_log("SYS: PC Kendi Kendini Onarma (Self-Healing) teşhisi başlatılıyor...")
        self.sound.play_startup()

        def _worker():
            try:
                from actions.self_healing import run_full_self_healing
                report = run_full_self_healing("full")
                for line in report.split("\n"):
                    if line.strip():
                        self.write_log(line)
                self.sound.play_success()
            except Exception as exc:
                self.write_log(f"ERR: Self-healing hatası: {exc}")
                self.sound.play_error()

        threading.Thread(target=_worker, daemon=True).start()

    def _capture_photo_ui(self):
        self.write_log("SYS: Kamera hazırlanıyor, fotoğraf çekiliyor...")
        def _worker():
            try:
                from actions.photo_capture import capture_user_photo
                res = capture_user_photo()
                self.write_log(f"SYS: {res}")
            except Exception as exc:
                self.write_log(f"ERR: Fotoğraf çekilemedi: {exc}")
        threading.Thread(target=_worker, daemon=True).start()

    def _shutdown(self, force: bool = False):
        self.terminate_app()

    def minimize_to_background(self):
        self._in_background_mode = True
        try:
            self.sound.stop_all()
        except Exception:
            pass
        if getattr(self, "_fullscreen", False):
            try:
                self.root.attributes("-fullscreen", False)
            except Exception:
                pass
        try:
            self.root.withdraw()
        except Exception:
            pass
        self.write_log("SYS: 💤 JARVIS arka plana alındı. [F8] veya 'Jarvis' seslenmesiyle dilediğiniz an açabilirsiniz.")
        print("[JARVIS] 💤 Arka plan moduna geçildi. 'Jarvis' veya [F8] bekleniyor...")
        try:
            if getattr(self, "_fullscreen", False):
                self.root.attributes("-fullscreen", False)
            try:
                self.root.iconify()
            except Exception:
                self.root.withdraw()
        except Exception:
            self.root.withdraw()
        self.write_log("SYS: JARVIS arka planda. Görev çubuğu simgesi aktif. [F8] ile Yüzen Ada açılır.")
        print("[JARVIS] 💤 Arka plan moduna geçildi. Görev çubuğunda simge aktif. 'Jarvis' veya [F8] bekleniyor...")

    def terminate_app(self):
        try:
            self.sound.stop_all()
        except Exception:
            pass
        try:
            import psutil
            for p in psutil.process_iter(['name', 'cmdline']):
                if p.info['name'] and 'powershell' in p.info['name'].lower():
                    cmd = " ".join(p.info['cmdline'] or [])
                    if 'MediaPlayer' in cmd:
                        p.kill()
        except Exception:
            pass
        self.write_log("SYS: JARVIS tamamen kapatılıyor...")
        self.root.after(200, os._exit, 0)

    # ── Input bar ────────────────────────────────────────────────────────────
    def _build_input_bar(self, lw: int):
        x0 = self.CHAT_X
        btn_w = 76
        gap = 8
        inp_w = lw - btn_w - gap

        self._input_var   = tk.StringVar()
        self._input_entry = tk.Entry(
            self.root, textvariable=self._input_var,
            fg=C_TEXT, bg="#041212", insertbackground=C_TEXT,
            borderwidth=0, font=font_body(11),
            highlightthickness=1, highlightbackground=C_DIM,
            highlightcolor=C_PRI)
        self._input_entry.place(
            x=x0, y=self.CHAT_INPUT_Y, width=inp_w, height=INPUT_H)
        self._input_entry.bind("<Return>",   self._on_input_submit)
        self._input_entry.bind("<KP_Enter>", self._on_input_submit)

        self._send_btn = tk.Button(
            self.root, text="SEND ▸",
            command=self._on_input_submit,
            fg=C_PRI, bg="#061a1a",
            activeforeground=C_BG, activebackground=C_ORG,
            font=font_body_bold(10),
            borderwidth=0, cursor="hand2",
            highlightthickness=1, highlightbackground=C_PRI)
        self._send_btn.place(
            x=x0+inp_w+gap, y=self.CHAT_INPUT_Y,
            width=btn_w, height=INPUT_H)

    def _place_layout_widgets(self):
        self.log_frame.place(x=self.CHAT_X, y=self.CHAT_Y, width=self.CHAT_W, height=self.CHAT_H)
        gap = 10
        mute_w = 126
        pause_w = 126
        cam_w  = 110
        shutdown_w = int(self._shutdown_canvas["width"])
        total = mute_w + pause_w + cam_w + shutdown_w + gap * 3
        start_x = self.FCX - total // 2
        start_x = max(8, min(start_x, self.W - total - 8))
        eff_f = 0 if getattr(self, "_fullscreen", False) else FOOTER_H; row1_y = self.H - eff_f - (50 if getattr(self, "_fullscreen", False) else 44)

        self._mute_canvas.place(x=start_x, y=row1_y)
        self._pause_canvas.place(x=start_x + mute_w + gap, y=row1_y)
        self._cam_canvas.place(x=start_x + mute_w + pause_w + gap * 2, y=row1_y)
        self._shutdown_canvas.place(x=start_x + mute_w + pause_w + cam_w + gap * 3, y=row1_y)

        geo = self._settings_geometry
        self._settings_btn_canvas.configure(width=geo["btn_w"], height=geo["btn_h"])
        self._settings_btn_canvas.place(x=geo["btn_x"], y=geo["btn_y"])
        self._draw_settings_button()
        panel_x = geo["panel_x"]
        panel_y = geo["panel_y"]
        panel_w = geo["panel_w"]
        panel_h = geo["panel_h"]
        if self._settings_open:
            self._settings_panel.place(x=panel_x, y=panel_y, width=panel_w, height=panel_h)
            self._settings_panel.lift()
            self._settings_title.place(x=14, y=10)
            tw = max(60, (panel_w - 28 - 18) // 4)
            self._settings_tab_settings.place(x=14, y=36, width=tw)
            self._settings_tab_apps.place(x=14 + tw + 6, y=36, width=tw)
            self._settings_tab_themes.place(x=14 + (tw + 6) * 2, y=36, width=tw)
            self._settings_tab_debug.place(x=14 + (tw + 6) * 3, y=36, width=tw)

            body_y = 70
            body_h = panel_h - 80
            body_w = panel_w - 24

            for b in (self._settings_body, self._apps_body, self._themes_body, self._debug_body):
                b.place_forget()

            if self._settings_tab == "debug":
                self._debug_body.place(x=12, y=body_y, width=body_w, height=body_h)
                self._debug_text.place(x=0, y=0, width=body_w, height=body_h)
                self._debug_body.lift()
            elif self._settings_tab == "apps":
                self._apps_body.place(x=12, y=body_y, width=body_w, height=body_h)
                self._apps_body.lift()
            elif self._settings_tab == "themes":
                self._themes_body.place(x=12, y=body_y, width=body_w, height=body_h)
                self._themes_body.lift()
            else:
                self._settings_body.place(x=12, y=body_y, width=body_w, height=body_h)
                self._settings_body.lift()
        else:
            self._settings_panel.place_forget()
            self._settings_title.place_forget()
            self._settings_tab_settings.place_forget()
            self._settings_tab_apps.place_forget()
            self._settings_tab_themes.place_forget()
            self._settings_tab_debug.place_forget()
            self._settings_body.place_forget()
            self._apps_body.place_forget()
            self._themes_body.place_forget()
            self._debug_body.place_forget()

        if hasattr(self, "_social_bar"):
            self._social_bar.place(x=14, y=max(HDR_H + 4, self.H - FOOTER_H - 52))

        inp_w = max(80, self.CHAT_W - 84)
        self._input_entry.place(x=self.CHAT_X, y=self.CHAT_INPUT_Y, width=inp_w, height=INPUT_H)
        self._send_btn.place(x=self.CHAT_X + inp_w + 8, y=self.CHAT_INPUT_Y, width=76, height=INPUT_H)

    def _on_input_submit(self, event=None):
        text = self._input_var.get().strip()
        if not text:
            return
        if self.paused:
            self.write_log("SYS: JARVIS duraklatılmış durumda. Devam etmek için pause'u kapat.")
            return
        self._input_var.set("")
        if text.lower() in ("sus", "dur", "stop", "sessiz", "kes"):
            self.write_log("SYS: ⏹ Ses kesildi.")
            if self.on_stop_command:
                threading.Thread(target=self.on_stop_command, daemon=True).start()
            return
        if self.on_text_command:
            threading.Thread(target=self.on_text_command, args=(text,), daemon=True).start()

    # ── State & callbacks ────────────────────────────────────────────────────
    def set_state(self, state: str):
        if threading.get_ident() != self._tk_thread_id:
            self._dispatch_ui(self.set_state, state)
            return
        previous = getattr(self, "_jarvis_state", "")
        self._jarvis_state = state
        self.speaking = (state == "SPEAKING")
        if state == "THINKING":
            self.sound.start_thinking()
        elif previous == "THINKING":
            self.sound.stop_thinking()
        if state == "ERROR" and previous != "ERROR":
            self.sound.play_error()

    def set_user_speaking(self, value: bool):
        self.mark_user_activity(value)

    def mark_user_activity(self, active: bool = True):
        if threading.get_ident() != self._tk_thread_id:
            self._dispatch_ui(self.mark_user_activity, active)
            return
        self.user_speaking = active
        self._user_speaking_until = time.time() + (0.9 if active else 0.0)

    def get_effects_volume(self) -> float:
        return self.sound.get_volume()

    def effects_enabled(self) -> bool:
        return bool(self._effects_active)

    def play_success_sfx(self):
        self._dispatch_ui(self.sound.play_success)

    def play_error_sfx(self):
        self._dispatch_ui(self.sound.play_error)

    def wake_up(self):
        """'Jarvis' seslenmesiyle tetiklenir — arka plandaysa Floating Island'ı sinematik animasyonla açar."""
        def _do():
            if getattr(self, "_in_background_mode", False) or not self.root.winfo_viewable():
                self._enter_floating_island()
            else:
                try:
                    self.root.deiconify(); (self._enter_fullscreen() if getattr(self, "_fullscreen", False) else None)
                    self.root.attributes("-topmost", True)
                    self.root.lift()
                    self.root.focus_force()
                    self.root.after(3000, lambda: self.root.attributes("-topmost", False))
                except Exception:
                    pass
        self._dispatch_ui(_do)

    # ── Webcam layout hesabı ─────────────────────────────────────────────────
    def _calc_cam_layout(self):
        """Kamera paneli boyutları + orb kayma değerlerini döndürür.

        Dönen değerler: (cam_w, cam_h, cam_x, cam_y, orb_shift, orb_face)
        """
        center_w  = self.CENTER_X1 - self.CENTER_X0
        cam_w     = max(220, min(center_w - 40, 580))
        cam_h     = max(124, int(cam_w * 9 / 16))
        total_h   = self.CTRL_Y - HDR_H          # merkez alanın toplam yüksekliği
        remaining = total_h - cam_h - 24         # kamera altında orb için kalan alan
        new_face  = max(120, min(int(remaining * 0.82),
                                 int(center_w  * 0.70), 520))
        new_cy    = HDR_H + cam_h + 16 + remaining // 2   # orb'un yeni merkezi
        shift     = new_cy - self.FCY
        cam_x     = self.FCX - cam_w // 2
        cam_y     = HDR_H + 8
        return cam_w, cam_h, cam_x, cam_y, shift, new_face

    def set_webcam_active(self, active: bool):
        if threading.get_ident() != self._tk_thread_id:
            self._dispatch_ui(self.set_webcam_active, active)
            return
        self._webcam_active = bool(active)
        self.root.after(0, self._draw_webcam_button)
        if active:
            cam_w, cam_h, cam_x, cam_y, shift, face = self._calc_cam_layout()
            self._cam_orb_shift_target = float(shift)
            self._cam_orb_face_target  = float(face)
            # İlk açılışta face'i FACE'den başlat ki animasyon doğal görünsün
            if self._cam_orb_face < 1.0:
                self._cam_orb_face = float(self.FACE)
            if self._cam_label is None:
                self._cam_label = tk.Label(
                    self.root,
                    bg="#020808",
                    fg=C_PRI,
                    text="KAMERA BASLATILIYOR...",
                    font=font_body_bold(11),
                    highlightthickness=1,
                    highlightbackground=C_MID,
                )
            self._cam_label.configure(image="", text="KAMERA BASLATILIYOR...")
            self._cam_label.place(x=cam_x, y=cam_y, width=cam_w, height=cam_h)
            self._cam_label.lift(self.bg)
        else:
            self._cam_orb_shift_target = 0.0
            # Hedef: normal FACE boyutuna geri dön. Animasyon bitince 0'a sıfırlanır
            # (_animate içinde), böylece FACE→0 geçişi görünmez.
            self._cam_orb_face_target  = float(self.FACE)
            self._webcam_photo  = None
            if self._cam_label is not None:
                self._cam_label.place_forget()
        self.write_log(f"SYS: Webcam {'CANLI' if active else 'KAPALI'}")

    def update_webcam_preview(self, jpeg_bytes: bytes) -> None:
        """Live webcam karesini dikdörtgen panel'de gösterir. Thread-safe."""
        with self._webcam_queue_lock:
            self._pending_webcam_frame = jpeg_bytes
            if self._webcam_frame_queued:
                return
            self._webcam_frame_queued = True
        self._ui_request_queue.put(("webcam_frame", None))

    def _show_webcam_preview(self, jpeg_bytes: bytes) -> None:
        """JPEG'i üst-orta alana dikdörtgen Label olarak basar."""
        if not self._webcam_active:
            return
        try:
            import io
            cam_w, cam_h, cam_x, cam_y, _, _ = self._calc_cam_layout()

            img   = Image.open(io.BytesIO(jpeg_bytes))
            # Oranı koru, merkez crop ile 16:9'a getir
            iw, ih  = img.size
            target_ratio = cam_w / cam_h
            src_ratio    = iw / ih
            if src_ratio > target_ratio:            # daha geniş → sol/sağ kırp
                new_w = int(ih * target_ratio)
                img   = img.crop(((iw - new_w) // 2, 0,
                                  (iw + new_w) // 2, ih))
            else:                                   # daha uzun → üst/alt kırp
                new_h = int(iw / target_ratio)
                img   = img.crop((0, (ih - new_h) // 2,
                                  iw, (ih + new_h) // 2))
            img   = img.resize((cam_w, cam_h), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            if self._cam_label is None:
                self._cam_label = tk.Label(
                    self.root, bg=C_BG,
                    highlightthickness=1,
                    highlightbackground=C_MID,
                )
            self._cam_label.configure(image=photo, text="")
            self._webcam_photo = photo          # referans tut — GC koruması
            self._cam_label.place(x=cam_x, y=cam_y,
                                  width=cam_w, height=cam_h)
            # bg canvas'ın hemen üstüne taşı — settings paneli vs. üstte kalır
            self._cam_label.lift(self.bg)
        except Exception as exc:
            print(f"[UI] Webcam preview güncellenemedi: {exc}")

    def focus_panel(self, section: str, duration_ms: int = 4200):
        section = (section or "").strip().lower()
        if not section:
            return

        def _apply():
            self._panel_focus = section
            self._panel_focus_until = time.time() + max(0.8, duration_ms / 1000.0)

        self._dispatch_ui(_apply)

    def _state_color(self, state: str | None = None) -> str:
        effective = state or self._jarvis_state
        if effective == "PAUSED":
            return C_MID
        return STATE_HEX_COLORS.get(effective, C_PRI)

    @staticmethod
    def _state_badge_text(state: str) -> str:
        if state == "INITIALISING":
            return "CONNECTING"
        if state == "ERROR":
            return "ERROR"
        return "ONLINE"

    # ── Log ──────────────────────────────────────────────────────────────────
    def write_log(self, text: str):
        if threading.get_ident() != self._tk_thread_id:
            self._dispatch_ui(self.write_log, text)
            return
        self.typing_queue.append(text)
        tl = text.lower()
        if tl.startswith("siz:") or tl.startswith("you:"):
            self.mark_user_activity(True)
            self.set_state("THINKING")
        elif tl.startswith("err:") or "error" in tl:
            self._error_hold_until = time.time() + 8.0
            self.set_state("ERROR")
            self.write_debug(text, level="ERROR")
        if not self.is_typing:
            self._start_typing()

    def _start_typing(self):
        if not self.typing_queue:
            self.is_typing = False
            if self._jarvis_state == "ERROR" and time.time() < self._error_hold_until:
                return
            if not self.speaking:
                self.set_state("LISTENING")
            return
        self.is_typing = True
        text = self.typing_queue.popleft()
        tl   = text.lower()
        if   tl.startswith("siz:") or tl.startswith("you:"):   tag = "you"
        elif tl.startswith("jarvis:") or tl.startswith("ai:"): tag = "ai"
        elif tl.startswith("err:") or "error" in tl:           tag = "err"
        else:                                                  tag = "sys"
        self.log_text.configure(state="normal")

        # Kullanıcı ve sistem mesajları anında yazılsın, bekletmesin
        if tag in ("you", "sys", "err") or len(self.typing_queue) > 0:
            self.log_text.insert(tk.END, text + "\n", tag)
            self.log_text.see(tk.END)
            self.log_text.configure(state="disabled")
            self.root.after(5, self._start_typing)
        else:
            # Sadece Jarvis konuşması akıcı ve ultra hızlı (3 karakter blok) aksın
            self._type_char(text, 0, tag)

    def _type_char(self, text, i, tag):
        if i < len(text):
            # 3-4 karakterlik mikro bloklar halinde yaz → hem siber daktilo hissi korunur hem de anında akar
            step = 3 if len(text) < 180 else 6
            chunk = text[i:i+step]
            self.log_text.insert(tk.END, chunk, tag)
            self.log_text.see(tk.END)
            self.root.after(4, self._type_char, text, i+len(chunk), tag)
        else:
            self.log_text.insert(tk.END, "\n")
            self.log_text.see(tk.END)
            self.log_text.configure(state="disabled")
            self.root.after(10, self._start_typing)

    # ── Stats ────────────────────────────────────────────────────────────────
    def _update_stats(self):
        try:
            self._stats['cpu']  = psutil.cpu_percent()
            self._stats['ram']  = psutil.virtual_memory().percent
            self._stats['disk'] = psutil.disk_usage('/').percent
            batt = psutil.sensors_battery()
            self._stats['battery'] = batt.percent if batt else 100.0
            now = time.time()
            net = psutil.net_io_counters()
            dt  = now - self._last_net_t
            if dt > 0:
                self._stats['net_up']   = max(0, (net.bytes_sent - self._last_net.bytes_sent) / dt / 1024)
                self._stats['net_down'] = max(0, (net.bytes_recv - self._last_net.bytes_recv) / dt / 1024)
            self._last_net   = net
            self._last_net_t = now
            self._cpu_hist.pop(0)
            self._cpu_hist.append(self._stats['cpu'])
        except Exception:
            pass

    # ── Animation loop ───────────────────────────────────────────────────────
    def _animate(self):
        if getattr(self, "_in_background_mode", False) or not self.root.winfo_viewable():
            self.root.after(200, self._animate)
            return
        self.tick += 1
        self._visual_tick = 0 if self._reduce_motion else self.tick
        t   = self.tick
        now = time.time()

        if self.user_speaking and now > self._user_speaking_until:
            self.user_speaking = False

        if t % 90 == 0:
            threading.Thread(target=self._update_stats, daemon=True).start()
        if t % 1800 == 1:
            self._kick_brief_refresh()

        if self.speaking and t % 3 == 0:
            self._wave_jarvis = [random.randint(6, 30) for _ in range(18)]
        if self.user_speaking and t % 3 == 0:
            self._wave_user = [random.randint(5, 24) for _ in range(18)]

        if now - self.last_t > (0.12 if self.speaking else 0.50):
            if self.paused:
                self.target_scale = random.uniform(0.58, 0.64)
                self.target_halo  = random.uniform(5, 10)
            elif self.speaking:
                self.target_scale = random.uniform(0.98, 1.10)
                self.target_halo  = random.uniform(180, 250)
            elif self.user_speaking:
                self.target_scale = random.uniform(0.88, 0.98)
                self.target_halo  = random.uniform(120, 175)
            elif self._jarvis_state in ("THINKING", "INITIALISING"):
                self.target_scale = random.uniform(0.80, 0.88)
                self.target_halo  = random.uniform(95, 145)
            else:
                self.target_scale = random.uniform(0.72, 0.80)
                self.target_halo  = random.uniform(34, 58)
            self.last_t = now

        sp          = 0.34 if self.speaking else 0.18
        self.scale  += (self.target_scale - self.scale) * sp
        self.halo_a += (self.target_halo   - self.halo_a) * sp

        # Kamera orb animasyonu — ~0.07 ease ≈ 400 ms settle @40ms frame
        _CE = 0.07
        self._cam_orb_shift += (self._cam_orb_shift_target - self._cam_orb_shift) * _CE
        self._cam_orb_face  += (self._cam_orb_face_target  - self._cam_orb_face)  * _CE
        if abs(self._cam_orb_shift_target - self._cam_orb_shift) < 0.5:
            self._cam_orb_shift = self._cam_orb_shift_target
        if abs(self._cam_orb_face_target - self._cam_orb_face) < 0.5:
            self._cam_orb_face = self._cam_orb_face_target
            # Kamera kapandıktan sonra animasyon bitince face'i temizle
            if not self._webcam_active:
                self._cam_orb_face        = 0.0
                self._cam_orb_face_target = 0.0

        if self.paused:
            spds = [0.0, 0.0, 0.0, 0.0]
        elif self.speaking:
            spds = [1.6, -1.1, 2.4, -0.7]
        else:
            spds = [0.55, -0.35, 0.90, -0.28]
        if not self._reduce_motion:
            effect_speed = {"calm": 0.62, "standard": 1.0, "cinematic": 1.45}.get(self._visual_effect_mode, 1.0)
            for i, spd in enumerate(spds):
                self.rings_spin[i] = (self.rings_spin[i] + spd * effect_speed) % 360

        # Pulse rings
        pspd  = 4.2 if self.speaking else 1.8
        limit = self.FACE * 0.68
        if not self._reduce_motion:
            self.pulse_r = [r + pspd for r in self.pulse_r if r + pspd < limit]
            if len(self.pulse_r) < 3 and random.random() < (0.07 if self.speaking else 0.02):
                self.pulse_r.append(0.0)

        if not self._reduce_motion:
            particle_speed = {"calm": 0.55, "standard": 1.0, "cinematic": 1.7}.get(self._visual_effect_mode, 1.0)
            for p in self.particles:
                p['x'] = (p['x'] + p['vx'] * particle_speed) % self.W
                p['y'] = (p['y'] + p['vy'] * particle_speed) % self.H

        if not self._reduce_motion and t % 38 == 0:
            self.status_blink = not self.status_blink

        self._draw()
        interval = 180 if self._reduce_motion else (32 if self._visual_effect_mode == "cinematic" else 50 if self._visual_effect_mode == "calm" else 40)
        self.root.after(interval, self._animate)

    # ── Yardımcı ─────────────────────────────────────────────────────────────
    @staticmethod
    def _ac(r, g, b, a):
        f = max(0, min(255, int(a))) / 255.0
        return f"#{int(r*f):02x}{int(g*f):02x}{int(b*f):02x}"

    def _orb_rgb(self):
        state = "PAUSED" if self.paused else self._jarvis_state
        return ORB_COLORS.get(state, ORB_COLORS["LISTENING"])

    @staticmethod
    def _split_summary_lines(text: str, limit: int = 4) -> list[str]:
        raw = (text or "").strip()
        if not raw:
            return []
        raw = raw.replace(" ve ", ", ")
        parts = [part.strip(" .") for part in raw.split(",") if part.strip()]
        return parts[:limit]

    def _parse_weather_card(self, text: str) -> dict:
        if not text or "alınamadı" in text.lower() or "alınamadi" in text.lower():
            return {
                "city": "Adana",
                "primary": "--",
                "details": ["Hava durumu alınamadı."],
            }

        prefix, _, body = text.partition(":")
        city = "Adana"
        if " için" in prefix:
            city = prefix.split(" için", 1)[0].strip().title()

        details = [part.strip(" .") for part in body.split(",") if part.strip()]
        primary = "--"
        if details:
            primary = details[0].replace(" derece", "°C")
        return {
            "city": city,
            "primary": primary,
            "details": details[1:4] or ["Anlık veri hazır."],
        }

    def _kick_brief_refresh(self):
        if self._brief_refresh_busy:
            return
        self._brief_refresh_busy = True
        threading.Thread(target=self._refresh_brief_cards, daemon=True).start()

    def _refresh_brief_cards(self):
        try:
            weather = get_weather_summary("Istanbul")
            self._weather_card = self._parse_weather_card(weather)
        except Exception:
            self._weather_card = {
                "city": "Istanbul",
                "primary": "--",
                "details": ["Hava durumu alınamadı."],
            }
        finally:
            self._brief_refresh_busy = False

    def _bar(self, c, x, y, w, h, pct, color):
        c.create_rectangle(x, y, x+w, y+h, fill="#061212", outline=C_DIM, width=1)
        fw = max(1, int(w * pct / 100))
        c.create_rectangle(x+1, y+1, x+fw, y+h-1, fill=color, outline="")

    def _sparkline(self, c, x, y, w, h, data):
        c.create_rectangle(x, y, x+w, y+h, fill="#050e0e", outline=C_DIM, width=1)
        n = len(data)
        if n < 2:
            return
        step = (w - 2) / (n - 1)
        h2   = h - 2
        coords = []
        for i, v in enumerate(data):
            coords.append(x + 1 + i * step)
            coords.append(y + h - 1 - int(h2 * v / 100))
        c.create_line(*coords, fill=C_PRI, width=1, smooth=True)

    def _bracket(self, c, x0, y0, pw, ph, col=None, bl=12):
        col = col or C_PRI
        for bx, by, sx, sy in [(x0, y0, 1, 1), (x0+pw, y0, -1, 1),
                                (x0, y0+ph, 1, -1), (x0+pw, y0+ph, -1, -1)]:
            c.create_line(bx, by, bx+sx*bl, by, fill=col, width=2)
            c.create_line(bx, by, bx, by+sy*bl, fill=col, width=2)

    def _draw_info_card(self, c, x0, y0, pw, ph, title, accent=C_PRI):
        focus = max(0.0, min(1.0, getattr(self, "_card_focus_boost", 0.0)))
        dimmed = bool(getattr(self, "_card_dimmed", False))
        glow = int(55 + 120 * focus)
        border = accent if focus > 0.08 else ("#35504d" if dimmed else self._ac(0, 120, 112, 190))
        fill = "#071111" if dimmed else "#030d0d"
        c.create_rectangle(x0, y0, x0+pw, y0+ph, fill=fill, outline="")
        if focus > 0.08:
            for inset in range(3):
                c.create_rectangle(
                    x0-inset, y0-inset, x0+pw+inset, y0+ph+inset,
                    outline=self._ac(*ORB_COLORS["LISTENING"], max(12, glow - inset * 28)),
                    width=1,
                )
        self._bracket(c, x0, y0, pw, ph, col=border, bl=10)
        title_fill = "#6f7d7b" if dimmed else accent
        line_fill = "#173130" if dimmed else C_DIM
        c.create_text(x0+14, y0+14, text=title, fill=title_fill,
                      font=font_display(10), anchor="w")
        c.create_line(x0+12, y0+28, x0+pw-12, y0+28, fill=line_fill)

    def _focus_boost_for(self, section: str) -> float:
        if self._panel_focus != section:
            return 0.0
        remaining = self._panel_focus_until - time.time()
        if remaining <= 0:
            return 0.0
        pulse = 0.65 + 0.35 * math.sin(self.tick * 0.12)
        return min(1.0, remaining / 4.0) * pulse

    # ── Sol panel ─────────────────────────────────────────────────────────────
    def _draw_left_panel(self, c):
        x0 = 10
        y0 = HDR_H + 10
        pw = self.LEFT_W - 18
        gap = 14
        eff_footer = 0 if getattr(self, "_fullscreen", False) else FOOTER_H
        total_h = self.H - HDR_H - eff_footer - (12 if getattr(self, "_fullscreen", False) else 20)
        card_area_h = total_h - gap * 3
        pad = 14
        bw = pw - 2 * pad

        cards = [
            ("time", 0.28, "TIME", C_GOLD),
            ("weather", 0.26, "WEATHER · ISTANBUL", C_BLUE),
            ("system", 0.46, "SYSTEM STATUS", C_PRI),
        ]
        any_focus_active = bool(self._panel_focus) and (self._panel_focus_until > time.time())
        weights = []
        for section, weight, _, _ in cards:
            weights.append(weight + (0.12 if self._focus_boost_for(section) > 0.08 else 0.0))
        total_weight = sum(weights)
        heights = [int(card_area_h * (weight / total_weight)) for weight in weights]
        heights[-1] += card_area_h - sum(heights)

        current_y = y0
        for (section, _, title, accent), ph in zip(cards, heights):
            focus_boost = self._focus_boost_for(section)
            dimmed = any_focus_active and focus_boost <= 0.08
            shift_x = int(14 * focus_boost)
            extra_w = int(22 * focus_boost)
            section_x = x0 + shift_x
            section_pw = pw + extra_w
            section_pad = pad + int(2 * focus_boost)
            section_bw = section_pw - 2 * section_pad
            muted_label = "#647270" if dimmed else C_MID
            muted_text = "#7e8a88" if dimmed else C_TEXT
            muted_primary = "#8ea19d" if dimmed else C_PRI
            muted_blue = "#829594" if dimmed else C_BLUE
            muted_green = "#85a393" if dimmed else C_GREEN
            muted_gold = "#a1997e" if dimmed else C_GOLD
            muted_warn = "#8d7f77" if dimmed else C_ORG2
            muted_red = "#8a7779" if dimmed else C_RED
            self._card_focus_boost = focus_boost
            self._card_dimmed = dimmed
            self._draw_info_card(c, section_x, current_y, section_pw, ph, title, accent=accent if not dimmed else "#72807f")

            if section == "time":
                c.create_text(section_x+section_pad, current_y+64, text=time.strftime("%H:%M"),
                              fill=muted_primary, font=font_display(36 if focus_boost > 0.08 else 34), anchor="w")
                c.create_text(section_x+section_pad, current_y+92, text=time.strftime(":%S"),
                              fill=muted_label, font=font_body_bold(13), anchor="w")
                c.create_text(section_x+section_pad, current_y+118, text=time.strftime("%d %B %Y").upper(),
                              fill=muted_gold, font=font_body_bold(11), anchor="w")
                c.create_text(section_x+section_pad, current_y+138, text=time.strftime("%A").upper(),
                              fill=muted_text, font=font_body(10), anchor="w")

            elif section == "weather":
                c.create_text(section_x+section_pad, current_y+58, text=self._weather_card["primary"],
                              fill=muted_primary, font=font_display(30 if focus_boost > 0.08 else 28), anchor="w")
                c.create_text(section_x+section_pad, current_y+84, text=self._weather_card["city"].upper(),
                              fill=muted_label, font=font_body_bold(10), anchor="w")
                wy = current_y + 108
                for line in self._weather_card["details"][:3]:
                    c.create_text(section_x+section_pad, wy, text=f"• {line}", fill=muted_text,
                                  font=font_body(10), anchor="w")
                    wy += 17

            elif section == "system":
                cy = current_y + 44
                uptime = int(time.time() - self._started_at)
                up_min, up_sec = divmod(uptime, 60)
                up_hr, up_min = divmod(up_min, 60)
                c.create_text(section_x+section_pad, cy, text=f"UPTIME  {up_hr:02d}:{up_min:02d}:{up_sec:02d}",
                              fill=muted_label, font=font_body_bold(9), anchor="w")
                cy += 22
                for label, key, unit in [("CPU", "cpu", "%"), ("RAM", "ram", "%"), ("DISK", "disk", "%"), ("BATTERY", "battery", "%")]:
                    val = self._stats[key]
                    col = C_RED if val > 80 and key != "battery" else C_ORG if val > 55 and key != "battery" else (C_RED if key == "battery" and val < 20 else C_GREEN if key == "battery" else C_PRI)
                    if dimmed:
                        col = muted_red if col == C_RED else muted_warn if col == C_ORG else muted_green if col == C_GREEN else muted_primary
                    c.create_text(section_x+section_pad, cy, text=label, fill=muted_label, font=font_body(10), anchor="w")
                    c.create_text(section_x+section_pw-section_pad, cy, text=f"{val:.0f}{unit}", fill=col, font=font_body_bold(10), anchor="e")
                    cy += 14
                    self._bar(c, section_x+section_pad, cy, section_bw, 7, val, col)
                    cy += 16
                up = self._stats["net_up"]
                down = self._stats["net_down"]
                up_s = f"{up:.1f} KB/s" if up < 1000 else f"{up/1024:.1f} MB/s"
                down_s = f"{down:.1f} KB/s" if down < 1000 else f"{down/1024:.1f} MB/s"
                c.create_line(section_x+section_pad, cy-4, section_x+section_pw-section_pad, cy-4, fill="#173130" if dimmed else C_DIM)
                c.create_text(section_x+section_pad, cy+10, text=f"▲ {up_s}", fill=muted_warn, font=font_body(10), anchor="w")
                c.create_text(section_x+section_pw-section_pad, cy+10, text=f"▼ {down_s}", fill=muted_green, font=font_body(10), anchor="e")

            current_y += ph + gap

        self._card_focus_boost = 0.0
        self._card_dimmed = False

    # ── Sağ panel ─────────────────────────────────────────────────────────────
    def _draw_right_panel(self, c):
        x0  = self.CHAT_PANEL_X
        y0  = self.CHAT_PANEL_Y
        pw  = self.CHAT_PANEL_W
        ph  = self.CHAT_PANEL_H
        pad = 10

        c.create_rectangle(x0, y0, x0+pw, y0+ph, fill="#030d0d", outline="")
        self._bracket(c, x0, y0, pw, ph, col=C_MID)

        if self.paused:
            sc, st = C_MID, "PAUSED"
        else:
            sc, st = self._state_color(self._jarvis_state), self._jarvis_state

        c.create_text(x0+14, y0+16, text="CONVERSATION", fill=C_PRI,
                      font=font_display(11), anchor="w")
        c.create_text(x0+pw-pad, y0+16, text=st, fill=sc,
                      font=font_body_bold(10), anchor="e")
        c.create_line(x0+pad, y0+28, x0+pw-pad, y0+28, fill=C_DIM)

    # ── ORB (ana çizim) ───────────────────────────────────────────────────────
    def _draw_orb(self, c, cam: bool = False):
        state = "PAUSED" if self.paused else self._jarvis_state
        t    = self.tick
        speak_pulse = 1.0
        if self.speaking:
            speak_pulse = 1.0 + 0.12 * math.sin(t * 0.23) + 0.05 * math.sin(t * 0.11 + 1.2)
        elif self.user_speaking:
            speak_pulse = 1.0 + 0.06 * math.sin(t * 0.18 + 0.7)
        elif state in ("THINKING", "INITIALISING"):
            speak_pulse = 1.0 + 0.03 * math.sin(t * 0.10)
        else:
            speak_pulse = 1.0 + 0.01 * math.sin(t * 0.07)

        move_x = 0
        move_y = 0
        if self.user_speaking:
            move_x = int(6 * math.sin(t * 0.06))
            move_y = int(4 * math.cos(t * 0.09 + 0.5))
        elif state in ("THINKING", "INITIALISING"):
            move_x = int(3 * math.sin(t * 0.045))
            move_y = int(2 * math.cos(t * 0.05 + 0.4))

        FCX  = self.FCX + move_x
        # _cam_orb_shift her zaman uygulanır — animasyon hem açılışta hem
        # kapanışta çalışır; kamera kapalıysa target=0 olduğundan doğal döner.
        FCY  = self.FCY + move_y + int(self._cam_orb_shift)
        base_face = (int(self._cam_orb_face) if self._cam_orb_face > 1.0 else self.FACE)
        FW   = int(base_face * self.scale * speak_pulse)
        R, G, B = self._orb_rgb()
        ha   = self.halo_a
        field_r = int(FW * 0.49)
        inner_r = int(FW * 0.34)
        activity = (
            0.10 if self.paused else
            1.00 if self.speaking else
            0.78 if self.user_speaking else
            0.62 if state in ("THINKING", "INITIALISING") else
            0.26
        )
        if state in ("THINKING", "INITIALISING"):
            accent_rgb = (255, 210, 72)
        elif self.speaking:
            accent_rgb = (170, 220, 255)
        elif self.user_speaking:
            accent_rgb = (118, 200, 255)
        else:
            accent_rgb = (120, 255, 185)

        # Pulse rings
        for pr in self.pulse_r:
            alpha = max(0, int(160 * (1.0 - pr / (FW * 0.70))))
            rr = int(pr + field_r * 0.96)
            c.create_oval(
                FCX-rr, FCY-rr, FCX+rr, FCY+rr,
                outline=self._ac(R, G, B, alpha),
                width=1,
            )

        # Large outer glow
        if not self.paused:
            for i in range(10, 0, -1):
                frac = i / 10
                rr = int(field_r * (1.02 + 0.045 * frac))
                alpha = int(ha * 0.10 * frac)
                if self.speaking:
                    ox = 0
                    oy = 0
                else:
                    ox = int(3 * math.sin(t * 0.010 + i))
                    oy = int(3 * math.cos(t * 0.009 + i * 1.3))
                c.create_oval(
                    FCX-rr+ox, FCY-rr+oy, FCX+rr+ox, FCY+rr+oy,
                    outline=self._ac(R, G, B, alpha),
                    width=3,
                )

        # Structural circles — kamera açıkken gizle (webcam zaten üstünü kapatır)
        if not cam:
            for frac, width, alpha_mult in (
                (1.00, 2, 0.34),
                (0.90, 2, 0.24),
                (0.76, 1, 0.18),
                (0.62, 1, 0.12),
            ):
                rr = int(field_r * frac)
                c.create_oval(
                    FCX-rr, FCY-rr, FCX+rr, FCY+rr,
                    outline=self._ac(R, G, B, int(ha * alpha_mult * (0.4 if self.paused else 1.0))),
                    width=width,
                )

        speak_shell_push = 1.16 if self.speaking else 1.07 if self.user_speaking else 1.0
        # Orb shell particles
        shell_r = field_r * 0.93 * speak_shell_push
        shell_count = {"calm": 42, "standard": 84, "cinematic": 112}.get(self._visual_effect_mode, 84)
        for idx, sp in enumerate(self.orb_shell_particles):
            if idx >= shell_count:
                break
            angle = sp['angle'] + t * sp['speed'] * (2.8 if self.speaking else 1.6 if self.user_speaking else 1.1)
            wobble = 1.0 + (0.07 if self.speaking else 0.035) * math.sin(t * 0.08 + sp['phase'])
            x = FCX + math.cos(angle) * shell_r * wobble
            y = FCY + math.sin(angle) * shell_r * wobble
            alpha = int((70 + 120 * sp['glow']) * (0.26 if self.paused else 0.52 + activity * 0.45))
            if idx % 9 == 0 and not self.paused:
                col = self._ac(accent_rgb[0], accent_rgb[1], accent_rgb[2], min(255, alpha + 30))
            else:
                col = self._ac(R, G, B, alpha)
            pr = sp['size'] * (1.0 + 0.24 * math.sin(t * 0.05 + sp['phase']))
            c.create_oval(x-pr, y-pr, x+pr, y+pr, fill=col, outline="")

        # Rotating segmented arcs — kamera açıkken gizle
        if not cam:
            arc_r1 = int(field_r * 0.96)
            arc_r2 = int(field_r * 0.78)
            for start, extent, width, accent in (
                (self.rings_spin[0], 52 if self.speaking else 34, 3, False),
                ((self.rings_spin[0] + 148) % 360, 26, 2, True),
                ((self.rings_spin[2] + 28) % 360, 64 if self.user_speaking else 40, 3, False),
                ((self.rings_spin[2] + 212) % 360, 18, 2, True),
            ):
                rr = arc_r1 if width == 3 else arc_r2
                if accent and not self.paused:
                    col = self._ac(accent_rgb[0], accent_rgb[1], accent_rgb[2], int(120 + 80 * activity))
                else:
                    col = self._ac(R, G, B, int(ha * (1.2 if width == 3 else 0.7)))
                c.create_arc(
                    FCX-rr, FCY-rr, FCX+rr, FCY+rr,
                    start=start, extent=extent,
                    outline=col, width=width, style="arc",
                )

        # Particle orb field
        field_limit = inner_r * (
            0.82 if self.paused else
            1.36 if self.speaking else
            1.16 if self.user_speaking else
            1.0
        )
        orb_count = {"calm": 64, "standard": 160, "cinematic": 260}.get(self._visual_effect_mode, 160)
        for idx, p in enumerate(self.orb_particles):
            if idx >= orb_count:
                break
            speed_mult = (
                0.10 if self.paused else
                3.10 if self.speaking else
                2.00 if self.user_speaking else
                1.10
            )
            angle = p['angle'] + t * p['speed'] * speed_mult
            wobble = 1.0 + (0.30 if self.speaking else 0.18) * math.sin(t * p['wobble'] + p['phase'])
            orbit = field_limit * p['orbit'] * wobble
            depth = 0.5 + 0.5 * math.sin(angle * 2.0 + t * 0.013 + p['phase'])
            y_squash = 0.62 + depth * 0.38
            drift = (8.0 if self.speaking else 5.0 if self.user_speaking else 4.0) * p['depth']
            x = FCX + math.cos(angle) * orbit + math.sin(t * 0.011 + p['phase']) * drift
            y = FCY + math.sin(angle) * orbit * y_squash + math.cos(t * 0.010 + p['phase']) * drift
            base_alpha = int((18 + 155 * p['depth']) * (0.24 + activity * 0.86) * (0.45 + depth * 0.75))
            if self.paused:
                base_alpha = int(base_alpha * 0.40)
            if idx % 11 == 0 and not self.paused:
                col = self._ac(accent_rgb[0], accent_rgb[1], accent_rgb[2], min(255, base_alpha + 25))
            elif self.user_speaking and idx % 7 == 0:
                col = self._ac(120, 205, 255, min(255, base_alpha + 20))
            else:
                col = self._ac(R, G, B, base_alpha)
            pr = p['size'] * (0.70 if self.paused else 0.90 + depth * 0.65 + 0.30 * activity * p['depth'])
            c.create_oval(x-pr, y-pr, x+pr, y+pr, fill=col, outline="")
            if idx % 18 == 0 and not self.paused:
                c.create_line(
                    FCX + (x-FCX) * 0.18,
                    FCY + (y-FCY) * 0.18,
                    x, y,
                    fill=self._ac(R, G, B, int(18 + 35 * p['depth'] * activity)),
                    width=1,
                )

        # Center void keeps the orb airy instead of lens-like.
        void_r = int(inner_r * (0.18 if self.paused else 0.12))
        if void_r > 0:
            c.create_oval(
                FCX-void_r, FCY-void_r, FCX+void_r, FCY+void_r,
                fill=C_BG,
                outline="",
            )

    # ── Ana çizim ─────────────────────────────────────────────────────────────
    def _draw(self):
        c  = self.bg
        W  = self.W
        H  = self.H
        t  = getattr(self, "_visual_tick", self.tick)
        c.delete("all")

        # ── Arka plan ────────────────────────────────────────────────────────
        # Nokta ızgarası — 3 karede bir çiz, geniş adım → düşük yük
        if t % 3 == 0:
            step = 72
            for x in range(0, W, step):
                for y in range(0, H, step):
                    c.create_rectangle(x, y, x+1, y+1, fill=C_DIMMER, outline="")

        # (Arka plan akıcı siber karanlık - sıfır kasma için animasyon çizgileri kaldırıldı)

        # Partiküller
        R, G, B = self._orb_rgb()
        background_count = {"calm": 8, "standard": 24, "cinematic": 48}.get(self._visual_effect_mode, 24)
        for p in self.particles[:background_count]:
            if self.speaking:
                col = self._ac(255, 110, 0, p['a'])
            else:
                col = self._ac(R, G, B, p['a'])
            r = p['r']
            c.create_oval(p['x']-r, p['y']-r, p['x']+r, p['y']+r,
                          fill=col, outline="")

        # ── Bölücü çizgiler (ince, soluk) ────────────────────────────────────
        eff_div_footer = 0 if getattr(self, "_fullscreen", False) else FOOTER_H
        c.create_line(self.LEFT_W, HDR_H, self.LEFT_W, H-eff_div_footer,
                      fill=C_DIM, width=1)
        c.create_line(W-self.RIGHT_W, HDR_H, W-self.RIGHT_W, H-eff_div_footer,
                      fill=C_DIM, width=1)

        # ── Yan paneller ──────────────────────────────────────────────────────
        self._draw_left_panel(c)
        self._draw_right_panel(c)

        # ── Orb — kamera açıkken aşağı kayar, sert halkalar gizlenir ─────────
        self._draw_orb(c, cam=self._webcam_active)

        state_label = "PAUSED" if self.paused else self._jarvis_state
        state_col = self._state_color(state_label)
        c.create_text(self.FCX, self.CTRL_Y - 34, text=SYSTEM_NAME,
                      fill=C_TEXT, font=font_display(18))
        c.create_text(self.FCX, self.CTRL_Y - 12, text=f"● {state_label.title()}",
                      fill=state_col, font=font_body_bold(11))

        # ── HEADER ───────────────────────────────────────────────────────────
        c.create_rectangle(0, 0, W, HDR_H, fill="#010a0a", outline="")
        # Alt çizgi — teal parlak
        c.create_line(0, HDR_H, W, HDR_H, fill=C_MID, width=1)
        for i in range(3):
            a = 60 - i * 18
            c.create_line(0, HDR_H-1-i, W, HDR_H-1-i,
                          fill=self._ac(0, 180, 165, a), width=1)

        # Büyük başlık
        c.create_text(W//2, 24, text=SYSTEM_NAME,
                      fill=C_PRI, font=font_display(26))
        c.create_text(W//2, 52, text="Just A Rather Very Intelligent System",
                      fill=C_MID, font=font_body(11))

        # Sol: model badge
        c.create_text(22, 36, text=MODEL_BADGE,
                      fill=C_DIM, font=font_body(10), anchor="w")

        # Sağ: durum indikatörü
        indicator_state = "PAUSED" if self.paused else self._jarvis_state
        ind_col = self._state_color(indicator_state)
        indicator_text = self._state_badge_text(indicator_state)
        sym = "●" if self.status_blink else "○"
        c.create_text(W-22, 28, text=f"{sym}  {indicator_text}",
                      fill=ind_col, font=font_body_bold(11), anchor="e")

        # Webcam canlı yayın göstergesi
        if self._webcam_active:
            cam_blink = "●" if self.status_blink else "◉"
            c.create_text(W-22, 52, text=f"{cam_blink}  CAM LIVE",
                          fill=C_RED, font=font_body_bold(9), anchor="e")

        # ── FOOTER (Tam ekrandayken alt boşluğu önlemek için gizlenir) ─────────
        if not getattr(self, "_fullscreen", False):
            c.create_rectangle(0, H-FOOTER_H, W, H, fill="#010a0a", outline="")
            c.create_line(0, H-FOOTER_H, W, H-FOOTER_H, fill=C_DIM, width=1)
            c.create_text(W//2, H-13, fill=C_DIM, font=font_body(9),
                          text="JARVIS V4 · Windows Edition · Realtime Voice Core")
            c.create_text(W-18, H-13, fill=C_DIM, font=font_body(9),
                          text="[F4] MUTE  [F5] PAUSE  [F6] CAM  [F8] ISLAND  [F11] FULLSCREEN  [ESC] WINDOWED", anchor="e")

    def wait_for_api_key(self):
        while not self._api_key_ready:
            time.sleep(0.1)

    def _show_setup_ui(self, edit_mode: bool = False):
        self._close_setup_ui()

        self.setup_frame = tk.Frame(self.root, bg="#00080d",
                                    highlightbackground=C_PRI,
                                    highlightthickness=1)
        self.setup_frame.place(relx=0.5, rely=0.5, anchor="center")

        title = "◈ API AYARLARI" if edit_mode else "◈ İLK KURULUM GEREKLİ"
        subtitle = (
            "Gemini API anahtarinizi guncelleyin."
            if edit_mode else
            "Gemini API anahtarinizi girin."
        )
        config = load_app_config()

        tk.Label(self.setup_frame, text=title,
                 fg=C_PRI, bg="#00080d", font=font_display(16)).pack(pady=(18, 4))
        tk.Label(self.setup_frame, text=subtitle,
                 fg=C_MID, bg="#00080d", font=font_body(11)).pack(pady=(0, 10))
        tk.Label(self.setup_frame, text="GEMINI API KEY",
                 fg=C_DIM, bg="#00080d", font=font_body(11)).pack(pady=(8, 2))

        self.api_entry = tk.Entry(
            self.setup_frame, width=52,
            fg=C_TEXT, bg="#000d12", insertbackground=C_TEXT,
            borderwidth=0, font=font_body(12), show="*")
        self.api_entry.pack(pady=(0, 6))

        current_key = str(config.get("gemini_api_key", "") or "")
        if current_key:
            self.api_entry.insert(0, current_key)

        buttons = tk.Frame(self.setup_frame, bg="#00080d")
        buttons.pack(pady=14)

        tk.Button(buttons, text="▸ KAYDET",
                  command=self._save_api_key, bg=C_BG, fg=C_PRI,
                  activebackground="#003344", font=font_body_bold(12),
                  borderwidth=0, padx=18, pady=8).pack(side="left", padx=6)

        if edit_mode:
            tk.Button(buttons, text="KAPAT",
                      command=self._close_setup_ui, bg="#08111a", fg=C_DIM,
                      activebackground="#10202b", font=font_body_bold(12),
                      borderwidth=0, padx=18, pady=8).pack(side="left", padx=6)

    def _save_api_key(self):
        was_ready = self._api_key_ready
        key = self.api_entry.get().strip() if self.api_entry else ""
        if not key:
            return
        youtube_key = self.youtube_api_entry.get().strip() if self.youtube_api_entry else ""
        youtube_handle = self.youtube_handle_entry.get().strip() if self.youtube_handle_entry else ""
        save_app_config(
            {
                "gemini_api_key": key,
                "youtube_api_key": youtube_key,
                "youtube_channel_handle": youtube_handle,
                "voice": self._current_voice,
            }
        )
        self._close_setup_ui()
        self._api_key_ready = True
        self._refresh_settings_status()
        if was_ready:
            self.write_log("SYS: API ayarlari guncellendi.")
        else:
            self.set_state("LISTENING")
            self.write_log("SYS: JARVIS hazır. Dinliyorum...")
