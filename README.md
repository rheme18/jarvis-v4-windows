<h1 align="center">⚡ J.A.R.V.I.S V4</h1>

<p align="center"><strong>Windows için sesli, kişiselleştirilebilir masaüstü asistanı</strong></p>

<p align="center">
  <a href="LICENSE"><img alt="MIT Lisansı" src="https://img.shields.io/badge/Lisans-MIT-2ea44f?style=for-the-badge"></a>
  <img alt="Windows 10 ve 11" src="https://img.shields.io/badge/Windows-10%20%7C%2011-0078D6?style=for-the-badge&logo=windows11&logoColor=white">
  <img alt="Python 3.10 ve üzeri" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img alt="Aktif geliştirme" src="https://img.shields.io/badge/Durum-Aktif%20Geli%C5%9Ftirme-ff9f1c?style=for-the-badge">
</p>

<p align="center">
  <a href="JARVIS_OZELLIKLERI.md">✨ Özellik rehberi</a> ·
  <a href="#kurulum">🚀 Kurulum</a> ·
  <a href="#gmail-kurulumu">📨 Gmail bağlantısı</a> ·
  <a href="JARVIS_SKILL_PLUGIN_ENVANTERI.md">🧩 Skill ve plugin envanteri</a>
</p>

> J.A.R.V.I.S V4; Gemini Live ile sesli görüşmeyi, Windows araçlarını, üretkenlik özelliklerini ve özelleştirilebilir bir HUD arayüzünü bir araya getiren bağımsız bir topluluk projesidir. Marvel, Anthropic, Google veya Technopat ile bağlantılı değildir.

## 🌌 Öne çıkanlar

<table>
  <tr>
    <td width="50%"><strong>🎙️ Sesli asistan</strong><br>Gemini Live ile sesli görüşme ve yazılı komutlar.</td>
    <td width="50%"><strong>🪟 Windows araçları</strong><br>Uygulama, pencere, dosya ve sistem yardımcıları.</td>
  </tr>
  <tr>
    <td><strong>🏝️ Yüzen Ada</strong><br>F8 ile erişilen, sürüklenebilir ve saydam mini HUD.</td>
    <td><strong>☁️ Entegrasyonlar</strong><br>Google, GitHub, Vercel ve medya servisleri için isteğe bağlı bağlantılar.</td>
  </tr>
  <tr>
    <td><strong>🧠 Kişisel üretkenlik</strong><br>Notlar, hatırlatıcılar, kişi kartları, odak sayacı ve günlük brifing.</td>
    <td><strong>🕹️ Mini oyunlar</strong><br>Tetris, Snake, Cyber-Pong, refleks testi ve JARVIS trivia.</td>
  </tr>
</table>

## 🧰 Özellikler

- **Ses ve yapay zekâ:** Gerçek zamanlı Gemini Live görüşmesi, yazılı komutlar, mikrofon/kamera kontrolleri ve konuşma ayarları.
- **Windows kontrolü:** Uygulama başlatma, pencere ve sistem bilgileri, dosya araçları, pano yardımcısı ve sistem sağlık raporu.
- **Görsel araçlar:** Webcam akışı, fotoğraf çekme, aktif pencereyi analiz etme ve isteğe bağlı el hareketi kontrolü.
- **Google servisleri:** Gmail’de arama ve etiket listeleme, Drive’da dosya arama, Calendar etkinliklerini okuma ve Google Tasks hatırlatıcıları.
- **Geliştirici araçları:** Yapılandırıldığında GitHub/Vercel işlemleri ve Claude API ile kod yardımı; yerel proje özeti ve iş akışı araçları.
- **Günlük işler:** Kişi kartları, yerel bellek, notlar, yapılacaklar, çalışma zamanlayıcısı, günlük brifing ve yerel yedekleme.
- **Görünüm:** HUD tema ve renk tercihleri, ses/efekt seçenekleri, App Hub ve canlı sistem panosu.
- **Güvenlik ve ağ:** DNS, IP, domain, SSL, dosya hash’i ve parola gücü gibi yardımcı kontroller.

> Bazı özellikler API anahtarı, OAuth izni, ek paket veya donanım gerektirir. Ağ kontrollerini yalnızca kendi cihazlarında veya izinli sistemlerde kullan. Hassas dosya ve sistem işlemleri onay isteyebilir.

Tüm özelliklerin ayrıntısı ve sınırları için [J.A.R.V.I.S V4 Özellik Rehberi](JARVIS_OZELLIKLERI.md) belgesine bak.

## 💻 Gereksinimler

| Bileşen | Gereksinim |
|---|---|
| İşletim sistemi | Windows 10 veya Windows 11 |
| Python | Python 3.10 veya üzeri |
| Yapay zekâ | Sesli Gemini Live kullanımı için Gemini API anahtarı |
| Ses | Sesli kullanım için mikrofon ve hoparlör |

