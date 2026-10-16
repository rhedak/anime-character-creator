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
  hair_color: "#17181c",
  eye_color: "#c4922c",
  hairstyle: "swept_ponytail",
  hair_length: 0.5,
  face: faceStyle({
    eye_size: 0.85,
    eye_width: 1.02,
    eye_openness: 0.9,
    eye_tilt: 0.22,
    eye_corner: 0.5,
    iris_size: 0.88,
    iris_aspect: 1.2,
    lid_shadow: 0.25,
    brow_weight: 0.7,
    blush: 0,
    mouth_curve: 0.7,
    mouth_width: 0.65,
    nose_dot: true,
    eye_gap: 0.42,
  }),
  outfit: outfit({ tunic_color: null, skirt_color: null, boot_color: null, underwear_top: true }),
});

const [out, json] = process.argv.slice(2);
if (out !== undefined) {
  const o = json === undefined ? {} : JSON.parse(json);
  const p = characterParams({ ...FRANZI, ...o, face: faceStyle({ ...FRANZI.face, ...(o.face ?? {}) }), outfit: outfit({ ...FRANZI.outfit, ...(o.outfit ?? {}) }) });
  mkdirSync(dirname(out), { recursive: true });
  writeFileSync(out, renderCharacter(p, null, null, false));
}
