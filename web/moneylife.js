// MoneyLife Military — browser half of the Financial OS core (ADR 0008).
// A line-for-line mirror of backend/app/domains/moneylife/calc.py. Data comes
// from kernel_data.js, which scripts/build_web.py GENERATES from
// config/moneylife_rules.json and data/reference/compensation.json.
// tests/test_moneylife.py runs the same golden cases through both and
// requires identical output, wording included.
//
// Arithmetic: integer cents; interest in BigInt fixed-point (SCALE = 10^12);
// half-up rounding only through rdiv(); no floats anywhere.
import { KDATA } from "./kernel_data.js";

const ML = KDATA.MONEYLIFE;
const RULES = ML.RULES, LIM = RULES.limits, V26 = ML.V26;
const SCALE = 10n ** 12n;
const CASES = ["optimistic", "base", "downside"];
const has = (o, k) => Object.prototype.hasOwnProperty.call(o, k);

export class MoneyInputError extends Error {
  constructor(field, message) { super(message); this.field = field; }
}

function rdivB(a, b) {                       // BigInt, a >= 0, b > 0
  if (a < 0n || b <= 0n) throw new Error("rdiv needs a >= 0 and b > 0");
  return (2n * a + b) / (2n * b);
}
const rdiv = (a, b) => Number(rdivB(BigInt(a), BigInt(b)));
const monthlyRate = aprBp => rdivB(BigInt(aprBp) * SCALE, 120000n);
function growth(rate, months) {
  let f = SCALE;
  for (let i = 0; i < months; i++) f = rdivB(f * (SCALE + rate), SCALE);
  return f;
}
const interestOn = (balance, rate) => Number(rdivB(BigInt(balance) * rate, SCALE));

// ── input reading: unknown is null, never 0 ──
function int(raw, field, lo, hi, required) {
  const v = raw[field];
  if (v === undefined || v === null) {
    if (required) throw new MoneyInputError(field, "is required");
    return null;
  }
  if (typeof v !== "number" || !Number.isInteger(v)) throw new MoneyInputError(field, "must be a whole number");
  if (v < lo || v > hi) throw new MoneyInputError(field, `must be between ${lo} and ${hi}`);
  return v;
}
const cents = (raw, f, req = false) => int(raw, f, 0, LIM.max_cents, req);
const bp = (raw, f, req = false) => int(raw, f, 0, LIM.max_apr_bp, req);
function flag(raw, field) {
  const v = has(raw, field) ? raw[field] : false;
  if (typeof v !== "boolean") throw new MoneyInputError(field, "must be true or false");
  return v;
}
function choice(raw, field, options, dflt = undefined) {
  const v = has(raw, field) ? raw[field] : dflt;
  if (!options.includes(v)) throw new MoneyInputError(field, "must be one of " + options.join(", "));
  return v;
}
const label60 = v => typeof v === "string" && v.length >= 1 && v.length <= 60;

// ── envelope ──
export function canonical(v) {
  if (v === null || v === undefined) return "null";
  if (Array.isArray(v)) return "[" + v.map(canonical).join(",") + "]";
  if (typeof v === "object") return "{" + Object.keys(v).sort().map(k => JSON.stringify(k) + ":" + canonical(v[k])).join(",") + "}";
  return JSON.stringify(v);
}
export function fnv1a64(text) {
  let h = 0xcbf29ce484222325n;
  for (const byte of new TextEncoder().encode(text)) { h ^= BigInt(byte); h = (h * 0x100000001b3n) & 0xFFFFFFFFFFFFFFFFn; }
  return h.toString(16).padStart(16, "0");
}
function envelope(calcType, inputs, output, { asOf, effectiveDate = null, assumptions = [], exclusions = [], warnings = [],
  dataStatus = "complete", confidence = "estimate" }) {
  return {
    calculation_type: calcType, engine: ML.ENGINE, ruleset_version: RULES.ruleset_version, source_version: ML.SOURCE_VERSION,
    effective_date: effectiveDate, as_of_date: asOf, input_summary: inputs, output,
    assumptions: [...assumptions], exclusions: [...exclusions], data_status: dataStatus, confidence,
    warnings: [...warnings], disclaimer: RULES.disclaimer,
    audit_id: "calc-" + fnv1a64(canonical([calcType, RULES.ruleset_version, inputs])),
  };
}
const unable = (t, inputs, asOf, reason, kw = {}) =>
  envelope(t, inputs, {}, { ...kw, asOf, dataStatus: "unable_to_assess", confidence: "none", warnings: [reason] });

