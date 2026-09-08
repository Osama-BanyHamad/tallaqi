from __future__ import annotations

from django.db import models

from django.core.serializers.json import DjangoJSONEncoder

from services.common import context
from services.common.models import TenantModel


def _jsonable(value):
    """Round-trip through Django's encoder so UUIDs, datetimes, Decimals and DRF ReturnDicts become plain JSON."""
    import json

    return None if value is None else json.loads(json.dumps(value, cls=DjangoJSONEncoder))


class AuditLog(TenantModel):
    actor = models.ForeignKey("identity.Account", null=True, blank=True, on_delete=models.SET_NULL)
    actor_type = models.CharField(max_length=16, default="user")   # user | system | platform
    action = models.CharField(max_length=80, db_index=True)
    object_type = models.CharField(max_length=80)
    object_id = models.CharField(max_length=64, blank=True)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    device = models.CharField(max_length=200, blank=True)
    request_id = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table = "audit_log"
        ordering = ["-created_at"]

    @classmethod
    def record(cls, request, action: str, object_type: str, object_id, *, before=None, after=None, actor_type="user"):
        meta = getattr(request, "META", {}) if request is not None else {}
        return cls.objects.create(
            actor=getattr(request, "user", None) if request is not None and getattr(request.user, "is_authenticated", False) else None,
            actor_type=actor_type, action=action, object_type=object_type, object_id=str(object_id),
            before=_jsonable(before), after=_jsonable(after),
            ip=(meta.get("HTTP_X_FORWARDED_FOR", "").split(",")[0] or meta.get("REMOTE_ADDR")) or None,
            device=meta.get("HTTP_USER_AGENT", "")[:200], request_id=context.current().request_id)
