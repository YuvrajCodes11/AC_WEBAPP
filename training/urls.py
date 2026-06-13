from django.urls import path
from . import views


urlpatterns = [

    path("", views.training_dashboard, name="training_dashboard"),

]