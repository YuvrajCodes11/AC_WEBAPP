from datetime import date, timedelta
from .models import Customer, CustomerServiceSchedule


def get_customer_popup_data():

    today = date.today()
    expiry_limit = today + timedelta(days=45)

    pending_services = CustomerServiceSchedule.objects.filter(
        status='PENDING',
        service_date__lte=today,
        customer__is_active=True
    ).select_related('customer')

    warranty_expiring = Customer.objects.filter(
        is_active=True,
        warranty_end_date__isnull=False,
        warranty_end_date__gte=today,
        warranty_end_date__lte=expiry_limit
    )

    amc_expiring = Customer.objects.filter(
        is_active=True,
        amc_end_date__isnull=False,
        amc_end_date__gte=today,
        amc_end_date__lte=expiry_limit
    )

    return {
        'pending_services': pending_services,
        'warranty_expiring': warranty_expiring,
        'amc_expiring': amc_expiring,
    }