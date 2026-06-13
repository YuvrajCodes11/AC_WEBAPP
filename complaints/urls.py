from django.urls import path
from . import views


urlpatterns = [
    path("", views.complaint_dashboard, name="complaint_dashboard"),
    path("list/", views.complaint_list, name="complaint_list"),
    path("add/", views.add_complaint, name="add_complaint"),
    path("edit/<int:pk>/", views.edit_complaint, name="edit_complaint"),
    path("detail/<int:pk>/", views.complaint_detail, name="complaint_detail"),
    path("yearly-report/", views.yearly_visit_report, name="yearly_visit_report"),
    path("customer-history/", views.customer_service_history_report, name="customer_service_history_report"),
    path("customer-history/pdf/<int:customer_id>/", views.customer_service_history_pdf, name="customer_service_history_pdf"),
]
