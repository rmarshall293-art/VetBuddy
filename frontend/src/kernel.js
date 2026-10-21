// VetBuddy browser kernel — logic half. Data (task library, labels, enums)
// comes from kernel_data.js, which scripts/build_web.py GENERATES from the
// Python source so wording can't drift. Pure functions: no I/O, no clock
// reads (callers pass `today`), no storage. tests/parity.test.mjs checks these
// against the Python kernel on shared golden fixtures.

import { KDATA } from "./kernel_data.js";

export { KDATA };
const DAY = 86400000;
function dayNumber(iso) { const [y, m, d] = iso.split("-").map(Number); return Date.UTC(y, m - 1, d) / DAY; }

export function computeStage(separationDate, today) {
  if (!separationDate) return ["unknown", null];
  const d = dayNumber(separationDate) - dayNumber(today);
  if (d > 730) return ["in_service", d];
  if (d > 365) return ["t_24_12m", d];
  if (d > 180) return ["t_12_6m", d];
  if (d > 90) return ["t_180_90d", d];
  if (d > 30) return ["t_90_30d", d];
  if (d >= 0) return ["t_30d_sep", d];
  const a = -d;
  if (a <= 30) return ["day_0_30", d];
  if (a <= 90) return ["day_31_90", d];
  if (a <= 365) return ["month_3_12", d];
  if (a <= 730) return ["year_1_2", d];
  if (a <= 1095) return ["year_2_3", d];
  if (a <= 1825) return ["year_3_5", d];
  return ["ongoing", d];
}

export function computeTrack(inp) {
  if (["spouse_family", "caregiver", "survivor"].includes(inp.persona)) return "spouse_family";
  if (inp.component === "medically_separated") return "medical_separation";
  if (["national_guard", "reserve", "retired_reserve_gray_area"].includes(inp.component)) return "guard_reserve";
  if (inp.component === "retired") return "retirement";
  if (inp.destination_jurisdiction && inp.destination_jurisdiction !== inp.current_jurisdiction)
    return inp.component === "active_duty" ? "pcs" : "re_entry";
  return inp.component === "active_duty" ? "ets_eas" : "re_entry";
}

export class RouterInputError extends Error { constructor(field, msg) { super(`${field}: ${msg}`); this.field = field; } }

export function validate(inp, known) {
  const need = (c, f, m) => { if (!c) throw new RouterInputError(f, m); };
  need(KDATA.PERSONAS.includes(inp.persona), "persona", "choose who you are");
  need(KDATA.BRANCHES.includes(inp.branch), "branch", "choose a branch");
  need(KDATA.COMPONENTS.includes(inp.component), "component", "choose a status");
  need(inp.legal_authority == null || KDATA.AUTHORITIES.includes(inp.legal_authority), "legal_authority", "unknown value");
  need(!(["national_guard", "reserve"].includes(inp.component) && inp.legal_authority == null), "legal_authority",
       "is required for National Guard and Reserve (choose 'unknown' if you do not have your orders)");
  need(known.has(inp.current_jurisdiction), "current_jurisdiction", "choose where you live");
  need(inp.destination_jurisdiction == null || known.has(inp.destination_jurisdiction), "destination_jurisdiction", "unknown jurisdiction");
  need(inp.goals.every(g => KDATA.GOALS.includes(g)), "goals", "unknown goal");
  need(KDATA.URGENCIES.includes(inp.urgency), "urgency", "unknown urgency");
}

function canonical(inp) {
  return { branch: inp.branch, component: inp.component, current_jurisdiction: inp.current_jurisdiction,
    destination_jurisdiction: inp.destination_jurisdiction ?? null, goals: [...new Set(inp.goals)].sort(),
    legal_authority: inp.legal_authority ?? null, persona: inp.persona,
    separation_date: inp.separation_date ?? null, urgency: inp.urgency };
}

// Same bytes as Python json.dumps(obj, sort_keys=True) for this ASCII-only shape.
function pyJson(v) {
  if (v === null) return "null";
  if (Array.isArray(v)) return "[" + v.map(pyJson).join(", ") + "]";
  if (typeof v === "object") return "{" + Object.keys(v).sort().map(k => JSON.stringify(k) + ": " + pyJson(v[k])).join(", ") + "}";
  return JSON.stringify(v);
}

export async function digest(inp) {
  const bytes = new TextEncoder().encode(pyJson(canonical(inp)));
  const h = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(h)].map(b => b.toString(16).padStart(2, "0")).join("");
}

