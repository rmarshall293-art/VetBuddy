"""Governance: manifests, grants, context packets, the pull ledger, the broker and egress."""
from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest

from app.domains.vault import VAULT_AGENT_ID
from app.domains.vault.canonical import GENESIS_HASH
from app.domains.vault.governance.broker import PullBroker, PullRequest
from app.domains.vault.governance.egress import EgressBlocked, EgressGuard
from app.domains.vault.governance.grants import GrantError, MemoryGrantStore, consent_text, new_grant
from app.domains.vault.governance.ledger import LedgerError, MemoryLedger, verify_chain
from app.domains.vault.governance.manifests import Exposure, Manifest, ManifestError, ManifestSet
from app.domains.vault.governance.packets import INVARIANTS, PacketError, forward, open_packet, seal
from app.domains.vault.guards import CitationValidator

from vault_support import NOW

TENANT = "0f6c7e1e-1111-4222-8333-444455556666"
PROFILE = "service_profile_agent"


@pytest.fixture()
def manifests(registry):
    return ManifestSet.from_registry(registry)


@pytest.fixture()
def gov(registry):
    return registry.governance


def grant(manifests, gov, keys=("service_status", "component"), mode="B", **kw):
    return new_grant(manifests, gov, tenant_ref=TENANT, source_agent=kw.pop("source", PROFILE), fact_keys=keys,
                     purpose=kw.pop("purpose", "benefit_matching"), mode=mode, now=kw.pop("now", NOW), **kw)


# ── manifests ─────────────────────────────────────────────────────────────

def test_registry_manifests_load(manifests):
    vault = manifests.get(VAULT_AGENT_ID)
    assert vault.may_pull_from_agents and not vault.exposes
    assert all(not m.may_issue_determinations for m in manifests.all())
    assert [m.agent_id for m in manifests.all() if m.may_pull_from_agents] == [VAULT_AGENT_ID]
    assert manifests.sources_for("va_rating") == ["va_status_agent"]
    assert manifests.sources_for("severe_disability") == []
    assert manifests.get("crisis_support_agent").exposes == ()


def base_items(registry):
    return [dict(a, exposes=[dict(e) for e in a["exposes"]]) for a in registry.agents]


@pytest.mark.parametrize("change", [
    lambda items: items[0].update(may_issue_determinations=True),
    lambda items: next(i for i in items if i["agent_id"] == "household_agent").update(may_pull_from_agents=True),
    lambda items: next(i for i in items if i["agent_id"] == VAULT_AGENT_ID).update(may_pull_from_agents=False),
    lambda items: next(i for i in items if i["agent_id"] == "va_status_agent")["exposes"].append(
        {"fact_key": "severe_disability", "data_class": "V4"}),
    lambda items: next(i for i in items if i["agent_id"] == "household_agent")["exposes"].append(
        {"fact_key": "va_rating", "data_class": "V1"}),
    lambda items: next(i for i in items if i["agent_id"] == VAULT_AGENT_ID)["exposes"].append(
        {"fact_key": "age", "data_class": "V1"}),
    lambda items: next(i for i in items if i["agent_id"] == "household_agent").update(highest_class_held="V1"),
    lambda items: items.append(dict(items[0])),
])
def test_manifest_pins(registry, change):
    items = base_items(registry)
    change(items)
    with pytest.raises(ManifestError):
        ManifestSet(items)


# ── grants ────────────────────────────────────────────────────────────────

def test_grant_is_scoped_and_expires(manifests, gov):
    g = grant(manifests, gov)
    assert g.grantee == VAULT_AGENT_ID and g.scope == "account" and g.purpose == "benefit_matching"
    assert g.expires_at - g.granted_at == timedelta(days=gov["grants"]["default_days"])
    assert g.active(NOW) and not g.active(g.expires_at) and g.state(g.expires_at) == "EXPIRED"
    session = grant(manifests, gov, mode="A", hours=2)
    assert session.scope == "session" and session.expires_at - session.granted_at == timedelta(hours=2)


@pytest.mark.parametrize("kwargs,reason", [
    ({"source": "nobody_agent"}, "NO_MANIFEST"),
    ({"source": VAULT_AGENT_ID}, "NOT_EXPOSED"),
    ({"keys": ("va_rating",)}, "NOT_EXPOSED"),
    ({"keys": ("discharge",), "mode": "A"}, "CLASS_ABOVE_MODE_CEILING"),
    ({"keys": ()}, "KEY_NOT_GRANTED"),
    ({"purpose": "marketing"}, "PURPOSE_NOT_ALLOWED"),
    ({"mode": "C"}, "MODE_C_UNREACHABLE"),
    ({"days": 91}, "DURATION_NOT_ALLOWED"),
    ({"days": 0}, "DURATION_NOT_ALLOWED"),
    ({"mode": "A", "hours": 25}, "DURATION_NOT_ALLOWED"),
    ({"mode": "A", "days": 1}, "DURATION_NOT_ALLOWED"),
])
def test_grant_refusals(manifests, gov, kwargs, reason):
    with pytest.raises(GrantError) as info:
        grant(manifests, gov, **kwargs)
    assert info.value.reason == reason


