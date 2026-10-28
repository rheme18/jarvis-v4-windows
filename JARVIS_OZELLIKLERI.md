# J.A.R.V.I.S V4 Özellik Rehberi

Bu belge, depodaki uygulama kodu ve yapılandırma dosyalarına göre J.A.R.V.I.S V4’ün özelliklerini ve entegrasyonlarının gereksinimlerini açıklar. Harici servis isteyen özellikler, ilgili hesap ve izinler kurulmadan çalışmayabilir.

## Kısa tanıtım

J.A.R.V.I.S V4, Windows masaüstünde çalışan; Gemini Live ile sesli görüşme, yazılı komut, Windows araçları, kişisel üretkenlik özellikleri, ağ/güvenlik yardımcıları ve özelleştirilebilir HUD arayüzünü bir araya getiren Python tabanlı bir asistandır. Ana konuşma modeli Gemini’dir. İsteğe bağlı servisler API anahtarı, Google OAuth izni veya kendi uygulama ayarlarını gerektirir.

## Özellik özeti

| Alan | Neler sunar? | Gereksinim / sınır |
|---|---|---|
| Sesli asistan | Gemini Live ile sesli görüşme, yazılı komut, konuşmayı duraklatma ve mikrofon kontrolü | Gemini API anahtarı; sesli kullanım için mikrofon ve hoparlör |
| Windows kontrolü | Uygulama açma, pencere ve sistem araçları, dosya işlemleri, süreç ve donanım bilgileri | Bazı işlemler Windows izinlerine bağlıdır; riskli dosya ve sistem işlemleri onay ister |
| Görsel araçlar | Kamera akışı, ekran görüntüsü analizi, fotoğraf çekme ve hava hareketleri | Kamera/ekran izinleri, uyumlu paketler ve donanım gerekir |
| Google | Gmail arama/etiket, Drive dosya arama, Calendar etkinliklerini okuma, Google Tasks hatırlatıcıları | OAuth istemcisi, API’ler ve izinler; görevler için ayrı kimlik dosyası akışı vardır |
| Üretkenlik | Yerel notlar, kişi kartları, hatırlatıcılar, kalıcı bellek, odak sayacı, günlük brifing ve yapılacaklar | Bazı veriler proje klasöründeki yerel dosyalara/veritabanına yazılır |
| Geliştirici araçları | GitHub ve Vercel işlemleri, Claude API ile kod yardımı, proje özeti, iş akışları, araç/skill/plugin kataloğu | GitHub/Vercel/Claude için ilgili hesap ve token/API anahtarı gerekir |
| İnternet ve medya | Web araması, URL açma, hava durumu, YouTube/Spotify oynatma ve YouTube kanal istatistikleri | İnternet bağlantısı; bazı servisler için API anahtarı veya oturum gerekir |
| Güvenlik ve ağ | IP/DNS/WHOIS/SSL kontrolleri, Wi-Fi/sistem durumu, hash ve parola gücü araçları, yerel süreç risk sinyalleri | Yalnızca kendi cihazında veya izinli hedeflerde kullan |
| Eğlence | Snake, Tetris, Cyber-Pong, refleks testi ve JARVIS bilgi yarışması | Yerel masaüstü arayüzü |
| Kişiselleştirme | HUD temaları ve renkleri, efekt/hareket, ses, görünüm, başlangıç ve güvenlik tercihleri | Seçenekler sürüme ve mevcut ayar ekranlarına bağlıdır |

## Sesli asistan ve komutlar

- Gemini Live üzerinden gerçek zamanlı sesli konuşma ve yazılı komut.
- Mikrofonu sessize alma, görüşmeyi duraklatma ve kamera akışını açıp kapatma.
- Türkçe varsayılan yanıt dili; kullanıcı başka dilde yazarsa o dilde yanıt verme talimatı.
- Hızlı komut paleti ve sesli komut yardım sistemi.
- Önemli tercihleri yerel belleğe kaydetme ve kullanıcı istediğinde kayıtları silme.

## Windows ve masaüstü araçları

- Uygulama başlatma ve URL/web araması açma.
- Pil, CPU, RAM, disk, tarih, saat ve ağ durumunu sorgulama; sistem sağlık raporu.
- Pencere, ses ve ekran kontrolleri; pencere yerleştirme/snap yardımcıları.
- Dosya ve klasör listeleme, arama, okuma, yazma, kopyalama, taşıma, hash ve durum inceleme.
- Pano yardımcıları, hızlı notlar, indirme klasörü temizliği ve yerel yedekleme.
- İşlem/süreç yönetimi, sistem onarım yardımcıları ve otomatik yazma (Ghost Typer).
- Riskli komut, silme, taşıma veya üzerine yazma gibi işlemler için onay akışları.

