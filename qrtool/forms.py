from django import forms


class QRBuildForm(forms.Form):
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

        for field_name, css_class in field_classes.items():
            widget = self.fields[field_name].widget
            existing_class = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing_class} {css_class}".strip()

        self.fields["url"].widget.attrs.update({"placeholder": "https://example.com"})
        self.fields["wifi_ssid"].widget.attrs.update({"placeholder": "SSID"})
        self.fields["wifi_password"].widget.attrs.update({"placeholder": "Wi-Fi şifresi"})
        self.fields["crypto_address"].widget.attrs.update({"placeholder": "Adres veya IBAN"})
        self.fields["crypto_label"].widget.attrs.update({"placeholder": "Etiket"})
        self.fields["crypto_amount"].widget.attrs.update({"placeholder": "0.00"})
        self.fields["logo"].widget.attrs.update({"accept": "image/*"})
        self.fields["primary_color"].widget.attrs["type"] = "color"
        self.fields["secondary_color"].widget.attrs["type"] = "color"


class QRScanForm(forms.Form):
    image = forms.FileField(label="QR Görseli")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["image"].widget.attrs.update({
            "class": "form-control",
            "accept": "image/*,.svg",
        })