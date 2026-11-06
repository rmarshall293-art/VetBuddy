"""The reviewer roster and review workflow (gate G1; migration 0016; owner decision 2026-10-29).

Covers: the roster file takes handles only; sync adds and retires, never
deletes; the database refuses a mark from anyone not active and in scope; a
review needs the exact content the reviewer read; every action is logged
append-only; a review reaches the production API on its next start; a
withdrawal undoes it. Leaves the test database as it found it.
"""
import datetime as dt
import tempfile
import unittest
from pathlib import Path

from app.api.main import create_app
from app.domains.vault import review
from app.domains.vault.agent import BenefitVaultAgent, Session
from app.domains.vault.registry import default_registry
from app.infra.db import DatabaseError, connect
from starlette.testclient import TestClient
from tests.support import APP_DSN, TODAY, admin, settings

GUEST_AL = {"residence_state": "AL", "service_status": "serving", "component": "guard", "guard_state": "AL",
            "relationship": "self"}
ON = dt.date(2026, 10, 29)


def roster_file(text: str) -> Path:
    f = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False)
    f.write(text)
    f.close()
    return Path(f.name)


class RosterFile(unittest.TestCase):
    def test_handles_only(self):
        good = "owner: project_owner\nreviewers:\n  - {handle: al-vso-01, role: accredited_vso_representative, scope: [AL, US], added_on: 2026-11-01}\n"
        self.assertEqual(review.load_roster(roster_file(good))[0]["handle"], "al-vso-01")
        for bad in ("handle: Jane Doe", "handle: jane@example.org", "handle: al-vso-01, name: Jane",
                    "handle: al-vso-01, email: j@x.org"):
            text = good.replace("handle: al-vso-01", bad)
            with self.assertRaises(review.ReviewError, msg=bad):
                review.load_roster(roster_file(text))
        with self.assertRaises(review.ReviewError):
            review.load_roster(roster_file(good.replace("owner: project_owner", "owner: someone")))
        with self.assertRaises(review.ReviewError):
            review.load_roster(roster_file(good.replace("scope: [AL, US]", "scope: [Alabama]")))

    def test_the_shipped_roster_is_empty_and_owned_by_the_project_owner(self):
        self.assertEqual(review.load_roster(), [])


class Workflow(unittest.TestCase):
    HANDLES = ("test-al-01", "test-tx-01")

    @classmethod
    def setUpClass(cls):
        reg = default_registry()
        env = BenefitVaultAgent(reg, environment="development").match(
            {"facts": GUEST_AL}, Session(mode="A", tenant_ref="g"), dt.datetime(2026, 10, 29, 12, tzinfo=dt.timezone.utc))
        cls.record = next(i for i in env["items"] if i["outcome"] == "PRELIMINARY_MATCH" and i["jurisdiction"] == "AL")
        cls.content_hash = reg.benefits[cls.record["benefit_id"]].content_hash
        cls.registry_status = reg.benefits[cls.record["benefit_id"]].record_status
        reviewers = [{"handle": "test-al-01", "role": "accredited_vso_representative", "scope": ["AL", "US"],
                      "added_on": ON},
                     {"handle": "test-tx-01", "role": "state_veterans_agency", "scope": ["TX"], "added_on": ON}]
        with admin() as a:
            review.sync_roster(a, reviewers, ON)

    @classmethod
    def tearDownClass(cls):
        with admin() as a:
            if a.one("SELECT 1 AS x FROM ref.vault_benefit WHERE benefit_id = $1 AND record_status = 'VERIFIED'",
                     [cls.record["benefit_id"]]):
                review.withdraw(a, cls.record["benefit_id"], cls.registry_status, ON)
            a.query("DELETE FROM ref.vault_reviewer WHERE handle = ANY($1)", [list(cls.HANDLES)])

    def _match_production(self):
        app = create_app(settings(), clock=lambda: TODAY)       # reviews are applied at startup
        env = TestClient(app).post("/api/v1/vault/match", json={"facts": GUEST_AL}).json()
        return next(i for i in env["items"] if i["benefit_id"] == self.record["benefit_id"])

    def test_review_lifecycle(self):
        bid = self.record["benefit_id"]
        self.assertEqual(self._match_production()["outcome"], "HUMAN_REVIEW_REQUIRED")
        with admin() as a:
            with self.assertRaises(review.ReviewError):                       # not the content read
                review.verify(a, bid, "test-al-01", "0" * 64, ON)
            with self.assertRaises(DatabaseError):                            # out of scope
                review.verify(a, bid, "test-tx-01", self.content_hash, ON)
            with self.assertRaises(DatabaseError):                            # not on the roster
                review.verify(a, bid, "nobody-01", self.content_hash, ON)
            review.verify(a, bid, "test-al-01", self.content_hash, ON)
            log = a.query("SELECT action, handle FROM ref.vault_review_event WHERE benefit_id = $1 ORDER BY event_id", [bid])
            self.assertEqual([(r["action"], r["handle"]) for r in log][-1], ("VERIFIED", "test-al-01"))
            with self.assertRaises(DatabaseError):                            # the log is append-only
                a.query("UPDATE ref.vault_review_event SET handle = 'x-01' WHERE benefit_id = $1", [bid])
        item = self._match_production()
        self.assertEqual(item["outcome"], "PRELIMINARY_MATCH")
        self.assertEqual(item["verified_by"], "test-al-01")
        with admin() as a:
            review.withdraw(a, bid, self.registry_status, ON)
            log = a.query("SELECT action FROM ref.vault_review_event WHERE benefit_id = $1 ORDER BY event_id", [bid])
            self.assertEqual([r["action"] for r in log][-2:], ["VERIFIED", "WITHDRAWN"])
        self.assertEqual(self._match_production()["outcome"], "HUMAN_REVIEW_REQUIRED")

    def test_retired_reviewers_cannot_review_and_are_never_deleted(self):
        with admin() as a:
            out = review.sync_roster(a, [{"handle": "test-al-01", "role": "accredited_vso_representative",
                                          "scope": ["AL", "US"], "added_on": ON}], ON)
            self.assertIn("test-tx-01", out["retired"])
            row = a.one("SELECT active, retired_on FROM ref.vault_reviewer WHERE handle = 'test-tx-01'")
            self.assertEqual((row["active"], row["retired_on"]), (False, ON))
            # put it back for the other tests
            review.sync_roster(a, [{"handle": h, "role": "accredited_vso_representative",
                                    "scope": ["AL", "US"] if h == "test-al-01" else ["TX"], "added_on": ON}
                                   for h in self.HANDLES], ON)

    def test_queue_starts_with_alabama(self):
        with admin() as a:
            q = review.queue(a, 40)
        self.assertEqual(q[0]["jurisdiction"], "AL")
        self.assertTrue(all(r["record_status"] in ("UNVERIFIED", "SOURCE_CHECKED") for r in q))

    def test_app_role_cannot_read_the_roster_or_log(self):
        with connect(APP_DSN) as c:
            for table in ("ref.vault_reviewer", "ref.vault_review_event"):
                with self.assertRaises(DatabaseError, msg=table):
                    c.query(f"SELECT 1 FROM {table} LIMIT 1")
