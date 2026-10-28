# VetBuddy — Architecture (current)

Governing spec: master prompt v6 (`docs/VETBUDDY_MASTER_SPEC.md`; ADR 0004).
v8 (Base44 directive) is a product-scope amendment; ADR 0005 says how it applies here.
Precedence, decisions and status live in the integrated record
(`docs/record.html` → `dist/vetbuddy-record.html`). This file covers how the
code is shaped, and the contracts the next slices must satisfy.

## 1. Shape

A modular monolith (master spec §5): one Starlette app (`backend/app/api/main.py`,
ADR 0002) with a single `/api/v1` prefix and `/readyz`, over one PostgreSQL
schema. Four services will be isolated later because they hold outside
credentials or touch untrusted files: model gateway, VA connector (read-only,
session-only), document intake (sandboxed, no network), worker (outbox).

| Plane | Owns | In this repo |
|---|---|---|
| 1 Trust & Identity | auth, tenancy, consent, privacy modes, audit, privacy rights | `domains/trust/` — MOCK principal, consent, hash-chained audit; `domains/privacy/` — export and account deletion; migrations 0001, 0009, 0010, 0013 |
| 2 Work OS | Master Mission, Master Case, lanes, tasks, deadlines | `domains/missions/` — deterministic router, service; migration 0006; `domains/vault/matcher.py`, `search.py`, `household.py` (benefit matching kernel) |
| 3 Secure Context Fabric | Guardian, ContextPackets, PDP/PEP | vault-local: `domains/vault/governance/` (manifests, grants, sealed packets, pull broker, hash-chained pull ledger, egress allowlist); platform-wide version not built (table `context_packet` only) |
| 4 Source Intelligence | jurisdictions, reference corpus, rule packs, determinations | `domains/reference/`, `domains/kernel/ratings.py`; migrations 0003, 0011, 0014; `data/reference/`; `domains/vault/registry.py`, `rules.py`, `discovery/` |
| 5 AI Workforce | orchestrator, specialists behind manifests | manifests DRAFT (0005, 0009); the Benefit Vault agent (`domains/vault/agent.py`) runs its guard pipeline with no model call |
| 6 Integration Gateway | external adapters | not built |
| 7 Operations Center | monitoring, outbox worker, kill switch | `outbox_event` table; no dispatcher |

### Single authorship

Each fact has one author; everything else is generated from it and
drift-tested.

| Fact | Author | Generated copies |
|---|---|---|
| Router policy, task wording, stages | `domains/missions/` | `web/kernel_data.js` (parity test runs both kernels) |
| Crisis contacts | `config/crisis_floor.yaml` | kernel data, guest app, record banner |
| Required and prohibited wording, v6 common notice, release-blocking operator fields | `config/governance_language.yaml` | guest app disclaimer and notice, referral block, Find-a-Rep link |
| Implementation labels (v6 §0) | `corpus.REPO_STATUSES` + SQL CHECK (0012) | governance data, record pills, guest app |
| Jurisdictions | migration 0003 (one parser: `corpus.known_jurisdictions`) | kernel data, record |
| Timeline windows, sources, rules, legal lane, conflicts | `data/reference/*.json` | `database/seeds/0011_reference.sql`, kernel data, record |
| Counts in the record (tests, migrations, rows) | the repository itself | `dist/vetbuddy-record.html` |
| Benefit Vault records, facts, rules, manifests, component status | `data/research/*.psv` + `config/benefit_vault_policy.yaml` → `data/reference/benefit_vault_registry.json` (`scripts/build_vault_registry.py`) | `database/seeds/0014_benefit_vault_seed.sql` (`build_vault_seed.py`), guest app catalog, record section |
| Vault notice | `config/governance_language.yaml` `common_notice` | registry `notice`, every vault response |

`scripts/build_reference.py --check`, `scripts/build_vault_registry.py --check`,
`scripts/build_vault_seed.py --check` and `scripts/build_web.py --check` fail CI
when any generated copy is stale.

## 2. One engine for every jurisdiction

One schema, one API, one matching path for all 57 jurisdictions. What varies is
data, not code: `jurisdiction.verification_status`. Unverified jurisdictions
carry the disclaimer from `config/jurisdiction_status.yaml`; "national site
live, Alabama the only verified state" is the default state of the system,
not a special case. Today 0 of 57 are verified (gap G1).

## 3. Contracts for upcoming slices

These replace the skeleton's FastAPI stub routers, which could not be mounted
(ADR 0002) and were removed in the consolidation. Build each against its
contract.

