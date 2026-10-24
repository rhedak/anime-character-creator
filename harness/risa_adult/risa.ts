// Draws Risa on the adult woman's body (docs/risa-adult-plan.md) in her underwear alone, optionally with overrides, for the harness's comparisons
// with ref/risa-adult/00-bikini.png. The colours are the medians of the reference's own layers.
//
//   node harness/risa_adult/risa.ts OUT.svg ['{"face":{"eye_size":0.8}}']     overrides are merged over the base

import { mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import { characterParams, faceStyle, outfit } from "../../ts/src/model.ts";
import { renderCharacter } from "../../ts/src/render.ts";
import { skeletonFor } from "../../ts/src/body.ts";
import { replace, type Skeleton } from "../../ts/src/skeleton.ts";
import { ADULT_BUILDS, type AdultBuild } from "../../ts/src/body-adult-build.ts";
import { PRESETS } from "../../ts/src/presets.ts";
import type { CharacterParams } from "../../ts/src/params.ts";

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

/**
 * The parameters and the skeleton for a set of overrides merged over `base`. `_build` (docs/risa-polish-plan.md, stage 2) lays an adult build on the skeleton: a name of
 * `ADULT_BUILDS`, or a whole build object, for fitting one before it has a name. `_preset` starts from a preset instead of `base` (`"risa"`: her uniform).
 */
export function withOverrides(json: string | undefined, base: CharacterParams = RISA_BIKINI): { p: CharacterParams; sk: Skeleton } {
  const { _build, _preset, ...o } = json === undefined ? {} : JSON.parse(json);
  const from = _preset === undefined ? base : (PRESETS[_preset] as CharacterParams);
  const p = characterParams({ ...from, ...o, face: faceStyle({ ...from.face, ...(o.face ?? {}) }), outfit: outfit({ ...from.outfit, ...(o.outfit ?? {}) }) });
  const sk = skeletonFor(p);
  if (_build === undefined) return { p, sk };
  return { p, sk: replace(sk, { adult_build: typeof _build === "string" ? (ADULT_BUILDS[_build] as AdultBuild) : (_build as AdultBuild) }) };
}

const [out, json] = process.argv.slice(2);
if (import.meta.main && out !== undefined) {
  const { p, sk } = withOverrides(json);
  mkdirSync(dirname(out), { recursive: true });
  writeFileSync(out, renderCharacter(p, sk, null, false));
}
