# Gelişmiş QR Kod Oluşturucu, Çözümleyici ve Güvenlik Tarayıcı

Bu proje, Django tabanlı bir web uygulamasıdır. Uygulama; QR kod üretimi, QR kod çözümleme (görselden okuma) ve URL güvenlik analizi özelliklerini tek panelde birleştirir. Sunum odaklı bakıldığında proje üç temel katmandan oluşur:

1. Sunum katmanı (HTML/CSS/JS): kullanıcı arayüzü, form etkileşimleri, canlı alan gösterme/gizleme.
2. Uygulama katmanı (Django view/form): veriyi doğrulama, payload üretme, güvenlik kontrolleri.
3. İşleme katmanı (kütüphaneler): QR üretme (`segno`), görsel işleme (`Pillow`, `opencv-python`), çözümleme (`pyzbar`), HTTP kontrolü (`requests`).

## Projenin Ana Amacı

Bu uygulama, farklı veri türleri için QR üretimini kolaylaştırırken güvenlik farkındalığını da artırmayı hedefler. Özellikle URL içeren QR kodlarda temel phishing belirtilerini kontrol ederek kullanıcıyı bilgilendirir.

## Temel Özellikler

1. URL, Wi-Fi, VCard ve Kripto/IBAN verisinden QR üretimi.
2. PNG, SVG ve GIF formatlarında çıktı alma.
3. QR merkezine logo/ikon ekleyebilme.
4. Renk, gradient ve şeffaf arka plan özelleştirmeleri.
5. Yüklenen görsellerden QR çözümleme.
6. Çözümleme sonrası bulunan metin URL ise güvenlik analizi.

## Kullanılan Teknolojiler

1. Django: web çatısı ve istek/yanıt yönetimi.
2. Segno: yüksek kaliteli QR üretimi.
3. Pillow: görsel birleştirme, logo bindirme ve raster işlemleri.
4. OpenCV + NumPy: görsel ön işleme.
5. pyzbar: barkod/QR çözümleme.
6. Bootstrap 5: responsive ve modern arayüz.

## Kurulum (Windows)

1. Proje klasörüne geçin.
2. Sanal ortam oluşturun ve aktif edin.
3. Bağımlılıkları kurun.
4. Migrasyonları çalıştırın.
5. Sunucuyu başlatın.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Tarayıcı: `http://127.0.0.1:8000`

## Dosya Bazlı Detaylı Açıklama (Sunum İçin)

### `manage.py`

1. Django komutlarının giriş noktasıdır.
2. `DJANGO_SETTINGS_MODULE` değişkenini ayarlayıp komutları çalıştırır.
3. `runserver`, `migrate`, `createsuperuser` gibi komutlar buradan tetiklenir.

### `qrcode_project/settings.py`

1. Projenin merkezi yapılandırma dosyasıdır.
2. Uygulama listesi (`INSTALLED_APPS`) içinde `qrtool` etkinleştirilmiştir.
3. Template klasörü, veritabanı, dil/saat dilimi ve static ayarları burada tanımlanır.

### `qrtool/views.py`

Bu proje mantığının çekirdeğidir.

