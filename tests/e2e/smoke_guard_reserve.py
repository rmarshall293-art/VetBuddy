"""Browser smoke test for the Guard & Reserve center (ADR 0011).

Guest flow: open the center -> a Guard-only status on a Reserve component is
refused -> AGR Title 32 in Iowa with orders and days -> checks, records and
recovered AI leads show, labelled as not checked. Light 1280 px and dark 390 px,
no horizontal overflow, no page errors.

    BASE_URL=http://localhost:8000 SHOTS=/tmp/shots python3 tests/e2e/smoke_guard_reserve.py
"""
import os
import sys

from playwright.sync_api import expect, sync_playwright

BASE = os.environ.get("BASE_URL", "http://localhost:8000")
SHOTS = os.environ.get("SHOTS", "/tmp/vb-shots")
os.makedirs(SHOTS, exist_ok=True)


def main() -> int:
    errors = []
    with sync_playwright() as p:
        exe = "/opt/pw-browsers/chromium" if os.path.exists("/opt/pw-browsers/chromium") else None
        b = p.chromium.launch(executable_path=exe)
        for scheme, width in (("light", 1280), ("dark", 390)):
            page = b.new_page(viewport={"width": width, "height": 900}, color_scheme=scheme)
            page.on("response", lambda r: r.url.startswith(BASE) and (r.status == 404 or r.status >= 500)
                    and errors.append(f"{r.status} {r.url}"))
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(BASE + "/#/")
            page.get_by_role("link", name="Guard & Reserve").first.click()
            expect(page.get_by_role("heading", name="Guard & Reserve", exact=True)).to_be_visible()

            # A National Guard status on a Reserve component is refused, with the reason.
            page.select_option("#gr-c", "usar")
            page.select_option("#gr-s", "agr32")
            page.get_by_role("button", name="Show my Guard & Reserve view").click()
            expect(page.get_by_text("Check your answers")).to_be_visible()

            page.select_option("#gr-c", "arng")
            page.select_option("#gr-gs", "IA")
            page.select_option("#gr-rs", "MO")
            page.fill("#gr-d", "120")
            page.locator("input[name=order_authorities][value=a11]").check()
            page.get_by_role("button", name="Show my Guard & Reserve view").click()
            expect(page.get_by_role("heading", name="How VetBuddy read your answers")).to_be_visible()
            expect(page.get_by_role("heading", name="Guard & Reserve checks")).to_be_visible()
            expect(page.get_by_role("heading", name="Research leads to check")).to_be_visible()
            expect(page.get_by_text("AI research lead · not checked").first).to_be_visible()
            expect(page.get_by_role("heading", name="Iowa")).to_be_visible()
            expect(page.get_by_role("heading", name="AGR retirement after 20 years of active federal service")).to_be_visible()
            # Missouri's flagged cell is withheld, not shown.
            expect(page.get_by_text("Wording held back by VetBuddy's safety check").first).to_be_visible()
            overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")
            if overflow:
                errors.append(f"horizontal overflow at {width}px")
            page.screenshot(path=f"{SHOTS}/gr-{scheme}.png", full_page=False)
            page.close()
        b.close()
    if errors:
        print("FAIL", *errors, sep="\n  ")
        return 1
    print("guard & reserve smoke: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
