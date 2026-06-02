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

1. `qrtool/renderers.py` (Yeni adıyla `qr_code_create.py`)
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
   - Üretimde: `payloads` + `qr_code_create.py`.
   - Çözümlemede: `decoders.py`.
5. Sonuç URL ise `security` analizi yapılır.
6. Context hazırlanır ve `templates/qrtool/index.html` render edilir.

## 6) Kütüphaneler: Hangileri, Neden ve Nerede Kullanıldı?

Projenin temel bileşenlerini oluşturan kütüphaneler ve kullanım detayları şunlardır:

### 1. Django
- **Neden Kullanıldı?** Web uygulamasının temel iskeletini oluşturmak, form doğrulama (validation), HTML template rendering ve MVC/MVT mimarisini hızlıca kurmak için.
- **Nerede Kullanıldı?** Projenin tüm HTTP istek/yanıt döngüsünde. Özellikle `qrtool/views.py` dosyasında `index()` fonksiyonunda istekleri (POST/GET) karşılamak ve orchestrate etmek (yönetmek) için; `qrtool/forms.py` dosyasında kullanıcıdan gelen verileri doğrulamak için kullanılmıştır.

### 2. segno
- **Neden Kullanıldı?** Güvenilir ve çok yetenekli bir QR matris (model) üretme kütüphanesi olduğu için. SVG, PNG gibi çıktıları doğrudan veya dolaylı verebilecek matris verisini üretir.
- **Nerede Kullanıldı?** `qrtool/qr_code_create.py` dosyasında, kullanıcı verisini (payload) QR matrisine dönüştürürken. Özellikle `_make_qr_matrix(payload)` fonksiyonu içinde `segno.make()` çağrısı ile kullanılmıştır.

### 3. Pillow (PIL)
- **Neden Kullanıldı?** Görseller üzerinde piksel tabanlı işlemler yapmak (raster görüntü oluşturma, çizim), karelere (framelere) ayırarak animasyonlu GIF'ler üretmek ve QR kodun ortasına logo bindirmek (overlay) için.
- **Nerede Kullanıldı?** `qrtool/qr_code_create.py` dosyasında `_render_png_or_gif` fonksiyonu içerisinde. QR modüllerini (`is_dark` olup olmamasına göre) tek tek piksel bazında çizerken, gradient efekti verirken ve `Image.open(logo_file)` ile logoyu QR içine gömerken kullanılır.

### 4. opencv-python (cv2)
- **Neden Kullanıldı?** Yüklenen kullanıcı görselleri üzerinde gelişmiş ön işlem (pre-processing) yapmak için. Bazen QR kodları bulanık, düşük ışıklı veya okunması zor olabilir; bu yüzden gri tonlama ve eşikleme (thresholding) yapmak başarı oranını büyük ölçüde artırır.
- **Nerede Kullanıldı?** `qrtool/decoders.py` dosyasında `iter_preprocessed_images()` fonksiyonu içerisinde. `cv2.imdecode` ile görseli okur, `cv2.cvtColor` ile gri tonlamaya çevirir, `cv2.threshold` ile OTSU veya standart siyah-beyaz (binary) filtreden geçirir.

### 5. numpy
- **Neden Kullanıldı?** OpenCV kütüphanesinin arka planda matrix hesaplamaları için ndarray (N-dimensional array) formatında çalışması gerektiği için. Python'daki byte verilerini OpenCV'nin anlayacağı formata çevirmek için kullanılır.
- **Nerede Kullanıldı?** `qrtool/decoders.py` dosyasında, kullanıcıdan gelen raw image bytelarını numpy array'e (`np.frombuffer`) dönüştürmek için kullanılmıştır.

### 6. pyzbar
- **Neden Kullanıldı?** C++ tabanlı ZBar kütüphanesinin Python binding'i olarak; görsel içerisindeki QR kod ve barkodları bulup içindeki metni (string) okumak için.
- **Nerede Kullanıldı?** `qrtool/decoders.py` dosyasındaki `decode_with_pyzbar` fonksiyonu içerisinde. OpenCV ile hazırlanan filtrelenmiş görseller pyzbar'ın `decode` fonksiyonuna verilir ve çıkan `item.data` çözümlenerek elde edilir.

### 7. requests
- **Neden Kullanıldı?** Güvenlik analizi yapılacak olan URL'lerin arkasında zararlı bir yönlendirme (redirect) olup olmadığını anlamak için sahte bir "HEAD" HTTP isteği atmak amacıyla.
- **Nerede Kullanıldı?** `qrtool/security.py` dosyasında `security_scan_url()` fonksiyonunda; `requests.head(url)` şeklinde yönlendirme zincirlerini takip etmek için.

---

## 7) Önemli Fonksiyonlar ve Kod Detayları

