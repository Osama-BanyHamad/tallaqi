from rest_framework.routers import DefaultRouter

from .views import DashboardView, HalaqahViewSet, StaffViewSet, StudentViewSet

router = DefaultRouter(trailing_slash=False)
router.register("students", StudentViewSet, basename="student")
router.register("staff", StaffViewSet, basename="staff")
router.register("halaqat", HalaqahViewSet, basename="halaqah")
router.register("dashboard", DashboardView, basename="dashboard")

urlpatterns = router.urls
