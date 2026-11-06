"""MoneyLife Military core (ADR 0008). Adversarial by intent: each test tries to
get an unconfirmed amount counted as income, an unknown counted as zero, two
offsetting payments added together, or the browser and server to disagree.

Sections:
  1. arithmetic against published or hand-checked values
  2. the specification's controls (unknown != 0, no stacking, labels)
  3. the specification's reference scenarios (Alabama/Texas, E-5 OHA ETS,
     15-year Chapter 61 at 50%, Guard/AGR, unknown fields, no bank provider)
  4. input refusal
  5. browser parity: web/moneylife.js on the same golden cases, wording included
  6. the stateless API
"""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

from app.domains.moneylife import calc
from app.domains.moneylife.calc import MoneyInputError, calculate

ROOT = Path(__file__).resolve().parents[2]
TODAY = "2026-11-06"


def run(t, raw):
    return calculate(t, raw, TODAY)


def out(t, raw):
    return run(t, raw)["output"]


# ── golden cases: shared by the Python tests and the browser parity run ──────

GOLDEN = [
    ("loan_payment", {"principal_cents": 30000000, "apr_bp": 650, "months": 360}),
    ("loan_payment", {"principal_cents": 1200000, "apr_bp": 0, "months": 36}),
    ("loan_payment", {"principal_cents": 2500000, "apr_bp": 699, "months": 60}),
    ("loan_payment", {"principal_cents": 1, "apr_bp": 10000, "months": 1}),
    ("emergency_fund", {"essential_monthly_cents": 520000, "target_months": 6, "liquid_savings_cents": 1000000}),
    ("emergency_fund", {"essential_monthly_cents": 520000, "target_months": 6}),
    ("emergency_fund", {"target_months": 3, "liquid_savings_cents": 5}),
    ("emergency_fund", {"essential_monthly_cents": 0, "target_months": 3, "liquid_savings_cents": 5}),
    ("debt_to_income", {"monthly_debt_cents": 45000, "gross_monthly_income_cents": 708333}),
    ("debt_to_income", {"monthly_debt_cents": 45000, "gross_monthly_income_cents": 0}),
    ("debt_payoff", {"method": "avalanche", "extra_monthly_cents": 20000, "debts": [
        {"label": "Card", "balance_cents": 500000, "apr_bp": 2400, "minimum_cents": 15000},
        {"label": "Car", "balance_cents": 1800000, "apr_bp": 700, "minimum_cents": 40000}]}),
    ("debt_payoff", {"method": "snowball", "extra_monthly_cents": 20000, "debts": [
        {"label": "Card", "balance_cents": 500000, "apr_bp": 2400, "minimum_cents": 15000},
        {"label": "Store card", "balance_cents": 90000, "apr_bp": 2900, "minimum_cents": 3500},
        {"label": "Car", "balance_cents": 1800000, "apr_bp": 700, "minimum_cents": 40000}]}),
    ("debt_payoff", {"method": "avalanche", "debts": [
        {"label": "Card", "balance_cents": 1000000, "apr_bp": 2400, "minimum_cents": 10000}]}),
    ("debt_payoff", {"method": "snowball", "debts": [
        {"label": "Paid", "balance_cents": 0, "apr_bp": 500, "minimum_cents": 0},
        {"label": "Loan", "balance_cents": 100000, "apr_bp": 500, "minimum_cents": 10000}]}),
    ("savings_forecast", {"initial_cents": 1000000, "monthly_deposit_cents": 50000, "hypothetical_apr_bp": 400,
                          "months": 120, "inflation_bp": 300}),
    ("savings_forecast", {"initial_cents": 0, "monthly_deposit_cents": 10000, "hypothetical_apr_bp": 0, "months": 12}),
    *[("va_illustration", {"rating": r}) for r in range(0, 101, 10)],
    ("va_illustration", {"rating": 100, "married": True, "children_under_18": 2}),
    ("va_illustration", {"rating": 100, "married": True, "children_under_18": 1, "children_in_school": 1,
                         "spouse_aid_and_attendance": True}),
    ("va_illustration", {"rating": 100, "children_under_18": 3}),
    ("va_illustration", {"rating": 50, "married": True, "children_under_18": 2}),
    ("va_illustration", {"rating": 70, "married": True}),
    ("va_illustration", {"rating": 20, "married": True, "children_under_18": 1}),
    ("va_illustration", {"rating": 100, "married": True, "children_in_school": 2}),
    ("regular_retirement", {"system": "high3", "high36_monthly_cents": 500000, "service_months": 240}),
    ("regular_retirement", {"system": "brs", "high36_monthly_cents": 612345, "service_months": 263}),
    ("regular_retirement", {"system": "high3", "high36_monthly_cents": 500000, "service_months": 180}),
    ("reserve_retirement", {"system": "high3", "high36_monthly_cents": 500000, "points": 4800}),
    ("reserve_retirement", {"system": "brs", "high36_monthly_cents": 731111, "points": 5123}),
    ("chapter61_retirement", {"system": "high3", "high36_monthly_cents": 420000, "service_months": 180, "dod_disability_pct": 50}),
    ("chapter61_retirement", {"system": "high3", "high36_monthly_cents": 420000, "service_months": 300, "dod_disability_pct": 30}),
    ("chapter61_retirement", {"system": "brs", "high36_monthly_cents": 420000, "service_months": 420, "dod_disability_pct": 100}),
    ("cash_flow", {"lines": [
        {"label": "Civilian wages", "monthly_cents": 708333, "kind": "civilian_wages", "confidence": "confirmed"},
        {"label": "VA award", "monthly_cents": 442810, "kind": "va_compensation", "confidence": "confirmed"},
        {"label": "Retired pay", "monthly_cents": None, "kind": "military_retired_pay", "confidence": "confirmed"},
        {"label": "Richard Star Act", "monthly_cents": 90000, "kind": "proposed_legislation", "confidence": "confirmed"}],
        "essential_expenses_cents": 520000, "debt_payments_cents": 45000}),
    ("cash_flow", {"lines": [
        {"label": "Base pay", "monthly_cents": 330000, "kind": "military_pay", "confidence": "confirmed"},
        {"label": "OHA", "monthly_cents": 180000, "kind": "military_allowance", "confidence": "confirmed"},
        {"label": "VA estimate", "monthly_cents": 431899, "kind": "va_illustration", "confidence": "expected"},
        {"label": "VA paid", "monthly_cents": 10000, "kind": "va_compensation", "confidence": "confirmed"}],
        "essential_expenses_cents": 470000, "debt_payments_cents": 0, "insurance_cents": 0, "taxes_cents": 40000}),
    ("cash_flow", {"lines": [
        {"label": "Chapter 61 retired pay", "monthly_cents": 210000, "kind": "military_retired_pay", "confidence": "confirmed"},
        {"label": "VA award", "monthly_cents": 132290, "kind": "va_compensation", "confidence": "confirmed"}],
        "essential_expenses_cents": 490000}),
    ("cash_flow", {"lines": [
        {"label": "Net retired pay (DFAS)", "monthly_cents": 77710, "kind": "military_retired_pay", "confidence": "confirmed"},
        {"label": "VA award", "monthly_cents": 132290, "kind": "va_compensation", "confidence": "confirmed"}],
        "retired_pay_offset_confirmed": True, "essential_expenses_cents": 0}),
    ("transition_forecast", {"months_until_separation": 6, "current_savings_cents": 1500000, "net_income_before_cents": 520000,
                             "expenses_before_cents": 470000, "civilian_net_after_cents": 350000,
                             "va_monthly_cents": 431899, "va_status": "estimate",
                             "one_time": [{"label": "Move home", "month": 0, "cents": 600000, "direction": "out"},
                                          {"label": "Leave sell-back", "month": -1, "cents": 250000, "direction": "in"}]}),
    ("transition_forecast", {"months_until_separation": 24, "current_savings_cents": 200000, "net_income_before_cents": 400000,
                             "expenses_before_cents": 410000, "expenses_after_cents": 380000}),
    ("transition_forecast", {"months_until_separation": 0, "current_savings_cents": 3000000, "net_income_before_cents": 0,
                             "expenses_before_cents": 450000, "civilian_net_after_cents": 500000,
                             "retired_pay_net_after_cents": 120000, "va_monthly_cents": 132290, "va_status": "confirmed",
                             "job_delay_optimistic": 1, "job_delay_base": 4, "job_delay_downside": 9}),
    ("state_comparison", {"origin_net_disposable_annual_cents": 7000000, "destination_net_disposable_annual_cents": 7300000,
                          "moving_costs_cents": 900000, "moving_cost_years": 3}),
    ("state_comparison", {"origin_net_disposable_annual_cents": 7000000, "destination_net_disposable_annual_cents": 6900000,
                          "verified_education_savings_annual_cents": 1200000, "approved_tax_savings_annual_cents": 0,
                          "incremental_housing_insurance_annual_cents": 300000, "moving_costs_cents": 0}),
]

