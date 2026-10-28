import cv2
import os
import time
import subprocess
from pathlib import Path

def verify_user(timeout=10):
    """
    LBPH Yüz Tanıma kullanarak kullanıcıyı doğrular.
    Kamera kilitlenmelerini ve arka plan thread donmalarını önler.
    """
    base_dir = Path(__file__).resolve().parent.parent
    trainer_path = base_dir / "assets" / "face" / "trainer.yml"
    
    if not trainer_path.exists():
        print("[JARVIS] ⚠️ Yüz modeli bulunamadı! Önce face_setup.py çalıştırılmalı.")
        return False

    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read(str(trainer_path))
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
    except Exception as exc:
        print(f"[JARVIS] ⚠️ Yüz tanıma modülü yüklenemedi: {exc}")
        return False

    backend = getattr(cv2, "CAP_DSHOW", 0) if os.name == "nt" else 0
    cap = cv2.VideoCapture(0, backend) if backend else cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[JARVIS] ⚠️ Kamera açılamadı veya başka bir servis (Webcam Streamer) tarafından kullanılıyor!")
        return False

    start_time = time.time()
    is_authenticated = False

    print("[JARVIS] 👁️ Biyometrik tarama başlatıldı...")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                face_roi = gray[y:y+h, x:x+w]
                face_roi = cv2.resize(face_roi, (200, 200))
                
                label, confidence = recognizer.predict(face_roi)
                
                if label == 1 and confidence < 65:
                    is_authenticated = True
                    print(f"[JARVIS] ✅ Patron yüzü doğrulandı! (Güven: %{int(100 - confidence)})")
                    break

            if is_authenticated:
                break
                
            time.sleep(0.04)
    finally:
        cap.release()
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
    
    return is_authenticated


def manage_secure_vault(base_dir_path, action="open"):
    """
    Kasayı Windows üzerinde tamamen görünmez/erişilemez yapar veya sadece Jarvis için açar.
    """
    locked_name = "kasa.{645FF040-5081-101B-9F08-00AA002F954E}"
    unlocked_name = "kasa_acik"
    
    locked_path = os.path.join(base_dir_path, locked_name)
    unlocked_path = os.path.join(base_dir_path, unlocked_name)
    
    if not os.path.exists(locked_path) and not os.path.exists(unlocked_path):
        os.makedirs(unlocked_path, exist_ok=True)
        os.rename(unlocked_path, locked_path)
        subprocess.run(["attrib", "+h", "+s", locked_path], check=False)
    
    if action == "open":
        subprocess.run(["attrib", "-h", "-s", locked_path], check=False)
        if os.path.exists(locked_path):
            os.rename(locked_path, unlocked_path)
            
        subprocess.run(["explorer", unlocked_path], check=False)
        return "Kasa erişimi sağlandı Patron."
        
    elif action == "close":
        if os.path.exists(unlocked_path):
            os.rename(unlocked_path, locked_path)
        subprocess.run(["attrib", "+h", "+s", locked_path], check=False)
        return "Kasa başarıyla kilitlendi ve gizlendi Patron."

    return "Geçersiz kasa eylemi (open veya close seçiniz)."
