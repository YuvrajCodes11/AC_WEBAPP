# amc/models.py

from datetime import timedelta

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

from customers.models import Customer


class AMCContract(models.Model):

    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('HOLD', 'Hold'),
        ('CANCELLED', 'Cancelled'),
    )

    FREQUENCY_CHOICES = (
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('HALF_YEARLY', 'Half Yearly'),
        ('YEARLY', 'Yearly'),
    )

    amc_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='amc_contracts'
    )

    contract_start_date = models.DateField()

    contract_end_date = models.DateField(
        blank=True,
        null=True
    )

    contract_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    services_per_year = models.PositiveIntegerField(default=4)

    service_frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='QUARTERLY'
    )

    technician_name = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def clean(self):
        if self.contract_start_date and self.contract_end_date:
            if self.contract_end_date < self.contract_start_date:
                raise ValidationError(
                    "AMC end date cannot be before AMC start date."
                )

    def save(self, *args, **kwargs):

        if self.contract_start_date and not self.contract_end_date:
            self.contract_end_date = self.contract_start_date + timedelta(days=365)

        self.clean()

        if not self.amc_id:

            last_amc = AMCContract.objects.order_by("-id").first()

            if last_amc:
                new_id = last_amc.id + 1
            else:
                new_id = 1

            self.amc_id = f"AMC{new_id:04d}"

        if self.contract_end_date and self.contract_end_date < timezone.localdate():
            self.status = "EXPIRED"

        super().save(*args, **kwargs)

    def is_expiring_soon(self):

        if not self.contract_end_date:
            return False

        today = timezone.localdate()

        days_left = (self.contract_end_date - today).days

        return 0 <= days_left <= 30

    def days_left(self):

        if not self.contract_end_date:
            return None

        today = timezone.localdate()

        return (self.contract_end_date - today).days

    def __str__(self):
        return f"{self.amc_id} - {self.customer.customer_name}"


class AMCVisit(models.Model):

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('MISSED', 'Missed'),
        ('RESCHEDULED', 'Rescheduled'),
    )

    visit_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    amc = models.ForeignKey(
        AMCContract,
        on_delete=models.CASCADE,
        related_name='visits'
    )

    visit_date = models.DateField()

    technician_name = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    work_done = models.TextField(
        blank=True,
        null=True
    )

    customer_feedback = models.TextField(
        blank=True,
        null=True
    )

    next_visit_date = models.DateField(
        blank=True,
        null=True
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-visit_date", "-id"]

    def save(self, *args, **kwargs):

        if not self.visit_id:

            last_visit = AMCVisit.objects.order_by("-id").first()

            if last_visit:
                new_id = last_visit.id + 1
            else:
                new_id = 1

            self.visit_id = f"AMCV{new_id:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.visit_id} - {self.amc.customer.customer_name}"