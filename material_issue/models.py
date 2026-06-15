# material_issue/models.py

from decimal import Decimal

from django.db import models, transaction
from django.db.models import Sum
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
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
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
        if not self.project_id and not (self.received_by or "").strip():
            raise ValidationError(
                "Select a project or enter the direct person/vendor name."
            )
        if self.boq_id and not self.project_id:
            raise ValidationError("A BOQ can only be selected with a project.")
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
        StoreTransaction.objects.filter(
            material_issue_item__material_issue=self
        ).update(
            purpose="PROJECT" if self.project_id else "GENERAL",
            project=self.project,
            boq=self.boq,
            issued_to=self.received_by or self.issued_to,
        )

    def total_items(self):
        return self.items.count()

    def __str__(self):
        destination = self.project or self.received_by or self.issued_to
        return f"{self.issue_id} - {destination}"


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
            + self.scrap_quantity
        )

        if total_used > self.issued_quantity:
            raise ValidationError(
                "Consumed + returned + scrap quantity cannot be greater than issued quantity."
            )

        previous_issued = Decimal("0.00")
        if self.pk:
            previous_issued = MaterialIssueItem.objects.only(
                "issued_quantity"
            ).get(pk=self.pk).issued_quantity
        additional_stock_needed = self.issued_quantity - previous_issued
        if additional_stock_needed > 0 and self.store_item.current_stock < additional_stock_needed:
            raise ValidationError(
                f"Not enough stock for {self.store_item.item_description}. "
                f"Available stock: {self.store_item.current_stock}"
            )

        if self.boq_item_id:
            if not self.material_issue.project_id:
                raise ValidationError("A BOQ item requires a project.")
            if self.boq_item.store_item_id != self.store_item_id:
                raise ValidationError("BOQ item and store item must refer to the same material.")
            if self.boq_item.boq.project_id != self.material_issue.project_id:
                raise ValidationError("BOQ item does not belong to the material issue project.")
            if self.material_issue.boq_id and self.boq_item.boq_id != self.material_issue.boq_id:
                raise ValidationError("BOQ item does not belong to the selected BOQ.")
            other_issued = MaterialIssueItem.objects.filter(
                boq_item=self.boq_item
            ).exclude(pk=self.pk).aggregate(
                total=Sum("issued_quantity")
            )["total"] or Decimal("0.00")
            if other_issued + self.issued_quantity > self.boq_item.required_quantity:
                raise ValidationError(
                    "Issued quantity cannot exceed the remaining BOQ quantity."
                )

    @transaction.atomic
    def save(self, *args, **kwargs):
        old_issued_quantity = Decimal("0.00")
        old_returned_quantity = Decimal("0.00")
        old_scrap_quantity = Decimal("0.00")
        old_boq_item_id = None
        if self.pk:
            old = MaterialIssueItem.objects.get(pk=self.pk)
            old_issued_quantity = old.issued_quantity
            old_returned_quantity = old.returned_quantity
            old_scrap_quantity = old.scrap_quantity
            old_boq_item_id = old.boq_item_id

        if (
            not self.boq_item_id
            and self.store_item_id
            and self.material_issue.project_id
        ):
            matching_boq_items = ProjectBOQItem.objects.filter(
                boq__project=self.material_issue.project,
                store_item_id=self.store_item_id,
            )
            if self.material_issue.boq_id:
                matching_boq_items = matching_boq_items.filter(
                    boq=self.material_issue.boq
                )
            if matching_boq_items.count() == 1:
                self.boq_item = matching_boq_items.first()

        if not self.pk and not self.serial_number and self.store_item_id:
            self.serial_number = self.store_item.serial_number
        elif (
            self.serial_number
            and self.store_item_id
            and self.store_item.serial_number != self.serial_number
        ):
            self.store_item.serial_number = self.serial_number
            self.store_item.save(update_fields=["serial_number"])

        self.clean()

        issued_delta = Decimal(self.issued_quantity) - old_issued_quantity
        if issued_delta:
            self.store_item.current_stock -= issued_delta
            self.store_item.save()
            self.is_stock_updated = True

        super().save(*args, **kwargs)
        self.sync_issue_transaction(old_issued_quantity)
        self.sync_return_transaction(old_returned_quantity)
        self.sync_scrap_transaction(old_scrap_quantity)
        self.sync_boq_totals(old_boq_item_id)
        self.sync_boq_totals(self.boq_item_id)

    def sync_issue_transaction(self, old_issued_quantity):
        if Decimal(self.issued_quantity) == Decimal(old_issued_quantity) and self.stock_transaction_id:
            return

        StoreTransaction.objects.filter(
            material_issue_item=self,
            transaction_type="OUT",
        ).delete()

        stock_after = self.store_item.current_stock
        is_project_issue = bool(self.material_issue.project_id)
        transaction = StoreTransaction.objects.create(
            item=self.store_item,
            transaction_type="OUT",
            purpose="PROJECT" if is_project_issue else "GENERAL",
            project=self.material_issue.project,
            boq=self.material_issue.boq,
            material_issue_item=self,
            quantity=self.issued_quantity,
            stock_before=stock_after + Decimal(self.issued_quantity),
            stock_after=stock_after,
            issued_to=self.material_issue.received_by or self.material_issue.issued_to,
            description=StoreTransaction.description_with_serial(
                f"Issued against {self.material_issue.issue_id}",
                self.serial_number or self.store_item.serial_number,
            ),
            is_stock_updated=True,
            created_by=self.material_issue.issued_by,
        )
        self.stock_transaction = transaction
        MaterialIssueItem.objects.filter(pk=self.pk).update(
            stock_transaction=transaction,
            is_stock_updated=True,
        )

    def sync_return_transaction(self, old_returned_quantity):
        return_quantity = Decimal(self.returned_quantity)
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
            is_project_issue = bool(self.material_issue.project_id)
            txn = StoreTransaction.objects.create(
                item=self.store_item,
                transaction_type="RETURN",
                purpose="PROJECT" if is_project_issue else "GENERAL",
                project=self.material_issue.project,
                boq=self.material_issue.boq,
                material_issue_item=self,
                quantity=return_quantity,
                issued_to=self.material_issue.received_by or self.material_issue.issued_to,
                description=StoreTransaction.description_with_serial(
                    f"Returned against {self.material_issue.issue_id}",
                    self.serial_number or self.store_item.serial_number,
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
            is_project_issue = bool(self.material_issue.project_id)
            txn = StoreTransaction.objects.create(
                item=self.store_item,
                transaction_type="SCRAP",
                purpose="PROJECT" if is_project_issue else "GENERAL",
                project=self.material_issue.project,
                boq=self.material_issue.boq,
                material_issue_item=self,
                quantity=self.scrap_quantity,
                stock_before=stock_now,
                stock_after=stock_now,
                issued_to=self.material_issue.received_by or self.material_issue.issued_to,
                description=StoreTransaction.description_with_serial(
                    f"Scrap against {self.material_issue.issue_id}: {self.scrap_reason or '-'}",
                    self.serial_number or self.store_item.serial_number,
                ),
                is_stock_updated=True,
                created_by=self.material_issue.issued_by,
            )
            self.scrap_stock_transaction = txn
            MaterialIssueItem.objects.filter(pk=self.pk).update(
                scrap_stock_transaction=self.scrap_stock_transaction
            )

    @staticmethod
    def sync_boq_totals(boq_item_id):
        if not boq_item_id:
            return
        totals = MaterialIssueItem.objects.filter(
            boq_item_id=boq_item_id
        ).aggregate(
            issued=Sum("issued_quantity"),
            consumed=Sum("consumed_quantity"),
            returned=Sum("returned_quantity"),
        )
        ProjectBOQItem.objects.filter(pk=boq_item_id).update(
            issued_quantity=totals["issued"] or Decimal("0.00"),
            consumed_quantity=totals["consumed"] or Decimal("0.00"),
            returned_quantity=totals["returned"] or Decimal("0.00"),
        )

    @transaction.atomic
    def delete(self, *args, **kwargs):
        boq_item_id = self.boq_item_id
        if self.is_stock_updated:
            self.store_item.current_stock += Decimal(self.issued_quantity)
            self.store_item.save()

        StoreTransaction.objects.filter(
            material_issue_item=self,
            transaction_type="OUT",
        ).delete()
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
        self.sync_boq_totals(boq_item_id)

    def balance_quantity(self):
        balance = (
            self.issued_quantity
            - self.consumed_quantity
            - self.returned_quantity
            - self.scrap_quantity
        )

        return balance if balance > 0 else Decimal("0.00")

    def __str__(self):
        return f"{self.material_issue.issue_id} - {self.store_item.item_description}"
