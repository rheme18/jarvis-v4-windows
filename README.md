<h1 align="center">J.A.R.V.I.S V4</h1>

<p align="center">Windows için sesli, kişiselleştirilebilir masaüstü asistanı</p>

<p align="center">
  <a href="LICENSE"><img alt="MIT Lisansı" src="https://img.shields.io/badge/Lisans-MIT-2ea44f?style=flat-square"></a>
  <img alt="Windows 10 ve 11" src="https://img.shields.io/badge/Windows-10%20%7C%2011-0078D6?style=flat-square&logo=windows11&logoColor=white">
  <img alt="Python 3.10 ve üzeri" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="Aktif geliştirme" src="https://img.shields.io/badge/Durum-Aktif%20Geli%C5%9Ftirme-ff9f1c?style=flat-square">
</p>

<p align="center">
  Gemini Live&nbsp; · &nbsp;Windows araçları&nbsp; · &nbsp;Yüzen Ada HUD&nbsp; · &nbsp;Üretkenlik&nbsp; · &nbsp;Mini oyunlar
</p>

> J.A.R.V.I.S V4; Gemini Live ile sesli görüşmeyi, Windows araçlarını, günlük üretkenlik özelliklerini ve özelleştirilebilir bir HUD arayüzünü bir araya getiren bağımsız bir topluluk projesidir. Marvel, Anthropic, Google veya Technopat ile bağlantılı değildir.

**[Özellik rehberi](JARVIS_OZELLIKLERI.md)** · **[Skill ve plugin envanteri](JARVIS_SKILL_PLUGIN_ENVANTERI.md)** · **[Lisans](LICENSE)**

## ✨ Neler yapabilir?

### 🎙️ Sesli asistan

- Gemini Live ile gerçek zamanlı sesli görüşme ve yazılı komutlar.
- Mikrofon, kamera ve konuşma ayarları için hızlı kontroller.
- F8 ile ana panel ve sürüklenebilir Yüzen Ada arasında geçiş.

### 🪟 Windows ve masaüstü

- Uygulama başlatma, pencere ve sistem bilgilerini yönetme.
- Dosya araçları, pano yardımcısı, hızlı notlar ve yerel yedekleme.
- Kamera akışı, fotoğraf çekme, ekran analizi ve isteğe bağlı el hareketi kontrolü.

### ☁️ Entegrasyonlar

- Gmail’de e-posta arama ve etiketleri listeleme; Google Drive’da dosya arama.
- Google Calendar etkinliklerini okuma ve Google Tasks hatırlatıcıları.
- Yapılandırıldığında GitHub, Vercel, Telegram, YouTube ve Spotify araçları.
- `CLAUDE_API_KEY` ayarlandığında Claude API ile kod yazma ve inceleme yardımı.

Harici servisler API anahtarı, OAuth izni veya ek yapılandırma gerektirebilir. Gmail bağlantısının mevcut kapsamı e-postaları okumaya yöneliktir; e-posta göndermez veya silmez.

### 🧠 Günlük işler

- Kişi kartları, notlar, hatırlatıcılar ve yerel bellek.
- Odak sayacı, günlük brifing, yapılacaklar ve çalışma zamanlayıcısı.
- App Hub profilleri, canlı sistem panosu ve özelleştirilebilir HUD renk/efekt ayarları.

### 🕹️ Eğlence ve yardımcı araçlar

- Tetris, Snake, Cyber-Pong, refleks testi ve JARVIS trivia.
- DNS, IP, domain, SSL, dosya hash’i ve parola gücü gibi kontroller.

Ağ kontrollerini yalnızca kendi cihazlarında veya izinli sistemlerde kullan. Hassas dosya ve sistem işlemleri onay isteyebilir.

## 💻 Gereksinimler

- Windows 10 veya Windows 11
- Python 3.10 veya üzeri
- Sesli Gemini Live kullanımı için Gemini API anahtarı
- Sesli kullanım için mikrofon ve hoparlör

Bazı Windows kontrolleri ve isteğe bağlı özellikler `requirements.txt` içindeki paketlere bağlıdır.

## 🚀 Kurulum

