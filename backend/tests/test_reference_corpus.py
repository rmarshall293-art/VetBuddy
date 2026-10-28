"""Slice 02: reference corpus integration.

Unit tests (no database) prove the validator rejects every class of bad row
it claims to; integration tests prove the database enforces the same rules
on its own (so they survive a bug in the loader), that the app role can read
but never write, and that the public API keeps crisis contacts first and
never returns a determination.
"""
import copy
import json
import re
import subprocess
import sys
import unittest

from app.domains.missions.task_library import TEMPLATES
from app.domains.reference import claims_boundary, corpus, service
from app.domains.reference.phone import normalize_phone
from app.infra.db import DatabaseError, connect
from app.platform.crisis_floor import REQUIRED_KEYS, crisis_floor_satisfied, load_crisis_contacts

from tests.support import ADMIN_DSN, APP_DSN, ApiCase

ROOT = corpus.ROOT
C = corpus.build()


class Phone(unittest.TestCase):
    def test_trailing_instruction_text_is_ignored(self):
        # Pinned defect A-6: a naive digit strip turned this into "9881".
        self.assertEqual(normalize_phone("988 (Press 1)"), "988")

    def test_short_codes_stay_bare(self):
        self.assertEqual(normalize_phone("838255"), "838255")
        self.assertEqual(normalize_phone("START to 88788"), "88788")

    def test_us_numbers_become_e164(self):
        self.assertEqual(normalize_phone("1-855-829-6636"), "+18558296636")
        self.assertEqual(normalize_phone("(334) 242-5077"), "+13342425077")
        self.assertEqual(normalize_phone("404-656-5893"), "+14046565893")

    def test_empty(self):
        self.assertIsNone(normalize_phone(None))
        self.assertIsNone(normalize_phone("no phone listed"))


class ClaimsBoundary(unittest.TestCase):
    BLOCKED = {
        "guarantee": ["You qualify for HUD-VASH.", "This is guaranteed.", "You're owed back pay."],
        "rating": ["You should be rated at 70%.", "This is worth 50%.", "Likely 70 percent."],
        "diagnosis": ["You have PTSD.", "This sounds like sleep apnea."],
        "representation": ["We'll file for you.", "Talk to your claim agent.", "We represent you."],
        "claim_coaching": ["Tell the examiner it hurts daily.", "Don't mention the old injury."],
    }
    ALLOWED = ["You may be eligible to explore this program.",
               "An accredited representative can file for you.",
               "VA's rating criteria for this are in 38 CFR 4.130.",
               "Talk to your health care provider about these symptoms."]

    def test_each_category_blocks_its_examples(self):
        for category, texts in self.BLOCKED.items():
            for t in texts:
                cats = {h.category for h in claims_boundary.scan(t)}
                self.assertIn(category, cats, t)

    def test_allowed_alternatives_pass(self):
        for t in self.ALLOWED:
            self.assertEqual(claims_boundary.scan(t), [], t)

    def test_phrase_level_not_exact_substring(self):
        # Normalization folds case, curly quotes and punctuation.
        self.assertTrue(claims_boundary.scan("YOU “QUALIFY”   FOR it"))

    def test_task_copy_is_clean(self):
        for key, t in TEMPLATES.items():
            for text in (t.title, t.why):
                self.assertEqual(claims_boundary.scan(text), [], f"{key}: {text}")

    def test_required_language_is_single_sourced(self):
        for key in ("standard_disclaimer", "vso_referral_block", "cfr_reference_label", "resume_label"):
            self.assertGreater(len(claims_boundary.required_text(key)), 40)
        self.assertIn("VA alone decides", claims_boundary.required_text("standard_disclaimer"))


