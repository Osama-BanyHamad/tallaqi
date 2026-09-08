#!/bin/sh
# Runs once on first PostgreSQL start (docker-entrypoint-initdb.d). Creates the non-superuser app role so RLS applies to it.
set -e
psql -v ON_ERROR_STOP=1 -U postgres <<SQL
DO \$\$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'talaqqi_app') THEN
    CREATE ROLE talaqqi_app LOGIN PASSWORD '${APP_DB_PASSWORD:-talaqqi_dev}' CREATEDB;
  END IF;
END \$\$;
SELECT 'CREATE DATABASE talaqqi OWNER talaqqi_app' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'talaqqi') \gexec
SQL
