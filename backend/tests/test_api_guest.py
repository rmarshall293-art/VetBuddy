"""Guest mode (Privacy Mode A) over HTTP: answers without storing anything."""

from conftest import GUARD_PROFILE, table_counts


def test_health_without_database(guest_client):
    assert guest_client.get("/api/v1/health/live").json() == {"status": "ok"}
    r = guest_client.get("/api/v1/health/ready").json()
    assert r["database"] == "not_configured" and r["model_gateway"] == "not_present" and r["sign_in"] == "off"


def test_evaluate_returns_brief(guest_client):
    r = guest_client.post("/api/v1/mission-router/evaluate", json=GUARD_PROFILE)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["stage"] == "t_12_6m" and body["privacy_mode"] == "A" and body["stored"] is False
    assert body["tasks"][0]["template_id"] in ("DOC-01", "GR-AUTH")
    assert "not VA" in body["disclosure"] and r.headers["X-VetBuddy-Notice"]
    assert r.headers["Cache-Control"] == "no-store"


def test_ssn_or_any_unknown_field_is_refused(guest_client):
    for extra in ({"ssn": "000-00-0000"}, {"ssn_last4": "0000"}, {"diagnosis": "x"}, {"name": "Synthetic"}):
        r = guest_client.post("/api/v1/mission-router/evaluate", json={**GUARD_PROFILE, **extra})
        assert r.status_code == 422
        err = r.json()["error"]
        assert err["code"] == "INVALID_INPUT" and len(err["trace_id"]) == 32
        assert "000-00-0000" not in r.text


def test_invalid_value_is_422_with_field(guest_client):
    r = guest_client.post("/api/v1/mission-router/evaluate", json={**GUARD_PROFILE, "current_jurisdiction": "ZZ"})
    assert r.status_code == 422 and "current_jurisdiction" in r.json()["error"]["message"]


def test_ratings_endpoint(guest_client):
    r = guest_client.post("/api/v1/ratings/combine", json={"ratings": [60, 40, 20]}).json()
    assert r["combined_rating"] == 80 and r["educational_only"] is True and "accredited" in r["vso_referral"]
    assert guest_client.post("/api/v1/ratings/combine", json={"ratings": [15]}).status_code == 422


def test_crisis_and_jurisdictions(guest_client):
    c = guest_client.get("/api/v1/crisis-resources").json()
    assert c["contacts"][0]["phone"] == "988" and c["contacts"][0]["text"] == "838255"
    j = guest_client.get("/api/v1/jurisdictions").json()
    assert j["total"] == 57 and j["verified"] == 0


def test_private_routes_need_sign_in_even_without_db(guest_client):
    assert guest_client.get("/api/v1/users/me").status_code == 401
    assert guest_client.post("/api/v1/dev/token", json={"subject": "x"}).status_code == 404


def test_guest_preview_writes_nothing(client, owner):
    before = table_counts(owner)
    for _ in range(3):
        assert client.post("/api/v1/mission-router/evaluate", json=GUARD_PROFILE).status_code == 200
        client.post("/api/v1/ratings/combine", json={"ratings": [50, 30]})
    assert table_counts(owner) == before


def test_unknown_route_uses_error_contract(guest_client):
    r = guest_client.get("/api/v1/nope")
    assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND"
