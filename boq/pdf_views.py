# boq/pdf_views.py  –  Requirement 1: BOQ Report PDF Download

from decimal import Decimal
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from puriaccooling.pdf_utils import (
    BRAND_BLUE, BRAND_BLUE_LIGHT, BRAND_GREEN, BRAND_ORANGE, BRAND_RED,
    BRAND_PURPLE, TABLE_ROW_ALT, TABLE_HEADER_BG, LIGHT_BORDER, TEXT_DARK, TEXT_MUTED,
    MARGIN, PAGE_W,
    add_page_number, build_header_block, fmt_date, fmt_money,
    get_styles, kv_table, section_header,
)

from .models import ProjectBOQ, ProjectBOQItem


STATUS_COLOURS = {
    "DRAFT":     colors.HexColor("#94A3B8"),
    "SUBMITTED": colors.HexColor("#2563EB"),
    "APPROVED":  colors.HexColor("#16A34A"),
    "REJECTED":  colors.HexColor("#DC2626"),
    "CLOSED":    colors.HexColor("#7C3AED"),
}


@login_required
def boq_pdf_report(request, id):
    boq = get_object_or_404(
        ProjectBOQ.objects.select_related(
            "project", "project__customer", "created_by", "approved_by"
        ),
        id=id,
    )
    boq_items = ProjectBOQItem.objects.select_related(
        "store_item", "store_item__category"
    ).filter(boq=boq).order_by("id")

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=20*mm,
        title=f"BOQ Report - {boq.boq_id}",
        author="Puri Air Conditioning ERP",
    )

    styles = get_styles()
    elements = []

    # ── Header ──────────────────────────────────────────────────────────────
    project_label = boq.project.project_id if boq.project else "No Project"
    elements += build_header_block(
        styles,
        title="BOQ Report",
        subtitle=f"{boq.boq_id}  |  {project_label}",
    )

    # ── BOQ Summary row ─────────────────────────────────────────────────────
    status_colour = STATUS_COLOURS.get(boq.status, BRAND_BLUE)
    status_cell = Paragraph(
        boq.get_status_display(),
        ParagraphStyle("sc", fontSize=10, fontName="Helvetica-Bold",
                       textColor=colors.white),
    )
    summary_data = [[
        Paragraph(boq.boq_id, ParagraphStyle("bid", fontSize=20,
                  fontName="Helvetica-Bold", textColor=BRAND_BLUE)),
        Paragraph(boq.title, ParagraphStyle("bt", fontSize=11,
                  fontName="Helvetica", textColor=TEXT_DARK)),
        status_cell,
    ]]
    summary_tbl = Table(
        summary_data,
        colWidths=[(PAGE_W - 2*MARGIN)*0.25,
                   (PAGE_W - 2*MARGIN)*0.5,
                   (PAGE_W - 2*MARGIN)*0.25],
    )
    summary_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
        ("BACKGROUND", (2, 0), (2, 0), status_colour),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (2, 0), (2, 0), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, LIGHT_BORDER),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    elements.append(summary_tbl)
    elements.append(Spacer(1, 8))

    # ── Project & Customer details ───────────────────────────────────────────
    elements += section_header("Project Information", styles)
    proj = boq.project
    cust = proj.customer if proj else None

    if proj:
        project_pairs = [
            ("Project ID",      proj.project_id),
            ("Site Name",       proj.site_name),
            ("Location",        proj.location or "—"),
            ("Status",          proj.get_project_status_display()),
            ("Capacity",        proj.get_capacity_display_text()),
            ("Project Value",   fmt_money(proj.project_value)),
            ("Start Date",      fmt_date(proj.start_date)),
            ("Expected End",    fmt_date(proj.expected_completion_date)),
            ("Actual End",      fmt_date(proj.actual_completion_date)),
            ("Site Address",    proj.site_address or "—"),
        ]
    else:
        project_pairs = [("Project", "No project linked")]
    elements.append(kv_table(project_pairs, styles))
    elements.append(Spacer(1, 6))

    elements += section_header("Customer Information", styles)
    if proj and cust:
        customer_pairs = [
            ("Customer ID",     cust.customer_id),
            ("Name",            proj.get_customer_name()),
            ("Company",         cust.company_name or "—"),
            ("Phone",           proj.get_customer_phone()),
            ("Email",           cust.email or "—"),
            ("WhatsApp",        cust.whatsapp_number or "—"),
            ("GST No.",         cust.gst_number or "—"),
            ("Category",        cust.get_customer_category_display()),
            ("City",            cust.city or "—"),
            ("State",           cust.state or "—"),
            ("Address",         cust.address or "—"),
            ("Landmark",        cust.landmark or "—"),
        ]
    else:
        customer_pairs = [("Customer", "No customer linked")]
    elements.append(kv_table(customer_pairs, styles))
    elements.append(Spacer(1, 6))

    elements += section_header("BOQ Information", styles)
    boq_pairs = [
        ("BOQ ID",          boq.boq_id),
        ("Title",           boq.title),
        ("Status",          boq.get_status_display()),
        ("Created By",      boq.created_by.get_full_name() or boq.created_by.username if boq.created_by else "—"),
        ("Created Date",    fmt_date(boq.created_at)),
        ("Approved By",     boq.approved_by.get_full_name() or boq.approved_by.username if boq.approved_by else "—"),
        ("Approved Date",   fmt_date(boq.approved_at)),
        ("Last Updated",    fmt_date(boq.updated_at)),
        ("Total Items",     str(boq.total_items())),
        ("Remarks",         boq.remarks or "—"),
    ]
    elements.append(kv_table(boq_pairs, styles))
    elements.append(Spacer(1, 8))

    # ── Material Items Table ─────────────────────────────────────────────────
    elements += section_header("Material Items", styles)

    col_widths = [
        (PAGE_W - 2*MARGIN)*0.36,
        (PAGE_W - 2*MARGIN)*0.10,
        (PAGE_W - 2*MARGIN)*0.14,
        (PAGE_W - 2*MARGIN)*0.13,
        (PAGE_W - 2*MARGIN)*0.13,
        (PAGE_W - 2*MARGIN)*0.07,
        (PAGE_W - 2*MARGIN)*0.07,
    ]

    def hdr(txt):
        return Paragraph(txt, ParagraphStyle(
            "th", fontSize=7, fontName="Helvetica-Bold",
            textColor=colors.white, alignment=1))

    def cell(txt, bold=False, align="LEFT", colour=TEXT_DARK):
        style = ParagraphStyle(
            "td", fontSize=7.5,
            fontName="Helvetica-Bold" if bold else "Helvetica",
            textColor=colour,
            alignment=2 if align == "RIGHT" else 0,
        )
        return Paragraph(str(txt), style)

    table_data = [[
        hdr("Item Description"),
        hdr("Unit"),
        hdr("BOQ Qty"),
        hdr("Issued"),
        hdr("Balance"),
        hdr("Rate (₹)"),
        hdr("Amount (₹)"),
    ]]

    grand_required = Decimal("0")
    grand_issued   = Decimal("0")
    grand_consumed = Decimal("0")
    grand_returned = Decimal("0")
    grand_amount   = Decimal("0")

    for i, item in enumerate(boq_items):
        balance  = item.balance_quantity()
        amount   = item.total_amount()
        grand_required += item.required_quantity
        grand_issued   += item.issued_quantity
        grand_consumed += item.consumed_quantity
        grand_returned += item.returned_quantity
        grand_amount   += amount

        desc_text = item.store_item.item_description
        code_text = item.store_item.item_code or ""
        if item.store_item.size:
            code_text += f" | {item.store_item.size}"
        code_text += f" | {item.store_item.item_type_display}"

        desc_para = Paragraph(
            f"<b>{desc_text}</b><br/><font size='6.5' color='#64748B'>{code_text}</font>",
            ParagraphStyle("dp", fontSize=7.5, fontName="Helvetica",
                           textColor=TEXT_DARK, leading=10),
        )

        row = [
            desc_para,
            cell(item.store_item.get_unit_display()),
            cell(f"{item.required_quantity:.2f}", align="RIGHT"),
            cell(f"{item.issued_quantity:.2f}", align="RIGHT",
                 colour=colors.HexColor("#2563EB")),
            cell(f"{balance:.2f}", bold=True, align="RIGHT",
                 colour=BRAND_RED),
            cell(f"{item.rate:.2f}", align="RIGHT"),
            cell(f"{amount:.2f}", bold=True, align="RIGHT",
                 colour=BRAND_GREEN),
        ]
        table_data.append(row)

    # Totals row
    table_data.append([
        Paragraph("<b>TOTALS</b>", ParagraphStyle(
            "tot", fontSize=8, fontName="Helvetica-Bold",
            textColor=BRAND_BLUE)),
        cell(""),
        cell(f"{grand_required:.2f}", bold=True, align="RIGHT"),
        cell(f"{grand_issued:.2f}", bold=True, align="RIGHT",
             colour=colors.HexColor("#2563EB")),
        cell(f"{max(grand_required - grand_issued, Decimal('0')):.2f}", bold=True, align="RIGHT",
             colour=BRAND_RED),
        cell(""),
        cell(f"{grand_amount:.2f}", bold=True, align="RIGHT",
             colour=BRAND_GREEN),
    ])

    n_rows = len(table_data)
    mat_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    row_styles = []
    for r in range(1, n_rows - 1):
        if r % 2 == 0:
            row_styles.append(("BACKGROUND", (0, r), (-1, r), TABLE_ROW_ALT))

    mat_table.setStyle(TableStyle([
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        # Total row
        ("BACKGROUND", (0, n_rows - 1), (-1, n_rows - 1),
         colors.HexColor("#EFF6FF")),
        ("FONTNAME", (0, n_rows - 1), (-1, n_rows - 1), "Helvetica-Bold"),
        ("LINEABOVE", (0, n_rows - 1), (-1, n_rows - 1), 1, BRAND_BLUE),
        # General
        ("GRID", (0, 0), (-1, -1), 0.3, LIGHT_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        *row_styles,
    ]))
    elements.append(mat_table)
    elements.append(Spacer(1, 8))

    # ── Cost Summary Box ─────────────────────────────────────────────────────
    elements += section_header("Cost Summary", styles)
    total_items = boq_items.count()
    summary_rows = [
        ["Total Material Items", str(total_items)],
        ["Total BOQ Quantity", f"{grand_required:.2f}"],
        ["Total Issued Quantity",   f"{grand_issued:.2f}"],
        ["Total Remaining Quantity", f"{max(grand_required - grand_issued, Decimal('0')):.2f}"],
        ["", ""],
        ["GRAND TOTAL (BOQ Value)", fmt_money(grand_amount)],
    ]
    cost_tbl = Table(
        [[Paragraph(r[0], ParagraphStyle(
              "cl", fontSize=9,
              fontName="Helvetica-Bold" if r[0].startswith("GRAND") else "Helvetica",
              textColor=BRAND_BLUE if r[0].startswith("GRAND") else TEXT_MUTED)),
          Paragraph(r[1], ParagraphStyle(
              "cv", fontSize=9,
              fontName="Helvetica-Bold",
              textColor=BRAND_GREEN if r[0].startswith("GRAND") else TEXT_DARK,
              alignment=2))]
         for r in summary_rows],
        colWidths=[(PAGE_W - 2*MARGIN)*0.6, (PAGE_W - 2*MARGIN)*0.4],
        hAlign="RIGHT",
    )
    cost_tbl.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.3, LIGHT_BORDER),
        ("BACKGROUND", (0, 0), (-1, -2), colors.HexColor("#F8FAFC")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#DBEAFE")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("LINEABOVE", (0, -1), (-1, -1), 1.5, BRAND_BLUE),
    ]))
    elements.append(cost_tbl)
    elements.append(Spacer(1, 8))

    # ── Remarks ──────────────────────────────────────────────────────────────
    if boq.remarks:
        elements += section_header("BOQ Remarks", styles)
        elements.append(Paragraph(boq.remarks, styles["note_text"]))
        elements.append(Spacer(1, 6))

    if proj and proj.remarks:
        elements += section_header("Project Remarks", styles)
        elements.append(Paragraph(proj.remarks, styles["note_text"]))
        elements.append(Spacer(1, 6))

    # ── Footer line ──────────────────────────────────────────────────────────
    elements.append(Spacer(1, 6))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_BORDER))
    elements.append(Spacer(1, 3))
    elements.append(Paragraph(
        "This is a system-generated BOQ report from Puri Air Conditioning ERP. "
        "For queries contact the management.",
        styles["footer_text"],
    ))

    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="BOQ_Report_{boq.boq_id}_{project_label}.pdf"'
    )
    return response
