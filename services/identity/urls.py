from django.urls import path

from .views import LoginView, MeView, RefreshView

urlpatterns = [
    path("login", LoginView.as_view(), name="auth-login"),
    path("refresh", RefreshView.as_view(), name="auth-refresh"),
    path("me", MeView.as_view(), name="auth-me"),
]
