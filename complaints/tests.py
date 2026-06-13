from django.test import TestCase

from customers.models import Customer
from .models import CustomerComplaint


class ComplaintSiteTypeTests(TestCase):
    def test_site_type_comes_from_customer_category(self):
        customer = Customer.objects.create(
            customer_name="AMC Customer",
            phone_number="9999999999",
            customer_category="AMC",
        )
        complaint = CustomerComplaint.objects.create(
            customer=customer,
            site_type="GENERAL",
            complaint_title="Cooling issue",
        )
        self.assertEqual(complaint.site_type, "AMC")
