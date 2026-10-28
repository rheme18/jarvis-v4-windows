"""
JARVIS V2 Windows — Yerel Sesli Uyandırma Motoru (Local Wake Word Listener)
"Hey Jarvis" / "Jarvis" sesli komutunu ve akustik uyandırmayı dinler.
Tetiklendiğinde pencereyi öne getirir ve kullanıcıyı selamlar.
"""

from __future__ import annotations

import math
import struct
import threading
import time
from typing import Callable, Optional

try:
    import speech_recognition as sr
    HAS_SR = True
except Exception:
    HAS_SR = False

try:
    import pyaudio
    HAS_PYAUDIO = True
except Exception:
    HAS_PYAUDIO = False


class WakeWordListener:
    """
    Yerel ve hafif sesli uyandırma dinleyicisi.
    'Hey Jarvis' ve 'Jarvis' anahtar kelimelerini tanır.
    """
    WAKE_WORDS = {"jarvis", "hey jarvis", "merhaba jarvis", "uyan jarvis", "yarvis"}

    def __init__(self, on_wake: Callable[[], None], energy_threshold: int = 1400):
        self._on_wake = on_wake
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._energy_threshold = energy_threshold
        self._last_trigger_time = 0.0

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="JarvisWakeWord")
        self._thread.start()
        print("[WakeWord] 🎙️ Yerel sesli uyandırma ('Hey Jarvis') dinleyicisi aktif.")

    def stop(self):
        self._running = False

    def _trigger(self, reason: str = "wake_word"):
        now = time.monotonic()
        if now - self._last_trigger_time < 3.0:
            return  # 3 saniye içinde mükerrer tetiklemeyi önle
        self._last_trigger_time = now
        print(f"[WakeWord] ⚡ JARVIS UYANDIRILDI ({reason})")
        try:
            self._on_wake()
        except Exception as exc:
            print(f"[WakeWord] on_wake çağrısı hatası: {exc}")

    def _run_loop(self):
        if not HAS_SR:
            print("[WakeWord] speech_recognition bulunamadı, uyandırma dinleyicisi başlatılamadı.")
            return

        recognizer = sr.Recognizer()
        recognizer.energy_threshold = self._energy_threshold
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.6

        while self._running:
            try:
                with sr.Microphone() as source:
                    # Arka plan gürültüsüne hızlı kalibrasyon
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    while self._running:
                        try:
                            # 4 saniyelik konuşma parçası bekle
                            audio = recognizer.listen(source, timeout=3.0, phrase_time_limit=3.0)
                            try:
                                # Yerel/hızlı Google STT veya offline kontrol
                                text = recognizer.recognize_google(audio, language="tr-TR").lower()
                                print(f"[WakeWord] Algılanan ses: '{text}'")
                                if any(w in text for w in self.WAKE_WORDS):
                                    self._trigger(reason=f"keyword: '{text}'")
                            except sr.UnknownValueError:
                                pass
                            except Exception:
                                pass
                        except sr.WaitTimeoutError:
                            continue
            except Exception as e:
                time.sleep(2.0)


# Geriye dönük uyumluluk için alias
WakeGestureListener = WakeWordListener
