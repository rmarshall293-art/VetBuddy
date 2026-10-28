"""Slice 01 integration tests against a real PostgreSQL.

P2 gate (master spec §19): two veterans and two organizations cannot access
each other's cases; consent revocation works; tasks persist.
"""
import json
import uuid

from app.infra.db import DatabaseError, connect, tenant_transaction
from tests.support import APP_DSN, ONBOARD, ApiCase, admin, settings
from starlette.testclient import TestClient
from app.api.main import create_app


class OnboardingAndBrief(ApiCase):
    def test_full_flow_persists_and_brief_is_reproducible(self):
        h = self.signup()
        mid = self.onboard(h)
        b1 = self.client.get(f"/api/v1/missions/{mid}/brief", headers=h).json()
        b2 = self.client.get(f"/api/v1/missions/{mid}/brief", headers=h).json()
        self.assertEqual(b1, b2)
        self.assertEqual(b1["generated_by"], "deterministic_router")
        self.assertEqual(b1["benefit_screening"]["status"], "DISABLED")
        self.assertEqual(len(b1["first_five_actions"]), 5)
        self.assertEqual({j["code"] for j in b1["jurisdictions"]}, {"AL", "TX"})
        self.assertTrue(all("disclaimer" in j for j in b1["jurisdictions"]), "unverified must be labelled")
        self.assertEqual(self.client.get("/api/v1/missions", headers=h).json()["missions"][0]["mission_id"], mid)

    def test_consent_required_to_persist(self):
        h = self.signup()
        r = self.client.post("/api/v1/onboarding", json={**ONBOARD, "consent": False}, headers=h)
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()["error"]["code"], "CONSENT_REQUIRED")

    def test_validation_errors_are_structured(self):
        h = self.signup()
        r = self.client.post("/api/v1/onboarding", json={**ONBOARD, "legal_authority": None}, headers=h)
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json()["error"]["fields"][0]["field"], "legal_authority")
        r = self.client.post("/api/v1/onboarding", json={**ONBOARD, "ssn": "000-00-0000"}, headers=h)
        self.assertEqual(r.status_code, 422, "unknown fields (e.g. SSN) are rejected, never stored")

    def test_task_lifecycle_concurrency_and_events(self):
        h = self.signup()
        mid = self.onboard(h)
        task = self.client.get(f"/api/v1/missions/{mid}/brief", headers=h).json()["tasks"][0]
        url = f"/api/v1/tasks/{task['task_id']}"
        r = self.client.patch(url, json={"status": "done", "version": task["version"]}, headers=h)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["version"], task["version"] + 1)
        stale = self.client.patch(url, json={"status": "todo", "version": task["version"]}, headers=h)
        self.assertEqual(stale.json()["error"]["code"], "VERSION_CONFLICT")
        bad = self.client.patch(url, json={"status": "blocked", "version": task["version"] + 1}, headers=h)
        self.assertEqual(bad.json()["error"]["code"], "INVALID_TRANSITION")
        brief = self.client.get(f"/api/v1/missions/{mid}/brief", headers=h).json()
        self.assertNotIn(task["task_id"], [t["task_id"] for t in brief["first_five_actions"]])
        with admin() as a:
            n = a.one("SELECT count(*) AS n FROM outbox_event WHERE event_type='TASK_COMPLETED' AND aggregate_id=$1",
                      [task["task_id"]])["n"]
        self.assertEqual(n, 1)


