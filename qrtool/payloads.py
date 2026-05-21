from urllib.parse import quote
import re

# QR kodu oluşturmak için farklı veri türlerine uygun payload oluşturma fonksiyonları.
def build_wifi_payload(ssid: str, password: str, encryption: str) -> str:
    ssid_escaped = ssid.replace("\\", "\\\\").replace(";", r"\;").replace(",", r"\,")
    password_escaped = password.replace("\\", "\\\\").replace(";", r"\;").replace(",", r"\,")
    return f"WIFI:T:{encryption};S:{ssid_escaped};P:{password_escaped};;"

# VCard formatında kişi bilgilerini içeren payload oluşturma
def build_vcard_payload(data: dict[str, str]) -> str:
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"N:{data.get('last_name', '')};{data.get('first_name', '')};;;",
        f"FN:{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
    ]
    if data.get("org"):
        lines.append(f"ORG:{data['org']}") # Organizasyon bilgisi ekleme
    if data.get("title"):
        lines.append(f"TITLE:{data['title']}") # Unvan bilgisi ekleme
    if data.get("phone"):
        lines.append(f"TEL;TYPE=CELL:{data['phone']}") # Telefon numarası ekleme
    if data.get("email"):
        lines.append(f"EMAIL:{data['email']}") # E-posta adresi ekleme
    if data.get("website"):
        lines.append(f"URL:{data['website']}") # Web sitesi URL'si ekleme
    lines.append("END:VCARD")
    return "\n".join(lines) # VCard formatında kişi bilgilerini içeren payload oluşturma

# Kripto para adresi veya IBAN bilgisi için gerekli alanlara göre payload oluşturma
def build_crypto_payload(wallet_type: str, address: str, label: str, amount: str) -> str:
    if wallet_type == "iban":
        iban = re.sub(r"\s+", "", address.upper())
        return f"IBAN:{iban}"

    query_parts: list[str] = []
    if label:
        query_parts.append(f"label={quote(label)}")
    if amount:
        query_parts.append(f"amount={quote(amount)}")
    query = f"?{'&'.join(query_parts)}" if query_parts else ""
    return f"crypto:{address}{query}"
