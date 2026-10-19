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

/** The dome is the whole of the mass; the front piece, the free locks and the strands are `adultHairFront` (body-adult-parts.ts). */
const swept = makeHairstyle(
  () => ADULT_HAIR_DOME,
  () => nothing,
  (): Chain[] => [[domeStart, domeSegments.slice(0, 0)]],
  () => [],
  { tip_range: [0.25, 0.7] },
);

HAIRSTYLES.swept_ponytail = swept;
