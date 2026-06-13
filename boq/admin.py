# boq/admin.py

from django.contrib import admin
from .models import ProjectBOQ, ProjectBOQItem


class ProjectBOQItemInline(admin.TabularInline):
    model = ProjectBOQItem
    extra = 1

    fields = (
        "store_item",
        "required_quantity",
        "issued_quantity",
        "consumed_quantity",
        "returned_quantity",
        "rate",
        "remarks",
    )


@admin.register(ProjectBOQ)
class ProjectBOQAdmin(admin.ModelAdmin):
    list_display = (
        "boq_id",
        "project",
        "title",
        "status",
        "created_by",
        "approved_by",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "boq_id",
        "title",
        "project__project_id",
        "project__site_name",
        "project__customer__customer_name",
    )

    readonly_fields = (
        "boq_id",
        "created_at",
        "updated_at",
        "approved_at",
    )

    inlines = [
        ProjectBOQItemInline
    ]


@admin.register(ProjectBOQItem)
class ProjectBOQItemAdmin(admin.ModelAdmin):
    list_display = (
        "boq",
        "store_item",
        "required_quantity",
        "issued_quantity",
        "consumed_quantity",
        "returned_quantity",
        "rate",
        "balance_quantity",
        "pending_collection_quantity",
        "total_amount",
    )

    search_fields = (
        "boq__boq_id",
        "store_item__item_code",
        "store_item__item_description",
    )

    list_filter = (
        "created_at",
    )