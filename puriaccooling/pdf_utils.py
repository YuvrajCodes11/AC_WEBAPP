# puriaccooling/pdf_utils.py
# Shared PDF generation utilities for Puri Air Conditioning ERP

import os
from decimal import Decimal
from io import BytesIO

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import KeepTogether

# ── Brand colours ────────────────────────────────────────────────────────────
BRAND_BLUE      = colors.HexColor("#0F4C81")
BRAND_BLUE_LIGHT = colors.HexColor("#1B6CA8")
BRAND_SKY       = colors.HexColor("#89CFF0")
BRAND_GREEN     = colors.HexColor("#16A34A")
BRAND_ORANGE    = colors.HexColor("#EA580C")
BRAND_RED       = colors.HexColor("#DC2626")
BRAND_PURPLE    = colors.HexColor("#7C3AED")
TABLE_HEADER_BG = colors.HexColor("#0F4C81")
TABLE_ROW_ALT   = colors.HexColor("#F0F7FF")
LIGHT_BORDER    = colors.HexColor("#CBD5E1")
TEXT_DARK       = colors.HexColor("#1E293B")
TEXT_MUTED      = colors.HexColor("#64748B")

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm


def get_logo_path():
    return os.path.join(settings.BASE_DIR, "static", "images", "logo.png")


def get_styles():
    styles = getSampleStyleSheet()
    custom = {
        "company_name": ParagraphStyle(
            "company_name",
            fontSize=18, fontName="Helvetica-Bold",
            textColor=BRAND_BLUE, alignment=TA_LEFT, spaceAfter=2,
        ),
        "company_sub": ParagraphStyle(
            "company_sub",
            fontSize=9, fontName="Helvetica",
            textColor=TEXT_MUTED, alignment=TA_LEFT, spaceAfter=0,
        ),
        "report_title": ParagraphStyle(
            "report_title",
            fontSize=22, fontName="Helvetica-Bold",
            textColor=BRAND_BLUE, alignment=TA_CENTER, spaceAfter=4,
        ),
        "section_title": ParagraphStyle(
            "section_title",
            fontSize=11, fontName="Helvetica-Bold",
            textColor=BRAND_BLUE, spaceBefore=10, spaceAfter=4,
        ),
        "label": ParagraphStyle(
            "label",
            fontSize=8, fontName="Helvetica-Bold",
            textColor=TEXT_MUTED,
        ),
        "value": ParagraphStyle(
            "value",
            fontSize=9, fontName="Helvetica",
            textColor=TEXT_DARK,
        ),
        "value_bold": ParagraphStyle(
            "value_bold",
            fontSize=9, fontName="Helvetica-Bold",
            textColor=TEXT_DARK,
        ),
        "table_header": ParagraphStyle(
            "table_header",
            fontSize=8, fontName="Helvetica-Bold",
            textColor=colors.white, alignment=TA_CENTER,
        ),
        "table_cell": ParagraphStyle(
            "table_cell",
            fontSize=8, fontName="Helvetica",
            textColor=TEXT_DARK,
        ),
        "table_cell_bold": ParagraphStyle(
            "table_cell_bold",
            fontSize=8, fontName="Helvetica-Bold",
            textColor=TEXT_DARK,
        ),
        "table_cell_right": ParagraphStyle(
            "table_cell_right",
            fontSize=8, fontName="Helvetica",
            textColor=TEXT_DARK, alignment=TA_RIGHT,
        ),
        "total_label": ParagraphStyle(
            "total_label",
            fontSize=10, fontName="Helvetica-Bold",
            textColor=BRAND_BLUE, alignment=TA_RIGHT,
        ),
        "total_value": ParagraphStyle(
            "total_value",
            fontSize=10, fontName="Helvetica-Bold",
            textColor=BRAND_GREEN,
        ),
        "footer_text": ParagraphStyle(
            "footer_text",
            fontSize=7, fontName="Helvetica",
            textColor=TEXT_MUTED, alignment=TA_CENTER,
        ),
        "status_badge": ParagraphStyle(
            "status_badge",
            fontSize=9, fontName="Helvetica-Bold",
            textColor=BRAND_BLUE, alignment=TA_CENTER,
        ),
        "note_text": ParagraphStyle(
            "note_text",
            fontSize=8, fontName="Helvetica",
            textColor=TEXT_DARK, leading=12,
        ),
    }
    return custom


