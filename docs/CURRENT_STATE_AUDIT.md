# Current State Audit

As of 20 Oct 2026, branch `claude/dazzling-clarke-59kw1x`. Observed facts first, then what this change added.

## 1. Baseline observed before this change (P0)

| Item | Observed |
|---|---|
| Remote / branch / HEAD | `rmarshall293-art/VetBuddy`, `c3d0f9b` ("Add Render backend deployment config") |
| Visibility | **Public** repository (checked via GitHub API). Treat everything committed as published. |
| Files | `.github/workflows/ci.yml`, `.gitignore`, `.gitkeep`, `README.md`, `backend/render.yaml`, `frontend/vercel.json`, `docs/DEPLOYMENT_CHECKLIST.md` |
| Application code | None. No `backend/app`, no frontend app, no package manifests, migrations, tests, agents or source registries. |
| Classification | GitHub configuration skeleton. Not a Base44 export, not a combined repo. |
| README claims | "Production-ready baseline" — **not supported by anything in the tree** (now corrected). References `docker-compose`, `.env.example` files and `supabase/schema.sql` that did not exist. |
| CI | Referenced `backend/requirements.txt`, `frontend/package-lock.json` and `pytest`/`npm run build`, none of which existed. CI could not have passed. |
| `render.yaml` | Started `uvicorn app.main:app` (no such module) and declared `SUPABASE_SERVICE_ROLE_KEY` (legacy name; a service key would bypass RLS if used for user requests). |
| Secrets in git | None found in the 7 tracked files. Full-history scan not run (`SOURCE_NOT_AVAILABLE`: no secret scanner installed in this session). |

## 2. Sources available to this execution

| Source | Status |
|---|---|
| Master Prompt v5 (HTML) | Available → `docs/VETBUDDY_MASTER_SPEC.md` |
| CLAUDE.md (project rules) | Available → `/CLAUDE.md` |
| Agent Governance Rules (PDF, 13 pp) | Available → summarized with enforcement status in `docs/GAP_MATRIX.md` |
| Build Reference (HTML) | Available. Describes an earlier build (47 tests, 10 migrations). **That code was not in this repo**; this change rebuilds the equivalent slice and re-proves it. |
| Guest app v2–v4, Integrated Record (21 Oct) | Integrated; see `docs/INTEGRATION_LEDGER.md` |
| `vetbuddy.html` guest app | Available. Its browser kernel and data were ported into `frontend/` unchanged (generated data verified byte-for-byte equal after re-generation from Python). |
| Base44 application export (source, entities, data) | `SOURCE_NOT_AVAILABLE` |
| Earlier code archives, 737-code VA rating dataset | `SOURCE_NOT_AVAILABLE` |

## 3. What exists now

Labels: `IMPLEMENTED_VERIFIED` = code + passing automated test; `MOCK`; `PARTIAL`; `NOT_PRESENT`.

| Capability | Label | Evidence |
|---|---|---|
| FastAPI app, `/api/v1`, one error contract with trace ids | IMPLEMENTED_VERIFIED | `backend/app/main.py`, `api/errors.py`; `test_api_guest.py` |
| Health live/ready (truthful about DB, sign-in, model gateway) | IMPLEMENTED_VERIFIED | `test_health_without_database` |
| PostgreSQL schema, forward-only checksummed migrations (6) | IMPLEMENTED_VERIFIED | `backend/migrations/`, `app/migrate.py`; runs on PostgreSQL 16 |
| Non-owner app role; FORCE RLS on every table; fail-closed context | IMPLEMENTED_VERIFIED | `test_isolation.py` (incl. mutation test: disabling RLS makes it leak) |
| RLS gap guard (C-06) | IMPLEMENTED_VERIFIED | migration 0006 + `test_no_rls_gaps` |
| Consent: purpose allowlist, 9 foreclosed purposes refused by CHECK even for owner, immediate revocation, revoke-and-delete | IMPLEMENTED_VERIFIED | `test_consent_and_work.py` |
| Privacy Mode A (guest, nothing stored) | IMPLEMENTED_VERIFIED | table counts before/after; browser test: no requests, no storage |
| Privacy Mode B (private, consented) | IMPLEMENTED_VERIFIED | API + full-stack browser test |
| Privacy Mode C (managed case) | NOT_PRESENT (unreachable by DB CHECK) | `test_mode_c_unreachable` |
| Deterministic Mission Router → Master Mission, Master Case, lanes, tasks, Mission Brief, next action, readiness by dimension | IMPLEMENTED_VERIFIED | `test_router.py` (24 boundary cases, determinism), `test_consent_and_work.py` |
| Task status with optimistic concurrency | IMPLEMENTED_VERIFIED | `test_task_status_with_optimistic_concurrency` |
| Combined rating, 38 CFR 4.25 + 4.26 bilateral factor, integer half-up, single final rounding | IMPLEMENTED_VERIFIED | `test_ratings.py` (regulation examples; AST ban on float/round) |
| Browser kernel ≡ server kernel | IMPLEMENTED_VERIFIED | 27 router + 12 rating golden fixtures, `frontend/tests/parity.test.mjs` |
| Hash-chained, append-only audit (refuses UPDATE/DELETE/TRUNCATE for owner) | IMPLEMENTED_VERIFIED | `test_audit_and_schema.py` |
| Transactional outbox | PARTIAL | Rows written in-transaction; **no dispatcher** (G19) |
| Sign-in | MOCK | HMAC dev tokens, 10-min TTL, refused in staging/production; one swap point (`auth.verify_token`) |
| ClaimsBoundaryGuard (prohibited-phrase list, governance §7) | PARTIAL | Lints all shipped copy in CI; weak on negation; not yet applied to model output (no model exists) |
| Reference data (`data/reference`: governance, sources, timeline, conflicts), validated at load, served read-only at `/api/v1/reference/*`, generated into the browser | IMPLEMENTED_VERIFIED (content UNVERIFIED) | `test_reference.py`; guest e2e checks claims guide and rules render from it |
| Crisis floor (6 hard-coded contacts, every screen, no network) | IMPLEMENTED_VERIFIED (UI) / NOT_PRESENT (detector) | browser test opens it; no free-text crisis detector yet (no free-text input exists) |
| Benefit eligibility engine, source registry, rule packs | NOT_PRESENT / BLOCKED_SOURCE | G1: no human-verified rule |
| Agents, model gateway, ContextPackets, Trust Kernel PDP/PEP | NOT_PRESENT | Blocked on model-provider contract (G21/G23) |
| Documents, claims tracker, referrals, CRM, community, education, career | NOT_PRESENT / DEFERRED | See `MIGRATION_MAP.md` |

## 4. Commands and results (latest run, 21 Oct 2026, after integrating guest app v3/v4 and the Integrated Record)

```
cd backend && pytest                          -> 163 passed (PostgreSQL 16.15, real non-owner role)
cd frontend && npm test                       -> 51 passed (browser/server parity, incl. 10 bilateral cases)
cd frontend && npm run build                  -> OK (vite 8.3.4)
cd frontend && npm run test:e2e               -> guest: 1 passed; full stack (with running API): 2 passed
npm audit                                     -> 0 vulnerabilities
python scripts/build_web.py --check           -> in sync
```

CI on GitHub has not run yet for this branch at the time of writing; see the Actions tab after push.
