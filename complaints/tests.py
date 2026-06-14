from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from customers.models import Customer, CustomerServiceSchedule
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


class CustomerVisitHistoryTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            customer_name="Scheduled Customer",
            phone_number="8888888888",
            warranty_start_date=date(2026, 1, 1),
            warranty_end_date=date(2026, 12, 31),
            amc_start_date=date(2026, 1, 1),
            amc_end_date=date(2026, 12, 31),
        )

    def test_pending_auto_schedules_are_not_counted_as_visits(self):
        self.assertEqual(
            CustomerServiceSchedule.objects.filter(
                customer=self.customer
            ).count(),
            8,
        )

        response = self.client.get(
            reverse("customer_service_history_report"),
            {"search": self.customer.customer_id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Scheduled Customer")
        self.assertContains(
            response,
            '<p class="text-2xl font-black text-green-700">0</p>',
            html=True,
        )
        self.assertContains(response, "No completed visits.")

    def test_completed_schedule_uses_actual_completion_date(self):
        schedule = CustomerServiceSchedule.objects.filter(
            customer=self.customer
        ).first()
        actual_date = schedule.service_date + timedelta(days=5)
        schedule.status = "COMPLETED"
        schedule.completed_date = actual_date
        schedule.save()

        response = self.client.get(
            reverse("customer_service_history_report"),
            {"search": self.customer.customer_id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<p class="text-2xl font-black text-green-700">1</p>',
            html=True,
        )
        self.assertContains(response, actual_date.strftime("%d %b %Y"))
        self.assertNotContains(
            response,
            schedule.service_date.strftime("%d %b %Y"),
        )

    def test_pending_complaint_is_not_counted_until_completed(self):
        complaint = CustomerComplaint.objects.create(
            customer=self.customer,
            complaint_title="Cooling issue",
            visit_date=date(2026, 6, 20),
            status="PENDING",
        )

        response = self.client.get(
            reverse("customer_service_history_report"),
            {"search": self.customer.customer_id},
        )
        self.assertContains(
            response,
            '<p class="text-2xl font-black text-green-700">0</p>',
            html=True,
        )

        complaint.status = "COMPLETED"
        complaint.save()
        response = self.client.get(
            reverse("customer_service_history_report"),
            {"search": self.customer.customer_id},
        )
        self.assertContains(
            response,
            '<p class="text-2xl font-black text-green-700">1</p>',
            html=True,
        )
        self.assertContains(response, "20 Jun 2026")
