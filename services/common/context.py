"""Request/job tenant context. Propagated via contextvars so repositories, RLS, and workers agree."""
from __future__ import annotations

import contextlib
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field

from django.db import connection


@dataclass
class TenantContext:
    tenant_id: uuid.UUID | None = None
    account_id: uuid.UUID | None = None
    membership_id: uuid.UUID | None = None
    bypass_rls: bool = False
    request_id: str = ""
    assignments: list = field(default_factory=list)   # resolved RoleAssignment snapshots


_ctx: ContextVar[TenantContext] = ContextVar("talaqqi_ctx", default=TenantContext())


def current() -> TenantContext:
    return _ctx.get()


def current_tenant_id() -> uuid.UUID | None:
    return _ctx.get().tenant_id


def _apply_db_settings(ctx: TenantContext) -> None:
    """Push the context into PostgreSQL session settings so RLS policies can see it."""
    with connection.cursor() as cur:
        cur.execute("SELECT set_config('app.tenant_id', %s, false)", [str(ctx.tenant_id) if ctx.tenant_id else ""])
        cur.execute("SELECT set_config('app.bypass_rls', %s, false)", ["on" if ctx.bypass_rls else "off"])


@contextlib.contextmanager
def use(ctx: TenantContext):
    token = _ctx.set(ctx)
    try:
        _apply_db_settings(ctx)
        yield ctx
    finally:
        _ctx.reset(token)
        try:
            _apply_db_settings(_ctx.get())
        except Exception:  # connection may already be closed
            pass


@contextlib.contextmanager
def tenant(tenant_id: uuid.UUID, **kw):
    with use(TenantContext(tenant_id=tenant_id, **kw)) as c:
        yield c


@contextlib.contextmanager
def platform_admin(reason: str = ""):
    """Bypass RLS. Only for platform operations (provisioning, seeding, support sessions). Audited by callers."""
    with use(TenantContext(bypass_rls=True, request_id=reason)) as c:
        yield c
