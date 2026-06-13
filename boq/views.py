# boq/views.py

from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from projects.models import CustomerProject
from store.models import StoreItem, StoreCategory
from .models import ProjectBOQ, ProjectBOQItem


def parse_decimal(value):
    try:
        if value:
            return Decimal(value)
        return Decimal("0")
    except InvalidOperation:
        return Decimal("0")


@login_required
def boq_list(request):
    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip()

    boqs = ProjectBOQ.objects.select_related(
        "project",
        "project__customer",
        "created_by",
        "approved_by"
    ).all().order_by("-id")

    if search:
        boqs = boqs.filter(
            Q(boq_id__icontains=search) |
            Q(title__icontains=search) |
            Q(project__project_id__icontains=search) |
            Q(project__site_name__icontains=search) |
            Q(project__customer__customer_name__icontains=search)
        )

    if status:
        boqs = boqs.filter(status=status)

    return render(request, "boq_list.html", {
        "boqs": boqs,
        "search": search,
        "status": status,
        "status_choices": ProjectBOQ.BOQ_STATUS_CHOICES,
        "total_boqs": ProjectBOQ.objects.count(),
        "draft_boqs": ProjectBOQ.objects.filter(status="DRAFT").count(),
        "submitted_boqs": ProjectBOQ.objects.filter(status="SUBMITTED").count(),
        "approved_boqs": ProjectBOQ.objects.filter(status="APPROVED").count(),
        "rejected_boqs": ProjectBOQ.objects.filter(status="REJECTED").count(),
        "closed_boqs": ProjectBOQ.objects.filter(status="CLOSED").count(),
    })


@login_required
def add_boq(request):
    projects = CustomerProject.objects.select_related(
        "customer"
    ).filter(
        is_active=True
    ).order_by("-id")

    store_items = StoreItem.objects.select_related(
        "category"
    ).all().order_by(
        "category__category_name",
        "item_description"
    )

    error = None

    if request.method == "POST":
        try:
            project_id = request.POST.get("project")
            title = request.POST.get("title", "Project BOQ").strip()
            remarks = request.POST.get("remarks", "").strip()

            store_item_ids = request.POST.getlist("store_item")
            required_quantities = request.POST.getlist("required_quantity")
            rates = request.POST.getlist("rate")
            item_remarks = request.POST.getlist("item_remarks")

            if not project_id:
                error = "Please select project."

            else:
                project = get_object_or_404(CustomerProject, id=project_id)

                boq = ProjectBOQ.objects.create(
                    project=project,
                    title=title or "Project BOQ",
                    remarks=remarks,
                    created_by=request.user,
                )

                item_added = False

                for index, store_item_id in enumerate(store_item_ids):
                    if not store_item_id:
                        continue

                    required_quantity = parse_decimal(
                        required_quantities[index]
                        if index < len(required_quantities)
                        else "0"
                    )

                    rate = parse_decimal(
                        rates[index]
                        if index < len(rates)
                        else "0"
                    )

                    if required_quantity <= 0:
                        continue

                    store_item = get_object_or_404(StoreItem, id=store_item_id)

                    remark = ""
                    if index < len(item_remarks):
                        remark = item_remarks[index].strip()

                    ProjectBOQItem.objects.create(
                        boq=boq,
                        store_item=store_item,
                        required_quantity=required_quantity,
                        rate=rate,
                        remarks=remark,
                    )

                    item_added = True

                if not item_added:
                    boq.delete()
                    error = "Please select at least one store item with quantity greater than 0."
                else:
                    messages.success(request, "BOQ created successfully.")
                    return redirect("boq_detail", id=boq.id)

        except Exception as e:
            error = str(e)

    return render(request, "add_boq.html", {
        "projects": projects,
        "store_items": store_items,
        "categories": StoreCategory.objects.all().order_by("category_name"),
        "error": error,
    })


@login_required
def boq_detail(request, id):
    boq = get_object_or_404(
        ProjectBOQ.objects.select_related(
            "project",
            "project__customer",
            "created_by",
            "approved_by"
        ),
        id=id
    )

    boq_items = ProjectBOQItem.objects.select_related(
        "store_item",
        "store_item__category"
    ).filter(
        boq=boq
    ).order_by("id")

    total_amount = sum(
        item.total_amount()
        for item in boq_items
    )

    total_required_quantity = boq_items.aggregate(
        total=Sum("required_quantity")
    )["total"] or Decimal("0.00")

    total_issued_quantity = boq_items.aggregate(
        total=Sum("issued_quantity")
    )["total"] or Decimal("0.00")

    total_consumed_quantity = boq_items.aggregate(
        total=Sum("consumed_quantity")
    )["total"] or Decimal("0.00")

    total_returned_quantity = boq_items.aggregate(
        total=Sum("returned_quantity")
    )["total"] or Decimal("0.00")

    return render(request, "boq_detail.html", {
        "boq": boq,
        "boq_items": boq_items,
        "total_amount": total_amount,
        "total_required_quantity": total_required_quantity,
        "total_issued_quantity": total_issued_quantity,
        "total_consumed_quantity": total_consumed_quantity,
        "total_returned_quantity": total_returned_quantity,
    })


