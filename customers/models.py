from datetime import timedelta

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


class Customer(models.Model):

    CUSTOMER_CATEGORY_CHOICES = (
        ("GENERAL", "General Customer"),
        ("WARRANTY", "Warranty Customer"),
        ("AMC", "AMC Customer"),
    )

    customer_id = models.CharField(max_length=20, unique=True, blank=True)

    customer_category = models.CharField(
        max_length=20,
        choices=CUSTOMER_CATEGORY_CHOICES,
        default="GENERAL"
    )

    customer_name = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200, blank=True, null=True)
    phone_number = models.CharField(max_length=15)

    whatsapp_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    gst_number = models.CharField(max_length=30, blank=True, null=True)

    address = models.TextField(blank=True, null=True)
    landmark = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)

    remarks = models.TextField(blank=True, null=True)

    warranty_start_date = models.DateField(blank=True, null=True)
    warranty_end_date = models.DateField(blank=True, null=True)

    amc_start_date = models.DateField(blank=True, null=True)
    amc_end_date = models.DateField(blank=True, null=True)

    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="created_customers"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]

    def clean(self):
        if self.warranty_start_date and self.warranty_end_date:
            if self.warranty_end_date < self.warranty_start_date:
                raise ValidationError(
                    "Warranty end date cannot be before warranty start date."
                )

        if self.amc_start_date and self.amc_end_date:
            if self.amc_end_date < self.amc_start_date:
                raise ValidationError(
                    "AMC end date cannot be before AMC start date."
                )

    def save(self, *args, **kwargs):

        # Warranty end date auto set: 1 year minus 1 day
        # Example: 02-06-2026 -> 01-06-2027
        if self.warranty_start_date and not self.warranty_end_date:
            self.warranty_end_date = self.warranty_start_date + timedelta(days=365) - timedelta(days=1)

        # AMC end date auto set: 1 year minus 1 day
        # Example: 02-06-2026 -> 01-06-2027
        if self.amc_start_date and not self.amc_end_date:
            self.amc_end_date = self.amc_start_date + timedelta(days=365) - timedelta(days=1)

        self.clean()

        if not self.customer_id:
            last_customer = Customer.objects.order_by("-id").first()
            new_id = last_customer.id + 1 if last_customer else 1
            self.customer_id = f"CUS{new_id:03d}"

        super().save(*args, **kwargs)

        self.create_service_schedules()

    def create_service_schedules(self):

        # Warranty services auto-created after 75, 150, 225 and 300 days
        # from warranty start date.
        if self.warranty_start_date and self.warranty_end_date:
            warranty_service_days = [75, 150, 225, 300]
            valid_warranty_dates = []

            for days in warranty_service_days:
                service_date = self.warranty_start_date + timedelta(days=days)

                if service_date <= self.warranty_end_date:
                    valid_warranty_dates.append(service_date)

                    CustomerServiceSchedule.objects.get_or_create(
                        customer=self,
                        service_type="WARRANTY",
                        service_date=service_date,
                        defaults={
                            "status": "PENDING"
                        }
                    )

            CustomerServiceSchedule.objects.filter(
                customer=self,
                service_type="WARRANTY",
                status="PENDING"
            ).exclude(
                service_date__in=valid_warranty_dates
            ).delete()

        else:
            CustomerServiceSchedule.objects.filter(
                customer=self,
                service_type="WARRANTY",
                status="PENDING"
            ).delete()

        # AMC services auto-created after 75, 150, 225 and 300 days
        # from AMC start date.
        if self.amc_start_date and self.amc_end_date:
            amc_service_days = [75, 150, 225, 300]
            valid_amc_dates = []

            for days in amc_service_days:
                service_date = self.amc_start_date + timedelta(days=days)

                if service_date <= self.amc_end_date:
                    valid_amc_dates.append(service_date)

                    CustomerServiceSchedule.objects.get_or_create(
                        customer=self,
                        service_type="AMC",
                        service_date=service_date,
                        defaults={
                            "status": "PENDING"
                        }
                    )

            CustomerServiceSchedule.objects.filter(
                customer=self,
                service_type="AMC",
                status="PENDING"
            ).exclude(
                service_date__in=valid_amc_dates
            ).delete()

        else:
            CustomerServiceSchedule.objects.filter(
                customer=self,
                service_type="AMC",
                status="PENDING"
            ).delete()

    def warranty_expiry_alert_date(self):
        if self.warranty_end_date:
            return self.warranty_end_date - timedelta(days=45)
        return None

    def amc_expiry_alert_date(self):
        if self.amc_end_date:
            return self.amc_end_date - timedelta(days=45)
        return None

    def is_warranty_expiring_soon(self):
        if not self.warranty_end_date:
            return False

        today = timezone.localdate()
        alert_date = self.warranty_expiry_alert_date()

        return alert_date <= today <= self.warranty_end_date

    def is_amc_expiring_soon(self):
        if not self.amc_end_date:
            return False

        today = timezone.localdate()
        alert_date = self.amc_expiry_alert_date()

        return alert_date <= today <= self.amc_end_date

    def pending_services_count(self):
        return self.service_schedules.filter(
            status="PENDING",
            service_date__lte=timezone.localdate()
        ).count()

    def __str__(self):
        return f"{self.customer_id} - {self.customer_name}"


class CustomerServiceSchedule(models.Model):

    SERVICE_TYPE_CHOICES = (
        ("WARRANTY", "Warranty Service"),
        ("AMC", "AMC Service"),
    )

    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("COMPLETED", "Completed"),
        ("MISSED", "Missed"),
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="service_schedules"
    )

    service_type = models.CharField(
        max_length=20,
        choices=SERVICE_TYPE_CHOICES
    )

    service_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    completed_date = models.DateField(blank=True, null=True)

    complaint_title = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    complaint_description = models.TextField(
        blank=True,
        null=True
    )

    complaint_register = models.FileField(
        upload_to="complaint_registers/",
        blank=True,
        null=True
    )

    remarks = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("customer", "service_type", "service_date")
        ordering = ["service_date"]

    def mark_completed(self):
        self.status = "COMPLETED"
        self.completed_date = timezone.localdate()
        self.save()

    def mark_missed(self):
        self.status = "MISSED"
        self.save()

    def is_due(self):
        return (
            self.status == "PENDING"
            and self.service_date <= timezone.localdate()
        )

    def __str__(self):
        return f"{self.customer.customer_name} - {self.service_type} - {self.service_date}"