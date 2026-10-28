# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S V4 — Cyber Arcade & Entertainment Hub
Tetris, Snake, Cyber-Pong (Jarvis AI), Refleks Testi ve Jarvis Trivia
"""

import json
import random
import time
import tkinter as tk
from pathlib import Path

BG = "#04090c"
PANEL = "#09141c"
CYAN = "#00F0FF"
PINK = "#FF0055"
GOLD = "#FFCC00"
GREEN = "#00FF88"
TEXT = "#D9E7EF"
DIM = "#13313d"

BASE_DIR = Path(__file__).resolve().parents[1]
SCORES_FILE = BASE_DIR / "memory" / "arcade_scores.json"


class JarvisArcade:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S V4 · SİBER ARCADE & EĞLENCE MERKEZİ")
        self.root.geometry("700x720")
        self.root.minsize(640, 680)
        self.root.configure(bg=BG)

        self.scores = self.load_scores()
        self.active_mode = "menu"
        self.job = None

        self._build_header()
        self._build_main_container()
        self.show_menu()

        self.root.bind("<Key>", self.handle_key)
        self.root.mainloop()

    def load_scores(self):
        if SCORES_FILE.exists():
            try:
                return json.loads(SCORES_FILE.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def save_score(self, key, value):
        best = self.scores.get(key, 0)
        if value > best:
            self.scores[key] = value
            try:
                SCORES_FILE.parent.mkdir(parents=True, exist_ok=True)
                SCORES_FILE.write_text(json.dumps(self.scores, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                pass

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=BG)
        hdr.pack(fill="x", padx=18, pady=(14, 6))

        tk.Label(hdr, text="⚡ J.A.R.V.I.S V4 · ENTERTAINMENT HUB ⚡",
                 font=("Consolas", 14, "bold"), fg=CYAN, bg=BG).pack(side="left")

        self.btn_back = tk.Button(
            hdr, text="⌂ MENÜYE DÖN", command=self.show_menu,
            bg=PANEL, fg=TEXT, activebackground=DIM, activeforeground=CYAN,
            relief="flat", font=("Consolas", 9, "bold"), padx=10, pady=4
        )
        self.btn_back.pack(side="right")

    def _build_main_container(self):
        self.container = tk.Frame(self.root, bg=BG)
        self.container.pack(fill="both", expand=True, padx=18, pady=10)

    def clear_container(self):
        if self.job:
            try:
                self.root.after_cancel(self.job)
            except Exception:
                pass
            self.job = None
        for w in self.container.winfo_children():
            w.destroy()

    # ── ANA MENÜ ─────────────────────────────────────────────────────────────
    def show_menu(self):
        self.active_mode = "menu"
        self.clear_container()

        title = tk.Label(self.container, text="PROTOKOL SEÇİMİ", font=("Consolas", 12, "bold"), fg="#4a8f96", bg=BG)
        title.pack(anchor="w", pady=(0, 10))

        games = [
            ("🕹️  CYBER TETRIS", "Klasik blok yerleştirme protokolü — refleks ve uzamsal zeka", "#00d4c0", self.start_tetris),
            ("🐍  CYBER SNAKE", "Neon veri akışı yılanı — parçacık topla ve hayatta kal", "#00ff88", self.start_snake),
            ("🏓  JARVIS PONG (AI DÜELLO)", "Jarvis'in yapay zekasına karşı hava hokeyi / tenis", "#ff0055", self.start_pong),
            ("🎯  REFLEKS TESTİ (REACTION)", "Milisaniye hassasiyetinde nöronal hız ve tepki ölçümü", "#ffcc00", self.start_reaction),
            ("🧠  JARVIS SİBER BİLGİ YARIŞMASI", "Teknoloji, bilim ve yapay zeka trivia düellosu", "#38bdf8", self.start_trivia),
        ]

        for name, desc, color, callback in games:
            card = tk.Frame(self.container, bg=PANEL, highlightbackground=color, highlightthickness=1)
            card.pack(fill="x", pady=6, ipady=4)

            btn = tk.Button(
                card, text=name, command=callback, bg=PANEL, fg=color,
                activebackground=DIM, activeforeground=color,
                font=("Consolas", 11, "bold"), relief="flat", anchor="w", cursor="hand2"
            )
            btn.pack(fill="x", padx=12, pady=(6, 2))

            tk.Label(card, text=desc, font=("Consolas", 9), fg="#7a9ba6", bg=PANEL, anchor="w").pack(fill="x", padx=14, pady=(0, 6))

        # En Yüksek Skorlar Özeti
        score_box = tk.Frame(self.container, bg="#020e14", highlightbackground=DIM, highlightthickness=1)
        score_box.pack(fill="x", pady=(14, 0), ipady=6)
        tk.Label(score_box, text="🏆 REKOR TABLOSU", font=("Consolas", 10, "bold"), fg=GOLD, bg="#020e14").pack(anchor="w", padx=12, pady=4)

        t_score = self.scores.get("tetris", 0)
        s_score = self.scores.get("snake", 0)
        p_score = self.scores.get("pong", 0)
        r_score = self.scores.get("reaction", "--")

        stats_txt = f"Tetris: {t_score} Puan  |  Snake: {s_score} Puan  |  Pong Galibiyet: {p_score}  |  En İyi Refleks: {r_score}ms"
        tk.Label(score_box, text=stats_txt, font=("Consolas", 9), fg=TEXT, bg="#020e14").pack(anchor="w", padx=12, pady=2)

    # ── 1. TETRIS ────────────────────────────────────────────────────────────
    def start_tetris(self):
        self.active_mode = "tetris"
        self.clear_container()

        bar = tk.Frame(self.container, bg=BG)
        bar.pack(fill="x", pady=(0, 6))
        self.t_score_var = tk.StringVar(value="SKOR: 0")
        tk.Label(bar, textvariable=self.t_score_var, font=("Consolas", 11, "bold"), fg=CYAN, bg=BG).pack(side="left")
        tk.Label(bar, text="SOL/SAĞ: Hareket  |  YUKARI: Döndür  |  AŞAĞI: Hızlandır  |  SPACE: Bırak",
                 font=("Consolas", 8), fg="#7a9ba6", bg=BG).pack(side="right")

        self.canvas = tk.Canvas(self.container, width=320, height=560, bg="#02080d",
                                highlightthickness=1, highlightbackground=CYAN)
        self.canvas.pack(pady=4)

        self.t_board = [[0] * 10 for _ in range(20)]
        self.t_points = 0
        self.t_game_over = False
        self.t_piece = self._new_tetris_piece()
        self._tetris_tick()

    def _new_tetris_piece(self):
        shapes = [
            ([(0, 0), (1, 0), (0, 1), (1, 1)], "#ffcc00"), # O
            ([(0, 0), (1, 0), (2, 0), (1, 1)], "#c084fc"), # T
            ([(0, 0), (1, 0), (2, 0), (3, 0)], "#00f0ff"), # I
            ([(0, 0), (0, 1), (1, 1), (2, 1)], "#ff9900"), # L
            ([(2, 0), (0, 1), (1, 1), (2, 1)], "#4488ff"), # J
            ([(1, 0), (2, 0), (0, 1), (1, 1)], "#00ff88"), # S
            ([(0, 0), (1, 0), (1, 1), (2, 1)], "#ff0055"), # Z
        ]
        coords, color = random.choice(shapes)
        return {"blocks": [(x + 3, y) for x, y in coords], "color": color}

    def _tetris_valid(self, blocks):
        for x, y in blocks:
            if x < 0 or x >= 10 or y >= 20:
                return False
            if y >= 0 and self.t_board[y][x]:
                return False
        return True

    def _tetris_tick(self):
        if self.t_game_over or self.active_mode != "tetris":
            return
        next_blocks = [(x, y + 1) for x, y in self.t_piece["blocks"]]
        if self._tetris_valid(next_blocks):
            self.t_piece["blocks"] = next_blocks
        else:
            for x, y in self.t_piece["blocks"]:
                if y < 0:
                    self.t_game_over = True
                    self.save_score("tetris", self.t_points)
                    self._draw_game_over("TETRIS PROTOKOLÜ TAMAMLANDI")
                    return
                self.t_board[y][x] = self.t_piece["color"]

            new_board = [row for row in self.t_board if any(c == 0 for c in row)]
            cleared = 20 - len(new_board)
            if cleared > 0:
                self.t_points += cleared * cleared * 100
                self.t_score_var.set(f"SKOR: {self.t_points}")
                self.t_board = [[0] * 10 for _ in range(cleared)] + new_board

            self.t_piece = self._new_tetris_piece()
            if not self._tetris_valid(self.t_piece["blocks"]):
                self.t_game_over = True
                self.save_score("tetris", self.t_points)
                self._draw_game_over("TETRIS OYUN BİTTİ")
                return

        self._draw_tetris()
        self.job = self.root.after(340, self._tetris_tick)

    def _draw_tetris(self):
        self.canvas.delete("all")
        cs = 28
        for i in range(1, 10):
            self.canvas.create_line(i * cs, 0, i * cs, 560, fill="#061622", width=1)
        for i in range(1, 20):
            self.canvas.create_line(0, i * cs, 280, i * cs, fill="#061622", width=1)

        for y in range(20):
            for x in range(10):
                color = self.t_board[y][x]
                if color:
                    self.canvas.create_rectangle(x * cs + 1, y * cs + 1, (x + 1) * cs - 1, (y + 1) * cs - 1,
                                                 fill=color, outline="#ffffff", width=1)

        if self.t_piece:
            color = self.t_piece["color"]
            for x, y in self.t_piece["blocks"]:
                if y >= 0:
                    self.canvas.create_rectangle(x * cs + 1, y * cs + 1, (x + 1) * cs - 1, (y + 1) * cs - 1,
                                                 fill=color, outline="#ffffff", width=1)

    # ── 2. SNAKE ─────────────────────────────────────────────────────────────
    def start_snake(self):
        self.active_mode = "snake"
        self.clear_container()

        bar = tk.Frame(self.container, bg=BG)
        bar.pack(fill="x", pady=(0, 6))
        self.s_score_var = tk.StringVar(value="SKOR: 0")
        tk.Label(bar, textvariable=self.s_score_var, font=("Consolas", 11, "bold"), fg=GREEN, bg=BG).pack(side="left")
        tk.Label(bar, text="OKLAR veya W A S D ile yönlendir", font=("Consolas", 9), fg="#7a9ba6", bg=BG).pack(side="right")

        self.canvas = tk.Canvas(self.container, width=500, height=500, bg="#02080d",
                                highlightthickness=1, highlightbackground=GREEN)
        self.canvas.pack(pady=4)

        self.snake = [(10, 10), (9, 10), (8, 10)]
        self.s_dir = (1, 0)
        self.s_pending = (1, 0)
        self.s_food = self._new_snake_food()
        self.s_points = 0
        self.s_game_over = False
        self._snake_tick()

    def _new_snake_food(self):
        avail = [(x, y) for x in range(20) for y in range(20) if (x, y) not in self.snake]
        return random.choice(avail) if avail else None

    def _snake_tick(self):
        if self.s_game_over or self.active_mode != "snake":
            return
        self.s_dir = self.s_pending
        hx, hy = self.snake[0]
        dx, dy = self.s_dir
        nx, ny = hx + dx, hy + dy

        if nx < 0 or nx >= 20 or ny < 0 or ny >= 20 or (nx, ny) in self.snake:
            self.s_game_over = True
            self.save_score("snake", self.s_points)
            self._draw_game_over("SNAKE BAĞLANTISI KOPTU")
            return

        self.snake.insert(0, (nx, ny))
        if (nx, ny) == self.s_food:
            self.s_points += 10
            self.s_score_var.set(f"SKOR: {self.s_points}")
            self.s_food = self._new_snake_food()
        else:
            self.snake.pop()

        self._draw_snake()
        speed = max(60, 130 - (self.s_points // 40) * 8)
        self.job = self.root.after(speed, self._snake_tick)

    def _draw_snake(self):
        self.canvas.delete("all")
        cs = 25
        if self.s_food:
            fx, fy = self.s_food
            self.canvas.create_oval(fx * cs + 3, fy * cs + 3, (fx + 1) * cs - 3, (fy + 1) * cs - 3,
                                    fill=PINK, outline="#ffffff", width=1)

        for idx, (sx, sy) in enumerate(self.snake):
            color = "#00ffcc" if idx == 0 else GREEN
            self.canvas.create_rectangle(sx * cs + 2, sy * cs + 2, (sx + 1) * cs - 2, (sy + 1) * cs - 2,
                                         fill=color, outline="#004d26", width=1)

    # ── 3. JARVIS PONG (AI DÜELLO) ──────────────────────────────────────────
    def start_pong(self):
        self.active_mode = "pong"
        self.clear_container()

        bar = tk.Frame(self.container, bg=BG)
        bar.pack(fill="x", pady=(0, 6))
        self.pong_score_var = tk.StringVar(value="SİZ: 0  |  JARVIS: 0")
        tk.Label(bar, textvariable=self.pong_score_var, font=("Consolas", 11, "bold"), fg=GOLD, bg=BG).pack(side="left")
        tk.Label(bar, text="W / S veya YUKARI / AŞAĞI Ok tuşları ile kontrol et", font=("Consolas", 9), fg="#7a9ba6", bg=BG).pack(side="right")

        self.canvas = tk.Canvas(self.container, width=580, height=440, bg="#02080d",
                                highlightthickness=1, highlightbackground=GOLD)
        self.canvas.pack(pady=4)

        self.p_player_y = 180
        self.p_ai_y = 180
        self.p_ball_x = 290
        self.p_ball_y = 220
        self.p_ball_dx = 5.0
        self.p_ball_dy = 3.5
        self.p_score_player = 0
        self.p_score_ai = 0
        self.p_game_over = False
        self._pong_tick()

    def _pong_tick(self):
        if self.p_game_over or self.active_mode != "pong":
            return

        self.p_ball_x += self.p_ball_dx
        self.p_ball_y += self.p_ball_dy

        if self.p_ball_y <= 8 or self.p_ball_y >= 432:
            self.p_ball_dy = -self.p_ball_dy

        target = self.p_ball_y - 35
        if self.p_ai_y < target:
            self.p_ai_y += min(4.2, target - self.p_ai_y)
        elif self.p_ai_y > target:
            self.p_ai_y -= min(4.2, self.p_ai_y - target)
        self.p_ai_y = max(10, min(370, self.p_ai_y))

        if 20 <= self.p_ball_x <= 36 and self.p_player_y <= self.p_ball_y <= self.p_player_y + 70:
            self.p_ball_dx = abs(self.p_ball_dx) * 1.05
            offset = (self.p_ball_y - (self.p_player_y + 35)) / 35.0
            self.p_ball_dy = offset * 5.0

        if 544 <= self.p_ball_x <= 560 and self.p_ai_y <= self.p_ball_y <= self.p_ai_y + 70:
            self.p_ball_dx = -abs(self.p_ball_dx) * 1.05
            offset = (self.p_ball_y - (self.p_ai_y + 35)) / 35.0
            self.p_ball_dy = offset * 5.0

        if self.p_ball_x < 0:
            self.p_score_ai += 1
            self._reset_pong_ball()
        elif self.p_ball_x > 580:
            self.p_score_player += 1
            self._reset_pong_ball()

        self.pong_score_var.set(f"SİZ: {self.p_score_player}  |  JARVIS: {self.p_score_ai}")

        if self.p_score_player >= 5:
            self.p_game_over = True
            self.save_score("pong", self.scores.get("pong", 0) + 1)
            self._draw_game_over("TEBRİKLER PATRON! JARVIS'İ YENDİNİZ!")
            return
        elif self.p_score_ai >= 5:
            self.p_game_over = True
            self._draw_game_over("JARVIS KAZANDI: 'Daha çok çalışmalıyız Patron!'")
            return

        self._draw_pong()
        self.job = self.root.after(20, self._pong_tick)

    def _reset_pong_ball(self):
        self.p_ball_x = 290
        self.p_ball_y = 220
        self.p_ball_dx = -5.0 if self.p_ball_dx > 0 else 5.0
        self.p_ball_dy = random.choice([-3.0, 3.0])

    def _draw_pong(self):
        self.canvas.delete("all")
        for y in range(0, 440, 20):
            self.canvas.create_line(290, y, 290, y + 10, fill="#12384a", width=2)
        self.canvas.create_rectangle(20, self.p_player_y, 30, self.p_player_y + 70, fill=GREEN, outline="")
        self.canvas.create_rectangle(550, self.p_ai_y, 560, self.p_ai_y + 70, fill=PINK, outline="")
        self.canvas.create_oval(self.p_ball_x - 6, self.p_ball_y - 6, self.p_ball_x + 6, self.p_ball_y + 6, fill=GOLD, outline="")

    # ── 4. REFLEKS TESTİ ─────────────────────────────────────────────────────
    def start_reaction(self):
        self.active_mode = "reaction"
        self.clear_container()

        tk.Label(self.container, text="🎯 NÖRONAL TEPKİ & HIZ TESTİ", font=("Consolas", 14, "bold"), fg=GOLD, bg=BG).pack(pady=10)
        self.r_lbl_status = tk.Label(self.container, text="KUTUYA TIKLA VE BAŞLA", font=("Consolas", 12), fg=TEXT, bg=BG)
        self.r_lbl_status.pack(pady=6)

        self.r_box = tk.Canvas(self.container, width=540, height=360, bg="#1a1a24", highlightthickness=2, highlightbackground=GOLD, cursor="hand2")
        self.r_box.pack(pady=14)
        self.r_box.bind("<Button-1>", self._on_reaction_click)

        self.r_state = "idle"
        self.r_start_time = 0
        self._set_reaction_state("idle")

    def _set_reaction_state(self, state):
        self.r_state = state
        self.r_box.delete("all")
        if state == "idle":
            self.r_box.configure(bg="#0c1622")
            self.r_box.create_text(270, 180, text="BAŞLAMAK İÇİN TIKLAYIN\n(KIRMIZI OLUNCA BEKLEYİN, YEŞİL OLUNCA TIKLAYIN)",
                                  fill=CYAN, font=("Consolas", 12, "bold"), justify="center")
        elif state == "waiting":
            self.r_box.configure(bg="#4a0e17")
            self.r_box.create_text(270, 180, text="BEKLEYİN...\nYEŞİL OLUNCA HEMEN TIKLAYIN!",
                                  fill="#ff99aa", font=("Consolas", 14, "bold"), justify="center")
        elif state == "ready":
            self.r_box.configure(bg="#004d26")
            self.r_box.create_text(270, 180, text="ŞİMDİ TIKLA!", fill="#00ff88", font=("Consolas", 24, "bold"))
            self.r_start_time = time.time()
        elif state == "too_early":
            self.r_box.configure(bg="#33000a")
            self.r_box.create_text(270, 180, text="ÇOK ERKEN!\nYeşil olmadan tıkladınız. Tekrar deneyin.", fill=PINK, font=("Consolas", 13, "bold"), justify="center")

    def _on_reaction_click(self, _event):
        if self.r_state == "idle":
            self._set_reaction_state("waiting")
            delay = random.randint(1800, 4200)
            self.job = self.root.after(delay, lambda: self._set_reaction_state("ready"))
        elif self.r_state == "waiting":
            if self.job:
                self.root.after_cancel(self.job)
            self._set_reaction_state("too_early")
            self.root.after(1600, lambda: self._set_reaction_state("idle"))
        elif self.r_state == "ready":
            elapsed_ms = int((time.time() - self.r_start_time) * 1000)
            self.r_box.delete("all")
            self.r_box.configure(bg="#041824")

            best = self.scores.get("reaction", 9999)
            if elapsed_ms < best or best == "--":
                self.scores["reaction"] = elapsed_ms
                self.save_score("reaction", elapsed_ms)

            evaluation = "Mükemmel F1 Pilotu Refleksi!" if elapsed_ms < 220 else "Çok Hızlı ve Keskin!" if elapsed_ms < 280 else "Ortalama İnsan Hızı."
            res_txt = f"SKORUNUZ: {elapsed_ms} ms\n\nJarvis Değerlendirmesi: {evaluation}\n\nTekrar denemek için tıklayın."
            self.r_box.create_text(270, 180, text=res_txt, fill=GOLD, font=("Consolas", 13, "bold"), justify="center")
            self.r_state = "idle"

    # ── 5. JARVIS TRIVIA BİLGİ YARIŞMASI ─────────────────────────────────────
    def start_trivia(self):
        self.active_mode = "trivia"
        self.clear_container()

        self.trivia_questions = [
            {"q": "Dünyanın ilk programcısı olarak kabul edilen tarihi figür kimdir?",
             "opts": ["Alan Turing", "Ada Lovelace", "Grace Hopper", "Nikola Tesla"], "ans": 1},
            {"q": "Python programlama dili adını nereden almıştır?",
             "opts": ["Piton yılanından", "Monty Python komedi grubundan", "Yunan mitolojisinden", "Kurucusunun köpeğinden"], "ans": 1},
            {"q": "Yapay zeka alanında 'Turing Testi' ilk kez hangi yılda önerilmiştir?",
             "opts": ["1936", "1950", "1968", "1984"], "ans": 1},
            {"q": "Kuantum bilgisayarlarındaki en küçük bilgi birimine ne ad verilir?",
             "opts": ["Bit", "Qubit", "Byte", "Quantum"], "ans": 1},
            {"q": "J.A.R.V.I.S kısaltmasının açılımı nedir?",
             "opts": ["Just A Rather Very Intelligent System", "Joint Automated Robotics Virtual Intelligence System", "Java Advanced Realtime Voice Interface System", "Junior Artificial Robotics Vector Integrated System"], "ans": 0},
            {"q": "İnternetin temeli sayılan ilk bilgisayar ağı hangisidir?",
             "opts": ["ARPANET", "ETHERNET", "USENET", "INTRANET"], "ans": 0},
        ]
        random.shuffle(self.trivia_questions)
        self.q_idx = 0
        self.t_score = 0

        self._show_next_trivia()

    def _show_next_trivia(self):
        self.clear_container()
        if self.q_idx >= len(self.trivia_questions):
            tk.Label(self.container, text="🏆 YARIŞMA TAMAMLANDI!", font=("Consolas", 16, "bold"), fg=GOLD, bg=BG).pack(pady=20)
            tk.Label(self.container, text=f"Toplam Skorunuz: {self.t_score} / {len(self.trivia_questions)}", font=("Consolas", 14), fg=CYAN, bg=BG).pack(pady=10)
            tk.Button(self.container, text="YENİDEN BAŞLA", command=self.start_trivia, bg=PANEL, fg=GREEN, font=("Consolas", 11, "bold"), padx=14, pady=6).pack(pady=20)
            return

        item = self.trivia_questions[self.q_idx]
        tk.Label(self.container, text=f"SORU {self.q_idx + 1} / {len(self.trivia_questions)}  |  Skor: {self.t_score}",
                 font=("Consolas", 11, "bold"), fg=GOLD, bg=BG).pack(anchor="w", pady=(10, 8))

        q_box = tk.Label(self.container, text=item["q"], font=("Consolas", 12, "bold"), fg=TEXT, bg=PANEL,
                         wraplength=600, justify="left", padx=16, pady=16)
        q_box.pack(fill="x", pady=(0, 14))

        for idx, opt in enumerate(item["opts"]):
            btn = tk.Button(
                self.container, text=f"[{chr(65 + idx)}]  {opt}",
                command=lambda i=idx: self._answer_trivia(i),
                bg="#061824", fg=CYAN, activebackground=DIM, activeforeground=CYAN,
                font=("Consolas", 11), relief="flat", anchor="w", padx=14, pady=8, cursor="hand2"
            )
            btn.pack(fill="x", pady=4)

    def _answer_trivia(self, chosen):
        item = self.trivia_questions[self.q_idx]
        correct = (chosen == item["ans"])
        if correct:
            self.t_score += 1

        self.q_idx += 1
        self._show_next_trivia()

    # ── GENEL OYUN BİTTİ EKRANI ──────────────────────────────────────────────
    def _draw_game_over(self, msg):
        self.canvas.create_rectangle(20, 180, self.canvas.winfo_reqwidth() - 20, 300, fill="#040c14", outline=PINK, width=2)
        self.canvas.create_text(self.canvas.winfo_reqwidth() // 2, 220, text=msg, fill=PINK, font=("Consolas", 12, "bold"))
        self.canvas.create_text(self.canvas.winfo_reqwidth() // 2, 260, text="R: Yeniden Başla  |  ESC: Menüye Dön", fill=TEXT, font=("Consolas", 10))

    def handle_key(self, event):
        k = event.keysym.lower()
        if k == "escape":
            self.show_menu()
            return

        if self.active_mode == "tetris":
            if self.t_game_over and k == "r":
                self.start_tetris()
            elif not self.t_game_over:
                if k in ("left", "a"):
                    nxt = [(x - 1, y) for x, y in self.t_piece["blocks"]]
                    if self._tetris_valid(nxt): self.t_piece["blocks"] = nxt; self._draw_tetris()
                elif k in ("right", "d"):
                    nxt = [(x + 1, y) for x, y in self.t_piece["blocks"]]
                    if self._tetris_valid(nxt): self.t_piece["blocks"] = nxt; self._draw_tetris()
                elif k in ("down", "s"):
                    nxt = [(x, y + 1) for x, y in self.t_piece["blocks"]]
                    if self._tetris_valid(nxt): self.t_piece["blocks"] = nxt; self._draw_tetris()
                elif k == "up":
                    b = self.t_piece["blocks"]
                    cx, cy = b[1][0], b[1][1]
                    rotated = [(cx - (y - cy), cy + (x - cx)) for x, y in b]
                    if self._tetris_valid(rotated): self.t_piece["blocks"] = rotated; self._draw_tetris()
                elif k == "space":
                    while self._tetris_valid([(x, y + 1) for x, y in self.t_piece["blocks"]]):
                        self.t_piece["blocks"] = [(x, y + 1) for x, y in self.t_piece["blocks"]]
                        self.t_points += 2
                    self._draw_tetris()

        elif self.active_mode == "snake":
            if self.s_game_over and k == "r":
                self.start_snake()
            else:
                moves = {"up": (0, -1), "w": (0, -1), "down": (0, 1), "s": (0, 1),
                         "left": (-1, 0), "a": (-1, 0), "right": (1, 0), "d": (1, 0)}
                if k in moves:
                    dx, dy = moves[k]
                    if (dx, dy) != (-self.s_dir[0], -self.s_dir[1]):
                        self.s_pending = (dx, dy)

        elif self.active_mode == "pong":
            if self.p_game_over and k == "r":
                self.start_pong()
            else:
                if k in ("w", "up"):
                    self.p_player_y = max(10, self.p_player_y - 25)
                elif k in ("s", "down"):
                    self.p_player_y = min(360, self.p_player_y + 25)


if __name__ == "__main__":
    JarvisArcade()
