from rest_framework import serializers, viewsets

from services.common.permissions import CapabilityPermission

from .models import AuditLog


class AuditSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = ["id", "actor_email", "actor_type", "action", "object_type", "object_id", "before", "after", "ip", "request_id", "created_at"]


class AuditViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditSerializer
    permission_classes = [CapabilityPermission]
    required_module = "platform.audit"
    required_permission = "platform.audit.read"
    filterset_fields = ["action", "object_type", "actor"]
    search_fields = ["action", "object_type", "object_id", "actor__email"]

    def get_queryset(self):
        return AuditLog.objects.select_related("actor").order_by("-created_at")
