"""Discovery: the gap planner and the source watcher."""
from __future__ import annotations

from datetime import date

import pytest

from app.domains.vault.discovery.planner import DiscoveryPlanner
from app.domains.vault.discovery.watcher import SourceWatcher
from app.domains.vault.governance.egress import EgressGuard


@pytest.fixture(scope="module")
def egress(registry):
    return EgressGuard.from_registry(registry)


def test_gaps_put_missing_sources_first(registry, egress):
    planner = DiscoveryPlanner(registry, egress)
    gaps = planner.gaps()
    assert gaps[0] == ("NO_SOURCE", "AS", None)
    assert ("TAIL_UNREAD", "NM", None) in gaps
    assert all(reason in ("NO_SOURCE", "TAIL_UNREAD", "CATEGORY_GAP") for reason, _, _ in gaps)


def test_plan_uses_only_fixed_vocabulary(registry, egress):
    planner = DiscoveryPlanner(registry, egress)
    tasks = planner.plan(limit=1000)
    assert tasks and not planner.executable
    ids = [t.task_id for t in tasks]
    assert len(ids) == len(set(ids))
    for task in tasks:
        assert not any(ch.isdigit() for ch in task.query)
        assert task.query.endswith(("for veterans", "for National Guard members"))
    assert planner.plan(reasons=["TAIL_UNREAD"])[0].jurisdiction == "NM"
    with pytest.raises(ValueError):
        planner.plan(limit=0)


def test_watcher_reports_due_sources(registry, egress):
    watcher = SourceWatcher(registry, egress)
    assert watcher.due(date(2026, 10, 28)) == []
    due = watcher.due(date(2027, 6, 1))
    assert len(due) == len(registry.sources) and all(d["age_days"] > 180 for d in due)


def test_watcher_without_a_fetcher_is_blocked(registry, egress):
    findings = SourceWatcher(registry, egress).check()
    assert {f.status for f in findings} == {"BLOCKED"}


def test_watcher_detects_changes(registry, egress):
    source_id = next(s for s, src in registry.sources.items() if src["url"] and "Texas" in src["url"])
    pages = {"text": "Texas Military and Veterans Benefits  page one"}
    watcher = SourceWatcher(registry, egress, fetch=lambda url: pages["text"])
    first = watcher.check([source_id])[0]
    assert first.status == "NEW_BASELINE" and first.affected_benefit_ids == ()
    pages["text"] = "texas military and veterans benefits page one"
    assert watcher.check([source_id])[0].status == "UNCHANGED"     # whitespace and case are normalized
    pages["text"] = "Texas Military and Veterans Benefits page two"
    changed = watcher.check([source_id])[0]
    assert changed.status == "CHANGED" and changed.affected_benefit_ids
    assert all(registry.benefits[b].source_id == source_id for b in changed.affected_benefit_ids)


def test_watcher_failures_are_findings(registry, egress):
    source_id = next(s for s, src in registry.sources.items() if src["url"])

    def boom(url):
        raise TimeoutError("slow")

    finding = SourceWatcher(registry, egress, fetch=boom).check([source_id])[0]
    assert finding.status == "UNREACHABLE" and finding.note == "TimeoutError"
    seen = next(s for s, src in registry.sources.items() if src["url"] is None)
    assert SourceWatcher(registry, egress, fetch=boom).check([seen])[0].status == "BLOCKED"
