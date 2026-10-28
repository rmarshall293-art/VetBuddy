"""Browser smoke test (Playwright, Chromium). Drives the real UI against a
running server: guest brief -> sign up -> save plan -> tick a task ->
withdraw consent -> locked -> restore. Saves screenshots to $SHOTS.

    BASE_URL=http://localhost:8000 SHOTS=/tmp/shots python3 tests/e2e/smoke_ui.py
"""
import os
import sys

from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get("BASE_URL", "http://localhost:8000")
SHOTS = os.environ.get("SHOTS", "/tmp/vb-shots")
os.makedirs(SHOTS, exist_ok=True)


def fill_form(page, save: bool):
    page.get_by_label("National Guard or Reserve").check(force=True)
    page.select_option("#branch", "Army")
    page.select_option("#component", "national_guard")
    page.select_option("#legal_authority", "unknown")
    page.fill("#separation_date", "2027-06-30")
    page.select_option("#current_jurisdiction", "AL")
    page.select_option("#destination_jurisdiction", "TX")
    for g in ("School or training", "Job or career", "Benefits"):
        page.get_by_label(g, exact=True).check(force=True)
    if save:
        page.locator("input[name=consent]").check()


def main() -> int:
    errors = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium" if os.path.exists("/opt/pw-browsers/chromium") else None)
        for scheme, width in (("light", 1280), ("dark", 390)):
            page = b.new_page(viewport={"width": width, "height": 900}, color_scheme=scheme)
            # Real failures only: JS exceptions, and same-origin responses that are
            # 404 or 5xx. (403 CONSENT_REQUIRED is an expected state in this flow;
            # third-party fonts may be blocked in sandboxed CI.)
            page.on("response", lambda r: r.url.startswith(BASE) and (r.status == 404 or r.status >= 500)
                    and errors.append(f"{r.status} {r.url}"))
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(BASE + "/#/")
            expect(page.get_by_role("heading", name="What matters now")).to_be_visible()
            page.screenshot(path=f"{SHOTS}/01-start-{scheme}.png", full_page=True)

            # guest
            page.get_by_role("link", name="Start as a guest").click()
            page.get_by_role("button", name="Show my brief").click()
            expect(page.get_by_text("Almost there.")).to_be_visible()      # validation path
            fill_form(page, save=False)
            page.get_by_role("button", name="Show my brief").click()
            expect(page.get_by_role("heading", name="Mission brief")).to_be_visible()
            expect(page.get_by_text("Guest · not saved")).to_be_visible()
            page.screenshot(path=f"{SHOTS}/02-guest-brief-{scheme}.png", full_page=True)

            # save
            page.get_by_role("button", name="Create a private profile").click()
            expect(page.get_by_role("heading", name="Build your private plan")).to_be_visible()
            fill_form(page, save=True)
            page.get_by_role("button", name="Build and save my brief").click()
            expect(page.get_by_text("Saved · private to you")).to_be_visible()
            if "null" in page.inner_text("main").split():
                errors.append("stray 'null' rendered on saved brief")
            first = page.locator("input.tick").first
            first.check()
            expect(page.get_by_text("Marked done.")).to_be_visible()
            page.screenshot(path=f"{SHOTS}/03-saved-brief-{scheme}.png", full_page=True)

            page.get_by_role("link", name="All tasks").click()
            expect(page.get_by_role("heading", name="All tasks")).to_be_visible()
            page.screenshot(path=f"{SHOTS}/04-tasks-{scheme}.png", full_page=True)

            # help
            page.get_by_role("button", name="Help me now").click()
            expect(page.get_by_text("Call 988, then Press 1")).to_be_visible()
            page.screenshot(path=f"{SHOTS}/05-help-{scheme}.png")
            page.get_by_role("button", name="Close").click()

            # consent withdraw -> locked -> restore
            page.get_by_role("link", name="Privacy").click()
            page.get_by_role("button", name="Withdraw consent").click()
            expect(page.get_by_text("withdrawn", exact=False).first).to_be_visible()
            page.get_by_role("link", name="Mission brief").click()
            expect(page.get_by_role("heading", name="Consent needed")).to_be_visible()
            page.screenshot(path=f"{SHOTS}/06-consent-gate-{scheme}.png")
            page.get_by_role("button", name="Give consent again").click()
            expect(page.get_by_role("heading", name="Mission brief")).to_be_visible()

            # Benefit Vault (server): search, compare, save with explicit confirmation
            page.locator("#nav").get_by_role("link", name="Benefits").click()
            expect(page.get_by_role("heading", name="Benefits", exact=True)).to_be_visible()
            expect(page.get_by_text("independent information and organization platform").first).to_be_visible()
            page.fill("#vq", "hunting")
            page.select_option("#vj", "AL")
            page.get_by_role("button", name="Search").click()
            item = page.locator(".vault-item").first
            expect(item).to_be_visible()
            expect(item.get_by_role("link", name="Official page")).to_be_visible()
            item.get_by_role("button", name="Save to my list").click()
            page.get_by_role("button", name="Confirm save").click()
            expect(page.get_by_text("Saved to your list.")).to_be_visible()
            page.select_option("#vm-residence_state", "TX")
            page.select_option("#vm-service_status", "separated")
            page.select_option("#vm-va_rating", "100")                   # V2 question: account only
            page.get_by_role("button", name="Compare").click()
            expect(page.get_by_text("Compared against").first).to_be_visible()
            expect(page.get_by_text("not yet checked by a reviewer").first).to_be_visible()
            page.screenshot(path=f"{SHOTS}/06b-benefits-{scheme}.png", full_page=False)

            # export, then delete the account (v6 §3)
            page.get_by_role("link", name="Privacy").click()
            with page.expect_download() as dl:
                page.get_by_role("button", name="Download my data").click()
            if dl.value.suggested_filename != "vetbuddy-export.json":
                errors.append("export download has the wrong name")
            page.get_by_role("link", name="Delete account").click()
            expect(page.get_by_role("heading", name="Delete account")).to_be_visible()
            page.screenshot(path=f"{SHOTS}/07-delete-{scheme}.png", full_page=True)
            page.get_by_role("button", name="Delete my account and data").click()
            expect(page.get_by_text("Type DELETE MY ACCOUNT exactly")).to_be_visible()
            page.fill("#confirm", "DELETE MY ACCOUNT")
            page.get_by_role("button", name="Delete my account and data").click()
            expect(page.get_by_role("heading", name="Account deleted")).to_be_visible()
            page.screenshot(path=f"{SHOTS}/08-deleted-{scheme}.png", full_page=True)
            expect(page.locator("#nav").get_by_role("link", name="Start")).to_be_visible()   # signed-out nav
            # guests get the finder too, with basic questions only and nothing stored
            page.locator("#nav").get_by_role("link", name="Benefits").click()
            expect(page.get_by_text("As a guest you're asked only basic questions")).to_be_visible()
            if page.locator("#vm-va_rating").count():
                errors.append("guest finder offers an account-only (V2) question")

            overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
            if overflow:
                errors.append(f"horizontal overflow at width {width}")
            page.close()
        b.close()
    if errors:
        print("UI ERRORS:", *errors, sep="\n  ")
        return 1
    print("UI smoke OK; screenshots in", SHOTS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
