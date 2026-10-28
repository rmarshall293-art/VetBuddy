"""Migration 0014 and its seed on PostgreSQL.

Covers the seed (exact copy of the registry, idempotent, keeps VERIFIED only
for unchanged content, prunes old rows), the governance pins in SQL,
privileges and row-level security, the grant rules, the hash-chained ledger
(Python verifies the database's chain; forging, concurrent appends and
tampering), saved benefits and discard, the agent and HTTP routes running on
the database store, and account deletion through slice 03's vb_delete_account.

Every test that counts tenant rows makes its own tenant (``new_tenant``).
"""
from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest

from app.infra import pg_compat  # noqa: E402
from app.infra.pg_compat import errors  # noqa: E402  (psycopg 3 surface over the repo driver, ADR 0005)
from starlette.applications import Starlette  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

from app.domains.vault.agent import BenefitVaultAgent, Session  # noqa: E402
from app.domains.vault.api import PREFIX, routes  # noqa: E402
from app.domains.vault.governance.grants import new_grant  # noqa: E402
from app.domains.vault.governance.ledger import verify_chain  # noqa: E402
from app.domains.vault.governance.manifests import ManifestSet  # noqa: E402
from app.domains.vault.vault_store import StoreError, VaultStore, load_reviews  # noqa: E402

from vault_support import AS_OF, MIGRATION, MIGRATIONS, NOW, SEED  # noqa: E402

REF_TABLES = ("vault_registry_meta", "vault_jurisdiction", "vault_source", "vault_fact", "vault_benefit",
              "vault_rule_lead", "vault_benefit_lead", "vault_caveat", "vault_license_reciprocity",
              "vault_agent_manifest", "vault_agent_exposure")
STAMPED = ("vault_jurisdiction", "vault_source", "vault_fact", "vault_benefit", "vault_rule_lead", "vault_caveat",
           "vault_license_reciprocity", "vault_agent_manifest")
TENANT_TABLES = ("vault_pull_grant", "vault_pull_ledger", "vault_saved_benefit")


# ── helpers ───────────────────────────────────────────────────────────────

def one(conn, sql, params=None):
    return conn.execute(sql, params).fetchone()


def as_tenant(conn, tenant):
    conn.execute("SELECT set_config('vetbuddy.tenant_id', %s, true)", (tenant,))


def refused(conn, error, sql, params=None, tenant=None):
    """Run one statement in its own transaction and expect ``error``."""
    with pytest.raises(error):
        with conn.transaction():
            if tenant is not None:
                as_tenant(conn, tenant)
            conn.execute(sql, params)


def digest(conn, table):
    return one(conn, f"SELECT count(*), md5(coalesce(string_agg(t::text, E'\\n' ORDER BY t::text), ''))"
                     f" FROM ref.{table} t")


def account_grant(registry, tenant, source="service_profile_agent", keys=("service_status", "component"), now=NOW):
    return new_grant(ManifestSet.from_registry(registry), registry.governance, tenant_ref=tenant,
                     source_agent=source, fact_keys=keys, purpose="benefit_matching", mode="B", now=now)


def append(store, tenant, i=0, **overrides):
    fields = dict(tenant_ref=tenant, occurred_at=NOW + timedelta(microseconds=i), event="PULL_ALLOWED",
                  requester="benefit_vault_agent", source_agent="service_profile_agent", purpose="benefit_matching",
                  fact_keys=["service_status", "component"], grant_id=str(uuid.uuid4()),
                  packet_id=str(uuid.uuid4()), reason="ALLOWED")
    fields.update(overrides)
    return store.append(**fields)


class Provider:
    def __init__(self, values):
        self.values = values
        self.calls = []

    def provide(self, tenant_ref, keys):
        self.calls.append(sorted(keys))
        return dict(self.values)


@pytest.fixture(scope="module")
def seedtest(pg):
    """A second database for tests that reseed or change reference rows."""
    pg.build("vault_seedtest")
    yield "vault_seedtest"
    pg.drop_db("vault_seedtest")


# ── the migration and the seed ────────────────────────────────────────────

