from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile, name="profile"),
    path("verify/", views.verify_phone, name="verify_phone"),
    path("verify/resend/", views.resend_verification, name="resend_verification"),
    path("complete-profile/", views.complete_profile, name="complete_profile"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
