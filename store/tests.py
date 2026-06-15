from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from customers.models import Customer
from material_issue.models import MaterialIssue, MaterialIssueItem
from projects.models import CustomerProject

from .models import StoreCategory, StoreItem


class StoreItemRecalculationTests(TestCase):
    def test_add_requires_serial_number_and_has_searchable_category(self):
        user = User.objects.create_user("add-store-tester", password="test-pass")
        category = StoreCategory.objects.create(category_name="Searchable Category")
        self.client.force_login(user)

        response = self.client.post(
            reverse("add_store_item"),
            {
                "category": category.id,
                "item_description": "Test Item",
                "serial_number": "",
                "unit": "NOS",
                "opening_stock": "1",
                "minimum_stock": "0",
                "alert_percentage": "85",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Serial number is required.")
        self.assertContains(response, 'id="category-select"')
        self.assertContains(response, 'id="category-search"')
        self.assertContains(response, 'placeholder="Search category..."')
        self.assertFalse(StoreItem.objects.filter(item_description="Test Item").exists())

    def test_item_type_supports_all_checkbox_combinations(self):
        category = StoreCategory.objects.create(category_name="Type Category")
        neither = StoreItem.objects.create(
            category=category,
            item_description="Neither",
        )
        vrv = StoreItem.objects.create(
            category=category,
            item_description="VRV",
            is_vrv=True,
        )
        non_vrv = StoreItem.objects.create(
            category=category,
            item_description="Non VRV",
            is_non_vrv=True,
        )
        both = StoreItem.objects.create(
            category=category,
            item_description="Both",
            is_vrv=True,
            is_non_vrv=True,
        )

        self.assertEqual(neither.item_type_display, "-")
        self.assertEqual(vrv.item_type_display, "VRV")
        self.assertEqual(non_vrv.item_type_display, "Non-VRV")
        self.assertEqual(both.item_type_display, "VRV / Non-VRV")

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
                "is_non_vrv": "on",
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