def test_seed_is_an_exact_copy_of_the_registry(pg, registry):
    with pg.connect() as conn:
        assert one(conn, "SELECT registry, version, as_of::text, sha256 FROM ref.vault_registry_meta") == (
            "vetbuddy.benefit_vault_registry", registry.version, registry.as_of, registry.sha256)
        for table in STAMPED:
            stale = one(conn, f"SELECT count(*) FROM ref.{table} WHERE registry_sha256 <> %s", (registry.sha256,))
            assert stale == (0,), table
        stored = {r[0]: r[1:] for r in conn.execute(
            "SELECT benefit_id, content_hash, rule, record_status, jurisdiction, category, kind, source_id"
            " FROM ref.vault_benefit")}
        assert stored == {b.benefit_id: (b.content_hash, b.rule, b.record_status, b.jurisdiction, b.category,
                                         b.kind, b.source_id) for b in registry.benefits.values()}
        assert {r[0] for r in conn.execute("SELECT source_id FROM ref.vault_source")} == set(registry.sources)
        counts = dict(conn.execute("SELECT code, benefit_count FROM ref.vault_jurisdiction").fetchall())
        assert counts == {code: j["benefit_count"] for code, j in registry.jurisdictions.items()}
        assert counts["AS"] == 0 and one(conn, "SELECT coverage FROM ref.vault_jurisdiction WHERE code = 'AS'") == (
            "SOURCE_NOT_AVAILABLE",)
        facts = {r[0]: r[1:] for r in conn.execute("SELECT fact_key, data_class, pullable FROM ref.vault_fact")}
        assert facts == {k: (v["data_class"], v["pullable"]) for k, v in registry.data["facts"].items()}
        exposures = set(conn.execute("SELECT agent_id, fact_key, data_class FROM ref.vault_agent_exposure"))
        assert exposures == {(a["agent_id"], e["fact_key"], e["data_class"]) for a in registry.agents
                             for e in a["exposes"]}
        links = set(conn.execute("SELECT benefit_id, lead_id FROM ref.vault_benefit_lead"))
        assert links == {(b.benefit_id, lead) for b in registry.benefits.values() for lead in b.lead_ids}
        assert conn.execute("SELECT agent_id FROM ref.vault_agent_manifest WHERE may_pull_from_agents").fetchall() == [
            ("benefit_vault_agent",)]
        assert one(conn, "SELECT count(*) FROM ref.vault_agent_manifest WHERE may_issue_determinations") == (0,)
        assert one(conn, "SELECT count(*) FROM ref.vault_benefit WHERE record_status = 'VERIFIED'") == (0,)


def test_postcheck_refuses_weakened_privileges(pg):
    pg.create_db("vault_postcheck")
    for path in MIGRATIONS:              # the real slice 03 chain up to 0013
        if path == MIGRATION:
            break
        pg.run_file(path, dbname="vault_postcheck")
    text = MIGRATION.read_text(encoding="utf-8")
    weakened = text.replace("GRANT SELECT, INSERT ON public.vault_pull_grant TO vetbuddy_app;",
                            "GRANT SELECT, INSERT, DELETE ON public.vault_pull_grant TO vetbuddy_app;")
    assert weakened != text
    with pytest.raises(errors.RaiseException, match="tenant table rule violated by: vault_pull_grant"):
        pg.run_file(MIGRATION, dbname="vault_postcheck", text=weakened)
    weakened = text.replace("GRANT SELECT ON ref.vault_registry_meta,", "GRANT SELECT, UPDATE ON ref.vault_registry_meta,")
    assert weakened != text
    with pytest.raises(errors.RaiseException, match="reference tables writable by vetbuddy_app"):
        pg.run_file(MIGRATION, dbname="vault_postcheck", text=weakened)
    # Forgetting the purger grant would leave rows account deletion cannot remove.
    weakened = text.replace("GRANT SELECT, DELETE ON public.vault_pull_grant, public.vault_pull_ledger, "
                            "public.vault_saved_benefit\n  TO vetbuddy_purger;",
                            "GRANT SELECT, DELETE ON public.vault_pull_grant, public.vault_pull_ledger\n  TO vetbuddy_purger;")
    assert weakened != text
    with pytest.raises(errors.RaiseException, match="account deletion cannot reach: vault_saved_benefit"):
        pg.run_file(MIGRATION, dbname="vault_postcheck", text=weakened)
    pg.drop_db("vault_postcheck")


def test_seed_is_idempotent(pg, seedtest):
    with pg.connect(dbname=seedtest) as conn:
        before = {t: digest(conn, t) for t in REF_TABLES}
    pg.run_file(SEED, dbname=seedtest)
    with pg.connect(dbname=seedtest) as conn:
        assert {t: digest(conn, t) for t in REF_TABLES} == before


def test_verified_needs_a_named_reviewer_and_unchanged_content(pg, seedtest, registry):
    benefit = registry.benefits["us.fry-scholarship"]
    mark = ("UPDATE ref.vault_benefit SET record_status = 'VERIFIED', verified_by = %s, verified_on = '2026-10-28',"
            " verified_content_hash = %s WHERE benefit_id = %s")
    with pg.connect(dbname=seedtest) as conn:
        refused(conn, errors.CheckViolation, "UPDATE ref.vault_benefit SET record_status = 'VERIFIED'"
                                             " WHERE benefit_id = %s", (benefit.benefit_id,))
        refused(conn, errors.CheckViolation, mark, ("  ", benefit.content_hash, benefit.benefit_id))
        refused(conn, errors.CheckViolation, mark, ("Jane Doe", benefit.content_hash, benefit.benefit_id))
        refused(conn, errors.CheckViolation, mark, ("reviewer@example.org", benefit.content_hash, benefit.benefit_id))
        refused(conn, errors.CheckViolation, mark, ("reviewer-01", "0" * 64, benefit.benefit_id))
        refused(conn, errors.CheckViolation, "UPDATE ref.vault_benefit SET verified_by = 'reviewer-01'"
                                             " WHERE benefit_id = %s", (benefit.benefit_id,))
        with conn.transaction():
            conn.execute(mark, ("reviewer-01", benefit.content_hash, benefit.benefit_id))
    # Reseeding the same registry keeps the mark.
    pg.run_file(SEED, dbname=seedtest)
    with pg.connect(dbname=seedtest) as conn:
        row = one(conn, "SELECT record_status, verified_by, verified_content_hash FROM ref.vault_benefit"
                        " WHERE benefit_id = %s", (benefit.benefit_id,))
        reviews = load_reviews(conn)
    assert row == ("VERIFIED", "reviewer-01", benefit.content_hash)
    assert [(r.benefit_id, r.verified_by, r.verified_on) for r in reviews] == [
        (benefit.benefit_id, "reviewer-01", "2026-10-28")]
    reviewed = registry.with_reviews(reviews)
    assert reviewed.benefits[benefit.benefit_id].record_status == "VERIFIED" and reviewed.stale_reviews == ()
    assert registry.benefits[benefit.benefit_id].record_status == benefit.record_status
    # A registry in which this record's content changed: the mark falls away.
    changed = SEED.read_text(encoding="utf-8").replace(benefit.content_hash, "f" * 64)
    pg.run_file(SEED, dbname=seedtest, text=changed)
    with pg.connect(dbname=seedtest) as conn:
        row = one(conn, "SELECT record_status, verified_by, verified_on, verified_content_hash, content_hash"
                        " FROM ref.vault_benefit WHERE benefit_id = %s", (benefit.benefit_id,))
        assert load_reviews(conn) == []
    assert row == (benefit.record_status, None, None, None, "f" * 64)
    pg.run_file(SEED, dbname=seedtest)
    with pg.connect(dbname=seedtest) as conn:
        assert one(conn, "SELECT record_status, content_hash FROM ref.vault_benefit WHERE benefit_id = %s",
                   (benefit.benefit_id,)) == (benefit.record_status, benefit.content_hash)


