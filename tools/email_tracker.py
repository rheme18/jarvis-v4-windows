# tools/email_tracker.py
import requests

def track_email_accounts(email: str) -> str:
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    headers = {'User-Agent': user_agent}
    
    # Orijinal scriptteki tüm siteler ve birebir mantıkları
    site_founds = []
    
    # 1. Instagram
    try:
        r = requests.Session().get("https://www.instagram.com/accounts/emailsignup/", headers=headers, timeout=3)
        if "email" in r.text or r.status_code == 200: site_founds.append("Instagram")
    except: pass
    
    # 2. Twitter
    try:
        r = requests.post("https://api.twitter.com/i/users/email_available.json", data={"email": email}, headers=headers, timeout=3)
        if '"valid":false' in r.text or r.status_code == 400: site_founds.append("Twitter/X")
    except: pass

    # 3. Pinterest
    try:
        r = requests.get(f"https://www.pinterest.com/resource/UserRegisterResource/get/?source_url=%2F&data=%7B%2F%22options%22%3A%7B%2F%22email%22%3A%2F%22{email}%2F%22%7D%7D", headers=headers, timeout=3)
        if '"status": "success"' in r.text: site_founds.append("Pinterest")
    except: pass

    # 4. Imgur
    try:
        r = requests.post("https://api.imgur.com/account/v1/emails/available", data={"email": email}, headers=headers, timeout=3)
        if '"available":false' in r.text: site_founds.append("Imgur")
    except: pass

    # 5. Patreon
    try:
        r = requests.post("https://www.patreon.com/api/register/check-email", data={"email": email}, headers=headers, timeout=3)
        if '"exists":true' in r.text: site_founds.append("Patreon")
    except: pass

    # 6. Spotify
    try:
        r = requests.get(f"https://spclient.wg.spotify.com/signup/public/v1/account?validate=1&email={email}", headers=headers, timeout=3)
        if '"status":2' in r.text or '"errors"' in r.text: site_founds.append("Spotify")
    except: pass

    # 7. FireFox
    try:
        r = requests.post("https://api.accounts.firefox.com/v1/account/status", json={"email": email}, headers=headers, timeout=3)
        if '"exists":true' in r.text: site_founds.append("FireFox")
    except: pass

    # 8. LastPass
    try:
        r = requests.post("https://lastpass.com/enterprise_check.php", data={"email": email}, headers=headers, timeout=3)
        if "is_enterprise" in r.text: site_founds.append("LastPass")
    except: pass

    # 9. Archive.org
    try:
        r = requests.get(f"https://archive.org/services/account.php?email={email}", headers=headers, timeout=3)
        if "already exists" in r.text: site_founds.append("Archive.org")
    except: pass

    # Yetişkin İçerik Siteleri (Orijinal kodda olduğu için birebir korundu patron)
    for adult_site, url in [("PornHub", "https://www.pornhub.com/signup"), ("Xnxx", "https://www.xnxx.com/register"), ("Xvideos", "https://www.xvideos.com/register")]:
        try:
            r = requests.post(url, data={"email": email}, headers=headers, timeout=3)
            if r.status_code == 400 or "already used" in r.text: site_founds.append(adult_site)
        except: pass

    if site_founds:
        return f"🎯 [SİBER İSTİHBARAT RAPORU] — {email}\n" + "\n".join([f" 🟢 Found: {site}" for site in site_founds])
    return f"🔍 {email} adresi için popüler platformlarda siber iz bulunamadı patron."