// The tables core-limbs builds at import time (`_HAND_FIST` by `_fist()`, `_HAND_OPEN` by `_square_wrist()`), against the numbers
// Python's import-time code computed (`core-limbs-expected.ts`, written by `harness/ts_port/gen_core_limbs.py --expected`), bit for bit.

import assert from "node:assert/strict";
import { test } from "node:test";
import { HAND_FIST, HAND_OPEN } from "../src/core-limbs-hands.ts";
import { COAT_CUTS, SLEEVE_CUTS, garmentCut } from "../src/core-limbs.ts";
import { HAND_FIST as EXPECTED_FIST, HAND_OPEN as EXPECTED_OPEN } from "./core-limbs-expected.ts";
import { encodeFloat } from "./fixtures.ts";

const bits = (v: unknown): unknown => (Array.isArray(v) ? v.map(bits) : typeof v === "number" ? encodeFloat(v) : v);

test("the fist, built at import time, is the one Python built", () => {
  assert.deepEqual(bits(HAND_FIST), bits(EXPECTED_FIST));
});

test("the open hand, built at import time, is the one Python built", () => {
  assert.deepEqual(bits(HAND_OPEN), bits(EXPECTED_OPEN));
});

test("the cut tables carry what Python's carry", () => {
  assert.deepEqual(Object.keys(COAT_CUTS), ["open_jacket", "lab_coat", "blazer"]);
  assert.deepEqual(Object.keys(SLEEVE_CUTS), ["wide"]);
  assert.equal(COAT_CUTS.lab_coat?.over_arms, false);
  assert.equal(COAT_CUTS.open_jacket?.bust_line_after, 2);
  assert.equal(garmentCut({ fills: [] }).line_weight, 0.7);
});
