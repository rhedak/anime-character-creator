// Harness only, adults only, never offered by the web tool or the API: the adult body's bare chest, for checking the bust
// shape against the reference. The body outline in skin colour with the two breasts' edges drawn as outlines and nothing else
// on them: no nipples, no other detail, no underwear top (the briefs stay on). Reached only from here; nothing in the figure's
// own render or in `CharacterParams` can ask for it.
//
//   node harness/franzi/bare_chest.ts OUT.svg [closed|open|thin|taper-a|taper-b|taper-c]
//
// closed: both breasts as closed loops. open: the top arc left out (the line starts under the strap side and ends over the
// inner edge), so each breast reads as a form fading into the chest. thin: the closed loop, its upper half tapering to a
// hairline. Variants for the owner to compare by eye.

import { mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import { adultBreastOutlines, adultBreastPoints, adultBustLine, adultSkin, ADULT_PARTS } from "../../ts/src/body-adult-parts.ts";
import { characterParams, outfit } from "../../ts/src/model.ts";
import { ALL_PARTS, renderStages } from "../../ts/src/render.ts";
import { FRANZI } from "./franzi.ts";
import { OUTLINE, outlineW, strokeW } from "../../ts/src/character.ts";
import type { CharacterParams } from "../../ts/src/params.ts";
import type { Skeleton } from "../../ts/src/skeleton.ts";

const [out, variant = "closed"] = process.argv.slice(2);
if (out === undefined) {
  process.stderr.write("usage: node harness/franzi/bare_chest.ts OUT.svg\n");
  process.exit(2);
}
if (!(FRANZI.face_age >= 0.9)) throw new Error("the bare view is for adults only (face_age at the floor)");
const p = characterParams({ ...FRANZI, outfit: outfit({ ...FRANZI.outfit }) });
const none = (): string => "";
const TAPERS: Record<string, { from: number; to: number; power: number }> = {
  "taper-a": { from: 0.47, to: 0.77, power: 1.4 },
  "taper-b": { from: 0.5, to: 0.95, power: 1.0, floor: 0.5 },
  "taper-b2": { from: 0.5, to: 0.95, power: 1.0, floor: 0.6 },
  "taper-c": { from: 0.47, to: 0.66, power: 2.0 },
};
const outline = (sk: Skeleton, v: string): string => {
  if (v === "closed") return adultBreastOutlines(sk);
  if (v in TAPERS) return adultBustLine(sk, TAPERS[v]);
  const sw = outlineW(strokeW(sk), 0.7);
  const seg = (a: [number, number], b: [number, number], width: number): string =>
    `<path d="M ${a[0].toFixed(1)} ${a[1].toFixed(1)} L ${b[0].toFixed(1)} ${b[1].toFixed(1)}" stroke="${OUTLINE}" stroke-width="${width.toFixed(2)}" stroke-linecap="round" fill="none" />`;
  let svg = "";
  for (const side of adultBreastPoints(sk, 8)) {
    for (let i = 1; i < side.length; i++) {
      const a = side[i - 1]!;
      const b = side[i]!;
      const d = (a.d + b.d) / 2;
      const x = (a.x + b.x) / 2;
      // the top arc: above the breast's middle and away from the inner edge near the centre line
      const upper = d < 0.62 && x > 0.1;
      if (v === "open") {
        if (!upper) svg += seg(a.pos as [number, number], b.pos as [number, number], sw);
      } else {
        const k = upper ? Math.max(0.15, (d - 0.49) / 0.13) : 1;
        svg += seg(a.pos as [number, number], b.pos as [number, number], sw * k);
      }
    }
  }
  return svg;
};
const parts = {
  ...ALL_PARTS,
  ...ADULT_PARTS,
  _torso: (sk: Skeleton, q: CharacterParams) => adultSkin(sk, q) + outline(sk, variant),
  _underwear_top: none,
};
mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, renderStages(p, { metadata: false }, parts).stages.get("doc") as string);
