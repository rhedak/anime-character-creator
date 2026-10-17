// Harness only, adults only, never offered by the web tool or the API: the adult body's bare chest, for checking the bust
// shape against the reference. The body outline in skin colour with the two breasts' edges drawn as outlines and nothing else
// on them: no nipples, no other detail, no underwear top (the briefs stay on). Reached only from here; nothing in the figure's
// own render or in `CharacterParams` can ask for it.
//
//   node harness/franzi/bare_chest.ts OUT.svg

import { mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import { adultBreastOutlines, adultSkin, ADULT_PARTS } from "../../ts/src/body-adult-parts.ts";
import { characterParams, outfit } from "../../ts/src/model.ts";
import { ALL_PARTS, renderStages } from "../../ts/src/render.ts";
import { FRANZI } from "./franzi.ts";
import type { CharacterParams } from "../../ts/src/params.ts";
import type { Skeleton } from "../../ts/src/skeleton.ts";

const [out] = process.argv.slice(2);
if (out === undefined) {
  process.stderr.write("usage: node harness/franzi/bare_chest.ts OUT.svg\n");
  process.exit(2);
}
if (!(FRANZI.face_age >= 0.9)) throw new Error("the bare view is for adults only (face_age at the floor)");
const p = characterParams({ ...FRANZI, outfit: outfit({ ...FRANZI.outfit }) });
const none = (): string => "";
const parts = {
  ...ALL_PARTS,
  ...ADULT_PARTS,
  _torso: (sk: Skeleton, q: CharacterParams) => adultSkin(sk, q) + adultBreastOutlines(sk),
  _underwear_top: none,
};
mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, renderStages(p, { metadata: false }, parts).stages.get("doc") as string);
