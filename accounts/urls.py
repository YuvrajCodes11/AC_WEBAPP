from django.urls import path
from . import views


urlpatterns = [
    path("", views.login_view, name="login"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("add-manager/", views.add_manager, name="add_manager"),
    path("logout/", views.logout_view, name="logout"),
]