def test_seed_prunes_rows_from_older_registries(pg, seedtest):
    old = "1" * 64
    with pg.connect(dbname=seedtest) as conn:
        with conn.transaction():
            conn.execute("INSERT INTO ref.vault_source (source_id, url, page_status, tier, opened_on, registry_sha256)"
                         " VALUES ('src.retired-page', 'https://example.org/retired', 'OPENED', 1, '2026-01-02', %s)",
                         (old,))
            conn.execute(
                "INSERT INTO ref.vault_benefit (benefit_id, jurisdiction, category, kind, title, groups, rule,"
                " rule_tokens, who_it_is_for, value, official_url, official_url_status, source_id, source_tier,"
                " record_status, content_hash, ledger_ref, registry_sha256) VALUES ('tx.retired-record', 'TX',"
                " 'PARKS', 'STATE_BENEFIT', 'Retired record', ARRAY['vet'], 'vet', ARRAY['vet'], 'Veterans',"
                " 'A pass', 'https://example.org/retired', 'SAME_AS_SOURCE', 'src.retired-page', 1, 'UNVERIFIED',"
                " %s, 'states/batch06_TN-WA.psv:1', %s)", (old, old))
            conn.execute("INSERT INTO ref.vault_caveat (caveat_id, text, registry_sha256)"
                         " VALUES ('retired_caveat', 'Old text.', %s)", (old,))
            conn.execute("INSERT INTO ref.vault_agent_manifest (agent_id, name, plane, role, highest_class_held,"
                         " registry_sha256) VALUES ('retired_agent', 'Retired', 2, 'retired', 'V1', %s)", (old,))
            conn.execute("INSERT INTO ref.vault_agent_exposure VALUES ('retired_agent', 'age', 'V1')")
    pg.run_file(SEED, dbname=seedtest)
    with pg.connect(dbname=seedtest) as conn:
        for table, key, value in (("vault_benefit", "benefit_id", "tx.retired-record"),
                                  ("vault_source", "source_id", "src.retired-page"),
                                  ("vault_caveat", "caveat_id", "retired_caveat"),
                                  ("vault_agent_manifest", "agent_id", "retired_agent"),
                                  ("vault_agent_exposure", "agent_id", "retired_agent")):
            assert one(conn, f"SELECT count(*) FROM ref.{table} WHERE {key} = %s", (value,)) == (0,), table


def test_governance_pins_hold_in_sql(pg, seedtest):
    statements = (
        "UPDATE ref.vault_agent_manifest SET may_issue_determinations = true WHERE agent_id = 'benefit_vault_agent'",
        "UPDATE ref.vault_agent_manifest SET may_pull_from_agents = true WHERE agent_id = 'household_agent'",
        "INSERT INTO ref.vault_agent_manifest (agent_id, name, plane, role, may_pull_from_agents, highest_class_held,"
        " registry_sha256) VALUES ('second_puller', 'x', 2, 'x', true, 'V1', repeat('0', 64))",
        "INSERT INTO ref.vault_agent_exposure VALUES ('household_agent', 'severe_disability', 'V2')",
        "INSERT INTO ref.vault_agent_exposure VALUES ('household_agent', 'va_rating', 'V1')",
        "INSERT INTO ref.vault_agent_exposure VALUES ('benefit_vault_agent', 'age', 'V1')",
        "INSERT INTO ref.vault_agent_exposure VALUES ('crisis_support_agent', 'age', 'V3')",
        "UPDATE ref.vault_agent_exposure SET data_class = 'V2' WHERE agent_id = 'household_agent' AND fact_key = 'age'",
        "UPDATE ref.vault_fact SET pullable = true WHERE fact_key = 'severe_disability'",
        "UPDATE ref.vault_fact SET session_only = true WHERE fact_key = 'age'",
        "UPDATE ref.vault_benefit SET official_url_status = 'SEEN_IN_SEARCH', record_status = 'SOURCE_CHECKED'"
        " WHERE benefit_id = 'us.fry-scholarship'",
        "UPDATE ref.vault_benefit SET category = 'SCHOLARSHIP' WHERE benefit_id LIKE 'tx.%'",
    )
    with pg.connect(dbname=seedtest) as conn:
        for sql in statements:
            refused(conn, errors.CheckViolation, sql)


