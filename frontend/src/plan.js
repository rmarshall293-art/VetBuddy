// Saved plan (Privacy Mode B) — exists only when the build sets VITE_API_URL.
// Sign-in is the development stand-in (MOCK, gap G17). The token lives in this
// module's memory only: never localStorage, sessionStorage or a cookie, so a
// closed tab is a signed-out tab. Nothing is saved without explicit consent.

import { KDATA } from "./kernel.js";

const API = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");
export const planEnabled = Boolean(API);

const P = { token: null, me: null, missions: [], open: null, error: null, busy: false };
const GUEST_STRIP = "Guest mode · runs entirely in your browser · nothing you enter is stored or sent anywhere";
const SIGNED_STRIP = "Signed in (development) · only plans you choose to save are stored, in your private account";

async function api(method, path, body) {
  const res = await fetch(API + "/api/v1" + path, {
    method, headers: { "content-type": "application/json", ...(P.token ? { authorization: "Bearer " + P.token } : {}) },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const e = data.error || {};
    throw new Error(`${e.message || "Request failed."} (${e.code || res.status}${e.trace_id ? ", trace " + e.trace_id.slice(0, 8) : ""})`);
  }
  return data;
}

function setStrip() {
  const s = document.querySelector(".strip");
  if (s) s.textContent = P.token ? SIGNED_STRIP : GUEST_STRIP;
}

const hasConsent = () => (P.me?.consents || []).some(c => c.purpose === "plan_storage");

export function planView({ el, L, S, rerender }) {
  const run = fn => async () => {
    P.busy = true; P.error = null; rerender();
    try { await fn(); } catch (e) { P.error = e.message; }
    P.busy = false; setStrip(); rerender();
  };
  const refresh = async () => {
    P.me = await api("GET", "/users/me");
    P.missions = hasConsent() ? (await api("GET", "/missions")).missions : [];
  };

  const head = [el("h1", {}, "Saved plan"),
    el("p", { class: "lede" }, "Keep your Mission Brief and check off steps across visits. Only what the brief needs is saved: no Social Security number, no medical details."),
    P.error ? el("div", { class: "errors", role: "alert" }, el("strong", {}, "That didn't work. "), P.error) : null];

  if (!P.token) {
    const subj = el("input", { type: "text", id: "subj", autocomplete: "off", value: "synthetic-demo-1" });
    return el("section", { class: "view" }, ...head,
      el("div", { class: "card" }, el("h2", {}, "Sign in"),
        el("div", { class: "banner" }, el("strong", {}, "Development sign-in (mock)"),
          "Real sign-in (ID.me or Microsoft) is not connected yet. Use a made-up name below; never a real one."),
        el("label", { class: "f", for: "subj" }, "Test identity"), subj,
        el("div", { class: "row" }, el("button", { class: "btn primary", type: "button", disabled: P.busy, onclick: run(async () => {
          P.token = (await api("POST", "/dev/token", { subject: subj.value.trim() })).access_token;
          await refresh();
        }) }, "Sign in (development)"))));
  }

  const signOut = el("button", { class: "btn", type: "button", onclick: () => { Object.assign(P, { token: null, me: null, missions: [], open: null }); setStrip(); rerender(); } }, "Sign out");

  if (!hasConsent()) {
    return el("section", { class: "view" }, ...head,
      el("div", { class: "card" }, el("h2", {}, "Your consent comes first"),
        el("p", {}, "VetBuddy saves a plan only with your permission. You can withdraw it at any time; withdrawing hides your saved plans immediately, and you can delete them at the same moment."),
        el("p", { class: "small" }, "VetBuddy never sells your data, never uses it for advertising or AI training, and never shares it with a claims company, lender or recruiter. Those uses are refused by the database itself, not just by policy."),
        el("div", { class: "row" },
          el("button", { class: "btn primary", type: "button", disabled: P.busy, onclick: run(async () => { await api("POST", "/consents", { purpose: "plan_storage" }); await refresh(); }) },
            "I agree: save my plans privately"), signOut)));
  }

  const saveCard = el("div", { class: "card" }, el("h2", {}, "Save a brief"),
    S.brief
      ? [el("p", {}, `Your current brief: ${S.brief.out.stage_label}.`),
         el("button", { class: "btn primary", type: "button", disabled: P.busy, onclick: run(async () => {
           P.open = await api("POST", "/missions", S.brief.inp); await refresh();
         }) }, "Save my current mission brief")]
      : el("p", {}, "Build a brief on the Mission brief tab first, then come back to save it."));

  const list = el("div", { class: "card" }, el("h2", {}, "Saved plans"),
    P.missions.length
      ? el("ul", { class: "plist" }, P.missions.map(m => el("li", {},
          el("span", {}, `${m.as_of} · ${KDATA.STAGE_LABELS[m.stage] || m.stage}`),
          el("button", { class: "btn", type: "button", onclick: run(async () => { P.open = await api("GET", `/missions/${m.id}`); }) }, "Open"))))
      : el("p", { class: "small" }, "No saved plans yet."));

  const openCard = P.open ? el("div", { class: "card" }, el("h2", {}, P.open.stage_label),
    el("p", { class: "small" }, `Saved ${P.open.as_of} · facts declared by you · ${P.open.policy_version}`),
    el("ol", { class: "actions" }, P.open.tasks.map(t => el("li", { class: t.status === "done" ? "done" : "" },
      el("input", { type: "checkbox", class: "tick", checked: t.status === "done", disabled: P.busy, "aria-label": "Mark done: " + t.title,
        onchange: run(async () => {
          await api("PATCH", `/tasks/${t.id}`, { status: t.status === "done" ? "todo" : "done", expected_version: t.version });
          P.open = await api("GET", `/missions/${P.open.mission_id}`);
        }) }),
      el("div", {}, el("h3", {}, t.title), el("p", { class: "why" }, t.why))))),
    el("div", { class: "dims" }, P.open.readiness.map(d => el("div", { class: "dim", "data-s": d.status },
      el("div", { class: "n" }, L.dims[d.dimension]), el("div", { class: "s" }, L.dimStatus[d.status] + (d.total ? ` · ${d.done}/${d.total}` : ""))))),
    el("div", { class: "row" }, el("button", { class: "btn", type: "button", onclick: run(async () => {
      await api("DELETE", `/missions/${P.open.mission_id}`); P.open = null; await refresh();
    }) }, "Delete this plan")),
    el("p", { class: "foot" }, P.open.disclosure)) : null;

  return el("section", { class: "view" }, ...head, saveCard, openCard, list,
    el("div", { class: "card" }, el("h2", {}, "Your data"),
      el("div", { class: "row" },
        el("button", { class: "btn", type: "button", onclick: run(async () => { await api("DELETE", "/consents/plan_storage"); P.open = null; await refresh(); }) }, "Withdraw consent"),
        el("button", { class: "btn", type: "button", onclick: run(async () => { await api("DELETE", "/consents/plan_storage?delete_data=true"); P.open = null; await refresh(); }) }, "Withdraw and delete my plans"),
        signOut)));
}
