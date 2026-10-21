// VetBuddy web app. Guest mode (Privacy Mode A) runs entirely here: no storage,
// no network calls carrying answers. The saved-plan view (Privacy Mode B) is
// present only when the build sets VITE_API_URL, and talks to the API with an
// in-memory development token.
import { KDATA, combineRatings, readiness, route, validate } from "./kernel.js";
import { planView, planEnabled } from "./plan.js";

// ── UI ──────────────────────────────────────────────────────────────────────
// No storage, no network: all state lives in this object and dies with the tab.
const S = { brief: null, done: new Set(), ratings: [70, 50], finder: "AL" };
const TODAY = (() => { const d = new Date(); return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10); })();

function el(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else if (k === "class") n.className = v;
    else if (v === true) n.setAttribute(k, "");
    else n.setAttribute(k, v);
  }
  for (const c of kids.flat(Infinity)) if (c !== null && c !== undefined && c !== false) n.append(c instanceof Node ? c : document.createTextNode(String(c)));
  return n;
}
const L = {
  persona: { service_member: "Service member (still serving)", veteran: "Veteran", guard_reserve: "National Guard or Reserve", spouse_family: "Spouse or family member", caregiver: "Caregiver", survivor: "Survivor" },
  component: { active_duty: "Active duty", national_guard: "National Guard", reserve: "Reserve", retired: "Retired", retired_reserve_gray_area: "Retired Reserve (gray area)", separated: "Separated", medically_separated: "Medically separated" },
  authority: { title_10: "Title 10 (federal orders)", title_32: "Title 32 (federal funding, state control)", state_active_duty: "State Active Duty", idt_annual_training: "Drill / annual training only", not_applicable: "Not applicable", unknown: "I don't know yet" },
  goals: { benefits: "Benefits", claims: "VA disability claim", education: "School or training", career: "Job or career", financial: "Money and budget", housing: "Housing", family: "Family", community: "Community" },
  urgency: { immediate: "Right now", "7_days": "This week", "30_days": "This month", "90_days": "Next 90 days", long_term: "Later", info_only: "Just exploring" },
  dims: { documents: "Documents", benefits: "Benefits", claims_evidence: "Claims & evidence", coverage: "Coverage", career: "Career", education: "Education", financial: "Financial", housing_relocation: "Housing & relocation", family: "Family", community: "Community" },
  dimStatus: { ready: "All steps done", in_progress: "In progress", not_started: "Not started", not_assessed: "No steps yet" },
  lanes: { benefits: "Benefits", claims_evidence: "Claims & evidence", career: "Career", education: "Education", financial: "Financial", healthcare_coverage: "Coverage", housing_stability: "Housing", family_caregiver_survivor: "Family", guard_reserve: "Guard & Reserve", state_local: "State & local", recreation_community: "Community", citizenship: "Citizenship", other: "General" },
};
const VIEWS = [["home", "Start"], ["brief", "Mission brief"], ["rating", "Rating calculator"], ["claims", "Claims guide"], ["finder", "Benefits finder"],
  ...(planEnabled ? [["plan", "Saved plan"]] : []), ["trust", "How it's built"]];

function show(view) {
  if (!VIEWS.some(v => v[0] === view)) view = "home";
  document.getElementById("tabs").replaceChildren(...VIEWS.map(([k, label]) => el("a", { href: "#" + k, "aria-current": k === view ? "page" : null }, label)));
  const m = document.getElementById("main");
  m.replaceChildren({ home: vHome, brief: vBrief, rating: vRating, claims: vClaims, finder: vFinder, trust: vTrust,
    plan: () => planView({ el, L, S, rerender: () => show("plan") }) }[view]());
  m.focus({ preventScroll: true });
}
function go(view) { if (location.hash === "#" + view) show(view); else location.hash = view; }