def test_every_vault_function_pins_its_search_path(pg):
    with pg.connect() as conn:
        rows = conn.execute(
            "SELECT p.oid::regprocedure::text, p.prosecdef, p.proconfig FROM pg_proc p"
            " JOIN pg_namespace n ON n.oid = p.pronamespace"
            " WHERE n.nspname IN ('public', 'ref') AND (p.proname LIKE 'vault%' OR p.proname = 'vb_vault_discard')"
        ).fetchall()
    assert len(rows) == 7          # six trigger functions and vb_vault_discard
    for name, definer, config in rows:
        assert config and any(c.startswith("search_path=pg_catalog, public") for c in config), name
        if definer:
            assert "search_path=pg_catalog, public, pg_temp" in config, name
    assert [name for name, definer, _ in rows if definer] == ["vb_vault_discard(text,uuid)"]
    with pg.connect() as conn:
        # Like slice 03's deletion functions, it runs as the RLS-bound purger, never the schema owner.
        owner = one(conn, "SELECT pg_get_userbyid(proowner) FROM pg_proc WHERE proname = 'vb_vault_discard'")
    assert owner == ("vetbuddy_purger",)


# ── privileges and row-level security ─────────────────────────────────────

def test_reference_tables_are_read_only_for_the_app(app_conn, registry):
    with app_conn.transaction():
        assert one(app_conn, "SELECT count(*) FROM ref.vault_benefit") == (len(registry.benefits),)
    for sql in ("UPDATE ref.vault_benefit SET title = 'x'",
                "UPDATE ref.vault_benefit SET record_status = 'VERIFIED', verified_by = 'x', verified_on = current_date,"
                " verified_content_hash = content_hash",
                "DELETE FROM ref.vault_source",
                "INSERT INTO ref.vault_caveat VALUES ('x', 'y', repeat('0', 64))",
                "TRUNCATE ref.vault_fact",
                "UPDATE ref.vault_agent_manifest SET may_pull_from_agents = true",
                "INSERT INTO ref.vault_agent_exposure VALUES ('household_agent', 'va_rating', 'V2')"):
        refused(app_conn, errors.InsufficientPrivilege, sql)


def test_app_holds_no_delete_truncate_or_rewrite(app_conn, registry, new_tenant):
    tenant = new_tenant()
    store = VaultStore(app_conn)
    store.add(account_grant(registry, tenant))
    append(store, tenant)
    store.save(tenant, "us.fry-scholarship", "INTERESTED", registry.benefits["us.fry-scholarship"].content_hash)
    for sql in ("DELETE FROM public.vault_saved_benefit", "DELETE FROM public.vault_pull_grant",
                "DELETE FROM public.vault_pull_ledger", "TRUNCATE public.vault_pull_ledger",
                "TRUNCATE public.vault_saved_benefit", "TRUNCATE public.vault_pull_grant",
                "UPDATE public.vault_pull_ledger SET reason = 'ALLOWED'",
                "UPDATE public.vault_pull_grant SET fact_keys = ARRAY['age']",
                "UPDATE public.vault_pull_grant SET expires_at = expires_at + interval '1 day'",
                "UPDATE public.vault_saved_benefit SET benefit_id = 'us.death-gratuity'"):
        refused(app_conn, errors.InsufficientPrivilege, sql, tenant=tenant)


def test_tenants_see_and_change_only_their_own_rows(app_conn, registry, new_tenant):
    mine, theirs = new_tenant(), new_tenant()
    store = VaultStore(app_conn)
    grant = store.add(account_grant(registry, mine))
    append(store, mine)
    saved = store.save(mine, "us.fry-scholarship", "INTERESTED", registry.benefits["us.fry-scholarship"].content_hash)
    assert [g.grant_id for g in store.list(mine)] == [grant.grant_id]
    assert len(store.entries(mine)) == 1 and [s["saved_id"] for s in store.saved(mine)] == [saved["saved_id"]]
    assert store.list(theirs) == [] and store.entries(theirs) == [] and store.saved(theirs) == []
    assert store.for_source(theirs, "service_profile_agent", "benefit_matching") == []
    assert store.revoke(theirs, grant.grant_id, NOW + timedelta(minutes=1)) is None
    assert store.list(mine)[0].revoked_at is None
    assert store.discard(theirs, "saved_benefit", saved["saved_id"]) is False
    assert [s["saved_id"] for s in store.saved(mine)] == [saved["saved_id"]]
    # Rows written for another tenant fail the policy's WITH CHECK.
    refused(app_conn, errors.InsufficientPrivilege,
            "INSERT INTO public.vault_saved_benefit (tenant_id, benefit_id, status, content_hash_at_save)"
            " VALUES (%s, 'us.death-gratuity', 'INTERESTED', repeat('0', 64))", (mine,), tenant=theirs)
    refused(app_conn, errors.InsufficientPrivilege,
            "INSERT INTO public.vault_pull_ledger (tenant_id, seq, occurred_at, event, requester, source_agent,"
            " purpose, reason, prev_hash, row_hash) VALUES (%s, 0, now(), 'GRANT_CREATED', 'benefit_vault_agent',"
            " 'household_agent', 'benefit_matching', 'ALLOWED', repeat('0', 64), repeat('0', 64))", (mine,),
            tenant=theirs)
    refused(app_conn, errors.InsufficientPrivilege,
            "INSERT INTO public.vault_pull_grant (tenant_id, source_agent, fact_keys, purpose, mode, granted_at,"
            " expires_at) VALUES (%s, 'household_agent', ARRAY['age'], 'benefit_matching', 'B', now(),"
            " now() + interval '1 day')", (mine,), tenant=theirs)


