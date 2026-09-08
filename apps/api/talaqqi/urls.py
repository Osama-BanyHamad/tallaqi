from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView

from services.common.health import healthz, readyz


def api_root(_request):
    return JsonResponse({"name": "Talaqqi API", "version": "1", "docs": "/api/docs/", "health": "/healthz"})


urlpatterns = [
    path("", api_root),
    path("healthz", healthz),
    path("readyz", readyz),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularRedocView.as_view(url_name="schema")),
    path("api/v1/auth/", include("services.identity.urls")),
    path("api/v1/", include("services.tenants.urls")),
    path("api/v1/", include("services.rbac.urls")),
    path("api/v1/quran/", include("services.quran.urls")),
    path("api/v1/", include("services.people.urls")),
    path("api/v1/", include("services.hifz.urls")),
    path("api/v1/finance/", include("services.finance.urls")),
    path("api/v1/ai/", include("services.ai.urls")),
    path("api/v1/", include("services.audit.urls")),
]