Bazı Windows kontrolleri ve isteğe bağlı özellikler `requirements.txt` içindeki paketlere bağlıdır.

## 🚀 Kurulum

1. Python’ı yükle ve kurulumda **Add Python to PATH** seçeneğini etkinleştir.
2. Bu depoyu indir veya klonla.
3. `setup.bat` dosyasını çalıştır. Betik sanal ortamı oluşturur ve gerekli paketleri yükler.
4. `config/api_keys.example.json` dosyasını `config/api_keys.json` adıyla kopyala ve Gemini API anahtarını ekle. Alternatif olarak `config/.env.example` dosyasını örnek alıp `config/.env` oluştur.
5. `jarvis.bat` dosyasını çalıştır.

## 📨 Gmail kurulumu

Gmail bağlantısı Google OAuth kullanır. OAuth istemci dosyası ve erişim token’ı kişisel dosyalardır; depoya veya herkese açık paylaşıma eklenmemelidir.

1. Google Cloud Console’da bir proje oluştur veya seç ve Gmail API’yi etkinleştir.
2. OAuth izin ekranını yapılandırıp **Desktop app** türünde OAuth istemcisi oluştur.
3. İndirilen OAuth JSON dosyasını `config/google_credentials.json` adıyla proje içine koy.
4. J.A.R.V.I.S’i başlat. İlk Gmail aramasında tarayıcıda Google hesabını seçip erişime izin ver.
5. J.A.R.V.I.S token’ı yerel olarak `config/google_token.json` dosyasına kaydeder.

Bu Gmail bağlantısı e-postaları arar, son postayı özetler ve etiketleri listeler. Mevcut `gmail.readonly` izniyle e-posta göndermez veya silmez. Ayrıntılı adımlar için [özellik rehberindeki Gmail bölümüne](JARVIS_OZELLIKLERI.md#gmail-kurulumu-kullanici-sorarsa-jarvis-ne-soylemeli) bak. Google’ın [kimlik bilgisi oluşturma](https://developers.google.com/workspace/guides/create-credentials) ve [Gmail izin kapsamları](https://developers.google.com/workspace/gmail/api/auth/scopes) belgeleri ek bilgi sağlar.

## ⌨️ Kısayollar ve pencere davranışı

| Kısayol / kontrol | İşlev |
|---|---|
| `F4` / `Ctrl+M` | Mikrofonu aç/kapat |
| `F5` | Duraklat/devam et |
| `F6` | Kamerayı aç/kapat |
| `F8` | Yüzen Ada’ya geç veya ana panele dön |
| `F11` / `Ctrl+F` | Tam ekranı aç/kapat |
| `Ctrl+K` | Hızlı komut menüsü |
| `Esc` | Tam ekrandan çık veya pencere modunda J.A.R.V.I.S’i kapat |
| Ana pencere `X` | J.A.R.V.I.S’i tamamen kapat |
| **ARKA PLAN** düğmesi | J.A.R.V.I.S’i çalışır durumda bırakıp pencereyi gizle |
| Yüzen Ada `X` | Ada’yı kapatıp ana arayüzü geri getir |

## 🔐 Gizlilik

API anahtarlarını, OAuth dosyalarını, kişi kayıtlarını, yüz profillerini ve yerel bellek/log dosyalarını paylaşma. `.gitignore` bu tür yerel verileri dışlar; commit veya yükleme öncesinde dosya listesini gözden geçir. Kamera, ses, ekran analizi, mesajlaşma ve bulut entegrasyonları hassas veri işleyebilir.

## 📁 Proje yapısı

| Klasör / dosya | İçerik |
|---|---|
| `main.py`, `ui.py` | Uygulama başlangıcı ve Windows HUD |
| `core/` | Asistan orkestrasyonu, ayarlar, onaylar ve eklenti altyapısı |
| `actions/`, `services/`, `tools/` | Windows araçları ve servis entegrasyonları |
| `integrations/`, `skills/` | Birlikte gelen plugin ve skill kaynakları |
| `games/` | Mini oyunlar |
| `config/`, `memory/`, `database/` | Örnek ayarlar ve çalışma sırasında oluşturulan yerel veriler |

## 📣 Durum ve katkı

Proje geliştirme aşamasındadır; özelliklerin çalışması Windows yapılandırmasına, paketlere ve harici hesaplara bağlı olabilir. Hata bildirirken Windows/Python sürümünü ve ilgili hata mesajını paylaş; API anahtarı, token, OAuth dosyası veya kişisel verileri ekleme. Skill ve plugin kaynaklarının kendi bildirimlerini koru.

## 📄 Lisans

J.A.R.V.I.S V4’ün proje kodu **MIT Lisansı** ile dağıtılır. Lisans koşulları için [LICENSE](LICENSE) dosyasına bak. Birlikte gelen üçüncü taraf skill, plugin, yazı tipi ve varlıkların kendi lisansları ve bildirimleri geçerlidir.