def test_without_a_tenant_nothing_is_visible_or_writable(app_conn, registry, new_tenant):
    tenant = new_tenant()
    store = VaultStore(app_conn)
    store.add(account_grant(registry, tenant))
    append(store, tenant)
    with app_conn.transaction():
        app_conn.execute("SELECT set_config('vetbuddy.tenant_id', '', true)")
        for table in TENANT_TABLES:
            assert one(app_conn, f"SELECT count(*) FROM public.{table}") == (0,), table
    refused(app_conn, errors.InsufficientPrivilege,
            "INSERT INTO public.vault_saved_benefit (tenant_id, benefit_id, status, content_hash_at_save)"
            " VALUES (%s, 'us.death-gratuity', 'INTERESTED', repeat('0', 64))", (tenant,))
    refused(app_conn, errors.InsufficientPrivilege, "SELECT public.vb_vault_discard('saved_benefit', gen_random_uuid())")
    refused(app_conn, errors.InvalidParameterValue, "SELECT public.vb_vault_discard('ledger', gen_random_uuid())",
            tenant=tenant)


def test_store_refuses_guests_and_treats_malformed_ids_as_missing(app_conn, registry, new_tenant):
    store = VaultStore(app_conn)
    for call in (lambda: store.list("session-guest"), lambda: store.entries(""), lambda: store.saved(None)):
        with pytest.raises(StoreError):
            call()
    session_grant = new_grant(ManifestSet.from_registry(registry), registry.governance, tenant_ref="session-1",
                              source_agent="household_agent", fact_keys=["age"], purpose="benefit_matching",
                              mode="A", now=NOW)
    with pytest.raises(StoreError):
        store.add(session_grant)
    tenant = new_tenant()
    assert store.revoke(tenant, "not-a-uuid", NOW) is None
    assert store.revoke(tenant, str(uuid.uuid4()), NOW) is None
    assert store.discard(tenant, "saved_benefit", "x") is False
    with pytest.raises(StoreError):
        store.discard(tenant, "ledger", str(uuid.uuid4()))


# ── grants ────────────────────────────────────────────────────────────────

def test_grant_rules_hold_in_sql(app_conn, pg, registry, new_tenant):
    tenant = new_tenant()
    insert = ("INSERT INTO public.vault_pull_grant (tenant_id, source_agent, fact_keys, purpose, mode, granted_at,"
              " expires_at) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING grant_id, fact_keys")

    def row(source="service_profile_agent", keys=("service_status",), purpose="benefit_matching", mode="B", days=30):
        return (tenant, source, list(keys), purpose, mode, NOW, NOW + timedelta(days=days))

    for params in (row(keys=("va_rating",)),                                  # not exposed by this agent
                   row(source="household_agent", keys=("severe_disability",)),  # session-only, never exposed
                   row(source="benefit_vault_agent"),                         # the vault grants nothing to itself
                   row(source="nobody_agent"),                                # no manifest
                   row(days=91), row(days=0),                                 # 1 to 90 days
                   row(mode="A"),                                             # session grants stay in memory
                   row(purpose="marketing"),                                  # one purpose only
                   row(keys=())):                                             # at least one key
        refused(app_conn, errors.CheckViolation, insert, params, tenant=tenant)
    with app_conn.transaction():
        as_tenant(app_conn, tenant)
        _, keys = one(app_conn, insert, row(keys=("wartime_service", "component", "service_status", "component")))
    assert keys == ["component", "service_status", "wartime_service"]

    store = VaultStore(app_conn)
    made = store.add(account_grant(registry, tenant))
    other = store.add(account_grant(registry, tenant, source="household_agent", keys=("age",)))
    first = store.revoke(tenant, made.grant_id, NOW + timedelta(hours=1))
    second = store.revoke(tenant, made.grant_id, NOW + timedelta(hours=2))
    assert first.revoked_at == second.revoked_at == NOW + timedelta(hours=1)
    refused(app_conn, errors.CheckViolation, "UPDATE public.vault_pull_grant SET revoked_at = granted_at"
            " - interval '1 second' WHERE grant_id = %s", (other.grant_id,), tenant=tenant)
    with pg.connect() as owner:
        refused(owner, errors.CheckViolation, "UPDATE public.vault_pull_grant SET revoked_at = NULL"
                " WHERE grant_id = %s", (made.grant_id,))
        refused(owner, errors.CheckViolation, "UPDATE public.vault_pull_grant SET revoked_at = revoked_at"
                " + interval '1 hour' WHERE grant_id = %s", (made.grant_id,))
        refused(owner, errors.CheckViolation, "UPDATE public.vault_pull_grant SET fact_keys = ARRAY['age']"
                " WHERE grant_id = %s", (made.grant_id,))
        refused(owner, errors.CheckViolation, "UPDATE public.vault_pull_grant SET expires_at = expires_at"
                " + interval '1 day' WHERE grant_id = %s", (other.grant_id,))


