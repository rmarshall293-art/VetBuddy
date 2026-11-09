# ADR 0005 — Integrate the Benefit Vault (0014) onto slice 03; place v8, the policy drafts and legacy prototypes

**Status:** Accepted, 2026-10-27

**Context.** The 2026-10-27 upload brought:

- the Benefit Vault package, `vetbuddy-vault-0014.zip` (sha256 `4e297c22…`): research, registry, migration, Python domain and 228 tests;
- its rendered viewer (`vetbuddy-vault-0014.html`) and summary (`VetBuddy_Benefit_Vault_Package.md`);
- the slice 03 bundle (identical to `2778641`);
- `VetBuddy_Unified_Master_Build_v8.html`, a Base44 build directive with a CRM-integration amendment;
- a consent package fragment: `README.md`, `onboarding-flow.html`, `geographic_aggregation.py` and `PRIVACY_POLICY.md`;
- `VetBuddy_Privacy_TOS_Security_Policy_Updated.pdf`;
- two stack PDFs (Data Mapping Architecture; Technical Architecture Pack);
- legacy prototypes: `main.py` (VTOS v5.1 FastAPI), `vetbuddy_os_demo.html`, `index.html`, `FinancialOS.html`;
- v6 `.md` and `.html` again. The `.md` is byte-identical to `docs/VETBUDDY_MASTER_SPEC.md`.

The vault was built against a *sandbox stand-in* for migrations 0001–0013 that has a `privacy.deletion_job` / `privacy.purge` design. Slice 03 has neither: deletion is `vb_delete_account()` running as `vetbuddy_purger` (0013).

**Decisions.**

1. **The vault joins as a domain, not a second app.** Code goes to `backend/app/domains/vault/`. Data goes to `data/research/` and `data/reference/benefit_vault_registry.json`. Policy goes to `config/benefit_vault_policy.yaml`. The schema is `schemas/json/`. Builders are `scripts/build_vault_{registry,seed}.py`, and the migration and seed are `0014`. Not copied: the sandbox baseline, the package markers and the two config copies, since the repository has its own.

2. **0014 uses slice 03's deletion, not the sandbox's.**
   - **Ledger deletes:** the append-only ledger allows DELETE only when `vetbuddy.purge_tenant` names the row's tenant *and* `current_user = 'vetbuddy_purger'`. Even the schema owner is refused (tested).
   - **Discard function:** `privacy.vault_discard` became `public.vb_vault_discard`, in line with the `vb_*` functions. Like 0013's functions, it is owned by `vetbuddy_purger`, which cannot bypass RLS. So the tenant scope is enforced twice: by the WHERE clause and by the policy.
   - **Purger grants:** `vetbuddy_purger` gets SELECT and DELETE on the three vault tenant tables.
   - **New postcondition:** 0014 fails if *any* public tenant table is unreachable by the purger, so a future table cannot silently escape deletion. A test proves the postcondition fires.
   - **Deletion test:** the vault's deletion test now calls `vb_delete_account` as the user would.

3. **Psycopg-shaped facade, not a second driver.** The vault store and tests use psycopg 3, which cannot be installed here (ADR 0002). `app/infra/pg_compat.py` implements the small part of psycopg's surface they use on top of the existing libpq driver: `connect`, `execute`, `%s` placeholders, nested `transaction()` as savepoints, `Rollback`, and `errors.*` by SQLSTATE. When psycopg can be installed, replace `pg_compat.connect` with `psycopg.connect`; nothing else changes. `infra/db.py` gained `query_rows` (tuple rows, row counts) and `transaction_status`.

4. **The vault's pytest-style tests run under the repository's unittest runner, unmodified in style.**
   - **Bridge:** `tests/pytest_bridge.py` registers a small `pytest` stand-in only when real pytest is absent, and collects fixtures, parametrize and `raises`.
   - **Database:** the tests run against a database built from the *real* chain (0001–0014 plus both seeds), not the sandbox baseline.
   - **Proof it fails when it should:** mutation checks confirmed that a broken assertion fails, and that so does a weakened ledger deletion rule.
   - **Test edits:** only for deliberate integration changes (notice, provenance copies, error shape, deletion path, function name).

5. **One notice, one error contract, one session rule.**
   - **Notice:** the vault notice is now the v6 common notice, read by the registry builder from `config/governance_language.yaml` (`notice_from: governance_language.common_notice`). This closes VD15 / C-09.
   - **Language guard:** it exempts only *exact* copies of the required texts, because the notice itself negates "guarantee".
   - **Errors:** vault errors use the `/api/v1` contract (`{"error": {code, message, trace_id, retryable, …}}`).
   - **Sessions:** a vault account (Mode B) request needs exactly what every protected route needs: a valid token, a live `app_user` row and active consent, in one tenant-scoped transaction. Anything less is a guest (Mode A) request, so guest features never need an account and a deleted account's token fails closed. The pull grant remains the purpose-bound consent for pulls (ApprovalGate).
   - **Reviews:** VERIFIED marks are applied at startup with `registry.with_reviews(load_reviews(conn))`. That closes VD10 at startup; a review takes effect on restart.

6. **Provenance stays verifiable.** The recovery manifest pinned the *slice 02* bytes of `governance_language.yaml` and `crisis_floor.yaml`. The runtime file has legitimately moved on, so the slice 02 bytes now ship as hash-checked provenance copies under `data/research/recovered/slice02/` instead of requiring the live config to stay frozen.

