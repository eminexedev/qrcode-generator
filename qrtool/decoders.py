from dataclasses import dataclass
from typing import Any, cast
import re
import io

import cv2
import numpy as np
from pyzbar.pyzbar import decode as pyzbar_decode

from .qr_code_create import _svg_bytes_to_png_bytes, _segno_svg_bytes_to_png_bytes

# QR kodu çözme işlemi için yardımcı fonksiyonlar ve veri sınıfları.
@dataclass
class QRDecodeResult:
    text: str
    barcode_type: str
    filter_name: str

# Yüklenen görseldeki QR kodunu çözmeye çalışır.
# SVG dosyaları için özel ön işlemler yapar ve farklı filtreler uygulayarak çözümleme şansını artırır.
def _decode_qr_image(uploaded_file) -> QRDecodeResult | None:
    raw_bytes = uploaded_file.read()

    image_sources = [raw_bytes]
    if uploaded_file.name.lower().endswith(".svg") or getattr(uploaded_file, "content_type", "") == "image/svg+xml":
        fitz_png_bytes = _svg_bytes_to_png_bytes(raw_bytes)
        if fitz_png_bytes:
            image_sources.insert(0, fitz_png_bytes)

        segno_png_bytes = _segno_svg_bytes_to_png_bytes(raw_bytes)
        if segno_png_bytes:
            image_sources.insert(0, segno_png_bytes)

# Görsel üzerinde farklı ön işlemler uygulayarak QR kodunu çözmeye çalışır.
    def iter_preprocessed_images(color_image: np.ndarray):
        grayscale_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
        _, binary_image = cv2.threshold(grayscale_image, 127, 255, cv2.THRESH_BINARY)
        _, otsu_image = cv2.threshold(grayscale_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return [
            ("Orijinal Hali", color_image),
            ("Gri Tonlama", grayscale_image),
            ("Kesin Siyah/Beyaz", binary_image),
            ("Dinamik Işık Dengesi", otsu_image),
        ]

# pyzbar kullanarak QR kodunu çözmeye çalışır.
    def decode_with_pyzbar(image_array: np.ndarray, filter_name: str) -> QRDecodeResult | None:
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
                return QRDecodeResult(text=text, barcode_type=barcode_type, filter_name=filter_name)

        return None

# Her görsel kaynağı için farklı ön işlemler uygulayarak QR kod çözme işlemi
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