# ── the ledger ────────────────────────────────────────────────────────────

def test_python_verifies_the_database_chain(app_conn, new_tenant):
    tenant = new_tenant()
    store = VaultStore(app_conn)
    for i in range(6):
        append(store, tenant, i, fact_keys=["service_status", "age", "component"][: i % 3 + 1])
    append(store, tenant, 10, event="PULL_DENIED", reason="NO_ACTIVE_GRANT", grant_id="", packet_id="",
           fact_keys=["va_rating"])
    append(store, tenant, 11, event="GRANT_REVOKED", source_agent="household_agent", fact_keys=["age"])
    entries = store.entries(tenant)
    assert [e.seq for e in entries] == list(range(1, 9))
    assert entries[0].prev_hash == "0" * 64
    assert all(b.prev_hash == a.row_hash for a, b in zip(entries, entries[1:]))
    assert entries[1].fact_keys == ("age", "service_status")
    assert verify_chain(entries) == (True, None) and store.verify(tenant) == (True, None)


def test_the_app_cannot_forge_sequence_or_hashes(app_conn, new_tenant):
    tenant = new_tenant()
    store = VaultStore(app_conn)
    append(store, tenant)
    with app_conn.transaction():
        as_tenant(app_conn, tenant)
        seq, prev_hash, row_hash, keys = one(
            app_conn,
            "INSERT INTO public.vault_pull_ledger (tenant_id, seq, occurred_at, event, requester, source_agent,"
            " purpose, fact_keys, reason, prev_hash, row_hash) VALUES (%s, 999, %s, 'GRANT_CREATED',"
            " 'benefit_vault_agent', 'household_agent', 'benefit_matching', ARRAY['relationship', 'age', 'age'],"
            " 'ALLOWED', repeat('a', 64), repeat('b', 64)) RETURNING seq, prev_hash, row_hash, fact_keys",
            (tenant, NOW))
    entries = store.entries(tenant)
    assert seq == 2 and prev_hash == entries[0].row_hash and row_hash not in ("a" * 64, "b" * 64)
    assert keys == ["age", "relationship"]
    assert verify_chain(entries) == (True, None)


def test_concurrent_appends_keep_one_chain(pg, new_tenant):
    tenant = new_tenant()

    def worker(n):
        with pg.connect(user="vb_app") as conn:
            store = VaultStore(conn)
            for i in range(15):
                append(store, tenant, n * 1000 + i)

    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in [pool.submit(worker, n) for n in range(4)]:
            future.result()
    with pg.connect(user="vb_app") as conn:
        entries = VaultStore(conn).entries(tenant)
    assert [e.seq for e in entries] == list(range(1, 61))
    assert verify_chain(entries) == (True, None)


def test_the_ledger_is_append_only_even_for_the_owner(pg, app_conn, new_tenant):
    tenant = new_tenant()
    store = VaultStore(app_conn)
    append(store, tenant)
    with pg.connect() as owner:
        refused(owner, errors.InsufficientPrivilege,
                "UPDATE public.vault_pull_ledger SET reason = reason WHERE tenant_id = %s", (tenant,))
        refused(owner, errors.InsufficientPrivilege, "DELETE FROM public.vault_pull_ledger WHERE tenant_id = %s",
                (tenant,))
        refused(owner, errors.InsufficientPrivilege, "TRUNCATE public.vault_pull_ledger")
        # Naming the tenant as the one being purged is not enough: only the purger role
        # (running vb_delete_account, migration 0013) may delete, not even the owner.
        with pytest.raises(errors.InsufficientPrivilege):
            with owner.transaction():
                owner.execute("SELECT set_config('vetbuddy.purge_tenant', %s, true)", (tenant,))
                owner.execute("DELETE FROM public.vault_pull_ledger WHERE tenant_id = %s", (tenant,))
    # The app role, with the setting and its own tenant context, has no DELETE grant at all.
    refused(app_conn, errors.InsufficientPrivilege, "DELETE FROM public.vault_pull_ledger", tenant=tenant)
    with pytest.raises(errors.InsufficientPrivilege):
        with app_conn.transaction():
            as_tenant(app_conn, tenant)
            app_conn.execute("SELECT set_config('vetbuddy.purge_tenant', %s, true)", (tenant,))
            app_conn.execute("DELETE FROM public.vault_pull_ledger")
    assert len(store.entries(tenant)) == 1 and store.verify(tenant) == (True, None)


