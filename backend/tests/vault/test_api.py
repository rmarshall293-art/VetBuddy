"""The Starlette routes under /api/v1/vault."""
from __future__ import annotations

import uuid

import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient

from app.domains.vault.agent import BenefitVaultAgent
from app.domains.vault.api import PREFIX, routes
from app.domains.vault.governance.grants import MemoryGrantStore
from app.domains.vault.governance.ledger import MemoryLedger

from vault_support import AS_OF, NOW, TENANT_A


class AccountStore:
    """In-memory stand-in for VaultStore (grants, ledger and saved benefits)."""

    def __init__(self):
        self.grants = MemoryGrantStore()
        self.ledger = MemoryLedger()
        self.rows = {}

    # grants
    def add(self, grant):
        return self.grants.add(grant)

    def revoke(self, tenant_ref, grant_id, now):
        return self.grants.revoke(tenant_ref, grant_id, now)

    def for_source(self, *args):
        return self.grants.for_source(*args)

    def list(self, tenant_ref):
        return self.grants.list(tenant_ref)

    # ledger
    def append(self, **fields):
        return self.ledger.append(**fields)

    def entries(self, tenant_ref):
        return self.ledger.entries(tenant_ref)

    def verify(self, tenant_ref):
        return self.ledger.verify(tenant_ref)

    # saved
    def save(self, tenant_ref, benefit_id, status, content_hash):
        row = self.rows.get(benefit_id) or {"saved_id": str(uuid.uuid4()), "benefit_id": benefit_id,
                                            "content_hash_at_save": content_hash, "saved_at": NOW.isoformat()}
        row.update(status=status, updated_at=NOW.isoformat())
        self.rows[benefit_id] = row
        return dict(row)

    def saved(self, tenant_ref):
        return [dict(r) for r in self.rows.values()]

    def discard(self, tenant_ref, kind, item_id):
        for key, row in list(self.rows.items()):
            if row["saved_id"] == item_id:
                del self.rows[key]
                return True
        return False


@pytest.fixture(scope="module")
def client(registry):
    agent = BenefitVaultAgent(registry, environment="development")
    stores = {}

    def resolver(request):
        return request.headers.get("x-test-tenant")

    def factory(tenant):
        return stores.setdefault(tenant, AccountStore())

    app = Starlette(routes=routes(agent, resolver=resolver, store_factory=factory, clock=lambda: NOW))
    return TestClient(app)


@pytest.fixture(scope="module")
def guest_only(registry):
    agent = BenefitVaultAgent(registry, environment="production")
    return TestClient(Starlette(routes=routes(agent, clock=lambda: NOW)))


AUTH = {"x-test-tenant": TENANT_A}


def test_catalog(client):
    body = client.get(f"{PREFIX}/catalog").json()
    assert body["counts"]["benefits"] == 1362 and body["publish_policy"] == "preview_unverified"
    assert body["governing_sentence"].startswith("Agents orchestrate")
    assert next(j for j in body["jurisdictions"] if j["code"] == "AS")["coverage"] == "SOURCE_NOT_AVAILABLE"
    assert body["rule_tokens"]["spkia"] == "the sponsor died in the line of duty"
    assert set(body["parametric_tokens"]) == {"r", "spr", "days", "age"}


def test_search_and_read(client):
    body = client.get(f"{PREFIX}/benefits", params={"q": "hunting", "jurisdiction": "AL,GA", "limit": 5}).json()
    assert body["kind"] == "search" and len(body["items"]) == 5
    assert {i["jurisdiction"] for i in body["items"]} <= {"AL", "GA"}
    detail = client.get(f"{PREFIX}/benefits/us.fry-scholarship").json()
    assert detail["item"]["benefit_id"] == "us.fry-scholarship"
    assert client.get(f"{PREFIX}/benefits/us.missing").status_code == 404
    assert client.get(f"{PREFIX}/benefits", params={"limit": "500"}).status_code == 422
    assert client.get(f"{PREFIX}/benefits", params={"category": "NOPE"}).status_code == 422


def test_match_as_guest_in_production(guest_only):
    response = guest_only.post(f"{PREFIX}/match", json={"facts": {"residence_state": "TX", "va_rating": 100,
                                                                  "service_status": "separated"}, "as_of": AS_OF})
    body = response.json()
    assert response.status_code == 200 and body["mode"] == "A" and body["publish_policy"] == "verified_only"
    assert body["counts"]["PRELIMINARY_MATCH"] == 0
    assert "va_rating" in body["subject"]["facts_not_used_in_this_mode"]


