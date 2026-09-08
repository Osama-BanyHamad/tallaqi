"""DRF integration for the capability + RBAC system (backend-enforced)."""
from __future__ import annotations

from rest_framework.permissions import BasePermission

from packages.permissions.resolve import Decision, can, module_enabled
from services.common import context
from services.common.exceptions import CapabilityDisabled, PermissionDenied


def _assignments(request):
    from services.rbac.models import RoleAssignment

    ctx = context.current()
    if ctx.assignments:
        return ctx.assignments
    if request.membership is None:
        return []
    ras = RoleAssignment.objects.filter(membership=request.membership).select_related("role").prefetch_related("role__permissions")
    snap = [ra.snapshot() for ra in ras]
    ctx.assignments = snap
    return snap


def enabled_modules(request) -> set[str]:
    from services.tenants.models import TenantModule

    if request.tenant is None:
        return set()
    cache = getattr(request, "_enabled_modules", None)
    if cache is None:
        cache = set(TenantModule.objects.filter(enabled=True).values_list("module_key", flat=True))
        request._enabled_modules = cache
    return cache


def check(request, permission: str, module: str | None = None, obj=None) -> Decision:
    if request.tenant is None:
        raise PermissionDenied("No tenant context.")
    mod = module or permission.rsplit(".", 1)[0]
    if not module_enabled(mod, enabled_modules(request)):
        raise CapabilityDisabled(f"Module '{mod}' is disabled for this tenant.")
    d = can(_assignments(request), permission, obj)
    if not d.allowed:
        raise PermissionDenied(d.reason)
    return d


class CapabilityPermission(BasePermission):
    """Views declare `required_module` and `required_permission` (str or dict by action)."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        perm = getattr(view, "required_permission", None)
        if isinstance(perm, dict):
            perm = perm.get(getattr(view, "action", None) or request.method.lower())
        if perm is None:
            return True
        check(request, perm, getattr(view, "required_module", None))
        return True

    def has_object_permission(self, request, view, obj):
        perm = getattr(view, "required_permission", None)
        if isinstance(perm, dict):
            perm = perm.get(getattr(view, "action", None) or request.method.lower())
        if perm is None:
            return True
        check(request, perm, getattr(view, "required_module", None), obj)
        return True


def scoped(request, queryset, *, branch_field="branch_id", halaqah_field=None, student_field=None, person_field=None):
    """Restrict a queryset to the caller's scopes. Tenant filtering already happened (manager + RLS)."""
    from django.db.models import Q

    snaps = _assignments(request)
    if any(s.scope_type == "tenant" for s in snaps):
        return queryset
    q = Q(pk__in=[])
    for s in snaps:
        if s.scope_type == "branch" and branch_field:
            q |= Q(**{f"{branch_field}__in": s.scope_refs})
        elif s.scope_type == "halaqah" and halaqah_field:
            q |= Q(**{f"{halaqah_field}__in": s.scope_refs})
        elif s.scope_type == "student_set" and student_field:
            q |= Q(**{f"{student_field}__in": s.scope_refs})
        elif s.scope_type == "self" and person_field and request.membership and request.membership.person_id:
            q |= Q(**{person_field: request.membership.person_id})
    return queryset.filter(q).distinct()
