"""Three-valued logic and the rule language."""
from __future__ import annotations

import itertools

import pytest

from app.domains.vault import rules
from app.domains.vault.facts import TOKEN_FACTS, FactSet, resolver
from app.domains.vault.rules import RuleError, Tok, evaluate, normalize, parse, render, tokens
from app.domains.vault.tri import Tri, all_of, any_of

T, U, F = Tri.TRUE, Tri.UNKNOWN, Tri.FALSE


@pytest.mark.parametrize("a,b,expected", [
    (T, T, T), (T, U, U), (T, F, F), (U, T, U), (U, U, U), (U, F, F), (F, T, F), (F, U, F), (F, F, F)])
def test_and_truth_table(a, b, expected):
    assert (a & b) is expected


@pytest.mark.parametrize("a,b,expected", [
    (T, T, T), (T, U, T), (T, F, T), (U, T, T), (U, U, U), (U, F, U), (F, T, T), (F, U, U), (F, F, F)])
def test_or_truth_table(a, b, expected):
    assert (a | b) is expected


def test_not_and_helpers():
    assert ~T is F and ~F is T and ~U is U
    assert all_of([]) is T and any_of([]) is F
    assert all_of([T, U]) is U and any_of([F, U]) is U
    with pytest.raises(TypeError):
        bool(U)
    with pytest.raises(TypeError):
        Tri.of(1)


def test_precedence_and_canonical_form():
    assert normalize("res & vet | ss") == "(res & vet) | ss"
    assert normalize("res&((vet&r>=100)|ss)") == "res & ((vet & r>=100) | ss)"
    assert normalize("!(sm | vet)") == "!(sm | vet)"
    assert normalize("((sm))") == "sm"
    assert normalize("sm & (vet & hon)") == "sm & vet & hon"
    for text in ("res & !stn & sm", "age>=16 & age<26 & ch", "spr>=50 | spsc", "true"):
        once = normalize(text)
        assert normalize(once) == once
        assert render(parse(once)) == render(parse(text))


@pytest.mark.parametrize("bad", [
    "", "   ", "res &", "& res", "(res", "res)", "res vet", "rez", "r>=", "r>=101", "r<10", "days>=0",
    "age", "sm>=1", "res | | vet", "res,vet", "*", "RES"])
def test_bad_rules_are_refused(bad):
    with pytest.raises(RuleError):
        parse(bad)


def test_rule_error_reports_position():
    with pytest.raises(RuleError) as info:
        parse("res & bogus")
    assert info.value.position == 6
    assert "bogus" in str(info.value)


def test_tokens_and_missing_keys():
    node = parse("res & ((vet & r>=100) | ss)")
    assert {t.render() for t in tokens(node)} == {"res", "vet", "r>=100", "ss"}
    facts = FactSet.from_mapping({"residence_state": "TX", "relationship": "self"})
    value, missing = evaluate(node, resolver(facts, "TX"))
    assert value is U
    assert missing == {"service_status", "va_rating"}
    facts = FactSet.from_mapping({"residence_state": "TX", "relationship": "self", "service_status": "serving"})
    value, missing = evaluate(node, resolver(facts, "TX"))
    assert value is F and missing == frozenset()


def test_false_short_circuits_missing_keys():
    facts = FactSet.from_mapping({"residence_state": "AL"})
    value, missing = evaluate(parse("res & vet & r>=50"), resolver(facts, "TX"))
    assert value is F and missing == frozenset()


def test_every_token_has_facts_and_a_resolver():
    assert set(TOKEN_FACTS) == set(rules.TOKEN_NAMES)
    empty = FactSet()
    for name in rules.PLAIN_TOKENS:
        value, _ = resolver(empty, "TX")(Tok(name))
        assert value in (T, U), name
    for name, (ops, low, high, _) in rules.PARAM_TOKENS.items():
        op = ">=" if ">=" in ops else "<"
        value, missing = resolver(empty, "TX")(Tok(name, op, max(low, 1)))
        assert value is U and missing


def test_every_registry_rule_is_canonical(registry):
    for benefit in registry.benefits.values():
        assert normalize(benefit.rule) == benefit.rule


def test_evaluate_matches_brute_force_kleene():
    """The evaluator agrees with a truth-table oracle on random small trees."""
    names = ["sm", "vet", "ss"]
    keys = {"sm": "service_status", "vet": "service_status", "ss": "relationship"}
    texts = ["sm | vet", "sm & !vet", "!(sm & ss) | vet", "(sm | ss) & (vet | !ss)"]
    for text in texts:
        node = parse(text)
        for combo in itertools.product((T, U, F), repeat=len(names)):
            table = dict(zip(names, combo))

            def resolve(tok, table=table):
                value = table[tok.name]
                return value, (frozenset({keys[tok.name]}) if value is U else frozenset())

            def oracle(n):
                if isinstance(n, rules.Tok):
                    return table[n.name]
                if isinstance(n, rules.Not):
                    return ~oracle(n.child)
                values = [oracle(c) for c in n.children]
                return all_of(values) if isinstance(n, rules.And) else any_of(values)

            assert evaluate(node, resolve)[0] is oracle(node)
