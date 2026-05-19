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
from PIL import Image, ImageColor, ImageDraw, ImageOps
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .forms import QRBuildForm, QRScanForm


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


def build_wifi_payload(ssid: str, password: str, encryption: str) -> str:
    ssid_escaped = ssid.replace("\\", "\\\\").replace(";", r"\;").replace(",", r"\,")
    password_escaped = password.replace("\\", "\\\\").replace(";", r"\;").replace(",", r"\,")
    return f"WIFI:T:{encryption};S:{ssid_escaped};P:{password_escaped};;"


def build_vcard_payload(data: dict[str, str]) -> str:
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


def is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


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


def _interpolate_color(start: Sequence[int], end: Sequence[int], ratio: float) -> tuple[int, int, int]:
    # Accept RGB or RGBA tuples; only interpolate RGB channels
    s: tuple[int, int, int] = tuple(start[:3])  # type: ignore[arg-type]
    e: tuple[int, int, int] = tuple(end[:3])  # type: ignore[arg-type]
    return tuple(int(s[i] + (e[i] - s[i]) * ratio) for i in range(3))


def _make_qr_matrix(payload: str):
    return segno.make(payload, error="h")


def _render_png_or_gif(
    qr_obj,
    primary_color: str,
    secondary_color: str,
    use_gradient: bool,
    transparent_bg: bool,
    logo_file,
    animated: bool,
) -> bytes:
    scale = 14
    border = 4
    modules = qr_obj.matrix
    size = len(modules)
    total = (size + border * 2) * scale
    frame_count = 8 if animated else 1
    frames: list[Image.Image] = []

    start_rgb_full = ImageColor.getrgb(primary_color)
    end_rgb_full = ImageColor.getrgb(secondary_color)
    # Ensure we work with RGB triples (ImageColor may return RGB or RGBA)
    start_rgb = tuple(start_rgb_full[:3])
    end_rgb = tuple(end_rgb_full[:3])
    bg_rgba = (255, 255, 255, 0) if transparent_bg else (255, 255, 255, 255)

    logo_image = None
    if logo_file:
        logo_image = Image.open(logo_file).convert("RGBA")

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
                    pulse = 20 if animated else 0
                    offset = int((frame_index % frame_count) * pulse / max(frame_count - 1, 1)) if animated else 0
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

    output = io.BytesIO()
    if animated:
        frames[0].save(
            output,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=120,
            loop=0,
            optimize=False,
            disposal=2,
        )
    else:
        frames[0].save(output, format="PNG")

    return output.getvalue()


def _inject_logo_into_svg(svg_text: str, logo_file, qr_size: int = 1000) -> str:
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


def _render_svg(qr_obj, primary_color: str, transparent_bg: bool, logo_file) -> bytes:
    output = io.StringIO()
    qr_obj.save(
        output,
        kind="svg",
        xmldecl=True,
        scale=12,
        border=4,
        dark=primary_color,
        light=None if transparent_bg else "#ffffff",
    )
    svg_text = output.getvalue()
    if logo_file:
        svg_text = _inject_logo_into_svg(svg_text, logo_file)
    return svg_text.encode("utf-8")


def _decode_qr_image(uploaded_file) -> str:
    image_bytes = np.frombuffer(uploaded_file.read(), np.uint8)
    image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
    if image is None:
        return ""
    # Help the type-checker: imdecode returns ndarray on success
    image_array: np.ndarray = cast(np.ndarray, image)
    detector = cv2.QRCodeDetector()
    decoded_text, _, _ = detector.detectAndDecode(image_array)
    return decoded_text.strip()


def _make_data_uri(binary: bytes, mime_type: str) -> str:
    encoded = base64.b64encode(binary).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def index(request: HttpRequest) -> HttpResponse:
    qr_form = QRBuildForm(request.POST or None, request.FILES or None)
    scan_form = QRScanForm(request.POST or None, request.FILES or None)

    context: dict[str, Any] = {
        "qr_form": qr_form,
        "scan_form": scan_form,
        "generated": False,
        "scan_result": None,
        "security_result": None,
        "qr_data_uri": None,
        "qr_svg": None,
        "download_name": None,
        "decoded_text": None,
    }

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "generate" and qr_form.is_valid():
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
                    "security_result": security_result,
                    "qr_data_uri": qr_data_uri,
                    "qr_svg": qr_svg,
                    "download_name": download_name,
                    "payload": payload,
                }
            )

        elif action == "scan" and scan_form.is_valid():
            decoded_text = _decode_qr_image(scan_form.cleaned_data["image"])
            security_result = security_scan_url(decoded_text) if is_http_url(decoded_text) else SecurityResult(
                safe=True,
                status_label="Güvenli",
                reasons=[],
                final_url=None,
            )
            context.update(
                {
                    "scan_result": True,
                    "decoded_text": decoded_text,
                    "security_result": security_result,
                }
            )

    return render(request, "qrtool/index.html", context)