## Kamera, ekran ve güvenlik modları

- Aktif pencerenin ekran görüntüsünü alıp görsel analiz aracına gönderme.
- Webcam akışını başlatma/durdurma ve kameradan fotoğraf çekme.
- Hava hareketleriyle kontrol için MediaPipe/OpenCV tabanlı araç.
- Yüz kaydı/doğrulaması ve Paranoid Mode üzerinden oda/alan güvenlik seçenekleri.
- Ekranı karartma veya davetsiz misafir fotoğrafı alma gibi seçenekler yapılandırmaya ve kamera erişimine bağlıdır. Bu özellikleri açmadan önce kaydedilen yüz ve fotoğraf verilerini gözden geçir.

## Google ve iletişim entegrasyonları

### Gmail

- Son e-postayı özetleme, arama sorgusuyla e-posta bulma ve etiketleri listeleme.
- Mevcut Gmail API bağlantısı `gmail.readonly` kapsamını ister; bu araçlar e-posta göndermez, silmez veya değiştirmez.
- İlk kullanımda masaüstü OAuth akışı tarayıcıda izin isteyebilir; yetki token’ı yerel dosyada saklanır.

### Google Drive ve Calendar

- Drive’da ada göre dosya arama.
- Calendar etkinliklerini okuma; bağlantı kurulamazsa Google Calendar tarayıcıda açılabilir.
- Takvime etkinlik ekleme komutu, etkinlik bilgileri doldurulmuş Google Calendar sayfasını tarayıcıda açar. Silme komutu da takvimi açıp kullanıcının işlemi orada yapmasını bekler; doğrudan Calendar API üzerinden silme yapmaz.

### Google Tasks ve yerel hatırlatıcılar

- Görev/hatırlatıcı listeleme, ekleme ve silme.
- Google Tasks kimliği hazır değilse JARVIS yerel hatırlatıcı dosyasına geri dönebilir.
- Bu akış, Gmail/Drive/Calendar için kullanılan `config/google_credentials.json` ve token yolundan ayrıdır; kod kök klasörde `credentials.json` ve `token.json` arar.

### Diğer iletişim

- WhatsApp için mesaj taslağı açma/gönderme ve sık kullanılan kişiyi kaydetme.
- Telegram bot modülü ve e-posta gönderim modülü projede bulunur; bunların kullanılabilirliği kendi token/SMTP ayarlarına ve uygulamadaki ilgili araca bağlıdır.
- Gmail OAuth salt okunur bağlantısı ile SMTP/App Password üzerinden e-posta gönderimi birbirinden farklı yapılandırmalardır.

## Üretkenlik, bellek ve çalışma araçları

- Kişisel veritabanına not, günlük, proje ve kişi kaydı ekleme; arama ve kişi kartı açma.
- Kalıcı bellek kaydı ve kullanıcı isteğiyle kaydı silme.
- Yerel veya Google Tasks tabanlı hatırlatıcılar.
- Odak/Pomodoro sayacı, çalışma/öğrenme zamanlayıcısı ve çalışma otomasyonu.
- Günlük brifing, yapılacaklar, hızlı notlar ve pano asistanı.
- App Hub profilleri; kodlama, planlama, toplantı, medya, tasarım, içerik ve DevOps çalışma ortamlarına kısayollar.

## Geliştirici araçları, beceriler ve eklentiler

- Token yapılandırıldığında GitHub bildirimleri, depo/issue/PR ve workflow bilgileri; bazı yazma işlemleri.
- Token yapılandırıldığında Vercel proje, deployment ve domain durumları.
- `CLAUDE_API_KEY` verildiğinde Claude API üzerinden kod yazma, inceleme, refactor ve özellik planlama yardımı.
- Yerel proje özeti/anlık görüntüsü, kod haritası, terminal komutları ve iş akışı oluşturma/çalıştırma araçları.
- Depoda PDF, Word, Excel/CSV, PowerPoint, tasarım, web uygulaması, MCP ve iletişim gibi alanlarda skill içerikleri bulunur.
- Ayrıca resmi ve harici Claude plugin kaynakları depoda yer alır. Bunların depoda bulunması, harici servislerin otomatik olarak bağlandığı veya her plugin’in etkin olduğu anlamına gelmez; plugin/skill yöneticisi ve gereken hesap/çalışma zamanı yapılandırması gerekir.

