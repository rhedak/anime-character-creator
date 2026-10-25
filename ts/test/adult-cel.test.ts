// The soft finish's cel shadows (body-adult-cel.ts, docs/risa-polish-plan.md stage 8): only in the soft finish and only on a cut that asks for them (Risa's), so the flat finish and Franzi's
// soft drawing are untouched; each is clipped to what it falls on; and the document's ids stay unique, the neck's included where the shirt draws it again.

import assert from "node:assert/strict";
import { test } from "node:test";
import { adultCutOf } from "../src/body-adult-cuts.ts";
import { celOn } from "../src/body-adult-cel.ts";
import { replace } from "../src/model.ts";
import { FRANZI, RISA } from "../src/presets.ts";
import { renderCharacter } from "../src/render.ts";

const draw = (p: typeof RISA): string => renderCharacter(p, null, null, false);
const softly = (p: typeof RISA): typeof RISA => replace(p, { finish: "soft" });
const CLIPS = ["adult-neck-cel", "adult-skirt-cast", "adult-skirt-cel", "adult-blazer-cel"];

test("the cel shadows are drawn only in the soft finish and only on a cut that asks for them", () => {
  assert.equal(adultCutOf(RISA).celShading, true);
  assert.equal(adultCutOf(FRANZI).celShading, false);
  assert.ok(celOn(softly(RISA)) && !celOn(replace(RISA, { finish: "flat" })) && !celOn(softly(FRANZI)));
  const flat = draw(replace(RISA, { finish: "flat" }));
  for (const id of CLIPS) assert.ok(!flat.includes(`id="${id}"`), `flat: ${id}`);
  const soft = draw(softly(RISA));
  for (const id of CLIPS) assert.ok(soft.includes(`id="${id}"`), `soft: ${id}`);
  for (const id of CLIPS) assert.ok(!draw(softly(FRANZI)).includes(`id="${id}"`), `Franzi soft: ${id}`);
});

test("in her underwear the top casts its shadow on the ribs, in the uniform the shirt hides it; the ids stay unique either way", () => {
  const bare = softly(replace(RISA, { outfit: { ...RISA.outfit, tunic_color: null, coat_color: null, skirt_color: null, underwear_top: true } }));
  for (const p of [softly(RISA), bare]) {
    const svg = draw(p);
    const ids = [...svg.matchAll(/ id="([^"]+)"/g)].map((m) => m[1] as string);
    assert.deepEqual(ids.filter((id, k) => ids.indexOf(id) !== k), []);
  }
  assert.ok(draw(bare).includes('id="adult-neck-cel"'));
  assert.ok(draw(softly(RISA)).includes('id="adult-neck-cel-over"'), "the shirt's redrawn neck keeps its own clip");
});
