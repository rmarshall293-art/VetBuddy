# Policy claims register

Every promise in the two policy drafts received on 2026-10-27, checked against what this build actually does.
Neither draft is published or rendered anywhere (v6 §4; `ReleaseGates.*`). The originals are kept in
`docs/sources/` (gitignored). This register is how counsel and the owner can see which sentences are true
today, which become true when a feature ships, and which must change.

- **A** = `PRIVACY_POLICY.md`, "[OPERATOR NAME, variant A]", draft 1.0.0, prepared 2026-07-31, six [COUNSEL] markers.
- **B** = `VetBuddy_Privacy_TOS_Security_Policy_Updated.pdf`, "[OPERATOR NAME, variant B]", effective date blank.

The governing wording is still v6 §4 (`privacy_notice_draft` in `config/governance_language.yaml`). Neither
draft supersedes it.

**Verdicts:**
- **TRUE:** holds in this build, with the evidence named.
- **TRUE (vacuous):** holds only because the feature does not exist yet.
- **NOT YET:** depends on a decision or deployment that has not happened.
- **FALSE:** the build contradicts it.
- **CONFLICT:** the two drafts disagree.

| # | Claim | Source | Verdict | Evidence or gap |
|---|---|---|---|---|
| P01 | We never sell your data | A, B | TRUE | `sale_of_personal_information` is a foreclosed consent purpose (0010, immutable); no sale path exists |
| P02 | Not shared with VA, DoD, employers, insurers, brokers or advertisers | A, B | TRUE | no outbound integration exists; `third_party_employment_screening`, `insurance_underwriting` and `third_party_marketing` are foreclosed (0010) |
| P03 | "We never share your data … the only exception is when *you* ask" | A | FALSE as worded | Hosting, database and font providers necessarily process data. Google Fonts already receives every visitor's IP (V6-23). B's list of exceptions (service providers, legal process) is the accurate shape. **CONFLICT** with B |
| P04 | Health answers are never stored | A | TRUE (vacuous) | No wellness or claim-prep flow exists. The vault stores grant *keys*, never values, and never echoes `severe_disability`. VA status (V4) never leaves its agent (vault VD14, manifests) |
| P05 | Your career map (ASVAB, MOS, matches) is stored | A | FALSE | No career map is built (V6-33 PLANNED). The skeleton's career tables are unused |
| P06 | We keep county-level location counts | A | FALSE | No county is stored. `insights/geo_aggregation.py` is a tested kernel with nothing feeding it; there is no `geographic_insight` consent purpose |
| P07 | Disability rating never touches career matching; a guard scans inputs; no join exists | A | TRUE (vacuous) / PARTIAL | `disability_based_occupation_filtering` is foreclosed (0010). The input-scanning guard (`consent_enforcement.py`) was not supplied (SOURCE_NOT_AVAILABLE); CB-01/02 ADA metamorphic test is still required before career matching |
| P08 | Account tied to an opaque random id, not name, email or DoD ID | A | PARTIAL | Ids are UUIDs. `app_user.email` and `person_profile.display_name` columns exist (optional; dev sign-up stores neither). G17 decides what identity data is collected |
| P09 | Name, SSN, DoD ID and DOB never collected | A | PARTIAL | No SSN, DoD ID or DOB field is collected. An optional display name is |
| P10 | Precise location never collected | A | TRUE | Jurisdiction is the finest location stored (`person_profile.state_territory`) |
| P11 | Download my data, machine-readable and complete | A, B | TRUE | `GET /api/v1/me/export`; `Export.*`; vault rows included (`test_account_rows_are_tenant_scoped_and_exported`) |
| P12 | Correct anything wrong; edit any field | A, B | PARTIAL | Privacy mode, consents and task status are editable. Profile and service record editing is not built |
| P13 | Delete cascades through every table immediately; no 30-day shadow copy | A | TRUE for the database / NOT YET for backups | `vb_delete_account`; every tenant table including the vault's (0014 postcondition). Backups and processors are V6-21 PLANNED |
| P14 | Data destroyed "within a reasonable retention period" after deactivation | B | **CONFLICT** with A (immediate) | The build purges immediately. B's retention language needs the retention schedule v6 §3 asks for |
| P15 | Opt out of automated career matching | A | TRUE (vacuous) | No career matching exists |
| P16 | Opt out of geographic aggregation; consent defaults off | A | TRUE (vacuous) | Nothing aggregates. Any future purpose must default off |
| P17 | Withdraw any consent; takes effect immediately | A | TRUE | Consent is checked inside every protected transaction; the vault's account routes follow the same rule (`test_withdrawn_consent_turns_account_routes_off`) |
| P18 | All data encrypted in transit and at rest | A, B | NOT YET | Depends on hosting (TLS, disk and backup encryption). Must not be published before deployment evidence exists |
| P19 | Access to production data limited, logged, reviewed | A, B | NOT YET | No production exists. App role is non-owner with forced RLS; audit is append-only |
| P20 | Building toward FedRAMP Moderate / NIST 800-53 alignment | A, B | NOT YET | v8 forbids claiming any certification without independent evidence. "Toward" needs a dated plan |
| P21 | No payment card data held; payments via processor | A | TRUE (vacuous) | No billing (V6-43 DISABLED) |
| P22 | Breaches disclosed honestly; timelines per state law | A, B | NOT YET | [COUNSEL]. Needs the v6 §13 legal applicability register (V6-44) |
| P23 | No users under 18 knowingly | A | NOT YET | No age gate exists. B says under-13 (COPPA): **CONFLICT** on the threshold |
| P24 | Never used to train models | A | TRUE | No model is called anywhere (the vault included); `training_external_models` is foreclosed (0010) |
| P25 | Data analysed to find service gaps and population trends, aggregated or de-identified "to the extent practicable" | B | **CONFLICT** with A | A makes area analysis an opt-in purpose that is off by default. The kernel enforces k = 11 with complementary suppression; nothing is wired |
| P26 | Disclosure when required by law, subpoena or court order | B | Policy decision | `proactive_law_enforcement_disclosure` is foreclosed (0010), which is *proactive* disclosure. Responding to legal process needs counsel's wording |
| P27 | Not a claims representative; no guarantee of outcomes | A, B | TRUE | v6 common notice on every vault response and the guest trust page; VSO referral block; claims-boundary scans |
| P28 | Operator name | A: "[OPERATOR NAME, variant A]"; B: "[OPERATOR NAME, variant B]" | **CONFLICT** | `legal_operator: null` until the owner decides (release blocker 3) |
| P29 | Governing law: Alabama | B | NOT YET | [COUNSEL] |
| P30 | The short pledge "does not keep or share information" | A (appendix) | FALSE as A itself explains | A's precise replacement is accurate in shape. Counsel decides whether executed contracts change |

**What would make a draft publishable** (in addition to v6 §4's own prerequisites):
- remove or condition P03, P05, P06 and P18;
- resolve the conflicts P14, P23, P25 and P28;
- answer the [COUNSEL] markers;
- re-run this register against the build being released.
