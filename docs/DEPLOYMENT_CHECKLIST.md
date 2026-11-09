# VetBuddy Deployment Checklist

Development → staging (synthetic data) → limited pilot → approved production. Nothing below is automated; each box needs a named person.

## Launch 0: static guest app (`vercel.json`)
- [ ] `python scripts/build_web.py` and commit `dist/` (CI fails if it is stale)
- [ ] Vercel serves `dist/` only; `/` rewrites to `dist/vetbuddy.html`. No build step, no backend; the page stores and sends nothing
- [ ] Re-verify the 6 crisis numbers in `config/crisis_floor.yaml` against their official pages

## API (`render.yaml`)
- [ ] As the database **owner** (`DATABASE_ADMIN_URL`), once, from a trusted machine: `python scripts/migrate.py`, then load `database/seeds/0011_reference.sql` and `database/seeds/0014_benefit_vault_seed.sql` (see `render.yaml`)
- [ ] Create the non-owner login in `vetbuddy_app` (as `scripts/dev_db.sh` does) and set it as `DATABASE_URL` in the host's secret store
- [ ] `VB_AUTH_MODE=disabled` until a real identity provider replaces the dev mock (G17); `VB_MODE_C_ENABLED=false`
- [ ] `/readyz` answers 200 (it stays 503 until the crisis floor verifies)

## Capacity (measured 2026-11-09, local 4-CPU machine shared with Postgres and the load generator)
- Measured: 2,000 mixed requests at 100 concurrent, 0 errors. 1 worker: 88 req/s. 4 workers: 236 req/s, p50 314 ms. Per route, single worker: rating code 6.6 ms, jurisdictions 4.9 ms, vault search 4.8 ms, VA estimate 1.4 ms, vault match 26.7 ms (it evaluates all 1,362 rules)
- [ ] The API holds no state between requests: scale by adding instances behind the load balancer; set `WEB_CONCURRENCY` to about one worker per CPU
- [ ] Put a connection pooler in front of Postgres (PgBouncer, or the Supabase pooler) in **transaction** mode. Each request opens its own connection, and tenant isolation uses `set_config(..., true)`, which lasts one transaction, so transaction pooling is safe
- [ ] Rate-limit at the edge (CDN or load balancer); the API has no per-client limit of its own
- [ ] Serve the guest app (`dist/`) from a CDN: it needs no server, so most visitors never reach the API
- [ ] Repeat the load test against staging with production-sized instances before launch

## Before any real user
- [ ] G1: a named reviewer verifies rules before any benefit match is shown
- [ ] G17 real sign-in; G21/G23 model-provider contract before any AI feature
- [ ] Legal operator named by the owner and counsel (policy drafts carry `[OPERATOR NAME]`)
- [ ] Counsel review of governance §2, §5, §7 language and both policy drafts (`docs/POLICY_CLAIMS_REGISTER.md`)
- [ ] Full git-history secret scan; repository visibility decision recorded (the repo is public)
- [ ] Backups + restore test, monitoring, incident runbook
