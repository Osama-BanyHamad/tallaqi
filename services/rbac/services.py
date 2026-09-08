"""Role provisioning and assignment (used by seed, tenant provisioning, and admin APIs)."""
from __future__ import annotations

from packages.permissions.catalog import SYSTEM_ROLES

from .models import Role, RoleAssignment, RolePermission


def ensure_system_roles(tenant) -> dict[str, Role]:
    roles: dict[str, Role] = {}
    for key, spec in SYSTEM_ROLES.items():
        role, _ = Role.objects.update_or_create(tenant=tenant, key=key, defaults={
            "name_ar": spec["name_ar"], "name_en": spec["name_en"], "system": True})
        existing = set(role.permissions.values_list("permission_key", flat=True))
        for p in spec["permissions"]:
            if p not in existing:
                RolePermission.objects.create(tenant=tenant, role=role, permission_key=p)
        roles[key] = role
    return roles


def assign(membership, role: Role, scope_type: str = "tenant", scope_refs: list | None = None) -> RoleAssignment:
    return RoleAssignment.objects.create(tenant=membership.tenant, membership=membership, role=role,
                                         scope_type=scope_type, scope_refs=[str(r) for r in (scope_refs or [])])
