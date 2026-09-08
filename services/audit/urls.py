from rest_framework.routers import DefaultRouter

from .views import AuditViewSet

router = DefaultRouter(trailing_slash=False)
router.register("audit", AuditViewSet, basename="audit")
urlpatterns = router.urls
