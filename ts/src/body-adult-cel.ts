// The soft finish's cel shadows on the adult woman (docs/risa-polish-plan.md, stage 8): hard-edged shapes in one darker tone of what they lie on, as the reference art shades her
// (ref/risa-adult/00 and 01, read as the pixels darker than their material's median: harness/risa_adult/shadow_map.py). Most are cast shadows, the shape of what casts them moved down a
// little and clipped to what they fall on (the jaw on the neck, the bikini top on the ribs, the skirt on the thighs, the blazer's hem on the skirt); the rest are bands along an edge (the
// torso's sides, the inner thighs, the blazer's sides and lapels, beside the skirt's pleats). Only under `finish = "soft"` and for a character whose cut asks for them (`celShading`:
// Risa's; Franzi's soft drawing is pinned): the flat finish, the house style, has none (CLAUDE.md).

import { adultCutOf } from "./body-adult-cuts.ts";
import { soft } from "./character.ts";
import { shade } from "./colorutil.ts";
import type { CharacterParams } from "./params.ts";
import { fmt2 } from "./pynum.ts";

/** A shadow's tone for each material, as `shade()`'s value factor and saturation boost: skin a little darker and warmer, the dark navy much darker (a shade of it scales with it), the skirt between. */
export const CEL_TONES = {
  skin: [0.86, 1.12],
  blazer: [0.62, 1.0],
  skirt: [0.8, 1.0],
} as const;

export const celTone = (color: string, material: keyof typeof CEL_TONES): string => shade(color, CEL_TONES[material][0], CEL_TONES[material][1]);

/** How far each cast shadow falls below what casts it, in head heights. */
export const CEL_CAST = {
  jaw: 0.08,
  top: 0.035,
  skirt: 0.06,
  blazer: 0.03,
} as const;

/** A shape `d` moved down by `dy` canvas units and filled with `fill`: a cast shadow, for the caller to clip to what it falls on. */
export const castShadow = (d: string, dy: number, fill: string): string => `<path d="${d}" transform="translate(0 ${fmt2(dy)})" fill="${fill}" />`;

/** Whether `p` is drawn with the cel shadows: the soft finish, on a cut that asks for them. */
export const celOn = (p: CharacterParams): boolean => soft(p) && adultCutOf(p).celShading;
