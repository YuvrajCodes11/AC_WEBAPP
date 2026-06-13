from django.db import models
from django.contrib.auth.models import User
from customers.models import Customer


class ServiceComplaint(models.Model):

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('HOLD', 'Hold'),
        ('CANCELLED', 'Cancelled'),
    )

    complaint_id = models.CharField(max_length=20, unique=True, blank=True)

    complaint_date = models.DateField()

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='service_complaints'
    )

    customer_address = models.TextField(blank=True, null=True)

    contact_number = models.CharField(max_length=15)

    nature_of_complaint = models.TextField()

    technician_name = models.CharField(max_length=150, blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    service_completed_date = models.DateField(blank=True, null=True)

    remarks = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):

        if not self.complaint_id:
            last_complaint = ServiceComplaint.objects.order_by("-id").first()

            if last_complaint:
                new_id = last_complaint.id + 1
            else:
                new_id = 1

            self.complaint_id = f"SER{new_id:04d}"

        super().save(*args, **kwargs)

    def customer_category(self):
        return self.customer.get_customer_category_display()

    def __str__(self):
        return f"{self.complaint_id} - {self.customer.customer_name}"