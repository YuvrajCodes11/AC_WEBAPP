# reports/urls.py

from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [

    # Dashboard
    path(
        "",
        views.reports_dashboard,
        name="reports_dashboard"
    ),

]