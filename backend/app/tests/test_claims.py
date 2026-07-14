"""Claims CRUD and evidence tests."""

from app.tests.conftest import API


def test_claims_crud(client, veteran_headers):
    create = client.post(
        f"{API}/claims",
        headers=veteran_headers,
        json={
            "title": "PTSD claim",
            "claim_type": "disability",
            "status": "draft",
            "disclaimer_acknowledged": True,
            "conditions": [
                {
                    "condition_name": "PTSD",
                    "current_diagnosis": "Chronic PTSD",
                    "claimed_rating": 70,
                }
            ],
        },
    )
    assert create.status_code == 201
    claim = create.json()
    claim_id = claim["id"]
    assert claim["title"] == "PTSD claim"
    assert len(claim["conditions"]) == 1
    assert claim["evidence_strength_score"] is not None

    listing = client.get(f"{API}/claims", headers=veteran_headers)
    assert listing.status_code == 200
    assert any(c["id"] == claim_id for c in listing.json())

    get_one = client.get(f"{API}/claims/{claim_id}", headers=veteran_headers)
    assert get_one.status_code == 200

    updated = client.patch(
        f"{API}/claims/{claim_id}",
        headers=veteran_headers,
        json={"status": "in_progress", "notes": "Gathering buddy statements"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "in_progress"

    deleted = client.delete(f"{API}/claims/{claim_id}", headers=veteran_headers)
    assert deleted.status_code == 200

    gone = client.get(f"{API}/claims/{claim_id}", headers=veteran_headers)
    assert gone.status_code == 404


def test_evidence_on_claim(client, veteran_headers):
    claim = client.post(
        f"{API}/claims",
        headers=veteran_headers,
        json={"title": "Tinnitus claim", "disclaimer_acknowledged": True},
    ).json()
    claim_id = claim["id"]

    evidence = client.post(
        f"{API}/claims/{claim_id}/evidence",
        headers=veteran_headers,
        json={
            "evidence_type": "medical_records",
            "title": "Service treatment records",
            "status": "uploaded",
            "checklist_item": "medical_records",
            "strength_weight": "2.0",
        },
    )
    assert evidence.status_code == 201
    ev_id = evidence.json()["id"]

    listed = client.get(f"{API}/claims/{claim_id}/evidence", headers=veteran_headers)
    assert listed.status_code == 200
    assert any(e["id"] == ev_id for e in listed.json())

    refreshed = client.get(f"{API}/claims/{claim_id}", headers=veteran_headers)
    assert refreshed.status_code == 200
    assert float(refreshed.json()["evidence_strength_score"]) > 0


def test_claim_isolation_between_users(client, veteran_headers, admin_headers, db):
    from app.tests.conftest import create_user

    create_user(db, email="other@example.com")
    db.commit()

    claim = client.post(
        f"{API}/claims",
        headers=veteran_headers,
        json={"title": "Private claim", "disclaimer_acknowledged": True},
    ).json()

    # Admin without ownership should not see veteran's claim
    forbidden = client.get(f"{API}/claims/{claim['id']}", headers=admin_headers)
    assert forbidden.status_code == 404
