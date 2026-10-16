// The garments domain: the registry the assembly calls, and the shapes of the traced tables the generator wrote.

import assert from "node:assert/strict";
import { test } from "node:test";
import { BELT_CUTS, COAT_BUTTONS, COLLAR_CUTS, HIP_POCKET_CUT, RIBBON_CUT } from "../src/garments.ts";
import { PARTS } from "../src/parts-garments.ts";

test("the garments registry holds every part the assembly calls, by Python name", () => {
  const names = [
    "_tunic", "_robe_front", "_placket", "_chest_pockets", "_strap", "_apron", "_coat", "_pouches", "_crystal_harness",
    "_traced_coat_and_belt", "_belt", "_collar", "_shoulder_bars", "_ribbon",
  ];
  for (const n of names) assert.equal(typeof PARTS[n], "function", n);
  assert.equal(Object.keys(PARTS).length, names.length);
});

test("the traced tables have the cuts Python names", () => {
  assert.deepEqual(Object.keys(COLLAR_CUTS), ["pointed", "shirt"]);
  assert.equal(COLLAR_CUTS["pointed"]?.fills.length, 3);
  assert.deepEqual(Object.keys(BELT_CUTS), ["buckled"]);
  assert.equal(BELT_CUTS["buckled"]?.strap.fills.length, 2);
  assert.equal(RIBBON_CUT.ref_body, "tall_slender");
  assert.ok(RIBBON_CUT.holes.length > 0);
  assert.equal(HIP_POCKET_CUT.fills.length, 2);
  assert.equal(COAT_BUTTONS.length, 3);
});
