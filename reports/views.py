import csv
from collections import defaultdict
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render

from customers.models import Customer
from projects.models import CustomerProject
from store.models import StoreItem, StoreTransaction
from boq.models import ProjectBOQ, ProjectBOQItem
from material_issue.models import MaterialIssue, MaterialIssueItem


def _store_items(search=""):
    items = StoreItem.objects.select_related("category").order_by(
        "category__category_name",
        "item_description",
    )
    if search:
        items = items.filter(
            Q(item_code__icontains=search)
            | Q(item_description__icontains=search)
            | Q(category__category_name__icontains=search)
            | Q(size__icontains=search)
        )
    return items


def _boq_vs_issued_rows():
    rows = []
    items = ProjectBOQItem.objects.select_related(
        "boq",
        "boq__project",
        "boq__project__customer",
        "store_item",
    )
    for item in items:
        extra_quantity = max(
            item.issued_quantity - item.required_quantity,
            Decimal("0.00"),
        )
        rows.append({
            "boq": item.boq,
            "project": item.boq.project,
            "store_item": item.store_item,
            "boq_qty": item.required_quantity,
            "issued_qty": item.issued_quantity,
            "extra_qty": extra_quantity,
            "status": "Exceeded" if extra_quantity else "Within BOQ",
        })
    return rows


def _new_issue_items():
    return MaterialIssueItem.objects.filter(
        boq_item__isnull=True
    ).select_related(
        "material_issue",
        "material_issue__project",
        "material_issue__project__customer",
        "store_item",
    )


def _project_consumption_rows():
    totals = defaultdict(lambda: Decimal("0.00"))
    objects = {}
    issue_items = MaterialIssueItem.objects.select_related(
        "material_issue__project",
        "material_issue__project__customer",
        "store_item",
    )
    for issue_item in issue_items:
        key = (
            issue_item.material_issue.project_id,
            issue_item.store_item_id,
        )
        totals[key] += issue_item.consumed_quantity
        objects[key] = (
            issue_item.material_issue.project,
            issue_item.store_item,
        )

    rows = []
    for key, quantity in totals.items():
        project, store_item = objects[key]
        rows.append({
            "project": project,
            "store_item": store_item,
            "total_quantity": quantity,
        })
    return sorted(
        rows,
        key=lambda row: (
            row["project"].project_id,
            row["store_item"].item_description,
        ),
    )


