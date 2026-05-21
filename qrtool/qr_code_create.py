import base64
import io
import re
import math
from typing import Sequence, Any, cast
import segno
from PIL import Image, ImageColor, ImageDraw, ImageOps

# QR kodu oluşturma ve renderlama işlemi yapan fonksiyonlar
def _interpolate_color(start: Sequence[int], end: Sequence[int], ratio: float) -> tuple[int, int, int]:
    s0 = int(start[0]) if len(start) > 0 else 0
    s1 = int(start[1]) if len(start) > 1 else 0
    s2 = int(start[2]) if len(start) > 2 else 0
    e0 = int(end[0]) if len(end) > 0 else 0
    e1 = int(end[1]) if len(end) > 1 else 0
    e2 = int(end[2]) if len(end) > 2 else 0
    s = (s0, s1, s2)
    e = (e0, e1, e2)
    return (int(s[0] + (e[0] - s[0]) * ratio), int(s[1] + (e[1] - s[1]) * ratio), int(s[2] + (e[2] - s[2]) * ratio))

# Verilen payloada göre QR kodu matrisi oluşturma
def _coerce_rgb_color(value: str, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    try:
        rgb = ImageColor.getrgb(value)
        r = int(rgb[0]) if len(rgb) > 0 else fallback[0]
        g = int(rgb[1]) if len(rgb) > 1 else fallback[1]
        b = int(rgb[2]) if len(rgb) > 2 else fallback[2]
        return (r, g, b)
    except Exception:
        return fallback

# QR kodunu PNG/GIF formatında renderlama
def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

# QR kodunu SVG formatında renderlama
def _make_qr_matrix(payload: str):
    return segno.make(payload, error="h")

# SVG içindeki QR koduna logo ekleme işlemi
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
    frame_count = 12 if animated else 1
    frames: list[Image.Image] = []

    start_rgb = _coerce_rgb_color(primary_color, (17, 17, 17))
    end_rgb = _coerce_rgb_color(secondary_color, (37, 99, 235))
    bg_rgba = (255, 255, 255, 0) if transparent_bg else (255, 255, 255, 255)

    logo_image = None
    if logo_file:
        logo_image = Image.open(logo_file).convert("RGBA")

# Her kare için QR kodunu çizerek animasyonlu GIF oluşturma veya tek kareli PNG oluşturma
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
                    if animated and frame_count > 1:
                        t = frame_index / frame_count
                        ease = (1 - math.cos(t * math.pi * 2)) / 2
                        offset = int(ease * pulse)
                    else:
                        offset = 0
                    fill_rgb = tuple(max(0, min(255, component - offset)) for component in start_rgb)

                draw.rectangle([x1, y1, x2, y2], fill=fill_rgb + (255,))

# Logo ekleme işlemi: Logonun boyutunu QR kodunun %22'si kadar yaparak ortalayarak yerleştirir.
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

# Her kare için QR kodunu çizerek animasyonlu GIF oluşturma veya 
# tek kareli PNG oluşturma: Logonun boyutunu QR kodunun %22'si kadar yaparak ortalayarak yerleştirir ve her karede renklerde hafif bir animasyon efekti uygular.
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

# SVG içindeki QR koduna logo ekleme işlemi: 
# SVG'yi XML olarak işleyerek logo görselini base64 formatında ekler 
# ve logonun boyutunu QR kodunun %22'si kadar yaparak ortalayarak yerleştirir.
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

# Her kare için QR kodunu çizerek animasyonlu GIF oluşturma veya tek kareli PNG oluşturma: 
# Logonun boyutunu QR kodunun %22'si kadar yaparak ortalayarak yerleştirir ve her karede renklerde hafif bir animasyon efekti uygular.
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

# Her kare için QR kodunu çizerek animasyonlu GIF oluşturma veya tek kareli PNG oluşturma: 
# Logonun boyutunu QR kodunun %22'si kadar yaparak ortalayarak yerleştirir ve her karede renklerde hafif bir animasyon efekti uygular.
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


# Her kare için QR kodunu çizerek animasyonlu GIF oluşturma veya tek kareli PNG oluşturma: 
# Logonun boyutunu QR kodunun %22'si kadar yaparak ortalayarak yerleştirir ve her karede renklerde hafif bir animasyon efekti uygular.
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

# SVG içindeki QR koduna logo ekleme işlemi: 
# SVG'yi XML olarak işleyerek logo görselini base64 formatında ekler ve logonun boyutunu QR kodunun %22'si kadar yaparak ortalayarak yerleştirir.
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

# SVG içindeki QR koduna logo ekleme işlemi: 
# SVG'yi XML olarak işleyerek logo görselini base64 formatında ekler ve logonun boyutunu QR kodunun %22'si kadar yaparak ortalayarak yerleştirir.
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


# Verilen payloada göre QR kodu matrisi oluşturma: 
# segno kütüphanesi kullanarak QR kodu matrisi oluşturur ve hata düzeltme seviyesini "h" olarak ayarlar.
def _make_data_uri(binary: bytes, mime_type: str) -> str:
    encoded = base64.b64encode(binary).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"
