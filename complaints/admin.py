from django.contrib import admin
from .models import CustomerComplaint


@admin.register(CustomerComplaint)
class CustomerComplaintAdmin(admin.ModelAdmin):
    list_display = (
        "complaint_id",
        "customer",
        "site_type",
        "visit_date",
        "no_of_technicians",
        "status",
    )

    search_fields = (
        "complaint_id",
        "customer__customer_name",
        "customer__phone_number",
        "complaint_title",
    )

    list_filter = (
        "site_type",
        "status",
        "visit_date",
    )

    readonly_fields = (
        "complaint_id",
        "created_at",
        "updated_at",
    )