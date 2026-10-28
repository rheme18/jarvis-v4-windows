# tools/username_tracker.py
import requests
from bs4 import BeautifulSoup
import time

def track_username_osint(username: str) -> str:
    username = username.lower().strip()
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    headers = {"User-Agent": user_agent}
    
    # Orijinal RedTiger Username Tracker listesindeki tüm siber ve sosyal platformlar (Eksiksiz)
    sites = {
        "Instagram": {"url": f"https://www.instagram.com/{username}", "verification": "instagram.com"},
        "TikTok": {"url": f"https://www.tiktok.com/@{username}", "verification": "tiktok.com"},
        "Twitter/X": {"url": f"https://x.com/{username}", "verification": "twitter.com"},
        "GitHub": {"url": f"https://github.com/{username}", "verification": "github.com"},
        "Steam": {"url": f"https://steamcommunity.com/id/{username}", "verification": "steamcommunity.com"},
        "Telegram": {"url": f"https://t.me/{username}", "verification": "t.me"},
        "YouTube": {"url": f"https://www.youtube.com/@{username}", "verification": "youtube.com"},
        "Twitch": {"url": f"https://www.twitch.tv/{username}", "verification": "twitch.tv"},
        "Pinterest": {"url": f"https://www.pinterest.com/{username}", "verification": "pinterest.com"},
        "Reddit": {"url": f"https://www.reddit.com/user/{username}", "verification": "reddit.com"},
        "Spotify": {"url": f"https://open.spotify.com/user/{username}", "verification": "spotify.com"},
        "Roblox": {"url": f"https://www.roblox.com/user.aspx?username={username}", "verification": "roblox.com"},
        "SoundCloud": {"url": f"https://soundcloud.com/{username}", "verification": "soundcloud.com"},
        "DeviantArt": {"url": f"https://www.deviantart.com/{username}", "verification": "deviantart.com"}
    }

    report = f"╔════════ OSINT USERNAME REPORT: [{username.upper()}] ════════\n"
    number_found = 0

    for site, info in sites.items():
        try:
            # İstek atılıyor (Orijinal RedTiger mantığıyla)
            r = requests.get(info["url"], headers=headers, timeout=4)
            if r.status_code == 200:
                # Telegram gibi yönlendirme sayfaları için özel içerik kontrolü
                if site == "Telegram" and "if you have Telegram" not in r.text:
                    report += f" 🔴 {site}: Bulunamadı\n"
                    continue
                
                report += f" 🟢 {site}: {info['url']}\n"
                number_found += 1
            else:
                report += f" 🔴 {site}: Bulunamadı\n"
        except Exception as e:
            report += f" ❌ {site}: İstek Hatası ({str(e)})\n"
        time.sleep(0.1)  # Rate limit yememek için hafif gecikme

    report += f"═══════════════════════════════════════════\n"
    report += f"📊 Toplam Taranan: {len(sites)} | Bulunan Profil: {number_found}"
    return report