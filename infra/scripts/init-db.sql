-- Application role is deliberately NOT a superuser so PostgreSQL row-level security applies to it.
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'talaqqi_app') THEN
    CREATE ROLE talaqqi_app LOGIN PASSWORD 'talaqqi_dev' CREATEDB;
  END IF;
END $$;
SELECT 'CREATE DATABASE talaqqi OWNER talaqqi_app' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'talaqqi') \gexec
