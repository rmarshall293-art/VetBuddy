# Guard & Reserve Benefit Vault (ADR 0011)

The Guard & Reserve vault is the v8 Guard/Reserve role of Benefits Intelligence. It is built for National Guard, Reserve and AGR members. Its sources are the Benefit Vault registry and the Operation Sentinel dataset. It is governed exactly like the vault: **agents orchestrate, gather and explain; they never decide.**

*Engineering documentation. Not legal advice. Not a government eligibility determination.*

## Files

| Path | What it is |
|---|---|
| `config/guard_reserve_vault_policy.yaml` | Authored policy: selection, questions, derivation table, caveat targets, lead checks, caveats, research gaps, component status |
| `data/reference/guard_reserve.json` | Operation Sentinel dataset (components, duty statuses, authorities, rule leads); unchanged |
| `backend/app/domains/vault/guard_reserve/policy.py` | Loads and cross-checks the policy, the dataset and the vault registry |
| `backend/app/domains/vault/guard_reserve/profile.py` | Answers, classification, derived facts, rule-lead checks |
| `backend/app/domains/vault/guard_reserve/agent.py` | The role over `BenefitVaultAgent` |
| `backend/app/domains/vault/guard_reserve/api.py` | Routes under `/api/v1/vault/guard-reserve` |
| `config/benefit_vault_policy.yaml` | Vault-side manifest `guard_reserve_agent` |
| `backend/app/agents/registry.json`, `database/migrations/0021_guard_reserve_agent.sql` | Platform manifest (DRAFT), with a configuration hash pinned by a test |
| `backend/app/domains/vault/guard_reserve/recovered.py` | Recovered Gemini leads (hash-checked, language-guarded) |
| `data/research/guard_reserve/source_checks.json` | What each opened page said about the report's claims |
| `backend/tests/vault/test_guard_reserve.py` | 75 tests |
| `web/app.js` (`viewGuardReserve`), `tests/e2e/smoke_guard_reserve.py` | The Guard & Reserve Center screen and its browser smoke test |

## Governance placement

```
person ──► guard_reserve_agent (plane 5, manifest: no pull, no decide, exposes nothing)
              │ validates Sentinel answers (V1, never stored)
              │ derives component / service_status / on_active_duty_orders (provenance "derived")
              ▼
           benefits_intelligence_agent ──► broker ──► service_profile_agent …  (person's grant; ledger names the parent)
              │ matcher (v6 outcomes, publish policy, VD21)
              ▼
           lens: Guard & Reserve section first, "also found" after, role caveats, Sentinel lead checks
              ▼
           ClaimsBoundaryGuard ──► OutputGuard (envelope, determination "none", common notice)
```

## Answers (all V1)

| Key | Values |
|---|---|
| `gr_component` | `arng`, `ang`, `usar`, `usafr`, `usnr`, `usmcr`, `cgr` |
| `duty_status` | `selres`, `agr32`, `agr10`, `tech`, `mob`, `sad`, `irr`, `ing`, `retres` |
| `order_authorities` | Sentinel ids `a1`–`a15`, or `unknown` |
| `qualifying_days` | 0–20000 |

Each answer can be marked `unsure`. Validation enforces the Sentinel limits:
- **Guard-only statuses:** AGR Title 32, technician, State Active Duty and ING need a Guard component.
- **Guard-only authorities:** 32 USC 502 authorities apply only to the Guard.
- **Coast Guard only:** 14 USC 3713 applies only to the Coast Guard Reserve.

DoD civilians are out of scope: civilian employment alone creates no Guard or Reserve status.

## Duty status → vault facts

| Status | service_status | on_active_duty_orders | Caveat (on records that read) |
|---|---|---|---|
| Traditional drilling | serving | false | — |
| AGR Title 32 | serving | true | `agr_title32` (orders) |
| AGR Title 10 | serving | true | `agr_full_time` (orders) |
| Dual-status technician | serving | false | `dual_status_technician` (status) |
| Mobilized | serving | true | `mobilized` (orders) |
| State Active Duty | serving | false | `state_active_duty` (orders) |
| IRR, ING | serving | false | `not_selected_reserve` (component) |
| Retired Reserve | retired | false | `retired_reserve` (status) |

## Rule-lead checks

