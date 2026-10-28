// VetBuddy web shell — slice 01. No framework, no build step (ADR 0002).
// All DOM is built with el() — never innerHTML with data — so server or
// user text can't inject markup. Case data lives in memory only; the dev
// session token is the only thing kept in sessionStorage.

const API = "/api/v1";
const state = { token: null, me: null, jurisdictions: null, guestBrief: null };
try { state.token = sessionStorage.getItem("vb.devtoken"); } catch { /* storage unavailable: stay signed out */ }

// ── tiny DOM helper ─────────────────────────────────────────────────────────
function el(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else if (k === "class") n.className = v;
    else if (v === true) n.setAttribute(k, "");
    else n.setAttribute(k, v);
  }
  for (const kid of kids.flat()) if (kid !== null && kid !== undefined && kid !== false)
    n.append(kid instanceof Node ? kid : document.createTextNode(String(kid)));
  return n;
}
const main = () => document.getElementById("main");
function render(...nodes) { const m = main(); m.replaceChildren(...nodes.flat().filter(n => n !== null && n !== undefined && n !== false)); m.focus({ preventScroll: true }); window.scrollTo(0, 0); }
function toast(msg) { const t = document.getElementById("toast"); t.textContent = msg; t.classList.add("on"); clearTimeout(toast._t); toast._t = setTimeout(() => t.classList.remove("on"), 2600); }

// ── API ─────────────────────────────────────────────────────────────────────
async function api(method, path, body) {
  const headers = { "content-type": "application/json" };
  if (state.token) headers.authorization = "Bearer " + state.token;
  let res;
  try { res = await fetch(API + path, { method, headers, body: body ? JSON.stringify(body) : undefined }); }
  catch { return { ok: false, status: 0, error: { code: "OFFLINE", message: "VetBuddy can't reach the server right now." } }; }
  const data = await res.json().catch(() => ({}));
  if (res.status === 401 && state.token) signOut(true);
  return res.ok ? { ok: true, status: res.status, data } : { ok: false, status: res.status, error: data.error || { message: "Request failed." } };
}

function setToken(t) {
  state.token = t;
  try { t ? sessionStorage.setItem("vb.devtoken", t) : sessionStorage.removeItem("vb.devtoken"); } catch { /* ignore */ }
}
function signOut(expired) { setToken(null); state.me = null; renderChrome(); if (expired) toast("Your session ended. Sign in again."); location.hash = "#/"; }

// ── labels ──────────────────────────────────────────────────────────────────
const L = {
  persona: { service_member: "Service member (still serving)", veteran: "Veteran", guard_reserve: "National Guard or Reserve",
             spouse_family: "Spouse or family member", caregiver: "Caregiver", survivor: "Survivor" },
  component: { active_duty: "Active duty", national_guard: "National Guard", reserve: "Reserve", retired: "Retired",
               retired_reserve_gray_area: "Retired Reserve (gray area)", separated: "Separated", medically_separated: "Medically separated" },
  authority: { title_10: "Title 10 (federal orders)", title_32: "Title 32 (federal funding, state control)",
               state_active_duty: "State Active Duty", idt_annual_training: "Drill / annual training only",
               not_applicable: "Not applicable", unknown: "I don't know yet" },
  goals: { benefits: "Benefits", claims: "VA disability claim", education: "School or training", career: "Job or career",
           financial: "Money and budget", housing: "Housing", family: "Family", community: "Community" },
  urgency: { immediate: "Right now", "7_days": "This week", "30_days": "This month", "90_days": "Next 90 days",
             long_term: "Later", info_only: "Just exploring" },
  dims: { documents: "Documents", benefits: "Benefits", claims_evidence: "Claims & evidence", coverage: "Coverage",
          career: "Career", education: "Education", financial: "Financial", housing_relocation: "Housing & relocation",
          family: "Family", community: "Community" },
  dimStatus: { ready: "All steps done", in_progress: "In progress", not_started: "Not started", not_assessed: "No steps yet" },
  lanes: { benefits: "Benefits", claims_evidence: "Claims & evidence", career: "Career", education: "Education",
           financial: "Financial", healthcare_coverage: "Coverage", housing_stability: "Housing",
           family_caregiver_survivor: "Family", guard_reserve: "Guard & Reserve", state_local: "State & local",
           recreation_community: "Community", citizenship: "Citizenship", other: "General" },
  status: { todo: "To do", in_progress: "In progress", blocked: "Blocked", done: "Done", cancelled: "Not needed" },
};
const BRANCHES = ["Army", "Navy", "Marine Corps", "Air Force", "Space Force", "Coast Guard"];

// ── chrome ──────────────────────────────────────────────────────────────────
function renderChrome() {
  const route = location.hash.split("/")[1] || "";
  const link = (href, label, key) => el("a", { href, "aria-current": route === key ? "page" : null }, label);
  const nav = document.getElementById("nav");
  nav.replaceChildren(...(state.token
    ? [link("#/brief", "Mission brief", "brief"), link("#/tasks", "All tasks", "tasks"), link("#/benefits", "Benefits", "benefits"), link("#/settings", "Privacy", "settings")]
    : [link("#/", "Start", ""), link("#/benefits", "Benefits", "benefits"), link("#/about", "How it works", "about")]));
  const dev = document.getElementById("devbar");
  dev.hidden = !state.token;
  dev.textContent = "Development sign-in — not a real identity provider. Use made-up details only.";
}

