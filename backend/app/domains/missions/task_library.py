"""
Task templates the deterministic Mission Router may emit.

Content rules (CLAUDE.md, master spec §2.7):
  * Organizational actions only. No template states an eligibility result,
    a filing deadline, a dollar amount, a rate, or that something is
    "required" by law. Where an official requirement may apply, the task
    tells the person WHO to confirm it with instead of asserting it.
  * Every template names its readiness dimension and lane so the brief can
    show transparent dimensions instead of a single opaque score.
  * Changing any wording or rule here is a policy change: bump
    ROUTER_POLICY_VERSION in router_policy.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TaskTemplate:
    template_id: str
    lane: str
    dimension: str
    title: str
    why: str
    priority: int                      # 1 = highest
    stages: frozenset[str] = field(default_factory=frozenset)  # empty = any stage
    confirm_with: str | None = None    # who holds the authoritative answer


PRE_SEPARATION = frozenset({"in_service", "t_24_12m", "t_12_6m", "t_180_90d", "t_90_30d", "t_30d_sep"})
EARLY_POST = frozenset({"day_0_30", "day_31_90", "month_3_12"})

TEMPLATES: dict[str, TaskTemplate] = {t.template_id: t for t in [
    # ── always-on foundations ──
    TaskTemplate("DOC-01", "benefits", "documents",
        "Locate your service and separation documents and keep a copy somewhere safe",
        "Almost every benefit, school, employer and agency process starts by asking for proof of service "
        "(for example a DD-214, or an NGB-22 for National Guard).", 1),
    TaskTemplate("FACT-DATE", "other", "documents",
        "Confirm your separation, retirement or release-from-orders date",
        "Your transition stage and the order of your next steps are calculated from this date. "
        "It is missing, so VetBuddy is not guessing a stage.", 1,
        confirm_with="your unit personnel office or your orders"),
    # ── Guard / Reserve (Sentinel: authority on the orders decides) ──
    TaskTemplate("GR-AUTH", "guard_reserve", "documents",
        "Find the legal authority printed on your orders (Title 10, Title 32, or State Active Duty)",
        "For Guard and Reserve members, what you may qualify for follows the authority cited on your orders, "
        "not the mission. You marked it as unknown, so nothing is assumed.", 1,
        confirm_with="the citation block on your orders, or your unit administrator"),
    TaskTemplate("GR-RECORD", "guard_reserve", "documents",
        "Keep a running list of every set of orders: authority, start date and end date",
        "Guard and Reserve benefits often depend on cumulative time under specific authorities. "
        "A complete list prevents under-counting later.", 2),
    # ── transition (pre-separation) ──
    TaskTemplate("TAP-01", "career", "career",
        "Contact your installation's Transition Assistance Program (TAP) office",
        "Ask which transition counseling and workshops apply to you and when to start them.", 1,
        stages=PRE_SEPARATION, confirm_with="your installation TAP office"),
    TaskTemplate("MED-01", "claims_evidence", "claims_evidence",
        "Ask your IDES / MEB point of contact which documents you should gather now",
        "Medical separation runs on its own process and timeline. The point of contact assigned to you "
        "is the authoritative source for what it needs.", 1,
        confirm_with="your IDES / MEB point of contact"),
    TaskTemplate("COV-01", "healthcare_coverage", "coverage",
        "List the health and life insurance coverage you have today, and ask how each one changes when you separate",
        "Coverage changes at separation are easy to miss. Write down what you have now so nothing lapses silently.", 2,
        stages=PRE_SEPARATION, confirm_with="your installation benefits or personnel office"),
    # ── lanes chosen by goals ──
    TaskTemplate("BEN-01", "benefits", "benefits",
        "Contact your state veterans affairs office about state benefits",
        "VetBuddy has not yet verified any state's benefit rules against primary sources, "
        "so it will not show you benefit matches. The state office is the authoritative source.", 2,
        confirm_with="your state's veterans affairs agency"),
    TaskTemplate("CLM-01", "claims_evidence", "claims_evidence",
        "Before filing a VA disability claim, talk with an accredited representative",
        "Accredited Veterans Service Organization representatives, attorneys and claims agents can help with a claim. "
        "VetBuddy is not a representative and does not file claims.", 2,
        confirm_with="VA's accreditation search for a representative"),
    TaskTemplate("CLM-02", "claims_evidence", "claims_evidence",
        "Start a private list of health conditions and the dates and places they began",
        "A dated personal record makes it easier to talk with a representative later. Keep it yourself — "
        "VetBuddy does not store health details in this version.", 3),
    TaskTemplate("EDU-01", "education", "education",
        "Request your military training transcript (for example JST or CCAF)",
        "Schools use it to evaluate credit for military training.", 2,
        confirm_with="your branch's transcript service"),
    TaskTemplate("EDU-02", "education", "education",
        "Write down the programs or schools you are considering",
        "Education benefit rules depend on the specific program and school. A short list lets you confirm the right ones.", 3),
    TaskTemplate("CAR-01", "career", "career",
        "Write down your military occupation code and the duties you actually performed",
        "This is the raw material for translating your experience into civilian job titles and a resume.", 2),
    TaskTemplate("CAR-02", "career", "career",
        "Pick two or three civilian job titles you want to explore",
        "A target keeps the resume and job search focused.", 3),
    TaskTemplate("FIN-01", "financial", "financial",
        "Build a transition budget that compares your pay and allowances now with expected income after",
        "Pay, allowances and tax treatment can change at separation. A side-by-side budget shows the gap early.", 2),
    TaskTemplate("HOU-01", "housing_stability", "housing_relocation",
        "List housing options and costs at your destination",
        "You told VetBuddy you are moving. Knowing real costs at the destination early keeps the budget honest.", 2),
    TaskTemplate("HOU-02", "housing_stability", "housing_relocation",
        "Write down your housing plan for the first 90 days after separation",
        "You chose housing as a goal. A written plan makes gaps visible before they become urgent.", 2),
    TaskTemplate("FAM-01", "family_caregiver_survivor", "family",
        "Talk with your household about the plan and who needs copies of which documents",
        "Family members often need to act on your behalf. Decide together; VetBuddy never shares records automatically.", 3),
    TaskTemplate("COM-01", "recreation_community", "community",
        "Identify one veteran or transition community near you to connect with",
        "You chose community as a goal. This is optional and private — VetBuddy does not post or share anything for you.", 3),
    TaskTemplate("REL-01", "state_local", "housing_relocation",
        "Check how moving changes your state-level benefits and taxes",
        "Your current and destination jurisdictions differ. VetBuddy will not compare them until both are verified.", 2,
        confirm_with="the veterans affairs agency in your destination state"),
]}

# goal (user-chosen) -> templates it adds
GOAL_TEMPLATES: dict[str, tuple[str, ...]] = {
    "benefits": ("BEN-01",),
    "claims": ("CLM-01", "CLM-02"),
    "education": ("EDU-01", "EDU-02"),
    "career": ("CAR-01", "CAR-02"),
    "financial": ("FIN-01",),
    "housing": ("HOU-02",),
    "family": ("FAM-01",),
    "community": ("COM-01",),
}

GOAL_LANES: dict[str, str] = {
    "benefits": "benefits", "claims": "claims_evidence", "education": "education",
    "career": "career", "financial": "financial", "housing": "housing_stability",
    "family": "family_caregiver_survivor", "community": "recreation_community",
}
