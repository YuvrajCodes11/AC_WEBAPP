from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .models import Profile


def login_view(request):
    error = None

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            Profile.objects.get_or_create(
                user=user,
                defaults={"role": "MANAGER"}
            )

            login(request, user)
            return redirect("dashboard")

        error = "Invalid username or password"

    return render(request, "login.html", {"error": error})


@login_required
def dashboard(request):
    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={"role": "MANAGER"}
    )

    managers = Profile.objects.filter(role="MANAGER")

    # Insurance expiry alerts: projects with insurance ending within 7 days
    from projects.models import CustomerProject
    today = timezone.localdate()
    from datetime import timedelta
    alert_date = today + timedelta(days=7)

    insurance_alerts = CustomerProject.objects.select_related(
        "customer"
    ).filter(
        is_active=True,
        insurance_end_date__isnull=False,
        insurance_end_date__gte=today,
        insurance_end_date__lte=alert_date,
    ).order_by("insurance_end_date")

    # Annotate days remaining for template
    for project in insurance_alerts:
        project.insurance_days_left = (project.insurance_end_date - today).days

    return render(request, "dashboard.html", {
        "profile": profile,
        "managers": managers,
        "insurance_alerts": insurance_alerts,
    })


@login_required
def add_manager(request):
    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={"role": "MANAGER"}
    )

    if profile.role != "CEO":
        return redirect("dashboard")

    error = None
    success = None

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            error = "Username already exists"

        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            Profile.objects.create(
                user=user,
                role="MANAGER"
            )

            success = "Manager added successfully"

    return render(request, "add_manager.html", {
        "error": error,
        "success": success
    })


def logout_view(request):
    logout(request)
    return redirect("login")