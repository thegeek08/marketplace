from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('<int:pk>/lire/', views.mark_read_and_redirect, name='notification_read'),
]
