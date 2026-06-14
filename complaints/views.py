from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import CustomerComplaint
from .forms import CustomerComplaintForm
from customers.models import Customer, CustomerServiceSchedule
from amc.models import AMCVisit
from service.models import ServiceComplaint


def _customer_visit_history(customer):
    visits = []

    schedules = CustomerServiceSchedule.objects.filter(
        customer=customer,
        status="COMPLETED",
        completed_date__isnull=False,
    )
    for schedule in schedules:
        visits.append({
            "date": schedule.completed_date,
            "type": schedule.get_service_type_display(),
            "status": schedule.get_status_display(),
            "notes": schedule.remarks or schedule.complaint_description or "-",
        })

    amc_visits = AMCVisit.objects.filter(
        amc__customer=customer,
        status="COMPLETED",
    )
    for visit in amc_visits:
        visits.append({
            "date": visit.visit_date,
            "type": "AMC Visit",
            "status": visit.get_status_display(),
            "notes": visit.work_done or visit.remarks or "-",
        })

    complaint_visits = CustomerComplaint.objects.filter(
        customer=customer,
        status="COMPLETED",
    )
    for complaint in complaint_visits:
        visits.append({
            "date": complaint.visit_date,
            "type": complaint.get_site_type_display(),
            "status": complaint.get_status_display(),
            "notes": complaint.work_done or complaint.remarks or "-",
        })

    service_visits = ServiceComplaint.objects.filter(
        customer=customer,
        status="COMPLETED",
        service_completed_date__isnull=False,
    )
    for service in service_visits:
        visits.append({
            "date": service.service_completed_date,
            "type": "Service Visit",
            "status": service.get_status_display(),
            "notes": service.remarks or service.nature_of_complaint or "-",
        })

    return sorted(
        visits,
        key=lambda visit: visit["date"],
        reverse=True,
    )


def _completed_visits_for_year(year):
    report = {}
    for customer in Customer.objects.all():
        for visit in _customer_visit_history(customer):
            if visit["date"].year != int(year):
                continue
            key = (customer.id, visit["type"])
            if key not in report:
                report[key] = {
                    "customer": customer,
                    "site_type": visit["type"],
                    "total_visits": 0,
                }
            report[key]["total_visits"] += 1
    return sorted(
        report.values(),
        key=lambda row: (row["customer"].customer_name, row["site_type"]),
    )


def complaint_dashboard(request):
    current_year = timezone.localdate().year

    total_complaints = CustomerComplaint.objects.count()

    completed_visits = [
        visit
        for customer in Customer.objects.all()
        for visit in _customer_visit_history(customer)
        if visit["date"].year == current_year
    ]
    warranty_visits_year = sum(
        "Warranty" in visit["type"] for visit in completed_visits
    )
    amc_visits_year = sum(
        "AMC" in visit["type"] for visit in completed_visits
    )

    completed_count = CustomerComplaint.objects.filter(
        status="COMPLETED"
    ).count()

    pending_count = CustomerComplaint.objects.filter(
        status="PENDING"
    ).count()

    partial_count = CustomerComplaint.objects.filter(
        status="PARTIAL"
    ).count()

    cancelled_count = CustomerComplaint.objects.filter(
        status="CANCELLED"
    ).count()

    recent_complaints = CustomerComplaint.objects.select_related(
        "customer"
    ).order_by("-id")[:10]

    context = {
        "current_year": current_year,
        "total_complaints": total_complaints,
        "warranty_visits_year": warranty_visits_year,
        "amc_visits_year": amc_visits_year,
        "completed_count": completed_count,
        "pending_count": pending_count,
        "partial_count": partial_count,
        "cancelled_count": cancelled_count,
        "recent_complaints": recent_complaints,
    }

    return render(request, "complaints/complaint_dashboard.html", context)


def complaint_list(request):
    search = request.GET.get("search", "")
    site_type = request.GET.get("site_type", "")
    status = request.GET.get("status", "")
    year = request.GET.get("year", "")

    complaints = CustomerComplaint.objects.select_related("customer").all()

    if search:
        complaints = complaints.filter(
            complaint_id__icontains=search
        ) | complaints.filter(
            customer__customer_name__icontains=search
        ) | complaints.filter(
            customer__phone_number__icontains=search
        ) | complaints.filter(
            complaint_title__icontains=search
        )

    if site_type:
        complaints = complaints.filter(site_type=site_type)

    if status:
        complaints = complaints.filter(status=status)

    if year:
        complaints = complaints.filter(visit_date__year=year)

    context = {
        "complaints": complaints,
        "search": search,
        "site_type": site_type,
        "status": status,
        "year": year,
    }

    return render(request, "complaints/complaint_list.html", context)


def add_complaint(request):
    if request.method == "POST":
        form = CustomerComplaintForm(request.POST)

        if form.is_valid():
            complaint = form.save()
            messages.success(
                request,
                f"Complaint {complaint.complaint_id} added successfully."
            )
            return redirect("complaint_list")
    else:
        form = CustomerComplaintForm()

    return render(request, "complaints/add_complaint.html", {"form": form})


