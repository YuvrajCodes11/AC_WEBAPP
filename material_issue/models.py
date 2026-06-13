# material_issue/models.py

from decimal import Decimal

from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

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

    heading = models.CharField(
        max_length=250,
        default="Material Issue"
    )

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

    def clean(self):
        if self.boq_id and self.boq.project_id != self.project_id:
            raise ValidationError("Selected BOQ does not belong to the selected project.")
        if self.pk:
            for item in self.items.select_related("boq_item__boq"):
                if item.boq_item_id and item.boq_item.boq.project_id != self.project_id:
                    raise ValidationError(
                        "Project cannot be changed because existing issue items belong to another project BOQ."
                    )
                if self.boq_id and item.boq_item_id and item.boq_item.boq_id != self.boq_id:
                    raise ValidationError(
                        "BOQ cannot be changed because existing issue items belong to another BOQ."
                    )

    def save(self, *args, **kwargs):
        self.clean()
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

    unused_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    scrap_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    scrap_date = models.DateField(
        blank=True,
        null=True
    )

    scrap_reason = models.TextField(
        blank=True,
        null=True
    )

    serial_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
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

    return_stock_transaction = models.ForeignKey(
        StoreTransaction,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="material_issue_return_items"
    )

    scrap_stock_transaction = models.ForeignKey(
        StoreTransaction,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="material_issue_scrap_items"
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

        if self.unused_quantity < 0:
            raise ValidationError("Unused quantity cannot be negative.")

        if self.scrap_quantity < 0:
            raise ValidationError("Scrap quantity cannot be negative.")

        if self.consumed_quantity > self.issued_quantity:
            raise ValidationError(
                "Consumed quantity cannot be greater than issued quantity."
            )

        if self.returned_quantity > self.issued_quantity:
            raise ValidationError(
                "Returned quantity cannot be greater than issued quantity."
            )

        total_used = (
            self.consumed_quantity
            + self.returned_quantity
            + self.unused_quantity
            + self.scrap_quantity
        )

        if total_used > self.issued_quantity:
            raise ValidationError(
                "Consumed + returned + unused + scrap quantity cannot be greater than issued quantity."
            )

        if not self.pk and self.store_item.current_stock < self.issued_quantity:
            raise ValidationError(
                f"Not enough stock for {self.store_item.item_description}. "
                f"Available stock: {self.store_item.current_stock}"
            )

        if self.boq_item_id:
            if self.boq_item.store_item_id != self.store_item_id:
                raise ValidationError("BOQ item and store item must refer to the same material.")
            if self.boq_item.boq.project_id != self.material_issue.project_id:
                raise ValidationError("BOQ item does not belong to the material issue project.")
            if self.material_issue.boq_id and self.boq_item.boq_id != self.material_issue.boq_id:
                raise ValidationError("BOQ item does not belong to the selected BOQ.")

    @transaction.atomic
    def save(self, *args, **kwargs):
        old_returned_quantity = Decimal("0.00")
        old_unused_quantity = Decimal("0.00")
        old_scrap_quantity = Decimal("0.00")
        if self.pk:
            old = MaterialIssueItem.objects.get(pk=self.pk)
            old_returned_quantity = old.returned_quantity
            old_unused_quantity = old.unused_quantity
            old_scrap_quantity = old.scrap_quantity

        if not self.serial_number and self.store_item_id:
            self.serial_number = self.store_item.serial_number

        self.clean()

        if not self.pk and not self.is_stock_updated:
            self.store_item.current_stock -= Decimal(self.issued_quantity)
            self.store_item.save()

            self.is_stock_updated = True

            if self.boq_item:
                self.boq_item.issued_quantity += Decimal(self.issued_quantity)
                self.boq_item.save()

        super().save(*args, **kwargs)
        self.sync_return_transaction(old_returned_quantity + old_unused_quantity)
        self.sync_scrap_transaction(old_scrap_quantity)

    def sync_return_transaction(self, old_returned_quantity):
        return_quantity = Decimal(self.returned_quantity) + Decimal(self.unused_quantity)
        delta = return_quantity - Decimal(old_returned_quantity)
        if delta == 0:
            return

        if old_returned_quantity > 0 and self.store_item.current_stock < old_returned_quantity:
            raise ValidationError(
                f"Not enough stock to update returned quantity for {self.store_item.item_description}."
            )

        for txn in StoreTransaction.objects.filter(
            material_issue_item=self,
            transaction_type="RETURN",
        ):
            txn.delete()
        self.return_stock_transaction = None

        if return_quantity > 0:
            txn = StoreTransaction.objects.create(
                item=self.store_item,
                transaction_type="RETURN",
                purpose="PROJECT",
                project=self.material_issue.project,
                boq=self.material_issue.boq,
                material_issue_item=self,
                quantity=return_quantity,
                issued_to=self.material_issue.issued_to,
                description=(
                    f"Return/unused against {self.material_issue.issue_id} "
                    f"(returned {self.returned_quantity}, unused {self.unused_quantity})"
                ),
                created_by=self.material_issue.issued_by,
            )
            self.return_stock_transaction = txn

        MaterialIssueItem.objects.filter(pk=self.pk).update(
            return_stock_transaction=self.return_stock_transaction
        )

    def sync_scrap_transaction(self, old_scrap_quantity):
        delta = Decimal(self.scrap_quantity) - Decimal(old_scrap_quantity)
        if delta == 0:
            return

        if self.scrap_quantity > 0 and not self.scrap_date:
            self.scrap_date = timezone.localdate()
            MaterialIssueItem.objects.filter(pk=self.pk).update(scrap_date=self.scrap_date)

        for txn in StoreTransaction.objects.filter(
            material_issue_item=self,
            transaction_type="SCRAP",
        ):
            txn.delete()
        self.scrap_stock_transaction = None

        stock_now = self.store_item.current_stock
        if self.scrap_quantity > 0:
            txn = StoreTransaction.objects.create(
                item=self.store_item,
                transaction_type="SCRAP",
                purpose="PROJECT",
                project=self.material_issue.project,
                boq=self.material_issue.boq,
                material_issue_item=self,
                quantity=self.scrap_quantity,
                stock_before=stock_now,
                stock_after=stock_now,
                issued_to=self.material_issue.issued_to,
                description=f"Scrap against {self.material_issue.issue_id}: {self.scrap_reason or '-'}",
                is_stock_updated=True,
                created_by=self.material_issue.issued_by,
            )
            self.scrap_stock_transaction = txn
            MaterialIssueItem.objects.filter(pk=self.pk).update(
                scrap_stock_transaction=self.scrap_stock_transaction
            )

    @transaction.atomic
    def delete(self, *args, **kwargs):
        if self.is_stock_updated:
            self.store_item.current_stock += Decimal(self.issued_quantity)
            self.store_item.save()

            if self.boq_item:
                self.boq_item.issued_quantity -= Decimal(self.issued_quantity)

                if self.boq_item.issued_quantity < 0:
                    self.boq_item.issued_quantity = Decimal("0.00")

                self.boq_item.save()

        for txn in StoreTransaction.objects.filter(
            material_issue_item=self,
            transaction_type="RETURN",
        ):
            txn.delete()
        for txn in StoreTransaction.objects.filter(
            material_issue_item=self,
            transaction_type="SCRAP",
        ):
            txn.delete()

        super().delete(*args, **kwargs)

    def balance_quantity(self):
        balance = (
            self.issued_quantity
            - self.consumed_quantity
            - self.returned_quantity
            - self.unused_quantity
            - self.scrap_quantity
        )

        return balance if balance > 0 else Decimal("0.00")

    def __str__(self):
        return f"{self.material_issue.issue_id} - {self.store_item.item_description}"
