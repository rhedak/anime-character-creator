// The props domain: what the stage and call oracles do not pin down by themselves.

import assert from "node:assert/strict";
import { test } from "node:test";
import { PARTS } from "../src/parts-props.ts";
import { katanaStretchFactor, katanaStretched, mirroredY } from "../src/props.ts";
import type { Chain } from "../src/tables.ts";

test("the props domain registers its five roots and hat_underside", () => {
  assert.deepEqual(Object.keys(PARTS).sort(), ["_familiar", "_hat", "_hat_underside", "_headscarf", "_katana", "_staff"]);
});

test("a sword of the traced length is not stretched, and the stretch leaves the hilt alone", () => {
  assert.equal(katanaStretchFactor(1.0), 1.0);
  const grow = katanaStretched(1.5);
  assert.deepEqual(grow([-0.5, 0.2]), [-0.5, 0.2]);
  assert.ok((grow([2.4, 0.0])[0] as number) > 2.4);
});

test("mirroredY flips a chain about its own middle: twice is the identity up to rounding, and x never moves", () => {
  const chain: Chain = [[0, 0], [[[1, 2], [2, 1]], [[3, 5], [4, 0]]]];
  const once = mirroredY(chain);
  const twice = mirroredY(once);
  assert.deepEqual(once[0], [0, 2 * (8 / 5) - 0]);
  assert.deepEqual(twice[1].map(([c, e]) => [c[0], e[0]]), chain[1].map(([c, e]) => [c[0], e[0]]));
  for (const [i, [c, e]] of twice[1].entries()) {
    assert.ok(Math.abs((c[1] as number) - (chain[1][i]![0][1] as number)) < 1e-12);
    assert.ok(Math.abs((e[1] as number) - (chain[1][i]![1][1] as number)) < 1e-12);
  }
});