// ── Start ──
function vHome() {
  const tile = (view, title, body, chip) => el("a", { class: "card", href: "#" + view, style: "text-decoration:none;color:inherit;display:block" },
    el("h2", {}, title), el("p", {}, body), chip ? el("span", { class: "chip c-muted" }, chip) : null);
  return el("section", { class: "view" },
    el("h1", {}, "What matters now, and what to do next"),
    el("p", { class: "lede" }, "VetBuddy turns where you are in your transition into a short, honest plan. Fixed rules do the work, not AI. It never guesses about your benefits, and in this guest version nothing you type leaves this page."),
    el("div", { class: "grid3" },
      tile("brief", "Mission brief", "Six questions. Get your transition stage, focus areas and first five actions.", "about 2 minutes"),
      tile("rating", "Rating calculator", "Combine disability percentages the way 38 CFR 4.25 does, with every step shown.", "educational"),
      tile("claims", "Claims guide", "What each VA claim status means, the windows that matter, and where to get free accredited help.", "VA sources"),
      tile("finder", "Benefits finder", "Pick your state or territory. See exactly what VetBuddy has verified there, which today is nothing yet.", "57 jurisdictions"),
      tile("trust", "How it's built", "The rules every answer follows, what is real, and what is still a mock.", null)),
    el("p", { class: "foot" }, KDATA.LANGUAGE.standard_disclaimer));
}

