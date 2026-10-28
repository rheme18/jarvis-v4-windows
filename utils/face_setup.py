# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S V4 — Biyometrik Yüz Haritalama & Kayıt Protokolü
Kullanıcının yüzünü canlı kamerada HUD ile takip eder,
yüksek çözünürlüklü ve detaylı 50 adet fotoğrafı yavaş aralıklarla (0.35s) kaydeder,
LBPH modeli eğiterek Paranoid Sentinel sistemine entegre eder.
"""

import os
import sys
import time
import json
from pathlib import Path
import cv2
import urllib.request
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
FACE_DIR = BASE_DIR / "assets" / "face"
DATASET_DIR = FACE_DIR / "dataset"
TRAINER_PATH = FACE_DIR / "trainer.yml"
PROFILE_PATH = FACE_DIR / "profile.json"


def draw_hud_box(frame, x, y, w, h, col=(0, 255, 200), bl=20):
    """Siber köşe braketleri ile yüz kutusunu çizer."""
    cv2.rectangle(frame, (x, y), (x + w, y + h), (col[0]//3, col[1]//3, col[2]//3), 1)
    # 4 köşe braketi
    # Sol Üst
    cv2.line(frame, (x, y), (x + bl, y), col, 2)
    cv2.line(frame, (x, y), (x, y + bl), col, 2)
    # Sağ Üst
    cv2.line(frame, (x + w, y), (x + w - bl, y), col, 2)
    cv2.line(frame, (x + w, y), (x + w, y + bl), col, 2)
    # Sol Alt
    cv2.line(frame, (x, y + h), (x + bl, y + h), col, 2)
    cv2.line(frame, (x, y + h), (x, y + h - bl), col, 2)
    # Sağ Alt
    cv2.line(frame, (x + w, y + h), (x + w - bl, y + h), col, 2)
    cv2.line(frame, (x + w, y + h), (x + w, y + h - bl), col, 2)


def setup_face(on_progress=None, on_finish=None) -> bool:
    print("\n[JARVIS] 🤖 Biyometrik Yüz Kayıt Protokolü Başlatılıyor...")
    DATASET_DIR.mkdir(parents=True, exist_ok=True)

    cascade_path = ""
    for cand in [
        str(BASE_DIR / "assets" / "haarcascades" / "haarcascade_frontalface_default.xml"),
        os.path.join(getattr(cv2.data, "haarcascades", ""), "haarcascade_frontalface_default.xml"),
        str(Path(cv2.__file__).resolve().parent / "data" / "haarcascade_frontalface_default.xml"),
    ]:
        if cand and os.path.isfile(cand):
            cascade_path = cand
            break
    if not cascade_path:
        b_path = BASE_DIR / "assets" / "haarcascades" / "haarcascade_frontalface_default.xml"
        b_path.parent.mkdir(parents=True, exist_ok=True)
        import urllib.request, ssl
        try:
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen("https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml", context=ctx, timeout=10) as r, open(str(b_path), "wb") as f:
                f.write(r.read())
            cascade_path = str(b_path)
            print("[JARVIS] 📥 Haar cascade indirildi ve kaydedildi.")
        except Exception as e:
            print(f"❌ HATA: Haar cascade indirilemedi: {e}")

    face_cascade = cv2.CascadeClassifier(cascade_path)
    if face_cascade.empty():
        print("❌ HATA: Yüz sınıflandırıcı XML bulunamadı.")
        return False

    backend = getattr(cv2, "CAP_DSHOW", 0) if os.name == "nt" else 0
    cap = cv2.VideoCapture(0, backend) if backend else cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ HATA: Kamera açılamadı Patron!")
        return False

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    TARGET_COUNT = 50
    INTERVAL = 0.35  # saniye (fotoğraflar aceleye gelmez, detaylı açılar yakalanır)
    
    count = 0
    face_samples = []
    face_labels = []
    last_capture_time = 0.0
    flash_until = 0.0

    window_name = "JARVIS - Biyometrik Yuz Tarama Protokolu"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

    try:
        while count < TARGET_COUNT:
            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.05)
                continue

            frame = cv2.flip(frame, 1)  # Ayna modu
            h, w = frame.shape[:2]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Üst ve Alt HUD Çubukları
            cv2.rectangle(frame, (0, 0), (w, 44), (10, 15, 15), -1)
            cv2.line(frame, (0, 44), (w, 44), (0, 240, 200), 1)

            cv2.putText(frame, "J.A.R.V.I.S  BIOMETRIC PROTOCOL - PATRON TARAMA",
                        (16, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 255, 200), 2)

            cv2.rectangle(frame, (0, h - 50), (w, h), (10, 15, 15), -1)
            cv2.line(frame, (0, h - 50), (w, h - 50), (0, 240, 200), 1)

            # Yüz tespiti
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.2,
                minNeighbors=5,
                minSize=(110, 110)
            )

            now = time.time()
            face_detected = False

            if len(faces) > 0:
                # En büyük yüzü al (en yakındaki kullanıcı)
                faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
                (x, y, fw, fh) = faces[0]
                face_detected = True

                # Köşe HUD kutusu
                box_col = (0, 255, 255) if (now < flash_until) else (0, 255, 200)
                draw_hud_box(frame, x, y, fw, fh, col=box_col)

                # Yavaş ve detaylı çekim aralığı
                if (now - last_capture_time) >= INTERVAL:
                    last_capture_time = now
                    flash_until = now + 0.15
                    count += 1

                    # Yüz bölgesini kırp ve histogram eşitle (ışık farklarını düzeltir)
                    roi = gray[y:y+fh, x:x+fw]
                    roi_norm = cv2.equalizeHist(roi)
                    roi_resized = cv2.resize(roi_norm, (200, 200))

                    face_samples.append(roi_resized)
                    face_labels.append(1)  # ID 1 = Patron

                    # Diske görsel kanıt olarak kaydet
                    sample_file = DATASET_DIR / f"patron_{count:03d}.jpg"
                    cv2.imwrite(str(sample_file), roi_resized)

                    if on_progress:
                        try:
                            on_progress(count, TARGET_COUNT)
                        except Exception:
                            pass

                cv2.putText(frame, f"HEDEF: PATRON #{count}/{TARGET_COUNT}",
                            (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.55, box_col, 2)
            else:
                cv2.putText(frame, "Kameraya dogru bakin ve kafanizi hafifce oynatin...",
                            (16, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 180, 255), 1)

            # İlerleme Çubuğu Çizimi
            progress_ratio = count / TARGET_COUNT
            bar_w = int((w - 32) * progress_ratio)
            cv2.rectangle(frame, (16, h - 35), (w - 16, h - 22), (40, 40, 40), -1)
            if bar_w > 0:
                cv2.rectangle(frame, (16, h - 35), (16 + bar_w, h - 22), (0, 255, 200), -1)
            cv2.putText(frame, f"%{int(progress_ratio * 100)} ({count}/{TARGET_COUNT})",
                        (w - 140, h - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            cv2.imshow(window_name, frame)
            key = cv2.waitKey(20) & 0xFF
            if key == 27 or key == ord('q'):  # ESC veya Q ile iptal
                print("⚠️ İşlem kullanıcı tarafından iptal edildi.")
                cap.release()
                cv2.destroyAllWindows()
                return False

    finally:
        cap.release()

    # Model Eğitimi
    if count >= TARGET_COUNT and len(face_samples) > 0:
        # Başarı ekranı
        success_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(success_frame, "FOTOGRAFLAR ALINDI!", (120, 200),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 200), 2)
        cv2.putText(success_frame, "LBPH Yapay Zeka Modeli Egitiliyor...", (120, 250),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
        cv2.imshow(window_name, success_frame)
        cv2.waitKey(600)

        print("[JARVIS] 🧠 LBPH Biyometrik Model eğitiliyor...")
        recognizer = cv2.face.LBPHFaceRecognizer_create(radius=2, neighbors=8, grid_x=8, grid_y=8)
        recognizer.train(face_samples, np.array(face_labels))

        FACE_DIR.mkdir(parents=True, exist_ok=True)
        recognizer.write(str(TRAINER_PATH))

        # Profil meta bilgisini kaydet
        profile_data = {
            "owner": "Emir Aras Koç (Patron)",
            "user_id": 1,
            "samples_count": count,
            "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "active"
        }
        PROFILE_PATH.write_text(json.dumps(profile_data, indent=2, ensure_ascii=False), encoding="utf-8")

        # Tamamlandı ekranı
        cv2.putText(success_frame, "BASARILI: Biyometrik Model Kilitlendi!", (80, 310),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 100), 2)
        cv2.imshow(window_name, success_frame)
        cv2.waitKey(1500)
        cv2.destroyAllWindows()

        print(f"🔒 [JARVIS] Biyometrik yapay zeka modeli kaydedildi: {TRAINER_PATH}")
        print("✓ Paranoid Sentinel artık yüzünüzü tanıyacak ve alarm çalmayacaktır!")
        if on_finish:
            try:
                on_finish(True)
            except Exception:
                pass
        return True
    else:
        cv2.destroyAllWindows()
        if on_finish:
            try:
                on_finish(False)
            except Exception:
                pass
        return False


if __name__ == "__main__":
    setup_face()
