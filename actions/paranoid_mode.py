# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S V4 — Paranoid Mode (Gelişmiş Güvenlik & Oda Nöbetçisi)
Biyometrik Yüz Tanıma (LBPH) Entegrasyonu:
- Patronun yüzünü (trainer.yml) tanır, patron başındayken alarm çalmaz.
- Yabancı / davetsiz misafir sezildiğinde:
  Ekranı karartır, davetsiz misafirin fotoğrafını çeker, loglar ve istenirse PC'yi kilitler.
"""

import json
import os
import time
import threading
from datetime import datetime
from pathlib import Path
import cv2

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config" / "paranoid_config.json"
INTRUDER_DIR = BASE_DIR / "database" / "intruders"
TRAINER_PATH = BASE_DIR / "assets" / "face" / "trainer.yml"

DEFAULT_CONFIG = {
    "enabled": False,
    "dim_screen": True,
    "lock_workstation": False,
    "capture_photo": True,
    "motion_threshold": 4500,
    "sensitivity": 0.6,
    "owner_confidence_threshold": 68.0,
    "last_alert": ""
}


def load_paranoid_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            return {**DEFAULT_CONFIG, **data}
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_paranoid_config(cfg: dict):
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


class ParanoidSentinel:
    """Arka planda odayı ve davetsiz misafirleri gözetleyen nöbetçi motoru."""

    def __init__(self, ui=None):
        self.ui = ui
        self.config = load_paranoid_config()
        self._thread = None
        self._stop_event = threading.Event()
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    def get_status(self) -> dict:
        has_face_model = TRAINER_PATH.exists()
        return {
            "is_active": self._active,
            "has_biometric_model": has_face_model,
            "config": self.config
        }

    def configure(self, dim_screen: bool = None, take_photo: bool = None, lock_workstation: bool = None):
        if dim_screen is not None:
            self.config["dim_screen"] = bool(dim_screen)
        if take_photo is not None:
            self.config["capture_photo"] = bool(take_photo)
        if lock_workstation is not None:
            self.config["lock_workstation"] = bool(lock_workstation)
        save_paranoid_config(self.config)

    def start(self) -> str:
        if self._active:
            return "Paranoid Mod zaten devrede Patron."
        self.config["enabled"] = True
        save_paranoid_config(self.config)
        self._active = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._surveillance_loop, daemon=True, name="ParanoidSentinelThread")
        self._thread.start()

        model_note = " (Biyometrik Patron Yüz Tanıma Aktif)" if TRAINER_PATH.exists() else " (⚠️ Biyometrik model yok, tüm hareketler taranıyor)"
        if self.ui and hasattr(self.ui, "write_log"):
            self.ui.write_log(f"SYS: 🛡️ PARANOID SENTINEL DEVREYE GİRDİ.{model_note}")
        return f"Paranoid Mod devrede Patron.{model_note} Oda nöbeti başlatıldı."

    def stop(self) -> str:
        self._active = False
        self.config["enabled"] = False
        save_paranoid_config(self.config)
        self._stop_event.set()
        if self.ui and hasattr(self.ui, "write_log"):
            self.ui.write_log("SYS: Paranoid Mod durduruldu.")
        return "Paranoid Mod devre dışı bırakıldı Patron."

    def _dim_display(self):
        """Ekran parlaklığını 0'a çeker."""
        try:
            import screen_brightness_control as sbc
            sbc.set_brightness(0)
        except Exception:
            pass

    def _lock_pc(self):
        """Windows oturumunu kilitler."""
        try:
            import ctypes
            ctypes.windll.user32.LockWorkStation()
        except Exception:
            pass

    def _trigger_alarm(self, frame, reason="Yabancı Kişi"):
        """Davetsiz misafir tespit edildiğinde savunma aksiyonlarını çalıştırır."""
        INTRUDER_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        photo_path = INTRUDER_DIR / f"Intruder_{stamp}.jpg"

        # 1. Fotoğraf çek ve delil kaydet
        if frame is not None and self.config.get("capture_photo", True):
            try:
                cv2.imwrite(str(photo_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
            except Exception:
                pass

        # 2. Ekranı karart
        if self.config.get("dim_screen", True):
            self._dim_display()

        # 3. İsteğe bağlı ekranı kilitle
        if self.config.get("lock_workstation", False):
            self._lock_pc()

        log_msg = f"⚠️ PARANOID ALARM [{reason}]! Saat: {datetime.now().strftime('%H:%M:%S')} (Fotoğraf: {photo_path.name})"
        self.config["last_alert"] = log_msg
        save_paranoid_config(self.config)

        if self.ui and hasattr(self.ui, "write_log"):
            self.ui.write_log(f"ERR: {log_msg}")

    def _surveillance_loop(self):
        backend = getattr(cv2, "CAP_DSHOW", 0) if os.name == "nt" else 0
        cap = cv2.VideoCapture(0, backend) if backend else cv2.VideoCapture(0)

        if not cap.isOpened():
            self._active = False
            if self.ui and hasattr(self.ui, "write_log"):
                self.ui.write_log("ERR: Paranoid Mod: Kamera açılamadı.")
            return

        # Yüz tespiti için Haar Cascade
        cascade_path = ""
        for cand in [
            str(BASE_DIR / "assets" / "haarcascades" / "haarcascade_frontalface_default.xml"),
            os.path.join(getattr(cv2.data, "haarcascades", ""), "haarcascade_frontalface_default.xml"),
            str(Path(cv2.__file__).resolve().parent / "data" / "haarcascade_frontalface_default.xml"),
        ]:
            if cand and os.path.isfile(cand):
                cascade_path = cand
                break
        face_cascade = cv2.CascadeClassifier(cascade_path)

        # Biyometrik Model Yükleme
        recognizer = None
        if TRAINER_PATH.exists():
            try:
                recognizer = cv2.face.LBPHFaceRecognizer_create()
                recognizer.read(str(TRAINER_PATH))
                if self.ui and hasattr(self.ui, "write_log"):
                    self.ui.write_log("SYS: [Paranoid] Patron biyometrik yüz modeli yüklendi.")
            except Exception as e:
                recognizer = None
                if self.ui and hasattr(self.ui, "write_log"):
                    self.ui.write_log(f"WARN: [Paranoid] Yüz modeli okunamadı: {e}")

        owner_thresh = float(self.config.get("owner_confidence_threshold", 68.0))
        first_frame = None

        try:
            while not self._stop_event.is_set():
                ret, frame = cap.read()
                if not ret or frame is None:
                    time.sleep(0.4)
                    continue

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                blur = cv2.GaussianBlur(gray, (21, 21), 0)

                # 1. Yüz Taraması
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80))

                if len(faces) > 0:
                    owner_detected = False
                    if recognizer is not None:
                        for (x, y, w, h) in faces:
                            face_roi = gray[y:y+h, x:x+w]
                            face_roi_norm = cv2.equalizeHist(face_roi)
                            face_roi_resized = cv2.resize(face_roi_norm, (200, 200))

                            label, confidence = recognizer.predict(face_roi_resized)
                            # LBPH: düşük güven değeri = daha yakın eşleşme
                            if label == 1 and confidence < owner_thresh:
                                owner_detected = True
                                break

                        if owner_detected:
                            # Patron bilgisayar başında — alarm çalma, nöbete sessizce devam et
                            first_frame = None
                            time.sleep(1.5)
                            continue
                        else:
                            # Tanınmayan yüz / Yabancı
                            self._trigger_alarm(frame, reason="Bilinmeyen Yüz")
                            time.sleep(12)
                            first_frame = None
                            continue
                    else:
                        # Model yoksa doğrudan alarm ver
                        self._trigger_alarm(frame, reason="Yüz Algılandı (Model Yok)")
                        time.sleep(12)
                        first_frame = None
                        continue

                # 2. Hareket Tespiti (Motion differencing)
                if first_frame is None:
                    first_frame = blur
                    continue

                delta = cv2.absdiff(first_frame, blur)
                thresh = cv2.threshold(delta, 35, 255, cv2.THRESH_BINARY)[1]
                motion_score = cv2.countNonZero(thresh)

                motion_threshold = int(self.config.get("motion_threshold", 4500))
                if motion_score > motion_threshold:
                    # Yüz henüz kadraja girmemiş olabilir, 0.4s sonra bir kez daha yüz tara
                    time.sleep(0.4)
                    r2, f2 = cap.read()
                    if r2 and f2 is not None:
                        g2 = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)
                        faces2 = face_cascade.detectMultiScale(g2, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80))
                        if len(faces2) > 0 and recognizer is not None:
                            # Patron mu kontrol et
                            patron_mu = False
                            for (x, y, w, h) in faces2:
                                roi = cv2.resize(cv2.equalizeHist(g2[y:y+h, x:x+w]), (200, 200))
                                lbl, conf = recognizer.predict(roi)
                                if lbl == 1 and conf < owner_thresh:
                                    patron_mu = True
                                    break
                            if patron_mu:
                                first_frame = None
                                time.sleep(1.5)
                                continue

                    self._trigger_alarm(frame, reason="Oda Hareketi")
                    time.sleep(12)
                    first_frame = None
                    continue

                time.sleep(0.3)
        finally:
            cap.release()
            self._active = False


_sentinel_singleton = None

def get_paranoid_sentinel(ui=None):
    global _sentinel_singleton
    if _sentinel_singleton is None:
        _sentinel_singleton = ParanoidSentinel(ui=ui)
    return _sentinel_singleton
