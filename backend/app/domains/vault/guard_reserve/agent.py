"""The Guard & Reserve role (plane 5), run over the Benefits Intelligence agent.

Pipeline for a match, in the vault's own order:

    CrisisGate -> MSTNarrativeGuard (parent)  ->  Guard & Reserve answers (V1, validated)
    -> vault facts (mode ceiling) -> derived facts (an answer the person gave always wins)
    -> pulls through the parent agent and its broker, under the person's grants
    -> the vault matcher -> Guard & Reserve lens (sections, role caveats, rule-lead checks)
    -> ClaimsBoundaryGuard -> (no model call) -> OutputGuard (envelope)

The role holds a manifest (``guard_reserve_agent``: may not pull, decide or
expose), so "no manifest, no access" holds for it as for every vault agent.
It never calls the broker: the parent's ``_pull`` does, and the pull ledger
names the parent as the requester, as it must.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Mapping, Optional

from ..agent import BenefitVaultAgent, RequestError, Session
from ..envelope import facts_canonical
from ..facts import TOKEN_FACTS
from ..guards import OutputBlocked
from ..rules import tokens
from . import ROLE_ID, ROLE_VERSION
from .policy import GuardReservePolicy, default_policy
from .profile import ProfileError, classify, derive, lead_checks, parse
from .recovered import RecoveredLeads


class GuardReserveAgent:
    agent_id = ROLE_ID

    def __init__(self, parent: BenefitVaultAgent, policy: Optional[GuardReservePolicy] = None,
                 recovered: Optional[RecoveredLeads] = None):
        self.parent = parent
        self.policy = policy or default_policy()
        self.recovered = recovered or RecoveredLeads(self.policy)
        self.policy.check_against(parent.registry)
        manifest = parent.manifests.get(ROLE_ID)
        if manifest is None or manifest.may_pull_from_agents or manifest.exposes:
            raise PermissionError(f"{ROLE_ID} has no manifest that allows it to run")
        self.manifest = manifest

    # ── selection ──────────────────────────────────────────────────────────
    def is_guard_reserve(self, benefit) -> bool:
        p = self.policy
        return bool(set(benefit.groups) & p.select_groups or benefit.category in p.select_categories
                    or {t.name for t in tokens(benefit.node)} & p.select_tokens
                    or any(lead.startswith(p.lead_prefix) for lead in benefit.lead_ids))

    def selection_counts(self) -> dict:
        selected = [b for b in self.parent.registry.benefits.values() if self.is_guard_reserve(b)]
        by_jur: Dict[str, int] = {}
        for b in selected:
            key = "US" if b.jurisdiction == "US" else "states_and_territories"
            by_jur[key] = by_jur.get(key, 0) + 1
        return {"records": len(selected), "federal": by_jur.get("US", 0),
                "state_and_territory": by_jur.get("states_and_territories", 0),
                "of_registry": len(self.parent.registry.benefits)}

    def _annotate(self, item: dict, derived_keys, status_caveats, checks_by_lead) -> dict:
        benefit = self.parent.registry.benefits[item["benefit_id"]]
        read = set()
        for tok in tokens(benefit.node):
            read |= TOKEN_FACTS[tok.name]
        role_caveats = [c for c in status_caveats if self.policy.caveat_targets[c] in read & derived_keys]
        leads = [checks_by_lead[i] for i in item["lead_ids"] if i in checks_by_lead]
        return {**item, "guard_reserve": {
            "section": "guard_reserve" if self.is_guard_reserve(benefit) else "also_found",
            "uses_derived_facts": sorted(read & derived_keys),
            "role_caveats": [{"id": c, "text": self.policy.caveats[c]} for c in role_caveats],
            "rule_lead_checks": [{"lead_id": c["lead_id"], "outcome": c["outcome"]} for c in leads],
        }}

    # ── match ──────────────────────────────────────────────────────────────
    def match(self, request: Mapping, session: Session, now: datetime) -> dict:
        parent = self.parent
        screened = parent._screen(request.get("note"), session)
        if screened:
            return screened
        try:
            profile = parse(request.get("guard_reserve"), self.policy)
        except ProfileError as exc:
            raise RequestError(str(exc)) from None
        facts = parent._facts(request)
        options = parent._options(request, session, now)
        facts, dropped = facts.limited_to(session.mode)
        derivation = derive(profile, facts, self.policy)
        facts = derivation.facts
        pulls = parent._pull(facts, options, session, now) if request.get("pull", True) else []
        include_other = request.get("include_other", True)
        if not isinstance(include_other, bool):
            raise RequestError("include_other is true or false")

        result = parent.matcher.match(facts, options)
        problems = parent.claims.check(result.items)
        policy_name = result.policy
        checks = lead_checks(profile, facts, self.policy, parent.registry, policy_name)
        outcome_checks = [c for c in checks if c["kind"] == "rule_lead_check"]
        problems += parent.claims.check(outcome_checks)
        if problems:
            raise OutputBlocked(problems)
        checks_by_lead = {c["lead_id"]: c for c in outcome_checks}
        derived_keys = frozenset(d["fact_key"] for d in derivation.derived)
        items = [self._annotate(i, derived_keys, derivation.caveat_ids, checks_by_lead) for i in result.items]
        guard_items = [i for i in items if i["guard_reserve"]["section"] == "guard_reserve"]
        other_items = [i for i in items if i["guard_reserve"]["section"] == "also_found"]

        general = []
        if dropped:
            general.append({"id": "mode_a_dropped", "text": parent.registry.caveats["mode_a_dropped"]})
        if profile.duty_status is None:
            general.append({"id": "authority_from_orders", "text": self.policy.caveats["authority_from_orders"]})

        questions = parent._questions(items)
        asked = {q["fact_key"] for q in questions}
        for key in ("gr_component", "duty_status", "order_authorities", "qualifying_days"):
            if key not in profile.answered() and key not in asked:
                questions.append({"fact_key": key, "question": self.policy.questions[key], "data_class": "V1",
                                  "can_answer_here": True, "records": 0, "role": ROLE_ID})

        payload = {
            "role": {"role_id": ROLE_ID, "role_version": ROLE_VERSION, "parent_agent": parent.agent_id,
                     "policy_version": self.policy.version, "policy_sha256": self.policy.policy_sha256,
                     "dataset_version": self.policy.dataset_version, "dataset_sha256": self.policy.dataset_sha256},
            "classification": classify(profile, self.policy),
            "subject": {
                "relationship": facts.get("relationship"),
                "guard_reserve_answers": profile.answered(),
                "facts_used": sorted(facts.keys()),
                "facts_derived": derivation.derived,
                "conflicts": derivation.conflicts,
                "facts_not_used_in_this_mode": sorted(dropped),
                "facts_pulled": sorted(({"fact_key": k, "source_agent": f.source_agent}
                                        for k, f in facts.facts.items() if f.provenance == "pulled"),
                                       key=lambda x: x["fact_key"]),
                "pulls": pulls,
            },
            "rule_lead_checks": checks,
            "scope": list(result.scope),
            "evaluated": result.evaluated,
            "counts": result.counts,
            "section_counts": {"guard_reserve": len(guard_items), "also_found": len(other_items)},
            "questions": questions[:10],
            "general_caveats": general,
            "research_gaps": self.policy.research_gaps,
            # Tier 4 leads from the owner-supplied Gemini report: never outcomes, never match inputs.
            "recovered_leads": self.recovered.for_person(
                profile.duty_status, [facts.get("guard_state"), facts.get("residence_state")]),
            "items": guard_items + (other_items if include_other else []),
        }
        inputs = {"role": ROLE_ID, "policy": self.policy.policy_sha256, "dataset": self.policy.dataset_sha256,
                  "guard_reserve": profile.canonical(), "facts": facts_canonical(facts),
                  "options": options.canonical(), "dropped": sorted(dropped), "include_other": include_other}
        return parent._envelope("guard_reserve_match", session, policy_name, inputs, payload)

    # ── reads ──────────────────────────────────────────────────────────────
    def catalog(self, session: Session) -> dict:
        payload = {**self.policy.catalog(), "selection": self.selection_counts(),
                   "recovered": self.recovered.summary(),
                   "manifest": {"agent_id": self.manifest.agent_id, "plane": self.manifest.plane,
                                "may_issue_determinations": self.manifest.may_issue_determinations,
                                "may_pull_from_agents": self.manifest.may_pull_from_agents,
                                "highest_class_held": self.manifest.highest_class_held}}
        return self.parent._envelope("guard_reserve_catalog", session, None, {"role": ROLE_ID}, payload)

    def leads(self, session: Session) -> dict:
        registry = self.parent.registry
        leads: List[dict] = [lead for lid, lead in sorted(registry.rule_leads.items())
                             if lid.startswith(self.policy.lead_prefix)]
        payload = {"rule_leads": leads, "checked": sorted(self.policy.lead_checks),
                   "license_reciprocity": registry.data.get("license_reciprocity")}
        return self.parent._envelope("guard_reserve_leads", session, None, {"role": ROLE_ID}, payload)

    def recovered_leads(self, session: Session, code: Optional[str] = None) -> dict:
        """The recovered Gemini leads: every jurisdiction row, or one, plus the federal leads."""
        if code is not None:
            row = self.recovered.jurisdiction(code.upper())
            if row is None:
                raise RequestError(f"unknown jurisdiction {code}")
            rows = [row]
        else:
            rows = [self.recovered.jurisdiction(c) for c in sorted(self.recovered.jurisdictions)]
        payload = {**self.recovered.summary(), "jurisdictions": rows, "federal": self.recovered.federal_for(None)}
        return self.parent._envelope("guard_reserve_recovered", session, None,
                                     {"role": ROLE_ID, "code": code, "recovered": self.recovered.provenance}, payload)

    def source_queue(self, session: Session) -> dict:
        """The research queue for the recovered leads: which pages to open, in order (no fetch here)."""
        queue = self.recovered.source_queue(self.parent.egress)
        payload = {"executable": False, "reason": "Pages are opened by a researcher with approved web access; "
                   "VetBuddy has no fetcher wired (hosting decision).", "queue": queue,
                   "counts": {"sources": len(queue), "host_known": sum(q["host_known"] for q in queue)}}
        return self.parent._envelope("guard_reserve_source_queue", session, None,
                                     {"role": ROLE_ID, "recovered": self.recovered.provenance}, payload)
