// Draws Franzi (ts/src/presets.ts, FRANZI: the preset, stage 5d of docs/adult-body-plan.md) to a file, optionally with overrides, for the harness's comparisons with the reference.
// She used to be defined here while the head, hair and hands were being tuned; the definition moved into the presets and this re-exports it, so the harness scripts that import FRANZI
// from here still do.
//
//   node harness/franzi/franzi.ts OUT.svg ['{"face":{"eye_size":0.8}}']     overrides are merged over the base
//   OVERLAY=breasts node harness/franzi/franzi.ts ...                          the full breast contours in red over the figure

import { mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import { characterParams, faceStyle, outfit } from "../../ts/src/model.ts";
import { FRANZI as PRESET } from "../../ts/src/presets.ts";
import { skeletonFor } from "../../ts/src/body.ts";
import { adultBreastOutlines } from "../../ts/src/body-adult-parts.ts";
import { renderCharacter } from "../../ts/src/render.ts";

/**
 * Franzi in her underwear alone: the preset without the dirndl (her blouse, bodice, skirt and apron). The harness compares the body, the head, the hands and the feet with the
 * references, which show her in a bikini, so this is the base here; the preset itself starts in the dirndl.
 */
export const FRANZI = characterParams({ ...PRESET, outfit: outfit({ ...PRESET.outfit, tunic_color: null, bodice_color: null, skirt_color: null, apron_color: null }) });

const [out, json] = process.argv.slice(2);
if (import.meta.main && out !== undefined) {
  const o = json === undefined ? {} : JSON.parse(json);
  const p = characterParams({ ...FRANZI, ...o, face: faceStyle({ ...FRANZI.face, ...(o.face ?? {}) }), outfit: outfit({ ...FRANZI.outfit, ...(o.outfit ?? {}) }) });
  mkdirSync(dirname(out), { recursive: true });
  let svg = renderCharacter(p, null, null, false);
  // OVERLAY=breasts draws the full breast contours in red over everything, to check a garment against the bust (harness/franzi/aligned.py runs this).
  if (process.env.OVERLAY === "breasts") svg = svg.replace(/<\/svg>\s*$/, `${adultBreastOutlines(skeletonFor(p)).replaceAll("#0d0d0d", "#e0102a")}</svg>`);
  writeFileSync(out, svg);
}
