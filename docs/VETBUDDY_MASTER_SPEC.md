# VetBuddy Master Implementation Prompt v6
## Mobile, web, SaaS, privacy, benefits accuracy and release governance

Prepared October 24, 2026. Paste this directive into Claude Code or Cursor with the source project available. It governs implementation, not merely a design exercise. No domain is selected or authorized by this document.

### 0. Mission and precedence

You are the engineering lead implementing VetBuddy, the visible companion within the VeteranOS framework. Preserve the prior master prompt v5, canonical integration v2, source architecture and valid existing work. Build a framework containing CRM, not a CRM with disconnected AI screens. Deliver working, tested vertical slices across responsive web/PWA and iOS/Android clients, with Windows/Edge compatibility and an optional Microsoft Store package. Do not silently replace the existing React/Vite application or introduce Next.js, Expo/React Native, Capacitor or a desktop shell without an architecture decision based on actual source and feature needs.

Precedence: this v6 directive and the user's current instructions override conflicting earlier product requirements; verified controlling authorities and current distribution policies override stale references; canonical v2 governance overrides legacy schemas; v5 supplies the detailed product/agent/migration inventory. Historical claims that code is live, compliant, licensed, clinically validated or production-ready must be independently tested. References to a repository snapshot describe history, not its present state. Existing claims such as “no data stored,” mandatory assessments, blanket partner sharing, hardcoded current rates, anonymous community posting, or automatic referral emails must be reconciled with the explicit controls below.

Inspect repository code, exported Base44 files, migrations, contracts, tests, SDKs, archived packages and deployment configuration. Build a requirements traceability register: requirement ID, originating artifact/path, current behavior, target behavior, implementation owner, platform, applicability, test, evidence, blocker. Deduplicate by content, preserve unique requirements and source lineage. Do not delete working features or change production data as a shortcut. Mark unavailable material SOURCE_NOT_AVAILABLE and distinguish IMPLEMENTED_TESTED, IMPLEMENTED_UNVERIFIED, PARTIAL, MOCK, PLANNED, DISABLED and BLOCKED. Do not claim this prompt itself creates compliance or app-store acceptance.

### 1. Product scope to retain

Retain one Ask VetBuddy interface, Mission Brief, Today/This Week, Next Best Action, shared Master Mission/Case graph, transition timelines, benefits/resource matching, source-linked eligibility, document vault, claims/evidence organization, VA forms, education, jobs, resume generation, original career/behavioral assessments, household/survivor support, MoneyLife, housing, women veterans, Guard/Reserve, Coast Guard, installations/TAP, overseas resources, citizenship pathways, Business Launchpad, Learning Academy, partner referrals, VSN/community, LegionConnect and authorized Command Center. Include active duty, retirees, medical separation, spouses, dependents and caregivers. Phase implementation rather than omitting domains silently.

Support all 50 states, DC, Puerto Rico, Guam, US Virgin Islands, American Samoa and Northern Mariana Islands, plus jurisdiction-aware local, tribal, installation and overseas resources where verified. Alabama is the first deep pilot; an atlas entry does not prove complete benefit coverage. Distinguish current residence, domicile, prospective move, service location and program-specific residency. Historical FY2025 compensation, taxes and program values remain historical until reverified. Do not reuse fiscal-impact estimates as proven outcomes or promises.

### 2. Entry modes and account lifecycle

First screen offers equally clear Continue as guest, Create account and Sign in. Public benefits, laws/source explanations, general job/career resources, accessibility, help, privacy, terms and deletion assistance are reachable without login. Never require an account solely to view public information. Gate saved personal work, syncing, private document vaults, managed cases and delegated sharing by the actual need for an account.

**Guest:** search/filter generic benefits by voluntarily chosen state, component, broad service category or goal; read current sources; view explanations and generic form guidance. Generic search should use structured catalog search without sending personal data to AI. Do not create a hidden account, persistent profile, device fingerprint or cross-site tracking identifier. Do not retain search text, health details, personal form content, conversation content or assessment responses. Anonymous rate-limit/security processing must be minimized and disclosed; an IP address may be processed by hosting infrastructure, so do not claim that no data is ever processed. Offer Clear session. If a limited guest resume/assessment/form workspace exists, keep content in memory by default and export locally; warn that closing loses work. Remote AI/OCR processing requires separate explicit consent and an approved ephemeral processing path. If provider retention cannot meet the guest promise, disable that sensitive guest path. Explain limits rather than pretending browser memory is secure erasure. Guest-to-account conversion imports only the items the user chooses after consent, never the whole session silently.

**Private account:** minimum verified email or selected identity-provider account; do not demand SSN, rating letters, DOB, military identity or medical records to register. Support verification, sign in/out, secure recovery, session expiration, all-device logout, passkeys/MFA where supported, profile correction, data export, connected-account revocation and deletion. Avoid email-account enumeration and insecure account linking. A user must be able to refuse optional AI, analytics and notifications and still use suitable core functions. Adult family members have independent access; family membership does not confer permission. Default self-service accounts to adults; guardian-managed dependent facts remain separate from child accounts. Any minor self-service rollout requires age-specific legal and safety review.

**Managed case:** invitation identifies organization, purpose, exact records, recipients, permissions and expiration before acceptance. Explicit granular consent and current legal authority are required. Organization admin status is not permission to inspect all veterans. Representatives have scoped time-limited delegated access with revocation. Show a user-readable access/share history. Organization retention obligations must be explained before case sharing; withdrawal does not magically recall information lawfully received by another controller.

### 3. Actual deletion, not account deactivation

Provide Settings → Account → Delete account in iOS, Android and web, with a similarly discoverable path in Windows packages. Also provide a public web account/data deletion request route that works when the app is uninstalled. Keep the final URL configurable; do not invent a domain. Explain what will be deleted, any lawful exceptions, expected times and billing consequences. Offer export before deletion without making export mandatory. Use proportional reauthentication/identity verification, accessible recovery alternatives and no forced phone call or support email as the normal path. A confirmation screen may prevent accidental deletion; do not add obstructive dark patterns.

Implement an authenticated, idempotent deletion workflow with states REQUESTED, VERIFIED, ACCESS_REVOKED, PURGING, PROCESSOR_PENDING, COMPLETE and FAILED_RETRYABLE. Immediately revoke access/refresh tokens, devices, push tokens, sharing grants, jobs and connected government/provider tokens. Handle Sign in with Apple token revocation when used. Stop queued retries, reminders, emails, referrals and background AI jobs from recreating data; maintain a minimized deletion tombstone only where needed for this purpose. Do not keep identifiable audit trails forever under an “immutable” label.

Purge or irreversibly de-identify personal records, documents/OCR, derived facts, embeddings, search projections, summaries, caches, messages as legally appropriate, resumes, assessment results, form drafts, exports, temporary uploads, support attachments, analytics identifiers and processor-held copies. Handle multi-user household/case records with field-level ownership rather than deleting another person's lawful data. Inventory legal holds and independent organization records, identify the basis and deadline, restrict retained material, and communicate exclusions accurately. Remove login identity only after the worker can complete authorized cleanup without keeping a reusable personal credential. Audit proofs contain minimal non-content metadata.

Backups need an approved expiration schedule, restricted restore access and a deletion-replay process so restored data is removed before serving traffic. Never promise immediate physical removal from every backup. Propagate deletion to contracted processors and record acknowledgement/failure/retry. User sees request receipt, status and completion/remaining exceptions. Deleting an account must not require keeping a paid subscription. Explain store-managed cancellation separately and provide subscription-management links; integrate cancellation where permitted. App uninstall, sign-out, subscription cancellation and account deletion are different actions. Tests must verify the data graph and provider cleanup, not just disappearance of a user row.

### 4. Privacy promises and consent

Implement these product commitments: no sale of personal information; no sharing for cross-context behavioral advertising; no targeted-advertising SDKs, session replay of private screens, data-broker disclosures or marketing pixels in protected flows; no training of VetBuddy models on personal content; prohibit processor training on that content through actual contracts/settings. Do not state that a vendor has zero retention or no training unless verified for the contracted product and all enabled features. No health/trauma/claims data in employer, community or advertising domains. No hidden monetization of veterans' information.

