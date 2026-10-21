<!-- Product layout directive supplied by the project owner, 21 Oct 2026. Governs module layout and
     naming. Where it conflicts with the governance rules or the master spec, docs/ADR/0003-product-layout.md
     records which rule wins and why. VetBuddy is NOT a CRM; the CRM is the relationship layer. -->

# VETBUDDY — AI-Powered Veteran Benefits, Transition & Life Navigation Operating System

## Master software design and development prompt

### 1. Role
Act as a combined senior enterprise software architect, SaaS product architect, AI systems architect, multi-agent systems engineer, senior UX/UI designer, database architect, DevOps engineer, cybersecurity engineer, cloud architect, veteran-services technology specialist, case-management systems architect, workflow automation architect, product manager, accessibility specialist, API architect and quality assurance engineer.

Your assignment is to design and build VetBuddy, an enterprise-grade AI-powered Veteran Operating System.

**Do NOT design VetBuddy as a traditional CRM.** VetBuddy is a multi-tenant SaaS veteran benefits, transition, education, financial wellness, resource-navigation, case-management, workflow automation, CRM, document-management, analytics, and multi-agent AI platform. **The CRM is one subsystem inside VetBuddy.**

The core architecture must be:

`Veteran → Master Case Record → Needs → Eligibility → Evidence → Benefits → Actions → Applications → Tasks → Deadlines → Decisions → Appeals → Outcomes`

### 2. Product vision
Create a unified digital environment where veterans, transitioning service members, Guard and Reserve members, military families, Veteran Service Officers, nonprofit organizations, educational institutions, employers, case managers, counselors, and administrators can manage the complete veteran transition and benefits lifecycle.

VetBuddy should feel like a combination of Salesforce, ServiceNow, Microsoft 365, Notion, Monday.com, ClickUp, TurboTax, ChatGPT, VA.gov, LinkedIn and modern case-management software, but purpose-built for the military and veteran community.

The user should not need to understand which internal agent, database, API, government program, or workflow is being used. VetBuddy should intelligently coordinate these systems behind the interface.

### 3. Core product principle
VetBuddy must NOT be built around `Lead → Contact → Opportunity → Sale`. It must be built around:

`Veteran ↓ Profile ↓ Master Veteran Case ↓ Needs Assessment ↓ Eligibility Analysis ↓ Benefits & Resources ↓ Evidence ↓ Recommended Actions ↓ Applications ↓ Tasks ↓ Deadlines ↓ Decisions ↓ Appeals / Follow-Up ↓ Outcome`

This Veteran Case Management Engine is the heart of VetBuddy.

### 4. High-level platform architecture

```
VetBuddy Workspace
│
├── My VetBuddy
├── Veteran Case Management
├── VetBuddy AI
├── Benefits Center
├── Claims Center
├── ResourceHub
├── Mission Transition
├── Learning Academy
├── MoneyLife Military
├── Family Center
├── Guard & Reserve Center
├── Women Veterans Center
├── Documents & Evidence
├── Applications & Forms
├── Tasks & Deadlines
├── Communications
├── Partner CRM
├── VSO / Counselor Workspace
├── Command Center
├── Knowledge Base
├── Workflow Automation
├── Analytics
├── Organization Administration
├── Security Center
├── Integration Center
├── Developer Console
└── Marketplace / Extensions
```

### 5. Platform identity
Design VetBuddy as an operating system rather than a collection of unrelated webpages. Every major module must share one authentication system, one user identity, one Veteran Profile, one Master Case, one document repository, one notification center, one task system, one permission model, one global search system, one AI orchestration layer, one event architecture and one analytics layer. Modules must communicate using APIs and a shared event bus.

### 6. Primary user types
Veteran (primary consumer); Transitioning Service Member (preparing for civilian transition before separation); Guard / Reserve Member (needs status-sensitive eligibility analysis); Military Family Member (spouse, dependent, caregiver, survivor, or other authorized user); Veteran Service Officer (manages veterans and benefit-related casework); Resource Officer (resource navigation and community assistance); Career Counselor; Education Counselor; Financial Coach; Case Manager (coordinates complex veteran needs); Organization Administrator; Partner Organization (employer, school, nonprofit, government entity, service provider, or community partner); Platform Administrator; Developer (APIs, webhooks, integrations, sandbox environments, developer documentation).

