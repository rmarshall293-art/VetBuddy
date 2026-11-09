# ADR 0006: Owner decisions on unchecked rules, helper names and the reviewer roster

**Status:** Accepted, 2026-10-29 (decisions by the project owner; implementation in this ADR)

## 1. Unchecked rules never hide a benefit (VD21)

**Decision.** Under the production policy (`verified_only`), when a person's answers miss the encoded rule of a record that no reviewer has checked, the record is listed as HUMAN_REVIEW_REQUIRED instead of being hidden as DOES_NOT_MEET_ENCODED_RULES.

**How it shows.**
- **Reason:** `RULE_NOT_VERIFIED`.
- **Caveat:** `unreviewed_rule_not_met` ("Your answers don't fit this program's rule as VetBuddy wrote it, but no reviewer has checked that rule yet…").
- **Order:** these leads sort after the ones the answers fit.

**Limits.**
- **Statuses covered:** only UNVERIFIED and SOURCE_CHECKED records with an allowlisted official link that was actually read and isn't stale. Superseded, contested, illustrative and heuristic records, and links seen only in search, stay hidden when the answers miss them: they aren't a reliable pointer either way.
- **Reviewed records:** a VERIFIED record's rule still says DOES_NOT_MEET_ENCODED_RULES.
- **Preview policy:** unchanged.

**Evidence.** `tests/vault/test_matcher.py` has five VD21 tests; removing the rule fails two of them.

**Effect for the demo people.** Production lists go from roughly 50–60 to 90–135 items per person. The extra ones are labelled "Doesn't fit the rule as written; the rule isn't checked yet" and shown last.

## 2. Helper names follow the v8 roster (VD06)

**Decision.**

| Before | After |
|---|---|
| `benefit_vault_agent` | `benefits_intelligence_agent` (v8 Benefits Intelligence: Federal Benefits, State & Territory, Guard/Reserve) |
| `claims_navigator_agent` | `claims_navigation_agent` (v8 Claims Navigation) |
| `crisis_support_agent` | Removed. Crisis help is a Tier 0 rule (CrisisGate and `config/crisis_floor.yaml`), not an agent |

**Migration.** 0014 is applied and immutable, so **0015** moves its pins forward:
- the manifest CHECK, the grant `grantee` CHECK and default, and `not_from_the_vault`;
- existing grants are renamed; the guard trigger is paused only inside that transaction, and the postcondition confirms it's re-enabled;
- pull-ledger rows keep the name they were written with, because the ledger is hash-chained history.

Tested on a fresh database and as an upgrade of a database holding the old seed and two live grants.

**What the rename unblocks.** `app/domains/vault/providers.py` wires `service_profile_agent` over slice 03's `service_record`. It provides only what the record supports:
- **component:** active, guard or reserve, for a declared serving component;
- **service status:** serving, separated or retired, from the declared component and end date.

It doesn't provide the following, even though the manifest exposes them:
- **legal residence:** onboarding asks where the person *lives now*, which is the state definition trap;
- **Guard state, orders, active-duty days, wartime service, discharge or awards:** never asked.

A partial answer is delivered and logged by key only. **Evidence:** `VaultPullsFromOnboarding` and `ProviderDerivation` in `tests/test_vault_integration.py`.

## 3. Reviewer roster, owned by the project owner (G1)

**Decision.**
- **Owner:** the project owner keeps the roster.
- **Reviewers:** VA-accredited representatives, starting with accredited service officers.
- **Order:** Alabama first, then records whose source was already checked.

**Implementation.**
- **Migration 0016:**
  - `ref.vault_reviewer` holds handles only: a role, a jurisdiction scope, `added_by = 'project_owner'`, and retired rather than deleted.
  - `ref.vault_review_event` is append-only for everyone.
  - A trigger refuses a VERIFIED mark unless its handle is on the roster, active and scoped to the record's jurisdiction.
  - The app role can read neither table.
- **Roster file:** `config/reviewer_roster.yaml` holds handles only, and the loader refuses names, emails and unexpected fields. It ships empty.
- **Script:** `scripts/vault_review.py` runs as the owner, with `sync-roster`, `queue`, `verify BENEFIT_ID --handle H --content-hash HASH` and `withdraw`.
  - A review needs the exact content hash the reviewer read.
  - It reaches the production API on its next start (`with_reviews`).
  - The seed keeps it only while the content is unchanged.

**Evidence.** `tests/test_vault_review.py` (6) and `test_verified_needs_a_named_reviewer_and_unchanged_content` (roster refusals).

**Status.** V21 goes from BLOCKED to PARTIAL: the workflow exists, but nobody is on the roster yet. G1 stays open until the owner adds the first handles and reviews begin.

## Consequences

- VD06 and VD21 are closed, and G1 has a working path.
- Still open:
  - providers for VA status and household have no slice 03 store;
  - the ledger head isn't anchored (VD09);
  - production sign-in (G17).