async function openHelp() {
  const dlg = document.getElementById("help");
  const list = document.getElementById("help-list");
  const r = await api("GET", "/crisis-contacts");
  const contacts = r.ok ? r.data.contacts : [{ label: "Veterans Crisis Line", phone: "988", extra: "Press 1" }];
  list.replaceChildren(...contacts.map(c => el("li", {},
    el("div", { class: "disp" }, c.label),
    el("a", { href: "tel:" + c.phone.replace(/[^0-9]/g, "") }, "Call " + c.phone + (c.extra ? ", then " + c.extra : "")),
    c.text ? el("div", {}, "Text: " + c.text) : null,
    c.chat_url ? el("div", {}, el("a", { href: c.chat_url, rel: "noopener", target: "_blank" }, "Chat online")) : null)));
  dlg.showModal();
}

// ── views ───────────────────────────────────────────────────────────────────
function viewStart() {
  render(
    el("h1", { class: "disp" }, "What matters now, and what to do next"),
    el("p", { class: "lede" }, "VetBuddy turns where you are in your transition into a short, honest plan. It doesn't guess about your benefits, and it won't store anything until you say so."),
    el("div", { class: "grid2" },
      el("section", { class: "card" },
        el("h2", { class: "disp" }, "Try it as a guest"),
        el("p", {}, "Answer a few questions and see a Mission Brief. Nothing is saved — close the tab and it's gone."),
        el("div", { class: "chips" }, el("span", { class: "chip muted" }, "Privacy mode A · nothing stored")),
        el("div", { class: "btn-row" }, el("a", { class: "btn primary", href: "#/onboard/guest" }, "Start as a guest"))),
      el("section", { class: "card" },
        el("h2", { class: "disp" }, "Save a private plan"),
        el("p", {}, "Keep your brief and check off tasks over time. Only you can see it, and you can withdraw consent at any time."),
        el("div", { class: "chips" }, el("span", { class: "chip seal" }, "Privacy mode B · private to you")),
        el("div", { class: "btn-row" },
          state.token
            ? el("a", { class: "btn primary", href: "#/brief" }, "Go to my brief")
            : el("button", { class: "btn primary", type: "button", onclick: devSignIn }, "Create a private profile")))),
    el("section", { class: "card" },
      el("h2", { class: "disp" }, "Look up benefits"),
      el("p", {}, "Search sourced federal, state, nonprofit and retail benefits for service members, veterans and families. No account needed, and nothing you type is saved."),
      el("div", { class: "btn-row" }, el("a", { class: "btn", href: "#/benefits" }, "Open the benefits finder"))),
    el("p", { class: "foot" }, "VetBuddy is not a VA-accredited representative and does not file anything for you. Until a named reviewer has checked a benefit's rule against the law, VetBuddy shows it as a lead to read, never as a match."));
}

function viewAbout() {
  render(el("h1", { class: "disp" }, "How it works"),
    el("div", { class: "card stack" },
      el("p", {}, "1. You tell VetBuddy your situation: service, timing, where you live, and what you want help with."),
      el("p", {}, "2. A fixed set of written rules — not AI — works out your transition stage and your first steps. Same answers in, same plan out."),
      el("p", {}, "3. Every step says why it's there and who holds the official answer. VetBuddy never claims you qualify for something."),
      el("p", {}, "4. State information is labelled “not yet verified” until a person has checked it against primary sources.")));
}

async function devSignIn() {
  const r = await api("POST", "/dev/signup");
  if (!r.ok) { toast(r.error.message); return; }
  setToken(r.data.token); renderChrome(); location.hash = "#/onboard/save";
}

async function loadJurisdictions() {
  if (state.jurisdictions) return state.jurisdictions;
  const r = await api("GET", "/jurisdictions");
  state.jurisdictions = r.ok ? r.data.jurisdictions.filter(j => j.kind !== "federal") : [];
  return state.jurisdictions;
}

