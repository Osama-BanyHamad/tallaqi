from rest_framework.routers import DefaultRouter

from .views import ReadingViewSet

router = DefaultRouter(trailing_slash=False)
router.register("reading", ReadingViewSet, basename="reading")

urlpatterns = router.urls