Do not publish “we do not collect or store any data” while operating saved accounts. Use minimum necessary data, purpose-limited processing and user-selected saving. Saved records are limited to the requested service and stated retention, plus narrowly documented legal/security exceptions. Reject an incompatible SDK/vendor or disable the feature rather than contradict privacy promises. Disclose processors, processing locations, purposes, categories, retention, third-party AI, security logging, user-directed external sharing and lawful disclosures. Never promise absolute security or unconditional secrecy.

Required draft privacy language, customized only after a verified data-flow inventory:

> VetBuddy does not sell your personal information or share it for cross-context behavioral advertising. You can browse public benefits as a guest without creating an account. Guest searches are not saved as a personal profile. Our systems and service providers process limited technical information needed to deliver and secure the service, as described in this policy. If you create an account, we store the account details and information you choose to save so we can provide those features. We use approved service providers only for disclosed service purposes and do not permit them to use your personal content to train their models. Personal information is sent to an external AI service only after the required disclosure and your explicit permission. Sharing with a representative or organization requires your authorization or another applicable lawful basis. You can manage consent, export information and request account deletion. Our retention schedule explains any limited legal, security and backup exceptions.

This is implementation-target copy, not a publishable attestation before controls and contracts exist. Publish accessible Privacy Notice, Terms of Use, AI/recommendation notice, consumer-health notice where applicable, cookie/storage notice, retention schedule, subprocessor list, accessibility/help contact and deletion instructions. Use configurable legal operator/contact fields and block release if unresolved. Do not invent a legal operator from inconsistent operator-name references in old documents. Version policies and consent receipts; distinguish acknowledgement of a notice from consent to optional processing. Separate purposes for account service, sensitive data, AI processing, organization sharing, optional analytics, marketing and notifications. Withdrawal is as easy as granting permission; server enforces it, including queued jobs and agents. No preselected optional toggles, bundled medical consent or coercive cookie banner. Provide GPC/universal opt-out handling where applicable, and avoid labeling necessary service processors as data sales merely because they are third parties.

### 5. Benefits and professional boundaries

Use this common notice with short contextual versions at relevant actions:

> VetBuddy is an independent information and organization platform, not VA, DoD or a government agency. Its benefit matches, career suggestions and form assistance are recommendations based on the information you provide and identified sources. They are not the law, an official eligibility or rating decision, medical advice, a diagnosis, a medical nexus opinion, legal representation or a guarantee of approval. The responsible agency determines eligibility and benefits. Verify current requirements with the administering agency and, for VA claims assistance, a currently VA-accredited representative, claims agent or attorney. Check any separate professional license with the appropriate state authority.

Use authoritative effective-dated rules and evidence, not a disclaimer as a substitute for accuracy or lawful practice. AI must not diagnose conditions, assign/predict an official disability rating, fabricate a nexus letter, invent symptoms, embellish service, manufacture evidence or coach exaggeration. Permit faithful organization of user-supplied records, chronology and quotations with source/page references; distinguish original evidence from generated summaries. Historical rating facts may be displayed as documented; educational examples must be clearly hypothetical. No automatic conversion of symptom descriptions into a diagnostic claim or rating forecast. Any existing SymptomDCAnalyzer or rating tool must be audited and restricted accordingly.

Deterministic eligibility engine outputs PRELIMINARY_MATCH, NEEDS_INFORMATION, NEEDS_EVIDENCE, DOES_NOT_MEET_ENCODED_RULES, SOURCE_STALE, CONFLICTING_AUTHORITY or HUMAN_REVIEW_REQUIRED, with per-condition reasoning. VERIFIED refers to a fact/source, not a promise that an agency will award a benefit. Record service-component/date/authority precisely; do not assume Title 10, Title 32, inactive duty, state active duty and all Guard/Reserve service are equivalent. Evaluate program-specific service, discharge, residence, dependent and entitlement rules. Missing facts never become “eligible.” Benefit stacking/offset/election checks need explicit versioned authority; unknown compatibility means review, not an inferred stack. Rank urgency, fit, goals, freshness, evidence burden and actionability without paid referral influence.

Each recommendation includes program, administering agency, jurisdiction, official link/citation, rule/effective dates, verification date, known facts, missing facts/evidence, limits, conflicts, recommended next step and review path. Agency decision history is a separate record. Material changes invalidate affected cached determinations. “Current” requires an approved freshness policy; preserve historical law for historical questions.

### 6. Representatives and referrals

For VA claims representation, verify the individual in VA Office of General Counsel's accreditation registry and the organization's VA recognition. The American Legion, VFW or DAV name/logo, nonprofit registration, state incorporation, accreditation in another profession or a claimed job title does not by itself prove the particular person is currently authorized. Attorneys also require an appropriate current state-bar check; clinicians and other licensed professionals require their relevant board check. A state registry complements, and does not replace, VA accreditation. Do not call a VSO “licensed” as a general substitute for accredited.

Store verification source/time, individual and organization identifiers, scope, state-license status where relevant and VERIFIED, STALE, NOT_FOUND, SUSPENDED or PENDING states. NOT_FOUND is not an invented finding of fraud; ask the user to verify and contact the responsible authority. Do not invent API access or scrape beyond permitted use. If registry access is unavailable, provide the official lookup and mark verification pending. Show status and time at referral. Block new referrals claiming current accredited representation when status is stale/unknown until verified. Recheck before sensitive transfer; do not block general directory navigation. Do not claim formal partnerships, endorsements or permissions to use logos without evidence. No undisclosed referral commissions or payment-linked recommendation ranking.

A referral is a user-approved transmission of specified records to a named recipient, not an automatic email generated merely by creating a case. Bind approval to recipient, document versions, purpose, payload hash and expiration; log minimal delivery and outcome. Respect VA representation/fee restrictions; do not sell unaccredited claims preparation through a SaaS label. Legal review must assess actual claims-assistance behavior under 38 CFR Part 14 before launching it. Disclaimers cannot authorize regulated representation.

### 7. Forms, burial and supporting records

Preserve Forms Hub, draft vault and official form links. Add guided pre-need burial eligibility assistance using the current official VA Form 40-10007 and instructions after verification; include existing 21-0966 and 21-526EZ workflows only with verified current templates and authorized functionality. Do not treat pre-need eligibility as a completed reservation, guaranteed burial or approval of every related burial payment. Agency-specific distinctions, survivor rules and current service requirements come from authoritative sources.

Fetch official form revision, instructions and OMB information from the responsible agency; store hash/version and field mapping. Never invent a signature, attestation, missing fact or medical statement. Mark generated packets DRAFT—REVIEW BEFORE USE, identify user-provided facts and missing evidence, and allow correction. The user chooses whether to save a draft; sensitive guest drafts stay in memory/local export. Warn users about downloaded files on shared devices.

Require a review screen, authenticated reauthorization and explicit approval before any supported submission. Approval binds the exact form version, content, destination and attachments; subsequent changes require new approval. Use provider-supported signatures/identity and authorized APIs only. If no approved submission integration exists, offer export and an official submission link and state “not submitted.” Never simulate a receipt, POA, intent-to-file timestamp or government status. Retain minimum submission receipt and provenance under the approved retention schedule. Any binding election, representation appointment or legal deadline receives appropriate human review.

### 8. Career, jobs, resumes and assessments

Retain military occupation translation, jobs, education/credentials, apprenticeships, career plans, original behavior/strengths profile and resume workflows. Use verified O*NET/CareerOneStop or other licensed data integrations with current terms/attribution; historical docs are not proof of API access. Guest generic career resources remain open. A user can skip an assessment and still search benefits/jobs. A personality assessment is not mandatory to obtain public information.

Resume builder supports entry/import, faithful skill translation, editable drafts, accessible export and optional account saving. Never invent employment, education, awards, licenses, skills, military duties or metrics. Separate generated suggestions from confirmed facts. No employer disclosure of health, disability, claims, assessment or dependent data without specific authority/permission; do not include them in resumes automatically. Job matches show source, freshness, location, compensation context and no guarantee of hiring; flag scams and expired postings. Do not auto-apply or send a resume without payload-specific consent.