// ── 1. loan payment ──
function loanPayment(raw, asOf) {
  const principal = cents(raw, "principal_cents", true), apr = bp(raw, "apr_bp", true);
  const months = int(raw, "months", 1, LIM.max_months, true);
  const inputs = { principal_cents: principal, apr_bp: apr, months };
  const r = monthlyRate(apr);
  let payment;
  if (r === 0n) payment = rdiv(principal, months);
  else { const f = growth(r, months); payment = Number(rdivB(BigInt(principal) * r * f, SCALE * (f - SCALE))); }
  let balance = principal, total = 0, last = payment;
  for (let m = 0; m < months; m++) {
    const interest = interestOn(balance, r), due = balance + interest;
    const pay = m === months - 1 ? due : Math.min(payment, due);
    balance = due - pay; total += interest; last = pay;
  }
  return envelope("loan_payment", inputs, { payment_cents: payment, final_payment_cents: last, total_interest_cents: total,
    total_paid_cents: principal + total }, { asOf, assumptions: ["Fixed rate and fixed payment; no fees, insurance, taxes or escrow."],
    exclusions: ["Mortgage insurance, VA funding fee, closing costs"] });
}

// ── 2. emergency fund ──
function emergencyFund(raw, asOf) {
  const essential = cents(raw, "essential_monthly_cents"), months = int(raw, "target_months", 1, 24, true);
  const saved = cents(raw, "liquid_savings_cents");
  const inputs = { essential_monthly_cents: essential, target_months: months, liquid_savings_cents: saved };
  if (essential === null) return unable("emergency_fund", inputs, asOf, "Enter essential monthly expenses; without them there is no target.");
  const target = essential * months, out = { target_cents: target }, warnings = [];
  let status;
  if (saved === null) { warnings.push("Savings not entered, so the gap isn't shown. It isn't assumed to be zero."); status = "partial"; }
  else { out.gap_cents = Math.max(0, target - saved); out.runway_tenths_of_month = essential === 0 ? null : Math.floor(saved * 10 / essential); status = "complete"; }
  return envelope("emergency_fund", inputs, out, { asOf, dataStatus: status, warnings,
    assumptions: [`Target of ${months} months of essential expenses, chosen by you.`] });
}

// ── 3. debt-to-income ──
function debtToIncome(raw, asOf) {
  const debt = cents(raw, "monthly_debt_cents", true), income = cents(raw, "gross_monthly_income_cents");
  const inputs = { monthly_debt_cents: debt, gross_monthly_income_cents: income };
  if (!income) return unable("debt_to_income", inputs, asOf, "Enter gross monthly income above zero.");
  return envelope("debt_to_income", inputs, { dti_bp: rdiv(debt * 10000, income) }, { asOf,
    warnings: ["Lenders define qualifying debt and income differently, and VA loans also use residual income. This ratio isn't a lending decision."] });
}