class CrossTenantIsolation(ApiCase):
    def test_two_veterans_cannot_see_each_other(self):
        ha, hb = self.signup(), self.signup()
        mid_a = self.onboard(ha)
        self.onboard(hb, persona="veteran", component="separated", legal_authority=None, current_jurisdiction="PR",
                     destination_jurisdiction=None)
        task_a = self.client.get(f"/api/v1/missions/{mid_a}/brief", headers=ha).json()["tasks"][0]
        # B reads/writes A's objects -> 404 (no enumeration), never 403
        self.assertEqual(self.client.get(f"/api/v1/missions/{mid_a}/brief", headers=hb).status_code, 404)
        r = self.client.patch(f"/api/v1/tasks/{task_a['task_id']}", json={"status": "done", "version": 1}, headers=hb)
        self.assertEqual(r.status_code, 404)
        ids_b = [m["mission_id"] for m in self.client.get("/api/v1/missions", headers=hb).json()["missions"]]
        self.assertNotIn(mid_a, ids_b)
        consents_a = self.client.get("/api/v1/consents", headers=ha).json()["consents"]
        r = self.client.post(f"/api/v1/consents/{consents_a[0]['consent_id']}/revoke", headers=hb)
        self.assertEqual(r.status_code, 404)
        # A's task untouched
        t = self.client.get(f"/api/v1/missions/{mid_a}/brief", headers=ha).json()["tasks"][0]
        self.assertEqual((t["status"], t["version"]), (task_a["status"], task_a["version"]))

    def test_database_enforces_isolation_for_app_role(self):
        """Bypass the API entirely: the app DB role itself cannot cross tenants."""
        ha = self.signup()
        mid = self.onboard(ha)
        with admin() as a:
            tenant_a = a.one("SELECT tenant_id FROM mission WHERE mission_id=$1", [mid])["tenant_id"]
        other = uuid.uuid4()
        with tenant_transaction(APP_DSN, other) as c:
            self.assertEqual(c.query("SELECT * FROM mission WHERE mission_id=$1", [mid]), [])
            self.assertEqual(c.query("SELECT * FROM task t JOIN crm_case cc USING (case_id) WHERE cc.mission_id=$1",
                                     [mid]), [])
        with tenant_transaction(APP_DSN, None) as c:   # no context at all
            for table in ("mission", "crm_case", "task", "person_profile", "service_record", "consent_record",
                          "audit_event", "outbox_event", "household", "tenant", "app_user"):
                self.assertEqual(c.one(f"SELECT count(*) AS n FROM {table}")["n"], 0, table)
        with self.assertRaises(DatabaseError) as e:   # cannot write into another tenant
            with tenant_transaction(APP_DSN, other) as c:
                c.query("INSERT INTO household (tenant_id) VALUES ($1)", [tenant_a])
        self.assertEqual(e.exception.sqlstate, "42501")
        with self.assertRaises(DatabaseError):        # cannot UPDATE across tenants either (0 rows, then check)
            with tenant_transaction(APP_DSN, tenant_a) as c:
                c.query("UPDATE mission SET tenant_id=$1 WHERE mission_id=$2", [other, mid])

    def test_two_organizations_cases_are_isolated(self):
        org1, org2 = uuid.uuid4(), uuid.uuid4()
        with admin() as a, a.transaction():
            for org in (org1, org2):
                a.query("INSERT INTO tenant (tenant_id, name, kind) VALUES ($1,'synthetic org','organization')", [org])
                p = a.one("INSERT INTO person_profile (tenant_id, display_name) VALUES ($1,'Synthetic Client')"
                          " RETURNING person_id", [org])["person_id"]
                m = a.one("INSERT INTO mission (tenant_id, person_id, title, primary_lane) VALUES ($1,$2,'t','benefits')"
                          " RETURNING mission_id", [org, p])["mission_id"]
                a.query("INSERT INTO crm_case (tenant_id, mission_id, lane) VALUES ($1,$2,'benefits')", [org, m])
        for mine, theirs in ((org1, org2), (org2, org1)):
            with tenant_transaction(APP_DSN, mine) as c:
                rows = c.query("SELECT tenant_id FROM crm_case")
                self.assertEqual({r["tenant_id"] for r in rows}, {mine})
                self.assertEqual(c.query("SELECT 1 FROM crm_case WHERE tenant_id=$1", [theirs]), [])

    def test_app_role_cannot_delete_or_rewrite_audit(self):
        h = self.signup()
        self.onboard(h)
        with admin() as a:
            tenant = a.one("SELECT tenant_id FROM audit_event ORDER BY created_at DESC LIMIT 1")["tenant_id"]
        for sql in ("DELETE FROM mission", "UPDATE audit_event SET reason='x'", "DELETE FROM audit_event"):
            with self.subTest(sql=sql), self.assertRaises(DatabaseError) as e:
                with tenant_transaction(APP_DSN, tenant) as c:
                    c.query(sql)
            self.assertEqual(e.exception.sqlstate, "42501")
        with self.assertRaises(DatabaseError):     # even the owner is stopped by the trigger
            with admin() as a:
                a.query("UPDATE audit_event SET reason='tamper'")


