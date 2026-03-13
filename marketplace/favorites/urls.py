from django.urls import path
from . import views

urlpatterns = [
    path('', views.favorite_list, name='favorite_list'),
    path('toggle/<int:product_pk>/', views.toggle_favorite, name='toggle_favorite'),
]