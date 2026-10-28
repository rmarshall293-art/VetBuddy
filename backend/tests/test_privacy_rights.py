"""Data export and account deletion (master prompt v6 §3; §14 tests 2 and 5)."""
import json
import uuid

from app.infra.db import DatabaseError, tenant_transaction
from tests.support import APP_DSN, ONBOARD, ApiCase, admin

CONFIRM = {"confirm": "DELETE MY ACCOUNT"}
PROTECTED = [("GET", "/api/v1/me"), ("GET", "/api/v1/missions"), ("GET", "/api/v1/consents"),
             ("GET", "/api/v1/me/export"), ("POST", "/api/v1/me/delete")]


def tenant_tables(a):
    return [r["t"] for r in a.query(
        "SELECT c.table_name::text AS t FROM information_schema.columns c JOIN information_schema.tables it "
        "ON it.table_schema=c.table_schema AND it.table_name=c.table_name "
        "WHERE c.table_schema='public' AND c.column_name='tenant_id' AND it.table_type='BASE TABLE'")]


def rows_for(a, tenant):
    return {t: a.one(f'SELECT count(*) AS n FROM "{t}" WHERE tenant_id=$1', [tenant])["n"] for t in tenant_tables(a)}


class Export(ApiCase):
    def _account(self):
        h = self.signup()
        mid = self.onboard(h)
        with admin() as a:
            tenant = a.one("SELECT tenant_id FROM mission WHERE mission_id=$1", [mid])["tenant_id"]
        return h, mid, tenant

    def test_export_is_complete_and_own_only(self):
        h, mid, tenant = self._account()
        _, other_mid, _ = self._account()
        r = self.client.get("/api/v1/me/export", headers=h)
        self.assertEqual(r.status_code, 200)
        self.assertIn("attachment", r.headers["content-disposition"])
        data = r.json()
        self.assertEqual(data["schema_version"], "vetbuddy.account-export.v1")
        with admin() as a:
            stored = {t: n for t, n in rows_for(a, tenant).items() if n}
        self.assertEqual({t: len(v) for t, v in data["tables"].items()}, stored)
        blob = json.dumps(data)
        self.assertIn(mid, blob)
        self.assertNotIn(other_mid, blob)

    def test_export_survives_consent_withdrawal(self):
        h, _, _ = self._account()
        cid = self.client.get("/api/v1/consents", headers=h).json()["consents"][0]["consent_id"]
        self.client.post(f"/api/v1/consents/{cid}/revoke", headers=h)
        self.assertEqual(self.client.get("/api/v1/missions", headers=h).status_code, 403)
        self.assertEqual(self.client.get("/api/v1/me/export", headers=h).status_code, 200)


