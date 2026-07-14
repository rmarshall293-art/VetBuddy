# Schema Reconciliation

How the VetBuddy v4 platform schema and the claims-focused schema were unified into a single canonical database design.

## Background

VetBuddy evolved through multiple schema iterations:

1. **v4 Platform Schema** — Broad platform tables for users, organizations, benefits, jurisdictions, subscriptions, and admin tooling.
2. **Claims Schema** — Focused tables for disability claims, conditions, evidence, documents, intent-to-file, and VA forms.
3. **State Comparison Schema** — Jurisdiction benefits, tax rules, Alabama ranking metrics, and saved comparisons.

These were developed in parallel branches and had overlapping tables with inconsistent naming, missing foreign keys, and duplicate user/profile definitions.

## Reconciliation Goals

1. **Single canonical schema** — One `database/schema.sql` as source of truth
2. **No duplicate tables** — Merge overlapping definitions
3. **Consistent UUID PKs** — All tables use `gen_random_uuid()`
4. **Complete FK graph** — Every relationship enforced at database level
5. **Soft-delete consistency** — `deleted_at` on users, claims, documents, organizations
6. **RBAC alignment** — Roles match `backend/app/core/rbac.py` enum values
7. **Supabase compatibility** — RLS policies, `auth_user_id()` helpers

## Merge Decisions

### Users and Identity

| v4 Schema | Claims Schema | Unified Decision |
|-----------|---------------|------------------|
| `users` with `stripe_customer_id` | `users` with `va_file_number` | Single `users` table; VA file number moved to `user_profiles.va_file_number_masked` |
| `profiles` table | `veteran_profiles` table | Merged into `user_profiles` (1:1 with users) |
| No MFA fields | No MFA fields | Added `mfa_enabled`, `mfa_secret_encrypted` |
| No OAuth fields | No OAuth fields | Added `oauth_provider`, `oauth_subject` |

### Claims Domain

| v4 Schema | Claims Schema | Unified Decision |
|-----------|---------------|------------------|
| No claims tables | `claims`, `conditions`, `evidence` | Adopted claims schema; added `metadata JSONB` |
| `documents` with `s3_key` | `documents` with `storage_path` | Unified as `storage_path` (provider-agnostic) |
| Missing ITF table | `intent_to_file` | Renamed to `intent_to_file_records`; FK from claims |
| No VA forms catalog | `va_forms` | Adopted as-is |

### Benefits and Jurisdictions

| v4 Schema | Claims Schema | Unified Decision |
|-----------|---------------|------------------|
| `states` table | `jurisdictions` table | Unified as `jurisdictions` (states + territories) |
| `state_benefits` | `jurisdiction_benefits` | Unified as `jurisdiction_benefits` with amount ranges in cents |
| `tax_exemptions` | `state_tax_rules` | Unified as `state_tax_rules` with JSONB `rules` for flexibility |
| No ranking metrics | `alabama_metrics` | Unified as `alabama_ranking_metrics` |

### Admin and Operations

| v4 Schema | Claims Schema | Unified Decision |
|-----------|---------------|------------------|
| `audit_log` (singular) | No audit table | Unified as `audit_logs` (plural, consistent naming) |
| `api_logs` | No API logs | Unified as `api_integration_logs` |
| `security_items` | No checklist | Unified as `security_checklist` |
| No legal checklist | No legal checklist | Added `legal_readiness_checklist` |
| No load test table | No load test table | Added `load_test_results` |

### Billing

| v4 Schema | Claims Schema | Unified Decision |
|-----------|---------------|------------------|
| `subscriptions` with Stripe fields | No billing | Adopted v4; `amount_cents` default 599 |
| `stripe_events` | No events | Renamed to `payment_events` |
| `stripe_customer_id` on users | N/A | Kept on both `users` and `subscriptions` |

### Resource Officers

| v4 Schema | Claims Schema | Unified Decision |
|-----------|---------------|------------------|
| `officer_assignments` | `caseload` | Unified as `resource_officer_assignments` |
| `organizations` | No orgs | Adopted v4 with UEI/CAGE fields for contracting |

## Naming Conventions Applied

| Rule | Example |
|------|---------|
| Plural table names | `audit_logs`, not `audit_log` |
| `_id` suffix for foreign keys | `user_id`, `claim_id` |
| `_at` suffix for timestamps | `created_at`, `deleted_at` |
| Amounts in cents (integer) | `amount_cents`, `monthly_amount_cents` |
| Status as varchar (not enum) | Allows adding values without migration |
| JSONB for extensible metadata | `metadata`, `rules`, `comparison_data` |

## Tables in Canonical Schema (30)

```
users                          user_profiles
roles                          user_roles
sessions                       organizations
claims                         claim_conditions
claim_evidence                 documents
va_forms                       intent_to_file_records
benefits                       jurisdictions
jurisdiction_benefits          state_tax_rules
va_rate_tables                 cola_tables
facilities                     resource_officer_assignments
audit_logs                     api_integration_logs
subscriptions                  payment_events
security_checklist             legal_readiness_checklist
load_test_results              notifications
saved_state_comparisons        alabama_ranking_metrics
```

## Views Reconciled

| View | Sources |
|------|---------|
| `claims_dashboard_view` | claims + conditions + evidence + documents |
| `user_benefits_dashboard_view` | users + profiles + jurisdictions + benefits + subscriptions |
| `state_comparison_view` | jurisdictions + benefits + tax rules + alabama metrics |

## Migration Path

For existing deployments with old schemas:

1. **Backup** the database
2. Run `canonical_migration.sql` on a fresh database (recommended for dev)
3. For production with existing data:
   - Write a one-time data migration script mapping old column names
   - Key mappings:
     - `profiles` → `user_profiles`
     - `states` → `jurisdictions`
     - `state_benefits` → `jurisdiction_benefits`
     - `s3_key` → `storage_path`
     - `audit_log` → `audit_logs`
     - `stripe_events` → `payment_events`
4. Verify FK integrity after migration
5. Apply RLS policies
6. Run application integration tests

## SQLAlchemy Model Alignment

The FastAPI backend should define SQLAlchemy models matching this schema. Key alignments needed in `app/db/models.py` (when created):

- `User` → `users` with relationships to `UserProfile`, `UserRole`, `Claim`
- `Claim` → `claims` with `ClaimCondition`, `ClaimEvidence`, `Document`
- `Role` enum values must match `roles.name` seed data exactly
- `Subscription` → `subscriptions` with Stripe field names

## Validation Queries

After migration, verify reconciliation:

```sql
-- All tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- FK integrity
SELECT conname, conrelid::regclass, confrelid::regclass
FROM pg_constraint
WHERE contype = 'f'
ORDER BY conrelid::regclass::text;

-- Role seed matches RBAC enum
SELECT name FROM roles ORDER BY name;

-- Views return data
SELECT COUNT(*) FROM claims_dashboard_view;
SELECT COUNT(*) FROM state_comparison_view;
```

## Future Schema Changes

All schema changes should:

1. Update `database/schema.sql` (canonical)
2. Add a dated migration file (e.g., `database/migrations/20250714_add_foo.sql`)
3. Update `canonical_migration.sql` if adding to base schema
4. Update this document with reconciliation notes
5. Update SQLAlchemy models and API schemas

Do not create parallel schema files in `supabase/` or other directories — `database/` is the single source of truth.