def build_header_block(styles, title, subtitle=None):
    """Returns a list of flowables forming the page header."""
    elements = []
    logo_path = get_logo_path()

    header_data = []

    # Left: logo + company
    left_col = []
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=40*mm, height=14*mm)
            logo.hAlign = "LEFT"
            left_col.append(logo)
        except Exception:
            pass
    left_col.append(Paragraph("Puri Air Conditioning", styles["company_name"]))
    left_col.append(Paragraph("HVAC Solutions & Cooling Management", styles["company_sub"]))

    from reportlab.platypus import KeepInFrame
    left_table = Table([[item] for item in left_col], colWidths=[PAGE_W - 2*MARGIN - 55*mm])

    # Right: title block
    right_lines = [Paragraph(title, ParagraphStyle(
        "hdr_title", fontSize=14, fontName="Helvetica-Bold",
        textColor=colors.white, alignment=TA_RIGHT,
    ))]
    if subtitle:
        right_lines.append(Paragraph(subtitle, ParagraphStyle(
            "hdr_sub", fontSize=8, fontName="Helvetica",
            textColor=colors.HexColor("#BFDBFE"), alignment=TA_RIGHT,
        )))

    hdr_table = Table(
        [[left_col[1] if not os.path.exists(logo_path) else left_col[0],
          Table([[r] for r in right_lines])]],
        colWidths=[PAGE_W - 2*MARGIN - 55*mm, 55*mm],
    )
    # Build a blue banner row
    banner = Table(
        [[Paragraph("Puri Air Conditioning", ParagraphStyle(
            "bn", fontSize=13, fontName="Helvetica-Bold",
            textColor=colors.white)),
          Paragraph(title, ParagraphStyle(
              "bnt", fontSize=13, fontName="Helvetica-Bold",
              textColor=colors.white, alignment=TA_RIGHT))]],
        colWidths=[PAGE_W - 2*MARGIN - 60*mm, 60*mm],
    )
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (0, -1), 10),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 10),
    ]))

    sub_row_data = [
        [Paragraph("HVAC Solutions & Cooling Management", styles["company_sub"]),
         Paragraph(subtitle or "", ParagraphStyle(
             "bs", fontSize=8, textColor=TEXT_MUTED, alignment=TA_RIGHT))]
    ]
    sub_row = Table(sub_row_data, colWidths=[PAGE_W - 2*MARGIN - 60*mm, 60*mm])
    sub_row.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 0),
    ]))

    elements.append(banner)
    elements.append(sub_row)
    elements.append(HRFlowable(width="100%", thickness=1.5, color=BRAND_BLUE, spaceAfter=8))
    return elements


def kv_table(pairs, styles, col_widths=None):
    """Build a two-column key-value info table."""
    if col_widths is None:
        col_widths = [35*mm, (PAGE_W - 2*MARGIN)/2 - 35*mm,
                      35*mm, (PAGE_W - 2*MARGIN)/2 - 35*mm]
    data = []
    row = []
    for i, (label, value) in enumerate(pairs):
        row.append(Paragraph(label, styles["label"]))
        row.append(Paragraph(str(value) if value else "—", styles["value"]))
        if len(row) == 4:
            data.append(row)
            row = []
    if row:
        # pad to full width
        while len(row) < 4:
            row.append(Paragraph("", styles["label"]))
        data.append(row)

    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("GRID", (0, 0), (-1, -1), 0.3, LIGHT_BORDER),
        ("TEXTCOLOR", (0, 0), (0, -1), TEXT_MUTED),   # label col 0
        ("TEXTCOLOR", (2, 0), (2, -1), TEXT_MUTED),   # label col 2
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
    ]))
    return t


def section_header(text, styles):
    return [
        Spacer(1, 6),
        Paragraph(text.upper(), ParagraphStyle(
            "sh", fontSize=9, fontName="Helvetica-Bold",
            textColor=colors.white,
            backColor=BRAND_BLUE_LIGHT,
            leftIndent=6, rightIndent=6,
            spaceBefore=0, spaceAfter=0,
            borderPad=4,
        )),
        Spacer(1, 4),
    ]


def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(TEXT_MUTED)
    page_str = f"Page {doc.page}  |  Puri Air Conditioning ERP  |  Generated on {__import__('datetime').date.today().strftime('%d %b %Y')}"
    canvas.drawCentredString(PAGE_W / 2, 10*mm, page_str)
    canvas.restoreState()


def fmt_date(d):
    if not d:
        return "—"
    try:
        return d.strftime("%d %b %Y")
    except Exception:
        return str(d)


def fmt_money(v):
    try:
        return f"₹{Decimal(v):,.2f}"
    except Exception:
        return f"₹{v}"
