"""Router vocabulary and task library — the single source of truth.

Edit wording HERE. scripts/build_web.py generates frontend/src/kernel_data.js
from this module, and tests/parity checks the browser kernel against it.
"""

from __future__ import annotations

ROUTER_POLICY_VERSION = 'mission-router.v0.1.0'

PERSONAS: tuple[str, ...] = ('service_member', 'veteran', 'guard_reserve', 'spouse_family', 'caregiver', 'survivor')

BRANCHES: tuple[str, ...] = ('Army', 'Navy', 'Marine Corps', 'Air Force', 'Space Force', 'Coast Guard')

COMPONENTS: tuple[str, ...] = ('active_duty',
 'national_guard',
 'reserve',
 'retired',
 'retired_reserve_gray_area',
 'separated',
 'medically_separated')

AUTHORITIES: tuple[str, ...] = ('title_10', 'title_32', 'state_active_duty', 'idt_annual_training', 'not_applicable', 'unknown')

GOALS: tuple[str, ...] = ('benefits', 'claims', 'education', 'career', 'financial', 'housing', 'family', 'community')

URGENCIES: tuple[str, ...] = ('immediate', '7_days', '30_days', '90_days', 'long_term', 'info_only')

DIMENSIONS: tuple[str, ...] = ('documents',
 'benefits',
 'claims_evidence',
 'coverage',
 'career',
 'education',
 'financial',
 'housing_relocation',
 'family',
 'community')

STAGE_LABELS: dict[str, str] = {'day_0_30': 'First 30 days after separation',
 'day_31_90': 'Days 31 to 90 after separation',
 'in_service': 'In-service readiness (more than 24 months out)',
 'month_3_12': 'Months 3 to 12 after separation',
 'ongoing': 'Ongoing veteran life (more than 5 years)',
 't_12_6m': '12 to 6 months before separation',
 't_180_90d': '180 to 90 days before separation',
 't_24_12m': '24 to 12 months before separation',
 't_30d_sep': 'Final 30 days before separation',
 't_90_30d': '90 to 30 days before separation',
 'unknown': 'Not yet known — separation date not provided',
 'year_1_2': 'Year 1 to 2 after separation',
 'year_2_3': 'Year 2 to 3 after separation',
 'year_3_5': 'Year 3 to 5 after separation'}

GOAL_LANES: dict[str, str] = {'benefits': 'benefits',
 'career': 'career',
 'claims': 'claims_evidence',
 'community': 'recreation_community',
 'education': 'education',
 'family': 'family_caregiver_survivor',
 'financial': 'financial',
 'housing': 'housing_stability'}

NOTICE_TEXT: dict[str, str] = {'AUTHORITY_UNKNOWN': 'Guard/Reserve authority is unknown. Nothing has been assumed about Title 10 or Title '
                      '32 service.',
 'BENEFIT_SCREENING_NOT_AVAILABLE': 'VetBuddy does not show benefit matches yet. No eligibility rule has '
                                    'completed primary-source verification by a named reviewer, and VetBuddy '
                                    'will not guess.',
 'STAGE_UNKNOWN': 'Your transition stage is unknown because no separation date was given.'}

GOAL_TEMPLATES: dict[str, tuple[str, ...]] = {'benefits': ('BEN-01',),
 'career': ('CAR-01', 'CAR-02'),
 'claims': ('CLM-01', 'CLM-02'),
 'community': ('COM-01',),
 'education': ('EDU-01', 'EDU-02'),
 'family': ('FAM-01',),
 'financial': ('FIN-01',),
 'housing': ('HOU-02',)}

UNVERIFIED_DISCLAIMER = ("This state's benefit and resource data has not yet completed VetBuddy's primary-source ver"
    'ification process. Information shown may be incomplete or out of date. Confirm details wit'
    'h the official state veterans agency before relying on this result.')

