"""Alabama benefits, training, and ranking tests."""

from app.tests.conftest import API


def test_alabama_benefits(client):
    response = client.get(f"{API}/alabama/benefits")
    assert response.status_code == 200
    body = response.json()
    assert body["jurisdiction"] == "AL"
    assert body["placeholder_warning"] is True
    assert isinstance(body["benefits"], list)


def test_resource_officer_training(client):
    response = client.get(f"{API}/alabama/resource-officer-training")
    assert response.status_code == 200
    body = response.json()
    assert body["jurisdiction"] == "AL"
    assert "levels" in body
    assert "level_1" in body["levels"]
    assert len(body["levels"]["level_1"]["modules"]) >= 3


def test_county_offices(client):
    response = client.get(f"{API}/alabama/county-offices")
    assert response.status_code == 200
    body = response.json()
    assert body["jurisdiction"] == "AL"
    assert isinstance(body["offices"], list)
    assert len(body["offices"]) >= 1


def test_alabama_ranking(client):
    response = client.get(f"{API}/alabama/ranking")
    assert response.status_code == 200
    body = response.json()
    assert body["jurisdiction"] == "AL"
    assert body["placeholder_warning"] is True
    assert len(body["metrics"]) >= 1
