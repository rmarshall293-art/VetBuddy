# ADR 0003: A separate `ref` schema for V0 reference data

**Status:** Accepted (slice 02), 2026-10-20

**Context.** Research reports, Sentinel and the module specs supply public reference data: directories, rates, state summaries, duty authorities and statistics. The skeleton's `resource`, `installation`, `source_record` and `institution` tables are tenant-scoped with forced RLS. Global data placed there would be copied per tenant or leak across tenants. None of the new data is about a user.

**Decision.**
- Add schema `ref` (migration 0011): no tenant, no person, no RLS, and a migration guard that fails if a person or tenant column appears.
- JSON in `data/reference/` is the source of truth. `scripts/build_reference.py` validates it and generates a committed seed that refreshes `ref` idempotently. The app role has SELECT only.
- Every row carries a `ref.record_status` and named sources. Leads and statistics can never be VERIFIED. Rates and timeline windows can be verified only with a named reviewer and date.
- Eligibility stays in `public.benefit` / `eligibility_rule` and behind G1. Nothing in `ref` may produce an outcome.

**Consequences.** Tenant tables keep organization-curated additions; `ref` holds the shared public layer. When a rule is verified, its rule pack cites the `ref` source it came from rather than copying it. Alembic, if adopted later, treats 0011 like the other SQL files.
