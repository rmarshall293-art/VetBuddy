# VetBuddy

A Veteran Operating System: one Master Mission per person, deterministic rules for anything consequential, and honest labels on everything else.

**Start here:** `dist/vetbuddy-record.html`, the integrated project record (generated from `docs/record.html` and the repository's own data).

**Status:** slice 01 of the master spec (§22) works end to end against a real PostgreSQL: onboarding, privacy modes, person and service record, Master Mission and lane cases, deterministic Mission Brief, and tasks. Slice 02 adds the reference corpus: 855 sourced, status-labelled rows (women veterans directory, pay and compensation, 51-jurisdiction financial summary, Guard/Reserve authorities, Alabama TAP landscape, education registry, governance register) in a read-only `ref` schema with public endpoints under `/api/v1/reference`. None of it is verified yet, and none of it decides eligibility. Slice 03 integrates master prompt v6 and adds the account rights it requires before real accounts launch: full data export and true account deletion (whole data graph purged, receipt with no personal data, sessions fail closed). Slice 04 integrates the Benefit Vault (migration 0014): 1,362 sourced federal, state, nonprofit and retail benefit records, a deterministic matcher that answers in the v6 outcome words, pull governance with a hash-chained ledger, and Benefits screens in both apps; nothing is VERIFIED yet, so production shows leads for review, never matches. The branch also carries the 38 CFR 4.26 bilateral factor in the rating calculator and the 737-code Part 4 rating schedule as unverified reference data (migration 0015; ADR 0007). It is **not production-ready**: sign-in is a development mock, benefit matching is intentionally off (no verified rules yet), and nothing has had a security review. See `docs/GAP_MATRIX.md`.

## Run it

Requires Python 3.12+, PostgreSQL 16 (server + `libpq`), and the packages in `requirements.txt`.

```bash
scripts/dev.sh          # creates vetbuddy_dev, applies migrations, serves http://127.0.0.1:8000
scripts/test.sh         # fresh vetbuddy_test DB (migrations + reference seed) + the full backend suite
scripts/test.sh --ui    # + Playwright browser smoke test
python3 scripts/build_web.py   # regenerate web/kernel_data.js, dist/vetbuddy.html and dist/vetbuddy-record.html
python3 scripts/build_reference.py   # validate data/reference/*.json and regenerate database/seeds/0011_reference.sql
python3 scripts/build_vault_registry.py   # research ledgers + policy -> data/reference/benefit_vault_registry.json
python3 scripts/build_vault_seed.py       # registry -> database/seeds/0014_benefit_vault_seed.sql
```

Postgres connection defaults to `localhost:5432` as `postgres`; override with `PGHOST`, `PGPORT`, `PGUSER`. See `.env.example`.

## Layout

```
CLAUDE.md                     standing engineering rules
docs/VETBUDDY_MASTER_SPEC.md  governing spec: master prompt v6 (v5 and canonical integration v2 inside as appendices)
docs/PRODUCT_LAYOUT.md        product layout: Case Management is the core, CRM the relationship layer (ADR 0006)
docs/REQUIREMENTS_TRACEABILITY.md  status of every v6 requirement + release blockers
docs/ACCOUNT_DELETION_RUNBOOK.md   export and deletion design and launch prerequisites
docs/BENEFIT_VAULT_ARCHITECTURE.md the vault's design, rule language, governance and defect register
docs/POLICY_CLAIMS_REGISTER.md     every promise in the two policy drafts, checked against the build
docs/CURRENT_STATE_AUDIT.md   what was observed, defects found by running the skeleton
docs/record.html              integrated record template -> dist/vetbuddy-record.html (generated)
docs/ARCHITECTURE.md          current structure, single-authorship map, contracts for upcoming slices
docs/GAP_MATRIX.md            every capability with an honest status label, plus open work
docs/ADR/                     decisions (source of truth; runtime stack)
database/migrations/          0001–0008 skeleton (unchanged) + 0009 hardening/onboarding + 0010 foreclosed purposes + 0011 ref schema + 0012 v6 labels + 0013 account deletion + 0014 Benefit Vault + 0015 rating schedule
database/seeds/0011_reference.sql   GENERATED reference seed (do not edit; edit data/reference/*.json)
database/seeds/0014_benefit_vault_seed.sql   GENERATED vault seed (edit data/research/ or config/benefit_vault_policy.yaml)
data/research/                research ledgers (one benefit per line) and hash-checked recovered data
config/benefit_vault_policy.yaml   the vault's authored policy: publish policy, grants, manifests, caveats
data/reference/               canonical reference JSON with sources and status on every record
config/crisis_floor.yaml      the one authored crisis floor (6 contacts)
config/governance_language.yaml  required disclaimers, VSO block, prohibited claim language
docs/INTEGRATION_LEDGER.md    what every input became, duplicates removed, conflicts kept
backend/app/
  api/main.py, api/v1.py      Starlette app, /api/v1, /readyz, error contract
  infra/db.py                 libpq driver + tenant-scoped transactions
  domains/trust/              principal (MOCK), consent, hash-chained audit
  domains/missions/           deterministic Mission Router, task library, service
  domains/kernel/ratings.py   38 CFR 4.25 combined rating (pure, integer)
  domains/privacy/            data export and account deletion (v6 §3)
  domains/vault/              Benefit Vault: registry, rule language, matcher, search, governance, agent, API
  domains/insights/           k-anonymity aggregation kernel (not wired to data)
  infra/pg_compat.py          psycopg 3 shaped facade over the libpq driver (ADR 0005)
  domains/reference/          corpus loader + validator, phone normalizer, claims-boundary scan, read service
web/                          framework-free web shell; kernel.js = browser twin of the Python kernel
web/standalone.html           guest app template -> dist/vetbuddy.html (no server, stores nothing)
tests/e2e/                    browser smoke tests: web shell (smoke_ui), guest app + record (smoke_standalone)
```

## Ground rules this build enforces in code

- The API connects as a **non-owner** role; RLS is forced and fails closed. A migration guard refuses to ship a tenant table without it.
- Guest mode persists nothing (tested by counting every table before and after).
- Deleting an account removes every row of every tenant table for it, in one transaction run by a role that cannot bypass RLS; its sessions then fail closed.
- Consent is checked inside every protected transaction, so revocation applies on the next request.
- Guard/Reserve authority is never inferred. The DB rejects a Guard/Reserve service record without one.
- Task text may not claim eligibility, amounts or deadlines (a lint test enforces this).
- Unverified jurisdictions always carry the disclaimer from `config/jurisdiction_status.yaml`.
- Benefit Vault: answers only in the v6 outcome words with `determination: none`; in production nothing is a match until a named reviewer verifies it; guests give V1 facts only and nothing is stored; every pull needs a user grant and is logged by key, never value.
- Reference data: every row names a registered source; nothing is VERIFIED without a named reviewer; the retired crisis number is refused; conflicts keep both readings; every directory answer starts with the crisis floor.

`docs/sources/` (original planning docs) is gitignored, because the GitHub repo was last observed as public.
