from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from customers.models import Customer
from material_issue.models import MaterialIssue, MaterialIssueItem
from projects.models import CustomerProject

from .models import StoreCategory, StoreItem


class StoreItemRecalculationTests(TestCase):
    def test_edit_keeps_material_issue_deduction_in_current_stock(self):
        user = User.objects.create_user("store-tester", password="test-pass")
        customer = Customer.objects.create(
            customer_name="Stock Customer",
            phone_number="9999999999",
        )
        project = CustomerProject.objects.create(
            customer=customer,
            site_name="Stock Site",
        )
        category = StoreCategory.objects.create(category_name="Stock Test")
        item = StoreItem.objects.create(
            category=category,
            item_description="VRV Unit",
            is_vrv=True,
            opening_stock=Decimal("10"),
            current_stock=Decimal("10"),
            minimum_stock=Decimal("1"),
        )
        issue = MaterialIssue.objects.create(project=project, issued_by=user)
        MaterialIssueItem.objects.create(
            material_issue=issue,
            store_item=item,
            issued_quantity=Decimal("4"),
        )

        self.client.force_login(user)
        response = self.client.post(
            reverse("edit_store_item", args=[item.id]),
            {
                "category": category.id,
                "item_description": item.item_description,
                "size": "",
                "serial_number": "",
                "remarks": "",
                "is_vrv": "on",
                "unit": "NOS",
                "opening_stock": "10",
                "minimum_stock": "1",
                "alert_percentage": "85",
            },
        )

        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.current_stock, Decimal("6"))

# Create your tests here.