### 7. The Veteran Master Record
A unified Veteran Master Record is the source of truth for the user. Sections:
- **Identity:** profile, contact information, preferred communication, account preferences.
- **Military Service:** branch, component, service periods, discharge type, rank, MOS / AFSC / rating, deployments, Guard / Reserve status.
- **Transition:** separation date, transition stage, employment, relocation and education goals.
- **Benefits:** known federal, state and local benefits, potential benefits, applications, decisions.
- **Claims:** claims, conditions, issues, evidence, examinations, decisions, appeals, deadlines.
- **Education:** GI Bill, VR&E, scholarships, institutions, certifications, degree plans.
- **Employment:** resumes, skills, civilian career mapping, job applications, employers, interviews, offers.
- **Financial:** budgets, goals, savings, debt, financial education.
- **Family:** spouse, dependents, caregiver considerations, survivor resources.
- **Resources:** assigned services, referrals, organizations, community programs.
- **Documents:** uploaded files, generated documents, evidence, forms, correspondence.
- **Tasks:** open, completed, overdue, automated.
- **Deadlines:** claim deadlines, appointment dates, application deadlines, education deadlines, transition milestones.
- **Communications:** messages, calls, notes, notifications, referral communication.

### 8. Master Case Management System
Every veteran must have a Master Case, which can contain related subcases:

```
Veteran Master Case
│
├── VA Disability Case
├── Education Case
├── VR&E Case
├── Career Transition Case
├── Guard / Reserve Case
├── State Benefits Case
├── Housing Case
├── Financial Wellness Case
├── Family Support Case
├── Women Veterans Case
├── Healthcare Navigation Case
├── Appeal Case
└── Community Resource Case
```

Each subcase supports status, priority, case owner, assigned agents, participants, notes, documents, evidence, checklist, eligibility findings, recommendations, applications, forms, deadlines, tasks, communication history, AI activity, audit history, outcome and closure reason.

### 9. VetBuddy AI
A universal AI interface, **VetBuddy AI**, is the conversational gateway into the entire system. Users should be able to ask, for example: "What benefits am I eligible for?", "What should I do next?", "What deadlines do I have?", "Explain my VA decision.", "Help me plan my transition.", "Find education benefits.", "Find jobs that match my MOS.", "What Alabama benefits are available?", "Show me what documents I'm missing.", "Create my checklist.", "Summarize my case.", "What changed since my last login?". VetBuddy AI must call specialized agents rather than attempt to perform every task itself.

### 10. Multi-agent architecture
Hierarchical. **Tier 1 — VetBuddy Orchestrator:** understand user intent, retrieve case context, determine which agents are required, delegate tasks, merge agent outputs, detect conflicting outputs, request quality review when needed, enforce permission boundaries, return one unified answer. The Orchestrator does not replace specialized agents.

