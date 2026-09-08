from rest_framework.routers import DefaultRouter

from .views import JourneyViewSet, PoliciesView, RecitationViewSet

router = DefaultRouter(trailing_slash=False)
router.register("journeys", JourneyViewSet, basename="journey")
router.register("recitations", RecitationViewSet, basename="recitation")
router.register("policies", PoliciesView, basename="policy")

urlpatterns = router.urls
