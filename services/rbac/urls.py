from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AssignmentViewSet, CapabilitiesView, RoleViewSet

router = DefaultRouter(trailing_slash=False)
router.register("roles", RoleViewSet, basename="role")
router.register("role-assignments", AssignmentViewSet, basename="role-assignment")

urlpatterns = [path("me/capabilities", CapabilitiesView.as_view())] + router.urls
