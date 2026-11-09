"""The fact catalog and the token resolver.

A fact is one thing a person tells the vault, or that the vault pulls from
another agent with the person's grant, or that it derives for a household
member. Each fact has a data class (V0-V5). The class decides which privacy
mode may hold it and whether it may ever travel between agents.

Income is not collected. Conditions and diagnoses are not collected: they
are V4 and no rule needs them. The only V4 fact is ``severe_disability``,
a yes/no self-attestation used inside one session and never stored, pulled
or logged.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, Mapping, Optional, Tuple

from .rules import Tok
from .tri import Tri
from .vocab import DATA_CLASSES, JURISDICTIONS, MODE_CEILING

SERVICE_STATUSES = ("serving", "separated", "retired", "never_served")
COMPONENTS = ("active", "guard", "reserve")
RELATIONSHIPS = ("self", "spouse", "child", "surviving_spouse", "parent")
DISCHARGES = ("honorable", "general", "other_than_honorable", "bad_conduct", "dishonorable", "uncharacterized")
SPONSOR_STATUSES = ("serving", "separated", "retired", "deceased")
PROVENANCES = ("self_attested", "pulled", "derived")


@dataclass(frozen=True)
class FactSpec:
    key: str
    data_class: str
    kind: str                       # enum, bool, int, rating, jurisdiction
    question: str
    values: Tuple[str, ...] = ()
    low: int = 0
    high: int = 0
    session_only: bool = False
    pullable: bool = True


_SPECS = (
    FactSpec("residence_state", "V1", "jurisdiction",
             "Which state or territory is your legal residence (your home state for taxes and voting)?"),
    FactSpec("duty_station_state", "V1", "jurisdiction",
             "If you, or the service member in your family, are serving, which state or territory is the duty station?"),
    FactSpec("service_status", "V1", "enum", "Are you serving now, separated, retired, or have you never served?", SERVICE_STATUSES),
    FactSpec("component", "V1", "enum", "Which component (active, National Guard or Reserve) are or were you in?", COMPONENTS),
    FactSpec("guard_state", "V1", "jurisdiction", "If you are or were in the National Guard, which state's Guard?"),
    FactSpec("on_active_duty_orders", "V1", "bool", "If you are in the Guard or Reserve, are you on active duty orders now?"),
    FactSpec("relationship", "V1", "enum", "Whose benefits are we looking at: yours, a spouse's, a child's, a surviving spouse's or a parent's?", RELATIONSHIPS),
    FactSpec("age", "V1", "int", "How old is the person?", low=0, high=120),
    FactSpec("active_duty_days", "V1", "int", "About how many days of federal active duty in total (not drill or annual training)?", low=0, high=20000),
    FactSpec("wartime_service", "V1", "bool", "Did the service fall in a wartime period?"),
    FactSpec("discharge", "V2", "enum", "What was the character of discharge?", DISCHARGES),
    FactSpec("va_rating", "V2", "rating", "What is the VA combined service-connected rating (or none)?"),
    FactSpec("rating_permanent_total", "V2", "bool", "Is the VA rating permanent and total?"),
    FactSpec("individual_unemployability", "V2", "bool", "Is VA paying at the unemployability (IU/TDIU) rate?"),
    FactSpec("purple_heart", "V2", "bool", "Was a Purple Heart awarded?"),
    FactSpec("medal_of_honor", "V2", "bool", "Was the Medal of Honor awarded?"),
    FactSpec("former_pow", "V2", "bool", "Was the person a prisoner of war?"),
    FactSpec("gold_star_family", "V2", "bool", "Is the person a Gold Star family member (a family member died while serving)?"),
    FactSpec("sponsor_status", "V2", "enum", "Is the service member or veteran in the family serving, separated, retired or deceased?", SPONSOR_STATUSES),
    FactSpec("sponsor_va_rating", "V2", "rating", "What is the sponsor's VA combined rating (or none)?"),
    FactSpec("sponsor_permanent_total", "V2", "bool", "Is the sponsor's VA rating permanent and total?"),
    FactSpec("sponsor_unemployability", "V2", "bool", "Is VA paying the sponsor at the unemployability rate?"),
    FactSpec("sponsor_service_connected", "V2", "bool", "Is the sponsor's disability or death service-connected?"),
    FactSpec("sponsor_died_in_line_of_duty", "V2", "bool", "Did the sponsor die in the line of duty?"),
    FactSpec("sponsor_pow_mia", "V2", "bool", "Is the sponsor missing in action or a prisoner of war?"),
    FactSpec("severe_disability", "V4", "bool",
             "Is there a severe service-connected disability such as loss of use of a limb or blindness? (Used for this search only; never saved.)",
             session_only=True, pullable=False),
)

CATALOG: Dict[str, FactSpec] = {spec.key: spec for spec in _SPECS}

# Pseudo-key reported when a discharge needs VA's character-of-discharge
# decision before a rule can say anything. It is never collected.
DISCHARGE_REVIEW = "discharge_review"
PSEUDO_KEYS = {DISCHARGE_REVIEW: "A VA character-of-discharge decision may be needed; an accredited representative can help."}

# Which fact keys each token reads. Used for minimum-necessary pulls: the
# vault asks only for facts that rules in scope actually mention.
TOKEN_FACTS: Dict[str, FrozenSet[str]] = {
    "true": frozenset(),
    "res": frozenset({"residence_state"}),
    "nonres": frozenset({"residence_state"}),
    "stn": frozenset({"service_status", "duty_station_state", "relationship", "sponsor_status"}),
    "ad": frozenset({"service_status", "component", "on_active_duty_orders"}),
    "ng": frozenset({"service_status", "component", "guard_state"}),
    "ngany": frozenset({"service_status", "component"}),
    "ngret": frozenset({"service_status", "component", "guard_state"}),
    "rsv": frozenset({"service_status", "component"}),
    "sm": frozenset({"service_status"}),
    "vet": frozenset({"service_status"}),
    "ret": frozenset({"service_status"}),
    "sc": frozenset({"va_rating"}),
    "r": frozenset({"va_rating"}),
    "pt": frozenset({"va_rating", "rating_permanent_total"}),
    "iu": frozenset({"va_rating", "individual_unemployability"}),
    "sev": frozenset({"severe_disability"}),
    "hon": frozenset({"discharge"}),
    "uhc": frozenset({"discharge"}),
    "otd": frozenset({"discharge"}),
    "wartime": frozenset({"wartime_service"}),
    "days": frozenset({"active_duty_days"}),
    "age": frozenset({"age"}),
    "ph": frozenset({"purple_heart"}),
    "moh": frozenset({"medal_of_honor"}),
    "pow": frozenset({"former_pow"}),
    "gs": frozenset({"gold_star_family"}),
    "sp": frozenset({"relationship"}),
    "ch": frozenset({"relationship"}),
    "dep": frozenset({"relationship"}),
    "ss": frozenset({"relationship"}),
    "spsc": frozenset({"relationship", "sponsor_service_connected"}),
    "sppt": frozenset({"relationship", "sponsor_permanent_total"}),
    "spiu": frozenset({"relationship", "sponsor_unemployability"}),
    "spkia": frozenset({"relationship", "sponsor_died_in_line_of_duty"}),
    "sppm": frozenset({"relationship", "sponsor_pow_mia"}),
    "spsm": frozenset({"relationship", "sponsor_status"}),
    "spret": frozenset({"relationship", "sponsor_status"}),
    "spvet": frozenset({"relationship", "sponsor_status"}),
    "spdec": frozenset({"relationship", "sponsor_status", "sponsor_died_in_line_of_duty"}),
    "spr": frozenset({"relationship", "sponsor_va_rating"}),
}


class FactError(ValueError):
    """A fact value that is not allowed for its key."""


def class_rank(data_class: str) -> int:
    return DATA_CLASSES.index(data_class)


def within_ceiling(data_class: str, mode: str) -> bool:
    if mode not in MODE_CEILING:
        return False
    return class_rank(data_class) <= class_rank(MODE_CEILING[mode])


def validate_value(key: str, value: Any) -> Any:
    """Return the value if it is allowed for the key, else raise FactError."""
    spec = CATALOG.get(key)
    if spec is None:
        raise FactError(f"unknown fact {key!r}")
    if spec.kind == "jurisdiction":
        if not isinstance(value, str) or value not in JURISDICTIONS or value == "US":
            raise FactError(f"{key} must be a state or territory code")
        return value
    if spec.kind == "enum":
        if value not in spec.values:
            raise FactError(f"{key} must be one of {', '.join(spec.values)}")
        return value
    if spec.kind == "bool":
        if not isinstance(value, bool):
            raise FactError(f"{key} must be true or false")
        return value
    if spec.kind == "int":
        if isinstance(value, bool) or not isinstance(value, int) or not spec.low <= value <= spec.high:
            raise FactError(f"{key} must be a whole number from {spec.low} to {spec.high}")
        return value
    if spec.kind == "rating":
        if value == "none":
            return value
        if isinstance(value, bool) or not isinstance(value, int) or value not in range(0, 101, 10):
            raise FactError(f"{key} must be 0-100 in steps of 10, or \"none\"")
        return value
    raise FactError(f"unsupported kind for {key}")  # pragma: no cover


@dataclass(frozen=True)
class Fact:
    key: str
    value: Any
    provenance: str = "self_attested"
    certain: bool = True
    source_agent: Optional[str] = None

    @property
    def data_class(self) -> str:
        return CATALOG[self.key].data_class


@dataclass
class FactSet:
    """The facts about one person, with how each was learned."""

    facts: Dict[str, Fact] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any], *, provenance: str = "self_attested",
                     uncertain: FrozenSet[str] = frozenset()) -> "FactSet":
        out = cls()
        for key, value in values.items():
            out.put(Fact(key, validate_value(key, value), provenance, key not in uncertain))
        return out

    def put(self, fact: Fact) -> None:
        if fact.provenance not in PROVENANCES:
            raise FactError(f"unknown provenance {fact.provenance!r}")
        validate_value(fact.key, fact.value)
        self.facts[fact.key] = fact

    def get(self, key: str) -> Any:
        fact = self.facts.get(key)
        return None if fact is None else fact.value

    def has(self, key: str) -> bool:
        return key in self.facts

    def keys(self):
        return self.facts.keys()

    def without(self, keys) -> "FactSet":
        return FactSet({k: f for k, f in self.facts.items() if k not in keys})

    def uncertain_keys(self) -> FrozenSet[str]:
        return frozenset(k for k, f in self.facts.items() if not f.certain)

    def limited_to(self, mode: str) -> Tuple["FactSet", FrozenSet[str]]:
        """Drop facts above the mode's ceiling; return what was dropped.

        Session-only facts survive only in Mode B, where they are used in
        memory for one search and never written anywhere.
        """
        kept: Dict[str, Fact] = {}
        dropped = set()
        for key, fact in self.facts.items():
            spec = CATALOG[key]
            allowed = within_ceiling(spec.data_class, mode) or (spec.session_only and mode == "B")
            if allowed:
                kept[key] = fact
            else:
                dropped.add(key)
        return FactSet(kept), frozenset(dropped)


def _flag(facts: FactSet, key: str) -> Tuple[Tri, FrozenSet[str]]:
    if not facts.has(key):
        return Tri.UNKNOWN, frozenset({key})
    return Tri.of(bool(facts.get(key))), frozenset()


def _status_is(facts: FactSet, *wanted: str) -> Tuple[Tri, FrozenSet[str]]:
    if not facts.has("service_status"):
        return Tri.UNKNOWN, frozenset({"service_status"})
    return Tri.of(facts.get("service_status") in wanted), frozenset()


def _component_is(facts: FactSet, wanted: str) -> Tuple[Tri, FrozenSet[str]]:
    if not facts.has("component"):
        return Tri.UNKNOWN, frozenset({"component"})
    return Tri.of(facts.get("component") == wanted), frozenset()


def _state_is(facts: FactSet, key: str, jurisdiction: str) -> Tuple[Tri, FrozenSet[str]]:
    if not facts.has(key):
        return Tri.UNKNOWN, frozenset({key})
    if jurisdiction == "US":
        return Tri.TRUE, frozenset()
    return Tri.of(facts.get(key) == jurisdiction), frozenset()


def _both(a, b):
    value = a[0] & b[0]
    if value is not Tri.UNKNOWN:
        return value, frozenset()
    return value, (a[1] if a[0] is Tri.UNKNOWN else frozenset()) | (b[1] if b[0] is Tri.UNKNOWN else frozenset())


def _either(a, b):
    value = a[0] | b[0]
    if value is not Tri.UNKNOWN:
        return value, frozenset()
    return value, (a[1] if a[0] is Tri.UNKNOWN else frozenset()) | (b[1] if b[0] is Tri.UNKNOWN else frozenset())


def _rating_at_least(facts: FactSet, key: str, bound: int) -> Tuple[Tri, FrozenSet[str]]:
    if not facts.has(key):
        return Tri.UNKNOWN, frozenset({key})
    value = facts.get(key)
    if value == "none":
        return Tri.FALSE, frozenset()
    return Tri.of(value >= bound), frozenset()


def _relationship_in(facts: FactSet, *wanted: str) -> Tuple[Tri, FrozenSet[str]]:
    if not facts.has("relationship"):
        return Tri.UNKNOWN, frozenset({"relationship"})
    return Tri.of(facts.get("relationship") in wanted), frozenset()


def _has_sponsor(facts: FactSet) -> Tuple[Tri, FrozenSet[str]]:
    return _relationship_in(facts, "spouse", "child", "surviving_spouse", "parent")


def resolver(facts: FactSet, jurisdiction: str):
    """Return a token resolver for one person and one record's jurisdiction."""

    def resolve(tok: Tok) -> Tuple[Tri, FrozenSet[str]]:
        name = tok.name
        if name == "true":
            return Tri.TRUE, frozenset()
        if name == "res":
            return _state_is(facts, "residence_state", jurisdiction)
        if name == "nonres":
            value, missing = _state_is(facts, "residence_state", jurisdiction)
            if jurisdiction == "US" and value is Tri.TRUE:
                return Tri.FALSE, frozenset()
            return ~value, missing
        if name == "sm":
            return _status_is(facts, "serving")
        if name == "vet":
            return _status_is(facts, "separated", "retired")
        if name == "ret":
            return _status_is(facts, "retired")
        if name == "stn":
            # The person is stationed there, or is the spouse or child of a member stationed there
            # (for a family member, duty_station_state is the service member's duty station).
            serving = _status_is(facts, "serving")
            if serving[0] is not Tri.TRUE:
                family = _relationship_in(facts, "spouse", "child")
                if family[0] is not Tri.FALSE:
                    if not facts.has("sponsor_status"):
                        sponsor_serving = (Tri.UNKNOWN, frozenset({"sponsor_status"}))
                    else:
                        sponsor_serving = (Tri.of(facts.get("sponsor_status") == "serving"), frozenset())
                    serving = _either(serving, _both(family, sponsor_serving))
            return _both(serving, _state_is(facts, "duty_station_state", jurisdiction))
        if name == "ad":
            serving = _status_is(facts, "serving")
            if serving[0] is Tri.FALSE:
                return serving
            on_orders = _flag(facts, "on_active_duty_orders")
            return _both(serving, _either(_component_is(facts, "active"), on_orders))
        if name in ("ngany", "ng"):
            base = _both(_status_is(facts, "serving"), _component_is(facts, "guard"))
            # For a federal record every state's Guard counts, so ng means ngany.
            if name == "ng" and jurisdiction != "US" and base[0] is not Tri.FALSE:
                return _both(base, _state_is(facts, "guard_state", jurisdiction))
            return base
        if name == "ngret":
            base = _both(_status_is(facts, "retired"), _component_is(facts, "guard"))
            if base[0] is Tri.FALSE or jurisdiction == "US":
                return base
            return _both(base, _state_is(facts, "guard_state", jurisdiction))
        if name == "rsv":
            return _both(_status_is(facts, "serving"), _component_is(facts, "reserve"))
        if name == "sc":
            if not facts.has("va_rating"):
                return Tri.UNKNOWN, frozenset({"va_rating"})
            return Tri.of(facts.get("va_rating") != "none"), frozenset()
        if name == "r":
            return _rating_at_least(facts, "va_rating", tok.value)
        if name in ("pt", "iu"):
            flag_key = "rating_permanent_total" if name == "pt" else "individual_unemployability"
            if facts.get("va_rating") == "none":
                return Tri.FALSE, frozenset()
            return _flag(facts, flag_key)
        if name == "sev":
            return _flag(facts, "severe_disability")
        if name in ("hon", "uhc", "otd"):
            if not facts.has("discharge"):
                return Tri.UNKNOWN, frozenset({"discharge"})
            discharge = facts.get("discharge")
            if name == "hon":
                return Tri.of(discharge == "honorable"), frozenset()
            if name == "uhc":
                return Tri.of(discharge in ("honorable", "general")), frozenset()
            if discharge in ("honorable", "general", "uncharacterized"):
                return Tri.TRUE, frozenset()
            if discharge == "dishonorable":
                return Tri.FALSE, frozenset()
            return Tri.UNKNOWN, frozenset({DISCHARGE_REVIEW})
        if name == "wartime":
            return _flag(facts, "wartime_service")
        if name == "days":
            if not facts.has("active_duty_days"):
                return Tri.UNKNOWN, frozenset({"active_duty_days"})
            return Tri.of(facts.get("active_duty_days") >= tok.value), frozenset()
        if name == "age":
            if not facts.has("age"):
                return Tri.UNKNOWN, frozenset({"age"})
            age = facts.get("age")
            return Tri.of(age >= tok.value if tok.op == ">=" else age < tok.value), frozenset()
        if name == "ph":
            return _flag(facts, "purple_heart")
        if name == "moh":
            return _flag(facts, "medal_of_honor")
        if name == "pow":
            return _flag(facts, "former_pow")
        if name == "gs":
            return _flag(facts, "gold_star_family")
        if name == "sp":
            return _relationship_in(facts, "spouse")
        if name == "ch":
            return _relationship_in(facts, "child")
        if name == "dep":
            return _relationship_in(facts, "spouse", "child")
        if name == "ss":
            return _relationship_in(facts, "surviving_spouse")
        # Sponsor tokens: false for a person evaluated as themselves.
        sponsor = _has_sponsor(facts)
        if sponsor[0] is Tri.FALSE:
            return Tri.FALSE, frozenset()
        if name in ("spsm", "spret", "spvet"):
            if not facts.has("sponsor_status"):
                status = (Tri.UNKNOWN, frozenset({"sponsor_status"}))
            else:
                wanted = {"spsm": ("serving",), "spret": ("retired",), "spvet": ("separated", "retired")}[name]
                status = (Tri.of(facts.get("sponsor_status") in wanted), frozenset())
            return _both(sponsor, status)
        if name == "spr":
            return _both(sponsor, _rating_at_least(facts, "sponsor_va_rating", tok.value))
        if name == "spdec":
            # A surviving spouse's sponsor has died; otherwise the sponsor's status or a death in the line of duty says so.
            if not facts.has("sponsor_status"):
                status = (Tri.UNKNOWN, frozenset({"sponsor_status"}))
            else:
                status = (Tri.of(facts.get("sponsor_status") == "deceased"), frozenset())
            died = _either(_relationship_in(facts, "surviving_spouse"),
                           _either(status, _flag(facts, "sponsor_died_in_line_of_duty")))
            return _both(sponsor, died)
        flag_key = {
            "spsc": "sponsor_service_connected",
            "sppt": "sponsor_permanent_total",
            "spiu": "sponsor_unemployability",
            "spkia": "sponsor_died_in_line_of_duty",
            "sppm": "sponsor_pow_mia",
        }.get(name)
        if flag_key is None:
            raise KeyError(f"no resolver for token {name!r}")
        return _both(sponsor, _flag(facts, flag_key))

    return resolve


def facts_for_tokens(toks) -> FrozenSet[str]:
    keys = set()
    for tok in toks:
        keys |= TOKEN_FACTS[tok.name]
    return frozenset(keys)


def catalog_view() -> Dict[str, Dict[str, Any]]:
    """A serialisable copy of the catalog for the registry and the API."""
    return {
        spec.key: {
            "data_class": spec.data_class,
            "kind": spec.kind,
            "question": spec.question,
            "values": list(spec.values),
            "session_only": spec.session_only,
            "pullable": spec.pullable,
        }
        for spec in _SPECS
    }