def test_grant_store_revocation(manifests, gov):
    store = MemoryGrantStore()
    g = store.add(grant(manifests, gov))
    revoked = store.revoke(TENANT, g.grant_id, NOW + timedelta(minutes=5))
    assert revoked.state(NOW + timedelta(minutes=6)) == "REVOKED"
    assert store.revoke("someone-else", g.grant_id, NOW) is None
    assert store.for_source(TENANT, PROFILE, "benefit_matching")[0].revoked_at is not None


def test_consent_text_names_the_scope(manifests):
    text = consent_text(manifests, PROFILE, ["service_status", "component"], "30 days")
    assert "component, service_status" in text and "Service Profile" in text and "turn this off" in text


# ── packets ───────────────────────────────────────────────────────────────

def sealed(manifests, gov, values=None, **kw):
    g = grant(manifests, gov)
    packet = seal(grant=g, consumer=VAULT_AGENT_ID, values=values or {"service_status": "serving"}, now=NOW,
                  ttl_seconds=600)
    return g, packet


def open_(packet, g, **kw):
    args = dict(consumer=VAULT_AGENT_ID, tenant_ref=TENANT, grant=g, requested={"service_status", "component"},
                mode="B", now=NOW + timedelta(seconds=1), ttl_seconds=600)
    args.update(kw)
    return open_packet(packet, **args)


def test_packet_round_trip(manifests, gov):
    g, packet = sealed(manifests, gov)
    assert open_(packet, g) == {"service_status": "serving"}
    assert packet.transferable is False and len(INVARIANTS) == 7


def test_packet_invariants(manifests, gov):
    g, packet = sealed(manifests, gov)
    cases = [
        ("ADDRESSED", dict(consumer="household_agent")),
        ("ADDRESSED", dict(tenant_ref="7a1d2c3b-aaaa-4bbb-8ccc-ddddeeeeffff")),
        ("PURPOSE_BOUND", dict(grant=replace(g, purpose="marketing"))),
        ("EXPIRING", dict(now=NOW + timedelta(seconds=601))),
        ("EXPIRING", dict(now=NOW - timedelta(seconds=1))),
        ("EXPIRING", dict(ttl_seconds=60)),
        ("MINIMUM_NECESSARY", dict(requested={"component"})),
        ("MINIMUM_NECESSARY", dict(grant=replace(g, fact_keys=frozenset({"component"})))),
        ("CLASS_CEILING", dict(mode="A")),
        ("NON_TRANSFERABLE", dict(grant=replace(g, grantee="household_agent"))),
    ]
    for invariant, kwargs in cases:
        with pytest.raises(PacketError) as info:
            open_(packet, g, **kwargs)
        assert info.value.invariant == invariant, (invariant, kwargs)
    tampered = replace(packet, facts=(("service_status", "retired", "V1"),))
    with pytest.raises(PacketError) as info:
        open_(tampered, g)
    assert info.value.invariant == "INTEGRITY"
    transferable = replace(packet, transferable=True)
    with pytest.raises(PacketError) as info:
        open_(transferable, g)
    assert info.value.invariant == "INTEGRITY"  # the flag is sealed into the hash too
    with pytest.raises(PacketError) as info:
        forward(packet, "household_agent")
    assert info.value.invariant == "NON_TRANSFERABLE"


def test_packet_class_ceiling_for_v2_in_mode_a(manifests, gov):
    g = grant(manifests, gov, keys=("discharge",))
    packet = seal(grant=g, consumer=VAULT_AGENT_ID, values={"discharge": "honorable"}, now=NOW, ttl_seconds=600)
    with pytest.raises(PacketError) as info:
        open_(packet, g, requested={"discharge"}, mode="A")
    assert info.value.invariant == "CLASS_CEILING"


# ── ledger ────────────────────────────────────────────────────────────────

