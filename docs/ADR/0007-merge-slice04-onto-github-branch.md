# ADR 0007: One codebase — slice 04 is the base of the GitHub branch

**Status:** Accepted, 2026-10-28 (owner decision)

## Context
Two working VetBuddy codebases existed:

- **This GitHub branch** (`claude/dazzling-clarke-59kw1x`, last at `108a9ec`): FastAPI + psycopg + Vite; 6 migrations; 163 backend and 51 parity tests. Unique work: 38 CFR 4.26 bilateral factor, the 737-code rating schedule, the product layout and its governance ADR.
- **Slice 04** (uploaded `VetBuddy-slice04.zip`, git bundle with branches slice 01–04): Starlette + an in-house libpq driver shaped like psycopg 3; 14 migrations; 371 tests. Unique work: the 855-row reference corpus, the 1,362-record Benefit Vault, data export and real account deletion, master prompt v6.

The two 38 CFR 4.25 kernels agree on all 1,364 combinations of up to four ratings. Slice 04's own ADR 0002 names FastAPI + psycopg as its planned stack once package registries are reachable.

## Decision
- The branch now carries the slice 04 tree as its base. Only **content** was imported: the bundle's commit history was not merged, because its commits carry a personal name and email address and this repository is public.
- This branch's unique work was ported onto it:
  - 38 CFR 4.26 in `backend/app/domains/kernel/ratings.py` and its browser twin `web/kernel.js`, with parity fixtures and the guest calculator toggle;
  - the 737-code schedule as `data/reference/rating_schedule.json` → `ref.rating_code` / `ref.rating_criterion` (migration 0015), served at `/api/v1/reference/rating-schedule`;
  - `docs/PRODUCT_LAYOUT.md` and ADR 0006 (was ADR 0003 on this branch).
- The stack swap to FastAPI + psycopg remains planned (ADR 0002), as its own slice.

## Feature map (nothing removed without a covering test)

| This branch had | Now provided by | Covering tests |
|---|---|---|
| Deterministic Mission Router, Mission Brief, tasks | `domains/missions` | `test_router_policy.py`, `test_slice01_api.py`, `test_web_parity.py` |
| 38 CFR 4.25 integer kernel | `domains/kernel/ratings.py` | `test_kernel_ratings.py` (regulation examples, AST purity) |
| 38 CFR 4.26 bilateral factor | ported into the same kernel | `test_kernel_ratings.py::BilateralFactor`, `test_web_parity.py::test_bilateral_identical`, `tests/e2e/smoke_standalone.py` |
| Forced RLS on a non-owner role; fail-closed context | migrations 0009+, `infra/db.py` | `test_slice01_api.py`, `test_privacy_rights.py`, `vault/test_database.py` |
| Consent with foreclosed purposes | migration 0010 | `test_slice01_api.py` |
| Hash-chained append-only audit | `domains/trust` | `test_slice01_api.py`, `test_privacy_rights.py` |
| Guest mode stores nothing | standalone guest app + Mode A API | `tests/e2e/smoke_standalone.py`, `test_slice01_api.py` |
| Reference data (governance, sources, timeline, conflicts) | `ref` schema corpus (superset) | `test_reference_corpus.py` |
| 737-code rating schedule | migration 0015 | `test_rating_schedule.py` |
| Dev sign-in (mock) | `domains/trust/principal` (mock) | `test_slice01_api.py` |
| FastAPI app, Vite build, Dockerfile, Compose | **Not carried**: Starlette app and `scripts/dev.sh` serve the same API shape; Vite build not needed for the framework-free `web/` | — |

**Rollback:** `git checkout 108a9ec` restores the previous tree exactly.
