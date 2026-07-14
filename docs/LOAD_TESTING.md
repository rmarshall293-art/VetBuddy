# Load Testing

How to run load tests against VetBuddy and store results in the `load_test_results` table.

## Overview

Load testing validates VetBuddy's API performance under concurrent user load. Results are stored in PostgreSQL for tracking across environments and releases.

### Tools

| Tool | Status | Location |
|------|--------|----------|
| Locust | Recommended | `tests/load/locustfile.py` (create when ready) |
| k6 | Alternative | `tests/load/k6/` (optional) |

This document focuses on **Locust** as the primary load testing tool.

## Prerequisites

```bash
pip install locust
```

Target environment running:

- FastAPI backend on port 8000 (or staging URL)
- PostgreSQL with schema applied
- Demo seed data loaded (for auth testing)

## Locust Setup

Create `tests/load/locustfile.py`:

```python
import os
from locust import HttpUser, task, between


API_PREFIX = os.getenv("API_PREFIX", "/api/v1")
BASE_URL = os.getenv("LOAD_TEST_BASE_URL", "http://localhost:8000")


class VeteranUser(HttpUser):
    """Simulates a veteran browsing claims and benefits."""

    wait_time = between(1, 3)
    token = None

    def on_start(self):
        response = self.client.post(
            f"{API_PREFIX}/auth/login",
            json={
                "email": "demo.veteran@vetbuddy.local",
                "password": "DemoPass123!",
            },
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")

    @property
    def auth_headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    @task(3)
    def get_profile(self):
        self.client.get(f"{API_PREFIX}/users/me", headers=self.auth_headers)

    @task(2)
    def list_claims(self):
        self.client.get(f"{API_PREFIX}/claims", headers=self.auth_headers)

    @task(2)
    def get_benefits(self):
        self.client.get(f"{API_PREFIX}/benefits", headers=self.auth_headers)

    @task(1)
    def state_comparison(self):
        self.client.get(f"{API_PREFIX}/jurisdictions/compare?states=AL,TX,FL")

    @task(1)
    def health_check(self):
        self.client.get("/health")


class AnonymousUser(HttpUser):
    """Simulates unauthenticated visitors."""

    wait_time = between(2, 5)
    weight = 1

    @task
    def health_check(self):
        self.client.get("/health")

    @task
    def public_benefits(self):
        self.client.get(f"{API_PREFIX}/jurisdictions")
```

## Running Locust

### Web UI Mode (Interactive)

```bash
cd tests/load
locust -f locustfile.py --host=http://localhost:8000
```

Open http://localhost:8089 and configure:

| Parameter | Staging | Stress Test |
|-----------|---------|-------------|
| Number of users | 50 | 200 |
| Spawn rate | 5/sec | 10/sec |
| Duration | 5 minutes | 15 minutes |

### Headless Mode (CI / Automated)

```bash
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  -u 50 \
  -r 5 \
  --run-time 5m \
  --csv=results/load_test_run \
  --html=results/load_test_report.html
```

### Against Staging

```bash
LOAD_TEST_BASE_URL=https://staging-api.vetbuddy.example.com \
locust -f tests/load/locustfile.py \
  --host=$LOAD_TEST_BASE_URL \
  --headless -u 100 -r 10 --run-time 10m
```

## Test Scenarios

| Scenario | Users | Duration | Purpose |
|----------|-------|----------|---------|
| Smoke | 10 | 1 min | Verify basic functionality |
| Baseline | 50 | 5 min | Normal load performance |
| Peak | 100 | 10 min | Expected peak traffic |
| Stress | 200+ | 15 min | Find breaking point |
| Soak | 50 | 60 min | Memory leaks, connection pool exhaustion |

## Metrics to Capture

| Metric | Target (Baseline) | Alert Threshold |
|--------|-------------------|-----------------|
| p50 response time | < 200ms | > 500ms |
| p95 response time | < 500ms | > 1000ms |
| p99 response time | < 1000ms | > 2000ms |
| Error rate | < 0.1% | > 1% |
| Requests/sec | > 100 | < 50 |

## Storing Results in Database

After a Locust run, insert results into `load_test_results`:

```sql
INSERT INTO load_test_results (
    test_run_id,
    scenario_name,
    concurrent_users,
    total_requests,
    success_rate,
    p50_ms,
    p95_ms,
    p99_ms,
    error_summary,
    environment
) VALUES (
    'run-20250714-001',
    'baseline_50_users',
    50,
    15000,
    99.95,
    145,
    380,
    720,
    '{"timeouts": 2, "500_errors": 1}'::jsonb,
    'staging'
);
```

Or via a post-run script (`tests/load/store_results.py`):

```python
import json
import sys
import psycopg2

def store_results(csv_stats_path, run_id, scenario, environment):
    # Parse Locust CSV output
    # Insert into load_test_results
    pass
```

## Locust CSV Output

Headless mode with `--csv=results/run` produces:

| File | Contents |
|------|----------|
| `run_stats.csv` | Per-endpoint statistics |
| `run_stats_history.csv` | Time-series data |
| `run_failures.csv` | Failed requests |

Parse `run_stats.csv` for aggregate p50/p95/p99 values.

## What to Monitor During Tests

### Application

- FastAPI response times (Locust dashboard)
- Error rate and error types
- JWT auth latency

### Database

```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity WHERE datname = 'vetbuddy';

-- Slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Infrastructure

- CPU and memory utilization
- Database connection pool saturation
- Network latency

## Known Bottlenecks

Based on architecture review (not yet load tested):

1. **Database connection pool** — Default pool size 10; may need tuning under 100+ concurrent users
2. **JWT validation** — CPU-bound; consider caching decoded tokens
3. **N+1 queries** — Claims dashboard view is pre-aggregated; API endpoints should use eager loading
4. **No Redis caching** — Benefits/jurisdiction data fetched from DB on every request
5. **Synchronous SQLAlchemy** — Consider async driver for high concurrency

## CI Integration

Add to `.github/workflows/ci.yml` (optional, against staging):

```yaml
load-test:
  runs-on: ubuntu-latest
  if: github.event_name == 'schedule'  # Weekly
  steps:
    - uses: actions/checkout@v4
    - run: pip install locust psycopg2-binary
    - run: |
        locust -f tests/load/locustfile.py \
          --host=${{ secrets.STAGING_API_URL }} \
          --headless -u 25 -r 5 --run-time 3m \
          --csv=results/run
```

## Safety Guidelines

- **Never load test production** without explicit approval and off-peak scheduling
- Use demo accounts (`demo.veteran@vetbuddy.local`) — not real veteran data
- Set `VA_MOCK_MODE=true` and `STRIPE_MOCK_MODE=true` on test targets
- Rate limit load test origin IP if testing shared staging
- Clean up test data after stress tests (claims, sessions created under load)

## Current Status

| Item | Status |
|------|--------|
| `load_test_results` table | Created in schema |
| Locust test file | Documented; create `tests/load/locustfile.py` |
| Baseline benchmarks | Not yet established |
| CI load test job | Not yet configured |
| Results storage script | Not yet implemented |

Establish baseline benchmarks after the first staging load test run and record them here.
