#!/usr/bin/env bash
# Create a local dev/test database, apply migrations, and create the
# non-owner login role the API uses. Synthetic data only — never point this
# at a database that holds real veteran records.
#
#   PGHOST/PGPORT/PGUSER   superuser connection (defaults: localhost/5432/postgres)
#   VB_DB                  database name (default: vetbuddy_dev)
#   VB_APP_PASSWORD        password for the vb_app login role (default: dev-only placeholder)
set -euo pipefail
cd "$(dirname "$0")/.."

PGHOST=${PGHOST:-localhost}; PGPORT=${PGPORT:-5432}; PGUSER=${PGUSER:-postgres}
VB_DB=${VB_DB:-vetbuddy_dev}
VB_APP_PASSWORD=${VB_APP_PASSWORD:-change-me-local-only}
export PGHOST PGPORT PGUSER

if [[ "${1:-}" == "--reset" ]]; then
  psql -q -d postgres -c "DROP DATABASE IF EXISTS ${VB_DB}"
fi
psql -qtA -d postgres -c "SELECT 1 FROM pg_database WHERE datname='${VB_DB}'" | grep -q 1 \
  || psql -q -d postgres -c "CREATE DATABASE ${VB_DB}"

DATABASE_ADMIN_URL="host=${PGHOST} port=${PGPORT} user=${PGUSER} dbname=${VB_DB}" \
  python3 scripts/migrate.py

# V0 reference corpus (migration 0011): full idempotent refresh, owner only.
psql -q -v ON_ERROR_STOP=1 -d "${VB_DB}" -f database/seeds/0011_reference.sql
# Benefit Vault registry (migration 0014): generated, idempotent, one transaction.
psql -q -v ON_ERROR_STOP=1 -1 -d "${VB_DB}" -f database/seeds/0014_benefit_vault_seed.sql

# Roles are cluster-wide; membership in vetbuddy_app (created by 0009) is the
# only privilege vb_app has. It owns nothing, so FORCE RLS always applies.
psql -q -d "${VB_DB}" <<SQL
DO \$\$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'vb_app') THEN
    CREATE ROLE vb_app LOGIN PASSWORD '${VB_APP_PASSWORD}' IN ROLE vetbuddy_app;
  END IF;
END \$\$;
GRANT vetbuddy_app TO vb_app;
SQL
echo "DATABASE_URL=host=${PGHOST} port=${PGPORT} user=vb_app password=*** dbname=${VB_DB}"
