# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S V4 — Proaktif Arka Plan Zeka Motoru (Proactive Daemon)
Sistemi, kaynakları, çalışma süresini ve zamanı gözetleyen,
gerektiğinde kullanıcıya proaktif tavsiyelerde bulunan öngörülü asistan motoru.
"""

import time
import threading
import psutil
from datetime import datetime


class ProactiveEngine:
    """
    Arka planda sessizce sistemi analiz eden proaktif gözetmen.
    CPU dostudur (dakikada birkaç kez uyanır).
    """

    def __init__(self, ui=None, speak_func=None):
        self.ui = ui
        self.speak_func = speak_func
        self.enabled = True

        self._started_at = time.time()
        self._last_break_alert = time.time()
        self._last_battery_alert = 0.0
        self._last_ram_alert = 0.0
        self._last_night_alert = 0.0

        self._thread = None
        self._stop_event = threading.Event()

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="JarvisProactiveDaemon")
        self._thread.start()
        print("[JARVIS] 👁️ Proaktif Zeka Motoru devrede.")

    def stop(self):
        self._stop_event.set()

    def _notify(self, message: str, sound: bool = True):
        """Bildirimi hem UI loguna yazar hem de gerekirse seslendirir."""
        if self.ui and hasattr(self.ui, "write_log"):
            self.ui.write_log(f"JARVIS [PROAKTİF]: {message}")

        if sound and self.speak_func:
            try:
                self.speak_func(message)
            except Exception:
                pass

    def _loop(self):
        # Başlangıçta 20 saniye ısınma beklemesi
        time.sleep(20)

        while not self._stop_event.is_set():
            if not self.enabled:
                time.sleep(10)
                continue

            try:
                now = time.time()
                current_time = datetime.now()

                # 1. Odak & Mola Gözetmeni (45 Dakikada Bir)
                if now - self._last_break_alert > 45 * 60:
                    self._last_break_alert = now
                    self._notify("Patron, 45 dakikadır aralıksız çalışıyorsunuz. Gözlerinizi dinlendirmek için kısa bir mola vermek ister misiniz?")

                # 2. Batarya & Pil Seviyesi Gözetmeni
                try:
                    battery = psutil.sensors_battery()
                    if battery and not battery.power_plugged:
                        percent = battery.percent
                        if percent <= 15 and (now - self._last_battery_alert > 20 * 60):
                            self._last_battery_alert = now
                            self._notify(f"Dikkat Patron: Batarya seviyesi %{percent}'e düştü. Cihazı şarja takmanızı öneririm.")
                except Exception:
                    pass

                # 3. Yüksek RAM Tüketim Alarmı
                try:
                    ram = psutil.virtual_memory().percent
                    if ram >= 90 and (now - self._last_ram_alert > 25 * 60):
                        self._last_ram_alert = now
                        self._notify(f"Sistem uyarısı: RAM kullanımı %{ram:.1f}'e ulaştı. Arka plandaki gereksiz süreçleri sonlandırabilir veya RAM Booster'ı çalıştırabilirim.")
                except Exception:
                    pass

                # 4. Gece Mesaisi Gözetmeni (Saat 00:30 - 05:00)
                hour = current_time.hour
                if (hour >= 1 or (hour == 0 and current_time.minute >= 30)) and hour < 5:
                    if now - self._last_night_alert > 4 * 60 * 60:
                        self._last_night_alert = now
                        self._notify("Saat oldukça geç oldu Patron. Sağlığınız için sistemi uyku moduna almamı ister misiniz?")

            except Exception as e:
                print(f"[ProactiveEngine] Gözlem hatası: {e}")

            # Her 30 saniyede bir kontrol döngüsü
            self._stop_event.wait(30)


_global_proactive_engine = None

def get_proactive_engine(ui=None, speak_func=None):
    global _global_proactive_engine
    if _global_proactive_engine is None:
        _global_proactive_engine = ProactiveEngine(ui=ui, speak_func=speak_func)
    return _global_proactive_engine