class CorpusShape(unittest.TestCase):
    def test_dataset_counts_add_up(self):
        self.assertEqual(sum(d["record_count"] for d in C.datasets), sum(len(v) for v in C.tables.values()))
        self.assertEqual({d["dataset_id"] for d in C.datasets}, set(corpus.DATASET_FILES))

    def test_expected_coverage(self):
        t = C.tables
        kinds = {}
        for r in t["directory_entry"]:
            kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
        self.assertEqual(kinds["state_office"], 50)
        self.assertEqual(kinds["territory_dv_coalition"], 5)
        self.assertEqual(kinds["mst_residential"], 13)
        self.assertEqual(kinds["clinic"], 23)
        self.assertEqual(len(t["care_type"]), 17)
        self.assertEqual(len(t["state_summary"]), 51)
        self.assertEqual(len(t["duty_authority"]), 15)
        self.assertEqual(len(t["education_program"]), 22)
        self.assertEqual({r["rule_id"] for r in t["governance_rule"] if r["family"] == "agent_rule"},
                         {f"R{i}" for i in range(1, 23)})
        self.assertEqual({r["rule_id"] for r in t["governance_rule"] if r["family"] == "tier0"},
                         {f"T0-{i:02d}" for i in range(1, 13)})

    def test_nothing_is_verified_and_no_rate_is_kernel_usable(self):
        for table, rows in C.tables.items():
            for r in rows:
                self.assertNotEqual(r.get("status"), "VERIFIED", f"{table}: {r}")
        self.assertEqual(corpus.kernel_usable_rates(C), [])

    def test_money_is_integer_cents(self):
        for r in C.tables["rate"]:
            self.assertIsInstance(r["amount_cents"], int)
        va = {(r["dims"].get("dependents"), r["dims"].get("rating")): r for r in C.tables["rate"]
              if r["rate_set"] == "va_comp_2025"}
        self.assertEqual(va[("veteran_alone", 100)]["amount_cents"], 383130)
        self.assertEqual(va[("veteran_alone", 70)]["status"], "CONTESTED")
        # Missing cells are absent, never interpolated.
        self.assertNotIn(("with_spouse_and_one_child", 40), va)

    def test_illustrative_and_heuristic_are_labelled(self):
        bah = [r for r in C.tables["rate"] if r["rate_set"] == "bah_sample_2025"]
        self.assertEqual(len(bah), 50)
        self.assertTrue(all(r["status"] == "ILLUSTRATIVE" and r["rounded"] for r in bah))
        heur = [r for r in C.tables["rule_lead"] if r["lead_id"] == "fin.income_replacement"]
        self.assertEqual(heur[0]["status"], "HEURISTIC")

    def test_no_personal_fields_in_state_offices(self):
        allowed = {"id", "jurisdiction", "agency", "program", "phone", "url", "mailbox", "dedicated_coordinator",
                   "caveat", "note"}
        for r in C.raw["women_veterans"]["state_offices"]:
            self.assertLessEqual(set(r), allowed, r["id"])

    def test_every_territory_has_a_dv_coalition(self):
        codes = {r["jurisdiction_code"] for r in C.tables["directory_entry"] if r["kind"] == "territory_dv_coalition"}
        self.assertEqual(codes, {"PR", "GU", "VI", "AS", "MP"})

    def test_contested_conflicts_keep_all_readings(self):
        for r in C.tables["conflict"]:
            if r["status"] == "contested_unresolved":
                self.assertGreaterEqual(len(r["readings"]), 2, r["conflict_id"])


class CrisisFloorSingleAuthorship(unittest.TestCase):
    def test_floor_merged_and_satisfied(self):
        keys = {c["key"] for c in load_crisis_contacts()}
        self.assertTrue(REQUIRED_KEYS <= keys)
        self.assertTrue(crisis_floor_satisfied())

    def test_retired_number_absent_everywhere(self):
        for c in load_crisis_contacts():
            for value in c.values():
                self.assertNotIn("273-8255", str(value), c["key"])
                self.assertNotEqual(normalize_phone(str(value)), "+18002738255", c["key"])
        for r in C.tables["directory_entry"]:
            self.assertNotEqual(r["phone_e164"], "+18002738255")

    def test_generated_copy_matches_the_authored_floor(self):
        js = (ROOT / "web/kernel_data.js").read_text()
        kdata = json.loads(js.split("export const KDATA = ", 1)[1].rstrip().rstrip(";"))
        self.assertEqual(kdata["CRISIS_CONTACTS"], load_crisis_contacts())

    def test_directory_entry_sharing_a_floor_number_says_so(self):
        wvcc = next(r for r in C.tables["directory_entry"] if r["entry_id"] == "nat.va.wvcc")
        self.assertEqual(wvcc["also_in_crisis_floor"], "women_veterans_call_center")


