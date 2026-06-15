# material_issue/views.py

from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import render, redirect, get_object_or_404

from projects.models import CustomerProject
from boq.models import ProjectBOQ, ProjectBOQItem
from store.models import StoreItem, StoreCategory

from .models import MaterialIssue, MaterialIssueItem


def decimal_zero():
    return Decimal("0.00")


@login_required
def material_issue_list(request):
    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip()

    material_issues = MaterialIssue.objects.select_related(
        "project",
        "project__customer",
        "boq",
        "issued_by",
    ).prefetch_related(
        "items",
        "items__store_item",
        "items__store_item__category",
    ).all().order_by("-id")

    if search:
        material_issues = material_issues.filter(
            Q(issue_id__icontains=search) |
            Q(heading__icontains=search) |
            Q(project__project_id__icontains=search) |
            Q(project__site_name__icontains=search) |
            Q(project__customer__customer_name__icontains=search) |
            Q(boq__boq_id__icontains=search) |
            Q(issued_to__icontains=search) |
            Q(received_by__icontains=search)
        )

    if status:
        material_issues = material_issues.filter(status=status)

    for issue in material_issues:
        issue.total_issued_quantity = issue.items.aggregate(
            total=Sum("issued_quantity")
        )["total"] or decimal_zero()

        issue.total_consumed_quantity = issue.items.aggregate(
            total=Sum("consumed_quantity")
        )["total"] or decimal_zero()

        issue.total_returned_quantity = issue.items.aggregate(
            total=Sum("returned_quantity")
        )["total"] or decimal_zero()

        issue.total_scrap_quantity = issue.items.aggregate(
            total=Sum("scrap_quantity")
        )["total"] or decimal_zero()

        issue.total_balance_quantity = (
            issue.total_issued_quantity
            - issue.total_consumed_quantity
            - issue.total_returned_quantity
            - issue.total_scrap_quantity
        )

    total_issues = MaterialIssue.objects.count()
    draft_issues = MaterialIssue.objects.filter(status="DRAFT").count()
    issued_issues = MaterialIssue.objects.filter(status="ISSUED").count()
    returned_issues = MaterialIssue.objects.filter(status="RETURNED").count()
    cancelled_issues = MaterialIssue.objects.filter(status="CANCELLED").count()

    return render(request, "material_issue_list.html", {
        "material_issues": material_issues,
        "search": search,
        "status": status,
        "status_choices": MaterialIssue.STATUS_CHOICES,
        "total_issues": total_issues,
        "draft_issues": draft_issues,
        "issued_issues": issued_issues,
        "returned_issues": returned_issues,
        "cancelled_issues": cancelled_issues,
    })


@login_required
def material_issue_customer_report(request):
    search = request.GET.get("search", "").strip()

    projects = CustomerProject.objects.select_related(
        "customer"
    ).prefetch_related(
        "material_issues",
        "material_issues__items",
        "material_issues__items__store_item",
        "material_issues__items__store_item__category",
    ).all().order_by("-id")

    if search:
        projects = projects.filter(
            Q(project_id__icontains=search) |
            Q(site_name__icontains=search) |
            Q(customer__customer_name__icontains=search) |
            Q(customer__phone_number__icontains=search)
        )

    report_data = []

    for project in projects:
        issue_items = MaterialIssueItem.objects.select_related(
            "material_issue",
            "material_issue__project",
            "material_issue__project__customer",
            "store_item",
            "store_item__category",
        ).filter(
            material_issue__project=project
        ).order_by(
            "-material_issue__id",
            "id"
        )

        total_issued = issue_items.aggregate(
            total=Sum("issued_quantity")
        )["total"] or decimal_zero()

        total_consumed = issue_items.aggregate(
            total=Sum("consumed_quantity")
        )["total"] or decimal_zero()

        total_returned = issue_items.aggregate(
            total=Sum("returned_quantity")
        )["total"] or decimal_zero()

        total_scrap = issue_items.aggregate(
            total=Sum("scrap_quantity")
        )["total"] or decimal_zero()

        total_balance = total_issued - total_consumed - total_returned - total_scrap

        if issue_items.exists():
            report_data.append({
                "project": project,
                "customer": project.customer,
                "issue_items": issue_items,
                "total_issued": total_issued,
                "total_consumed": total_consumed,
                "total_returned": total_returned,
                "total_scrap": total_scrap,
                "total_balance": total_balance,
            })

    return render(request, "material_issue_customer_report.html", {
        "report_data": report_data,
        "search": search,
    })