Retain original Level 2 Drive/Influence/Steadiness/Precision and strengths content as a design input after IP/provenance and quality review. Call it VetBuddy Behavioral Style & Strengths Profile; do not claim it is Everything DiSC, a validated clinical test or a certified commercial instrument. Commercial assessments require actual licenses and qualified interpretation when stipulated; free availability is not proof of unrestricted app reuse. Deterministic versioned scoring, scoring transparency, accessibility, skip/withdraw controls and error handling are required. Results are optional career exploration, not diagnostic, employability/pass-fail, benefits eligibility or employer screening. No inferred mental-health status from behavioral style. Wellness is a separate opt-in session-only domain, excluded from career scoring, employer exports and ordinary agent context. Do not launch clinical screening content, thresholds or safety escalation until qualified review and current usage rights are documented. Do not introduce persistent Redis wellness storage while claiming RAM-only handling; inventory persistence, swap, snapshots, logs and TTL behavior across the actual system.

### 9. Architecture and backend enforcement

Start with a modular monolith: web/PWA/BFF, FastAPI domain API, workers, PostgreSQL/Supabase, private object storage and a model/integration gateway. Logical boundaries: identity/tenancy; consent/delegation; profile/household; public catalog; rules/eligibility; source/evidence; recommendation/conflicts; vault; mission/case/CRM; career/assessments; forms/submissions; integrations; audit/security; privacy/deletion; optional billing. Extract microservices only for demonstrated scale, isolation or operational need. Avoid 50 premature services.

Traffic: client → edge/WAF/rate limits → gateway/BFF → authenticated domain services. Check object, field, tenant, role, purpose, delegation and current consent on every sensitive operation. Do not trust a caller-supplied tenant/person ID or frontend hidden button. Authorize document download, search, embeddings, exports, realtime topics, background jobs and agent tools, not just REST records. Public catalog is separate from personal data. No direct agent SQL or raw credentials. A Trust Kernel is shared policy enforcement across ALL entry points; it is not a magical service the rest of the system can bypass.

Use OIDC/OAuth authorization code with PKCE where applicable, verified redirect allowlists, short-lived tokens, refresh-token rotation, audience/issuer validation, replay protection and revocation. Use secure HttpOnly/SameSite web cookies with CSRF protections where appropriate; native credentials in OS secure storage, not AsyncStorage/localStorage. Require MFA/step-up for privileged operations and sensitive sharing. Secrets use workload identity plus managed secret storage/KMS; field-level envelope encryption for high-risk identifiers and refresh tokens with narrowly separated decrypt permissions. No production PII in development or client-side admin/service-role keys. Rotate credentials; separate environments; redact logs/traces/errors. TLS, least-privilege DB roles and RLS are mandatory layered controls, including tenant-isolation tests against worker/admin bypasses. Never log SSNs, raw prompts, token values, medical text, form payloads or signed download URLs.

Uploads: enforce size/type/magic bytes, malware scanning, quarantine, private storage, metadata stripping where appropriate, safe OCR/parser isolation, egress restrictions and short-lived authorized downloads. Treat uploaded documents and retrieved web content as untrusted data; ignore embedded instructions. Prevent prompt injection, SSRF, tool escalation and exfiltration. Restrict external tools by allowlisted destinations, validated schemas, budgets and timeout. Require consent-aware redaction/minimization before model requests. Policy decisions are deterministic; an LLM validation pass cannot replace access control.

Document original evidence remains unmodified while lawfully retained; version summaries separately. Source registries and public rule history may have long-lived version history, but personal “immutability” must not defeat deletion. Store provenance, effective date, jurisdiction, source version/hash, review state and supersession. Vector stores are derived indexes with identical authorization and deletion, not the truth/eligibility database. Cache keys must include policy/tenant/subject context, and sensitive responses must not enter a public CDN cache.

API baseline under /api/v1: public benefit/resource/source search; account/session/profile; consents/delegations; missions/cases/tasks; eligibility evaluations and recommendations; resume drafts/exports; assessment sessions/results; document upload/read/delete; form drafts/validate/export/submit; referrals/approvals; privacy exports/requests/deletion status; notification preferences/subscriptions; AI consent/reporting. Use explicit request/response JSON Schemas/OpenAPI, pagination, bounded queries, idempotency keys for side effects, consistent error codes, versioning and no sensitive query strings. Never expose an unauthenticated arbitrary-user deletion endpoint. Verified deletion requests create narrowly scoped worker authorization.

Tables/entities include users, tenants, memberships, identities, device_sessions, consent_receipts, delegations, profile_facts, households, service_periods, sources/source_versions, benefits/rule_versions, eligibility_evaluations, evidence_links, missions/cases/tasks, documents, resume_drafts, career_assessments, form_versions/drafts, action_approvals, submissions, referrals, notification_preferences, privacy_requests/deletion_jobs, retention_rules/legal_holds, processor_requests and minimized audit_events. Public catalog has no veteran PII. Define ownership, retention, classification, indexes, foreign keys and RLS per table. Do not migrate old seeds directly to trusted current facts.

Workers use transactional outbox, bounded retries/backoff, idempotent handlers, dead-letter review, duplicate-event handling and trace IDs. Government APIs live behind dedicated permission-aware adapters with LIVE/SANDBOX/MOCK/DISABLED states, circuit breakers and honest user-upload/manual fallbacks. Never assume access to VA/DoD/identity services or scrape credentials. Government-data retention restrictions apply independently of generic consent. Honor session-only requirements until a separately lawful and explicitly authorized persistent integration is approved.

### 10. Platform-specific acceptance matrix

Create one dated matrix per distribution target with requirement source/section, applicability, implementation, evidence, test and remaining blocker. Recheck official policy and build SDK requirements at submission; distinguish effective rules from future announced changes. A website working in Edge does not require Microsoft Store certification. Microsoft does not govern iOS/Android distribution. A PWA install is not an App Store submission and a thin WebView is not automatically acceptable.

**Apple / iOS / iPadOS:** implement public guest browsing and in-app account deletion when accounts can be created. Audit current App Review Guidelines sections 2, 3, 4 and 5, including login-service equivalence/Sign in with Apple applicability, privacy, sensitive information, minimum functionality, UGC and accurate metadata. Sign in with Apple is not universally required merely because an account exists; document applicability/exceptions to login-services rules. Disclose third-party AI recipients and obtain explicit permission before sending personal data. Create accurate App Privacy answers from observed app and SDK behavior; include PrivacyInfo.xcprivacy, required-reason API declarations and third-party SDK privacy/signature requirements where applicable. No tracking SDKs by default; if tracking is ever introduced, treat policy change/ATT applicability as a blocked new scope, not a pretext to ask all users for tracking now. Use appropriate purpose strings and just-in-time camera/photo/location/notification access with alternatives and no unrelated permissions. Never require notification access to use core service. Audit Keychain, ATS, secure links, background execution limits and safe app-switcher previews. Package a signed build using Apple's then-required SDK/Xcode; complete age/category/content and any health-related declarations accurately. Provide working reviewer access or a complete demo mode with synthetic data, live backend/support/privacy links, screenshots and no placeholder claims. If paid digital access is enabled, apply current storefront-specific purchase/subscription rules and approved entitlements rather than assuming external web checkout is always permitted. Provide restore/manage purchases and verified server entitlement handling where applicable.

**Google Play / Android:** provide in-app deletion and a functional external web deletion request resource, consistent Data safety answers including every SDK, accessible privacy policy and transparent sensitive-data disclosures/consent. Review current User Data, permissions, health-content, AI-generated-content, UGC, Families, billing and impersonation policies for actual features. Include in-app reporting of problematic AI outputs and moderation response, not only an external email. Complete health-app declarations where applicable; do not market diagnostic/medical functionality the product does not provide. Target the required Android API at submission; official guidance reviewed for this prompt states new apps/updates target Android 16/API 36 from August 31, 2026, subject to applicable exceptions and later changes. Verify native dependency/16 KB page-size requirements where applicable. Use signed AAB, protected signing keys, current supported SDKs, scoped storage/photo picker, notification permission and Android backup/data-extraction rules; exclude protected records/tokens from automatic backups. Verified App Links, Android Back, edge-to-edge/insets, keyboard and large-screen behavior must work. No permission prompts before context or excessive location access. Use current Play Billing policy and receipt/entitlement verification if digital subscriptions are enabled; document any eligibility for exceptions rather than inventing one. Fulfill account-specific testing/verification and production-access requirements in Play Console.

