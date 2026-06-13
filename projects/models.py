# projects/models.py

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from customers.models import Customer


class CustomerProject(models.Model):

    PROJECT_STATUS_CHOICES = (
        ("PLANNING", "Planning"),
        ("ONGOING", "Ongoing"),
        ("MATERIAL_REQUIRED", "Material Required"),
        ("MATERIAL_ISSUED", "Material Issued"),
        ("INSTALLATION", "Installation"),
        ("TESTING", "Testing"),
        ("HOLD", "Hold"),
        ("COMMISSIONED", "Commissioned"),
        ("CANCELLED", "Cancelled"),
    )

    CAPACITY_UNIT_CHOICES = (
        ("TR", "TR"),
        ("HP", "HP"),
    )

    project_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        related_name="projects",
        blank=True,
        null=True
    )

    site_name = models.CharField(
        max_length=200,
        default="New Project Site"
    )

    location = models.CharField(
        max_length=250,
        blank=True,
        null=True,
        default="Muzaffarpur"
    )

    site_address = models.TextField(
        blank=True,
        null=True
    )

    capacity_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    capacity_unit = models.CharField(
        max_length=10,
        choices=CAPACITY_UNIT_CHOICES,
        default="TR"
    )

    project_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    start_date = models.DateField(
        blank=True,
        null=True
    )

    expected_completion_date = models.DateField(
        blank=True,
        null=True
    )

    actual_completion_date = models.DateField(
        blank=True,
        null=True
    )

    project_status = models.CharField(
        max_length=30,
        choices=PROJECT_STATUS_CHOICES,
        default="PLANNING"
    )

    material_consumed_notes = models.TextField(
        blank=True,
        null=True
    )

    material_collection_notes = models.TextField(
        blank=True,
        null=True
    )

    project_stage_notes = models.TextField(
        blank=True,
        null=True
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    insurance_start_date = models.DateField(
        blank=True,
        null=True
    )

    insurance_end_date = models.DateField(
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="created_projects"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-id"]
        verbose_name = "Customer Project"
        verbose_name_plural = "Customer Projects"

    def clean(self):
        if (
            self.start_date
            and self.expected_completion_date
            and self.expected_completion_date < self.start_date
        ):
            raise ValidationError(
                "Expected completion date cannot be before start date."
            )

        if (
            self.start_date
            and self.actual_completion_date
            and self.actual_completion_date < self.start_date
        ):
            raise ValidationError(
                "Actual completion date cannot be before start date."
            )

        if (
            self.insurance_start_date
            and self.insurance_end_date
            and self.insurance_end_date < self.insurance_start_date
        ):
            raise ValidationError(
                "Insurance end date cannot be before insurance start date."
            )

    def save(self, *args, **kwargs):
        self.clean()

        if not self.project_id:
            last_project = CustomerProject.objects.order_by("-id").first()
            new_id = last_project.id + 1 if last_project else 1
            self.project_id = f"PRJ{new_id:04d}"

        super().save(*args, **kwargs)

    def get_customer_name(self):
        if self.customer:
            return self.customer.customer_name
        return "No Customer"

    def get_customer_phone(self):
        if self.customer:
            return self.customer.phone_number
        return "-"

    def get_customer_company(self):
        if self.customer and self.customer.company_name:
            return self.customer.company_name
        return "-"

    def get_customer_city(self):
        if self.customer and self.customer.city:
            return self.customer.city
        return "-"

    def get_capacity_display_text(self):
        return f"{self.capacity_value} {self.capacity_unit}"

    def insurance_days_remaining(self):
        from django.utils import timezone
        if self.insurance_end_date:
            today = timezone.localdate()
            delta = (self.insurance_end_date - today).days
            return delta
        return None

    def is_insurance_expiring_soon(self):
        """Returns True if insurance expires within 7 days and has not expired."""
        days = self.insurance_days_remaining()
        if days is None:
            return False
        return 0 <= days <= 7

    def is_insurance_active(self):
        from django.utils import timezone
        if not self.insurance_end_date:
            return False
        return self.insurance_end_date >= timezone.localdate()

    def is_on_hold(self):
        return self.project_status == "HOLD"

    def is_commissioned(self):
        return self.project_status == "COMMISSIONED"

    def __str__(self):
        return f"{self.project_id} - {self.get_customer_name()} - {self.site_name}"
