# Sunum Provası - QR Kod Üretici, Çözümleyici ve Güvenlik Kontrolü

## 1) Projeyi 30 Saniyede Anlat

Bu proje Django tabanlı bir web uygulamasıdır. Kullanıcı URL, Wi-Fi, VCard veya Kripto/IBAN verisiyle QR kod üretebilir; ayrıca görsel yükleyerek QR çözümleyebilir. Eğer üretilen ya da çözümlenen içerik URL ise sistem temel heuristik güvenlik kontrolü yapar ve kullanıcıyı olası riskler hakkında uyarır.

## 2) Projeyi 90 Saniyede Anlat

Uygulama tek sayfada iki ana iş yapıyor: QR üretme ve QR çözme.

1. QR üretim tarafında kullanıcı önce veri türünü seçiyor, sonra ilgili alanları dolduruyor.
2. Backend tarafı veriyi uygun payload formatına çeviriyor.
3. Payload, QR matrisine dönüştürülüp PNG/SVG/GIF olarak render ediliyor.
4. İsteğe bağlı logo ekleme, gradient ve şeffaf arka plan destekleniyor.
5. QR çözümleme tarafında kullanıcı bir görsel yüklüyor.
6. Görsel OpenCV tabanlı birkaç ön işleme filtresinden geçirilip pyzbar ile çözülüyor.
7. Son metin URL ise güvenlik katmanı hızlı risk analizi yapıyor.
8. Son güncelleme ile boş veriyle QR üretimi server-side validasyonla engellendi.

## 3) Neyi Çözüyor?

1. Farklı veri tipleri için tek merkezden QR üretim ihtiyacı.
2. QR içeriğini sonradan okuma/doğrulama ihtiyacı.
3. Link tabanlı QR kullanımında temel güvenlik farkındalığı.
4. Sunum ve demo için anlaşılır, modüler ve sürdürülebilir kod yapısı.

## 4) Güncel Mimari (Refactor Sonrası)

### Akış Katmanı

1. `qrtool/views.py`
   - Sadece orchestration yapar.
   - Formu alır, ilgili modülü çağırır, sonucu template'e taşır.

### İş Kuralları Katmanı

1. `qrtool/payloads.py`
   - Veri türüne göre payload üretir.
   - `build_wifi_payload`, `build_vcard_payload`, `build_crypto_payload`.

2. `qrtool/security.py`
   - URL heuristik analizi yapar.
   - `is_http_url`, `security_scan_url`, `SecurityResult`.

### Görsel İşleme Katmanı

1. `qrtool/renderers.py`
   - QR matris üretimi ve render işlemleri.
   - PNG/GIF/SVG üretimi, logo ekleme, SVG raster yardımcıları.

2. `qrtool/decoders.py`
   - Görselden QR çözümleme.
   - Çoklu filtre yaklaşımı ile okuma başarısını artırır.

### Giriş Doğrulama Katmanı

1. `qrtool/forms.py`
   - Alan tanımları ve UI sınıfları.
   - `clean()` ile veri türüne göre zorunlu alan doğrulaması.

## 5) İstek Akışı (Sunumda Tahtaya Çizilecek Özet)

1. Kullanıcı formu gönderir (`generate` veya `scan`).
2. `views.index` isteği alır.
3. `forms.py` validasyonu çalışır.
4. Geçerliyse ilgili modül çağrılır:
   - Üretimde: `payloads` + `renderers`.
   - Çözümlemede: `decoders`.
5. Sonuç URL ise `security` analizi yapılır.
6. Context hazırlanır ve `templates/qrtool/index.html` render edilir.

## 6) Son Değişiklik: Boş Veriyle QR Üretimini Engelleme

Bu bölüm sunumda özellikle anlatılmalı.

### Sorun

Bazı veri türlerinde alanlar boş bırakıldığında yine de üretim akışı tetiklenebiliyordu.

### Çözüm

`QRBuildForm.clean()` içinde veri türüne özel kurallar eklendi.

1. URL türünde `url` zorunlu.
2. Wi-Fi türünde `wifi_ssid` zorunlu.
3. Wi-Fi şifreleme `nopass` değilse `wifi_password` zorunlu.
4. VCard türünde en az ad veya soyad zorunlu.
5. Kripto/IBAN türünde `crypto_address` zorunlu.

### Kazanım

1. Boş/anlamsız payload ile QR üretimi engellendi.
2. İş kuralı sunucu tarafına taşındığı için güvenilirlik arttı.
3. Frontend atlatılsa bile backend veri bütünlüğü korunuyor.

## 7) QR Üretim Akışını Teknik Anlatım

1. Formdan `data_type` ve alanlar gelir.
2. `payloads.py` ilgili standarda göre metin üretir.
3. `renderers._make_qr_matrix` ile matris çıkarılır.
4. Çıktı formatına göre:
   - PNG/GIF: `_render_png_or_gif`
   - SVG: `_render_svg`
5. Üretilen binary veri data URI olarak template'e gönderilir.
6. Kullanıcı önizler ve indirir.

## 8) QR Çözümleme Akışını Teknik Anlatım

1. Kullanıcı görsel yükler.
2. SVG ise önce raster dönüşüm alternatifleri denenir.
3. OpenCV ile gri tonlama, threshold ve OTSU filtreleri uygulanır.
4. pyzbar ile QR decode edilir.
5. Sonuç text bulunursa type/filter bilgisiyle birlikte döndürülür.
6. Text URL ise güvenlik analizi yapılır.

## 9) Güvenlik Katmanı Nasıl Çalışıyor?

`security_scan_url` basit bir risk skorlama mantığı yerine neden listesi yaklaşımı kullanır.

Kontrol edilen başlıca işaretler:

