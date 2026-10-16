// The parts-face branches the corpus never reaches, against Python's answers (`harness/ts_port/gen_face_expected.py`):
// `_eye_lash` with no `reach`, `_jaw_track` when no degree reaches `y0`, `_ear_place`, `_mouth_depth_share`, `_blush`, and a
// whole parts on looks the corpus does not name (a negative beard, an extreme gaze, a closed eye with a scar).

import assert from "node:assert/strict";
import { test } from "node:test";
import { skeletonFor } from "../src/body.ts";
import { blush, earPlace, ears, eyeLash, face, head, mouthDepthShare } from "../src/face.ts";
import { beard, glasses, jawTrack } from "../src/face-wear.ts";
import { characterParams, faceStyle } from "../src/model.ts";
import { plainParams } from "../src/plain.ts";
import type { FaceStyle } from "../src/params.ts";
import { FACE_EXPECTED as X } from "./face-expected.ts";
import { sameBits } from "./fixtures.ts";

// Within `ulps` of the last place: the skull's points come from the engine's `sin` and `cos`, which can be an ulp off the C
// library's (the maths-library policy of docs/ts-port-plan.md, section 4).
const near = (a: number, b: number, ulps: number): boolean => {
  if (sameBits(a, b)) return true;
  const dv = new DataView(new ArrayBuffer(16));
  dv.setFloat64(0, a);
  dv.setFloat64(8, b);
  return Math.abs(Number(dv.getBigInt64(0) - dv.getBigInt64(8))) <= ulps && a * b >= 0;
};

const bitsEqual = (got: unknown, want: unknown, what: string, ulps = 0): void => {
  if (typeof want === "number") {
    assert.ok(typeof got === "number" && near(got, want, ulps), `${what}: ${String(got)} against ${want}`);
  } else if (Array.isArray(want)) {
    assert.ok(Array.isArray(got) && got.length === want.length, `${what}: length`);
    want.forEach((w, i) => bitsEqual((got as unknown[])[i], w, `${what}[${i}]`, ulps));
  } else {
    assert.equal(got, want, what);
  }
};

test("_eye_lash, with and without a reach", () => {
  for (const c of X.lash) {
    bitsEqual(eyeLash(c.er, faceStyle(c.face as Partial<FaceStyle>), c.edge_w, c.reach), c.out, `lash ${JSON.stringify(c.face)} reach ${c.reach}`);
  }
});

test("_jaw_track, including the default of 90 degrees", () => {
  for (const c of X.jaw) bitsEqual(jawTrack(c.y0, c.build, c.drop, c.inset), c.out, `jaw ${c.y0} ${c.build}`, 4);
});

test("_ear_place", () => {
  for (const c of X.place) bitsEqual(earPlace(c.build)([c.pt[0], c.pt[1]]), c.out, `place ${c.build} ${c.pt}`, 4);
});

test("_mouth_depth_share", () => {
  for (const c of X.depth) bitsEqual(mouthDepthShare(c.x), c.out, `depth ${c.x}`);
});

test("_blush over light and dark skin", () => {
  for (const c of X.blush) bitsEqual(blush(c.skin), c.out, `blush ${c.skin}`);
});

test("whole parts on looks the corpus does not name", () => {
  const parts = { head, face, beard, glasses, ears };
  for (const c of X.wholes) {
    const p = plainParams(characterParams({ ...(c.params as object), face: faceStyle(c.face as Partial<FaceStyle>) }));
    const sk = skeletonFor(p);
    for (const [name, fn] of Object.entries(parts)) {
      assert.equal(fn(sk, p), (c.out as Record<string, string>)[name], `${name} of ${JSON.stringify(c.params)} ${JSON.stringify(c.face)}`);
    }
  }
});
