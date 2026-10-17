// Franzi as the harness draws her while the head, hair and hands are being tuned (docs/adult-body-plan.md, stage 5).
// Moves to ts/src/presets.ts at stage 5d. Adult floor: face_age 1.0.
//
//   node harness/franzi/franzi.ts OUT.svg ['{"face":{"eye_size":0.8}}']     overrides are merged over the base

import { mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import { characterParams, faceStyle, outfit } from "../../ts/src/model.ts";
import { renderCharacter } from "../../ts/src/render.ts";

export const FRANZI = characterParams({
  body: "adult_female",
  face_age: 1.0,
  skin_tone: "#ffd0b5",
  hair_color: "#1b1c22",
  eye_color: "#c4922c",
  hairstyle: "swept_ponytail",
  hair_length: 0.5,
  face: faceStyle({
    // Risa's eyes (the anime-like tall oval with an iris that fills it), her brows and mouth, with the gap tuned for this head.
    eye_size: 0.82,
    eye_width: 0.694,
    eye_openness: 0.9,
    eye_lower_lid: 1.0,
    eye_tilt: -0.05,
    eye_corner: 0.2,
    eye_gap: 1.3,
    iris_size: 0.978,
    iris_inset: 1.0,
    iris_aspect: 1.5,
    lash: 1.6,
    lid_shadow: 0.15,
    brow_tilt: -0.15,
    brow_weight: 0.9,
    brow_length: 0.9,
    nose_dot: true,
    mouth_curve: 0.6,
    mouth_width: 0.55,
    mouth_drop: 0.06,
    // no blush: the shared blush code redraws the chibi head's outline, which would show round the adult head
    blush: 0,
  }),
  outfit: outfit({ tunic_color: null, skirt_color: null, boot_color: null, underwear_top: true }),
});

const [out, json] = process.argv.slice(2);
if (import.meta.main && out !== undefined) {
  const o = json === undefined ? {} : JSON.parse(json);
  const p = characterParams({ ...FRANZI, ...o, face: faceStyle({ ...FRANZI.face, ...(o.face ?? {}) }), outfit: outfit({ ...FRANZI.outfit, ...(o.outfit ?? {}) }) });
  mkdirSync(dirname(out), { recursive: true });
  writeFileSync(out, renderCharacter(p, null, null, false));
}
