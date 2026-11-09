# ADR 0004 — Adopt master prompt v6; reconcile its vocabularies with the code

**Status:** Accepted, 2026-10-25

**Context.** `VetBuddy_Master_Prompt_v6` (24 Oct 2026) supersedes v5 where they
conflict. It embeds v5 unchanged (byte-identical to the previous
`docs/VETBUDDY_MASTER_SPEC.md`) and the Canonical Data Integration Spec v2 as
subordinate appendices. The `.html` upload renders the same Markdown and is
not committed separately. Integrating v6 must not break what already works:
RLS, consent, the deterministic router, the reference corpus, single
authorship and the browser/server parity.

**Decisions.**

1. **Spec.** `docs/VETBUDDY_MASTER_SPEC.md` is now the v6 file. Nothing from
   v5 is lost; it is v6 Appendix A.

2. **Implementation labels** follow v6 §0. Mapping applied by migration 0012
   and in every file that used the old set:

   | Before | v6 |
   |---|---|
   | IMPLEMENTED_VERIFIED | IMPLEMENTED_TESTED |
   | IMPLEMENTED_UNTESTED | IMPLEMENTED_UNVERIFIED |
   | PARTIAL, MOCK | unchanged |
   | NOT_PRESENT | PLANNED |
   | BLOCKED_SOURCE | BLOCKED (missing material is still called SOURCE_NOT_AVAILABLE) |
   | DEFERRED | PLANNED |
   | (new) | DISABLED: built or designed, deliberately switched off (Mode C, benefit screening) |

3. **Eligibility statuses** follow v6 §5: `PRELIMINARY_MATCH, NEEDS_INFORMATION,
   NEEDS_EVIDENCE, DOES_NOT_MEET_ENCODED_RULES, SOURCE_STALE,
   CONFLICTING_AUTHORITY, HUMAN_REVIEW_REQUIRED`. They replace v5's list and the
   canonical v2 `eligible / possibly_eligible / not_eligible /
   insufficient_information`. No engine exists yet (G1), so this changes the
   contract in `docs/ARCHITECTURE.md` §3, not code.

4. **Reference record status is kept, with a crosswalk.** The `ref` schema's
   statuses (UNVERIFIED, SOURCE_CHECKED, CONTESTED, SUPERSEDED, VERIFIED,
   ILLUSTRATIVE, HEURISTIC) are enforced in SQL, Python and tests and
   already satisfy canonical v2's gates. Canonical v2 is subordinate to v6
   and its package files (`vetbuddy_canonical_schema_v2.sql`, seed, manifest)
   were not supplied (SOURCE_NOT_AVAILABLE). Renaming would churn a working
   schema for no behaviour change. Crosswalk for any v2 consumer:

   | ref status | canonical v2 `data_status` |
   |---|---|
   | VERIFIED | verified |
   | SOURCE_CHECKED | provisional |
   | UNVERIFIED | needs_verification |
   | CONTESTED | needs_verification (v2 rule 4: conflicts are never silently resolved) |
   | SUPERSEDED | superseded |
   | ILLUSTRATIVE, HEURISTIC | placeholder (never used for matching) |
   | FY2025 rate rows | historical (v6 §1: FY2025 values stay historical until reverified) |

   The v2 gate "needs_verification may appear only in an administrative view
   unless clearly labelled provisional" is met: every corpus row reaches users
   with its status label, and none is used to assert eligibility.

5. **Mission Router stays separate from eligibility** (canonical v2, v6 §5),
   as built. The Mission Brief's `benefit_screening.status` becomes `DISABLED`
   (switched off until verified rules exist), replacing `NOT_PRESENT`.

6. **Runtime stack unchanged.** v6 §0 forbids silently replacing the React/Vite
   app or adding Next.js, Expo, Capacitor or a desktop shell without an ADR.
   ADR 0002 stands; no Vite export has been supplied. Native iOS/Android and
   Microsoft Store packaging (v6 §10) are PLANNED, behind sequence step 7.

7. **Next slice is v6 sequence step 3.** Accounts exist (dev MOCK sign-in), and
   v6 says account collection must not launch before deletion and security.
   So this session builds real data export and account deletion (v6 §3) as
   the next vertical slice, before any other feature work.

**Consequences.** A single label vocabulary is enforced in SQL (0012), the
corpus validator and the record generator. The conflict-free crosswalks above
are the only translation layer; nothing else is renamed.