// ── 4. debt payoff ──
function cmp(a, b) { for (let i = 0; i < a.length; i++) { if (a[i] < b[i]) return -1; if (a[i] > b[i]) return 1; } return 0; }
function debtPayoff(raw, asOf) {
  const method = choice(raw, "method", ["avalanche", "snowball"]);
  const extra = cents(raw, "extra_monthly_cents") ?? 0;
  const items = raw.debts;
  if (!Array.isArray(items) || items.length < 1 || items.length > LIM.max_debts) throw new MoneyInputError("debts", `must list 1 to ${LIM.max_debts} debts`);
  const debts = items.map((d, i) => {
    if (typeof d !== "object" || d === null || Array.isArray(d)) throw new MoneyInputError(`debts[${i}]`, "must be an object");
    if (!label60(d.label)) throw new MoneyInputError(`debts[${i}].label`, "must be 1 to 60 characters");
    const x = { label: d.label, balance: cents(d, "balance_cents", true), apr: bp(d, "apr_bp", true), minimum: cents(d, "minimum_cents", true), paid_month: null };
    if (x.balance === 0) x.paid_month = 0;
    return x;
  });
  const inputs = { method, extra_monthly_cents: extra, debts: debts.map(d => ({ label: d.label, balance_cents: d.balance, apr_bp: d.apr, minimum_cents: d.minimum })) };
  const budget = debts.reduce((s, d) => s + d.minimum, 0) + extra;
  const firstInterest = debts.reduce((s, d) => s + interestOn(d.balance, monthlyRate(d.apr)), 0);
  if (budget <= firstInterest && debts.some(d => d.balance)) return unable("debt_payoff", inputs, asOf, "The monthly payments don't cover the interest, so the balance never falls.");
  let total = 0, month = 0;
  const key = method === "avalanche" ? d => [-d.apr, d.balance] : d => [d.balance, -d.apr];
  while (debts.some(d => d.balance > 0)) {
    if (month >= LIM.max_months) return unable("debt_payoff", inputs, asOf, "Not paid off within 50 years at these payments.");
    month += 1;
    let left = budget;
    for (const d of debts) if (d.balance > 0) { const i = interestOn(d.balance, monthlyRate(d.apr)); d.balance += i; total += i; }
    for (const d of debts) { const pay = Math.min(d.minimum, d.balance, left); d.balance -= pay; left -= pay; }
    for (const d of debts.filter(d => d.balance > 0).sort((a, b) => cmp(key(a), key(b)))) { const pay = Math.min(d.balance, left); d.balance -= pay; left -= pay; }
    for (const d of debts) if (d.balance === 0 && d.paid_month === null) d.paid_month = month;
  }
  const paid = {};
  for (const d of debts) paid[d.label] = d.paid_month;
  return envelope("debt_payoff", inputs, { months: month, total_interest_cents: total,
    payoff_order: [...debts].sort((a, b) => cmp([a.paid_month, a.label], [b.paid_month, b.label])).map(d => d.label), paid_month: paid },
    { asOf, assumptions: ["Fixed rates, no new borrowing, no fees; minimums freed by a paid-off debt roll into the next one."] });
}

// ── 5. savings forecast ──
function savingsForecast(raw, asOf) {
  const start = cents(raw, "initial_cents", true), deposit = cents(raw, "monthly_deposit_cents") ?? 0;
  const apr = bp(raw, "hypothetical_apr_bp", true), months = int(raw, "months", 1, LIM.max_months, true);
  const inflation = bp(raw, "inflation_bp");
  const inputs = { initial_cents: start, monthly_deposit_cents: deposit, hypothetical_apr_bp: apr, months, inflation_bp: inflation };
  const r = monthlyRate(apr);
  let bal = start;
  for (let i = 0; i < months; i++) bal = bal + interestOn(bal, r) + deposit;
  const out = { balance_cents: bal, contributed_cents: start + deposit * months, growth_cents: bal - start - deposit * months };
  if (inflation !== null) out.todays_dollars_cents = Number(rdivB(BigInt(bal) * SCALE, growth(monthlyRate(inflation), months)));
  return envelope("savings_forecast", inputs, out, { asOf, confidence: "illustrative",
    assumptions: ["The rate is a what-if you chose, compounded monthly, deposits at month end."],
    warnings: ["Returns aren't guaranteed. This is not investment advice."] });
}