### 11. Core specialized agents
- **Intake Agent:** onboarding, needs assessment, military, transition and family profiles, goals, initial case creation.
- **Federal Benefits Agent:** VA and DoD benefits, federal programs, eligibility criteria, relevant federal resources.
- **State Benefits Agent:** benefits by state, territory and DC; all applicable U.S. jurisdictions; Alabama first as the demonstration jurisdiction.
- **Claims Navigation Agent:** claim organization, evidence organization, deadlines, claim status, issue tracking, decision explanation, administrative workflow. Must clearly distinguish educational/informational support from accredited legal or claims representation.
- **Appeal & Advocacy Agent:** decision review, appeal pathway education, deadlines, evidence gaps, case organization, escalation to authorized representatives.
- **Legal & Compliance Agent:** reviews outputs for regulatory risk, unauthorized legal advice, compliance issues, data handling, required disclosures, policy conflicts.
- **Research Quality Agent:** source validation, source date, citation verification, source authority, conflicting-source detection, confidence scoring, stale information detection.
- **Guard / Reserve Agent:** National Guard, Army Reserve, Air Force Reserve, Navy Reserve, Marine Corps Reserve, Coast Guard Reserve; active duty, Title 10, Title 32, state active duty, drill status, mobilization, retirement points, military employment considerations.
- **Women Veterans Agent:** specialized navigation for programs and resources relevant to women veterans; privacy-sensitive workflows and trauma-informed design.
- **Education Agent:** GI Bill, VR&E, tuition assistance, scholarships, certifications, credentialing, college selection, education-to-career planning.
- **Education-to-Career Agent:** Education → Credentials → Civilian occupation → Skills → Employment opportunities.
- **Career Transition Agent:** MOS-to-civilian career mapping, resumes, skill translation, career planning, interview preparation, job-search strategy, employer matching.
- **Funding Stack Agent:** combinations of federal and state funding, grants, scholarships, employment programs and educational benefits; prevent duplicate or incompatible funding recommendations.
- **Financial Wellness Agent:** budgeting, debt education, savings, credit education, retirement education, income planning, scenario forecasting; do not represent educational tools as personalized professional financial advice.
- **Resource Navigation Agent:** nonprofits, community, state and county programs, housing, employment and educational resources, veteran organizations.
- **Family Benefits Agent:** authorized information relating to spouses, dependents, caregivers, survivors and family transition.
- **Document Agent:** classification, metadata extraction, summaries, document comparison, missing-document detection, evidence organization, duplicate detection, timeline extraction.
- **Forms Agent:** identify likely form, explain requirements, prefill permitted fields, validate completeness, identify missing information, save drafts, route to user review. Never submit legally consequential forms without explicit authorized user action.
- **Communications Agent:** letters, messages, reminders, outreach, appointment and organization communications.
- **Scheduling Agent:** deadlines, appointments, follow-ups, tasks, reminders.
- **Data Analyst Agent:** case and organizational analytics, program trends, resource utilization, workload, outcomes.
- **Security Agent:** unusual account activity, unauthorized access, high-risk actions, permission conflicts, suspicious API activity.

### 12. Agent object model
Every agent has: Agent ID, Name, Description, Avatar, Version, Status, Owner, Department, System Prompt, Capabilities, Assigned Tools, API Access, Knowledge Sources, Permissions, Data Scope, Memory Scope, Escalation Rules, Confidence Threshold, Human Review Rules, Active Jobs, Completed Jobs, Error Logs, Conversation History, Token Usage, Model Usage, Cost Metrics, Performance Metrics, Evaluation Scores, Last Updated.

### 13. Agent boundaries
Agents may not modify information outside their scope. The Education Agent may recommend education programs but must not modify a disability claim. The Financial Agent may create budgeting education but must not interpret VA claims regulations. The Claims Agent may organize claim information but must not alter educational records. Only the Orchestrator or an authorized workflow engine can coordinate cross-domain changes.

### 14. AI confidence system
Every consequential AI finding contains confidence, source, source authority, source date, jurisdiction, reason, limitations and verification status. Never fabricate confidence. *(See ADR 0003: confidence is shown as evidence and verification status; a number appears only when computed deterministically.)*

### 15. Knowledge architecture
Separate knowledge spaces: Global (public authoritative), Federal, State (each state and territory), Organization (private), Department, Case (authorized for the specific case), Agent. Maintain strict data separation.

### 16. Retrieval architecture
RAG with semantic, embedding, metadata-filtered, hybrid, keyword and full-text search; source ranking; citation retrieval; jurisdiction and date filters; authority ranking. Prioritize authoritative sources.

### 17. Document & Evidence Center
Upload, drag-and-drop, mobile scan, OCR, classification, tagging, case and evidence association, metadata, document date, source, type, summary, AI analysis, version history, duplicate detection, approval workflow, retention controls, document-level permissions, search, export. Categories: DD-214, service treatment records, VA decisions, medical evidence, statements, education documents, transcripts, resumes, employment records, financial documents, correspondence, forms, state documents, identification, organization documents. Sensitive documents require stricter access rules.

