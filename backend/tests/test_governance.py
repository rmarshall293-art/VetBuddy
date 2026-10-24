"""ClaimsBoundaryGuard over every user-facing string, plus generated-file sync.

The guard must (a) catch each blocked example in governance §7 and (b) pass
all copy VetBuddy actually ships: task library, notices, required language,
API messages and the web app's strings.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

from app.governance import language
from app.governance.language import check_text
from app.kernel import vocab

ROOT = Path(__file__).resolve().parents[2]

BLOCKED = [
    ("guarantee", "You will get this benefit."), ("guarantee", "You qualify for the GI Bill."),
    ("guarantee", "This is guaranteed."), ("guarantee", "We guarantee approval."), ("guarantee", "You're owed back pay."),
    ("rating", "You should be rated at 70%."), ("rating", "This is worth 50%."), ("rating", "Likely 70% for this."),
    ("diagnosis", "You have PTSD."), ("diagnosis", "That sounds like sleep apnea."),
    ("representation", "We'll file for you."), ("representation", "I am your claim agent."),
    ("representation", "We represent you before VA."),
    ("claim_coaching", "Tell the examiner it hurts daily."), ("claim_coaching", "Describe it as constant."),
    ("claim_coaching", "Don’t mention the good days."),
    ("fees", "Pay a $300 fee to file."),
]


@pytest.mark.parametrize("category,text", BLOCKED)
def test_guard_catches_governance_examples(category, text):
    assert category in {v.category for v in check_text(text)}


@pytest.mark.parametrize("text", [
    "You may be eligible to explore this program.", "That's worth asking your rep about.",
    "VA's rating criteria for this are in 38 CFR 4.x.", "Talk to your health care provider about these symptoms.",
    "An accredited representative can file for you.", "Bring your questions to your accredited representative.",
])
def test_guard_allows_governance_alternatives(text):
    assert check_text(text) == []


def _shipped_strings() -> list[tuple[str, str]]:
    out = [(f"template {k}.{f}", v[f]) for k, v in vocab.TEMPLATES.items() for f in ("title", "why") ]
    out += [(f"notice {k}", v) for k, v in vocab.NOTICE_TEXT.items()]
    out += [(f"stage {k}", v) for k, v in vocab.STAGE_LABELS.items()]
    out += [("unverified", vocab.UNVERIFIED_DISCLAIMER)]
    out += [(f"language.{n}", getattr(language, n)) for n in
            ("AI_DISCLOSURE", "STANDARD_DISCLAIMER", "VSO_REFERRAL", "CFR_REFERENCE_LABEL", "RESUME_LABEL")]
    for py in (ROOT / "backend" / "app").rglob("*.py"):
        if py.name == "language.py":
            continue
        out += [(str(py.relative_to(ROOT)), s) for s in re.findall(r'"([^"\n]{12,})"', py.read_text())]
    for js in (ROOT / "frontend" / "src").glob("*.js"):
        text = js.read_text()
        out += [(str(js.relative_to(ROOT)), s) for s in re.findall(r'"([^"\n]{12,})"|`([^`]{12,})`', text) for s in s if s]
    out += [("frontend/index.html", (ROOT / "frontend" / "index.html").read_text())]
    return out


def test_all_shipped_copy_passes_the_guard():
    bad = [(where, v.category, v.excerpt) for where, s in _shipped_strings() for v in check_text(s)]
    assert bad == []


def test_required_blocks_are_present():
    assert "accredited" in language.VSO_REFERRAL and "free" in language.VSO_REFERRAL
    assert "VA alone decides" in language.STANDARD_DISCLAIMER
    src = (ROOT / "frontend" / "src" / "main.js").read_text()
    data = (ROOT / "frontend" / "src" / "kernel_data.js").read_text()
    assert "KDATA.LANGUAGE.vso_search_url" in src and "va.gov/get-help-from-accredited-representative/find-rep" in data


def test_generated_browser_files_are_in_sync():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_web.py"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
