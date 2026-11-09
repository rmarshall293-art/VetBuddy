"""Browser test for dist/vetbuddy-demo.html (the guest app plus four sample people).

Checks the demo stays honest: today's view never shows a benefit as a match
(nothing is reviewed yet), the preview is labelled as such, account actions are
simulated in memory, and like the guest app it makes no network request
besides fonts and uses no browser storage.
    SHOTS=/tmp/shots python3 tests/e2e/smoke_demo.py
"""
import os
import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
URL = (ROOT / "dist/vetbuddy-demo.html").as_uri()
SHOTS = os.environ.get("SHOTS", "/tmp/vb-shots")
os.makedirs(SHOTS, exist_ok=True)
FONT_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com")
MATCH = "Fits the rules as written (preliminary)"


def main() -> int:
    errors = []
    with sync_playwright() as p:
        exe = "/opt/pw-browsers/chromium"
        b = p.chromium.launch(executable_path=exe if os.path.exists(exe) else None)
        for scheme, width in (("light", 1280), ("dark", 390)):
            ctx = b.new_context(viewport={"width": width, "height": 900}, color_scheme=scheme)
            page = ctx.new_page()
            requests = []
            page.on("request", lambda r: requests.append(r.url))
            page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
            page.goto(URL)
            expect(page.get_by_role("heading", name="VetBuddy, shown through four sample people")).to_be_visible()
            expect(page.get_by_text("four invented people")).to_be_visible()
            page.screenshot(path=f"{SHOTS}/demo-people-{scheme}.png", full_page=True)

            page.get_by_role("button", name="See VetBuddy as Marcus").click()
            expect(page.get_by_role("heading", name="Mission brief")).to_be_visible()
            expect(page.get_by_text("Sample person · not saved")).to_be_visible()
            expect(page.get_by_text("Viewing as Marcus (sample person)")).to_be_visible()
            page.screenshot(path=f"{SHOTS}/demo-brief-{scheme}.png", full_page=False)

            page.get_by_role("link", name="Their benefits").click()
            expect(page.get_by_role("heading", name="Benefits for Marcus")).to_be_visible()
            expect(page.get_by_text("May apply: not yet reviewed").first).to_be_visible()
            if page.get_by_text(MATCH).count():
                errors.append("today's view shows a preliminary match although nothing is reviewed")
            page.screenshot(path=f"{SHOTS}/demo-benefits-{scheme}.png", full_page=False)
            page.get_by_role("button", name="Preview: once records are reviewed").click()
            expect(page.get_by_text("Preview only.")).to_be_visible()
            expect(page.get_by_text(MATCH).first).to_be_visible()
            page.get_by_role("button", name="As it works today").click()
            page.get_by_role("button", name="Save to list").first.click()
            expect(page.get_by_text("Manage it under Account.")).to_be_visible()

            page.get_by_role("link", name="Their career").click()
            expect(page.get_by_role("heading", name="Career for Marcus")).to_be_visible()
            expect(page.locator("table.matrix tbody tr").first).to_be_visible()
            if page.locator("table.matrix tbody tr").count() != 4:
                errors.append(f"expected 4 requirement rows for Marcus, found {page.locator('table.matrix tbody tr').count()}")
            # the ATS resume proposes one invented figure; the gate must hold it, visibly, with its reason
            expect(page.get_by_text("1 proposed line was held.")).to_be_visible()
            expect(page.locator(".cdoc .held").first).to_contain_text("Uses a number no verified record contains.")
            if page.get_by_text("do not currently meet").count():
                errors.append("Marcus's letter discloses a gap no record documents")
            for word in ("guarantee", "PTSD", "disability rating"):
                if page.locator(".cdoc").filter(has_text=word).count():
                    errors.append(f"career documents contain {word!r}")
            page.screenshot(path=f"{SHOTS}/demo-career-{scheme}.png", full_page=True)
            page.get_by_role("button", name="Federal (USAJOBS)").click()
            expect(page.get_by_text("Every proposed line passed.")).to_be_visible()

            page.get_by_role("link", name="Account").click()
            expect(page.get_by_role("heading", name="Marcus's account")).to_be_visible()
            if page.locator("ul.saved li").count() != 2:
                errors.append(f"expected 2 saved benefits, found {page.locator('ul.saved li').count()}")
            page.get_by_role("button", name="Show my data").click()
            expect(page.locator("pre.export")).to_contain_text("vault_saved_benefit")
            page.get_by_label("Store my mission data so I can come back to it").uncheck()
            expect(page.get_by_text("Consent withdrawn")).to_be_visible()
            page.get_by_role("button", name="Delete my account and data").click()
            expect(page.get_by_text("Type DELETE MY ACCOUNT exactly")).to_be_visible()
            page.fill("#confirm", "DELETE MY ACCOUNT")
            page.get_by_role("button", name="Delete my account and data").click()
            expect(page.get_by_role("heading", name="Account deleted")).to_be_visible()
            page.screenshot(path=f"{SHOTS}/demo-deleted-{scheme}.png", full_page=False)

            # the guest tools still work in the demo
            page.get_by_role("link", name="Benefits finder").click()
            page.select_option("#fj", "AL")
            expect(page.locator("#vault-results .vault-item").first).to_be_visible()

            stray = [u for u in requests if not u.startswith("file://") and not any(h in u for h in FONT_HOSTS)]
            if stray:
                errors.append(f"network requests besides fonts: {stray}")
            if page.evaluate("[localStorage.length, sessionStorage.length, document.cookie]") != [0, 0, ""]:
                errors.append("browser storage used")
            for view in ("people", "benefits", "career", "account"):
                page.evaluate(f"location.hash = '{view}'")
                if page.evaluate("document.documentElement.scrollWidth > window.innerWidth"):
                    errors.append(f"horizontal overflow on {view} at {width}px")
            ctx.close()
        b.close()
    if errors:
        print("ERRORS:", *errors, sep="\n  ")
        return 1
    print("demo smoke OK; screenshots in", SHOTS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