@login_required
def reports_dashboard(request):

    total_customers = Customer.objects.count()

    total_projects = CustomerProject.objects.count()

    total_boqs = ProjectBOQ.objects.count()

    total_boq_items = ProjectBOQItem.objects.count()

    total_material_issues = MaterialIssue.objects.count()

    total_material_issue_items = MaterialIssueItem.objects.count()

    total_store_items = StoreItem.objects.count()

    total_store_transactions = StoreTransaction.objects.count()

    low_stock_items = StoreItem.objects.filter(
        current_stock__lte=models.F("minimum_stock")
    ).count()

    warranty_customers = Customer.objects.filter(
        customer_category="WARRANTY"
    ).count()

    amc_customers = Customer.objects.filter(
        customer_category="AMC"
    ).count()

    planning_projects = CustomerProject.objects.filter(
        project_status="PLANNING"
    ).count()

    ongoing_projects = CustomerProject.objects.filter(
        project_status="ONGOING"
    ).count()

    material_required_projects = CustomerProject.objects.filter(
        project_status="MATERIAL_REQUIRED"
    ).count()

    material_issued_projects = CustomerProject.objects.filter(
        project_status="MATERIAL_ISSUED"
    ).count()

    installation_projects = CustomerProject.objects.filter(
        project_status="INSTALLATION"
    ).count()

    testing_projects = CustomerProject.objects.filter(
        project_status="TESTING"
    ).count()

    hold_projects = CustomerProject.objects.filter(
        project_status="HOLD"
    ).count()

    commissioned_projects = CustomerProject.objects.filter(
        project_status="COMMISSIONED"
    ).count()

    cancelled_projects = CustomerProject.objects.filter(
        project_status="CANCELLED"
    ).count()

    draft_boqs = ProjectBOQ.objects.filter(
        status="DRAFT"
    ).count()

    submitted_boqs = ProjectBOQ.objects.filter(
        status="SUBMITTED"
    ).count()

    approved_boqs = ProjectBOQ.objects.filter(
        status="APPROVED"
    ).count()

    rejected_boqs = ProjectBOQ.objects.filter(
        status="REJECTED"
    ).count()

    closed_boqs = ProjectBOQ.objects.filter(
        status="CLOSED"
    ).count()

    draft_material_issues = MaterialIssue.objects.filter(
        status="DRAFT"
    ).count()

    issued_material_issues = MaterialIssue.objects.filter(
        status="ISSUED"
    ).count()

    partial_return_material_issues = MaterialIssue.objects.filter(
        status="PARTIAL_RETURN"
    ).count()

    returned_material_issues = MaterialIssue.objects.filter(
        status="RETURNED"
    ).count()

    cancelled_material_issues = MaterialIssue.objects.filter(
        status="CANCELLED"
    ).count()

    total_stock_quantity = StoreItem.objects.aggregate(
        total=models.Sum("current_stock")
    )["total"] or 0

    total_opening_stock = StoreItem.objects.aggregate(
        total=models.Sum("opening_stock")
    )["total"] or 0

    total_boq_required_quantity = ProjectBOQItem.objects.aggregate(
        total=models.Sum("required_quantity")
    )["total"] or 0

    total_boq_issued_quantity = ProjectBOQItem.objects.aggregate(
        total=models.Sum("issued_quantity")
    )["total"] or 0

    total_boq_consumed_quantity = ProjectBOQItem.objects.aggregate(
        total=models.Sum("consumed_quantity")
    )["total"] or 0

    total_material_issued_quantity = MaterialIssueItem.objects.aggregate(
        total=models.Sum("issued_quantity")
    )["total"] or 0

    total_material_consumed_quantity = MaterialIssueItem.objects.aggregate(
        total=models.Sum("consumed_quantity")
    )["total"] or 0

    total_material_returned_quantity = MaterialIssueItem.objects.aggregate(
        total=models.Sum("returned_quantity")
    )["total"] or 0

    total_material_scrap_quantity = MaterialIssueItem.objects.aggregate(
        total=models.Sum("scrap_quantity")
    )["total"] or 0

    recent_customers = Customer.objects.order_by("-id")[:10]

    recent_projects = CustomerProject.objects.select_related(
        "customer"
    ).order_by("-id")[:10]

    recent_boqs = ProjectBOQ.objects.select_related(
        "project",
        "project__customer"
    ).order_by("-id")[:10]

    recent_material_issues = MaterialIssue.objects.select_related(
        "project",
        "project__customer",
        "boq",
        "issued_by"
    ).order_by("-id")[:10]

    low_stock_list = StoreItem.objects.select_related(
        "category"
    ).filter(
        current_stock__lte=models.F("minimum_stock")
    ).order_by("current_stock")[:10]

    recent_store_transactions = StoreTransaction.objects.select_related(
        "item",
        "item__category",
        "project",
        "created_by"
    ).order_by("-id")[:10]

    return render(request, "reports/dashboard.html", {
        "total_customers": total_customers,
        "total_projects": total_projects,
        "total_boqs": total_boqs,
        "total_boq_items": total_boq_items,
        "total_material_issues": total_material_issues,
        "total_material_issue_items": total_material_issue_items,
        "total_store_items": total_store_items,
        "total_store_transactions": total_store_transactions,

        "low_stock_items": low_stock_items,
        "warranty_customers": warranty_customers,
        "amc_customers": amc_customers,

        "planning_projects": planning_projects,
        "ongoing_projects": ongoing_projects,
        "material_required_projects": material_required_projects,
        "material_issued_projects": material_issued_projects,
        "installation_projects": installation_projects,
        "testing_projects": testing_projects,
        "hold_projects": hold_projects,
        "commissioned_projects": commissioned_projects,
        "cancelled_projects": cancelled_projects,

        "draft_boqs": draft_boqs,
        "submitted_boqs": submitted_boqs,
        "approved_boqs": approved_boqs,
        "rejected_boqs": rejected_boqs,
        "closed_boqs": closed_boqs,

        "draft_material_issues": draft_material_issues,
        "issued_material_issues": issued_material_issues,
        "partial_return_material_issues": partial_return_material_issues,
        "returned_material_issues": returned_material_issues,
        "cancelled_material_issues": cancelled_material_issues,

        "total_stock_quantity": total_stock_quantity,
        "total_opening_stock": total_opening_stock,
        "total_boq_required_quantity": total_boq_required_quantity,
        "total_boq_issued_quantity": total_boq_issued_quantity,
        "total_boq_consumed_quantity": total_boq_consumed_quantity,
        "total_material_issued_quantity": total_material_issued_quantity,
        "total_material_consumed_quantity": total_material_consumed_quantity,
        "total_material_returned_quantity": total_material_returned_quantity,
        "total_material_scrap_quantity": total_material_scrap_quantity,

        "recent_customers": recent_customers,
        "recent_projects": recent_projects,
        "recent_boqs": recent_boqs,
        "recent_material_issues": recent_material_issues,
        "low_stock_list": low_stock_list,
        "recent_store_transactions": recent_store_transactions,
    })


