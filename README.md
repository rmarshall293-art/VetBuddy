# VetBuddy

A Veteran Operating System: one companion that turns where a service member, veteran or family member is in their transition into a short, honest plan — and never guesses about benefits.

**Status: early foundation, not production-ready.** Sign-in is a development stand-in, no benefit rule has been verified by a human reviewer, and no AI model is called anywhere. See [`docs/CURRENT_STATE_AUDIT.md`](docs/CURRENT_STATE_AUDIT.md) and [`docs/GAP_MATRIX.md`](docs/GAP_MATRIX.md).

## What works today

- **Guest app** (`frontend/`): Mission Brief, 38 CFR 4.25 rating calculator, claims guide, benefits finder (shows verification status), crisis help on every screen. Runs entirely in the browser; stores and sends nothing (browser-tested).
- **API** (`backend/`): deterministic Mission Router, rating arithmetic, and saved plans (Master Mission → Master Case → lanes → tasks) for signed-in users who consent.
- **Database**: PostgreSQL 16 with forced row-level security on a non-owner role, purpose-scoped consent (foreclosed purposes refused by the database), hash-chained append-only audit, transactional outbox.

## Run it

```bash
# Everything (Postgres, migrations, API on :8000, web on :5173)
docker compose up --build

# Or piece by piece
cd backend && pip install -r requirements-dev.txt
DATABASE_URL=postgresql://owner@localhost/vetbuddy APP_DB_LOGIN=vetbuddy_api APP_DB_PASSWORD=... python -m app.migrate
APP_DATABASE_URL=postgresql://vetbuddy_api:...@localhost/vetbuddy AUTH_MODE=dev AUTH_DEV_SECRET=<32+ chars> \
  CORS_ORIGINS=http://localhost:5173 uvicorn app.main:app --reload
cd frontend && npm ci && VITE_API_URL=http://localhost:8000 npm run dev   # omit VITE_API_URL for guest-only
```

API docs: `http://localhost:8000/api/docs`.

## Test it

```bash
cd backend && pytest                 # needs a Postgres you can create databases on
                                     # (TEST_DATABASE_ADMIN_URL, default local socket :5433)
cd frontend && npm test              # browser kernel == Python kernel (golden fixtures)
cd frontend && npm run build && npm run test:e2e   # set VB_E2E_API_URL for the full-stack test
python scripts/build_web.py --check  # generated browser data is in sync
```

## Layout

```
backend/app/kernel/       deterministic router, rating math, vocab (source of truth for wording)
backend/app/governance/   required language + ClaimsBoundaryGuard phrase list
backend/app/api/          /api/v1 routes, schemas (unknown fields -> 422), error contract
backend/app/services/     Work OS persistence (consent, missions, tasks, audit, outbox)
backend/migrations/       forward-only SQL migrations (roles, RLS, consent, audit)
frontend/src/             guest app + saved-plan view; kernel_data.js is generated
data/reference/           governance wording + rule status, sources, transition windows, conflicts (single author)
scripts/build_web.py      generates browser data and parity fixtures from Python + data/reference
docs/                     master spec, audit, gap matrix, integration ledger, migration map, ADRs, architecture
```

## Rules that bind every change

Read [`CLAUDE.md`](CLAUDE.md) and [`docs/VETBUDDY_MASTER_SPEC.md`](docs/VETBUDDY_MASTER_SPEC.md). In short: deterministic services decide, AI only explains; no invented benefits, sources or deadlines; VetBuddy never prepares or files a claim and claims help is always free; no real PII or secrets in git — **this repository is public**.

VetBuddy is not affiliated with or endorsed by VA or DoD, and it is not a VSO, an attorney or a clinician.
