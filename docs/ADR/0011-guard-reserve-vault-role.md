# ADR 0011: Guard & Reserve Benefit Vault as a role of Benefits Intelligence

**Status:** Accepted, 2026-11-20 (owner request: a Guard and Reserve and AGR-specific benefits vault that plugs into VetBuddy as an agent and follows the existing governance layout)

## Context

- **What was asked.** A Guard, Reserve and AGR-specific benefit vault, built from the existing Benefit Vault and the Guard and Reserve research, plugged into VetBuddy as an agent and aligned with the agent governance profile.
- **What governance already says.** Four pins constrain any new vault agent.
  - **v8 roster (migration 0015, ADR 0006):** Guard/Reserve is a role *inside* Benefits Intelligence, not a separate agent family.
  - **Single puller:** only `benefits_intelligence_agent` may pull facts from other agents. This is pinned by the JSON Schema, the loaders, a database CHECK, a unique index, and tests.
  - **Single runtime source:** the vault registry is the only runtime source of benefit records, and the matcher is the only source of outcomes.
  - **No manifest, no access:** every agent needs a manifest, both in the vault manifest set and in the platform `agent_manifest` table (0005).
- **What exists.**
  - **Sentinel dataset:** `data/reference/guard_reserve.json` (Operation Sentinel, Module 01) holds the components, duty statuses, order authorities and nine rule leads.
  - **Registry:** it already carries 378 Guard and Reserve records (38 federal, 340 state and territory).
  - **Placeholder manifest:** a `guard_reserve_agent` manifest has been NOT_IMPLEMENTED since 0005.
- **What was not available.** Two inputs could not be read:
  - **Gemini analysis:** the shared Gemini Guard and Reserve analysis returned a sign-in page, not the conversation (SOURCE_NOT_AVAILABLE).
  - **Web research:** pages could not be read in this session, so no new benefit record could be sourced.

## Decision

1. **A role, not a second vault.** `guard_reserve_agent` is the Guard/Reserve role of Benefits Intelligence. It runs in process over `BenefitVaultAgent`, using the same registry, reviews, matcher, guards, envelope, grants and broker.
2. **Manifests in both places.**
   - **Vault side:** `config/benefit_vault_policy.yaml` gains the manifest (plane 5, holds up to V2, `may_pull_from_agents: false`, `may_issue_determinations: false`, exposes nothing). The registry and seed are regenerated from it.
   - **Platform side:** `backend/app/agents/registry.json` is realigned with the v8 role.
   - **Migration 0021:** it updates the 0005 `agent_manifest` row to DRAFT and stores a configuration hash. A test fails if that hash drifts from the registry entry.
3. **The person's own terms, V1 only.**
   - **Answers:** the role accepts component, duty status (traditional, AGR Title 32, AGR Title 10, dual-status technician, mobilized, State Active Duty, IRR, ING, Retired Reserve), the authorities on the orders, and qualifying days.
   - **Validation:** answers are checked against the Sentinel vocabulary, for example a Guard-only status on a Reserve component.
   - **Handling:** the answers are not stored, not pulled and not logged.
4. **Derived facts never overwrite answers.** Duty status and component derive the vault's `component`, `service_status` and `on_active_duty_orders` with provenance `derived`. When an answer the person gave disagrees, the answer is kept and the disagreement is reported. A status caveat (for example Title 32 AGR is not Title 10 active duty) is attached only to records whose rule reads the derived fact.
5. **Rule-lead checks restate the lead; they never decide.**
   - **Leads checked:** `gr.ch33` (the 90-day threshold, the 85–89 day warning, and the tier caveat for 12301(h), 12304a and 12304b), `gr.ch1606` and `gr.fta` (Selected Reserve status), and `gr.rudisill` (contested, always CONFLICTING_AUTHORITY).
   - **Notice:** `gr.state_definition_trap` is shown as a notice.
   - **Production rule:** in production an unreviewed lead never shows as PRELIMINARY_MATCH, the same as vault records.
   - **Not evaluated:** `gr.naturalization` needs facts VetBuddy never collects, so it is not evaluated.
6. **The lens hides nothing.**
   - **Same results:** every record the matcher returns is shown, with the same counts as a plain vault match.
   - **Sections:** Guard and Reserve records come first. Everything else follows under "also found" (owner decision VD21).
7. **AGR gaps are research targets, not records.** Ten Guard, Reserve and AGR topics have no record yet. Each one is listed as SOURCE_NOT_AVAILABLE until its page is read. The topics include TRICARE Retired Reserve, non-regular retired pay, AGR health care and retirement, RCSBP, gray-area privileges, federal civilian military leave and BRS.

## Consequences

- **Pulls:** these run only through the parent agent. The pull ledger names `benefits_intelligence_agent` as the requester, and the role asks only for the facts its own answers did not already supply.
- **Routes:** `GET /api/v1/vault/guard-reserve/catalog`, `GET /leads` and `POST /match`. All are Mode A safe. Mode B shares the vault's session rules.
- **Registry identity:** the registry's records are unchanged (still 1,362), but its hash changes because a manifest was added.
- **Tests:** 48 new tests in `backend/tests/vault/test_guard_reserve.py`.
- **Open items:**
  - **Family members:** family members of Guard and Reserve sponsors are PLANNED (VD11).
  - **AGR records:** these wait on research (GR07).
  - **Gemini analysis:** it should be folded in once its text is supplied.

## Addendum (2026-11-20): the Gemini report