def test_tampering_is_detected_but_a_dropped_tail_is_not(pg, app_conn, new_tenant):
    tenant = new_tenant()
    store = VaultStore(app_conn)
    for i in range(3):
        append(store, tenant, i)
    read = f"SELECT {VaultStore._LEDGER_COLS} FROM public.vault_pull_ledger WHERE tenant_id = %s ORDER BY seq"

    def chain(conn):
        return verify_chain([VaultStore._entry(r) for r in conn.execute(read, (tenant,)).fetchall()])

    with pg.connect() as owner:
        with owner.transaction():
            owner.execute("ALTER TABLE public.vault_pull_ledger DISABLE TRIGGER vault_pull_ledger_append_only")
            with owner.transaction():
                owner.execute("UPDATE public.vault_pull_ledger SET fact_keys = ARRAY['va_rating']"
                              " WHERE tenant_id = %s AND seq = 2", (tenant,))
                assert chain(owner) == (False, 2)
                raise pg_compat.Rollback()
            with owner.transaction():
                owner.execute("DELETE FROM public.vault_pull_ledger WHERE tenant_id = %s AND seq = 2", (tenant,))
                assert chain(owner) == (False, 3)
                raise pg_compat.Rollback()
            with owner.transaction():
                # Known gap (defect register): removing the newest entry leaves a valid, shorter chain.
                owner.execute("DELETE FROM public.vault_pull_ledger WHERE tenant_id = %s AND seq = 3", (tenant,))
                assert chain(owner) == (True, None)
                raise pg_compat.Rollback()
            raise pg_compat.Rollback()
    assert len(store.entries(tenant)) == 3 and store.verify(tenant) == (True, None)
    with pg.connect() as owner:
        assert one(owner, "SELECT tgenabled FROM pg_trigger WHERE tgname = 'vault_pull_ledger_append_only'") == ("O",)


# ── saved benefits and discard ────────────────────────────────────────────

def test_saved_benefits_and_discard(app_conn, pg, registry, new_tenant):
    mine, theirs = new_tenant(), new_tenant()
    store = VaultStore(app_conn)
    content = registry.benefits["us.death-gratuity"].content_hash
    first = store.save(mine, "us.death-gratuity", "INTERESTED", content)
    again = store.save(mine, "us.death-gratuity", "APPLIED_ON_MY_OWN", "0" * 64)
    assert again["saved_id"] == first["saved_id"] and again["status"] == "APPLIED_ON_MY_OWN"
    assert again["content_hash_at_save"] == content and again["saved_at"] == first["saved_at"]
    assert datetime.fromisoformat(again["updated_at"]) > datetime.fromisoformat(first["updated_at"])
    with pytest.raises(errors.ForeignKeyViolation):
        store.save(mine, "us.not-a-record", "INTERESTED", content)
    with pytest.raises(StoreError):
        store.save(mine, "us.death-gratuity", "DONE", content)
    refused(app_conn, errors.CheckViolation, "UPDATE public.vault_saved_benefit SET status = 'DONE'", tenant=mine)
    theirs_row = store.save(theirs, "us.death-gratuity", "INTERESTED", content)
    with pg.connect() as owner:
        refused(owner, errors.CheckViolation, "UPDATE public.vault_saved_benefit SET benefit_id = 'us.fry-scholarship'"
                " WHERE saved_id = %s", (theirs_row["saved_id"],))
        refused(owner, errors.CheckViolation, "UPDATE public.vault_saved_benefit SET content_hash_at_save ="
                " repeat('1', 64) WHERE saved_id = %s", (theirs_row["saved_id"],))
    assert store.discard(mine, "saved_benefit", theirs_row["saved_id"]) is False
    assert store.discard(mine, "saved_benefit", first["saved_id"]) is True
    assert store.saved(mine) == [] and [r["saved_id"] for r in store.saved(theirs)] == [theirs_row["saved_id"]]
    # A grant can be discarded only once it is revoked or expired, and only by its tenant.
    now = datetime.now(timezone.utc)
    live = store.add(account_grant(registry, mine, source="household_agent", keys=("age",), now=now))
    assert store.discard(mine, "grant", live.grant_id) is False
    store.revoke(mine, live.grant_id, now + timedelta(seconds=1))
    assert store.discard(theirs, "grant", live.grant_id) is False
    assert store.discard(mine, "grant", live.grant_id) is True and store.list(mine) == []
    lapsed = store.add(account_grant(registry, mine, source="household_agent", keys=("age",),
                                     now=now - timedelta(days=31)))
    assert store.discard(mine, "grant", lapsed.grant_id) is True


# ── the agent and the HTTP routes on the database store ──────────────────

