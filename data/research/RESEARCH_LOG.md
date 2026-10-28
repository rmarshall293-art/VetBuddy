# Benefit Vault research log

Working notes for the research ledgers. The importer (`backend/app/domains/vault/discovery/importer.py`)
is the only reader; this file records method and progress so a resumed session can continue.

## Ledger format

`CAT|TITLE|GROUPS|RULE|ELIGIBLE|VALUE|URL`, one benefit per line. Comment lines start with `#`.
A `# JUR=XX SRC=<page> PAGE_UPDATED=<date|none>` line opens each jurisdiction block. Optional header
attributes: `OPENED=<date>` (the day the page was read), `TAIL_UNREAD=<characters>` (text past the
reading limit not yet read), `PART=tail` (a block holding rows from the second read of a long page), and,
with `SRC=none`, `SEEN_IN_SEARCH=<date>` (rows whose link was only seen in search results). `URL` is an
https link or `PAGE` (the block's source page).

RULE may itself contain `|` (the OR operator), so a parser takes the first three fields from the
left, the last three from the right, and joins whatever remains as the RULE. No other field may
contain `|`.

## Categories

INCTAX, PROPTAX, PLATES, GUARD_EDU, EDU, JOBS, GUARD_PAY, HUNTFISH, PARKS, HOMES, BURIAL, BONUS,
OTHER (state ledgers); the federal ledger adds SCHOLARSHIP, PASS, TICKETS, DEALS, TRAVEL, MWR,
HEALTH, HOUSING, INSURANCE, FAMILY, LICENSE.

## Groups

ad, ng, rsv, vet, dv, ret, sp, ch, ss, gs, sm, all.

## Rule tokens (subject = the person the search is for)

true, res, nonres, stn, ad, ng, ngany, ngret, rsv, sm, vet, ret, sc, r>=N, pt, iu, sev, hon, uhc,
otd, wartime, days>=N, age>=N, age<N, ph, moh, pow, gs, sp, ch, dep, ss, spsc, sppt, spiu, spkia,
sppm, spsm, spret, spvet, spdec, spr>=N (meanings in `backend/app/domains/vault/rules.py` and the
registry vocabulary). `res` and `nonres` are about legal residence (the home state for taxes and
voting), which is how the pages use "resident" and "nonresident members stationed in the state";
`stn` also covers the spouse or child of a member stationed in the state. Operators: `&`, `|`, `!`,
parentheses. Rules encode necessary conditions only. When a
condition is uncertain it is left out of the rule and stays in ELIGIBLE (a loose rule shows a
preliminary match the person can read; a strict rule could hide a benefit).

## Sources

State ledgers: MyArmyBenefits State/Territory Benefits pages (U.S. Army, tier 2) read with WebFetch;
each row keeps the official link the page gives for that benefit. Federal programs that state pages
repeat (USERRA, SGLI, TRICARE Reserve Select, federal hiring preference) are dropped from state
ledgers and kept once in the federal ledger.

## Progress

- batch01 (AL AK AZ AR CA CO CT DE FL GA HI ID): done before this log.
- batch02 (IL IN IA KS KY LA ME MD MA MI), batch03 (MN MS MO MT NE NV), batch04 (NH NJ NY NC ND OH),
  batch05 (OK OR PA RI SC SD), batch06 (TN TX UT VT VA WA): done.
- batch07 (WV WI WY DC PR VI MP GU NM): done 2026-10-27. NM comes from the MyAirForceBenefits page (same DoD
  library) because the MyArmyBenefits NM page was not reachable; its last 451 characters are unread (TAIL_UNREAD=451).
- American Samoa: neither DoD site has a State/Territory page and no official territorial page was found. It has
  no block and is recorded as SOURCE_NOT_AVAILABLE in the registry and the defect register.
- Long pages: WebFetch reads 100,000 characters per call. Every page was re-read at offset 100,000 on 2026-10-27;
  pages shorter than that answered "nothing left to read". The tails that existed are in batch08_tails.psv as
  PART=tail blocks (an empty block records a tail read that held nothing new). The main-block TAIL_UNREAD markers
  were removed once the tail was read.
- Rows written: 1,281 across 55 jurisdictions (50 states, DC, PR, VI, MP, GU), after one duplicate Ohio
  veterans homes row was removed from the tails ledger.

## Federal ledger (data/research/federal)

- federal01_core.psv and federal02_deals_family.psv: 81 rows, all JUR=US. Each block names the page that was
  read (OPENED=2026-10-27); the two SRC=none blocks hold 6 rows whose URL was only seen in search results
  (Waves of Honor and NMFA block automated readers; SkillBridge, USERRA, ESGR and the commissary row were not read).
- Sources by tier: agency pages (va.gov, nps.gov, tricare.mil, opm.gov, militaryonesource.mil, home.army.mil),
  DoD benefit libraries (MyArmyBenefits, MyAirForceBenefits), program operators (Fisher House, TAPS, AER/NMCRS/
  AFAS/CGMA, Folds of Honor, American Legion, VFW, MCSF, Tillman, Vet Tix, AFVC, Shades of Green, Hale Koa) and
  vendors' own pages for commercial deals (Home Depot, Lowe's, Amtrak, T-Mobile, Verizon, Hilton, Six Flags).
- Added sponsor tokens: spret (the sponsor is a military retiree) and spvet (the sponsor is a veteran).
- New categories used: PASS, TICKETS, DEALS, TRAVEL, MWR, SCHOLARSHIP, HEALTH, INSURANCE, HOUSING, FAMILY, LICENSE.
- Recovered leads (data/research/recovered) are imported as tier-4 leads and never published as facts.

## Method notes

- New tokens added after batch01: spiu, spsc, true. Batch01 used ngany for "active or retired Guard" in one
  Alabama row; the importer maps nothing automatically, the row was corrected by hand to ng | ngret.
- WebFetch refuses constructed URLs; a WebSearch for the state page puts its URL on the allowlist first.
- The extraction model's rules were reviewed by hand before writing. Recurring fixes: moh and ph swapped, pt written
  for ph, uhc used for iu, days>=N used for time stationed (removed), dependants' rules written about the sponsor
  (rewritten with sp*/dep tokens), double negatives, Guard tokens on state-employee leave rows (ngany | rsv).
- Check pass, 2026-10-27 (after the registry was built). Five records were re-read against their pages (NPS
  military passes, the DoD expanded-access fact sheet, Blue Star Museums 2026, MyAirForceBenefits Space-A, and the
  Stephen F. Austin State University Hazlewood page, because the Texas Veterans Commission site refuses automated
  reading). Space-A for disabled veterans now reads "rated as total" (100% or a total rating for unemployability);
  Hazlewood for veterans now accepts a general discharge under honorable conditions, as the Hazlewood page says.
  A consistency scan then compared each record's family groups and wording with its rule. 45 rules were
  corrected so the family members their text names can match: surviving spouses of members killed or deceased
  (ss and the new spdec token), spouses and children for state veterans cemeteries and homes, and spouses and
  surviving spouses for property tax relief. Family members of members stationed in a state are covered by the
  wider stn token (a code change; those rules were not edited). Guard programs whose family coverage runs
  through the member's own enrollment (state Guard life insurance, for example) stay member-only; ten family
  tags broader than the text read are listed in the defect register (VD11).
- Dropped on purpose: federal programs repeated on state pages (USERRA, SGLI, TRICARE, MSRRA, VA disability and DIC
  tax exclusions, federal funeral honors, Veterans Upward Bound, NADL), medals, certificates, recognition-only
  plates, voting, justice programs and bare links. Federal programs are kept once in the federal ledger.