def test_ledger_chain_and_tamper_detection():
    ledger = MemoryLedger()
    for i in range(3):
        ledger.append(tenant_ref=TENANT, occurred_at=NOW + timedelta(seconds=i), event="PULL_ALLOWED",
                      requester=VAULT_AGENT_ID, source_agent=PROFILE, purpose="benefit_matching",
                      fact_keys=["component", "service_status"], grant_id="g-1", packet_id=f"p-{i}")
    entries = ledger.entries(TENANT)
    assert entries[0].prev_hash == GENESIS_HASH and entries[1].prev_hash == entries[0].row_hash
    assert ledger.verify(TENANT) == (True, None)
    forged = list(entries)
    forged[1] = replace(forged[1], fact_keys=("va_rating",))
    assert verify_chain(forged) == (False, 2)
    dropped = [entries[0], entries[2]]
    assert verify_chain(dropped) == (False, 3)
    assert ledger.verify("another-tenant") == (True, None)


@pytest.mark.parametrize("fields", [
    dict(event="PULL_MAYBE"),
    dict(reason="BECAUSE"),
    dict(event="PULL_DENIED", reason="ALLOWED"),
    dict(event="PULL_ALLOWED", reason="NO_ACTIVE_GRANT"),
    dict(fact_keys=["va_rating=100"]),
    dict(source_agent="agent|with|pipes"),
    dict(packet_id="value: honorable"),
    dict(tenant_ref="tenant|x"),
])
def test_ledger_refuses_values_and_bad_codes(fields):
    args = dict(tenant_ref=TENANT, occurred_at=NOW, event="PULL_ALLOWED", requester=VAULT_AGENT_ID,
                source_agent=PROFILE, purpose="benefit_matching", fact_keys=["age"], reason="ALLOWED")
    args.update(fields)
    with pytest.raises(LedgerError):
        MemoryLedger().append(**args)


# ── broker ────────────────────────────────────────────────────────────────

class Provider:
    def __init__(self, values=None, fail=False):
        self.values = values or {}
        self.fail = fail
        self.calls = []

    def provide(self, tenant_ref, keys):
        self.calls.append((tenant_ref, frozenset(keys)))
        if self.fail:
            raise RuntimeError("source down")
        return dict(self.values)


def broker_with(manifests, gov, grants=(), provider=None):
    store = MemoryGrantStore()
    for g in grants:
        store.add(g)
    ledger = MemoryLedger()
    providers = {PROFILE: provider} if provider is not None else {}
    return PullBroker(manifests, store, ledger, providers, 600), store, ledger


def req(keys=("service_status", "component"), **kw):
    fields = dict(tenant_ref=TENANT, requester=VAULT_AGENT_ID, source_agent=PROFILE, fact_keys=frozenset(keys),
                  purpose="benefit_matching", mode="B", needed=frozenset({"service_status", "component", "discharge"}))
    fields.update(kw)
    return PullRequest(**fields)


def test_allowed_pull_delivers_only_granted_and_valid_values(manifests, gov):
    g = grant(manifests, gov, keys=("service_status", "component"))
    provider = Provider({"service_status": "serving", "component": "warp", "discharge": "honorable",
                         "secret_note": "never"})
    broker, _, ledger = broker_with(manifests, gov, [g], provider)
    decision = broker.request(req(), NOW)
    assert decision.allowed and decision.reason == "ALLOWED"
    assert decision.delivered == {"service_status"}        # "warp" is not a component; discharge not granted
    assert decision.packet.keys == {"service_status"}
    entry = ledger.entries(TENANT)[-1]
    assert entry.event == "PULL_ALLOWED" and entry.fact_keys == ("service_status",)
    assert "serving" not in repr(entry.view()) and "never" not in repr(entry.view())


@pytest.mark.parametrize("request_kwargs,reason", [
    (dict(mode="C"), "MODE_C_UNREACHABLE"),
    (dict(requester="household_agent"), "REQUESTER_NOT_PERMITTED"),
    (dict(requester="rogue|agent"), "REQUESTER_NOT_PERMITTED"),
    (dict(source_agent="unknown_agent"), "NO_MANIFEST"),
    (dict(purpose="advertising"), "PURPOSE_NOT_ALLOWED"),
    (dict(fact_keys=frozenset({"va_rating"})), "NOT_EXPOSED"),
    (dict(fact_keys=frozenset({"discharge"}), mode="A"), "CLASS_ABOVE_MODE_CEILING"),
    (dict(fact_keys=frozenset({"age"}), source_agent="household_agent", needed=frozenset({"service_status"})),
     "NOT_MINIMUM_NECESSARY"),
    (dict(fact_keys=frozenset()), "NOT_MINIMUM_NECESSARY"),
    (dict(fact_keys=frozenset({"discharge"})), "KEY_NOT_GRANTED"),
])
def test_denials_are_ledgered(manifests, gov, request_kwargs, reason):
    g = grant(manifests, gov, keys=("service_status", "component"))
    broker, _, ledger = broker_with(manifests, gov, [g], Provider({"service_status": "serving"}))
    decision = broker.request(req(**request_kwargs), NOW)
    assert not decision.allowed and decision.reason == reason and decision.packet is None
    entry = ledger.entries(TENANT)[-1]
    assert entry.event == "PULL_DENIED" and entry.reason == reason
    assert ledger.verify(TENANT) == (True, None)


