from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from customers.models import Customer
from projects.models import CustomerProject


class InsuranceAlertDashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="dashboard-user",
            password="test-password",
        )
        self.client.force_login(self.user)
        self.customer = Customer.objects.create(
            customer_name="Alert Customer",
            phone_number="7777777777",
        )

    def create_project(self, name, days, is_active=True):
        return CustomerProject.objects.create(
            customer=self.customer,
            site_name=name,
            insurance_end_date=timezone.localdate() + timedelta(days=days),
            is_active=is_active,
        )

    def test_popup_shows_only_active_insurance_expiring_within_seven_days(self):
        self.create_project("Expires Today", 0)
        self.create_project("Expires In Seven Days", 7)
        self.create_project("Expires In Eight Days", 8)
        self.create_project("Already Expired", -1)
        self.create_project("Inactive Project", 3, is_active=False)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="insurance-alert-modal"')
        self.assertContains(response, "Expires Today")
        self.assertContains(response, "Expires In Seven Days")
        self.assertNotContains(response, "Expires In Eight Days")
        self.assertNotContains(response, "Already Expired")
        self.assertNotContains(response, "Inactive Project")

    def test_popup_is_absent_when_no_insurance_is_expiring(self):
        self.create_project("Later Project", 8)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'id="insurance-alert-modal"')