1. Payload üretim fonksiyonları: `build_wifi_payload`, `build_vcard_payload`, `build_crypto_payload`.
1. Güvenlik analiz fonksiyonu: `security_scan_url` (regex, kara liste, redirect ve alan adı kalıpları).
1. QR üretim fonksiyonları: `_make_qr_matrix`, `_render_png_or_gif`, `_render_svg`, `_inject_logo_into_svg`.
1. Çözümleme fonksiyonları: `_decode_qr_image` ve SVG raster dönüştürme yardımcıları.
1. Ana akış fonksiyonu: `index` (generate ve scan işlemlerini yürütür, sonucu context ile template'e taşır).

## Güvenlik Tarama Mekanizması (Kısa)

Uygulama URL verisinde temel pattern ve redirect kontrolleri yapar. Bu kontrol üretim seviyesinde olmayan, demo amaçlı bir heuristik katmanıdır.

## Sunum Notu

Sunum sırasında demo adımlarını kısa ve net tutun: üret, önizle, indir; çözümle, güvenlik sonucunu göster.

## Hocanın Sorabileceği Sorular ve Hazır Cevaplar

Bu bölüm, sunum sırasında sık gelebilecek "nasıl yaptın?" sorularına kısa ve net cevap vermen için hazırlandı. Cevapları ezberlemekten çok mantığını kavraman yeterli.

### 1. "Bu projeyi nasıl yaptın?"

Projeyi Django ile web tabanlı bir uygulama olarak kurdum. Kullanıcıdan form ile veri alıyorum, bu veriyi `views.py` içinde işleyip QR kod üretiyorum veya var olan görseli çözümlüyorum. Görsel işlemler için Pillow ve OpenCV, QR üretimi için Segno, çözümleme için de pyzbar kullanıyorum.

### 2. "Farklı veri türleri nasıl destekleniyor?"

Tek bir form içinde URL, Wi-Fi, VCard ve Kripto/IBAN alanlarını topladım. Kullanıcı seçtiği veri tipine göre ilgili alanları dolduruyor, backend tarafında da o tipe uygun payload üretiliyor. Böylece aynı sistem farklı senaryolara uyum sağlıyor.

### 3. "Wi-Fi QR kodu nasıl çalışıyor?"

Wi-Fi için QR içine özel bir metin formatı yazıyorum. Bu formatta SSID, şifre ve şifreleme tipi yer alıyor. Telefon kamerayla QR kodu okuduğunda bu yapı anlaşılır hale geliyor ve ağ bilgileri doğrudan kullanılabiliyor.

### 4. "VCard QR kodunu nasıl oluşturdun?"

Kullanıcının ad, soyad, telefon, e-posta, kurum ve web sitesi bilgilerini VCard formatına çeviriyorum. QR kodun içine bu standarda uygun metin gömülüyor. Böylece okuyan cihaz kişi kartı olarak algılayabiliyor.

### 5. "Kripto veya IBAN bilgisi nasıl kodlanıyor?"

Kripto adresi veya IBAN bilgisini tek bir payload içinde tutuyorum. İsteğe bağlı olarak etiket ve tutar da eklenebiliyor. Amaç, ödeme bilgisini hızlıca okutulabilir hale getirmek.

### 6. "PNG, SVG ve GIF çıktıları nasıl veriliyor?"

QR verisini önce matrise dönüştürüyorum, sonra seçilen formata göre farklı render işlemleri yapıyorum. PNG ve GIF için raster çıktı, SVG için ise vektör çıktı üretiyorum. Bu sayede hem kalite hem de kullanım alanı açısından esneklik sağlıyorum.

### 7. "Logo ekleme özelliğini nasıl yaptın?"

Kullanıcının yüklediği logoyu QR kodun merkezine yerleştiriyorum. Logo boyutunu kontrollü tutuyorum ki QR kodun okunabilirliği bozulmasın. Yani tasarım eklerken okunabilirliği korumaya dikkat ettim.

### 8. "Gradient ve renk seçimi nasıl uygulanıyor?"

Kullanıcı ana ve ikinci renkleri seçebiliyor. Eğer gradient aktifse iki renk arasında geçişli bir görünüm oluşturuyorum, değilse tek renk kullanıyorum. Bu kısım tamamen görsel özelleştirme amacı taşıyor.

### 9. "Şeffaf arka plan ne işe yarıyor?"

QR kodun arka planını düz beyaz yerine transparan üretebiliyorum. Böylece farklı tasarımlara veya koyu arka planlara daha rahat uyum sağlıyor.

### 10. "Yüklenen görsellerden QR nasıl okuyorsun?"

Önce görseli alıyorum, sonra gerekirse ön işleme tabi tutuyorum. Ardından pyzbar ile QR kodu çözmeye çalışıyorum. Eğer görsel SVG ise önce raster formata çevirip sonra çözümleme yapıyorum.

### 11. "URL güvenlik kontrolü tam olarak ne yapıyor?"

Bu özellik tam kapsamlı antivirüs gibi değil, temel bir kontrol katmanı. URL içinde şüpheli desenler, yönlendirme izleri, alan adı anormallikleri gibi işaretleri kontrol ediyorum. Amaç kullanıcıyı olası risklere karşı uyarmak.

### 12. "Bu güvenlik kontrolü kesin sonuç verir mi?"

Hayır, bu bir demo amaçlı heuristik kontroldür. Yani bazı riskleri yakalayabilir ama %100 karar mekanizması değildir. Sunumda bunu özellikle belirtmek iyi olur.

### 13. "Neden Django kullandın?"

Çünkü form yönetimi, template sistemi ve backend mantığını hızlı ve düzenli kurmamı sağladı. Ayrıca Python tabanlı kütüphanelerle entegrasyon kolay olduğu için bu proje için uygun bir seçim oldu.

### 14. "Bu projede en önemli teknik nokta neydi?"

En önemli nokta, üretim ve çözümleme akışını tek bir panelde birleştirmekti. Hem kullanıcı dostu arayüz hem de arka planda doğru payload üretimi ve güvenilir görsel işleme birlikte çalışmalıydı.

### 15. "Sunumda takılırsam ne söyleyeyim?"

Şunu söyleyebilirsin: "Bu özellik, formdan gelen veriyi backend’de uygun payload’a çevirip QR koda dönüştürüyor. Amaç, kullanıcının veriyi hem üretmesi hem de gerekirse çözümlemesi." Bu cümle çoğu teknik soruyu toparlar.

## Kısa Ezber Cümleleri

1. "Formdan veri alıyorum, backend’de payload üretiyorum, QR koda çeviriyorum."
2. "Logo eklerken okunabilirliği koruyacak boyutlandırma yapıyorum."
3. "Güvenlik kontrolü tam analiz değil, temel risk uyarısı veren bir heuristik katman."
4. "SVG için vektör, PNG/GIF için raster çıktı üretiyorum."
5. "Aynı form yapısıyla farklı veri tiplerini tek sistemde topladım."

## Sunumda Kullanılacak Kısa Strateji

1. Önce özelliği bir cümlede anlat.
2. Sonra nasıl çalıştığını teknik olarak tek paragrafta açıkla.
3. Soru gelirse örnek ver.
4. Çok detaya girme; önce akışı, sonra gerektiğinde iç mekanizmayı anlat.

## Dosyalar Ne İşe Yarıyor?

Bu bölüm, projedeki her ana dosyanın görevini ve içindeki önemli kodların ne yaptığını anlatır. Sunumda hoca bir dosyayı sorarsa burada yer alan açıklamalar doğrudan kullanılabilir.

### manage.py

Bu dosya Django projesinin komut giriş noktasıdır. Terminalden çalıştırılan migrate, runserver, createsuperuser gibi komutlar bu dosya üzerinden Django'ya iletilir.

Önemli nokta, DJANGO_SETTINGS_MODULE ayarının qrcode_project.settings olarak belirlenmesidir. Bu sayede Django hangi ayar dosyasını kullanacağını bilir.

Sunumda şöyle anlatabilirsin: "manage.py, Django'nun başlangıç dosyasıdır. Ben burada proje ayarlarını gösterip terminal komutlarını Django'ya yönlendiriyorum."

### qrcode_project/settings.py

Bu dosya projenin ana yapılandırma merkezidir. Uygulamanın hangi bileşenleri kullanacağını, template klasörlerini, veritabanını, dil ve saat dilimini burada tanımlıyorum.

Önemli kısımlar:

1. INSTALLED_APPS: qrtool uygulaması burada aktif ediliyor. Bu olmadan Django uygulamayı tanımaz.
2. TEMPLATES: templates klasörünün proje genelinde kullanılmasını sağlıyor.
3. DATABASES: SQLite veritabanı bağlantısı burada tanımlı.
4. LANGUAGE_CODE ve TIME_ZONE: uygulamanın Türkçe ve İstanbul saat dilimine göre çalışmasını sağlıyor.
5. STATICFILES_DIRS: static klasörü varsa burada ekleniyor, böylece CSS ve JS dosyaları geliştirirken rahatça kullanılabiliyor.

Sunumda anlatım şekli: "settings.py, uygulamanın ayar merkezidir. Hangi app'ler açık, template nerede, veritabanı ne, bunların hepsi burada belirleniyor."

### qrcode_project/urls.py

Bu dosya proje seviyesindeki yönlendirme yapısını yönetir. Yani gelen isteğin admin paneline mi yoksa qrtool uygulamasına mı gideceğine burada karar verilir.

Önemli kodlar:

1. path("admin/", admin.site.urls): yönetici paneli rotasıdır.
2. path("", include("qrtool.urls")): ana sayfa ve uygulama rotalarını qrtool uygulamasına devreder.

Sunumda şöyle diyebilirsin: "Bu dosya ana trafik yöneticisi gibi çalışıyor. Admin yolu ayrı, kullanıcı arayüzü yolu ayrı şekilde yönlendiriliyor."

### qrtool/urls.py

Bu dosya uygulama içindeki rota tanımını tutar. Şu anda tek giriş noktası olan index view'ine yönlendirme yapıyor.

Önemli kod:

1. path("", index, name="index"): ana sayfayı views.py içindeki index fonksiyonuna bağlar.

Sunumda anlatım: "Kullanıcı ana sayfaya geldiğinde sistem doğrudan index fonksiyonuna gidiyor. Uygulamanın ana akışı burada başlıyor."

### qrtool/forms.py

Bu dosya kullanıcıdan alınacak tüm verileri düzenli bir şekilde toplar. İki ana form var: QRBuildForm ve QRScanForm.

QRBuildForm içinde önemli alanlar:

1. data_type: URL, Wi-Fi, VCard veya Kripto/IBAN seçimini yaptırır.
2. output_format: PNG, SVG veya GIF çıktısı seçtirir.
3. url, wifi_ssid, wifi_password, vcard alanları, crypto alanları: veri tipine göre doldurulan girişlerdir.
4. primary_color, secondary_color, use_gradient, transparent_bg, logo: QR görünümünü özelleştiren alanlardır.

__init__ metodu içinde önemli mantık vardır. Her alana Bootstrap uyumlu CSS sınıfları eklenir, placeholder değerleri verilir ve renk alanları color input olarak ayarlanır. Bu kısım kullanıcı deneyimini iyileştirir.

QRScanForm ise yalnızca QR görseli yüklemek için kullanılır. image alanı ile kullanıcıdan dosya alınır.

Sunumda şöyle anlatabilirsin: "forms.py, kullanıcıdan alınan verinin düzenli ve doğrulanmış biçimde toplanmasını sağlıyor. Ayrıca arayüz tarafında form elemanlarını Bootstrap'a uygun hale getiriyor."

### qrtool/views.py

Bu dosya projenin asıl iş mantığını taşır. QR üretimi, QR çözümleme, payload oluşturma ve güvenlik kontrolü burada yapılır.

Önemli veri yapıları:

1. SecurityResult: güvenlik taramasının sonucunu tutar. safe, status_label, reasons ve final_url alanları vardır.
2. QRDecodeResult: çözümlenen QR metnini ve okuma bilgisini taşır.

Önemli fonksiyonlar:

1. build_wifi_payload: Wi-Fi için özel QR metnini oluşturur. SSID, şifre ve şifreleme türünü standart formata çevirir.
2. build_vcard_payload: kişi bilgilerini VCard 3.0 formatına dönüştürür.
3. build_crypto_payload: kripto adresi veya IBAN bilgisini QR'a uygun metne çevirir.
4. is_http_url: gelen verinin HTTP veya HTTPS URL olup olmadığını kontrol eder.
5. security_scan_url: URL üzerinde hızlı bir risk analizi yapar. Şüpheli kelime kalıpları, IP kullanımını, punycode alan adlarını, yönlendirme denemelerini ve örnek kara liste eşleşmelerini kontrol eder.
6. _make_qr_matrix: Segno ile QR matrisini üretir.
7. _render_png_or_gif: PNG veya GIF çıktısını oluşturur. Gradient, animasyon, logo ve şeffaf arka plan mantığı burada çalışır.
8. _render_svg: SVG çıktısını üretir. İstenirse logo da SVG içine gömülür.
9. _inject_logo_into_svg: SVG dosyasının ortasına base64 gömülü logo ekler.
10. _svg_bytes_to_png_bytes ve _segno_svg_bytes_to_png_bytes: SVG çözümleme için raster dönüşüm yardımı sağlar.

Ana akış fonksiyonu olan index çok önemlidir. Bu fonksiyon formdan gelen veriyi alır, hangi işlemin yapılacağını belirler, payload üretir, QR render eder veya çözümleme yapar ve sonucu template'e gönderir.

Sunumda güçlü bir açıklama şöyle olur: "views.py, kullanıcı aksiyonlarını işleyen merkezdir. Formdan gelen bilgiyi alır, doğru payload'a dönüştürür, QR üretir, gerekirse de görseli çözümler."

### templates/qrtool/base.html

Bu dosya tüm sayfalarda ortak kullanılan ana HTML iskeletidir. Bootstrap bağlantısı, renk değişkenleri, arka plan tasarımı ve ortak kart stilleri burada tanımlanır.

Önemli noktalar:

1. CSS değişkenleri: arka plan, panel, yazı ve vurgu renkleri burada merkezi şekilde tutulur.
2. .hero ve .glass-card sınıfları: modern cam efekti görünümünü sağlar.
3. .app-button sınıfları: tüm butonların ortak tasarımını oluşturur.
4. .file-picker ve .color-control gibi sınıflar: dosya seçimi ve renk alanlarının daha kullanışlı görünmesini sağlar.

Sunumda anlatım: "base.html, arayüzün ortak tasarım katmanıdır. Sayfalarda kullanılan modern görünüm ve buton stilleri burada tanımlanıyor."

### templates/qrtool/index.html

Bu dosya ana kullanıcı arayüzüdür. QR üretme ve QR çözümleme sekmeleri burada yer alır.

Önemli bölümler:

1. toolTabs: üretme ve çözümleme sekmeleri arasında geçiş yapar.
2. Generator formu: veri türü, çıktı formatı, logo, renkler, gradient ve şeffaf arka plan ayarlarını kullanıcıdan alır.
3. field-group blokları: seçilen veri tipine göre ilgili alanları gösterip gizler.
4. Scanner formu: QR görseli yükleyip çözümleme yapar.
5. Sonuç paneli: üretilen payload, çözümlenen metin, güvenlik sonucu ve indirme bağlantısını gösterir.
6. Önizleme alanı: üretilen QR kodun ekran üzerinde görünmesini sağlar.

Sunumda şöyle denebilir: "index.html, kullanıcının uygulamayla temas ettiği ana ekrandır. Formlar, sekmeler ve sonuç gösterimi burada toplanıyor."

### qr_code.py

Bu dosya tek başına çalışan basit bir örnek betiktir. Django uygulamasının parçası değil, Segno kütüphanesinin temel kullanımını göstermek için eklenmiş bir yardımcı dosya gibidir.

İçindeki önemli mantık:

1. data değişkeni: QR içine yazılacak sabit örnek bağlantıdır.
2. segno.make(...): QR nesnesini oluşturur.
3. qr.save("qr_code.png", ...): QR kodu dosya olarak kaydeder.

Sunumda şunu söyleyebilirsin: "qr_code.py, Segno'nun temel kullanımını denemek için hazırladığım basit örnek dosyadır. Asıl web mantığı views.py içinde çalışır."

## Dosyaları Anlatırken Kullanabileceğin Kısa Sıralama

1. manage.py ile başla: giriş noktası olduğunu söyle.
2. settings.py ile devam et: ayarlar, app listesi, veritabanı.
3. urls.py dosyalarıyla akışı anlat: ana rota ve uygulama rotası.
4. forms.py ile kullanıcı verisinin nasıl alındığını açıkla.
5. views.py ile asıl işlem mantığını anlat: payload, QR üretimi, çözümleme, güvenlik kontrolü.
6. templates ile arayüzü tamamla: base.html tasarım, index.html ekran.
7. qr_code.py ile bunun küçük bir örnek yardımcı dosya olduğunu belirt.

## Hocaya Kısa Cevap Şablonları

1. "Bu dosya projenin şu kısmını yönetiyor: ..."
2. "Bu fonksiyonun görevi, gelen veriyi QR'a uygun formata çevirmek."
3. "Bu bölümde kullanıcı arayüzünü ve form akışını yönetiyorum."
4. "Bu kısımda güvenlik için heuristik kontroller yapıyorum, kesin karar mekanizması değil."
5. "Bu dosya ana iş mantığını taşıyor, diğerleri onu destekliyor."

## Kütüphaneler Neden Kullanıldı?

Bu bölümde projede kullanılan ana kütüphaneleri, neden seçildiklerini ve kodun hangi kısmında kullanıldıklarını anlatıyorum. Sunumda hoca "neden bunu kullandın?" diye sorarsa buradaki cevaplar yeterli olur.

### Django

Django, projenin ana web çatısıdır. Kullanıcıdan veri alma, form doğrulama, sayfa yönlendirme, template render etme ve istek/yanıt akışını yönetme işi onunla yapılır.

Nerede kullanıldı:

1. [manage.py](sunum%20provasi.md#L160) ile Django komutları başlatılıyor.
2. [qrcode_project/settings.py](sunum%20provasi.md#L160) içinde proje ayarları, app listesi ve template ayarları tutuluyor.
3. [qrcode_project/urls.py](sunum%20provasi.md#L160) ve [qrtool/urls.py](sunum%20provasi.md#L160) ile routing yapılıyor.
4. [qrtool/forms.py](sunum%20provasi.md#L160) ile form alanları tanımlanıyor.
5. [qrtool/views.py](sunum%20provasi.md#L160) içinde tüm iş mantığı çalışıyor.
6. [templates/qrtool/index.html](sunum%20provasi.md#L160) ile kullanıcı arayüzü gösteriliyor.

Neden seçildi:

1. Python ile doğal uyum sağlar.
2. Form ve template yapısı bu proje için çok uygundur.
3. QR üretimi, çözümleme ve güvenlik kontrolü gibi farklı akışları tek çatı altında toplamak kolay olur.

Sunum cümlesi: "Django'yu projenin omurgası olarak kullandım; çünkü form, routing ve template yönetimini düzenli şekilde çözmemi sağladı."

### segno

segno, QR kod üretimi için kullandığım ana kütüphanedir. Bu kütüphane QR matrisini oluşturur ve çıktı formatlarına dönüştürmeyi kolaylaştırır.

Nerede kullanıldı:

1. [qrtool/views.py](sunum%20provasi.md#L160) içindeki _make_qr_matrix fonksiyonunda QR nesnesi üretiliyor.
2. Aynı dosyada _render_svg fonksiyonunda SVG çıktısı oluşturuluyor.
3. _render_png_or_gif fonksiyonunda segno'nun ürettiği QR matrisi piksel bazlı çizim için temel oluyor.
4. [qr_code.py](sunum%20provasi.md#L160) içinde basit örnek kullanım da var.

Neden seçildi:

1. Hata düzeltme seviyesi yüksek QR üretimi sağlar.
2. SVG gibi vektörel çıktıyı doğrudan destekler.
3. QR verisini farklı render akışlarına uygun şekilde üretmek kolaydır.

Sunum cümlesi: "QR'ın kendisini üretmek için segno kullandım; çünkü hem sağlam QR matrisi oluşturuyor hem de PNG, GIF ve SVG gibi farklı çıktılara uygun çalışıyor."

### Pillow

Pillow, görsel işleme tarafında kullandığım ana kütüphanedir. Logo bindirme, renk işleme, arka plan düzenleme ve çıktı kaydetme gibi işler burada yapılır.

Nerede kullanıldı:

1. [qrtool/views.py](sunum%20provasi.md#L160) içinde Image, ImageColor, ImageDraw ve ImageOps import ediliyor.
2. _render_png_or_gif fonksiyonunda QR kod piksel piksel çiziliyor.
3. Logo dosyası varsa merkezde birleştiriliyor.
4. _inject_logo_into_svg içinde SVG mantığına yardımcı olacak logo görseli işlemleri yapılıyor.
5. _segno_svg_bytes_to_png_bytes fonksiyonunda SVG'den bitmap üretiminde çizim kullanılıyor.

Neden seçildi:

1. Python tarafında görsel işleme için pratik ve güçlüdür.
2. QR'a logo ekleme gibi tasarımsal işleri kolaylaştırır.
3. PNG ve GIF gibi raster formatları güvenilir biçimde üretir.

Sunum cümlesi: "Pillow'u görsel düzenleme için kullandım; özellikle logo ekleme, renk çizimi ve PNG/GIF üretimi bu kütüphane ile yapılıyor."

### OpenCV

OpenCV, görüntü ön işleme ve QR çözümleme performansını artırmak için kullanıldı. QR görsellerini çözmeden önce bazı durumlarda filtreleme veya format hazırlama amacıyla tercih edilir.

Nerede kullanıldı:

1. [qrtool/views.py](sunum%20provasi.md#L160) içinde cv2 import ediliyor.
2. QR çözümleme akışında görselin işlenmesi için yardımcı rol oynuyor.

Neden seçildi:

1. Görüntü işleme konusunda güçlü bir altyapı sunar.
2. Zor okunabilen görsellerde ön işleme için faydalıdır.
3. Python ekosisteminde QR çözümleme gibi işleri destekleyen standart araçlardan biridir.

Sunum cümlesi: "OpenCV'yi görsel ön işleme için kullandım; çünkü QR okuma sırasında görüntüyü daha uygun hale getirmeye yardımcı oluyor."

### NumPy

NumPy, görüntü ve piksel verileri üzerinde sayısal işlem yapmak için kullanıldı. OpenCV ile birlikte özellikle matris tabanlı işlemlerde faydalıdır.

Nerede kullanıldı:

1. [qrtool/views.py](sunum%20provasi.md#L160) içinde np import ediliyor.
2. Görsel ön işleme ve matris tabanlı dönüşümlerde yardımcı rol oynuyor.

Neden seçildi:

1. Görüntüler sayısal matrislerdir; NumPy bu yapı için uygundur.
2. OpenCV ile doğal biçimde birlikte çalışır.
3. Hızlı ve pratik veri dönüşümü sağlar.

Sunum cümlesi: "NumPy'yi görüntüleri matris olarak işlemek için kullandım; OpenCV ile birlikte çözümleme tarafını destekliyor."

### pyzbar

pyzbar, QR ve barkod çözümleme için kullandığım kütüphanedir. Kullanıcının yüklediği görselin içindeki QR verisini okumak için bu kütüphane üzerinden decode işlemi yapılıyor.

Nerede kullanıldı:

1. [qrtool/views.py](sunum%20provasi.md#L160) içinde from pyzbar.pyzbar import decode as pyzbar_decode satırı var.
2. QR çözümleme akışında görselden veri okumak için kullanılıyor.

Neden seçildi:

1. QR ve barkod çözümleme için doğrudan ve sade bir API sağlar.
2. Python tarafında pratik kullanım sunar.
3. Çözümleme sonucunda tip ve içerik bilgisi vermesi sunum açısından da güçlüdür.

Sunum cümlesi: "QR kodu okuma kısmında pyzbar kullandım; çünkü görselin içindeki QR verisini doğrudan çözebiliyor."

### requests

requests, URL güvenlik kontrolü sırasında dış istekte bulunmak için kullanılıyor. Özellikle yönlendirme olup olmadığını hızlıca anlamak için HEAD isteği atılıyor.

Nerede kullanıldı:

1. [qrtool/views.py](sunum%20provasi.md#L160) içindeki security_scan_url fonksiyonunda requests.head kullanılıyor.

Neden seçildi:

1. HTTP istekleri için en sade ve yaygın Python kütüphanelerinden biridir.
2. Redirect kontrolü yapmak için kolay kullanılır.
3. Güvenlik taraması gibi küçük kontrol işlerinde yeterince hızlıdır.

Sunum cümlesi: "requests'i URL kontrolü için kullandım; özellikle yönlendirme ve şüpheli cevapları hızlıca kontrol etmek için."

### Bootstrap 5

Bootstrap, kullanıcı arayüzünü daha düzenli, responsive ve modern yapmak için kullanıldı. Formların hizalanması, sekmeler, kart yapıları ve butonlar burada güçlü şekilde destekleniyor.

Nerede kullanıldı:

1. [templates/qrtool/base.html](sunum%20provasi.md#L160) içinde CDN üzerinden ekleniyor.
2. [templates/qrtool/index.html](sunum%20provasi.md#L160) içinde nav-tabs, grid ve form sınıflarıyla kullanılıyor.
3. [qrtool/forms.py](sunum%20provasi.md#L160) içinde form alanlarına bootstrap sınıfları ekleniyor.

Neden seçildi:

1. Hızlı ve temiz arayüz oluşturur.
2. Mobil uyumlu tasarımı kolaylaştırır.
3. Form tabanlı projelerde düzenli bir görünüm sağlar.

Sunum cümlesi: "Bootstrap'ı arayüzü hızlıca düzenlemek ve responsive hale getirmek için kullandım."

### HTML, CSS ve JavaScript

Bunlar ayrı paket değil ama projenin ön yüzünü oluşturan temel web teknolojileridir. HTML yapı kurar, CSS görünümü tasarlar, JavaScript ise alan gösterme/gizleme ve renk güncelleme gibi dinamik davranışları yönetir.

Nerede kullanıldı:

1. [templates/qrtool/base.html](sunum%20provasi.md#L160) içinde genel stil tanımları var.
2. [templates/qrtool/index.html](sunum%20provasi.md#L160) içinde form ve sekme yapısı kurulmuş.
3. Sayfadaki bazı dinamik davranışlar JavaScript ile yönetiliyor.

Neden seçildi:

1. Web arayüzü için zorunlu temel katmandır.
2. Kullanıcı deneyimini doğrudan iyileştirir.
3. QR üretiminde gerekli alanları koşullu olarak göstermek için uygundur.

Sunum cümlesi: "Ön yüzü HTML, CSS ve JavaScript ile kurdum; form görünümü ve dinamik alan geçişleri burada yönetiliyor."

## Kütüphaneleri Anlatırken Kullanabileceğin Kısa Mantık

1. "Bu kütüphaneyi şu işi kolaylaştırdığı için kullandım."
2. "Kodda şu fonksiyonda kullanılıyor."
3. "Alternatif vardı ama bu çözüm hem daha sade hem de proje ihtiyacına daha uygundu."
4. "Bu kütüphane işin şu parçasını çözüyor: üretim, çözümleme, görsel işleme veya güvenlik kontrolü."
