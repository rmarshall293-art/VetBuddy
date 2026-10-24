// Browser kernel vs Python kernel on the golden fixtures that
// scripts/build_web.py writes from the Python implementation. Any drift in
// stages, task choice, ordering, wording, hashing or rating math fails here.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { KDATA, combineRatings, route, validate } from "../src/kernel.js";

const fx = JSON.parse(readFileSync(new URL("./fixtures/parity.json", import.meta.url)));
const known = new Set(KDATA.JURISDICTIONS.map(j => j.code));

test("fixture set is non-trivial", () => {
  assert.ok(fx.router.length >= 25);
  assert.equal(new Set(fx.router.map(c => c.expected.stage)).size, Object.keys(KDATA.STAGE_LABELS).length);
});

for (const [i, c] of fx.router.entries()) {
  test(`router case ${i}: ${c.input.persona}/${c.input.component} -> ${c.expected.stage}`, async () => {
    validate(c.input, known);
    assert.deepEqual(await route(c.input, fx.today), c.expected);
  });
}

for (const c of fx.ratings) {
  test(`ratings ${c.input.join("+")} -> ${c.expected.combined_rating}`, () => {
    assert.deepEqual(combineRatings(c.input), c.expected);
  });
}

for (const c of fx.bilateral) {
  test(`bilateral ${c.bilateral.join("+")} with ${c.ratings.join("+") || "none"} -> ${c.expected.combined_rating}`, () => {
    assert.deepEqual(combineRatings(c.ratings, c.bilateral), c.expected);
  });
}

test("rating input errors match Python's refusals", () => {
  assert.throws(() => combineRatings([50], [30]), RangeError);
  for (const bad of [[], [15], [110], [-10], [true], ["50"], [50.5]]) assert.throws(() => combineRatings(bad), RangeError);
});