@login_required
def scrap_report(request):
    search = request.GET.get("search", "").strip()

    scrap_items = MaterialIssueItem.objects.select_related(
        "material_issue",
        "material_issue__project",
        "material_issue__project__customer",
        "store_item",
        "store_item__category",
    ).filter(scrap_quantity__gt=0).order_by("-scrap_date", "-id")

    if search:
        scrap_items = scrap_items.filter(
            Q(material_issue__issue_id__icontains=search) |
            Q(material_issue__project__project_id__icontains=search) |
            Q(material_issue__project__customer__customer_name__icontains=search) |
            Q(store_item__item_code__icontains=search) |
            Q(store_item__item_description__icontains=search) |
            Q(scrap_reason__icontains=search)
        )

    total_scrap = scrap_items.aggregate(
        total=Sum("scrap_quantity")
    )["total"] or decimal_zero()

    return render(request, "scrap_report.html", {
        "scrap_items": scrap_items,
        "total_scrap": total_scrap,
        "search": search,
    })


@login_required
def add_material_issue(request):
    projects = CustomerProject.objects.select_related(
        "customer"
    ).all().order_by("-id")

    boqs = ProjectBOQ.objects.select_related(
        "project",
        "project__customer"
    ).all().order_by("-id")

    store_items = StoreItem.objects.select_related(
        "category"
    ).all().order_by(
        "category__category_name",
        "item_description",
        "size"
    )

    boq_items = ProjectBOQItem.objects.select_related(
        "boq",
        "store_item",
        "store_item__category",
    ).all().order_by("-id")

    error = None

    if request.method == "POST":
        try:
            project_id = request.POST.get("project")
            boq_id = request.POST.get("boq") or None
            issued_to = request.POST.get("issued_to", "Site Engineer").strip()
            heading = request.POST.get("heading", "").strip() or "Material Issue"
            received_by = request.POST.get("received_by", "").strip()
            status = request.POST.get("status") or "ISSUED"
            remarks = request.POST.get("remarks", "").strip()
            issue_file = request.FILES.get("issue_file")

            store_item_ids = request.POST.getlist("store_item")
            category_ids = request.POST.getlist("category")
            boq_item_ids = request.POST.getlist("boq_item")
            issued_quantities = request.POST.getlist("issued_quantity")
            item_remarks = request.POST.getlist("item_remarks")

            if not project_id:
                error = "Please select project."

            else:
                project = get_object_or_404(CustomerProject, id=project_id)

                boq = None
                if boq_id:
                    boq = get_object_or_404(ProjectBOQ, id=boq_id, project=project)

                serial_numbers = request.POST.getlist("serial_number")

                with transaction.atomic():
                    material_issue = MaterialIssue.objects.create(
                        project=project,
                        boq=boq,
                        heading=heading,
                        issued_to=issued_to or "Site Engineer",
                        received_by=received_by,
                        status=status,
                        remarks=remarks,
                        issue_file=issue_file,
                        issued_by=request.user,
                    )

                    for index, store_item_id in enumerate(store_item_ids):
                        if not store_item_id:
                            continue

                        issued_quantity = Decimal(
                            issued_quantities[index] or "0"
                        )

                        if issued_quantity <= 0:
                            continue

                        store_item = get_object_or_404(
                            StoreItem,
                            id=store_item_id
                        )
                        if index < len(category_ids) and category_ids[index]:
                            if str(store_item.category_id) != category_ids[index]:
                                raise ValueError(
                                    "Selected store item does not belong to the selected category."
                                )

                        boq_item = None

                        if index < len(boq_item_ids):
                            boq_item_id = boq_item_ids[index]
                            if boq_item_id:
                                boq_item = get_object_or_404(
                                    ProjectBOQItem,
                                    id=boq_item_id,
                                    boq__project=project,
                                )

                        remark = ""
                        if index < len(item_remarks):
                            remark = item_remarks[index].strip()

                        serial_number = ""
                        if index < len(serial_numbers):
                            serial_number = serial_numbers[index].strip()

                        MaterialIssueItem.objects.create(
                            material_issue=material_issue,
                            store_item=store_item,
                            boq_item=boq_item,
                            issued_quantity=issued_quantity,
                            serial_number=serial_number or store_item.serial_number,
                            remarks=remark,
                        )

                messages.success(request, "Material issue created successfully.")
                return redirect("material_issue_detail", id=material_issue.id)

        except InvalidOperation:
            error = "Invalid quantity value."

        except Exception as e:
            error = str(e)

    return render(request, "add_material_issue.html", {
        "projects": projects,
        "boqs": boqs,
        "store_items": store_items,
        "boq_items": boq_items,
        "categories": StoreCategory.objects.all().order_by("category_name"),
        "status_choices": MaterialIssue.STATUS_CHOICES,
        "error": error,
    })


