import base64
import io
import ipaddress
import re
from dataclasses import dataclass
from typing import Any, Sequence, Tuple, cast
from urllib.parse import quote, urlparse

import cv2
import numpy as np
import requests
import segno
import math
from PIL import Image, ImageColor, ImageDraw, ImageOps
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from pyzbar.pyzbar import decode as pyzbar_decode

from .forms import QRBuildForm, QRScanForm


# Örnek kara liste: gerçek projede harici tehdit istihbaratı ile genişletilmelidir.
SUSPICIOUS_DOMAINS = {
    "paypa1.com",
    "secure-login.example",
    "bitly.example",
    "phishing.test",
}

PHISHING_PATTERN = re.compile(
    r"(@|xn--|%[0-9a-fA-F]{2}|https?://[^/]+@|\b(?:login|verify|update|secure|account)\b)",
    re.IGNORECASE,
)


@dataclass
class SecurityResult:
    safe: bool
    status_label: str
    reasons: list[str]
    final_url: str | None = None


@dataclass
class QRDecodeResult:
    text: str
    barcode_type: str
    filter_name: str


def build_wifi_payload(ssid: str, password: str, encryption: str) -> str:
    # Wi-Fi QR standardında özel karakterleri kaçışlayarak payload(veri) üretir.
    ssid_escaped = ssid.replace("\\", "\\\\").replace(";", r"\;").replace(",", r"\,")
    password_escaped = password.replace("\\", "\\\\").replace(";", r"\;").replace(",", r"\,")
    return f"WIFI:T:{encryption};S:{ssid_escaped};P:{password_escaped};;"

# VCard formatında QR kodu için payload oluşturur; alanları isteğe bağlı olarak ekler.
def build_vcard_payload(data: dict[str, str]) -> str:
    # VCard 3.0 formatında satır tabanlı içerik oluşturur.
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"N:{data.get('last_name', '')};{data.get('first_name', '')};;;",
        f"FN:{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
    ]
    if data.get("org"):
        lines.append(f"ORG:{data['org']}")
    if data.get("title"):
        lines.append(f"TITLE:{data['title']}")
    if data.get("phone"):
        lines.append(f"TEL;TYPE=CELL:{data['phone']}")
    if data.get("email"):
        lines.append(f"EMAIL:{data['email']}")
    if data.get("website"):
        lines.append(f"URL:{data['website']}")
    lines.append("END:VCARD")
    return "\n".join(lines)

# Kripto cüzdanları için URI şeması oluşturur; IBAN için sade format, kripto için query parametreli şema kullanılır.
def build_crypto_payload(wallet_type: str, address: str, label: str, amount: str) -> str:
    # IBAN için sade format, kripto için query parametreli şema kullanılır.
    if wallet_type == "iban":
        iban = re.sub(r"\s+", "", address.upper())
        return f"IBAN:{iban}"
# Kripto para adresleri için URI şeması oluşturur; etiket ve tutar gibi isteğe bağlı bilgileri query parametreleri olarak ekler.
    query_parts: list[str] = []
    if label:
        query_parts.append(f"label={quote(label)}") # Etiket bilgisi URL kodlamasıyla güvenli hale getirilir.
    if amount:
        query_parts.append(f"amount={quote(amount)}")
    query = f"?{'&'.join(query_parts)}" if query_parts else "" 
    return f"crypto:{address}{query}"


def is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

# Temel güvenlik kuralları ile URL üzerinde hızlı risk analizi yapar.
def security_scan_url(url: str) -> SecurityResult:
    # Temel güvenlik kuralları ile URL üzerinde hızlı risk analizi yapar.
    reasons: list[str] = []
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()

# Şüpheli kalıplar, karakterler veya kelimeler içerip içermediğini kontrol eder.
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

# QR çözümleme için dosya yüklemesi yapıldığında,
# farklı ön işleme teknikleri uygulayarak pyzbar ile çözümlemeyi dener.
def _interpolate_color(start: Sequence[int], end: Sequence[int], ratio: float) -> tuple[int, int, int]:
    s0 = int(start[0]) if len(start) > 0 else 0
    s1 = int(start[1]) if len(start) > 1 else 0
    s2 = int(start[2]) if len(start) > 2 else 0
    e0 = int(end[0]) if len(end) > 0 else 0
    e1 = int(end[1]) if len(end) > 1 else 0
    e2 = int(end[2]) if len(end) > 2 else 0
    s: tuple[int, int, int] = (s0, s1, s2)
    e: tuple[int, int, int] = (e0, e1, e2)
    return (int(s[0] + (e[0] - s[0]) * ratio), int(s[1] + (e[1] - s[1]) * ratio), int(s[2] + (e[2] - s[2]) * ratio))

