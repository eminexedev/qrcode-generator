import base64
from typing import Any, cast
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .forms import QRBuildForm, QRScanForm
from .payloads import build_wifi_payload, build_vcard_payload, build_crypto_payload
from .security import security_scan_url, is_http_url, SecurityResult
from .qr_code_create import _make_qr_matrix, _render_png_or_gif, _render_svg, _make_data_uri
from .decoders import _decode_qr_image


def index(request: HttpRequest) -> HttpResponse:
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
                safe=True, status_label="Güvenli", reasons=[], final_url=None
            )

            qr_obj = _make_qr_matrix(payload)
            logo_file = request.FILES.get("logo")
            transparent_bg = bool(qr_form.cleaned_data["transparent_bg"])
            use_gradient = bool(qr_form.cleaned_data["use_gradient"])
            qr_svg = None

            if output_format == "svg":
                rendered = _render_svg(
                    qr_obj, qr_form.cleaned_data["primary_color"], transparent_bg, logo_file
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
            context["qr_form"] = QRBuildForm()

        elif action == "scan":
            uploaded_file = request.FILES.get("qr_image") or request.FILES.get("image")

            if uploaded_file is None:
                context.update({"scan_result": True, "scan_error": "QR kod okunamadı"})
            else:
                decode_result = _decode_qr_image(uploaded_file)

                if decode_result is None:
                    context.update({"scan_result": True, "active_tab": "scanner", "scan_error": "QR kod okunamadı"})
                else:
                    decoded_text = decode_result.text
                    security_result = security_scan_url(decoded_text) if is_http_url(decoded_text) else SecurityResult(
                        safe=True, status_label="Güvenli", reasons=[], final_url=None
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
