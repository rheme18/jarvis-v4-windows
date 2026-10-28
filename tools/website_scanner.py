# tools/website_scanner.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

def scan_website_secret_urls(url: str) -> str:
    if "https://" not in url and "http://" not in url:
        url = "https://" + url
        
    domain = re.sub(r'^https?://', '', url).split('/')[0]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    # Orijinal Uzantı Kontrol Regexi
    def IsValidExtension(target_url):
        return re.search(r'\.(html|xhtml|php|js|css)$', target_url) or not re.search(r'\.\w+$', target_url)

    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return f"❌ Hedef siteye erişilemedi. HTTP Durum Kodu: {response.status_code}"
            
        soup = BeautifulSoup(response.text, 'html.parser')
        tags = soup.find_all(['a', 'link', 'script', 'form'])
        
        extracted_links = []
        for tag in tags:
            attr = tag.get('href') or tag.get('src') or tag.get('action')
            if attr:
                full_url = urljoin(url, attr)
                if IsValidExtension(full_url) and full_url not in extracted_links:
                    extracted_links.append(full_url)
                    
        if not extracted_links:
            return f"🔍 {domain} kaynak kodlarında hiçbir açık bağlantı saptanamadı patron."
            
        report = [
            f"🕸️ [WEB SİTESİ URL TARAMA RAPORU] — {domain}",
            f"🔹 Toplam Çıkarılan Bağlantı: {len(extracted_links)}",
            "\n📌 Saptanan Bağlantılar (İlk 15):"
        ]
        for i, link in enumerate(extracted_links[:15]):
            report.append(f"  [{i+1}] {link}")
            
        return "\n".join(report)
    except Exception as e:
        return f"❌ Web tarama katmanında siber kilitlenme: {str(e)}"