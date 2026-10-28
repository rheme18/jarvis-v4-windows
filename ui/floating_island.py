# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S V4 — 4K Ultra-Smooth Apple Dynamic Island HUD
Sinematik Doğuş Animasyonu (Cinematic Reveal Animation):
- F8 veya 'Jarvis' dendiğinde ekranın alt ortasında dönen saf beyaz akıcı ışıklı siyah küre doğar
- Noktasız, kusursuz akıcı ipeksi sıvı beyaz ışık küre içinde yüzer
- Organik bir yay/genleşme ile sola ve sağa doğru açılarak Dynamic Island'a dönüşür
- 4K Supersampling (2x Retina) ile jilet keskinliğinde vektörel mikrofon ve kapatma butonu
- 5 katmanlı ipeksi duman / ışık dalgası (Multi-harmonic Silk Ribbon Wave)
- Sürüklenebilir ve çift tıklamayla ana paneli geri açar.
"""

import math
import random
import time
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw

PILL_W = 300
PILL_H = 46
ORB_SIZE = 46
SCALE = 2  # 2x Supersampling -> 4K / Retina pürüzsüzlüğü


class FloatingIsland:
    def __init__(self, jarvis_ui, on_restore_callback=None, animate_intro=True):
        self.jarvis_ui = jarvis_ui
        self.on_restore_callback = on_restore_callback

        self.root = tk.Toplevel()
        self.root.title("JARVIS Dynamic Island 4K")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        self.trans_bg = "#010101"
        try:
            self.root.attributes("-transparentcolor", self.trans_bg)
        except Exception:
            pass

        self.root.configure(bg=self.trans_bg)

        self.sw = self.root.winfo_screenwidth()
        self.sh = self.root.winfo_screenheight()
        self.start_y = max(40, self.sh - PILL_H - 85)

        # Animasyon durumları: "SPAWNING_ORB" -> "EXPANDING" -> "ACTIVE" -> "COLLAPSING"
        if animate_intro:
            self.stage = "SPAWNING_ORB"
            self.current_w = ORB_SIZE
            self.current_h = ORB_SIZE
            self.current_x = (self.sw - ORB_SIZE) // 2
            self.current_y = self.start_y
            self._orb_frames = 0
            self._orb_angle = 0.0
            self._orb_pulse = 0.0
            self._expand_start_time = 0.0
            self._expand_duration = 0.45
        else:
            self.stage = "ACTIVE"
            self.current_w = PILL_W
            self.current_h = PILL_H
            self.current_x = (self.sw - PILL_W) // 2
            self.current_y = self.start_y

        self.root.geometry(f"{self.current_w}x{self.current_h}+{self.current_x}+{self.current_y}")

        self._drag_start_x = 0
        self._drag_start_y = 0

        # İpeksi dalga fazları ve genlikleri
        self._phase = 0.0
        self._smoothed_amp = 0.5
        self._photo_ref = None

        self._setup_canvas()
        self._bind_events()
        self._is_running = True
        self._animate()

    def _setup_canvas(self):
        self.canvas = tk.Canvas(
            self.root, width=self.current_w, height=self.current_h,
            bg=self.trans_bg, highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

    def _bind_events(self):
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<Double-Button-1>", lambda e: self.restore_main_ui())

    def _on_click(self, event):
        if self.stage != "ACTIVE":
            return
        x = event.x
        # Sol Mikrofon (x: 8 to 46)
        if 8 <= x <= 46:
            self._toggle_mute()
            return
        # Sağ Kapat (x: PILL_W - 46 to PILL_W - 6)
        if (PILL_W - 46) <= x <= (PILL_W - 6):
            self.close()
            return
        # Gövdeyi sürükle
        self._drag_start_x = event.x_root - self.root.winfo_x()
        self._drag_start_y = event.y_root - self.root.winfo_y()

    def _on_drag(self, event):
        if self.stage != "ACTIVE":
            return
        new_x = event.x_root - self._drag_start_x
        new_y = event.y_root - self._drag_start_y
        self.current_x = new_x
        self.current_y = new_y
        self.root.geometry(f"+{new_x}+{new_y}")

    def _toggle_mute(self):
        if hasattr(self.jarvis_ui, "_toggle_mute"):
            self.jarvis_ui._toggle_mute()
        elif hasattr(self.jarvis_ui, "muted"):
            self.jarvis_ui.muted = not self.jarvis_ui.muted

    def restore_main_ui(self):
        self._is_running = False
        try:
            self.root.destroy()
        except Exception:
            pass
        if self.on_restore_callback:
            self.on_restore_callback()
        elif hasattr(self.jarvis_ui, "root"):
            try:
                self.jarvis_ui.root.deiconify()
                self.jarvis_ui.root.lift()
                self.jarvis_ui.root.focus_force()
            except Exception:
                pass

    def close(self):
        if self.stage == "ACTIVE":
            self.stage = "COLLAPSING"
            self._collapse_start_time = time.time()
            self._collapse_duration = 0.28
        else:
            self._destroy_now()

    def _destroy_now(self):
        # The main JARVIS window is withdrawn while the island is active.
        # Closing the island must restore the main UI, otherwise the process
        # keeps running with no visible window.
        if self.on_restore_callback:
            self.restore_main_ui()
            return

        self._is_running = False
        try:
            self.root.destroy()
        except Exception:
            pass
        if hasattr(self.jarvis_ui, "root"):
            try:
                self.jarvis_ui._in_background_mode = False
                self.jarvis_ui.root.deiconify()
                self.jarvis_ui.root.lift()
                self.jarvis_ui.root.focus_force()
            except Exception:
                pass

    # ── 4K Supersampled Render Motoru ─────────────────────────────────────────
    def _render_image(self):
        W = self.current_w * SCALE
        H = PILL_H * SCALE

        img = Image.new("RGBA", (W, H), (1, 1, 1, 0))
        draw = ImageDraw.Draw(img)

        pad = 2 * SCALE
        r = (H - 2 * pad) // 2

        # ── 1. SAHNE: SPAWNING ORB (Siyah Daire İçinde Yüzen Akıcı Beyaz Işık - Noktasız) ──
        if self.stage == "SPAWNING_ORB":
            cx = W // 2
            cy = H // 2
            orb_r = (W - 2 * pad) // 2

            pulse_factor = 0.5 + 0.5 * math.sin(self._orb_pulse)

            # 1. Dış katman: Ethereal yumuşak haleler (Concentric Ambient Aura)
            for halo_offset, alpha in [(5, 20), (3, 45), (1, 75)]:
                hr = orb_r + int(halo_offset * SCALE * (0.85 + 0.25 * pulse_factor))
                draw.ellipse(
                    (cx - hr, cy - hr, cx + hr, cy + hr),
                    fill=None,
                    outline=(255, 255, 255, int(alpha * (0.6 + 0.4 * pulse_factor))),
                    width=int(1.2 * SCALE)
                )

            # 2. Gövde: Derin OLED Saf Siyah Cam Küre
            draw.ellipse(
                (pad, pad, W - pad, H - pad),
                fill=(0, 0, 0, 255),
                outline=(255, 255, 255, int(210 + 45 * pulse_factor)),
                width=int(1.8 * SCALE)
            )

            # 3. Yüzen Sıvı Beyaz Işık Çekirdeği (Apple Siri Glow - Luminous Liquid Swimming Core)
            # 3 adet iç içe yüzen, orbit yapan yumuşak beyaz sıvı ışık elipsi
            t_pulse = self._orb_pulse
            for idx, (spd_x, spd_y, rad_x, rad_y, max_alpha) in enumerate([
                (1.4, 1.8, 0.42, 0.35, 160),
                (-1.7, 1.2, 0.32, 0.28, 190),
                (0.9, -1.5, 0.22, 0.20, 240)
            ]):
                lx = cx + math.sin(t_pulse * spd_x + idx * 1.5) * (orb_r * 0.32)
                ly = cy + math.cos(t_pulse * spd_y + idx * 1.2) * (orb_r * 0.26)
                ew = int(orb_r * rad_x + 3.0 * SCALE * pulse_factor)
                eh = int(orb_r * rad_y + 2.5 * SCALE * pulse_factor)
                al = int(max_alpha * (0.65 + 0.35 * pulse_factor))
                draw.ellipse(
                    (lx - ew, ly - eh, lx + ew, ly + eh),
                    fill=(255, 255, 255, al),
                    outline=None
                )

            # 4. Yüzen Akıcı Rim Highlight (Dönen akıcı tepe yansıması - noktasız)
            arc_start = self._orb_angle
            draw.arc(
                (pad + int(2 * SCALE), pad + int(2 * SCALE), W - pad - int(2 * SCALE), H - pad - int(2 * SCALE)),
                start=arc_start,
                end=arc_start + 135.0,
                fill=(255, 255, 255, 255),
                width=int(2.6 * SCALE)
            )

            # Ters yönde yüzen pürüzsüz opal ışık akışı
            rev_start = (-self._orb_angle * 0.75 + 140.0) % 360.0
            draw.arc(
                (pad + int(4 * SCALE), pad + int(4 * SCALE), W - pad - int(4 * SCALE), H - pad - int(4 * SCALE)),
                start=rev_start,
                end=rev_start + 110.0,
                fill=(235, 250, 255, int(150 + 80 * pulse_factor)),
                width=int(2.0 * SCALE)
            )

            # 5. Küre İçinde Yüzen Organik Beyaz Sıvı Dalgası (Silk Ribbon Wave)
            num_pts = 48
            wave_span = orb_r * 0.78
            curve1 = []
            for i in range(num_pts + 1):
                prog = i / float(num_pts)
                lx = (cx - wave_span) + prog * (wave_span * 2.0)
                env = math.sin(prog * math.pi)
                ly = cy + (math.sin(prog * math.pi * 2.2 + t_pulse * 2.1) * (8.0 * SCALE) + math.cos(t_pulse * 1.4) * (4.0 * SCALE)) * env
                curve1.append((lx, ly))

            draw.line(curve1, fill=(255, 255, 255, int(220 + 35 * pulse_factor)), width=int(2.8 * SCALE), joint="curve")

            # 5. Küre İçinde Yüzen İkinci İpeksi Işık Dalgası 2 (Ters salınımlı saydam şerit)
            curve2 = []
            for i in range(num_pts + 1):
                prog = i / float(num_pts)
                lx = (cx - wave_span * 0.88) + prog * (wave_span * 1.76)
                env = math.sin(prog * math.pi)
                ly = cy + (math.sin(prog * math.pi * 2.6 - t_pulse * 1.6 + 1.2) * (6.0 * SCALE) - math.sin(t_pulse * 1.1) * (3.0 * SCALE)) * env
                curve2.append((lx, ly))

            draw.line(curve2, fill=(225, 245, 255, int(120 + 60 * pulse_factor)), width=int(1.8 * SCALE), joint="curve")

            # 6. Yüzen Saydam Parıltı Hüzmesi (Floating Specular Shimmer - yumuşak elips ışığı)
            shim_x = cx + math.sin(t_pulse * 1.3) * (orb_r * 0.26)
            shim_y = cy + math.cos(t_pulse * 1.6) * (orb_r * 0.20)
            rw = int(orb_r * 0.38 + 2.0 * SCALE * pulse_factor)
            rh = int(orb_r * 0.22 + 1.5 * SCALE * pulse_factor)
            draw.ellipse(
                (shim_x - rw, shim_y - rh, shim_x + rw, shim_y + rh),
                fill=(255, 255, 255, int(55 + 50 * pulse_factor)),
                outline=None
            )

            final_img = img.resize((self.current_w, PILL_H), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(final_img)

        # ── 2. SAHNE: EXPANDING / ACTIVE / COLLAPSING ─────────────────────────
        draw.rounded_rectangle(
            (pad, pad, W - pad, H - pad),
            radius=r,
            fill=(0, 0, 0, 255),
            outline=(255, 255, 255, 250),
            width=int(1.6 * SCALE)
        )

        fade_ratio = 1.0
        if self.stage == "EXPANDING":
            if self.current_w < 140:
                fade_ratio = 0.0
            else:
                fade_ratio = min(1.0, (self.current_w - 140) / (PILL_W - 140))
        elif self.stage == "COLLAPSING":
            fade_ratio = max(0.0, (self.current_w - 140) / (PILL_W - 140))

        if fade_ratio > 0.05:
            alpha_mult = fade_ratio
            is_muted = getattr(self.jarvis_ui, "muted", False)
            is_speaking = getattr(self.jarvis_ui, "speaking", False)
            is_paused = getattr(self.jarvis_ui, "paused", False)
            state = getattr(self.jarvis_ui, "_jarvis_state", "LISTENING")

            # Sol Vektörel Mikrofon
            mic_cx = int(25 * SCALE)
            mic_cy = H // 2
            if is_muted:
                mic_col = (255, 69, 58, int(255 * alpha_mult))
            else:
                mic_col = (235, 235, 240, int(240 * alpha_mult))

            mw = int(3.2 * SCALE)
            draw.rounded_rectangle(
                (mic_cx - mw, mic_cy - int(8 * SCALE), mic_cx + mw, mic_cy + int(2 * SCALE)),
                radius=mw, fill=mic_col
            )
            draw.arc(
                (mic_cx - int(6.5 * SCALE), mic_cy - int(4 * SCALE), mic_cx + int(6.5 * SCALE), mic_cy + int(7 * SCALE)),
                start=0, end=180, fill=mic_col, width=int(1.6 * SCALE)
            )
            draw.line(
                [(mic_cx, mic_cy + int(7 * SCALE)), (mic_cx, mic_cy + int(10 * SCALE))],
                fill=mic_col, width=int(1.6 * SCALE)
            )
            draw.line(
                [(mic_cx - int(4 * SCALE), mic_cy + int(10 * SCALE)), (mic_cx + int(4 * SCALE), mic_cy + int(10 * SCALE))],
                fill=mic_col, width=int(1.6 * SCALE)
            )
            if is_muted:
                draw.line(
                    [(mic_cx - int(7 * SCALE), mic_cy - int(7 * SCALE)), (mic_cx + int(7 * SCALE), mic_cy + int(8 * SCALE))],
                    fill=(255, 69, 58, int(255 * alpha_mult)), width=int(2.0 * SCALE)
                )

            # Sağ Vektörel Minimalist Çarpı (✕)
            cl_cx = W - int(25 * SCALE)
            cl_cy = H // 2
            cl_r = int(9 * SCALE)
            draw.ellipse(
                (cl_cx - cl_r, cl_cy - cl_r, cl_cx + cl_r, cl_cy + cl_r),
                fill=(28, 28, 30, int(240 * alpha_mult)),
                outline=(60, 60, 64, int(200 * alpha_mult)),
                width=int(1 * SCALE)
            )
            xr = int(3.6 * SCALE)
            draw.line([(cl_cx - xr, cl_cy - xr), (cl_cx + xr, cl_cy + xr)], fill=(160, 160, 165, int(240 * alpha_mult)), width=int(1.6 * SCALE))
            draw.line([(cl_cx + xr, cl_cy - xr), (cl_cx - xr, cl_cy + xr)], fill=(160, 160, 165, int(240 * alpha_mult)), width=int(1.6 * SCALE))

            # Orta İpeksi Çok Katmanlı Duman/Işık Dalgası (5-Harmonic Silk Ribbons)
            wave_start_x = int(52 * SCALE)
            wave_end_x = W - int(52 * SCALE)
            wave_w = max(10, wave_end_x - wave_start_x)
            center_y = H // 2

            self._phase += 0.15

            if is_muted:
                target_amp = 0.0
            elif is_paused:
                target_amp = 3.0 * SCALE
            elif is_speaking:
                target_amp = 14.0 * SCALE
            elif state == "THINKING":
                target_amp = 9.0 * SCALE
            else:
                target_amp = 5.5 * SCALE

            self._smoothed_amp += (target_amp - self._smoothed_amp) * 0.24

            if self._smoothed_amp < 0.8:
                draw.line(
                    [(wave_start_x, center_y), (wave_end_x, center_y)],
                    fill=(70, 70, 75, int(180 * alpha_mult)),
                    width=int(1.5 * SCALE)
                )
            else:
                ribbons = [
                    {"speed": 1.0,  "freq": 3.0, "amp_m": 1.00, "phase_off": 0.0, "alpha": int(240 * alpha_mult), "width": int(2.2 * SCALE)},
                    {"speed": -1.2, "freq": 4.2, "amp_m": 0.85, "phase_off": 1.2, "alpha": int(180 * alpha_mult), "width": int(1.8 * SCALE)},
                    {"speed": 0.8,  "freq": 2.5, "amp_m": 0.70, "phase_off": 2.4, "alpha": int(140 * alpha_mult), "width": int(1.5 * SCALE)},
                    {"speed": -1.5, "freq": 5.0, "amp_m": 0.55, "phase_off": 3.6, "alpha": int(100 * alpha_mult), "width": int(1.2 * SCALE)},
                    {"speed": 1.3,  "freq": 3.6, "amp_m": 0.40, "phase_off": 4.8, "alpha": int(70  * alpha_mult), "width": int(1.0 * SCALE)},
                ]

                num_steps = 60
                for r_info in ribbons:
                    points = []
                    for step in range(num_steps + 1):
                        t = step / float(num_steps)
                        px = wave_start_x + t * wave_w
                        envelope = math.sin(t * math.pi)
                        wave_val = math.sin(self._phase * r_info["speed"] + t * math.pi * r_info["freq"] + r_info["phase_off"])
                        py = center_y + wave_val * (self._smoothed_amp * r_info["amp_m"]) * envelope
                        points.append((px, py))

                    if is_speaking:
                        wave_rgba = (120, 220, 255, r_info["alpha"])
                    else:
                        wave_rgba = (255, 255, 255, r_info["alpha"])

                    draw.line(points, fill=wave_rgba, width=r_info["width"], joint="curve")

        final_img = img.resize((self.current_w, PILL_H), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(final_img)

    def _animate(self):
        if not self._is_running:
            return

        # ── State Machine Geçişleri ──────────────────────────────────────────
        if self.stage == "SPAWNING_ORB":
            self._orb_frames += 1
            self._orb_angle = (self._orb_angle + 4.5) % 360.0
            self._orb_pulse += 0.055
            if self._orb_frames >= 65:  # ~1.1 saniye süper akıcı siri açılış efekti
                self.stage = "EXPANDING"
                self._expand_start_time = time.time()

        elif self.stage == "EXPANDING":
            elapsed = time.time() - self._expand_start_time
            progress = min(1.0, elapsed / self._expand_duration)
            ease = 1.0 - math.pow(1.0 - progress, 3)
            self.current_w = int(ORB_SIZE + (PILL_W - ORB_SIZE) * ease)
            self.current_x = (self.sw - self.current_w) // 2

            self.root.geometry(f"{self.current_w}x{PILL_H}+{self.current_x}+{self.current_y}")
            self.canvas.config(width=self.current_w, height=PILL_H)

            if progress >= 1.0:
                self.stage = "ACTIVE"
                self.current_w = PILL_W
                self.current_x = (self.sw - PILL_W) // 2
                self.root.geometry(f"{PILL_W}x{PILL_H}+{self.current_x}+{self.current_y}")
                self.canvas.config(width=PILL_W, height=PILL_H)

        elif self.stage == "COLLAPSING":
            elapsed = time.time() - self._collapse_start_time
            progress = min(1.0, elapsed / self._collapse_duration)
            ease = math.pow(progress, 3)  # cubic ease in
            self.current_w = max(ORB_SIZE, int(PILL_W - (PILL_W - ORB_SIZE) * ease))
            self.current_x = (self.sw - self.current_w) // 2

            self.root.geometry(f"{self.current_w}x{PILL_H}+{self.current_x}+{self.current_y}")
            self.canvas.config(width=self.current_w, height=PILL_H)

            if progress >= 1.0:
                self._destroy_now()
                return

        # ── Frame Render ─────────────────────────────────────────────────────
        try:
            self._photo_ref = self._render_image()
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, image=self._photo_ref, anchor="nw")
        except Exception as e:
            print(f"[DynamicIsland] Render hatası: {e}")

        # 16ms -> ~60 FPS kusursuz akıcılık
        self.root.after(16, self._animate)