// ── Mission brief ──
function vBrief() {
  if (S.brief) return briefView(S.brief);
  const errBox = el("div", { class: "errors", role: "alert", hidden: true, tabindex: "-1" });
  const radios = (name, opts, checked) => el("div", { class: "choices", role: "radiogroup", "aria-label": name },
    Object.entries(opts).map(([v, l]) => el("label", { class: "choice" }, el("input", { type: "radio", name, value: v, checked: v === checked }), el("span", {}, l))));
  const js = KDATA.JURISDICTIONS.filter(j => j.kind !== "federal").sort((a, b) => a.name.localeCompare(b.name));
  const jSel = (id, opt) => el("select", { id, name: id }, el("option", { value: "" }, opt ? "Not moving / not sure" : "Choose…"), js.map(j => el("option", { value: j.code }, j.name)));
  const auth = el("div", { hidden: true },
    el("label", { class: "f", for: "legal_authority" }, "Authority printed on your orders"),
    el("p", { class: "hint" }, "What you may qualify for follows the authority on your orders, not the mission. Read it off the citation block. No orders handy? Choose “I don't know yet”."),
    el("select", { id: "legal_authority", name: "legal_authority" }, el("option", { value: "" }, "Choose…"), Object.entries(L.authority).map(([v, l]) => el("option", { value: v }, l))));
  const comp = el("select", { id: "component", name: "component", onchange: e => { auth.hidden = !["national_guard", "reserve"].includes(e.target.value); } },
    el("option", { value: "" }, "Choose…"), Object.entries(L.component).map(([v, l]) => el("option", { value: v }, l)));
  const date = el("input", { type: "date", id: "separation_date", name: "separation_date" });
  const noDate = el("input", { type: "checkbox", id: "no_date", onchange: e => { date.disabled = e.target.checked; if (e.target.checked) date.value = ""; } });
  const form = el("form", { novalidate: true, onsubmit: submit }, errBox,
    el("fieldset", {}, el("legend", {}, "Who you are"), radios("persona", L.persona, null)),
    el("fieldset", {}, el("legend", {}, "Service"),
      el("p", { class: "hint" }, "Family members: answer for the service member."),
      el("label", { class: "f", for: "branch" }, "Branch"),
      el("select", { id: "branch", name: "branch" }, el("option", { value: "" }, "Choose…"), KDATA.BRANCHES.map(b => el("option", { value: b }, b))),
      el("label", { class: "f", for: "component" }, "Status"), comp, auth),
    el("fieldset", {}, el("legend", {}, "Timing"),
      el("label", { class: "f", for: "separation_date" }, "Separation, retirement or release date (past or future)"), date,
      el("label", { class: "check" }, noDate, el("span", {}, "I don't know the date yet. Don't guess it."))),
    el("fieldset", {}, el("legend", {}, "Where"),
      el("label", { class: "f", for: "current_jurisdiction" }, "Where you live now"), jSel("current_jurisdiction", false),
      el("label", { class: "f", for: "destination_jurisdiction" }, "Where you're moving (optional)"), jSel("destination_jurisdiction", true)),
    el("fieldset", {}, el("legend", {}, "What you want help with"),
      el("div", { class: "choices" }, Object.entries(L.goals).map(([v, l]) => el("label", { class: "choice" }, el("input", { type: "checkbox", name: "goals", value: v }), el("span", {}, l))))),
    el("fieldset", {}, el("legend", {}, "How soon"), radios("urgency", L.urgency, "30_days")),
    el("div", { class: "row" }, el("button", { class: "btn primary", type: "submit" }, "Show my brief"),
      el("button", { class: "btn", type: "button", onclick: sample }, "Fill in an example")));

  function sample() {
    form.querySelector('input[name=persona][value=guard_reserve]').checked = true;
    form.branch.value = "Army"; comp.value = "national_guard"; auth.hidden = false; form.legal_authority.value = "unknown";
    const d = new Date(TODAY); d.setUTCDate(d.getUTCDate() + 250); date.value = d.toISOString().slice(0, 10);
    form.current_jurisdiction.value = "AL"; form.destination_jurisdiction.value = "TX";
    form.querySelectorAll("input[name=goals]").forEach(c => { c.checked = ["education", "career", "benefits"].includes(c.value); });
  }
  async function submit(ev) {
    ev.preventDefault();
    const f = new FormData(form);
    const inp = { persona: f.get("persona"), branch: f.get("branch"), component: f.get("component"),
      legal_authority: f.get("legal_authority") || null, separation_date: noDate.checked ? null : (f.get("separation_date") || null),
      current_jurisdiction: f.get("current_jurisdiction") || null, destination_jurisdiction: f.get("destination_jurisdiction") || null,
      goals: f.getAll("goals"), urgency: f.get("urgency") || "30_days" };
    if (auth.hidden) inp.legal_authority = null;
    const miss = [];
    if (!inp.persona) miss.push("who you are"); if (!inp.branch) miss.push("branch"); if (!inp.component) miss.push("status");
    if (!auth.hidden && !inp.legal_authority) miss.push("the authority on your orders");
    if (!inp.separation_date && !noDate.checked) miss.push("a date, or tick “I don't know the date yet”");
    if (!inp.current_jurisdiction) miss.push("where you live now");
    if (miss.length) return fail("Please add: " + miss.join(", ") + ".");
    try { validate(inp, new Set(KDATA.JURISDICTIONS.map(j => j.code))); } catch (e) { return fail(e.message); }
    S.brief = { inp, out: await route(inp, TODAY) }; S.done = new Set(); show("brief");
  }
  function fail(msg) { errBox.replaceChildren(el("strong", {}, "Almost there. "), msg); errBox.hidden = false; errBox.focus(); }
  return el("section", { class: "view" }, el("h1", {}, "Mission brief"),
    el("p", { class: "lede" }, "Six short sections. Only what's needed to plan: no Social Security number, no medical details."), form);
}

