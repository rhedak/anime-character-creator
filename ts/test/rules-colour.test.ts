// Rules of the colour kernel: tests/test_colorutil.py and the three colour tests of tests/test_soft_locks.py.
// `colorutil.shade()` and the soft finish's tone helpers (litTone, softShadowTone, highlightRise) are exercised on their
// own, outside the default hue range, rather than only through full renders.

import assert from "node:assert/strict";
import { test } from "node:test";
import { highlightRise, hexToRgb01, litTone, rgb01ToHex, shade, softShadowTone } from "../src/colorutil.ts";
import { SOFT_LOCK_HIGH_RISE } from "../src/hair.ts";
import { PRESETS } from "../src/presets.ts";
import { PRESET_NAMES, approx, assertApprox, hsvOf } from "./rules-util.ts";

test("test_hex_rgb01_round_trip", () => {
  for (const hex of ["#000000", "#ffffff", "#e8b84b", "#4a9c6d", "#123456"]) {
    assert.equal(rgb01ToHex(hexToRgb01(hex)), hex);
  }
  // Beyond the five colours of the Python test: every level of every channel survives the trip, so a rounding that is
  // off by one at some level (a floor where a round belongs) cannot hide behind five lucky colours.
  const two = (n: number): string => n.toString(16).padStart(2, "0");
  for (let n = 0; n < 256; n++) {
    const hex = `#${two(n)}${two(255 - n)}${two((n * 7) % 256)}`;
    assert.equal(rgb01ToHex(hexToRgb01(hex)), hex);
  }
});

test("test_shade_darkens_by_default", () => {
  const base = "#e8b84b";
  const shaded = shade(base);
  const vBase = hsvOf(base)[2];
  const vShaded = hsvOf(shaded)[2];
  assert.ok(vShaded < vBase, `${vShaded} is not below ${vBase}`);
});

test("test_shade_black_stays_black", () => {
  // v=0 has nothing for a value multiply to darken further.
  assert.equal(shade("#000000"), "#000000");
});

test("test_shade_white_saturation_boost_clamps_at_one", () => {
  // White has s=0, so the saturation boost multiply is a no-op regardless of factor; this only proves the clamp
  // does not error or overshoot.
  assert.equal(shade("#ffffff", 1.0, 100.0), "#ffffff");
});

test("test_shade_saturation_boost_clamps_on_saturated_color", () => {
  // A fully saturated colour already sits at s=1.0; an aggressive boost must clamp rather than push the HSV to RGB
  // conversion out of [0, 1].
  const result = shade("#ff0000", 1.0, 5.0);
  const s = hsvOf(result)[1];
  assert.ok(approx(s, 1.0), `saturation ${s}`);
});

for (const hex of ["#ff0000", "#00ff00", "#0000ff", "#7f00ff", "#ffbf00"]) {
  test(`test_shade_value_factor_scales_value_directly[${hex}]`, () => {
    const vBase = hsvOf(hex)[2];
    const shaded = shade(hex, 0.5, 1.0);
    const vShaded = hsvOf(shaded)[2];
    assertApprox(vShaded, vBase * 0.5, 1 / 255, hex);
  });
}

for (const name of PRESET_NAMES) {
  test(`test_the_tones_keep_the_hair_saturation[${name}]`, () => {
    const hair = PRESETS[name]!.hair_color;
    const [, s0, v0] = hsvOf(hair);
    const high = litTone(hair, highlightRise(hair) * SOFT_LOCK_HIGH_RISE);
    const [, s1, v1] = hsvOf(high);
    assert.ok(v1 >= v0, `${name}: the lit tone ${v1} is darker than the hair ${v0}`);
    if (v0 < 0.7) assert.ok(s1 >= 0.93 * s0, `${name}: the lit tone lost saturation (${s1} against ${s0})`);
    const shadow = softShadowTone(hair);
    const [, s2, v2] = hsvOf(shadow);
    assert.ok(v2 < v0 && s2 >= 0.9 * s0, `${name}: the shadow tone is not darker (${v2} against ${v0}) or lost saturation (${s2} against ${s0})`);
  });
}

test("test_a_yellow_green_colour_is_not_nudged_toward_green", () => {
  const h0 = hsvOf("#fff700")[0];
  const h1 = hsvOf(litTone("#fff700", 0.0))[0];
  assertApprox(h1, h0, 0.002);
});

test("test_a_higher_strength_moves_every_tone_further_from_the_hair_colour", () => {
  const value = (c: string): number => hsvOf(c)[2];
  for (const hair of ["#e8b84b", "#e56a9c", "#b5602b", "#a9763f", "#6b1f2a"]) {
    const shadows = [0.0, 0.5, 1.0].map((g) => value(softShadowTone(hair, g)));
    assertApprox(value(hair), shadows[0] as number, 0.01, hair);
    assert.ok((shadows[0] as number) > (shadows[1] as number) && (shadows[1] as number) > (shadows[2] as number), `${hair}: shadows ${shadows}`);
    const lits = [0.0, 0.5, 1.0].map((g) => value(litTone(hair, highlightRise(hair) * g)));
    assert.ok((lits[0] as number) < (lits[1] as number) && (lits[1] as number) < (lits[2] as number), `${hair}: lits ${lits}`);
  }
});
