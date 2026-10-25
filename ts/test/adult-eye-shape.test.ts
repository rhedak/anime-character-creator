// A cut's own traced eye (`AdultEyeShape`, body-adult-eyes.ts `tracedEye`, docs/risa-polish-plan.md stage 7): Risa's cut draws hers, Franzi's keeps her measured eye; the iris has three
// tones in the flat finish; the highlights keep the image's orientation (the light from the same side on both eyes); and her shut eye is her own line in her lid's colour.

import assert from "node:assert/strict";
import { test } from "node:test";
import { adultCutOf } from "../src/body-adult-cuts.ts";
import { OUTLINE } from "../src/character.ts";
import { replace } from "../src/model.ts";
import { FRANZI, RISA } from "../src/presets.ts";
import { renderCharacter } from "../src/render.ts";

const draw = (p: typeof RISA): string => renderCharacter(p, null, null, false);
const eyeOf = (svg: string, id: string): string => {
  const i = svg.indexOf(`<clipPath id="${id}">`);
  const j = svg.indexOf(`<clipPath id="${id === "adult-eye-l" ? "adult-eye-r" : "zzz"}">`, i + 1);
  return svg.slice(i, j < 0 ? i + 20000 : j);
};

test("Risa's cut draws its traced eye, Franzi's her measured one", () => {
  assert.notEqual(adultCutOf(RISA).eyeShape, null);
  assert.equal(adultCutOf(FRANZI).eyeShape, null);
  assert.ok(draw(RISA).includes('<clipPath id="adult-eye-l-iris">'));
  assert.ok(!draw(FRANZI).includes('<clipPath id="adult-eye-l-iris">'));
});

test("the flat traced iris lays three tones: its middle band, the dark top band and the light crescent", () => {
  const eye = eyeOf(draw(RISA), "adult-eye-l");
  const fills = new Set([...eye.matchAll(/<(?:ellipse|path) [^>]*fill="(#[0-9a-f]{6})"/g)].map((m) => m[1]));
  // the white, the middle band, the top band, the crescent, the pupil, the highlight, the lid (and the lower line and crease, drawn as fills)
  assert.ok(fills.size >= 7, [...fills].join(" "));
});

test("the highlights keep the image's orientation: on both eyes they lie to the viewer's left of the iris's centre", () => {
  const svg = draw(RISA);
  for (const id of ["adult-eye-l", "adult-eye-r"]) {
    const eye = eyeOf(svg, id);
    const iris = eye.match(/<clipPath id="[^"]+-iris"><ellipse cx="([0-9.]+)"/);
    const hl = [...eye.matchAll(/<ellipse cx="([0-9.]+)" cy="[0-9.]+" rx="[0-9.]+" ry="[0-9.]+" fill="#ffffff"/g)];
    assert.ok(iris !== null && hl.length > 0, id);
    for (const m of hl) assert.ok(Number(m[1]) < Number(iris![1]), `${id}: highlight at ${m[1]}, iris at ${iris![1]}`);
  }
});

test("her shut eye is her own line in her lid's colour, not Franzi's black one", () => {
  const shut = draw(replace(RISA, { face: { ...RISA.face, eyes_closed: true } }));
  const lid = adultCutOf(RISA).eye.lidColor as string;
  assert.ok(shut.includes(`fill="${lid}"`));
  const franziShut = draw(replace(FRANZI, { face: { ...FRANZI.face, eyes_closed: true } }));
  assert.ok(franziShut.includes(`fill="${OUTLINE}"`));
});
