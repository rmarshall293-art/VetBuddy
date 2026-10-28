# Gap Matrix

Labels (v6 §0, ADR 0004): IMPLEMENTED_TESTED · IMPLEMENTED_UNVERIFIED · PARTIAL · MOCK · PLANNED · DISABLED · BLOCKED

## Slice 01 — Auth → Privacy → Person → Service → Onboarding → Mission/Case → Brief/Tasks

| Capability | Status | Evidence |
|---|---|---|
| Single `/api/v1` prefix, `/readyz` (503 until crisis floor + DB OK) | IMPLEMENTED_TESTED | `PlatformBasics.*` |
| Tenant isolation: RLS forced, fail-closed, non-owner app role | IMPLEMENTED_TESTED | `CrossTenantIsolation.*`, mutation-tested (disabling RLS makes 2 tests fail) |
| Two veterans / two orgs cannot see each other's cases (P2 gate) | IMPLEMENTED_TESTED | `test_two_veterans…`, `test_two_organizations…` |
| Auth: one `current_principal` swap point | **MOCK** | HMAC dev tokens, `VB_AUTH_MODE=dev`; any other mode fails closed (`test_auth_disabled_fails_closed`) |
| Real identity (OIDC / ID.me / Microsoft) | BLOCKED | Master Record default #3 needs your decision + relying-party agreement |
| Privacy Mode A (guest, nothing persisted) | IMPLEMENTED_TESTED | `test_guest_preview_persists_nothing` counts every table before/after |
| Privacy Mode B (personal, consented) | IMPLEMENTED_TESTED | onboarding tests |
| Privacy Mode C (managed case) | DISABLED (unreachable) | API 409 + DB CHECK, `test_mode_c_is_unreachable` |
| Consent grant / revoke, checked in-transaction on every read/write | IMPLEMENTED_TESTED | `test_revocation_takes_effect_on_next_request` |
| Consent purpose allowlist | IMPLEMENTED_TESTED | FK + API, `test_unlisted_consent_purpose…` |
| Person profile + service record (DECLARED provenance) | IMPLEMENTED_TESTED | onboarding flow |
| Guard/Reserve requires orders authority (never inferred) | IMPLEMENTED_TESTED | router validation + DB CHECK |
| Transition stage engine (13 stages + unknown) | IMPLEMENTED_TESTED | `StageTests` (24 boundary cases) |
| Deterministic Mission Router, versioned, input-hashed | IMPLEMENTED_TESTED | `DeterminismTests` (P3 gate: two personas route differently) |
| Master Mission + lane cases + tasks persisted | IMPLEMENTED_TESTED | API tests |
| Mission Brief: situation, first five actions, readiness dimensions (not a score), jurisdiction labels | IMPLEMENTED_TESTED | API + browser smoke |
| Task status, optimistic concurrency, transition rules | IMPLEMENTED_TESTED | `test_task_lifecycle…` |
| Hash-chained append-only audit | IMPLEMENTED_TESTED | `test_audit_chain_verifies`; app role cannot UPDATE/DELETE; trigger blocks the owner too |
| Transactional outbox (written in the same transaction) | PARTIAL | rows written and tested; **no consumer/dispatcher yet** |
| Task copy contains no eligibility/amount/deadline claims | IMPLEMENTED_TESTED | `ContentSafetyTests` lint |
| Help Me Now (crisis floor from the single config) | IMPLEMENTED_TESTED | `test_crisis_contacts_verbatim` + UI smoke |
| Web shell (guest, save, brief, tasks, privacy, help) | IMPLEMENTED_TESTED (smoke) | `tests/e2e/smoke_ui.py`, light + dark, 1280 + 390 px, no horizontal overflow |
| Accessibility WCAG 2.2 AA | PARTIAL | semantic forms/landmarks, 44px targets, focus rings, reduced motion; **no axe/screen-reader audit yet** |
| Rate limiting, CSRF | PLANNED | bearer tokens (not cookies), so CSRF is not applicable yet; rate limiting is a P11 item |

## Carried forward (not in this slice)

