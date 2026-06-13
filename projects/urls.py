# projects/urls.py

from django.urls import path
from . import views

urlpatterns = [

    path(
        "",
        views.project_list,
        name="project_list"
    ),

    path(
        "add/",
        views.add_project,
        name="add_project"
    ),

    path(
        "detail/<int:id>/",
        views.project_detail,
        name="project_detail"
    ),

    path(
        "edit/<int:id>/",
        views.edit_project,
        name="edit_project"
    ),

    path(
        "delete/<int:id>/",
        views.delete_project,
        name="delete_project"
    ),

]