### 18. Benefits Center
Unified benefits discovery filtered by branch, component, veteran status, disability status, service era, discharge, state, county, family status, education status, employment status, age and transition stage. Results categorized (confirmed / likely / possible eligibility, more information needed, likely not eligible). Never describe uncertain eligibility as guaranteed. *(See ADR 0003 for the status vocabulary actually used.)*

### 19. Jurisdiction system
Supports 50 states, DC, territories and other supported jurisdictions. Each holds veteran agency, benefit programs, eligibility rules, property, education, employment, licensing, recreational, family and tax benefits, contact information, official links, last verified date and source history. Alabama first; the rest added without redesign.

### 20. Claims Center
Claims Dashboard: active claims, claim stage, claimed issues, evidence, examinations, pending actions, deadlines, decisions, appeals. Claim Record: Claim ID, Veteran ID, Case ID, claim type, date filed, issues, evidence, timeline, forms, decisions, examinations, correspondence, deadlines, assigned representative, notes, AI findings, source citations.

### 21. Claim timeline
Automatic chronological timeline (service → medical event → separation → initial claim → VA decision → medical evidence → new claim → exam → decision → review → appeal), filterable by condition, claim, document, event type, date and source.

### 22. ResourceHub
Searchable resource ecosystem: benefits, healthcare, housing, employment, education, transportation, food assistance, financial support, legal resources, mental wellness, family services, community and veteran organizations, emergency assistance; location and eligibility filtering, bookmarking, referral, case association, contact tracking.

### 23. Mission Transition
Separation countdown, transition checklist, MOS translator, skills inventory, resume builder, AI resume optimization, job matching, employment tracker, interview preparation, employer directory, certification and education recommendations, salary and relocation comparison, transition milestones.

### 24. Learning Academy
LMS: courses, modules, lessons, video, text, quizzes, assessments, assignments, certificates, learning paths, AI tutoring, progress tracking, instructor and student dashboards, organization curriculum. Curriculum: VA benefits, military transition, employment, financial literacy, entrepreneurship, education planning, veteran resource officer training, VSO-support training where appropriate.

### 25. MoneyLife Military
Budgeting, cash-flow visualization, savings goals, emergency fund, debt planner, credit, home- and vehicle-buying, retirement and investment education, military-to-civilian income planning, benefits income education, scenario forecasting; dashboards, calculators, content and AI coaching. Clearly distinguish education from regulated financial advice.

### 26. CRM — relationship layer
**The CRM does not control the primary VetBuddy data model.** It manages relationships surrounding the veteran. Entities: veterans, family members, VSOs, counselors, American Legion posts, nonprofits, government agencies, colleges, universities, employers, recruiters, healthcare organizations, service providers, community organizations, donors, sponsors, volunteers, vendors, partners. Capabilities: organizations, contacts, relationships, communication timeline, referral tracking, meetings, notes, tasks, documents, tags, custom fields, pipelines, partner status, referral outcomes, partner engagement, service history.

### 27. Referral management
Veteran → Organization → Service → Case. Statuses: identified, recommended, referred, contacted, appointment scheduled, service started, service completed, unsuccessful, follow-up needed. Track outcomes.

### 28. VSO / Counselor Workspace
Assigned veterans, active and priority cases, upcoming deadlines, outstanding evidence, unread messages, referrals, appointments, tasks, workload, case alerts, recent AI findings.

### 29. Command Center
Executive (users, active veterans, cases, resolutions, utilization, workload, referral outcomes, AI activity); Case Management (cases by type, overdue, average age, deadlines, staff workload); Benefits (discovered, applications, outcome trends); Transition (employment, education, certification, milestones); Resource (referrals, provider usage, geographic gaps, demand); AI (usage, tasks, cost, latency, failure rate, confidence, human escalation).

### 30. Universal workspace
Persistent shell. Sidebar: Home, My Case, VetBuddy AI, Benefits, Claims, Resources, Transition, Education, Money, Documents, Tasks, Calendar, Messages. Organizational users may also see: CRM, Cases, Members, Partners, Analytics, Automation, AI Center, Admin, Developer.

