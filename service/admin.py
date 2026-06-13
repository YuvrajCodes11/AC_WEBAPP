from django.contrib import admin
from .models import ServiceComplaint


@admin.register(ServiceComplaint)
class ServiceComplaintAdmin(admin.ModelAdmin):

    list_display = (
        'complaint_id',
        'complaint_date',
        'customer',
        'customer_category',
        'contact_number',
        'technician_name',
        'status',
        'service_completed_date',
    )

    search_fields = (
        'complaint_id',
        'customer__customer_name',
        'contact_number',
        'technician_name',
        'nature_of_complaint',
    )

    list_filter = (
        'customer__customer_category',
        'status',
        'complaint_date',
        'service_completed_date',
    )