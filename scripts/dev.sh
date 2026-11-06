#!/usr/bin/env bash
# One command: migrate a local DB and serve the API + web shell on :8000.
set -euo pipefail
cd "$(dirname "$0")/.."
VB_DB=${VB_DB:-vetbuddy_dev} scripts/dev_db.sh
export DATABASE_URL=${DATABASE_URL:-"host=${PGHOST:-localhost} port=${PGPORT:-5432} user=vb_app password=${VB_APP_PASSWORD:-change-me-local-only} dbname=${VB_DB:-vetbuddy_dev}"}
export VB_AUTH_MODE=${VB_AUTH_MODE:-dev}
cd backend && exec python3 -m uvicorn app.api.main:app --host 127.0.0.1 --port ${PORT:-8000}
