from django.urls import path
from . import views


urlpatterns = [

    path("", views.service_list, name="service_list"),

    path("add/", views.add_service, name="add_service"),

    path("detail/<int:id>/", views.service_detail, name="service_detail"),

    path("edit/<int:id>/", views.edit_service, name="edit_service"),

    path("delete/<int:id>/", views.delete_service, name="delete_service"),

]