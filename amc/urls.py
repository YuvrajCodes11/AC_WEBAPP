from django.urls import path
from . import views


urlpatterns = [

    path("", views.amc_list, name="amc_list"),

    path("add/", views.add_amc, name="add_amc"),

    path("detail/<int:id>/", views.amc_detail, name="amc_detail"),

    path("edit/<int:id>/", views.edit_amc, name="edit_amc"),

    path("delete/<int:id>/", views.delete_amc, name="delete_amc"),

    path("visit/add/<int:amc_id>/", views.add_amc_visit, name="add_amc_visit"),

    path("visit/edit/<int:visit_id>/", views.edit_amc_visit, name="edit_amc_visit"),

    path("visit/delete/<int:visit_id>/", views.delete_amc_visit, name="delete_amc_visit"),

]