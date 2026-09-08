from __future__ import annotations

import uuid

from django.http import JsonResponse
from django.utils.translation import activate

from . import context


class RequestIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        rid = request.headers.get("X-Request-Id") or uuid.uuid4().hex
        request.request_id = rid
        response = self.get_response(request)
        response["X-Request-Id"] = rid
        return response


class TenantContextMiddleware:
    """Resolves the tenant for authenticated API calls and establishes the DB context.

    Tenant selection: `X-Tenant: <slug>` header. If absent and the account has exactly one membership,
    that membership is used. Ambiguity is a 400, never a guess.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = (request.headers.get("Accept-Language") or "ar").split(",")[0].split("-")[0]
        activate(lang if lang in ("ar", "en") else "ar")
        ctx = context.TenantContext(request_id=getattr(request, "request_id", ""))
        request.tenant = None
        request.membership = None
        path = request.path
        if path.startswith("/api/v1/") and not path.startswith("/api/v1/auth/"):
            from rest_framework_simplejwt.authentication import JWTAuthentication

            from services.tenants.models import Membership

            try:
                auth = JWTAuthentication().authenticate(request)
            except Exception:
                auth = None
            if auth is not None:
                account, _token = auth
                request.user = account
                slug = request.headers.get("X-Tenant")
                with context.platform_admin("resolve-membership"):
                    qs = Membership.objects.unsafe_all().select_related("tenant").filter(account=account, status="active")
                    memberships = list(qs.filter(tenant__slug=slug)) if slug else list(qs[:2])
                if slug and not memberships:
                    return JsonResponse({"code": "tenant_not_found", "detail": "No active membership in this tenant."}, status=403)
                if not slug and len(memberships) > 1:
                    return JsonResponse({"code": "tenant_required", "detail": "Send X-Tenant header."}, status=400)
                if memberships:
                    m = memberships[0]
                    request.tenant = m.tenant
                    request.membership = m
                    ctx = context.TenantContext(tenant_id=m.tenant_id, account_id=account.id, membership_id=m.id,
                                                request_id=ctx.request_id)
        with context.use(ctx):
            return self.get_response(request)