# Task templates. `stages` empty = applies at every stage. Lower priority = sooner.
TEMPLATES: dict[str, dict] = {
    'BEN-01': dict(
        lane='benefits', dimension='benefits', priority=2,
        stages=(),
        title='Contact your state veterans affairs office about state benefits',
        why="VetBuddy has not yet verified any state's benefit rules against primary sources, so it will not show you benefit matches. The state office is the authoritative source.",
        confirm_with="your state's veterans affairs agency",
    ),
    'CAR-01': dict(
        lane='career', dimension='career', priority=2,
        stages=(),
        title='Write down your military occupation code and the duties you actually performed',
        why='This is the raw material for translating your experience into civilian job titles and a resume.',
        confirm_with=None,
    ),
    'CAR-02': dict(
        lane='career', dimension='career', priority=3,
        stages=(),
        title='Pick two or three civilian job titles you want to explore',
        why='A target keeps the resume and job search focused.',
        confirm_with=None,
    ),
    'CLM-01': dict(
        lane='claims_evidence', dimension='claims_evidence', priority=2,
        stages=(),
        title='Before filing a VA disability claim, talk with an accredited representative',
        why='Accredited Veterans Service Organization representatives, attorneys and claims agents can help with a claim. VetBuddy is not a representative and does not file claims.',
        confirm_with="VA's accreditation search for a representative",
    ),
    'CLM-02': dict(
        lane='claims_evidence', dimension='claims_evidence', priority=3,
        stages=(),
        title='Start a private list of health conditions and the dates and places they began',
        why='A dated personal record makes it easier to talk with a representative later. Keep it yourself — VetBuddy does not store health details in this version.',
        confirm_with=None,
    ),
    'COM-01': dict(
        lane='recreation_community', dimension='community', priority=3,
        stages=(),
        title='Identify one veteran or transition community near you to connect with',
        why='You chose community as a goal. This is optional and private — VetBuddy does not post or share anything for you.',
        confirm_with=None,
    ),
    'COV-01': dict(
        lane='healthcare_coverage', dimension='coverage', priority=2,
        stages=('in_service', 't_12_6m', 't_180_90d', 't_24_12m', 't_30d_sep', 't_90_30d'),
        title='List the health and life insurance coverage you have today, and ask how each one changes when you separate',
        why='Coverage changes at separation are easy to miss. Write down what you have now so nothing lapses silently.',
        confirm_with='your installation benefits or personnel office',
    ),
    'DOC-01': dict(
        lane='benefits', dimension='documents', priority=1,
        stages=(),
        title='Locate your service and separation documents and keep a copy somewhere safe',
        why='Almost every benefit, school, employer and agency process starts by asking for proof of service (for example a DD-214, or an NGB-22 for National Guard).',
        confirm_with=None,
    ),
    'EDU-01': dict(
        lane='education', dimension='education', priority=2,
        stages=(),
        title='Request your military training transcript (for example JST or CCAF)',
        why='Schools use it to evaluate credit for military training.',
        confirm_with="your branch's transcript service",
    ),
    'EDU-02': dict(
        lane='education', dimension='education', priority=3,
        stages=(),
        title='Write down the programs or schools you are considering',
        why='Education benefit rules depend on the specific program and school. A short list lets you confirm the right ones.',
        confirm_with=None,
    ),
    'FACT-DATE': dict(
        lane='other', dimension='documents', priority=1,
        stages=(),
        title='Confirm your separation, retirement or release-from-orders date',
        why='Your transition stage and the order of your next steps are calculated from this date. It is missing, so VetBuddy is not guessing a stage.',
        confirm_with='your unit personnel office or your orders',
    ),
    'FAM-01': dict(
        lane='family_caregiver_survivor', dimension='family', priority=3,
        stages=(),
        title='Talk with your household about the plan and who needs copies of which documents',
        why='Family members often need to act on your behalf. Decide together; VetBuddy never shares records automatically.',
        confirm_with=None,
    ),
    'FIN-01': dict(
        lane='financial', dimension='financial', priority=2,
        stages=(),
        title='Build a transition budget that compares your pay and allowances now with expected income after',
        why='Pay, allowances and tax treatment can change at separation. A side-by-side budget shows the gap early.',
        confirm_with=None,
    ),
    'GR-AUTH': dict(
        lane='guard_reserve', dimension='documents', priority=1,
        stages=(),
        title='Find the legal authority printed on your orders (Title 10, Title 32, or State Active Duty)',
        why='For Guard and Reserve members, what you may qualify for follows the authority cited on your orders, not the mission. You marked it as unknown, so nothing is assumed.',
        confirm_with='the citation block on your orders, or your unit administrator',
    ),
    'GR-RECORD': dict(
        lane='guard_reserve', dimension='documents', priority=2,
        stages=(),
        title='Keep a running list of every set of orders: authority, start date and end date',
        why='Guard and Reserve benefits often depend on cumulative time under specific authorities. A complete list prevents under-counting later.',
        confirm_with=None,
    ),
    'HOU-01': dict(
        lane='housing_stability', dimension='housing_relocation', priority=2,
        stages=(),
        title='List housing options and costs at your destination',
        why='You told VetBuddy you are moving. Knowing real costs at the destination early keeps the budget honest.',
        confirm_with=None,
    ),
    'HOU-02': dict(
        lane='housing_stability', dimension='housing_relocation', priority=2,
        stages=(),
        title='Write down your housing plan for the first 90 days after separation',
        why='You chose housing as a goal. A written plan makes gaps visible before they become urgent.',
        confirm_with=None,
    ),
    'MED-01': dict(
        lane='claims_evidence', dimension='claims_evidence', priority=1,
        stages=(),
        title='Ask your IDES / MEB point of contact which documents you should gather now',
        why='Medical separation runs on its own process and timeline. The point of contact assigned to you is the authoritative source for what it needs.',
        confirm_with='your IDES / MEB point of contact',
    ),
    'REL-01': dict(
        lane='state_local', dimension='housing_relocation', priority=2,
        stages=(),
        title='Check how moving changes your state-level benefits and taxes',
        why='Your current and destination jurisdictions differ. VetBuddy will not compare them until both are verified.',
        confirm_with='the veterans affairs agency in your destination state',
    ),
    'TAP-01': dict(
        lane='career', dimension='career', priority=1,
        stages=('in_service', 't_12_6m', 't_180_90d', 't_24_12m', 't_30d_sep', 't_90_30d'),
        title="Contact your installation's Transition Assistance Program (TAP) office",
        why='Ask which transition counseling and workshops apply to you and when to start them.',
        confirm_with='your installation TAP office',
    ),
}
