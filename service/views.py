from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from accounts.models import Profile
from customers.models import Customer
from .models import ServiceComplaint


def get_profile(request):

    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={
            "role": "MANAGER"
        }
    )

    return profile


@login_required
def service_list(request):

    profile = get_profile(request)

    search = request.GET.get("search", "")
    status = request.GET.get("status", "")
    customer_category = request.GET.get("customer_category", "")

    complaints = ServiceComplaint.objects.select_related(
        "customer",
        "created_by"
    ).all().order_by("-id")

    if search:
        complaints = complaints.filter(
            Q(complaint_id__icontains=search) |
            Q(customer__customer_name__icontains=search) |
            Q(contact_number__icontains=search) |
            Q(technician_name__icontains=search) |
            Q(nature_of_complaint__icontains=search)
        )

    if status:
        complaints = complaints.filter(status=status)

    if customer_category:
        complaints = complaints.filter(
            customer__customer_category=customer_category
        )

    pending_count = ServiceComplaint.objects.filter(status="PENDING").count()

    amc_pending_count = ServiceComplaint.objects.filter(
        status="PENDING",
        customer__customer_category="AMC"
    ).count()

    warranty_pending_count = ServiceComplaint.objects.filter(
        status="PENDING",
        customer__customer_category="WARRANTY"
    ).count()

    general_pending_count = ServiceComplaint.objects.filter(
        status="PENDING",
        customer__customer_category="GENERAL"
    ).count()

    return render(request, "service_list.html", {
        "profile": profile,
        "complaints": complaints,
        "search": search,
        "status": status,
        "customer_category": customer_category,
        "pending_count": pending_count,
        "amc_pending_count": amc_pending_count,
        "warranty_pending_count": warranty_pending_count,
        "general_pending_count": general_pending_count,
    })


@login_required
def add_service(request):

    profile = get_profile(request)

    customers = Customer.objects.all().order_by("customer_name")

    if request.method == "POST":

        customer = get_object_or_404(
            Customer,
            id=request.POST.get("customer")
        )

        ServiceComplaint.objects.create(
            complaint_date=request.POST.get("complaint_date"),
            customer=customer,
            customer_address=request.POST.get("customer_address"),
            contact_number=request.POST.get("contact_number"),
            nature_of_complaint=request.POST.get("nature_of_complaint"),
            technician_name=request.POST.get("technician_name"),
            status=request.POST.get("status"),
            service_completed_date=request.POST.get("service_completed_date") or None,
            remarks=request.POST.get("remarks"),
            created_by=request.user,
        )

        return redirect("service_list")

    return render(request, "add_service.html", {
        "profile": profile,
        "customers": customers,
    })


@login_required
def service_detail(request, id):

    profile = get_profile(request)

    complaint = get_object_or_404(
        ServiceComplaint.objects.select_related("customer", "created_by"),
        id=id
    )

    return render(request, "service_detail.html", {
        "profile": profile,
        "complaint": complaint,
    })


@login_required
def edit_service(request, id):

    profile = get_profile(request)

    complaint = get_object_or_404(ServiceComplaint, id=id)

    customers = Customer.objects.all().order_by("customer_name")

    if request.method == "POST":

        complaint.customer = get_object_or_404(
            Customer,
            id=request.POST.get("customer")
        )

        complaint.complaint_date = request.POST.get("complaint_date")
        complaint.customer_address = request.POST.get("customer_address")
        complaint.contact_number = request.POST.get("contact_number")
        complaint.nature_of_complaint = request.POST.get("nature_of_complaint")
        complaint.technician_name = request.POST.get("technician_name")
        complaint.status = request.POST.get("status")
        complaint.service_completed_date = request.POST.get("service_completed_date") or None
        complaint.remarks = request.POST.get("remarks")

        complaint.save()

        return redirect("service_detail", id=complaint.id)

    return render(request, "edit_service.html", {
        "profile": profile,
        "complaint": complaint,
        "customers": customers,
    })


@login_required
def delete_service(request, id):

    profile = get_profile(request)

    if profile.role != "CEO":
        return redirect("service_list")

    complaint = get_object_or_404(ServiceComplaint, id=id)

    complaint.delete()

    return redirect("service_list")