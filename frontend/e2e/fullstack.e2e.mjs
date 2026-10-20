// Full stack in a real browser: UI -> API -> PostgreSQL (Privacy Mode B).
// Needs a running API with a migrated database and AUTH_MODE=dev whose
// CORS_ORIGINS includes the preview origin below. Set VB_E2E_API_URL to it;
// without it this test is skipped (CI always sets it).
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { spawn, spawnSync } from "node:child_process";
import { chromium } from "playwright";

const API = process.env.VB_E2E_API_URL;
const PORT = 4180;
const BASE = `http://127.0.0.1:${PORT}`;
let server, browser;

async function waitFor(url, ms = 15000) {
  const end = Date.now() + ms;
  while (Date.now() < end) {
    try { if ((await fetch(url)).ok) return; } catch { /* not up yet */ }
    await new Promise(r => setTimeout(r, 200));
  }
  throw new Error(`${url} did not come up`);
}

before(async () => {
  if (!API) return;
  const b = spawnSync("npx", ["vite", "build", "--outDir", "dist-e2e"], { env: { ...process.env, VITE_API_URL: API }, stdio: "inherit" });
  assert.equal(b.status, 0, "build with VITE_API_URL failed");
  server = spawn("npx", ["vite", "preview", "--outDir", "dist-e2e", "--port", String(PORT), "--strictPort", "--host", "127.0.0.1"], { stdio: "ignore" });
  await waitFor(BASE);
  await waitFor(API + "/api/v1/health/live");
  browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
});

after(async () => { await browser?.close(); server?.kill(); });

test("sign in, consent, save brief, check off a task, withdraw and delete", { skip: !API && "VB_E2E_API_URL not set" }, async () => {
  const page = await browser.newPage();
  await page.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());
  const apiCalls = [];
  page.on("request", r => { if (r.url().startsWith(API)) apiCalls.push(`${r.method()} ${new URL(r.url()).pathname}`); });

  await page.goto(BASE + "/#brief");
  await page.click("text=Fill in an example");
  await page.click("text=Show my brief");
  await page.waitForSelector("text=Your first five actions");
  assert.equal(apiCalls.length, 0, "building a brief must not call the API");

  await page.click("text=Save this plan to my account");
  await page.fill("#subj", "synthetic-e2e-" + Date.now());
  await page.click("text=Sign in (development)");
  await page.waitForSelector("text=Your consent comes first");
  assert.ok((await page.textContent(".strip")).includes("Signed in (development)"));

  await page.click("text=I agree: save my plans privately");
  await page.click("text=Save my current mission brief");
  await page.waitForSelector("h2:has-text('12 to 6 months before separation')");
  assert.equal(await page.locator(".plist li").count(), 1);

  const firstTick = page.locator(".card ol.actions input.tick").first();
  await firstTick.check();
  await page.waitForSelector(".card ol.actions li.done");
  await page.reload();  // memory-only token: a reload signs you out
  await page.goto(BASE + "/#plan");
  await page.waitForSelector("text=Development sign-in (mock)");

  const storage = await page.evaluate(() => [localStorage.length, sessionStorage.length, document.cookie]);
  assert.deepEqual(storage, [0, 0, ""]);
  assert.ok(apiCalls.includes("POST /api/v1/missions") && apiCalls.some(c => c.startsWith("PATCH /api/v1/tasks/")));
});

test("withdraw and delete clears saved plans", { skip: !API && "VB_E2E_API_URL not set" }, async () => {
  const page = await browser.newPage();
  await page.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());
  await page.goto(BASE + "/#brief");
  await page.click("text=Fill in an example");
  await page.click("text=Show my brief");
  await page.click("text=Save this plan to my account");
  await page.fill("#subj", "synthetic-e2e-del-" + Date.now());
  await page.click("text=Sign in (development)");
  await page.click("text=I agree: save my plans privately");
  await page.click("text=Save my current mission brief");
  await page.waitForSelector(".plist li");
  await page.click("text=Withdraw and delete my plans");
  await page.waitForSelector("text=Your consent comes first");
  await page.click("text=I agree: save my plans privately");
  await page.waitForSelector("text=No saved plans yet.");
});
