from django.contrib import admin
from .models import AMCContract, AMCVisit


class AMCVisitInline(admin.TabularInline):
    model = AMCVisit
    extra = 1


@admin.register(AMCContract)
class AMCContractAdmin(admin.ModelAdmin):

    list_display = (
        'amc_id',
        'customer',
        'contract_start_date',
        'contract_end_date',
        'contract_value',
        'services_per_year',
        'service_frequency',
        'technician_name',
        'status',
    )

    search_fields = (
        'amc_id',
        'customer__customer_name',
        'technician_name',
    )

    list_filter = (
        'status',
        'service_frequency',
        'contract_start_date',
        'contract_end_date',
    )

    inlines = [AMCVisitInline]


@admin.register(AMCVisit)
class AMCVisitAdmin(admin.ModelAdmin):

    list_display = (
        'visit_id',
        'amc',
        'visit_date',
        'technician_name',
        'status',
        'next_visit_date',
    )

    search_fields = (
        'visit_id',
        'amc__amc_id',
        'amc__customer__customer_name',
        'technician_name',
    )

    list_filter = (
        'status',
        'visit_date',
        'next_visit_date',
    )