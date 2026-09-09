from django.urls import path

from .signup import SignupView
from .views import LoginView, MeView, RefreshView

urlpatterns = [
    path("login", LoginView.as_view(), name="auth-login"),
    path("signup", SignupView.as_view(), name="auth-signup"),
    path("refresh", RefreshView.as_view(), name="auth-refresh"),
    path("me", MeView.as_view(), name="auth-me"),
]