### 31. Global dashboard
Rearrangeable widgets: welcome, case progress, upcoming deadlines, recommended benefits, pending tasks, document requests, recent messages, transition, education and financial progress, resource and AI recommendations, recent activity.

### 32. Global search
Cases, benefits, veterans, documents, organizations, resources, tasks, claims, knowledge, conversations, courses; natural-language queries (e.g. "Show Alabama education benefits for a disabled veteran.").

### 33. Workflow engine
Visual automation. Triggers (veteran registered, case created, document uploaded, deadline approaching, decision received, case status changed); conditions (e.g. State = Alabama AND disability rating ≥ configured threshold → run State Benefits Agent); actions (create task, send notification, invoke agent, request document, create referral, update case, schedule review, generate report, send authorized email).

### 34. Event bus
`USER_REGISTERED, PROFILE_COMPLETED, CASE_CREATED, DOCUMENT_UPLOADED, DOCUMENT_ANALYZED, BENEFIT_IDENTIFIED, APPLICATION_CREATED, TASK_CREATED, TASK_COMPLETED, DEADLINE_APPROACHING, CLAIM_DECISION_ADDED, REFERRAL_CREATED, AGENT_TASK_STARTED, AGENT_TASK_COMPLETED, HUMAN_REVIEW_REQUIRED`.

### 35–37. Tasks, calendar, communications
Tasks: title, description, category, owner, case, due date, priority, dependency, status, reminder, source, AI-generated indicator; list, kanban, calendar and timeline views. Calendars: personal, case and organization (appointments, deadlines, training, claims events, interviews, educational deadlines, follow-ups). Communication Center: secure in-app messaging, email, SMS, push, announcements, reminders, logging; never expose private case information to unauthorized channels.

### 38–40. Multi-tenant SaaS, templates, white labeling
Individual accounts and organization workspaces (American Legion, VSO, state agency, university, nonprofit, employer) with organization, department, team, user, role, permission, workspace and configuration. Templates (Veteran Individual, VSO Office, American Legion Department / Post, University Veteran Center, State Veteran Agency, Employer Military Recruiting Team, Veteran Nonprofit) change enabled modules without separate applications. Future white labeling (logo, colors, domain, navigation, modules, terminology, email branding) never compromises data-security boundaries.

### 41–43. Database, relationships, vectors
PostgreSQL / Supabase, normalized, UUIDs, timestamps, soft deletion where appropriate, immutable audit for sensitive activity. Core domains: users, profiles, veterans, military_service_records, organizations, organization_members, roles, permissions; master_cases, subcases, case_participants, case_notes, case_events; benefits, benefit_rules, benefit_sources, eligibility_assessments; claims, claim_issues, claim_events, claim_decisions; documents, document_versions, document_metadata, evidence_links; applications, application_steps; tasks, deadlines, appointments; resources, resource_providers, referrals; education_records, courses, lessons, progress; career_profiles, skills, resumes, job_applications; financial_profiles, budgets, goals; contacts, crm_organizations, crm_relationships, communications; agents, agent_tools, agent_permissions, agent_memories, agent_jobs, agent_logs; knowledge_sources, knowledge_documents, embeddings; workflows, workflow_triggers, workflow_conditions, workflow_actions; notifications, audit_logs, security_events, api_keys, webhooks, integrations.

Central relationship: `User → Veteran Profile → Master Case → Subcases → Tasks / Documents / Applications / Claims / Referrals`. AI agents operate on authorized subsets of this graph. pgvector (or compatible) for knowledge, document, semantic case and policy retrieval and resource matching, stored apart from sensitive transactional data; never the sole source of authoritative decisions.

### 44–48. AI providers, model router, memory, human-in-the-loop, auditability
Provider abstraction (OpenAI, Anthropic, Google, Azure OpenAI, local models, Ollama, OpenRouter where appropriate); never hard-coded to one vendor. Model Router chooses by complexity, risk, latency, cost, privacy, reasoning and tool needs. Memory: session, user (approved), case (authorized), agent, organization, department; never leak organization memory across tenants. Human review for claims submissions, appeals, legal interpretation, sensitive record changes, financial decisions, external communications, document and application submission; display AI Recommendation versus Verified Human Action. Every AI action records agent, model, timestamp, user, case, prompt version, tools used, data accessed, output, sources, confidence and review status, viewable in an AI Audit Viewer.