function briefView({ inp, out }) {
  const tasks = out.tasks.map(t => ({ ...t, status: S.done.has(t.template_id) ? "done" : "todo" }));
  const open = tasks.filter(t => t.status !== "done");
  const jur = [inp.current_jurisdiction, inp.destination_jurisdiction].filter((c, i, a) => c && a.indexOf(c) === i)
    .map(c => KDATA.JURISDICTIONS.find(j => j.code === c));
  const s = out;
  const item = t => el("li", { class: t.status === "done" ? "done" : "" },
    el("input", { type: "checkbox", class: "tick", checked: t.status === "done", "aria-label": "Mark done: " + t.title,
      onchange: e => { e.target.checked ? S.done.add(t.template_id) : S.done.delete(t.template_id); show("brief"); } }),
    el("div", {}, el("h3", {}, t.title), el("p", { class: "why" }, t.why), t.confirm_with ? el("p", { class: "confirm" }, "Official answer: " + t.confirm_with) : null));
  const noticeTitle = { BENEFIT_SCREENING_NOT_AVAILABLE: "Benefit matches are off", STAGE_UNKNOWN: "Stage unknown", AUTHORITY_UNKNOWN: "Orders authority unknown" };
  return el("section", { class: "view" },
    el("div", { class: "row" }, el("span", { class: "chip c-muted" }, "Guest · not saved"), el("span", { class: "chip c-muted" }, "Facts: declared by you")),
    el("h1", {}, "Mission brief"),
    el("p", { class: "lede" }, `As of ${TODAY}. Built by fixed rules from what you told VetBuddy. Same answers in, same plan out.`),
    el("div", { class: "grid2" },
      el("div", { class: "card" }, el("h2", {}, "Your situation"),
        el("div", { class: "stage" }, s.stage_label),
        s.days_to_separation !== null ? el("p", { class: "small" }, s.days_to_separation >= 0 ? `${s.days_to_separation} days until separation` : `${-s.days_to_separation} days since separation`) : null,
        el("dl", { class: "kv" },
          el("dt", {}, "You are"), el("dd", {}, L.persona[inp.persona]),
          el("dt", {}, "Service"), el("dd", {}, `${inp.branch} · ${L.component[inp.component]}`),
          inp.legal_authority ? [el("dt", {}, "Orders authority"), el("dd", {}, L.authority[inp.legal_authority])] : null,
          el("dt", {}, "Focus areas"), el("dd", {}, s.lanes.map(l => L.lanes[l] || l).join(", ")),
          el("dt", {}, "How soon"), el("dd", {}, L.urgency[inp.urgency]))),
      el("div", { class: "card" }, el("h2", {}, "What VetBuddy can't tell you yet"),
        s.notices.map(n => el("div", { class: "banner" }, el("strong", {}, noticeTitle[n.code]), n.message)),
        jur.map(j => el("div", { class: "banner" }, el("strong", {}, `${j.name}: not yet verified`), KDATA.UNVERIFIED_DISCLAIMER)))),
    el("div", { class: "card" }, el("h2", {}, "Your first five actions"),
      open.length ? el("ol", { class: "actions" }, open.slice(0, 5).map(item)) : el("p", {}, "Every action is checked off."),
      tasks.length > 5 ? el("details", {}, el("summary", {}, `All ${tasks.length} actions`), el("ol", { class: "actions" }, tasks.map(item))) : null),
    el("div", { class: "card" }, el("h2", {}, "Readiness by area"),
      el("p", { class: "hint" }, "Progress on your steps in each area. Not a score, and not a prediction."),
      el("div", { class: "dims" }, readiness(tasks.map(t => ({ readiness_dimension: t.dimension, status: t.status }))).map(d =>
        el("div", { class: "dim", "data-s": d.status }, el("div", { class: "n" }, L.dims[d.dimension]), el("div", { class: "s" }, L.dimStatus[d.status] + (d.total ? ` · ${d.done}/${d.total}` : "")))))),
    el("div", { class: "row" }, el("button", { class: "btn", type: "button", onclick: () => { S.brief = null; show("brief"); } }, "Start over"),
      planEnabled ? el("a", { class: "btn primary", href: "#plan" }, "Save this plan to my account") : null),
    el("p", { class: "foot" }, "Everything here is based on facts you declared; none has been checked against your records. Check-offs vanish when you close the tab. ",
      el("br"), `${s.policy_version} · input ${s.input_hash.slice(0, 12)}`));
}

