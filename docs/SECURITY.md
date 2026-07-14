# VetBuddy Security

Security posture, controls, and honest limitations for the VetBuddy platform.

> **VetBuddy is not FedRAMP authorized.** See [FEDRAMP_READINESS.md](./FEDRAMP_READINESS.md) for gap analysis.

## Security Philosophy

VetBuddy handles sensitive veteran data including disability claim information, medical document references, and payment records. Security is implemented in layers:

1. **Transport:** TLS 1.2+ for all client-server communication
2. **Authentication:** JWT access tokens + refresh token rotation
3. **Authorization:** FastAPI RBAC (primary) + PostgreSQL RLS (defense-in-depth)
4. **Data protection:** Encryption at rest (cloud provider), bcrypt passwords, encrypted MFA secrets
5. **Audit:** Immutable `audit_logs` table for admin actions
6. **Monitoring:** Structured JSON logging; optional Sentry integration

## OWASP Top 10 Mitigations

| OWASP Risk | VetBuddy Control | Status |
|------------|------------------|--------|
| A01 Broken Access Control | FastAPI RBAC + Postgres RLS | Implemented (baseline) |
| A02 Cryptographic Failures | bcrypt passwords, TLS, encrypted MFA field | Implemented |
| A03 Injection | SQLAlchemy parameterized queries; no raw SQL from user input | Implemented |
| A04 Insecure Design | Role separation, least-privilege RLS | Implemented (baseline) |
| A05 Security Misconfiguration | Env-based secrets, CORS config, checklist tracking | Partial |
| A06 Vulnerable Components | CI dependency scanning (planned) | Pending |
| A07 Auth Failures | JWT expiry, refresh rotation, MFA schema ready | Partial (MFA UI pending) |
| A08 Data Integrity Failures | Stripe webhook signature verification | Implemented when Stripe live |
| A09 Logging Failures | `audit_logs`, `api_integration_logs`, structured logging | Implemented |
| A10 SSRF | No user-controlled URL fetching in current API | N/A (current scope) |

## Authentication

### Password Storage

Passwords are hashed with **bcrypt** (cost factor 12) via Passlib:

```python
# backend/app/core/security.py
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

Demo seed data uses password `DemoPass123!` — never deploy seed users to production.

### JWT Tokens

- Access tokens: 30-minute expiry (configurable)
- Refresh tokens: 14-day expiry with `jti` stored in `sessions` table for revocation
- Algorithm: HS256 (upgrade to RS256 with key pair for multi-service deployments)

### MFA (Multi-Factor Authentication)

The `users` table includes MFA-ready fields:

- `mfa_enabled` (boolean)
- `mfa_secret_encrypted` (AES-256-GCM encrypted TOTP secret)

MFA enforcement for admin accounts is tracked in `security_checklist` but not yet enforced in application code.

### OAuth

OAuth provider fields on `users`:

- `oauth_provider` (google, apple, va_lighthouse)
- `oauth_subject` (provider sub claim)

OAuth flows are scaffolded via environment variables; not fully wired in current release.

## Authorization

### Application Layer (Primary)

FastAPI enforces role-based access via `app/core/rbac.py`:

| Role | Access |
|------|--------|
| `veteran` | Own claims, documents, profile, benefits |
| `family_member` | Delegated access (planned) |
| `vso_resource_officer` | Assigned veterans' records |
| `american_legion_resource_officer` | Assigned veterans' records |
| `department_admin` | Organization-level admin |
| `super_admin` | Full platform admin |

### Database Layer (Defense-in-Depth)

RLS policies in `database/rls_policies.sql` enforce the same boundaries when clients connect directly to Postgres (Supabase PostgREST, Realtime, ad-hoc queries).

**Important:** FastAPI should be the primary data access path in production. RLS is a safety net, not a replacement for application-level authorization logic.

## Encryption

### In Transit

- All API endpoints must be served over HTTPS
- Database connections should use SSL (`sslmode=require` on cloud Postgres)
- Stripe and VA API calls use TLS

### At Rest

- Cloud Postgres (Supabase, RDS, Azure) provides disk encryption by default
- MFA secrets encrypted at application layer before storage
- Document files stored in private object storage buckets
- VA file numbers stored masked (`va_file_number_masked`); full numbers not stored in plaintext

### Secrets Management

- **Never commit secrets** to source control
- Use environment variables locally; cloud secrets manager in production
- `SECRET_KEY`, Stripe keys, and VA OAuth credentials via env only

## Row-Level Security Summary

| Table Group | Policy |
|-------------|--------|
| `users`, `user_profiles` | Own record + admin + assigned RO |
| `claims`, `documents` | Owner + assigned RO + admin |
| `subscriptions`, `payment_events` | Owner + admin |
| `audit_logs`, checklists | Admin only |
| Reference data (benefits, jurisdictions) | Authenticated read |

## PII and Sensitive Data

VetBuddy may process:

- Name, address, date of birth
- Military service history
- Disability claim conditions and ratings
- Medical document references (not full records in DB)
- Payment information (via Stripe — no card numbers stored locally)

### Handling Requirements

- Redact PII from application logs (checklist item: `sec_pii_redaction`)
- Soft-delete for users, claims, documents (`deleted_at`)
- Audit trail for admin access to veteran records

## API Security

- CORS restricted to configured origins (`CORS_ORIGINS` env var)
- Rate limiting configured (`rate_limit_per_minute`, default 120) — enforcement pending full middleware
- Input validation via Pydantic models
- Stripe webhook signature verification when live

## What We Do NOT Claim

- **Not FedRAMP authorized** — no ATO, no FedRAMP package
- **Not HIPAA compliant** — not a covered entity; no BAA in place
- **Not VA-certified** — not an official VA system of record
- **Not penetration tested** — no third-party pentest completed

## Security Checklist

Track progress in the `security_checklist` database table. Key items:

1. JWT secret rotation policy
2. MFA enforcement for admins
3. RLS verification (complete in schema)
4. Encryption at rest confirmation
5. TLS enforcement
6. Secrets manager migration
7. PII log redaction
8. Dependency vulnerability scanning

## Incident Response

Incident response plan is tracked in `legal_readiness_checklist` (`legal_incident_response`). Not yet documented as a standalone runbook. Recommended steps:

1. Contain: revoke compromised sessions via `sessions.revoked_at`
2. Assess: query `audit_logs` and `api_integration_logs`
3. Notify: follow state breach notification requirements
4. Remediate: rotate secrets, patch vulnerabilities
5. Document: post-incident review

## Reporting Security Issues

Report vulnerabilities to the project maintainers privately. Do not open public GitHub issues for security findings.
