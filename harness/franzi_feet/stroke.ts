// Harness only: the adult body's half outline stroke in head heights, and the anchors the foot has to meet.
//   node harness/franzi_feet/stroke.ts
import { characterParams, outfit } from "../../ts/src/model.ts";
import { skeletonFor } from "../../ts/src/body.ts";
import { outlineW, strokeW } from "../../ts/src/character.ts";
import "../../ts/src/body-adult-parts.ts";

const p = characterParams({ body: "adult_female", face_age: 1.0, height: 1, outfit: outfit({ tunic_color: null, skirt_color: null, boot_color: null, underwear_top: true }) });
const sk = skeletonFor(p);
const hH = 2 * sk.head_r;
const hs = outlineW(strokeW(sk)) / 2;
console.log(JSON.stringify({ head_r: sk.head_r, hH, outline_w: 2 * hs, hs, hs_in_H: hs / hH, ankle_y_in_H: (sk.ankle_y - (sk.head_cy + sk.head_r)) / hH, foot_y_in_H: (sk.foot_y - (sk.head_cy + sk.head_r)) / hH }));