**What arrived.** The owner supplied the Gemini analysis as an HTML export. Its disposition is recorded in `docs/INTEGRATION_LEDGER.md`, under "Guard & Reserve inputs".

**Decision.** The report is an AI-written secondary source. VetBuddy has not opened the sources it names, so it enters the way every other recovered input has entered:
- **Hash-pinned:** it is listed in `RECOVERY_MANIFEST.json`, with three files. A changed byte refuses to load.
- **Tier 4 and UNVERIFIED:** every row carries the `recovered_ai_lead` caveat and `source_opened: false`.
- **Leads only:** it never becomes a record, an outcome or a match input. The match counts are unchanged.
- **Language-guarded:** a flagged cell is withheld, not reworded.
- **Deadlines and elections stay questions:** the RCSBP 90-day window, the line-of-duty time limit, and the choice between the Retired Reserve and a discharge are shown as questions to bring to the named office. Two of these are irreversible elections (HITL level 4).

**What changes.**
- **Match payload:** the match now returns `recovered_leads`. These are the rows for the person's Guard state and state of residence, plus the federal leads for their duty status. For example, an AGR member sees AGR retirement but not Gray Area retirement.
- **New routes:** `GET /api/v1/vault/guard-reserve/recovered` and `/recovered/{code}`.
- **Research gaps:** the ten gaps become fifteen. Eleven are now PARTIAL, because a recovered lead names a source to read.
- **New component GR10:** recovered leads are IMPLEMENTED_TESTED.

**What stays open.**
- **GR07, AGR-specific records:** still PARTIAL until someone reads the named pages and writes ledger rows.
- **No calculators from this report:** the reduced-age retirement rule and the points formula are not built as calculators. The summary leaves out how qualifying days are grouped by fiscal year.

## Addendum (2026-11-20, later): screen and source queue

- **Screen.** The role has a screen: the Guard & Reserve Center at `#/guard-reserve`, in the web shell's navigation. The mission brief links to it when the Guard/Reserve lane is open. Recovered leads sit under a "Not checked yet" banner, apart from the outcomes.
- **Source queue.** `GET /source-queue` plans the reads of all 83 named sources, AGR and Gray Area first. The reads were attempted this session, but the page-fetch approvals timed out, so no source was opened and no record was added. The queue is where the next research session starts.

## Addendum (2026-11-21): sources opened

- **Pages read.** With page reads approved, 34 pages were read: 31 from the queue, plus 3 found by search for the AGR gaps. Two named pages did not load.
- **Records written.** 15 records were written:
  - TRICARE Retired Reserve, and TRICARE Prime and Select at 60.
  - Reserve retired pay, the reduced retirement age, and the 15-year letter.
  - Chapter 61 disability retired pay and severance pay.
  - CRSC and CRDP.
  - RCSBP.
  - Army AGR retirement, BRS retired pay for AGR, and TRICARE Prime on full-time duty.
  - Michigan Guard pay exemption, and the South Carolina AGR 39-day exemption.
- **Gaps.** GRG01–GRG04, GRG11 and GRG12 are now IMPLEMENTED_UNVERIFIED: records exist, but no named reviewer has checked them yet.
- **Lead annotations.** Each recovered lead now carries `source_checks` (verdict and note per opened page), `check_state` (NOT_OPENED, CHECKED or CORRECTED) and the records written from its source. The Guard & Reserve Center shows these on every lead card.

## Addendum (2026-11-21, later): queue finished

- **Queue status.** All 83 named sources have been tried: 81 opened and 2 failed (twice). The queue shows 0 NOT_OPENED.
- **Jurisdiction rows.** All 56 rows now carry a check. Connecticut is marked CORRECTED.
- **New record and gaps.** The line of duty record (AR 600-8-4) moves GRG08 to IMPLEMENTED_UNVERIFIED. GRG14 points to the 26 state SSLI records the vault already held.
- **Still open:**
  - The RCSBP election details (GRG05) and TRICARE 2027 premiums.
  - Air Force AGR and Air Guard pages.
  - Iowa's and Utah's AGR tax rules (GRG13). The pages read don't address them.
  - A named reviewer for every record (G1).

## Addendum (2026-11-21, third pass)

**Records.** Seven more records were written, 23 in all:
- Air Guard and Air Force Reserve AGR retirement.
- Air Guard BRS.
- Air Guard TRICARE Prime.
- Iowa's Title 10 / Title 32 pay rule.
- Utah's waiver with its AGR exclusion.
- Federal civilian military leave.
- VA health care after federal activation.

**RCSBP.** The record now carries the sourced 90-day election window.

**Gaps.** 13 of 15 gaps are IMPLEMENTED_UNVERIFIED. Two remain PARTIAL:
- GRG09: BRS for drilling members.
- GRG15: the choice between the Retired Reserve and a discharge (an irreversible decision; HITL level 4).

## Addendum (2026-11-21, final pass)

- **Gaps closed:** GRG09 (BRS for drilling members) and GRG15 (Retired Reserve or discharge) now have records, so all 15 gaps are IMPLEMENTED_UNVERIFIED.
- **Irreversible choices:** the policy lists them (`irreversible_choices`). Those records carry the `irreversible_choice` caveat: VetBuddy explains and refers, and never recommends (v6 HITL level 4).
- **TRICARE 2027 premiums:** confirmed only by MOAA, so they are recorded as a source check, not written into records.
- **Remaining, outside research:** a named reviewer for each record (G1), and production sign-in (G17).