BAD = [
    ("loan_payment", {"principal_cents": -1, "apr_bp": 500, "months": 12}),
    ("loan_payment", {"principal_cents": 100.5, "apr_bp": 500, "months": 12}),
    ("loan_payment", {"principal_cents": True, "apr_bp": 500, "months": 12}),
    ("loan_payment", {"principal_cents": 100, "apr_bp": 500, "months": 0}),
    ("loan_payment", {"principal_cents": 100, "apr_bp": 10001, "months": 12}),
    ("loan_payment", {"principal_cents": 100000000001, "apr_bp": 1, "months": 12}),
    ("loan_payment", {"principal_cents": "1000", "apr_bp": 1, "months": 12}),
    ("va_illustration", {"rating": 55}),
    ("va_illustration", {"rating": 100, "spouse_aid_and_attendance": True}),
    ("va_illustration", {"rating": 100, "married": "yes"}),
    ("debt_payoff", {"method": "avalanche", "debts": []}),
    ("debt_payoff", {"method": "fastest", "debts": [{"label": "x", "balance_cents": 1, "apr_bp": 1, "minimum_cents": 1}]}),
    ("cash_flow", {"lines": [{"label": "", "monthly_cents": 1, "kind": "other", "confidence": "confirmed"}]}),
    ("cash_flow", {"lines": [{"label": "x", "monthly_cents": 1, "kind": "lottery", "confidence": "confirmed"}]}),
    ("transition_forecast", {"months_until_separation": 25, "current_savings_cents": 0, "net_income_before_cents": 0,
                             "expenses_before_cents": 0}),
    ("transition_forecast", {"months_until_separation": 3, "current_savings_cents": 0, "net_income_before_cents": 0,
                             "expenses_before_cents": 0, "va_monthly_cents": 100}),
    ("transition_forecast", {"months_until_separation": 3, "current_savings_cents": 0, "net_income_before_cents": 0,
                             "expenses_before_cents": 0, "one_time": [{"label": "x", "month": -4, "cents": 1, "direction": "in"}]}),
    ("chapter61_retirement", {"system": "high3", "high36_monthly_cents": 1, "service_months": 1, "dod_disability_pct": 20}),
    ("no_such_calc", {}),
]


