# Gelişmiş QR Kod Oluşturucu, Çözümleyici ve Güvenlik Tarayıcı

Bu proje, Django tabanlı bir web uygulamasıdır. Uygulama; QR üretimi, QR çözümleme ve URL güvenlik analizi özelliklerini tek ekranda sunar.

## Özellikler

1. URL, Wi-Fi, VCard ve Kripto/IBAN verisinden QR üretimi.
2. PNG, SVG ve GIF çıktıları.
3. Logo/ikon ekleme, renk seçimi, gradient ve şeffaf arka plan desteği.
4. Yüklenen görsellerden QR çözümleme.
5. Çözümlenen metin URL ise temel heuristik güvenlik analizi.
6. Veri türüne göre zorunlu alan validasyonu (boş değerle QR üretimi engellenir).

## Güncel Mimari

İş mantığı modüler hale getirilmiştir:

- `qrtool/views.py`: yalnızca akış orkestrasyonu (`index`).
- `qrtool/payloads.py`: payload üretimi (`build_wifi_payload`, `build_vcard_payload`, `build_crypto_payload`).
- `qrtool/security.py`: URL analizi (`security_scan_url`, `is_http_url`, `SecurityResult`).
- `qrtool/renderers.py`: QR render katmanı (PNG/GIF/SVG, logo, SVG raster yardımcıları).
- `qrtool/decoders.py`: QR çözümleme (`_decode_qr_image`, `QRDecodeResult`).
- `qrtool/forms.py`: form alanları + veri türüne göre server-side validasyon.

## Teknolojiler

1. Django
2. Segno
3. Pillow
4. OpenCV + NumPy
5. pyzbar
6. requests
7. Bootstrap 5

## Kurulum (Windows)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Tarayıcı: `http://127.0.0.1:8000`

## Hızlı Doğrulama

```powershell
.\.venv\Scripts\python.exe manage.py check
```

## Not

Güvenlik taraması, üretim seviyesinde tam kapsamlı bir tehdit motoru değildir. Demo amaçlı temel heuristik kontrol katmanı olarak tasarlanmıştır.