async function viewOnboard(mode) {
  if (mode === "save" && !state.token) { location.hash = "#/"; return; }
  const js = await loadJurisdictions();
  const errBox = el("div", { class: "errors", role: "alert", hidden: true });
  const radios = (name, opts, checked) => el("div", { class: "choices", role: "radiogroup" },
    Object.entries(opts).map(([v, label]) => el("label", { class: "choice" },
      el("input", { type: "radio", name, value: v, checked: v === checked, required: true }), el("span", {}, label))));
  const jSelect = (name, optional) => el("select", { id: name, name, required: !optional },
    optional ? el("option", { value: "" }, "Not moving / not sure") : el("option", { value: "" }, "Choose…"),
    js.map(j => el("option", { value: j.code }, j.name)));

  const authorityBox = el("div", { hidden: true },
    el("label", { class: "field", for: "legal_authority" }, "Authority printed on your orders"),
    el("p", { class: "hint" }, "What you may qualify for follows the authority on your orders, not the mission. Read it off the citation block — if you don't have them, choose “I don't know yet”."),
    el("select", { id: "legal_authority", name: "legal_authority" }, el("option", { value: "" }, "Choose…"),
      Object.entries(L.authority).map(([v, l]) => el("option", { value: v }, l))));
  const component = el("select", { id: "component", name: "component", required: true,
    onchange: e => { const gr = ["national_guard", "reserve"].includes(e.target.value); authorityBox.hidden = !gr; authorityBox.querySelector("select").required = gr; } },
    el("option", { value: "" }, "Choose…"), Object.entries(L.component).map(([v, l]) => el("option", { value: v }, l)));
  const dateInput = el("input", { type: "date", id: "separation_date", name: "separation_date" });
  const noDate = el("input", { type: "checkbox", id: "no_date", onchange: e => { dateInput.disabled = e.target.checked; if (e.target.checked) dateInput.value = ""; } });

  const form = el("form", { novalidate: true, onsubmit: submit },
    errBox,
    el("fieldset", {}, el("legend", {}, el("span", { class: "step-n" }, "01"), "Who you are"), radios("persona", L.persona, null)),
    el("fieldset", {}, el("legend", {}, el("span", { class: "step-n" }, "02"), "Service"),
      el("p", { class: "hint" }, "If you're a family member, answer for the service member."),
      el("label", { class: "field", for: "branch" }, "Branch"),
      el("select", { id: "branch", name: "branch", required: true }, el("option", { value: "" }, "Choose…"), BRANCHES.map(b => el("option", { value: b }, b))),
      el("label", { class: "field", for: "component" }, "Status"), component, authorityBox),
    el("fieldset", {}, el("legend", {}, el("span", { class: "step-n" }, "03"), "Timing"),
      el("label", { class: "field", for: "separation_date" }, "Separation, retirement or release date (past or future)"),
      dateInput,
      el("label", { class: "check", style: "margin-top:10px" }, noDate, el("span", {}, "I don't know the date yet — don't guess it"))),
    el("fieldset", {}, el("legend", {}, el("span", { class: "step-n" }, "04"), "Where"),
      el("label", { class: "field", for: "current_jurisdiction" }, "Where you live now"), jSelect("current_jurisdiction", false),
      el("label", { class: "field", for: "destination_jurisdiction" }, "Where you're moving (optional)"), jSelect("destination_jurisdiction", true)),
    el("fieldset", {}, el("legend", {}, el("span", { class: "step-n" }, "05"), "What you want help with"),
      el("div", { class: "choices" }, Object.entries(L.goals).map(([v, l]) => el("label", { class: "choice" },
        el("input", { type: "checkbox", name: "goals", value: v }), el("span", {}, l))))),
    el("fieldset", {}, el("legend", {}, el("span", { class: "step-n" }, "06"), "How soon"), radios("urgency", L.urgency, "30_days")),
    mode === "save" ? el("fieldset", {}, el("legend", {}, el("span", { class: "step-n" }, "07"), "Your consent"),
      el("label", { class: "check" }, el("input", { type: "checkbox", name: "consent", required: true }),
        el("span", {}, "Store my profile, service context, mission, cases and tasks so VetBuddy can build my Mission Brief. Not shared with anyone. I can withdraw this at any time in Privacy."))) : null,
    el("div", { class: "btn-row" }, el("button", { class: "btn primary", type: "submit" }, mode === "save" ? "Build and save my brief" : "Show my brief")));

  async function submit(ev) {
    ev.preventDefault();
    const f = new FormData(form);
    const body = {
      persona: f.get("persona"), branch: f.get("branch"), component: f.get("component"),
      legal_authority: f.get("legal_authority") || null,
      separation_date: noDate.checked ? null : (f.get("separation_date") || null),
      current_jurisdiction: f.get("current_jurisdiction"),
      destination_jurisdiction: f.get("destination_jurisdiction") || null,
      goals: f.getAll("goals"), urgency: f.get("urgency") || "30_days",
    };
    const missing = [];
    if (!body.persona) missing.push("who you are");
    if (!body.branch) missing.push("branch");
    if (!body.component) missing.push("status");
    if (!authorityBox.hidden && !body.legal_authority) missing.push("the authority on your orders");
    if (!body.separation_date && !noDate.checked) missing.push("a date, or tick “I don't know the date yet”");
    if (!body.current_jurisdiction) missing.push("where you live now");
    if (mode === "save" && !f.get("consent")) missing.push("your consent to store the plan");
    if (missing.length) return showErrors(["Please add: " + missing.join(", ") + "."]);
    let r;
    if (mode === "save") { body.consent = true; r = await api("POST", "/onboarding", body); }
    else r = await api("POST", "/brief/preview", body);
    if (!r.ok) return showErrors(r.error.fields ? r.error.fields.map(x => x.message) : [r.error.message]);
    if (mode === "save") location.hash = "#/brief/" + r.data.mission_id;
    else { state.guestBrief = r.data; location.hash = "#/brief/guest"; }
  }
  function showErrors(list) { errBox.replaceChildren(el("strong", {}, "Almost there."), el("ul", {}, list.map(x => el("li", {}, x)))); errBox.hidden = false; errBox.focus?.(); errBox.scrollIntoView({ block: "center" }); }

  render(el("h1", { class: "disp" }, mode === "save" ? "Build your private plan" : "Guest brief"),
    el("p", { class: "lede" }, mode === "save"
      ? "Seven short sections. Only what's needed to plan — no Social Security number, no medical details."
      : "Six short sections. Nothing you enter here is saved."), form);
}