**Microsoft / Windows / Edge:** responsive Edge experience and accessible keyboard/mouse/touch interaction are required. If submitted to Microsoft Store, verify current Store Policies (reviewed version 7.20 effective October 22, 2026), identity/publisher verification, product value, accurate metadata, privacy/consent, content/age ratings, security, account management, testing instructions and product-type commerce rules. Produce the appropriate signed/package-identified application or PWA package with least-privilege capabilities, icons, supported architectures and update behavior. Audit WebView2/native bridge isolation if used. Store packaging does not justify assuming all Windows applications must use Microsoft's payment system; determine the rule for the actual product. Windows notifications/startup/background operations follow platform consent/preferences. Do not require Microsoft login just because a user is on Windows.

**Web/PWA:** no hardcoded final domain. Use deployment configuration for origins, canonical URLs, callback allowlists, universal/app links, privacy/deletion/support routes and email sender settings. At release populate a controlled HTTPS origin, HSTS after validation, secure DNS/TLS, restrictive CORS, CSP, frame controls, content-type protections, secure cookies and appropriate referrer policy. Protect account/workspace pages from indexing and shared caching. Public benefit pages can be indexed but must contain no personal facts. Test Safari/iOS, Chrome/Android, Edge/Windows, Firefox and current supported desktop browsers, narrow phones through tablets/desktops. PWA manifest has stable id, scope, start URL, name, icons/maskable assets, theme/display settings and accessible install guidance. A service worker is a chosen reliability feature, not universally mandatory for Edge installation. Cache public shell/catalog only under freshness rules, never private API responses/documents/form drafts. Clear app-managed private caches on logout/deletion. Handle service-worker version transitions without losing work or replaying submissions. Offline mode clearly labels cached public data and disables sensitive server operations; do not claim the session authenticated offline is valid for new disclosures. Downloads, print/export and browser navigation must work.

### 11. Refresh, toggles, notifications and accessibility

Pull-to-refresh is a requested product feature, not a blanket legal/store requirement. Implement it on appropriate mobile lists with visible accessible Refresh buttons and keyboard equivalents. Refresh uses authorized idempotent reads, loading/success/error states, last-refreshed time, timeout, cancellation and preserved scroll/filter context. It does not resubmit forms or silently replace user edits. Background refresh and push are best-effort within OS limits; show last sync and offer manual refresh. Handle denied permission, unsupported browsers, poor connections, stale data, token expiration and provider outage without a spinner forever.

Provide real server-enforced toggles for AI assistance, optional analytics, notification topics, email/SMS preferences, sensitive AI use, document saving and organization sharing, with immediate effect and consent receipts. Distinguish account-wide choices from device OS permissions. Essential service/security notices may need separate treatment disclosed accurately. Push content defaults to generic text, no disability, health, financial, claim or dependent facts on the lock screen. Deep links reauthorize access. Maintain APNs/FCM/web-push token lifecycle, logout cleanup and preference enforcement. Marketing needs independent opt-in and compliant opt-out handling. Never promise push delivery or that toggling notifications cancels legal deadlines.

Use WCAG 2.2 AA as the engineering target, with VoiceOver, TalkBack and Narrator, semantic controls, labels/errors, focus order, visible focus, contrast, reduced motion, text enlargement/reflow, captions where relevant and alternatives to gestures/color/dragging. Native touch targets follow the actual platform guidelines. Forms, login, consent, deletion, assessment and generated documents must be accessible. Test manual assistive technology flows, not only automated scanners. Do not claim WCAG 2.2 is the identical legal standard under every law; record applicable ADA/Section 504/508 or public-sector contract requirements separately.

### 12. SaaS operations and conditional commerce

Implement tenant isolation, role/permission management, organization offboarding, user export/deletion, consent/terms versions, DPA/subprocessor management, incident response, retention, change management, backup restoration, status/support, uptime monitoring and abuse prevention. Set measurable service objectives, recovery targets, escalation owners and tested restore procedures before promising an SLA. Monitor redacted metrics, source freshness and agent failure rates. Audit code/dependencies/secrets, SDK data flows and outbound requests; produce SBOM, threat model and privacy-impact assessment. Penetration/security review must cover APIs, RLS, uploads, mobile storage and authorization bypass. Production rollback and migration rollback must be rehearsed. Never use real personal records as test fixtures.

Earlier v5 excludes unsolicited monetization. Preserve that restriction: do not invent tiers, prices, paid referrals or checkout. SaaS architecture does not require immediate billing. If the owner enables subscriptions, release is conditional on an approved product/region/store billing matrix, transparent total/recurring price, trial conversion/renewal disclosure, explicit purchase consent, receipts, accessible cancellation, refunds and restore/manage purchases as applicable. Use processor-hosted payment handling and minimize PCI scope; never store card PAN/CVV. Server validates signed webhooks, transaction identifiers and entitlements with replay/idempotency controls. Cancellation and deletion remain independent. Assess ROSCA, FTC Act and effective state automatic-renewal laws and then-current rules/court decisions; do not cite a vacated rule as binding. Include tax/financial retention analysis and no guarantee that every payment record is deletable. Billing is not a way to charge impermissibly for unaccredited VA claims assistance.

### 13. Federal/state legal applicability and release gates

There is no single “SaaS compliance law,” and a prompt cannot certify compliance with all laws. Build an obligation register from current official statutes/regulations/regulator guidance and qualified legal review. For EACH supported US state, DC and inhabited territory record privacy, consumer-health, breach-notification, reasonable-security, consumer-protection, auto-renewal, children/teens, biometrics, communications, accessibility and veteran-claims-assistance rules as applicable. Record enacted/effective dates, amendments, thresholds, scope/exemptions, data vs entity exemptions, consumer/employee context, deadlines, source URL/section, responsible reviewer, required controls, test evidence and review date. Never infer nonprofit exemption, HIPAA exemption or small-business exemption globally. Count thresholds using actual operations. UNKNOWN is a blocker for the affected sensitive feature/jurisdiction, not a fabricated “compliant” row. Do not mislabel proposed legislation as law. Review conflicts and federal/tribal jurisdiction explicitly. Guest public navigation may remain available when a particular regulated workflow is disabled.

Seed the register for all 56 jurisdictions rather than claiming the seed is a completed 50-state legal survey. Federal categories include FTC Act deceptive/unfair practices; applicable FTC Health Breach Notification Rule; HIPAA/HITECH only when covered-entity/business-associate facts trigger them and necessary BAAs/security exist; COPPA when directed to under-13 users or actual knowledge applies; ADA and contract-specific Section 504/508; VA accreditation/claims representation and fee restrictions under 38 CFR Part 14 and relevant Title 38 provisions; CAN-SPAM/TCPA for actual communications; E-SIGN/UETA when signatures/records rely on them; ROSCA and effective renewal requirements if billing; GLBA/FCRA/financial-services restrictions only if activities trigger them; FERPA/student-data obligations only where relevant institutional relationships/data invoke them. Career screening, employer-use or automated consequential decisions require separate discrimination/employment/AI-law analysis; default VetBuddy to user-controlled career exploration. Do not permit an employer/admin to repurpose assessment scores into hiring screening. If public/federal contracts, CUI, tax data or substance-use records are introduced, evaluate their additional contractual/statutory regimes before enabling them. Do not advertise FedRAMP, FISMA, HIPAA, SOC 2 or government endorsement without the actual scope/evidence/authorization.

