"""State comparison endpoint tests."""

from app.tests.conftest import API


def test_list_states(client, seeded_jurisdictions):
    response = client.get(f"{API}/states")
    assert response.status_code == 200
    states = response.json()
    assert len(states) >= 5
    codes = {s["code"] for s in states}
    for required in ("AL", "TX", "FL", "DC", "PR"):
        assert required in codes


def test_compare_states(client, seeded_jurisdictions):
    response = client.get(f"{API}/states/compare", params={"from": "AL", "to": "TX"})
    assert response.status_code == 200
    body = response.json()
    assert body["from_jurisdiction"]["code"] == "AL"
    assert body["to_jurisdiction"]["code"] == "TX"
    assert "metrics" in body
    assert body["placeholder_warning"] is True
    assert "va_disability_tax_rule" in body["metrics"]


def test_get_state_by_code(client, seeded_jurisdictions):
    response = client.get(f"{API}/states/AL")
    assert response.status_code == 200
    assert response.json()["name"] == "Alabama"


def test_custom_compare_save_requires_auth(client, seeded_jurisdictions):
    response = client.post(
        f"{API}/states/compare/custom",
        json={"from_code": "AL", "to_code": "FL", "save": True, "label": "AL vs FL"},
    )
    assert response.status_code == 401


def test_custom_compare_save_authenticated(client, veteran_headers, seeded_jurisdictions):
    response = client.post(
        f"{API}/states/compare/custom",
        headers=veteran_headers,
        json={
            "from_code": "AL",
            "to_code": "FL",
            "save": True,
            "label": "AL vs FL",
            "metrics": ["va_disability_tax_rule", "ranking_score"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "saved_id" in body
    assert body["metrics"]["va_disability_tax_rule"]["from"] is not None
