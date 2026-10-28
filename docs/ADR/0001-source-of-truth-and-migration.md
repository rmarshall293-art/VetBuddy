# ADR 0001 — Source of truth and migration approach

**Status:** Accepted (slice 01), 2026-10-20

**Context.** The intended inputs were the GitHub repo, the Base44 export, skeleton v1, and the planning docs. Only skeleton v1 and the docs were available to this session.

**Decision.**
- PostgreSQL is the canonical store. SQL files in `database/migrations/` are the schema of record and apply in order through `scripts/migrate.py`, which records a sha256 per file and refuses edited history (fix forward only).
- 0001–0008 are preserved unmodified. Corrections land in new files (0009+).
- The API connects as `vb_app`, a non-owner role in `vetbuddy_app`. The owner DSN is used only for migrations and test fixtures.
- Base44 is a migration source. When its export arrives, ingest it into raw/staging tables and map it route by route (master spec §11). Never import it straight into domain tables.

**Consequences.** Alembic stays in the plan but isn't used yet. If adopted, the SQL files become its baseline revision.
