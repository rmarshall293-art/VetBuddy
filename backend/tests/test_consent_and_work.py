"""Consent gates storage; revocation is immediate; tasks persist with versioning."""

import psycopg
import pytest

from conftest import GUARD_PROFILE, VETERAN_PROFILE, table_counts


def test_no_consent_means_nothing_stored(make_user, owner):
    u = make_user()
    before = table_counts(owner)
    r = u.post("/api/v1/missions", json=GUARD_PROFILE)
    assert r.status_code == 409 and r.json()["error"]["code"] == "CONSENT_REQUIRED"
    after = table_counts(owner)
    assert {k: v for k, v in after.items() if k != "users"} == {k: v for k, v in before.items() if k != "users"}


def test_mission_case_tasks_persist_and_brief_reads_back(make_user, owner):
    u = make_user().consent()
    r = u.post("/api/v1/missions", json=GUARD_PROFILE)
    assert r.status_code == 201, r.text
    b = r.json()
    assert b["privacy_mode"] == "B" and b["stage"] == "t_12_6m" and b["facts"]["source"] == "DECLARED"
    assert len(b["first_five_actions"]) == 5 and "guard_reserve" in b["lanes"]
    got = u.get(f"/api/v1/missions/{b['mission_id']}").json()
    assert got["input_hash"] == b["input_hash"] and [t["id"] for t in got["tasks"]] == [t["id"] for t in b["tasks"]]
    assert u.get(f"/api/v1/cases/{b['case_id']}").json()["lanes"] == b["lanes"]
    nxt = u.get(f"/api/v1/missions/{b['mission_id']}/next-action").json()["next_action"]
    assert nxt["id"] == b["tasks"][0]["id"]
    events = [r[0] for r in owner.execute(
        "SELECT event_type FROM vb.outbox WHERE aggregate_id IN (%s, %s) ORDER BY created_at",
        (b["mission_id"], b["case_id"])).fetchall()]
    assert sorted(events) == ["CASE_CREATED", "MISSION_CREATED"]


def test_task_status_with_optimistic_concurrency(make_user):
    u = make_user().consent()
    b = u.post("/api/v1/missions", json=VETERAN_PROFILE).json()
    t = b["tasks"][0]
    ok = u.patch(f"/api/v1/tasks/{t['id']}", json={"status": "done", "expected_version": 1})
    assert ok.status_code == 200 and ok.json()["version"] == 2
    stale = u.patch(f"/api/v1/tasks/{t['id']}", json={"status": "todo", "expected_version": 1})
    assert stale.status_code == 409 and stale.json()["error"]["code"] == "VERSION_CONFLICT"
    brief = u.get(f"/api/v1/missions/{b['mission_id']}").json()
    assert t["id"] not in [x["id"] for x in brief["first_five_actions"]]
    dim = next(d for d in brief["readiness"] if d["dimension"] == t["readiness_dimension"])
    assert dim["done"] >= 1
    assert u.patch(f"/api/v1/tasks/{t['id']}", json={"status": "archived", "expected_version": 2}).status_code == 422


def test_revocation_hides_data_immediately_and_regrant_restores(make_user):
    u = make_user().consent()
    b = u.post("/api/v1/missions", json=GUARD_PROFILE).json()
    assert u.delete("/api/v1/consents/plan_storage").json()["missions_deleted"] == 0
    assert u.get(f"/api/v1/missions/{b['mission_id']}").status_code == 404
    assert u.get("/api/v1/missions").json()["missions"] == []
    assert u.post("/api/v1/missions", json=GUARD_PROFILE).status_code == 409
    u.consent()
    assert u.get(f"/api/v1/missions/{b['mission_id']}").status_code == 200


def test_revoke_and_delete_removes_everything(make_user, owner):
    u = make_user().consent()
    b = u.post("/api/v1/missions", json=GUARD_PROFILE).json()
    r = u.delete("/api/v1/consents/plan_storage", params={"delete_data": "true"}).json()
    assert r["missions_deleted"] == 1
    for t, col, val in (("missions", "id", b["mission_id"]), ("master_cases", "id", b["case_id"]),
                        ("tasks", "case_id", b["case_id"]), ("case_lanes", "case_id", b["case_id"])):
        assert owner.execute(f"SELECT count(*) FROM vb.{t} WHERE {col} = %s", (val,)).fetchone()[0] == 0


def test_delete_single_mission(make_user):
    u = make_user().consent()
    b = u.post("/api/v1/missions", json=VETERAN_PROFILE).json()
    assert u.delete(f"/api/v1/missions/{b['mission_id']}").status_code == 204
    assert u.get(f"/api/v1/missions/{b['mission_id']}").status_code == 404


FORECLOSED = ["advertising", "ad_targeting", "data_sale", "model_training", "claims_company_sharing",
              "lender_sharing", "recruiter_sharing", "data_broker_sharing", "bulk_research_export"]


@pytest.mark.parametrize("purpose", FORECLOSED)
def test_foreclosed_purpose_refused_by_api(make_user, purpose):
    r = make_user().post("/api/v1/consents", json={"purpose": purpose})
    assert r.status_code == 422 and r.json()["error"]["code"] == "PURPOSE_FORECLOSED"


def test_foreclosed_purpose_refused_even_for_schema_owner(owner, make_user):
    me = make_user().get("/api/v1/users/me").json()
    tenant = owner.execute("SELECT id FROM vb.tenants WHERE slug = 'public'").fetchone()[0]
    for purpose in FORECLOSED:
        with pytest.raises(psycopg.errors.CheckViolation):
            owner.execute("INSERT INTO vb.consents (tenant_id, user_id, purpose, policy_version) VALUES (%s, %s, %s, 'x')",
                          (tenant, me["user_id"], purpose))


def test_purpose_table_matches_constraint(owner):
    rows = owner.execute("SELECT purpose, foreclosed FROM vb.consent_purposes").fetchall()
    assert sorted(p for p, f in rows if f) == sorted(FORECLOSED)
    allowed = sorted(p for p, f in rows if not f)
    check = owner.execute("""SELECT pg_get_constraintdef(oid) FROM pg_constraint
                              WHERE conname = 'consent_purpose_allowed'""").fetchone()[0]
    assert all(f"'{p}'" in check for p in allowed) and not any(f"'{p}'" in check for p in FORECLOSED)


def test_unknown_purpose(make_user):
    assert make_user().post("/api/v1/consents", json={"purpose": "anything"}).json()["error"]["code"] == "UNKNOWN_PURPOSE"


def test_mode_c_unreachable(owner, make_user):
    me = make_user().consent().get("/api/v1/users/me").json()
    tenant = owner.execute("SELECT id FROM vb.tenants WHERE slug = 'public'").fetchone()[0]
    with pytest.raises(psycopg.errors.CheckViolation):
        owner.execute("""INSERT INTO vb.missions (tenant_id, user_id, privacy_mode, policy_version, input_hash, router_input,
                         as_of, stage, track) VALUES (%s, %s, 'C', 'x', repeat('a', 64), '{}', '2026-10-20', 'unknown', 'x')""",
                      (tenant, me["user_id"]))