// ── Rating calculator ──
function vRating() {
  let res = null, err = null;
  try { res = S.ratings.length ? combineRatings(S.ratings) : null; } catch (e) { err = e.message; }
  const set = r => { S.ratings = r; show("rating"); };
  return el("section", { class: "view" },
    el("h1", {}, "Combined rating calculator"),
    el("p", { class: "lede" }, "VA doesn't add disability percentages. Each rating applies to the part of you that is still “efficient” after the ones before it, and the total is rounded to the nearest 10 only once, at the end."),
    el("div", { class: "grid2" },
      el("div", { class: "card" }, el("h2", {}, "Your ratings"),
        el("div", { class: "ratings", "aria-live": "polite" }, S.ratings.length ? S.ratings.map((r, i) => el("span", { class: "rpill" }, r + "%",
          el("button", { type: "button", "aria-label": `Remove ${r}%`, onclick: () => set(S.ratings.filter((_, j) => j !== i)) }, "×"))) : el("span", { class: "small" }, "No ratings yet.")),
        el("p", { class: "hint", id: "addh" }, "Add a rating:"),
        el("div", { class: "addr", role: "group", "aria-labelledby": "addh" }, [10, 20, 30, 40, 50, 60, 70, 80, 90, 100].map(v =>
          el("button", { type: "button", onclick: () => set([...S.ratings, v]) }, v + "%"))),
        el("div", { class: "row" }, el("button", { class: "btn", type: "button", onclick: () => set([]) }, "Clear"),
          el("button", { class: "btn", type: "button", onclick: () => set([60, 40, 20]) }, "Example: 60, 40, 20"))),
      el("div", { class: "card", "aria-live": "polite" }, el("h2", {}, "Result"),
        res ? [
          el("div", { class: "result-num" }, res.combined_rating + "%"),
          el("p", {}, `Combined value ${res.combined_value}, rounded once to the nearest 10 (values ending in 5 go up).`),
          el("div", { class: "tw" }, el("table", { class: "steps" },
            el("thead", {}, el("tr", {}, el("th", {}, "Step"), el("th", {}, "Rating"), el("th", {}, "Applies to"), el("th", {}, "Combined"))),
            el("tbody", {}, res.ratings.map((r, i) => el("tr", {}, el("td", {}, i + 1), el("td", {}, r + "%"),
              el("td", {}, i === 0 ? "100" : String(100 - res.steps[i - 1])), el("td", {}, res.steps[i]))))))
        ] : el("p", { class: "small" }, err || "Add at least one rating."))),
    el("div", { class: "banner" }, el("strong", {}, "Educational only"),
      "This follows the combining and rounding rules in 38 CFR 4.25. It does not apply the bilateral factor (38 CFR 4.26) for conditions affecting both arms or both legs, and it can't tell you what VA will rate. VA decides your rating."),
    el("p", { class: "foot" }, "Source: 38 CFR 4.25 (eCFR, checked 2026-10-20). Regulation examples reproduced: 50+30 → 65 → 70; 40+20 → 52 → 50; 60+40+20 → 76 → 81 → 80."));
}