// ── 6. VA compensation illustration ──
function vaCell(table, rating) {
  if (table === "veteran_alone") return V26.veteran_alone[String(rating)] ?? null;
  return (V26.dependents[table] || {})[String(rating)] ?? null;
}
function vaIllustration(raw, asOf) {
  const rating = int(raw, "rating", 0, 100, true);
  if (rating % 10) throw new MoneyInputError("rating", "must be a multiple of 10");
  const married = flag(raw, "married");
  const under18 = int(raw, "children_under_18", 0, LIM.max_children, false) || 0;
  const school = int(raw, "children_in_school", 0, LIM.max_children, false) || 0;
  const aa = flag(raw, "spouse_aid_and_attendance");
  const inputs = { rating, married, children_under_18: under18, children_in_school: school, spouse_aid_and_attendance: aa };
  const kw = { effectiveDate: V26.effective_from, confidence: "illustrative" };
  const common = ["Not an award. VA decides the amount and the date it starts.",
    "Dependent parents and Special Monthly Compensation aren't included."];
  if (aa && !married) throw new MoneyInputError("spouse_aid_and_attendance", "needs a spouse");
  if (rating === 0) return envelope("va_illustration", inputs, { monthly_cents: 0 }, { ...kw, asOf, warnings: common, exclusions: ["A 0% rating has no monthly payment."] });
  if (rating < 30) {
    const notes = [...common, ...((married || under18 || school) ? ["Ratings below 30% have no dependent additions."] : [])];
    return envelope("va_illustration", inputs, { monthly_cents: vaCell("veteran_alone", rating), cells: [["veteran_alone", rating]] }, { ...kw, asOf, warnings: notes });
  }
  if (under18 === 0 && school > 0) return unable("va_illustration", inputs, asOf, "When every child is 18 to 23 and in school, VA's table is applied differently. Use VA's rate page for this case.", kw);
  const base = under18 ? (married ? "with_spouse_and_child" : "with_child") : (married ? "with_spouse" : "veteran_alone");
  const cells = [[base, rating]];
  if (under18 > 1) cells.push(["each_additional_child_under_18", rating, under18 - 1]);
  if (school) cells.push(["each_additional_child_18_23_in_school", rating, school]);
  if (aa) cells.push(["spouse_aid_and_attendance", rating, 1]);
  let total = vaCell(base, rating);
  for (const c of cells.slice(1)) total += vaCell(c[0], rating) * c[2];
  return envelope("va_illustration", inputs, { monthly_cents: total, cells }, { ...kw, asOf, warnings: common });
}

// ── 7. retirement ──
const DFAS_NOTE = "DFAS computes the actual amount. Cost-of-living adjustments, survivor plan costs and VA waivers aren't applied.";
function regularRetirement(raw, asOf) {
  const system = choice(raw, "system", ["high3", "brs"]), high36 = cents(raw, "high36_monthly_cents", true);
  const months = int(raw, "service_months", 0, LIM.max_service_months, true);
  const inputs = { system, high36_monthly_cents: high36, service_months: months };
  const per = ML.PER_YEAR_BP[system], warnings = [DFAS_NOTE];
  if (months < 240) warnings.unshift("Regular retirement generally needs 20 years. This shows the formula only; disability retirement and early-retirement programs use different rules.");
  return envelope("regular_retirement", inputs, { multiplier_bp: rdiv(per * months, 12), monthly_gross_cents: rdiv(BigInt(high36) * BigInt(per) * BigInt(months), 120000) },
    { asOf, warnings, assumptions: [RULES.citations.regular_multiplier] });
}
function reserveRetirement(raw, asOf) {
  const system = choice(raw, "system", ["high3", "brs"]), high36 = cents(raw, "high36_monthly_cents", true);
  const points = int(raw, "points", 0, LIM.max_reserve_points, true);
  const inputs = { system, high36_monthly_cents: high36, points };
  const per = ML.PER_YEAR_BP[system];
  return envelope("reserve_retirement", inputs, { equivalent_years_hundredths: rdiv(points * 100, 360), multiplier_bp: rdiv(per * points, 360),
    monthly_gross_cents: rdiv(BigInt(high36) * BigInt(per) * BigInt(points), 3600000) }, { asOf, assumptions: [RULES.citations.reserve_points],
    warnings: ["Needs 20 qualifying years. Pay usually starts at 60, earlier with qualifying active service; High-36 is measured when pay starts, not today."] });
}
function chapter61Retirement(raw, asOf) {
  const system = choice(raw, "system", ["high3", "brs"]), high36 = cents(raw, "high36_monthly_cents", true);
  const months = int(raw, "service_months", 0, LIM.max_service_months, true), dod = int(raw, "dod_disability_pct", 30, 100, true);
  const inputs = { system, high36_monthly_cents: high36, service_months: months, dod_disability_pct: dod };
  const yearsBp = rdiv(ML.PER_YEAR_BP[system] * months, 12), ratingBp = dod * 100, used = Math.min(Math.max(yearsBp, ratingBp), 7500);
  return envelope("chapter61_retirement", inputs, { years_method_bp: yearsBp, rating_method_bp: ratingBp, multiplier_bp: used,
    method: ratingBp > yearsBp ? "rating" : "years", monthly_gross_cents: rdiv(BigInt(high36) * BigInt(used), 10000) }, { asOf,
    assumptions: [RULES.citations.chapter61],
    warnings: ["The DoD disability percentage is not the VA rating; enter the one on the DoD decision.",
      "With under 20 years, VA compensation usually reduces this retired pay dollar for dollar unless Combat-Related Special Compensation applies. It is never simply added to VA pay.",
      "Temporary disability retirement (TDRL) is reviewed and can change."] });
}