7. **v8 (Base44 directive v7.0 plus the v8 CRM amendment) is a product-scope amendment, not a replacement for v6 in this repository.** v8 targets the Base44 runtime ("Base44 work must be exportable to GitHub, then … migrated behind Supabase data adapters"). This repository *is* that GitHub and PostgreSQL target, and v6 remains its engineering directive. Adopted where compatible:
   - **CRM:** a contained partner-relationship bounded context, never CRM-first. It was already in CLAUDE.md and is now traced as V8-01.
   - **Monetization:** no sales or revenue labels in veteran UI, and benefit matches are never monetized.
   - **SARGE:** a skippable onboarding persona over one orchestrator, not an agent.
   - **Assessment:** the optional work-style assessment stays opt-in and never adjudicates.
   - **Tasks:** one task and deadline owner.
   - **Regression scenarios:** v8's list is mapped in `docs/REQUIREMENTS_TRACEABILITY.md`.
   - **Labels:** v8's own labels (LIVE_VERIFIED, PRESENT_VERIFIED, PLACEHOLDER …) apply to the Base44 inventory. This repository keeps the v6 labels (crosswalk below).
   - **Jurisdiction count:** v8 counts 56 jurisdictions (50 states, DC, five inhabited territories). The vault and the 0003 seed list 57 rows because they add the federal scope (`US`). Same footprint, different definition; American Samoa has no vault source.
   - **Agent roster:** v8's 22-role Tier 2 roster is the candidate target for the vault's agent-id mapping (VD06). Mapping proposal: `benefit_vault_agent` → v8 "Benefits Intelligence", which covers the Federal Benefits, State & Territory and Guard/Reserve roles; `claims_navigator_agent` → "Claims Navigation"; `crisis_support_agent` → a Tier 0 safety rule, since v8 makes crisis access a gate bypass, not an agent. **Still the owner's decision**; nothing is renamed.

   | v8 label | v6 label here |
   |---|---|
   | LIVE_VERIFIED, PRESENT_VERIFIED | IMPLEMENTED_TESTED (plus a source VERIFIED mark only via G1) |
   | PRESENT_UNVERIFIED | IMPLEMENTED_UNVERIFIED |
   | PLACEHOLDER | MOCK |
   | MISSING | PLANNED |
   | BLOCKED | BLOCKED |
   | SANDBOX | MOCK |

8. **Stack PDFs (Data Mapping; Technical Architecture Pack) are recorded, not adopted.** Their principles already hold here: PostgreSQL canonical, case-driven orchestration, framework-neutral domain contracts, an outbox for events and retrieval-bounded AI. Their concrete stack (Supabase or Firebase projections, Flutter, a Node BFF, Redis, a GraphQL gateway) needs its own ADR under v6's "no silent stack replacement" rule.

9. **Policy drafts stay unpublished, and their claims are checked against the build.** `PRIVACY_POLICY.md` ([OPERATOR NAME] draft 1.0.0) and the Privacy/TOS/Security PDF ([OPERATOR NAME, variant B]) go to `docs/sources/` (gitignored). They are not rendered anywhere, matching v6 §4 and the existing release gate. `docs/POLICY_CLAIMS_REGISTER.md` lists each promise with its truth in this build. The two drafts name the operator differently, so `legal_operator` stays `null` (release blocker 3).

10. **Geographic aggregation joins as a tested kernel; the feature stays PLANNED.**
    - **Placement:** `app/domains/insights/geo_aggregation.py`.
    - **Fixes:** five disclosure defects (GA-01 to GA-05) were fixed and proven by a randomized attacker test. The received module leaks in 291 of 300 trials; the integrated one in none.
    - **Not wired:** there is no county field and no `geographic_insight` consent purpose, so nothing feeds it.

11. **Legacy prototypes are mined, not merged.** Their features map to owners in `docs/INTEGRATION_LEDGER.md` §10. `main.py` is not adopted, for these reasons:
    - **Passwords:** unsalted SHA-256 hashes.
    - **Sessions:** in-memory tokens that never expire.
    - **Rating math:** its combined rating diverges from 38 CFR 4.25's step-by-step table rounding in 6 of 990 combinations, always 10 points low (e.g. 90/30/10/10 → 90 instead of 100).
    - **Rates:** FY2025 rates presented as current.
    - **Gross-up factor:** an unsourced 1.385 tax "gross-up".
    - **Medical inference:** secondary-condition "suggestions" are prohibited by v6 §5.
    - **AI coach:** it sends rating and pay to a model without consent.

**Consequences.** One migration chain, one deletion path, one error contract, one notice, one test runner. The vault's own defect register (VD01–VD20) stays authoritative in `docs/BENEFIT_VAULT_ARCHITECTURE.md`. Integration adds:

- **VD21 (open decision):** DOES_NOT_MEET_ENCODED_RULES from *unverified* rules hides a record from the default list (counted, not shown). A wrongly encoded rule can therefore hide a real benefit. Options: show non-matches from unverified rules as HUMAN_REVIEW_REQUIRED leads in production, or keep them hidden and show the count with a "see all" control.
- **VD22:** the vault's route handlers are `async` but make blocking libpq calls. That is correct, but concurrent vault requests serialize on the event loop. Fix: run the store calls in the threadpool, as the `/api/v1` handlers do.
