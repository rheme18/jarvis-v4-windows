# J.A.R.V.I.S V4 — Windows Asistanı

J.A.R.V.I.S V4; Python ile geliştirilmiş, Windows üzerinde çalışan sesli ve yazılı bir masaüstü asistanıdır. Gemini Live sesli görüşmesini, Windows araçlarını, isteğe bağlı çevrim içi entegrasyonları ve özelleştirilebilir bir HUD arayüzünü modüler bir yapıda bir araya getirir.

> Bu, bağımsız bir topluluk projesidir. Marvel, Anthropic, Google veya Technopat ile bağlantılı değildir.

Özellikleri, entegrasyon gereksinimlerini ve Gmail kurulum adımlarını görmek için [J.A.R.V.I.S V4 Özellik Rehberi](JARVIS_OZELLIKLERI.md) belgesine bakın.

## Özellikler

- Gerçek zamanlı sesli görüşme ve yazılı komutlar
- Windows uygulamalarını başlatma, pencereleri yönetme ve sistem bilgilerini görüntüleme
- İsteğe bağlı kamera ve ekran analiz araçları
- Yapılandırıldığında Google Takvim, Görevler, Gmail ve Drive entegrasyonları
- Yapılandırıldığında GitHub, Vercel, Telegram ve web paneli entegrasyonları
- Kişi kartları, hatırlatıcılar, notlar, yerel bellek ve vektör araması
- Kodlama, planlama, toplantı, medya, tasarım, içerik üretimi ve DevOps için App Hub profilleri
- Odak sayacı, günlük özet, pano yardımcısı ve yerel yedekleme araçları
- Snake ve Tetris oyunları
- F8 ile açılıp kapatılabilen, sürüklenebilir Yüzen Ada HUD’u
- Özelleştirilebilir HUD temaları, vurgu renkleri, hareket/efekt tercihleri ve ses ayarları
- Hassas işlemler için onay kontrolleri içeren araç orkestrasyonu

Bazı entegrasyonlar API anahtarı, OAuth dosyası, ek paket veya kullanıcı yapılandırması gerektirir. Kimlik bilgileri eksik olduğunda uygulama açılmalı; ilgili özellik yapılandırma gerektiğini bildirmelidir.

## Gereksinimler

- Windows 10 veya 11
- Python 3.10 veya üzeri
- Canlı yapay zekâ görüşmesi için Gemini API anahtarı
- Sesli kullanım için mikrofon ve hoparlör

Bazı Windows kontrolleri ve isteğe bağlı özellikler, `requirements.txt` dosyasındaki ek paketlere bağlıdır.

## Kurulum ve çalıştırma

1. Python’ı yükleyin. Kurulum sırasında **Add Python to PATH** seçeneğini etkinleştirin.
2. Depoyu klonlayın veya indirin.
3. `setup.bat` dosyasını çalıştırın. Kurulum betiği sanal ortamı oluşturur ve paketleri yükler.
4. `config/api_keys.example.json` dosyasını `config/api_keys.json` adıyla kopyalayıp Gemini API anahtarınızı ekleyin. Alternatif olarak `config/.env.example` dosyasını örnek alıp desteklenen değerleri `config/.env` dosyasında tanımlayın.
5. `jarvis.bat` dosyasını çalıştırın.

## Klavye kısayolları

- `F4` / `Ctrl+M` — mikrofonu kapatıp açma
- `F5` — duraklatma veya devam ettirme
- `F6` — kamerayı açıp kapatma
- `F11` / `Ctrl+F` — tam ekranı açıp kapatma
- `Ctrl+K` — hızlı komut menüsünü açma
- `F8` — Yüzen Ada’yı açma veya ana panele dönme
- `Esc` — tam ekrandan çıkma veya pencere modunda J.A.R.V.I.S’i kapatma

Ana arayüzün `ARKA PLAN` düğmesi J.A.R.V.I.S’i çalışır durumda bırakıp pencereyi gizler; F8 Yüzen Ada’yı açar veya ana panele döner. Ana pencerenin `X` düğmesi J.A.R.V.I.S’i tamamen kapatır. Yüzen Ada’nın `X` düğmesi Ada’yı kapatıp ana arayüzü geri getirir.

API anahtarlarını, OAuth kimlik bilgilerini, kişi kayıtlarını, yüz profillerini ve çalışma belleği dosyalarını Git commit’lerine eklemeyin. `.gitignore` bu yerel dosyaları dışlar; paylaşmadan önce `git status` çıktısını kontrol edin.

## Gizlilik ve izinler

Ses, kamera, ekran analizi, mesajlaşma ve bulut entegrasyonları hassas verileri işleyebilir. Yalnızca kullanmayı planladığınız özellikleri etkinleştirin, kimlik bilgilerini yerel olarak yapılandırın ve entegrasyonların izinlerini gözden geçirin. Bazı sistem ve dosya işlemleri çalışmadan önce onay isteyebilir.

## Proje yapısı

- `main.py`, `ui.py` — uygulama başlangıcı ve Windows HUD arayüzü
- `core/` — bağlam, orkestrasyon, ayarlar, onaylar ve eklenti altyapısı
- `actions/`, `services/`, `tools/` — asistan araçları ve entegrasyonlar
- `integrations/`, `skills/` — projeyle birlikte gelen eklenti ve beceri kaynakları
- `games/` — mini oyunlar
- `config/`, `memory/`, `database/` — yapılandırma örnekleri ve uygulamanın yerel çalışma verileri

## Durum ve hata bildirimi

J.A.R.V.I.S V4 geliştirme aşamasındadır. Kurulum ve özelliklerin kullanılabilirliği Windows yapılandırmasına, yüklü paketlere ve harici kimlik bilgilerine göre değişebilir. Sorun bildirirken Windows ve Python sürümünüzü ve ilgili günlük kaydını ekleyin. Hata bildirimlerine API anahtarı, token, OAuth dosyası veya kişisel kişi verisi koymayın.

## Lisans

J.A.R.V.I.S V4’ün proje kodu MIT Lisansı ile dağıtılır; ayrıntılar için [LICENSE](LICENSE) dosyasına bakın. Birlikte gelen üçüncü taraf beceriler, eklentiler, yazı tipleri ve varlıklar kendi lisanslarına ve bildirimlerine tabidir; bu bildirimler korunmalıdır.