export async function route(inp, today) {
  const [stage, days] = computeStage(inp.separation_date, today);
  const track = computeTrack(inp);
  const relocating = !!(inp.destination_jurisdiction && inp.destination_jurisdiction !== inp.current_jurisdiction);
  const T = KDATA.TEMPLATES;
  const chosen = ["DOC-01"];
  if (stage === "unknown" && ["service_member", "guard_reserve", "veteran"].includes(inp.persona)) chosen.push("FACT-DATE");
  if (["national_guard", "reserve"].includes(inp.component)) {
    if (inp.legal_authority === "unknown") chosen.push("GR-AUTH");
    chosen.push("GR-RECORD");
  }
  if (["active_duty", "national_guard", "reserve"].includes(inp.component) && T["TAP-01"].stages.includes(stage)) chosen.push("TAP-01");
  if (inp.component === "medically_separated") chosen.push("MED-01");
  if (T["COV-01"].stages.includes(stage)) chosen.push("COV-01");
  for (const g of [...new Set(inp.goals)].sort()) chosen.push(...KDATA.GOAL_TEMPLATES[g]);
  if (relocating) chosen.push("REL-01", "HOU-01");

  const seen = new Set(); const tasks = [];
  for (const id of chosen) {
    if (seen.has(id)) continue; seen.add(id);
    const t = T[id];
    if (t.stages.length && !t.stages.includes(stage)) continue;
    tasks.push({ template_id: id, lane: t.lane, dimension: t.dimension, title: t.title, why: t.why,
                 priority: t.priority, confirm_with: t.confirm_with });
  }
  tasks.sort((a, b) => a.priority - b.priority || (a.template_id < b.template_id ? -1 : a.template_id > b.template_id ? 1 : 0));

  const lanes = [];
  for (const lane of [...[...new Set(inp.goals)].sort().map(g => KDATA.GOAL_LANES[g]), ...tasks.map(t => t.lane)])
    if (lane !== "other" && !lanes.includes(lane)) lanes.push(lane);
  if (["national_guard", "reserve", "retired_reserve_gray_area"].includes(inp.component) && !lanes.includes("guard_reserve")) lanes.push("guard_reserve");
  if (relocating && !lanes.includes("state_local")) lanes.push("state_local");
  if (!lanes.length) lanes.push("benefits");

  const notices = [{ code: "BENEFIT_SCREENING_NOT_AVAILABLE", message: KDATA.NOTICE_TEXT.BENEFIT_SCREENING_NOT_AVAILABLE }];
  if (stage === "unknown") notices.push({ code: "STAGE_UNKNOWN", message: KDATA.NOTICE_TEXT.STAGE_UNKNOWN });
  if (inp.legal_authority === "unknown") notices.push({ code: "AUTHORITY_UNKNOWN", message: KDATA.NOTICE_TEXT.AUTHORITY_UNKNOWN });

  return { policy_version: KDATA.ROUTER_POLICY_VERSION, input_hash: await digest(inp), stage,
           stage_label: KDATA.STAGE_LABELS[stage], days_to_separation: days, track, lanes, tasks, notices };
}

export function readiness(rows) {
  return KDATA.DIMENSIONS.map(dim => {
    const ts = rows.filter(t => t.readiness_dimension === dim && t.status !== "cancelled");
    const done = ts.filter(t => t.status === "done").length;
    const status = !ts.length ? "not_assessed" : done === ts.length ? "ready"
      : (done || ts.some(t => t.status === "in_progress")) ? "in_progress" : "not_started";
    return { dimension: dim, status, done, total: ts.length };
  });
}

// 38 CFR 4.25 + 4.26 — integer arithmetic only, half-up per Table I step, one
// final conversion to the nearest 10 with 5s up. Bilateral ratings (paired
// extremities) are combined first, 10% of that value is added (rounded
// half-up), and the result is treated as one disability. Mirrors
// backend/app/kernel/ratings.py.
function checkRatings(rs) {
  for (const r of rs) if (!Number.isInteger(r) || r < 0 || r > 100 || r % 10 !== 0)
    throw new RangeError("each rating must be a whole multiple of 10 from 0 to 100");
}
function combineValues(values) {
  const ordered = [...values].sort((a, b) => b - a);
  let combined = ordered[0]; const steps = [combined];
  for (const v of ordered.slice(1)) { combined += Math.floor((2 * (100 - combined) * v + 100) / 200); steps.push(combined); }
  return [ordered, steps];
}
export function combineRatings(ratings, bilateral = []) {
  if (!ratings.length && !bilateral.length) throw new RangeError("at least one rating is required");
  checkRatings(ratings); checkRatings(bilateral);
  if (bilateral.length === 1) throw new RangeError("the bilateral factor needs ratings on both sides (at least two)");
  const out = { citation: "38 CFR 4.25", bilateral_factor_applied: bilateral.length > 0 };
  const values = [...ratings];
  if (bilateral.length) {
    const [bOrdered, bSteps] = combineValues(bilateral);
    const bCombined = bSteps[bSteps.length - 1];
    const value = Math.floor((10 * bCombined + bCombined + 5) / 10);
    out.bilateral = { ratings: bOrdered, steps: bSteps, combined_value: bCombined, factor_tenths: bCombined,
                      value_with_factor: value, citation: "38 CFR 4.26" };
    values.push(value);
  }
  const [ordered, steps] = combineValues(values);
  const combined = steps[steps.length - 1];
  return { ...out, ratings: ordered, steps, combined_value: combined,
           combined_rating: Math.min(Math.floor((combined + 5) / 10) * 10, 100) };
}
