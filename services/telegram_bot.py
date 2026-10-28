#!/usr/bin/env python3
import threading
import requests
import time
import json
import os

# TOKEN alanın ve dinamik URL çözümlemesi
def _get_bot_token() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if token:
        return token
    try:
        from app_config import get_app_config_value

        token = str(get_app_config_value("telegram_bot_token", "") or "").strip()
        if token:
            return token
    except Exception:
        pass
    try:
        from core.settings_store import load_settings

        return str(load_settings().get("integrations", {}).get("telegram_bot_token", "") or "").strip()
    except Exception:
        return ""

def send_to_jarvis(command, chat_id):
    """JARVIS web sunucusuna yerel API üzerinden komutu ve Telegram Chat ID'sini iletir."""
    try:
        payload = {
            "command": command,
            "chat_id": chat_id
        }
        response = requests.post("http://127.0.0.1:8000/api/remote", json=payload, timeout=5)
        print(f"[TELEGRAM BOT] Çekirdeğe istek atıldı. HTTP Kodu: {response.status_code}")
    except Exception as e:
        print(f"[TELEGRAM BOT] JARVIS sunucusuna bağlanılamadı: {e}")

def run_bot():
    bot_token = _get_bot_token()
    if not bot_token:
        print("[TELEGRAM BOT] Token yok; Telegram bot baslatilmadi.")
        return
    api_url = f"https://api.telegram.org/bot{bot_token}/"
    print("[TELEGRAM BOT] Bot aktif, Telegram'dan komutlar bekleniyor...")
    last_update_id = 0
    while True:
        try:
            params = {"offset": last_update_id + 1, "timeout": 30}
            response = requests.get(api_url + "getUpdates", params=params, timeout=35)
            
            if response.status_code != 200:
                print(f"[TELEGRAM BOT] Telegram API Bağlantı Hatası: {response.status_code}")
                time.sleep(5)
                continue
                
            data = response.json()

            if data.get("result"):
                for update in data["result"]:
                    last_update_id = update["update_id"]
                    message_obj = update.get("message", {})
                    msg = message_obj.get("text", "")
                    chat_id = message_obj.get("chat", {}).get("id")
                    
                    if msg:
                        print(f"[TELEGRAM BOT] Telegram'dan gelen ham mesaj: {msg}")
                    
                    # Sadece "Jarvis" ile başlayan mesajları filtrele ve çekirdeğe yolla
                    if msg and msg.lower().startswith("jarvis"):
                        cmd = msg[6:].strip()
                        if cmd and chat_id:
                            print(f"[TELEGRAM BOT] Komut ayrıştırıldı: {cmd} (Chat ID: {chat_id})")
                            send_to_jarvis(cmd, chat_id)
        except Exception as e:
            print(f"[TELEGRAM BOT] Döngü anlık kesintiye uğradı: {e}")
            time.sleep(5)
        time.sleep(1)

def start_telegram_bot():
    """Ana scriptten çağrıldığında botu arka planda (daemon) tetikler."""
    if not _get_bot_token():
        print("[TELEGRAM BOT] TELEGRAM_BOT_TOKEN/config token yok; servis atlandi.")
        return
    threading.Thread(target=run_bot, daemon=True).start()
