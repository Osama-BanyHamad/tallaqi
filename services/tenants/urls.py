from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import BranchViewSet, ModulesView, TenantView

router = DefaultRouter(trailing_slash=False)
router.register("branches", BranchViewSet, basename="branch")

urlpatterns = [
    path("tenant", TenantView.as_view()),
    path("tenant/modules", ModulesView.as_view()),
] + router.urls
