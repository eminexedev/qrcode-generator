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


class QRScanForm(forms.Form):
    image = forms.ImageField(label="QR Görseli")