async function currentMissionId() {
  const r = await api("GET", "/missions");
  if (!r.ok) return { error: r.error };
  return { id: r.data.missions[0]?.mission_id || null };
}

async function viewBrief(id) {
  let brief;
  if (id === "guest") {
    brief = state.guestBrief;
    if (!brief) { location.hash = "#/onboard/guest"; return; }
  } else {
    if (!state.token) { location.hash = "#/"; return; }
    if (!id) {
      const m = await currentMissionId();
      if (m.error) return renderConsentGate(m.error);
      if (!m.id) { location.hash = "#/onboard/save"; return; }
      id = m.id;
    }
    const r = await api("GET", `/missions/${id}/brief`);
    if (!r.ok) return r.error.code === "CONSENT_REQUIRED" ? renderConsentGate(r.error) : render(el("p", {}, r.error.message));
    brief = r.data;
  }
  const s = brief.situation;
  const guest = !brief.persisted;
  const actionItem = t => el("li", { class: t.status === "done" ? "done" : "" },
    guest ? el("span", { class: "chip muted", "aria-hidden": "true" }, String(t.priority))
          : el("input", { type: "checkbox", class: "tick", checked: t.status === "done", "aria-label": "Mark done: " + t.title,
              onchange: e => setTask(t, e.target.checked ? "done" : "todo", () => viewBrief(brief.mission_id)) }),
    el("div", {}, el("h3", {}, t.title), el("p", { class: "why" }, t.why),
      t.confirm_with ? el("p", { class: "confirm" }, "Official answer: " + t.confirm_with) : null));

  render(
    el("div", { class: "chips", style: "margin-bottom:10px" },
      el("span", { class: "chip " + (guest ? "muted" : "seal") }, guest ? "Guest · not saved" : "Saved · private to you"),
      el("span", { class: "chip muted" }, "Facts: declared by you")),
    el("h1", { class: "disp" }, "Mission brief"),
    el("p", { class: "lede" }, `As of ${brief.as_of}. Built by fixed rules from what you told us — no AI, no guessing.`),
    el("div", { class: "grid2" },
      el("section", { class: "card", "aria-labelledby": "sit-h" },
        el("h2", { id: "sit-h", class: "disp" }, "Your situation"),
        el("div", { class: "stage disp" }, s.stage_label),
        s.days_to_separation !== null ? el("p", { class: "small" }, s.days_to_separation >= 0 ? `${s.days_to_separation} days until separation` : `${-s.days_to_separation} days since separation`) : null,
        brief.stage_changed_since_created ? el("p", { class: "small" }, "Your stage has moved on since this plan was made.") : null,
        el("dl", { class: "kv" },
          el("dt", {}, "You are"), el("dd", {}, L.persona[s.persona]),
          el("dt", {}, "Service"), el("dd", {}, `${s.branch} · ${L.component[s.component]}`),
          s.legal_authority ? [el("dt", {}, "Orders authority"), el("dd", {}, L.authority[s.legal_authority])] : null,
          el("dt", {}, "Focus areas"), el("dd", {}, brief.lanes.map(l => L.lanes[l] || l).join(", ")),
          el("dt", {}, "How soon"), el("dd", {}, L.urgency[brief.urgency]))),
      el("section", { class: "card stack", "aria-labelledby": "src-h" },
        el("h2", { id: "src-h", class: "disp" }, "What VetBuddy can't tell you yet"),
        brief.notices.map(n => el("div", { class: "banner" }, el("strong", {}, n.code === "BENEFIT_SCREENING_NOT_AVAILABLE" ? "Benefit matches are off" : n.code === "STAGE_UNKNOWN" ? "Stage unknown" : "Orders authority unknown"), el("p", {}, n.message))),
        brief.jurisdictions.map(j => el("div", { class: "banner" }, el("strong", {}, `${j.name}: not yet verified`), el("p", {}, j.disclaimer))))),
    el("section", { class: "card", style: "margin-top:16px", "aria-labelledby": "next-h" },
      el("h2", { id: "next-h", class: "disp" }, "Your first five actions"),
      brief.first_five_actions.length ? el("ol", { class: "actions" }, brief.first_five_actions.map(actionItem))
        : el("p", {}, "Every open action is done. Nice work."),
      !guest ? el("div", { class: "btn-row" }, el("a", { class: "btn", href: "#/tasks" }, `See all ${brief.tasks.length} tasks`)) : null),
    el("section", { class: "card", style: "margin-top:16px", "aria-labelledby": "ready-h" },
      el("h2", { id: "ready-h", class: "disp" }, "Readiness by area"),
      el("p", { class: "hint" }, "Progress on your steps in each area — not a score, and not a prediction."),
      el("div", { class: "dims" }, brief.readiness.map(d => el("div", { class: "dim", "data-s": d.status },
        el("div", { class: "n" }, L.dims[d.dimension]),
        el("div", { class: "s" }, L.dimStatus[d.status] + (d.total ? ` · ${d.done}/${d.total}` : "")))))),
    guest ? el("section", { class: "card", style: "margin-top:16px" },
      el("h2", { class: "disp" }, "Want to keep this?"),
      el("p", {}, "Create a private profile to save the plan and check steps off over time."),
      el("div", { class: "btn-row" }, el("button", { class: "btn primary", type: "button", onclick: devSignIn }, "Create a private profile"))) : null,
    el("div", { class: "foot" },
      brief.limitations.map(x => el("div", {}, "· " + x)),
      el("div", { style: "margin-top:8px" }, `${brief.policy_version} · input ${brief.input_hash.slice(0, 12)}`)));
}

