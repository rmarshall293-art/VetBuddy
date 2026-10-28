# Requirements traceability — master prompt v6

One row per v6 requirement group. Status uses the v6 §0 labels.
**Evidence** names the test or file that proves the status; a row without
evidence is not IMPLEMENTED_TESTED. **Blocker** is what stops the next
status. v5 rows (route, entity and agent inventories) remain in
`docs/GAP_MATRIX.md` and the spec's Appendix A; canonical v2 crosswalks are
in ADR 0004.

| ID | v6 § | Requirement | Status | Evidence | Blocker / next |
|---|---|---|---|---|---|
| V6-01 | 0 | v6 governs; v5 + canonical v2 preserved as subordinate appendices | IMPLEMENTED_TESTED | `docs/VETBUDDY_MASTER_SPEC.md` (sha256 b35113d8…); v5 appendix byte-identical to the prior spec; ADR 0004 | — |
| V6-02 | 0 | v6 implementation-label vocabulary everywhere | IMPLEMENTED_TESTED | migration 0012; `V6Vocabulary.test_sql_enforces_v6_labels`; corpus validator | — |
| V6-03 | 0 | Requirements traceability register | PARTIAL | this file | Base44 export and v2.0 source are SOURCE_NOT_AVAILABLE, so their rows can't be traced |
| V6-04 | 0, 9 | No silent stack replacement (Vite, Next.js, Expo, Capacitor) | IMPLEMENTED_TESTED | ADR 0002 and 0004; no framework added | Vite export SOURCE_NOT_AVAILABLE |
| V6-05 | 1 | Retain all product domains, phased | PARTIAL | GAP_MATRIX "Open work" | most domains PLANNED |
| V6-06 | 1 | 50 states + DC + 5 territories; Alabama first; atlas ≠ coverage | IMPLEMENTED_TESTED | 57 jurisdictions; `test_jurisdictions_labelled_and_complete`; 0 verified (G1) | G1 |
| V6-07 | 1 | FY2025 values stay historical until reverified | PARTIAL | corpus rate rows UNVERIFIED/ILLUSTRATIVE; `kernel_usable_rates() == []`; crosswalk to `historical` in ADR 0004 | rate reverification (G1) |
| V6-08 | 2 | Guest / Create account / Sign in equally clear; public info never needs an account | PARTIAL | web shell start page; guest app needs no account | "Sign in" for returning users needs real identity (G17) |
| V6-09 | 2 | Guest: no hidden account, profile, fingerprint, retained content | IMPLEMENTED_TESTED | `test_guest_preview_persists_nothing`; standalone smoke: no non-font requests, no storage | hosting/CDN log disclosure needs the deployment (V6-31) |
| V6-10 | 2 | Guest "Clear session" | IMPLEMENTED_TESTED | standalone smoke (`Clear session` → brief gone) | — |
| V6-11 | 2 | Private account: minimal data, no SSN/DOB/records to register | IMPLEMENTED_TESTED | dev signup stores tenant + user only; unknown fields 422 (`test_validation_errors_are_structured`) | — |
| V6-12 | 2 | Verification, recovery, passkeys/MFA, all-device logout, account linking | BLOCKED | auth is MOCK (signed dev tokens) | G17 identity provider decision |
| V6-13 | 2 | Managed case: invitation, scoped delegation, share history | DISABLED | Mode C unreachable (API 409 + DB CHECK) | security review; delegation workflow |
| V6-14 | 3 | In-app account deletion (Settings → Account → Delete account) | IMPLEMENTED_TESTED | `POST /api/v1/me/delete`; `Deletion.*` (8 tests); web smoke deletes an account | — |
| V6-15 | 3 | Deletion purges the full data graph; other accounts untouched; no resurrection | IMPLEMENTED_TESTED | `test_deletion_purges_the_whole_data_graph_and_nothing_else` (row counts across every tenant table; outbox empty); vault tables included, and 0014 fails if any tenant table is unreachable by the purger | documents, embeddings, caches don't exist yet; the purge covers them automatically once they live in tenant tables |
| V6-16 | 3 | Deletion state machine and receipt without personal data | IMPLEMENTED_TESTED | `privacy_deletion_receipt`; `test_receipt_holds_no_personal_identifiers`; public status by receipt | FAILED_RETRYABLE only becomes reachable with external processors |
| V6-17 | 3 | Revoke sessions/tokens immediately | IMPLEMENTED_TESTED | `test_sessions_fail_closed_after_deletion` (every protected route → 401 SESSION_INVALID) | real token revocation list arrives with G17 |
| V6-18 | 3 | Proportional reauthentication before deletion | MOCK | typed confirmation phrase only | step-up auth needs G17 |
| V6-19 | 3 | Public web deletion request (app uninstalled) | BLOCKED | status lookup is public; *requesting* needs identity verification | G17; configurable `public_origin` |
| V6-20 | 3 | Shared household/org records: field-level ownership, never over-delete | PARTIAL | shared tenants refused (`test_shared_tenant_is_refused_not_over_deleted`) | per-person ownership model |
| V6-21 | 3 | Backups, processors, legal holds: expiry, propagation, replay on restore | PLANNED | runbook; receipt states the dev build has none | hosting decision; processor contracts |
| V6-22 | 3, 4 | Export before deletion, optional | IMPLEMENTED_TESTED | `GET /api/v1/me/export`; `Export.*`; works after consent withdrawal | — |
| V6-23 | 4 | No sale, ad sharing, tracking SDKs, session replay, pixels | IMPLEMENTED_TESTED | no third-party script except Google Fonts; standalone smoke asserts no other requests | self-host fonts before release to remove the last third party |
| V6-24 | 4 | Truthful privacy copy; draft language not published early | IMPLEMENTED_TESTED | `privacy_notice_draft` in config, unrendered; `ReleaseGates.*` | data-flow inventory, processors, counsel |
| V6-25 | 4 | Separate consent purposes; withdrawal as easy as grant; server-enforced | PARTIAL | purpose allowlist + 9 foreclosed purposes (0010); in-transaction checks; revocation test | AI, analytics, notification and sharing purposes arrive with those features |
| V6-26 | 4, 15 | Legal operator, contact, origin are configurable and release-blocking | IMPLEMENTED_TESTED | `legal_operator/privacy_contact/public_origin: null` in config; `test_no_invented_domain_or_operator_in_pages` | owner decision (Master Record §7.1 rows 1–3) |
| V6-27 | 5 | Common notice wording | IMPLEMENTED_TESTED | `common_notice` in config → guest app trust page; `test_required_language_is_the_config` | counsel review before release |
| V6-28 | 5 | Eligibility vocabulary PRELIMINARY_MATCH … HUMAN_REVIEW_REQUIRED; missing facts never become eligible | PARTIAL | Benefit Vault matcher emits only the seven v6 outcomes and `determination: none` (`tests/vault/test_matcher.py`, `test_agent.py`). Production policy `verified_only` shows no PRELIMINARY_MATCH (`test_catalog_carries_the_common_notice_and_no_determination`). The Mission Router still never screens (`benefit_screening: DISABLED`) | G1 verified rules; VD21 |
| V6-29 | 5 | Guard/Reserve authority never assumed | IMPLEMENTED_TESTED | DB CHECK + router validation + tests | — |
| V6-30 | 5 | No diagnosis, rating prediction, nexus, coaching | PARTIAL | rating calculator is math on entered numbers only; claims-boundary pattern scan; vault OutputGuard and ClaimsBoundaryGuard on every response (`test_output_guard_blocks_prohibited_language`) | agents beyond the vault |
| V6-31 | 6 | Representative verification (VA OGC registry), referral as approved transmission | PLANNED | app links VA's official Find-a-Rep search only | registry access terms; referral workflow |
| V6-32 | 7 | Forms: official templates, DRAFT marking, NOT_SUBMITTED, burial 40-10007 | PLANNED | no form flows built | verified current templates |
| V6-33 | 8 | Career, resume (no invented facts), optional Behavioral Style & Strengths Profile | PLANNED | ARCHITECTURE §3–4 | CB-01/02 ADA metamorphic test first |
| V6-34 | 9 | Authorization on every sensitive operation; no caller-supplied tenant | IMPLEMENTED_TESTED | principal binds tenant; forced RLS; cross-tenant tests; purge bound to caller (`test_purge_function_is_bound_to_the_caller`); vault account routes resolve the tenant from the session only (`test_account_rows_are_tenant_scoped_and_exported`) | uploads, vectors, workers, realtime don't exist yet |
| V6-35 | 9 | Personal "immutability" must not defeat deletion | IMPLEMENTED_TESTED | audit append-only except the sanctioned purge; `test_audit_stays_append_only_outside_the_purge` | — |
| V6-36 | 9 | Uploads: scanning, quarantine, injection defenses | PLANNED | no upload path | document intake service |
| V6-37 | 9 | Workers: outbox, retries, idempotency, dead letter | PARTIAL | outbox written transactionally with idempotency keys | dispatcher (G19) |
| V6-38 | 10 | iOS / Android / Microsoft Store packaging and policy matrix | PLANNED | sequence step 7 | native client ADR; signed builds |
| V6-39 | 10 | Web/PWA security headers, no hardcoded domain, no private caching | PARTIAL | CSP, nosniff, no-store on `/api`; no domain in code (test) | HSTS, manifest and service worker need the real origin |
| V6-40 | 11 | Pull-to-refresh, real server toggles, safe push | PLANNED | — | notifications and AI toggles arrive with those features |
| V6-41 | 11 | WCAG 2.2 AA with manual assistive-technology passes | PARTIAL | semantic forms, focus, 44px targets, reduced motion; browser smoke in light/dark at 390 px | axe pass + VoiceOver/TalkBack/Narrator audit |
| V6-42 | 12 | SaaS operations: SLOs, restore drills, SBOM, threat model, pen test | PLANNED | — | hosting decision |
| V6-43 | 12 | Billing only if owner enables it; never on claims help | DISABLED | no billing code; R4 in governance | owner decision |
| V6-44 | 13 | Legal applicability register for 56 jurisdictions | PLANNED | — | counsel; seed the register with UNKNOWN rows, never "compliant" |
| V6-45 | 14 | Required tests 1–12 | PARTIAL | tests 1, 3, 5 (in-DB scope), 6 (router side) automated | 2, 4, 7–12 depend on PLANNED features |

