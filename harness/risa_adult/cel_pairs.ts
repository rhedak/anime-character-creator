// Stage 8 of docs/risa-polish-plan.md: blind pairs for the owner, Risa in the soft finish with and without the cel shadows (body-adult-cel.ts), each pair in an order drawn at random and
// written down in a key the owner opens after judging (docs/soft-hair-plan.md's method). The cut is a module constant, so its `celShading` is turned off in place for one render.
//
//   node harness/risa_adult/cel_pairs.ts OUTDIR      writes OUTDIR/<pair>-a.svg, <pair>-b.svg and OUTDIR/key.json

import { mkdirSync, writeFileSync } from "node:fs";
import { adultCutOf } from "../../ts/src/body-adult-cuts.ts";
import { renderCharacter } from "../../ts/src/render.ts";
import { withOverrides } from "./risa.ts";

const [outDir] = process.argv.slice(2);
if (outDir === undefined) {
  process.stderr.write("usage: node harness/risa_adult/cel_pairs.ts OUTDIR\n");
  process.exit(2);
}
mkdirSync(outDir, { recursive: true });
const PAIRS: Readonly<Record<string, string>> = {
  uniform: '{"_preset":"risa","finish":"soft"}',
  bikini: '{"finish":"soft"}',
  waving: '{"_preset":"risa","finish":"soft","right_arm_out":6,"right_elbow":150}',
};
const key: Record<string, string> = {};
for (const [name, json] of Object.entries(PAIRS)) {
  const { p, sk } = withOverrides(json);
  const cut = adultCutOf(p) as { celShading: boolean };
  const withCel = renderCharacter(p, sk, null, false);
  cut.celShading = false;
  const without = renderCharacter(p, sk, null, false);
  cut.celShading = true;
  const celIsA = Math.random() < 0.5;
  writeFileSync(`${outDir}/${name}-a.svg`, celIsA ? withCel : without);
  writeFileSync(`${outDir}/${name}-b.svg`, celIsA ? without : withCel);
  key[name] = celIsA ? "a has the cel shadows" : "b has the cel shadows";
}
writeFileSync(`${outDir}/key.json`, JSON.stringify(key, null, 1) + "\n");
console.log(`wrote ${Object.keys(PAIRS).length} pairs and the key to ${outDir}`);
