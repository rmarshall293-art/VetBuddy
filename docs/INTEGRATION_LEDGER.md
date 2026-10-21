# Integration Ledger

What every supplied input became, what was dropped as a duplicate, and what is still not in hand. Add a row whenever a new input is integrated.

## 21 Oct 2026 (second batch)

Privacy check first: all 13 uploads and the full git history were scanned for personal VA-decision data (names with claim or file numbers, ratings, dates of birth, SSNs, decision text). **None found.** The only SSN-shaped value in the repository is the synthetic `000-00-0000` a test uses to prove SSNs are refused. The owner's first name appears in planning documents (not committed); the GitHub username appears in repo URLs.

| Input | What it is | Disposition |
|---|---|---|
| `va-rating-app.html` | Self-contained React reference app: 737 diagnostic codes of 38 CFR Part 4 (2020 edition), 2026 pay table, presumptive lists, a calculator | **Partly integrated.** The 737 codes → `data/reference/rating_schedule.json`, all `UNVERIFIED`, the 51 digestive codes `SUPERSEDED` (rule changed 2024-05-19); its symptom→body-system keyword table was **not** imported. Its calculator was **not** used: unrounded floating-point combining disagrees with 38 CFR 4.25 in 31 of 714 rating combinations (always 10 points low, e.g. 30+20+10+10 → 50 instead of 60), and it saves ratings and dependents to `localStorage`. Its 4.26 bilateral idea was rebuilt in the repo kernel with whole-number rounding. Its two different 60% rates went to `conflicts.json`. |
| `va_claims_data.json` | FY2025 "VASRD" catalog: 101 code rows, rates, SMC, evidence, forms, organizations | **Not integrated.** Against the 737-code schedule: 6 codes do not exist (9420, 9999, 8110, 6814, 6848, 6399), about 25 carry another condition's name (e.g. 9421, 9424, 6832), 17 maximum ratings differ (e.g. 6847 sleep apnea 50 vs 100). It maps 339 symptom keywords to diagnostic codes (prohibited, governance §5), coaches claim strategy ("File ITF before gathering evidence… maximizing retroactive compensation"), mislabels 21-4142 as the buddy-statement form, cites 38 U.S.C. 3313 for the PACT Act, omits TDIU's 40% single-disability condition, and lists VBA and Vet Centers as accredited organizations. Its 70% rate went to `conflicts.json` as evidence. |
| `VA_Benefits.html` | Saved copy of codeplatoon.org/va-benefits (a coding bootcamp's marketing page, with Google Analytics, Google Ads and HubSpot trackers and three named alumni) | **Not integrated.** Not a VA source; school-participation claims (GI Bill, VR&E, VET TEC 2.0) need confirmation against VA before any use; kept as a lead for the education module only. |
| `VeteranOS_VetBuddy_Onboarding_MultiLayer_CRM_Master_Prompt.md` | CRM-centered consolidation prompt | **Not adopted** as the layout (owner: "don't make this a CRM"). Superseded by `docs/PRODUCT_LAYOUT.md`; see ADR 0003 for what was kept. |
| Product layout directive (owner, in chat) | VetBuddy Veteran Operating System layout | **Adopted** → `docs/PRODUCT_LAYOUT.md`; conflicts with governance resolved in `docs/ADR/0003-product-layout.md`. |

## 21 Oct 2026

| Input | What it is | Disposition |
|---|---|---|
| `vetbuddy.html` (v1) | Guest app, first version | Already integrated 20 Oct. |
| `VetBuddy-2.html` (v2) | Guest app | **Duplicate of v1** (data and logic identical). Nothing to integrate. |
| `vetbuddy-3.html` (v3) | Guest app: same router and rating kernels; claims guide and "How it's built" read from data; 6 crisis contacts | **Integrated.** Its data became `data/reference/*.json`; its UI replaced the claims and trust views in `frontend/src/main.js`. The generated browser data matches v3 key for key (sources add two governance entries). |
| `VetBuddy-4.html` (v4) | Guest app | **Duplicate of v3** (only the page wrapper differs). |
| `VetBuddy_Integrated_Record-2.html` | Generated project record from a different build lineage | **Partly integrated.** Tier 0 rules, release gates RG-01–10, human-in-the-loop levels, pipeline order → `governance.json`. The 15 contested readings it renders → `conflicts.json`. Not committed as a page: its counts describe a build that is not in this repository (see below). |

### Data now in `data/reference/` (single author; API serves it at `/api/v1/reference/*`, browser copy is generated)

| File | Contents | Status |
|---|---|---|
| `governance.json` | Governing sentence, 4 non-negotiables, required language, legal lane (8), agent rules R1–R22, Tier 0 rules (12), release gates (10), HITL levels (6), pipeline order | Wording from the governance documents; `repo_status` describes this repo |
| `sources.json` | 10 sources (8 from v3, plus the Governance Rules PDF and the Integrated Record) | Listed, not verified |
| `transition_timeline.json` | 12 transition windows, each citing sources and naming the authority to verify against | All `UNVERIFIED`; the validator refuses `VERIFIED` without a named reviewer and date |
| `conflicts.json` | 15 contested subjects with their competing readings | `CONTESTED` (14) / resolved by design (1); per-reading sources `SOURCE_NOT_AVAILABLE` |

### Corrections made on the way in

- **T0-12 (no self-approval):** the Record says Partial; this repo has no approval workflow, so it is `NOT_PRESENT` here.
- **Crisis floor:** grew from 3 to 6 contacts (VA Women Veterans Call Center, National Call Center for Homeless Veterans, DoD Safe Helpline). The three new numbers came from the uploads and must be re-verified against their official pages before release, like the others.

### Claims in the Integrated Record that do NOT describe this repository

114 backend tests, 11 migrations (e.g. "migration 0010", "0009 guard"), an 855-row reference corpus in 17 `ref` tables from 12 JSON datasets, `config/crisis_floor.yaml`, `config/governance_language.yaml`, `docs/record.html`. This repository has its own counts in `docs/CURRENT_STATE_AUDIT.md`. The equivalent closures (CB-03, C-06) are in migrations 0003 and 0006 here.

### Still not in hand (`SOURCE_NOT_AVAILABLE`)

- The 855-row reference corpus itself: women veterans directory (152), compensation (363), state benefits (94), Guard/Reserve authorities (24), Alabama landscape (54), statistics (30), education registry (22), modules (8), and 8 of the 23 conflict rows.
- The v2.0 `veteranos` source and datasets (the 737 diagnostic codes are now in hand from `va-rating-app.html`, 2020 edition; still missing: 2026 rate tables as source data, presumptive conditions, 87 manifests, 10 rule packs).
- The Women Veterans 181-row seed; Education Navigator and Women Veterans runtime source; the Base44 export.

Per the Record's own instruction: recover these rather than re-creating them from memory.
