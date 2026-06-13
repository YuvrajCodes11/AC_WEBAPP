# reports/views.py

from django.contrib.auth.decorators import login_required
from django.db import models
from django.shortcuts import render

from customers.models import Customer
from projects.models import CustomerProject
from store.models import StoreItem, StoreTransaction
from boq.models import ProjectBOQ, ProjectBOQItem
from material_issue.models import MaterialIssue, MaterialIssueItem


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

    total_material_unused_quantity = MaterialIssueItem.objects.aggregate(
        total=models.Sum("unused_quantity")
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
        "total_material_unused_quantity": total_material_unused_quantity,
        "total_material_scrap_quantity": total_material_scrap_quantity,

        "recent_customers": recent_customers,
        "recent_projects": recent_projects,
        "recent_boqs": recent_boqs,
        "recent_material_issues": recent_material_issues,
        "low_stock_list": low_stock_list,
        "recent_store_transactions": recent_store_transactions,
    })