async function setTask(t, status, after) {
  const r = await api("PATCH", `/tasks/${t.task_id}`, { status, version: t.version });
  if (!r.ok) toast(r.error.message); else toast(status === "done" ? "Marked done." : "Updated.");
  after();
}

async function viewTasks() {
  if (!state.token) { location.hash = "#/"; return; }
  const m = await currentMissionId();
  if (m.error) return renderConsentGate(m.error);
  if (!m.id) { location.hash = "#/onboard/save"; return; }
  const r = await api("GET", `/missions/${m.id}/brief`);
  if (!r.ok) return renderConsentGate(r.error);
  const byLane = {};
  for (const t of r.data.tasks) (byLane[t.lane] ||= []).push(t);
  render(el("h1", { class: "disp" }, "All tasks"),
    el("p", { class: "lede" }, "Grouped by area. Change a status and it saves straight away."),
    Object.entries(byLane).map(([lane, ts]) => el("section", { class: "card lane", "aria-label": L.lanes[lane] || lane },
      el("h2", { class: "disp" }, L.lanes[lane] || lane),
      el("table", { class: "tasks" },
        el("thead", {}, el("tr", {}, el("th", { scope: "col" }, "Task"), el("th", { scope: "col" }, "Why"), el("th", { scope: "col" }, "Status"))),
        el("tbody", {}, ts.map(t => el("tr", {},
          el("td", {}, t.title), el("td", {}, t.why),
          el("td", {}, el("select", { "aria-label": "Status for " + t.title, onchange: e => setTask(t, e.target.value, viewTasks) },
            Object.entries(L.status).map(([v, l]) => el("option", { value: v, selected: v === t.status }, l)))))))))));
}

function renderConsentGate(error) {
  render(el("h1", { class: "disp" }, "Consent needed"),
    el("div", { class: "card" }, el("p", {}, error.message || "VetBuddy needs your consent to show stored mission data."),
      el("div", { class: "btn-row" },
        el("button", { class: "btn primary", type: "button", onclick: async () => {
          const r = await api("POST", "/consents", { purpose: "personal_mission_planning" });
          if (r.ok) { toast("Consent restored."); location.hash = "#/brief"; route(); } else toast(r.error.message);
        } }, "Give consent again"),
        el("a", { class: "btn", href: "#/settings" }, "Privacy settings"))));
}

async function viewSettings() {
  if (!state.token) { location.hash = "#/"; return; }
  const [me, cs] = await Promise.all([api("GET", "/me"), api("GET", "/consents")]);
  if (!me.ok) return;
  render(el("h1", { class: "disp" }, "Privacy"),
    el("div", { class: "grid2" },
      el("section", { class: "card" }, el("h2", { class: "disp" }, "Privacy mode"),
        el("p", {}, el("strong", {}, "Mode " + me.data.privacy_mode + " — personal and private.")),
        el("p", { class: "hint" }, "Your plan is visible only to you. Managed-case mode (sharing with an organization) stays switched off until its security review is complete.")),
      el("section", { class: "card" }, el("h2", { class: "disp" }, "Consents"),
        (cs.ok ? cs.data.consents : []).map(c => el("div", { style: "border-top:1px solid var(--rule);padding:10px 0" },
          el("div", { class: "chips" }, el("span", { class: "chip " + (c.status === "active" ? "seal" : "muted") }, c.status)),
          el("p", {}, c.description),
          el("p", { class: "small" }, "Granted " + c.granted_at.slice(0, 10) + (c.revoked_at ? " · withdrawn " + c.revoked_at.slice(0, 10) : "")),
          c.status === "active" ? el("button", { class: "btn", type: "button", onclick: async () => {
            const r = await api("POST", `/consents/${c.consent_id}/revoke`);
            toast(r.ok ? "Consent withdrawn. Your plan is locked until you give it again." : r.error.message); viewSettings();
          } }, "Withdraw consent") : null)))),
    el("section", { class: "card", style: "margin-top:16px", "aria-labelledby": "acct-h" },
      el("h2", { id: "acct-h", class: "disp" }, "Your account and data"),
      el("p", {}, "Download everything VetBuddy stores for your account, or delete the account and all of its data."),
      el("div", { class: "btn-row" },
        el("button", { class: "btn", type: "button", onclick: downloadExport }, "Download my data"),
        el("a", { class: "btn", href: "#/delete" }, "Delete account"))),
    el("div", { class: "btn-row" }, el("button", { class: "btn", type: "button", onclick: () => signOut(false) }, "Sign out")));
}

