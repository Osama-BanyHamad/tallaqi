from __future__ import annotations

from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from packages.permissions.catalog import MODULES
from services.common import context
from services.common.permissions import CapabilityPermission, _assignments, enabled_modules

from .models import Role, RoleAssignment


class CapabilitiesView(APIView):
    """The manifest the UI renders from. The backend enforces; this is a projection."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.tenant is None:
            return Response({"code": "tenant_required", "detail": "Send X-Tenant header."}, status=400)
        enabled = enabled_modules(request)
        snaps = _assignments(request)
        perms = sorted({p for s in snaps for p in s.permissions})
        t = request.tenant
        return Response({
            "tenant": {"slug": t.slug, "name": t.name, "name_en": t.name_en, "kind": t.kind, "locale": t.default_locale,
                       "locales": t.locales, "timezone": t.timezone, "currency": t.currency, "calendar": t.calendar,
                       "riwayah": t.default_riwayah, "mushaf_type": t.default_mushaf_type, "branding": t.branding,
                       "recording_allowed": t.recording_allowed},
            "person_id": request.membership.person_id,
            "modules": {m.key: {"enabled": m.core or m.key in enabled, "safety": m.safety, "core": m.core} for m in MODULES.values()},
            "permissions": perms,
            "roles": sorted({s.role_key for s in snaps}),
            "scopes": [{"type": s.scope_type, "refs": list(s.scope_refs)} for s in snaps],
        })


class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ["id", "key", "name_ar", "name_en", "system", "permissions"]

    def get_permissions(self, obj):
        return sorted(obj.permissions.values_list("permission_key", flat=True))


class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RoleSerializer
    permission_classes = [CapabilityPermission]
    required_permission = "platform.rbac.read"

    def get_queryset(self):
        return Role.objects.all().prefetch_related("permissions").order_by("key")


class AssignmentSerializer(serializers.ModelSerializer):
    role_key = serializers.CharField(source="role.key", read_only=True)
    account_email = serializers.EmailField(source="membership.account.email", read_only=True)

    class Meta:
        model = RoleAssignment
        fields = ["id", "membership", "role", "role_key", "account_email", "scope_type", "scope_refs", "valid_from", "valid_to"]


class AssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssignmentSerializer
    permission_classes = [CapabilityPermission]
    required_permission = {"list": "platform.rbac.read", "retrieve": "platform.rbac.read", "create": "platform.rbac.assign",
                           "update": "platform.rbac.assign", "partial_update": "platform.rbac.assign", "destroy": "platform.rbac.assign"}

    def get_queryset(self):
        return RoleAssignment.objects.select_related("role", "membership__account").order_by("-created_at")

    def perform_create(self, serializer):
        # Cannot grant permissions you do not hold yourself.
        role = serializer.validated_data["role"]
        mine = {p for s in _assignments(self.request) for p in s.permissions}
        theirs = set(role.permissions.values_list("permission_key", flat=True))
        if not theirs <= mine:
            from services.common.exceptions import PermissionDenied
            raise PermissionDenied("Cannot assign a role with permissions you do not hold.")
        obj = serializer.save()
        from services.audit.models import AuditLog
        AuditLog.record(self.request, "permission.changed", "RoleAssignment", obj.id, after=AssignmentSerializer(obj).data)
        context.current().assignments = []
