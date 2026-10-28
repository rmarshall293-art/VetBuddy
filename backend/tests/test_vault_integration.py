"""The Benefit Vault mounted in the real app (migration 0014 on the slice 03 chain).

The vault's own suite (tests/vault) covers the kernel, governance and database
in depth; this file checks the seams with the platform: one error contract,
guest use stores nothing, account use needs the same live session and
consent as every protected route, export includes vault rows, and account
deletion removes them and closes the session.
"""
from app.infra import config
from tests.support import ApiCase, admin
from tests.test_privacy_rights import CONFIRM, rows_for, tenant_tables

VAULT = "/api/v1/vault"
TX_VET = {"residence_state": "TX", "service_status": "separated", "va_rating": 100,
          "discharge": "honorable", "relationship": "self"}
VAULT_TABLES = ("vault_pull_grant", "vault_pull_ledger", "vault_saved_benefit")


def notice() -> str:
    import yaml
    return " ".join(yaml.safe_load((config.ROOT / "config/governance_language.yaml").read_text())["common_notice"].split())


class VaultGuest(ApiCase):
    def test_catalog_carries_the_common_notice_and_no_determination(self):
        r = self.client.get(f"{VAULT}/catalog")
        self.assertEqual(r.status_code, 200)
        cat = r.json()
        self.assertEqual(cat["notice"], notice())
        self.assertEqual(cat["publish_policy"], "verified_only")      # production default, fail-safe
        env = self.client.post(f"{VAULT}/match", json={"facts": TX_VET}).json()
        self.assertEqual(env["determination"], "none")
        self.assertEqual(env["notice"], notice())
        self.assertEqual(env["mode"], "A")
        # Nothing is VERIFIED (G1), so production shows matches as leads for review, never a match.
        self.assertEqual(env["counts"]["PRELIMINARY_MATCH"], 0)
        self.assertGreater(env["counts"]["HUMAN_REVIEW_REQUIRED"], 0)

    def test_guest_use_persists_nothing(self):
        with admin() as a:
            before = {t: a.one(f'SELECT count(*) AS n FROM "{t}"')["n"] for t in tenant_tables(a)}
        self.assertEqual(self.client.get(f"{VAULT}/benefits?q=hunting&jurisdiction=AL").status_code, 200)
        self.assertEqual(self.client.post(f"{VAULT}/match", json={"facts": TX_VET}).status_code, 200)
        household = {"facts": TX_VET, "members": [{"member_id": "spouse", "relationship": "spouse"}]}
        self.assertEqual(self.client.post(f"{VAULT}/household", json=household).status_code, 200)
        with admin() as a:
            after = {t: a.one(f'SELECT count(*) AS n FROM "{t}"')["n"] for t in tenant_tables(a)}
        self.assertEqual(before, after)

    def test_errors_use_the_one_contract(self):
        r = self.client.get(f"{VAULT}/grants")
        self.assertEqual(r.status_code, 403)
        err = r.json()["error"]
        self.assertEqual(err["code"], "ACCOUNT_REQUIRED")
        self.assertTrue(err["trace_id"])
        self.assertEqual(r.headers["cache-control"], "no-store")
        bad = self.client.post(f"{VAULT}/match", json={"facts": "x"})
        self.assertEqual(bad.status_code, 422)
        self.assertEqual(bad.json()["error"]["code"], "VALIDATION_FAILED")


class VaultAccount(ApiCase):
    def _account(self):
        h = self.signup()
        mid = self.onboard(h)
        with admin() as a:
            row = a.one("SELECT m.tenant_id, pp.user_id FROM mission m JOIN person_profile pp USING (person_id) "
                        "WHERE m.mission_id=$1", [mid])
        return h, row["tenant_id"], row["user_id"]

    def _use_vault(self, h):
        grant = self.client.post(f"{VAULT}/grants", headers=h,
                                 json={"source_agent": "household_agent", "fact_keys": ["age"], "confirm": True})
        self.assertEqual(grant.status_code, 200, grant.text)
        saved = self.client.post(f"{VAULT}/saved", headers=h, json={"benefit_id": "us.fry-scholarship", "confirm": True})
        self.assertEqual(saved.status_code, 200, saved.text)
        ledger = self.client.get(f"{VAULT}/ledger", headers=h).json()
        self.assertTrue(ledger["chain_ok"])
        return grant.json()["grant"]["grant_id"]

    def test_writes_need_confirmation(self):
        h, _, _ = self._account()
        r = self.client.post(f"{VAULT}/saved", headers=h, json={"benefit_id": "us.fry-scholarship"})
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()["error"]["code"], "APPROVAL_REQUIRED")
        self.assertIn("consent_text", r.json()["error"])

    def test_account_rows_are_tenant_scoped_and_exported(self):
        h, tenant, _ = self._account()
        other, other_tenant, _ = self._account()
        self._use_vault(h)
        self.assertEqual(self.client.get(f"{VAULT}/saved", headers=other).json()["saved"], [])
        with admin() as a:
            counts = rows_for(a, tenant)
        self.assertEqual({t: counts[t] for t in VAULT_TABLES},
                         {"vault_pull_grant": 1, "vault_pull_ledger": 1, "vault_saved_benefit": 1})
        export = self.client.get("/api/v1/me/export", headers=h).json()["tables"]
        for t in VAULT_TABLES:
            self.assertEqual(len(export[t]), 1, t)
        self.assertNotIn(str(other_tenant), str(export))

    def test_withdrawn_consent_turns_account_routes_off(self):
        h, _, _ = self._account()
        self._use_vault(h)
        cid = self.client.get("/api/v1/consents", headers=h).json()["consents"][0]["consent_id"]
        self.client.post(f"/api/v1/consents/{cid}/revoke", headers=h)
        self.assertEqual(self.client.get(f"{VAULT}/saved", headers=h).status_code, 403)
        # Guest features keep working for the same person (v6: guest access never needs an account).
        env = self.client.post(f"{VAULT}/match", headers=h, json={"facts": TX_VET}).json()
        self.assertEqual(env["mode"], "A")

    def test_account_deletion_removes_vault_rows_and_closes_the_session(self):
        h, tenant, _ = self._account()
        self._use_vault(h)
        r = self.client.post("/api/v1/me/delete", headers=h, json=CONFIRM)
        self.assertEqual(r.status_code, 200, r.text)
        receipt = r.json()
        status = self.client.get(f"/api/v1/privacy/deletions/{receipt['receipt_id']}").json()
        for t in VAULT_TABLES:
            self.assertGreaterEqual(status["rows_purged"].get(t, 0), 1, t)
        with admin() as a:
            self.assertEqual({t: n for t, n in rows_for(a, tenant).items() if n}, {})
        self.assertEqual(self.client.get(f"{VAULT}/ledger", headers=h).status_code, 403)
        self.assertEqual(self.client.post(f"{VAULT}/match", headers=h, json={"facts": TX_VET}).json()["mode"], "A")
