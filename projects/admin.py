from django.contrib import admin
from .models import CustomerProject


@admin.register(CustomerProject)
class CustomerProjectAdmin(admin.ModelAdmin):

    list_display = (
        "get_customer_name",
        "site_name",
        "location",
        "capacity_value",
        "capacity_unit",
        "project_status",
        "created_by",
        "created_at",
    )

    search_fields = (
        "project_id",
        "site_name",
        "location",
        "customer__customer_name",
        "customer__phone_number",
        "customer__company_name",
    )

    list_filter = (
        "project_status",
        "capacity_unit",
        "is_active",
        "created_at",
    )

    def get_customer_name(self, obj):
        return obj.customer.customer_name if obj.customer else "No Customer"

    get_customer_name.short_description = "Customer Name"
    get_customer_name.admin_order_field = "customer__customer_name"