def test_match_errors(client):
    assert client.post(f"{PREFIX}/match", json={"facts": {"va_rating": 55}}).status_code == 422
    assert client.post(f"{PREFIX}/match", content=b"not json").status_code == 422
    assert client.post(f"{PREFIX}/match", json=[1, 2]).status_code == 422
    assert client.post(f"{PREFIX}/match", content=b"{" + b" " * 70000 + b"}").status_code == 422


def test_household_route(client):
    body = client.post(f"{PREFIX}/household", headers=AUTH, json={
        "facts": {"residence_state": "VA", "service_status": "separated", "va_rating": 100},
        "members": [{"member_id": "s", "relationship": "spouse"}], "as_of": AS_OF}).json()
    assert body["kind"] == "household" and body["mode"] == "B"
    ids = {i["benefit_id"] for i in body["members"][0]["items"]}
    assert any(i.startswith("va.virginia-military-survivors") for i in ids)


def test_governance_route_shows_the_pins(client):
    body = client.get(f"{PREFIX}/governance").json()
    agents = {a["agent_id"]: a for a in body["agents"]}
    assert all(a["may_issue_determinations"] is False for a in agents.values())
    assert [a for a, m in agents.items() if m["may_pull_from_agents"]] == ["benefit_vault_agent"]
    assert body["mode_ceiling"] == {"A": "V1", "B": "V2"} and body["never_pullable"] == ["V3", "V4", "V5"]


def test_leads_and_discovery(client):
    leads = client.get(f"{PREFIX}/leads").json()
    assert len(leads["recovered_leads"]) == 23 and len(leads["rule_leads"]) == 9
    plan = client.get(f"{PREFIX}/discovery/plan", params={"limit": 5}).json()
    assert plan["executable"] is False and plan["tasks"][0]["jurisdiction"] == "AS"
    assert plan["tasks"][0]["query"] == "American Samoa other benefits for veterans"


def test_account_routes_need_sign_in(guest_only):
    for method, path in (("get", "/grants"), ("post", "/grants"), ("get", "/ledger"), ("get", "/saved"),
                         ("post", "/saved"), ("post", "/grants/x/revoke"), ("post", "/saved/x/discard")):
        url = f"{PREFIX}{path}"
        response = guest_only.post(url, json={}) if method == "post" else guest_only.get(url)
        assert response.status_code == 403, path
        assert "G17" in response.json()["error"]["message"]


def test_grant_lifecycle_over_http(client):
    payload = {"source_agent": "va_status_agent", "fact_keys": ["va_rating"]}
    first = client.post(f"{PREFIX}/grants", headers=AUTH, json=payload)
    assert first.status_code == 409 and "VA Status" in first.json()["error"]["consent_text"]
    made = client.post(f"{PREFIX}/grants", headers=AUTH, json={**payload, "confirm": True}).json()
    grant_id = made["grant"]["grant_id"]
    assert client.get(f"{PREFIX}/grants", headers=AUTH).json()["grants"][0]["state"] == "ACTIVE"
    assert client.post(f"{PREFIX}/grants/{grant_id}/revoke", headers=AUTH).json()["grant"]["state"] == "REVOKED"
    assert client.post(f"{PREFIX}/grants/nope/revoke", headers=AUTH).status_code == 404
    bad = client.post(f"{PREFIX}/grants", headers=AUTH, json={"source_agent": "va_status_agent",
                                                              "fact_keys": ["discharge"], "confirm": True})
    assert bad.status_code == 422 and "NOT_EXPOSED" in bad.json()["error"]["message"]
    ledger = client.get(f"{PREFIX}/ledger", headers=AUTH).json()
    assert ledger["chain_ok"] and [e["event"] for e in ledger["entries"]] == ["GRANT_CREATED", "GRANT_REVOKED"]


def test_saved_benefits_over_http(client):
    assert client.post(f"{PREFIX}/saved", headers=AUTH, json={"benefit_id": "us.fry-scholarship"}).status_code == 409
    saved = client.post(f"{PREFIX}/saved", headers=AUTH,
                        json={"benefit_id": "us.fry-scholarship", "status": "GATHERING_DOCUMENTS", "confirm": True})
    assert saved.status_code == 200
    rows = client.get(f"{PREFIX}/saved", headers=AUTH).json()["saved"]
    assert rows[0]["title"] == "Fry Scholarship" and rows[0]["changed_since_saved"] is False
    assert client.post(f"{PREFIX}/saved", headers=AUTH,
                       json={"benefit_id": "us.fry-scholarship", "status": "DONE", "confirm": True}).status_code == 422
    saved_id = rows[0]["saved_id"]
    assert client.post(f"{PREFIX}/saved/{saved_id}/discard", headers=AUTH, json={}).status_code == 409
    removed = client.post(f"{PREFIX}/saved/{saved_id}/discard", headers=AUTH, json={"confirm": True}).json()
    assert removed == {"removed": True}
