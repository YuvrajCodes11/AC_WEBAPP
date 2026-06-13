# projects/views.py

from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from customers.models import Customer
from accounts.models import Profile
from .models import CustomerProject


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


def parse_decimal(value):
    try:
        if value:
            return Decimal(value)
        return Decimal("0")
    except InvalidOperation:
        return Decimal("0")


@login_required
def project_list(request):
    profile = get_profile(request)

    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip()

    projects = CustomerProject.objects.select_related(
        "customer",
        "created_by"
    ).all().order_by("-id")

    if search:
        projects = projects.filter(
            Q(project_id__icontains=search) |
            Q(customer__customer_name__icontains=search) |
            Q(customer__company_name__icontains=search) |
            Q(customer__phone_number__icontains=search) |
            Q(site_name__icontains=search) |
            Q(location__icontains=search) |
            Q(site_address__icontains=search) |
            Q(project_stage_notes__icontains=search) |
            Q(material_consumed_notes__icontains=search) |
            Q(material_collection_notes__icontains=search) |
            Q(remarks__icontains=search)
        )

    if status:
        projects = projects.filter(project_status=status)

    total_projects = CustomerProject.objects.count()
    planning_projects = CustomerProject.objects.filter(project_status="PLANNING").count()
    ongoing_projects = CustomerProject.objects.filter(project_status="ONGOING").count()
    hold_projects = CustomerProject.objects.filter(project_status="HOLD").count()
    commissioned_projects = CustomerProject.objects.filter(project_status="COMMISSIONED").count()

    return render(request, "project_list.html", {
        "profile": profile,
        "projects": projects,
        "search": search,
        "status": status,
        "status_choices": CustomerProject.PROJECT_STATUS_CHOICES,
        "total_projects": total_projects,
        "planning_projects": planning_projects,
        "ongoing_projects": ongoing_projects,
        "hold_projects": hold_projects,
        "commissioned_projects": commissioned_projects,
    })


@login_required
def add_project(request):
    profile = get_profile(request)
    customers = Customer.objects.filter(is_active=True).order_by("customer_name")

    error = None

    if request.method == "POST":
        try:
            customer_id = request.POST.get("customer")
            customer = None

            if customer_id:
                customer = get_object_or_404(Customer, id=customer_id)

            site_name = request.POST.get("site_name", "").strip()

            if not site_name:
                site_name = "New Project Site"

            project = CustomerProject.objects.create(
                customer=customer,
                site_name=site_name,
                location=request.POST.get("location", "").strip() or "Muzaffarpur",
                site_address=request.POST.get("site_address", "").strip(),
                capacity_value=parse_decimal(request.POST.get("capacity_value")),
                capacity_unit=request.POST.get("capacity_unit") or "TR",
                project_value=parse_decimal(request.POST.get("project_value")),
                start_date=parse_date(request.POST.get("start_date")),
                expected_completion_date=parse_date(request.POST.get("expected_completion_date")),
                actual_completion_date=parse_date(request.POST.get("actual_completion_date")),
                project_status=request.POST.get("project_status") or "PLANNING",
                material_consumed_notes=request.POST.get("material_consumed_notes", "").strip(),
                material_collection_notes=request.POST.get("material_collection_notes", "").strip(),
                project_stage_notes=request.POST.get("project_stage_notes", "").strip(),
                remarks=request.POST.get("remarks", "").strip(),
                is_active=True if request.POST.get("is_active") == "on" else True,
                created_by=request.user,
            )

            messages.success(request, "Project added successfully.")
            return redirect("project_detail", id=project.id)

        except Exception as e:
            error = str(e)

    return render(request, "add_project.html", {
        "profile": profile,
        "customers": customers,
        "status_choices": CustomerProject.PROJECT_STATUS_CHOICES,
        "capacity_unit_choices": CustomerProject.CAPACITY_UNIT_CHOICES,
        "error": error,
    })


@login_required
def edit_project(request, id):
    profile = get_profile(request)

    project = get_object_or_404(
        CustomerProject.objects.select_related("customer", "created_by"),
        id=id
    )

    customers = Customer.objects.filter(is_active=True).order_by("customer_name")

    error = None

    if request.method == "POST":
        try:
            customer_id = request.POST.get("customer")
            customer = None

            if customer_id:
                customer = get_object_or_404(Customer, id=customer_id)

            site_name = request.POST.get("site_name", "").strip()

            if not site_name:
                site_name = "New Project Site"

            project.customer = customer
            project.site_name = site_name
            project.location = request.POST.get("location", "").strip() or "Muzaffarpur"
            project.site_address = request.POST.get("site_address", "").strip()
            project.capacity_value = parse_decimal(request.POST.get("capacity_value"))
            project.capacity_unit = request.POST.get("capacity_unit") or "TR"
            project.project_value = parse_decimal(request.POST.get("project_value"))
            project.start_date = parse_date(request.POST.get("start_date"))
            project.expected_completion_date = parse_date(request.POST.get("expected_completion_date"))
            project.actual_completion_date = parse_date(request.POST.get("actual_completion_date"))
            project.project_status = request.POST.get("project_status") or "PLANNING"
            project.material_consumed_notes = request.POST.get("material_consumed_notes", "").strip()
            project.material_collection_notes = request.POST.get("material_collection_notes", "").strip()
            project.project_stage_notes = request.POST.get("project_stage_notes", "").strip()
            project.remarks = request.POST.get("remarks", "").strip()
            project.is_active = True if request.POST.get("is_active") == "on" else False

            project.save()

            messages.success(request, "Project updated successfully.")
            return redirect("project_detail", id=project.id)

        except Exception as e:
            error = str(e)

    return render(request, "edit_project.html", {
        "profile": profile,
        "project": project,
        "customers": customers,
        "status_choices": CustomerProject.PROJECT_STATUS_CHOICES,
        "capacity_unit_choices": CustomerProject.CAPACITY_UNIT_CHOICES,
        "error": error,
    })


@login_required
def project_detail(request, id):
    profile = get_profile(request)

    project = get_object_or_404(
        CustomerProject.objects.select_related("customer", "created_by"),
        id=id
    )

    return render(request, "project_detail.html", {
        "profile": profile,
        "project": project,
    })


@login_required
def delete_project(request, id):
    profile = get_profile(request)

    if profile.role != "CEO":
        messages.error(request, "Only CEO can delete project.")
        return redirect("project_list")

    project = get_object_or_404(CustomerProject, id=id)
    project.delete()

    messages.success(request, "Project deleted successfully.")
    return redirect("project_list")