| Area | Status | Blocker |
|---|---|---|
| Benefit screening / eligibility engine (P4) | PLANNED, intentionally withheld in the UI | **G1: zero verified rules.** A named human must verify the 8 Alabama rules |
| Benefits, agents and career routes | PLANNED | contracts in `docs/ARCHITECTURE.md` §3 (skeleton stub routers removed in consolidation) |
| Runtime agents (P5) | PLANNED; manifests are DRAFT | Model-provider zero-retention contract (Master Record default #5) |
| Documents, claims, referrals, career, education, MoneyLife, VSN | PLANNED | P6–P9 |
| Base44 route/entity parity map | BLOCKED | Base44 export not supplied |
| GitHub re-scan / CI run on GitHub | BLOCKED | GitHub not linked to this session |
| FastAPI / psycopg / Vite | PLANNED | Registries blocked here. See ADR 0002 |

## Open design decisions surfaced by this slice

- Meaning of red in the design system (Master Record §7.1). The shell uses red **only** for crisis help.
- WCAG 2.1 vs 2.2 AA target (Master Record §7.1). The shell aims at 2.2.

## Session 2 (2026-10-20): spec integration + HTML deliverables

| Capability | Status | Evidence |
|---|---|---|
| Nine foreclosed consent purposes as rows; grant refused by trigger even for the owner; rows immutable (CB-03) | IMPLEMENTED_TESTED | `0010`, `test_foreclosed_purposes_refused_everywhere` |
| Combined rating kernel, 38 CFR 4.25 (integer, half-up per Table I step, one final conversion) | IMPLEMENTED_TESTED | `test_kernel_ratings` (regulation examples, A-01 regression, AST purity) |
| Bilateral factor 38 CFR 4.26 (A-03) | IMPLEMENTED_TESTED | integer kernel + browser twin + guest toggle; `test_kernel_ratings.py::BilateralFactor`, parity fixtures, guest smoke test (ADR 0007) |
| Browser kernel `web/kernel.js` = Python kernel | IMPLEMENTED_TESTED | `test_web_parity`: 22 router + 11 rating fixtures via Node |
| Generated kernel data / standalone build current | IMPLEMENTED_TESTED | `scripts/build_web.py --check` in tests and CI |
| Standalone guest app `dist/vetbuddy.html` (Launch-0 privacy gates) | IMPLEMENTED_TESTED (smoke) | `tests/e2e/smoke_standalone.py`: no non-font network requests, no storage, no overflow, light/dark |
| Claims guide content (VA 8 statuses, deadline windows) | PARTIAL | statuses checked on VA.gov 2026-10-20; windows now generated from `transition_timeline.json` (UNVERIFIED, shown as such) |

## Slice 02 (2026-10-20): reference corpus integration

See `docs/INTEGRATION_LEDGER.md` for sources, removed duplicates and conflicts.

| Capability | Status | Evidence |
|---|---|---|
| `ref` schema (migration 0011): 17 tables, public V0, app role read-only, zero-PII guard | IMPLEMENTED_TESTED | `DatabaseEnforces.*` |
| Reference corpus: 847 rows at slice 02 (855 after consolidation) / 12 datasets, every row sourced and status-labelled; 0 VERIFIED | IMPLEMENTED_TESTED | `CorpusShape.*`, `test_counts_match_corpus` |
| Validator rejects retired crisis numbers, personal mailboxes, duplicate org+place, unregistered sources, single-reading conflicts, float money, prohibited language | IMPLEMENTED_TESTED | `ValidatorRejects.*` (13 mutation cases) |
| Same rules enforced by the database on its own | IMPLEMENTED_TESTED | `DatabaseEnforces.*` |
| Crisis floor merged (6 contacts, one authored file, generated copy checked) | IMPLEMENTED_TESTED | `CrisisFloorSingleAuthorship.*` + UI and standalone smoke |
| ClaimsBoundaryGuard pattern set (T0-01..03) + required language in one config | PARTIAL | scan + tests; runtime placement waits for agents |
| Public API: `/reference`, `/reference/women-veterans`, `/reference/jurisdictions/{code}`, `/reference/conflicts`, `/reference/guard-reserve` | IMPLEMENTED_TESTED | `ReferenceApi.*` (crisis first, 404s, no determinations) |
| Women veterans directory: 50 state offices, 32 national, 6 VA facility roles, 5 territory DV coalitions, 23 Cohen clinics, 13 MST residential | PARTIAL | data UNVERIFIED; MST rows rest on a 2009 source; WV 181-row seed still missing |
| State financial summary (50 states + DC) + 42 benefit leads (Sentinel + finance) | PARTIAL | all leads; G1/G2 unchanged |
| Pay, BAS, BAH samples, VA 2025 rates as integer cents | PARTIAL | UNVERIFIED / ILLUSTRATIVE; `kernel_usable_rates() == []` by design |
| Guard/Reserve duty authorities (15) + rule leads (9) | PARTIAL | SOURCE_CHECKED by Sentinel; determination withheld (G1) |
| Education program registry (22, deduplicated) | PARTIAL | authority stubs only (G3) |
| TDIU threshold check | PLANNED | v2.0 had it; source not in hand (4.26 is now implemented, see A-03) |
| WV runtime (CrisisGate, PIIMinimizer, MSTNarrativeGuard), EdNav engines | BLOCKED | specs only |
| v2.0 datasets: 737 codes | PARTIAL | 737 codes + criteria text (2020 edition) in `ref.rating_code` (migration 0015), all UNVERIFIED, digestive SUPERSEDED; re-transcribe from current eCFR |
| v2.0 datasets: 2026 rates, presumptives, 87 manifests | BLOCKED | not in any upload |
| License reciprocity (teacher, UBE, real estate) | BLOCKED | two unsourced datasets disagree for 42 of 51 states (`conflict.license_reciprocity.two_datasets`); verify against NCBE and state boards |

## Consolidation (2026-10-20): slice 02 merged, redundancies removed

| Capability | Status | Evidence |
|---|---|---|
| One integrated record, generated: governance tables, conflicts, corpus counts, crisis banner, test and migration counts filled from repository data | IMPLEMENTED_TESTED | `docs/record.html` → `dist/vetbuddy-record.html`; `build_web.py --check`; `RecordGenerated.*` |
| Guest app reads timeline windows, sources, non-negotiables, R1–R22, legal lane and required wording from the corpus and config (no hand copies) | IMPLEMENTED_TESTED | `GuestAppSingleAuthorship.*`; standalone smoke |
| Three claims windows only the app held (VGLI apply, separation effective date, decision review) moved into the corpus with sources | PARTIAL | UNVERIFIED like every window; verify against the named authority (G1) |
| Legal lane table in `governance.json` (single author) | IMPLEMENTED_TESTED | `GuestAppSingleAuthorship.test_legal_lane_language_is_clean` |

## Open work (folded in from the retired BACKLOG.md)

| Item | Priority | Note |
|---|---|---|
| Human verification of the 8 Alabama rules, then the riskiest reference rows (13 MST programs, G.I. Dependents' cap, 2025→2026 VA and BAS rates, statutory windows) | P0 | G1; a named reviewer, no bulk import |
| Approval state must stay in the `approval` table (never in memory) before more than one worker runs; service check that reviewer ≠ submitter | P0 | schema CHECK exists (0005); service lands with approvals in P5 |
| Prototype defects to re-check when the v2.0 source returns: CAREGIVER missing from the dependent context set; `any_of_rules` operator declared but unimplemented | P1 | BLOCKED |
| Disclaimer renders on every unverified-jurisdiction result in every client before any state-2 data, even as drafts | P1 | web shell, guest app and API do today |
| Data Trust Card on every new benefit or resource row, enforced at insert | P1 | `ref` schema enforces sources and status; tenant `benefit` table enforces citation, tier and dates |
| Career/MOS module: crosswalk, job matching, DD-214 resume builder | P2 | after CB-01/02; see ARCHITECTURE §3–4 |
| Work-style assessment | P2 | blocked on instrument or licence decision (ARCHITECTURE §4) |
| Regulatory change feed for "50 years of VA law" content | P2 | never a static page |
| Insurance content (VGLI/SGLI education, no product rankings) | P2 | until a licensed producer partnership exists |
| ID.me relying-party agreement; VA Lighthouse production access (month-plus lead time) | P2 | G17, G18 |
| Explicitly deferred: CRM-as-core, marketplace and monetization, white-labeling, autonomous agent sprawl, desktop app, marketing as core build | — | per v4.0 and the Master Record |

## Slice 03 (2026-10-25): master prompt v6 integrated; export and account deletion

Per-requirement status against v6 is in `docs/REQUIREMENTS_TRACEABILITY.md`.

| Capability | Status | Evidence |
|---|---|---|
| v6 adopted as the governing spec; labels migrated (0012) | IMPLEMENTED_TESTED | ADR 0004; `V6Vocabulary.*` |
| Data export of everything stored for the account | IMPLEMENTED_TESTED | `Export.*`; web smoke downloads `vetbuddy-export.json` |
| Account deletion: full data-graph purge, receipt, sessions fail closed | IMPLEMENTED_TESTED | `Deletion.*` (8); mutation-tested; web smoke deletes an account |
| Shared-tenant deletion | PARTIAL | refused safely; per-person ownership not built |
| Backups, processors, legal holds in deletion | PLANNED | `docs/ACCOUNT_DELETION_RUNBOOK.md` |
| v6 common notice; draft privacy notice held back; operator fields release-blocking | IMPLEMENTED_TESTED | `ReleaseGates.*`, `GuestAppSingleAuthorship.*` |
| Guest Clear session | IMPLEMENTED_TESTED | standalone smoke |

## Slice 04 (2026-10-27): Benefit Vault integrated; v8 placed; aggregation kernel

Decisions: ADR 0005. Vault components (V01–V25) and its own defects (VD01–VD20) are in `docs/BENEFIT_VAULT_ARCHITECTURE.md` §12–13; the status below is after integration.

| Capability | Status | Evidence |
|---|---|---|
| Vault registry: 1,362 records, 116 sources, 56 of 57 jurisdiction rows (American Samoa SOURCE_NOT_AVAILABLE) | IMPLEMENTED_TESTED | `build_vault_registry.py --check`; `tests/vault/test_importer_registry.py` |
| Migration 0014 on the real slice 03 chain (RLS, append-only ledger, purger grants, deletion postcondition) | IMPLEMENTED_TESTED | `tests/vault/test_database.py` (22) on a database built from 0001–0014; postcondition mutation tests |
| Account deletion reaches the vault tables | IMPLEMENTED_TESTED | `test_purge_removes_every_vault_row_of_one_tenant`; `test_account_deletion_removes_vault_rows_and_closes_the_session` |
| Vault API mounted at `/api/v1/vault` with the platform session, consent and error contract | IMPLEMENTED_TESTED | `tests/test_vault_integration.py` (7) |
| Mode B account routes (grants, ledger, saved) | PARTIAL | Work with the dev sign-in (MOCK); production sign-in waits on G17 |
| Matching outcomes | PARTIAL | v6 outcomes only. Production policy `verified_only` shows no PRELIMINARY_MATCH until G1 |
| Pull providers over slice 03 stores (V12) | PARTIAL | Agent ids are not mapped yet (VD06; v8 roster proposal in ADR 0005 §7) |
| Named-reviewer verification (V21) | BLOCKED | G1 |
| Benefits screens (V25) | IMPLEMENTED_TESTED | Web shell `#/benefits` (server); guest app Benefits finder (catalog search only, no matching); smoke tests |
| psycopg-shaped facade and pytest bridge | IMPLEMENTED_TESTED | 228 vault tests under unittest; mutation checks |
| k-anonymity aggregation kernel (k = 11, complementary suppression on rows and columns) | IMPLEMENTED_TESTED | `tests/test_geo_aggregation.py` (randomized attacker; the received module fails it) |
| Area-need reporting | PLANNED | Needs a county field and a `geographic_insight` consent purpose (both owner decisions) |
| Policy drafts | Not published | `docs/POLICY_CLAIMS_REGISTER.md` |
| CRM bounded context (v8) | PLANNED | Contained subsystem only; never CRM-first |

**New open items:**
- **VD21 (decision):** in production, a non-match from an *unverified* rule hides the record (counted, not listed). Show these as review leads instead?
- **VD22:** vault handlers make blocking database calls inside `async` routes; move store calls to the threadpool.
- **VD06:** agent-id mapping; v8's roster is the proposed target.
- **GA:** county field, consent purpose and a county domain list are needed before any area report.
