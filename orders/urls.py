from django.urls import path
from . import views

urlpatterns = [
    # Client
    path('checkout/', views.checkout, name='checkout'),
    path('<int:pk>/', views.order_detail, name='order_detail'),
    path('mes-commandes/', views.order_list, name='order_list'),
    # Vendeur
    path('vendeur/', views.vendor_order_list, name='vendor_order_list'),
    path('vendeur/<int:pk>/', views.vendor_order_detail, name='vendor_order_detail'),
    path('vendeur/<int:pk>/statut/', views.update_order_status, name='update_order_status'),
]
