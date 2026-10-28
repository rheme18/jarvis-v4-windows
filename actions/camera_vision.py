#!/usr/bin/env python3
import cv2
import os
import time
from PIL import Image

def capture_and_analyze_shot(client, model) -> str:
    # client ve model, main.py'dan gelen genai nesneleridir
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return "Hata: Kamera donanımına erişilemedi."
        
    for _ in range(5): cap.read(); time.sleep(0.1)
    ret, frame = cap.read()
    cap.release()
    
    if not ret: return "Hata: Görüntü okunamadı."
        
    photo_path = os.path.join(os.getcwd(), "camera_shot.jpg")
    cv2.imwrite(photo_path, frame)
    
    try:
        img = Image.open(photo_path)
        prompt = "Bu kameradan gelen görüntü. Analiz et."
        response = client.models.generate_content(model=model, contents=[img, prompt])
        analysis = response.text.strip()
        
        # Telegram kısmını burada da tetikleyebilirsin
        return f"Analiz sonucu: {analysis}"
    except Exception as err:
        return f"Hata: {err}"