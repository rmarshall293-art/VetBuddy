"""Phase 2 gate: two veterans and two organizations cannot reach each other's cases.

Isolation is enforced by PostgreSQL row-level security on a non-owner role,
so these tests go through the API AND straight at the database.
"""

import psycopg
from psycopg.rows import dict_row

from conftest import APP_LOGIN, GUARD_PROFILE, VETERAN_PROFILE


def _mission(user, profile):
    r = user.post("/api/v1/missions", json=profile)
    assert r.status_code == 201, r.text
    return r.json()


def test_cross_user_and_cross_tenant_reads_are_404(make_user, second_tenant):
    alice, bob = make_user().consent(), make_user().consent()
    carol = make_user(second_tenant).consent()
    a = _mission(alice, GUARD_PROFILE)
    _mission(bob, VETERAN_PROFILE)
    task_id = a["tasks"][0]["id"]
    for intruder in (bob, carol):
        assert intruder.get(f"/api/v1/missions/{a['mission_id']}").status_code == 404
        assert intruder.get(f"/api/v1/cases/{a['case_id']}").status_code == 404
        assert intruder.get(f"/api/v1/missions/{a['mission_id']}/next-action").status_code == 404
        assert intruder.patch(f"/api/v1/tasks/{task_id}", json={"status": "done", "expected_version": 1}).status_code == 404
        assert intruder.delete(f"/api/v1/missions/{a['mission_id']}").status_code == 404
        ids = [m["id"] for m in intruder.get("/api/v1/missions").json()["missions"]]
        assert a["mission_id"] not in ids
        assert task_id not in [t["id"] for t in intruder.get("/api/v1/tasks").json()["tasks"]]
    # Alice still sees her own, untouched.
    again = alice.get(f"/api/v1/missions/{a['mission_id']}").json()
    assert again["tasks"][0]["status"] == "todo"


def test_same_subject_in_two_tenants_is_two_people(client, second_tenant):
    from conftest import User
    u1 = User(client, "same-subject-xyz").consent()
    u2 = User(client, "same-subject-xyz", second_tenant).consent()
    assert u1.get("/api/v1/users/me").json()["user_id"] != u2.get("/api/v1/users/me").json()["user_id"]
    m = _mission(u1, VETERAN_PROFILE)
    assert u2.get(f"/api/v1/missions/{m['mission_id']}").status_code == 404


def test_unset_context_reads_zero_rows(database, make_user):
    _mission(make_user().consent(), GUARD_PROFILE)
    with psycopg.connect(database["app_url"], row_factory=dict_row) as conn:
        for t in ("missions", "master_cases", "case_lanes", "tasks", "consents", "users", "tenants"):
            assert conn.execute(f"SELECT count(*) AS n FROM vb.{t}").fetchone()["n"] == 0, t
        # And an empty-string context (what a pooled connection holds after a LOCAL set ends) fails closed too.
        conn.execute("SELECT set_config('app.tenant_id', '', false), set_config('app.user_id', '', false)")
        assert conn.execute("SELECT count(*) AS n FROM vb.missions").fetchone()["n"] == 0


def test_app_role_cannot_forge_another_owner(database, make_user):
    alice, bob = make_user().consent(), make_user().consent()
    _mission(alice, GUARD_PROFILE)
    me_a = alice.get("/api/v1/users/me").json()
    me_b = bob.get("/api/v1/users/me").json()
    with psycopg.connect(database["app_url"]) as conn:
        tenant = conn.execute("SELECT tenant_id FROM vb.resolve_principal('public', 'nobody-' || gen_random_uuid())").fetchone()
        conn.execute("SELECT set_config('app.tenant_id', %s, true), set_config('app.user_id', %s, true)",
                     (str(tenant[0]), me_b["user_id"]))
        # Bob's context, Alice's user_id in the row: the WITH CHECK refuses it.
        try:
            conn.execute("""INSERT INTO vb.missions (tenant_id, user_id, policy_version, input_hash, router_input, as_of, stage, track)
                            VALUES (%s, %s, 'x', repeat('a', 64), '{}', '2026-10-20', 'unknown', 're_entry')""",
                         (str(tenant[0]), me_a["user_id"]))
            raise AssertionError("insert for another user was accepted")
        except psycopg.errors.InsufficientPrivilege:
            conn.rollback()


def test_app_role_is_least_privilege(owner):
    row = owner.execute("""SELECT rolsuper, rolbypassrls, rolcreaterole, rolcreatedb FROM pg_roles WHERE rolname = %s""",
                        (APP_LOGIN,)).fetchone()
    assert row == (False, False, False, False)
    owned = owner.execute("""SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                              WHERE n.nspname = 'vb' AND pg_get_userbyid(c.relowner) IN (%s, 'vetbuddy_app')""",
                          (APP_LOGIN,)).fetchone()[0]
    assert owned == 0
    # No TRUNCATE, no UPDATE on identity columns, no reading the audit trail.
    assert not owner.execute("SELECT has_table_privilege(%s, 'vb.tasks', 'TRUNCATE')", (APP_LOGIN,)).fetchone()[0]
    assert not owner.execute("SELECT has_column_privilege(%s, 'vb.tasks', 'user_id', 'UPDATE')", (APP_LOGIN,)).fetchone()[0]
    assert not owner.execute("SELECT has_table_privilege(%s, 'vb.audit_events', 'SELECT')", (APP_LOGIN,)).fetchone()[0]


def test_isolation_tests_fail_when_rls_is_removed(database, make_user, owner):
    """Mutation check: with RLS disabled the same cross-user read DOES leak,
    so the tests above are measuring RLS rather than passing by accident."""
    alice, bob = make_user().consent(), make_user().consent()
    _mission(alice, GUARD_PROFILE)
    me_b = bob.get("/api/v1/users/me").json()
    tenant = owner.execute("SELECT id FROM vb.tenants WHERE slug = 'public'").fetchone()[0]
    owner.execute("ALTER TABLE vb.missions DISABLE ROW LEVEL SECURITY")
    try:
        with psycopg.connect(database["app_url"]) as conn:
            conn.execute("SELECT set_config('app.tenant_id', %s, true), set_config('app.user_id', %s, true)",
                         (str(tenant), me_b["user_id"]))
            leaked = conn.execute("SELECT count(*) FROM vb.missions WHERE user_id <> %s", (me_b["user_id"],)).fetchone()[0]
        assert leaked > 0
    finally:
        owner.execute("ALTER TABLE vb.missions ENABLE ROW LEVEL SECURITY")
    assert owner.execute("SELECT count(*) FROM vb.rls_gaps()").fetchone()[0] == 0