At minimum research and assess California CCPA/CPRA and related privacy/medical rules, Washington My Health My Data, Nevada consumer-health provisions and other applicable comprehensive/sensitive-data statutes, including states without broad revenue thresholds for relevant health obligations. Benefit interests and inferred disability/health conditions may be sensitive health data even when not obtained from a clinic. Do not treat being outside HIPAA as being outside health privacy law. Alabama's breach law is a specific pilot obligation, not a nationwide notification template. Incident workflow maps actual individuals/jurisdictions/data/affected processors and regulator/consumer deadlines with counsel, rather than hardcoding one “72-hour US rule.” Use interim containment and evidence preservation without exposing records in general logs.

Universal product baseline: minimization, purpose limits, transparent notices, no sale/ad sharing, appropriate sensitive-data consent, access/correction/export/deletion/withdrawal, authorized-agent requests and appeals where applicable, non-discrimination, reasonable security, processor agreements and risk assessments. These helpful controls do not replace each law's exact scope, exceptions and deadlines. Provide a verified rights-request channel to guests and non-account data subjects too. Avoid disproportionate identity collection to exercise rights. No direct minor self-service, biometrics, ad-tech, employer screening or new regulated advice until a separate approved scope is implemented; OS-local passkeys do not justify building a biometric identity database.

International access/resource listings do not prove compliance abroad. Assess GDPR/UK GDPR, ePrivacy, transfers, representation and other local obligations if territorial scope is triggered; gate unsupported personal-data workflows rather than promise worldwide compliance. Review official law/policy changes before release and on a documented recurring operational schedule. Counsel approval is a real release artifact, not an AI signature or invented certification. Continue building safe reversible functionality while marking release blockers honestly.

### 14. Required tests and evidence

Implement meaningful automated and manual tests:

1. A logged-out guest searches public benefits without an account or persistent personal profile; no query content appears in DB/logs/analytics/traces. Inspect network/storage behavior including SDKs and CDN logs. Clear session removes app-held state. Anonymous requests cannot enumerate private data.
2. Registration, verification, recovery, passkeys/MFA, logout, all-session revocation and provider linking work without account takeover/enumeration. Expired/deleted sessions fail closed.
3. Tenant A cannot read/write/export/search/subscribe to Tenant B records through guessed IDs, worker events, vectors, signed URLs or APIs; household access remains scoped.
4. AI-disabled and consent-denied users receive no personal-data model calls. Consent withdrawal invalidates queued work, and external-sharing authorization is checked immediately before execution. Uploaded prompt injection cannot obtain other records or invoke unauthorized tools.
5. Deletion removes the user's owned data and derived indexes, revokes Apple/provider/session/push tokens, initiates processor deletion, handles shared records/legal holds and prevents restore/job resurrection. Simulate processor failure, duplicate request, backup restore and final status. Verify declared retention against actual infrastructure.
6. Unknown Guard/Reserve service authority, missing residency, stale rules, conflicting sources or unknown stacking produces uncertainty/review and no fabricated eligibility. Current sources and historical effective dates yield different appropriate results.
7. Resume exports contain only confirmed facts; original assessment scoring is reproducible; wellness data never influences jobs, employers or career scores. Licensing and skip controls work.
8. Burial/other forms validate against official current templates; unsupported submission returns NOT_SUBMITTED. Replay and payload change cannot bypass approval; no signature/evidence fabrication.
9. Stale/unverified VA individual accreditation cannot be displayed as verified. A recognized organization alone cannot grant the individual status. Referral transfer requires named-recipient consent and rechecks.
10. Refresh never triggers a write/submission; offline, slow network, expired session, double tap, background resume, permission denial, provider outage and cache update paths have recoverable UI. Notification payloads contain no sensitive text.
11. Complete keyboard, screen-reader, text enlargement, contrast and gesture-alternative checks through signup, guest search, consent, resume, forms and deletion on all supported clients. Test protected-cache leakage on shared devices.
12. Verify actual signed app builds, store declarations, privacy links, deletion URL, SDK inventory, reviewer/demo access and current submission settings. Run native device/platform tests; a web browser test cannot certify native behavior. Billing tests are conditional on billing enabled, including webhook replay, cancellation, refund and restoration.

### 15. Deliverables and implementation sequence

Create docs/CURRENT_STATE, REQUIREMENTS_TRACEABILITY, SOURCE_MANIFEST, CONFLICT_REGISTER, ARCHITECTURE/ADRs, DATA_MAP_AND_RETENTION, THREAT_MODEL, AGENT_CONSTITUTION, API/OpenAPI, AUTHORIZATION_MATRIX, PRIVACY_AND_CONSENT_SPEC, ACCOUNT_DELETION_RUNBOOK, PLATFORM_POLICY_MATRIX, LEGAL_APPLICABILITY_REGISTER, ACCESSIBILITY_TESTS, DATA_MIGRATION_MAP, TEST_EVIDENCE, RELEASE_BLOCKERS and OPERATIONS_RUNBOOK. Choose suitable file extensions. Include versioned privacy/terms/disclaimer drafts with unresolved legal operator/contact fields clearly marked, and a store submission checklist per target. Do not publish placeholders. Implement the actual backend, migrations, RLS, clients, workers, APIs and tests; documents are not substitutes.

Sequence: (1) inspect/deduplicate/map existing sources and preserve baseline; (2) public guest catalog + governed sources + accessible shell; (3) minimum private accounts + real consent + private storage/export/deletion as one tested slice; (4) deterministic benefits + source-linked recommendations + mission/case; (5) resume/career/original optional assessment; (6) form draft/review/export including pre-need burial, verified referral and approved integrations; (7) native client/platform packaging and privacy/permission behavior; (8) organization tenancy, community moderation/report/block controls and other retained modules; (9) optional approved billing; (10) security, legal, accessibility and store evidence gates before production release. Phases can be refined around proven dependencies but account collection must not launch before deletion/security are implemented.

First execution: inspect the source tree and provided artifacts, identify architecture/privacy conflicts, produce the traceability and source inventory, then implement the first incomplete safe vertical slice. Run relevant tests. Report concrete files changed, demonstrated user journeys, actual test/build results, remaining unverified integrations and specific release blockers. Do not say “meets every federal/state law” or “approved by Apple/Google/Microsoft” unless evidence supports the exact assertion. No final domain, pricing or unsupported government partnership is authorized.

### 16. Official reference register — reverify at implementation/submission

These references support requirements design; not every potentially applicable law or policy is researched exhaustively here. Recheck the actual policy sections, regional exceptions, effective dates and console requirements before release.

- Apple App Review Guidelines: https://developer.apple.com/app-store/review/guidelines/
- Apple account deletion: https://developer.apple.com/help/app-review/guideline-reference/5-1-1-account-deletion
- Apple third-party AI/privacy update: https://developer.apple.com/news/?id=ey6d8onl
- Google account deletion: https://support.google.com/googleplay/android-developer/answer/13327111
- Google Data safety: https://support.google.com/googleplay/android-developer/answer/10787469
- Google AI-generated content: https://support.google.com/googleplay/android-developer/answer/13985936
- Android target SDK: https://developer.android.com/google/play/requirements/target-sdk
- Google policy center: https://play.google/developer-content-policy/
- Microsoft Store policies: https://learn.microsoft.com/en-us/windows/apps/publish/store-policies
- Microsoft PWA development: https://learn.microsoft.com/en-us/microsoft-edge/progressive-web-apps/how-to/
- VA accreditation lookup: https://www.va.gov/ogc/apps/accreditation/
- VA accreditation/fees: https://www.va.gov/ogc/accreditation.asp
- VA representative FAQs: https://www.va.gov/resources/va-accredited-representative-faqs/
- 38 CFR Part 14: https://www.ecfr.gov/current/title-38/chapter-I/part-14
- HHS covered entities/business associates: https://www.hhs.gov/hipaa/for-professionals/covered-entities/index.html
- FTC Health Breach Notification Rule: https://www.ftc.gov/business-guidance/resources/complying-ftcs-health-breach-notification-rule-0
- FTC COPPA: https://www.ftc.gov/legal-library/browse/rules/childrens-online-privacy-protection-rule-coppa
- California CCPA: https://oag.ca.gov/privacy/ccpa
- Washington consumer-health privacy: https://www.atg.wa.gov/protecting-washingtonians-personal-health-data-and-privacy
- Nevada NRS 603A: https://www.leg.state.nv.us/nrs/nrs-603a.html
- Alabama breach notification: https://www.alabamaag.gov/data-breach-notification/
- DOJ web accessibility: https://www.ada.gov/resources/web-guidance/
- FTC negative-option rule status: https://www.ftc.gov/legal-library/browse/rules/negative-option-rule
- Current federal rulemaking context: https://www.federalregister.gov/documents/2026/03/13/2026-04952/rule-concerning-the-use-of-prenotification-negative-option-plans

