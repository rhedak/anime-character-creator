// Rules of the finish switch: tests/test_soft_finish.py (the portable ones) and
// tests/test_consumers_stay_flat.py::test_nothing_that_is_drawn_by_default_is_soft. "flat" is the house style and the
// default, "soft" is an opt-in that adds gradients and tinted lines and moves no shape.

import assert from "node:assert/strict";
import { test } from "node:test";
import { ADULT_BODY_TYPES } from "../src/body-adult.ts";
import { characterParams, replace } from "../src/model.ts";
import type { CharacterParams } from "../src/params.ts";
import { NEUTRAL_BASES, PRESETS } from "../src/presets.ts";
import { renderCharacter } from "../src/render.ts";
import { PRESET_NAMES, assertRaises, soft } from "./rules-util.ts";
import { fromstring } from "./svg-scan.ts";

test("test_nothing_that_is_drawn_by_default_is_soft", () => {
  assert.equal(characterParams().finish, "flat");
  assert.ok(Object.values(PRESETS).every((p) => p.finish === "flat"));
  assert.ok(Object.values(NEUTRAL_BASES).every((p) => p.finish === "flat"));
  assert.ok(Object.keys(PRESETS).length >= 20 && Object.keys(NEUTRAL_BASES).length === 2, "the registries are not empty");
});

test("test_flat_has_none_of_what_soft_adds", () => {
  const flat = renderCharacter(PRESETS.satoko);
  for (const marker of ["linearGradient", "radialGradient", "feGaussianBlur", "iris-grad", "blush-grad", "soft-face-clip"]) {
    assert.ok(!flat.includes(marker), `the flat drawing contains ${marker}`);
  }
  // The control: the soft drawing of the same character does carry the gradient markers.
  assert.ok(soft("satoko").includes("linearGradient"));
});

test("test_an_unknown_finish_is_refused", () => {
  assertRaises(() => renderCharacter(replace(characterParams(), { finish: "glossy" as never })), "ValueError", "finish must be one of");
  // The message names the finishes and quotes the offending value as Python's repr does.
  assertRaises(() => renderCharacter(replace(characterParams(), { finish: "glossy" as never })), "ValueError", "flat, soft, not 'glossy'");
});

for (const name of PRESET_NAMES) {
  test(`test_every_preset_draws_soft_as_well_formed_svg_without_blur[${name}]`, () => {
    const svg = soft(name);
    fromstring(svg);
    // cairosvg writes the PNGs and has no gaussian blur: the finish is gradients only.
    assert.ok(!svg.includes("feGaussianBlur"));
    // The adult woman's parts draw the one finish: the soft finish's gradients are the chibi head's and hair's, and she has her own head, hair and body.
    if (!Object.hasOwn(ADULT_BODY_TYPES, (PRESETS[name] as CharacterParams).body)) assert.ok(svg.includes("linearGradient") && svg.includes("radialGradient"));
  });
}
