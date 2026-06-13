# material_issue/models.py

from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from projects.models import CustomerProject
from boq.models import ProjectBOQ, ProjectBOQItem
from store.models import StoreItem, StoreTransaction


class MaterialIssue(models.Model):

    STATUS_CHOICES = (
        ("DRAFT", "Draft"),
        ("ISSUED", "Issued"),
        ("PARTIAL_RETURN", "Partial Return"),
        ("RETURNED", "Returned"),
        ("CANCELLED", "Cancelled"),
    )

    issue_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    project = models.ForeignKey(
        CustomerProject,
        on_delete=models.CASCADE,
        related_name="material_issues"
    )

    boq = models.ForeignKey(
        ProjectBOQ,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="material_issues"
    )

    issue_date = models.DateField(auto_now_add=True)

    issued_to = models.CharField(
        max_length=200,
        default="Site Engineer"
    )

    received_by = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT"
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    issue_file = models.FileField(
        upload_to="material_issue_files/",
        blank=True,
        null=True
    )

    issued_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="material_issues_created"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]

    def save(self, *args, **kwargs):
        if not self.issue_id:
            last_issue = MaterialIssue.objects.order_by("-id").first()
            new_id = last_issue.id + 1 if last_issue else 1
            self.issue_id = f"MIS{new_id:04d}"

        super().save(*args, **kwargs)

    def total_items(self):
        return self.items.count()

    def __str__(self):
        return f"{self.issue_id} - {self.project}"


class MaterialIssueItem(models.Model):

    material_issue = models.ForeignKey(
        MaterialIssue,
        on_delete=models.CASCADE,
        related_name="items"
    )

    store_item = models.ForeignKey(
        StoreItem,
        on_delete=models.CASCADE,
        related_name="material_issue_items"
    )

    boq_item = models.ForeignKey(
        ProjectBOQItem,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="material_issue_items"
    )

    issued_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    consumed_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    returned_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    stock_transaction = models.ForeignKey(
        StoreTransaction,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="material_issue_items"
    )

    is_stock_updated = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def clean(self):
        if self.issued_quantity <= 0:
            raise ValidationError("Issued quantity must be greater than 0.")

        if self.consumed_quantity < 0:
            raise ValidationError("Consumed quantity cannot be negative.")

        if self.returned_quantity < 0:
            raise ValidationError("Returned quantity cannot be negative.")

        if self.consumed_quantity > self.issued_quantity:
            raise ValidationError(
                "Consumed quantity cannot be greater than issued quantity."
            )

        if self.returned_quantity > self.issued_quantity:
            raise ValidationError(
                "Returned quantity cannot be greater than issued quantity."
            )

        total_used = self.consumed_quantity + self.returned_quantity

        if total_used > self.issued_quantity:
            raise ValidationError(
                "Consumed + returned quantity cannot be greater than issued quantity."
            )

        if not self.pk and self.store_item.current_stock < self.issued_quantity:
            raise ValidationError(
                f"Not enough stock for {self.store_item.item_description}. "
                f"Available stock: {self.store_item.current_stock}"
            )

    def save(self, *args, **kwargs):
        self.clean()

        if not self.pk and not self.is_stock_updated:
            self.store_item.current_stock -= Decimal(self.issued_quantity)
            self.store_item.save()

            self.is_stock_updated = True

            if self.boq_item:
                self.boq_item.issued_quantity += Decimal(self.issued_quantity)
                self.boq_item.save()

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.is_stock_updated:
            self.store_item.current_stock += Decimal(self.issued_quantity)
            self.store_item.save()

            if self.boq_item:
                self.boq_item.issued_quantity -= Decimal(self.issued_quantity)

                if self.boq_item.issued_quantity < 0:
                    self.boq_item.issued_quantity = Decimal("0.00")

                self.boq_item.save()

        super().delete(*args, **kwargs)

    def balance_quantity(self):
        balance = (
            self.issued_quantity
            - self.consumed_quantity
            - self.returned_quantity
        )

        return balance if balance > 0 else Decimal("0.00")

    def __str__(self):
        return f"{self.material_issue.issue_id} - {self.store_item.item_description}"