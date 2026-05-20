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
