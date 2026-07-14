# VetBuddy Deployment Guide

This guide covers deploying VetBuddy across local development, managed Postgres (Supabase), and common cloud platforms.

## Prerequisites

- PostgreSQL 14+ (or Supabase project)
- Python 3.11+ (backend)
- Node.js 18+ (frontend)
- `psql` client for running migrations

## Database Migration

Apply the canonical migration before starting the API:

```bash
# Full migration with demo seed data
psql "$DATABASE_URL" -f database/canonical_migration.sql

# Production: skip seed data
psql "$DATABASE_URL" -v VETBUDDY_SKIP_SEED=1 -f database/canonical_migration.sql
```

Or run files individually in order: `schema.sql` → `indexes.sql` → `views.sql` → `rls_policies.sql` → `seed_data.sql`.

---

## Local Development (Docker)

### Option A: Docker Compose (recommended)

Create `docker-compose.yml` at the project root:

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: vetbuddy
      POSTGRES_PASSWORD: vetbuddy
      POSTGRES_DB: vetbuddy
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  api:
    build: ./backend
    environment:
      DATABASE_URL: postgresql+psycopg2://vetbuddy:vetbuddy@db:5432/vetbuddy
      SECRET_KEY: dev-only-change-me
      VA_MOCK_MODE: "true"
      STRIPE_MOCK_MODE: "true"
    ports:
      - "8000:8000"
    depends_on:
      - db

volumes:
  pgdata:
```

Start and migrate:

```bash
docker compose up -d db
sleep 3
docker compose exec db psql -U vetbuddy -d vetbuddy -f /path/to/canonical_migration.sql
docker compose up --build
```

### Option B: Local Postgres

```bash
createdb vetbuddy
psql vetbuddy -f database/canonical_migration.sql
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend env (`.env`):

```env
DATABASE_URL=postgresql+psycopg2://vetbuddy:vetbuddy@localhost:5432/vetbuddy
SECRET_KEY=<openssl rand -hex 32>
VA_MOCK_MODE=true
STRIPE_MOCK_MODE=true
CORS_ORIGINS=http://localhost:5173
```

---

## Supabase Postgres

Supabase is the recommended managed Postgres for VetBuddy.

### Steps

1. Create a project at [supabase.com](https://supabase.com).
2. Open **SQL Editor** and paste contents of `database/canonical_migration.sql`, or upload individual SQL files in order.
3. For production, run with seed data skipped (set `VETBUDDY_SKIP_SEED=1` via psql locally against the Supabase connection string).
4. Copy credentials to `.env`:
   ```env
   DATABASE_URL=postgresql+psycopg2://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
   SUPABASE_URL=https://[ref].supabase.co
   SUPABASE_ANON_KEY=eyJ...
   SUPABASE_SERVICE_ROLE_KEY=eyJ...
   ```
5. Enable RLS — policies are applied by `rls_policies.sql`.
6. Create storage buckets: `documents` (private), `avatars` (public read).

### Supabase Auth vs FastAPI Auth

VetBuddy uses FastAPI-issued JWTs as the primary auth mechanism. Supabase Auth can coexist but is not required. If using Supabase client libraries with RLS, ensure JWTs include `sub` and `roles` claims matching `rls_policies.sql` helper functions.

---

## AWS

### Architecture

```
Route 53 → CloudFront (frontend) + ALB (API) → ECS Fargate / EC2
                                              → RDS PostgreSQL
                                              → S3 (documents)
                                              → Secrets Manager
```

### RDS Setup

1. Create RDS PostgreSQL 16 instance (Multi-AZ for production).
2. Enable encryption at rest (default).
3. Security group: allow port 5432 from API subnet only.
4. Run migration via bastion or CI:
   ```bash
   psql "$RDS_DATABASE_URL" -v VETBUDDY_SKIP_SEED=1 -f database/canonical_migration.sql
   ```
5. Store `DATABASE_URL`, `SECRET_KEY`, Stripe keys in AWS Secrets Manager.

### API Deployment (ECS)

- Container image from `backend/Dockerfile`
- Environment from Secrets Manager
- Health check: `GET /health`
- Auto-scaling on CPU/request count

### Frontend

- Build: `cd frontend && npm run build`
- Deploy `dist/` to S3 + CloudFront

---

## Azure

### Architecture

```
Azure Front Door → Static Web Apps (frontend)
                → App Service / Container Apps (API)
                → Azure Database for PostgreSQL Flexible Server
                → Blob Storage (documents)
                → Key Vault
```

### PostgreSQL

1. Create Azure Database for PostgreSQL Flexible Server.
2. Enable SSL (`sslmode=require` in connection string).
3. Run canonical migration from Azure Cloud Shell or CI pipeline.
4. Store secrets in Azure Key Vault; reference from App Service settings.

---

## Render

`backend/render.yaml` provides a starter blueprint:

```yaml
services:
  - type: web
    name: vetbuddy-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: vetbuddy-db
          property: connectionString
databases:
  - name: vetbuddy-db
    plan: starter
```

Post-deploy: run migration via Render shell or one-off job.

---

## Fly.io

```bash
fly launch --name vetbuddy-api
fly postgres create --name vetbuddy-db
fly postgres attach vetbuddy-db
fly secrets set SECRET_KEY=... STRIPE_SECRET_KEY=... VA_MOCK_MODE=true
fly deploy
```

Run migration:

```bash
fly ssh console -C "psql \$DATABASE_URL -v VETBUDDY_SKIP_SEED=1 -f /app/database/canonical_migration.sql"
```

---

## Railway

1. Create project with PostgreSQL plugin.
2. Deploy backend from GitHub repo.
3. Set `DATABASE_URL` from Railway Postgres variables.
4. Use Railway CLI or deploy hook to run migration:
   ```bash
   railway run psql $DATABASE_URL -v VETBUDDY_SKIP_SEED=1 -f database/canonical_migration.sql
   ```

---

## Vercel (Frontend Only)

```bash
cd frontend
vercel --prod
```

Set environment variables in Vercel dashboard:

```env
VITE_API_URL=https://api.yourdomain.com/api/v1
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

---

## Production Checklist

- [ ] Run migration with `VETBUDDY_SKIP_SEED=1`
- [ ] Set strong `SECRET_KEY` (32+ byte random hex)
- [ ] Set `VA_MOCK_MODE=false` only after Lighthouse sandbox approval
- [ ] Set `STRIPE_MOCK_MODE=false` with live Stripe keys
- [ ] Enable HTTPS everywhere
- [ ] Restrict CORS to production frontend origin
- [ ] Enable database backups (daily minimum)
- [ ] Configure error tracking (Sentry DSN)
- [ ] Review `security_checklist` and `legal_readiness_checklist` tables

## Environment Variable Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | SQLAlchemy Postgres connection string |
| `SECRET_KEY` | Yes | JWT signing key |
| `STRIPE_SECRET_KEY` | Prod | Stripe API secret key |
| `STRIPE_WEBHOOK_SECRET` | Prod | Stripe webhook signing secret |
| `STRIPE_PRICE_ID_CONSUMER` | Prod | Price ID for $5.99/month tier |
| `VA_CLIENT_ID` | Optional | VA Lighthouse OAuth client ID |
| `VA_CLIENT_SECRET` | Optional | VA Lighthouse OAuth secret |
| `VA_MOCK_MODE` | Yes | `true` until Lighthouse approved |
| `STRIPE_MOCK_MODE` | Yes | `true` until Stripe configured |
| `SENTRY_DSN` | Optional | Error tracking |
