# material_issue/pdf_views.py  –  Requirement 2: Full Project PDF Report

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
    BRAND_PURPLE, TABLE_ROW_ALT, LIGHT_BORDER, TEXT_DARK, TEXT_MUTED,
    MARGIN, PAGE_W,
    add_page_number, build_header_block, fmt_date, fmt_money,
    get_styles, kv_table, section_header,
)

from projects.models import CustomerProject
from boq.models import ProjectBOQ, ProjectBOQItem
from .models import MaterialIssue, MaterialIssueItem


@login_required
def project_full_pdf_report(request, project_id):
    project = get_object_or_404(
        CustomerProject.objects.select_related("customer", "created_by"),
        id=project_id,
    )

    customer = project.customer

    # Gather related data
    boqs = ProjectBOQ.objects.select_related(
        "created_by", "approved_by"
    ).filter(project=project).order_by("id")

    material_issues = MaterialIssue.objects.select_related(
        "boq", "issued_by"
    ).prefetch_related(
        "items", "items__store_item", "items__store_item__category",
        "items__boq_item",
    ).filter(project=project).order_by("id")

    # AMC / Warranty from customer
    amc_records = []
    if customer:
        from amc.models import AMCContract
        try:
            amc_records = list(AMCContract.objects.filter(
                customer=customer
            ).order_by("-id")[:5])
        except Exception:
            pass

    # Complaints
    complaints = []
    try:
        from complaints.models import Complaint
        complaints = list(Complaint.objects.filter(
            project=project
        ).order_by("-id")[:20])
    except Exception:
        pass

    # ── Build PDF ────────────────────────────────────────────────────────────
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=20*mm,
        title=f"Project Report - {project.project_id}",
        author="Puri Air Conditioning ERP",
    )
    styles = get_styles()
    elements = []

    # ── Header ───────────────────────────────────────────────────────────────
    elements += build_header_block(
        styles,
        title="Project Full Report",
        subtitle=f"{project.project_id}  |  {project.site_name}",
    )

    # ── Project banner ────────────────────────────────────────────────────────
    status_colours = {
        "PLANNING": colors.HexColor("#2563EB"),
        "ONGOING": colors.HexColor("#16A34A"),
        "HOLD": colors.HexColor("#DC2626"),
        "COMMISSIONED": colors.HexColor("#7C3AED"),
        "CANCELLED": colors.HexColor("#94A3B8"),
    }
    sc = status_colours.get(project.project_status, BRAND_BLUE)

    banner_data = [[
        Paragraph(project.project_id, ParagraphStyle(
            "pid", fontSize=22, fontName="Helvetica-Bold", textColor=BRAND_BLUE)),
        Paragraph(project.site_name, ParagraphStyle(
            "psite", fontSize=12, fontName="Helvetica", textColor=TEXT_DARK)),
        Paragraph(project.get_project_status_display(), ParagraphStyle(
            "pst", fontSize=10, fontName="Helvetica-Bold",
            textColor=colors.white, alignment=1)),
    ]]
    banner_tbl = Table(
        banner_data,
        colWidths=[(PAGE_W - 2*MARGIN)*0.22,
                   (PAGE_W - 2*MARGIN)*0.52,
                   (PAGE_W - 2*MARGIN)*0.26],
    )
    banner_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#EFF6FF")),
        ("BACKGROUND", (2, 0), (2, 0), sc),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (2, 0), (2, 0), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, LIGHT_BORDER),
    ]))
    elements.append(banner_tbl)
    elements.append(Spacer(1, 8))

    # ── Project Details ───────────────────────────────────────────────────────
    elements += section_header("Project Details", styles)
    proj_pairs = [
        ("Project ID",      project.project_id),
        ("Site Name",       project.site_name),
        ("Location",        project.location or "—"),
        ("Status",          project.get_project_status_display()),
        ("Capacity",        project.get_capacity_display_text()),
        ("Project Value",   fmt_money(project.project_value)),
        ("Start Date",      fmt_date(project.start_date)),
        ("Expected End",    fmt_date(project.expected_completion_date)),
        ("Actual End",      fmt_date(project.actual_completion_date)),
        ("Active",          "Yes" if project.is_active else "No"),
        ("Created By",      project.created_by.get_full_name() or project.created_by.username if project.created_by else "—"),
        ("Created Date",    fmt_date(project.created_at)),
    ]
    elements.append(kv_table(proj_pairs, styles))

    # Notes
    for label, val in [
        ("Material Consumed Notes", project.material_consumed_notes),
        ("Material Collection Notes", project.material_collection_notes),
        ("Project Stage Notes", project.project_stage_notes),
        ("Remarks", project.remarks),
    ]:
        if val:
            elements.append(Spacer(1, 4))
            elements.append(Paragraph(f"<b>{label}:</b> {val}", styles["note_text"]))

    elements.append(Spacer(1, 6))

    # ── Customer Details ──────────────────────────────────────────────────────
    elements += section_header("Customer Details", styles)
    if customer:
        cust_pairs = [
            ("Customer ID",   customer.customer_id),
            ("Name",          customer.customer_name),
            ("Company",       customer.company_name or "—"),
            ("Category",      customer.get_customer_category_display()),
            ("Phone",         customer.phone_number),
            ("WhatsApp",      customer.whatsapp_number or "—"),
            ("Email",         customer.email or "—"),
            ("GST No.",       customer.gst_number or "—"),
            ("Address",       customer.address or "—"),
            ("Landmark",      customer.landmark or "—"),
            ("City",          customer.city or "—"),
            ("State",         customer.state or "—"),
            ("Warranty",      f"{fmt_date(customer.warranty_start_date)} → {fmt_date(customer.warranty_end_date)}"),
            ("AMC",           f"{fmt_date(customer.amc_start_date)} → {fmt_date(customer.amc_end_date)}"),
            ("Active",        "Yes" if customer.is_active else "No"),
            ("Remarks",       customer.remarks or "—"),
        ]
    else:
        cust_pairs = [("Customer", "No customer linked to this project")]
    elements.append(kv_table(cust_pairs, styles))
    elements.append(Spacer(1, 6))

    # ── BOQ Summary ───────────────────────────────────────────────────────────
    elements += section_header(f"BOQ Summary  ({boqs.count()} BOQ records)", styles)

    for boq in boqs:
        boq_items = ProjectBOQItem.objects.select_related(
            "store_item"
        ).filter(boq=boq).order_by("id")

        boq_hdr = Table(
            [[Paragraph(f"<b>{boq.boq_id}</b>  —  {boq.title}", ParagraphStyle(
                "bh", fontSize=9, fontName="Helvetica-Bold", textColor=BRAND_BLUE)),
              Paragraph(boq.get_status_display(), ParagraphStyle(
                  "bs2", fontSize=8, fontName="Helvetica-Bold",
                  textColor=colors.white, alignment=1))]],
            colWidths=[(PAGE_W - 2*MARGIN)*0.75, (PAGE_W - 2*MARGIN)*0.25],
        )
        boq_hdr.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#EFF6FF")),
            ("BACKGROUND", (1, 0), (1, 0), BRAND_BLUE_LIGHT),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.3, LIGHT_BORDER),
        ]))
        elements.append(boq_hdr)

        # BOQ items mini table
        if boq_items.exists():
            def hdr(t): return Paragraph(t, ParagraphStyle(
                "mh", fontSize=7, fontName="Helvetica-Bold",
                textColor=colors.white, alignment=1))
            def td(t, bold=False, align=0, col=TEXT_DARK):
                return Paragraph(str(t), ParagraphStyle(
                    "mt", fontSize=7,
                    fontName="Helvetica-Bold" if bold else "Helvetica",
                    textColor=col, alignment=align))

            cw = [(PAGE_W - 2*MARGIN)*p for p in [0.36, 0.1, 0.12, 0.12, 0.12, 0.18]]
            bdata = [[hdr("Item"), hdr("Unit"), hdr("BOQ Qty"), hdr("Issued"),
                      hdr("Balance"), hdr("Amount")]]
            gtot = Decimal("0")
            for item in boq_items:
                gtot += item.total_amount()
                bdata.append([
                    td(f"{item.store_item.item_description} ({'VRV' if item.store_item.is_vrv else 'Non-VRV'})"),
                    td(item.store_item.get_unit_display(), align=1),
                    td(f"{item.required_quantity:.1f}", align=2),
                    td(f"{item.issued_quantity:.1f}", col=colors.HexColor("#2563EB"), align=2),
                    td(f"{item.balance_quantity():.1f}", bold=True, col=BRAND_RED, align=2),
                    td(fmt_money(item.total_amount()), bold=True, col=BRAND_GREEN, align=2),
                ])
            nr = len(bdata)
            bdata.append([
                td("Total", bold=True), td(""), td(""), td(""), td(""),
                td(fmt_money(gtot), bold=True, col=BRAND_GREEN, align=2),
            ])
            bt = Table(bdata, colWidths=cw, repeatRows=1)
            alt_styles = [("BACKGROUND", (0, r), (-1, r), TABLE_ROW_ALT)
                          for r in range(1, nr) if r % 2 == 0]
            bt.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), BRAND_BLUE),
                ("BACKGROUND", (0, nr), (-1, nr), colors.HexColor("#EFF6FF")),
                ("LINEABOVE", (0, nr), (-1, nr), 0.8, BRAND_BLUE),
                ("GRID", (0, 0), (-1, -1), 0.3, LIGHT_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                *alt_styles,
            ]))
            elements.append(bt)
        else:
            elements.append(Paragraph("  No items in this BOQ.", styles["note_text"]))
        elements.append(Spacer(1, 5))

    if not boqs.exists():
        elements.append(Paragraph("No BOQ records found for this project.", styles["note_text"]))
    elements.append(Spacer(1, 4))

    # ── Material Issues ───────────────────────────────────────────────────────
    elements += section_header(
        f"Material Issue Details  ({material_issues.count()} issues)", styles)

    for issue in material_issues:
        items = issue.items.select_related("store_item").all()
        total_issued   = sum(i.issued_quantity for i in items)
        total_returned = sum(i.returned_quantity for i in items)
        total_unused = sum(i.unused_quantity for i in items)
        total_consumed = sum(i.consumed_quantity for i in items)
        total_scrap = sum(i.scrap_quantity for i in items)

        issue_hdr = Table([[
            Paragraph(f"<b>{issue.issue_id}</b><br/>{issue.heading}", ParagraphStyle(
                "ih", fontSize=9, fontName="Helvetica-Bold", textColor=BRAND_BLUE)),
            Paragraph(f"Date: {fmt_date(issue.issue_date)}  |  To: {issue.issued_to}  |  BOQ: {issue.boq.boq_id if issue.boq else '—'}", ParagraphStyle(
                "im", fontSize=8, fontName="Helvetica", textColor=TEXT_MUTED)),
            Paragraph(issue.get_status_display(), ParagraphStyle(
                "is2", fontSize=8, fontName="Helvetica-Bold",
                textColor=colors.white, alignment=1)),
        ]], colWidths=[(PAGE_W - 2*MARGIN)*0.18,
                      (PAGE_W - 2*MARGIN)*0.57,
                      (PAGE_W - 2*MARGIN)*0.25])
        issue_hdr.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#F0FDF4")),
            ("BACKGROUND", (2, 0), (2, 0), BRAND_GREEN),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.3, LIGHT_BORDER),
        ]))
        elements.append(issue_hdr)

        if items.exists():
            def hdr(t): return Paragraph(t, ParagraphStyle(
                "mh2", fontSize=7, fontName="Helvetica-Bold",
                textColor=colors.white, alignment=1))
            def td(t, bold=False, align=0, col=TEXT_DARK):
                return Paragraph(str(t), ParagraphStyle(
                    "mt2", fontSize=7,
                    fontName="Helvetica-Bold" if bold else "Helvetica",
                    textColor=col, alignment=align))

            cw2 = [(PAGE_W - 2*MARGIN)*p for p in [0.27, 0.08, 0.11, 0.11, 0.11, 0.11, 0.11, 0.10]]
            idata = [[hdr("Item"), hdr("Unit"), hdr("Issued"),
                      hdr("Consumed"), hdr("Returned"), hdr("Not Used"), hdr("Scrap"), hdr("Balance")]]
            for it in items:
                idata.append([
                    td(f"{it.store_item.item_description} ({'VRV' if it.store_item.is_vrv else 'Non-VRV'})"),
                    td(it.store_item.get_unit_display(), align=1),
                    td(f"{it.issued_quantity:.2f}", col=colors.HexColor("#2563EB"), align=2),
                    td(f"{it.consumed_quantity:.2f}", col=BRAND_ORANGE, align=2),
                    td(f"{it.returned_quantity:.2f}", col=BRAND_PURPLE, align=2),
                    td(f"{it.unused_quantity:.2f}", col=colors.HexColor("#0891B2"), align=2),
                    td(f"{it.scrap_quantity:.2f}", col=TEXT_MUTED, align=2),
                    td(f"{it.balance_quantity():.2f}", bold=True, col=BRAND_RED, align=2),
                ])
            nr2 = len(idata)
            idata.append([
                td("Totals", bold=True), td(""),
                td(f"{total_issued:.2f}", bold=True, col=colors.HexColor("#2563EB"), align=2),
                td(f"{total_consumed:.2f}", bold=True, col=BRAND_ORANGE, align=2),
                td(f"{total_returned:.2f}", bold=True, col=BRAND_PURPLE, align=2),
                td(f"{total_unused:.2f}", bold=True, col=colors.HexColor("#0891B2"), align=2),
                td(f"{total_scrap:.2f}", bold=True, col=TEXT_MUTED, align=2),
                td(f"{total_issued - total_consumed - total_returned - total_unused - total_scrap:.2f}", bold=True, col=BRAND_RED, align=2),
            ])
            it2 = Table(idata, colWidths=cw2, repeatRows=1)
            alt2 = [("BACKGROUND", (0, r), (-1, r), TABLE_ROW_ALT)
                    for r in range(1, nr2) if r % 2 == 0]
            it2.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), BRAND_GREEN),
                ("BACKGROUND", (0, nr2), (-1, nr2), colors.HexColor("#F0FDF4")),
                ("LINEABOVE", (0, nr2), (-1, nr2), 0.8, BRAND_GREEN),
                ("GRID", (0, 0), (-1, -1), 0.3, LIGHT_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                *alt2,
            ]))
            elements.append(it2)
        else:
            elements.append(Paragraph("  No items in this issue.", styles["note_text"]))
        elements.append(Spacer(1, 5))

    if not material_issues.exists():
        elements.append(Paragraph("No material issues found for this project.", styles["note_text"]))

    # ── AMC Info ──────────────────────────────────────────────────────────────
    if customer:
        elements.append(Spacer(1, 4))
        elements += section_header("AMC / Warranty Information", styles)
        amc_pairs = [
            ("Warranty Start",  fmt_date(customer.warranty_start_date)),
            ("Warranty End",    fmt_date(customer.warranty_end_date)),
            ("AMC Start",       fmt_date(customer.amc_start_date)),
            ("AMC End",         fmt_date(customer.amc_end_date)),
            ("Warranty Soon",   "Yes" if customer.is_warranty_expiring_soon() else "No"),
            ("AMC Expiring",    "Yes" if customer.is_amc_expiring_soon() else "No"),
        ]
        elements.append(kv_table(amc_pairs, styles,
                                 col_widths=[40*mm, 50*mm, 40*mm, 50*mm]))
        if amc_records:
            elements.append(Spacer(1, 4))
            elements.append(Paragraph("<b>AMC Contract Records:</b>",
                                      styles["note_text"]))
            for rec in amc_records:
                try:
                    elements.append(Paragraph(
                        f"  • {rec}", styles["note_text"]))
                except Exception:
                    pass

    # ── Complaints ────────────────────────────────────────────────────────────
    if complaints:
        elements.append(Spacer(1, 4))
        elements += section_header(f"Complaints  ({len(complaints)})", styles)
        for c in complaints:
            try:
                elements.append(Paragraph(f"  • {c}", styles["note_text"]))
            except Exception:
                pass

    # ── Footer ────────────────────────────────────────────────────────────────
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_BORDER))
    elements.append(Spacer(1, 3))
    elements.append(Paragraph(
        "This is a system-generated comprehensive project report from "
        "Puri Air Conditioning ERP. All figures are as recorded in the system.",
        styles["footer_text"],
    ))

    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="Project_Report_{project.project_id}.pdf"'
    )
    return response
