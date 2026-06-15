import os
import csv
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from accounts.models import Profile
from .models import Customer, CustomerServiceSchedule


def get_profile(request):
    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={
            "role": "MANAGER"
        }
    )
    return profile


def parse_date(value):
    if value:
        return datetime.strptime(value, "%Y-%m-%d").date()
    return None


@login_required
def customer_list(request):
    profile = get_profile(request)

    search = request.GET.get("search", "").strip()
    category = request.GET.get("category", "").strip()
    status = request.GET.get("status", "").strip()

    customers = Customer.objects.all().order_by("-id")

    if search:
        customers = customers.filter(
            Q(customer_id__icontains=search) |
            Q(customer_name__icontains=search) |
            Q(company_name__icontains=search) |
            Q(phone_number__icontains=search) |
            Q(whatsapp_number__icontains=search) |
            Q(email__icontains=search) |
            Q(gst_number__icontains=search) |
            Q(city__icontains=search) |
            Q(state__icontains=search) |
            Q(pincode__icontains=search) |
            Q(landmark__icontains=search) |
            Q(address__icontains=search) |
            Q(remarks__icontains=search)
        )

    if category:
        customers = customers.filter(customer_category=category)

    if status == "ACTIVE":
        customers = customers.filter(is_active=True)

    if status == "INACTIVE":
        customers = customers.filter(is_active=False)

    today = timezone.localdate()

    pending_services = CustomerServiceSchedule.objects.select_related(
        "customer"
    ).filter(
        status="PENDING",
        service_date__lte=today
    ).order_by("service_date")

    warranty_expiring = [
        customer for customer in Customer.objects.all()
        if customer.is_warranty_expiring_soon()
    ]

    amc_expiring = [
        customer for customer in Customer.objects.all()
        if customer.is_amc_expiring_soon()
    ]

    context = {
        "profile": profile,
        "customers": customers,
        "search": search,
        "category": category,
        "status": status,

        "pending_services": pending_services,
        "warranty_expiring": warranty_expiring,
        "amc_expiring": amc_expiring,

        "total_customers": Customer.objects.count(),
        "active_customers": Customer.objects.filter(is_active=True).count(),
        "inactive_customers": Customer.objects.filter(is_active=False).count(),
        "general_customers": Customer.objects.filter(customer_category="GENERAL").count(),
        "warranty_customers": Customer.objects.filter(customer_category="WARRANTY").count(),
        "amc_customers": Customer.objects.filter(customer_category="AMC").count(),
    }

    return render(request, "customer_list.html", context)


@login_required
def add_customer(request):
    profile = get_profile(request)

    if request.method == "POST":
        try:
            customer = Customer.objects.create(
                customer_category=request.POST.get("customer_category") or "GENERAL",
                customer_name=request.POST.get("customer_name", "").strip(),
                company_name=request.POST.get("company_name", "").strip(),
                phone_number=request.POST.get("phone_number", "").strip(),
                whatsapp_number=request.POST.get("whatsapp_number", "").strip(),
                email=request.POST.get("email", "").strip(),
                gst_number=request.POST.get("gst_number", "").strip(),
                address=request.POST.get("address", "").strip(),
                landmark=request.POST.get("landmark", "").strip(),
                city=request.POST.get("city", "").strip(),
                state=request.POST.get("state", "").strip(),
                pincode=request.POST.get("pincode", "").strip(),
                remarks=request.POST.get("remarks", "").strip(),

                warranty_start_date=parse_date(request.POST.get("warranty_start_date")),
                warranty_end_date=parse_date(request.POST.get("warranty_end_date")),
                amc_start_date=parse_date(request.POST.get("amc_start_date")),
                amc_end_date=parse_date(request.POST.get("amc_end_date")),

                is_active=True if request.POST.get("is_active") == "on" else False,
                created_by=request.user
            )

            messages.success(request, "Customer added successfully.")
            return redirect("customer_detail", id=customer.id)

        except Exception as e:
            messages.error(request, str(e))

    return render(request, "add_customer.html", {
        "profile": profile,
    })