@login_required
def material_issue_detail(request, id):
    material_issue = get_object_or_404(
        MaterialIssue.objects.select_related(
            "project",
            "project__customer",
            "boq",
            "issued_by",
        ),
        id=id
    )

    issue_items = MaterialIssueItem.objects.select_related(
        "store_item",
        "store_item__category",
        "boq_item",
    ).filter(
        material_issue=material_issue
    ).order_by("id")

    total_issued_quantity = issue_items.aggregate(
        total=Sum("issued_quantity")
    )["total"] or decimal_zero()

    total_consumed_quantity = issue_items.aggregate(
        total=Sum("consumed_quantity")
    )["total"] or decimal_zero()

    total_returned_quantity = issue_items.aggregate(
        total=Sum("returned_quantity")
    )["total"] or decimal_zero()

    total_scrap_quantity = issue_items.aggregate(
        total=Sum("scrap_quantity")
    )["total"] or decimal_zero()

    total_balance_quantity = (
        total_issued_quantity
        - total_consumed_quantity
        - total_returned_quantity
        - total_scrap_quantity
    )

    return render(request, "material_issue_detail.html", {
        "material_issue": material_issue,
        "issue_items": issue_items,
        "total_issued_quantity": total_issued_quantity,
        "total_consumed_quantity": total_consumed_quantity,
        "total_returned_quantity": total_returned_quantity,
        "total_scrap_quantity": total_scrap_quantity,
        "total_balance_quantity": total_balance_quantity,
    })


@login_required
def edit_material_issue(request, id):
    material_issue = get_object_or_404(MaterialIssue, id=id)

    projects = CustomerProject.objects.select_related(
        "customer"
    ).all().order_by("-id")

    boqs = ProjectBOQ.objects.select_related(
        "project",
        "project__customer"
    ).all().order_by("-id")

    error = None

    if request.method == "POST":
        try:
            project_id = request.POST.get("project")
            boq_id = request.POST.get("boq") or None

            if not project_id:
                error = "Please select project."

            else:
                material_issue.project = get_object_or_404(
                    CustomerProject,
                    id=project_id
                )

                if boq_id:
                    material_issue.boq = get_object_or_404(
                        ProjectBOQ,
                        id=boq_id,
                        project=material_issue.project
                    )
                else:
                    material_issue.boq = None

                material_issue.issued_to = request.POST.get(
                    "issued_to",
                    "Site Engineer"
                ).strip()

                material_issue.heading = (
                    request.POST.get("heading", "").strip() or "Material Issue"
                )

                material_issue.received_by = request.POST.get(
                    "received_by",
                    ""
                ).strip()

                material_issue.status = request.POST.get("status") or "DRAFT"

                material_issue.remarks = request.POST.get(
                    "remarks",
                    ""
                ).strip()

                if request.FILES.get("issue_file"):
                    material_issue.issue_file = request.FILES.get("issue_file")

                material_issue.save()

                messages.success(request, "Material issue updated successfully.")
                return redirect("material_issue_detail", id=material_issue.id)

        except Exception as e:
            error = str(e)

    return render(request, "edit_material_issue.html", {
        "material_issue": material_issue,
        "projects": projects,
        "boqs": boqs,
        "status_choices": MaterialIssue.STATUS_CHOICES,
        "error": error,
    })


@login_required
def add_material_issue_item(request, issue_id):
    material_issue = get_object_or_404(MaterialIssue, id=issue_id)

    store_items = StoreItem.objects.select_related(
        "category"
    ).all().order_by(
        "category__category_name",
        "item_description",
        "size"
    )

    boq_items = ProjectBOQItem.objects.select_related(
        "boq",
        "store_item",
        "store_item__category",
    )

    if material_issue.boq:
        boq_items = boq_items.filter(boq=material_issue.boq)
    else:
        boq_items = boq_items.filter(boq__project=material_issue.project)

    error = None

    if request.method == "POST":
        try:
            store_item_id = request.POST.get("store_item")
            category_id = request.POST.get("category")
            boq_item_id = request.POST.get("boq_item") or None

            issued_quantity = Decimal(
                request.POST.get("issued_quantity") or "0"
            )

            remarks = request.POST.get("remarks", "").strip()
            serial_number = request.POST.get("serial_number", "").strip()

            if not store_item_id:
                error = "Please select store item."

            elif issued_quantity <= 0:
                error = "Issued quantity must be greater than 0."

            else:
                store_item = get_object_or_404(StoreItem, id=store_item_id)
                if category_id and str(store_item.category_id) != category_id:
                    raise ValueError(
                        "Selected store item does not belong to the selected category."
                    )

                boq_item = None
                if boq_item_id:
                    boq_item = get_object_or_404(
                        ProjectBOQItem,
                        id=boq_item_id,
                        boq__project=material_issue.project,
                    )

                MaterialIssueItem.objects.create(
                    material_issue=material_issue,
                    store_item=store_item,
                    boq_item=boq_item,
                    issued_quantity=issued_quantity,
                    serial_number=serial_number or store_item.serial_number,
                    remarks=remarks,
                )

                messages.success(request, "Material issue item added successfully.")
                return redirect("material_issue_detail", id=material_issue.id)

        except InvalidOperation:
            error = "Invalid quantity value."

        except Exception as e:
            error = str(e)

    return render(request, "add_material_issue_item.html", {
        "material_issue": material_issue,
        "store_items": store_items,
        "boq_items": boq_items,
        "categories": StoreCategory.objects.all().order_by("category_name"),
        "error": error,
    })