@login_required
def store_report(request):
    search = request.GET.get("search", "").strip()
    return render(request, "store_report.html", {
        "items": _store_items(search),
        "search": search,
    })


@login_required
def export_store_report(request):
    search = request.GET.get("search", "").strip()
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="store-report.csv"'
    writer = csv.writer(response)
    writer.writerow([
        "Code",
        "Category",
        "Description",
        "Type",
        "Size",
        "Unit",
        "Current Stock",
        "Minimum Stock",
        "Status",
    ])
    for item in _store_items(search):
        writer.writerow([
            item.item_code,
            item.category.category_name,
            item.item_description,
            "VRV" if item.is_vrv else "Non-VRV",
            item.size or "",
            item.get_unit_display(),
            item.current_stock,
            item.minimum_stock,
            "Low Stock" if item.is_low_stock() else "Available",
        ])
    return response


@login_required
def boq_vs_issued_report(request):
    return render(request, "boq_vs_issued_report.html", {
        "rows": _boq_vs_issued_rows(),
        "new_items": _new_issue_items(),
    })


@login_required
def export_boq_vs_issued_report(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="boq-vs-issued.csv"'
    writer = csv.writer(response)
    writer.writerow([
        "BOQ",
        "Customer",
        "Project",
        "Material",
        "Type",
        "BOQ Qty",
        "Issued Qty",
        "Extra Qty",
        "Status",
    ])
    for row in _boq_vs_issued_rows():
        project = row["project"]
        writer.writerow([
            row["boq"].boq_id,
            project.get_customer_name() if project else "No Customer",
            project.project_id if project else "No Project Linked",
            row["store_item"].item_description,
            "VRV" if row["store_item"].is_vrv else "Non-VRV",
            row["boq_qty"],
            row["issued_qty"],
            row["extra_qty"],
            row["status"],
        ])
    return response


@login_required
def project_consumption_report(request):
    return render(request, "project_consumption_report.html", {
        "rows": _project_consumption_rows(),
    })


@login_required
def export_project_consumption_report(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        'attachment; filename="project-consumption.csv"'
    )
    writer = csv.writer(response)
    writer.writerow([
        "Customer",
        "Project",
        "Location",
        "Material",
        "Type",
        "Size",
        "Unit",
        "Consumed Qty",
    ])
    for row in _project_consumption_rows():
        project = row["project"]
        item = row["store_item"]
        writer.writerow([
            project.get_customer_name(),
            project.project_id,
            project.location or "",
            item.item_description,
            "VRV" if item.is_vrv else "Non-VRV",
            item.size or "",
            item.get_unit_display(),
            row["total_quantity"],
        ])
    return response
