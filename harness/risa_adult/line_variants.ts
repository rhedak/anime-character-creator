// Stage 5 of docs/risa-polish-plan.md: Risa's line work, tried as variants before any of it becomes a setting. Each variant is the preset drawn as it is, then a text pass over the
// finished SVG (as the soft finish's `softStrokeWidths` is): every stroke's width scaled by `scale`, and with `tint`, the hair's outline (the silhouette's, the fringe's and the front
// locks') drawn in the hair's strand tone instead of the black outline. The reference's lines measure about 2 px on the bikini grid everywhere and are near-black on the uniform and the
// legs, dark red on the hair (harness/risa_adult/line_measure.py); ours measure 4 to 6.
//
//   node harness/risa_adult/line_variants.ts OUTDIR ['{"right_arm_out":130}']     writes OUTDIR/<variant>.svg for each variant

import { mkdirSync, writeFileSync } from "node:fs";
import { characterParams } from "../../ts/src/model.ts";
import { renderCharacter } from "../../ts/src/render.ts";
import { OUTLINE } from "../../ts/src/character.ts";
import { colorStr } from "../../ts/src/body-parts-legs.ts";
import { shade } from "../../ts/src/colorutil.ts";
import { adultCutOf } from "../../ts/src/body-adult-cuts.ts";
import { fmt2, pyFloat } from "../../ts/src/pynum.ts";
import { PRESETS } from "../../ts/src/presets.ts";

export interface LineVariant {
  readonly finish: "flat" | "soft";
  readonly scale: number;
  readonly tint: boolean;
}

export const VARIANTS: Readonly<Record<string, LineVariant>> = {
  "a-flat": { finish: "flat", scale: 1.0, tint: false },
  "b-soft": { finish: "soft", scale: 1.0, tint: false },
  "c-flat-060-tint": { finish: "flat", scale: 0.6, tint: true },
  "d-flat-045-tint": { finish: "flat", scale: 0.45, tint: true },
  "e-soft-070-tint": { finish: "soft", scale: 0.7, tint: true },
};

/** `svg` with the line work of `v`: stroke widths scaled, and the hair's outline in the strand tone. */
export function withLines(svg: string, hairColor: string, strandTone: readonly [number, number], v: LineVariant): string {
  let out = svg;
  if (v.tint) {
    const tone = shade(hairColor, strandTone[0], strandTone[1]);
    const hair = colorStr(hairColor);
    // a tag filled with the hair's colour and inked in black: the silhouette and the fringe
    out = out.replace(/<[a-zA-Z][^>]*>/g, (tag) => (tag.includes(`fill="${hair}"`) && tag.includes(`stroke="${OUTLINE}"`) ? tag.replace(`stroke="${OUTLINE}"`, `stroke="${tone}"`) : tag));
    // the front locks' outlines, each in its own masked group
    out = out.replace(/(<g mask="url\(#adult-front-locks-ink\)"><path [^>]*?)stroke="#0d0d0d"/g, `$1stroke="${tone}"`);
  }
  if (v.scale !== 1.0) out = out.replace(/<[a-zA-Z][^>]*>/g, (tag) => tag.replace(/stroke-width="([0-9.]+)"/g, (_m, w: string) => `stroke-width="${fmt2(pyFloat(w) * v.scale)}"`));
  return out;
}

const [outDir, json] = process.argv.slice(2);
if (import.meta.main && outDir !== undefined) {
  mkdirSync(outDir, { recursive: true });
  const base = PRESETS["risa"]!;
  const o = json === undefined ? {} : JSON.parse(json);
  for (const [name, v] of Object.entries(VARIANTS)) {
    const p = characterParams({ ...base, ...o, finish: v.finish });
    const cut = adultCutOf(p);
    writeFileSync(`${outDir}/${name}.svg`, withLines(renderCharacter(p, null, null, false), p.hair_color, cut.strandTone, v));
  }
}
