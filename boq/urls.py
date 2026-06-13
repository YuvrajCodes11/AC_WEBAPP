# boq/urls.py

from django.urls import path
from . import views
from .pdf_views import boq_pdf_report

urlpatterns = [

    path(
        "report/pdf/<int:id>/",
        boq_pdf_report,
        name="boq_pdf_report"
    ),

    path(
        "",
        views.boq_list,
        name="boq_list"
    ),

    path(
        "add/",
        views.add_boq,
        name="add_boq"
    ),

    path(
        "detail/<int:id>/",
        views.boq_detail,
        name="boq_detail"
    ),

    path(
        "edit/<int:id>/",
        views.edit_boq,
        name="edit_boq"
    ),

    path(
        "delete/<int:id>/",
        views.delete_boq,
        name="delete_boq"
    ),

    path(
        "item/add/<int:boq_id>/",
        views.add_boq_item,
        name="add_boq_item"
    ),

    path(
        "item/edit/<int:id>/",
        views.edit_boq_item,
        name="edit_boq_item"
    ),

    path(
        "item/delete/<int:id>/",
        views.delete_boq_item,
        name="delete_boq_item"
    ),

]