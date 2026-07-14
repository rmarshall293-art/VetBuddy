# VetBuddy Load Test Report

**Run name:** `{RUN_NAME}`  
**Date:** `{DATE}`  
**Environment:** `{ENVIRONMENT}`  
**Host:** `{HOST}`  
**Tool:** Locust `{LOCUST_VERSION}`

## Configuration

| Parameter | Value |
|-----------|-------|
| Concurrent users | `{USERS}` |
| Spawn rate | `{SPAWN_RATE}` |
| Duration | `{DURATION}` |
| Scenarios | VetBuddyUser, AnonymousBrowseUser, ConcurrentCheckoutUser |

## Summary

| Metric | Result | Target | Pass |
|--------|--------|--------|------|
| Total requests | `{TOTAL_REQUESTS}` | — | — |
| Failures | `{FAILURES}` | < 1% | `{PASS_FAIL_RATE}` |
| Failure rate | `{FAILURE_RATE}%` | < 1% | `{PASS_FAIL_RATE}` |
| RPS (avg) | `{RPS}` | Baseline TBD | — |
| p50 latency | `{P50} ms` | — | — |
| p95 latency | `{P95} ms` | < 500–1200 ms | `{PASS_P95}` |
| p99 latency | `{P99} ms` | — | — |

## Endpoint breakdown

| Name | # reqs | # fails | Median (ms) | p95 (ms) | Avg (ms) |
|------|--------|---------|-------------|----------|----------|
| health | | | | | |
| auth/register | | | | | |
| auth/login | | | | | |
| claims/list | | | | | |
| claims/create | | | | | |
| states/compare | | | | | |
| va/mock/profile | | | | | |
| alabama/ranking | | | | | |
| payments/create-checkout-session | | | | | |

## Observations

- 
- 

## Issues / regressions

1. 
2. 

## Recommendations

1. 
2. 

## Artifacts

- HTML report: `load_tests/reports/{ARTIFACT_HTML}`
- CSV stats: `load_tests/reports/{ARTIFACT_CSV}_stats.csv`
- Locust log: `{LOG_PATH}`

## Sign-off

| Role | Name | Date |
|------|------|------|
| Engineer | | |
| Reviewer | | |
