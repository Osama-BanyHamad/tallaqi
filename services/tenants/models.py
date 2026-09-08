from __future__ import annotations

from django.db import models

from services.common.models import TenantModel, TimeStamped


class Tenant(TimeStamped):
    KINDS = [("center", "مركز"), ("academy", "أكاديمية"), ("institution", "مؤسسة"), ("mosque", "مسجد"),
             ("organization", "منظمة"), ("individual", "معلم مستقل")]
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200, blank=True)
    kind = models.CharField(max_length=20, choices=KINDS, default="center")
    status = models.CharField(max_length=20, default="active")
    plan = models.CharField(max_length=40, default="self_hosted")
    data_region = models.CharField(max_length=20, default="default")
    # settings (tenant-level; branches may override a subset)
    default_locale = models.CharField(max_length=8, default="ar")
    locales = models.JSONField(default=list)                       # ["ar", "en"]
    timezone = models.CharField(max_length=64, default="Asia/Amman")
    currency = models.CharField(max_length=3, default="JOD")
    calendar = models.CharField(max_length=12, default="both")     # gregorian | hijri | both
    default_riwayah = models.CharField(max_length=32, default="hafs_asim")
    default_mushaf_type = models.CharField(max_length=32, default="madani_15_line")
    branding = models.JSONField(default=dict)                      # logo_key, accent, app_name
    recording_allowed = models.BooleanField(default=False)
    communication_policy = models.JSONField(default=dict)

    class Meta:
        db_table = "tenants_tenant"

    def __str__(self):
        return self.slug


class Branch(TenantModel):
    name = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200, blank=True)
    code = models.CharField(max_length=20, blank=True)
    timezone = models.CharField(max_length=64, blank=True)
    locale = models.CharField(max_length=8, blank=True)
    address = models.JSONField(default=dict)
    gender_policy = models.CharField(max_length=12, default="mixed")   # mixed | male | female
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "tenants_branch"
        unique_together = [("tenant", "name")]

    def scope_attrs(self):
        from packages.permissions.resolve import ScopeAttrs
        return ScopeAttrs(branch_id=str(self.id))


class Membership(TimeStamped):
    """Bridge between a global Account and a Tenant. Not under RLS (needed before tenant selection)."""
    account = models.ForeignKey("identity.Account", on_delete=models.CASCADE, related_name="memberships")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="memberships")
    person = models.ForeignKey("people.Person", null=True, blank=True, on_delete=models.SET_NULL, related_name="memberships")
    status = models.CharField(max_length=16, default="active")

    objects = models.Manager()

    class Meta:
        db_table = "tenants_membership"
        unique_together = [("account", "tenant")]

    @classmethod
    def unsafe_all(cls):
        return cls.objects.all()


# expose unsafe_all on the manager for symmetry with TenantManager
Membership.objects.unsafe_all = lambda: Membership.objects.all()  # type: ignore[attr-defined]


class TenantModule(TenantModel):
    module_key = models.CharField(max_length=64)
    enabled = models.BooleanField(default=True)
    settings = models.JSONField(default=dict)

    class Meta:
        db_table = "tenants_module"
        unique_together = [("tenant", "module_key")]