# RGB renk değerlerini çeşitli formatlardan (hex, renk isimleri vb.) kabul ederek tutarlı bir şekilde işleyebilmek için yardımcı fonksiyonlar sağlar.
def _coerce_rgb_color(value: str, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    try:
        rgb = ImageColor.getrgb(value)
        r = int(rgb[0]) if len(rgb) > 0 else fallback[0]
        g = int(rgb[1]) if len(rgb) > 1 else fallback[1]
        b = int(rgb[2]) if len(rgb) > 2 else fallback[2]
        return (r, g, b)
    except Exception:
        return fallback


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def _make_qr_matrix(payload: str):
    # Segno ile yüksek hata düzeltmeli QR matrisini üretir.
    return segno.make(payload, error="h")

# PNG/GIF çıktısını piksel bazlı çizimle üretir; gradient ve logo desteği içerir.
def _render_png_or_gif(
    qr_obj,
    primary_color: str,
    secondary_color: str,
    use_gradient: bool,
    transparent_bg: bool,
    logo_file,
    animated: bool,
) -> bytes:
    # PNG/GIF çıktısını piksel bazlı çizimle üretir; gradient ve logo desteği içerir.
    scale = 14
    border = 4
    modules = qr_obj.matrix
    size = len(modules)
    total = (size + border * 2) * scale
    frame_count = 12 if animated else 1
    frames: list[Image.Image] = []

    start_rgb = _coerce_rgb_color(primary_color, (17, 17, 17))
    end_rgb = _coerce_rgb_color(secondary_color, (37, 99, 235))
    bg_rgba = (255, 255, 255, 0) if transparent_bg else (255, 255, 255, 255)

    logo_image = None
    if logo_file:
        logo_image = Image.open(logo_file).convert("RGBA")

# Animasyonlu GIF için her karede modüllerin rengini hafifçe değiştirerek hareket efekti yaratır; 
# gradient seçeneği varsa renkler arasında geçiş yapar.
    for frame_index in range(frame_count):
        image = Image.new("RGBA", (total, total), bg_rgba)
        draw = ImageDraw.Draw(image)

        for row_index, row in enumerate(modules):
            for col_index, is_dark in enumerate(row):
                if not is_dark:
                    continue

                x1 = (col_index + border) * scale
                y1 = (row_index + border) * scale
                x2 = x1 + scale
                y2 = y1 + scale

                if use_gradient:
                    gradient_ratio = (row_index + frame_index * 0.2) / max(size - 1, 1)
                    fill_rgb = _interpolate_color(start_rgb, end_rgb, gradient_ratio)
                else:
                    pulse = 28 if animated else 0
                    # Daha yumuşak bir hareket için kosinüs tabanlı easing kullanıyoruz
                    if animated and frame_count > 1:
                        t = frame_index / frame_count
                        ease = (1 - math.cos(t * math.pi * 2)) / 2
                        offset = int(ease * pulse)
                    else:
                        offset = 0
                    fill_rgb = tuple(max(0, min(255, component - offset)) for component in start_rgb)

                draw.rectangle([x1, y1, x2, y2], fill=fill_rgb + (255,))

        if logo_image:
            logo_size = int(total * 0.22)
            logo = ImageOps.contain(logo_image, (logo_size, logo_size))
            if not transparent_bg:
                shield = Image.new("RGBA", (logo.width + 24, logo.height + 24), (255, 255, 255, 255))
                image.alpha_composite(shield, ((total - shield.width) // 2, (total - shield.height) // 2))
            image.alpha_composite(logo, ((total - logo.width) // 2, (total - logo.height) // 2))

        if animated:
            frames.append(image.convert("P", palette=Image.Palette.ADAPTIVE))
        else:
            frames.append(image)

# PIL'in optimize edilmiş GIF kaydetme yeteneklerini kullanarak animasyonlu GIF'i oluşturur; 
# tek kareli PNG için doğrudan kaydeder.
    output = io.BytesIO()
    if animated:
        frames[0].save(
            output,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=100,
            loop=0,
            optimize=True,
            disposal=2,
        )
    else:
        frames[0].save(output, format="PNG")

    return output.getvalue()

# SVG çıktısına logo eklemek için XML manipülasyonu yapar; 
# logo dosyasını base64 ile gömülü hale getirir.
def _inject_logo_into_svg(svg_text: str, logo_file, qr_size: int = 1000) -> str:
    # SVG içine gömülü (base64) logo ekler.
    if not logo_file:
        return svg_text

    import xml.etree.ElementTree as ET

    svg_file = io.BytesIO(svg_text.encode("utf-8"))
    tree = ET.parse(svg_file)
    root = tree.getroot()

    logo_bytes = logo_file.read()
    logo_b64 = base64.b64encode(logo_bytes).decode("ascii")
    logo_href = f"data:{logo_file.content_type};base64,{logo_b64}"

    ET.register_namespace("", "http://www.w3.org/2000/svg")

    center_size = int(qr_size * 0.22)
    x_pos = (qr_size - center_size) // 2
    y_pos = (qr_size - center_size) // 2

    background = ET.Element(
        "{http://www.w3.org/2000/svg}rect",
        {
            "x": str(x_pos - 8),
            "y": str(y_pos - 8),
            "width": str(center_size + 16),
            "height": str(center_size + 16),
            "rx": "18",
            "fill": "#ffffff",
            "fill-opacity": "0.95",
        },
    )
    image = ET.Element(
        "{http://www.w3.org/2000/svg}image",
        {
            "x": str(x_pos),
            "y": str(y_pos),
            "width": str(center_size),
            "height": str(center_size),
            "href": logo_href,
            "preserveAspectRatio": "xMidYMid meet",
        },
    )

    root.append(background)
    root.append(image)
    return ET.tostring(root, encoding="unicode")

# SVG formatında vektörel çıktı üretir.
def _render_svg(qr_obj, primary_color: str, transparent_bg: bool, logo_file) -> bytes:
    dark_rgb = _coerce_rgb_color(primary_color, (17, 17, 17))
    output = io.BytesIO()
    qr_obj.save(
        output,
        kind="svg",
        xmldecl=True,
        scale=12,
        border=4,
        dark=_rgb_to_hex(dark_rgb),
        light=None if transparent_bg else "#ffffff",
    )
    svg_text = output.getvalue().decode("utf-8")
    if logo_file:
        svg_text = _inject_logo_into_svg(svg_text, logo_file)
    return svg_text.encode("utf-8")

# hem QR kod üretimi hem de görsel tabanlı çözümleme işlemlerini yönetir.
def _svg_bytes_to_png_bytes(svg_bytes: bytes) -> bytes:
    try:
        import importlib

        fitz = cast(Any, importlib.import_module("fitz"))

        document = fitz.open(stream=svg_bytes, filetype="svg")
        page = document.load_page(0)
        pixmap = page.get_pixmap(matrix=fitz.Matrix(4, 4), alpha=False)
        return pixmap.tobytes("png")
    except Exception:
        pass

        return b""

# Segno'nun SVG çıktısındaki path verisini basitçe rasterize ederek PNG elde etmeye çalışır;
def _segno_svg_bytes_to_png_bytes(svg_bytes: bytes) -> bytes:
    import xml.etree.ElementTree as ET

    root = ET.fromstring(svg_bytes)
    width = int(float(root.attrib.get("width", "0")))
    height = int(float(root.attrib.get("height", "0")))
    if width <= 0 or height <= 0:
        return b""

    image = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    draw = ImageDraw.Draw(image)
    drew_anything = False

    def parse_number(value: str) -> float:
        match = re.match(r"-?\d+(?:\.\d+)?", value)
        return float(match.group(0)) if match else 0.0

    def draw_segment(start_x: float, start_y: float, length: float, scale: float) -> None:
        nonlocal drew_anything
        x0 = int(round(start_x * scale))
        y0 = int(round(start_y * scale))
        x1 = int(round((start_x + length) * scale))
        y1 = int(round((start_y + 1.0) * scale))
        left = min(x0, x1)
        right = max(x0, x1)
        top = min(y0, y1)
        bottom = max(y0, y1)
        if right <= left or bottom <= top:
            return
        draw.rectangle([left, top, right, bottom], fill=(0, 0, 0, 255))
        drew_anything = True

    for element in root.iter():
        if not element.tag.endswith("path"):
            continue

        path_data = element.attrib.get("d", "")
        transform = element.attrib.get("transform", "")
        scale_match = re.search(r"scale\(([-\d.]+)\)", transform)
        scale = float(scale_match.group(1)) if scale_match else 1.0

        tokens = re.findall(r"[MmHhVv]|-?\d+(?:\.\d+)?", path_data)
        index = 0
        current_x = 0.0
        current_y = 0.0

        while index < len(tokens):
            token = tokens[index]
            index += 1

            if token == "M":
                current_x = parse_number(tokens[index])
                current_y = parse_number(tokens[index + 1])
                index += 2
                if current_y.is_integer() and current_y % 1 == 0 and current_y > 0:
                    current_y -= 0.5
                continue

            if token == "m":
                current_x += parse_number(tokens[index])
                current_y += parse_number(tokens[index + 1])
                index += 2
                continue

            if token == "h":
                length = parse_number(tokens[index])
                index += 1
                draw_segment(current_x, current_y, length, scale)
                current_x += length
                continue

            if token == "v":
                current_y += parse_number(tokens[index])
                index += 1

    if not drew_anything:
        return b""

    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _decode_qr_image(uploaded_file) -> QRDecodeResult | None:
    # Dosyayı RAM'de oku; diske yazmadan OpenCV ile işlenecek ham byte dizisini hazırla.
    raw_bytes = uploaded_file.read()

    image_sources = [raw_bytes]
    if uploaded_file.name.lower().endswith(".svg") or getattr(uploaded_file, "content_type", "") == "image/svg+xml":
        # SVG yüklemelerinde önce PNG'ye dönüştürüp aynı ön işleme hattını uygula.
        fitz_png_bytes = _svg_bytes_to_png_bytes(raw_bytes)
        if fitz_png_bytes:
            image_sources.insert(0, fitz_png_bytes)

        segno_png_bytes = _segno_svg_bytes_to_png_bytes(raw_bytes)
        if segno_png_bytes:
            image_sources.insert(0, segno_png_bytes)

    def iter_preprocessed_images(color_image: np.ndarray):
        # QR çözümleme için sırayla denenmesi istenen dört varyasyonu üret.
        grayscale_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
        _, binary_image = cv2.threshold(grayscale_image, 127, 255, cv2.THRESH_BINARY)
        _, otsu_image = cv2.threshold(grayscale_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return [
            ("Orijinal Hali", color_image),
            ("Gri Tonlama", grayscale_image),
            ("Kesin Siyah/Beyaz", binary_image),
            ("Dinamik Işık Dengesi", otsu_image),
        ]

    def decode_with_pyzbar(image_array: np.ndarray, filter_name: str) -> QRDecodeResult | None:
        # pyzbar sonuçları arasında yalnızca QR kodu kabul et.
        decoded_items = pyzbar_decode(image_array)
        for item in decoded_items:
            barcode_type = item.type or "QR_CODE"
            if barcode_type.upper() != "QRCODE":
                continue

            try:
                text = item.data.decode("utf-8").strip()
            except UnicodeDecodeError:
                text = item.data.decode("utf-8", errors="replace").strip()

            if text:
                return QRDecodeResult(
                    text=text,
                    barcode_type=barcode_type,
                    filter_name=filter_name,
                )

        return None
    
# Birden fazla görsel kaynağı varsa sırayla dene; her kaynak için farklı ön işleme filtreleri uygula ve pyzbar ile çözümlemeyi dene.
    for source_bytes in image_sources:
        image_bytes = np.frombuffer(source_bytes, np.uint8)
        image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
        if image is None:
            continue

        image_array: np.ndarray = cast(np.ndarray, image)
        for filter_name, candidate_image in iter_preprocessed_images(image_array):
            decode_result = decode_with_pyzbar(candidate_image, filter_name)
            if decode_result:
                return decode_result

    return None

# Görsel baytlarını HTML'de kullanılabilir data URI biçimine çevirir.
def _make_data_uri(binary: bytes, mime_type: str) -> str:
    # Görsel baytlarını HTML'de kullanılabilir data URI biçimine çevirir.
    encoded = base64.b64encode(binary).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"

# Ana view: hem QR kod üretimi hem de görsel tabanlı çözümleme işlemlerini yönetir.
def index(request: HttpRequest) -> HttpResponse:
    # Hem üretim hem çözümleme işlemlerini yöneten ana view.
    qr_form = QRBuildForm(request.POST or None, request.FILES or None)
    scan_form = QRScanForm(request.POST or None, request.FILES or None)

    context: dict[str, Any] = {
        "qr_form": qr_form,
        "scan_form": scan_form,
        "generated": False,
        "scan_result": None,
        "active_tab": "generator",
        "security_result": None,
        "qr_data_uri": None,
        "qr_svg": None,
        "download_name": None,
        "decoded_text": None,
    }

# POST isteği geldiğinde hangi işlemin yapılacağını belirlemek için gizli "action" alanını kontrol eder.
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "generate" and qr_form.is_valid():
            # Kullanıcı seçimine göre QR payload'ı hazırlanır.
            data_type = qr_form.cleaned_data["data_type"]
            output_format = qr_form.cleaned_data["output_format"]
            payload = ""

            if data_type == "url":
                payload = qr_form.cleaned_data["url"]
            elif data_type == "wifi":
                payload = build_wifi_payload(
                    qr_form.cleaned_data["wifi_ssid"],
                    qr_form.cleaned_data["wifi_password"],
                    qr_form.cleaned_data["wifi_encryption"],
                )
            elif data_type == "vcard":
                payload = build_vcard_payload(
                    {
                        "first_name": qr_form.cleaned_data["vcard_first_name"],
                        "last_name": qr_form.cleaned_data["vcard_last_name"],
                        "phone": qr_form.cleaned_data["vcard_phone"],
                        "email": qr_form.cleaned_data["vcard_email"],
                        "org": qr_form.cleaned_data["vcard_org"],
                        "title": qr_form.cleaned_data["vcard_title"],
                        "website": qr_form.cleaned_data["vcard_website"],
                    }
                )
            else:
                payload = build_crypto_payload(
                    qr_form.cleaned_data["crypto_type"] or "crypto",
                    qr_form.cleaned_data["crypto_address"],
                    qr_form.cleaned_data["crypto_label"],
                    qr_form.cleaned_data["crypto_amount"],
                )

            security_result = security_scan_url(payload) if is_http_url(payload) else SecurityResult(
                safe=True,
                status_label="Güvenli",
                reasons=[],
                final_url=None,
            )

            qr_obj = _make_qr_matrix(payload)
            logo_file = request.FILES.get("logo")
            transparent_bg = bool(qr_form.cleaned_data["transparent_bg"])
            use_gradient = bool(qr_form.cleaned_data["use_gradient"])
            qr_svg = None

            if output_format == "svg":
                # SVG çıktı ayrıca ham metin olarak önizlemeye gönderilir.
                rendered = _render_svg(
                    qr_obj,
                    qr_form.cleaned_data["primary_color"],
                    transparent_bg,
                    logo_file,
                )
                mime_type = "image/svg+xml"
                download_name = "qr_code.svg"
                qr_data_uri = _make_data_uri(rendered, mime_type)
                qr_svg = rendered.decode("utf-8")
            else:
                rendered = _render_png_or_gif(
                    qr_obj,
                    qr_form.cleaned_data["primary_color"],
                    qr_form.cleaned_data["secondary_color"],
                    use_gradient,
                    transparent_bg,
                    logo_file,
                    animated=output_format == "gif",
                )
                mime_type = "image/gif" if output_format == "gif" else "image/png"
                download_name = f"qr_code.{output_format}"
                qr_data_uri = _make_data_uri(rendered, mime_type)

            context.update(
                {
                    "generated": True,
                    "active_tab": "generator",
                    "security_result": security_result,
                    "qr_data_uri": qr_data_uri,
                    "qr_svg": qr_svg,
                    "download_name": download_name,
                    "payload": payload,
                }
            )
            # Formu temizleyerek yeni bir QR oluşturma deneyimi sunar.
            context["qr_form"] = QRBuildForm()

        elif action == "scan":
            # Yeni anahtar adı olan qr_image'i önce dene; eski form alanı image ile geriye dönük uyumluluk sağla.
            uploaded_file = request.FILES.get("qr_image") or request.FILES.get("image")

            if uploaded_file is None:
                context.update(
                    {
                        "scan_result": True,
                        "scan_error": "QR kod okunamadı",
                    }
                )
            else:
                decode_result = _decode_qr_image(uploaded_file)

                if decode_result is None:
                    context.update(
                        {
                            "scan_result": True,
                            "active_tab": "scanner",
                            "scan_error": "QR kod okunamadı",
                        }
                    )
                else:
                    decoded_text = decode_result.text
                    security_result = security_scan_url(decoded_text) if is_http_url(decoded_text) else SecurityResult(
                        safe=True,
                        status_label="Güvenli",
                        reasons=[],
                        final_url=None,
                    )
                    context.update(
                        {
                            "scan_result": True,
                            "active_tab": "scanner",
                            "decoded_text": decoded_text,
                            "decoded_type": decode_result.barcode_type,
                            "used_filter": decode_result.filter_name,
                            "security_result": security_result,
                        }
                    )

    return render(request, "qrtool/index.html", context)