def test_grant_state_denials(manifests, gov):
    broker, store, _ = broker_with(manifests, gov, [], Provider({"service_status": "serving"}))
    assert broker.request(req(), NOW).reason == "NO_ACTIVE_GRANT"
    g = store.add(grant(manifests, gov, days=1))
    assert broker.request(req(), NOW + timedelta(days=2)).reason == "GRANT_EXPIRED"
    store.revoke(TENANT, g.grant_id, NOW + timedelta(hours=1))
    assert broker.request(req(), NOW + timedelta(hours=2)).reason == "GRANT_REVOKED"


def test_source_failures_are_denials(manifests, gov):
    g = grant(manifests, gov)
    broker, _, _ = broker_with(manifests, gov, [g], None)
    assert broker.request(req(), NOW).reason == "SOURCE_UNAVAILABLE"
    broker, _, _ = broker_with(manifests, gov, [g], Provider(fail=True))
    assert broker.request(req(), NOW).reason == "SOURCE_UNAVAILABLE"


def test_never_pullable_class_is_refused_even_if_a_manifest_slipped(manifests, gov):
    """Defence in depth: a hand-built manifest exposing a V4 fact still cannot be pulled."""
    rogue = Manifest(agent_id="rogue_agent", name="Rogue", plane=2, role="test", may_pull_from_agents=False,
                     highest_class_held="V4", exposes=(Exposure("severe_disability", "V4"),))
    manifests._by_id["rogue_agent"] = rogue
    broker = PullBroker(manifests, MemoryGrantStore(), MemoryLedger(), {}, 600)
    decision = broker.request(req(source_agent="rogue_agent", fact_keys=frozenset({"severe_disability"}),
                                  needed=frozenset({"severe_disability"})), NOW)
    assert decision.reason == "CLASS_NEVER_PULLABLE"


def test_broker_needs_aware_time(manifests, gov):
    broker, _, _ = broker_with(manifests, gov)
    with pytest.raises(ValueError):
        broker.request(req(), NOW.replace(tzinfo=None))


# ── egress ────────────────────────────────────────────────────────────────

def test_egress_allowlist(registry):
    egress = EgressGuard.from_registry(registry)
    assert egress.allowed("https://www.va.gov/education/about-gi-bill-benefits/post-9-11/")
    for url in ("http://www.va.gov/", "https://evil.example.com/", "https://user:pw@www.va.gov/",
                "https://www.va.gov:8443/", "ftp://www.va.gov/", ""):
        assert not egress.allowed(url)
    with pytest.raises(EgressBlocked) as info:
        egress.check_url("https://evil.example.com/")
    assert info.value.reason == "HOST_NOT_ALLOWED"
    # A link can be shown exactly when it could be fetched.
    citations = CitationValidator(registry.governance["egress_allowlist"])
    for url in ("https://www.va.gov/", "https://WWW.VA.GOV/x", "https://www.va.gov:443/x", "http://www.va.gov/",
                "https://user:pw@www.va.gov/", "https://www.va.gov:8443/", "https://www.va.gov:abc/", "https://[::1",
                "https://evil.example.com/?u=https://www.va.gov/", "", None):
        assert citations.ok(url) == egress.allowed(url), url


def test_discovery_queries_use_only_v0_vocabulary(registry):
    egress = EgressGuard.from_registry(registry)
    query = egress.build_query("jur_cat_vet", jurisdiction="Alabama", category="state parks")
    assert query == "Alabama state parks for veterans"
    for bad in (dict(jurisdiction="Alabama", category="my 70% rating"),
                dict(jurisdiction="John Smith", category="state parks"),
                dict(jurisdiction="Alabama")):
        with pytest.raises(EgressBlocked):
            egress.build_query("jur_cat_vet", **bad)
    with pytest.raises(EgressBlocked):
        egress.build_query("free_text", jurisdiction="Alabama", category="state parks")
    with pytest.raises(ValueError):
        EgressGuard(["www.va.gov"], {"leak": "{jurisdiction} {ssn}"})
