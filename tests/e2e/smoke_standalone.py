"""Browser test for dist/vetbuddy.html (Launch-0 style guest app) and the
generated integrated record dist/vetbuddy-record.html.

Gates from the governance record: entering facts sends zero network requests;
crisis resources render with no network call; no browser storage is used.
    SHOTS=/tmp/shots python3 tests/e2e/smoke_standalone.py
"""
import os
import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
URL = (ROOT / "dist/vetbuddy.html").as_uri()
SHOTS = os.environ.get("SHOTS", "/tmp/vb-shots")
os.makedirs(SHOTS, exist_ok=True)
FONT_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com")


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
            page.on("console", lambda m: m.type == "error" and not any(h in m.text for h in ("net::", "Failed to load")) and errors.append(m.text))
            page.goto(URL)
            expect(page.get_by_role("heading", name="What matters now")).to_be_visible()
            page.screenshot(path=f"{SHOTS}/sa-home-{scheme}.png", full_page=True)

            page.get_by_role("link", name="Mission brief").first.click()
            page.get_by_role("button", name="Show my brief").click()
            expect(page.get_by_text("Almost there.")).to_be_visible()
            page.get_by_role("button", name="Fill in an example").click()
            page.get_by_role("button", name="Show my brief").click()
            expect(page.get_by_text("Guest · not saved")).to_be_visible()
            expect(page.get_by_text("Alabama: not yet verified")).to_be_visible()
            page.locator("input.tick").first.click()
            expect(page.locator(".dim[data-s=in_progress]").first).to_be_visible()
            page.screenshot(path=f"{SHOTS}/sa-brief-{scheme}.png", full_page=True)

            page.get_by_role("button", name="Clear session").click()            # v6 §2
            expect(page.get_by_text("Session cleared")).to_be_visible()
            page.get_by_role("link", name="Mission brief").first.click()
            expect(page.get_by_role("button", name="Show my brief")).to_be_visible()  # brief is gone

            page.get_by_role("link", name="Rating calculator").click()
            expect(page.locator(".result-num")).to_have_text("90%")          # 70 + 50 -> 85 -> 90
            page.get_by_role("button", name="Example: 60, 40, 20").click()
            expect(page.locator(".result-num")).to_have_text("80%")
            page.get_by_role("button", name="Example: 50 + both knees 30, 20").click()   # 38 CFR 4.26
            expect(page.locator(".result-num")).to_have_text("70%")          # 30+20 -> 44, +4.4 -> 48; 50 & 48 -> 74
            expect(page.get_by_text("gives 48")).to_be_visible()
            page.screenshot(path=f"{SHOTS}/sa-rating-{scheme}.png", full_page=True)

            page.get_by_role("link", name="Claims guide").click()
            expect(page.get_by_text("Preparing decision letter")).to_be_visible()
            expect(page.get_by_text("38 CFR 3.400(b)(2)")).to_be_visible()          # window from the corpus
            expect(page.get_by_role("link", name="Find an accredited representative on VA.gov")).to_have_attribute(
                "href", "https://www.va.gov/get-help-from-accredited-representative/find-rep/")
            page.screenshot(path=f"{SHOTS}/sa-claims-{scheme}.png", full_page=True)

            page.get_by_role("link", name="Benefits finder").click()
            page.select_option("#fj", "PR")
            expect(page.get_by_role("heading", name="Puerto Rico", exact=True)).to_be_visible()
            expect(page.get_by_text("Verification required")).to_be_visible()
            # Benefit Vault catalog, generated from the registry: records to read, never matches
            page.select_option("#fj", "AL")
            page.fill("#fq", "hunting")
            first = page.locator("#vault-results .vault-item").first
            expect(first).to_be_visible()
            expect(first.get_by_text("Not yet reviewed")).to_be_visible()
            expect(first.get_by_role("link", name="Official page")).to_have_attribute("href", __import__("re").compile(r"^https://"))
            page.select_option("#fj", "AS")                                       # no source: said plainly
            expect(page.get_by_text("No official source for this jurisdiction has been found yet")).to_be_visible()
            page.screenshot(path=f"{SHOTS}/sa-finder-{scheme}.png", full_page=False)

            page.get_by_role("link", name="How it's built").click()
            expect(page.get_by_text("The 22 agent rules, and what exists today")).to_be_visible()
            expect(page.get_by_text("No guarantees", exact=True)).to_be_visible()
            expect(page.get_by_text("independent information and organization platform")).to_be_visible()
            page.screenshot(path=f"{SHOTS}/sa-trust-{scheme}.png", full_page=True)

            # Money plan: every tab computes, refusals show, estimates never become income
            page.get_by_role("link", name="Money plan").click()
            expect(page.get_by_role("heading", name="Money plan")).to_be_visible()
            page.get_by_role("button", name="E-5 leaving an overseas post").click()
            page.get_by_role("button", name="Work it out").click()
            expect(page.get_by_role("heading", name="What the next months look like")).to_be_visible()
            expect(page.locator(".mlchart svg polyline")).to_have_count(3)
            if not page.locator("table.steps tbody tr").filter(has_text="Downside").filter(has_text="after separation").count():
                errors.append("E-5 example: the downside case should show savings running out after separation")
            page.screenshot(path=f"{SHOTS}/sa-money-{scheme}.png", full_page=True)
            if page.evaluate("document.documentElement.scrollWidth > window.innerWidth"):
                errors.append(f"money plan: horizontal overflow at {width}px")
            page.get_by_role("button", name="VA estimate").click()
            page.get_by_role("button", name="Work it out").click()
            expect(page.get_by_text("$666.47")).to_be_visible()                       # 30%, spouse and 1 child: VA.gov table, 2025-12-01
            page.get_by_label("Combined VA rating").select_option("100")
            page.get_by_label("Children under 18").fill("2")
            page.get_by_role("button", name="Work it out").click()
            expect(page.get_by_text("$4,428.10")).to_be_visible()
            expect(page.get_by_text("Illustration, not an award")).to_be_visible()
            page.get_by_role("button", name="Retirement", exact=True).click()
            page.get_by_label("Kind of retirement").select_option("chapter61")
            page.get_by_label("Average of your highest 36 months of base pay ($/month)").fill("4,200")
            page.get_by_label("Years of service (regular and Chapter 61)").fill("15")
            page.get_by_label("DoD disability percentage (Chapter 61; not your VA rating)").fill("50")
            page.get_by_role("button", name="Work it out").click()
            expect(page.get_by_text("$2,100.00")).to_be_visible()
            expect(page.get_by_text("never simply added to VA pay", exact=False)).to_be_visible()
            page.get_by_role("button", name="Loan payment").click()
            page.get_by_label("Amount borrowed ($)").fill("300,000")
            page.get_by_label("Interest rate (APR %)").fill("6.5")
            page.get_by_label("Years", exact=True).fill("30")
            page.get_by_role("button", name="Work it out").click()
            expect(page.get_by_text("$1,896.20")).to_be_visible()
            page.get_by_label("Amount borrowed ($)").fill("-5")
            page.get_by_role("button", name="Work it out").click()
            expect(page.get_by_role("alert")).to_contain_text("enter dollars")
            page.get_by_role("button", name="Savings & debt").click()
            page.get_by_label("Essential spending per month ($)").fill("4,200")
            page.get_by_role("button", name="Work it out").first.click()
            expect(page.get_by_text("Savings not entered, so the gap isn't shown.", exact=False)).to_be_visible()

            page.get_by_role("button", name="Help me now").click()
            expect(page.get_by_text("988 · Press 1")).to_be_visible()
            page.screenshot(path=f"{SHOTS}/sa-help-{scheme}.png")
            page.keyboard.press("Escape")

            stray = [u for u in requests if not u.startswith("file://") and not any(h in u for h in FONT_HOSTS)]
            if stray:
                errors.append(f"network requests besides fonts: {stray}")
            storage = page.evaluate("[localStorage.length, sessionStorage.length, document.cookie]")
            if storage != [0, 0, ""]:
                errors.append(f"browser storage used: {storage}")
            if page.evaluate("document.documentElement.scrollWidth > window.innerWidth"):
                errors.append(f"horizontal overflow at {width}px")
            ctx.close()

        # the integrated record renders, fills every slot, and fits a phone
        for scheme, width in (("light", 1280), ("dark", 390)):
            pg = b.new_page(viewport={"width": width, "height": 900}, color_scheme=scheme)
            pg.on("pageerror", lambda e: errors.append(f"record pageerror: {e}"))
            pg.goto((ROOT / "dist/vetbuddy-record.html").as_uri())
            expect(pg.get_by_role("heading", name="VetBuddy Integrated Record")).to_be_visible()
            expect(pg.get_by_text("Agent rules R1–R22")).to_be_visible()
            if pg.evaluate("document.documentElement.scrollWidth > window.innerWidth"):
                errors.append(f"record horizontal overflow at {width}px")
            pg.screenshot(path=f"{SHOTS}/record-{scheme}.png", full_page=False)
            pg.close()
        b.close()
    if errors:
        print("ERRORS:", *errors, sep="\n  ")
        return 1
    print("standalone smoke OK; screenshots in", SHOTS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