**Benefit matches** (`GET /api/v1/benefits/matches?jurisdiction_code=`, P4).
Deterministic only; no model call in the path. A missing or unknown fact never
resolves to a denial (three-valued). Each result carries benefit, status,
matched and unknown rules, source citation, source tier and last verified.
Statuses (v6 §5, ADR 0004): `PRELIMINARY_MATCH | NEEDS_INFORMATION |
NEEDS_EVIDENCE | DOES_NOT_MEET_ENCODED_RULES | SOURCE_STALE |
CONFLICTING_AUTHORITY | HUMAN_REVIEW_REQUIRED`, with per-condition reasoning;
never "approved", "eligible" or "guaranteed". Each recommendation carries
program, administering agency, jurisdiction, citation, rule and verification
dates, known and missing facts, conflicts and next step. Unknown stacking
compatibility means review, never an inferred stack. Unverified jurisdictions wrap the whole response
in the disclaimer. Eligibility logic lives in the engine, never in a route.

**Resources** (`/api/v1/reference/*` today). Installations, Guard/Reserve and
women-veteran records are categories in one store, not separate services.
Women-veteran results must pass the same guards as everything else
(MSTNarrativeGuard, PIIMinimizer); no parallel, less-governed path.

**Agents** (`POST /api/v1/agents/{agent_id}/run`, P5). No manifest, no access:
look up `agent_manifest`; 404 if absent, 409 unless `PRODUCTION`; issue a
minimum-necessary ContextPacket; dispatch. `backend/app/agents/registry.json`
holds the draft manifests for the planned career, Guard/Reserve, women
veterans and installation agents; fill readable classes, purposes and tools
before any status change.

**Career** (P8). MOS translation uses public O*NET / CareerOneStop crosswalks.
The DD-214 resume builder produces a draft that needs explicit user approval
before export. The ADA metamorphic test and fact-level allowlist (CB-01/02)
come first.

## 4. Work-style assessment: licensing flag

DiSC is a licensed, trademarked instrument. Do not build or brand an
assessment as "DISC" without a licence. The schema's generic
`work_style_assessment` table supports either a licensed instrument with an
executed agreement, or an original, transparently scored assessment; the
assessment endpoint stays blocked until that decision is made (Master Record
§7.1 row 23).

## 5. Privacy rights (v6 §3)

Export and deletion live in `domains/privacy/` and need no mission consent.
Deletion is one transaction inside `vb_delete_account`, run as
`vetbuddy_purger`, a NOLOGIN role that cannot bypass RLS, so the database
scopes every delete to the caller's tenant on top of the function's own
predicate. The audit trail stays append-only except for that sanctioned
purge. Details, and what must exist before real accounts launch, are in
`docs/ACCOUNT_DELETION_RUNBOOK.md`.

## 6. Benefit Vault (migration 0014; ADR 0005)

Design, rule language, governance and defects: `docs/BENEFIT_VAULT_ARCHITECTURE.md`.
How it sits in this app:

- **Routes** `/api/v1/vault/*` are built once in `create_app` (`v1.vault_routes`).
  The agent is built from the registry plus any named-reviewer VERIFIED marks
  in the database (`load_reviews`), so a review takes effect on restart.
- **Modes.** A request is Mode B (account) only if it passes the same checks as
  every protected route: a valid token, a live `app_user`, active consent, in
  one tenant-scoped transaction (`v1.vault_tenant`). Anything else is Mode A
  (guest): V1 facts only, nothing stored.
- **Store.** `VaultStore(connect=...)` opens a connection per operation with
  `vetbuddy.tenant_id` set locally; it uses `app.infra.pg_compat` (psycopg 3
  surface over the libpq driver).
- **Deletion.** `vb_delete_account` reaches the three vault tenant tables;
  the ledger allows DELETE only to `vetbuddy_purger` during that tenant's
  purge; 0014's postcondition fails if any tenant table is unreachable.
- **Errors** follow the `/api/v1` contract.
- **Tests.** `tests/vault/` (pytest style, run by `tests/pytest_bridge.py`)
  plus `tests/test_vault_integration.py` for the seams.

## 7. Aggregate insights

`domains/insights/geo_aggregation.py`: k = 11 floor, allow and deny lists of
dimensions, withheld cells carry no count, and complementary suppression on
every line (rows and columns) until withheld cells hold at least k people.
Nothing feeds it: there is no county field and no `geographic_insight`
consent purpose (both owner decisions; re-identification of aggregates is a
foreclosed purpose).
