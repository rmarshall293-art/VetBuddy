"""The rule language (architecture doc section 6.3).

A rule states the necessary conditions a person must meet for a benefit to be
worth showing as a preliminary match. It never states sufficient conditions:
when the research could not pin a condition down, the condition stays in the
plain-language "who it is for" text and out of the rule, so a loose rule shows
a lead the person can read while a strict rule could hide a real benefit.

Grammar (``&`` binds tighter than ``|``; ``!`` binds tightest)::

    expr  := and ( "|" and )*
    and   := not ( "&" not )*
    not   := "!" not | atom
    atom  := "(" expr ")" | token
    token := NAME | NAME ">=" INT | NAME "<" INT

The subject of every token is the person being evaluated. Sponsor tokens
(``sp...``) describe the service member or veteran that person is a family
member of. Evaluation uses three-valued logic: a missing fact is UNKNOWN and
stays UNKNOWN, so a rule over unknown facts yields NEEDS_INFORMATION rather
than a silent "no".
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, FrozenSet, Iterable, Tuple, Union

from .tri import Tri

# Plain tokens and what they mean. The explanations are copied into the
# registry vocabulary, returned by the API's catalog route, and listed in the
# architecture document (section 6.3).
PLAIN_TOKENS = {
    "true": "always true (no encoded condition)",
    "res": "is a legal resident of the record's state or territory",
    "nonres": "is a legal resident somewhere other than the record's state or territory",
    "stn": ("is serving and stationed in the record's state or territory, or is the spouse or child of a "
            "service member stationed there"),
    "ad": "is serving on active duty (active component, or Guard or Reserve on active duty orders)",
    "ng": "is serving in the record's state National Guard",
    "ngany": "is serving in any National Guard",
    "ngret": "is retired from the National Guard (the record's state, for state records)",
    "rsv": "is serving in a federal Reserve component",
    "sm": "is serving in any component",
    "vet": "has served and separated or retired",
    "ret": "is a military retiree",
    "sc": "has a VA service-connected rating (any percentage, including 0%)",
    "pt": "the VA rating is permanent and total",
    "iu": "is paid at the 100% rate for individual unemployability",
    "sev": "has a severe service-connected disability (loss of use of limbs, blindness); session-only",
    "hon": "was discharged honorably",
    "uhc": "was discharged honorably or under honorable conditions (general)",
    "otd": "was discharged under conditions other than dishonorable",
    "wartime": "served during a wartime period",
    "ph": "received the Purple Heart",
    "moh": "received the Medal of Honor",
    "pow": "is a former prisoner of war",
    "gs": "is a Gold Star family member",
    "sp": "is the spouse of a living service member or veteran",
    "ch": "is the child of a service member or veteran",
    "dep": "is a spouse or child of a service member or veteran",
    "ss": "is a surviving spouse",
    "spsc": "the sponsor's disability or death is service-connected",
    "sppt": "the sponsor's VA rating is permanent and total",
    "spiu": "the sponsor is paid at the unemployability rate",
    "spkia": "the sponsor died in the line of duty",
    "sppm": "the sponsor is missing in action or a prisoner of war",
    "spsm": "the sponsor is serving",
    "spret": "the sponsor is a military retiree",
    "spvet": "the sponsor has served and separated or retired",
    "spdec": "the sponsor has died (any cause)",
}

# Parametric tokens: name -> (operator, low bound, high bound, explanation).
PARAM_TOKENS = {
    "r": (">=", 0, 100, "VA combined rating is at least N percent"),
    "spr": (">=", 0, 100, "the sponsor's VA combined rating is at least N percent"),
    "days": (">=", 1, 10000, "has at least N days of active duty"),
    "age": (">=<", 0, 120, "age is at least N (age>=N) or under N (age<N)"),
}

TOKEN_NAMES = frozenset(PLAIN_TOKENS) | frozenset(PARAM_TOKENS)


class RuleError(ValueError):
    """A rule that does not parse or names an unknown token."""

    def __init__(self, message: str, rule: str, position: int):
        super().__init__(f"{message} at position {position} in rule {rule!r}")
        self.rule = rule
        self.position = position


@dataclass(frozen=True)
class Tok:
    name: str
    op: str = ""
    value: int = 0

    def render(self) -> str:
        return f"{self.name}{self.op}{self.value}" if self.op else self.name


@dataclass(frozen=True)
class Not:
    child: "Node"


@dataclass(frozen=True)
class And:
    children: Tuple["Node", ...]


@dataclass(frozen=True)
class Or:
    children: Tuple["Node", ...]


Node = Union[Tok, Not, And, Or]

_LEX = re.compile(r"\s*(?:(?P<op>[&|!()])|(?P<tok>[a-z]+(?:>=|<)?\d*))")


def _lex(rule: str):
    position = 0
    items = []
    stripped_end = len(rule.rstrip())
    while position < stripped_end:
        match = _LEX.match(rule, position)
        if not match or match.end() == position:
            raise RuleError("unexpected character", rule, position)
        start = match.start("op") if match.group("op") else match.start("tok")
        items.append((match.group("op") or match.group("tok"), start))
        position = match.end()
    return items


def _make_token(text: str, rule: str, position: int) -> Tok:
    match = re.fullmatch(r"([a-z]+)(?:(>=|<)(\d+))?", text)
    if not match:
        raise RuleError(f"malformed token {text!r}", rule, position)
    name, op, number = match.group(1), match.group(2) or "", match.group(3)
    if name in PLAIN_TOKENS:
        if op:
            raise RuleError(f"token {name!r} takes no comparison", rule, position)
        return Tok(name)
    if name in PARAM_TOKENS:
        allowed, low, high, _ = PARAM_TOKENS[name]
        if not op:
            raise RuleError(f"token {name!r} needs a comparison such as {name}>=N", rule, position)
        if op not in (">=", "<") or (op == "<" and "<" not in allowed) or (op == ">=" and ">=" not in allowed):
            raise RuleError(f"token {name!r} does not take {op!r}", rule, position)
        value = int(number)
        if not low <= value <= high:
            raise RuleError(f"{name}{op}{value} is out of range {low}-{high}", rule, position)
        return Tok(name, op, value)
    raise RuleError(f"unknown token {name!r}", rule, position)


class _Parser:
    def __init__(self, rule: str):
        self.rule = rule
        self.items = _lex(rule)
        self.index = 0

    def peek(self):
        return self.items[self.index][0] if self.index < len(self.items) else None

    def position(self) -> int:
        return self.items[self.index][1] if self.index < len(self.items) else len(self.rule)

    def take(self):
        item = self.items[self.index]
        self.index += 1
        return item

    def parse(self) -> Node:
        if not self.items:
            raise RuleError("empty rule", self.rule, 0)
        node = self.expr()
        if self.index != len(self.items):
            raise RuleError(f"unexpected {self.peek()!r}", self.rule, self.position())
        return node

    def expr(self) -> Node:
        parts = [self.conj()]
        while self.peek() == "|":
            self.take()
            parts.append(self.conj())
        return parts[0] if len(parts) == 1 else Or(tuple(parts))

    def conj(self) -> Node:
        parts = [self.neg()]
        while self.peek() == "&":
            self.take()
            parts.append(self.neg())
        return parts[0] if len(parts) == 1 else And(tuple(parts))

    def neg(self) -> Node:
        if self.peek() == "!":
            self.take()
            return Not(self.neg())
        return self.atom()

    def atom(self) -> Node:
        current = self.peek()
        if current is None:
            raise RuleError("rule ends early", self.rule, self.position())
        if current == "(":
            self.take()
            node = self.expr()
            if self.peek() != ")":
                raise RuleError("missing ')'", self.rule, self.position())
            self.take()
            return node
        if current in ("&", "|", ")"):
            raise RuleError(f"unexpected {current!r}", self.rule, self.position())
        text, position = self.take()
        return _make_token(text, self.rule, position)


def parse(rule: str) -> Node:
    """Parse a rule string into a tree, or raise RuleError."""
    if not isinstance(rule, str):
        raise TypeError("a rule is a string")
    return _Parser(rule).parse()


def _flatten(node: Node) -> Node:
    if isinstance(node, Not):
        return Not(_flatten(node.child))
    if isinstance(node, (And, Or)):
        kind = type(node)
        children = []
        for child in (_flatten(c) for c in node.children):
            if isinstance(child, kind):
                children.extend(child.children)
            else:
                children.append(child)
        return kind(tuple(children))
    return node


def render(node: Node) -> str:
    """Render a tree in the canonical spelling: single spaces, minimal brackets."""
    node = _flatten(node)
    if isinstance(node, Tok):
        return node.render()
    if isinstance(node, Not):
        inner = render(node.child)
        return f"!{inner}" if isinstance(_flatten(node.child), (Tok, Not)) else f"!({inner})"
    if isinstance(node, And):
        return " & ".join(f"({render(c)})" if isinstance(c, Or) else render(c) for c in node.children)
    return " | ".join(f"({render(c)})" if isinstance(c, And) else render(c) for c in node.children)


def normalize(rule: str) -> str:
    """The canonical spelling of a rule; equal meaning in form gives equal text."""
    return render(parse(rule))


def tokens(node: Node) -> FrozenSet[Tok]:
    """Every token a rule mentions."""
    if isinstance(node, Tok):
        return frozenset({node})
    if isinstance(node, Not):
        return tokens(node.child)
    out = set()
    for child in node.children:
        out |= tokens(child)
    return frozenset(out)


Resolver = Callable[[Tok], Tuple[Tri, FrozenSet[str]]]
_EMPTY: FrozenSet[str] = frozenset()


def evaluate(node: Node, resolve: Resolver) -> Tuple[Tri, FrozenSet[str]]:
    """Evaluate a tree with three-valued logic.

    Returns the truth value and, when it is UNKNOWN, the fact keys whose
    answers could still change it. A FALSE or TRUE result carries no keys.
    """
    if isinstance(node, Tok):
        value, missing = resolve(node)
        if not isinstance(value, Tri):
            raise TypeError("a resolver returns a Tri")
        return value, (frozenset(missing) if value is Tri.UNKNOWN else _EMPTY)
    if isinstance(node, Not):
        value, missing = evaluate(node.child, resolve)
        return ~value, missing
    results = [evaluate(child, resolve) for child in node.children]
    value = Tri.TRUE if isinstance(node, And) else Tri.FALSE
    for child_value, _ in results:
        value = (value & child_value) if isinstance(node, And) else (value | child_value)
    if value is not Tri.UNKNOWN:
        return value, _EMPTY
    missing = set()
    for child_value, child_missing in results:
        if child_value is Tri.UNKNOWN:
            missing |= child_missing
    return value, frozenset(missing)


def compile_rule(rule: str) -> Tuple[Node, str]:
    """Parse and return the tree with its canonical spelling."""
    node = parse(rule)
    return node, render(node)


def token_names(rules: Iterable[str]) -> FrozenSet[str]:
    names = set()
    for rule in rules:
        names |= {t.name for t in tokens(parse(rule))}
    return frozenset(names)
