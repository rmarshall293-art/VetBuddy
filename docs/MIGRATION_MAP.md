# Base44 → VetBuddy Migration Map

The Base44 export is `SOURCE_NOT_AVAILABLE`. Nothing here was migrated from Base44 code or data; statuses describe what exists in this repo for each legacy feature named in the blueprint (`docs/VETBUDDY_MASTER_SPEC.md` §11–13). Status vocabulary: `REBUILT`, `MAPPED`, `DEFERRED`, `MISSING_SOURCE`.

## Routes

| Legacy route | Target domain | Status | Where now |
|---|---|---|---|
| `/` Dashboard | Master Case / Command Center | REBUILT (partial) | Web `#home`; API `GET /missions` |
| `/case-overview` | Master Case | REBUILT (partial) | `GET /cases/{id}`, web `#plan` |
| `/coach` Transition Coach | Mission Transition | REBUILT (deterministic part) | Mission Router + brief; no AI coach |
| `/mission-timeline` | Workflow / case plan | REBUILT (tasks only) | `GET /tasks`, `PATCH /tasks/{id}` |
| `/transition-mode` | Personalization | MAPPED | Absorbed into router input (no separate state) |
| `/benefits-match`, `/state-benefits`, `/saved-benefits` | Benefits Center | DEFERRED (G1) | Finder shows verification status only |
| `/benefits-estimator` | Benefits tools | REBUILT (4.25 only) | `POST /ratings/combine`, web `#rating` |
| `/claims-guide` | Claims education | REBUILT | Web `#claims` (VA statuses, windows, legal lane) |
| `/atlas/*`, `/jurisdiction-compare` | Jurisdiction intelligence | REBUILT (registry only) | `GET /jurisdictions` (57, 0 verified) |
| `/profile`, `/settings` | Identity / consent | REBUILT (consent only) | `GET /users/me`, `/consents` |
| `/assistant` VetBuddy AI | Orchestrator | DEFERRED (G21/G23) | — |
| `/claims-tracker`, `/va-forms`, `/document-vault` | Claims / documents | DEFERRED | — |
| `/referrals`, `/vso-directory`, `/accredited-registry`, `/contacts` | ResourceHub / CRM | DEFERRED | Find-a-Rep link only |
| `/careers`, `/career-compass`, `/career-transition-map`, `/business`, `/installation-navigator` | Mission Transition | DEFERRED (ADA test first) | — |
| `/wellness`, `/assessment-referral` | Wellness navigation | DEFERRED | Crisis floor only |
| `/women-veterans`, `/citizenship`, `/insurance` | ResourceHub / knowledge | DEFERRED | — |
| `/community`, `/vsn`, `/training`, `/training-tracker` | Community / Learning | DEFERRED | — |
| `/transition-calculator` | MoneyLife | DEFERRED | — |
| `/admin-*`, `/data-import`, `/atlas/admin`, `/resource-center` | Admin / data governance | DEFERRED | — |
| `/about`, `/privacy`, `/terms`, `/security` | Public pages | MISSING_SOURCE | Need counsel-reviewed text |

## Entities

| Legacy entity | Canonical table(s) here | Status |
|---|---|---|
| User | `vb.users` (IdP subject only) + `vb.consents` | REBUILT (split; no profile fields yet) |
| VeteranCase, TransitionChecklist | `vb.missions`, `vb.master_cases`, `vb.case_lanes`, `vb.tasks` | REBUILT |
| Region, StateBenefit, GuardReserveBenefit | `JURISDICTIONS` registry (code) | MAPPED (no benefit records) |
| All other 34 entities | — | DEFERRED / MISSING_SOURCE |

## Functions and automations

All 10 handlers and 5 automations: `DEFERRED`. The outbox (`vb.outbox`) is the intended trigger point; no worker exists (G19), so nothing can double-fire.
