from __future__ import annotations

import uuid

from django.db import models

from . import context


def uuid7() -> uuid.UUID:
    """Time-ordered UUID (v7-style) for friendlier indexes."""
    import os
    import time

    ts = int(time.time() * 1000)
    rand = int.from_bytes(os.urandom(10), "big")
    value = (ts << 80) | (0x7 << 76) | ((rand >> 4) & ((1 << 76) - 1))
    value = (value & ~(0x3 << 62)) | (0x2 << 62)
    return uuid.UUID(int=value)


class TimeStamped(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantQuerySet(models.QuerySet):
    def for_current_tenant(self):
        tid = context.current_tenant_id()
        if context.current().bypass_rls:
            return self
        if tid is None:
            return self.none()
        return self.filter(tenant_id=tid)


class TenantManager(models.Manager):
    """Belt-and-braces: application-level tenant filter in addition to PostgreSQL RLS."""

    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db).for_current_tenant()

    def unsafe_all(self):
        """Explicit escape hatch for platform tooling. Grep-able. Must be paired with context.platform_admin()."""
        return TenantQuerySet(self.model, using=self._db)


class TenantModel(TimeStamped):
    """Every tenant-owned row. RLS policy is attached by services.common.rls for each concrete subclass."""
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, editable=False, db_index=True)

    objects = TenantManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.tenant_id is None:
            tid = context.current_tenant_id()
            if tid is None:
                raise RuntimeError("No tenant context while saving a tenant-owned row")
            self.tenant_id = tid
        super().save(*args, **kwargs)