1. Şüpheli regex kalıpları.
2. `@` içeren netloc yapısı.
3. Punycode (`xn--`) olasılığı.
4. Örnek şüpheli domain listesi eşleşmesi.
5. Host yerine doğrudan IP kullanımı.
6. Aşırı alt alan adı zinciri.
7. HEAD isteği ile redirect belirtileri.

Sonuç olarak:

1. Neden yoksa `Güvenli`.
2. En az bir neden varsa `Şüpheli Link`.

## 10) Dosyaları Tek Tek Anlatım Notları

### `manage.py`

1. Django komut giriş noktasıdır.
2. `runserver`, `migrate`, `check` buradan yürür.

### `qrcode_project/settings.py`

1. Proje ayar merkezi.
2. `INSTALLED_APPS`, template, DB ve locale ayarları burada.

### `qrcode_project/urls.py`

1. Üst seviye routing.
2. `admin/` ve uygulama route delegasyonu burada.

### `qrtool/urls.py`

1. Uygulama route tanımları.
2. Ana route `index` view'a bağlı.

### `qrtool/forms.py`

1. Üretim ve çözümleme form tanımları.
2. `clean()` ile koşullu doğrulama.
3. Widget/CSS sınıfları ile UX iyileştirmesi.

### `qrtool/views.py`

1. İş akışı koordinasyon noktası.
2. Üretim ve çözümleme sonrasında context günceller.

### `qrtool/payloads.py`

1. Veri standardizasyonu katmanı.
2. Wi-Fi, VCard, Kripto/IBAN payload üretimi.

### `qrtool/renderers.py`

1. Görsel üretim katmanı.
2. Format bağımlı render işlemleri.

### `qrtool/decoders.py`

1. Görselden QR okuma katmanı.
2. Filtre temelli çözümleme yaklaşımı.

### `qrtool/security.py`

1. URL risk kontrol katmanı.
2. Sonuçları standart bir veri sınıfı ile döndürür.

### `templates/qrtool/base.html`

1. Ortak UI iskeleti.
2. Tema, düzen ve ortak stiller.

### `templates/qrtool/index.html`

1. Tek ekranlı ana iş akışı.
2. Generator/Scanner sekmeleri ve sonuç paneli.

## 11) Kütüphaneleri Neden Kullandın?

1. Django: Form + routing + template + hızlı backend geliştirme.
2. Segno: Stabil QR matris üretimi.
3. Pillow: Görsel çizim, logo bindirme ve çıktı işleme.
4. OpenCV: Görsel ön işleme.
5. NumPy: Matris dönüşümleri.
6. pyzbar: QR decode.
7. requests: URL HEAD kontrolü.
8. Bootstrap: Hızlı ve responsive arayüz.

## 12) Demo Senaryosu (Dakika Dakika)

### 0:00 - 0:30

1. Projenin amacı ve iki ana fonksiyonu: üretim + çözümleme.

### 0:30 - 1:30

1. URL ile QR üretimi.
2. Çıktı formatı değişimi.
3. QR önizleme ve indirme.

### 1:30 - 2:30

1. Scanner sekmesine geçiş.
2. Test görseli yükleme.
3. Çözümlenen içeriğin gösterimi.

### 2:30 - 3:00

1. Güvenlik etiketi ve nedenler.
2. Boş değerle üretim denemesi ve validasyon mesajı.

## 13) Hoca Soruları ve Hazır Cevaplar

1. Neden modüler yapıya geçtin?
   - Tek dosyada çok sorumluluk vardı. Modüler yapı bakım ve test kolaylığı sağladı.

2. Performans olarak ne kazandırdı?
   - Büyük bir hız artışından çok sürdürülebilirlik ve hata ayıklama kolaylığı sağladı.

3. Bu güvenlik sistemi antivirüs mü?
   - Hayır. Bu temel heuristik risk uyarı katmanı.

4. Neden server-side validasyon önemli?
   - Frontend manipüle edilse bile iş kurallarını backend garanti eder.

5. SVG neden ayrı akış?
   - Çünkü decode için raster dönüşüm gerekebiliyor.

6. GIF üretimi nasıl sağlanıyor?
   - QR modülleri frame bazlı çizdirilip GIF olarak encode ediliyor.

7. Logo eklemek okunabilirliği bozmaz mı?
   - Boyut kontrollü merkez yerleşim kullanıldığı için risk azaltılıyor.

8. Hata aldığında ilk nereyi kontrol ediyorsun?
   - Form validasyonu, payload üretimi, render katmanı ve decode giriş formatı.

9. Çözümleme başarısı düşük olursa ne yaparsın?
   - Ek filtreler, kontrast ayarı ve alternatif decoder yaklaşımı eklerim.

10. Bu proje nasıl büyütülür?
    - Kullanıcı geçmişi, API katmanı, daha güçlü URL reputation entegrasyonu eklenebilir.

## 14) Kısa Ezber Cümleleri

1. "Bu projede üretim, çözümleme ve güvenlik farkındalığını tek panelde birleştirdim."
2. "Refactor sonrası views sadece orchestration yapıyor, iş kuralları modüllere ayrıldı."
3. "Son güncelleme ile boş veriyle QR üretimini server-side validasyonla engelledim."
4. "URL içeriklerinde heuristik güvenlik kontrolü ile kullanıcıya risk uyarısı veriyorum."

## 15) Çalıştırma Komutları

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py runserver
```

## 16) Güçlü Kapanış Cümlesi

Bu çalışmada yalnızca QR üretimi değil; modüler yazılım tasarımı, veri doğrulama disiplini, görsel işleme ve temel güvenlik farkındalığı aynı üründe birleştirildi. Son güncelleme ile boş değer üretimi de kapatılarak uygulamanın güvenilirliği artırıldı.
