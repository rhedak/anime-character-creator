// Harness only: Risa's body outline alone (neck to soles, the arms and hands), filled and inked in black, for the silhouette gate (harness/risa_adult/gate.py,
// docs/risa-polish-plan.md stage 1). No hair, no face, no garment, no detail of any kind: the outline the skin is drawn with, so the gate measures the body and nothing over it.
//
//   node harness/risa_adult/body_outline.ts OUT.svg ['{"bust":-0.1}']     overrides as risa.ts takes them (`_build` lays an adult build on the skeleton)

import { mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import { adultBodyPath, inkAttrs } from "../../ts/src/body-adult-parts.ts";
import { withOverrides } from "./risa.ts";

const [out, json] = process.argv.slice(2);
if (out === undefined) {
  process.stderr.write("usage: node harness/risa_adult/body_outline.ts OUT.svg [OVERRIDES_JSON]\n");
  process.exit(2);
}
const { sk } = withOverrides(json);
mkdirSync(dirname(out), { recursive: true });
writeFileSync(
  out,
  `<svg xmlns="http://www.w3.org/2000/svg" width="${sk.canvas_w}" height="${sk.canvas_h}" viewBox="0 0 ${sk.canvas_w} ${sk.canvas_h}">` +
    `<path d="${adultBodyPath(sk)}" ${inkAttrs(sk, "#000000").replace(/stroke="[^"]*"/, 'stroke="#000000"')} /></svg>\n`,
);
writeFileSync(out.replace(/\.svg$/, ".json"), JSON.stringify({ canvas_w: sk.canvas_w, canvas_h: sk.canvas_h, head_r: sk.head_r, chin_y: sk.head_cy + sk.head_r }));
