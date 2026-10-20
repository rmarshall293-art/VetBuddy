<!-- Source: VetBuddy_Claude_Code_Master_Prompt_v5.html (20 Oct 2026), converted to Markdown. Engineering directive only: contains no credentials, PII or runtime prompts. -->

# VETBUDDY — COMPLETE CLAUDE CODE MASTER INTEGRATION & PRODUCTION BUILD DIRECTIVE
**Version:** 5.0 Consolidated, October 20, 2026  
**Use:** Authoritative engineering mission for Claude Code acting *inside the real VetBuddy repository*.  
**Mode:** Audit → preserve → reconcile → design → implement complete vertical slices → test → document → deploy only with authorization.  
**Coverage:** VetBuddy / VeteranOS product decisions, Base44 prototype, prior production-build prompt v4, architecture handoff, security architecture, agent catalog, connected GitHub repository findings, benefits and jurisdiction scope.
> **TO CLAUDE CODE: Read and execute this as the governing project directive. It is a specification, not proof that anything is implemented. Never report a capability as working without inspecting its implementation and running relevant tests. If a referenced artifact is unavailable, report `SOURCE_NOT_AVAILABLE`, continue with the files actually present, and build a safe stub or contract rather than inventing underlying source data.**
## 0. YOUR ROLE, AUTHORITY, AND FINAL GOAL
Act as one coordinated engineering lead with expertise in enterprise architecture, full-stack development, Python/FastAPI, React/TypeScript, PostgreSQL/Supabase, AI-agent orchestration, zero-trust security, VA/veteran-benefits source governance, rule engines, domain-driven design, accessibility, data migration, DevSecOps, observability, test engineering, and production operations.
Build **VetBuddy** as the user-facing application: an AI-powered *Veteran Operating System* for service members, veterans, Guard/Reserve, Coast Guard, families, caregivers, survivors, approved organizations, accredited representatives, and resource counselors. VeteranOS describes the framework; VetBuddy remains the single visible companion. Other historical working names must be reconciled as aliases or domains, not competing products. The CRM is a **contained relationship-management subsystem** attached to the Master Case, **not the architectural center**.
Mission loop:
`Person / Household → Service & Transition Context → Needs → Master Mission → Master Case → Eligibility / Sources / Evidence → Benefits & Resources → Next Best Action → Forms / Applications / Tasks / Deadlines → Authorized Referrals / Submissions → Agency Decisions / Appeals → Outcomes → Re-evaluation`.
The system must answer: **What is my situation? What matters now? What may I qualify for? Why? What is missing? What should I do next? When is it due? What changed? Did the action achieve an outcome?** Do not build independent prototype silos, one-off pages, unrelated calculators, or an array of autonomous bots without an integrated mission loop.
Success requires real database persistence, authorized data access, proven service-to-service and agent-to-service contracts, navigable UI, observable workflows, auditable source evidence, integrated tests, functioning CI, and a reproducible deployment path. A page rendering does not prove a feature works. A compiled application does not prove it is secure. An architecture diagram does not constitute implementation. Never guarantee 100% security or correctness.
## 1. IMPORTANT VERIFIED SOURCE STATE (DO NOT CONFUSE WITH REQUIREMENTS)
**A. Connected GitHub repository inspection (October 20, 2026):** `https://github.com/rmarshall293-art/VetBuddy` on branch `main` (tree SHA `c3d0f9bf43ad6823772569755646e67bc96be9e5` when inspected). At that point it was a **public repository**. The observed tree contained only `.github/workflows/ci.yml`, `.gitignore`, `.gitkeep`, `README.md`, `backend/render.yaml`, `frontend/vercel.json`, and `docs/DEPLOYMENT_CHECKLIST.md`, plus directories. No actual `backend/app`, frontend React application, package manifests, database migrations, tests, source registries, or agents appeared in the observed tree. Re-scan in Claude Code because the repository may change. Do **not** repeat the README's "production-ready baseline" claim without evidence. The README references `docker-compose`, `.env.example`, and `supabase/schema.sql`, which were not observed in that tree. CI references backend `requirements.txt`, frontend `package-lock.json`, and npm build/tests that likewise were not in the observed tree. Treat these as broken/incomplete until verified. `backend/render.yaml` has a legacy `SUPABASE_SERVICE_ROLE_KEY` name: determine key migration without revealing secrets. The repo's public visibility is a security warning: never commit private data, credentials, proprietary unredacted prompts, VA records, or restricted design secrets. Do not change repository visibility without owner approval.
**B. Base44 application blueprint (October 4, 2026):** The separate Base44 prototype was documented as React 18 + Vite SPA, Tailwind, shadcn/ui, TanStack Query, React Router, Recharts, Leaflet, Framer Motion, jsPDF, drag/drop, Base44 entities/functions/automations/auth/integrations/realtime. It documents 47 named route/features, 38 data entities, 10 backend functions, 5 automations, a 56-jurisdiction benefits atlas, and AI assistant behavior. This blueprint is a **feature and intent inventory**, not proof the implementation files were imported into GitHub. Obtain the actual Base44 export/working source and verify it file-by-file.
**C. Forensic audit PDF (October 4, 2026):** The supplied 14-page PDF contains a large HTML/preview shell dump; it is not adequate proof of a complete forensic code audit. Its observations are not authoritative until validated against actual repository files, schemas, tests, and runnable application behavior.
**D. Legacy design artifacts:** Prior `VetBuddy Final Production Build Master Prompt v4.0` (45-page design), `VetBuddy Foundation Architecture Handoff`, `VetBuddy-VeteranOS-Architecture.html`, `VetBuddy-App-Blueprint.pdf`, and `VetBuddy-Forensic-Audit.pdf` are project inputs. If they are checked into or supplied to Claude Code, use them as requirements/provenance, never as evidence of functionality.
**Source precedence:** Running code, actual migrations, verified current external source, and real test results determine observed state; validated security and canonical architecture determine target state; prototype/docs specify intended features; outdated examples are lowest authority. Maintain an explicit discrepancy register.
## 2. HARD RULES: PRESERVE, MIGRATE, NO INTERFERENCE
1. **Inspect before edit.** Enumerate repository directories, dependencies, routes, pages, entities, functions, agent configs, secrets exposure, environment contracts, schema, imports, tests, CI, deployment, logs. Record source path and implementation status for every claimed feature.
2. **Protect user work.** Never delete functional code, database rows, existing screens, source files, datasets, event history, or settings without a documented migration, tests, rollback path, and explicit approval for destructive operations. Create a dedicated migration branch and baseline commit. Do not force-push or touch production infrastructure without permission.
3. **Make one canonical owner per data type.** Identity, Mission/Case, Source/Policy, Benefits, Evidence, Documents, Tasks, Referrals, Communication, Analytics, and Agent Runtime have clear bounded-domain owners. No two agents/services independently overwrite the same authoritative record.
4. **Do not assume export equals runtime.** If no Base44 source or database export is accessible, mark it unavailable, create a mapping and data adapter interface, and request that missing artifact at the appropriate handoff. Do not fabricate migration statistics or source content.
5. **No competing stores of truth.** PostgreSQL/Supabase is the canonical domain datastore. Base44/SQLite/JSON/HTML/Vite prototypes are ingestion/compatibility sources. Maintain raw immutable staging, deduplication, provenance, and idempotent migration crosswalks.
6. **AI explains and assists; deterministic services decide.** Authentication, authorization, consent, rule evaluation, deadlines, privacy routing, safety triage, official record changes, and financial arithmetic must never be finally decided by an LLM.
7. **Zero invented official facts.** Do not invent VA benefits, statutes, rates, rules, filing deadlines, contacts, school participation, accredited status, qualifying service types, tribal eligibility, regional law, education benefits, acceptance of funding, appeal rights, claims status, or government API capabilities.
8. **Software is not an accredited representative.** Claims guidance is educational/organizational unless provided through independently verified accredited/authorized personnel and approved workflows. No false guarantees of ratings, nexus evidence, medical diagnoses, lawyer/VSO status, legal representation, agency filing, or medical/financial/immigration determinations.
9. **Secrets are secret.** Do not place API keys, service secrets, encryption keys, raw identity records, tokens, or passwords in client bundles, code, commits, AI prompts, logs, screenshots, debugging traces, or public artifact exports.
10. **No unrelated commercial work.** Exclude purchase/acquisition, sales/marketing websites, pricing, monetization, billing, valuation, fundraising, investor material, marketplaces, and unrelated white-label expansion. Do not make public marketing pages the central deliverable.
11. **No fake integrations.** Label every external adapter `LIVE`, `SANDBOX`, `MOCK`, `PLANNED`, `INCOMPLETE`, or `DISABLED`. No status `LIVE` without an authenticated integration test, provider permission, monitoring, and representative success/failure traces.
12. **Build incrementally.** A large master prompt is a constitution. Implement and validate one bounded vertical slice at a time, preserving compatibility with existing working Vite/Base44 screens. Select a Next.js migration with an Architecture Decision Record and actual benefit; never silently rewrite the UI.
## 3. PERSONAS, JURISDICTIONS, AND LIFECYCLE
Personas: active-duty service members, transitioning personnel, veterans, Guard, Reserve, Coast Guard/Coast Guard Reserve, retirees, medical separation/IDES/MEB/PEB participants, spouses, dependents, caregivers, survivors/Gold Star families, non-citizen service members/family when appropriate, accredited VSO representatives, case managers, resource officers, transition and education counselors, vetted partners and organization admins. Adults have separable identities; children have guardian-controlled minimum-information records. No automatic sharing just because persons are related.
Jurisdictions: **all 50 U.S. states, Washington D.C., five main inhabited territories (Puerto Rico, Guam, U.S. Virgin Islands, American Samoa, Northern Mariana Islands),** and further supported federal possessions; national/virtual programs, counties/parishes/boroughs, cities/municipalities, tribal jurisdictions/sovereign programs, installations worldwide, overseas resources and U.S. embassies/consulates when relevant. "56-jurisdiction Atlas" is legacy display shorthand: do not let it cap the underlying jurisdiction model or confuse territorial scope. Seed **Alabama** first in depth, but make routing, rules, schemas, map, and APIs jurisdiction-agnostic. Distinguish current residence, legal domicile, prospective destination, duty station, installation, service-record jurisdiction, program-specific residency and school/agency location.
Transition engine: in-service readiness; T-24–12m; T-12–6m; T-180–90d; T-90–30d; T-30d–separation; day 0–30; day 31–90; months 3–12; years 1–2; 2–3; 3–5; ongoing veteran life. Tracks: ETS/EAS, retirement, medical separation/IDES, Guard/Reserve mobilization/demobilization/gray area, PCS/relocation, OCONUS/overseas return, education, employment, federal employment, apprenticeship/credential, entrepreneurship, spouse/family, veteran re-entry. Lifecycle change creates versioned mission proposals/alerts/tasks, not hidden submissions or unilateral decisions.
## 4. USER EXPERIENCE AND CORE NAVIGATION
One visible "Ask VetBuddy" companion, no competing agent chat interfaces. Main user experience: **My Mission Brief** (situation, goals, top verified opportunities, blockers, first five actions), **Today / This Week**, **Next Best Action**, **Master Case**, **Transition Coach**, **Benefits & Resources**, **Document Vault**, **Claims & Evidence**, **Education & Career**, **MoneyLife**, **Family & Status**, **ResourceHub/Referrals**, **VSN/Community** (isolated consent wall), **Learning Academy**, and **Command Center** for authorized organizations. Include "Help Me Now" urgent routing with verified crisis/stability resources, graceful fallback, and appropriate privacy.
Keep onboarding progressive and optional: persona; privacy mode; current service status; transition timing; current/destination geography and duty station; user goals; urgency (now, 7d, 30d, 90d, later); optional household; optional medical/disability/case facts only if necessary; explicit consent; communication/accessibility preferences. Generate deterministic Mission Brief then AI explanation. Transparent readiness dimensions: documents, benefits, claims/evidence, coverage, career, education, financial, housing/relocation, family, and community; no opaque universal "readiness score".
Preserve actual Base44 navigation functionality via route adapter/migration mapping. Every legacy route below must end `KEPT`, `MAPPED`, `REBUILT`, `DEFERRED`, `RETIRED_WITH_REASON`, or `MISSING_SOURCE` with tests and owner. Avoid broken links and blank screens.
## 5. DOMAIN-BOUND ARCHITECTURE: MODULAR MONOLITH FIRST
Implement a modular monolith with clean interfaces and internal eventing before considering microservices. Suggested deployables: Web/PWA application, Python FastAPI domain backend, worker service, optional realtime/messaging service, PostgreSQL/Supabase data infrastructure, and model gateway. Logical domains:
- **Identity/Trust:** users, profiles, tenants/organizations, sessions, devices, MFA/passkeys, roles, attributes, consents, disclosures, delegation, classification, approval, audit.
- **Person/Household/Service:** people, adult and minor relationships, guardianship, service periods, component/branch, orders, occupations (MOS/AFSC/rating/NEC), deployments, installations, discharge/service details with effective dates.
- **Mission & Work OS:** Master Mission, Master Case, subcases, lanes, goals, tasks, milestones, deadlines, appointments, communication, status changes, human reviews, outcome timeline.
- **Source/Benefits/Policy:** sources, legal authorities, programs, eligibility requirements, exceptions, rule versions, source trust cards, deterministic screening, benefit interactions and funding stacking.
- **Geography/Installations:** administrative hierarchy, tribal/overseas representation, geocoding/PostGIS, current/destination and installation context.
- **ResourceHub & referrals:** service directories, program capacities/eligibility, organizations/providers, contacts, closed-loop referral steps, support services, relationship CRM.
- **Documents/Claims/Evidence:** encrypted source files, immutable original, metadata, document versions, extractions (candidate facts), verified facts, evidence links, claims, decisions, deadlines, appeals/review, form drafts.
- **Education & Career:** school/program catalogs, GI Bill/VR&E/other pathways, institution participation status, school policies, credentialing, MOS translator, resume/job flow, applications, accommodation resources, funding stacking.
- **MoneyLife/Coverage:** opt-in budgeting/scenarios, pay transitions, rates with versioned calculations, insurance/coverage, foreign/OCONUS information, required safety disclaimers.
- **Family & specialty:** spouse/dependent/caregiver/survivor, women veterans/SHE Shield, Guard/Reserve, citizenship, recreation, transportation, housing/stability and health-resource navigation.
- **Learning Academy/VSN:** courses/certification, state resource officer training; moderated community and realtime chat, segregated from confidential cases.
- **AI & Operations:** orchestrator, capability manifests, tool broker, model gateway, context packets, source verification, evals, operation/audit metrics, security monitoring, incident/source queues.
Use `/api/v1` versioned schemas with `/api/v2` only when justified, no breaking unversioned changes. Internal events are not shared database write privileges. Extract microservices only when the architecture decision records separate operational owners, trust boundaries, scaling or runtime needs. Avoid distributed transactions and duplicated business rules.
Suggested technical choices, reconcile against actual source and maintenance burden: React + TypeScript web/PWA; **preserve Vite + React initially if actually present**, potentially adopt Next.js by planned migration; accessible shadcn/Tailwind design system; TanStack Query; React Hook Form/Zod. Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL 16+, Supabase Auth/Storage and RLS as appropriate, PostGIS, object storage; pgvector only for authorized retrieval, Redis/workers only when justified. Docker Compose local, GitHub Actions CI, separate development/testing/staging/pilot/production. Later Expo React Native and Tauri clients consume same APIs; no duplicate eligibility engine in mobile.
## 6. TRUST KERNEL / PRIVACY / IDENTITY REQUIREMENTS
A mandatory Trust Kernel / Secure Context Fabric sits between ALL callers (human, API, internal worker, agent, plugin, integration) and protected data/actions. Enforce an actual policy decision and enforcement point, per-request identity, role, tenant, ownership, purpose, consent, classification, session/time, jurisdiction and risk; service-to-service identity; object/field-level authorization; minimum necessary response; audit. Do not assume "logged in" means "authorized to view any record". Implement tenant/household/agent isolation tests.
**Privacy modes:** `A GUEST_ANONYMOUS` (no persistent personal PII, public calculators and research); `B PERSONAL_PRIVATE` (minimum self-managed profile; sensitive uploads optional); `C MANAGED_CASE` (explicit user consent, authorized representative/organization and verified purpose, field/tenant isolation, disclosure records). Mode C feature-flagged until reviewed tests pass. No silent escalation from A/B to C. Consent scope, purpose, parties, allowed data, start/end, revocation, and expiry must be honored at every read/write. On revocation, invalidate derived authorization and halt further sharing; apply lawfully required retention rules.
**Classification:** `V0 PUBLIC`, `V1 INTERNAL`, `V2 PII`, `V3 HIGH_RISK_PII`, `V4 HEALTH_SENSITIVE`, `V5 EXTRA_RESTRICTED` (MST, intimate-partner/domestic violence, particularly sensitive behavioral-health, substance-use/HIV related, and other restricted content). Strongest classification wins. Child data, health and case-community crossing require heightened controls. Never transmit V4/V5 to an AI provider without purpose/authorization, applicable vendor terms, retention controls, and explicit risk review.
Use Auth/OIDC/OAuth PKCE, appropriate MFA/passkeys, short-lived sessions/tokens, secure cookie handling, CSRF and replay mitigations, rate limits, abuse protections and step-up auth for sensitive actions. Supabase tables and storage use RLS/grants: test allow/deny for owner, other user, same/different organization, delegated representative, guardian, worker and admin. Verify views, SECURITY DEFINER functions, RPC, vector searches, storage URLs and server-side secret/service keys do not bypass authorization inadvertently. Never put secret/admin keys in browsers; use current Supabase publishable keys client-side and secret keys server-side according to verified docs. Document HIPAA applicability rather than claiming universal HIPAA compliance, and review other applicable privacy/breach/security obligations based on actual workflow and partners. Data retention, export, incident response, backups, disaster recovery and deletion subject to legal holds.
**Secrets:** managed secret store/KMS, per-environment keys, least privilege, key rotation, no secrets in source, git history, logs, untrusted agent context, HTML or snapshots. Examples of ENV VARIABLE NAMES ONLY: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `VA_API_KEY`, `EMAIL_API_TOKEN`, `ENCRYPTION_KEY_ID`. `*.env.example` must contain placeholders only. Scan history for leaked credentials and require revocation if observed; do not print values to output.
**Runtime approval tiers:** 0 public read; 1 internal organize; 2 user draft/recommend; 3 protected internal record update; 4 external communication/disclosure; 5 high-consequence claims/appeals/agency filing/immigration/legal/medical/financial act. Tier 3+ always passes deterministic authorization; tier 4+ explicit authorized confirmation; tier 5 often requires verified qualified human role. Human review actions must be visible, reversible when possible and auditable.
## 7. SOURCE-GOVERNED BENEFITS & ELIGIBILITY ENGINE
Build the following services, not just an LLM prompt:
`JurisdictionResolver → SourceRegistry + SourceSnapshot → RuleVersionRepository → EligibilityEvaluator → BenefitConflict/StackingEvaluator → RequiredEvidencePlanner → RecommendationRanker → TrustCard → Verified Explanation`.
Canonical benefit fields: ID, official title, jurisdiction ID/scope, responsible administering entity, categories, eligible populations, criteria, exclusions, service types, effective-from/to, verification status, reviewer, authority tier, official URL/ref, timestamp/source hash and version, required documentation, application forms/deadlines, restrictions, interaction/conflict/stacking, source change log, next review. Keep federal law/regulations vs responsible agency source vs accredited supporting records vs secondary discovery clearly ranked; no secondary-only definitive recommendations.
Required structured screening statuses: `POTENTIALLY_ELIGIBLE`, `LIKELY_NOT_ELIGIBLE`, `NEEDS_INFORMATION`, `REQUIRES_HUMAN_REVIEW`, `NOT_APPLICABLE`, `UNVERIFIED_OR_STALE`; an agency determination is never implied. If a rule lacks a verified source/effective date, downgrade to research candidate, not a vetted benefit. Distinguish user-declared facts, extracted unconfirmed documents, verified records, and inferred fields. Do not fill absent facts with guesses. For partial matching, ask only minimum necessary personal questions.
**Source freshness and regulatory patch management:** monitor official agency/statute/form/rate and institution pages via permitted methods; parse/normalize into staging; detect diffs; human-verify consequential changes; sign/version changes; mark dependent outputs `STALE`, re-evaluate relevant rules, and only then notify authorized users. Never auto-publish unverified legal or benefit changes. Track records as VERIFIED, PENDING_REVIEW, STALE, DISPUTED, RETIRED, DISCOVERY_ONLY. Citations/last verified/limitation must accompany material guidance, and source conflict blocks overconfident advice.
**Jurisdiction coverage:** 50 states + DC + territorial, tribal, municipal, overseas and installations. Seed Alabama in detail, build all-jurisdiction schema and a coverage/completeness table by program category. Do not assert comprehensive 56-jurisdiction data until each jurisdiction has verified content and source age. Compare only genuinely comparable, currency/date-aligned facts. Verify institution or employer actually honors a benefit before claiming acceptance.
**Examples of benefits/capabilities to support, not auto-assert as current law:** VA health/claims education, pension/compensation, education (Post-9/11 GI Bill, MGIB, VR&E, transfer rules where qualified), state/territorial programs, property tax and license benefits, Guard/Reserve federal/state component rules, USERRA/transition support, survivor/dependent/caregiver support, burial/cemetery, grants/scholarships, credentialing, housing, jobs, recreation, transportation, naturalization/USCIS pathways. Each must be verified and governed before publishing.
## 8. SHARED CASE GRAPH AND BUSINESS PROCESSES
Persist **Veteran Master Record** + **Master Mission** + **Master Case**; each has immutable IDs and effective-date context. Case sublanes: benefits, claims/evidence, education, careers/employment, financial/coverage, housing/stability, health/wellness resources, family/survivor/caregiver, Guard/Reserve, women veterans, citizenship, local/tribal resources, recreation/transportation, business pathways if selected, community connections. No lane can read another lane's restricted files merely through common case ID.
Typed domain events through transactional outbox/inbox: `PROFILE_COMPLETED`, `TRANSITION_STAGE_CHANGED`, `MISSION_CREATED`, `CASE_CREATED`, `TASK_CREATED`, `TASK_COMPLETED`, `DEADLINE_APPROACHING`, `DOCUMENT_UPLOADED`, `DOCUMENT_CLASSIFIED`, `BENEFIT_MATCH_GENERATED`, `CLAIM_EVENT_ADDED`, `REFERRAL_RECOMMENDED`, `REFERRAL_SENT`, `REFERRAL_ACCEPTED`, `REFERRAL_COMPLETED`, `REFERRAL_STALLED`, `SOURCE_VERIFIED`, `SOURCE_CHANGED`, `SOURCE_STALE`, `CONSENT_UPDATED`, `HUMAN_REVIEW_REQUIRED`, `LIFE_EVENT_RECORDED`, `AGENT_TASK_STARTED`, `AGENT_TASK_COMPLETED`.
Standard event envelope: unique event ID; schema version; tenant; actor/service/agent; aggregate type/id; aggregate version; UTC time; effective time; causation/correlation; idempotency key; classification; purpose/consent reference; trace; payload reference (not raw secrets); retry count. Use outbox DB transaction, at-least-once delivery, idempotent consumers, dedupe, ordering where required, concurrency/optimistic locks, dead-letter/replay with authorization, and versioned schemas. Source changing can trigger recomputation, not unilateral submission. Approvals block external messages and filings.
Workflow examples: new applicant → private onboarding → needs and source-aware mission brief → tasks → verified benefit match → missing document prompt → user-approved referral → partner accept/schedule/complete/feedback → actual outcome. Claim document upload → malware/OCR → extracted *unverified* facts → user review → evidence link → rule/evidence gap → authorized draft. State move → jurisdiction re-evaluation and notification. Consent revoked → access and pending share halted. Every workflow has ownership, retries, timeout, state-machine transitions, audit and failure recovery.
## 9. ONE GOVERNED RUNTIME AI WORKFORCE (NOT 22 AUTONOMOUS CHATBOTS)
**Distinguish Claude Code development subagents from VetBuddy runtime agents.** Claude Code may use parallel code-review/test/security assistants; those are NOT automatically user-facing deployed agents. Runtime is controlled by typed manifests, agent registry, tool broker and trust service. Default architecture is **eight to ten primary bounded runtime agents** plus 22 named specialist capabilities from the prior handoff. Start with essential runtime routes, expand only after evaluation and need.
Primary orchestration profiles: `Mission Commander / VetBuddy Orchestrator`, `Intake / Transition`, `Benefits & Resource Navigation`, `Claims & Evidence`, `Education & Career`, `Financial & Coverage`, `Family / Special Populations`, `Document Intelligence`, `Source Verification / Research Quality`, `Communications / Referral Follow-Up`. Additional specialist capability manifests (including 22 named legacy agents) can be invoked under the primary services.
**Required manifest per agent:** `agent_id`, semver/version/prompt_hash/config_hash, purpose, domain owner, approved model(s), tool allowlist, input JSON schema, output JSON schema, allowed fields/classifications/tenant/purpose, denied fields, context TTL, data retention, source tiers, source-freshness rules, confidence method, autonomy/risk level, human review thresholds, observability, evaluation fixtures, rate limits, failure/circuit behavior, kill switch. **NO MANIFEST → NO TOOL ACCESS.** Agents cannot self-issue permissions, open a database admin connection or invoke arbitrary endpoints.
**Agent communication:** use minimum-necessary, purpose-bound, signed/integrity-checked, expiring `ContextPacket` with `packet_id, transaction_id, tenant_id, pseudonymous_person_id, mission_id, case_id, authorized fields, redacted fields, classification, purpose, consent_ref, policy_version, originating_agent, destination_agent, allowed_actions, prohibited_actions, sources, expiry, audit_id, integrity_hash`. Never pass entire case by default. Shared vector memory, prompt logs, embeddings and agent traces must obey same RLS/classification. Do not use model-generated statements as permission grants or facts without provenance.
**Orchestration pipeline:** user asks → authentication/guest mode → urgency/safety intent classifier (deterministic fallback) → consent/purpose/tenant policy evaluation → fetch minimum permitted data and verified public sources → route approved specialists → enforce each tool invocation and retries → deterministic eligibility/evidence checks → independent source/output QA → surface conflicts/unknowns → compose one response → optional user-reviewed action → append audit/trace. Task fan-out is bounded; avoid cycles, double writes, duplicate notifications, context bloat and cross-agent interference.
**Provider-neutral model gateway:** allow Anthropic, OpenAI (including Responses API/Agents SDK if approved), other vetted providers, and a deterministic mock for tests through the same interface. Do not hardwire the product to Claude Code. Classify provider, risk, contract/data processing, data retention, model/version, costs, timeouts and latency; enforce outbound redaction and denial where no approved data-processing basis exists. Use structured output validation with retries but never allow model output to bypass policy.
**Required standard runtime agent result** (may extend, not weaken):
```json
{
  "schema_version": "vetbuddy.agent-result.v1",
  "agent_id": "<registered ID>",
  "run_id": "<UUID>",
  "mission_id": "<UUID or null>",
  "case_id": "<UUID or null>",
  "status": "SUCCESS|NEEDS_INFORMATION|HUMAN_REVIEW|BLOCKED|ERROR",
  "summary": "string",
  "screening": "POTENTIALLY_ELIGIBLE|LIKELY_NOT_ELIGIBLE|NEEDS_INFORMATION|REQUIRES_HUMAN_REVIEW|NOT_APPLICABLE|UNVERIFIED_OR_STALE|null",
  "facts_used": [{"fact_ref":"string","verification_status":"DECLARED|EXTRACTED_UNCONFIRMED|VERIFIED"}],
  "sources": [{"source_id":"string","url":"string","version":"string","last_verified":"ISO date","authority_tier":1}],
  "next_actions": [{"action_id":"string","type":"DRAFT|TASK|REFERRAL|INFORMATION","approval_required":true}],
  "missing_information": ["string"],
  "limitations": ["string"],
  "confidence_evidence": "provenance and completeness rationale, not guessed numeric score",
  "policy_version": "string",
  "review_status": "NOT_REQUIRED|PENDING|APPROVED|REJECTED",
  "trace_id": "string"
}
```
Expose bounded tools (real permission-enforcing backend functions, not invented calls): `get_authorized_profile`, `resolve_jurisdiction`, `get_case_summary`, `get_transition_stage`, `search_verified_benefits`, `evaluate_eligibility`, `get_source_trust_card`, `get_evidence_requirements`, `classify_document`, `propose_extracted_facts`, `search_vetted_resources`, `draft_case_task`, `draft_referral`, `draft_form`, `request_user_approval`, `get_allowed_deadlines`, `record_review`. Separate read-only and mutating tools. Every tool has request ID, schema, auth context, timeout, idempotency, audit and error contract. The Agent Trust Kernel controls actual execution.
**Agent collision-avoidance contract:** a) source registry alone owns legal/benefit facts; b) eligibility engine owns encoded match statuses; c) documents vault owns original bytes; d) Mission/Case service owns case status; e) Workflow service owns task, reminder and referral transitions; f) communications agent may draft but only approved notification service sends; g) individual specialists never write another specialist's records; h) human-accepted updates produce canonical versioned events; i) conflicting agent output is flagged for reconciliation, never last-write-wins; j) when a specialist fails the user gets safe partial results + traceable error, not a fabricated substitute.
## 10. FULL SPECIALIST AGENT CATALOG AND GOVERNANCE
Preserve the following 22 handoff agents, as independent agents *only where justified* or capability manifests under the primary runtime profiles. Additional specialized capabilities can include education regulatory compliance, VA disability/appeal pathway review, claims form guide, Mission Transition, business/SBDC/Operation Boots to Business (O2O), Resource Officer training, command analytics, Guard/Reserve/Coast Guard, college funding stack, women veterans/SHE Shield, authorized service-organization workflows and source-regulatory monitoring.
1. **VetBuddy Orchestrator** — Routes intent, gathers minimum authorized context, invokes specialist agents, composes response. **Guardrail:** No direct unrestricted writes; no cross-tenant context; consequential actions require workflow authorization.
2. **Intake Agent** — Progressive onboarding, needs assessment, profile completeness, case creation suggestions. **Guardrail:** May propose changes; user confirms sensitive profile facts.
3. **Federal Benefits Agent** — Federal benefits discovery and explanation. **Guardrail:** Uses structured benefit records/sources; does not guarantee eligibility.
4. **State Benefits Agent** — Jurisdiction-specific benefits including Alabama-first and Guard/Reserve rules. **Guardrail:** Must cite jurisdiction/source/version; flags stale/unverified data.
5. **Research Quality Agent** — Checks source authority, freshness, conflicts and citation completeness. **Guardrail:** Can block/flag low-confidence output; cannot invent confidence.
6. **Resource Navigation Agent** — Matches users to organizations, services and referrals. **Guardrail:** Does not expose case data to providers without consent.
7. **Document Agent** — Classifies, extracts, summarizes, links and detects evidence/document gaps. **Guardrail:** Original immutable; extracted facts are proposed until confirmed.
8. **Claims Navigation Agent** — Organizes claim stages, evidence, deadlines and educational explanations. **Guardrail:** No representation, no guaranteed outcome, no silent submission.
9. **Forms Agent** — Identifies forms, prepares drafts, validates completeness. **Guardrail:** Explicit user review before consequential submission.
10. **Appeal & Advocacy Agent** — Explains review/appeal pathways and evidence gaps. **Guardrail:** Escalates to authorized/accredited representation when appropriate.
11. **Legal & Compliance Agent** — Checks high-risk outputs and policy/compliance boundaries. **Guardrail:** Review role; does not become legal counsel.
12. **Career Transition Agent** — MOS/skills translation, resumes, job planning, transition milestones. **Guardrail:** Keep employment recommendations explainable; user controls saved profile data.
13. **Education Agent** — GI Bill/VR&E/education planning and school/credential pathways. **Guardrail:** Uses current authoritative sources and separates institutional claims from verified rules.
14. **Funding Stack Agent** — Combines compatible education/funding options. **Guardrail:** Detects conflicts/duplication; no fabricated funding.
15. **Guard/Reserve Agent** — Component/status-sensitive Guard/Reserve benefit reasoning. **Guardrail:** Requires service-status inputs; distinguishes Title 10/32/state contexts where data supports it.
16. **Women Veterans Agent** — Dedicated resource/benefit navigation for women veterans. **Guardrail:** Privacy-aware and resource-focused; no unnecessary sensitive inference.
17. **Family Benefits Agent** — Spouse/dependent/caregiver/survivor resource navigation. **Guardrail:** Access only authorized family/case data.
18. **Financial Wellness Agent** — Budgeting/financial education and transition planning. **Guardrail:** Educational boundary; no unsupported regulated advice.
19. **Communications Agent** — Drafts case communications and notices. **Guardrail:** External send requires authorized action and channel-safe data.
20. **Scheduling Agent** — Deadlines, reminders, appointments, follow-up tasks. **Guardrail:** Uses workflow permissions; no hidden schedule changes.
21. **Data Analyst Agent** — Operational/case analytics over permitted aggregates. **Guardrail:** Prefer de-identified/aggregate data; tenant boundaries enforced.
22. **Security Agent** — Monitors security events and permission anomalies. **Guardrail:** Advisory/alerting role; privileged actions require admin workflow.
**Additional capabilities and control expectations:** women-veteran agent supports care navigation, MST/sexual violence resources, trauma-aware consent and V5 protection; Guard/Reserve agent distinguishes component, orders, Title 10/Title 32/state authority when official evidence supports it; education agent verifies program eligibility, institutional participation, current tuition/scholarship/certification policies and benefit interactions; financial navigator may model scenarios but never collect bank logins or promise financial outcomes; career agent supports military-to-civilian skill translation, veteran resumes and federal/state job pathways; claims/evidence agents never create false evidence or claim authorized representation; research quality agent can veto publication based on bad sources and stale rules; partner/referral agent cannot disclose service/medical notes by default.
## 11. BASE44 FEATURE PARITY / LEGACY ROUTE MAP
The 2026-10-04 Base44 blueprint recorded these nine sidebar groups and routes, plus guest pages. Reconcile by actual source path, backend entity/handler, user purpose, target domain, target screen, implementation status and test ID. The inventory is not a feature-completion claim.
- **Mission Control / Dashboard** `/` → Master Case / Command Center [KEEP + REWIRE]. Replace aggregate Base44 entity queries with case-centric read models backed by Supabase.
- **Mission Control / Case Overview** `/case-overview` → Master Case [KEEP + ELEVATE]. Make this the canonical Veteran Master Case workspace; claims, referrals, documents, contacts, tasks and next actions become child domains.
- **Mission Control / Transition Coach** `/coach` → Mission Transition [KEEP + REFACTOR]. Move coaching logic behind Orchestrator + Transition Agent; readiness becomes a case plan, not global app state.
- **Mission Control / Benefits Matcher** `/benefits-match` → Benefits Center [KEEP + REFACTOR]. Use structured benefits/rules/sources/eligibility assessments; AI explains results but does not own eligibility rules.
- **Mission Control / Referral Tracker** `/referrals` → ResourceHub / Referrals [KEEP]. Promote Referral to a first-class case-linked workflow with partner CRM relationship records.
- **Mission Control / Transition Mode** `/transition-mode` → Personalization / AI Context [MERGE]. Absorb into user/case context and agent routing; remove as a separate architectural pillar.
- **Mission Control / Mission Timeline** `/mission-timeline` → Workflow / Case Plan [KEEP + REWIRE]. Unify milestones, tasks, reminders, deadlines and case events under workflow/event layer.
- **Mission Control / VetBuddy AI** `/assistant` → Universal AI / Orchestrator [KEEP + ELEVATE]. Make this the single conversational gateway that routes to bounded specialist agents.
- **Mission Control / Community Feed** `/community` → Community / VSN [DEFER CORE]. Preserve code and data model, but keep outside MVP case-management critical path.
- **Mission Control / VSN Chat** `/vsn` → Community / VSN [DEFER CORE]. Preserve realtime channel concept; isolate from case data and sensitive records.
- **Mission Control / Training Module** `/training` → Learning Academy [KEEP + REHOME]. Move curricula and progress tracking into Learning Academy domain.
- **Claims / My Claims** `/claims-tracker` → Claims Center [KEEP + REFACTOR]. Claims become subcases linked to Master Case; evidence, stages, decisions and timeline get normalized tables.
- **Claims / VA Forms Hub** `/va-forms` → Forms / Applications [KEEP + HARDEN]. Retain form wizards as drafts; require explicit user review before consequential submission.
- **Claims / Claims Guide** `/claims-guide` → Knowledge Base / Claims Education [KEEP]. Treat as educational content with source governance and versioning.
- **Claims / VSO Directory** `/vso-directory` → ResourceHub / Partner CRM [KEEP + MERGE]. Represent VSOs as organizations/providers with accreditation and service metadata.
- **Claims / My Contacts** `/contacts` → CRM Relationship Layer [KEEP + REHOME]. Personal contacts remain, but CRM becomes a supporting relationship layer linked to cases/referrals.
- **Claims / Laws & Rights** `/laws` → Knowledge / Regulatory Sources [KEEP + HARDEN]. Store official source, jurisdiction, effective date, verification date and simplified explanation separately.
- **Claims / Accredited Registry** `/accredited-registry` → ResourceHub / Partner CRM [KEEP + MERGE]. Normalize nonprofits/providers/accreditation into organization and resource-provider models.
- **Career & Business / Career Compass** `/career-compass` → Mission Transition [KEEP]. Keep session-first/low-PII design; results can be saved only with explicit user action.
- **Career & Business / Career Engine** `/careers` → Mission Transition [KEEP + AGENTIZE]. Route resume, skill translation and career planning through Career Transition Agent.
- **Career & Business / Transition Map** `/career-transition-map` → Mission Transition / Jurisdictions [KEEP + MERGE]. Reuse jurisdiction data and career resources; separate source data from AI recommendations.
- **Career & Business / Assessment Referral** `/assessment-referral` → ResourceHub / Referrals [KEEP + SAFETY REVIEW]. Route to resources; avoid diagnostic claims and keep sensitive assessment data minimal.
- **Career & Business / Business Launchpad** `/business` → Mission Transition / Entrepreneurship [KEEP LATER]. Preserve as later module linked to career/transition case plan.
- **Career & Business / Installation & TAP** `/installation-navigator` → ResourceHub / Transition [KEEP]. Normalize installations and TAP services as providers/locations/resources.
- **Wellness / Wellness Check-In** `/wellness` → Wellness Navigation [KEEP ISOLATED]. Maintain zero-PII/session-only default; separate from claims and Master Case unless user explicitly saves/authorizes data.
- **Housing & Family / Benefits & Resources** `/state-benefits` → Benefits Center / ResourceHub [KEEP + MERGE]. Unify federal/state benefit browsing with canonical benefits and resources domains.
- **Housing & Family / Citizenship Guide** `/citizenship` → ResourceHub / Knowledge [KEEP]. Treat as sourced resource/knowledge content.
- **Housing & Family / Women Veterans** `/women-veterans` → Women Veterans Center [KEEP + AGENTIZE]. Preserve dedicated experience; add Women Veterans Agent and privacy-aware routing.
- **Guard & Reserve Atlas / Atlas Dashboard** `/atlas` → Guard & Reserve Center [KEEP + ELEVATE]. Make atlas a specialized benefits view over canonical jurisdictions/benefits data.
- **Guard & Reserve Atlas / Browse States** `/atlas/states` → Guard & Reserve Center [KEEP]. Retain 56-jurisdiction browse UX backed by canonical jurisdiction records.
- **Guard & Reserve Atlas / State Detail** `/atlas/state/:abbr` → Guard & Reserve Center [KEEP]. Use benefit sources/rules and verification metadata rather than duplicated page-specific data.
- **Guard & Reserve Atlas / Compare States** `/atlas/compare` → Guard & Reserve Center [KEEP]. Comparison becomes a query/read model over jurisdiction and benefit domains.
- **Guard & Reserve Atlas / Atlas Data Mgmt** `/atlas/admin` → Admin / Data Governance [KEEP + HARDEN]. Move confidence and verification workflows into source governance/admin tools.
- **Jurisdiction Compare / Compare 56 States** `/jurisdiction-compare` → Jurisdiction Intelligence [KEEP + MERGE]. Consolidate Region + GuardReserveBenefit + StateBenefit into canonical jurisdiction/benefit models.
- **Jurisdiction Compare / Resource Center** `/resource-center` → ResourceHub / Data Governance [KEEP + REHOME]. Separate public ResourceHub from admin data-management tooling.
- **My Records / Saved Benefits** `/saved-benefits` → Benefits Center / Case Plan [KEEP + REWIRE]. Saved benefits become veteran-benefit relationships with status, notes, tasks and application links.
- **My Records / Document Vault** `/document-vault` → Documents & Evidence [KEEP + ELEVATE]. Make canonical document/evidence layer with Supabase Storage, metadata, versions, provenance and case links.
- **My Records / Benefits Estimator** `/benefits-estimator` → Benefits Tools [KEEP + VALIDATE]. Keep deterministic calculations separate from AI; add test fixtures and source/version metadata.
- **My Records / Transition Calculator** `/transition-calculator` → MoneyLife / Transition [KEEP LATER]. Preserve calculations; move under transition/financial education boundary.
- **My Records / Insurance & Abroad** `/insurance` → ResourceHub / Knowledge [KEEP]. Treat as sourced educational/resource content.
- **My Records / My Profile** `/profile` → Veteran Master Record [KEEP + SPLIT]. Split User into auth profile, veteran profile, military service records, preferences and consent.
- **My Records / Settings** `/settings` → Identity / Preferences / Consent [KEEP + HARDEN]. Centralize privacy consent, AI preferences, notifications, devices and data-sharing controls.
- **Admin / Readiness Board** `/admin-readiness` → Security / Production Readiness [KEEP + REHOME]. Retain as internal compliance/readiness workspace; do not present checklist completion as certification.
- **Admin / Claims Readiness** `/admin-claims-board` → Case Operations Dashboard [KEEP + REFACTOR]. Use tenant-scoped case analytics and least-privilege access; avoid broad cross-user exposure.
- **Admin / Content CMS** `/admin-cms` → Knowledge / Content Governance [KEEP]. Add source/version/approval fields and separate public copy from authoritative rules.
- **Admin / Data Import** `/data-import` → Data Governance / Import Pipeline [KEEP + HARDEN]. Validate schemas, stage imports, preview diffs, audit changes and reject unsafe bulk writes.
- **Admin / Training Tracker** `/training-tracker` → Learning Academy Admin [KEEP + REHOME]. Normalize progress/enrollment and role-based training administration.
Pay particular attention to `Transition Mode`, `Sarge` voice guides, `FloatingAssistant`, Atlas 56 jurisdiction compare and admin editor, Veterans Support Network's six channels, 8-stage claims stage tracker, VA 21-0966 and 21-526EZ draft guides, veteran career competency assessment, Installation & TAP navigator, Women Veterans center, wellness zero-PII session tools, secure document vault, referral feedback and state resource officer training. Preserve users' navigation intent even if component names change.
## 12. BASE44 ENTITY MIGRATION & CANONICAL SCHEMA
Legacy entities from the blueprint (the existence of a name does not prove every record or schema was exported):
- **User** → auth.users + profiles + veterans + military_service_records + user_preferences [SPLIT]. Do not keep military/service/consent data on one user record.
- **UserClaim** → claims [MIGRATE]. Link every claim to master_case_id/subcase_id and normalize issues/events/decisions.
- **ClaimStage** → claim_stages reference + claim_events [REFINE]. Use reference taxonomy plus event history rather than stage-only state.
- **VSOContact** → contacts + case_contacts + crm_relationships [MIGRATE]. CRM remains relationship layer.
- **SavedBenefit** → veteran_benefits / saved_benefits [MIGRATE]. Add status, source, case link, tasks and application links.
- **VALaw** → knowledge_sources + regulatory_sources [MIGRATE]. Track authority, jurisdiction, effective date, last verified.
- **StateBenefit** → benefits + benefit_rules + benefit_sources [NORMALIZE]. Do not encode eligibility only in prose.
- **Region** → jurisdictions + jurisdiction_metrics [NORMALIZE]. Use canonical jurisdiction IDs and versioned metrics.
- **GuardReserveBenefit** → benefits + audience/component rules [MERGE]. Avoid a parallel benefits universe.
- **AccreditedNonProfit** → organizations + provider_accreditations + resources [NORMALIZE]. Separate organization identity, accreditation and offered resources.
- **StateTrainingProgress** → learning_enrollments + learning_progress [MIGRATE]. Move to Learning Academy.
- **WomenVeteranResource** → resources + audience_tags [MERGE]. Dedicated UX/agent can query canonical resource data.
- **Installation** → resource_providers + provider_locations [NORMALIZE]. Treat installations/TAP offices as provider/location records.
- **PeerSupportForum** → community_forums [PRESERVE/DEFER]. Keep isolated from case data.
- **ForumPost** → community_posts [PRESERVE/DEFER]. Community domain.
- **ForumReply** → community_replies [PRESERVE/DEFER]. Community domain.
- **ForumMembership** → community_memberships [PRESERVE/DEFER]. Community domain.
- **ForumNotification** → notifications [MERGE]. Use central notification service with community event types.
- **VSNMessage** → community_messages [PRESERVE/DEFER]. Realtime community messaging; strict privacy boundary.
- **ReadinessChecklistItem** → compliance_controls + readiness_checks [MIGRATE]. Internal readiness only.
- **LoadTestResult** → performance_test_runs [MIGRATE]. Observability/testing domain.
- **SymptomLog** → ephemeral wellness session or consented wellness record [RESTRICT]. Default to session-only; do not automatically feed claims.
- **Referral** → referrals + referral_events [ELEVATE]. First-class case workflow linked to provider and outcome.
- **BusinessProfile** → entrepreneurship_profiles [PRESERVE LATER]. Mission Transition expansion.
- **CommunityPost** → community_posts [MERGE]. Avoid duplicate post models if possible.
- **CitizenshipResource** → resources + knowledge_sources [MERGE]. Canonical ResourceHub.
- **VaultDocument** → documents + document_versions + document_metadata + evidence_links [ELEVATE]. Supabase Storage object + relational metadata/provenance.
- **RecreationBenefit** → benefits/resources [MERGE]. Canonical benefit/resource taxonomy.
- **VAFormSubmission** → form_drafts + applications + application_steps [REFACTOR]. Explicit review/authorization before submission.
- **InsuranceInfo** → knowledge_sources/resources [MERGE]. Educational content.
- **VeteranCase** → master_cases + subcases [ELEVATE]. This becomes the central domain, not a side entity.
- **VaultNote** → document_notes / case_notes [MERGE]. Use scoped notes with audit trail.
- **TransitionChecklist** → case_plans + tasks + milestones [NORMALIZE]. Workflow/case plan layer.
- **ContentItem** → content_items + knowledge_sources [REFINE]. Add approval, source, version, publish state.
- **TransitionAdvisor** → agent_configs or transition_plan recommendations [REMODEL]. If this is data, separate AI config from generated recommendations.
- **Resource** → resources + resource_providers [ELEVATE]. Canonical ResourceHub model.
- **VSO** → organizations + provider_services + accreditation [NORMALIZE]. Partner CRM / ResourceHub.
- **CareerProfile** → career_profiles + skills + goals [MIGRATE]. Mission Transition domain.
Create a source-to-canonical migration matrix for each, documenting file/entity owner, fields, shared meaning, PII classification, target table, FK, tenant/user ownership, data steward, source authority, effective dates, data quality, duplicates, deleted state, imported count, checksum, backout plan and parity tests. Canonical domains and example tables:
- `trust`: tenants, memberships, users, user_profiles, sessions, devices, consents, delegations, approvals, disclosures, access_policies, audit_events.
- `persons`: persons, person_private, households, family_relationships, guardianships.
- `military`: service_records, service_periods, duty_stations, service_orders, deployments, occupations, training.
- `work`: master_missions, master_cases, case_lanes, case_participants, goals, milestones, tasks, appointments, deadlines, statuses, outcomes, timeline_events.
- `source_intelligence`: jurisdictions, source_records, source_snapshots, legal_authorities, rules, rule_versions, benefits, benefit_program_links, rule_tests, verification_tasks, interaction_rules.
- `resources`: resource_providers, provider_services, contacts, locations, capacities, referrals, referral_events, feedback, CRM_relationships.
- `documents`: documents, secure_document_versions, document_extractions, unconfirmed_facts, evidence_records, evidence_links, access_events.
- `claims`: user_claims, claimed_issues, claim_events, decisions, review_options, appeal_education, form_drafts.
- `education_career`: schools, school_programs, participation_evidence, education_plans, funding_options, funding_combinations, military_skills, resumes, job_matches, applications.
- `money_coverage`: financial_plans, opt_in_scenarios, input_versions, rule_versions, coverage_resources, calc_runs.
- `community_training`: classes, modules, enrollments, course_progress, forum_topics/posts/replies, VSN_messages, moderation_actions.
- `ai_ops`: agent_manifests, agent_runs, tool_invocations, context_packets, prompt_versions, source_evaluations, integration_status, provider_logs, import_batches, outbox/inbox, failure_retries.
Use UUIDs for canonical IDs and preserve legacy IDs in a separate `legacy_id_map`. Treat source date, verification and classification as core fields, not afterthoughts. SQLAlchemy/Alembic and RLS migration with `DROP` privilege restricted. Build minimum schema only for the current vertical slice, not all tables at once. Use PostgreSQL grants plus RLS, versioned schema and idempotent migrators. For app migration: `IMMUTABLE_ORIGINAL → INVENTORY → STAGING → PARSE → NORMALIZE → DEDUP → VERIFY/QUARANTINE → CANONICAL_MAP → LOAD_IDEMPOTENTLY → PARITY_TEST → CUTOVER_FEATURE_FLAG → DEPRECATE_ONLY_AFTER_APPROVAL`.
## 13. BACKEND FUNCTIONS, AUTOMATIONS & OUTBOX PARITY
The Base44 blueprint identifies these serverless Deno handlers and triggers; each must be assigned a canonical FastAPI/worker implementation or a justified retained adapter, with retry/idempotency, permission, consent and tests. No accidental double-trigger from Base44 and the new worker after migration.
- **analyzeEvidenceGaps** → Document/Claims Agent tool [KEEP + GUARD]. Guardrail: Read-only analysis; structured output; source/evidence provenance; human confirmation.
- **analyzeVaultDocument** → Document Agent pipeline [KEEP + ELEVATE]. Guardrail: OCR/extraction/summarization behind queue; never overwrite original; confidence/provenance required.
- **checkVaultDocReminders** → Workflow scheduler [KEEP]. Guardrail: Translate to DEADLINE/DOCUMENT reminder events; idempotent job.
- **createForumNotifications** → Notification service [KEEP LATER]. Guardrail: Community event consumer.
- **generateEvidenceRecommendations** → Claims Navigation Agent tool [KEEP + GUARD]. Guardrail: Recommendations only; no guarantee or automatic claim action.
- **getClaimsReadinessBoard** → Case analytics read model [KEEP + HARDEN]. Guardrail: Tenant-scoped aggregation; no unrestricted cross-user reads.
- **notifyForumActivity** → Notification service [KEEP LATER]. Guardrail: Community domain event consumer.
- **notifyVsnResourceAlert** → ResourceHub → Community event [KEEP LATER]. Guardrail: Publish resource-created event; community subscriber decides channel.
- **referralFeedbackChecker** → Workflow scheduler [KEEP]. Guardrail: Case-linked scheduled follow-up; idempotent and auditable.
- **referralWorkflowEngine** → Referral workflow [KEEP + ELEVATE]. Guardrail: Move from email-centric automation to referral state machine + notifications + audit events.
- **VSN Alert — New State Resource** event: `RESOURCE_CREATED` → Community subscriber [DEFER CORE]
- **VSN Alert — New Accredited Non-Profit** event: `PROVIDER_ACCREDITATION_CREATED` → Community subscriber [DEFER CORE]
- **Referral Created — Partner Notification** event: `REFERRAL_CREATED` → Referral workflow + notification [KEEP]
- **Vault Document Reminders** event: `DOCUMENT_REQUIREMENT_DUE` → Workflow scheduler [KEEP]
- **Referral Feedback Checker** event: `REFERRAL_FOLLOWUP_DUE` → Workflow scheduler [KEEP]
Specific contract tests: document reminder scheduled daily (timezone/consent/idempotency), referral feedback after 48h and hourly scheduler behavior, referral creation partner notifications only with approved permission and valid contact, new resource/provider alert to VSN only public verified content after moderation, forum notification fan-out honoring subscriptions and privacy; no private case notes in any community notification. For scheduled jobs, use durable job IDs, a locking/lease mechanism, dedupe, retries/backoff, dead-letter queue and observable run status. State whether a job is live or mock.
## 14. CLAIMS, FORMS, WELLNESS, EDUCATION, FINANCE & COMMUNITY GUARDRAILS
**Claims & appeals:** education about stages, record organization, deadline calculation only from verified official effective rules, document evidence mapping and drafts; separate *user-provided statements*, *LLM extraction candidates*, and *official claim/agency decisions*. Accreditations must be verified and represented clearly. No unauthorized filing, POA assignment, fabricated symptom/nexus statements, or automatic submission to VA. Human review for all material actions; support complaints/appeals via legitimate authorized channels.
**Health/wellness/Guardian Force:** safety triage and resource guidance only, no diagnosis or AI clinical adjudication, and no silent storage of crisis/mental health/trauma responses. Zero-PII session-only career/wellness tools retain this as default; opt-in medical vault requires separate threat model, retention, disclosures and audit controls. Urgent assistance should present localized resources only if verified for the user’s actual location and current availability where relevant. Keep health data separate from community and ordinary case context.
**Education/Funding Stack:** validate school participation, institutional award policies, military benefit acceptance, term dates, statutory eligibility, combined funding restrictions and deadlines. Evidence-backed possible pathways, explicit conflicts and no fabricated scholarships. Give user educational guidance without pretending to be certifying school official or VA.
**Career/Mission Transition:** skill translation by MOS/AFSC/rating; interactive pathways and assessments; resume/cover-letter/job plan; DOL/O*NET/CareerOneStop sources subject to verification; private session assessment by default; workforce referrals, federal/state eligibility, disability/ADA resource navigation with employment-law limitations.
**MoneyLife Military:** opt-in goals and budgeting, transition cash-flow, VA compensation/pension examples, retirement comparisons and insurance educational resources; versioned source rates/effective dates, calculation golden tests, no assertion of eligibility from raw disability percentages, no lender/investment instructions disguised as regulated advice, no credential harvesting.
**Family/SHE Shield/Guard/Reserve/Citizenship:** service-status and relationship-aware eligibility, guardian consent, women-veteran resource privacy, survivor/caregiver permissions, Guard orders/qualifying Title statuses, USCIS primary sources and approved referrals for immigration questions. Sensitive needs must not be reused by unrelated agents.
**VSN community:** keep forums, posts and chat in separate privacy domain and permission context. Six historical channels: general, basic_needs, transition, housing, employment, mental_health. Anonymous posting must not leak true identity/PII through badge, events, user IDs, metadata, embeddings, moderator interfaces or UI. Moderation rules, abuse reporting and private-resource posting controls before production. Direct case import requires deliberate user action; nothing crawls community into sensitive case records.
**Learning Academy:** training for veterans and authorized state Resource Officers/Post Resource Officers, from Veteran Basics → Claims & Evidence → Advanced Tools; track verified progress/certification, role capabilities and privacy; no accreditation claims unless true.
## 15. PUBLIC API CONTRACTS & INTEGRATION GATEWAY
Typed FastAPI/Pydantic v2 server contracts (`/api/v1`) and OpenAPI: authentication/session, users/me, households/service, onboarding, missions/cases, tasks, deadlines, benefits/jurisdictions/sources/rules, resources/referrals, documents/evidence, claims/forms, education/career, financial scenarios, agents/runs and audit/operations. Required minimum examples:
```text
GET  /api/v1/health/live                    (internal/safe only)
GET  /api/v1/health/ready                   (safe, no credentials)
GET  /api/v1/users/me
POST /api/v1/onboarding/sessions
POST /api/v1/mission-router/evaluate
GET  /api/v1/missions
POST /api/v1/missions
GET  /api/v1/missions/{id}/next-action
GET  /api/v1/cases/{id}
GET  /api/v1/benefits/matches
GET  /api/v1/sources/{id}/trust-card
GET  /api/v1/resources/search
POST /api/v1/referrals/drafts
POST /api/v1/referrals/{id}/request-approval
POST /api/v1/documents
GET  /api/v1/tasks
GET  /api/v1/deadlines
POST /api/v1/agents/runs
GET  /api/v1/agents/runs/{id}
```
Use consistent error contract (code, message, trace ID, retry advice, no secret leakage), request validation, 401/403/404 distinctions without object enumeration, pagination, max sizes, rate limits, idempotency keys, concurrency controls, locale/timezone and effective-date handling. `POST` actions in protected domains require canonical policy verification at route AND service/tool execution boundary. Never use a broad "backend service key" as replacement for end-user authorization. Public/browser RLS access must not grant hidden extra data.
Integration adapters are server-side for official source retrieval, AI providers, VA/DoD APIs *only where available/approved*, state agency data, education/institution data, O*NET/DOL/CareerOneStop, USCIS resource guidance, maps/geocoding, email/SMS/push, secure storage, Login.gov/ID.me/OIDC future pathways. Each adapter lists provider, environment, authentication type, scoped permissions, approved endpoints, retries/backoff/circuit break, rate-limit, freshness, health, error behavior, source provenance and integration status. Do not claim an official VA claims or rating feed exists or is authorized unless provider documentation and test credentials verify it.
## 16. VISIBLE APP ARCHITECTURE AND ACCESSIBILITY
Baseline source blueprint says Vite + React Router / lazy-loading / Query / Tailwind/shadcn. Prior v4 desired Next.js/React TypeScript PWA. Resolve by an ADR: if real Vite export exists and already works, preserve the UI and add typed data adapters; do not rewrite it merely for framework purity. Consider a gradual Next.js migration only after core functionality and tests are green, and when SSR, routing, accessibility, deployment or operational evidence justifies it. Keep module import contracts and design tokens.
UI includes guest public information routes with **privacy Mode A** (no personal persistence), signed-in Mode B shell, verified Mode C provider views. Accessibility WCAG 2.2 AA goal: keyboard navigation, semantic forms/headings, screen readers, large touch targets, contrast, reduced motion, captions/voice controls where relevant, low-bandwidth modes and mobile responsiveness. PWA caches only safe public data unless separately security-reviewed; no case data in localStorage or unencrypted offline storage. Responsive desktop/mobile dashboards, multi-column case timeline, clear citation/source freshness UI, case/permission indicators, safe and visible human approval buttons, progressive disclosures and explicit save actions.
## 17. APPLICATION RELIABILITY, OBSERVABILITY, SECURITY & TESTING
**Operational reliability:** database schema constraints and transactions; workload backpressure; per-tenant quotas; protection against retry storms; idempotent commands; migration rollback; concurrency tests for same case being touched by multiple agents; event ordering tests; task queue visibility; safe degraded mode if model, data source, VA integration, mailer, Redis or map provider fails. User-facing status should truthfully identify unavailable services.
**Observability:** structured logs with PII redaction, trace IDs across UI → API → agent → tool → DB, latency and error dashboards, queue lag, workflow stuck states, referral completion, source freshness, rule coverage, budget/cost per model (no commercial pricing work), agent output validation, security anomalies, auth denials and consent revocations. Separate security audits from model reasoning traces. Avoid exporting protected medical notes into analytics.
**Automated tests:** TypeScript + Python unit; Postgres/Alembic migration; OpenAPI/consumer contract; tenant/RLS allow/deny; role/guardian/delegation/consent revocation; agent JSON schema and tool allowlists; risk tiers; legal sources and stale-source rejection; deterministic eligibility/golden calculators; privacy data leaks; prompt injection in uploaded PDF/web content; XSS/CSRF/SSRF/path traversal/upload malware; idempotency/duplicate notifications; concurrent case updates; event replay/outbox; file storage read URLs; integration sandbox/mock; route parity; accessibility; load/smoke; end-to-end user mission; safe crisis routing and zero-PII session tools. Human/pilot acceptance before production. Generate fixtures using synthetic PII, never real veterans' sensitive information.
**Security frameworks for design/testing (not blanket certification):** NIST zero trust, NIST identity controls, OWASP Web/API/LLM application risks, OAuth security best practices, least privilege, encryption-in-transit/at-rest, DLP, secret scans, dependency/SBOM checks, WAF/DDoS configuration, incident response, backups/restore, breach response, penetration test plan and legal review. Build production readiness evidence; never self-certify HIPAA, FedRAMP, VA accreditation or other compliance without independently verified scope and review.
**Deployment gates:** development → staging (synthetic) → limited pilot → approved production. CI must include format, typecheck, lint, unit, DB migrations, database access tests, agent evals, SAST/dependency/secret scans, build, E2E, smoke, backup and recovery check. No direct production write, provider email blast, organization enrollment, API key rotation, cloud billable resource creation, or data export without explicit authorization.
## 18. DEVELOPMENT TOOLCHAIN / PROJECT STRUCTURE
Ownership: **GitHub** is canonical source control and CI audit; **Supabase** is canonical managed PostgreSQL/Auth/Storage when configured; **Base44** is migration source / visual prototype only; **Cursor** is editor/daily implementation; **Claude Code** performs audit, plans, code/migrations/tests and architecture review; **Codex** can independently review/test the same versioned repo. Do not create competing codebases or allow parallel tools to stomp the same files. Use one branch per scoped feature and CI-based merges; architecture decisions and migration crosswalks in `/docs`.
Suggested structure (modify only after inspection):
```text
VetBuddy/
  CLAUDE.md                         # short always-loaded engineering rules
  README.md
  .github/workflows/ci.yml
  docs/
    VETBUDDY_MASTER_SPEC.md
    ARCHITECTURE.md
    CURRENT_STATE_AUDIT.md
    GAP_MATRIX.md
    MIGRATION_MAP.md
    AGENT_REGISTRY.md
    SECURITY_MODEL.md
    SOURCE_GOVERNANCE.md
    ADR/
    RUNBOOKS/
    FEATURE_ACCEPTANCE.md
  apps/web/                         # or existing frontend/ if retaining Vite
  backend/                          # FastAPI service, modular domains and tools
    app/
      api/v1/
      domains/{trust,persons,military,missions,benefits,resources,documents,claims,education,career,money,community}/
      agents/{orchestrator,manifests,tools,evaluations}/
      infra/{db,messaging,storage,providers,observability}/
    alembic/
    tests/
  supabase/migrations/              # if Supabase-managed RLS policies
  workers/
  packages/contracts/              # generated/openapi TS and Python shared contracts
  packages/design-system/
  data/{raw,staging,seed,verified}/ # no production PII in git
  tests/{integration,e2e,security,agent_eval}/
  scripts/
  docker-compose.yml
  .env.example                       # placeholders only
```
Do not create duplicate packages/DB migrations because this tree is illustrative. Existing working layout outranks directory preferences. Generate `CLAUDE.md` with fewer than ~200 lines of standing rules; keep this full spec in `/docs/VETBUDDY_MASTER_SPEC.md`. Add optional specialized Claude Code audit/security/test subagents and hooks only where supported by current Claude Code docs, and never confuse their implementation with VetBuddy's runtime agents. Hooks may enforce that sensitive files are not touched, and CI must validate regardless of agent instructions.
## 19. EXECUTION PHASES: DO THE WORK, NOT ONLY WRITE A PLAN
Complete each phase with commits/PR-ready diffs and passing tests. Do not dump an unreviewable 1,000-file generated application. Each step lists a measurable acceptance gate and leaves app runnable locally.
**P0 / Preservation & Forensic Inventory:** identify HEAD/branch, root package manifests, service providers, historical branch/source exports, credentials risk, import mappings; create baseline snapshot/branch; produce `CURRENT_STATE_AUDIT.md` and `GAP_MATRIX.md` with IMPLEMENTED / PARTIAL / MOCK / CONFIGURED_NOT_IMPLEMENTED / REFERENCED_DEPENDENCY / MISSING / DEPRECATED, route + entity + function + agent + test inventory; list prerequisites and source gaps. Test current CI or document exact failure. Reconcile public repo with Base44 export.
**P1 / Trusted Skeleton:** implement actual runnable frontend shell (preserve Vite if available), FastAPI backend, health/readiness endpoints, PostgreSQL/Supabase connection, Alembic, auth/identity, test fixture factory, Docker Compose, CI, environment templates, typed errors and health probes. No PII in git. Gate: one-command local app + DB migration + mock E2E works and CI actually builds.
**P2 / Consent & Case Foundation:** privacy Modes A/B/C (C off), person + household + military service + transition context, Master Mission + Master Case, tasks/deadlines, RLS/ABAC/consent/audit; end-to-end anonymous and personal onboarding. Gate: two different test veterans and two organizations cannot access each other's cases; revocation works; task persists.
**P3 / Mission & Transition:** intake, transition lifecycle, deterministic Mission Router, Mission Brief, readiness dimensions, Today/This Week, Next Best Action and timeline. Gate: two personas with different branches/dates/jurisdictions get correctly routed, reproducible deterministic output; no AI required to pass.
**P4 / Source Registry & Benefit Pilot:** normalized jurisdictions, official source snapshots/trust cards, rule-version engine, first Alabama + federal VERIFIED reference dataset, deterministic screener, missing-information path, conflict/stacking, Research Quality agent. Gate: each displayed material recommendation cites an actual verified source and date; stale/unverified benefits blocked; no fake official eligibility.
**P5 / Runtime Agent Minimum Loop:** Orchestrator, Intake, Federal & State Benefits, Research Quality, Resource Navigation and Document Agent with manifests/tool allowlists/context packets, structured output/evals/audits. Gate: query traverses UI → backend → permission → specialist → deterministic matcher/source → composed citation → safe task draft; unauthorized tool calls and cross-tenant context blocked.
**P6 / Document Vault / Claims & Evidence:** secure upload, scan, immutable original, extraction candidates, approval, evidence links, claim milestones and form drafts, secure storage RLS; no filing. Gate: unconfirmed OCR cannot change service history or claim facts; unauthorized download denied; evidence gap produces an auditable task.
**P7 / ResourceHub, CRM & Referrals:** vetted provider registry, CRM as a contained case relationship layer, referral draft/approval, partner communications, accepted/completed/stalled status, 48h followup and verified outcome. Gate: exactly one notification per approved referral, successful closure and feedback; unconsented case details not shared.
**P8 / Education, Career, MoneyLife, Family, Guard, Women, Citizenship, Recreation, Health Resources:** add vertical slices progressively, each reusing identity, source registry, case, documents, tasks and agent tools. Gate: full source, effective-date and privacy tests per domain; no independent case silo.
**P9 / Learning Academy & VSN:** training modules and progress, safe public community, realtime subscriptions, channels, moderation and notification jobs; community-cases privacy wall. Gate: anonymous message content/metadata cannot reveal protected user identity; community agent cannot read private document vault.
**P10 / Admin Operations & PWA:** source update verification queue, security/anomaly reports, RLS-enforced organization dashboards, analytics aggregation, limited PWA safe cache, robust accessibility. Gate: admins see only authorized tenant aggregates; source stale update invalidates dependent recommendation.
**P11 / Launch Engineering:** monitoring, rate limiting, security test, load/restore, backups, audit retention, runbooks, incident response, SBOM/dependency updates, environment separation, integration health dashboards, limited-pilot signoff and production release approval. Gate: all blockers closed with evidence; no unverified claim of compliance or "fully production-ready".
Do not move to a new phase if its **security, data-integrity or cross-tenant gate** fails. Other independent planned work can continue behind disabled flags, but do not expose incomplete high-risk functionality to users. For every phase record PR/commit, changed files, executed commands, passing/failing tests, debt and blockers.
## 20. NON-INTERFERENCE / CONCURRENCY / RUNTIME PROOFS
Add automated integration tests for at least these interactions:
1. Benefits Agent + Education Agent simultaneously ask for a shared verified source: one source version and no divergent eligibility facts.
2. Document extraction proposes incorrect service fact; veteran confirmation is withheld: Master Record remains unchanged.
3. Guard/Reserve specialist changes qualifying service status proposal while federal benefits matcher runs: immutable input snapshot and versioned recomputation, not race-based answer.
4. Referrals Agent and Scheduler both receive `REFERRAL_CREATED`: one approved notification and one 48h follow-up; duplicate event replay does not duplicate messages.
5. Consent for household member revoked during an agent run: downstream request is denied; cached context invalidated; action is not sent.
6. Two tenants and two unrelated veterans have similarly named files: vector/keyword search, signed URLs, API and agent tools never cross boundaries.
7. Source revised or expired while cached recommendation exists: mark stale, remove unjustified 'verified' status and trigger authorized recheck.
8. Model provider fails or replies with invalid JSON: safe fallback and trace; no invented benefit or silent state write.
9. Claims/appeal drafts touch protected field: user review/human approval gate; no autonomous agency filing.
10. Anonymous VSN post + case search: metadata, user IDs, subscriptions and embeddings cannot reveal identity or contaminate private mission context.
11. Pending job and revoked consent: canceled/denied at execution time, not only at enqueue time.
12. User switches Alabama → another jurisdiction: do not copy Alabama-specific criteria into federal or other-state rule; prevent incorrect benefit overlap/stacking.
Deliver a machine-readable test report and an architecture dependency graph showing each module's data owner, APIs, subscribed/published events, allowed agents, risks and integration status.
## 21. REQUIRED FILE OUTPUTS, WORKING CODE, AND REPORT CONTRACT
Create/update the actual source code and these documents where supported by the repository, not merely describe them:
`docs/CURRENT_STATE_AUDIT.md`; `docs/GAP_MATRIX.md`; `docs/ARCHITECTURE.md`; `docs/ADR/*`; `docs/MIGRATION_MAP.md`; `docs/AGENT_REGISTRY.md`; `docs/SECURITY_MODEL.md`; `docs/SOURCE_GOVERNANCE.md`; `docs/INTEGRATIONS_STATUS.md`; `docs/FEATURE_ACCEPTANCE.md`; `docs/RUNBOOKS/`; `docs/RELEASE_READINESS.md`; `CLAUDE.md`; local startup instructions; `.env.example` placeholders; `Dockerfile`/`docker-compose.yml` where appropriate; schema/migrations and Postgres RLS/grants; typed APIs; agent manifests and unit/eval fixtures; test suites; CI pipeline. Create module/service ownership and an end-to-end sequence diagram, plus schema/event/agent/data-flow diagrams as Mermaid or code-as-documentation.
**Every final status response must contain:**
- `Verified current baseline` — observed files/commands/results, not a guess.
- `Completed this execution` — exact code/files changed and tests run.
- `Functional integration proof` — passing E2E contract/trace details.
- `Source/data gaps` — what was not available from Base44/GitHub/exports.
- `Known mocks/inactive features` — no misleading green status.
- `Security and compliance blockers` — RLS, consents, missing approvals, source gaps.
- `Next bounded implementation slice` — concrete files, acceptance tests, dependencies.
For each feature, label **IMPLEMENTED_VERIFIED**, **IMPLEMENTED_UNTESTED**, **PARTIAL**, **MOCK**, **NOT_PRESENT**, **BLOCKED_SOURCE**, or **DEFERRED**. Never call features "fully integrated", "secure", "production-ready" or "complete" without actual measurable and documented evidence. If you cannot access a tool/provider, say so and continue with mock contract/test coverage.
## 22. FIRST CLAUDE CODE EXECUTION (START HERE, WITHOUT DELETING ANYTHING)
At the start of the first coding session:
1. Print current directory, repo remote, branch, HEAD SHA and `git status`; classify whether the workspace is GitHub skeleton, Base44 export, a combined repo, or other. Do not commit credentials or unreviewed private files.
2. Enumerate file tree and actual packages (limit vendor dirs), inspect README, lockfiles, Docker, frontend, backend, Supabase migrations, hooks/agents, provider keys **by variable name only**. Test the existing install/build/tests with captured exit codes; do not pretend absent files work.
3. Compare observed routes/entities/functions/automations to the canonical inventories in this file. Identify missing Base44 source; do not hallucinate it. Summarize all security exposure, particularly a public repo and missing service key boundaries.
4. Create `docs/CURRENT_STATE_AUDIT.md`, `docs/GAP_MATRIX.md`, `docs/MIGRATION_MAP.md`, `docs/ADR/0001-source-of-truth-and-migration.md`, and concise `CLAUDE.md`. Establish agreed trust boundaries and first tests.
5. Build the **first complete vertical slice**, choosing from `Auth → Privacy → Person/Household → Service Record → Progressive Onboarding → Master Mission/Case → Mission Brief/Tasks`. If workspace is skeleton, first scaffold only the minimum real local backend/frontend/database/CI needed to test that slice. Retain Vite if a runnable Base44 export exists; otherwise choose a justified UI starter.
6. Run tests and report actual test results. Make no production changes and do not represent the application as fully complete. At the next turn, continue the highest-priority unfinished work using the stored gap matrix rather than restarting architectural speculation.
**Critical instruction:** Use the comprehensive vision to guide implementation, but work in bounded, testable, non-destructive increments. Where the current repository is insufficient, state the gap and implement a legitimate foundation. Do not invent source records, fabricated production integrations, or unearned test success. Do not solicit sensitive veterans' records or secrets in AI chat. Do not remove source features without migration coverage. Integrate existing components through one canonical contract and preserve verified outcomes.
## 23. SOURCE PROVENANCE AND ARTIFACT INDEX
- Final Production Build Master Prompt v4.0 (September 26, 2026): 45-page architecture, privacy modes A/B/C, V0–V5 data, secure context, lifecycle T-24 to year five, all-jurisdiction mission loop, seven architecture planes, bounded agent workforce and release roadmap.
- Base44 App Blueprint (October 4, 2026): React/Vite inventory, 47 routes/pages, 38 entities, 10 serverless handlers, five automations and six VSN channels.
- Foundation Architecture Handoff (October 4, 2026): 22 agent names and guardrails, migration manifest, twelve migration phases, Base44-to-Supabase canonical redesign.
- Forensic Audit PDF (October 4, 2026): preview/HTML inspection, not adequate as runnable source-code proof.
- VeteranOS Security Architecture HTML (October 7, 2026): trust kernel, source-grounded eligibility, RLS, approved agent tools, secret isolation, API gateway, human approvals and audit.
- Connected VetBuddy GitHub branch `main` (inspected October 20, 2026): minimal public skeleton. This initial observation must be revalidated at execution.
- Official documents to verify at implementation time: Anthropic Claude Code project instructions/features; Supabase RLS and publishable/secret key docs; NIST SP 800-207 and 800-63; OWASP API/LLM guidance; applicable VA, DoD, USCIS, DOL, state and institutional sources.
**END OF GOVERNING MASTER PROMPT.**
---
# APPENDIX A — ORIGINAL BASE44 BLUEPRINT TRANSCRIPT (REFERENCE ONLY)
This appendix preserves the user-supplied blueprint's parsed content. **Treat as feature-documentation; implementation must be verified against actual files.**
VetBuddy
Mission OS — Complete App Blueprint
App layout, features, and code/data flow reference
Generated 10/4/2026
VetBuddy Blueprint  •  Page 1 of 11
1. Platform Overview
VetBuddy is an AI-driven benefits management platform that connects service members and veterans to the federal,
state, and nonprofit benefits they have earned. It centralizes VA claims guidance, a 56-jurisdiction benefits atlas,
career transition tooling, peer support, wellness screening, and administrator readiness into one mission OS.
Technology Stack
React 18 + Vite (SPA), Tailwind CSS + shadcn/ui, lucide-react icons, @tanstack/react-query for server state, react-router-dom for
routing, recharts for charts, react-leaflet for maps, framer-motion for animation, jsPDF for document export, @hello-pangea/dnd for
drag-and-drop. Backend: Base44 BaaS — entities (JSON schemas), backend functions (Deno entry.ts), automations
(scheduled/entity-triggered), and built-in integrations (InvokeLLM, UploadFile, SendEmail, GenerateImage, etc.).
Authentication & Access
Authentication is platform-managed. AuthProvider wraps the app; users join via invite. Guests see a limited public layout (landing,
benefits, VSO directory, laws, careers, AI assistant, legal pages). Authenticated users get the full sidebar Mission OS. Protected
routes fall behind AppLayout.
Architecture
Every page is lazy-loaded via React.lazy + Suspense for fast initial load. The app is organized into src/pages (route screens),
src/components (feature components), src/lib (engines, contexts, data), base44/entities (data schemas), base44/functions
(serverless handlers), and base44/agents (AI agent configs). A centralized color token system in src/index.css feeds
tailwind.config.js.
VetBuddy Blueprint  •  Page 2 of 11
2. Navigation — Task Bars (Sidebar Groups)
The sidebar groups every feature into 9 task bars. Each item below lists its route, label, and how the code works (data sources,
key components, and integrations).
Mission Control
Dashboard  —  /
Central command center pulling active claims, saved benefits, upcoming deadlines, AI recommendations, and quick stats via
React Query. Renders snapshot cards (ActiveClaimsSnapshot, BenefitSuggestionsSnapshot, UpcomingDeadlines,
ClaimsReadinessScore) and quick-action tiles.
Case Overview  —  /case-overview
Aggregates a veteran's full case: claims, referrals, documents, contacts, and next actions into a unified panel
(CaseMissionBanner, CaseNextActions, CaseDocumentPanel, CaseReferralPanel).
Transition Coach  —  /coach
AI transition coach (TransitionCoach) walks users through a guided transition with readiness scoring, eligibility engine, status
dashboard, benefit-expiration alerts, and a duty-station finder.
Benefits Matcher  —  /benefits-match
Filters federal, state, and nonprofit resources by branch, component, and eligibility profile. Generates smart alerts and feeds a
jurisdiction comparison table (BenefitsComparisonTable).
Referral Tracker  —  /referrals
Manages referrals to partners/services. Cards track status, outcomes, follow-ups. A backend engine (referralWorkflowEngine)
emails partners on creation; referralFeedbackChecker prompts feedback 48h post-meeting.
Transition Mode  —  /transition-mode
Toggles an AI-assisted transition state across the app (AIAssistantContext). Drives contextual hints, page voice guides, and the
Sarge walkthrough.
Mission Timeline  —  /mission-timeline
Goal-driven timeline (MilestoneCard, TimelineProgress, GoalSetupPanel, RemindersPanel) with tasks, reminders, and milestone
tracking.
VetBuddy AI  —  /assistant
Full-page AI chat (AssistantChat) with context-aware system prompts, quick topic navigation, crisis resources, and the AI toggle to
enable/disable assistance.
Community Feed  —  /community
Unified feed of moderated community posts (PostCard) plus peer-support forums by condition (ForumCard, ForumDetail). New
posts go through moderation; forum activity triggers notifications.
VSN Chat  —  /vsn
Real-time Veteran Support Network chat across 6 channels (general, basic_needs, transition, housing, employment,
mental_health). Supports anonymous posting, reply threading, branch badges, and live subscriptions. Auto-alerts posted when
new resources/non-profits are added.
Training Module  —  /training
3-level training curriculum (Veteran Basics, Claims & Evidence, Advanced Tools) for state resource officers, tracked via
StateTrainingProgress.
Claims
My Claims  —  /claims-tracker
Tracks VA disability claims through 8 stages (ClaimStage). Manages claims (UserClaim), stage roadmaps, evidence, symptom
analysis (SymptomDCAnalyzer), and a claim timeline with optimistic updates.
VetBuddy Blueprint  •  Page 3 of 11
VA Forms Hub  —  /va-forms
Directory of VA forms (VAFormDirectory) plus step-by-step wizards for 21-0966 (Intent to File) and 21-526EZ (disability
compensation). Saved forms stored in a vault (SavedFormsVault).
Claims Guide  —  /claims-guide
Educational guide to the VA claims process, claim types, evidence requirements, and the 8-stage lifecycle with what-to-do
guidance.
VSO Directory  —  /vso-directory
Searchable directory of Veteran Service Organizations for claims representation and POA assignment.
My Contacts  —  /contacts
Personal CRM for VSO reps, claims agents, and attorneys (VSOContact). Contact cards, add/edit modal, POA flag, and notes.
Laws & Rights  —  /laws
Library of VA-related laws (VALaw) with official + simplified summaries, key provisions, who benefits, and an AI law fetcher for
missing legislation.
Accredited Registry  —  /accredited-registry
Searchable registry of accredited nonprofits (AccreditedNonProfit) by state and accreditation type, showing services, eligibility, and
verification status.
Career & Business
Career Compass  —  /career-compass
Session-based career quiz (CareerCompassQuiz) mapping military skills to civilian career pathways with results
(CareerCompassResults). Zero-PII, session-only storage.
Career Engine  —  /careers
MOS/AFSC/Rating translation, job readiness scoring, career path exploration, AI resume builder (ResumeBuilder), disability/ADA
accommodations (DisabilityAccommodations), and employer resources.
Transition Map  —  /career-transition-map
State selection grid driving state-specific employment resources and Guard/Reserve preferences. Integrates an AI Job Search
Algorithm (filterable by industry/skill, sortable by salary) and a Counselor Prep Strategy checklist.
Assessment Referral  —  /assessment-referral
Routes veterans to appropriate assessments (mental health, vocational, etc.) based on inputs, generating referral
recommendations.
Business Launchpad  —  /business
Veteran entrepreneurship resources: SBA partner programs, SDVOSB certification guidance, business planning tools, and a vet
business guide.
Installation & TAP  —  /installation-navigator
Directory of military installations (Installation) with TAP office contacts, TRICARE, mental health, family support, legal, housing,
MWR, and overseas resources.
Wellness
Wellness Check-In  —  /wellness
Guided wellness screening flow (WellnessCheckInFlow) with crisis bar, results (WellnessResults), and referral routing. Zero-PII
session-only storage with data-driven questions (wellnessData.js).
Housing & Family
Benefits & Resources  —  /state-benefits
Browse federal + state benefits (StateBenefit) by category and region, with eligibility, source links, and save-to-vault actions.
National resources merged in here.
VetBuddy Blueprint  •  Page 4 of 11
Citizenship Guide  —  /citizenship
Naturalization and citizenship resources for service members and families (CitizenshipResource), including military naturalization
pathways.
Women Veterans  —  /women-veterans
Dedicated module surfacing women-veteran-specific resources (WomenVeteranResource) by care type: PTSD, MST, mental
health, parenthood, DV/IPV, housing, childcare, employment, crisis, and state coordinators.
Guard & Reserve Atlas
Atlas Dashboard  —  /atlas
Hub for the Guard/Reserve State Benefits Atlas (GuardReserveBenefit). Summary stats, tax-friendliness distribution, recent
updates, and a colored US state grid (USAMap).
Browse States  —  /atlas/states
Paginated list of all 56 jurisdictions with tax friendliness, education, healthcare, employment, and retirement benefit summaries.
State Detail  —  /atlas/state/:abbr
Deep dive into one state's Guard/Reserve benefits: education, healthcare, death/burial, employment (USERRA), tax, retirement,
and license reciprocity.
Compare States  —  /atlas/compare
Side-by-side comparison of selected states across all benefit categories with a comparison tool.
Atlas Data Mgmt  —  /atlas/admin
Admin editor for Guard/Reserve benefit records (AtlasEditDialog) with confidence tracking and verification dates.
Jurisdiction Compare
Compare 56 States  —  /jurisdiction-compare
Cross-jurisdiction comparison tool (JurisdictionCompareTool) across all 56 states/territories using Region data: cost of living,
housing, unemployment, tax rules, healthcare access, and veteran population.
Resource Center  —  /resource-center
Centralized resource center with jurisdiction data management (JurisdictionDataManager) and detail panels
(JurisdictionDetailPanel).
My Records
Saved Benefits  —  /saved-benefits
Personal saved list of benefits (SavedBenefit) from federal, state, nonprofit, and AI recommendations, with notes and action steps.
Document Vault  —  /document-vault
Secure document storage (VaultDocument) with upload (UploadDocumentModal), AI analysis (analyzeVaultDocument), evidence
gap detection, OCR, VA records requests, VSO sharing, milestone checklists, and vault notes/locks.
Benefits Estimator  —  /benefits-estimator
Calculates combined VA disability ratings (vaClaimsEngine), monthly compensation, TDIU and SMC eligibility, and benefits
continuance projections.
Transition Calculator  —  /transition-calculator
Financial transition planning: pay comparisons, retirement projections, and a transition results panel (TransitionResultsPanel).
Insurance & Abroad  —  /insurance
Insurance info (InsuranceInfo) and overseas/OCONUS coverage guidance including VA Foreign Medical Program.
My Profile  —  /profile
User profile: service details, branch, component, disability rating, and transition status stored on the User entity.
VetBuddy Blueprint  •  Page 5 of 11
Settings  —  /settings
App preferences, notification controls, privacy consent, and AI assistant configuration.
Admin
Readiness Board  —  /admin-readiness
Admin dashboard for security (NIST/OWASP) and legal/contracting readiness checklists (ReadinessChecklistItem), performance
benchmarks (LoadTestResult), and jurisdiction data panels. Admin-gated.
Claims Readiness  —  /admin-claims-board
Cross-user claims readiness board backed by getClaimsReadinessBoard backend function, surfacing claim progress and
evidence gaps across the org.
Content CMS  —  /admin-cms
Content management (ContentItem) for editing benefit text, resources, and static content with a modal editor (ContentItemModal).
Data Import  —  /data-import
Bulk import of entity records from CSV/Excel/JSON files into any entity for seeding benefits, regions, and resources.
Training Tracker  —  /training-tracker
Tracks which state resource officers have completed the 3-level training curriculum (StateTrainingProgress) with completion dates
and officer details.
VetBuddy Blueprint  •  Page 6 of 11
3. Public / Guest Pages
Guest Home  —  /
Public landing page (GuestLayout) showcasing the platform, with links to public benefits, VSO directory, laws, careers, AI
assistant, and legal pages. Converts guests to signed-in users.
Executive Summary  —  /about
Platform overview, mission, capabilities, and security posture for public/stakeholder review.
Privacy Policy  —  /privacy
Data privacy policy — VetBuddy is zero-PII for wellness/career tools, storing only what users explicitly save.
Terms of Service  —  /terms
Terms governing platform use.
Security Policy  —  /security
Security practices, NIST/OWASP controls, and compliance posture.
VetBuddy Blueprint  •  Page 7 of 11
4. Backend Functions (Serverless Handlers)
Deno functions in base44/functions/<name>/entry.ts. Reused by automations and frontend via base44.functions.invoke.
analyzeEvidenceGaps
Inspects a claim's submitted evidence against required evidence types and returns gap recommendations
(EvidenceRecommendations).
analyzeVaultDocument
Runs AI analysis (OCR + summarization) on an uploaded vault document, extracting key data points.
checkVaultDocReminders
Scheduled daily. Finds missing vault documents and expiring medical evidence per user's active claims and creates in-app
reminders.
createForumNotifications
Generates ForumNotification records for new posts, replies, mentions, and moderation actions to subscribed members.
generateEvidenceRecommendations
AI-driven recommendations for what evidence to gather next to strengthen a claim.
getClaimsReadinessBoard
Aggregates org-wide claim readiness data for the admin Claims Readiness board.
notifyForumActivity
Notifies forum members of new activity (posts/replies) per their membership and notification preferences.
notifyVsnResourceAlert
Triggered on new Resource/AccreditedNonProfit creation. Routes to the best VSN channel by service category and posts a
VetBuddy Alerts message naming the state and linking the resource.
referralFeedbackChecker
Scheduled hourly. Finds referrals 48h+ post-appointment and prompts the veteran for feedback.
referralWorkflowEngine
Triggered on referral creation. Sends the partner a notification email, logs the event, and advances the referral workflow.
VetBuddy Blueprint  •  Page 8 of 11
5. Automations
Automations run backend functions automatically — on entity create/update/delete, on a schedule, or via connector webhooks.
VSN Alert — New State Resource
Type: Entity (Resource create)
Runs notifyVsnResourceAlert when a Resource is created.
VSN Alert — New Accredited Non-Profit
Type: Entity (AccreditedNonProfit create)
Runs notifyVsnResourceAlert when an AccreditedNonProfit is created.
Referral Created — Partner Notification
Type: Entity (Referral create)
Runs referralWorkflowEngine to email the partner and log the referral.
Vault Document Reminders
Type: Scheduled (daily)
Runs checkVaultDocReminders for document/expiring-evidence reminders.
Referral Feedback Checker — 48h Post-Meeting
Type: Scheduled (hourly)
Runs referralFeedbackChecker to prompt veteran feedback.
VetBuddy Blueprint  •  Page 9 of 11
6. Data Entities
Entities are JSON schemas defining stored data. Built-in fields on every record: id, created_date, updated_date, created_by_id.
• User
• UserClaim
• ClaimStage
• VSOContact
• SavedBenefit
• VALaw
• StateBenefit
• Region
• GuardReserveBenefit
• AccreditedNonProfit
• StateTrainingProgress
• WomenVeteranResource
• Installation
• PeerSupportForum
• ForumPost
• ForumReply
• ForumMembership
• ForumNotification
• VSNMessage
• ReadinessChecklistItem
• LoadTestResult
• SymptomLog
• Referral
• BusinessProfile
• CommunityPost
• CitizenshipResource
• VaultDocument
• RecreationBenefit
• VAFormSubmission
• InsuranceInfo
• VeteranCase
• VaultNote
• TransitionChecklist
• ContentItem
• TransitionAdvisor
• Resource
• VSO
• CareerProfile
VetBuddy Blueprint  •  Page 10 of 11
7. Integrations & AI
Built-in integrations available on the base44 client: InvokeLLM (multi-model AI with optional web context), UploadFile /
UploadPrivateFile, SendEmail (registered users), GenerateImage, GenerateSpeech, GenerateVideo, TranscribeAudio,
ExtractDataFromUploadedFile, CreateFileSignedUrl.
AI Assistant
A floating assistant (FloatingAssistant) and full-page VetAssistant deliver context-aware help. System prompts are generated per
route, user profile, and transition status. The AIAssistantContext toggles assistance app-wide.
Realtime
Entities support live subscriptions (base44.entities.X.subscribe) used by VSN chat and forum activity for real-time updates.
VetBuddy Blueprint  •  Page 11 of 11
# APPENDIX B — FOUNDATION HANDOFF MACHINE-READABLE MIGRATION MANIFEST (REFERENCE ONLY)
```json
{
  "architectural_rule": {
    "platform": "VetBuddy",
    "core": "Veteran Master Record + Master Case",
    "intelligence": "Bounded multi-agent AI",
    "operating_engine": "Workflow/Event Layer",
    "relationship_layer": "CRM",
    "system_of_record": "Supabase/PostgreSQL",
    "code_source_of_truth": "GitHub"
  },
  "source_state": {
    "frontend": "React 18 + Vite SPA, Tailwind/shadcn, React Query, React Router",
    "current_backend": "Base44 entities/functions/automations/integrations",
    "migration_principle": "Preserve UI/business concepts; migrate authoritative data/security/workflows to explicit domains and Supabase-backed services."
  },
  "pages": [
    {
      "group": "Mission Control",
      "name": "Dashboard",
      "route": "/",
      "target": "Master Case / Command Center",
      "status": "KEEP + REWIRE",
      "notes": "Replace aggregate Base44 entity queries with case-centric read models backed by Supabase."
    },
    {
      "group": "Mission Control",
      "name": "Case Overview",
      "route": "/case-overview",
      "target": "Master Case",
      "status": "KEEP + ELEVATE",
      "notes": "Make this the canonical Veteran Master Case workspace; claims, referrals, documents, contacts, tasks and next actions become child domains."
    },
    {
      "group": "Mission Control",
      "name": "Transition Coach",
      "route": "/coach",
      "target": "Mission Transition",
      "status": "KEEP + REFACTOR",
      "notes": "Move coaching logic behind Orchestrator + Transition Agent; readiness becomes a case plan, not global app state."
    },
    {
      "group": "Mission Control",
      "name": "Benefits Matcher",
      "route": "/benefits-match",
      "target": "Benefits Center",
      "status": "KEEP + REFACTOR",
      "notes": "Use structured benefits/rules/sources/eligibility assessments; AI explains results but does not own eligibility rules."
    },
    {
      "group": "Mission Control",
      "name": "Referral Tracker",
      "route": "/referrals",
      "target": "ResourceHub / Referrals",
      "status": "KEEP",
      "notes": "Promote Referral to a first-class case-linked workflow with partner CRM relationship records."
    },
    {
      "group": "Mission Control",
      "name": "Transition Mode",
      "route": "/transition-mode",
      "target": "Personalization / AI Context",
      "status": "MERGE",
      "notes": "Absorb into user/case context and agent routing; remove as a separate architectural pillar."
    },
    {
      "group": "Mission Control",
      "name": "Mission Timeline",
      "route": "/mission-timeline",
      "target": "Workflow / Case Plan",
      "status": "KEEP + REWIRE",
      "notes": "Unify milestones, tasks, reminders, deadlines and case events under workflow/event layer."
    },
    {
      "group": "Mission Control",
      "name": "VetBuddy AI",
      "route": "/assistant",
      "target": "Universal AI / Orchestrator",
      "status": "KEEP + ELEVATE",
      "notes": "Make this the single conversational gateway that routes to bounded specialist agents."
    },
    {
      "group": "Mission Control",
      "name": "Community Feed",
      "route": "/community",
      "target": "Community / VSN",
      "status": "DEFER CORE",
      "notes": "Preserve code and data model, but keep outside MVP case-management critical path."
    },
    {
      "group": "Mission Control",
      "name": "VSN Chat",
      "route": "/vsn",
      "target": "Community / VSN",
      "status": "DEFER CORE",
      "notes": "Preserve realtime channel concept; isolate from case data and sensitive records."
    },
    {
      "group": "Mission Control",
      "name": "Training Module",
      "route": "/training",
      "target": "Learning Academy",
      "status": "KEEP + REHOME",
      "notes": "Move curricula and progress tracking into Learning Academy domain."
    },
    {
      "group": "Claims",
      "name": "My Claims",
      "route": "/claims-tracker",
      "target": "Claims Center",
      "status": "KEEP + REFACTOR",
      "notes": "Claims become subcases linked to Master Case; evidence, stages, decisions and timeline get normalized tables."
    },
    {
      "group": "Claims",
      "name": "VA Forms Hub",
      "route": "/va-forms",
      "target": "Forms / Applications",
      "status": "KEEP + HARDEN",
      "notes": "Retain form wizards as drafts; require explicit user review before consequential submission."
    },
    {
      "group": "Claims",
      "name": "Claims Guide",
      "route": "/claims-guide",
      "target": "Knowledge Base / Claims Education",
      "status": "KEEP",
      "notes": "Treat as educational content with source governance and versioning."
    },
    {
      "group": "Claims",
      "name": "VSO Directory",
      "route": "/vso-directory",
      "target": "ResourceHub / Partner CRM",
      "status": "KEEP + MERGE",
      "notes": "Represent VSOs as organizations/providers with accreditation and service metadata."
    },
    {
      "group": "Claims",
      "name": "My Contacts",
      "route": "/contacts",
      "target": "CRM Relationship Layer",
      "status": "KEEP + REHOME",
      "notes": "Personal contacts remain, but CRM becomes a supporting relationship layer linked to cases/referrals."
    },
    {
      "group": "Claims",
      "name": "Laws & Rights",
      "route": "/laws",
      "target": "Knowledge / Regulatory Sources",
      "status": "KEEP + HARDEN",
      "notes": "Store official source, jurisdiction, effective date, verification date and simplified explanation separately."
    },
    {
      "group": "Claims",
      "name": "Accredited Registry",
      "route": "/accredited-registry",
      "target": "ResourceHub / Partner CRM",
      "status": "KEEP + MERGE",
      "notes": "Normalize nonprofits/providers/accreditation into organization and resource-provider models."
    },
    {
      "group": "Career & Business",
      "name": "Career Compass",
      "route": "/career-compass",
      "target": "Mission Transition",
      "status": "KEEP",
      "notes": "Keep session-first/low-PII design; results can be saved only with explicit user action."
    },
    {
      "group": "Career & Business",
      "name": "Career Engine",
      "route": "/careers",
      "target": "Mission Transition",
      "status": "KEEP + AGENTIZE",
      "notes": "Route resume, skill translation and career planning through Career Transition Agent."
    },
    {
      "group": "Career & Business",
      "name": "Transition Map",
      "route": "/career-transition-map",
      "target": "Mission Transition / Jurisdictions",
      "status": "KEEP + MERGE",
      "notes": "Reuse jurisdiction data and career resources; separate source data from AI recommendations."
    },
    {
      "group": "Career & Business",
      "name": "Assessment Referral",
      "route": "/assessment-referral",
      "target": "ResourceHub / Referrals",
      "status": "KEEP + SAFETY REVIEW",
      "notes": "Route to resources; avoid diagnostic claims and keep sensitive assessment data minimal."
    },
    {
      "group": "Career & Business",
      "name": "Business Launchpad",
      "route": "/business",
      "target": "Mission Transition / Entrepreneurship",
      "status": "KEEP LATER",
      "notes": "Preserve as later module linked to career/transition case plan."
    },
    {
      "group": "Career & Business",
      "name": "Installation & TAP",
      "route": "/installation-navigator",
      "target": "ResourceHub / Transition",
      "status": "KEEP",
      "notes": "Normalize installations and TAP services as providers/locations/resources."
    },
    {
      "group": "Wellness",
      "name": "Wellness Check-In",
      "route": "/wellness",
      "target": "Wellness Navigation",
      "status": "KEEP ISOLATED",
      "notes": "Maintain zero-PII/session-only default; separate from claims and Master Case unless user explicitly saves/authorizes data."
    },
    {
      "group": "Housing & Family",
      "name": "Benefits & Resources",
      "route": "/state-benefits",
      "target": "Benefits Center / ResourceHub",
      "status": "KEEP + MERGE",
      "notes": "Unify federal/state benefit browsing with canonical benefits and resources domains."
    },
    {
      "group": "Housing & Family",
      "name": "Citizenship Guide",
      "route": "/citizenship",
      "target": "ResourceHub / Knowledge",
      "status": "KEEP",
      "notes": "Treat as sourced resource/knowledge content."
    },
    {
      "group": "Housing & Family",
      "name": "Women Veterans",
      "route": "/women-veterans",
      "target": "Women Veterans Center",
      "status": "KEEP + AGENTIZE",
      "notes": "Preserve dedicated experience; add Women Veterans Agent and privacy-aware routing."
    },
    {
      "group": "Guard & Reserve Atlas",
      "name": "Atlas Dashboard",
      "route": "/atlas",
      "target": "Guard & Reserve Center",
      "status": "KEEP + ELEVATE",
      "notes": "Make atlas a specialized benefits view over canonical jurisdictions/benefits data."
    },
    {
      "group": "Guard & Reserve Atlas",
      "name": "Browse States",
      "route": "/atlas/states",
      "target": "Guard & Reserve Center",
      "status": "KEEP",
      "notes": "Retain 56-jurisdiction browse UX backed by canonical jurisdiction records."
    },
    {
      "group": "Guard & Reserve Atlas",
      "name": "State Detail",
      "route": "/atlas/state/:abbr",
      "target": "Guard & Reserve Center",
      "status": "KEEP",
      "notes": "Use benefit sources/rules and verification metadata rather than duplicated page-specific data."
    },
    {
      "group": "Guard & Reserve Atlas",
      "name": "Compare States",
      "route": "/atlas/compare",
      "target": "Guard & Reserve Center",
      "status": "KEEP",
      "notes": "Comparison becomes a query/read model over jurisdiction and benefit domains."
    },
    {
      "group": "Guard & Reserve Atlas",
      "name": "Atlas Data Mgmt",
      "route": "/atlas/admin",
      "target": "Admin / Data Governance",
      "status": "KEEP + HARDEN",
      "notes": "Move confidence and verification workflows into source governance/admin tools."
    },
    {
      "group": "Jurisdiction Compare",
      "name": "Compare 56 States",
      "route": "/jurisdiction-compare",
      "target": "Jurisdiction Intelligence",
      "status": "KEEP + MERGE",
      "notes": "Consolidate Region + GuardReserveBenefit + StateBenefit into canonical jurisdiction/benefit models."
    },
    {
      "group": "Jurisdiction Compare",
      "name": "Resource Center",
      "route": "/resource-center",
      "target": "ResourceHub / Data Governance",
      "status": "KEEP + REHOME",
      "notes": "Separate public ResourceHub from admin data-management tooling."
    },
    {
      "group": "My Records",
      "name": "Saved Benefits",
      "route": "/saved-benefits",
      "target": "Benefits Center / Case Plan",
      "status": "KEEP + REWIRE",
      "notes": "Saved benefits become veteran-benefit relationships with status, notes, tasks and application links."
    },
    {
      "group": "My Records",
      "name": "Document Vault",
      "route": "/document-vault",
      "target": "Documents & Evidence",
      "status": "KEEP + ELEVATE",
      "notes": "Make canonical document/evidence layer with Supabase Storage, metadata, versions, provenance and case links."
    },
    {
      "group": "My Records",
      "name": "Benefits Estimator",
      "route": "/benefits-estimator",
      "target": "Benefits Tools",
      "status": "KEEP + VALIDATE",
      "notes": "Keep deterministic calculations separate from AI; add test fixtures and source/version metadata."
    },
    {
      "group": "My Records",
      "name": "Transition Calculator",
      "route": "/transition-calculator",
      "target": "MoneyLife / Transition",
      "status": "KEEP LATER",
      "notes": "Preserve calculations; move under transition/financial education boundary."
    },
    {
      "group": "My Records",
      "name": "Insurance & Abroad",
      "route": "/insurance",
      "target": "ResourceHub / Knowledge",
      "status": "KEEP",
      "notes": "Treat as sourced educational/resource content."
    },
    {
      "group": "My Records",
      "name": "My Profile",
      "route": "/profile",
      "target": "Veteran Master Record",
      "status": "KEEP + SPLIT",
      "notes": "Split User into auth profile, veteran profile, military service records, preferences and consent."
    },
    {
      "group": "My Records",
      "name": "Settings",
      "route": "/settings",
      "target": "Identity / Preferences / Consent",
      "status": "KEEP + HARDEN",
      "notes": "Centralize privacy consent, AI preferences, notifications, devices and data-sharing controls."
    },
    {
      "group": "Admin",
      "name": "Readiness Board",
      "route": "/admin-readiness",
      "target": "Security / Production Readiness",
      "status": "KEEP + REHOME",
      "notes": "Retain as internal compliance/readiness workspace; do not present checklist completion as certification."
    },
    {
      "group": "Admin",
      "name": "Claims Readiness",
      "route": "/admin-claims-board",
      "target": "Case Operations Dashboard",
      "status": "KEEP + REFACTOR",
      "notes": "Use tenant-scoped case analytics and least-privilege access; avoid broad cross-user exposure."
    },
    {
      "group": "Admin",
      "name": "Content CMS",
      "route": "/admin-cms",
      "target": "Knowledge / Content Governance",
      "status": "KEEP",
      "notes": "Add source/version/approval fields and separate public copy from authoritative rules."
    },
    {
      "group": "Admin",
      "name": "Data Import",
      "route": "/data-import",
      "target": "Data Governance / Import Pipeline",
      "status": "KEEP + HARDEN",
      "notes": "Validate schemas, stage imports, preview diffs, audit changes and reject unsafe bulk writes."
    },
    {
      "group": "Admin",
      "name": "Training Tracker",
      "route": "/training-tracker",
      "target": "Learning Academy Admin",
      "status": "KEEP + REHOME",
      "notes": "Normalize progress/enrollment and role-based training administration."
    }
  ],
  "entities": [
    {
      "source": "User",
      "target": "auth.users + profiles + veterans + military_service_records + user_preferences",
      "status": "SPLIT",
      "notes": "Do not keep military/service/consent data on one user record."
    },
    {
      "source": "UserClaim",
      "target": "claims",
      "status": "MIGRATE",
      "notes": "Link every claim to master_case_id/subcase_id and normalize issues/events/decisions."
    },
    {
      "source": "ClaimStage",
      "target": "claim_stages reference + claim_events",
      "status": "REFINE",
      "notes": "Use reference taxonomy plus event history rather than stage-only state."
    },
    {
      "source": "VSOContact",
      "target": "contacts + case_contacts + crm_relationships",
      "status": "MIGRATE",
      "notes": "CRM remains relationship layer."
    },
    {
      "source": "SavedBenefit",
      "target": "veteran_benefits / saved_benefits",
      "status": "MIGRATE",
      "notes": "Add status, source, case link, tasks and application links."
    },
    {
      "source": "VALaw",
      "target": "knowledge_sources + regulatory_sources",
      "status": "MIGRATE",
      "notes": "Track authority, jurisdiction, effective date, last verified."
    },
    {
      "source": "StateBenefit",
      "target": "benefits + benefit_rules + benefit_sources",
      "status": "NORMALIZE",
      "notes": "Do not encode eligibility only in prose."
    },
    {
      "source": "Region",
      "target": "jurisdictions + jurisdiction_metrics",
      "status": "NORMALIZE",
      "notes": "Use canonical jurisdiction IDs and versioned metrics."
    },
    {
      "source": "GuardReserveBenefit",
      "target": "benefits + audience/component rules",
      "status": "MERGE",
      "notes": "Avoid a parallel benefits universe."
    },
    {
      "source": "AccreditedNonProfit",
      "target": "organizations + provider_accreditations + resources",
      "status": "NORMALIZE",
      "notes": "Separate organization identity, accreditation and offered resources."
    },
    {
      "source": "StateTrainingProgress",
      "target": "learning_enrollments + learning_progress",
      "status": "MIGRATE",
      "notes": "Move to Learning Academy."
    },
    {
      "source": "WomenVeteranResource",
      "target": "resources + audience_tags",
      "status": "MERGE",
      "notes": "Dedicated UX/agent can query canonical resource data."
    },
    {
      "source": "Installation",
      "target": "resource_providers + provider_locations",
      "status": "NORMALIZE",
      "notes": "Treat installations/TAP offices as provider/location records."
    },
    {
      "source": "PeerSupportForum",
      "target": "community_forums",
      "status": "PRESERVE/DEFER",
      "notes": "Keep isolated from case data."
    },
    {
      "source": "ForumPost",
      "target": "community_posts",
      "status": "PRESERVE/DEFER",
      "notes": "Community domain."
    },
    {
      "source": "ForumReply",
      "target": "community_replies",
      "status": "PRESERVE/DEFER",
      "notes": "Community domain."
    },
    {
      "source": "ForumMembership",
      "target": "community_memberships",
      "status": "PRESERVE/DEFER",
      "notes": "Community domain."
    },
    {
      "source": "ForumNotification",
      "target": "notifications",
      "status": "MERGE",
      "notes": "Use central notification service with community event types."
    },
    {
      "source": "VSNMessage",
      "target": "community_messages",
      "status": "PRESERVE/DEFER",
      "notes": "Realtime community messaging; strict privacy boundary."
    },
    {
      "source": "ReadinessChecklistItem",
      "target": "compliance_controls + readiness_checks",
      "status": "MIGRATE",
      "notes": "Internal readiness only."
    },
    {
      "source": "LoadTestResult",
      "target": "performance_test_runs",
      "status": "MIGRATE",
      "notes": "Observability/testing domain."
    },
    {
      "source": "SymptomLog",
      "target": "ephemeral wellness session or consented wellness record",
      "status": "RESTRICT",
      "notes": "Default to session-only; do not automatically feed claims."
    },
    {
      "source": "Referral",
      "target": "referrals + referral_events",
      "status": "ELEVATE",
      "notes": "First-class case workflow linked to provider and outcome."
    },
    {
      "source": "BusinessProfile",
      "target": "entrepreneurship_profiles",
      "status": "PRESERVE LATER",
      "notes": "Mission Transition expansion."
    },
    {
      "source": "CommunityPost",
      "target": "community_posts",
      "status": "MERGE",
      "notes": "Avoid duplicate post models if possible."
    },
    {
      "source": "CitizenshipResource",
      "target": "resources + knowledge_sources",
      "status": "MERGE",
      "notes": "Canonical ResourceHub."
    },
    {
      "source": "VaultDocument",
      "target": "documents + document_versions + document_metadata + evidence_links",
      "status": "ELEVATE",
      "notes": "Supabase Storage object + relational metadata/provenance."
    },
    {
      "source": "RecreationBenefit",
      "target": "benefits/resources",
      "status": "MERGE",
      "notes": "Canonical benefit/resource taxonomy."
    },
    {
      "source": "VAFormSubmission",
      "target": "form_drafts + applications + application_steps",
      "status": "REFACTOR",
      "notes": "Explicit review/authorization before submission."
    },
    {
      "source": "InsuranceInfo",
      "target": "knowledge_sources/resources",
      "status": "MERGE",
      "notes": "Educational content."
    },
    {
      "source": "VeteranCase",
      "target": "master_cases + subcases",
      "status": "ELEVATE",
      "notes": "This becomes the central domain, not a side entity."
    },
    {
      "source": "VaultNote",
      "target": "document_notes / case_notes",
      "status": "MERGE",
      "notes": "Use scoped notes with audit trail."
    },
    {
      "source": "TransitionChecklist",
      "target": "case_plans + tasks + milestones",
      "status": "NORMALIZE",
      "notes": "Workflow/case plan layer."
    },
    {
      "source": "ContentItem",
      "target": "content_items + knowledge_sources",
      "status": "REFINE",
      "notes": "Add approval, source, version, publish state."
    },
    {
      "source": "TransitionAdvisor",
      "target": "agent_configs or transition_plan recommendations",
      "status": "REMODEL",
      "notes": "If this is data, separate AI config from generated recommendations."
    },
    {
      "source": "Resource",
      "target": "resources + resource_providers",
      "status": "ELEVATE",
      "notes": "Canonical ResourceHub model."
    },
    {
      "source": "VSO",
      "target": "organizations + provider_services + accreditation",
      "status": "NORMALIZE",
      "notes": "Partner CRM / ResourceHub."
    },
    {
      "source": "CareerProfile",
      "target": "career_profiles + skills + goals",
      "status": "MIGRATE",
      "notes": "Mission Transition domain."
    }
  ],
  "functions": [
    {
      "source": "analyzeEvidenceGaps",
      "target": "Document/Claims Agent tool",
      "status": "KEEP + GUARD",
      "guardrail": "Read-only analysis; structured output; source/evidence provenance; human confirmation."
    },
    {
      "source": "analyzeVaultDocument",
      "target": "Document Agent pipeline",
      "status": "KEEP + ELEVATE",
      "guardrail": "OCR/extraction/summarization behind queue; never overwrite original; confidence/provenance required."
    },
    {
      "source": "checkVaultDocReminders",
      "target": "Workflow scheduler",
      "status": "KEEP",
      "guardrail": "Translate to DEADLINE/DOCUMENT reminder events; idempotent job."
    },
    {
      "source": "createForumNotifications",
      "target": "Notification service",
      "status": "KEEP LATER",
      "guardrail": "Community event consumer."
    },
    {
      "source": "generateEvidenceRecommendations",
      "target": "Claims Navigation Agent tool",
      "status": "KEEP + GUARD",
      "guardrail": "Recommendations only; no guarantee or automatic claim action."
    },
    {
      "source": "getClaimsReadinessBoard",
      "target": "Case analytics read model",
      "status": "KEEP + HARDEN",
      "guardrail": "Tenant-scoped aggregation; no unrestricted cross-user reads."
    },
    {
      "source": "notifyForumActivity",
      "target": "Notification service",
      "status": "KEEP LATER",
      "guardrail": "Community domain event consumer."
    },
    {
      "source": "notifyVsnResourceAlert",
      "target": "ResourceHub → Community event",
      "status": "KEEP LATER",
      "guardrail": "Publish resource-created event; community subscriber decides channel."
    },
    {
      "source": "referralFeedbackChecker",
      "target": "Workflow scheduler",
      "status": "KEEP",
      "guardrail": "Case-linked scheduled follow-up; idempotent and auditable."
    },
    {
      "source": "referralWorkflowEngine",
      "target": "Referral workflow",
      "status": "KEEP + ELEVATE",
      "guardrail": "Move from email-centric automation to referral state machine + notifications + audit events."
    }
  ],
  "automations": [
    {
      "source": "VSN Alert — New State Resource",
      "event": "RESOURCE_CREATED",
      "target": "Community subscriber",
      "status": "DEFER CORE"
    },
    {
      "source": "VSN Alert — New Accredited Non-Profit",
      "event": "PROVIDER_ACCREDITATION_CREATED",
      "target": "Community subscriber",
      "status": "DEFER CORE"
    },
    {
      "source": "Referral Created — Partner Notification",
      "event": "REFERRAL_CREATED",
      "target": "Referral workflow + notification",
      "status": "KEEP"
    },
    {
      "source": "Vault Document Reminders",
      "event": "DOCUMENT_REQUIREMENT_DUE",
      "target": "Workflow scheduler",
      "status": "KEEP"
    },
    {
      "source": "Referral Feedback Checker",
      "event": "REFERRAL_FOLLOWUP_DUE",
      "target": "Workflow scheduler",
      "status": "KEEP"
    }
  ],
  "agents": [
    {
      "name": "VetBuddy Orchestrator",
      "purpose": "Routes intent, gathers minimum authorized context, invokes specialist agents, composes response.",
      "guardrail": "No direct unrestricted writes; no cross-tenant context; consequential actions require workflow authorization."
    },
    {
      "name": "Intake Agent",
      "purpose": "Progressive onboarding, needs assessment, profile completeness, case creation suggestions.",
      "guardrail": "May propose changes; user confirms sensitive profile facts."
    },
    {
      "name": "Federal Benefits Agent",
      "purpose": "Federal benefits discovery and explanation.",
      "guardrail": "Uses structured benefit records/sources; does not guarantee eligibility."
    },
    {
      "name": "State Benefits Agent",
      "purpose": "Jurisdiction-specific benefits including Alabama-first and Guard/Reserve rules.",
      "guardrail": "Must cite jurisdiction/source/version; flags stale/unverified data."
    },
    {
      "name": "Research Quality Agent",
      "purpose": "Checks source authority, freshness, conflicts and citation completeness.",
      "guardrail": "Can block/flag low-confidence output; cannot invent confidence."
    },
    {
      "name": "Resource Navigation Agent",
      "purpose": "Matches users to organizations, services and referrals.",
      "guardrail": "Does not expose case data to providers without consent."
    },
    {
      "name": "Document Agent",
      "purpose": "Classifies, extracts, summarizes, links and detects evidence/document gaps.",
      "guardrail": "Original immutable; extracted facts are proposed until confirmed."
    },
    {
      "name": "Claims Navigation Agent",
      "purpose": "Organizes claim stages, evidence, deadlines and educational explanations.",
      "guardrail": "No representation, no guaranteed outcome, no silent submission."
    },
    {
      "name": "Forms Agent",
      "purpose": "Identifies forms, prepares drafts, validates completeness.",
      "guardrail": "Explicit user review before consequential submission."
    },
    {
      "name": "Appeal & Advocacy Agent",
      "purpose": "Explains review/appeal pathways and evidence gaps.",
      "guardrail": "Escalates to authorized/accredited representation when appropriate."
    },
    {
      "name": "Legal & Compliance Agent",
      "purpose": "Checks high-risk outputs and policy/compliance boundaries.",
      "guardrail": "Review role; does not become legal counsel."
    },
    {
      "name": "Career Transition Agent",
      "purpose": "MOS/skills translation, resumes, job planning, transition milestones.",
      "guardrail": "Keep employment recommendations explainable; user controls saved profile data."
    },
    {
      "name": "Education Agent",
      "purpose": "GI Bill/VR&E/education planning and school/credential pathways.",
      "guardrail": "Uses current authoritative sources and separates institutional claims from verified rules."
    },
    {
      "name": "Funding Stack Agent",
      "purpose": "Combines compatible education/funding options.",
      "guardrail": "Detects conflicts/duplication; no fabricated funding."
    },
    {
      "name": "Guard/Reserve Agent",
      "purpose": "Component/status-sensitive Guard/Reserve benefit reasoning.",
      "guardrail": "Requires service-status inputs; distinguishes Title 10/32/state contexts where data supports it."
    },
    {
      "name": "Women Veterans Agent",
      "purpose": "Dedicated resource/benefit navigation for women veterans.",
      "guardrail": "Privacy-aware and resource-focused; no unnecessary sensitive inference."
    },
    {
      "name": "Family Benefits Agent",
      "purpose": "Spouse/dependent/caregiver/survivor resource navigation.",
      "guardrail": "Access only authorized family/case data."
    },
    {
      "name": "Financial Wellness Agent",
      "purpose": "Budgeting/financial education and transition planning.",
      "guardrail": "Educational boundary; no unsupported regulated advice."
    },
    {
      "name": "Communications Agent",
      "purpose": "Drafts case communications and notices.",
      "guardrail": "External send requires authorized action and channel-safe data."
    },
    {
      "name": "Scheduling Agent",
      "purpose": "Deadlines, reminders, appointments, follow-up tasks.",
      "guardrail": "Uses workflow permissions; no hidden schedule changes."
    },
    {
      "name": "Data Analyst Agent",
      "purpose": "Operational/case analytics over permitted aggregates.",
      "guardrail": "Prefer de-identified/aggregate data; tenant boundaries enforced."
    },
    {
      "name": "Security Agent",
      "purpose": "Monitors security events and permission anomalies.",
      "guardrail": "Advisory/alerting role; privileged actions require admin workflow."
    }
  ],
  "phases": [
    {
      "phase": 1,
      "name": "Architecture Freeze & Preservation",
      "tools": "GitHub + docs",
      "scope": "Inventory Base44 assets; create target domain map; preserve all existing code before refactor.",
      "exit_criteria": "No feature deletion; master spec, architecture, migration manifest and AGENTS.md committed."
    },
    {
      "phase": 2,
      "name": "Supabase Foundation",
      "tools": "Supabase + migrations",
      "scope": "Auth, profiles, organizations, military service, master cases, subcases, tasks, deadlines, audit logs, RLS.",
      "exit_criteria": "Tenant/RLS tests pass; synthetic data only."
    },
    {
      "phase": 3,
      "name": "Application Shell Migration",
      "tools": "Base44 UI + Cursor",
      "scope": "Keep React/Vite/Tailwind/shadcn shell; replace Base44 data calls behind adapters.",
      "exit_criteria": "Dashboard/Profile/Master Case render from Supabase dev data."
    },
    {
      "phase": 4,
      "name": "Core Veteran Journey",
      "tools": "Cursor + Supabase",
      "scope": "Registration → intake → Veteran Master Record → Master Case → tasks/deadlines/documents.",
      "exit_criteria": "End-to-end test passes."
    },
    {
      "phase": 5,
      "name": "AI Core",
      "tools": "Claude Code/Codex + model APIs",
      "scope": "Orchestrator, Intake, Federal/State Benefits, Research Quality, Resource Navigation, Document Agent.",
      "exit_criteria": "Agents have typed contracts, tool boundaries, logs and evals."
    },
    {
      "phase": 6,
      "name": "Benefits & Jurisdiction Data",
      "tools": "Supabase + admin governance",
      "scope": "Normalize StateBenefit/GuardReserveBenefit/Region into benefits/rules/sources/jurisdictions.",
      "exit_criteria": "Alabama + federal pilot data verified and versioned."
    },
    {
      "phase": 7,
      "name": "Documents & Evidence",
      "tools": "Supabase Storage + workers",
      "scope": "Vault migration, metadata, versions, extraction, provenance, evidence links.",
      "exit_criteria": "Original files immutable; analysis is auditable."
    },
    {
      "phase": 8,
      "name": "Claims Center",
      "tools": "Claims domain + guarded agents",
      "scope": "Claims, issues, events, decisions, evidence, forms, readiness.",
      "exit_criteria": "Claims guidance is educational/organizational with explicit review gates."
    },
    {
      "phase": 9,
      "name": "ResourceHub & Partner CRM",
      "tools": "Resources + referrals + CRM",
      "scope": "Organizations/providers/contacts/referrals become relationship layer around cases.",
      "exit_criteria": "CRM never becomes system core; referrals link case ↔ provider ↔ outcome."
    },
    {
      "phase": 10,
      "name": "Transition / Education / Specialized Centers",
      "tools": "Feature waves",
      "scope": "Mission Transition, Learning Academy, Guard/Reserve, Women Veterans, Family, MoneyLife.",
      "exit_criteria": "Each module reuses core identity/case/document/workflow layers."
    },
    {
      "phase": 11,
      "name": "Community & Realtime",
      "tools": "VSN/community",
      "scope": "Reintroduce forums/chat after privacy, moderation and isolation controls are stable.",
      "exit_criteria": "Community data cannot traverse into case context without explicit user action."
    },
    {
      "phase": 12,
      "name": "Production Hardening",
      "tools": "GitHub Actions + staging",
      "scope": "CI/CD, observability, backups, security tests, accessibility, load tests, incident runbooks.",
      "exit_criteria": "Human release checklist completed before production."
    }
  ]
}
```
