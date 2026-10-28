# ADR 0006: Product layout — Veteran Operating System, not a CRM

**Status:** Accepted, 2026-10-21 (owner direction: "don't make this a CRM; this is how the app should lay out to prevent conflict"); carried onto the slice 04 base 2026-10-28 (ADR 0007).

## Decision
`docs/PRODUCT_LAYOUT.md` is the governing **product layout**: module names, the workspace tree, the Veteran Master Record, Master Case + subcases, and the layer hierarchy. Case Management is the core; the CRM is the **relationship layer** and never owns the primary data model.

The *VeteranOS Onboarding Multi-Layer CRM Master Prompt* is **not adopted** as a layout. Its privacy-mode resolution and safety-triage-first onboarding remain useful inputs; its CRM-centered framing, OpenAI-specific agents, Stripe/billing, Amplitude and Next.js requirements do not apply.

## Precedence where documents disagree
1. Running code and test results.
2. **Agent Governance Rules** (four non-negotiables, Tier 0 rules, claims legal lane): legal-risk boundaries that win over any layout detail.
3. `docs/VETBUDDY_MASTER_SPEC.md` (master prompt v6) + `CLAUDE.md`.
4. `docs/PRODUCT_LAYOUT.md` (product layout and phasing).

## Specific conflicts and how they are resolved

| Layout item | Conflicts with | Resolution |
|---|---|---|
| §11 Forms Agent "prefill permitted fields" | Governance R3 / T0-04: never prepare, sign or submit 21-526EZ, 21-0966, 21-22 or a decision review | Forms Agent identifies forms, explains requirements and builds checklists. **No prefill of claim, ITF, POA or decision-review forms.** Prefill of non-claim forms (e.g. 10-10EZ) only after the claims-lane legal opinion. |
| §14 "Confidence: 92%" example | v6: provenance, not a guessed score; T0-01 | Show source, authority, date, verification status and which facts were used. A number appears only if computed deterministically (e.g. criteria met / criteria total); never model-estimated. |
| §18 "confirmed eligibility … likely not eligible" | v6 outcome vocabulary; R7 / T0-07 (unknown is never "no") | Use the v6 words only: `PRELIMINARY_MATCH`, `NEEDS_INFORMATION`, `NEEDS_EVIDENCE`, `DOES_NOT_MEET_ENCODED_RULES`, `SOURCE_STALE`, `CONFLICTING_AUTHORITY`, `HUMAN_REVIEW_REQUIRED`. "Confirmed" is reserved for an agency decision the veteran has recorded, never a VetBuddy computation. |
| §9 "Explain my VA decision" | Governance §5 (CFR is a reference, not an assessment) | Plain-language explanation of what the letter says and the review options and deadlines it triggers; ends with the VSO referral block. Never re-rates, second-guesses the percentage, or suggests what to claim. |
| §56 "Benefits Found 14" | G1 (no rule verified) | Counts only verified records; until G1 closes the Benefit Vault shows leads for review, never matches. |
| §59 progress percentages | v6 / master spec §4: no opaque readiness score | Per-area progress computed from the veteran's own tasks (done / total). No single combined score. |
| §60–61 Base44-first, Base44 Development Copilot | CLAUDE.md: GitHub is code source of truth; Postgres is canonical data | Base44 may prototype screens; canonical code, schema, rules and agent manifests live in this repo. The Copilot is internal developer tooling, never part of the veteran product; deferred. |
| §97 monetization / billing | CLAUDE.md "no sales/pricing"; R4 claims help is free | No billing work now. When designed, every claims-related feature is permanently outside any paid tier. |
| §51 Google / Apple sign-in | Open decision G17 | Stays an owner decision; the identity seam accepts any OIDC provider chosen. |
| §69 "React / Next.js style" | ADR 0002 (runtime stack) | A framework move needs its own ADR. |
| §26 CRM entities "donors, sponsors" | No sales/acquisition work | Relationship records only; no fundraising pipeline features. |

## Where the code sits in the layout (slice 04 base)

| Layout module | In this repo | Status (v6 labels) |
|---|---|---|
| Veteran Case Management | Master Mission, lane cases, tasks (slice 01) | PARTIAL |
| Veteran Master Record | person, household, service record with Guard/Reserve authority | PARTIAL |
| Benefits Center | Benefit Vault: 1,362 sourced records, deterministic matcher in v6 words, leads only | PARTIAL (BLOCKED for matches until G1) |
| Claims Center | claims guide, 4.25 + 4.26 calculator, 737-code reference schedule | PARTIAL (education only) |
| Knowledge Base | `ref` schema reference corpus at `/api/v1/reference/*` | PARTIAL |
| Security Center | forced RLS, consent, hash-chained audit, data export, real account deletion | PARTIAL |
| VetBuddy AI, Orchestrator, agents | vault agent behind governance; no model gateway | PLANNED (G21/G23) |
| Partner CRM | — | PLANNED (relationship layer; after the case core) |
| All other modules | — | PLANNED per layout phases |

## Consequences
New work is named and placed using the layout's module tree. Any feature that would make a contact or organization record the primary object, or route a veteran's case through a CRM pipeline, is out of scope.
