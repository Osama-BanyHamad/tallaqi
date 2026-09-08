from rest_framework.routers import DefaultRouter

from .views import AiViewSet

router = DefaultRouter(trailing_slash=False)
router.register("", AiViewSet, basename="ai")

urlpatterns = router.urls
