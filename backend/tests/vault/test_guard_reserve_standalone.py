"""The Guard & Reserve standalone page (dist/vetbuddy-guard-reserve.html): synthetic
profiles only, the agent's own results, current with the repository, and a page
that stores and sends nothing."""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAGE = ROOT / "dist" / "vetbuddy-guard-reserve.html"
PERSONAS = ROOT / "data" / "synthetic" / "guard_reserve_personas.json"


def test_page_is_current():
    r = subprocess.run([sys.executable, str(ROOT / "scripts/build_guard_reserve_html.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_profiles_are_synthetic_and_hold_no_personal_data():
    data = json.loads(PERSONAS.read_text())
    assert data["notice"].startswith("SYNTHETIC.")
    allowed_facts = {"guard_state", "residence_state"}
    for p in data["personas"]:
        assert re.fullmatch(r"SYN-GR-\d{2}", p["id"])
        assert set(p["request"]) <= {"guard_reserve", "facts"}
        assert set(p["request"].get("facts", {})) <= allowed_facts
        text = json.dumps(p)
        assert not re.search(r"@|\d{3}[-.\s]\d{2}[-.\s]\d{4}|\d{3}[-.\s]\d{3}[-.\s]\d{4}", text)


def test_page_stores_and_sends_nothing():
    html = PAGE.read_text()
    script = html[html.index("<script>"):]
    for needle in ("fetch(", "XMLHttpRequest", "localStorage", "sessionStorage", "navigator.sendBeacon", "WebSocket", "<form"):
        assert needle not in script, needle
    assert "src=\"http" not in html and "<link" not in html     # no outside code or styles


def test_page_shows_the_agents_results_not_its_own():
    html = PAGE.read_text()
    blob = html[html.index("const GR = ") + len("const GR = "):html.index(";\nconst DATA_SHA256")]
    data = json.loads(blob.replace("<\\/", "</"))
    for p in data["personas"]:
        for env in ("production", "development"):
            run = p["env"][env]
            assert re.fullmatch(r"[0-9a-f]{64}", run["hashes"]["inputs"]) and re.fullmatch(r"[0-9a-f]{64}", run["hashes"]["output"])
        # production never shows an unverified record as a match
        prod = [i for i in p["env"]["production"]["items"] if i[1] == "PRELIMINARY_MATCH"]
        verified = {r[0] for r in data["records"] if r[data["cols"].index("record_status")] == "VERIFIED"}
        assert {i[0] for i in prod} <= verified
    assert "988" in json.dumps(data["crisis"])