# ── 1. arithmetic ────────────────────────────────────────────────────────────

class Arithmetic(unittest.TestCase):
    def test_standard_mortgage_payment(self):
        # $300,000 at 6.5% for 30 years: the published amortization figure is $1,896.20.
        self.assertEqual(out("loan_payment", {"principal_cents": 30000000, "apr_bp": 650, "months": 360})["payment_cents"],
                         189620)

    def test_zero_rate_loan_and_the_last_payment_absorbs_rounding(self):
        o = out("loan_payment", {"principal_cents": 1200000, "apr_bp": 0, "months": 36})
        self.assertEqual((o["payment_cents"], o["total_interest_cents"], o["total_paid_cents"]), (33333, 0, 1200000))
        self.assertEqual(o["payment_cents"] * 35 + o["final_payment_cents"], 1200000)

    def test_va_100_married_two_children_matches_the_spec_illustration(self):
        # Spec §4: $4,428.10 a month ($4,318.99 with spouse and child + $109.11 for the second child).
        self.assertEqual(out("va_illustration", {"rating": 100, "married": True, "children_under_18": 2})["monthly_cents"],
                         442810)

    def test_retirement_multipliers(self):
        self.assertEqual(out("regular_retirement", {"system": "high3", "high36_monthly_cents": 500000,
                                                    "service_months": 240})["monthly_gross_cents"], 250000)
        self.assertEqual(out("regular_retirement", {"system": "brs", "high36_monthly_cents": 500000,
                                                    "service_months": 240})["monthly_gross_cents"], 200000)
        r = out("reserve_retirement", {"system": "high3", "high36_monthly_cents": 500000, "points": 4800})
        self.assertEqual((r["equivalent_years_hundredths"], r["monthly_gross_cents"]), (1333, 166667))

    def test_chapter61_uses_the_greater_method_and_caps_at_75(self):
        a = out("chapter61_retirement", {"system": "high3", "high36_monthly_cents": 420000, "service_months": 180,
                                         "dod_disability_pct": 50})
        self.assertEqual((a["method"], a["multiplier_bp"], a["monthly_gross_cents"]), ("rating", 5000, 210000))
        b = out("chapter61_retirement", {"system": "high3", "high36_monthly_cents": 420000, "service_months": 300,
                                         "dod_disability_pct": 30})
        self.assertEqual((b["method"], b["multiplier_bp"]), ("years", 6250))
        c = out("chapter61_retirement", {"system": "brs", "high36_monthly_cents": 420000, "service_months": 420,
                                         "dod_disability_pct": 100})
        self.assertEqual(c["multiplier_bp"], 7500)

    def test_savings_at_zero_rate_is_exactly_the_contributions(self):
        o = out("savings_forecast", {"initial_cents": 0, "monthly_deposit_cents": 10000, "hypothetical_apr_bp": 0, "months": 12})
        self.assertEqual((o["balance_cents"], o["growth_cents"]), (120000, 0))

    def test_inflation_shrinks_todays_dollars(self):
        o = out("savings_forecast", {"initial_cents": 1000000, "monthly_deposit_cents": 50000, "hypothetical_apr_bp": 400,
                                     "months": 120, "inflation_bp": 300})
        self.assertLess(o["todays_dollars_cents"], o["balance_cents"])

    def test_avalanche_and_snowball_order(self):
        debts = [{"label": "Card", "balance_cents": 500000, "apr_bp": 2400, "minimum_cents": 15000},
                 {"label": "Store card", "balance_cents": 90000, "apr_bp": 1200, "minimum_cents": 3500},
                 {"label": "Car", "balance_cents": 1800000, "apr_bp": 700, "minimum_cents": 40000}]
        av = out("debt_payoff", {"method": "avalanche", "extra_monthly_cents": 20000, "debts": debts})
        sb = out("debt_payoff", {"method": "snowball", "extra_monthly_cents": 20000, "debts": debts})
        self.assertEqual(sb["payoff_order"][0], "Store card")
        self.assertLessEqual(av["total_interest_cents"], sb["total_interest_cents"])

    def test_no_floats_reach_any_output(self):
        def walk(v):
            if isinstance(v, float):
                raise AssertionError(f"float in output: {v}")
            for x in (v.values() if isinstance(v, dict) else v if isinstance(v, list) else []):
                walk(x)
        for t, raw in GOLDEN:
            walk(run(t, raw))