### 49–53. Security, authentication, RBAC + ABAC, consent
Controls derived from NIST 800-53, NIST CSF, OWASP Top 10, Zero Trust; never claim FedRAMP or other certification before formal authorization. Encryption in transit and at rest, RLS, least privilege, MFA, secure sessions, refresh-token rotation, device tracking, brute-force protection, rate limiting, security event logging, secret management, key rotation, secure backups, vulnerability and dependency scanning, audit logging, retention controls, tenant isolation. Authentication via email/password, Google, Apple, Microsoft, OAuth/OIDC, MFA, recovery, device and session management; future SSO/SAML. RBAC combined with ABAC (e.g. a counselor sees only assigned, in-organization or explicitly shared cases). Veterans grant and revoke organization access, share selected documents or case areas, set expiration and review access history.

### 54–59. UX
Not government-like: clean, modern, reassuring, professional, simple, accessible, mobile-first, low cognitive load, plain language, progressive disclosure. Design system with typography, spacing, grid, cards, forms, buttons, inputs, alerts, badges, tables, tabs, modals, navigation, timelines, progress, charts, dashboards, loading, empty and error states; light, dark and high-contrast modes; keyboard and screen-reader support; WCAG.

After login: *Welcome back. Your VetBuddy Status — Benefits Found, Open Cases, Tasks, Upcoming Deadlines, Documents Needed. Recommended Next Action → Upload your latest VA decision. Ask VetBuddy: "What should I work on today?"*

Progressive onboarding: (1) Who are you? (2) Military service (3) Current transition / veteran status (4) What do you need help with? (VA benefits, disability claims, employment, education, financial planning, housing, family support, transition, community resources) (5) Create personalized workspace; continue gradually afterwards. Personalized home: a transitioning member sees separation countdown, resume, jobs, education, financial transition; a veteran managing disability benefits sees claims, evidence, deadlines, decisions, benefits. Progress engine shows per-area progress (military records, benefits review, resume, education plan, financial plan, employment).

### 60–64. Base44-first development, copilot, internal workspace, developer agents, pipeline
Optimize the initial UI for Base44 while keeping business logic, data model, API contracts, agent definitions and workflow definitions portable and documented. A Base44 Development Copilot turns approved specifications into copy-paste Base44 prompts (page requirements, entities, fields, relationships, UI, actions, permissions, validations, workflows, mock data, acceptance criteria). An internal development workspace (roadmap, features, user stories, requirements, prompts, bugs, releases, test plans, architecture, documentation, AI development agents) and developer agents (Product, UX, Frontend, Backend, Database, Security, QA, DevOps, Documentation, Base44) are separate from the veteran product and never touch veteran production data without explicit authorization. Pipeline: Requirement → Product Analysis → Architecture → Database → UX → Base44 Build Prompt → Implementation → Automated Tests → Security Review → Human Review → Staging → Production.

### 65–72. APIs, mocks, interoperability, infrastructure, jobs
API-first, REST (optional GraphQL), webhooks, event bus, streaming; versioned `/api/v1/` (e.g. `GET /veterans/{id}`, `GET /cases/{id}`, `GET /benefits`, `POST /eligibility/analyze`, `POST /agents/run`, `GET /tasks`, `POST /referrals`). Clearly marked mock connectors for VA claims, education benefits, state benefits, healthcare interoperability and employment; never depend on unavailable government APIs during the MVP. Health models able to evolve toward FHIR without overbuilding. Docker / Compose locally; cloud-agnostic (AWS, Azure, GCP, Supabase, Railway, Render, Fly.io); Kubernetes later. Components: React / Next.js-style frontend, API layer, PostgreSQL, Supabase-compatible auth, S3-compatible storage, Redis cache and queue, pgvector, internal event bus, AI provider abstraction. Background jobs for queued AI analysis, document processing, scheduled eligibility updates, notifications, reports, workflows, integration sync, index rebuilds and source revalidation, run by server workers, queues, schedules, event handlers and webhooks, not device-level daemons.