## İnternet, medya ve güvenlik yardımcıları

- Web araması ve web sayfası açma; hava durumu sorgusu.
- YouTube/Spotify’da içerik açma ve YouTube kanalının herkese açık istatistiklerini getirme.
- IP, DNS, domain/WHOIS, SSL sertifikası, URL itibar sinyali ve Wi-Fi hız kontrolü.
- Parola gücü denetimi, dosya hash’i ve mesaj şifreleme/çözme.
- Yerel süreçler ve bilgisayar/ağ sağlık durumu için temel risk sinyalleri.
- Bu modüller kapsamlı veya garantili bir antivirüs/penetrasyon testi değildir. Ağ taramalarını yalnızca sahibi olduğun ya da açıkça izin aldığın sistemlerde kullan.

## Oyunlar ve arayüz

- Cyber Arcade içinde Tetris, Snake, Cyber-Pong, refleks testi ve JARVIS trivia.
- Sürüklenebilir, üstte kalan şeffaf Yüzen Ada HUD’u; F8 ile açılır, Ada üzerindeki X ana kontrol panelini geri getirir.
- Ana UI’deki pencere X’i J.A.R.V.I.S’i tamamen kapatır; Yüzen Ada’nın X’i ana UI’yi geri açar.
- Ana UI’deki **ARKA PLAN** düğmesi uygulamayı çalışır durumda tutarak pencereyi gizler; F8 Yüzen Ada’yı açar veya ana panele geri döner.
- Özelleştirilebilir HUD temaları/vurgu rengi, animasyon/efekt ve ses tercihleri.
- Ayarlar, sistem ve uygulama merkezi, App Hub, canlı sistem panosu, odak modu, günlük brifing, pano, hızlı notlar, yerel yedekleme ve Windows kontrol pencereleri.
- Bazı panellerin görünümü Windows ölçeklendirme/çözünürlüğüne göre değişebilir.

## Gmail kurulumu: kullanıcı sorarsa JARVIS ne söylemeli?

JARVIS artık kurulum sorusuna proje ile uyumlu adımları anlatacak şekilde talimatlandırılmıştır. Kullanıcı hesabına kendi başına giriş yapmaz; Google’ın OAuth izin ekranını açar ve kullanıcının onayını bekler.

1. Google Cloud Console’da bir proje oluştur veya seç.
2. Projede Gmail API’yi etkinleştir. Drive veya Calendar da kullanılacaksa ilgili API’leri de etkinleştir.
3. Google Auth Platform/OAuth izin ekranını yapılandır ve OAuth istemci türü olarak **Desktop app** seç.
4. İndirilen OAuth istemci JSON’unu `config/google_credentials.json` adıyla proje klasörüne koy. Başka konum kullanılıyorsa `config/.env` içindeki `GOOGLE_CREDENTIALS_FILE` yolunu ayarla.
5. `setup.bat` ile gerekli paketleri kurup JARVIS’i başlat. Gmail’de ilk arama/etiket/son posta isteğinde tarayıcıdan Google hesabını seçip izin ver.
6. Yetkilendirme sonrasında token `config/google_token.json` konumuna yazılır. Bu dosya kişiseldir; paylaşılmaz ve Git’e eklenmez. Özel token yolu gerekiyorsa `GOOGLE_TOKEN_FILE` kullanılabilir.

Gmail kapsamı okuma içindir; bu bağlantıyla e-posta gönderme veya silme yapılmaz. `gmail.readonly` Google tarafından restricted kapsam olarak sınıflandırılır; dağıtım/harici kullanıcı senaryosunda Google’ın OAuth doğrulama koşulları ayrıca incelenmelidir. OAuth istemci dosyası ve token’ı GitHub’a yüklemeyin.

Google’ın resmi belgeleri: [Workspace kimlik bilgileri oluşturma](https://developers.google.com/workspace/guides/create-credentials), [Workspace API’lerini etkinleştirme](https://developers.google.com/workspace/guides/enable-apis), [Gmail API izin kapsamları](https://developers.google.com/workspace/gmail/api/auth/scopes).

## İlgili belgeler

- Kurulum ve genel proje bilgisi: [README.md](README.md)
- Paket listesi: [requirements.txt](requirements.txt)
- Skill/plugin envanteri: [JARVIS_SKILL_PLUGIN_ENVANTERI.md](JARVIS_SKILL_PLUGIN_ENVANTERI.md)
- Lisans: [LICENSE](LICENSE)
