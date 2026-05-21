import re
import ipaddress
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse
import requests


# Örnek kara liste: prodda harici tehdit istihbaratı ile genişletilmeli.
SUSPICIOUS_DOMAINS = {
    "paypa1.com",
    "secure-login.example",
    "bitly.example",
    "phishing.test",
}

# Şüpheli kelime ve karakter kalıplarını içeren regex deseni
PHISHING_PATTERN = re.compile(
    r"(@|xn--|%[0-9a-fA-F]{2}|https?://[^/]+@|\b(?:login|verify|update|secure|account)\b)",
    re.IGNORECASE,
)


@dataclass
class SecurityResult:
    safe: bool
    status_label: str
    reasons: list[str]
    final_url: Optional[str] = None


def is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

# Basit güvenlik taraması: regex, kara liste, IP kontrolü, yönlendirme tespiti
def security_scan_url(url: str) -> SecurityResult:
    reasons: list[str] = []
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()

    if PHISHING_PATTERN.search(url):
        reasons.append("Şüpheli kelime veya karakter kalıbı bulundu.")

    if "@" in parsed.netloc:
        reasons.append("Kullanıcı adı / şifre ayracı (@) içeriyor.")

    if hostname.startswith("xn--") or "xn--" in hostname:
        reasons.append("Punycode/homografik alan adı tespit edildi.")

    if hostname in SUSPICIOUS_DOMAINS:
        reasons.append("Alan adı örnek kara listeyle eşleşti.")

    try:
        ipaddress.ip_address(hostname)
        reasons.append("Alan adı yerine IP adresi kullanıyor.")
    except ValueError:
        pass

    if hostname.count(".") >= 4:
        reasons.append("Aşırı alt alan adı zinciri tespit edildi.")

    try:
        response = requests.head(url, allow_redirects=False, timeout=3)
        if 300 <= response.status_code < 400:
            reasons.append("HTTP yönlendirmesi (redirect) tespit edildi.")
        if response.headers.get("Location"):
            reasons.append("Location başlığı ile yönlendirme denemesi bulundu.")
    except requests.RequestException:
        reasons.append("Harici yönlendirme kontrolü tamamlanamadı.")

    safe = len(reasons) == 0
    return SecurityResult(
        safe=safe,
        status_label="Güvenli" if safe else "Şüpheli Link",
        reasons=reasons,
        final_url=url,
    )