def test_the_agent_runs_unchanged_on_the_database(app_conn, registry, new_tenant):
    tenant = new_tenant()
    store = VaultStore(app_conn)
    provider = Provider({"service_status": "retired", "component": "guard", "guard_state": "TX",
                         "discharge": "honorable"})
    agent = BenefitVaultAgent(registry, providers={"service_profile_agent": provider}, environment="development")
    session = Session(mode="B", tenant_ref=tenant, grants=store, ledger=store, saved=store)
    created = agent.create_grant({"source_agent": "service_profile_agent", "confirm": True,
                                  "fact_keys": ["service_status", "component", "guard_state", "discharge"]},
                                 session, NOW)
    env = agent.match({"facts": {"residence_state": "TX", "va_rating": 100}, "as_of": AS_OF}, session,
                      NOW + timedelta(minutes=1))
    assert {p["fact_key"] for p in env["subject"]["facts_pulled"]} == {"service_status", "component",
                                                                        "guard_state", "discharge"}
    homestead = next(i for i in env["items"] if i["benefit_id"] == "tx.100-disabled-veteran-homestead-exemption")
    assert homestead["outcome"] == "PRELIMINARY_MATCH"
    agent.revoke_grant(created["grant"]["grant_id"], session, NOW + timedelta(minutes=2))
    later = agent.match({"facts": {"residence_state": "TX"}, "as_of": AS_OF}, session, NOW + timedelta(minutes=3))
    assert later["subject"]["facts_pulled"] == [] and len(provider.calls) == 1
    agent.save_benefit({"benefit_id": homestead["benefit_id"], "confirm": True}, session)
    saved = agent.saved(session)["saved"]
    assert [(s["benefit_id"], s["changed_since_saved"], s["retired"]) for s in saved] == [
        (homestead["benefit_id"], False, False)]
    ledger = agent.ledger(session)
    assert ledger["chain_ok"] and [e["event"] for e in ledger["entries"]] == [
        "GRANT_CREATED", "PULL_ALLOWED", "GRANT_REVOKED"]
    with app_conn.transaction():
        as_tenant(app_conn, tenant)
        text = one(app_conn, "SELECT string_agg(t::text, ' ') FROM public.vault_pull_ledger t")[0]
    assert "retired" not in text and "honorable" not in text


def test_http_routes_on_the_database(app_conn, registry, new_tenant):
    tenant = new_tenant()
    agent = BenefitVaultAgent(registry, environment="development")
    app = Starlette(routes=routes(agent, resolver=lambda request: tenant,
                                  store_factory=lambda t: VaultStore(app_conn), clock=lambda: NOW))
    with TestClient(app) as client:
        made = client.post(f"{PREFIX}/grants", json={"source_agent": "household_agent", "fact_keys": ["age"],
                                                     "confirm": True})
        assert made.status_code == 200 and made.json()["grant"]["state"] == "ACTIVE"
        assert client.post(f"{PREFIX}/grants/not-a-uuid/revoke").status_code == 404
        assert client.post(f"{PREFIX}/grants/{uuid.uuid4()}/revoke").status_code == 404
        assert client.post(f"{PREFIX}/saved/not-a-uuid/discard", json={"confirm": True}).json() == {"removed": False}
        saved = client.post(f"{PREFIX}/saved", json={"benefit_id": "us.fry-scholarship", "confirm": True}).json()
        saved_id = saved["saved"]["saved_id"]
        assert client.post(f"{PREFIX}/saved/{saved_id}/discard", json={"confirm": True}).json() == {"removed": True}
        ledger = client.get(f"{PREFIX}/ledger").json()
        assert ledger["chain_ok"] and [e["event"] for e in ledger["entries"]] == ["GRANT_CREATED"]


# ── account deletion ──────────────────────────────────────────────────────

def test_purge_removes_every_vault_row_of_one_tenant(pg, app_conn, registry, new_tenant):
    """Slice 03's account deletion (vb_delete_account, migration 0013) reaches the vault tables."""
    leaving, staying = new_tenant(), new_tenant()
    with pg.connect() as owner:
        user = one(owner, "INSERT INTO public.app_user (tenant_id) VALUES (%s) RETURNING user_id", (leaving,))[0]
    store = VaultStore(app_conn)
    for tenant in (leaving, staying):
        made = store.add(account_grant(registry, tenant))
        store.revoke(tenant, made.grant_id, NOW + timedelta(minutes=1))
        store.add(account_grant(registry, tenant, source="household_agent", keys=("age",)))
        for i in range(3):
            append(store, tenant, i)
        store.save(tenant, "us.fry-scholarship", "INTERESTED", registry.benefits["us.fry-scholarship"].content_hash)
    with app_conn.transaction():          # the user's own request, as the app role
        as_tenant(app_conn, leaving)
        receipt = one(app_conn, "SELECT vb_delete_account(%s)", (user,))[0]
    with app_conn.transaction():
        status, counts = one(app_conn, "SELECT state, rows_purged FROM vb_deletion_status(%s)", (receipt,))
    assert status == "COMPLETE"
    assert counts == {"tenant": 1, "app_user": 1, "vault_pull_grant": 2, "vault_pull_ledger": 3,
                      "vault_saved_benefit": 1}
    with pg.connect() as owner:
        for table in ("tenant", "app_user") + TENANT_TABLES:
            assert one(owner, f"SELECT count(*) FROM public.{table} WHERE tenant_id = %s", (leaving,)) == (0,)
    with pytest.raises(errors.NoDataFound):   # a second request finds no account
        with app_conn.transaction():
            as_tenant(app_conn, leaving)
            app_conn.execute("SELECT vb_delete_account(%s)", (user,))
    assert len(store.list(staying)) == 2 and len(store.entries(staying)) == 3 and len(store.saved(staying)) == 1
    assert store.verify(staying) == (True, None)
