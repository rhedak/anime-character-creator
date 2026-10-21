// Draws Risa on the adult woman's body (docs/risa-adult-plan.md) in her underwear alone, optionally with overrides, for the harness's comparisons
// with ref/risa-adult/00-bikini.png. The colours are the medians of the reference's own layers.
//
//   node harness/risa_adult/risa.ts OUT.svg ['{"face":{"eye_size":0.8}}']     overrides are merged over the base

import { mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import { characterParams, faceStyle, outfit } from "../../ts/src/model.ts";
import { renderCharacter } from "../../ts/src/render.ts";

export const RISA_BIKINI = characterParams({
  body: "adult_female",
  face_age: 1.0,
  skin_tone: "#fac4a8",
  hair_color: "#7b232d",
  // The iris is two tones, the lower the colour and the upper a dark shade of it: the reference's lower half is (120, 146, 90) and its upper (50, 72, 46).
  eye_color: "#78925a",
  hairstyle: "long_straight_fringed",
  // A bust smaller than the traced one (Franzi's): on the adult woman `bust` is an offset from it, and -0.18 puts the cups at the reference's width and lower edge (harness/risa_adult/bust_metrics.py).
  bust: -0.18,
  hair_length: 0.5,
  outfit: outfit({ tunic_color: null, skirt_color: null, boot_color: null, underwear_top: true, underwear_color: "#f5ebea", hair_clip_color: "#d2a368", hair_clip: "bracket" }),
  face: faceStyle({ eye_openness: 0.85, blush: 1.12 }),
});

const [out, json] = process.argv.slice(2);
if (import.meta.main && out !== undefined) {
  const o = json === undefined ? {} : JSON.parse(json);
  const p = characterParams({ ...RISA_BIKINI, ...o, face: faceStyle({ ...RISA_BIKINI.face, ...(o.face ?? {}) }), outfit: outfit({ ...RISA_BIKINI.outfit, ...(o.outfit ?? {}) }) });
  mkdirSync(dirname(out), { recursive: true });
  writeFileSync(out, renderCharacter(p, null, null, false));
}
