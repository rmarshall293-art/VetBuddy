# ADR 0008: MoneyLife Military, the Financial OS core

**Status:** Accepted, 2026-11-06.

**Implementation:**
- `backend/app/domains/moneylife/`
- `web/moneylife.js`
- `config/moneylife_rules.json`
- `backend/tests/test_moneylife.py`
- the guest app's "Money plan" view

## Context

The uploads were:
- *VetBuddy Financial OS: Complete Specification* v4.0 (product requirements);
- the Claude Code, Base44 and QA prompts (process instructions);
- a single-file browser prototype labelled "BROWSER_TESTED".

The zip contained byte-identical copies of the three documents. The spec calls for a module inside VetBuddy (v8 module #9, MoneyLife Military) whose engine could also run standalone. That engine must be deterministic, work in integer cents, carry versioned sources, never count unknown as zero, and never count unconfirmed or proposed money as income.

### What we checked

We ran the prototype in Chromium at 1280 px and 390 px, using Playwright, light and dark. Results:
- all 14 sections render;
- there are no console errors or network requests, and no horizontal overflow.

We also found these defects:

| # | Defect | Spec rule it breaks |
|---|---|---|
| F1 | The default household counts an *illustrative* $4,428.10 VA amount as income in the dashboard margin | §11, §9 "illustrative VA rates … excluded from confirmed income" |
| F2 | The E-5 ETS preset adds VA compensation ($4,318.99, rating 100, not P&T) on top of active-duty pay and OHA, giving a $10,896/month margin | 38 U.S.C. 5304(c) |
| F3 | A blank field becomes $0 (`Number(v) \|\| 0`) | §10 "distinguish unknown from zero" |
| F4 | Negative expenses are accepted (−$9,000 saved) | §10 "reject invalid values" |
| F5 | The college estimate ignores ages (a 30-year-old is still a student) and doubles one cost | §3 college cost |
| F6 | "Confirmed" concurrent receipt sums Chapter 61 retired pay and VA | §7 "never simply sum" |
| F7 | Floating-point money ($4,428.0999…) and whole-dollar display | §10 "preserve cents" |
| F8 | VA rates, BAS and presets are hard-coded in UI code | §17 "never hard-code current rates into UI" |
| F9 | Its 30–90% dependent VA cells match one secondary source and disagree with another | §7 source verification |

## Decision

1. **One engine in two languages, held identical.**
   - `app/domains/moneylife/calc.py` is the authority. `web/moneylife.js` mirrors it line for line, so the guest app can compute with nothing sent anywhere.
   - `test_moneylife.BrowserParity` runs the same golden and refusal cases through both under Node. It requires identical envelopes, warning wording and audit ids included. This follows the pattern of the router and rating kernels (`test_web_parity`).
2. **The arithmetic contract.**
   - Money is integer cents (the corpus rule, premise P8).
   - Rates come in as basis points. Interest uses integer fixed-point at 10^12 (Python `int`, JS `BigInt`), with half-up rounding through one function.
   - Nothing reads a float. A test walks every output for floats.
3. **Twelve calculators.** Each returns the spec's envelope:
   - `calculation_type`, `ruleset_version`, `source_version`, `effective_date`, `as_of_date`, `input_summary`, `output`;
   - `assumptions`, `exclusions`, `data_status`, `confidence`, `warnings`, `disclaimer`, `audit_id`.

   The audit id is an FNV-1a hash of the type, the ruleset and the inputs. It is an identifier, not a security control. The calculators are:
   - loan payment;
   - emergency fund;
   - debt-to-income;
   - debt payoff (avalanche or snowball);
   - savings forecast (with inflation);
   - VA illustration;
   - regular, reserve and Chapter 61 retirement;
   - household cash flow by confidence tier;
   - a forecast of up to 24 months before and 24 after separation, with optimistic, base and downside cases;
   - the spec's state-to-state formula.
4. **Rules the code enforces (each has a test):**
   - Unknown stays unknown: it is excluded and named, never zeroed. An unknown essential spend makes a result "unable to assess".
   - An illustrative VA amount, and proposed law such as the Richard Star Act, always count as *hypothetical*, whatever the person marks them.
   - VA compensation listed beside active-duty pay drops to *expected* (38 U.S.C. 5304(c)).
   - Retired pay listed beside VA drops to *expected* unless the person confirms the DFAS offset.
   - Chapter 61 uses the greater of the years method and the **DoD** percentage, capped at 75%. It never adds VA.
   - In the forecast, an estimated VA amount counts only in the optimistic case.
   - There are no bank connections. Capabilities say so, and the UI says so.
5. **No duplicate data.**
   - Rates live once, in `data/reference/compensation.json`. The engine and the guest app read them from there through the generated kernel data.
   - `config/moneylife_rules.json` holds only limits, vocabularies, scenario defaults, citations and wording.
   - The 56 jurisdictions are the existing registry. A test checks that every name the spec lists is present.
6. **2026 VA rates go into the corpus as UNVERIFIED** (rate set `va_comp_2026`, effective 2025-12-01), with two secondary sources and the prototype.
   - **Agreed cells are loaded:** veteran-alone 10–100%, and every 100% dependent cell. Where the corpus holds the 2025 cell, each equals it × 1.028 to the cent.
   - **The 42 cells for 30–90% with dependents are contested** between the two sources (whole-dollar additions against cell × 1.028). They are recorded as `conflict.va_comp.2026_dependent_cells` and not loaded as rates.
   - For those cells the engine returns the veteran-alone rate as a **floor**, never a pick.
   - VA.gov was not reachable from the build environment, so verification against it is the next step. The engine's VA results are labelled illustrations until a G1 reviewer verifies them.
7. **The API is stateless, guest Mode A:** `GET /api/v1/moneylife/capabilities` and `POST /api/v1/moneylife/{calc_type}`. Nothing is persisted and no account is needed.
8. **Deferred:**
   - Saved households and scenarios: they need sign-in (G17) and must be covered by export and deletion.
   - Pay-table and BAH/OHA calculators: they need dated DFAS and DTMO tables; the corpus has only FY2025 rounded gates.
   - Tax engines, insurance comparisons and college costs.
   - The learning academy.
   - Bank aggregation: it needs a vendor, consent, server-side tokens and deletion.
   - The governance and specialist agents.

## Consequences

- **What it adds:** the guest app gains "Money plan", with five calculators and three invented examples (E-5 overseas ETS, 15-year Chapter 61, Guard member). The browser smoke test covers each tab, refusals and the 390 px layout.
- **Status:** MoneyLife moves from PLANNED to PARTIAL. The prototype is kept as a reference; its prompts are process instructions, not architecture.
- **Not claimed:** no award, entitlement, tax result or lending decision. All examples are synthetic.