### 72–78. Observability, testing, environments, CI/CD, feature flags
Track uptime, latency, API errors, DB performance, queue depth, AI latency and cost, agent failures, security events, workflow failures, application errors. Unit, integration, API, RLS, security, accessibility, performance, end-to-end, agent and retrieval evaluation (Playwright, Vitest/Jest, k6, Locust). AI evaluated for hallucination, incorrect eligibility, missing citations, conflicting sources, improper tool use, privacy violations, cross-tenant leakage, unauthorized recommendations, incomplete workflows. Performance tests across registration, login, dashboard, case retrieval, document and benefits search, state comparison, AI conversations, orchestration, CRM search, concurrency, RLS, pooling, throttling. Environments Local → Development → Testing → Staging → Production; never develop against production. CI/CD with validation, tests, lint, security scanning, migrations, staged deployment and rollback. Feature flags (e.g. `FEATURE_CLAIMS_AGENT`, `FEATURE_STATE_COMPARE`, `FEATURE_FINANCE`, `FEATURE_LEARNING`, `FEATURE_PARTNER_PORTAL`).

### 79–83. Phased delivery
**Do not build the entire operating system simultaneously.**
- **Phase 1 (MVP):** authentication, Veteran Profile, progressive intake, Master Case, case management, VetBuddy AI, Orchestrator, Federal and State Benefits Agents, Alabama benefits dataset, ResourceHub, documents, tasks, deadlines, benefits discovery, basic claims organization, basic partner CRM, admin console, audit logging, Base44 Development Copilot.
- **Phase 2:** Mission Transition, Education Agent, Learning Academy, education benefits, employment tools, resume system, MOS translator, referral management, partner portal, Guard / Reserve Agent.
- **Phase 3:** MoneyLife Military, funding stack, Family Center, Women Veterans Center, expanded claims workflows, VSO and counselor workspaces, advanced analytics.
- **Phase 4:** nationwide state dataset, employer and university ecosystems, enterprise workspaces, white labeling, marketplace, advanced API platform, mobile application, broader interoperability.

Web first, then PWA, then native or cross-platform mobile, all on one shared API/backend.

### 84–86. Public website and differentiator
`vetbuddy.com` (public information), `app.vetbuddy.com` (authenticated workspace); potential `partners.`, `developers.`, `status.` subdomains. Landing sections: Hero, What is VetBuddy?, Find Your Benefits, Manage Your Transition, Organize Your Claims, Education, Career, Financial Wellness, ResourceHub, VetBuddy AI, Family Support, For Organizations, Privacy & Security, CTA. Message: **One Veteran. One Profile. One Plan. One VetBuddy.** VetBuddy answers "What should I do next?", turning information into personalized recommendations, case plans, workflows, checklists, deadlines, tasks, referrals, applications and measurable progress.

### 87–91. Source governance, priority, stale data, analytics privacy, notifications
Every benefits source tracks name, URL, authority level, publication and effective dates, jurisdiction, last checked, next review, version, active status. Source priority: (1) federal or state government source, (2) governing regulation / statute / manual, (3) official agency publication, (4) accredited or recognized institutional source, (5) secondary trusted source, clearly identified. Old or unverifiable critical information displays **Verification Required**. Aggregate analytics; no unnecessary PII in executive dashboards. Notifications: Critical, Important, Recommended, Informational; avoid excess.

### 92–96. End-to-end and organizational experience, audit, developer console, marketplace
Registration → Intake Agent → Master Case → Orchestrator detects needs → Federal, State, Education and Career agents → Research Quality Agent validates → "Your VetBuddy Plan" → user chooses an action → workflow updates the case → VetBuddy monitors progress. Counselor dashboard with assigned veterans, priority cases, deadlines, documents needed, pending referrals and AI reviews; counselor approves, modifies or rejects the Recommended Next Action. Every important modification records who, when, old and new values, reason, source, automated/manual and agent. Developer Console: API explorer, webhooks, API keys, logs, sandbox, agent and workflow testers, event explorer, docs, integration management. Future marketplace of approved agents, integrations, templates, content and connectors under security review and permission manifests.

