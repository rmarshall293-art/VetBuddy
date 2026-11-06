"""MoneyLife calculators. Mirrored line for line by web/moneylife.js.

Arithmetic contract (both languages):
  - money: integer cents
  - rates: integer basis points in, fixed-point at SCALE = 10**12 inside
  - rounding: half up, only through rdiv(), only on non-negative values
  - nothing reads a float
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import ENGINE_NAME, ENGINE_VERSION

ROOT = Path(__file__).resolve().parents[4]
RULES: Dict[str, Any] = json.loads((ROOT / "config" / "moneylife_rules.json").read_text())
COMP: Dict[str, Any] = json.loads((ROOT / "data" / "reference" / "compensation.json").read_text())
LIM = RULES["limits"]
SCALE = 10 ** 12
CASES = ("optimistic", "base", "downside")


class MoneyInputError(ValueError):
    def __init__(self, field: str, message: str):
        super().__init__(f"{field}: {message}")
        self.field = field
        self.message = message


def rdiv(a: int, b: int) -> int:
    """Half-up integer division for a >= 0, b > 0."""
    if a < 0 or b <= 0:
        raise ValueError("rdiv needs a >= 0 and b > 0")
    return (2 * a + b) // (2 * b)


def monthly_rate(apr_bp: int) -> int:
    return rdiv(apr_bp * SCALE, 120000)


def growth(rate: int, months: int) -> int:
    f = SCALE
    for _ in range(months):
        f = rdiv(f * (SCALE + rate), SCALE)
    return f


# ── input reading: unknown is None, never 0 ──────────────────────────────────

def _int(raw: Dict[str, Any], field: str, lo: int, hi: int, required: bool) -> Optional[int]:
    v = raw.get(field)
    if v is None:
        if required:
            raise MoneyInputError(field, "is required")
        return None
    if isinstance(v, bool) or not isinstance(v, int):
        raise MoneyInputError(field, "must be a whole number")
    if v < lo or v > hi:
        raise MoneyInputError(field, f"must be between {lo} and {hi}")
    return v


def cents(raw, field, required=False):
    return _int(raw, field, 0, LIM["max_cents"], required)


def bp(raw, field, required=False):
    return _int(raw, field, 0, LIM["max_apr_bp"], required)


def flag(raw: Dict[str, Any], field: str) -> bool:
    v = raw.get(field, False)
    if not isinstance(v, bool):
        raise MoneyInputError(field, "must be true or false")
    return v


def choice(raw: Dict[str, Any], field: str, options, default=None) -> str:
    v = raw.get(field, default)
    if v not in options:
        raise MoneyInputError(field, "must be one of " + ", ".join(options))
    return v


# ── envelope ─────────────────────────────────────────────────────────────────

def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def fnv1a64(text: str) -> str:
    h = 0xcbf29ce484222325
    for byte in text.encode("utf-8"):
        h ^= byte
        h = (h * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return format(h, "016x")


def envelope(calc_type: str, inputs: Dict[str, Any], output: Dict[str, Any], *, as_of: str,
             effective_date: Optional[str] = None, assumptions=(), exclusions=(), warnings=(),
             data_status: str = "complete", confidence: str = "estimate") -> Dict[str, Any]:
    return {
        "calculation_type": calc_type,
        "engine": f"{ENGINE_NAME}@{ENGINE_VERSION}",
        "ruleset_version": RULES["ruleset_version"],
        "source_version": COMP["version"],
        "effective_date": effective_date,
        "as_of_date": as_of,
        "input_summary": inputs,
        "output": output,
        "assumptions": list(assumptions),
        "exclusions": list(exclusions),
        "data_status": data_status,
        "confidence": confidence,
        "warnings": list(warnings),
        "disclaimer": RULES["disclaimer"],
        "audit_id": "calc-" + fnv1a64(canonical([calc_type, RULES["ruleset_version"], inputs])),
    }


def unable(calc_type: str, inputs, as_of: str, reason: str, **kw) -> Dict[str, Any]:
    kw.pop("confidence", None)                       # nothing was estimated
    return envelope(calc_type, inputs, {}, as_of=as_of, data_status="unable_to_assess", confidence="none",
                    warnings=[reason], **kw)


# ── 1. loan payment ──────────────────────────────────────────────────────────

def loan_payment(raw: Dict[str, Any], as_of: str) -> Dict[str, Any]:
    principal = cents(raw, "principal_cents", True)
    apr = bp(raw, "apr_bp", True)
    months = _int(raw, "months", 1, LIM["max_months"], True)
    inputs = {"principal_cents": principal, "apr_bp": apr, "months": months}
    r = monthly_rate(apr)
    if r == 0:
        payment = rdiv(principal, months)
    else:
        f = growth(r, months)
        payment = rdiv(principal * r * f, SCALE * (f - SCALE))
    balance, interest_total, last = principal, 0, payment
    for m in range(months):
        interest = rdiv(balance * r, SCALE)
        due = balance + interest
        pay = due if m == months - 1 else min(payment, due)
        balance = due - pay
        interest_total += interest
        last = pay
    return envelope("loan_payment", inputs,
                    {"payment_cents": payment, "final_payment_cents": last, "total_interest_cents": interest_total,
                     "total_paid_cents": principal + interest_total},
                    as_of=as_of, assumptions=["Fixed rate and fixed payment; no fees, insurance, taxes or escrow."],
                    exclusions=["Mortgage insurance, VA funding fee, closing costs"])


# ── 2. emergency fund ────────────────────────────────────────────────────────

def emergency_fund(raw: Dict[str, Any], as_of: str) -> Dict[str, Any]:
    essential = cents(raw, "essential_monthly_cents")
    months = _int(raw, "target_months", 1, 24, True)
    saved = cents(raw, "liquid_savings_cents")
    inputs = {"essential_monthly_cents": essential, "target_months": months, "liquid_savings_cents": saved}
    if essential is None:
        return unable("emergency_fund", inputs, as_of, "Enter essential monthly expenses; without them there is no target.")
    target = essential * months
    out = {"target_cents": target}
    warnings = []
    if saved is None:
        warnings.append("Savings not entered, so the gap isn't shown. It isn't assumed to be zero.")
        status = "partial"
    else:
        out["gap_cents"] = max(0, target - saved)
        out["runway_tenths_of_month"] = None if essential == 0 else saved * 10 // essential
        status = "complete"
    return envelope("emergency_fund", inputs, out, as_of=as_of, data_status=status, warnings=warnings,
                    assumptions=[f"Target of {months} months of essential expenses, chosen by you."])


# ── 3. debt-to-income ────────────────────────────────────────────────────────

def debt_to_income(raw: Dict[str, Any], as_of: str) -> Dict[str, Any]:
    debt = cents(raw, "monthly_debt_cents", True)
    income = cents(raw, "gross_monthly_income_cents")
    inputs = {"monthly_debt_cents": debt, "gross_monthly_income_cents": income}
    if not income:
        return unable("debt_to_income", inputs, as_of, "Enter gross monthly income above zero.")
    return envelope("debt_to_income", inputs, {"dti_bp": rdiv(debt * 10000, income)}, as_of=as_of,
                    warnings=["Lenders define qualifying debt and income differently, and VA loans also use residual "
                              "income. This ratio isn't a lending decision."])


# ── 4. debt payoff (avalanche or snowball) ───────────────────────────────────

def debt_payoff(raw: Dict[str, Any], as_of: str) -> Dict[str, Any]:
    method = choice(raw, "method", ("avalanche", "snowball"))
    extra = cents(raw, "extra_monthly_cents") or 0
    items = raw.get("debts")
    if not isinstance(items, list) or not 1 <= len(items) <= LIM["max_debts"]:
        raise MoneyInputError("debts", f"must list 1 to {LIM['max_debts']} debts")
    debts = []
    for i, d in enumerate(items):
        if not isinstance(d, dict):
            raise MoneyInputError(f"debts[{i}]", "must be an object")
        label = d.get("label")
        if not isinstance(label, str) or not 1 <= len(label) <= 60:
            raise MoneyInputError(f"debts[{i}].label", "must be 1 to 60 characters")
        debts.append({"label": label, "balance": cents(d, "balance_cents", True), "apr": bp(d, "apr_bp", True),
                      "minimum": cents(d, "minimum_cents", True), "paid_month": None})
        if debts[-1]["balance"] == 0:
            debts[-1]["paid_month"] = 0
    inputs = {"method": method, "extra_monthly_cents": extra,
              "debts": [{"label": d["label"], "balance_cents": d["balance"], "apr_bp": d["apr"],
                         "minimum_cents": d["minimum"]} for d in debts]}
    budget = sum(d["minimum"] for d in debts) + extra
    first_interest = sum(rdiv(d["balance"] * monthly_rate(d["apr"]), SCALE) for d in debts)
    if budget <= first_interest and any(d["balance"] for d in debts):
        return unable("debt_payoff", inputs, as_of,
                      "The monthly payments don't cover the interest, so the balance never falls.")
    total_interest, month = 0, 0
    while any(d["balance"] > 0 for d in debts):
        if month >= LIM["max_months"]:
            return unable("debt_payoff", inputs, as_of, "Not paid off within 50 years at these payments.")
        month += 1
        left = budget
        for d in debts:
            if d["balance"] > 0:
                interest = rdiv(d["balance"] * monthly_rate(d["apr"]), SCALE)
                d["balance"] += interest
                total_interest += interest
        for d in debts:
            pay = min(d["minimum"], d["balance"], left)
            d["balance"] -= pay
            left -= pay
        key = (lambda d: (-d["apr"], d["balance"])) if method == "avalanche" else (lambda d: (d["balance"], -d["apr"]))
        for d in sorted([d for d in debts if d["balance"] > 0], key=key):
            pay = min(d["balance"], left)
            d["balance"] -= pay
            left -= pay
        for d in debts:
            if d["balance"] == 0 and d["paid_month"] is None:
                d["paid_month"] = month
    return envelope("debt_payoff", inputs,
                    {"months": month, "total_interest_cents": total_interest,
                     "payoff_order": [d["label"] for d in sorted(debts, key=lambda d: (d["paid_month"], d["label"]))],
                     "paid_month": {d["label"]: d["paid_month"] for d in debts}},
                    as_of=as_of, assumptions=["Fixed rates, no new borrowing, no fees; minimums freed by a paid-off "
                                              "debt roll into the next one."])


# ── 5. savings forecast ──────────────────────────────────────────────────────

def savings_forecast(raw: Dict[str, Any], as_of: str) -> Dict[str, Any]:
    start = cents(raw, "initial_cents", True)
    deposit = cents(raw, "monthly_deposit_cents") or 0
    apr = bp(raw, "hypothetical_apr_bp", True)
    months = _int(raw, "months", 1, LIM["max_months"], True)
    inflation = bp(raw, "inflation_bp")
    inputs = {"initial_cents": start, "monthly_deposit_cents": deposit, "hypothetical_apr_bp": apr, "months": months,
              "inflation_bp": inflation}
    r, bal = monthly_rate(apr), start
    for _ in range(months):
        bal = bal + rdiv(bal * r, SCALE) + deposit
    out = {"balance_cents": bal, "contributed_cents": start + deposit * months,
           "growth_cents": bal - start - deposit * months}
    if inflation is not None:
        out["todays_dollars_cents"] = rdiv(bal * SCALE, growth(monthly_rate(inflation), months))
    return envelope("savings_forecast", inputs, out, as_of=as_of, confidence="illustrative",
                    assumptions=["The rate is a what-if you chose, compounded monthly, deposits at month end."],
                    warnings=["Returns aren't guaranteed. This is not investment advice."])


# ── 6. VA compensation illustration ──────────────────────────────────────────

V26 = COMP["va_compensation_2026"]
CONTESTED = {(c["table"], c["rating"]) for c in V26["contested"]}


def _va_cell(table: str, rating: int) -> Optional[int]:
    if table == "veteran_alone":
        return V26["veteran_alone"].get(str(rating))
    if rating == 100:
        return V26["dependents_100"].get(table)
    return None


def va_illustration(raw: Dict[str, Any], as_of: str) -> Dict[str, Any]:
    rating = _int(raw, "rating", 0, 100, True)
    if rating % 10:
        raise MoneyInputError("rating", "must be a multiple of 10")
    married = flag(raw, "married")
    under18 = _int(raw, "children_under_18", 0, LIM["max_children"], False) or 0
    school = _int(raw, "children_in_school", 0, LIM["max_children"], False) or 0
    aa = flag(raw, "spouse_aid_and_attendance")
    inputs = {"rating": rating, "married": married, "children_under_18": under18, "children_in_school": school,
              "spouse_aid_and_attendance": aa}
    kw = dict(effective_date=V26["effective_from"], confidence="illustrative")
    common = ["Not an award. VA decides the amount and the date it starts.",
              "Dependent parents and Special Monthly Compensation aren't included."]
    if aa and not married:
        raise MoneyInputError("spouse_aid_and_attendance", "needs a spouse")
    if rating == 0:
        return envelope("va_illustration", inputs, {"monthly_cents": 0}, as_of=as_of, warnings=common,
                        exclusions=["A 0% rating has no monthly payment."], **kw)
    if rating < 30:
        notes = common + (["Ratings below 30% have no dependent additions."] if (married or under18 or school) else [])
        return envelope("va_illustration", inputs, {"monthly_cents": _va_cell("veteran_alone", rating),
                                                    "cells": [["veteran_alone", rating]]}, as_of=as_of, warnings=notes, **kw)
    if under18 == 0 and school > 0:
        return unable("va_illustration", inputs, as_of, "When every child is 18 to 23 and in school, VA's table is "
                      "applied differently. Use VA's rate page for this case.", **kw)
    base = ("with_spouse_and_child" if married else "with_child") if under18 else ("with_spouse" if married else "veteran_alone")
    cells = [[base, rating]]
    if under18 > 1:
        cells.append(["each_additional_child_under_18", rating, under18 - 1])
    if school:
        cells.append(["each_additional_child_18_23_in_school", rating, school])
    if aa:
        cells.append(["spouse_aid_and_attendance", rating, 1])
    alone = _va_cell("veteran_alone", rating)
    if any((c[0], rating) in CONTESTED for c in cells):
        return envelope("va_illustration", inputs, {"floor_cents": alone, "cells": [["veteran_alone", rating]]},
                        as_of=as_of, data_status="partial",
                        warnings=common + [f"Two sources disagree on the 2026 {rating}% amounts with dependents "
                                           f"({V26['contested_conflict_id']}). Shown: the veteran-alone rate, which "
                                           "the dependent amount is at least."], **kw)
    total = _va_cell(base, rating)
    for c in cells[1:]:
        total += _va_cell(c[0], rating) * c[2]
    return envelope("va_illustration", inputs, {"monthly_cents": total, "cells": cells}, as_of=as_of,
                    warnings=common, **kw)


# ── 7. retirement ────────────────────────────────────────────────────────────

SYSTEMS = {s["id"]: s for s in COMP["retirement_systems"]["systems"]}
PER_YEAR_BP = {k: int(SYSTEMS[k]["multiplier_pct_per_year"].replace(".", "")) * 10 ** (2 - len(
    SYSTEMS[k]["multiplier_pct_per_year"].partition(".")[2])) for k in ("high3", "brs")}   # "2.5" -> 250, no floats


def kernel_data() -> Dict[str, Any]:
    """What web/moneylife.js needs, generated into web/kernel_data.js by scripts/build_web.py."""
    return {"RULES": RULES, "PER_YEAR_BP": PER_YEAR_BP, "SOURCE_VERSION": COMP["version"],
            "ENGINE": f"{ENGINE_NAME}@{ENGINE_VERSION}",
            "V26": {k: V26[k] for k in ("rate_set", "effective_from", "status", "veteran_alone", "dependents_100",
                                       "contested_conflict_id")},
            "CONTESTED": sorted([t, r] for t, r in CONTESTED),
            "EXAMPLES": json.loads((ROOT / "data" / "demo" / "moneylife_examples.json").read_text())["examples"]}


def regular_retirement(raw: Dict[str, Any], as_of: str) -> Dict[str, Any]:
    system = choice(raw, "system", ("high3", "brs"))
    high36 = cents(raw, "high36_monthly_cents", True)
    months = _int(raw, "service_months", 0, LIM["max_service_months"], True)
    inputs = {"system": system, "high36_monthly_cents": high36, "service_months": months}
    per = PER_YEAR_BP[system]
    warnings = ["DFAS computes the actual amount. Cost-of-living adjustments, survivor plan costs and VA waivers "
                "aren't applied."]
    if months < 240:
        warnings.insert(0, "Regular retirement generally needs 20 years. This shows the formula only; disability "
                           "retirement and early-retirement programs use different rules.")
    return envelope("regular_retirement", inputs,
                    {"multiplier_bp": rdiv(per * months, 12), "monthly_gross_cents": rdiv(high36 * per * months, 120000)},
                    as_of=as_of, warnings=warnings, assumptions=[RULES["citations"]["regular_multiplier"]])


def reserve_retirement(raw: Dict[str, Any], as_of: str) -> Dict[str, Any]:
    system = choice(raw, "system", ("high3", "brs"))
    high36 = cents(raw, "high36_monthly_cents", True)
    points = _int(raw, "points", 0, LIM["max_reserve_points"], True)
    inputs = {"system": system, "high36_monthly_cents": high36, "points": points}
    per = PER_YEAR_BP[system]
    return envelope("reserve_retirement", inputs,
                    {"equivalent_years_hundredths": rdiv(points * 100, 360),
                     "multiplier_bp": rdiv(per * points, 360),
                     "monthly_gross_cents": rdiv(high36 * per * points, 3600000)},
                    as_of=as_of, assumptions=[RULES["citations"]["reserve_points"]],
                    warnings=["Needs 20 qualifying years. Pay usually starts at 60, earlier with qualifying active "
                              "service; High-36 is measured when pay starts, not today."])


def chapter61_retirement(raw: Dict[str, Any], as_of: str) -> Dict[str, Any]:
    system = choice(raw, "system", ("high3", "brs"))
    high36 = cents(raw, "high36_monthly_cents", True)
    months = _int(raw, "service_months", 0, LIM["max_service_months"], True)
    dod = _int(raw, "dod_disability_pct", 30, 100, True)
    inputs = {"system": system, "high36_monthly_cents": high36, "service_months": months, "dod_disability_pct": dod}
    years_bp = rdiv(PER_YEAR_BP[system] * months, 12)
    rating_bp = dod * 100
    used = min(max(years_bp, rating_bp), 7500)
    return envelope("chapter61_retirement", inputs,
                    {"years_method_bp": years_bp, "rating_method_bp": rating_bp, "multiplier_bp": used,
                     "method": "rating" if rating_bp > years_bp else "years",
                     "monthly_gross_cents": rdiv(high36 * used, 10000)},
                    as_of=as_of, assumptions=[RULES["citations"]["chapter61"]],
                    warnings=["The DoD disability percentage is not the VA rating; enter the one on the DoD decision.",
                              "With under 20 years, VA compensation usually reduces this retired pay dollar for dollar "
                              "unless Combat-Related Special Compensation applies. It is never simply added to VA pay.",
                              "Temporary disability retirement (TDRL) is reviewed and can change."])


# ── 8. household cash flow ───────────────────────────────────────────────────

MILITARY_PAY = {"military_pay", "military_allowance"}


def cash_flow(raw: Dict[str, Any], as_of: str) -> Dict[str, Any]:
    items = raw.get("lines")
    if not isinstance(items, list) or len(items) > LIM["max_lines"]:
        raise MoneyInputError("lines", f"must list up to {LIM['max_lines']} income lines")
    lines = []
    for i, ln in enumerate(items):
        if not isinstance(ln, dict):
            raise MoneyInputError(f"lines[{i}]", "must be an object")
        label = ln.get("label")
        if not isinstance(label, str) or not 1 <= len(label) <= 60:
            raise MoneyInputError(f"lines[{i}].label", "must be 1 to 60 characters")
        lines.append({"label": label, "monthly_cents": cents(ln, "monthly_cents"),
                      "kind": choice(ln, "kind", RULES["line_kinds"]),
                      "confidence": choice(ln, "confidence", RULES["confidence"])})
    offset_confirmed = flag(raw, "retired_pay_offset_confirmed")
    out_fields = ("essential_expenses_cents", "debt_payments_cents", "insurance_cents", "taxes_cents")
    outs = {f: cents(raw, f) for f in out_fields}
    inputs = {"lines": [dict(x) for x in lines], "retired_pay_offset_confirmed": offset_confirmed, **outs}
    warnings, exclusions = [], []
    kinds = {x["kind"] for x in lines if x["monthly_cents"]}
    for x in lines:
        reason = None
        if x["kind"] in RULES["always_hypothetical"] and x["confidence"] != "hypothetical":
            x["confidence"], reason = "hypothetical", RULES["always_hypothetical"][x["kind"]]
        elif x["kind"] == "va_compensation" and kinds & MILITARY_PAY and x["confidence"] == "confirmed":
            x["confidence"], reason = "expected", RULES["citations"]["va_active_duty"] + \
                " It is counted as expected, not confirmed, while active-duty pay is listed."
        elif (x["kind"] == "military_retired_pay" and {"va_compensation", "va_illustration"} & kinds
              and not offset_confirmed and x["confidence"] == "confirmed"):
            x["confidence"], reason = "expected", ("Retired pay is usually reduced by VA compensation unless CRDP or "
                                                   "CRSC applies. Enter the net amount from your DFAS statement and "
                                                   "mark the offset confirmed to count it as confirmed.")
        if reason:
            warnings.append(f"{x['label']}: {reason}")
        x["counted_as"] = x["confidence"]
        if x["monthly_cents"] is None:
            exclusions.append(f"{x['label']}: amount unknown, left out (not counted as zero)")
    tiers = {t: sum(x["monthly_cents"] for x in lines if x["monthly_cents"] is not None and x["counted_as"] == t)
             for t in RULES["confidence"]}
    known_out = sum(v for v in outs.values() if v is not None)
    for f, v in outs.items():
        if v is None:
            exclusions.append(f"{f.removesuffix('_cents').replace('_', ' ')}: unknown, left out (not counted as zero)")
    if outs["taxes_cents"] is None:
        warnings.append("Taxes not entered: the margins below are before tax.")
    out = {"income_cents": tiers, "outflow_cents": known_out,
           "margin_confirmed_cents": tiers["confirmed"] - known_out,
           "margin_with_expected_cents": tiers["confirmed"] + tiers["expected"] - known_out,
           "margin_with_hypothetical_cents": sum(tiers.values()) - known_out,
           "lines": [{"label": x["label"], "kind": x["kind"], "monthly_cents": x["monthly_cents"],
                      "counted_as": x["counted_as"]} for x in lines]}
    return envelope("cash_flow", inputs, out, as_of=as_of, warnings=warnings, exclusions=exclusions,
                    data_status="partial" if exclusions else "complete")


# ── 9. transition forecast: up to 24 months before, 24 after ─────────────────

def transition_forecast(raw: Dict[str, Any], as_of: str) -> Dict[str, Any]:
    before = _int(raw, "months_until_separation", 0, LIM["max_months_before_separation"], True)
    savings = cents(raw, "current_savings_cents", True)
    pay_before = cents(raw, "net_income_before_cents", True)
    exp_before = cents(raw, "expenses_before_cents", True)
    civ = cents(raw, "civilian_net_after_cents")
    exp_after = cents(raw, "expenses_after_cents")
    retired = cents(raw, "retired_pay_net_after_cents") or 0
    other = cents(raw, "other_net_after_cents") or 0
    va = cents(raw, "va_monthly_cents") or 0
    va_status = choice(raw, "va_status", ("none", "confirmed", "estimate"), "none")
    if va and va_status == "none":
        raise MoneyInputError("va_status", "is needed when a VA amount is entered")
    delays = dict(RULES["scenario_defaults"]["job_delay_months"])
    for case in CASES:
        v = _int(raw, f"job_delay_{case}", 0, 24, False)
        if v is not None:
            delays[case] = v
    va_delay = _int(raw, "va_estimate_delay_months", 0, 24, False)
    va_delay = RULES["scenario_defaults"]["va_estimate_delay_months"]["optimistic"] if va_delay is None else va_delay
    events = raw.get("one_time", []) or []
    if not isinstance(events, list) or len(events) > 12:
        raise MoneyInputError("one_time", "must list up to 12 one-time amounts")
    one_time = []
    for i, e in enumerate(events):
        if not isinstance(e, dict) or not isinstance(e.get("label"), str) or not 1 <= len(e["label"]) <= 60:
            raise MoneyInputError(f"one_time[{i}]", "needs a label of 1 to 60 characters")
        one_time.append({"label": e["label"], "month": _int(e, "month", -before, 23, True),
                         "cents": cents(e, "cents", True), "direction": choice(e, "direction", ("in", "out"))})
    inputs = {"months_until_separation": before, "current_savings_cents": savings, "net_income_before_cents": pay_before,
              "expenses_before_cents": exp_before, "civilian_net_after_cents": civ, "expenses_after_cents": exp_after,
              "retired_pay_net_after_cents": retired, "other_net_after_cents": other, "va_monthly_cents": va,
              "va_status": va_status, "job_delays": delays, "va_estimate_delay_months": va_delay, "one_time": one_time}
    warnings, assumptions = [], [f"Job starts after {delays['optimistic']}, {delays['base']} and {delays['downside']} "
                                 "months in the optimistic, base and downside cases (your assumption)."]
    if civ is None:
        warnings.append("No civilian income entered, so after separation these cases show how long savings last "
                        "with none. Unknown pay isn't treated as a salary.")
    if exp_after is None:
        exp_after = exp_before
        assumptions.append("Expenses after separation equal expenses now (not entered).")
    if va_status == "estimate":
        warnings.append(f"The VA amount is an estimate, so it counts only in the optimistic case, from month "
                        f"{va_delay} after separation. Base and downside leave it out.")
    if retired:
        warnings.append("Retired pay is used as entered: enter the net after any VA waiver.")
    cases = {}
    for case in CASES:
        bal, rows = savings, []
        low, low_month, first_negative, at_sep = savings, -before, None, savings
        for m in range(-before, 24):
            hyp = 0
            if m < 0:
                conf, out = pay_before, exp_before
            else:
                conf = (civ or 0) * (m >= delays[case]) + retired + other
                if va_status == "confirmed":
                    conf += va
                elif va_status == "estimate" and case == "optimistic" and m >= va_delay:
                    hyp = va
                out = exp_after
            for e in one_time:
                if e["month"] == m:
                    if e["direction"] == "in":
                        conf += e["cents"]
                    else:
                        out += e["cents"]
            if m == 0:
                at_sep = bal
            net = conf + hyp - out
            bal += net
            rows.append([m, conf, hyp, out, net, bal])
            if bal < low:
                low, low_month = bal, m
            if bal < 0 and first_negative is None:
                first_negative = m
        cases[case] = {"rows": rows, "lowest_balance_cents": low, "lowest_month": low_month,
                       "first_negative_month": first_negative, "balance_at_separation_cents": at_sep,
                       "end_balance_cents": bal,
                       "runway_tenths_at_separation": None if exp_after == 0 or at_sep <= 0 else at_sep * 10 // exp_after}
    return envelope("transition_forecast", inputs, {"row_columns": ["month", "confirmed_in_cents", "hypothetical_in_cents",
                                                                     "out_cents", "net_cents", "balance_cents"],
                                                    "cases": cases},
                    as_of=as_of, assumptions=assumptions, warnings=warnings,
                    exclusions=["Taxes are whatever you built into the net amounts", "Investment returns"],
                    data_status="partial" if civ is None else "complete")


# ── 10. state-to-state comparison (spec §3 formula) ──────────────────────────

def state_comparison(raw: Dict[str, Any], as_of: str) -> Dict[str, Any]:
    origin = cents(raw, "origin_net_disposable_annual_cents", True)
    dest = cents(raw, "destination_net_disposable_annual_cents", True)
    years = _int(raw, "moving_cost_years", 1, 30, False) or 1
    parts = {k: cents(raw, k) for k in ("verified_education_savings_annual_cents", "approved_tax_savings_annual_cents",
                                        "incremental_housing_insurance_annual_cents", "moving_costs_cents")}
    inputs = {"origin_net_disposable_annual_cents": origin, "destination_net_disposable_annual_cents": dest,
              "moving_cost_years": years, **parts}
    exclusions = [f"{k.removesuffix('_cents').replace('_', ' ')}: unknown, left out (not counted as zero)"
                  for k, v in parts.items() if v is None]
    p = {k: v or 0 for k, v in parts.items()}
    move = rdiv(p["moving_costs_cents"], years)
    adv = (dest - origin + p["verified_education_savings_annual_cents"] + p["approved_tax_savings_annual_cents"]
           - p["incremental_housing_insurance_annual_cents"] - move)
    return envelope("state_comparison", inputs, {"annual_advantage_cents": adv, "moving_cost_per_year_cents": move},
                    as_of=as_of, exclusions=exclusions, data_status="partial" if exclusions else "complete",
                    warnings=["Only verified education savings and approved tax savings belong here; a benefit "
                              "you might qualify for is not a saving yet. Property-tax relief isn't cash income."])


CALCULATORS = {
    "loan_payment": loan_payment, "emergency_fund": emergency_fund, "debt_to_income": debt_to_income,
    "debt_payoff": debt_payoff, "savings_forecast": savings_forecast, "va_illustration": va_illustration,
    "regular_retirement": regular_retirement, "reserve_retirement": reserve_retirement,
    "chapter61_retirement": chapter61_retirement, "cash_flow": cash_flow,
    "transition_forecast": transition_forecast, "state_comparison": state_comparison,
}


def calculate(calc_type: str, raw: Dict[str, Any], as_of: str) -> Dict[str, Any]:
    if calc_type not in CALCULATORS:
        raise MoneyInputError("calculation_type", "unknown calculation")
    if not isinstance(raw, dict):
        raise MoneyInputError("body", "must be a JSON object")
    return CALCULATORS[calc_type](raw, as_of)


def capabilities() -> Dict[str, Any]:
    return {"engine": f"{ENGINE_NAME}@{ENGINE_VERSION}", "ruleset_version": RULES["ruleset_version"],
            "calculations": sorted(CALCULATORS), "persists": False,
            "bank_connections": "not available: needs a server-side aggregator, consent and sign-in (spec §13)",
            "va_rates": {"rate_set": V26["rate_set"], "effective_from": V26["effective_from"], "status": V26["status"],
                         "contested_cells": len(CONTESTED), "conflict_id": V26["contested_conflict_id"]},
            "verify_links": RULES["verify_links"]}


__all__ = ["calculate", "capabilities", "CALCULATORS", "MoneyInputError", "rdiv", "growth", "monthly_rate"]