## v8 amendment (Base44 directive v7.0 + v8; ADR 0005 §7)

v8 governs the Base44 runtime. These rows trace what it adds that applies to this repository.

| ID | Requirement | Status | Evidence | Blocker / next |
|---|---|---|---|---|
| V8-01 | CRM is a contained partner-relationship context; never CRM-first; no CRM role sees cases | PLANNED | CLAUDE.md; no CRM code | partner CRM slice |
| V8-02 | No sales, revenue or lead language in veteran UI; matches never monetized | IMPLEMENTED_TESTED | claims-boundary and vault language guards; no billing | — |
| V8-03 | SARGE: optional, skippable tour persona over one orchestrator; crisis help throughout | PLANNED | onboarding has crisis floor on every page | tour content |
| V8-04 | Optional work-style assessment: opt-in, versioned, never adjudicates | PLANNED | ARCHITECTURE §4 licensing flag | licensed or original items |
| V8-05 | One task/deadline owner; claims kanban on one canonical subcase timeline | PARTIAL | tasks belong to the Master Mission | claims domain |
| V8-06 | Guard/Reserve atlas: an inventory, not proof; versioned, stale values marked | IMPLEMENTED_TESTED | vault registry statuses, staleness (SOURCE_STALE) and caveats; corpus Guard/Reserve leads | G1 |
| V8-07 | 56-jurisdiction footprint; 57-item counts need a crosswalk | IMPLEMENTED_TESTED | 57 = 56 + federal `US` (ADR 0005 §7); American Samoa SOURCE_NOT_AVAILABLE | territorial source |
| V8-08 | Regression: guest search creates no user record and sends nothing to agents | IMPLEMENTED_TESTED | `test_guest_use_persists_nothing` (every tenant table counted) | — |

## Release blockers (v6 §15: account collection must not launch before these)

1. G17 real identity: verification, recovery, MFA/passkeys, step-up before deletion, public deletion request (V6-12, V6-18, V6-19).
2. Backups, processors and legal holds defined and wired into deletion (V6-21).
3. Legal operator, privacy contact and public origin set by the owner; privacy notice and terms reviewed by counsel (V6-24, V6-26).
4. Accessibility audit with assistive technology (V6-41).
5. G1 verified rules before any eligibility output (V6-28).
