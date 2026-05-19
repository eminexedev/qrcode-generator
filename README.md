# Gelişmiş QR Kod Oluşturucu, Çözümleyici ve Güvenlik Tarayıcı

Bu proje, güvenlik ve özelleştirme odaklı bir web tabanlı QR araç setidir. Django ile yazılmış backend; `segno`, `Pillow` ve `opencv-python` kullanılarak QR üretme, logo bindirme, çeşitli çıktı formatları (PNG, SVG, GIF) ve görselden QR çözümleme yetenekleri sunar. Ayrıca URL içeriği için temel bir güvenlik tarayıcısı (phishing heuristics, kara liste, redirect kontrolü) içerir.

Özellikler
- Standart URL, Wi-Fi (otomatik bağlanma formatı), VCard ve Kripto/IBAN destekli QR üretimi.
- Logo/ikon bindirme; renk, gradient ve şeffaf arka plan seçenekleri.
- Çıktı olarak yüksek kaliteli `SVG`, `PNG` ve animasyonlu `GIF` desteği.
- Görsel yükleyerek QR kod çözümleme (OpenCV tabanlı).
- URL güvenlik taraması: regex tabanlı phishing bulguları, örnek kara liste ve HTTP redirect kontrolü.
- Bootstrap 5 ile hızlı, karanlık temalı ve modern arayüz.

Gereksinimler
- Python 3.11+ (projede kullanılan ortam 3.13 ile test edildi)
- Sanal ortam tavsiye edilir

Kurulum (Hızlı Başlangıç - Windows)

1. Depoyu klonlayın veya dosyaları indirin.

2. Proje dizinine gidin ve sanal ortam oluşturun:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Bağımlılıkları yükleyin:

```powershell
pip install -r requirements.txt
```

4. Veritabanı migrasyonlarını uygulayın:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
```

5. Geliştirme sunucusunu çalıştırın:

```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Kullanım
- Tarayıcıdan `http://127.0.0.1:8000` adresine gidin.
- "QR Üret" sekmesinde veri tipini seçin (URL, Wi-Fi, VCard, Kripto/IBAN).
- Girdi alanlarını doldurun, tercihinize göre `PNG`, `SVG` veya `GIF` seçin.
- Logo ekleyerek merkezine ikon bindirebilirsiniz; şeffaf arka plan veya gradient seçeneklerini kullanın.
- Üret butonuna bastığınızda önizleme ve indirme linki oluşacaktır.
- "QR Çözümle" sekmesinde bir görsel yükleyerek içeriği çözümleyebilirsiniz.

Güvenlik Tarama Açıklaması
- Uygulama, bir URL içerip içermediğini kontrol eder; eğer geçmişse:
  - Basit regex ile phishing/şüpheli anahtar kelimeler aranır.
  - Örnek bir kara listeyle karşılaştırma yapılır (uygulanabilir bir veritabanı ile genişletin).
  - `requests.head` ile yönlendirme (redirect) olup olmadığı kontrol edilir.
- Bu tarama, üretim sınıfı bir tarayıcı yerine temel heuristikler sağlar; gerçek dünya dağıtımları için harici hizmetler (Google Safe Browsing, VirusTotal vb.) ve kapsamlı alan/WHOIS/IP analizleri eklemeniz önerilir.

Dosya Yapısı (Önemli Dosyalar)
- `manage.py` — Django yönetim aracı
- `requirements.txt` — Proje bağımlılıkları
- `qrcode_project/` — Django proje ayarları
- `qrtool/` — Uygulama: `views.py`, `forms.py`, `urls.py`
- `templates/qrtool/` — `base.html`, `index.html` (UI)
- `qr_code.py` — yardimci script (segno ile örnek QR üretimi)

Geliştirme Notları ve İpuçları
- `segno` SVG üretimi için esnektir; logo ekleme ve SVG manipülasyonu `ElementTree` ile yapılır.
- GIF animasyonları basit çerçeve tabanlı animasyonlardır; daha sofistike GIF veya APNG gereksinimleri için ek optimizasyon gerekebilir.
- OpenCV'nin `QRCodeDetector` sınıfı birçok görseli çözebilir; düşük kaliteli veya kırpılmış görsellerde hata düzeltme seviyeleri önemlidir.

İleri Adımlar / İyileştirmeler
- Güvenlik tarayıcısını gerçek servislerle entegre etme (Google Safe Browsing API, VirusTotal).
- Kullanıcı kimlik doğrulama, kullanım kotaları ve oluşturulan QR'ların izlenmesi/loglama.
- Asenkron görev kuyruğu (Celery/RQ) ile büyük resim işlemleri veya maliyetli güvenlik sorgularını arka plana alma.

Katkıda Bulunma
- Pull request açmadan önce issue oluşturup kısa bir açıklama bırakınız.

Lisans
- Bu proje örnek amaçlıdır; lisans eklemek istiyorsanız `LICENSE` dosyası ekleyin.

İletişim
- Daha fazla yardım isterseniz proje sahibine mesaj atın veya issue açın.
