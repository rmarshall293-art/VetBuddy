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
| `backend/tests/vault/test_guard_reserve.py` | 48 tests |

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
| GR07 | AGR-specific records | SOURCE_NOT_AVAILABLE (gaps GRG01–GRG10) |
| GR08 | Family members of Guard and Reserve sponsors | PLANNED (VD11) |
| GR09 | Model-written explanations | BLOCKED (G21, G23) |

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

The Gemini Guard and Reserve analysis named by the owner was not readable (SOURCE_NOT_AVAILABLE). Its findings go into these gaps once its text is supplied.

## Run

```
python3 scripts/build_vault_registry.py --check && python3 scripts/build_vault_seed.py --check
scripts/test.sh
```
