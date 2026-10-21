// Guest mode (Privacy Mode A) in a real browser: after the page loads, using
// every tool sends nothing over the network and leaves nothing in storage.
// Runs against `vite preview` of a guest-only build (no VITE_API_URL).
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { chromium } from "playwright";

const PORT = 4179;
const BASE = `http://127.0.0.1:${PORT}`;
let server, browser;

async function waitFor(url, ms = 15000) {
  const end = Date.now() + ms;
  while (Date.now() < end) {
    try { if ((await fetch(url)).ok) return; } catch { /* not up yet */ }
    await new Promise(r => setTimeout(r, 200));
  }
  throw new Error("preview server did not start");
}

before(async () => {
  server = spawn("npx", ["vite", "preview", "--port", String(PORT), "--strictPort", "--host", "127.0.0.1"], { stdio: "ignore" });
  await waitFor(BASE);
  browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
});

after(async () => { await browser?.close(); server?.kill(); });

test("guest tools send nothing and store nothing", async () => {
  const page = await browser.newPage();
  const requests = [];
  // Third-party font requests are blocked here (no outbound network in CI); they carry no answers either way.
  await page.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());
  page.on("request", r => requests.push(r.url()));
  await page.goto(BASE + "/#home");
  await page.waitForSelector("text=What matters now");
  const afterLoad = requests.length;

  await page.click("text=Mission brief >> nth=0");
  await page.click("text=Fill in an example");
  await page.click("text=Show my brief");
  await page.waitForSelector("text=Your first five actions");
  assert.ok(await page.isVisible("text=12 to 6 months before separation"));
  await page.locator("input.tick").first().check();

  await page.goto(BASE + "/#rating");
  await page.click("text=Example: 60, 40, 20");
  assert.equal((await page.textContent(".result-num")).trim(), "80%");
  await page.click("text=Example: 50 + both knees 30, 20");
  assert.equal((await page.textContent(".result-num")).trim(), "70%");  // 30+20 -> 44, +4.4 -> 48; 50 & 48 -> 74 -> 70
  assert.ok(await page.isVisible("text=gives 48"));

  await page.goto(BASE + "/#finder");
  await page.selectOption("#fj", "AL");
  assert.ok(await page.isVisible("text=Verification required"));

  // Claims guide and "How it's built" render from data/reference, not hand-copied text.
  await page.goto(BASE + "/#claims");
  assert.ok(await page.isVisible("text=After an Intent to File"));
  assert.ok(await page.isVisible("text=38 CFR 3.155"));
  assert.ok((await page.locator("table.lane .chip").count()) >= 3, "timeline windows must carry their unverified status");
  assert.equal(await page.locator("table.lane >> text=Only with your approval").count(), 1);
  await page.goto(BASE + "/#trust");
  assert.ok(await page.isVisible("text=Four non-negotiables"));
  assert.equal(await page.locator("table.lane tbody tr").count(), 22);

  await page.click("#help-btn");
  assert.ok(await page.isVisible("#help >> text=Veterans Crisis Line"));
  assert.ok(await page.isVisible("#help >> text=838255"));
  assert.equal(await page.locator("#crisis li").count(), 6);

  const later = requests.slice(afterLoad).filter(u => !u.startsWith(BASE + "/#"));
  assert.deepEqual(later, [], "guest actions made network requests");
  const storage = await page.evaluate(async () => ({
    local: localStorage.length, session: sessionStorage.length, cookie: document.cookie,
    idb: (await indexedDB.databases()).length,
  }));
  assert.deepEqual(storage, { local: 0, session: 0, cookie: "", idb: 0 });
  assert.equal(await page.locator("nav.tabs >> text=Saved plan").count(), 0, "guest build must not show the saved-plan tab");
});