class ValidatorRejects(unittest.TestCase):
    """Each mutation is a class of defect the integration must never let in."""

    def mutate(self, fn):
        c = copy.deepcopy(C)
        fn(c.tables)
        with self.assertRaises(corpus.CorpusError) as ctx:
            corpus.validate(c)
        return str(ctx.exception)

    def _entry(self, t, entry_id):
        return next(r for r in t["directory_entry"] if r["entry_id"] == entry_id)

    def test_retired_crisis_number(self):
        def f(t):
            e = self._entry(t, "nat.np.nchv")
            e["phone"], e["phone_e164"] = "1-800-273-8255", "+18002738255"
        self.assertIn("RETIRED", self.mutate(f))

    def test_undeclared_crisis_floor_duplicate(self):
        def f(t):
            self._entry(t, "nat.va.wvcc")["also_in_crisis_floor"] = None
        self.assertIn("duplicates crisis floor", self.mutate(f))

    def test_personal_mailbox(self):
        def f(t):
            self._entry(t, "st.IL.coord")["mailbox"] = "jane.doe@illinois.gov"
        self.assertIn("personal mailbox", self.mutate(f))

    def test_same_organization_and_place(self):
        def f(t):
            dup = dict(self._entry(t, "cvn.TX.killeen"))
            dup["entry_id"] = "cvn.TX.killeen2"
            t["directory_entry"].append(dup)
        self.assertIn("same organization+place", self.mutate(f))

    def test_phone_alone_is_not_a_duplicate(self):
        # Hinesville GA and Jacksonville FL share a number; both survive.
        ids = {r["entry_id"] for r in C.tables["directory_entry"]}
        self.assertTrue({"cvn.GA.hinesville", "cvn.FL.jacksonville"} <= ids)

    def test_unregistered_source(self):
        def f(t):
            t["statistic"][0]["source_ids"] = ["src.rr.not_a_source"]
        self.assertIn("unregistered source", self.mutate(f))

    def test_verified_without_reviewer(self):
        def f(t):
            t["timeline_window"][0]["status"] = "VERIFIED"
        self.assertIn("without a named reviewer", self.mutate(f))

    def test_float_money(self):
        def f(t):
            t["rate"][0]["amount_cents"] = 1759.19
        self.assertIn("integer cents", self.mutate(f))

    def test_single_reading_conflict(self):
        def f(t):
            t["conflict"][0]["readings"] = t["conflict"][0]["readings"][:1]
        self.assertIn("fewer than two readings", self.mutate(f))

    def test_contested_lead_without_conflict(self):
        def f(t):
            lead = next(r for r in t["benefit_lead"] if r["status"] == "CONTESTED")
            lead["conflict_id"] = None
        self.assertIn("CONTESTED without a conflict id", self.mutate(f))

    def test_prohibited_language(self):
        def f(t):
            self._entry(t, "nat.np.final_salute")["eligibility_note"] = "You qualify for H.O.M.E. housing."
        self.assertIn("prohibited guarantee language", self.mutate(f))

    def test_unknown_jurisdiction(self):
        def f(t):
            t["benefit_lead"][0]["jurisdiction_code"] = "ZZ"
        self.assertIn("unknown jurisdiction", self.mutate(f))

    def test_non_ascii_id(self):
        def f(t):
            t["finding"][0]["finding_id"] = "al.advа"
        self.assertIn("malformed id", self.mutate(f))


