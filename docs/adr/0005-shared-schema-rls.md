# ADR-0005 — Multi-tenancy: shared schema + PostgreSQL row-level security

Status: accepted · Date: 2026-09-08

## Decision
Every tenant-owned table carries `tenant_id`. Two independent layers enforce isolation:
1. Application: `TenantManager` filters every queryset by the request/job context (`services/common/context.py`); unscoped access requires the grep-able `unsafe_all()` inside `context.platform_admin()`.
2. Database: `ENABLE + FORCE ROW LEVEL SECURITY` with policy `tenant_id = current_setting('app.tenant_id')` unless `app.bypass_rls = 'on'` (`services/common/rls.py`). The application role is never a superuser.

Quran Core tables have no `tenant_id`; a trigger rejects writes unless `app.quran_core_load='on'` (loader only).

## Consequences
- One database and one migration run; a single VPS suffices.
- `tests/test_isolation_and_permissions.py` proves list, search, IDOR, and raw-SQL isolation.
- Large or regulated tenants can later be routed to a dedicated database with the same schema without application changes.
