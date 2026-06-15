from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from customers.models import Customer
from projects.models import CustomerProject
from store.models import StoreCategory, StoreItem

from .models import ProjectBOQ, ProjectBOQItem


class BOQPdfFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="pdf-user",
            password="test-password",
        )
        self.client.force_login(self.user)
        self.customer = Customer.objects.create(
            customer_name="PDF Customer",
            phone_number="8888888888",
        )
        self.project = CustomerProject.objects.create(
            customer=self.customer,
            site_name="PDF Site",
            insurance_start_date=timezone.localdate(),
            insurance_end_date=timezone.localdate() + timedelta(days=7),
        )
        category = StoreCategory.objects.create(category_name="PDF Category")
        self.item = StoreItem.objects.create(
            category=category,
            item_description="VRV Indoor Unit",
            is_vrv=True,
            opening_stock=Decimal("5.00"),
            current_stock=Decimal("5.00"),
        )

    def test_boq_pdf_supports_boq_without_project(self):
        boq = ProjectBOQ.objects.create(project=None)
        ProjectBOQItem.objects.create(
            boq=boq,
            store_item=self.item,
            required_quantity=Decimal("2.00"),
        )

        response = self.client.get(reverse("boq_pdf_report", args=[boq.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertTrue(response["Content-Disposition"].startswith("inline;"))

    def test_project_pdf_renders_linked_project_data(self):
        response = self.client.get(
            reverse("project_full_pdf_report", args=[self.project.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertTrue(response["Content-Disposition"].startswith("inline;"))

    def test_add_boq_initializes_category_search_for_each_new_row(self):
        response = self.client.get(reverse("add_boq"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "initializeSingleCategorySearch")
        self.assertContains(
            response,
            "initializeSingleCategorySearch(categorySelect)",
        )
        self.assertContains(response, "overflow-wrap: anywhere")

    def test_boq_detail_displays_full_item_description_and_synced_columns(self):
        long_description = (
            "VRV indoor cassette unit with complete control assembly and accessories"
        )
        self.item.item_description = long_description
        self.item.size = "Large ceiling cassette"
        self.item.save()
        boq = ProjectBOQ.objects.create(project=self.project)
        ProjectBOQItem.objects.create(
            boq=boq,
            store_item=self.item,
            required_quantity=Decimal("4"),
            issued_quantity=Decimal("3"),
            consumed_quantity=Decimal("1"),
            returned_quantity=Decimal("1"),
        )

        response = self.client.get(reverse("boq_detail", args=[boq.id]))

        self.assertContains(response, long_description)
        self.assertContains(response, "Large ceiling cassette")
        self.assertContains(response, "Consumed")
        self.assertContains(response, "Returned")
