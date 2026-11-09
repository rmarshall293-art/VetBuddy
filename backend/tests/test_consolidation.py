"""Single authorship after the consolidation: the integrated record and the
guest app restate nothing that exists as data; they are generated from it."""
import html
import json
import re
import sys
import unittest
from pathlib import Path

from app.domains.reference import claims_boundary

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import build_web  # noqa: E402


def _ref(name):
    return json.loads((ROOT / "data/reference" / f"{name}.json").read_text())


def _text(page: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", page))


class RecordGenerated(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = (ROOT / "dist/vetbuddy-record.html").read_text()
        cls.text = " ".join(_text(cls.page).split())

    def test_no_unfilled_slots(self):
        self.assertEqual(re.findall(r"<!--@@[A-Z_]+@@-->", self.page), [])

    def test_every_governance_rule_and_status_is_rendered(self):
        gov = _ref("governance")
        for r in gov["agent_rules"] + gov["tier0_rules"]:
            with self.subTest(rule=r["id"]):
                self.assertIn(" ".join(html.unescape(r["rule"]).split()), self.text)
                self.assertIn(build_web.REPO_PILL[r["repo_status"]][1], self.text)
        for g in gov["release_gates"]:
            self.assertIn(g["id"], self.text)

    def test_every_conflict_is_rendered(self):
        for r in _ref("conflicts")["records"]:
            with self.subTest(conflict=r["id"]):
                self.assertIn(" ".join(r["subject"].split()), self.text)

    def test_counts_match_the_repository(self):
        self.assertIn(f"{build_web.count_tests():,} backend tests", self.text)
        self.assertIn(f"{len(list((ROOT / 'database/migrations').glob('*.sql')))} migrations", self.text)

    def test_crisis_banner_comes_from_the_floor(self):
        from app.platform.crisis_floor import load_crisis_contacts
        for c in load_crisis_contacts():
            self.assertIn(c["label"], self.text)
        self.assertNotIn("1-800-273-8255", self.page)

    def test_retired_record_files_are_gone(self):
        for p in ("docs/integrated-record.html", "docs/INTEGRATED_RECORD.md", "docs/reference",
                  "dist/vetbuddy-reference.html", "dist/vetbuddy-artifact.html", "docs/SOURCES.md", "docs/BACKLOG.md",
                  "backend/app/api/routers"):
            self.assertFalse((ROOT / p).exists(), p)


class GuestAppSingleAuthorship(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = (ROOT / "web/standalone.html").read_text()
        kd = (ROOT / "web/kernel_data.js").read_text()
        cls.kdata = json.loads(kd[kd.index("{"):kd.rindex("}") + 1])

    def test_windows_are_the_corpus_windows(self):
        self.assertEqual(self.kdata["TIMELINE"]["windows"], _ref("transition_timeline")["windows"])

    def test_template_holds_no_hand_copied_facts(self):
        for literal in ("1 year and 120 days", "240 days", "find-rep", "Benefits Delivery at Discharge",
                        "Higher-Level Review", "VetBuddy is not VA", "fees for an initial claim"):
            with self.subTest(literal=literal):
                self.assertNotIn(literal, self.template)

    def test_required_language_is_the_config(self):
        for key in ("standard_disclaimer", "common_notice", "vso_referral_block", "vso_search_url"):
            self.assertEqual(self.kdata["LANGUAGE"][key], claims_boundary.required_text(key))

    def test_rules_and_lane_are_governance_data(self):
        gov = _ref("governance")
        self.assertEqual(self.kdata["AGENT_RULES"], gov["agent_rules"])
        self.assertEqual(self.kdata["LEGAL_LANE"], gov["legal_lane"])
        self.assertEqual(self.kdata["NON_NEGOTIABLES"], gov["non_negotiables"])

    def test_every_shown_source_is_registered(self):
        ids = {r["id"] for r in _ref("sources")["records"]}
        for w in self.kdata["TIMELINE"]["windows"]:
            for s in w["sources"]:
                self.assertIn(s, ids)
                self.assertIn(s, self.kdata["SOURCES"])

    def test_legal_lane_language_is_clean(self):
        for r in _ref("governance")["legal_lane"]:
            self.assertIn(r["allowed"], ("yes", "share_card", "no"))
            self.assertEqual(claims_boundary.scan(r["activity"]), [], r["activity"])
        for w in _ref("transition_timeline")["windows"]:
            self.assertEqual(claims_boundary.scan(w["item"]), [], w["id"])


class ReleaseGates(unittest.TestCase):
    """v6 §4/§15: draft legal copy and invented operator details never ship."""

    def test_draft_privacy_notice_is_not_rendered_while_operator_unset(self):
        lang = claims_boundary.language()
        self.assertIsNone(lang["legal_operator"], "setting this needs counsel's sign-off, not a code change")
        draft = " ".join(lang["privacy_notice_draft"].split())
        probe = draft[:80]
        pages = [ROOT / "dist/vetbuddy.html", ROOT / "dist/vetbuddy-record.html", ROOT / "web/kernel_data.js",
                 *(ROOT / "web").glob("*.html"), *(ROOT / "web").glob("*.js")]
        for page in pages:
            with self.subTest(page=page.name):
                self.assertNotIn(probe, " ".join(page.read_text().split()))

    def test_no_invented_domain_or_operator_in_pages(self):
        # The legal operator is undecided (release blocker): no page may name a
        # company (any LLC / Inc. / Corp. form) or claim a final domain.
        operator = __import__("re").compile(r"\b(llc|l\.l\.c\.|inc\.|corp\.|incorporated)\b")
        for page in (ROOT / "dist/vetbuddy.html", ROOT / "web/app.js", ROOT / "web/index.html"):
            text = page.read_text().lower()
            with self.subTest(page=page.name):
                self.assertNotIn("vetbuddy.com", text)
                self.assertIsNone(operator.search(text), page.name)


if __name__ == "__main__":
    unittest.main()
