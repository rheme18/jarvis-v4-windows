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

J.A.R.V.I.S V4, tek bir sohbet penceresinden fazlası olacak şekilde tasarlandı: sesli asistanı, Windows araçlarını, günlük iş akışlarını ve ayrı HUD panellerini aynı masaüstü uygulamasında toplar. Aşağıdaki özellikler kaynak kodunda bulunan modül ve araçlara dayanır; bazıları hesap, anahtar, izin veya ek paket gerektirir.

### 🎙️ Sesli asistan ve komut akışı

- Gemini Live ile gerçek zamanlı sesli görüşme ve metin kutusundan yazılı komut gönderme.
- Mikrofonu sessize alma, konuşmayı duraklatma/sürdürme, kamera akışını açma/kapatma ve ses tercihlerini düzenleme.
- Hızlı komut paleti ile araçları arama ve başlatma; sık kullanılan uygulama ve çalışma profillerini App Hub’dan açma.
- Önemli tercihleri yerel belleğe kaydetme ve kullanıcının isteğiyle bellek kayıtlarını silme.
- İlk açılışta Gemini API anahtarı yoksa ayar ekranından anahtar girişi.

Gemini API anahtarı sesli yapay zekâ özellikleri içindir; Google Gmail OAuth kimlik dosyasıyla aynı şey değildir.

### 🪟 Windows kontrolü ve masaüstü işleri

- Spotify, Chrome, Terminal ve Dosya Gezgini gibi uygulamaları adlarıyla açma; sık kullanılanları App Hub profillerinde toplama.
- Açık pencereleri listeleme, pencereye odaklanma, pencereyi kapatma, ekranı bölme/snap etme ve tüm pencereleri küçültme.
- Pil, CPU, RAM, disk, saat, tarih ve ağ durumunu görüntüleme; canlı sistem panosunda donanım ve süreç özetini izleme.
- Sistem ve uygulama sesini değiştirme/sessize alma, ekran parlaklığını ayarlama ve Windows bildirimi gösterme.
- Dosya ve klasör arama, inceleme, okuma, yazma, kopyalama, taşıma ve hash alma; indirme temizliği ve yerel yedek planlama.
- Pano yardımcısı, hızlı notlar, Ghost Typer ile odaktaki pencereye metin yazma ve seçili sistem sorunları için self-healing yardımcıları.

Silme, taşıma, üzerine yazma, komut satırı ve güç işlemleri gibi riskli adımlarda onay akışı kullanılabilir. Self-healing veya güvenlik araçları her sistem sorununu otomatik çözme garantisi vermez.

<img width="1320" height="707" alt="image" src="https://github.com/user-attachments/assets/9e00e6ea-f3e9-433e-b456-3a32c4a1bd81" />

### 👁️ Kamera, ekran ve çevresel araçlar

- Aktif pencerenin ekran görüntüsünü analiz ederek ekrandaki içerik veya hata hakkında yardım alma.
- Webcam akışını açma, kameradan fotoğraf çekme ve MediaPipe/OpenCV mevcutsa el hareketi kontrolünü kullanma.
- Yüz doğrulama/Paranoid Mode seçenekleriyle oda güvenliği işlevlerini yapılandırma.
- Web araması veya URL açma, hava durumu sorgusu, YouTube/Spotify içeriği açma ve herkese açık YouTube kanal istatistiklerini görüntüleme.

Kamera, ekran ve biyometrik özellikler donanım/izin gerektirir. Yüz profili ve çekilen fotoğraflar yerel kişisel veri sayılır; paylaşılacak depoya koyulmamalıdır.

### ☁️ Google ve diğer servis bağlantıları

- **Gmail:** son postayı özetleme, arama sorgusuyla ileti bulma ve etiketleri listeleme. OAuth kapsamı `gmail.readonly`; bu bağlantı e-posta göndermez, silmez veya değiştirmez.
- **Google Drive:** dosya adına göre arama.
- **Google Calendar:** etkinlikleri okuma; etkinlik ekleme/silme akışı Google Calendar sayfasını tarayıcıda açar ve kullanıcı orada tamamlar.
- **Google Tasks:** hatırlatıcı ekleme, listeleme ve silme; kimlik doğrulama hazır değilse yerel hatırlatıcı yedeği kullanılabilir.
- **GitHub ve Vercel:** token ayarlandıktan sonra depo/issue/PR/workflow bilgileri ve deployment/proje durumları gibi işlemler.
- **Claude API:** `CLAUDE_API_KEY` ayarlanırsa kod yazma, kod inceleme, refactor ve özellik planlama yardımı.
- **WhatsApp, Telegram, YouTube ve Spotify:** uygun uygulama, token, hesap veya API ayarları olduğunda ilgili mesajlaşma/medya araçları.