async function downloadExport() {
  const r = await api("GET", "/me/export");
  if (!r.ok) { toast(r.error.message); return; }
  const url = URL.createObjectURL(new Blob([JSON.stringify(r.data, null, 2)], { type: "application/json" }));
  const a = el("a", { href: url, download: "vetbuddy-export.json" });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  toast("Your data is downloading as vetbuddy-export.json.");
}

// v6 §3: one clear confirmation step, export offered but never required,
// no obstruction. Deletion is immediate and cannot be undone.
function viewDelete() {
  if (!state.token) { location.hash = "#/"; return; }
  const PHRASE = "DELETE MY ACCOUNT";
  const errBox = el("div", { class: "errors", role: "alert", hidden: true, tabindex: "-1" });
  const input = el("input", { type: "text", id: "confirm", autocomplete: "off", spellcheck: "false" });
  const form = el("form", { novalidate: true, onsubmit: async ev => {
      ev.preventDefault();
      if (input.value !== PHRASE) { errBox.replaceChildren(`Type ${PHRASE} exactly to confirm.`); errBox.hidden = false; errBox.focus(); return; }
      const r = await api("POST", "/me/delete", { confirm: input.value });
      if (!r.ok) { errBox.replaceChildren(r.error.message); errBox.hidden = false; errBox.focus(); return; }
      setToken(null); state.me = null; renderChrome();
      viewDeleted(r.data);
    } },
    errBox,
    el("label", { class: "field", for: "confirm" }, `Type ${PHRASE} to confirm`), input,
    el("div", { class: "btn-row" },
      el("button", { class: "btn primary", type: "submit" }, "Delete my account and data"),
      el("a", { class: "btn", href: "#/settings" }, "Cancel")));
  render(el("h1", { class: "disp" }, "Delete account"),
    el("div", { class: "card stack" },
      el("p", {}, "This permanently deletes your account and everything saved with it: your profile, service details, mission, cases, tasks, consents, and the account's history and event records."),
      el("p", {}, "It takes effect immediately and cannot be undone. You'll be signed out on every device that uses this account."),
      el("p", {}, "Want a copy first? ", el("button", { class: "btn", type: "button", onclick: downloadExport }, "Download my data"), " (optional)."),
      el("p", { class: "small" }, "This development build has no backups, outside service providers or legal holds, so nothing is kept. When those exist, this page will list exactly what is kept, why, and for how long."),
      form));
}

function viewDeleted(receipt) {
  render(el("h1", { class: "disp" }, "Account deleted"),
    el("div", { class: "card stack" },
      el("p", {}, "Your account and its data have been deleted, and you've been signed out."),
      el("dl", { class: "kv" },
        el("dt", {}, "Status"), el("dd", {}, receipt.state === "COMPLETE" ? "Complete" : receipt.state),
        el("dt", {}, "Records removed"), el("dd", {}, String(Object.values(receipt.rows_purged).reduce((a, b) => a + b, 0))),
        el("dt", {}, "Receipt number"), el("dd", { class: "mono" }, receipt.receipt_id)),
      el("p", { class: "small" }, "Keep the receipt number if you want to check this deletion later. It contains nothing about you."),
      receipt.exceptions.length ? el("p", { class: "small" }, receipt.exceptions.join(" ")) : null,
      el("div", { class: "btn-row" }, el("a", { class: "btn", href: "#/" }, "Back to start"))));
}

// ── Benefits (Benefit Vault, /api/v1/vault) ─────────────────────────────────
// Every result is a record from the vault registry with its official link.
// Outcomes come from the vault's deterministic matcher in the v6 words; this
// page only labels them. Guests (and anyone without an account and consent)
// are Mode A: only V1 questions are asked and nothing is stored.
const OUTCOME = {
  PRELIMINARY_MATCH: ["Fits the rules as written (preliminary)", "seal"],
  NEEDS_EVIDENCE: ["Fits only with answers you weren't sure about", "ochre"],
  NEEDS_INFORMATION: ["Needs an answer before it can be compared", "muted"],
  HUMAN_REVIEW_REQUIRED: ["May apply: not yet checked by a reviewer, read the official page", "ochre"],
  CONFLICTING_AUTHORITY: ["Sources disagree", "ochre"],
  SOURCE_STALE: ["Source may be out of date", "ochre"],
  DOES_NOT_MEET_ENCODED_RULES: ["Doesn't fit the rules as written", "muted"],
};
const RECORD_STATUS = { VERIFIED: "Checked by a named reviewer", SOURCE_CHECKED: "Source checked, not reviewed",
  UNVERIFIED: "Not yet reviewed", CONTESTED: "Contested", SUPERSEDED: "Superseded", ILLUSTRATIVE: "Illustrative only",
  HEURISTIC: "Rule of thumb" };
const vaultState = { catalog: null, account: false };