@login_required
def edit_customer(request, id):
    profile = get_profile(request)

    if profile.role not in ["CEO", "MANAGER"]:
        messages.error(request, "You do not have permission to edit customer.")
        return redirect("customer_list")

    customer = get_object_or_404(Customer, id=id)

    if request.method == "POST":
        try:
            customer.customer_category = request.POST.get("customer_category") or "GENERAL"
            customer.customer_name = request.POST.get("customer_name", "").strip()
            customer.company_name = request.POST.get("company_name", "").strip()
            customer.phone_number = request.POST.get("phone_number", "").strip()
            customer.whatsapp_number = request.POST.get("whatsapp_number", "").strip()
            customer.email = request.POST.get("email", "").strip()
            customer.gst_number = request.POST.get("gst_number", "").strip()
            customer.address = request.POST.get("address", "").strip()
            customer.landmark = request.POST.get("landmark", "").strip()
            customer.city = request.POST.get("city", "").strip()
            customer.state = request.POST.get("state", "").strip()
            customer.pincode = request.POST.get("pincode", "").strip()
            customer.remarks = request.POST.get("remarks", "").strip()

            customer.warranty_start_date = parse_date(request.POST.get("warranty_start_date"))
            customer.warranty_end_date = parse_date(request.POST.get("warranty_end_date"))
            customer.amc_start_date = parse_date(request.POST.get("amc_start_date"))
            customer.amc_end_date = parse_date(request.POST.get("amc_end_date"))

            customer.is_active = True if request.POST.get("is_active") == "on" else False

            customer.save()

            messages.success(request, "Customer updated successfully.")
            return redirect("customer_detail", id=customer.id)

        except Exception as e:
            messages.error(request, str(e))

    return render(request, "edit_customer.html", {
        "profile": profile,
        "customer": customer,
    })


@login_required
def toggle_customer_status(request, id):
    profile = get_profile(request)

    if profile.role not in ["CEO", "MANAGER"]:
        messages.error(request, "You do not have permission to change customer status.")
        return redirect("customer_list")

    customer = get_object_or_404(Customer, id=id)

    customer.is_active = not customer.is_active
    customer.save(update_fields=["is_active"])

    if customer.is_active:
        messages.success(request, f"{customer.customer_name} activated successfully.")
    else:
        messages.success(request, f"{customer.customer_name} marked as inactive successfully.")

    return redirect("customer_list")


@login_required
def customer_detail(request, id):
    profile = get_profile(request)

    customer = get_object_or_404(Customer, id=id)

    service_schedules = CustomerServiceSchedule.objects.filter(
        customer=customer
    ).order_by("service_date")

    pending_services = service_schedules.filter(
        status="PENDING",
        service_date__lte=timezone.localdate()
    )

    return render(request, "customer_detail.html", {
        "profile": profile,
        "customer": customer,
        "service_schedules": service_schedules,
        "pending_services": pending_services,
    })


@login_required
def customer_service_schedule_list(request):
    profile = get_profile(request)

    search = request.GET.get("search", "").strip()
    service_type = request.GET.get("service_type", "").strip()
    status = request.GET.get("status", "").strip()

    schedules = CustomerServiceSchedule.objects.select_related(
        "customer"
    ).all().order_by("service_date")

    if search:
        schedules = schedules.filter(
            Q(customer__customer_id__icontains=search) |
            Q(customer__customer_name__icontains=search) |
            Q(customer__company_name__icontains=search) |
            Q(customer__phone_number__icontains=search) |
            Q(customer__whatsapp_number__icontains=search) |
            Q(customer__city__icontains=search) |
            Q(customer__state__icontains=search) |
            Q(customer__pincode__icontains=search) |
            Q(complaint_title__icontains=search) |
            Q(complaint_description__icontains=search) |
            Q(remarks__icontains=search)
        )

    if service_type:
        schedules = schedules.filter(service_type=service_type)

    if status:
        schedules = schedules.filter(status=status)

    return render(request, "customer_service_schedule_list.html", {
        "profile": profile,
        "schedules": schedules,
        "search": search,
        "service_type": service_type,
        "status": status,
        "service_type_choices": CustomerServiceSchedule.SERVICE_TYPE_CHOICES,
        "status_choices": CustomerServiceSchedule.STATUS_CHOICES,
    })


@login_required
def complete_service_schedule(request, id):
    profile = get_profile(request)

    schedule = get_object_or_404(CustomerServiceSchedule, id=id)

    if request.method == "POST":
        schedule.status = "COMPLETED"
        schedule.completed_date = timezone.localdate()

        schedule.complaint_title = request.POST.get("complaint_title", "").strip()
        schedule.complaint_description = request.POST.get("complaint_description", "").strip()
        schedule.remarks = request.POST.get("remarks", "").strip()

        if request.FILES.get("complaint_register"):
            schedule.complaint_register = request.FILES.get("complaint_register")

        schedule.save()

        messages.success(request, "Service marked as completed successfully.")
        return redirect("customer_service_schedule_list")

    return render(request, "complete_service_schedule.html", {
        "profile": profile,
        "schedule": schedule,
    })


@login_required
def edit_service_schedule(request, id):
    profile = get_profile(request)

    schedule = get_object_or_404(CustomerServiceSchedule, id=id)

    if request.method == "POST":
        schedule.complaint_title = request.POST.get("complaint_title", "").strip()
        schedule.complaint_description = request.POST.get("complaint_description", "").strip()
        schedule.remarks = request.POST.get("remarks", "").strip()

        status = request.POST.get("status", "").strip()
        if status in ["PENDING", "COMPLETED", "MISSED"]:
            schedule.status = status

        completed_date = parse_date(request.POST.get("completed_date"))
        schedule.completed_date = completed_date

        if request.FILES.get("complaint_register"):
            schedule.complaint_register = request.FILES.get("complaint_register")

        schedule.save()

        messages.success(request, "Service schedule updated successfully.")
        return redirect("customer_detail", id=schedule.customer.id)

    return render(request, "edit_service_schedule.html", {
        "profile": profile,
        "schedule": schedule,
        "status_choices": CustomerServiceSchedule.STATUS_CHOICES,
    })


