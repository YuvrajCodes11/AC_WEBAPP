# material_issue/admin.py

from django.contrib import admin

from .models import (
    MaterialIssue,
    MaterialIssueItem,
)


class MaterialIssueItemInline(admin.TabularInline):
    model = MaterialIssueItem
    extra = 1

    fields = (
        "store_item",
        "boq_item",
        "issued_quantity",
        "consumed_quantity",
        "returned_quantity",
        "unused_quantity",
        "scrap_quantity",
        "serial_number",
        "scrap_date",
        "balance_quantity",
        "remarks",
    )

    readonly_fields = (
        "balance_quantity",
    )


@admin.register(MaterialIssue)
class MaterialIssueAdmin(admin.ModelAdmin):
    list_display = (
        "issue_id",
        "heading",
        "project",
        "boq",
        "issue_date",
        "issued_to",
        "received_by",
        "status",
        "issued_by",
        "created_at",
    )

    list_filter = (
        "status",
        "issue_date",
        "created_at",
    )

    search_fields = (
        "issue_id",
        "heading",
        "project__project_id",
        "project__site_name",
        "project__customer__customer_name",
        "boq__boq_id",
        "issued_to",
        "received_by",
    )

    readonly_fields = (
        "issue_id",
        "created_at",
        "updated_at",
    )

    inlines = [
        MaterialIssueItemInline,
    ]


@admin.register(MaterialIssueItem)
class MaterialIssueItemAdmin(admin.ModelAdmin):
    list_display = (
        "material_issue",
        "store_item",
        "boq_item",
        "issued_quantity",
        "consumed_quantity",
        "returned_quantity",
        "unused_quantity",
        "scrap_quantity",
        "serial_number",
        "scrap_date",
        "balance_quantity",
        "is_stock_updated",
        "created_at",
    )

    list_filter = (
        "is_stock_updated",
        "created_at",
    )

    search_fields = (
        "material_issue__issue_id",
        "store_item__item_code",
        "store_item__item_description",
        "boq_item__boq__boq_id",
    )

    readonly_fields = (
        "balance_quantity",
        "created_at",
    )
