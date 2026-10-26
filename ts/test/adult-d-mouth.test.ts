// An open mouth on the adult woman: Risa's cut draws the reference's laugh (a D, a lighter fill, teeth and a tongue, lifted toward the nose);
// Franzi's cut keeps the traced line with a dark lip hung below it, exactly as the companion's expression pack drew it.

import assert from "node:assert/strict";
import { test } from "node:test";
import { replace } from "../src/model.ts";
import { FRANZI, RISA } from "../src/presets.ts";
import { MOUTH_INSIDE } from "../src/face.ts";
import { renderCharacter } from "../src/render.ts";

const draw = (p: typeof RISA, mouth_open: number): string => renderCharacter(replace(p, { face: replace(p.face, { mouth_open }) }), null, null, false);

test("Risa's open mouth is the D, with its own fill, teeth and tongue", () => {
  const svg = draw(RISA, 0.9);
  assert.ok(svg.includes("adult-mouth-clip"));
  assert.ok(!svg.includes(MOUTH_INSIDE));
});

test("Risa's closed mouth and Franzi's open one are not the D", () => {
  assert.ok(!draw(RISA, 0).includes("adult-mouth-clip"));
  const franzi = draw(FRANZI, 0.9);
  assert.ok(!franzi.includes("adult-mouth-clip"));
  assert.ok(franzi.includes(MOUTH_INSIDE));
});