Projedeki en kritik fonksiyonların nasıl çalıştığı detaylandırılmıştır:

### 1. `qrtool/views.py` -> `index()`
**Amacı:** Kullanıcının tüm etkileşimini (QR oluşturma ve QR tarama) tek bir endpoint üzerinden orkestre eden Ana İstek Yönetici Fonksiyonudur.
**Detaylı Kod Mantığı:**
- Formların POST edilip edilmediğine bakar: `action == "generate"` mi yoksa `action == "scan"` mi?
- Eğer "generate" (üretme) işlemi gelirse, önce veri tipini (`url`, `wifi`, `vcard`, vb.) `qr_form.cleaned_data["data_type"]` üzerinden alır ve ilgili `payloads.py` builder'ını çağırarak QR'a gömülecek ham metni (payload) oluşturur.
- Sonrasında güvenlik analizi (`security_scan_url()`) yapılır ve `_make_qr_matrix()` ile QR matrisi hesaplanır. Seçilen formata göre PNG, GIF veya SVG çıktısı alınarak `context`'e basılır.
- Eğer "scan" (tarama) işlemiyse, `_decode_qr_image()` fonksiyonuna yüklenen dosya gönderilir ve çıkan sonuç yine güvenliğe sokularak ekrana yansıtılır.

### 2. `qrtool/qr_code_create.py` -> `_render_png_or_gif()`
**Amacı:** `segno` ile oluşturulmuş mantıksal (1'ler ve 0'lardan oluşan) QR matrisini, Pillow (PIL) kullanarak piksellere dökmek, renk/gradient uygulamak ve gerekirse animasyonlu bir GIF veya statik bir PNG üretmek.
**Detaylı Kod Mantığı:**
- Matrisin her bir satırını (`row`) ve sütununu (`col`) iterasyona sokar (`for row_index, row in enumerate(modules)`). Ekranda siyah kare (`is_dark = True`) olması gereken yerleri belirler.
- Eğer gradient açıksa, `_interpolate_color()` fonksiyonunu çağırarak yukarıdan aşağıya doğru iki renk arasında geçiş hesaplar.
- Eğer animasyon açıksa, `frame_count` (12 kare) kadar döngü çalışır. Her karede, renk tonunu kosinüs dalgası (`math.cos`) mantığı ile parlaklaştırıp karartarak pulse (nabız) efekti yaratır.
- Eğer logo varsa, `ImageOps.contain` ile logoyu QR kodun %22'si boyutuna ölçekler ve tam orta noktaya `alpha_composite` ile yapıştırır.

### 3. `qrtool/decoders.py` -> `iter_preprocessed_images()` ve `_decode_qr_image()`
**Amacı:** Kullanıcının yüklediği bulanık veya kötü ışıklı bir QR kodunu pyzbar'ın anlayabilmesi için ön işlemden geçirmek ve çözümleme şansını maksimize etmek.
**Detaylı Kod Mantığı:**
- Gelen resmi önce OpenCV `cv2.imdecode` ile okur.
- `iter_preprocessed_images()` adında bir generator mantığı kurularak tek bir görselden 4 farklı versiyon üretilir:
  1. Orijinal Hali (`color_image`)
  2. Gri Tonlama (`cv2.cvtColor(.., cv2.COLOR_BGR2GRAY)`)
  3. Kesin Siyah/Beyaz (`cv2.threshold(.., 127, 255)`)
  4. Dinamik Işık Dengesi / OTSU (`cv2.THRESH_OTSU`)
- Her bir filtreli görsel için `decode_with_pyzbar` çalıştırılır. Eğer pyzbar içlerinden birinde dahi QR'ı başarıyla okursa, işlemi keser (`return decode_result`) ve sonucu kullanıcıya döndürür. Bu "brute-force filter" yaklaşımı projenin en zeki özelliklerinden biridir.

---

## 8) QR Code Generate Etme ve Taramayı Kodlarıyla Anlatım

Aşağıda bu projenin temelini oluşturan QR kod üretme ve QR kod tarama işlemlerinin "en saf" (core) kod örnekleri anlatılmaktadır.

### QR Code Generate Etme (Üretme) İşlemi
Kullanıcının girdiği bir linki (`payload`) `segno` ile matrise çevirip, Pillow ile PNG'ye dönüştürme mantığı aşağıdaki gibidir:

