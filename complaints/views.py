from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Sum
from django.utils import timezone

from .models import CustomerComplaint
from .forms import CustomerComplaintForm


def complaint_dashboard(request):
    current_year = timezone.localdate().year

    total_complaints = CustomerComplaint.objects.count()

    warranty_visits_year = CustomerComplaint.objects.filter(
        site_type="WARRANTY",
        visit_date__year=current_year
    ).count()

    amc_visits_year = CustomerComplaint.objects.filter(
        site_type="AMC",
        visit_date__year=current_year
    ).count()

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

    total_visits = CustomerComplaint.objects.filter(
        customer=customer
    ).count()

    warranty_visits = CustomerComplaint.objects.filter(
        customer=customer,
        site_type="WARRANTY"
    ).count()

    amc_visits = CustomerComplaint.objects.filter(
        customer=customer,
        site_type="AMC"
    ).count()

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

    reports = CustomerComplaint.objects.filter(
        visit_date__year=year
    ).values(
        "customer__customer_id",
        "customer__customer_name",
        "customer__phone_number",
        "site_type",
    ).annotate(
        total_visits=Count("id"),
        total_technicians=Sum("no_of_technicians")
    ).order_by(
        "customer__customer_name"
    )

    context = {
        "year": year,
        "reports": reports,
    }

    return render(request, "complaints/yearly_visit_report.html", context)