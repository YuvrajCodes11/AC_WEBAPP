# customers/urls.py

from django.urls import path
from . import views

urlpatterns = [

    # =====================================================
    # CUSTOMER
    # =====================================================

    path(
        "",
        views.customer_list,
        name="customer_list"
    ),

    path(
        "add/",
        views.add_customer,
        name="add_customer"
    ),

    path(
        "detail/<int:id>/",
        views.customer_detail,
        name="customer_detail"
    ),

    path(
        "edit/<int:id>/",
        views.edit_customer,
        name="edit_customer"
    ),

    path(
        "customers/<int:id>/status/",
        views.toggle_customer_status,
        name="toggle_customer_status"
    ),

    path(
        "export-csv/",
        views.export_customers_csv,
        name="export_customers_csv"
    ),

    # =====================================================
    # SERVICE SCHEDULES
    # =====================================================

    path(
        "service-schedules/",
        views.customer_service_schedule_list,
        name="customer_service_schedule_list"
    ),

    path(
        "service-schedules/complete/<int:id>/",
        views.complete_service_schedule,
        name="complete_service_schedule"
    ),

    path(
        "service-schedules/edit/<int:id>/",
        views.edit_service_schedule,
        name="edit_service_schedule"
    ),

    path(
        "service-schedules/missed/<int:id>/",
        views.mark_service_missed,
        name="mark_service_missed"
    ),

    path(
        "service-schedules/export/",
        views.export_service_schedules_csv,
        name="export_service_schedules_csv"
    ),

    # =====================================================
    # ALERT DASHBOARD
    # =====================================================

    path(
        "alerts/",
        views.customer_alert_dashboard,
        name="customer_alert_dashboard"
    ),

]