// Franzi's hair, the adult body's first cut: swept back from a centre parting into a low ponytail that falls over the viewer's
// right shoulder, with one long lock down the left of the face. Traced from ref/franzi/ (harness/franzi_hair/trace.py), so the
// data is in body-adult-head-data.ts. Registered as an extra cut: `HAIRSTYLES` mirrors the frozen Python and is enumerated by
// the catalogue and its tests, so a cut with no Python counterpart lives in `EXTRA_HAIRSTYLES` (core-head.ts), which
// `hairstyleFor` also reads.
//
// The hair is one shape drawn over the head. `mass` is its outline joined with the head, and the front piece is the
// hairline followed by the mass's own segments over the top and down the ponytail, so the two share their silhouette exactly
// and nothing doubles. The ponytail and the lock hang clear of the body (nothing of the body lies behind them), so one piece
// in front is enough.

import { EXTRA_HAIRSTYLES, makeHairstyle } from "./core-head.ts";
import type { Chain, Segment } from "./tables.ts";
import { ADULT_HAIR_LINE, ADULT_HAIR_MASS, ADULT_HAIR_STRANDS, ADULT_HAIR_TOP_SEGMENTS } from "./body-adult-head-data.ts";
import type { Hairline } from "./core-head-cuts.ts";

const [massStart, massSegments] = ADULT_HAIR_MASS;
const top: readonly Segment[] = massSegments.slice(0, ADULT_HAIR_TOP_SEGMENTS);
const [lineStart, lineSegments] = ADULT_HAIR_LINE;
const lineEnd = lineSegments[lineSegments.length - 1]![1];

/** A quadratic that is a straight line, so the corners at its ends stay corners. */
const straight = (a: readonly [number, number], b: readonly [number, number]): Segment => [[(a[0] + b[0]) / 2, (a[1] + b[1]) / 2], b];

const swept = makeHairstyle(
  () => ADULT_HAIR_MASS,
  (): Hairline => [lineStart, lineSegments, [straight(lineEnd, massStart), ...top]],
  (): Chain[] => [[massStart, top]],
  () => [],
  { tip_range: [0.25, 0.7], strands: () => [...ADULT_HAIR_STRANDS], strand_weight: 0.5 },
);

EXTRA_HAIRSTYLES.swept_ponytail = swept;
