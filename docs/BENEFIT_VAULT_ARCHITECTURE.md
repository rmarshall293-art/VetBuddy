# Benefit Vault architecture (migration 0014)

As of 2026-10-27. Registry 1.0.0, SHA-256 `aaa67e4231d53936304f4d425d3c4d79ec9733111c50a9b3f63e7a7ea958145f`.
**Integrated 2026-10-27 onto this repository's slice 03 (ADR 0005).** The package was built against a
sandbox stand-in for 0001–0013 (described below as "slice 03 (commit d5ae5f7) with the coverage bridge"); here it
runs on the real chain. What changed on integration:
- **Deletion:** `privacy.purge` and `privacy.deletion_job` are replaced by slice 03's `vb_delete_account` and
  `vetbuddy_purger`.
- **Discard function:** `privacy.vault_discard` is now `public.vb_vault_discard`, owned by the purger.
- **Notice:** it is the v6 common notice (VD15 closed).
- **Errors:** they use the `/api/v1` contract.
- **Tests:** they run under unittest through `backend/tests/pytest_bridge.py`, with `app/infra/pg_compat.py`
  standing in for psycopg.
- **New defects:** VD21 and VD22 are listed in ADR 0005.

The Benefit Vault finds benefits and deals for active duty members, National Guard and Reserve members,
veterans and their families: state and federal benefits, scholarships, park and museum passes, hunting and
fishing licenses, plates, tax relief, homes, cemeteries, travel, MWR and retail offers. It is the only agent
allowed to pull facts from other agents, and only under a grant the person gives, through a broker that logs
every decision.

Master Prompt v6 governs: **agents orchestrate, gather and explain; they never decide.** Every outcome comes
from a deterministic matcher using the v6 outcome words. Nothing here calls a model.

*Engineering documentation. Not legal advice. Not a government eligibility determination.*

---

## 1. Package layout

| Path | What it is |
|---|---|
| `data/research/states/*.psv`, `data/research/federal/*.psv` | Research ledgers: one benefit per line, written while each page was read |
| `data/research/RESEARCH_LOG.md` | Ledger format, method, progress and the check pass |
| `data/research/recovered/` | Data recovered from earlier VetBuddy work (the Guard and Reserve zip, the recreation zip, slice 02), each file hash-checked against `RECOVERY_MANIFEST.json` |
| `config/benefit_vault_policy.yaml` | The authored half of the registry: publish policy, review period, grant limits, agent manifests, caveats, lead links, cross-checks, discovery templates, component status |
| `config/governance_language.yaml`, `config/crisis_floor.yaml` | Byte-identical copies of the slice 02 files (slice 03 already has them) |
| `schemas/json/benefit_vault_registry.schema.json` | JSON Schema (Draft 2020-12) for the registry |
| `scripts/build_vault_registry.py` | Builds the registry from ledgers, recovered data and policy; `--check` fails on drift |
| `data/reference/benefit_vault_registry.json` | **The single runtime source** (generated, integrity-stamped) |
| `scripts/build_vault_seed.py` | Generates the SQL seed from the registry; `--check` fails on drift |
| `database/migrations/0014_benefit_vault.sql` | Reference tables, tenant tables, triggers, row-level security, postconditions |
| `database/seeds/0014_benefit_vault_seed.sql` | Generated, idempotent seed |
| `database/test_fixtures/standalone_baseline.sql` | Sandbox only: stands in for the parts of 0001-0013 that 0014 needs |
| `backend/app/domains/vault/` | The Python domain (section 7) |
| `backend/tests/vault/` | 228 tests (section 11) |

`backend/app/__init__.py` and `backend/app/domains/__init__.py` are package markers for running the package on
its own; slice 03 has its own.

---

## 2. Governing rules carried into the vault

- **Outcomes** (v6, exactly seven): PRELIMINARY_MATCH, NEEDS_INFORMATION, NEEDS_EVIDENCE,
  DOES_NOT_MEET_ENCODED_RULES, SOURCE_STALE, CONFLICTING_AUTHORITY, HUMAN_REVIEW_REQUIRED. The vault never says
  "eligible" or "approved". Every envelope carries `"determination": "none"` and the common notice.
- **Record status** (v6): UNVERIFIED, SOURCE_CHECKED, CONTESTED, SUPERSEDED, ILLUSTRATIVE, HEURISTIC, VERIFIED.
  VERIFIED needs a named reviewer (gate G1) and holds only while the reviewed content is unchanged. No record is
  VERIFIED. The reviewer is recorded by a roster handle (lowercase letters, digits, `.`, `-`, `_`), never a
  personal name or email address; the database refuses anything else.
- **Build status** (v6): every vault component carries one of the eight labels (section 12).
- **Data classes** V0-V5 and **privacy modes**: Mode A (guest) holds at most V1; Mode B (private account) holds
  at most V2; Mode C is unreachable in this build. V3, V4 and V5 never travel between agents.
- **No manifest, no access.** Every manifest is pinned to `may_issue_determinations = false`, and only
  `benefit_vault_agent` may pull from other agents. Both pins are enforced four ways: the JSON Schema, the
  loaders, database CHECK constraints, and tests.
- **Pipeline order** (Integrated Record §4): CrisisGate, MSTNarrativeGuard, PIIMinimizer, deterministic engines,
  CitationValidator, ClaimsBoundaryGuard, model call (none), OutputGuard, ApprovalGate (writes only), audit.