class ConsentAndPrivacy(ApiCase):
    def test_revocation_takes_effect_on_next_request(self):
        h = self.signup()
        mid = self.onboard(h)
        cid = self.client.get("/api/v1/consents", headers=h).json()["consents"][0]["consent_id"]
        self.assertEqual(self.client.post(f"/api/v1/consents/{cid}/revoke", headers=h).status_code, 200)
        for r in (self.client.get(f"/api/v1/missions/{mid}/brief", headers=h),
                  self.client.get("/api/v1/missions", headers=h)):
            self.assertEqual(r.status_code, 403)
            self.assertEqual(r.json()["error"]["code"], "CONSENT_REQUIRED")
        self.assertEqual(self.client.post("/api/v1/consents", json={"purpose": "personal_mission_planning"},
                                          headers=h).status_code, 200)
        self.assertEqual(self.client.get(f"/api/v1/missions/{mid}/brief", headers=h).status_code, 200)

    def test_unlisted_consent_purpose_cannot_be_stored(self):
        h = self.signup()
        r = self.client.post("/api/v1/consents", json={"purpose": "sell_to_marketers"}, headers=h)
        self.assertEqual(r.json()["error"]["code"], "PURPOSE_NOT_ALLOWED")
        with admin() as a:
            u = a.one("SELECT user_id, tenant_id FROM app_user ORDER BY created_at DESC LIMIT 1")
            with self.assertRaises(DatabaseError) as e:
                a.query("INSERT INTO consent_record (tenant_id,user_id,purpose,data_categories) VALUES ($1,$2,$3,$4)",
                        [u["tenant_id"], u["user_id"], "sell_to_marketers", ["V2"]])
            self.assertEqual(e.exception.sqlstate, "23503")

    def test_foreclosed_purposes_refused_everywhere(self):
        """CB-03: the nine foreclosed purposes exist as rows and can never be granted."""
        h = self.signup()
        r = self.client.post("/api/v1/consents", json={"purpose": "third_party_marketing"}, headers=h)
        self.assertEqual(r.json()["error"]["code"], "PURPOSE_NOT_ALLOWED")
        with admin() as a:
            self.assertEqual(a.one("SELECT count(*) AS n FROM consent_purpose WHERE foreclosed")["n"], 9)
            u = a.one("SELECT user_id, tenant_id FROM app_user ORDER BY created_at DESC LIMIT 1")
            for sql, args in (
                ("INSERT INTO consent_record (tenant_id,user_id,purpose,data_categories) VALUES ($1,$2,$3,$4)",
                 [u["tenant_id"], u["user_id"], "training_external_models", ["V2"]]),
                ("UPDATE consent_purpose SET allowed = true WHERE purpose = $1", ["insurance_underwriting"]),
                ("UPDATE consent_purpose SET foreclosed = false WHERE purpose = $1", ["insurance_underwriting"]),
                ("DELETE FROM consent_purpose WHERE purpose = $1", ["sale_of_personal_information"]),
            ):
                with self.subTest(sql=sql), self.assertRaises(DatabaseError) as e:
                    with a.transaction():
                        a.query(sql, args)
                self.assertEqual(e.exception.sqlstate, "23514")

    def test_mode_c_is_unreachable(self):
        h = self.signup()
        r = self.client.put("/api/v1/me/privacy-mode", json={"mode": "C"}, headers=h)
        self.assertEqual(r.json()["error"]["code"], "MODE_C_DISABLED")
        with admin() as a:
            uid = a.one("SELECT user_id FROM app_user ORDER BY created_at DESC LIMIT 1")["user_id"]
            with self.assertRaises(DatabaseError) as e:
                a.query("UPDATE app_user SET privacy_mode='C' WHERE user_id=$1", [uid])
            self.assertEqual(e.exception.sqlstate, "23514")

    def test_guest_preview_persists_nothing(self):
        def counts():
            with admin() as a:
                tables = [r["tablename"] for r in a.query("SELECT tablename FROM pg_tables WHERE schemaname='public'")]
                return {t: a.one(f'SELECT count(*) AS n FROM "{t}"')["n"] for t in tables}
        before = counts()
        r = self.client.post("/api/v1/brief/preview", json={**ONBOARD, "display_name": "Should Not Persist"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertFalse(r.json()["persisted"])
        self.assertIsNone(r.json()["mission_id"])
        self.assertEqual(before, counts())

    def test_guard_reserve_without_authority_rejected_by_database(self):
        h = self.signup()
        mid = self.onboard(h)
        with admin() as a:
            row = a.one("SELECT tenant_id, person_id FROM mission WHERE mission_id=$1", [mid])
            with self.assertRaises(DatabaseError) as e:
                a.query("INSERT INTO service_record (tenant_id, person_id, branch, component) VALUES"
                        " ($1,$2,'Army','reserve')", [row["tenant_id"], row["person_id"]])
            self.assertEqual(e.exception.sqlstate, "23514")


class AuthAndAudit(ApiCase):
    def test_tampered_and_missing_tokens(self):
        h = self.signup()
        tok = h["authorization"].split(" ", 1)[1]
        parts = tok.split(".")
        forged = ".".join([parts[0], str(uuid.uuid4()), parts[2], parts[3], parts[4]])
        for hdr in ({}, {"authorization": "Bearer " + forged}, {"authorization": "Bearer junk"}):
            r = self.client.get("/api/v1/me", headers=hdr)
            self.assertEqual(r.status_code, 401)
            self.assertEqual(r.json()["error"]["code"], "UNAUTHENTICATED")

    def test_auth_disabled_fails_closed(self):
        c = TestClient(create_app(settings(auth_mode="disabled")))
        self.assertEqual(c.post("/api/v1/dev/signup").status_code, 404)
        h = self.signup()
        self.assertEqual(c.get("/api/v1/me", headers=h).status_code, 401)

    def test_audit_chain_verifies(self):
        from app.domains.trust import audit
        h = self.signup()
        mid = self.onboard(h)
        task = self.client.get(f"/api/v1/missions/{mid}/brief", headers=h).json()["tasks"][0]
        self.client.patch(f"/api/v1/tasks/{task['task_id']}", json={"status": "in_progress", "version": 1}, headers=h)
        with admin() as a:
            tenant = a.one("SELECT tenant_id FROM mission WHERE mission_id=$1", [mid])["tenant_id"]
            actions = [r["action"] for r in a.query(
                "SELECT action FROM audit_event WHERE tenant_id=$1 ORDER BY created_at", [tenant])]
            self.assertEqual(actions, ["ACCOUNT_CREATED", "CONSENT_GRANTED", "MISSION_CREATED", "TASK_STATUS_CHANGED"])
            self.assertTrue(audit.verify_chain(a, tenant))
            blob = json.dumps(a.query("SELECT new_value FROM audit_event WHERE tenant_id=$1", [tenant]), default=str)
            self.assertNotIn("2027-06-30", blob, "audit stores references, not personal facts")


class PlatformBasics(ApiCase):
    def test_readyz_and_headers(self):
        r = self.client.get("/readyz")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["jurisdictions"], 57)
        for k in ("content-security-policy", "x-content-type-options", "x-trace-id"):
            self.assertIn(k, r.headers)

    def test_readyz_503_when_database_down(self):
        c = TestClient(create_app(settings(database_url="host=localhost port=1 user=vb_app dbname=nope connect_timeout=1")))
        self.assertEqual(c.get("/readyz").status_code, 503)

    def test_crisis_contacts_verbatim(self):
        contacts = self.client.get("/api/v1/crisis-contacts").json()["contacts"]
        vcl = next(c for c in contacts if c["key"] == "veterans_crisis_line")
        self.assertEqual((vcl["phone"], vcl["extra"]), ("988", "Press 1"))

    def test_jurisdictions_labelled_and_complete(self):
        js = self.client.get("/api/v1/jurisdictions").json()["jurisdictions"]
        self.assertEqual(len(js), 57)               # FEDERAL + 50 states + DC + 5 territories
        self.assertEqual(js[0]["code"], "FEDERAL")
        self.assertTrue(all(j["verification_status"] == "unverified" and j["disclaimer"] for j in js))

    def test_unknown_api_path_uses_error_contract(self):
        r = self.client.get("/api/v1/nope")
        self.assertEqual(r.status_code, 404)
        self.assertIn("trace_id", r.json()["error"])

    def test_rls_guard_holds(self):
        with admin() as a:
            bad = a.query("""SELECT c.relname FROM pg_class c WHERE c.relnamespace='public'::regnamespace
                AND c.relkind='r' AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public'
                AND table_name=c.relname AND column_name='tenant_id') AND NOT (relrowsecurity AND relforcerowsecurity)""")
            self.assertEqual(bad, [])
            self.assertEqual(a.query("SELECT 1 FROM agent_manifest WHERE status='PRODUCTION'"), [])