// ── Claims guide ──
function vClaims() {
  const steps = [
    ["Claim received", "VA has the claim in its system."],
    ["Initial review", "VA checks the claim for basic information it needs."],
    ["Evidence gathering", "VA makes sure it has all the evidence and information it needs."],
    ["Evidence review", "VA reviews all the evidence for the claim."],
    ["Rating", "VA decides the claim and determines the disability rating."],
    ["Preparing decision letter", "VA prepares the decision letter."],
    ["Final review", "A senior reviewer does a final review of the claim and the letter."],
    ["Claim decided", "The decision letter is available in VA's claim status tool."],
  ];
  // Windows, the legal lane and referral wording come from the reference
  // corpus and config/governance_language.yaml (generated into KDATA).
  const ANCHOR = { intent_to_file: "After an Intent to File", separation: "Around separation", decision_letter: "After a decision letter", retirement: "At retirement", career: "Over a career" };
  const claimAnchors = ["intent_to_file", "separation", "decision_letter"];
  const windows = KDATA.TIMELINE.windows.filter(w => claimAnchors.includes(w.anchor) && w.kind !== "limit");
  const srcName = id => (KDATA.SOURCES[id] || {}).title || id;
  const ALLOWED = { yes: ["Yes, free", "yes"], share_card: ["Only with your approval", "yes"], no: ["No: free accredited help instead", "no"] };
  return el("section", { class: "view" },
    el("h1", {}, "Claims guide"),
    el("p", { class: "lede" }, "What VA's claim statuses mean, the time windows worth knowing, and what VetBuddy will and won't do."),
    el("div", { class: "card" }, el("h2", {}, "The 8 disability-claim statuses on VA.gov"),
      el("ol", { class: "track" }, steps.map(([t, d]) => el("li", {}, el("div", {}, el("h3", {}, t), el("p", { class: "why" }, d))))),
      el("p", { class: "small" }, `Source: ${srcName("src.va.claim_status")} (checked 2026-10-20). Other claim types use a shorter 5-status track.`)),
    el("div", { class: "card" }, el("h2", {}, "Windows worth knowing"),
      el("div", { class: "tw" }, el("table", { class: "lane" }, el("thead", {}, el("tr", {}, el("th", {}, "When"), el("th", {}, "What to know"), el("th", {}, "Check against"))),
        el("tbody", {}, windows.map(w => el("tr", {},
          el("td", {}, el("strong", {}, ANCHOR[w.anchor] || w.anchor), el("div", { class: "small mono" }, w.offset)),
          el("td", {}, w.item, el("div", { class: "small" }, "Source: " + w.sources.map(srcName).join("; "))),
          el("td", {}, w.verify_against, el("div", {}, el("span", { class: "chip c-ochre" }, KDATA.TIMELINE.default_status.toLowerCase())))))))),
      el("div", { class: "banner" }, el("strong", {}, "Confirm your own dates with VA or an accredited representative"),
        "No window here has been checked against its authority by a named reviewer yet, so treat each one as a lead. Exceptions exist, and VetBuddy doesn't compute your personal deadlines in this guest version.")),
    el("div", { class: "card" }, el("h2", {}, "What VetBuddy will and won't do"),
      el("div", { class: "tw" }, el("table", { class: "lane" }, el("thead", {}, el("tr", {}, el("th", {}, "Activity"), el("th", {}, "VetBuddy"))),
        el("tbody", {}, KDATA.LEGAL_LANE.map(r => el("tr", {}, el("td", {}, r.activity), el("td", { class: ALLOWED[r.allowed][1] }, ALLOWED[r.allowed][0])))))),
      el("p", {}, KDATA.LANGUAGE.vso_referral_block),
      el("div", { class: "row" }, el("a", { class: "btn primary", href: KDATA.LANGUAGE.vso_search_url, target: "_blank", rel: "noopener" }, "Find an accredited representative on VA.gov")),
      el("p", { class: "small" }, KDATA.LANGUAGE.vso_search_url)));
}

// ── Benefits finder ──
function vFinder() {
  const js = [...KDATA.JURISDICTIONS].sort((a, b) => (a.kind === "federal" ? -1 : b.kind === "federal" ? 1 : a.name.localeCompare(b.name)));
  const j = KDATA.JURISDICTIONS.find(x => x.code === S.finder);
  const verified = KDATA.JURISDICTIONS.filter(x => x.verification_status === "verified").length;
  return el("section", { class: "view" },
    el("h1", {}, "Benefits finder"),
    el("p", { class: "lede" }, "One engine for the federal government, all 50 states, DC and 5 territories. What changes from place to place is whether a person has verified the rules against the law yet."),
    el("div", { class: "card" },
      el("label", { class: "f", for: "fj" }, "Jurisdiction"),
      el("select", { id: "fj", onchange: e => { S.finder = e.target.value; show("finder"); } }, js.map(x => el("option", { value: x.code, selected: x.code === S.finder }, x.name)))),
    el("div", { class: "card", "aria-live": "polite" },
      el("div", { class: "row", style: "justify-content:space-between" }, el("h2", {}, j.name), el("span", { class: "verdict" }, "Verification required")),
      el("p", {}, "No benefit rule for this jurisdiction has been checked against primary law by a named reviewer yet, so VetBuddy shows no matches here. Showing a guess would be worse than showing nothing."),
      el("div", { class: "banner" }, el("strong", {}, "Until verification is done"), KDATA.UNVERIFIED_DISCLAIMER),
      el("p", { class: "small" }, `Verified jurisdictions today: ${verified} of ${KDATA.JURISDICTIONS.length}. Alabama is first in line: its rules are drafted and waiting on a human reviewer.`)));
}

