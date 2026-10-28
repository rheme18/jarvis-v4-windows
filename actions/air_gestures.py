# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S V4 — Sci-Fi Air Gestures & Holographic Hand Skeleton Engine
Kamera üzerinden el eklemlerini fütüristik neon iskelet efektiyle tarar;
Temassız el hareketleriyle (Avuç ➔ İşaret Parmağı vb.) medya ve ses kontrollerini yönetir.
MediaPipe ve OpenCV Cyber Vision çift motorlu mimari: Sıfır hata garantisi.
"""

import sys
import os
import time
import threading
import ctypes
import math
from pathlib import Path
import cv2

# Windows Multimedia Key Codes
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_MEDIA_NEXT_TRACK = 0xB0
VK_VOLUME_UP = 0xAF
VK_VOLUME_DOWN = 0xAE


def send_windows_key(vk_code: int):
    """Windows donanım medya tuşunu simüle eder."""
    try:
        user32 = ctypes.windll.user32
        user32.keybd_event(vk_code, 0, 0, 0)
        time.sleep(0.04)
        user32.keybd_event(vk_code, 0, 2, 0)  # KEYEVENTF_KEYUP
    except Exception:
        pass


def _resolve_mediapipe():
    """MediaPipe Hands modülünü dinamik olarak yükler."""
    mp_hands = None
    mp_draw = None

    # sys.path kontrolü (site-packages ekleme)
    try:
        import site
        for sp in site.getsitepackages():
            if sp not in sys.path:
                sys.path.insert(0, sp)
    except Exception:
        pass

    # Deneme 1: mediapipe.python.solutions.hands
    try:
        import mediapipe.python.solutions.hands as mh
        import mediapipe.python.solutions.drawing_utils as md
        if hasattr(mh, "Hands"):
            return mh, md
    except Exception:
        pass

    # Deneme 2: mediapipe.solutions.hands
    try:
        from mediapipe import solutions as sol
        if hasattr(sol, "hands"):
            return sol.hands, getattr(sol, "drawing_utils", None)
    except Exception:
        pass

    # Deneme 3: mediapipe as mp -> mp.solutions.hands
    try:
        import mediapipe as mp
        if hasattr(mp, "solutions") and hasattr(mp.solutions, "hands"):
            return mp.solutions.hands, getattr(mp.solutions, "drawing_utils", None)
    except Exception:
        pass

    return None, None


class AirGestureController:
    def __init__(self, ui=None):
        self.ui = ui
        self._active = False
        self._thread = None
        self._stop_event = threading.Event()
        self.show_preview = True

        # Jest durum takibi
        self._last_gesture = "NONE"
        self._cooldown_until = 0.0
        self._last_wrist_y = None
        self._engine_type = "UNKNOWN"

        # MediaPipe Hands
        self.mp_hands = None
        self.mp_draw = None
        self._try_load_mediapipe()

    def _try_load_mediapipe(self):
        mh, md = _resolve_mediapipe()
        if mh:
            self.mp_hands = mh
            self.mp_draw = md
            self._engine_type = "NEURAL_MEDIAPIPE"
            return True
        return False

    def is_active(self) -> bool:
        return self._active

    def is_running(self) -> bool:
        return self._active

    def start(self, preview: bool = True) -> str:
        self.show_preview = preview
        if self._active:
            return "El Hareketi Kontrolü (Air Gestures) zaten devrede Patron."

        # MediaPipe kontrol et, yoksa tekrar dene
        if not self.mp_hands:
            self._try_load_mediapipe()

        if self.mp_hands:
            self._engine_type = "NEURAL_MEDIAPIPE"
            info = "Holografik Neural MediaPipe İskelet Motoru aktif."
        else:
            self._engine_type = "CYBER_OPENCV"
            info = "Yüksek Hızlı Siber Kontur Görme Motoru (OpenCV) devrede."

        self._active = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._gesture_loop, daemon=True, name="AirGestureThread")
        self._thread.start()

        msg = f"🖐️ AIR GESTURES BAŞLATILDI! ({info})"
        if self.ui and hasattr(self.ui, "write_log"):
            self.ui.write_log(f"SYS: {msg}")
        return f"Air Gestures devrede Patron. {info}"

    def stop(self) -> str:
        self._active = False
        self._stop_event.set()
        if self.ui and hasattr(self.ui, "write_log"):
            self.ui.write_log("SYS: Air Gestures durduruldu.")
        return "Air Gestures kapatıldı Patron."

    # ── MediaPipe Sınıflandırma ──────────────────────────────────────────────
    def _classify_mp_hand(self, landmarks) -> str:
        index_up = landmarks[8].y < landmarks[6].y
        middle_up = landmarks[12].y < landmarks[10].y
        ring_up = landmarks[16].y < landmarks[14].y
        pinky_up = landmarks[20].y < landmarks[18].y
        up_count = sum([index_up, middle_up, ring_up, pinky_up])

        if index_up and middle_up and ring_up and pinky_up:
            return "OPEN_PALM"
        if index_up and not middle_up and not ring_up and not pinky_up:
            return "INDEX_POINT"
        if index_up and middle_up and not ring_up and not pinky_up:
            return "PEACE"
        if up_count == 0:
            return "FIST"
        return "UNKNOWN"

    def _draw_cyber_skeleton(self, frame, hand_landmarks):
        h, w, _ = frame.shape
        points = []
        for lm in hand_landmarks.landmark:
            cx, cy = int(lm.x * w), int(lm.y * h)
            points.append((cx, cy))

        connections = getattr(self.mp_hands, "HAND_CONNECTIONS", None)
        if connections:
            for connection in connections:
                s, e = connection[0], connection[1]
                cv2.line(frame, points[s], points[e], (0, 255, 136), 2, cv2.LINE_AA)
                cv2.line(frame, points[s], points[e], (125, 255, 246), 1, cv2.LINE_AA)

        for pt in points:
            cv2.circle(frame, pt, 4, (0, 240, 255), -1, cv2.LINE_AA)
            cv2.circle(frame, pt, 7, (0, 180, 210), 1, cv2.LINE_AA)

    # ── OpenCV Gelişmiş Kontur & Konveksite Sınıflandırma (Fallback) ──────────
    def _process_opencv_hand(self, frame):
        """MediaPipe olmadan da çalışan ultra hızlı siber ten rengi & kontur takip motoru."""
        h, w, _ = frame.shape
        # ROI: Kameranın sağ 2/3'lük orta bölgesi
        roi_x1, roi_y1, roi_x2, roi_y2 = int(w * 0.15), int(h * 0.15), int(w * 0.85), int(h * 0.85)
        roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        # Adaptif ten rengi maskesi
        lower_skin = (0, 30, 60)
        upper_skin = (25, 180, 255)
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        mask = cv2.GaussianBlur(mask, (5, 5), 0)

        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return "NONE", None

        max_c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(max_c)
        if area < 4000:
            return "NONE", None

        # Kontur çizimi (Neon Siber Çerçeve)
        offset_c = max_c + [roi_x1, roi_y1]
        cv2.drawContours(frame, [offset_c], -1, (0, 255, 180), 2)

        # Konveks gövde ve defektler (Parmak analizi)
        hull = cv2.convexHull(max_c, returnPoints=False)
        defects_count = 0
        if hull is not None and len(hull) > 3:
            try:
                defects = cv2.convexityDefects(max_c, hull)
                if defects is not None:
                    for i in range(defects.shape[0]):
                        s, e, f, d = defects[i, 0]
                        start = tuple(max_c[s][0])
                        end = tuple(max_c[e][0])
                        far = tuple(max_c[f][0])
                        a = math.dist(start, end)
                        b = math.dist(start, far)
                        c = math.dist(end, far)
                        angle = math.acos(max(-1.0, min(1.0, (b**2 + c**2 - a**2) / (2 * b * c + 1e-5))))
                        if angle <= math.pi / 2.1 and d > 9000:
                            defects_count += 1
                            cv2.circle(frame, (far[0] + roi_x1, far[1] + roi_y1), 5, (0, 255, 255), -1)
            except Exception:
                pass

        # Ağırlık merkezi (Wrist Y)
        M = cv2.moments(max_c)
        cy = (M["m01"] / (M["m00"] + 1e-5) + roi_y1) / float(h)

        if defects_count >= 3:
            return "OPEN_PALM", cy
        elif defects_count == 2:
            return "PEACE", cy
        elif defects_count == 1:
            return "INDEX_POINT", cy
        else:
            return "FIST", cy

    # ── Ana Jest Döngüsü ─────────────────────────────────────────────────────
    def _gesture_loop(self):
        backend = getattr(cv2, "CAP_DSHOW", 0) if os.name == "nt" else 0
        cap = cv2.VideoCapture(0, backend) if backend else cv2.VideoCapture(0)

        if not cap.isOpened():
            self._active = False
            if self.ui and hasattr(self.ui, "write_log"):
                self.ui.write_log("ERR: Air Gestures kamera bağlantısı kuramadı.")
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        use_mp = bool(self.mp_hands)
        hands = None
        if use_mp:
            try:
                hands = self.mp_hands.Hands(
                    static_image_mode=False,
                    max_num_hands=1,
                    min_detection_confidence=0.65,
                    min_tracking_confidence=0.65
                )
            except Exception:
                use_mp = False
                hands = None

        try:
            while not self._stop_event.is_set():
                ret, frame = cap.read()
                if not ret or frame is None:
                    time.sleep(0.04)
                    continue

                frame = cv2.flip(frame, 1)  # Ayna modu
                h, w, _ = frame.shape
                now = time.time()
                current_gesture = "NONE"
                detected_wrist_y = None

                # 1. MediaPipe Denemesi
                if use_mp and hands:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = hands.process(rgb)
                    if results.multi_hand_landmarks:
                        hl = results.multi_hand_landmarks[0]
                        self._draw_cyber_skeleton(frame, hl)
                        current_gesture = self._classify_mp_hand(hl.landmark)
                        detected_wrist_y = hl.landmark[0].y
                else:
                    # 2. OpenCV Siber Vizyon Denemesi
                    current_gesture, detected_wrist_y = self._process_opencv_hand(frame)

                # HUD Bilgi Katmanı
                cv2.rectangle(frame, (10, 10), (380, 75), (5, 20, 20), -1)
                cv2.rectangle(frame, (10, 10), (380, 75), (0, 212, 192), 1)
                engine_tag = "NEURAL MEDIAPIPE" if use_mp else "CYBER OPENCV 60FPS"
                cv2.putText(frame, f"JARVIS AIR GESTURES [{engine_tag}]", (20, 32),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 240, 255), 1, cv2.LINE_AA)

                status_col = (0, 255, 136) if current_gesture != "NONE" else (100, 160, 160)
                cv2.putText(frame, f"JEST: {current_gesture}", (20, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_col, 2, cv2.LINE_AA)

                # Komut Yürütme Mantığı
                if now > self._cooldown_until and current_gesture not in ("NONE", "UNKNOWN"):
                    # 1. Açık Avuç ➔ Tek İşaret Parmağı: Oynat / Duraklat
                    if self._last_gesture == "OPEN_PALM" and current_gesture == "INDEX_POINT":
                        send_windows_key(VK_MEDIA_PLAY_PAUSE)
                        self._cooldown_until = now + 1.5
                        if self.ui and hasattr(self.ui, "write_log"):
                            self.ui.write_log("AIR GESTURE: ⏯️ Medya Oynat / Duraklat tetiklendi.")

                    # 2. Barış / V-Sign: Sonraki Şarkı
                    elif current_gesture == "PEACE":
                        send_windows_key(VK_MEDIA_NEXT_TRACK)
                        self._cooldown_until = now + 1.8
                        if self.ui and hasattr(self.ui, "write_log"):
                            self.ui.write_log("AIR GESTURE: ⏭️ Sonraki parçaya geçildi.")

                    # 3. Yumruk yukarı/aşağı: Ses kontrolü
                    if current_gesture == "FIST" and detected_wrist_y is not None:
                        if self._last_wrist_y is not None:
                            diff = self._last_wrist_y - detected_wrist_y
                            if diff > 0.045:  # Yukarı el hareketi
                                send_windows_key(VK_VOLUME_UP)
                                self._cooldown_until = now + 0.25
                            elif diff < -0.045:  # Aşağı el hareketi
                                send_windows_key(VK_VOLUME_DOWN)
                                self._cooldown_until = now + 0.25
                        self._last_wrist_y = detected_wrist_y
                    else:
                        self._last_wrist_y = None

                    self._last_gesture = current_gesture
                elif current_gesture == "NONE":
                    self._last_wrist_y = None

                # Önizleme penceresi
                if self.show_preview:
                    cv2.imshow("JARVIS V4 · Holographic Gesture HUD", frame)
                    if cv2.waitKey(1) & 0xFF == 27:  # ESC tuşu
                        break

                time.sleep(0.025)

        finally:
            cap.release()
            cv2.destroyAllWindows()
            self._active = False


_air_controller = None

def get_air_gesture_controller(ui=None):
    global _air_controller
    if _air_controller is None:
        _air_controller = AirGestureController(ui=ui)
    elif ui and _air_controller.ui is None:
        _air_controller.ui = ui
    return _air_controller
