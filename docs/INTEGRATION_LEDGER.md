# Integration Ledger

What every supplied input became, what was dropped as a duplicate, and what is still not in hand. Add a row whenever a new input is integrated.

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
- The v2.0 `veteranos` source and datasets (737 diagnostic codes, 2026 rate tables, presumptive conditions, 87 manifests, 10 rule packs).
- The Women Veterans 181-row seed; Education Navigator and Women Veterans runtime source; the Base44 export.

Per the Record's own instruction: recover these rather than re-creating them from memory.