// ── 8. household cash flow ──
const MILITARY_PAY = ["military_pay", "military_allowance"];
const pretty = f => f.replace(/_cents$/, "").replaceAll("_", " ");
function cashFlow(raw, asOf) {
  const items = raw.lines;
  if (!Array.isArray(items) || items.length > LIM.max_lines) throw new MoneyInputError("lines", `must list up to ${LIM.max_lines} income lines`);
  const lines = items.map((ln, i) => {
    if (typeof ln !== "object" || ln === null || Array.isArray(ln)) throw new MoneyInputError(`lines[${i}]`, "must be an object");
    if (!label60(ln.label)) throw new MoneyInputError(`lines[${i}].label`, "must be 1 to 60 characters");
    return { label: ln.label, monthly_cents: cents(ln, "monthly_cents"), kind: choice(ln, "kind", RULES.line_kinds), confidence: choice(ln, "confidence", RULES.confidence) };
  });
  const offsetConfirmed = flag(raw, "retired_pay_offset_confirmed");
  const outFields = ["essential_expenses_cents", "debt_payments_cents", "insurance_cents", "taxes_cents"];
  const outs = {};
  for (const f of outFields) outs[f] = cents(raw, f);
  const inputs = { lines: lines.map(x => ({ ...x })), retired_pay_offset_confirmed: offsetConfirmed, ...outs };
  const warnings = [], exclusions = [];
  const kinds = new Set(lines.filter(x => x.monthly_cents).map(x => x.kind));
  for (const x of lines) {
    let reason = null;
    if (has(RULES.always_hypothetical, x.kind) && x.confidence !== "hypothetical") { x.confidence = "hypothetical"; reason = RULES.always_hypothetical[x.kind]; }
    else if (x.kind === "va_compensation" && MILITARY_PAY.some(k => kinds.has(k)) && x.confidence === "confirmed") {
      x.confidence = "expected"; reason = RULES.citations.va_active_duty + " It is counted as expected, not confirmed, while active-duty pay is listed.";
    } else if (x.kind === "military_retired_pay" && (kinds.has("va_compensation") || kinds.has("va_illustration")) && !offsetConfirmed && x.confidence === "confirmed") {
      x.confidence = "expected"; reason = "Retired pay is usually reduced by VA compensation unless CRDP or CRSC applies. Enter the net amount from your DFAS statement and mark the offset confirmed to count it as confirmed.";
    }
    if (reason) warnings.push(`${x.label}: ${reason}`);
    x.counted_as = x.confidence;
    if (x.monthly_cents === null) exclusions.push(`${x.label}: amount unknown, left out (not counted as zero)`);
  }
  const tiers = {};
  for (const t of RULES.confidence) tiers[t] = lines.filter(x => x.monthly_cents !== null && x.counted_as === t).reduce((s, x) => s + x.monthly_cents, 0);
  const knownOut = Object.values(outs).filter(v => v !== null).reduce((s, v) => s + v, 0);
  for (const f of outFields) if (outs[f] === null) exclusions.push(`${pretty(f)}: unknown, left out (not counted as zero)`);
  if (outs.taxes_cents === null) warnings.push("Taxes not entered: the margins below are before tax.");
  const out = { income_cents: tiers, outflow_cents: knownOut, margin_confirmed_cents: tiers.confirmed - knownOut,
    margin_with_expected_cents: tiers.confirmed + tiers.expected - knownOut,
    margin_with_hypothetical_cents: tiers.confirmed + tiers.expected + tiers.hypothetical - knownOut,
    lines: lines.map(x => ({ label: x.label, kind: x.kind, monthly_cents: x.monthly_cents, counted_as: x.counted_as })) };
  return envelope("cash_flow", inputs, out, { asOf, warnings, exclusions, dataStatus: exclusions.length ? "partial" : "complete" });
}