### 97. Monetization architecture
Design billing support without forcing monetization into the veteran experience; veteran-access business decisions remain configurable. *(Deferred — see ADR 0003.)*

### 98–100. Solo-founder development format
Every feature is divisible into small independent jobs with: objective, user story, database, UI, API and agent changes, permissions, workflows, edge cases, security concerns, tests, acceptance criteria, Base44 build prompt. Feature responses follow: (1) Feature Objective (2) User Story (3) User Flow (4) Screens (5) Database Entities (6) Field Definitions (7) Relationships (8) API Requirements (9) AI Agents Involved (10) Workflow Events (11) Permissions (12) Security Controls (13) UI Components (14) Validation (15) Error States (16) Test Cases (17) Acceptance Criteria (18) Base44 Implementation Prompt (19) Future Expansion. Internal Product Workspace: Vision, Roadmap, Features, Requirements, User Stories, Base44 Prompts, Architecture, Database, APIs, AI Agents, Design System, Security, Testing, Bugs, Releases, Documentation. *(This replaces the earlier multi-agent CRM development concept.)*

### 101. Do NOT
Design VetBuddy primarily as a CRM; create one giant AI agent; mix tenant data; allow unrestricted agent permissions; hard-code AI vendors; hard-code benefits rules into UI components; hard-code secrets; represent AI output as an official government determination; claim legal, financial, medical, government or security certification that has not occurred; automatically submit consequential applications without user authorization; design separate incompatible web and mobile backends; create dozens of disconnected microservices before needed; build every planned module before validating the core case-management product.

### 102. Architectural rule (mandatory hierarchy)

| Layer | Role |
|---|---|
| VetBuddy | Platform |
| Case Management | **Core** |
| AI | Intelligence |
| Workflow | Operating Engine |
| Veteran Master Record | Source of Truth |
| Documents | Evidence Layer |
| Knowledge Base | Information Layer |
| ResourceHub | Resource Layer |
| **CRM** | **Relationship Layer** |
| Learning Academy | Education Layer |
| Mission Transition | Career Layer |
| MoneyLife Military | Financial Layer |
| Command Center | Administration & Analytics Layer |

### 103. Positioning
VetBuddy is an AI-powered Veteran Operating System that brings benefits, claims organization, transition planning, education, employment, financial wellness, family resources, case management, documents, community resources and personalized AI guidance into one secure workspace. For organizations, VetBuddy gives veteran-serving organizations a unified case-management, CRM, workflow, analytics, knowledge and AI-agent platform for supporting veterans at scale.

### 104–106. Deliverables, build order, first response
Deliverables span product, system, information, workspace and AI-agent architecture; agent responsibility matrix; domain model and ERD; PostgreSQL/Supabase schema; RLS model; API, event, workflow, RAG and memory architecture; security, authentication and authorization architecture; design system, screen map, wireframes, component library; veteran, counselor and Command Center dashboards; Partner CRM; developer workspace; Base44 workflow; mock APIs; testing and AI evaluation; deployment, CI/CD, monitoring, backup and DR; developer, administrator and user documentation; production-readiness checklist.

Build order: (1) product blueprint (2) domain architecture (3) database (4) security (5) AI (6) workflow (7) UX (8) MVP plan (9) Base44 prompts (10) build feature-by-feature. **Do not immediately generate the entire application. Do not start with the CRM.** The first build prompt creates the VetBuddy Workspace Shell + Authentication + Veteran Profile + Master Case foundation.

### Final design directive
Every architectural decision must answer: *Does this help VetBuddy understand the veteran's situation, determine what they may need, organize what they must do next, connect them to the right benefit or resource, and help them move that case toward a measurable outcome?* If not, reconsider whether the feature belongs in the core platform. Build VetBuddy as a Veteran Operating System, not simply another veteran website, chatbot, CRM, benefits directory, or project-management application.