async function vaultCatalog() {
  if (vaultState.catalog) return vaultState.catalog;
  const r = await api("GET", "/vault/catalog");
  if (r.ok) vaultState.catalog = r.data;
  return vaultState.catalog;
}

function placeName(code) {
  if (code === "US") return "Federal";
  const j = vaultState.catalog && vaultState.catalog.jurisdictions.find(x => x.code === code);
  return j ? j.name : code;
}
const sentence = v => { const t = v.replace(/_/g, " "); return t.charAt(0).toUpperCase() + t.slice(1); };

function recordCard(item, extra) {
  const status = RECORD_STATUS[item.record_status] || item.record_status;
  return el("article", { class: "card stack vault-item" },
    el("h3", { class: "disp" }, item.title),
    el("div", { class: "chips" },
      el("span", { class: "chip muted" }, item.jurisdiction_name || placeName(item.jurisdiction)),
      el("span", { class: "chip muted" }, item.category_label || (vaultState.catalog && vaultState.catalog.categories[item.category]) || item.category),
      el("span", { class: "chip " + (item.record_status === "VERIFIED" ? "seal" : "ochre") }, status)),
    item.value ? el("p", {}, item.value) : null,
    item.who_it_is_for ? el("p", { class: "small" }, "Who it is for, as the source puts it: " + item.who_it_is_for) : null,
    (item.caveats || []).map(c => el("p", { class: "small" }, c.text)),
    el("div", { class: "btn-row" },
      el("a", { class: "btn", href: item.official_url, target: "_blank", rel: "noopener noreferrer" }, "Official page"),
      extra || null));
}

function saveButton(item) {
  if (!vaultState.account) return null;
  const box = el("span", {});
  const btn = el("button", { class: "btn", type: "button", onclick: async () => {
    const first = await api("POST", "/vault/saved", { benefit_id: item.benefit_id });
    if (first.status !== 409) { toast(first.ok ? "Saved to your list." : first.error.message); return; }
    box.replaceChildren(el("span", { class: "small" }, first.error.consent_text + " "),
      el("button", { class: "btn primary", type: "button", onclick: async () => {
        const r = await api("POST", "/vault/saved", { benefit_id: item.benefit_id, confirm: true });
        toast(r.ok ? "Saved to your list." : r.error.message);
        box.replaceChildren(el("span", { class: "small" }, r.ok ? "Saved." : ""));
      } }, "Confirm save"));
  } }, "Save to my list");
  box.append(btn);
  return box;
}