def edit_complaint(request, pk):
    complaint = get_object_or_404(CustomerComplaint, pk=pk)

    if request.method == "POST":
        form = CustomerComplaintForm(request.POST, instance=complaint)

        if form.is_valid():
            form.save()
            messages.success(request, "Complaint updated successfully.")
            return redirect("complaint_list")
    else:
        form = CustomerComplaintForm(instance=complaint)

    return render(request, "complaints/edit_complaint.html", {
        "form": form,
        "complaint": complaint,
    })


def complaint_detail(request, pk):
    complaint = get_object_or_404(
        CustomerComplaint.objects.select_related("customer"),
        pk=pk
    )

    customer = complaint.customer

    total_complaints = CustomerComplaint.objects.filter(
        customer=customer
    ).count()

    visit_history = _customer_visit_history(customer)
    total_visits = len(visit_history)
    warranty_visits = sum(
        "Warranty" in visit["type"] for visit in visit_history
    )
    amc_visits = sum(
        "AMC" in visit["type"] for visit in visit_history
    )

    context = {
        "complaint": complaint,
        "total_complaints": total_complaints,
        "total_visits": total_visits,
        "warranty_visits": warranty_visits,
        "amc_visits": amc_visits,
    }

    return render(request, "complaints/complaint_detail.html", context)


def yearly_visit_report(request):
    year = request.GET.get("year", timezone.localdate().year)
    try:
        year = int(year)
    except (TypeError, ValueError):
        year = timezone.localdate().year

    reports = _completed_visits_for_year(year)

    context = {
        "year": year,
        "reports": reports,
    }

    return render(request, "complaints/yearly_visit_report.html", context)


def customer_service_history_report(request):
    search = request.GET.get("search", "").strip()

    customers = Customer.objects.prefetch_related(
        "complaints",
        "service_schedules",
        "service_complaints",
    ).all().order_by("customer_name")

    if search:
        customers = customers.filter(
            Q(customer_id__icontains=search) |
            Q(customer_name__icontains=search) |
            Q(phone_number__icontains=search) |
            Q(company_name__icontains=search)
        )

    report_data = []
    for customer in customers:
        complaints = CustomerComplaint.objects.filter(
            customer=customer
        ).order_by("-visit_date", "-id")

        visits = _customer_visit_history(customer)

        service_complaints = customer.service_complaints.all().order_by(
            "-complaint_date", "-id"
        )

        if (
            complaints.exists()
            or customer.service_schedules.exists()
            or visits
            or service_complaints.exists()
        ):
            report_data.append({
                "customer": customer,
                "total_complaints": complaints.count() + service_complaints.count(),
                "total_visits": len(visits),
                "complaints": complaints,
                "visits": visits,
                "service_complaints": service_complaints,
            })

    return render(request, "complaints/customer_service_history_report.html", {
        "search": search,
        "report_data": report_data,
    })


def customer_service_history_pdf(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    complaints = CustomerComplaint.objects.filter(customer=customer).order_by("-visit_date")
    visits = _customer_visit_history(customer)
    service_complaints = customer.service_complaints.all().order_by("-complaint_date")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=f"Service History - {customer.customer_id}")
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("Puri Air Conditioning", styles["Title"]),
        Paragraph("Customer Visit & Complaint History", styles["Heading2"]),
        Spacer(1, 12),
        Paragraph(
            f"<b>{customer.customer_id} - {customer.customer_name}</b><br/>"
            f"Phone: {customer.phone_number}<br/>"
            f"Company: {customer.company_name or '-'}<br/>"
            f"Address: {customer.address or '-'}",
            styles["BodyText"],
        ),
        Spacer(1, 12),
        Paragraph(
            f"<b>Total Complaints:</b> {complaints.count() + service_complaints.count()} &nbsp;&nbsp; "
            f"<b>Total Visits:</b> {len(visits)}",
            styles["BodyText"],
        ),
        Spacer(1, 12),
        Paragraph("Visit History", styles["Heading3"]),
    ]

    visit_data = [["Date", "Type", "Status", "Notes"]]
    for visit in visits:
        visit_data.append([
            visit["date"].strftime("%d %b %Y"),
            visit["type"],
            visit["status"],
            visit["notes"],
        ])
    if len(visit_data) == 1:
        visit_data.append(["-", "-", "-", "No visits"])

    complaint_data = [["Date", "Complaint", "Status", "Service History", "Technician"]]
    for complaint in complaints:
        complaint_data.append([
            complaint.visit_date.strftime("%d %b %Y"),
            f"{complaint.complaint_id} - {complaint.complaint_title}",
            complaint.get_status_display(),
            complaint.work_done or complaint.complaint_description or "-",
            "-",
        ])
    for complaint in service_complaints:
        complaint_data.append([
            complaint.complaint_date.strftime("%d %b %Y"),
            complaint.complaint_id,
            complaint.get_status_display(),
            complaint.nature_of_complaint,
            complaint.technician_name or "-",
        ])
    if len(complaint_data) == 1:
        complaint_data.append(["-", "No complaints", "-", "-", "-"])

    for data in (visit_data, complaint_data):
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F4C81")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))
        if data is visit_data:
            elements.append(Paragraph("Complaint History", styles["Heading3"]))

    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Service_History_{customer.customer_id}.pdf"'
    return response
