# ADR 0007: Career Navigator core, rebuilt from its architecture spec

**Status:** Accepted, 2026-10-29. Implementation: `backend/app/domains/career/`, `config/career_rules.json`, `backend/tests/test_career.py`.

## Context

The input was `VeteranOS-Career-Navigator-Architecture.html`, a reverse-engineered specification of a separate `veteranos-career-navigator` repository. That repository's source was not supplied (SOURCE_NOT_AVAILABLE). The spec describes two implementations that disagree: a Python core and a browser copy in JavaScript. It lists ten defects (D-1 to D-10) and fourteen divergences between the two (D1 to D14).

The repository rule says no career module ships before the ADA metamorphic test and the fact-level allowlist exist (CB-01, CB-02).

## Decision

1. **One implementation, in Python.** It is a pure library: no I/O beyond reading its rules file, no persistence, no network and no model. The browser copy isn't ported. The demo shows output computed at build time by this library, so there is one author.
2. **Rule tables are data.** `config/career_rules.json` holds:
   - protected and structural patterns;
   - the number token, prohibited assurances and stopwords;
   - requirement-category rules and headings;
   - jargon, status labels and the closed audit vocabulary;
   - never-grantable fields and the nine-module consent catalog.

   Where the spec gave intent but no table (the category regexes and the full stopword list), the tables were written from that intent. Tests pin them.
3. **The thesis is kept: generators propose, a deterministic gate disposes.**
   - Protected content is checked first and voids the whole document.
   - Only a verified metric licenses a number.
   - A record of absence is never support.
   - A legally required credential blocks.
   - Results are one label per category, with no composite score.
   - Held lines are shown with their reason, never hidden.
4. **All ten documented defects are fixed,** plus the JS-side corrections that matter:
   - D1: all-MODERATE means "Competitive with minor gaps";
   - D2: whole tokens, and the title is in the haystack;
   - D5: a series and grade is not a claim;
   - D6: "single" is not marital status, and therapy is health information.

   Each fix has a named regression test.
5. **Fixes found by running the four sample people** (`data/demo/career.json`):
   - **CN-11:** an empty evidence bank yields "Insufficient information", never a gap.
   - **CN-12:** a legally required credential that's on file but unverified gets "verify it", not "go get it".
   - **CN-13:** only a credential record can support a legally required licence. A dispatch job that mentions "drivers" is not a CDL. A record of absence speaks only to credential, clearance and education requirements.
   - **CN-14:** a cover letter discloses a missing requirement only when a record documents it as missing. Unknown is not missing.
   - **Military codes are structural, not claimed metrics.** MOS (88M), AFSC (3D0X2) and Navy rating (IT1) codes are excluded from the number check. The structural patterns are ordered so that compound dates match before the bare year: "05/2019" no longer leaves "05" behind.
   - **Requirement wording is kept as posted.** Letters keep "GS-09" and "STIGs" as written instead of lower-casing them.
6. **CB-01, the ADA metamorphic test.** For any profile and any value of a health-derived fact, career output must not change.
   - **Mechanism:** `redact_protected` removes every clause that carries a protected or health fact before matching. It removes the whole clause, not just the matched span, because removing only the span left "manages" (from "Manages PTSD…") and "disabled" behind to match on, and the first version of the test caught that.
   - **Field boundaries:** title, summary and skills are joined as separate clauses.
   - **Test:** `ADAMetamorphic` injects 20 health and protected-class facts (every rating from 0 to 100%, P&T, PTSD, TBI, medication, marital status, religion, race, birth date) into every record of three people, then compares against three announcements. The matrix, the category labels and the tailoring order must be identical.
   - **Mutation check:** disabling redaction fails 18 tests.
7. **CB-02, the fact-level allowlist.** The consent broker:
   - refuses any grant that names a never-grantable field or a field outside the module's allowlist;
   - structurally severs `wellness_checkin`;
   - refuses (and audits the refusal of) destinations other than the career navigator and purpose mismatches;
   - projects every read onto requested ∩ allowed − never-grantable.

   No engine entry point has a parameter that names a health field.
8. **Persistence and routes are deferred.** Evidence banks, documents and the audit log aren't stored, and no `/api/v1/career` route exists. The reason is that account collection waits on sign-in (G17), and the CLAUDE.md rule is "No account collection launches before deletion, export and security are implemented". When they land, they need:
   - tenant tables under forced RLS;
   - coverage by `vb_delete_account` and export;
   - the audit log appended to the hash-chained ledger;
   - an agent manifest for the career agent.

## Consequences

- **Status:** CB-01 and CB-02 are IMPLEMENTED_TESTED in the core. V6-33 moves from PLANNED to PARTIAL. MOS crosswalks (O*NET / CareerOneStop), persistence, routes and the work-style assessment remain PLANNED.
- **Tests:** `backend/tests/test_career.py` has 74 tests:
  - the spec's 38, ported;
  - regressions for D-1 to D-10, D1, D2, D5, D6 and CN-11 to CN-14;
  - the surfaces the spec lists as untested;
  - an adversarial matrix of 3 announcements × 4 evidence banks × 6 resume types;
  - CB-01 and CB-02.

  Mutation checks: turning off CN-13 fails 2 tests and weakening D-5 fails 3.
- **Demo:** `dist/vetbuddy-demo.html` gains "Their career" for each sample person. It shows the evidence bank, the qualification matrix, category labels, six resume types and a cover letter. Held lines are crossed out with their reason. The ATS resume deliberately proposes one invented figure so the gate is seen working. The smoke test checks that it is held, that no health term reaches a document and that Marcus's letter claims no gap.
- **Not claimed:** no outcome, interview or hiring probability. Sample people and announcements are synthetic.
