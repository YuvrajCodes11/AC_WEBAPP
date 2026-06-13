# boq/models.py

from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

from projects.models import CustomerProject
from store.models import StoreItem


class ProjectBOQ(models.Model):

    BOQ_STATUS_CHOICES = (
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("CLOSED", "Closed"),
    )

    boq_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    project = models.ForeignKey(
        CustomerProject,
        on_delete=models.CASCADE,
        related_name="boqs",
        blank=True,
        null=True
    )

    title = models.CharField(
        max_length=200,
        default="Project BOQ"
    )

    status = models.CharField(
        max_length=20,
        choices=BOQ_STATUS_CHOICES,
        default="DRAFT"
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="boq_created_by"
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="boq_approved_by"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-id"]

    def save(self, *args, **kwargs):
        if not self.boq_id:
            last_boq = ProjectBOQ.objects.order_by("-id").first()
            new_id = last_boq.id + 1 if last_boq else 1
            self.boq_id = f"BOQ{new_id:04d}"

        if self.status == "APPROVED" and not self.approved_at:
            self.approved_at = timezone.now()

        super().save(*args, **kwargs)

    def total_items(self):
        return self.items.count()

    def total_amount(self):
        total = Decimal("0.00")

        for item in self.items.all():
            total += item.total_amount()

        return total

    def __str__(self):
        project_str = self.project.project_id if self.project else "No Project"
        return f"{self.boq_id} - {project_str}"


class ProjectBOQItem(models.Model):

    boq = models.ForeignKey(
        ProjectBOQ,
        on_delete=models.CASCADE,
        related_name="items"
    )

    store_item = models.ForeignKey(
        StoreItem,
        on_delete=models.CASCADE,
        related_name="boq_items"
    )

    required_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
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

    rate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        unique_together = ("boq", "store_item")

    def clean(self):
        if self.required_quantity < 0:
            raise ValidationError("Required quantity cannot be negative.")

        if self.issued_quantity < 0:
            raise ValidationError("Issued quantity cannot be negative.")

        if self.consumed_quantity < 0:
            raise ValidationError("Consumed quantity cannot be negative.")

        if self.returned_quantity < 0:
            raise ValidationError("Returned quantity cannot be negative.")

        if self.issued_quantity > self.required_quantity:
            raise ValidationError(
                "Issued quantity cannot be greater than required quantity."
            )

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
                "Consumed quantity plus returned quantity cannot be greater than issued quantity."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def balance_quantity(self):
        balance = self.required_quantity - self.issued_quantity
        return balance if balance > 0 else Decimal("0.00")

    def pending_collection_quantity(self):
        pending = self.issued_quantity - self.consumed_quantity - self.returned_quantity
        return pending if pending > 0 else Decimal("0.00")

    def total_amount(self):
        return self.required_quantity * self.rate

    def __str__(self):
        return f"{self.boq.boq_id} - {self.store_item.item_description}"


# Temporary backward compatibility for old imports.
BOQItem = ProjectBOQItem