END OF V6 GOVERNING DIRECTIVE. The following source appendix preserves v5's complete detailed product inventory; conflicting legacy requirements are superseded by the directive above.


---

## Source review scope and reconciliation notes

This consolidation located 50 named VetBuddy/VeteranOS files. Review used extracted document text, schema/data and packaged text-source inspection, archive inventory and the roadmap image. It is a requirements synthesis, not a line-by-line security audit, a new live GitHub/Base44 inspection, an execution test of the code archives or an exhaustive legal opinion. Other generically named uploads referenced inside prior files are not independently reviewed here unless included in these artifacts. Archived source packages and quoted audit findings must be revalidated against the actual shipping repository. Duplicate formats/versions are retained in the inventory. The tar.gz package was inventoried; the corresponding zip supplied text-source review. No prior “production-ready” claim is accepted as proof.

Key reconciliations:
- Earlier zero-storage language conflicts with persistent accounts/CRM. V6 requires truthful mode-specific disclosures and backend retention controls.
- A reverse-engineering document describes authentication falling back to a demo user on API failure. Treat this as a priority verification/remediation item; production authentication must fail closed.
- Another source documents duplicate responsive route trees that can select a hidden desktop layout. Verify and use one responsive route tree instead of assuming mobile works.
- Earlier deletion included demo state removal or broad cascade deletion. V6 requires a data-graph, processor and backup-aware deletion workflow that respects shared records.
- Assessment documents mix original content, licensed instruments, optional wellness and historical clinical/provider claims. V6 preserves original exploration while requiring rights/quality verification, no diagnostic claims and strict wellness isolation.
- The forensic-audit PDF largely contains preview-shell HTML. It does not prove a comprehensive application audit.
- Source documents disagree about the legal operator and runtime stack. V6 blocks invented legal identity and unnecessary rewrites.
- Older prompts mention auto-referral emails, paid tiers, hardcoded rates and all-data agent context. V6 makes sharing explicit, billing conditional, rules versioned and context minimum necessary.
- The complete v5 prompt below is retained for its detailed route/entity/function/agent inventories, not as evidence of working functionality. Canonical integration v2 is also embedded to keep migration/source governance available in this single handoff.


## File review inventory

| Source file | SHA-256 (first 16 characters) | Review basis |
|---|---|---|
| # VeteranOS — Multi-Layer Consolidation and Build Prompt.pdf | a38bb28637740216 | Extracted document/text or packaged source review |
| # VeteranOS — Multi-Layer Cons….pdf | 886548bf7985f413 | Extracted document/text or packaged source review |
| 5e9e4683c_VetBuddy-Assessment-Architecture.docx | 43eee5f4beddc70d | Extracted document/text or packaged source review |
| 83c80800e_vetbuddy-career-quiz.html | b59fa1aab562d8a4 | Extracted document/text or packaged source review |
| VetBuddy_Complete_Software_Architecture_Reverse_Engineering(1).docx | 04cc7a54a2e6ea25 | Extracted document/text or packaged source review |
| VetBuddy_Complete_Software_Architecture_Reverse_Engineering.docx | 06a586a27bca5c2d | Extracted document/text or packaged source review |
| Estimated Fiscal and Social Impact of Deploying VetBuddy Veteran Transition OS in Alabama.pdf | 088efb632f0118ff | Extracted document/text or packaged source review |
| Military-to-Civilian Transition Finances: A Data-Driven Roadmap for VetBuddy(1).pdf | ec816a505ca5cf1b | Extracted document/text or packaged source review |
| Military-to-Civilian Transition Finances: A Data-Driven Roadmap for VetBuddy.pdf | ec816a505ca5cf1b | Extracted document/text or packaged source review |
| VetBuddy Build-to-Production Roadmap.png | 6b83c94e0d32b80c | Roadmap image inspected |
| VetBuddy-App-Blueprint.pdf | ad9d6b519a0901d1 | Extracted document/text or packaged source review |
| VetBuddy-Forensic-Audit.pdf | 89a9436f16a7a1a2 | Extracted document/text or packaged source review |
| VetBuddy-VeteranOS-Architecture(1).html | 249d158b4792615a | Extracted document/text or packaged source review |
| VetBuddy-VeteranOS-Architecture.html | 249d158b4792615a | Extracted document/text or packaged source review |
| VetBuddy_CLAUDE.md | 63f5c79c56b9b5fb | Extracted document/text or packaged source review |
| VetBuddy_Canonical_Data_Integration_Spec_v2.md | e340f0fa23628cb3 | Extracted document/text or packaged source review |
| VetBuddy_Canonical_Data_Integration_v2.zip | 92fa3a286c262071 | Extracted document/text or packaged source review |
| VetBuddy_Canonical_Integration_Spec_v1.md | f43a1ddd6a1c419d | Extracted document/text or packaged source review |
| VetBuddy_Claude_Code_Master_Prompt_v5.html | 957992a455c4f8a5 | Extracted document/text or packaged source review |
| VetBuddy_Claude_Code_Master_Prompt_v5.md | 94f5d389bca01bf5 | Extracted document/text or packaged source review |
| VetBuddy_Code_Only_Reverse_Engineering_Master_Prompt(1).docx | e7b0ac2f2f333271 | Extracted document/text or packaged source review |
| VetBuddy_Code_Only_Reverse_Engineering_Master_Prompt.docx | e7b0ac2f2f333271 | Extracted document/text or packaged source review |
| VetBuddy_Final_Production_Build_Master_Prompt_v4.docx | 19416410b27af8bc | Extracted document/text or packaged source review |
| VetBuddy_Foundation_Architecture_Handoff.html | 3c177d228e5a4ae3 | Extracted document/text or packaged source review |
| VetBuddy_Master_Application_Reverse_Engineering_Prompt.pdf | d940e42106f46813 | Extracted document/text or packaged source review |
| VetBuddy_Master_Build_Prompt_FINAL.docx | 154c5aa6829ff23d | Extracted document/text or packaged source review |
| VetBuddy_Master_Build_Prompt_FINAL.pdf | 2ed3a3c4484fb175 | Extracted document/text or packaged source review |
| VetBuddy_Multi_Agent_OS_Master_Architecture.pdf | 1a0730b01cb959a6 | Extracted document/text or packaged source review |
| VetBuddy_Unified_Architecture_Master_Build_Prompt_v3(1).pdf | 5099e0cff58b620c | Extracted document/text or packaged source review |
| VetBuddy_Unified_Architecture_Master_Build_Prompt_v3.pdf | 5099e0cff58b620c | Extracted document/text or packaged source review |
| VetBuddy_VeteranOS_Master_AI_CRM_Workspace_Prompt.md | ead9489891ce1512 | Extracted document/text or packaged source review |
| VetBuddy_VeteranOS_Master_AI_CRM_Workspace_Prompt.txt | ead9489891ce1512 | Extracted document/text or packaged source review |
| VeteranOS_Career_Enterprise_Reverse_Engineering_Master_Prompt.pdf | 151824dcd3da28b0 | Extracted document/text or packaged source review |
| VeteranOS_Claude_Cursor_GitHub_Field_Test_Tutorial.pdf | fde59a2c560a3878 | Extracted document/text or packaged source review |
| VeteranOS_Multi_Layer_Consolidation_Master_Prompt.md | e9cf7ad750f1fc03 | Extracted document/text or packaged source review |
| VeteranOS_Unified_Master_Build_Prompt.pdf | 00db90c5fbed714a | Extracted document/text or packaged source review |
| VeteranOS_VetBuddy_First_Runnable_Vertical_Slice_v1.0.0.tar.gz | 990f5e6c754a99bf | Archive path inventory; text-source counterpart reviewed from ZIP |
| VeteranOS_VetBuddy_First_Runnable_Vertical_Slice_v1.0.0.zip | 6318dc48a018f398 | Extracted document/text or packaged source review |
| VeteranOS_VetBuddy_Master_Application_Build_Prompt.pdf | 76a9e75c85e117a8 | Extracted document/text or packaged source review |
| VeteranOS_VetBuddy_Onboarding_MultiLayer_CRM_Master_Prompt.md | 4a288d3f191cdc75 | Extracted document/text or packaged source review |
| VeteranOS_VetBuddy_Reverse_Engineering_Master_Prompt.pdf | 24bfd88a10ffc4ba | Extracted document/text or packaged source review |
| vetbuddy_alabama_production_repo.zip | d1384410bfbf7201 | Extracted document/text or packaged source review |
| vetbuddy_app.html | 374ceb11cfc8a732 | Extracted document/text or packaged source review |
| vetbuddy_canonical_contract_v1.schema.json | 61b4d65fdbc92d2c | Extracted document/text or packaged source review |
| vetbuddy_canonical_schema_v2.sql | c90003e834c29df9 | Extracted document/text or packaged source review |
| vetbuddy_canonical_seed_v2.json | 13c3f0d3a803caab | Extracted document/text or packaged source review |
| vetbuddy_code_stack.zip | 875df1d789e7bc31 | Extracted document/text or packaged source review |
| vetbuddy_legacy_mapping_v1.json | b90b250cb8237c03 | Extracted document/text or packaged source review |
| vetbuddy_legacy_migration_manifest_v2.json | 7d07e6f8b2be4d70 | Extracted document/text or packaged source review |
| vetbuddy_os_demo_v6.html | db5c338b2041705b | Extracted document/text or packaged source review |


