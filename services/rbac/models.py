from __future__ import annotations

from django.db import models

from packages.permissions.resolve import AssignmentSnapshot
from services.common.models import TenantModel


class Role(TenantModel):
    key = models.CharField(max_length=40)
    name_ar = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100, blank=True)
    system = models.BooleanField(default=False)

    class Meta:
        db_table = "rbac_role"
        unique_together = [("tenant", "key")]

    def __str__(self):
        return self.key


class RolePermission(TenantModel):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="permissions")
    permission_key = models.CharField(max_length=80)

    class Meta:
        db_table = "rbac_role_permission"
        unique_together = [("role", "permission_key")]


class RoleAssignment(TenantModel):
    SCOPES = [("tenant", "tenant"), ("branch", "branch"), ("halaqah", "halaqah"), ("course", "course"),
              ("student_set", "student_set"), ("self", "self")]
    membership = models.ForeignKey("tenants.Membership", on_delete=models.CASCADE, related_name="role_assignments")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="assignments")
    scope_type = models.CharField(max_length=16, choices=SCOPES, default="tenant")
    scope_refs = models.JSONField(default=list)     # list of ids (str)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "rbac_role_assignment"

    def snapshot(self) -> AssignmentSnapshot:
        return AssignmentSnapshot(self.role.key, frozenset(p.permission_key for p in self.role.permissions.all()),
                                  self.scope_type, tuple(str(r) for r in self.scope_refs))