Entegrasyonlar varsayılan olarak hesaplara giriş yapmaz. İlk OAuth bağlantısında kullanıcı tarayıcıdaki izin ekranını kendisi onaylar. Gmail kurulumu için [Gmail bölümüne](#gmail-kurulumu) bak.

### 🧠 Üretkenlik, hafıza ve otomasyon

- Kişisel yerel veritabanında kişi kartı, not, günlük ve proje kaydı oluşturma; kayıtları arama ve kişi kartı penceresini açma.
- Hatırlatıcı ve yapılacaklar; odak/Pomodoro sayacı, çalışma zamanlayıcısı ve LGS çalışma desteği.
- Günlük brifingde sistem, hava durumu, takvim ve seçilen diğer özetleri bir araya getirme.
- Ödev mesajlarından görev çıkarmaya, çalışma planı oluşturmaya ve rutin adımları otomatikleştirmeye yönelik yardımcılar.
- İş akışı oluşturucu ile araç adımlarını bir zincirde düzenleme, kaydetme ve çalıştırma.
- Yerel proje özeti/anlık görüntüsü ve kullanıcı profili bağlamı gibi araçlarla tekrarlanan işleri kolaylaştırma.

Yerel bellek, kişi kayıtları, hatırlatıcılar, puanlar ve tercihler ilk çalıştırmada veya kullanım sırasında proje klasöründe dosyalar oluşturabilir. Gerçek kullanıcı verilerini GitHub’a eklemeyin.

### 🧰 Geliştirici becerileri ve eklentiler

- Skill kitaplığı becerileri listeleyip arama ve seçilen becerinin talimatlarını okuma akışı sağlar. Depoda PDF, DOCX, XLSX, PPTX, web tasarımı, iletişim, görsel üretim ve MCP gibi alanlarda beceri içerikleri bulunur.
- Claude plugin kitaplığı plugin kaynaklarını ve bileşenlerini incelemeye yardımcı olur; depoda bulunmaları, harici entegrasyonların otomatik olarak bağlandığı anlamına gelmez.
- GitHub/Vercel kontrol araçları, kod haritası, proje yardımcısı, workflow araçları ve isteğe bağlı Claude API geliştirici akışları bulunur.
- Bazı plugin’ler kendi komut satırı aracı, OAuth bağlantısı, API anahtarı veya ek çalışma zamanı ister.

Skill ve plugin içeriklerinin ayrıntısı için [envanter belgesine](JARVIS_SKILL_PLUGIN_ENVANTERI.md) bak.

### 🛡️ Ağ, güvenlik ve metin yardımcıları

- IP, DNS, domain/WHOIS, SSL sertifikası, URL itibar sinyali ve Wi-Fi bağlantı/hız kontrolleri.
- Yerel süreçler için temel risk sinyalleri; parola gücü, dosya hash’i ve AES/Fernet tabanlı metin şifreleme yardımcıları.
- Metin/JSON, Base64, renk ve kelime sayımı gibi hızlı araçlar.

Bu araçlar kapsamlı antivirüs veya profesyonel penetrasyon testi değildir. Ağ taramalarını yalnızca kendi cihazlarında veya açıkça izin aldığın sistemlerde çalıştır.

### 🕹️ Oyunlar ve görünüm

- Cyber Arcade içinde Tetris, Snake, Cyber-Pong, refleks testi ve JARVIS trivia.
- HUD temaları, özel neon vurgu rengi, animasyon/efekt yoğunluğu, ses tercihleri ve başlangıç seçenekleri.
- Sürüklenebilir Yüzen Ada: F8 ile ana panelden geçiş, Ada’daki X ile ana arayüze dönüş; ana arayüzdeki X uygulamayı kapatır, **ARKA PLAN** düğmesi ise JARVIS’i çalışır bırakır.
- Tam ekran, hızlı komut paleti, canlı sistem panosu, ayarlar, App Hub ve ayrı araç/oyun pencereleri.

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
