from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from boq.models import ProjectBOQ, ProjectBOQItem
from customers.models import Customer
from material_issue.models import MaterialIssue, MaterialIssueItem
from projects.models import CustomerProject
from store.models import StoreCategory, StoreItem


class ReportFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="report-user",
            password="test-password",
        )
        self.client.force_login(self.user)
        self.customer = Customer.objects.create(
            customer_name="Test Customer",
            phone_number="9999999999",
        )
        self.project = CustomerProject.objects.create(
            customer=self.customer,
            site_name="Test Site",
        )
        category = StoreCategory.objects.create(category_name="AC")
        self.item = StoreItem.objects.create(
            category=category,
            item_description="Outdoor Unit",
            is_vrv=True,
            opening_stock=Decimal("10.00"),
            current_stock=Decimal("10.00"),
        )

    def test_reports_render_and_exports_include_vrv_type(self):
        boq = ProjectBOQ.objects.create(project=self.project)
        boq_item = ProjectBOQItem.objects.create(
            boq=boq,
            store_item=self.item,
            required_quantity=Decimal("5.00"),
        )
        issue = MaterialIssue.objects.create(
            project=self.project,
            boq=boq,
        )
        MaterialIssueItem.objects.create(
            material_issue=issue,
            store_item=self.item,
            boq_item=boq_item,
            issued_quantity=Decimal("2.00"),
            consumed_quantity=Decimal("1.00"),
        )

        for name in (
            "reports:reports_dashboard",
            "reports:store_report",
            "reports:boq_vs_issued_report",
            "reports:project_consumption_report",
        ):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200)

        for name in (
            "reports:export_store_report",
            "reports:export_boq_vs_issued_report",
            "reports:export_project_consumption_report",
        ):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200)
            self.assertIn("VRV", response.content.decode())

    def test_boq_report_supports_boq_without_project(self):
        boq = ProjectBOQ.objects.create(project=None)
        ProjectBOQItem.objects.create(
            boq=boq,
            store_item=self.item,
            required_quantity=Decimal("3.00"),
        )

        response = self.client.get(reverse("reports:boq_vs_issued_report"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No Project Linked")
        self.assertContains(response, "No Customer")