// ── 9. transition forecast ──
function transitionForecast(raw, asOf) {
  const before = int(raw, "months_until_separation", 0, LIM.max_months_before_separation, true);
  const savings = cents(raw, "current_savings_cents", true), payBefore = cents(raw, "net_income_before_cents", true);
  const expBefore = cents(raw, "expenses_before_cents", true), civ = cents(raw, "civilian_net_after_cents");
  let expAfter = cents(raw, "expenses_after_cents");
  const retired = cents(raw, "retired_pay_net_after_cents") ?? 0, other = cents(raw, "other_net_after_cents") ?? 0;
  const va = cents(raw, "va_monthly_cents") ?? 0;
  const vaStatus = choice(raw, "va_status", ["none", "confirmed", "estimate"], "none");
  if (va && vaStatus === "none") throw new MoneyInputError("va_status", "is needed when a VA amount is entered");
  const delays = { ...RULES.scenario_defaults.job_delay_months };
  for (const c of CASES) { const v = int(raw, `job_delay_${c}`, 0, 24, false); if (v !== null) delays[c] = v; }
  let vaDelay = int(raw, "va_estimate_delay_months", 0, 24, false);
  vaDelay = vaDelay === null ? RULES.scenario_defaults.va_estimate_delay_months.optimistic : vaDelay;
  const events = raw.one_time || [];
  if (!Array.isArray(events) || events.length > 12) throw new MoneyInputError("one_time", "must list up to 12 one-time amounts");
  const oneTime = events.map((e, i) => {
    if (typeof e !== "object" || e === null || !label60(e.label)) throw new MoneyInputError(`one_time[${i}]`, "needs a label of 1 to 60 characters");
    return { label: e.label, month: int(e, "month", -before, 23, true), cents: cents(e, "cents", true), direction: choice(e, "direction", ["in", "out"]) };
  });
  const inputs = { months_until_separation: before, current_savings_cents: savings, net_income_before_cents: payBefore,
    expenses_before_cents: expBefore, civilian_net_after_cents: civ, expenses_after_cents: expAfter,
    retired_pay_net_after_cents: retired, other_net_after_cents: other, va_monthly_cents: va, va_status: vaStatus,
    job_delays: delays, va_estimate_delay_months: vaDelay, one_time: oneTime };
  const warnings = [], assumptions = [`Job starts after ${delays.optimistic}, ${delays.base} and ${delays.downside} months in the optimistic, base and downside cases (your assumption).`];
  if (civ === null) warnings.push("No civilian income entered, so after separation these cases show how long savings last with none. Unknown pay isn't treated as a salary.");
  if (expAfter === null) { expAfter = expBefore; assumptions.push("Expenses after separation equal expenses now (not entered)."); }
  if (vaStatus === "estimate") warnings.push(`The VA amount is an estimate, so it counts only in the optimistic case, from month ${vaDelay} after separation. Base and downside leave it out.`);
  if (retired) warnings.push("Retired pay is used as entered: enter the net after any VA waiver.");
  const cases = {};
  for (const c of CASES) {
    let bal = savings, low = savings, lowMonth = -before, firstNeg = null, atSep = savings;
    const rows = [];
    for (let m = -before; m < 24; m++) {
      let conf, out, hyp = 0;
      if (m < 0) { conf = payBefore; out = expBefore; }
      else {
        conf = (m >= delays[c] ? (civ ?? 0) : 0) + retired + other;
        if (vaStatus === "confirmed") conf += va;
        else if (vaStatus === "estimate" && c === "optimistic" && m >= vaDelay) hyp = va;
        out = expAfter;
      }
      for (const e of oneTime) if (e.month === m) { if (e.direction === "in") conf += e.cents; else out += e.cents; }
      if (m === 0) atSep = bal;
      const net = conf + hyp - out;
      bal += net;
      rows.push([m, conf, hyp, out, net, bal]);
      if (bal < low) { low = bal; lowMonth = m; }
      if (bal < 0 && firstNeg === null) firstNeg = m;
    }
    cases[c] = { rows, lowest_balance_cents: low, lowest_month: lowMonth, first_negative_month: firstNeg,
      balance_at_separation_cents: atSep, end_balance_cents: bal,
      runway_tenths_at_separation: expAfter === 0 || atSep <= 0 ? null : Math.floor(atSep * 10 / expAfter) };
  }
  return envelope("transition_forecast", inputs, { row_columns: ["month", "confirmed_in_cents", "hypothetical_in_cents", "out_cents", "net_cents", "balance_cents"], cases },
    { asOf, assumptions, warnings, exclusions: ["Taxes are whatever you built into the net amounts", "Investment returns"], dataStatus: civ === null ? "partial" : "complete" });
}

