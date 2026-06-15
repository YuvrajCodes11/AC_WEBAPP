# store/admin.py

from django.contrib import admin

from .models import (
    StoreCategory,
    StoreItem,
    StoreTransaction,
)


@admin.register(StoreCategory)
class StoreCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "category_name",
        "created_at",
    )

    search_fields = (
        "category_name",
    )


@admin.register(StoreItem)
class StoreItemAdmin(admin.ModelAdmin):
    list_display = (
        "item_code",
        "category",
        "item_description",
        "size",
        "is_vrv",
        "is_non_vrv",
        "unit",
        "opening_stock",
        "current_stock",
        "minimum_stock",
        "used_quantity",
        "used_percentage",
        "stock_alert_status",
        "created_by",
        "created_at",
    )

    list_filter = (
        "category",
        "is_vrv",
        "is_non_vrv",
        "unit",
        "created_at",
    )

    search_fields = (
        "item_code",
        "item_description",
        "size",
        "remarks",
    )

    readonly_fields = (
        "item_code",
        "used_quantity",
        "used_percentage",
        "stock_alert_status",
        "created_at",
    )


@admin.register(StoreTransaction)
class StoreTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_id",
        "item",
        "transaction_type",
        "purpose",
        "quantity",
        "stock_before",
        "stock_after",
        "project",
        "boq",
        "material_issue_item",
        "issued_to",
        "created_by",
        "created_at",
    )

    list_filter = (
        "transaction_type",
        "purpose",
        "created_at",
    )

    search_fields = (
        "transaction_id",
        "item__item_code",
        "item__item_description",
        "project__project_id",
        "project__site_name",
        "boq__boq_id",
        "issued_to",
        "description",
    )

    readonly_fields = (
        "transaction_id",
        "stock_before",
        "stock_after",
        "is_stock_updated",
        "created_at",
    )