```python
import segno
import io
from PIL import Image, ImageDraw

def simple_qr_generate(payload: str, color: tuple = (0, 0, 0)) -> bytes:
    # 1. Aşama: Payload'ı kullanarak mantıksal QR matrisini oluştur (Hata düzeltme yüksek "h")
    qr_obj = segno.make(payload, error="h")
    modules = qr_obj.matrix
    scale = 10
    size = len(modules) * scale
    
    # 2. Aşama: Boş bir beyaz Pillow Canvas (tuval) oluştur
    image = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # 3. Aşama: Matrisi tarayarak 1 (dark) olan pikselleri çiz
    for row_idx, row in enumerate(modules):
        for col_idx, is_dark in enumerate(row):
            if is_dark:
                x1, y1 = col_idx * scale, row_idx * scale
                x2, y2 = x1 + scale, y1 + scale
                draw.rectangle([x1, y1, x2, y2], fill=color + (255,))
    
    # 4. Aşama: Resmi byte formatına çevir ve döndür
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
```
**Nasıl Çalışır?**
`segno.make()` fonksiyonu string veriyi alır ve QR standartlarına göre iki boyutlu bir boolean matris (True/False tablosu) döner. Kodumuz bu tabloyu tek tek gezer; `True` olan kısımlara bir kare (`draw.rectangle`) çizer. Böylece matematiksel veri görsel bir PNG dosyasına dönüşür.

### QR Code Tarama (Çözme - Decode) İşlemi
Bir görsel dosyasının OpenCV ile okunup, pyzbar ile içindeki metnin çıkarılma mantığı aşağıdaki gibidir:

```python
import cv2
import numpy as np
from pyzbar.pyzbar import decode as pyzbar_decode

def simple_qr_scan(image_bytes: bytes) -> str:
    # 1. Aşama: Byte formatındaki veriyi Numpy dizisine çevir
    image_array = np.frombuffer(image_bytes, np.uint8)
    
    # 2. Aşama: Numpy dizisini OpenCV görüntü formatına çevir
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    
    if image is None:
        return "Görsel okunamadı."

    # 3. Aşama: Görseli daha rahat okunması için Siyah-Beyaz (Gri) tona çevir (Ön işlem)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 4. Aşama: pyzbar ile görseli tara
    decoded_items = pyzbar_decode(gray_image)
    
    # 5. Aşama: Bulunan QR kodlarının içindeki veriyi çıkar
    for item in decoded_items:
        if item.type == "QRCODE":
            # UTF-8 olarak metne çevir
            text = item.data.decode("utf-8")
            return text
            
    return "QR Code bulunamadı."
```
**Nasıl Çalışır?**
`cv2.imdecode()` fonksiyonu dosyayı RAM'e açarak piksellerden oluşan bir matrise çevirir. Görüntüyü gri tona çevirmek (`COLOR_BGR2GRAY`) renk karmaşasını ortadan kaldırır. `pyzbar_decode()` arka planda siyah beyaz piksellerdeki hizalama karelerini (finder patterns) bulur, standart bir QR kodu olduğunu anlar ve üzerindeki bitleri decode ederek orijinal metne (string) ulaşır.

---

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

## 10) Hoca Soruları ve Hazır Cevaplar

1. **Neden modüler yapıya geçtin?**
   - Tek dosyada çok sorumluluk vardı. Modüler yapı bakım ve test kolaylığı sağladı.
2. **Performans olarak ne kazandırdı?**
   - Büyük bir hız artışından çok sürdürülebilirlik ve hata ayıklama kolaylığı sağladı.
3. **Bu güvenlik sistemi antivirüs mü?**
   - Hayır. Bu temel heuristik risk uyarı katmanı.
4. **Neden server-side validasyon önemli?**
   - Frontend manipüle edilse bile iş kurallarını backend garanti eder.
5. **SVG neden ayrı akış?**
   - Çünkü decode için raster dönüşüm gerekebiliyor.
6. **GIF üretimi nasıl sağlanıyor?**
   - QR modülleri frame bazlı çizdirilip GIF olarak encode ediliyor.
7. **Logo eklemek okunabilirliği bozmaz mı?**
   - Boyut kontrollü merkez yerleşim (%22) kullanıldığı için risk azaltılıyor ve QR kodun hata düzeltme seviyesi "h" (yüksek) tutuluyor.
8. **Çözümleme başarısı düşük olursa ne yaparsın?**
   - OpenCV ile `iter_preprocessed_images` içerisinde yaptığım gibi ekstra filtreler (OTSU threshold, grayscale) uygularım.

## 11) Çalıştırma Komutları

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py runserver
```

## 12) Güçlü Kapanış Cümlesi

Bu çalışmada yalnızca QR üretimi değil; modüler yazılım tasarımı, veri doğrulama disiplini, görsel işleme ve temel güvenlik farkındalığı aynı üründe birleştirildi. Son güncelleme ile boş değer üretimi de kapatılarak uygulamanın güvenilirliği artırıldı. Ayrıca farklı görüntü filtreleme teknikleriyle gerçek hayat kullanım senaryolarındaki okuma başarısı maksimize edildi.
