# ADR 0003: Product layout — Veteran Operating System, not a CRM

Status: Accepted, 21 Oct 2026 (owner direction: "don't make this a CRM; this is how the app should lay out to prevent conflict")

## Decision
`docs/PRODUCT_LAYOUT.md` is the governing **product layout**: module names, the workspace tree, the Veteran Master Record, Master Case + subcases, and the layer hierarchy. Case Management is the core; the CRM is the **relationship layer** and never owns the primary data model.

The *VeteranOS Onboarding Multi-Layer CRM Master Prompt* (uploaded 21 Oct) is **not adopted** as a layout. Its privacy-mode resolution and safety-triage-first onboarding remain useful inputs; its CRM-centered framing, OpenAI-specific agents, Stripe/billing, Amplitude and Next.js requirements do not apply.

## Precedence where documents disagree
1. Running code and test results (what actually exists).
2. **Agent Governance Rules** (four non-negotiables, Tier 0 rules, claims legal lane) — these are legal-risk boundaries and win over any layout detail.
3. `docs/VETBUDDY_MASTER_SPEC.md` + `CLAUDE.md` (engineering directive).
4. `docs/PRODUCT_LAYOUT.md` (product layout and phasing).

## Specific conflicts and how they are resolved

| Layout item | Conflicts with | Resolution |
|---|---|---|
| §11 Forms Agent "prefill permitted fields" | Governance R3 / T0-04: never prepare, sign or submit 21-526EZ, 21-0966, 21-22 or a decision review | Forms Agent identifies forms, explains requirements and builds checklists. **No prefill of claim, ITF, POA or decision-review forms.** Prefill of non-claim forms (e.g. 10-10EZ) only after the claims-lane legal opinion. |
| §14 "Confidence: 92%" example | Master spec §9: confidence is "provenance and completeness rationale, not guessed numeric score"; T0-01 | Show source, authority, date, verification status and which facts were used. A number appears only if computed deterministically (e.g. criteria met / criteria total); never model-estimated. |
| §18 "confirmed eligibility … likely not eligible" | R7 / T0-07 (unknown is never "no"); master spec status vocabulary | Use `POTENTIALLY_ELIGIBLE`, `NEEDS_INFORMATION`, `REQUIRES_HUMAN_REVIEW`, `UNVERIFIED_OR_STALE`, `NOT_APPLICABLE`, `LIKELY_NOT_ELIGIBLE` (only from a verified rule with all facts known). "Confirmed" is reserved for an agency decision the veteran has recorded, never a VetBuddy computation. |
| §9 "Explain my VA decision" | Governance §5 (CFR is a reference, not an assessment) | Allowed as plain-language explanation of what the letter says and the review options and deadlines it triggers; ends with the VSO referral block. Never re-rates, second-guesses the percentage, or suggests what to claim. |
| §56 "Benefits Found 14" | G1 (no rule verified) | Shows only benefits from VERIFIED rules; until G1 closes the tile reads "Verification required". |
| §59 progress percentages | Master spec §4: no opaque universal readiness score | Per-area progress computed from the veteran's own tasks (done / total), as the readiness view already does. No single combined score. |
| §60–61 Base44-first, Base44 Development Copilot | CLAUDE.md: GitHub is code source of truth; Postgres is canonical data | Base44 may be used to prototype screens; canonical code, schema, rules and agent manifests live in this repo. The Copilot is internal developer tooling (Product Workspace), never part of the veteran product; deferred. |
| §97 monetization / billing | CLAUDE.md "no sales/pricing"; R4 claims help is free | No billing work now. When designed, every claims-related feature is permanently outside any paid tier. |
| §51 Google / Apple sign-in | Open decision G17 (default ID.me + Microsoft) | Stays an owner decision; the sign-in swap point (`auth.verify_token`) accepts any OIDC provider chosen. |
| §69 "React / Next.js style" | ADR 0002 (Vite now) | Compatible: "style" is satisfied by the current Vite app; a framework move needs its own ADR. |
| §26 CRM entities "donors, sponsors" | No sales/acquisition work | Relationship records only (who helps whom); no fundraising pipeline features. |

## Where today's code sits in the layout (Phase 1 subset)

| Layout module | In this repo now | Status |
|---|---|---|
| My VetBuddy / Home | Web `#home`, Mission Brief | PARTIAL |
| Veteran Case Management | `vb.missions` → `vb.master_cases` → `vb.case_lanes` (= subcases) → `vb.tasks` | PARTIAL (no subcase owner/participants yet) |
| Veteran Master Record | Declared routing facts on the mission; `vb.users` | PARTIAL (no profile tables yet) |
| Tasks & Deadlines | Tasks with versioned status; transition windows as unverified reference | PARTIAL |
| Benefits Center | Jurisdiction registry, "verification required" finder | BLOCKED_SOURCE (G1) |
| Claims Center | Claims guide, 4.25/4.26 calculator, 737-code reference schedule | PARTIAL (education only) |
| Knowledge Base | `data/reference/*` served at `/api/v1/reference/*` | PARTIAL |
| Security Center | RLS, consent, hash-chained audit | PARTIAL |
| VetBuddy AI, Orchestrator, agents | — | NOT_PRESENT (G21/G23) |
| Partner CRM | — | DEFERRED (relationship layer; after the case core) |
| All other modules | — | DEFERRED per layout phases |

## Consequences
New work is named and placed using the layout's module tree. Any feature that would make a contact/organization record the primary object, or route a veteran's case through a CRM pipeline, is out of scope. The next slice follows layout §106: Workspace Shell + Veteran Profile + Master Case foundation, built on the existing auth seam, consent and RLS.