@login_required
def mark_service_missed(request, id):
    schedule = get_object_or_404(CustomerServiceSchedule, id=id)

    schedule.status = "MISSED"
    schedule.save()

    messages.success(request, "Service marked as missed.")
    return redirect("customer_service_schedule_list")


@login_required
def customer_alert_dashboard(request):
    profile = get_profile(request)
    today = timezone.localdate()
    upcoming_limit = today + timedelta(days=7)

    pending_services = CustomerServiceSchedule.objects.select_related(
        "customer"
    ).filter(
        status="PENDING",
        service_date__lte=today
    ).order_by("service_date")

    upcoming_services = CustomerServiceSchedule.objects.select_related(
        "customer"
    ).filter(
        status="PENDING",
        service_date__gt=today,
        service_date__lte=upcoming_limit
    ).order_by("service_date")

    expiring_warranty_customers = [
        customer for customer in Customer.objects.all()
        if customer.is_warranty_expiring_soon()
    ]

    expiring_amc_customers = [
        customer for customer in Customer.objects.all()
        if customer.is_amc_expiring_soon()
    ]

    return render(request, "customer_alert_dashboard.html", {
        "profile": profile,
        "pending_services": pending_services,
        "upcoming_services": upcoming_services,
        "expiring_warranty_customers": expiring_warranty_customers,
        "expiring_amc_customers": expiring_amc_customers,
    })


@login_required
def export_customers_csv(request):
    dataset_folder = os.path.join(settings.BASE_DIR, "dataset")
    os.makedirs(dataset_folder, exist_ok=True)

    file_path = os.path.join(dataset_folder, "customers.csv")

    customers = Customer.objects.all().order_by("customer_id")

    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow([
            "Customer ID",
            "Customer Category",
            "Customer Name",
            "Company Name",
            "Phone Number",
            "WhatsApp Number",
            "Email",
            "GST Number",
            "Address",
            "Landmark",
            "City",
            "State",
            "Pincode",
            "Warranty Start Date",
            "Warranty End Date",
            "AMC Start Date",
            "AMC End Date",
            "Remarks",
            "Status",
            "Created By",
            "Created At",
            "Updated At",
        ])

        for customer in customers:
            writer.writerow([
                customer.customer_id,
                customer.get_customer_category_display(),
                customer.customer_name,
                customer.company_name or "",
                customer.phone_number,
                customer.whatsapp_number or "",
                customer.email or "",
                customer.gst_number or "",
                customer.address or "",
                customer.landmark or "",
                customer.city or "",
                customer.state or "",
                customer.pincode or "",
                customer.warranty_start_date or "",
                customer.warranty_end_date or "",
                customer.amc_start_date or "",
                customer.amc_end_date or "",
                customer.remarks or "",
                "Active" if customer.is_active else "Inactive",
                customer.created_by.username if customer.created_by else "",
                customer.created_at.strftime("%d-%m-%Y %H:%M"),
                customer.updated_at.strftime("%d-%m-%Y %H:%M"),
            ])

    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename="customers.csv"
    )


@login_required
def export_service_schedules_csv(request):
    dataset_folder = os.path.join(settings.BASE_DIR, "dataset")
    os.makedirs(dataset_folder, exist_ok=True)

    file_path = os.path.join(dataset_folder, "customer_service_schedules.csv")

    schedules = CustomerServiceSchedule.objects.select_related(
        "customer"
    ).all().order_by("service_date")

    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow([
            "Customer ID",
            "Customer Name",
            "Company Name",
            "Phone Number",
            "Service Type",
            "Service Date",
            "Status",
            "Completed Date",
            "Complaint Title",
            "Complaint Description",
            "Complaint File",
            "Remarks",
            "Created At",
            "Updated At",
        ])

        for schedule in schedules:
            writer.writerow([
                schedule.customer.customer_id,
                schedule.customer.customer_name,
                schedule.customer.company_name or "",
                schedule.customer.phone_number,
                schedule.get_service_type_display(),
                schedule.service_date,
                schedule.get_status_display(),
                schedule.completed_date or "",
                schedule.complaint_title or "",
                schedule.complaint_description or "",
                schedule.complaint_register.url if schedule.complaint_register else "",
                schedule.remarks or "",
                schedule.created_at.strftime("%d-%m-%Y %H:%M"),
                schedule.updated_at.strftime("%d-%m-%Y %H:%M"),
            ])

    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename="customer_service_schedules.csv"
    )
