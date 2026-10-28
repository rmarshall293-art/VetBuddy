#!/usr/bin/env bash
# Fresh test DB -> unit + integration tests. Add --ui to also run the browser smoke test.
set -euo pipefail
cd "$(dirname "$0")/.."
VB_DB=vetbuddy_test scripts/dev_db.sh --reset >/dev/null
export TEST_DATABASE_URL=${TEST_DATABASE_URL:-"host=${PGHOST:-localhost} port=${PGPORT:-5432} user=vb_app password=${VB_APP_PASSWORD:-change-me-local-only} dbname=vetbuddy_test"}
export TEST_DATABASE_ADMIN_URL=${TEST_DATABASE_ADMIN_URL:-"host=${PGHOST:-localhost} port=${PGPORT:-5432} user=${PGUSER:-postgres} dbname=vetbuddy_test"}
# pytest collects both the unittest-style suites and backend/tests/vault (pytest-style).
(cd backend && VB_LOG_LEVEL=WARNING python3 -m pytest -q -p no:cacheprovider tests)
if [[ "${1:-}" == "--ui" ]]; then
  (cd backend && VB_AUTH_MODE=dev DATABASE_URL="$TEST_DATABASE_URL" python3 -m uvicorn app.api.main:app --port 8765 >/dev/null 2>&1 & echo $! > /tmp/vb-ui.pid)
  sleep 2; trap 'kill $(cat /tmp/vb-ui.pid)' EXIT
  BASE_URL=http://localhost:8765 python3 tests/e2e/smoke_ui.py
  python3 tests/e2e/smoke_standalone.py
fi
