// Draws Franzi (ts/src/presets.ts, FRANZI: the preset, stage 5d of docs/adult-body-plan.md) to a file, optionally with overrides, for the harness's comparisons with the reference.
// She used to be defined here while the head, hair and hands were being tuned; the definition moved into the presets and this re-exports it, so the harness scripts that import FRANZI
// from here still do.
//
//   node harness/franzi/franzi.ts OUT.svg ['{"face":{"eye_size":0.8}}']     overrides are merged over the base

import { mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import { characterParams, faceStyle, outfit } from "../../ts/src/model.ts";
import { FRANZI } from "../../ts/src/presets.ts";
import { renderCharacter } from "../../ts/src/render.ts";

export { FRANZI };

const [out, json] = process.argv.slice(2);
if (import.meta.main && out !== undefined) {
  const o = json === undefined ? {} : JSON.parse(json);
  const p = characterParams({ ...FRANZI, ...o, face: faceStyle({ ...FRANZI.face, ...(o.face ?? {}) }), outfit: outfit({ ...FRANZI.outfit, ...(o.outfit ?? {}) }) });
  mkdirSync(dirname(out), { recursive: true });
  writeFileSync(out, renderCharacter(p, null, null, false));
}
