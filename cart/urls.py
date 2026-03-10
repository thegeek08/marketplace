from django.urls import path
from . import views

urlpatterns = [
    path('', views.cart_detail, name='cart_detail'),
    path('add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('update/<int:pk>/', views.update_quantity, name='update_quantity'),
    path('clear/', views.clear_cart, name='clear_cart'),
]