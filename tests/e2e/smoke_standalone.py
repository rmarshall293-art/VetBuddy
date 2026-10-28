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