# ── 2. the specification's controls ─────────────────────────────────────────

class Controls(unittest.TestCase):
    def test_every_result_carries_the_full_envelope(self):
        keys = {"calculation_type", "ruleset_version", "source_version", "effective_date", "as_of_date", "input_summary",
                "output", "assumptions", "exclusions", "data_status", "confidence", "warnings", "disclaimer", "audit_id"}
        for t, raw in GOLDEN:
            with self.subTest(t=t):
                self.assertLessEqual(keys, set(run(t, raw)))

    def test_audit_id_is_deterministic_and_input_sensitive(self):
        a = run("debt_to_income", {"monthly_debt_cents": 1, "gross_monthly_income_cents": 2})["audit_id"]
        self.assertEqual(a, run("debt_to_income", {"monthly_debt_cents": 1, "gross_monthly_income_cents": 2})["audit_id"])
        self.assertNotEqual(a, run("debt_to_income", {"monthly_debt_cents": 1, "gross_monthly_income_cents": 3})["audit_id"])

    def test_unknown_is_never_zero(self):
        r = run("emergency_fund", {"essential_monthly_cents": 520000, "target_months": 6})
        self.assertNotIn("gap_cents", r["output"])
        self.assertEqual(r["data_status"], "partial")
        self.assertEqual(run("emergency_fund", {"target_months": 6})["data_status"], "unable_to_assess")
        cf = run("cash_flow", GOLDEN_BY["cash_flow"][0])
        self.assertIn("Retired pay: amount unknown, left out (not counted as zero)", cf["exclusions"])
        self.assertIn("taxes: unknown, left out (not counted as zero)", cf["exclusions"])
        self.assertIn("Taxes not entered: the margins below are before tax.", cf["warnings"])

    def test_proposed_law_and_va_illustrations_are_never_confirmed(self):
        cf = run("cash_flow", GOLDEN_BY["cash_flow"][0])
        star = next(x for x in cf["output"]["lines"] if x["kind"] == "proposed_legislation")
        self.assertEqual(star["counted_as"], "hypothetical")
        self.assertEqual(cf["output"]["income_cents"]["confirmed"], 708333 + 442810)
        e5 = run("cash_flow", GOLDEN_BY["cash_flow"][1])
        est = next(x for x in e5["output"]["lines"] if x["kind"] == "va_illustration")
        self.assertEqual(est["counted_as"], "hypothetical")

    def test_va_pay_isnt_confirmed_beside_active_duty_pay(self):
        e5 = run("cash_flow", GOLDEN_BY["cash_flow"][1])
        paid = next(x for x in e5["output"]["lines"] if x["label"] == "VA paid")
        self.assertEqual(paid["counted_as"], "expected")
        self.assertTrue(any("38 U.S.C. 5304(c)" in w for w in e5["warnings"]))

    def test_retired_pay_and_va_are_never_simply_added(self):
        ch61 = run("cash_flow", GOLDEN_BY["cash_flow"][2])
        rp = next(x for x in ch61["output"]["lines"] if x["kind"] == "military_retired_pay")
        self.assertEqual(rp["counted_as"], "expected")
        self.assertEqual(ch61["output"]["income_cents"]["confirmed"], 132290)
        net = run("cash_flow", GOLDEN_BY["cash_flow"][3])
        self.assertEqual(net["output"]["income_cents"]["confirmed"], 77710 + 132290)

    def test_contested_va_cells_show_a_floor_never_a_pick(self):
        r = run("va_illustration", {"rating": 50, "married": True, "children_under_18": 2})
        self.assertNotIn("monthly_cents", r["output"])
        self.assertEqual(r["output"]["floor_cents"], 113290)
        self.assertEqual(r["data_status"], "partial")
        self.assertTrue(any("conflict.va_comp.2026_dependent_cells" in w for w in r["warnings"]))
        self.assertEqual(len(calc.CONTESTED), 42)

    def test_va_illustration_is_labelled_and_dated(self):
        r = run("va_illustration", {"rating": 100})
        self.assertEqual((r["confidence"], r["effective_date"]), ("illustrative", "2025-12-01"))
        self.assertIn("Not an award. VA decides the amount and the date it starts.", r["warnings"])

    def test_estimated_va_counts_only_in_the_optimistic_case(self):
        f = out("transition_forecast", GOLDEN_BY["transition_forecast"][0])
        hyp = {c: sum(row[2] for row in f["cases"][c]["rows"]) for c in f["cases"]}
        self.assertGreater(hyp["optimistic"], 0)
        self.assertEqual((hyp["base"], hyp["downside"]), (0, 0))

    def test_forecast_spans_24_months_each_side_and_finds_the_cliff(self):
        f = out("transition_forecast", GOLDEN_BY["transition_forecast"][1])
        rows = f["cases"]["base"]["rows"]
        self.assertEqual((len(rows), rows[0][0], rows[-1][0]), (48, -24, 23))
        self.assertIsNotNone(f["cases"]["base"]["first_negative_month"])
        self.assertEqual(run("transition_forecast", GOLDEN_BY["transition_forecast"][1])["data_status"], "partial")

    def test_cases_are_ordered_by_risk(self):
        f = out("transition_forecast", GOLDEN_BY["transition_forecast"][2])["cases"]
        self.assertGreaterEqual(f["optimistic"]["end_balance_cents"], f["base"]["end_balance_cents"])
        self.assertGreaterEqual(f["base"]["end_balance_cents"], f["downside"]["end_balance_cents"])

    def test_state_comparison_leaves_unknowns_out(self):
        r = run("state_comparison", GOLDEN_BY["state_comparison"][0])
        self.assertEqual(r["output"]["annual_advantage_cents"], 300000 - 300000)
        self.assertEqual(len(r["exclusions"]), 3)

    def test_no_payment_never_pays_off(self):
        r = run("debt_payoff", GOLDEN_BY["debt_payoff"][2])
        self.assertEqual(r["data_status"], "unable_to_assess")


