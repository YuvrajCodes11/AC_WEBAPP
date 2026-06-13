from django.db import models
from django.utils import timezone

from customers.models import Customer


class CustomerComplaint(models.Model):

    SITE_TYPE_CHOICES = (
        ("WARRANTY", "Warranty Site"),
        ("AMC", "AMC Site"),
        ("GENERAL", "General Site"),
    )

    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
        ("PARTIAL", "Partial Work"),
    )

    complaint_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="complaints"
    )

    site_type = models.CharField(
        max_length=20,
        choices=SITE_TYPE_CHOICES,
        default="GENERAL"
    )

    visit_date = models.DateField(
        default=timezone.localdate
    )

    no_of_technicians = models.PositiveIntegerField(
        default=1
    )

    complaint_title = models.CharField(
        max_length=200
    )

    complaint_description = models.TextField(
        blank=True,
        null=True
    )

    work_done = models.TextField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-visit_date", "-id"]

    def save(self, *args, **kwargs):
        if not self.complaint_id:
            last_complaint = CustomerComplaint.objects.order_by("-id").first()
            new_id = last_complaint.id + 1 if last_complaint else 1
            self.complaint_id = f"CMP{new_id:04d}"

        if self.customer_id:
            if self.customer.customer_category == "WARRANTY":
                self.site_type = "WARRANTY"
            elif self.customer.customer_category == "AMC":
                self.site_type = "AMC"
            else:
                self.site_type = "GENERAL"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.complaint_id} - {self.customer.customer_name}"