- **Never**: store an SSN, staff names or personal emails; present a match as a determination; present uncertain
  eligibility as assured; present stale information as current; show the retired Veterans Crisis Line number
  (the crisis gate refuses a floor that contains it; the current line is 988, then press 1).

---

## 3. From pages to records

```
pages read (WebFetch, 2026-10-27)
   │  one line per benefit: CAT|TITLE|GROUPS|RULE|ELIGIBLE|VALUE|URL
   ▼
data/research/*.psv  ──►  discovery/importer.py  ──►  build_vault_registry.py  ──►  benefit_vault_registry.json
recovered/ (hash-checked) ──────────────────────────┘        ▲                          │
config/benefit_vault_policy.yaml ───────────────────────────┘                          ├──► Python (in process)
                                                                                         └──► build_vault_seed.py ──► SQL seed
```

**The importer** (the only reader of the ledgers) turns each row into a record with a stable id
(`<jurisdiction>.<title slug>`), the rule in canonical spelling, the page actually read (the source) and its
tier, how the official link is known (`SAME_AS_SOURCE`, `LINKED_FROM_SOURCE`, `SEEN_IN_SEARCH`), a content hash,
and a ledger reference (`file:line`). A record is SOURCE_CHECKED when its page was opened and is the program's
own page (tier 1 or 3), otherwise UNVERIFIED. Nothing imports as VERIFIED.

**Source tiers**: 1, the administering government body's own page or official law text; 2, an official summary
or aggregator, or an unofficial copy of the law (the DoD benefit libraries, Justia); 3, the program operator's
own page (nonprofit, association or vendor); 4, a secondary source or a recovered lead.

**What the registry holds** (all counts are generated and pinned by tests):

| | |
|---|---|
| Records | 1,362: 1,281 state (55 jurisdictions), 60 federal, 12 nonprofit programs, 9 commercial deals |
| Record status | 47 SOURCE_CHECKED, 1,315 UNVERIFIED, 0 VERIFIED |
| Official link | 93 same as the page read, 1,263 linked from it, 6 seen in search only |
| Sources | 116 (115 opened; tier 1: 14, tier 2: 78, tier 3: 23, tier 4: 1) |
| Coverage | 56 of 57 jurisdictions (50 states, DC, PR, VI, GU, MP and federal); American Samoa SOURCE_NOT_AVAILABLE |
| Categories | jobs 165, hunting and fishing 151, plates 147, education 143, income tax 142, property tax 105, bonuses and aid 84, state parks 72, Guard pay and insurance 64, Guard tuition 62, burial 60, other 58, homes 53, scholarships 14, insurance 6, MWR 6, passes 5, tickets 5, travel 5, family 5, deals 4, health 3, housing 2, licensing 1 |
| Leads | 9 Guard and Reserve rule leads (slice 02), 23 recovered recreation leads (tier 4, each cross-checked: 6 agree, 9 differ, 8 have no record) and a 51-state license reciprocity lead table (UNVERIFIED) |
| Egress allowlist | 471 hosts: every page read and every official link recorded |

State rows come from the DoD benefit-library State/Territory pages (MyArmyBenefits; New Mexico from
MyAirForceBenefits because its Army page was unreachable). Every long page was read a second time from
character 100,000; the tails are `PART=tail` blocks. Two tails are still partly unread (section 12, VD04).
Federal programs repeated on state pages are kept once, in the federal ledger.

---

## 4. The registry

`data/reference/benefit_vault_registry.json` is the only runtime source. It is valid against the JSON Schema and
stamped with the SHA-256 of its canonical JSON (keys sorted, separators `,` and `:`, UTF-8, no NaN, the
`integrity` member left out): the same rule the coverage registry (0013) uses. The build is deterministic; both
generators have a `--check` mode and a test runs them.

Loading (`registry.py`) refuses the registry unless: the stamp matches; the outcomes and the fact catalog equal
the code's; every manifest has `may_issue_determinations` false and exactly one agent pulls; every exposure is
at the catalog's class, never above V2 and never session-only; every rule compiles to its stored canonical
spelling; every content hash matches; no generated record claims VERIFIED.

The schema pins the same things independently: `may_issue_determinations` is `const false`; only
`benefit_vault_agent` may pull and it exposes nothing; exposures are V0-V2; a state record is a STATE_BENEFIT in a
state category; a link seen only in search is UNVERIFIED and tier 4; production's publish policy is
`verified_only`; `counts.verified` is 0.

**Publish policy.** `verified_only` in production and staging (the default when no environment is named):
a record that fits but is not VERIFIED is shown as HUMAN_REVIEW_REQUIRED with its official link.
`preview_unverified` in development and test lets such records show as PRELIMINARY_MATCH, flagged with their
status. The environment comes from the argument, then `VETBUDDY_ENV`, then the default.

**Reviews.** VERIFIED marks are made in the database (`ref.vault_benefit`, gate G1) and read back with
`vault_store.load_reviews`; `registry.with_reviews` applies a review only if its reviewer handle is well-formed
and the record's content hash is the one reviewed. Anything else lands in `stale_reviews`.

---

## 5. Facts and data classes

A fact is one thing the person tells the vault, a fact pulled from another agent under a grant, or a fact
derived for a household member. Income, conditions and diagnoses are never collected.