// ── 10. state-to-state comparison ──
function stateComparison(raw, asOf) {
  const origin = cents(raw, "origin_net_disposable_annual_cents", true), dest = cents(raw, "destination_net_disposable_annual_cents", true);
  const years = int(raw, "moving_cost_years", 1, 30, false) || 1;
  const keys = ["verified_education_savings_annual_cents", "approved_tax_savings_annual_cents", "incremental_housing_insurance_annual_cents", "moving_costs_cents"];
  const parts = {};
  for (const k of keys) parts[k] = cents(raw, k);
  const inputs = { origin_net_disposable_annual_cents: origin, destination_net_disposable_annual_cents: dest, moving_cost_years: years, ...parts };
  const exclusions = keys.filter(k => parts[k] === null).map(k => `${pretty(k)}: unknown, left out (not counted as zero)`);
  const p = {};
  for (const k of keys) p[k] = parts[k] ?? 0;
  const move = rdiv(p.moving_costs_cents, years);
  const adv = dest - origin + p.verified_education_savings_annual_cents + p.approved_tax_savings_annual_cents - p.incremental_housing_insurance_annual_cents - move;
  return envelope("state_comparison", inputs, { annual_advantage_cents: adv, moving_cost_per_year_cents: move }, { asOf, exclusions,
    dataStatus: exclusions.length ? "partial" : "complete",
    warnings: ["Only verified education savings and approved tax savings belong here; a benefit you might qualify for is not a saving yet. Property-tax relief isn't cash income."] });
}

export const CALCULATORS = {
  loan_payment: loanPayment, emergency_fund: emergencyFund, debt_to_income: debtToIncome, debt_payoff: debtPayoff,
  savings_forecast: savingsForecast, va_illustration: vaIllustration, regular_retirement: regularRetirement,
  reserve_retirement: reserveRetirement, chapter61_retirement: chapter61Retirement, cash_flow: cashFlow,
  transition_forecast: transitionForecast, state_comparison: stateComparison,
};

export function calculate(calcType, raw, asOf) {
  if (!has(CALCULATORS, calcType)) throw new MoneyInputError("calculation_type", "unknown calculation");
  if (typeof raw !== "object" || raw === null || Array.isArray(raw)) throw new MoneyInputError("body", "must be a JSON object");
  return CALCULATORS[calcType](raw, asOf);
}
