# reports/urls.py

from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("", views.reports_dashboard, name="reports_dashboard"),
    path("store/", views.store_report, name="store_report"),
    path("store/export/", views.export_store_report, name="export_store_report"),
    path("boq-vs-issued/", views.boq_vs_issued_report, name="boq_vs_issued_report"),
    path(
        "boq-vs-issued/export/",
        views.export_boq_vs_issued_report,
        name="export_boq_vs_issued_report",
    ),
    path(
        "project-consumption/",
        views.project_consumption_report,
        name="project_consumption_report",
    ),
    path(
        "project-consumption/export/",
        views.export_project_consumption_report,
        name="export_project_consumption_report",
    ),
]
