# store/urls.py

from django.urls import path
from . import views

urlpatterns = [

    # Dashboard
    path(
        "",
        views.store_dashboard,
        name="store_dashboard"
    ),

    # Category
    path(
        "categories/",
        views.store_category_list,
        name="store_category_list"
    ),

    path(
        "categories/add/",
        views.add_store_category,
        name="add_store_category"
    ),

    path(
        "categories/edit/<int:id>/",
        views.edit_store_category,
        name="edit_store_category"
    ),

    path(
        "categories/delete/<int:id>/",
        views.delete_store_category,
        name="delete_store_category"
    ),

    # Store Items
    path(
        "items/",
        views.store_item_list,
        name="store_item_list"
    ),

    path(
        "items/add/",
        views.add_store_item,
        name="add_store_item"
    ),

    path(
        "items/edit/<int:id>/",
        views.edit_store_item,
        name="edit_store_item"
    ),

    path(
        "items/delete/<int:id>/",
        views.delete_store_item,
        name="delete_store_item"
    ),

    path(
        "items/detail/<int:id>/",
        views.store_item_detail,
        name="store_item_detail"
    ),

    # Transactions
    path(
        "transactions/",
        views.store_transaction_list,
        name="store_transaction_list"
    ),

    path(
        "transactions/add/",
        views.add_store_transaction,
        name="add_store_transaction"
    ),

    path(
        "transactions/detail/<int:id>/",
        views.store_transaction_detail,
        name="store_transaction_detail"
    ),

    path(
        "transactions/delete/<int:id>/",
        views.delete_store_transaction,
        name="delete_store_transaction"
    ),

]