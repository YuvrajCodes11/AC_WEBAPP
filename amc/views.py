from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from accounts.models import Profile
from customers.models import Customer
from .models import AMCContract, AMCVisit


def get_profile(request):

    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={
            "role": "MANAGER"
        }
    )

    return profile


@login_required
def amc_list(request):

    profile = get_profile(request)

    search = request.GET.get("search", "")

    status = request.GET.get("status", "")

    amcs = AMCContract.objects.select_related(
        "customer",
        "created_by"
    ).all().order_by("-id")

    if search:
        amcs = amcs.filter(
            Q(amc_id__icontains=search) |
            Q(customer__customer_name__icontains=search) |
            Q(technician_name__icontains=search)
        )

    if status:
        amcs = amcs.filter(status=status)

    today = timezone.now().date()

    expiry_date = today + timedelta(days=30)

    expiring_count = AMCContract.objects.filter(
        status="ACTIVE",
        contract_end_date__range=[today, expiry_date]
    ).count()

    pending_visit_count = AMCVisit.objects.filter(
        status="PENDING",
        visit_date__lte=today
    ).count()

    return render(request, "amc_list.html", {
        "profile": profile,
        "amcs": amcs,
        "search": search,
        "status": status,
        "expiring_count": expiring_count,
        "pending_visit_count": pending_visit_count,
    })


@login_required
def add_amc(request):

    profile = get_profile(request)

    customers = Customer.objects.all().order_by("customer_name")

    if request.method == "POST":

        customer = get_object_or_404(
            Customer,
            id=request.POST.get("customer")
        )

        amc = AMCContract.objects.create(
            customer=customer,
            contract_start_date=request.POST.get("contract_start_date"),
            contract_end_date=request.POST.get("contract_end_date"),
            contract_value=request.POST.get("contract_value") or 0,
            services_per_year=request.POST.get("services_per_year") or 4,
            service_frequency=request.POST.get("service_frequency"),
            technician_name=request.POST.get("technician_name"),
            status=request.POST.get("status"),
            remarks=request.POST.get("remarks"),
            created_by=request.user,
        )

        return redirect("amc_detail", id=amc.id)

    return render(request, "add_amc.html", {
        "profile": profile,
        "customers": customers,
    })


@login_required
def amc_detail(request, id):

    profile = get_profile(request)

    amc = get_object_or_404(
        AMCContract.objects.select_related("customer", "created_by"),
        id=id
    )

    visits = amc.visits.all().order_by("-visit_date")

    return render(request, "amc_detail.html", {
        "profile": profile,
        "amc": amc,
        "visits": visits,
    })


@login_required
def edit_amc(request, id):

    profile = get_profile(request)

    if profile.role != "CEO":
        return redirect("amc_list")

    amc = get_object_or_404(AMCContract, id=id)

    customers = Customer.objects.all().order_by("customer_name")

    if request.method == "POST":

        amc.customer = get_object_or_404(
            Customer,
            id=request.POST.get("customer")
        )

        amc.contract_start_date = request.POST.get("contract_start_date")
        amc.contract_end_date = request.POST.get("contract_end_date")
        amc.contract_value = request.POST.get("contract_value") or 0
        amc.services_per_year = request.POST.get("services_per_year") or 4
        amc.service_frequency = request.POST.get("service_frequency")
        amc.technician_name = request.POST.get("technician_name")
        amc.status = request.POST.get("status")
        amc.remarks = request.POST.get("remarks")

        amc.save()

        return redirect("amc_detail", id=amc.id)

    return render(request, "edit_amc.html", {
        "profile": profile,
        "amc": amc,
        "customers": customers,
    })


@login_required
def delete_amc(request, id):

    profile = get_profile(request)

    if profile.role != "CEO":
        return redirect("amc_list")

    amc = get_object_or_404(AMCContract, id=id)

    amc.delete()

    return redirect("amc_list")


@login_required
def add_amc_visit(request, amc_id):

    profile = get_profile(request)

    amc = get_object_or_404(AMCContract, id=amc_id)

    if request.method == "POST":

        visit = AMCVisit.objects.create(
            amc=amc,
            visit_date=request.POST.get("visit_date"),
            technician_name=request.POST.get("technician_name"),
            status=request.POST.get("status"),
            work_done=request.POST.get("work_done"),
            customer_feedback=request.POST.get("customer_feedback"),
            next_visit_date=request.POST.get("next_visit_date") or None,
            remarks=request.POST.get("remarks"),
            created_by=request.user,
        )

        return redirect("amc_detail", id=amc.id)

    return render(request, "add_amc_visit.html", {
        "profile": profile,
        "amc": amc,
    })


@login_required
def edit_amc_visit(request, visit_id):

    profile = get_profile(request)

    visit = get_object_or_404(AMCVisit, id=visit_id)

    if request.method == "POST":

        visit.visit_date = request.POST.get("visit_date")
        visit.technician_name = request.POST.get("technician_name")
        visit.status = request.POST.get("status")
        visit.work_done = request.POST.get("work_done")
        visit.customer_feedback = request.POST.get("customer_feedback")
        visit.next_visit_date = request.POST.get("next_visit_date") or None
        visit.remarks = request.POST.get("remarks")

        visit.save()

        return redirect("amc_detail", id=visit.amc.id)

    return render(request, "edit_amc_visit.html", {
        "profile": profile,
        "visit": visit,
    })


@login_required
def delete_amc_visit(request, visit_id):

    profile = get_profile(request)

    if profile.role != "CEO":
        return redirect("amc_list")

    visit = get_object_or_404(AMCVisit, id=visit_id)

    amc_id = visit.amc.id

    visit.delete()

    return redirect("amc_detail", id=amc_id)