<!-- VetBuddy Financial OS development prompts, Version 4.0, 2026-11-06 (owner-supplied).
     One copy of two uploads: VetBuddy_Financial_OS_CLAUDE_BASE44_PROMPTS_FIXED.docx and .txt carry the
     same text (the .docx adds only this title block). Precedence and conflicts: see the notes at the end. -->

# VetBuddy Financial OS — Claude Code, Base44 and QA prompts

Financial OS is the **MoneyLife Military** module of `docs/PRODUCT_LAYOUT.md` (the Financial layer), not a separate product and not a CRM.

```text
CLAUDE CODE
ROLE: Lead software architect, full-stack engineer, financial rules engineer, accessibility and security lead for VetBuddy Financial OS.

INPUTS: Read VetBuddy_Financial_OS_COMPLETE_SPECIFICATION_FIXED.docx, the working VetBuddy Financial OS HTML, the existing VetBuddy repository, and the legacy Financial OS SDK. Treat code and existing schemas as authoritative for current implementation; treat specification as product requirements. Do not replace VetBuddy with a CRM.

STEP 1 — DISCOVER: Inventory modules, routes, tables, agent boundaries, integrations and tests. Produce a feature-by-feature traceability matrix covering all 56 jurisdictions, military pay, VA, retirement, tax, family, education, relocation, housing, emergency assistance, learning, business and survivor tools. Identify duplicates and unsupported claims.

STEP 2 — REPAIR UI: Open the HTML in a real desktop and mobile browser. Reproduce broken navigation, inputs, calculations, exports and responsive behavior. Fix with real event wiring and deterministic functions. Provide browser test evidence; never claim testing not performed.

STEP 3 — CANONICAL DATA: Implement jurisdiction, benefit, version, eligibility, valuation, legal source, source snapshot, verification approval, household, service history, dependents, property, education, bank consent, account, transaction, scenario, assessment, and audit models. Preserve existing VetBuddy entities via adapters and migrations.

STEP 4 — CALCULATIONS: Version official pay tables and rules. Implement military base pay, OHA, BAH, BAS, COLA, taxes, ETS/PCS, 48-month cash flow, spouse income, VA compensation, disability severance, High-3/BRS, Reserve points, AGR, Chapter 61, CRDP/CRSC, debt, savings, housing, education and state comparison. Clearly distinguish estimates from agency-confirmed awards. Do not count proposed Richard Star Act benefits as current law.

STEP 5 — INTEGRATE: Permissioned interfaces to Benefits Vault, Mission Transition, Claims Navigator, ResourceHub, Learning Academy, state benefits atlas, family navigator, survivor planning, healthcare, entrepreneurship, application tracker and referrals. Scope each agent to necessary facts. Do not duplicate private records.

STEP 6 — SECURITY: Manual entry must work without banking links. Implement optional read-only bank linking only after a real backend, consent, token exchange, revocation, encrypted storage, RLS, deletion and audit are available. Never place API secrets or bank passwords in frontend code. Support veteran/service-member free core access.

STEP 7 — VERIFY: Obtain current official sources, record retrieval/effective dates, legal authority and confidence. Unverified states remain 'verification required'. Implement human approval before consequential rule releases. Treat each of 56 jurisdictions as independent completeness work.

STEP 8 — TEST: Run lint, typecheck, unit, integration, browser E2E, security and accessibility checks. Test married 100% P&T Alabama vs Texas; overseas E-5 OHA ETS; 15-year 50% Chapter 61 case; Guard/AGR and spouse/college cases; unknown fields and unavailable bank provider. Document exact pass/fail results.

DELIVER: changed files, migrations, tests, source registry, outstanding verification queue, architecture diagram, deployment notes and user acceptance checklist. Never assert production readiness without proof. Request approval before destructive migrations or deployments.

BASE44
ROLE: Base44 implementation lead for VetBuddy Financial OS.

SOURCE OF TRUTH: The separate complete specification and existing VetBuddy design. Keep Financial OS a module inside VetBuddy with a reusable standalone-capable domain layer. Do not create a CRM replacement or claim a prototype is production-ready.

BUILD: A responsive, keyboard-accessible application with functional dashboard, role onboarding, household editor, military profile, 56-jurisdiction selector, state comparison, income/tax model, VA and retirement scenario, ETS/PCS/overseas planning, spouse and children, property and college benefit screening, budget, debt, savings, family assistance, application tracking, learning lessons and referrals.

DATA: Use normalized entities for jurisdictions, benefits, source verification, eligibility rules, households, dependents, military service, income, property, education, financial scenarios and calculation history. Include rule status: verified, provisional, stale, missing, agency-confirmed. Do not fabricate rates or state benefits.

FUNCTIONALITY: Every visible button, navigation element, filter, save, export and calculator must have an implemented action. Use manual data entry and local illustrative calculations until secure services are available. Bank-link actions must show 'requires secure backend connection' rather than a fake success.

GOVERNANCE: Connect to VetBuddy Benefits Vault and other agents through scoped references and consent, not copied sensitive documents. Source and effective dates accompany each monetary result. Keep proposed legislation in hypothetical scenarios only.

ACCEPTANCE: Verify all 56 jurisdiction names, Alabama/Texas eligibility screening, overseas E-5 OHA ETS, 15-year medical retirement, spouse income, two-child college planning, Guard/Reserve scenarios, all visible controls, dark mode and mobile layout. Produce a gap report for all unverified jurisdiction data and all unimplemented backend services.

HANDOFF: Export source files and structured schema/API notes for Claude Code and Cursor. Preserve existing VetBuddy application architecture.

QA
REPAIR AND ACCEPTANCE PROMPT

Inspect the actual generated application, do not assume a green build means working functionality. Open desktop and mobile browser sessions. Click every navigation item, submit every form, change each dropdown, run every calculator and verify exported data. Compare displayed outputs against documented deterministic formulas and official effective-dated rules. Test unknown inputs, missing data, large numbers and zero values. Ensure there are no uncaught JavaScript exceptions, broken links, empty panels, false bank connection states, or invented benefit determinations. List each failure with reproduction steps, file/line, fix and retest evidence. Do not mark an untested feature complete.```

## How these prompts sit with the rest of the repository

| Item | Status here |
|---|---|
| Inputs named in the prompt: `VetBuddy_Financial_OS_COMPLETE_SPECIFICATION_FIXED.docx`, "the legacy Financial OS SDK" | `SOURCE_NOT_AVAILABLE`: neither has been uploaded |
| "The working VetBuddy Financial OS HTML" | `VetBuddy_Financial_OS_BROWSER_TESTED.html` (uploaded 2026-11-06); recorded in `docs/INTEGRATION_LEDGER.md` §12, not committed as a page (one author per screen) |
| "56 jurisdictions" | The 50 states, DC and 5 territories: the repo's 57 `jurisdiction` rows minus the federal row |
| Bank linking | Same rule as v6 §3: manual entry only; no aggregator until backend consent, token exchange, revocation, encrypted storage, RLS, deletion and audit exist |
| "Support veteran/service-member free core access" | Consistent with R4 (claims help free) and CLAUDE.md (no pricing work); no paid tier is designed here |
| Base44 prompt | Base44 may prototype screens; code, schema and rules stay in this repo (ADR 0006) |
| Rule statuses "verified, provisional, stale, missing, agency-confirmed" | Map to the repo vocabulary: VERIFIED, UNVERIFIED, SUPERSEDED/`SOURCE_STALE`, `SOURCE_NOT_AVAILABLE`, and an agency decision the veteran records (never computed) |
| Richard Star Act | Proposal only; hypothetical scenarios, never counted as income (matches governance) |
