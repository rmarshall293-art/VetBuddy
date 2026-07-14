# VetBuddy

Secure, scalable veteran benefits, claims-analysis, state comparison, and resource-navigation platform — Alabama pilot first, designed for all **56 jurisdictions**.

**Stack:** Next.js 15 + React + TypeScript + Tailwind · FastAPI (Python 3.12) · PostgreSQL · Alembic · Stripe (mock-ready) · VA Lighthouse (mock-ready) · Docker Compose · GitHub Actions

> VetBuddy is **not** affiliated with the Department of Veterans Affairs, **not** FedRAMP certified, and does **not** provide legal advice or accredited VA representation. VA and Stripe integrations run in **mock mode** unless live credentials are configured.

## Quick Start (Docker Compose)

```bash
git clone https://github.com/rmarshall293-art/VetBuddy.git
cd VetBuddy
cp .env.example .env
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| Health | http://localhost:8000/health |

## Local Development (without Docker)

```bash
# Database
createdb vetbuddy
psql vetbuddy -f database/canonical_migration.sql

# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

### Demo accounts (after SQL seed)

| Email | Password | Role |
|-------|----------|------|
| `demo.veteran@vetbuddy.local` | `DemoPass123!` | veteran |
| `demo.admin@vetbuddy.local` | `DemoPass123!` | super_admin |
| `demo.officer@vetbuddy.local` | `DemoPass123!` | vso_resource_officer |

## Project Structure

```text
vetbuddy/
  backend/           # FastAPI app, Alembic, Pytest
  frontend/          # Next.js App Router UI
  database/          # Canonical schema, RLS, views, seed SQL
  data/              # 56 jurisdictions + VA rates + Alabama JSON
  load_tests/        # Locust scenarios + report template
  docs/              # Deployment, security, VA, payments, legal
  .github/workflows/ # CI (lint, test, docker, migrations)
  docker-compose.yml
  .env.example
```

## What Is Production-Ready

1. Canonical PostgreSQL schema (30 tables, 3 views, RLS policies, indexes)
2. FastAPI auth (register/login/refresh/logout/account delete) with JWT + refresh rotation
3. Role-based access (veteran, family member, VSO/AL resource officer, department admin, super admin)
4. Claims analysis CRUD + evidence scoring + ITF / forms guidance
5. 56-jurisdiction state comparison API + UI
6. Alabama benefits, county offices, ranking, and resource-officer training module
7. Stripe checkout/webhook/subscription status in **mock mode** ($5.99/mo consumer tier)
8. VA Lighthouse adapter with **mock** profile/claims/session
9. Admin security + legal readiness checklists
10. Health endpoint, structured logging, audit/API integration logs
11. Pytest suite (32 tests), Locust load-test package, GitHub Actions CI
12. Docker Compose local stack + multi-cloud deployment guide

## What Still Requires Live Credentials / External Work

| Area | Status |
|------|--------|
| VA Lighthouse / FHIR | Mock only until `VA_CLIENT_ID` / `VA_CLIENT_SECRET` + developer.va.gov registration |
| Stripe production billing | Mock only until Stripe keys + price ID + webhook secret |
| Google / Apple OAuth | Placeholders only |
| MFA enforcement | Account model ready; full MFA UX/enforcement still to wire |
| FedRAMP / third-party audit | **Not certified** — readiness docs and checklists only |
| SDVOSB / SAM.gov / UEI / CAGE | Tracked in admin legal checklist — not completed by this repo |
| Document object storage | Schema ready; configure S3/Supabase Storage separately |
| Redis | Optional; app runs without it |

## Tests

```bash
cd backend && pytest -q
cd frontend && npm run lint && npm run build
# Load tests (API must be running)
cd load_tests && locust -f locustfile.py --host http://localhost:8000
```

## Documentation

| Doc | Purpose |
|-----|---------|
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Local, Supabase, AWS, Azure, Render/Fly/Railway |
| [docs/SECURITY.md](docs/SECURITY.md) | OWASP, encryption, RLS — no certification claims |
| [docs/NIST_800_53_MAPPING.md](docs/NIST_800_53_MAPPING.md) | Control mapping (readiness) |
| [docs/FEDRAMP_READINESS.md](docs/FEDRAMP_READINESS.md) | Explicitly **not certified** |
| [docs/VA_API_INTEGRATION.md](docs/VA_API_INTEGRATION.md) | Mock vs live Lighthouse steps |
| [docs/PAYMENT_SETUP.md](docs/PAYMENT_SETUP.md) | Stripe $5.99 setup |
| [docs/SCHEMA_RECONCILIATION.md](docs/SCHEMA_RECONCILIATION.md) | Unified schema notes |
| [docs/LOAD_TESTING.md](docs/LOAD_TESTING.md) | Locust guide |
| [docs/LEGAL_CONTRACTING_READINESS.md](docs/LEGAL_CONTRACTING_READINESS.md) | Business readiness checklist |

## Disclaimer

VetBuddy provides **educational guidance and organization support only**. It is not legal advice and does not confer VA accreditation. Veterans should consult an accredited VSO, attorney, or claims agent for representation.

## License

Private / Internal Use
