-- =============================================================================
-- VetBuddy Canonical Migration
-- =============================================================================
-- Single idempotent migration that creates the full VetBuddy database.
-- Safe to run multiple times (IF NOT EXISTS / ON CONFLICT patterns throughout).
--
-- Usage (local):
--   psql -U vetbuddy -d vetbuddy -f database/canonical_migration.sql
--
-- Usage (Supabase SQL Editor):
--   Paste and run this file, or run individual files in order.
--
-- File order:
--   1. schema.sql      — tables, triggers, comments
--   2. indexes.sql     — performance indexes
--   3. views.sql       — dashboard views
--   4. rls_policies.sql — row-level security
--   5. seed_data.sql   — demo data (optional; skip in production)
-- =============================================================================

\set ON_ERROR_STOP on

\echo '==> VetBuddy canonical migration starting...'

-- -----------------------------------------------------------------------------
-- 1. Schema
-- -----------------------------------------------------------------------------
\echo '==> Applying schema...'
\ir schema.sql

-- -----------------------------------------------------------------------------
-- 2. Indexes
-- -----------------------------------------------------------------------------
\echo '==> Applying indexes...'
\ir indexes.sql

-- -----------------------------------------------------------------------------
-- 3. Views
-- -----------------------------------------------------------------------------
\echo '==> Applying views...'
\ir views.sql

-- -----------------------------------------------------------------------------
-- 4. RLS Policies
-- -----------------------------------------------------------------------------
\echo '==> Applying RLS policies...'
\ir rls_policies.sql

-- -----------------------------------------------------------------------------
-- 5. Seed Data (development/demo only)
-- Set VETBUDDY_SKIP_SEED=1 to skip: psql -v VETBUDDY_SKIP_SEED=1 -f ...
-- -----------------------------------------------------------------------------
\if :{?VETBUDDY_SKIP_SEED}
\echo '==> Skipping seed data (VETBUDDY_SKIP_SEED is set)'
\else
\echo '==> Applying seed data...'
\ir seed_data.sql
\endif

\echo '==> VetBuddy canonical migration complete.'
