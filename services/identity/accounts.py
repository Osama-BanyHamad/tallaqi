"""Tenant account administration: invite a person as a user with a role + scope. Backend-enforced by platform.rbac.assign."""
from __future__ import annotations

import secrets

from django.db import transaction
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from services.audit.models import AuditLog
from services.common import context
from services.common.exceptions import DomainError, PermissionDenied
from services.common.permissions import CapabilityPermission, _assignments
from services.identity.models import Account
from services.rbac.models import Role, RoleAssignment
from services.rbac.services import assign
from services.tenants.models import Membership


class InviteIn(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField()
    password = serializers.CharField(required=False, allow_blank=True, default="", min_length=0)
    person_id = serializers.UUIDField(required=False, allow_null=True)
    role_key = serializers.CharField()
    scope_type = serializers.ChoiceField(choices=["tenant", "branch", "halaqah", "student_set", "self"], default="tenant")
    scope_refs = serializers.ListField(child=serializers.CharField(), required=False, default=list)


class AccountsViewSet(viewsets.ViewSet):
    permission_classes = [CapabilityPermission]
    required_module = "platform.rbac"
    required_permission = {"list": "platform.rbac.read", "create": "platform.rbac.assign", "revoke": "platform.rbac.assign", "reset_password": "platform.rbac.assign"}

    def list(self, request):
        with context.platform_admin("list-accounts"):
            ms = list(Membership.objects.unsafe_all().filter(tenant=request.tenant).select_related("account", "person"))
        ras = RoleAssignment.objects.filter(membership__in=ms).select_related("role")
        by = {}
        for ra in ras:
            by.setdefault(ra.membership_id, []).append({"id": ra.id, "role": ra.role.key, "role_name": ra.role.name_ar, "scope_type": ra.scope_type, "scope_refs": ra.scope_refs})
        return Response([{"membership_id": m.id, "email": m.account.email, "full_name": m.account.full_name, "status": m.status, "is_active": m.account.is_active,
                          "person_id": m.person_id, "person_name": m.person.display_name_ar if m.person else None, "last_login": m.account.last_login,
                          "assignments": by.get(m.id, [])} for m in ms])

    @transaction.atomic
    def create(self, request):
        s = InviteIn(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        role = Role.objects.filter(key=d["role_key"]).first()
        if role is None:
            raise DomainError("Unknown role.")
        mine = {p for a in _assignments(request) for p in a.permissions}
        theirs = set(role.permissions.values_list("permission_key", flat=True))
        if not theirs <= mine:
            raise PermissionDenied("Cannot assign a role with permissions you do not hold.")
        if d["scope_type"] != "tenant" and d["scope_type"] != "self" and not d["scope_refs"]:
            raise DomainError("scope_refs required for this scope.")
        generated = None
        with context.platform_admin("invite"):
            account = Account.objects.filter(email=d["email"].lower()).first()
            if account is None:
                generated = d["password"] or secrets.token_urlsafe(9)
                account = Account.objects.create_user(email=d["email"].lower(), password=generated, full_name=d["full_name"], locale=request.tenant.default_locale)
                if d["password"]:
                    generated = None
            membership, _ = Membership.objects.get_or_create(account=account, tenant=request.tenant, defaults={"person_id": d.get("person_id")})
            if d.get("person_id") and not membership.person_id:
                membership.person_id = d["person_id"]
                membership.save()
        ra = assign(membership, role, d["scope_type"], d["scope_refs"])
        AuditLog.record(request, "permission.changed", "RoleAssignment", ra.id, after={"email": account.email, "role": role.key, "scope": d["scope_type"], "refs": d["scope_refs"]})
        return Response({"membership_id": membership.id, "email": account.email, "assignment_id": ra.id, "generated_password": generated}, status=201)

    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None):
        ra = RoleAssignment.objects.filter(pk=pk).select_related("role").first()
        if ra is None:
            return Response({"code": "not_found"}, status=404)
        AuditLog.record(request, "permission.changed", "RoleAssignment", ra.id, before={"role": ra.role.key, "scope": ra.scope_type}, after=None)
        ra.delete()
        return Response({"revoked": pk})

    @action(detail=True, methods=["post"], url_path="reset-password")
    def reset_password(self, request, pk=None):
        with context.platform_admin("reset-password"):
            m = Membership.objects.unsafe_all().filter(pk=pk, tenant=request.tenant).select_related("account").first()
            if m is None:
                return Response({"code": "not_found"}, status=404)
            new = secrets.token_urlsafe(9)
            m.account.set_password(new)
            m.account.save(update_fields=["password"])
        AuditLog.record(request, "account.password_reset", "Account", m.account_id)
        return Response({"email": m.account.email, "generated_password": new})
