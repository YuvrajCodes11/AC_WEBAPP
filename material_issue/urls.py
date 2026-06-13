# material_issue/urls.py

from django.urls import path
from . import views
from .pdf_views import project_full_pdf_report

urlpatterns = [

    path(
        "project-report/pdf/<int:project_id>/",
        project_full_pdf_report,
        name="project_full_pdf_report"
    ),

    path(
        "",
        views.material_issue_list,
        name="material_issue_list"
    ),

    path(
        "add/",
        views.add_material_issue,
        name="add_material_issue"
    ),

    path(
        "detail/<int:id>/",
        views.material_issue_detail,
        name="material_issue_detail"
    ),

    path(
        "edit/<int:id>/",
        views.edit_material_issue,
        name="edit_material_issue"
    ),

    path(
        "delete/<int:id>/",
        views.delete_material_issue,
        name="delete_material_issue"
    ),

    path(
        "print/<int:id>/",
        views.material_issue_print,
        name="material_issue_print"
    ),

    path(
        "item/add/<int:issue_id>/",
        views.add_material_issue_item,
        name="add_material_issue_item"
    ),

    path(
        "item/edit/<int:id>/",
        views.edit_material_issue_item,
        name="edit_material_issue_item"
    ),

    path(
        "item/delete/<int:id>/",
        views.delete_material_issue_item,
        name="delete_material_issue_item"
    ),
    path(
        "customer-report/",
        views.material_issue_customer_report,
        name="material_issue_customer_report"
    ),

]