// ── How it's built ──
function vTrust() {
  // Every rule and status below is generated from data/reference/governance.json;
  // this page restates nothing by hand.
  const LABEL = { IMPLEMENTED_VERIFIED: ["Built and tested", "yes"], IMPLEMENTED_UNTESTED: ["Built, not yet tested", "no"],
    PARTIAL: ["Partly built", "no"], MOCK: ["Stand-in only", "no"], NOT_PRESENT: ["Not built yet", "no"],
    BLOCKED_SOURCE: ["Waiting on source material", "no"], DEFERRED: ["Deferred", "no"] };
  const counts = {};
  for (const r of KDATA.AGENT_RULES) counts[r.repo_status] = (counts[r.repo_status] || 0) + 1;
  return el("section", { class: "view" },
    el("h1", {}, "How it's built"),
    el("p", { class: "lede" }, KDATA.GOVERNING_SENTENCE),
    el("div", { class: "card" }, el("h2", {}, "Four non-negotiables"),
      el("div", { class: "grid2" }, KDATA.NON_NEGOTIABLES.map(n => el("div", {}, el("h3", {}, n.name), el("p", { class: "why" }, n.text))))),
    el("div", { class: "card" }, el("h2", {}, "The 22 agent rules, and what exists today"),
      el("p", { class: "hint" }, `${counts.IMPLEMENTED_VERIFIED || 0} built and tested · ${counts.PARTIAL || 0} partly built · ${counts.NOT_PRESENT || 0} not built yet. No AI agent runs in VetBuddy today, so rules about agents are written down before the agents exist.`),
      el("div", { class: "tw" }, el("table", { class: "lane" }, el("thead", {}, el("tr", {}, el("th", {}, "Rule"), el("th", {}, "Status"))),
        el("tbody", {}, KDATA.AGENT_RULES.map(r => el("tr", {},
          el("td", {}, el("span", { class: "mono small" }, r.id + " "), r.rule),
          el("td", { class: (LABEL[r.repo_status] || ["", "no"])[1] }, (LABEL[r.repo_status] || [r.repo_status])[0]))))))),
    el("div", { class: "card" }, el("h2", {}, "Your privacy on this page"),
      el("p", {}, "Guest mode stores nothing: no account, no cookies, no browser storage, no analytics. Your answers exist only in this tab's memory and disappear when you close it."),
      el("p", {}, `Benefit rules verified so far: ${KDATA.JURISDICTIONS.filter(j => j.verification_status === "verified").length} of ${KDATA.JURISDICTIONS.length} jurisdictions. Sign-in, the AI assistant and any VA data connection are not built yet.`)),
    el("p", { class: "foot" }, `Router ${KDATA.ROUTER_POLICY_VERSION} · rules engine has no network access · not affiliated with or endorsed by VA or DoD`));
}

// ── crisis (no network, from the single crisis-floor config) ──
document.getElementById("crisis").replaceChildren(...KDATA.CRISIS_CONTACTS.map(c => el("li", {},
  el("div", { class: "disp" }, c.label),
  el("div", { class: "num" }, c.phone + (c.extra ? " · " + c.extra : "")),
  c.text ? el("div", {}, "Text: ", el("strong", {}, c.text)) : null,
  c.chat_url ? el("div", {}, el("a", { href: c.chat_url, target: "_blank", rel: "noopener" }, "Chat online")) : null)));
document.getElementById("help-btn").addEventListener("click", () => document.getElementById("help").showModal());
window.addEventListener("hashchange", () => show(location.hash.slice(1)));
show(location.hash.slice(1) || "home");