| Lead | Encoded condition | Outcomes |
|---|---|---|
| `gr.ch33` Post-9/11 GI Bill | qualifying days ≥ 90; days with only non-qualifying authorities go to a person | PRELIMINARY_MATCH (HUMAN_REVIEW_REQUIRED in production), DOES_NOT_MEET_ENCODED_RULES (85–89 adds `near_threshold`), NEEDS_INFORMATION, NEEDS_EVIDENCE |
| `gr.ch1606` Selected Reserve GI Bill | Selected Reserve status | as above |
| `gr.fta` Tuition Assistance | Sentinel TA status | as above |
| `gr.rudisill` | contested | CONFLICTING_AUTHORITY |
| `gr.state_definition_trap` | Guard or Reserve with under 181 federal active duty days, or the days unknown | notice (`applies`) |

## Routes

| Method and path | Mode | Purpose |
|---|---|---|
| `GET /api/v1/vault/guard-reserve/catalog` | guest | vocabulary, questions, manifest, selection counts, research gaps, component status |
| `GET /api/v1/vault/guard-reserve/leads` | guest | `gr.*` rule leads and the license reciprocity table |
| `POST /api/v1/vault/guard-reserve/match` | guest or account | `{"guard_reserve": {...}, "facts": {...}, "as_of", "jurisdictions", "categories", "include_other", "note"}` |

## Component status (v6 labels)

| Id | Component | Status |
|---|---|---|
| GR01 | Answers and validation | IMPLEMENTED_TESTED |
| GR02 | Classification and derived facts | IMPLEMENTED_TESTED |
| GR03 | Sentinel rule-lead checks | IMPLEMENTED_TESTED |
| GR04 | Lens over the matcher | IMPLEMENTED_TESTED |
| GR05 | Routes (Mode A) | IMPLEMENTED_TESTED |
| GR06 | Pulls through Benefits Intelligence (Mode B) | PARTIAL (G17) |
| GR07 | Guard, Reserve and AGR records from opened sources | IMPLEMENTED_UNVERIFIED (25 records; awaiting a named reviewer, G1) |
| GR13 | Irreversible-choice caveat | IMPLEMENTED_TESTED |
| GR10 | Recovered Gemini leads | IMPLEMENTED_TESTED |
| GR11 | Guard & Reserve Center screen | IMPLEMENTED_TESTED |
| GR12 | Source-check queue | IMPLEMENTED_TESTED (page reads need approved web access) |
| GR08 | Family members of Guard and Reserve sponsors | PLANNED (VD11) |
| GR09 | Model-written explanations | BLOCKED (G21, G23) |

## Recovered Gemini leads (tier 4, UNVERIFIED)

The owner-supplied Gemini report is kept in `data/research/recovered/gemini_guard_reserve/`, with every file hash-pinned in `RECOVERY_MANIFEST.json`.

| File | What it holds |
|---|---|
| `report.html` | The export, as supplied |
| `jurisdictions_56.json` | The 56-row table, word for word, as generated by `scripts/extract_gemini_guard_reserve.py` (`--check` fails on drift). Each row also carries tags (AGR-specific rule, Title 10/32 split, no state income tax, no National Guard), the language guard's findings, and a cross-check against the vault |
| `federal_leads.json` | GF01–GF15: Chapter 61 and 12731b disability retirement, line of duty, IDES, Gray Area and reduced-age retirement, the points formula, Retired Reserve or discharge, RCSBP, TRICARE Retired Reserve and Reserve Select premiums, AGR retirement, CRSC and CRDP, SSLI, and component rules |

The match returns `recovered_leads`:
- **Jurisdiction rows:** for the Guard state and the state of residence.
- **Federal leads:** those for the person's duty status.

Every lead has no outcome, carries `source_opened: false` and the `recovered_ai_lead` caveat, and names the source the report cites. A cell the language guard flags is withheld.

| Method and path | Mode | Purpose |
|---|---|---|
| `GET /api/v1/vault/guard-reserve/recovered` | guest | all 56 rows, the federal leads, the report's consistency check, and the vault cross-check counts |
| `GET /api/v1/vault/guard-reserve/recovered/{code}` | guest | one jurisdiction |
| `GET /api/v1/vault/guard-reserve/source-queue` | guest | every source the report names, once, in the order to open them (AGR and Gray Area first, then the 11 jurisdictions with AGR-specific rules), with the leads and gaps each one settles; `host_known` says whether the host is already on the vault's allowlist |

## Screen

The web shell has a **Guard & Reserve** page at `#/guard-reserve`, the "Guard & Reserve Center" of `docs/PRODUCT_LAYOUT.md`. It's in the navigation, and the mission brief links to it when the Guard/Reserve lane is open.