| Fact | Class | Values | |
|---|---|---|---|
| `residence_state` | V1 | state or territory code (legal residence: the home state for taxes and voting) | |
| `duty_station_state` | V1 | state or territory code (for a family member, the serving member's duty station) | |
| `service_status` | V1 | serving, separated, retired, never_served | |
| `component` | V1 | active, guard, reserve | |
| `guard_state` | V1 | state or territory code | |
| `on_active_duty_orders` | V1 | true/false | |
| `relationship` | V1 | self, spouse, child, surviving_spouse, parent (defaults to self) | |
| `age` | V1 | 0-120 | |
| `active_duty_days` | V1 | 0-20000 (federal active duty, not drill or annual training) | |
| `wartime_service` | V1 | true/false | |
| `discharge` | V2 | honorable, general, other_than_honorable, bad_conduct, dishonorable, uncharacterized | |
| `va_rating` | V2 | 0-100 in steps of 10, or none | |
| `rating_permanent_total`, `individual_unemployability` | V2 | true/false | |
| `purple_heart`, `medal_of_honor`, `former_pow`, `gold_star_family` | V2 | true/false | |
| `sponsor_status` | V2 | serving, separated, retired, deceased | |
| `sponsor_va_rating` | V2 | 0-100 in steps of 10, or none | |
| `sponsor_permanent_total`, `sponsor_unemployability`, `sponsor_service_connected`, `sponsor_died_in_line_of_duty`, `sponsor_pow_mia` | V2 | true/false | |
| `severe_disability` | V4 | true/false | session only: used in memory in Mode B, never stored, pulled, logged or echoed |

Each fact keeps its provenance (`self_attested`, `pulled`, `derived`) and whether the person was sure. Mode A
drops every fact above V1 before matching and says so (`facts_not_used_in_this_mode` and the `mode_a_dropped`
caveat).

**Household derivation** (`household.py`). A spouse's or child's benefits mostly turn on the sponsor, so the
vault derives the sponsor facts for each member from the sponsor's own answers: status, rating, permanent and
total, unemployability, service connection; a living sponsor describing their household did not die in the
line of duty. Residence and, for a serving sponsor, the duty station carry over. A member's own service status
defaults to never served, marked unsure. A derived fact keeps the class of the fact it came from, so deriving
never moves information to a lower class. At most 12 members.

---

## 6. The kernel

### 6.1 Three-valued logic

`tri.py` is strong Kleene logic: FALSE < UNKNOWN < TRUE; AND is the minimum, OR the maximum, NOT keeps UNKNOWN.
A missing fact is UNKNOWN and stays UNKNOWN. It never silently becomes FALSE.

### 6.2 Evaluation

Evaluating a rule returns the truth value and, when it is UNKNOWN, the fact keys whose answers could still
change it. Those keys become the questions shown with NEEDS_INFORMATION, each marked with its class and whether
it can be answered in the current mode. A discharge of other than honorable or bad conduct makes `otd` UNKNOWN
with the pseudo-key `discharge_review`: VA's character-of-discharge decision is needed, and an accredited
representative can help. It is never collected.

### 6.3 The rule language

A rule states the **necessary** conditions for a record to be worth showing as a preliminary match. It never
states sufficient conditions. When the research could not pin a condition down (branch, service dates, income,
how long the person has lived in the state, home of record at entry), the condition stays in the plain-language
"who it is for" text and out of the rule: a loose rule shows a lead the person can read, while a strict rule
could hide a real benefit.

Grammar (`&` binds tighter than `|`; `!` binds tightest):

```
expr  := and ( "|" and )*
and   := not ( "&" not )*
not   := "!" not | atom
atom  := "(" expr ")" | token
token := NAME | NAME ">=" INT | NAME "<" INT
```

The canonical spelling uses single spaces and the fewest brackets (an AND inside an OR is bracketed). The
registry stores only canonical rules, and loading fails on any other spelling. The subject of every token is
the person being evaluated; sponsor tokens (`sp...`) describe the service member or veteran that person is a
family member of, and are FALSE for a person evaluated as themselves.

| Token | Meaning | Facts read |
|---|---|---|
| `true` | always true (no encoded condition) | none |
| `res` | is a legal resident of the record's state or territory | `residence_state` |
| `nonres` | is a legal resident somewhere other than the record's state or territory | `residence_state` |
| `stn` | is serving and stationed in the record's state or territory, or is the spouse or child of a service member stationed there | `duty_station_state`, `relationship`, `service_status`, `sponsor_status` |
| `ad` | is serving on active duty (active component, or Guard or Reserve on active duty orders) | `component`, `on_active_duty_orders`, `service_status` |
| `ng` | is serving in the record's state National Guard (any state's Guard on a federal record) | `component`, `guard_state`, `service_status` |
| `ngany` | is serving in any National Guard | `component`, `service_status` |
| `ngret` | is retired from the National Guard (the record's state, for state records) | `component`, `guard_state`, `service_status` |
| `rsv` | is serving in a federal Reserve component | `component`, `service_status` |
| `sm` | is serving in any component | `service_status` |
| `vet` | has served and separated or retired | `service_status` |
| `ret` | is a military retiree | `service_status` |
| `sc` | has a VA service-connected rating (any percentage, including 0%) | `va_rating` |
| `pt` | the VA rating is permanent and total | `rating_permanent_total`, `va_rating` |
| `iu` | is paid at the 100% rate for individual unemployability | `individual_unemployability`, `va_rating` |
| `sev` | has a severe service-connected disability (loss of use of limbs, blindness); session-only | `severe_disability` |
| `hon` | was discharged honorably | `discharge` |
| `uhc` | was discharged honorably or under honorable conditions (general) | `discharge` |
| `otd` | was discharged under conditions other than dishonorable | `discharge` |
| `wartime` | served during a wartime period | `wartime_service` |
| `ph` | received the Purple Heart | `purple_heart` |
| `moh` | received the Medal of Honor | `medal_of_honor` |
| `pow` | is a former prisoner of war | `former_pow` |
| `gs` | is a Gold Star family member | `gold_star_family` |
| `sp` | is the spouse of a living service member or veteran | `relationship` |
| `ch` | is the child of a service member or veteran | `relationship` |
| `dep` | is a spouse or child of a service member or veteran | `relationship` |
| `ss` | is a surviving spouse | `relationship` |
| `spsc` | the sponsor's disability or death is service-connected | `relationship`, `sponsor_service_connected` |
| `sppt` | the sponsor's VA rating is permanent and total | `relationship`, `sponsor_permanent_total` |
| `spiu` | the sponsor is paid at the unemployability rate | `relationship`, `sponsor_unemployability` |
| `spkia` | the sponsor died in the line of duty | `relationship`, `sponsor_died_in_line_of_duty` |
| `sppm` | the sponsor is missing in action or a prisoner of war | `relationship`, `sponsor_pow_mia` |
| `spsm` | the sponsor is serving | `relationship`, `sponsor_status` |
| `spret` | the sponsor is a military retiree | `relationship`, `sponsor_status` |
| `spvet` | the sponsor has served and separated or retired | `relationship`, `sponsor_status` |
| `spdec` | the sponsor has died (any cause) | `relationship`, `sponsor_died_in_line_of_duty`, `sponsor_status` |
| `r>=N` (0-100) | the VA combined rating is at least N percent | `va_rating` |
| `spr>=N` (0-100) | the sponsor's VA combined rating is at least N percent | `relationship`, `sponsor_va_rating` |
| `days>=N` (1-10000) | at least N days of active duty | `active_duty_days` |
| `age>=N`, `age<N` (0-120) | age is at least N, or under N | `age` |

Examples from the registry: `res & ((vet & (r>=100 | iu)) | ss)` (Texas 100% disabled veteran homestead
exemption); `vet & pt & (r>=100 | iu)` (Space-A for veterans whose permanent disability is rated as total);
`(dep | ss) & (spkia | sppm | spr>=100 | spiu | (spsc & spdec))` (Hazlewood for spouses and children).
`facts.TOKEN_FACTS` maps every token to the facts it reads; the broker uses it to ask other agents only for what
the rules in scope mention (minimum necessary).

### 6.4 The matcher

For a person and a scope, the matcher evaluates every record in scope and reports one outcome each:

| Outcome | When |
|---|---|
| PRELIMINARY_MATCH | the facts given fit every encoded condition |
| NEEDS_EVIDENCE | they fit only because of answers marked unsure (`facts_to_document` lists them) |
| NEEDS_INFORMATION | an unanswered question could change the result (`facts_needed` lists it) |
| DOES_NOT_MEET_ENCODED_RULES | the facts given miss an encoded condition; says nothing about eligibility (hidden unless asked for) |
| SOURCE_STALE | the source page was read more than 180 days ago, or the record is SUPERSEDED |
| CONFLICTING_AUTHORITY | the record is CONTESTED |
| HUMAN_REVIEW_REQUIRED | the facts may fit but the record cannot be shown as a match: not VERIFIED under `verified_only`, link only seen in search, illustrative or heuristic data, or a link off the allowlist |

**Scope** is the federal records plus the person's residence, duty station and Guard state, because a member
stationed in another state, or serving in another state's Guard, can use some of that state's benefits. A
request may name jurisdictions instead. Results sort by outcome, then scope order, category and id.

**Caveats** are attached automatically: commercial offers and nonprofit programs say so; a link seen only in
search, a record not yet reviewed, a page with an unread tail, unsure answers, a stale or superseded source. The
**state definition trap** caveat is added when the person is in the Guard or Reserve, the state rule uses
`vet`, and active duty days are unknown or under 181: many states define a veteran by federal active duty
(Texas Hazlewood needs 181 days), and drill, annual training or State Active Duty may not meet it.

### 6.5 Search and envelope

Search (`search.py`) needs no facts and is safe in Mode A. The query passes the PII minimizer first (SSNs,
emails, phone numbers, DoD ID numbers and dates are removed and reported) and never leaves the process.
Scoring is by title, category and group labels and body text, with everyday synonyms ("park pass", "hunting
license").

Every response is a v6 envelope (`envelope.py`): engine and registry identity, mode, publish policy,
`determination: "none"`, the notice, the payload, and two hashes: `inputs` over everything that went in and
`output` over everything that came out. Equal inputs give equal outputs. The OutputGuard checks every text in
the envelope against `config/governance_language.yaml` (phrase-level, on normalized text) and blocks the
response on a hit.

---

## 7. Governance: the only agent that may pull

```
Benefit Vault agent ──► PullRequest ──► Pull broker (Privacy and Consent Guardian)
                                          │ mode C unreachable · requester may pull · source has a manifest
                                          │ purpose = benefit_matching · each key exposed · never V3/V4/V5
                                          │ within the mode ceiling · minimum necessary (rules in scope need it)
                                          │ an active grant covers every key · the source answers
                                          ├──► pull ledger: ALLOWED or DENIED with a reason code (keys, never values)
                                          ▼
                                   sealed context packet ──► open_packet (seven invariants) ──► facts (provenance "pulled")
```

**Manifests** (`governance/manifests.py`, policy file). Seven vault-side agents:

| Agent | Plane | Holds up to | Exposes to the vault |
|---|---|---|---|
| `benefit_vault_agent` | 5 | V2 | nothing; the only agent that may pull |
| `service_profile_agent` | 2 | V2 | residence, duty station, status, component, Guard state, orders, active duty days, wartime (V1); discharge, Purple Heart, Medal of Honor, former POW (V2) |
| `va_status_agent` | 2 | V4 | rating, permanent and total, unemployability (V2); conditions (V4) never leave it |
| `household_agent` | 2 | V2 | relationship, age (V1); Gold Star family, sponsor status, sponsor died in the line of duty (V2) |
| `coverage_bridge_agent` | 2 | V2 | nothing |
| `claims_navigator_agent` | 3 | V4 | nothing |
| `crisis_support_agent` | 3 | V5 | nothing |

**Grants** (`governance/grants.py`). A grant names one source agent, the exact fact keys, the one purpose
(`benefit_matching`), the mode and an expiry: 30 days by default and at most 90 for an account (Mode B, stored
in `public.vault_pull_grant`), at most 24 hours for a guest session (Mode A, in memory, V1 facts only). Creating
one needs the person's confirmation of a plain consent sentence (ApprovalGate). Revoking stops pulls at once and
is final. The agent asks once per active grant, so keys granted in separate grants are all honored, and never
asks a source for the same key twice in one request.

**Context packets** (`governance/packets.py`). Pulled facts reach the vault only in a packet the broker seals.
Opening it checks seven invariants and refuses the whole packet on any failure: ADDRESSED (this consumer and
tenant), PURPOSE_BOUND (benefit matching, equal to the grant's), EXPIRING (issued, not expired, life within the
600-second TTL), INTEGRITY (hash over the canonical body), MINIMUM_NECESSARY (keys within the grant and the
request), CLASS_CEILING (each fact at its catalog class, within the mode, never V3-V5), NON_TRANSFERABLE (only
the agent the grant names; `forward` always refuses).

**The pull ledger** (`governance/ledger.py`, `public.vault_pull_ledger`). Every pull, allowed or denied, and
every grant created or revoked is one entry: event, requester, source, purpose, fact keys, grant and packet ids,
and a reason code. Never a value. Entries are hash-chained per tenant, so deleting an account removes one whole
chain and breaks no one else's:

```
row_hash = sha256(prev_hash|seq|tenant|occurred_at (UTC, microseconds)|event|requester|source_agent|purpose|keys|grant_id|packet_id|reason)
```

The database trigger and `verify_chain` build the same text, so Python verifies a chain the database wrote. The
trigger assigns `seq`, `prev_hash` and `row_hash` itself (the app cannot forge them) under a per-tenant advisory
lock, so concurrent appends keep one chain.

**Egress** (`governance/egress.py`). A URL may be fetched or shown only if it is plain https (no user, password
or non-443 port) on the allowlist; the citation validator and the fetch guard use the same function, so a link
is shown exactly when it could be fetched. A discovery query may be built only from fixed templates filled with
V0 vocabulary (jurisdiction names, category labels, group labels); no numbers or addresses. Nothing about the
person can leave through a search engine.

---

## 8. The agent and the API

`agent.py` runs the pipeline for every request:

1. **CrisisGate** on any free text (`note`, search query). A signal returns the crisis floor from
   `config/crisis_floor.yaml` (988 then press 1, text 838255, chat; and the other slice 02 contacts) and stops.
2. **MSTNarrativeGuard**: a personal account of military sexual trauma is neither stored nor processed; the
   person gets confidential support contacts. A plain query such as "MST support" still searches.
3. **PIIMinimizer** on search text.
4. **Facts** validated against the catalog, then cut to the mode's ceiling.
5. **Pulls** through the broker for the facts the rules in scope need and the person has granted.
6. **Matcher** or **search**; **CitationValidator** drops links off the allowlist; **ClaimsBoundaryGuard**
   checks every outcome is a v6 outcome.
7. No model call. **OutputGuard** checks the envelope's wording.
8. Writes (a grant, a saved benefit, a discard) pass the **ApprovalGate** first: without `"confirm": true`
   the API answers 409 with the consent text.

Routes (`api.py`, Starlette, under `/api/v1/vault`):

| Method and path | Mode | Purpose |
|---|---|---|
| `GET /catalog` | guest | registry identity, notice, vocabularies, rule tokens, facts, jurisdictions, publish policy |
| `GET /benefits` | guest | search (`q`, `jurisdiction`, `category`, `group`, `kind`, `limit` 1-100, `offset`) |
| `GET /benefits/{benefit_id}` | guest | one record with its rule, ledger reference, content hash and rule leads |
| `POST /match` | guest or account | match the person's facts |
| `POST /household` | guest or account | match each spouse or child from the sponsor's facts |
| `GET /governance` | guest | manifests, ceilings, grant limits, publish policy, component status |
| `GET /leads` | guest | rule leads, recovered leads, license reciprocity |
| `GET /discovery/plan` | guest | the research plan (not executable) |
| `GET /grants`, `POST /grants`, `POST /grants/{id}/revoke` | account | grants |
| `GET /ledger` | account | the person's pull ledger and whether its chain verifies |
| `GET /saved`, `POST /saved`, `POST /saved/{id}/discard` | account | the person's saved benefits (statuses: interested, gathering documents, applied on my own, not for me) |

Account routes need an authenticated tenant. Slice 03 has no sign-in for the vault yet (G17), so the default
resolver returns none and those routes answer 403. Errors: 422 for a bad request, 404 for an unknown id, 409
for a missing confirmation, 400 for a store error; bodies over 64 KB are refused.

---

## 9. Database (migration 0014)

**Reference tables** (`ref.vault_*`, read-only for `vetbuddy_app`): registry meta, jurisdictions, sources,
facts, benefits, rule leads, benefit-lead links, caveats, license reciprocity, agent manifests, agent
exposures. CHECK constraints repeat the registry pins: VERIFIED needs a reviewer handle, a review date and the
reviewed content hash equal to the current one; unreviewed records carry no reviewer fields; state records are
state benefits in state categories; a link seen only in search is UNVERIFIED; `may_issue_determinations` is
false; only `benefit_vault_agent` may pull (plus a unique index on the puller); V3-V5 and session-only facts are
never pullable; an exposure must match the catalog class, on a pullable fact, never on the puller (trigger).

**Tenant tables** (each with a NOT NULL `tenant_id` referencing `public.tenant`, forced row-level security
scoped by `public.vb_current_tenant()`, and no DELETE or TRUNCATE grant):

| Table | App may | Guards |
|---|---|---|
| `vault_pull_grant` | SELECT, INSERT, UPDATE of `revoked_at` | grantee is the vault, source is not; purpose benefit_matching; Mode B; 1-90 days; keys exposed by the source and within V2 (trigger); keys sorted and de-duplicated; only revoking, once |
| `vault_pull_ledger` | SELECT, INSERT | the chain trigger; append-only for everyone, even the owner, except DELETE for the tenant a deletion job is purging; no TRUNCATE |
| `vault_saved_benefit` | SELECT, INSERT, UPDATE of `status` | the record must exist; only the status changes; one row per record per tenant; no free text |

`privacy.vault_discard(kind, id)` (security definer, `search_path` pinned with `pg_temp` last) removes a saved
benefit, or a grant that is already revoked or expired, for the caller's tenant only. The ledger is never
discarded; account deletion (`privacy.purge`, migration 0012) removes it with everything else, because the
purge deletes from every public table with a `tenant_id` and sets `vetbuddy.purge_tenant`.

A postcondition block fails the migration if any vault tenant table breaks the 0012 rule, if the app could
update the ledger, or if the app could write a reference table.

**The seed** is generated from the registry. It upserts every reference row stamped with the registry hash,
then prunes rows with an older stamp, so it is idempotent. A VERIFIED mark made in the database survives a
reseed only while the record's content hash is the one reviewed; otherwise the record returns to its registry
status.

---

## 10. Discovery

`discovery/planner.py` lists gaps in priority order (a jurisdiction with no source, a page with an unread tail,
a state category with no record) and turns each into a V0-only search query. American Samoa comes first. The
registry names no search endpoint, so the plan is not executable until a hosting decision names one.

`discovery/watcher.py` lists sources due for review (read more than 180 days ago) and, given a fetcher, compares
a hash of each page's normalized text with its last baseline; a changed page sends its records to review. No
fetcher is wired, so `check` reports BLOCKED rather than pretending to watch.

---

## 11. Tests

228 tests, all passing on Python 3.13 and PostgreSQL 16, as an ordinary user (initdb refuses root; as root the
22 database tests skip):

| File | Tests | Covers |
|---|---:|---|
| `test_tri_rules.py` | 44 | Kleene truth tables; the grammar, precedence, canonical spelling, errors with positions |
| `test_facts_household.py` | 24 | fact validation, classes and ceilings; every token's semantics; household derivation |
| `test_importer_registry.py` | 34 | the importer; full ledgers; deterministic, current build; schema and loader pins; tamper detection; reviews; SQL CHECK lists equal the vocabulary; family-tagged records can match a family member |
| `test_matcher.py` | 18 | outcomes, publish policy, NEEDS_EVIDENCE, staleness, caveats, the state definition trap |
| `test_governance.py` | 52 | manifests, grants, packets (each invariant), the ledger chain, the broker's denial reasons, egress |
| `test_agent.py` | 18 | the pipeline, envelope determinism, Mode A and C, V4 handling, pulls with grants, household, crisis and MST gates |
| `test_api.py` | 10 | every route, sign-in gating, confirmations |
| `test_discovery.py` | 6 | the planner and the watcher |
| `test_database.py` | 22 | 0014 and the seed on PostgreSQL: exact copy, postconditions, idempotent, VERIFIED, pruning, pins, pinned search paths, privileges, RLS, grants, the chain (forging, concurrency, tampering), discard, the agent and routes on the database, purge |

```
python3 scripts/build_vault_registry.py --check && python3 scripts/build_vault_seed.py --check
scripts/test.sh                       # whole suite, vault included (unittest + pytest_bridge, real 0001-0014 chain)
pytest backend/tests/vault            # the same files, where pytest is installed
```

`VETBUDDY_PG_BIN` points the database fixture at the PostgreSQL binaries if they are not in
`/usr/lib/postgresql/16/bin`.

---

## 12. Component status (v6 labels)

| Id | Component | Status |
|---|---|---|
| V01 | Research ledger importer | IMPLEMENTED_TESTED |
| V02 | Canonical registry with JSON Schema and integrity stamp | IMPLEMENTED_TESTED |
| V03 | Rule language and three-valued evaluator | IMPLEMENTED_TESTED |
| V04 | Fact catalog and data classes | IMPLEMENTED_TESTED |
| V05 | Household derivation | IMPLEMENTED_TESTED |
| V06 | Matcher (v6 outcomes, publish policy, caveats) | IMPLEMENTED_TESTED |
| V07 | Search | IMPLEMENTED_TESTED |
| V08 | Response envelope and determinism hashes | IMPLEMENTED_TESTED |
| V09 | Agent manifests and pins | IMPLEMENTED_TESTED |
| V10 | Pull grants | IMPLEMENTED_TESTED |
| V11 | Context packets (seven invariants) | IMPLEMENTED_TESTED |
| V12 | Pull broker | PARTIAL: tested with in-memory providers; no slice 03 store is wired as a provider |
| V13 | Hash-chained pull ledger | IMPLEMENTED_TESTED |
| V14 | Egress guard | IMPLEMENTED_TESTED |
| V15 | Discovery planner | IMPLEMENTED_TESTED |
| V16 | Source watcher | PARTIAL: tested with an injected fetcher; none wired |
| V17 | Agent pipeline and guards | IMPLEMENTED_TESTED |
| V18 | API routes (Mode A) | IMPLEMENTED_TESTED |
| V19 | API routes (Mode B) | PARTIAL: mounted with the platform session and consent rule; development sign-in only; production sign-in waits on G17 |
| V20 | Migration 0014 and seed | IMPLEMENTED_TESTED on the real 0001-0014 chain |
| V21 | Named-reviewer verification workflow | BLOCKED (G1) |
| V22 | Model-written explanations | BLOCKED (G21, G23) |
| V23 | American Samoa coverage | SOURCE_NOT_AVAILABLE |
| V24 | Recovered lead import | IMPLEMENTED_TESTED |
| V25 | Screens | IMPLEMENTED_TESTED: web shell Benefits view; guest app catalog finder |

---

## 13. Defect register and honest gaps

| Id | Defect or gap | Effect | What closes it |
|---|---|---|---|
| VD01 | Nothing is VERIFIED (G1 open). | In production every record that fits shows as HUMAN_REVIEW_REQUIRED with its official link; PRELIMINARY_MATCH appears only in development and test. | A reviewer roster and the review workflow (V21). |
| VD02 | Evidence depth. All 1,281 state rows come from DoD benefit-library pages (tier 2); their official links were taken from those pages, but the agency pages were not opened. 6 federal rows were seen in search only (Waves of Honor and NMFA block automated readers). | 1,315 records UNVERIFIED; amounts, dates and limits may have changed since the library pages were written. | Open each official link during review; the watcher once a fetcher exists. |
| VD03 | American Samoa has no source: neither DoD library has a page and no official territorial page was found. | No American Samoa records; the planner lists it first. | A territorial source. |
| VD04 | Two page tails are partly unread: T-Mobile (7,042 characters) and New Mexico (451). | Records from those pages carry the `tail_unread` caveat; some offers or New Mexico benefits may be missing. | Re-read the tails. |
| VD05 | Not merged. The sandbox baseline stands in for 0001-0013; 0014 has run only against it. | Integration risk with the real 0012 purge and roles. | Apply in the repository and run the slice 03 deletion test. |
| VD06 | Agent ids are vault-side names. Candidate mapping to the blueprint: `benefit_vault_agent` to `benefits_discovery_agent` (route 15, "what am I missing"); `claims_navigator_agent` to `claims_readiness_agent`; `crisis_support_agent` to `safety_triage_agent`. `service_profile_agent`, `va_status_agent` and `household_agent` are plane 2 data holders, not routed agents. No provider is wired. | Pulls work only with injected providers (V12 PARTIAL). | the owner's mapping; providers over the slice 03 stores. |
| VD07 | Account routes need sign-in (G17). | Grants, ledger and saved benefits answer 403 in production. | G17. |
| VD08 | Packets and manifests are a vault-local subset of the blueprint's platform design. The packet integrity is a SHA-256 content hash, not a keyed signature, and packets never leave the process. Manifests lack the blueprint's configuration hash, kill switch, lifecycle stage and autonomy level; the blueprint's own seven packet invariants (approved and redacted fields, consent reference for V2 and above, Share Card for external disclosure, provenance) differ from these seven. | Sound inside one process; not a cross-service protocol. | Adopt the platform packet and manifest when slice 04 builds them; key the integrity hash if packets ever cross a process boundary. |
| VD09 | The ledger is tamper-evident against the app role only. The database owner can rewrite a chain consistently, and removing the newest entries leaves a valid shorter chain (a test pins this). The chain trigger assumes READ COMMITTED: under REPEATABLE READ a concurrent append fails with a unique violation and must be retried. The pull ledger is separate from the slice 03 audit ledger (C06), and discards are not audited (as bridge D05). | An insider with owner rights could hide pulls. | Anchor each chain head outside the database; mirror grant events to the audit ledger. |
| VD10 | Two read paths (as bridge D13): the API reads the registry JSON in process; SQL holds a copy. VERIFIED marks live in the database and reach the API only if startup applies `registry.with_reviews(load_reviews(conn))`. | A review made in the database is invisible to the API until that call is wired. | The integration step in section 15. |
| VD11 | Family coverage has known limits. Guard programs whose family coverage runs through the member's own enrollment (state Guard life insurance, Healthcare for Heroes, the Arizona Guard tuition transfer, the Virginia Guard parks passport, the Missouri relief fund) match the member only. Ten family tags are broader than the text read (listed in `test_family_tagged_records_can_match_a_family_member`). The household route uses only the facts sent with it; it does not pull from other agents. | A spouse or child sees those programs only on the sponsor's results. | Sponsor component and Guard-state facts; per-record review of the ten tags; pulls in the household flow. |
| VD12 | Rules encode necessary conditions only. | A PRELIMINARY_MATCH can still fail conditions kept in the text: branch, service dates, income, years of residence, home of record at entry, school enrollment. Income is never collected. | By design; the "who it is for" text and the official link carry the rest. |
| VD13 | The watcher and discovery cannot run: no fetcher and no search endpoint (hosting). Watcher baselines are in memory, and the research read pages through a summarizing tool, so no raw-page baselines exist. | Changes to source pages are not detected; staleness is by date only (sources read 2026-10-27 become stale after 2027-04-25). | A fetcher, a search endpoint and a baseline table. |
| VD14 | The envelope's `inputs` hash covers the presence of `severe_disability` but not its value, which is never echoed. | Two requests that differ only in that answer have equal input hashes and different outputs. | Accepted for privacy; documented. |
| VD15 | The notice is authored for the vault. | It may differ from the v6 common notice. | Swap in the common notice at integration (C-09; as bridge D06). |
| VD16 | Open conflicts were given defaults here: the Mode B ceiling (V2), four authority tiers (four or five is open), and rules as text expressions inside JSON (YAML or JSON is open). | Changing any of them needs a registry rebuild. | the owner's decisions (Integrated Record §8). |
| VD17 | No screens and no model-written explanations. | The vault is an API and a kernel. | V25; G21 and G23 for any model. |
| VD18 | Retiring an agent manifest that a grant still references makes the seed fail (the foreign key refuses). | Safe, but there is no procedure. | Decide: revoke and discard the grants first, or keep retired manifests. |
| VD19 | Time-bound records: Blue Star Museums (May 16-September 7, 2026), national park fee-free days (2026), the NMCRS 2027-28 window, commercial offers. | They go out of date between reviews. | Review dates per record; the watcher. |
| VD20 | The tier rule is a host heuristic: `.gov`, `.mil` and `.us` hosts are tier 1 unless listed as tier 2. | A commercial `.us` host would be misread as tier 1 (none is in the data). | Review tiers with each new source. |

**Fixed during this build** (each with a test): the key-sorting expression in both 0014 triggers was invalid SQL
(`SELECT DISTINCT ... ORDER BY ... COLLATE`) and no grant or ledger row could be written; malformed grant and
saved-benefit ids reached PostgreSQL and would have answered 500 (now 404 or `removed: false`); the citation
validator and the egress guard disagreed on URLs with ports or user info; keys granted in two separate grants
were refused as KEY_NOT_GRANTED; `ng` and `ngret` asked for a Guard state on federal records; security-definer
functions now put `pg_temp` last in `search_path`; the reviewer field could hold a personal name. The check pass
(section 14) corrected 47 rules.

---

## 14. Verification record

On 2026-10-27, after the build, five records were re-read against their sources: the NPS military passes page
(annual pass for current members and dependents; lifetime pass for veterans, Guard and Reserve service
included, and Gold Star families; entrance and standard amenity fees, not camping or tours), the DoD expanded
access fact sheet (service-connected veterans including 0% with a VHIC, Purple Heart recipients, former POWs and
primary family caregivers; 5% commissary surcharge), Blue Star Museums 2026 (May 16-September 7; serving
members and up to five family members; veterans not included), the MyAirForceBenefits Space-A page, and a
public university's Hazlewood page (the Texas Veterans Commission site refuses automated reading). Two records
were corrected: Space-A for disabled veterans now follows the page's "rated as total" (a 100% rating, or a total
rating for unemployability), and Hazlewood for veterans now accepts a general discharge under honorable
conditions.

A consistency scan then compared every record's family groups and wording with its rule and found rules that
could never match the family members their own text names. 45 rules were corrected: surviving spouses of
members killed or deceased (`ss` and the new `spdec` token), spouses and children for state veterans cemeteries
and homes, and spouses and surviving spouses for property tax relief. The `stn` token now covers the spouse or
child of a member stationed in the state, and `res`/`nonres` now mean legal residence, which is how the pages
use "resident" and "nonresident members stationed in the state". The scan is now a test.

---

## 15. Integration steps

Done on 2026-10-27, except step 4, which waits on the VD06 mapping. The steps as received:

1. Copy the package into the repository, except `database/test_fixtures/standalone_baseline.sql`, the two
   package markers (`backend/app/__init__.py`, `backend/app/domains/__init__.py`) and the two config copies
   (`config/governance_language.yaml`, `config/crisis_floor.yaml`, byte-identical to the slice 02 files).
2. Apply `0014_benefit_vault.sql` after 0013, then `0014_benefit_vault_seed.sql`, each in one transaction, as the
   migration owner.
3. Add the routes to `backend/app/api/v1.py`: build the agent from
   `default_registry().with_reviews(load_reviews(conn))`, then `vault_routes.routes(agent, resolver=...,
   store_factory=lambda tenant: VaultStore(conn))` once G17 provides a tenant resolver.
4. Map the agent ids (VD06) and wire providers over the slice 03 stores.
5. Swap in the v6 common notice (C-09) in `config/benefit_vault_policy.yaml` and rebuild the registry and seed.
6. Run the slice 03 suite (its deletion test confirms `privacy.purge` reaches `vault_pull_grant`,
   `vault_pull_ledger` and `vault_saved_benefit`) and the vault suite as a non-root user.
