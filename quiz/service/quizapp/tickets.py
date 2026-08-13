"""Раздаточный лист с билетами: QR-коды на A4, режутся ножницами.

Билет анонимен, поэтому лист печатается один раз и раздаётся кому угодно —
сортировать по фамилиям не нужно (docs/adr/0004). Рядом с QR печатается тот же
код словами: телефон может не прочитать код, а ввести восемь символов можно
всегда.
"""

from __future__ import annotations

import io

import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from .store import pretty_token

COLS, ROWS = 3, 4
MARGIN = 12 * mm
QR_SIDE = 38 * mm

# Встроенные шрифты reportlab не покрывают кириллицу. Ищем что-нибудь из
# системных; если ничего нет, подписи печатаются латиницей — код всё равно
# состоит из цифр и заглавных латинских букв.
_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
]


def _register_font() -> str:
    for path in _FONT_CANDIDATES:
        try:
            pdfmetrics.registerFont(TTFont("QuizSans", path))
            return "QuizSans"
        except Exception:  # noqa: BLE001 - шрифта просто нет, это не ошибка
            continue
    return "Helvetica"


def ticket_url(base_url: str, token: str) -> str:
    return f"{base_url.rstrip('/')}/t/{token}"


def _qr_image(data: str) -> ImageReader:
    qr = qrcode.QRCode(box_size=10, border=1, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(data)
    qr.make(fit=True)
    buf = io.BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def build_pdf(*, base_url: str, tokens: list[str], heading: str) -> bytes:
    font = _register_font()
    buf = io.BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    cell_w = (width - 2 * MARGIN) / COLS
    cell_h = (height - 2 * MARGIN - 10 * mm) / ROWS
    per_page = COLS * ROWS

    for index, token in enumerate(tokens):
        slot = index % per_page
        if slot == 0:
            if index:
                pdf.showPage()
            pdf.setFont(font, 11)
            pdf.drawString(MARGIN, height - MARGIN + 2 * mm, heading)

        col, row = slot % COLS, slot // COLS
        x = MARGIN + col * cell_w
        y = height - MARGIN - 10 * mm - (row + 1) * cell_h

        pdf.setDash(1, 3)
        pdf.setLineWidth(0.4)
        pdf.rect(x, y, cell_w, cell_h)
        pdf.setDash()

        qr_x = x + (cell_w - QR_SIDE) / 2
        pdf.drawImage(
            _qr_image(ticket_url(base_url, token)),
            qr_x,
            y + cell_h - QR_SIDE - 7 * mm,
            QR_SIDE,
            QR_SIDE,
        )
        pdf.setFont(font, 15)
        pdf.drawCentredString(x + cell_w / 2, y + 12 * mm, pretty_token(token))
        pdf.setFont(font, 7.5)
        pdf.drawCentredString(x + cell_w / 2, y + 6 * mm, base_url.replace("https://", ""))

    pdf.showPage()
    pdf.save()
    return buf.getvalue()
