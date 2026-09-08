"""PostgreSQL row-level security helpers used by migrations.

Policy: rows are visible/writable only when app.tenant_id matches, unless app.bypass_rls = 'on'.
FORCE ROW LEVEL SECURITY makes the table owner subject to the policy too (superusers still bypass;
the application role must never be a superuser)."""
from django.db import migrations

POLICY_SQL = """
ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
ALTER TABLE {table} FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation ON {table};
CREATE POLICY tenant_isolation ON {table}
  USING (
    current_setting('app.bypass_rls', true) = 'on'
    OR tenant_id::text = current_setting('app.tenant_id', true)
  )
  WITH CHECK (
    current_setting('app.bypass_rls', true) = 'on'
    OR tenant_id::text = current_setting('app.tenant_id', true)
  );
"""

REVERSE_SQL = """
DROP POLICY IF EXISTS tenant_isolation ON {table};
ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;
ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;
"""


def enable_rls(*tables: str) -> list[migrations.RunSQL]:
    return [migrations.RunSQL(POLICY_SQL.format(table=t), REVERSE_SQL.format(table=t)) for t in tables]


READONLY_SQL = """
CREATE OR REPLACE FUNCTION talaqqi_forbid_write() RETURNS trigger AS $$
BEGIN
  IF current_setting('app.quran_core_load', true) = 'on' THEN
    IF TG_OP = 'DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
  END IF;
  RAISE EXCEPTION 'Quran Core table % is read-only (sacred content boundary)', TG_TABLE_NAME;
END; $$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS forbid_write ON {table};
CREATE TRIGGER forbid_write BEFORE INSERT OR UPDATE OR DELETE ON {table}
  FOR EACH ROW EXECUTE FUNCTION talaqqi_forbid_write();
"""


def make_readonly(*tables: str) -> list[migrations.RunSQL]:
    """Quran Core tables: writes raise unless the loader explicitly sets app.quran_core_load='on'."""
    return [migrations.RunSQL(READONLY_SQL.format(table=t), f"DROP TRIGGER IF EXISTS forbid_write ON {t};") for t in tables]