1. Python’ı yüklerken **Add Python to PATH** seçeneğini etkinleştir.
2. Depoyu indir veya klonla.
3. `setup.bat` dosyasını çalıştır; sanal ortamı oluşturup gerekli paketleri kurar.
4. `config/api_keys.example.json` dosyasını `config/api_keys.json` adıyla kopyalayıp Gemini API anahtarını ekle. Alternatif olarak `config/.env.example` dosyasını örnek alıp `config/.env` oluştur.
5. `jarvis.bat` dosyasını çalıştır.

## 📨 Gmail kurulumu

1. Google Cloud Console’da proje oluştur veya seç ve Gmail API’yi etkinleştir.
2. OAuth izin ekranını yapılandırıp **Desktop app** türünde istemci oluştur.
3. İndirilen OAuth JSON dosyasını `config/google_credentials.json` adıyla proje klasörüne koy.
4. J.A.R.V.I.S’i başlat. İlk Gmail isteğinde tarayıcıdan Google hesabını seçip erişim izni ver.
5. Yetkilendirme token’ı yerel olarak `config/google_token.json` konumuna kaydedilir.

OAuth istemci dosyası ve token kişisel kimlik bilgileridir; GitHub’a yükleme. Ayrıntılar için [özellik rehberindeki Gmail bölümüne](JARVIS_OZELLIKLERI.md#gmail-kurulumu-kullanici-sorarsa-jarvis-ne-soylemeli) bak. Google’ın [kimlik bilgisi oluşturma](https://developers.google.com/workspace/guides/create-credentials) ve [Gmail izin kapsamları](https://developers.google.com/workspace/gmail/api/auth/scopes) belgeleri ek bilgi sağlar.

## ⌨️ Kısayollar

- `F4` / `Ctrl+M` — mikrofonu aç/kapat
- `F5` — duraklat/devam et
- `F6` — kamerayı aç/kapat
- `F8` — Yüzen Ada’ya geç veya ana panele dön
- `F11` / `Ctrl+F` — tam ekranı aç/kapat
- `Ctrl+K` — hızlı komut menüsünü aç
- `Esc` — tam ekrandan çık veya pencere modunda J.A.R.V.I.S’i kapat

Ana pencerenin `X` düğmesi J.A.R.V.I.S’i tamamen kapatır. **ARKA PLAN** düğmesi uygulamayı çalışır durumda bırakıp pencereyi gizler. Yüzen Ada’nın `X` düğmesi ana arayüzü geri getirir.

## 🔐 Gizlilik

API anahtarlarını, OAuth dosyalarını, kişi kayıtlarını, yüz profillerini ve yerel bellek/günlük dosyalarını paylaşma. `.gitignore` bu tür yerel verileri dışlar; commit veya yükleme öncesinde dosya listesini gözden geçir. Kamera, ses, ekran analizi, mesajlaşma ve bulut entegrasyonları hassas veri işleyebilir.

## 🗂️ Proje yapısı

- `main.py`, `ui.py` — uygulama başlangıcı ve Windows HUD
- `core/` — orkestrasyon, ayarlar, onaylar ve plugin altyapısı
- `actions/`, `services/`, `tools/` — Windows araçları ve servis bağlantıları
- `integrations/`, `skills/` — birlikte gelen plugin ve skill kaynakları
- `games/` — mini oyunlar
- `config/`, `memory/`, `database/` — örnek ayarlar ve yerel çalışma verileri

## 📄 Lisans

J.A.R.V.I.S V4’ün proje kodu **MIT Lisansı** ile dağıtılır; ayrıntılar için [LICENSE](LICENSE) dosyasına bak. Birlikte gelen üçüncü taraf skill, plugin, yazı tipi ve varlıkların kendi lisansları ve bildirimleri geçerlidir.

## 🛠️ Durum ve hata bildirimi

Proje geliştirme aşamasındadır. Özelliklerin kullanılabilirliği Windows yapılandırmasına, yüklü paketlere ve harici hesaplara bağlı olabilir. Sorun bildirirken Windows/Python sürümünü ve ilgili hata mesajını paylaş; API anahtarı, token, OAuth dosyası veya kişisel verileri ekleme.