| What it asks | What it shows |
|---|---|
| Component, duty status, Guard state, home state, orders authorities, qualifying days | How the answers were read; the Sentinel checks in the v6 words; Guard & Reserve records first, then the others on request; the recovered AI leads under a "Not checked yet" banner, with withheld cells marked |

Browser smoke test: `tests/e2e/smoke_guard_reserve.py`, run by `scripts/test.sh --ui`.

## Source checks (2026-11-21)

Every page the report names has been tried: 81 opened and 2 did not load (tried twice). Three more pages were found by search for AGR health care and retirement, so 84 pages were read in all.

| Result | Count |
|---|---|
| Findings: agrees / agrees in part / differs / source silent | 22 / 60 / 2 / 8 |
| Jurisdiction rows checked | 56 of 56 (14 agree, 41 agree in part, Connecticut corrected) |
| Records written | 25 (21 federal in `federal03_guard_reserve.psv`, 4 state in `batch09_guard_reserve.psv`), Army and Air Force |
| Pages found by search for gaps the report missed | 15 (Army and Air Force AGR, RCSBP enrollment, Iowa revenue, Utah waiver, OPM, VA, commissary, BRS for drilling members, Retired Reserve pay credit, MOAA 2027 premiums) |
| Research gaps with records | 15 of 15 |

**Irreversible choices.** Two records concern a choice that cannot be undone: RCSBP, and the Retired Reserve or discharge choice. Both carry the `irreversible_choice` caveat (v6 HITL level 4). VetBuddy explains and refers, and never recommends an option.
| Named pages still to open | 0 |

**Where the report goes wrong across the states:**
- **Overstated amounts:** "100%" where the page says "up to" or "last dollar."
- **AGR taxation:** "drill/AGR taxed" where the page only says resident military pay is taxed.
- **Leave scope:** leave written as if for every Guard and Reserve member, when it is for state employees.
- **Wrong scope:** a few benefits credited to the wrong group.

The per-page findings are in `data/research/guard_reserve/source_checks.json`. Every lead in the match, the `recovered` route and the screen carries:
- `source_checks`: the verdict and note from each opened page;
- `check_state`: NOT_OPENED, CHECKED or CORRECTED;
- `records`: the records written from its source.

The source queue reports each page as OPENED, FETCH_FAILED or NOT_OPENED.

**What the checks changed.**
- **CRDP (GF13), corrected:** the 50% VA rating requirement was missing from the report.
- **Reduced retirement age (GF06), narrower in the report than in law:** the report left out the rule allowing two consecutive fiscal years after 30 Sep 2014, and that national-emergency 502(f) duty counts.
- **Not confirmed:** Iowa's Title 10 / Title 32 tax split and Utah's AGR exclusion.

## Turning the remaining leads into records

Each remaining lead becomes a record in five steps:

1. Open the page at the top of the source queue.
2. Write a ledger row in `data/research/federal/` or the state ledger, with `OPENED=<date>`, following `data/research/RESEARCH_LOG.md`.
3. Rebuild the registry. The page's host joins the allowlist at this point.
4. Record where the lead agreed or differed in the INTEGRATION_LEDGER.
5. Move the gap from PARTIAL toward IMPLEMENTED once a named reviewer checks it (G1).

## Research gaps (no record until a page is read)

| Id | Topic |
|---|---|
| GRG01 | TRICARE Retired Reserve |
| GRG02 | Non-regular retired pay and reduced retirement age |
| GRG03 | AGR health care |
| GRG04 | AGR active-service retirement |
| GRG05 | Reserve Component Survivor Benefit Plan |
| GRG06 | Retired Reserve ID card and privileges before retired pay |
| GRG07 | Federal civilian military leave |
| GRG08 | Incapacitation pay and line of duty care |
| GRG09 | BRS for Guard and Reserve members |
| GRG10 | VA health care after Title 10 activation |
| GRG11 | Chapter 61 and non-regular disability retirement, IDES |
| GRG12 | CRSC and CRDP for Guard and Reserve retirees |
| GRG13 | State income tax on Title 10 and Title 32 AGR pay |
| GRG14 | State-Sponsored Life Insurance |
| GRG15 | Retired Reserve or discharge after 20 years |

All 15 gaps are IMPLEMENTED_UNVERIFIED: records exist and wait for a named reviewer (G1).

## Run

```
python3 scripts/build_vault_registry.py --check && python3 scripts/build_vault_seed.py --check
scripts/test.sh
```
