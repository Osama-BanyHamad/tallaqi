from __future__ import annotations

from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from services.common import context
from services.tenants.models import Membership


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class MembershipOut(serializers.Serializer):
    tenant_slug = serializers.CharField()
    tenant_name = serializers.CharField()
    tenant_kind = serializers.CharField()
    roles = serializers.ListField(child=serializers.CharField())


def memberships_for(account):
    from services.rbac.models import RoleAssignment
    with context.platform_admin("login-memberships"):
        ms = list(Membership.objects.unsafe_all().select_related("tenant").filter(account=account, status="active"))
        ras = RoleAssignment.objects.unsafe_all().filter(membership__in=ms).select_related("role")
        by_m: dict = {}
        for ra in ras:
            by_m.setdefault(ra.membership_id, []).append(ra.role.key)
    return [{"tenant_slug": m.tenant.slug, "tenant_name": m.tenant.name, "tenant_kind": m.tenant.kind,
             "roles": sorted(set(by_m.get(m.id, [])))} for m in ms]


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    @extend_schema(request=LoginSerializer, responses=inline_serializer("LoginOut", {
        "access": serializers.CharField(), "refresh": serializers.CharField(),
        "account": inline_serializer("AccountOut", {"id": serializers.UUIDField(), "email": serializers.EmailField(),
                                                    "full_name": serializers.CharField(), "locale": serializers.CharField()}),
        "memberships": MembershipOut(many=True)}))
    def post(self, request):
        s = LoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = authenticate(request, username=s.validated_data["email"].lower(), password=s.validated_data["password"])
        if user is None or not user.is_active:
            return Response({"code": "invalid_credentials", "detail": "البريد الإلكتروني أو كلمة المرور غير صحيحة."}, status=status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token), "refresh": str(refresh),
            "account": {"id": user.id, "email": user.email, "full_name": user.full_name, "locale": user.locale},
            "memberships": memberships_for(user),
        })


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        u = request.user
        return Response({"id": u.id, "email": u.email, "full_name": u.full_name, "locale": u.locale,
                         "is_platform_admin": u.is_platform_admin, "memberships": memberships_for(u)})


class RefreshView(TokenRefreshView):
    authentication_classes = []