---

# Appendix A — Preserved v5 source prompt (subordinate to v6)

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


---

# Appendix B — Canonical integration v2 (subordinate to v6)

# VetBuddy Canonical Data Integration Specification v2.0

## Purpose

This package converts the uploaded VetBuddy/VeteranOS/VetConnect material from overlapping prompts, prototype code, seed data, and research notes into one integration model. It does **not** externally re-verify benefit, legal, contact, rate, or eligibility facts. Source values are preserved where useful and any record that lacks authoritative per-record provenance is quarantined as `needs_verification` rather than silently treated as production truth.

## Executive decision

Do not merge the uploads into another flat “master JSON.” Use **PostgreSQL as the canonical system of record** and JSON only as a versioned interchange envelope. Separate people/cases from public resource data, separate eligibility from mission routing, and separate time-sensitive rates from narrative content.

The integration is organized into eight bounded data planes:

| Plane | Canonical responsibility | Sensitivity |
|---|---|---|
| Identity & CRM | tenants, users, contacts, households, cases, tasks, referrals, consent | restricted |
| Military profile | service periods, component/status, occupations, deployments, disability/dependent facts | restricted |
| Public catalog | resources, organizations, jurisdictions, installations, contacts, locations | public/internal |
| Eligibility & policy | effective-dated rules that evaluate explicit profile facts | internal governed |
| Governed knowledge | laws, forms, claim stages, education/insurance explainers, content versions | public/internal governed |
| Rates & calculations | pay/BAH/BAS/VA scenarios/COL/tax parameters and reproducible outputs | internal governed |
| Source governance | sources, versions, verification, imports, lineage, review status | internal governed |
| Derived/search/analytics | search index, ranking projections, privacy-safe analytics events | derived |

## Data-quality disposition of uploaded sources

| Source | Disposition | Canonical use |
|---|---|---|
| `VeteranOS_Multi_Layer_Consolidation_Master_Prompt.md` | KEEP | Architecture and migration authority |
| `Pasted text (2)(1).txt` | MERGE UNIQUE / ARCHIVE | Requirements traceability only after master precedence |
| `Pasted text (2).txt` + `Pasted text(1).txt` | DEDUPLICATE | Exact duplicate pair; retain one raw copy, mine durable requirements/data, discard build chatter from canonical layer |
| `Pasted markdown (3).md` | KEEP AS RESEARCH INPUT | Resource/facility/state research staged behind verification |
| `Pasted markdown(1).md` | ARCHIVE AFTER UNIQUE DIFF | Near duplicate of prior research report; preserve only unique deltas |
| `Pasted markdown (2).md` | HISTORICAL RULESET | FY2025 financial data; never an unversioned “current” default |
| `Pasted text (4).txt` | MIGRATE + QUARANTINE | 12 VetConnect resources + legacy Alabama agency seed transformed to v2 format |
| `Pasted text (5).txt` | RETIRE RUNTIME | Salvage concepts only; replace eligibility logic |
| `Pasted text (6).txt` | RETIRE SCHEMA | Migration source/compatibility only; superseded by PostgreSQL canonical model |

Local checksum analysis found the two 551 KB `Pasted text` files are byte-for-byte identical. The two national-resource Markdown reports are highly similar but not identical, so they should be diffed rather than blindly deleting one.

## Material removed from production canonical data

1. Assistant/build narration, “Revert” logs, deployment chatter, and historical UI implementation notes.
2. Placeholder state rows or generated mock benefits that are not backed by an authoritative source.
3. Fictional demo people outside dedicated test fixtures.
4. Duplicate copies of resources, research, rules, and screens.
5. Frontend-hardcoded legal rules, eligibility rules, rates, contact lists, or rating schedules.
6. FY2025 values presented as current without a ruleset/effective date.
7. Static staff names/contact values lacking freshness metadata when a stable office/facility contact can be retained instead.
8. Legacy eligibility shortcuts that infer facts the user never supplied.

## Critical irregularities corrected in the model

### 1. Resource type was overloaded

Legacy `resource_type` mixed **provider identity** (`federal`, `state`, `nonprofit`) with **urgency** (`crisis`) and mixed scope (`federal_state`). v2 separates:

- `provider_type`
- `coverage_scope`
- `urgency`
- taxonomy/category
- accreditation/verification status

### 2. ResourceHub improperly owned veteran PII

Legacy resource tables stored name, email, phone, discharge, disability, homelessness, income, caregiver and dependent status. v2 keeps those facts in Identity/CRM/Military Profile and keeps the public ResourceHub catalog independent. User-to-resource relationships belong in saved-resource, referral, case, or recommendation tables.

### 3. Eligibility engine fabricated status

The prototype added `active_duty`, `veteran`, `national_guard`, and `reservist` to every profile and inferred VA healthcare enrollment from discharge status. v2 requires explicit facts and three-valued evaluation (`true`, `false`, `unknown`). `unknown` must not be coerced into eligibility.

### 4. Global income threshold was not program-safe

The prototype treated annual income below $30,000 as universal `low_income`. v2 stores program/jurisdiction/effective-date-specific thresholds inside rule sets. No global threshold is used.

### 5. Crisis ranking was mixed with generic search relevance

A crisis resource received a blanket score boost even without crisis context. v2 uses a separate urgency/safety policy. Crisis resources can be surfaced by context and safety policy without contaminating ordinary benefits relevance scoring.

### 6. JSON-to-SQL ingestion lost fields

The VetConnect JSON supports email, text and chat contacts and service-era attributes, but the prototype SQL/Python loader did not preserve all of them. v2 uses child `resource_contacts` plus governed eligibility rules so contact channels and rule dimensions are not dropped.

### 7. Time-sensitive financial data was mixed with product logic

The financial report is FY2025-specific. v2 loads such material as `calculation_rule_sets` with `effective_from`, `effective_to`, version, source and status. A calculation result stores the exact ruleset version used so it can be reproduced later.

## Canonical integration envelope

