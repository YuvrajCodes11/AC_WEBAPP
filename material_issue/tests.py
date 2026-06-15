import re
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from boq.models import ProjectBOQ, ProjectBOQItem
from customers.models import Customer
from projects.models import CustomerProject
from store.models import StoreCategory, StoreItem, StoreTransaction
from .models import MaterialIssue, MaterialIssueItem


class MaterialIssueStockTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("tester")
        self.customer = Customer.objects.create(
            customer_name="Test Customer",
            phone_number="9999999999",
        )
        self.project = CustomerProject.objects.create(
            customer=self.customer,
            site_name="Test Site",
        )
        self.category = StoreCategory.objects.create(category_name="Machines")
        self.item = StoreItem.objects.create(
            category=self.category,
            item_description="Outdoor Unit",
            serial_number="SN-100",
            is_vrv=True,
            opening_stock=Decimal("10"),
            current_stock=Decimal("10"),
        )
        self.boq = ProjectBOQ.objects.create(
            project=self.project,
            created_by=self.user,
        )
        self.boq_item = ProjectBOQItem.objects.create(
            boq=self.boq,
            store_item=self.item,
            required_quantity=Decimal("8"),
        )
        self.issue = MaterialIssue.objects.create(
            project=self.project,
            boq=self.boq,
            heading="Site Material",
            issued_by=self.user,
        )

    def test_issue_return_scrap_and_delete_are_synchronised(self):
        issue_item = MaterialIssueItem.objects.create(
            material_issue=self.issue,
            store_item=self.item,
            boq_item=self.boq_item,
            issued_quantity=Decimal("6"),
        )
        self.item.refresh_from_db()
        self.boq_item.refresh_from_db()
        self.assertEqual(self.item.current_stock, Decimal("4"))
        self.assertEqual(self.boq_item.issued_quantity, Decimal("6"))
        self.assertEqual(issue_item.serial_number, "SN-100")

        issue_item.consumed_quantity = Decimal("1")
        issue_item.returned_quantity = Decimal("3")
        issue_item.scrap_quantity = Decimal("1")
        issue_item.scrap_reason = "Damaged at site"
        issue_item.save()

        self.item.refresh_from_db()
        self.assertEqual(self.item.current_stock, Decimal("7"))
        self.assertEqual(issue_item.balance_quantity(), Decimal("1"))
        self.assertEqual(
            StoreTransaction.objects.filter(
                material_issue_item=issue_item,
                transaction_type="RETURN",
            ).get().quantity,
            Decimal("3"),
        )
        self.assertEqual(
            StoreTransaction.objects.filter(
                material_issue_item=issue_item,
                transaction_type="SCRAP",
            ).get().quantity,
            Decimal("1"),
        )

        issue_item.delete()
        self.item.refresh_from_db()
        self.boq_item.refresh_from_db()
        self.assertEqual(self.item.current_stock, Decimal("10"))
        self.assertEqual(self.boq_item.issued_quantity, Decimal("0"))
        self.assertEqual(self.boq_item.consumed_quantity, Decimal("0"))
        self.assertEqual(self.boq_item.returned_quantity, Decimal("0"))

    def test_edit_synchronises_store_boq_and_serial_number(self):
        issue_item = MaterialIssueItem.objects.create(
            material_issue=self.issue,
            store_item=self.item,
            boq_item=self.boq_item,
            issued_quantity=Decimal("4"),
            serial_number="SITE-SN-200",
        )

        issue_item.issued_quantity = Decimal("6")
        issue_item.consumed_quantity = Decimal("2")
        issue_item.returned_quantity = Decimal("1")
        issue_item.save()

        self.item.refresh_from_db()
        self.boq_item.refresh_from_db()
        self.assertEqual(self.item.current_stock, Decimal("5"))
        self.assertEqual(self.item.serial_number, "SITE-SN-200")
        self.assertEqual(self.boq_item.issued_quantity, Decimal("6"))
        self.assertEqual(self.boq_item.consumed_quantity, Decimal("2"))
        self.assertEqual(self.boq_item.returned_quantity, Decimal("1"))
        self.assertEqual(
            StoreTransaction.objects.filter(
                material_issue_item=issue_item,
                transaction_type="OUT",
            ).get().quantity,
            Decimal("6"),
        )

    def test_unique_project_boq_item_is_linked_automatically(self):
        issue_without_boq = MaterialIssue.objects.create(
            project=self.project,
            heading="Automatic Link",
            issued_by=self.user,
        )

        issue_item = MaterialIssueItem.objects.create(
            material_issue=issue_without_boq,
            store_item=self.item,
            issued_quantity=Decimal("3"),
        )

        issue_item.refresh_from_db()
        self.boq_item.refresh_from_db()
        self.assertEqual(issue_item.boq_item, self.boq_item)
        self.assertEqual(self.boq_item.issued_quantity, Decimal("3"))

    def test_add_page_lists_new_and_inactive_projects(self):
        inactive_project = CustomerProject.objects.create(
            customer=self.customer,
            site_name="Inactive But Visible",
            is_active=False,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("add_material_issue"))

        self.assertContains(response, self.project.project_id)
        self.assertContains(response, inactive_project.project_id)
        self.assertContains(response, "Inactive But Visible")

    def test_add_item_rejects_boq_item_for_different_store_item(self):
        other_item = StoreItem.objects.create(
            category=self.category,
            item_description="Different Unit",
            opening_stock=Decimal("10"),
            current_stock=Decimal("10"),
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("add_material_issue_item", args=[self.issue.id]),
            {
                "category": self.category.id,
                "store_item": other_item.id,
                "boq_item": self.boq_item.id,
                "issued_quantity": "2",
                "serial_number": "",
                "remarks": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No ProjectBOQItem matches the given query")
        self.assertFalse(
            MaterialIssueItem.objects.filter(
                material_issue=self.issue,
                store_item=other_item,
            ).exists()
        )

    def test_delete_item_restores_store_and_boq_values(self):
        issue_item = MaterialIssueItem.objects.create(
            material_issue=self.issue,
            store_item=self.item,
            boq_item=self.boq_item,
            issued_quantity=Decimal("4"),
            consumed_quantity=Decimal("1"),
            returned_quantity=Decimal("1"),
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("delete_material_issue_item", args=[issue_item.id])
        )

        self.assertEqual(response.status_code, 302)
        self.item.refresh_from_db()
        self.boq_item.refresh_from_db()
        self.assertEqual(self.item.current_stock, Decimal("10"))
        self.assertEqual(self.boq_item.issued_quantity, Decimal("0"))
        self.assertEqual(self.boq_item.consumed_quantity, Decimal("0"))
        self.assertEqual(self.boq_item.returned_quantity, Decimal("0"))

    def test_unrelated_boq_is_rejected(self):
        other_project = CustomerProject.objects.create(site_name="Other Site")
        other_boq = ProjectBOQ.objects.create(project=other_project)
        invalid_issue = MaterialIssue(project=self.project, boq=other_boq)
        with self.assertRaises(ValidationError):
            invalid_issue.save()

    def test_issue_cannot_exceed_boq_quantity(self):
        with self.assertRaises(ValidationError):
            MaterialIssueItem.objects.create(
                material_issue=self.issue,
                store_item=self.item,
                boq_item=self.boq_item,
                issued_quantity=Decimal("9"),
            )

    def test_material_ledger_column_order(self):
        MaterialIssueItem.objects.create(
            material_issue=self.issue,
            store_item=self.item,
            boq_item=self.boq_item,
            issued_quantity=Decimal("6"),
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("material_issue_detail", args=[self.issue.id])
        )

        self.assertEqual(response.status_code, 200)
        ledger = response.content.decode().split("Material Items Ledger", 1)[1]
        headings = [
            "Item Description",
            "Category",
            "Size",
            "Unit",
            "BOQ Quantity",
            "Sent",
            "BOQ Balance",
            "Consumed",
            "Returned",
            "Scrap",
            "Balance",
            "Remarks",
            "Action",
        ]
        table_head = ledger.split("</thead>", 1)[0]
        rendered_headings = [
            heading.strip()
            for heading in re.findall(
                r"<th[^>]*>\s*([^<]+?)\s*</th>",
                table_head,
            )
        ]
        self.assertEqual(rendered_headings, headings)
        self.assertContains(response, str(self.boq_item.required_quantity))
        self.assertNotContains(response, "Not Used")

    def test_direct_person_issue_without_project_updates_store(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("add_material_issue"),
            {
                "project": "",
                "boq": "",
                "heading": "Direct Vendor Issue",
                "issued_to": "Vendor",
                "received_by": "Sharma Traders",
                "status": "ISSUED",
                "category": [str(self.category.id)],
                "store_item": [str(self.item.id)],
                "boq_item": [""],
                "issued_quantity": ["2"],
                "serial_number": ["SN-100"],
                "item_remarks": ["Direct issue"],
            },
        )

        self.assertEqual(response.status_code, 302)
        direct_issue = MaterialIssue.objects.get(heading="Direct Vendor Issue")
        self.assertIsNone(direct_issue.project)
        self.assertEqual(direct_issue.received_by, "Sharma Traders")
        direct_item = direct_issue.items.get()
        self.item.refresh_from_db()
        self.assertEqual(self.item.current_stock, Decimal("8"))
        self.assertIsNone(direct_item.boq_item)
        transaction = StoreTransaction.objects.get(
            material_issue_item=direct_item,
            transaction_type="OUT",
        )
        self.assertEqual(transaction.purpose, "GENERAL")
        self.assertIsNone(transaction.project)
        self.assertEqual(transaction.issued_to, "Sharma Traders")

        detail = self.client.get(
            reverse("material_issue_detail", args=[direct_issue.id])
        )
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Direct Issue - Sharma Traders")

        direct_issue.project = self.project
        direct_issue.received_by = ""
        direct_issue.save()
        transaction.refresh_from_db()
        self.assertEqual(transaction.purpose, "PROJECT")
        self.assertEqual(transaction.project, self.project)

    def test_direct_issue_requires_person_or_project(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("add_material_issue"),
            {
                "project": "",
                "boq": "",
                "heading": "Invalid Direct Issue",
                "received_by": "",
                "status": "ISSUED",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Select a project or enter the direct person/vendor name.",
        )
        self.assertFalse(
            MaterialIssue.objects.filter(heading="Invalid Direct Issue").exists()
        )