@login_required
def edit_material_issue_item(request, id):
    issue_item = get_object_or_404(MaterialIssueItem, id=id)

    store_items = StoreItem.objects.select_related(
        "category"
    ).all().order_by(
        "category__category_name",
        "item_description",
        "size"
    )

    boq_items = ProjectBOQItem.objects.select_related(
        "boq",
        "store_item",
        "store_item__category",
    )

    if issue_item.material_issue.boq:
        boq_items = boq_items.filter(boq=issue_item.material_issue.boq)
    else:
        boq_items = boq_items.filter(boq__project=issue_item.material_issue.project)

    error = None

    if request.method == "POST":
        try:
            issue_item.issued_quantity = Decimal(
                request.POST.get("issued_quantity") or "0"
            )
            issue_item.consumed_quantity = Decimal(
                request.POST.get("consumed_quantity") or "0"
            )

            issue_item.returned_quantity = Decimal(
                request.POST.get("returned_quantity") or "0"
            )

            issue_item.serial_number = (
                request.POST.get("serial_number", "").strip()
                or issue_item.store_item.serial_number
            )

            issue_item.scrap_quantity = Decimal(
                request.POST.get("scrap_quantity") or "0"
            )

            issue_item.scrap_date = request.POST.get("scrap_date") or None
            issue_item.scrap_reason = request.POST.get("scrap_reason", "").strip()
            issue_item.remarks = request.POST.get("remarks", "").strip()

            issue_item.save()

            messages.success(request, "Material issue item updated successfully.")
            return redirect(
                "material_issue_detail",
                id=issue_item.material_issue.id
            )

        except InvalidOperation:
            error = "Invalid quantity value."

        except Exception as e:
            error = str(e)

    return render(request, "edit_material_issue_item.html", {
        "issue_item": issue_item,
        "store_items": store_items,
        "boq_items": boq_items,
        "categories": StoreCategory.objects.all().order_by("category_name"),
        "error": error,
    })


@login_required
def delete_material_issue_item(request, id):
    issue_item = get_object_or_404(MaterialIssueItem, id=id)
    material_issue_id = issue_item.material_issue.id

    issue_item.delete()

    messages.success(request, "Material issue item deleted successfully.")
    return redirect("material_issue_detail", id=material_issue_id)


@login_required
def delete_material_issue(request, id):
    material_issue = get_object_or_404(MaterialIssue, id=id)

    material_issue.delete()

    messages.success(request, "Material issue deleted successfully.")
    return redirect("material_issue_list")


@login_required
def material_issue_print(request, id):
    material_issue = get_object_or_404(
        MaterialIssue.objects.select_related(
            "project",
            "project__customer",
            "boq",
            "issued_by",
        ),
        id=id
    )

    issue_items = MaterialIssueItem.objects.select_related(
        "store_item",
        "store_item__category",
        "boq_item",
    ).filter(
        material_issue=material_issue
    ).order_by("id")

    total_issued_quantity = issue_items.aggregate(
        total=Sum("issued_quantity")
    )["total"] or decimal_zero()

    total_consumed_quantity = issue_items.aggregate(
        total=Sum("consumed_quantity")
    )["total"] or decimal_zero()

    total_returned_quantity = issue_items.aggregate(
        total=Sum("returned_quantity")
    )["total"] or decimal_zero()

    total_scrap_quantity = issue_items.aggregate(
        total=Sum("scrap_quantity")
    )["total"] or decimal_zero()

    total_balance_quantity = (
        total_issued_quantity
        - total_consumed_quantity
        - total_returned_quantity
        - total_scrap_quantity
    )

    return render(request, "material_issue_print.html", {
        "material_issue": material_issue,
        "issue_items": issue_items,
        "total_issued_quantity": total_issued_quantity,
        "total_consumed_quantity": total_consumed_quantity,
        "total_returned_quantity": total_returned_quantity,
        "total_scrap_quantity": total_scrap_quantity,
        "total_balance_quantity": total_balance_quantity,
    })
