from django.urls import path
from . import views

urlpatterns = [
    path('', views.conversation_list, name='conversation_list'),
    path('<int:pk>/', views.conversation_detail, name='conversation_detail'),
    path('start/<int:product_pk>/', views.start_conversation, name='start_conversation'),
    path('<int:pk>/bloquer/', views.block_user, name='block_user'),
    path('<int:pk>/signaler/', views.report_user, name='report_user'),
]