@login_required
def edit_boq(request, id):
    boq = get_object_or_404(ProjectBOQ, id=id)

    projects = CustomerProject.objects.select_related(
        "customer"
    ).filter(
        is_active=True
    ).order_by("-id")

    error = None

    if request.method == "POST":
        try:
            project_id = request.POST.get("project")
            status = request.POST.get("status")
            title = request.POST.get("title", "").strip()
            remarks = request.POST.get("remarks", "").strip()

            if not project_id:
                error = "Please select project."

            else:
                project = get_object_or_404(CustomerProject, id=project_id)

                boq.project = project
                boq.title = title or "Project BOQ"
                boq.status = status or "DRAFT"
                boq.remarks = remarks

                if boq.status == "APPROVED" and not boq.approved_by:
                    boq.approved_by = request.user
                    boq.approved_at = timezone.now()

                boq.save()

                messages.success(request, "BOQ updated successfully.")
                return redirect("boq_detail", id=boq.id)

        except Exception as e:
            error = str(e)

    return render(request, "edit_boq.html", {
        "boq": boq,
        "projects": projects,
        "status_choices": ProjectBOQ.BOQ_STATUS_CHOICES,
        "error": error,
    })


@login_required
def add_boq_item(request, boq_id):
    boq = get_object_or_404(ProjectBOQ, id=boq_id)

    store_items = StoreItem.objects.select_related(
        "category"
    ).all().order_by(
        "category__category_name",
        "item_description"
    )

    error = None

    if request.method == "POST":
        try:
            store_item_id = request.POST.get("store_item")
            required_quantity = parse_decimal(
                request.POST.get("required_quantity")
            )
            rate = parse_decimal(
                request.POST.get("rate")
            )
            remarks = request.POST.get("remarks", "").strip()

            if not store_item_id:
                error = "Please select store item."

            elif required_quantity <= 0:
                error = "Required quantity must be greater than 0."

            else:
                store_item = get_object_or_404(StoreItem, id=store_item_id)

                ProjectBOQItem.objects.create(
                    boq=boq,
                    store_item=store_item,
                    required_quantity=required_quantity,
                    rate=rate,
                    remarks=remarks,
                )

                messages.success(request, "BOQ item added successfully.")
                return redirect("boq_detail", id=boq.id)

        except Exception as e:
            error = str(e)

    return render(request, "add_boq_item.html", {
        "boq": boq,
        "store_items": store_items,
        "categories": StoreCategory.objects.all().order_by("category_name"),
        "error": error,
    })


@login_required
def edit_boq_item(request, id):
    boq_item = get_object_or_404(ProjectBOQItem, id=id)

    store_items = StoreItem.objects.select_related(
        "category"
    ).all().order_by(
        "category__category_name",
        "item_description"
    )

    error = None

    if request.method == "POST":
        try:
            store_item_id = request.POST.get("store_item")

            if not store_item_id:
                error = "Please select store item."

            else:
                boq_item.store_item = get_object_or_404(
                    StoreItem,
                    id=store_item_id
                )

                boq_item.required_quantity = parse_decimal(
                    request.POST.get("required_quantity")
                )

                boq_item.issued_quantity = parse_decimal(
                    request.POST.get("issued_quantity")
                )

                boq_item.consumed_quantity = parse_decimal(
                    request.POST.get("consumed_quantity")
                )

                boq_item.returned_quantity = parse_decimal(
                    request.POST.get("returned_quantity")
                )

                boq_item.rate = parse_decimal(
                    request.POST.get("rate")
                )

                boq_item.remarks = request.POST.get("remarks", "").strip()

                boq_item.save()

                messages.success(request, "BOQ item updated successfully.")
                return redirect("boq_detail", id=boq_item.boq.id)

        except Exception as e:
            error = str(e)

    return render(request, "edit_boq_item.html", {
        "boq_item": boq_item,
        "store_items": store_items,
        "categories": StoreCategory.objects.all().order_by("category_name"),
        "error": error,
    })


@login_required
def delete_boq_item(request, id):
    boq_item = get_object_or_404(ProjectBOQItem, id=id)
    boq_id = boq_item.boq.id

    boq_item.delete()

    messages.success(request, "BOQ item deleted successfully.")
    return redirect("boq_detail", id=boq_id)


@login_required
def delete_boq(request, id):
    boq = get_object_or_404(ProjectBOQ, id=id)
    boq.delete()

    messages.success(request, "BOQ deleted successfully.")
    return redirect("boq_list")