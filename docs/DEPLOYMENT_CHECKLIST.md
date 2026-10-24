# VetBuddy Deployment Checklist

Development → staging (synthetic data) → limited pilot → approved production. Nothing below is done by automation; each box needs a named person.

## Database (PostgreSQL 16 / Supabase)
- [ ] Create the database; keep the owner credential in the host's secret store only
- [ ] Run `python -m app.migrate` with the owner `DATABASE_URL` (pre-deploy step) and `APP_DB_LOGIN`/`APP_DB_PASSWORD` set
- [ ] Confirm `SELECT * FROM vb.rls_gaps()` returns no rows
- [ ] Confirm the API login is NOT a superuser, has no BYPASSRLS, owns nothing
- [ ] Never give the API a service key that bypasses RLS

## Backend (FastAPI, `backend/render.yaml`)
- [ ] Set `APP_DATABASE_URL` (least-privilege login), `CORS_ORIGINS`, `ENVIRONMENT`
- [ ] `AUTH_MODE=off` until a real identity provider replaces the dev stand-in (G17); the app refuses `dev` in staging/production
- [ ] `/api/v1/health/ready` reports `database: ok`

## Frontend (Vite, `frontend/vercel.json`)
- [ ] Guest-only (Launch 0): build without `VITE_API_URL`
- [ ] With saved plans: set `VITE_API_URL` to the API origin (also added to the page CSP at build)

## Before any real user
- [ ] G1: a named reviewer verifies rules before any benefit answer is shown
- [ ] G17: real sign-in; G21/G23: model provider contract before any AI feature
- [ ] Counsel review of governance §2, §5, §7 language, privacy policy, terms
- [ ] Re-verify crisis line numbers against the source registry
- [ ] Full git-history secret scan; repository visibility decision recorded
- [ ] Backups + restore test, monitoring, incident runbook