async function viewBenefits() {
  const cat = await vaultCatalog();
  if (!cat) { render(el("h1", { class: "disp" }, "Benefits"), el("p", {}, "The benefits finder can't be reached right now.")); return; }
  const saved = state.token ? await api("GET", "/vault/saved") : { ok: false };
  vaultState.account = saved.ok;
  const juris = cat.jurisdictions.filter(j => j.coverage === "COVERED");
  const jOpts = (blankLabel) => [el("option", { value: "" }, blankLabel),
    ...juris.map(j => el("option", { value: j.code }, j.name))];
  const results = el("div", { class: "stack", "aria-live": "polite" });
  const matchOut = el("div", { class: "stack", "aria-live": "polite" });

  const search = el("form", { class: "card stack", onsubmit: async e => {
      e.preventDefault();
      const f = new FormData(search);
      const q = new URLSearchParams({ q: f.get("q") || "", limit: "25" });
      if (f.get("jurisdiction")) q.set("jurisdiction", f.get("jurisdiction"));
      if (f.get("category")) q.set("category", f.get("category"));
      const r = await api("GET", "/vault/benefits?" + q.toString());
      if (!r.ok) { results.replaceChildren(el("p", {}, r.error.message)); return; }
      if (r.data.crisis_floor) { openHelp(); return; }
      results.replaceChildren(
        el("p", { class: "small" }, `${r.data.total} record${r.data.total === 1 ? "" : "s"} found${r.data.total > r.data.items.length ? `; showing the first ${r.data.items.length}` : ""}.`),
        ...r.data.items.map(i => recordCard(i, saveButton(i))));
    } },
    el("h2", { class: "disp" }, "Search"),
    el("label", { class: "f", for: "vq" }, "What are you looking for?"),
    el("input", { id: "vq", name: "q", type: "search", placeholder: "e.g. hunting license, property tax, scholarship" }),
    el("div", { class: "grid2" },
      el("div", {}, el("label", { class: "f", for: "vj" }, "Where"), el("select", { id: "vj", name: "jurisdiction" }, jOpts("Anywhere"))),
      el("div", {}, el("label", { class: "f", for: "vc" }, "Kind of benefit"),
        el("select", { id: "vc", name: "category" }, el("option", { value: "" }, "Any"),
          Object.entries(cat.categories).map(([k, label]) => el("option", { value: k }, label))))),
    el("div", { class: "btn-row" }, el("button", { class: "btn primary", type: "submit" }, "Search")));

  const sel = (name, label, values, labels) => el("div", {},
    el("label", { class: "f", for: "vm-" + name }, label),
    el("select", { id: "vm-" + name, name }, el("option", { value: "" }, "Skip"),
      values.map(v => el("option", { value: v }, (labels && labels[v]) || sentence(v)))));
  const facts = cat.facts;
  const check = el("form", { class: "card stack", onsubmit: async e => {
      e.preventDefault();
      const f = new FormData(check);
      const given = {};
      for (const [k, v] of f.entries()) {
        if (v === "") continue;
        if (k === "wartime_service") given[k] = v === "yes";
        else if (k === "va_rating") given[k] = Number(v);
        else given[k] = v;
      }
      const r = await api("POST", "/vault/match", { facts: given });
      if (!r.ok) { matchOut.replaceChildren(el("p", {}, r.error.message)); return; }
      if (r.data.crisis_floor) { openHelp(); return; }
      const env = r.data;
      const hidden = env.counts.DOES_NOT_MEET_ENCODED_RULES || 0;
      matchOut.replaceChildren(
        el("div", { class: "card stack" },
          el("p", { class: "small" }, env.notice),
          el("p", {}, `Compared against ${env.evaluated} records in ${env.scope.length} place${env.scope.length === 1 ? "" : "s"}. ` +
            (env.publish_policy === "verified_only" ? "Only records a named reviewer has checked can show as fitting; everything else is a lead to read." : "Development data: unreviewed records can show as fitting.")),
          hidden ? el("p", { class: "small" }, `${hidden} record${hidden === 1 ? "" : "s"} didn't fit the rules as written and aren't listed. The rules are simplified, so read the official page if one looks relevant.`) : null,
          env.questions.length ? el("div", {}, el("h3", { class: "disp" }, "Questions that would change these results"),
            el("ul", {}, env.questions.slice(0, 6).map(q => el("li", {}, q.question + (q.can_answer_here ? "" : " (answered only in a private account)"))))) : null),
        ...env.items.slice(0, 40).map(i => recordCard({ ...i, caveats: i.caveats },
          el("span", { class: "chip " + OUTCOME[i.outcome][1] }, OUTCOME[i.outcome][0]))));
    } },
    el("h2", { class: "disp" }, "What may apply to me"),
    el("p", { class: "small" }, vaultState.account
      ? "Private account: you can also answer rating and discharge questions. Nothing here is stored unless you save a benefit."
      : "As a guest you're asked only basic questions, and nothing is stored."),
    el("div", { class: "grid2" },
      el("div", {}, el("label", { class: "f", for: "vm-residence_state" }, facts.residence_state.question),
        el("select", { id: "vm-residence_state", name: "residence_state" }, jOpts("Skip"))),
      sel("service_status", facts.service_status.question, facts.service_status.values),
      sel("component", facts.component.question, facts.component.values, { active: "Active", guard: "National Guard", reserve: "Reserve" }),
      sel("relationship", facts.relationship.question, facts.relationship.values),
      sel("wartime_service", facts.wartime_service.question, ["yes", "no"]),
      vaultState.account ? sel("discharge", facts.discharge.question, facts.discharge.values) : null,
      vaultState.account ? sel("va_rating", facts.va_rating.question, ["0", "10", "20", "30", "40", "50", "60", "70", "80", "90", "100"]) : null),
    el("div", { class: "btn-row" }, el("button", { class: "btn primary", type: "submit" }, "Compare")));

  const savedList = vaultState.account ? el("section", { class: "card stack" },
    el("h2", { class: "disp" }, "My saved benefits"),
    saved.data.saved.length
      ? el("ul", {}, saved.data.saved.map(sv => el("li", {}, sv.title || sv.benefit_id, " ",
          el("span", { class: "chip muted" }, sv.status.replace(/_/g, " ").toLowerCase()),
          sv.changed_since_saved ? el("span", { class: "chip ochre" }, "changed since you saved it") : null)))
      : el("p", { class: "small" }, "Nothing saved yet.")) : null;

  render(
    el("h1", { class: "disp" }, "Benefits"),
    el("p", { class: "lede" }, `${cat.counts ? cat.counts.benefits.toLocaleString() + " sourced records" : "Sourced records"} for service members, Guard and Reserve, veterans and families: federal, all 50 states, DC and four territories, plus nonprofit and retail offers. Each one links to its official page.`),
    el("div", { class: "banner" }, el("strong", {}, "Read this first"), cat.notice),
    el("p", { class: "small" }, `Registry ${cat.version}, read ${cat.as_of}. No record has been checked by a named reviewer yet. American Samoa has no source yet.`),
    savedList, search, results, check, matchOut);
}

// ── router ──────────────────────────────────────────────────────────────────
async function route() {
  renderChrome();
  const [, a, b] = location.hash.split("/");
  if (a === "onboard") return viewOnboard(b === "save" ? "save" : "guest");
  if (a === "brief") return viewBrief(b || null);
  if (a === "tasks") return viewTasks();
  if (a === "settings") return viewSettings();
  if (a === "delete") return viewDelete();
  if (a === "about") return viewAbout();
  if (a === "benefits") return viewBenefits();
  return viewStart();
}
window.addEventListener("hashchange", route);
document.getElementById("help-btn").addEventListener("click", openHelp);
route();