GOLDEN_BY = {}
for _t, _raw in GOLDEN:
    GOLDEN_BY.setdefault(_t, []).append(_raw)


# ── 3. the specification's reference scenarios ──────────────────────────────

class ReferenceScenarios(unittest.TestCase):
    def test_all_56_jurisdictions_are_selectable_from_the_existing_registry(self):
        from app.domains.reference.corpus import known_jurisdictions
        names = {j["name"] for j in known_jurisdictions()}
        spec = ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", "Florida",
                "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine",
                "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska",
                "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
                "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas",
                "Utah", "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming", "District of Columbia",
                "Puerto Rico", "Guam", "U.S. Virgin Islands", "American Samoa", "Northern Mariana Islands"]
        missing = [n for n in spec if n not in names]
        self.assertEqual(missing, [], "names the spec uses but the registry spells differently or lacks")

    def test_alabama_texas_married_100_pt_two_children(self):
        # Combined wages $85,000; VA award entered as confirmed; retired pay of unknown type and amount.
        cf = run("cash_flow", {"lines": [
            {"label": "Combined civilian wages", "monthly_cents": 708333, "kind": "civilian_wages", "confidence": "confirmed"},
            {"label": "VA award", "monthly_cents": 442810, "kind": "va_compensation", "confidence": "confirmed"},
            {"label": "Retired pay", "monthly_cents": None, "kind": "military_retired_pay", "confidence": "expected"}],
            "essential_expenses_cents": 520000, "debt_payments_cents": 45000})
        self.assertEqual(cf["output"]["income_cents"]["confirmed"], 1151143)
        self.assertEqual(cf["data_status"], "partial")
        # No tax saving between the states is computed: only entered, approved figures count.
        sc = run("state_comparison", {"origin_net_disposable_annual_cents": 10000000,
                                      "destination_net_disposable_annual_cents": 10000000})
        self.assertEqual(sc["output"]["annual_advantage_cents"], 0)
        self.assertEqual(len(sc["exclusions"]), 4)

    def test_e5_overseas_oha_to_ets(self):
        f = out("transition_forecast", {"months_until_separation": 4, "current_savings_cents": 800000,
                                        "net_income_before_cents": 330000 + 180000 + 47695,
                                        "expenses_before_cents": 470000, "expenses_after_cents": 380000 + 180000,
                                        "civilian_net_after_cents": 400000, "va_monthly_cents": 431899,
                                        "va_status": "estimate"})
        base = f["cases"]["base"]
        self.assertTrue(all(r[1] == 0 for r in base["rows"] if 0 <= r[0] < 3))      # OHA and pay stop; job not started
        self.assertIsNotNone(base["first_negative_month"])                          # the cliff the prototype hid

    def test_15_year_chapter61_at_50_percent(self):
        r = run("chapter61_retirement", {"system": "high3", "high36_monthly_cents": 420000, "service_months": 180,
                                         "dod_disability_pct": 50})
        self.assertTrue(any("never simply added to VA pay" in w for w in r["warnings"]))
        self.assertNotIn("combined_cents", r["output"])

    def test_guard_member_with_agr_time(self):
        r = run("reserve_retirement", {"system": "high3", "high36_monthly_cents": 600000, "points": 18 * 50 + 3 * 365})
        self.assertEqual(r["output"]["equivalent_years_hundredths"], rdiv_hundredths(18 * 50 + 3 * 365))
        self.assertTrue(any("Needs 20 qualifying years" in w for w in r["warnings"]))

    def test_unavailable_bank_provider_is_said_plainly(self):
        self.assertTrue(calc.capabilities()["bank_connections"].startswith("not available"))
        self.assertFalse(calc.capabilities()["persists"])


