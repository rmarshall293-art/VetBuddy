# VetBuddy Documentation

Technical documentation for the VetBuddy veteran support platform database, deployment, security, and integrations.

## What VetBuddy Is

VetBuddy is a veteran support platform that helps veterans track disability claims, compare state-level benefits, connect with resource officers, and manage a consumer subscription tier. The stack is:

- **Frontend:** React + Vite
- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL (Supabase-compatible)
- **Payments:** Stripe ($5.99/month consumer tier)
- **VA Integration:** Mock mode by default; Lighthouse sandbox when configured

## Documentation Index

| Document | Purpose |
|----------|---------|
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Local Docker, Supabase, AWS, Azure, Render/Fly/Railway |
| [SECURITY.md](./SECURITY.md) | OWASP controls, encryption, RLS, honest security posture |
| [NIST_800_53_MAPPING.md](./NIST_800_53_MAPPING.md) | NIST 800-53 control mapping (readiness, not certification) |
| [FEDRAMP_READINESS.md](./FEDRAMP_READINESS.md) | FedRAMP gap analysis — **NOT certified** |
| [VA_API_INTEGRATION.md](./VA_API_INTEGRATION.md) | Mock VA integration and Lighthouse registration |
| [PAYMENT_SETUP.md](./PAYMENT_SETUP.md) | Stripe $5.99/month subscription setup |
| [SCHEMA_RECONCILIATION.md](./SCHEMA_RECONCILIATION.md) | How v4 and claims schemas were unified |
| [LOAD_TESTING.md](./LOAD_TESTING.md) | Running Locust load tests |
| [LEGAL_CONTRACTING_READINESS.md](./LEGAL_CONTRACTING_READINESS.md) | SDVOSB, SAM.gov, UEI, CAGE checklist |

## Database Package

All SQL lives under `/database/`:

| File | Description |
|------|-------------|
| `schema.sql` | Canonical table definitions (30 tables) |
| `views.sql` | Dashboard views |
| `indexes.sql` | Performance indexes |
| `rls_policies.sql` | Row-level security policies |
| `canonical_migration.sql` | Single idempotent migration runner |
| `seed_data.sql` | Demo roles, users, jurisdictions, checklists |

Apply with:

```bash
psql $DATABASE_URL -f database/canonical_migration.sql
```

Skip seed data in production:

```bash
psql $DATABASE_URL -v VETBUDDY_SKIP_SEED=1 -f database/canonical_migration.sql
```

## What Works Today (Production-Ready Baseline)

- PostgreSQL schema with UUID PKs, foreign keys, soft-delete, MFA/OAuth fields
- RBAC role model (veteran, resource officer, department admin, super admin)
- Row-level security policies for defense-in-depth
- FastAPI JWT auth with bcrypt password hashing
- Stripe integration scaffold (mock mode default)
- VA Lighthouse integration scaffold (mock mode default)
- Security and legal readiness checklists in the database
- Alabama ranking metrics table for state comparison features

## What Is Mocked or Incomplete

| Area | Status |
|------|--------|
| VA Lighthouse API | **Mock mode** — returns fixture data, no live VA claims sync |
| Stripe payments | **Mock mode** — test keys required for real charges |
| OAuth (Google/Apple) | Placeholder env vars only |
| MFA (TOTP) | Schema fields exist; UI/enforcement not complete |
| FedRAMP | **Not certified** — see FEDRAMP_READINESS.md |
| Live VA claim submission | **Not implemented** — guided forms only |
| Email notifications | Schema only; no SMTP/SES wired |
| Document storage | `storage_path` column; bucket config required |
| Full frontend | Baseline scaffold; not all views wired to API |

## Demo Accounts

After running `seed_data.sql`:

| Email | Password | Role |
|-------|----------|------|
| `demo.veteran@vetbuddy.local` | `DemoPass123!` | veteran |
| `demo.admin@vetbuddy.local` | `DemoPass123!` | super_admin |
| `demo.officer@vetbuddy.local` | `DemoPass123!` | vso_resource_officer |

**Do not use these credentials in production.** Rotate or omit seed data entirely.

## Authorization Model

Authorization is enforced at two layers:

1. **Application layer (primary):** FastAPI validates JWTs and enforces RBAC via `app/core/rbac.py`.
2. **Database layer (defense-in-depth):** RLS policies in `database/rls_policies.sql` restrict direct Postgres/Supabase access.

Always route production traffic through the FastAPI API. RLS protects against accidental direct database access.

## Honest Limitations

- VetBuddy is **not** affiliated with the Department of Veterans Affairs.
- VetBuddy is **not** FedRAMP authorized.
- VetBuddy does **not** have live VA claim submission capability in the current release.
- Benefits data, Alabama ranking metrics, and tax rules in seed data are **demo values** — verify against official sources before production use.
