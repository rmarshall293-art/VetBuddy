# Gap Matrix

Single list of what is open. Update this file in the same commit that closes a gap.

## Decisions waiting on the owner

| ID | Decision | Default in this build | Unblocks |
|---|---|---|---|
| G1 | Who verifies benefit rules against primary law | Nobody named → 0/57 jurisdictions verified; finder shows "verification required" | Any benefit answer |
| G17 | Identity provider + token model | Dev HMAC tokens, 10-min TTL, refused outside dev/test | Real users in Mode B |
| G21/G23 | Model provider contract (zero retention, no training) | No model called anywhere | Model gateway, every agent |
| G18 | VA Lighthouse sandbox access | None | Read-only VA connector |
| — | Hosting region for API/DB/workers | Render + any Postgres 16 (config only) | Secrets manager / KMS |
| — | Legal review of governance §2, §5, §7 copy | Wording used as written, flagged unreviewed | Launch 1 claims screens |
| — | Repository visibility | **Public** — left unchanged (owner decision) | Committing any non-public material |

## Engineering gaps

| ID | Gap | Status |
|---|---|---|
| G19 | Outbox dispatcher / worker (reminders, referral follow-ups) | Open — table + in-transaction writes exist |
| G2/G3 | No verified jurisdiction or education records | Open (needs G1) |
| G4/G5 | Rating schedule data (Part 4 codes) | Open; only 4.25 arithmetic implemented |
| A-03 | §4.26 bilateral factor | Open; labeled in UI and API response |
| CB-01/02 | ADA metamorphic test for career module | Open; write before any career code |
| T0-12 | Self-approval prohibition in running code | Open; no approval workflow exists yet |
| — | Free-text crisis detector (CrisisGate) | Open; today there are no free-text inputs to screen |
| — | ClaimsBoundaryGuard negation handling | Partial; phrase list only |
| — | Full git-history secret scan in CI | Open (add gitleaks or equivalent) |
| — | Data export endpoint (deletion exists) | Open |
| A-01/A-02 | Float rounding; client/server disagreement | **Closed** (integer kernel + parity test) |
| C-06 | RLS on with no policy | **Closed** (migration 0006 guard + test) |
| CB-03 | Foreclosed consent purposes storable | **Closed** (CHECK constraint, proven against owner) |

## Agent rules R1–R22 / Tier 0 rules — status in this repo

No runtime agent exists, so rules about agent behavior hold only because the capability is absent.

| Rule | Status here |
|---|---|
| R1 Says it is software, not VA/VSO/attorney/clinician | Disclosure on every brief, API header, footer |
| R2 / T0-05 Engine decides, never a model | Router + rating kernel deterministic; no model |
| R3 / T0-04 Never prepares/signs/submits a claim or ITF | No such path exists |
| R4 Claims help free | No billing exists |
| R5 Refer to accredited rep | Links VA's Find a Rep; VSO referral block in API |
| R6 / T0-06 Citation for every fact | NOT_PRESENT (no source registry) |
| R7 / T0-07 Unknown stays unknown | Missing date → stage `unknown` + task; Guard authority `unknown` → task |
| R10 Numbers from engine only | Yes |
| R11/I2 ContextPacket / Guardian | NOT_PRESENT |
| R12 Acts only for signed-in person | Subject bound from token; cross-user → 404 |
| R14 Never asks for SSN | Unknown fields → 422, tested |
| R16 / T0-08 Crisis first | Crisis floor on every screen; no detector |
| T0-01..03 No guarantee / rating / diagnosis language | Copy lint over all shipped strings (CI) |
| T0-11 Purpose-scoped consent | `plan_storage` consent checked by RLS in-transaction |

## Next bounded slice (recommended)

**Source registry + Alabama rule pack skeleton (P4), behind verification status.** Tables `source_records`, `source_snapshots`, `rules`, `rule_versions` with forced RLS; a three-valued screener that returns only `NEEDS_INFORMATION` / `UNVERIFIED_OR_STALE` until a named reviewer marks a rule VERIFIED; trust-card endpoint; tests that an unverified rule can never produce `POTENTIALLY_ELIGIBLE`. Needs G1 for any real content.
