from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

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

    return render(request, "dashboard.html", {
        "profile": profile,
        "managers": managers
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