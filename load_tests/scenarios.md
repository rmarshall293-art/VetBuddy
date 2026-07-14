# VetBuddy Load Test Scenarios

This document describes Locust scenarios in `locustfile.py` for VetBuddy API load testing.

## Prerequisites

- Running VetBuddy API (`docker compose up` or `uvicorn` locally)
- Python 3.12+
- `pip install locust`

## Scenarios

| User class | Weight | Description |
|------------|--------|-------------|
| `VetBuddyUser` | default (3) | Full veteran journey: register/login, claims CRUD, state comparison, VA mock, benefits search, Alabama ranking |
| `AnonymousBrowseUser` | 1 | Unauthenticated state browse and VA mock profile |
| `ConcurrentCheckoutUser` | 1 | Payment mock checkout + webhook under concurrent auth |

## Endpoint coverage

1. **Account creation & login** — `POST /api/v1/auth/register`, `POST /api/v1/auth/login`
2. **Claims dashboard** — `GET/POST /api/v1/claims`
3. **State comparison** — `GET /api/v1/states`, `GET /api/v1/states/compare`, `POST /api/v1/states/compare/custom`
4. **VA mock** — `GET /api/v1/va/mock/profile`, `GET /api/v1/va/mock/claims`, `POST /api/v1/va/lighthouse/session`
5. **Benefit search** — `GET /api/v1/benefits/search`
6. **Alabama ranking** — `GET /api/v1/alabama/benefits`, `/ranking`, `/county-offices`
7. **Health** — `GET /health`
8. **Payments (mock)** — checkout session, subscription status, webhook

## Recommended runs

### Smoke (local)

```bash
locust -f load_tests/locustfile.py --host http://localhost:8000 \
  --users 10 --spawn-rate 2 --run-time 2m --headless
```

### Staging soak

```bash
locust -f load_tests/locustfile.py --host https://staging-api.vetbuddy.example \
  --users 100 --spawn-rate 10 --run-time 30m --headless \
  --html load_tests/reports/soak-$(date +%Y%m%d).html
```

### Concurrent users ramp

```bash
for users in 25 50 100 200; do
  locust -f load_tests/locustfile.py --host http://localhost:8000 \
    --users $users --spawn-rate $((users / 5)) --run-time 5m --headless \
    --csv load_tests/reports/run_${users}
done
```

## Success criteria (placeholder targets)

| Metric | Target |
|--------|--------|
| p95 latency (read endpoints) | < 500 ms |
| p95 latency (auth + claims write) | < 1200 ms |
| Error rate | < 1% |
| Throughput | Baseline TBD per environment |

## Notes

- Tests use mock Stripe and VA modes by default.
- Register creates unique emails per virtual user to avoid collisions.
- For production-like DB load, point Locust at a Docker Compose stack with Postgres.
- Store HTML/CSV reports under `load_tests/reports/` (gitignored).
