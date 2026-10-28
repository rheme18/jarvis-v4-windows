# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S V4 — High Resolution Photo Capture Tool
Kullanıcının isteğiyle kameradan anlık fotoğraf çeker, diske kaydeder ve bildirir.
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
import cv2

BASE_DIR = Path(__file__).resolve().parent.parent


def play_shutter_sound():
    """Windows varsayılan kamera deklanşör sesini çalar."""
    try:
        import winsound
        # Windows sistem bildirim sesi veya beeper
        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
    except Exception:
        pass


def capture_user_photo(destination: str = "pictures", open_after: bool = True) -> str:
    """
    Webcam'den anlık net bir fotoğraf çeker ve kaydeder.
    """
    try:
        # Klasör hazırla
        if destination == "database":
            out_dir = BASE_DIR / "database" / "pngs"
        else:
            pictures_path = Path.home() / "Pictures" / "Jarvis_Photos"
            pictures_path.mkdir(parents=True, exist_ok=True)
            out_dir = pictures_path

        out_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Jarvis_Shot_{timestamp}.jpg"
        target_path = out_dir / filename

        # Kamera yakala
        backend = getattr(cv2, "CAP_DSHOW", 0) if os.name == "nt" else 0
        cap = cv2.VideoCapture(0, backend) if backend else cv2.VideoCapture(0)

        if not cap.isOpened():
            return "Hata: Kamera cihazına erişilemedi. Başka bir uygulamanın kamerayı kullanmadığından emin olun."

        # Yüksek çözünürlük ayarla
        try:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        except Exception:
            pass

        # Sensörün ışığı ayarlaması için birkaç kare ısınma
        for _ in range(6):
            cap.read()
            time.sleep(0.04)

        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            return "Hata: Kameradan net görüntü kareleri alınamadı."

        # Ayna düzeltmesi (selfie perspektifi)
        frame = cv2.flip(frame, 1)

        # En yüksek JPEG kalitesiyle kaydet
        cv2.imwrite(str(target_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        play_shutter_sound()

        # Otomatik varsayılan fotoğraf görüntüleyici ile aç
        if open_after:
            try:
                os.startfile(str(target_path))
            except Exception:
                pass

        return f"Fotoğrafınız başarıyla çekildi ve kaydedildi Patron: {target_path.name}\nKonum: {target_path}"

    except Exception as exc:
        return f"Fotoğraf çekme işlemi sırasında bir hata oluştu: {exc}"


if __name__ == "__main__":
    print(capture_user_photo())