```json
{
  "schema_version": "vetbuddy.integration.v2.0",
  "record_type": "resource",
  "record_id": "resource:res005",
  "name": "Post-9/11 GI Bill (Chapter 33)",
  "classification": {
    "provider_type": "federal_agency",
    "coverage_scope": "national",
    "urgency": "routine",
    "categories": ["benefits_compensation"],
    "services": ["tuition", "housing_allowance", "books_stipend", "transferability"]
  },
  "coverage": {"jurisdiction_codes": [], "is_national": true},
  "contacts": [{"channel": "website", "value": "<legacy value>", "is_primary": true}],
  "eligibility": {
    "legacy_flags": ["post_9_11_service"],
    "ruleset_ref": null,
    "evaluation_mode": "unverified_legacy_flags",
    "human_review_required": true
  },
  "governance": {
    "data_status": "needs_verification",
    "source_date": "2026-04-28",
    "last_verified_at": null,
    "authoritative_source_present": false
  },
  "source_refs": ["src:vetconnect-json-1.0.0"],
  "legacy": {"legacy_id": "RES005", "source_file": "Pasted text (4).txt"}
}
```

## Controlled statuses

`data_status`:

- `verified` — authoritative source checked and within review window
- `provisional` — credible but awaiting final review
- `needs_verification` — imported legacy record lacking sufficient verification
- `stale` — verification window expired
- `historical` — valid only for an earlier effective period
- `placeholder` — demo/test only, never production matching
- `rejected` — failed validation or source policy
- `archived` — retained only for lineage
- `superseded` — replaced by a newer canonical record/version

## Eligibility contract

Profile facts must be explicit and typed. At minimum, use:

```json
{
  "service": {
    "branch": "army",
    "component": "reserve",
    "status": "separated",
    "service_periods": [],
    "discharge_character": "honorable",
    "pay_grade": "E-6",
    "occupation_codes": []
  },
  "location": {
    "jurisdiction_id": "...",
    "country_code": "US",
    "installation_id": null,
    "overseas": false
  },
  "benefits": {"va_disability_rating": 70, "va_health_enrolled": null},
  "household": {"has_dependents": true, "caregiver_role": false},
  "employment": {},
  "citizenship": {"screening_requested": false}
}
```

Eligibility rules use a small JSON expression language such as `all`, `any`, `not` with typed predicates. Rules are effective-dated and source-linked. A resource match should return `eligible`, `possibly_eligible`, `not_eligible`, or `insufficient_information`, plus the matched/missing predicates and ruleset version.

## Mission Router is not the eligibility engine

Keep two independent decisions:

| Engine | Question | Output |
|---|---|---|
| Eligibility | “Could this program apply under its rules?” | eligibility state + evidence/missing facts + ruleset/source |
| Mission Router | “What should the user do next?” | primary lane, secondary lanes, next action/document/referral, urgency, confidence, policy version |

This prevents a high-priority mission need from being mistaken for statutory/program eligibility.

## Resource deduplication strategy

Use deterministic matching before fuzzy matching:

**Exact keys:** authoritative external ID → canonical source URL + external ID → legacy namespace/ID.

**Normalized candidate key:** provider organization + normalized program name + jurisdiction + coverage scope + location/facility.

**Fuzzy matching:** may create a merge candidate only. It must not auto-merge records with different effective periods, different source authorities, different locations, or materially different eligibility.

When merged, preserve every legacy ID and source record through `legacy_refs` and `resource_source_links`.

## Source precedence and conflict resolution

1. Do not pick the newest text fragment merely because it is newer.
2. Preserve each conflicting value with its source/effective period in staging.
3. Prefer an approved authoritative source only after verification policy accepts it.
4. If two accepted sources conflict, mark the canonical record `provisional` or `needs_verification`; do not silently select one.
5. Current display APIs must include source date, verification state and confidence where the underlying domain requires freshness.

## Specialty datasets

Women-veteran, Guard/Reserve, caregiver, survivor, tribal, overseas and recreation data should **not** each create a parallel resource table. They become:

- shared `resources`
- shared `organizations`
- shared `locations`
- shared eligibility rule sets
- taxonomy terms and `resource_collections` for specialty discovery

Keep compatibility views/routes during migration, but all writes go to canonical records.

## Installation normalization

Do not create a 33-column record with one field per service. Use:

- `military_installations`
- `installation_services`
- `installation_contacts`
- `installation_eligibility`
- `resource_locations`
- `source_records` / `verification_records`

A service such as legal assistance, TAP, education, medical, childcare or citizenship support becomes a repeatable child record. This handles worldwide installations without schema redesign.

## Organization and accreditation normalization

A VSO/nonprofit/legal provider is an `organization`. Accreditation is a separate effective-dated record with status and source. Never infer accreditation from organization type or name. Resource search can filter or badge verified accreditation without turning it into a boolean on the organization itself.

## Financial data policy

FY2025 values from the uploaded financial research should be loaded only with:

```text
calculation_key = military_transition_compensation
version         = FY2025
status          = historical
source/effective period required
```

New rate years are additional rule sets, never destructive overwrites. Calculations are server-reproducible and store input snapshot, ruleset version and output.

## VetBuddy API boundary

Recommended v2 endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/resources` | governed catalog/search |
| `GET /api/v1/organizations` | providers/VSO/nonprofits/accreditation |
| `GET /api/v1/jurisdictions` | state/territory/tribal/local/global geography |
| `GET /api/v1/installations` | installation + repeatable services |
| `POST /api/v1/eligibility/evaluate` | deterministic resource-rule evaluation |
| `POST /api/v1/mission-router/evaluate` | workflow prioritization |
| `GET /api/v1/sources/{id}` | provenance/freshness |
| `POST /api/v1/imports` | idempotent ingestion |
| `POST /api/v1/calculations/run` | versioned deterministic calculations |

Current legacy routes can remain as compatibility projections until the frontend is migrated.

## Ingestion pipeline

```text
RAW UPLOAD
  -> immutable source object + checksum
  -> parser
  -> staging records
  -> schema validation
  -> field normalization
  -> exact duplicate detection
  -> fuzzy merge candidates
  -> source/provenance validation
  -> human review when required
  -> canonical upsert (idempotent)
  -> search index
  -> compatibility views/API
```

Each import returns parsed, accepted, rejected and duplicate counts plus field-level issues. Never use `INSERT OR REPLACE` as the migration strategy because it hides data loss and overwrites lineage.

## Migration sequence

1. Freeze legacy write paths and checksum every source.
2. Load files into immutable raw storage and register source records.
3. Migrate jurisdictions/organizations/resources first; do not migrate veteran PII into ResourceHub.
4. Convert specialty datasets into collections/taxonomies over the shared catalog.
5. Build explicit service/profile facts and replace the legacy eligibility engine.
6. Load FY2025 financial values as historical rule sets; create new current rule sets only from separately verified sources.
7. Build compatibility views for existing VetBuddy screens/routes.
8. Run duplicate, referential-integrity, source, permission, RLS and calculation golden tests.
9. Switch reads to canonical APIs, then writes.
10. Archive legacy runtime/schema files after parity testing; retain raw sources and lineage.

## Acceptance gates before a record can influence a user recommendation

A production recommendation record must have a canonical ID, valid taxonomy, valid geography/scope, valid contact shape, source record, data status other than placeholder/rejected/archived, effective-date handling when applicable, and a deterministic eligibility rule or an explicit “informational only/no eligibility rule” designation.

Any resource with `needs_verification` may appear only in an administrative/research view unless product policy explicitly permits a clearly labeled provisional display. It must not be used to assert eligibility.

## Files in this integration package

- `VetBuddy_Canonical_Data_Integration_Spec_v2.md` — this specification
- `vetbuddy_canonical_schema_v2.sql` — PostgreSQL/PostGIS integration backbone
- `vetbuddy_canonical_seed_v2.json` — migrated VetConnect v1 seed in canonical envelope, quarantined pending verification
- `vetbuddy_legacy_migration_manifest_v2.json` — source-by-source disposition, including duplicate handling

## What remains intentionally unresolved

This normalization pass does not claim that benefit amounts, contact details, agency leadership, program names, eligibility rules, tax laws, VA rates or installation data are currently correct. The uploaded research itself identifies volatile and incomplete fields. Those facts need a separate authoritative-source verification pass before promotion to `verified` production status.
