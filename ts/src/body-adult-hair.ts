// Franzi's hair, the adult body's first cut: swept back from a centre parting into a low ponytail that falls over the viewer's
// right shoulder, with one long lock down the left of the face. Traced from ref/franzi/ (harness/franzi_hair/trace.py), so the
// data is in body-adult-head-data.ts. Registered in `HAIRSTYLES` (core-head.ts) when this module
// is loaded, which render.ts and catalogue-tables.ts do; since the Python it mirrored is gone it is a cut like the others.
//
// The hair is one shape drawn over the head. `mass` is its outline joined with the head, and the front piece is the
// hairline followed by the mass's own segments over the top and down the ponytail, so the two share their silhouette exactly
// and nothing doubles. The ponytail and the lock hang clear of the body (nothing of the body lies behind them), so one piece
// in front is enough.

import { HAIRSTYLES, makeHairstyle } from "./core-head.ts";
import type { Chain } from "./tables.ts";
import { ADULT_HAIR_DOME } from "./body-adult-head-data.ts";
import type { Hairline } from "./core-head-cuts.ts";

const [domeStart, domeSegments] = ADULT_HAIR_DOME;
const nothing: Hairline = [domeStart, [], []];

/**
 * The region of the hair in its `hair_tip_color`: everything from `from` head radii below the head's centre down, as a chain (a wide box, the silhouette clips it). The adult hair is traced
 * silhouettes, not the shared fall, so a cut says where its tips begin as one height: Franzi's ponytail ends at 1.73, Risa's hair at 4.21. Drawn by `adultHairShape` and `adultFrontLocks`.
 */
export function tipBand(from: number): Chain[] {
  const mid = (a: readonly [number, number], b: readonly [number, number]): [number, number] => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
  const corners: [number, number][] = [[-3, from], [3, from], [3, 9], [-3, 9], [-3, from]];
  return [[corners[0] as [number, number], corners.slice(1).map((c, i) => [mid(corners[i] as [number, number], c), c] as const)]];
}

/** The dome is the whole of the mass; the front piece, the free locks and the strands are `adultHairFront` (body-adult-parts.ts). */
const swept = makeHairstyle(
  () => ADULT_HAIR_DOME,
  () => nothing,
  (): Chain[] => [[domeStart, domeSegments.slice(0, 0)]],
  () => tipBand(0.95),
  { tip_range: [0.25, 0.7] },
);

HAIRSTYLES.swept_ponytail = swept;

/**
 * Risa's cut, long and straight with a blunt fringe, hanging behind the shoulders and the arms (docs/risa-adult-plan.md). Like the swept ponytail it is drawn by the adult head
 * parts, from its own traced data (body-adult-cuts.ts, body-adult-risa-data.ts); the shared hair code only ever sees the dome, which the shared parts that measure the head
 * (the clip, the brows over the hair) read.
 */
HAIRSTYLES.long_straight_fringed = makeHairstyle(
  () => ADULT_HAIR_DOME,
  () => nothing,
  (): Chain[] => [[domeStart, domeSegments.slice(0, 0)]],
  () => tipBand(2.6),
  { tip_range: [0.25, 0.7] },
);
