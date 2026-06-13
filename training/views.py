from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from accounts.models import Profile


def get_profile(request):

    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={
            "role": "MANAGER"
        }
    )

    return profile


@login_required
def training_dashboard(request):

    profile = get_profile(request)

    return render(request, "training_dashboard.html", {
        "profile": profile
    })