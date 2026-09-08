from __future__ import annotations

from rest_framework import serializers, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from packages.permissions.catalog import MODULES, validate_enable
from services.common.exceptions import DomainError
from services.common.permissions import CapabilityPermission, enabled_modules, scoped

from .models import Branch, Tenant, TenantModule


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ["id", "slug", "name", "name_en", "kind", "status", "default_locale", "locales", "timezone", "currency",
                  "calendar", "default_riwayah", "default_mushaf_type", "branding", "recording_allowed", "communication_policy"]
        read_only_fields = ["id", "slug", "status"]


class TenantView(APIView):
    permission_classes = [CapabilityPermission]
    required_permission = {"get": "platform.tenancy.read", "patch": "platform.tenancy.manage"}

    def get(self, request):
        return Response(TenantSerializer(request.tenant).data)

    def patch(self, request):
        s = TenantSerializer(request.tenant, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data)


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "name", "name_en", "code", "timezone", "locale", "address", "gender_policy", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class BranchViewSet(viewsets.ModelViewSet):
    serializer_class = BranchSerializer
    permission_classes = [CapabilityPermission]
    required_permission = {"list": "platform.tenancy.read", "retrieve": "platform.tenancy.read",
                           "create": "platform.tenancy.manage", "update": "platform.tenancy.manage",
                           "partial_update": "platform.tenancy.manage", "destroy": "platform.tenancy.manage"}
    search_fields = ["name", "name_en", "code"]

    def get_queryset(self):
        return scoped(self.request, Branch.objects.all(), branch_field="id").order_by("name")


class ModulesView(APIView):
    """Capability configuration. Backend-enforced: disabling a module makes its endpoints return 403."""
    permission_classes = [CapabilityPermission]
    required_permission = {"get": "platform.tenancy.read", "put": "platform.tenancy.manage"}

    def get(self, request):
        enabled = enabled_modules(request)
        rows = TenantModule.objects.all()
        settings = {r.module_key: r.settings for r in rows}
        return Response([{"key": m.key, "name_ar": m.name_ar, "name_en": m.name_en, "safety": m.safety, "core": m.core,
                          "requires": list(m.requires), "enabled": m.core or m.key in enabled,
                          "settings": settings.get(m.key, {})} for m in MODULES.values()])

    def put(self, request):
        key = request.data.get("key")
        enabled = bool(request.data.get("enabled", True))
        if key not in MODULES:
            raise DomainError("Unknown module.")
        m = MODULES[key]
        if m.core and not enabled:
            raise DomainError("Core modules cannot be disabled.")
        current = enabled_modules(request)
        if enabled:
            missing = validate_enable(key, current)
            if missing:
                raise DomainError(f"Enable dependencies first: {', '.join(missing)}")
        else:
            dependents = [x.key for x in MODULES.values() if key in x.requires and x.key in current]
            if dependents:
                raise DomainError(f"Disable dependents first: {', '.join(dependents)}")
        row, _ = TenantModule.objects.update_or_create(module_key=key, defaults={"enabled": enabled,
                                                       "settings": request.data.get("settings", {})})
        from services.audit.models import AuditLog
        AuditLog.record(request, "tenant.module.changed", "TenantModule", row.id, before={"enabled": not enabled},
                        after={"enabled": enabled})
        request._enabled_modules = None
        return Response({"key": key, "enabled": enabled})
