from django import forms


class QRBuildForm(forms.Form):
    # Kullanıcının üretmek istediği QR veri türleri.
    DATA_TYPE_CHOICES = [
        ("url", "Standart URL"),
        ("wifi", "Wi-Fi"),
        ("vcard", "VCard"),
        ("crypto", "Kripto / IBAN"),
    ]

    OUTPUT_FORMAT_CHOICES = [
        ("png", "PNG"),
        ("svg", "SVG"),
        ("gif", "GIF"),
    ]

    WIFI_ENCRYPTION_CHOICES = [
        ("WPA", "WPA/WPA2"),
        ("WEP", "WEP"),
        ("nopass", "Şifresiz"),
    ]

    # QR oluşturmak için gerekli tüm veri türlerini tek bir formda toplama
    data_type = forms.ChoiceField(label="Veri Türü", choices=DATA_TYPE_CHOICES)
    output_format = forms.ChoiceField(label="Çıktı Formatı", choices=OUTPUT_FORMAT_CHOICES, initial="png")

    url = forms.URLField(label="URL", required=False)

    wifi_ssid = forms.CharField(label="Wi-Fi Adı (SSID)", required=False)
    wifi_password = forms.CharField(label="Wi-Fi Şifresi", required=False, widget=forms.PasswordInput)
    wifi_encryption = forms.ChoiceField(label="Şifreleme", required=False, choices=WIFI_ENCRYPTION_CHOICES)

    vcard_first_name = forms.CharField(label="Ad", required=False)
    vcard_last_name = forms.CharField(label="Soyad", required=False)
    vcard_phone = forms.CharField(label="Telefon", required=False)
    vcard_email = forms.EmailField(label="E-posta", required=False)
    vcard_org = forms.CharField(label="Kuruluş", required=False)
    vcard_title = forms.CharField(label="Unvan", required=False)
    vcard_website = forms.URLField(label="Web Sitesi", required=False)

    # Kripto para adresi veya IBAN bilgisi için gerekli alanlar.
    crypto_type = forms.ChoiceField(
        label="Cüzdan Türü",
        choices=[("crypto", "Kripto Adresi"), ("iban", "IBAN")],
        required=False,
    )
    crypto_address = forms.CharField(label="Adres / IBAN", required=False)
    crypto_label = forms.CharField(label="Etiket", required=False)
    crypto_amount = forms.CharField(label="Tutar", required=False)

    primary_color = forms.CharField(label="Ana Renk", initial="#111111")
    secondary_color = forms.CharField(label="İkinci Renk", initial="#2563eb")
    use_gradient = forms.BooleanField(label="Gradient kullan", required=False)
    transparent_bg = forms.BooleanField(label="Şeffaf arka plan", required=False)
    logo = forms.ImageField(label="Logo / İkon", required=False)

# Formun her alanına uygun CSS sınıflarını ekleyerek Bootstrap ile uyumlu hale getirir ve kullanıcı deneyimini iyileştirir.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Arayüz tutarlılığı için alan bazlı CSS sınıf eşleşmeleri.
        field_classes = {
            "data_type": "form-select",
            "output_format": "form-select",
            "url": "form-control",
            "wifi_ssid": "form-control",
            "wifi_password": "form-control",
            "wifi_encryption": "form-select",
            "vcard_first_name": "form-control",
            "vcard_last_name": "form-control",
            "vcard_phone": "form-control",
            "vcard_email": "form-control",
            "vcard_org": "form-control",
            "vcard_title": "form-control",
            "vcard_website": "form-control",
            "crypto_type": "form-select",
            "crypto_address": "form-control",
            "crypto_label": "form-control",
            "crypto_amount": "form-control",
            "primary_color": "form-control form-control-color",
            "secondary_color": "form-control form-control-color",
            "use_gradient": "form-check-input",
            "transparent_bg": "form-check-input",
            "logo": "file-picker__input",
        }

        # Her alan için tanımlanan CSS sınıfları widget'lara eklenir.
        for field_name, css_class in field_classes.items():
            widget = self.fields[field_name].widget
            existing_class = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing_class} {css_class}".strip()

        # Kullanıcı deneyimini iyileştiren örnek metin ve input özellikleri.
        self.fields["url"].widget.attrs.update({"placeholder": "https://example.com"})
        self.fields["wifi_ssid"].widget.attrs.update({"placeholder": "SSID"})
        self.fields["wifi_password"].widget.attrs.update({"placeholder": "Wi-Fi şifresi"})
        self.fields["crypto_address"].widget.attrs.update({"placeholder": "Adres veya IBAN"})
        self.fields["crypto_label"].widget.attrs.update({"placeholder": "Etiket"})
        self.fields["crypto_amount"].widget.attrs.update({"placeholder": "0.00"})
        self.fields["logo"].widget.attrs.update({"accept": "image/*"})
        self.fields["primary_color"].widget.attrs["type"] = "color"
        self.fields["secondary_color"].widget.attrs["type"] = "color"

    def clean(self):
        cleaned = super().clean()
        data_type = cleaned.get("data_type")
        errors_found = False

        if data_type == "url":
            if not cleaned.get("url"):
                self.add_error("url", "URL alanı gereklidir.")
                errors_found = True

        elif data_type == "wifi":
            if not cleaned.get("wifi_ssid"):
                self.add_error("wifi_ssid", "Wi‑Fi adı (SSID) gereklidir.")
                errors_found = True
            enc = cleaned.get("wifi_encryption")
            if enc and enc != "nopass" and not cleaned.get("wifi_password"):
                self.add_error("wifi_password", "Seçilen şifreleme için parola gereklidir.")
                errors_found = True

        elif data_type == "vcard":
            if not (cleaned.get("vcard_first_name") or cleaned.get("vcard_last_name")):
                self.add_error("vcard_first_name", "Ad veya soyad girilmelidir.")
                errors_found = True

        elif data_type == "crypto":
            if not cleaned.get("crypto_address"):
                self.add_error("crypto_address", "Adres veya IBAN gereklidir.")
                errors_found = True

        if errors_found:
            raise forms.ValidationError("Lütfen gerekli alanları doldurun.")

        return cleaned


class QRScanForm(forms.Form):
    # QR çözümleme için kullanıcıdan görsel dosyası alınır.
    image = forms.FileField(label="QR Görseli")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["image"].widget.attrs.update({
            "class": "form-control",
            "accept": "image/*,.svg",
        })