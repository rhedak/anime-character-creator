// Rules for the adult woman's builds (body-adult-build.ts, docs/risa-polish-plan.md stage 2). TypeScript only, with no Python oracle: the tests pin that a build reaches nothing it should not
// (the traced body, every other body type, the recorded skeletons), that the warp is a warp (neutral at factor 1, never folding the outline), and what Risa's build does.

import assert from "node:assert/strict";
import { test } from "node:test";
import { ADULT_BUILDS, type AdultBuild, spacedDepths, warpDepth, warpHalf } from "../src/body-adult-build.ts";
import { BLAZER_BUTTON_DEPTHS } from "../src/body-adult-blazer-data.ts";
import { place } from "../src/body-adult-parts.ts";
import { skeletonFor } from "../src/body.ts";
import { characterParams, replace } from "../src/model.ts";
import { PyError } from "../src/pynum.ts";
import { FRANZI, PRESETS, RISA } from "../src/presets.ts";
import { renderCharacter } from "../src/render.ts";

const NEUTRAL: AdultBuild = { shorten: 0, shorten_from: 0.95, shorten_to: 1.26, arm_shorten: 0, body: [[0, 1]], leg_gap: [[0, 1]], arm_in: [[0, 0]], arm_out: [[0, 0]] };
const GRID_D = Array.from({ length: 49 }, (_, i) => 0.1 * i); // 0 to 4.8 H, past the feet
const GRID_V = Array.from({ length: 121 }, (_, i) => 0.01 * i); // 0 to 1.2 H, past the hands

test("without a build the skeleton has no adult_build key, so it is the object the recorded calls hold; every other body ignores the field", () => {
  for (const [name, p] of Object.entries(PRESETS)) {
    if (p.body_build === null) assert.ok(!("adult_build" in skeletonFor(p)), name);
  }
  const chibi = characterParams({ body: "tall_chibi_long_torso" });
  const slenderChibi = replace(chibi, { body_build: "slender" });
  assert.ok(!("adult_build" in skeletonFor(slenderChibi)));
  assert.equal(renderCharacter(slenderChibi, null, null, false), renderCharacter(chibi, null, null, false));
});

test("an unknown build is a KeyError on the adult body, as an unknown body type is", () => {
  assert.throws(() => skeletonFor(replace(FRANZI, { body_build: "no_such_build" })), (e: unknown) => e instanceof PyError && e.pyType === "KeyError");
});

test("a neutral build (no shortening, every factor 1) moves no knot", () => {
  for (const d of GRID_D) {
    assert.ok(Math.abs(warpDepth(NEUTRAL, d) - d) < 1e-12);
    for (const v of GRID_V) {
      assert.ok(Math.abs(warpHalf(NEUTRAL, d, v) - v) < 1e-12, `${d} ${v}`);
      assert.ok(Math.abs(warpHalf(NEUTRAL, d, -v) + v) < 1e-12, `mirrored ${d} ${v}`);
      assert.ok(Math.abs(warpDepth(NEUTRAL, d, v) - d) < 1e-12);
    }
  }
});

test("every build keeps the outline from folding: at each depth a larger half-width stays larger, and a lower depth stays lower", () => {
  for (const [name, b] of Object.entries(ADULT_BUILDS)) {
    for (const d of GRID_D) {
      let prev = -Infinity;
      for (const v of GRID_V) {
        const w = warpHalf(b, d, v);
        assert.ok(w > prev, `${name}: at ${d} H the half-width ${v} folds back`);
        prev = w;
      }
    }
    for (const v of [0, 0.3, 0.6, 1.0]) {
      let prev = -Infinity;
      for (const d of GRID_D) {
        const y = warpDepth(b, d, v);
        assert.ok(y > prev, `${name}: at half-width ${v} the depth ${d} folds back`);
        prev = y;
      }
    }
  }
});

test("Risa is on the slender build: a shorter torso, narrower thighs, the hands raised less than the hips, and the traced knees and feet", () => {
  assert.equal(RISA.body_build, "slender");
  const traced = place(skeletonFor(replace(RISA, { body_build: null })));
  const slender = place(skeletonFor(RISA));
  // the hips come up by the torso's shortening, the hand by the arm's, which is less
  const hipUp = traced.y(2.0) - slender.y(2.0);
  const handUp = traced.y(2.3, 1.0) - slender.y(2.3, 1.0);
  assert.ok(hipUp > 0 && handUp > 0 && handUp < hipUp, `${hipUp} ${handUp}`);
  // a thigh is narrower (its outer edge in, about its inner edge), the ankle is the traced one
  assert.ok(slender.w(2.7, 0.537) < traced.w(2.7, 0.537) - 2);
  assert.ok(Math.abs(slender.w(4.2, 0.367) - traced.w(4.2, 0.367)) < 1e-9);
});

test("a row of buttons keeps its spacing under a build: the warped gaps in the traced proportions, and nothing moved without a build", () => {
  assert.equal(spacedDepths(undefined, BLAZER_BUTTON_DEPTHS), BLAZER_BUTTON_DEPTHS);
  const b = ADULT_BUILDS["slender"] as AdultBuild;
  const ws = spacedDepths(b, BLAZER_BUTTON_DEPTHS).map((d) => warpDepth(b, d));
  const ds = BLAZER_BUTTON_DEPTHS;
  const k = ((ws[2] as number) - (ws[0] as number)) / ((ds[2] as number) - (ds[0] as number));
  assert.ok(Math.abs((ws[1] as number) - (ws[0] as number) - k * ((ds[1] as number) - (ds[0] as number))) < 1e-9);
  // the warp alone would bunch them: the top gap well under the lower one, against the traced near-equal gaps
  const raw = ds.map((d) => warpDepth(b, d));
  assert.ok((raw[1] as number) - (raw[0] as number) < 0.8 * ((raw[2] as number) - (raw[1] as number)));
});
