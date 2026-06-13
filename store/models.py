# store/models.py

from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from projects.models import CustomerProject


class StoreCategory(models.Model):
    category_name = models.CharField(
        max_length=200,
        unique=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["category_name"]

    def __str__(self):
        return self.category_name


class StoreItem(models.Model):

    UNIT_CHOICES = (
        ("NOS", "Nos"),
        ("MTR", "Meter"),
        ("RFT", "Rft"),
        ("MTR_AND_RFT", "MTR and RFT"),
        ("KG", "Kg"),
        ("PKT", "Packet"),
        ("NOS_PKT", "Nos / Packet"),
        ("LTR", "Liter"),
        ("SQMTR", "Sq. Meter"),
        ("ROLL", "Roll"),
        ("BOX", "Box"),
        ("COIL", "Coil"),
    )

    item_code = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    category = models.ForeignKey(
        StoreCategory,
        on_delete=models.CASCADE,
        related_name="items"
    )

    item_description = models.CharField(
        max_length=250
    )

    size = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    serial_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="AC unit serial number (if applicable)."
    )

    remarks = models.CharField(
        max_length=250,
        blank=True,
        null=True
    )

    unit = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES,
        default="NOS"
    )

    opening_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    current_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    minimum_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    alert_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=85,
        help_text="Alert when stock is 85% used from opening stock."
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="created_store_items"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["category__category_name", "item_description"]

    def save(self, *args, **kwargs):
        if not self.item_code:
            last_item = StoreItem.objects.order_by("-id").first()
            new_id = last_item.id + 1 if last_item else 1
            self.item_code = f"STK{new_id:04d}"

        if self.pk is None and self.current_stock == 0:
            self.current_stock = self.opening_stock

        super().save(*args, **kwargs)

    def used_quantity(self):
        used = self.opening_stock - self.current_stock
        return used if used > 0 else Decimal("0.00")

    def used_percentage(self):
        if self.opening_stock <= 0:
            return Decimal("0.00")

        percentage = (self.used_quantity() / self.opening_stock) * 100
        return round(percentage, 2)

    def is_low_stock(self):
        return self.current_stock <= self.minimum_stock

    def is_85_percent_used(self):
        return self.used_percentage() >= self.alert_percentage

    def stock_alert_status(self):
        if self.is_low_stock():
            return "LOW_STOCK"

        if self.is_85_percent_used():
            return "85_PERCENT_USED"

        return "OK"

    def __str__(self):
        size_text = f" - {self.size}" if self.size else ""
        return f"{self.item_code} - {self.item_description}{size_text}"


class StoreTransaction(models.Model):

    TRANSACTION_TYPE_CHOICES = (
        ("IN", "Stock In"),
        ("OUT", "Stock Out"),
        ("RETURN", "Material Return"),
        ("ADJUSTMENT", "Stock Adjustment"),
    )

    PURPOSE_CHOICES = (
        ("PROJECT", "Project Work"),
        ("AMC", "AMC Work"),
        ("WARRANTY", "Warranty Work"),
        ("SERVICE", "Service Work"),
        ("PURCHASE", "Purchase"),
        ("STORE", "Store Adjustment"),
        ("GENERAL", "General"),
    )

    transaction_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    item = models.ForeignKey(
        StoreItem,
        on_delete=models.CASCADE,
        related_name="transactions"
    )

    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES
    )

    purpose = models.CharField(
        max_length=20,
        choices=PURPOSE_CHOICES,
        default="GENERAL"
    )

    project = models.ForeignKey(
        CustomerProject,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="store_transactions"
    )

    boq = models.ForeignKey(
        "boq.ProjectBOQ",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="store_transactions"
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    stock_before = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    stock_after = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    issued_to = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    amc_customer_name = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    warranty_customer_name = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    service_customer_name = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    invoice_file = models.FileField(
        upload_to="store_invoices/",
        blank=True,
        null=True
    )

    is_stock_updated = models.BooleanField(
        default=False
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="created_store_transactions"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-id"]

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than 0.")

        if self.purpose == "PROJECT" and not self.project:
            raise ValidationError("Please select project for project transaction.")

        if self.purpose == "AMC" and not self.amc_customer_name:
            raise ValidationError("Please enter AMC customer name.")

        if self.purpose == "WARRANTY" and not self.warranty_customer_name:
            raise ValidationError("Please enter warranty customer name.")

        if self.purpose == "SERVICE" and not self.service_customer_name:
            raise ValidationError("Please enter service customer name.")

        if self.transaction_type == "OUT" and self.item.current_stock < self.quantity:
            raise ValidationError(
                f"Not enough stock for {self.item.item_description}. "
                f"Available stock: {self.item.current_stock}"
            )

    def save(self, *args, **kwargs):
        self.clean()

        if not self.transaction_id:
            last_transaction = StoreTransaction.objects.order_by("-id").first()
            new_id = last_transaction.id + 1 if last_transaction else 1
            self.transaction_id = f"TRN{new_id:04d}"

        if not self.pk and not self.is_stock_updated:
            qty = Decimal(self.quantity)

            self.stock_before = self.item.current_stock

            if self.transaction_type == "IN":
                self.item.current_stock += qty

            elif self.transaction_type == "OUT":
                self.item.current_stock -= qty

            elif self.transaction_type == "RETURN":
                self.item.current_stock += qty

            elif self.transaction_type == "ADJUSTMENT":
                self.item.current_stock += qty

            self.item.save()

            self.stock_after = self.item.current_stock
            self.is_stock_updated = True

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.is_stock_updated:
            qty = Decimal(self.quantity)

            if self.transaction_type == "IN":
                self.item.current_stock -= qty

            elif self.transaction_type == "OUT":
                self.item.current_stock += qty

            elif self.transaction_type == "RETURN":
                self.item.current_stock -= qty

            elif self.transaction_type == "ADJUSTMENT":
                self.item.current_stock -= qty

            self.item.save()

        super().delete(*args, **kwargs)

    def related_party(self):
        if self.project:
            return str(self.project)

        if self.amc_customer_name:
            return self.amc_customer_name

        if self.warranty_customer_name:
            return self.warranty_customer_name

        if self.service_customer_name:
            return self.service_customer_name

        return "-"

    def __str__(self):
        return f"{self.transaction_id} - {self.item.item_description} - {self.transaction_type}"