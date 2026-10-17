// Harness only: the underwear-only figure of a body type, no hair below the chin, no garment, for the silhouette
// gate (harness/franzi/gate.py). Never offered by the web tool.
//
//   node harness/franzi/underwear.ts BODY OUT.svg [HEIGHT] [silhouette]
//
// `silhouette` leaves the underwear off, for comparing the plain outline with the target. It draws only the body's
// outline in skin colour: no detail of any kind. Harness only, adults only, never offered by the web tool.

import { mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import { characterParams, outfit } from "../../ts/src/model.ts";
import { skeletonFor } from "../../ts/src/body.ts";
import { ADULT_PARTS, withLoweredHead } from "../../ts/src/body-adult-parts.ts";
import { ALL_PARTS, renderCharacter, renderStages } from "../../ts/src/render.ts";

const [body, out, heightArg, mode] = process.argv.slice(2);
const height = heightArg === "-" ? undefined : heightArg;
if (body === undefined || out === undefined) {
  process.stderr.write("usage: node harness/franzi/underwear.ts BODY OUT.svg [HEIGHT]\n");
  process.exit(2);
}
const p = characterParams({
  body,
  face_age: 1.0,
  hairstyle: "short_layered",
  hair_length: 0.2,
  height: height === undefined ? 1 : Number(height),
  outfit: outfit({ tunic_color: null, skirt_color: null, boot_color: null, underwear_top: true }),
});
mkdirSync(dirname(out), { recursive: true });
if (mode === "silhouette") {
  const none = (): string => "";
  const parts = { ...ALL_PARTS, ...withLoweredHead(ALL_PARTS), ...ADULT_PARTS, _legs_and_boots: none, _underwear_top: none };
  writeFileSync(out, renderStages(p, { metadata: false }, parts).stages.get("doc") as string);
} else {
  writeFileSync(out, renderCharacter(p, null, null, false));
}
const sk = skeletonFor(p);
writeFileSync(out.replace(/\.svg$/, ".json"), JSON.stringify({ canvas_w: sk.canvas_w, canvas_h: sk.canvas_h, head_r: sk.head_r, chin_y: sk.head_cy + sk.head_r, neck_y: sk.neck_y, foot_y: sk.foot_y }));
