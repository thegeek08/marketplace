from django.urls import path
from . import views

urlpatterns = [
    path("list/", views.product_list, name="product_list"),
    path("add/", views.add_product, name="add_product"),
    path("<int:pk>/", views.product_detail, name="product_detail"),
    path("edit/<int:pk>/", views.edit_product, name="edit_product"),
    path("delete/<int:pk>/", views.delete_product, name="delete_product"),
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),
]