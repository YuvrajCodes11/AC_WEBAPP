from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):

    list_display = (
        'customer_id',
        'customer_category',
        'customer_name',
        'company_name',
        'phone_number',
        'city',
        'state',
        'created_at',
    )

    search_fields = (
        'customer_id',
        'customer_name',
        'company_name',
        'phone_number',
        'city',
        'state',
    )

    list_filter = (
        'customer_category',
        'city',
        'state',
        'created_at',
    )