def rdiv_hundredths(points):
    return calc.rdiv(points * 100, 360)


# ── 4. input refusal ─────────────────────────────────────────────────────────

class Refusal(unittest.TestCase):
    def test_bad_inputs_are_refused_with_the_field(self):
        for t, raw in BAD:
            with self.subTest(t=t, raw=raw), self.assertRaises(MoneyInputError) as e:
                run(t, raw)
            self.assertTrue(e.exception.field)

    def test_nan_and_infinity_from_json_are_refused(self):
        for token in ("NaN", "Infinity", "-Infinity"):
            raw = json.loads('{"principal_cents": %s, "apr_bp": 1, "months": 1}' % token)
            with self.subTest(token=token), self.assertRaises(MoneyInputError):
                run("loan_payment", raw)


# ── 5. browser parity ───────────────────────────────────────────────────────

NODE = """
import { calculate } from %s;
const fx = JSON.parse(process.argv[1]);
const res = [];
for (const [t, raw] of fx.cases) {
  try { res.push({ ok: calculate(t, raw, fx.today) }); }
  catch (e) { res.push({ err: [e.field ?? null, e.message] }); }
}
process.stdout.write(JSON.stringify(res));
"""


@unittest.skipUnless(shutil.which("node"), "node not installed")
class BrowserParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = NODE % json.dumps((ROOT / "web/moneylife.js").as_uri())
        cases = [[t, raw] for t, raw in GOLDEN + BAD]
        res = subprocess.run(["node", "--input-type=module", "-e", script, json.dumps({"cases": cases, "today": TODAY})],
                             capture_output=True, text=True, timeout=120)
        if res.returncode:
            raise AssertionError(res.stderr)
        cls.js = json.loads(res.stdout)

    def test_golden_cases_identical_wording_included(self):
        for (t, raw), js in zip(GOLDEN, self.js):
            with self.subTest(t=t, raw=raw):
                self.assertEqual(js, {"ok": json.loads(json.dumps(run(t, raw)))})

    def test_refusals_identical(self):
        for (t, raw), js in zip(BAD, self.js[len(GOLDEN):]):
            with self.subTest(t=t, raw=raw):
                with self.assertRaises(MoneyInputError) as e:
                    run(t, raw)
                self.assertEqual(js, {"err": [e.exception.field, e.exception.message]})


# ── 6. stateless API ─────────────────────────────────────────────────────────

class Api(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from starlette.testclient import TestClient
        from tests.support import settings
        from app.api.main import create_app
        cls.client = TestClient(create_app(settings()))

    def test_calculate_and_capabilities(self):
        r = self.client.post("/api/v1/moneylife/va_illustration", json={"rating": 100, "married": True,
                                                                         "children_under_18": 2})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["output"]["monthly_cents"], 442810)
        c = self.client.get("/api/v1/moneylife/capabilities").json()
        self.assertEqual(c["va_rates"]["contested_cells"], 42)

    def test_errors_name_the_field_and_store_nothing(self):
        r = self.client.post("/api/v1/moneylife/loan_payment", json={"principal_cents": -5, "apr_bp": 1, "months": 1})
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json()["error"]["fields"][0]["field"], "principal_cents")
        self.assertEqual(self.client.post("/api/v1/moneylife/horoscope", json={}).status_code, 404)
        self.assertEqual(self.client.post("/api/v1/moneylife/loan_payment", content=b"{").status_code, 400)