class Deletion(ApiCase):
    def _account(self):
        h = self.signup()
        mid = self.onboard(h)
        with admin() as a:
            row = a.one("SELECT m.tenant_id, pp.user_id FROM mission m JOIN person_profile pp USING (person_id) "
                        "WHERE m.mission_id=$1", [mid])
        return h, row["tenant_id"], row["user_id"]

    def test_confirmation_is_required(self):
        h, tenant, _ = self._account()
        for body in ({}, {"confirm": "yes"}, {"confirm": "delete my account"}):
            r = self.client.post("/api/v1/me/delete", json=body, headers=h)
            self.assertIn(r.status_code, (422,))
        with admin() as a:
            self.assertEqual(a.one("SELECT count(*) AS n FROM app_user WHERE tenant_id=$1", [tenant])["n"], 1)

    def test_deletion_purges_the_whole_data_graph_and_nothing_else(self):
        h, tenant, user = self._account()
        hb, tenant_b, _ = self._account()
        with admin() as a:
            before_b = rows_for(a, tenant_b)
            before = {t: n for t, n in rows_for(a, tenant).items() if n}
        exported = self.client.get("/api/v1/me/export", headers=h).json()["tables"]
        r = self.client.post("/api/v1/me/delete", json=CONFIRM, headers=h)
        self.assertEqual(r.status_code, 200, r.text)
        receipt = r.json()
        self.assertEqual(receipt["state"], "COMPLETE")
        self.assertEqual([s["state"] for s in receipt["history"]],
                         ["REQUESTED", "VERIFIED", "ACCESS_REVOKED", "PURGING", "PROCESSOR_PENDING", "COMPLETE"])
        self.assertEqual(receipt["rows_purged"], before)
        self.assertEqual(receipt["rows_purged"], {t: len(v) for t, v in exported.items()},
                         "everything exportable was deleted, and only that")
        with admin() as a:
            self.assertEqual(sum(rows_for(a, tenant).values()), 0, "no row of any tenant table survives")
            self.assertEqual(rows_for(a, tenant_b), before_b, "another account is untouched")
            self.assertEqual(a.one("SELECT count(*) AS n FROM outbox_event WHERE tenant_id=$1", [tenant])["n"], 0,
                             "no queued event can resurrect data")
        self.assertEqual(self.client.get("/api/v1/me", headers=hb).status_code, 200)

    def test_receipt_holds_no_personal_identifiers(self):
        h, tenant, user = self._account()
        receipt = self.client.post("/api/v1/me/delete", json=CONFIRM, headers=h).json()
        blob = json.dumps(receipt)
        for ident in (str(tenant), str(user)):
            self.assertNotIn(ident, blob)
        with admin() as a:
            cols = {r["column_name"] for r in a.query(
                "SELECT column_name FROM information_schema.columns WHERE table_name='privacy_deletion_receipt'")}
        self.assertFalse(cols & {"tenant_id", "user_id", "email", "person_id"})

    def test_sessions_fail_closed_after_deletion(self):
        h, _, _ = self._account()
        self.client.post("/api/v1/me/delete", json=CONFIRM, headers=h)
        for method, path in PROTECTED:
            with self.subTest(path=path):
                r = self.client.request(method, path, headers=h, json=CONFIRM if method == "POST" else None)
                self.assertEqual(r.status_code, 401)
                self.assertEqual(r.json()["error"]["code"], "SESSION_INVALID")

    def test_status_is_public_by_receipt_only(self):
        h, _, _ = self._account()
        rid = self.client.post("/api/v1/me/delete", json=CONFIRM, headers=h).json()["receipt_id"]
        self.assertEqual(self.client.get(f"/api/v1/privacy/deletions/{rid}").json()["state"], "COMPLETE")
        self.assertEqual(self.client.get(f"/api/v1/privacy/deletions/{uuid.uuid4()}").status_code, 404)
        self.assertEqual(self.client.get("/api/v1/privacy/deletions/not-a-uuid").status_code, 404)

    def test_purge_function_is_bound_to_the_caller(self):
        _, tenant_a, _ = self._account()
        _, _, user_b = self._account()
        with self.assertRaises(DatabaseError) as e:      # no tenant context at all
            with tenant_transaction(APP_DSN, None) as c:
                c.query("SELECT vb_delete_account($1)", [user_b])
        self.assertEqual(e.exception.sqlstate, "42501")
        with self.assertRaises(DatabaseError) as e:      # someone else's user id under my tenant
            with tenant_transaction(APP_DSN, tenant_a) as c:
                c.query("SELECT vb_delete_account($1)", [user_b])
        self.assertEqual(e.exception.sqlstate, "P0002")
        with admin() as a:
            self.assertEqual(a.one("SELECT count(*) AS n FROM app_user WHERE user_id=$1", [user_b])["n"], 1)

    def test_shared_tenant_is_refused_not_over_deleted(self):
        org = uuid.uuid4()
        with admin() as a, a.transaction():
            a.query("INSERT INTO tenant (tenant_id, name, kind) VALUES ($1,'synthetic org','organization')", [org])
            u1 = a.one("INSERT INTO app_user (tenant_id) VALUES ($1) RETURNING user_id", [org])["user_id"]
            a.query("INSERT INTO app_user (tenant_id) VALUES ($1)", [org])
        with self.assertRaises(DatabaseError) as e:
            with tenant_transaction(APP_DSN, org) as c:
                c.query("SELECT vb_delete_account($1)", [u1])
        self.assertEqual(e.exception.sqlstate, "0A000")
        with admin() as a:
            self.assertEqual(a.one("SELECT count(*) AS n FROM app_user WHERE tenant_id=$1", [org])["n"], 2)

    def test_audit_stays_append_only_outside_the_purge(self):
        h, tenant, _ = self._account()
        with self.assertRaises(DatabaseError) as e:      # app role: no DELETE grant even with the flag set
            with tenant_transaction(APP_DSN, tenant) as c:
                c.query("SELECT set_config('vetbuddy.purge_tenant', $1, true)", [str(tenant)])
                c.query("DELETE FROM audit_event")
        self.assertEqual(e.exception.sqlstate, "42501")
        with self.assertRaises(DatabaseError):           # owner without the flag: trigger refuses
            with admin() as a:
                a.query("DELETE FROM audit_event WHERE tenant_id=$1", [tenant])

    def test_purger_role_cannot_bypass_rls_and_covers_every_tenant_table(self):
        with admin() as a:
            role = a.one("SELECT rolsuper, rolbypassrls, rolcanlogin FROM pg_roles WHERE rolname='vetbuddy_purger'")
            self.assertEqual((role["rolsuper"], role["rolbypassrls"], role["rolcanlogin"]), (False, False, False))
            owners = {r["proname"]: r["owner"] for r in a.query(
                "SELECT proname, proowner::regrole::text AS owner FROM pg_proc WHERE proname IN "
                "('vb_delete_account','vb_deletion_status')")}
            self.assertEqual(set(owners.values()), {"vetbuddy_purger"})
            missing = [t for t in tenant_tables(a) if not a.one(
                "SELECT has_table_privilege('vetbuddy_purger', $1, 'DELETE') AS ok", [f"public.{t}"])["ok"]]
            self.assertEqual(missing, [], "a new tenant table must grant DELETE to vetbuddy_purger")


class V6Vocabulary(ApiCase):
    def test_sql_enforces_v6_labels(self):
        with admin() as a:
            labels = {r["repo_status"] for r in a.query(
                "SELECT DISTINCT repo_status FROM ref.governance_rule WHERE repo_status IS NOT NULL")}
            self.assertTrue(labels <= {"IMPLEMENTED_TESTED", "IMPLEMENTED_UNVERIFIED", "PARTIAL", "MOCK",
                                       "PLANNED", "DISABLED", "BLOCKED"}, labels)
            with self.assertRaises(DatabaseError) as e, a.transaction():
                a.query("UPDATE ref.governance_rule SET repo_status='NOT_PRESENT' WHERE rule_id='R1'")
            self.assertEqual(e.exception.sqlstate, "23514")
