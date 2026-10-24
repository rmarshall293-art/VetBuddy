# ADR 0001: Source of truth, data store and migration approach

Status: Accepted, 20 Oct 2026

## Context
The repository held only deployment config. The Base44 prototype source and data are not available. The project rules name GitHub as the code source of truth and PostgreSQL/Supabase as the canonical data store.

## Decision
- **Code:** this repository. One modular monolith: `backend/` (FastAPI) and `frontend/` (Vite).
- **Data:** PostgreSQL 16, schema `vb`. Any Postgres works (Supabase included); no Supabase-specific feature is used yet, so the store can be chosen later (Master Record conflict rows 11/13 stay open).
- **Migrations:** plain SQL files applied in order by `python -m app.migrate`, each recorded with a checksum; editing an applied file is an error. Chosen over Alembic because the security model (roles, forced RLS, definer functions, CHECKs) is SQL-first and must be readable in review. Revisit if ORM models appear.
- **Access model:** the API connects as a LOGIN role in `vetbuddy_app` (no ownership, no BYPASSRLS). Tenant/user context is set `LOCAL` per transaction; every table forces RLS; definer functions are owned by a separate NOLOGIN role whose policies are written per table.
- **Base44:** when an export arrives, it enters as immutable staging and maps through `docs/MIGRATION_MAP.md`; nothing here invents its records.

## Consequences
Isolation is enforced by the database and tested through it, not by query discipline. Service keys that bypass RLS (e.g. the legacy `SUPABASE_SERVICE_ROLE_KEY` in the old `render.yaml`) are not used for user requests.