class GeneratedSeedCurrent(unittest.TestCase):
    def test_build_check(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts/build_reference.py"), "--check"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)


# ── database ─────────────────────────────────────────────────────────────────

class DatabaseEnforces(unittest.TestCase):
    """The database refuses bad rows by itself (survives a loader bug)."""

    def refuse(self, sql: str, params=()):
        with connect(ADMIN_DSN) as conn:
            conn.query("BEGIN")
            try:
                with self.assertRaises(DatabaseError):
                    conn.query(sql, list(params))
            finally:
                conn.query("ROLLBACK")

    def test_counts_match_corpus(self):
        with connect(APP_DSN) as conn:
            for table, rows in C.tables.items():
                n = conn.one(f"SELECT count(*) AS n FROM ref.{table}")["n"]
                self.assertEqual(n, len(rows), table)

    def test_app_role_cannot_write(self):
        with connect(APP_DSN) as conn:
            for sql in ("INSERT INTO ref.care_type VALUES ('wv_x', 'x')",
                        "UPDATE ref.rate SET amount_cents = 0",
                        "DELETE FROM ref.conflict"):
                with self.assertRaises(DatabaseError):
                    conn.query(sql)

    def test_verified_needs_a_named_reviewer(self):
        self.refuse("UPDATE ref.timeline_window SET status = 'VERIFIED' WHERE window_id = 'tl.tap_start'")

    def test_leads_and_statistics_can_never_be_verified(self):
        self.refuse("UPDATE ref.benefit_lead SET status = 'VERIFIED' WHERE lead_id = 'sb.TX.income'")
        self.refuse("UPDATE ref.statistic SET status = 'VERIFIED' WHERE stat_id = 'stat.al.vet_unemployment_2024'")

    def test_retired_crisis_number_refused(self):
        self.refuse("UPDATE ref.directory_entry SET phone_e164 = '+18002738255' WHERE entry_id = 'nat.np.nchv'")

    def test_unregistered_source_refused(self):
        self.refuse("UPDATE ref.statistic SET source_ids = ARRAY['src.nope'] WHERE stat_id = 'stat.wv.enrollment'")

    def test_single_reading_conflict_refused(self):
        self.refuse("UPDATE ref.conflict SET readings = '[{\"value\":\"x\"}]'::jsonb "
                    "WHERE conflict_id = 'conflict.tx.hazlewood_legacy_age'")

    def test_contested_lead_needs_conflict(self):
        self.refuse("UPDATE ref.benefit_lead SET conflict_id = NULL WHERE lead_id = 'sb.TX.hazlewood_legacy'")

    def test_natural_key_dedupe(self):
        self.refuse("INSERT INTO ref.directory_entry (entry_id, kind, jurisdiction_code, name, place, status, source_ids) "
                    "VALUES ('dup', 'clinic', 'TX', 'COHEN VETERANS NETWORK CLINIC', 'killeen', 'UNVERIFIED', "
                    "ARRAY['src.rr.women_veterans_50_state'])")

    def test_unknown_care_type_refused(self):
        self.refuse("UPDATE ref.directory_entry SET care_types = ARRAY['wv_nope'] WHERE entry_id = 'nat.np.nchv'")

    def test_status_vocabulary_matches_python(self):
        # RG-08: CHECK constraints match Python enums.
        with connect(ADMIN_DSN) as conn:
            src = conn.one("SELECT pg_get_constraintdef(c.oid) AS d FROM pg_constraint c "
                           "JOIN pg_type t ON t.oid = c.contypid JOIN pg_namespace n ON n.oid = t.typnamespace "
                           "WHERE n.nspname = 'ref' AND t.typname = 'record_status'")["d"]
        self.assertEqual(set(re.findall(r"'([A-Z_]+)'", src)), set(corpus.STATUSES))

    def test_seed_is_idempotent(self):
        sql = (ROOT / "database/seeds/0011_reference.sql").read_text()
        with connect(ADMIN_DSN) as conn:
            before = conn.query("SELECT dataset_id, sha256, record_count FROM ref.dataset ORDER BY 1")
            conn.execute_script(sql)
            after = conn.query("SELECT dataset_id, sha256, record_count FROM ref.dataset ORDER BY 1")
        self.assertEqual(before, after)


class ReferenceApi(ApiCase):
    def test_overview_is_honest(self):
        j = self.client.get("/api/v1/reference").json()
        self.assertEqual(j["records_verified_by_a_named_human"], 0)
        self.assertEqual(j["coverage"]["verified"], 0)
        self.assertEqual(len(j["datasets"]), len(corpus.DATASET_FILES))
        self.assertIn("VA alone decides", j["notice"])

    def test_crisis_contacts_lead_every_directory_answer(self):
        for q in ("", "?jurisdiction=AL", "?jurisdiction=PR&care_type=wv_dv_ipv", "?care_type=wv_mst"):
            j = self.client.get("/api/v1/reference/women-veterans" + q).json()
            self.assertEqual(list(j)[0], "crisis_contacts")
            self.assertEqual({c["key"] for c in j["crisis_contacts"]} & REQUIRED_KEYS, REQUIRED_KEYS)

    def test_care_type_filter_and_local_rows(self):
        j = self.client.get("/api/v1/reference/women-veterans?jurisdiction=PR&care_type=wv_dv_ipv").json()
        self.assertTrue(all("wv_dv_ipv" in e["care_types"] for e in j["entries"]))
        self.assertEqual(j["local_count"], 1)
        self.assertIn("disclaimer", j["jurisdiction"])

    def test_gap_is_stated_not_hidden(self):
        # DC has no state-office row in the corpus: say so, never imply absence of services.
        j = self.client.get("/api/v1/reference/women-veterans?jurisdiction=DC").json()
        self.assertEqual(j["local_count"], 0)
        self.assertIn("not that there is nothing", j["coverage_note"])

    def test_unknown_inputs_are_404(self):
        self.assertEqual(self.client.get("/api/v1/reference/women-veterans?jurisdiction=ZZ").status_code, 404)
        self.assertEqual(self.client.get("/api/v1/reference/women-veterans?care_type=wv_nope").status_code, 404)
        self.assertEqual(self.client.get("/api/v1/reference/jurisdictions/ZZ").status_code, 404)

    def test_jurisdiction_profile_never_decides(self):
        r = self.client.get("/api/v1/reference/jurisdictions/TX")
        j = r.json()
        self.assertEqual(j["lead_label"], service.LEAD_LABEL)
        self.assertEqual({c["conflict_id"] for c in j["conflicts"]},
                         {"conflict.tx.hazlewood_legacy_age", "conflict.tx.hazlewood_dependent_hours"})
        self.assertNotRegex(r.text, r'"eligible"\s*:')

    def test_guard_reserve_drill_does_not_count(self):
        j = self.client.get("/api/v1/reference/guard-reserve").json()
        q = {a["authority_id"]: a["qualifies_ch33"] for a in j["authorities"]}
        self.assertEqual(len(q), 15)
        self.assertFalse(q["a13"] or q["a14"] or q["a15"])
        self.assertTrue(all(lead["status"] != "VERIFIED" for lead in j["rule_leads"]))

    def test_reference_reads_need_no_account(self):
        self.assertEqual(self.client.get("/api/v1/reference/conflicts").status_code, 200)
