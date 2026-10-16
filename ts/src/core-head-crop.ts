// The core-head module, part two: Satoshi's traced crop, his tousled crop, and Risa's fringed cut. Port of character.py's
// hair block from `_crop_real_point` to `_fringed_shade`. Generated once by harness/ts_port/gen_core_head.py from the Python
// (so no coordinate is typed), then owned by hand. See core-head-cuts.ts for the conventions.

import { at, copysign, pyCos, pyMax, pySin, pySlice, radians } from "./pynum.ts";
import type { Chain, Point, Segment } from "./tables.ts";
import {
  CROP_BASE_TIP,
  CROP_CROWN_AT,
  CROP_EDGE,
  CROP_FILL_INSET,
  CROP_FRINGE,
  CROP_FRINGE_START,
  CROP_NOTCHES,
  CROP_REAL_CROWN_AT,
  CROP_REAL_EAR_BUFFER,
  CROP_REAL_EAR_MARGIN,
  CROP_REAL_EAR_X,
  CROP_REAL_EDGE,
  CROP_REAL_FALL,
  CROP_REAL_SCALE,
  CROP_REAL_SIDEBURN_L,
  CROP_REAL_SIDEBURN_PUSH,
  CROP_REAL_SIDEBURN_R,
  CROP_REAL_START,
  CROP_REAL_TEMPLE_L,
  CROP_REAL_TEMPLE_R,
  CROP_REAL_TOL,
  CROP_START,
  CROP_STRAND_RUN,
  CROP_SWEEP,
  CROP_TEMPLE_L,
  CROP_TEMPLE_R,
  CROP_TONE_LIFT,
  CROWN_TO_TEMPLE,
  EAR_BOT_Y,
  EAR_TOP_Y,
  FRINGED_BASE_TIP,
  FRINGED_FRONT,
  FRINGED_LOCKS,
  FRINGED_MASS,
  FRINGED_OPENINGS,
  FRINGED_SHADE,
  FRINGED_STRANDS,
  FRINGED_UNDERSIDE,
  HAIR_FADE,
  type Lock,
  TOUSLE_CROWN,
  TOUSLE_NOTCHES,
  TOUSLE_TEMPLE,
  TOUSLE_TIPS,
  inRange,
} from "./core-head-tables.ts";
import { type Hairline, arc, fallQ, lerp, mirror, pyMinIter, reverse, scalePoint, straight } from "./core-head-cuts.ts";

// ---------------------------------------------------------------------------------------------------------
// Satoshi's traced crop

/**
 * A point from `_CROP_REAL_EDGE` (or `_CROP_REAL_START` at `i=-1`), at
 * render size.
 */
export function cropRealPoint(i: number, pt: Point): Point {
  let [x, y] = pt;
  // A chained comparison, `lo <= y <= hi`, written as the two tests it is.
  const atEarHeight = EAR_TOP_Y - CROP_REAL_EAR_BUFFER <= y && y <= EAR_BOT_Y + CROP_REAL_EAR_BUFFER;
  if (atEarHeight) {
    const floor = CROP_REAL_EAR_X[1] + CROP_REAL_EAR_MARGIN;
    x = copysign(pyMax(Math.abs(x), floor), x);
  } else if (inRange(i, CROP_REAL_SIDEBURN_L) || inRange(i, CROP_REAL_SIDEBURN_R)) {
    x = x * CROP_REAL_SIDEBURN_PUSH;
  }
  return scalePoint([x, y], CROP_REAL_SCALE);
}

/**
 * The traced contour at the size this build wants, left tip round to right.
 *
 * One scalar carries the whole build difference, and that is a measurement
 * rather than a convenience: the canon's chibi contour over its adult one is
 * 1.32 across the crown with a standard deviation of 0.008, and stays near 1.23
 * even down at the jaw where the shoulders make the reading worst. A cut that
 * needed its proportions to change with the build would not come out that flat.
 */
export function cropOutline(fall: number): Chain {
  if (Math.abs(fall - CROP_REAL_FALL) < CROP_REAL_TOL) {
    return [
      cropRealPoint(-1, CROP_REAL_START),
      CROP_REAL_EDGE.map(([c, e], i): Segment => [cropRealPoint(i, c), cropRealPoint(i, e)]),
    ];
  }
  const v = fall / CROP_BASE_TIP;
  const start: Point = [CROP_START[0] * v, CROP_START[1] * v];
  return [start, CROP_EDGE.map(([c, e]): Segment => [[c[0] * v, c[1] * v], [e[0] * v, e[1] * v]])];
}

/**
 * `(temple_l, temple_r, crown_at)` for whichever trace `_crop_outline`
 * picked at this `fall`, since the two traces disagree on where those
 * points fall in their own point lists.
 */
export function cropIndices(fall: number): readonly [number, number, number] {
  if (Math.abs(fall - CROP_REAL_FALL) < CROP_REAL_TOL) {
    return [CROP_REAL_TEMPLE_L, CROP_REAL_TEMPLE_R, CROP_REAL_CROWN_AT];
  }
  return [CROP_TEMPLE_L, CROP_TEMPLE_R, CROP_CROWN_AT];
}

/**
 * The whole silhouette, closed across the nape.
 *
 * The closing edge runs behind the neck and the shoulders at every build and is
 * never seen, so it is one quadratic rather than a shape. It dips below both
 * tips so the join cannot cut the corner off either of them.
 */
export function cropMassShape(fall: number): Chain {
  const [start, edge] = cropOutline(fall);
  const end = at(edge, -1)[1];
  const nape: Point = [(end[0] + start[0]) / 2, pyMax(end[1], start[1]) + 0.18];
  return [start, [...edge, [nape, start]]];
}

/**
 * Both sides of the outline, each running from its bottom tip to the crown.
 *
 * Taken out of the mass's own point data rather than restated, so the two
 * cannot drift apart the way the long cut's fall edge did before task 59 pulled
 * it into shared constants. Two entries rather than one mirrored, because this
 * cut is not symmetric: the canon's is not, and handing back one side let the
 * drawing code stamp the right-hand edge onto the left.
 */
export function cropFallEdge(fall: number): Chain[] {
  const [start, edge] = cropOutline(fall);
  const [, , crownAt] = cropIndices(fall);
  return [
    reverse(at(edge, crownAt)[1], pySlice(edge, crownAt + 1)),
    [start, pySlice(edge, null, crownAt + 1)],
  ];
}

/**
 * The fringe, temple to temple, and nothing else.
 *
 * **The front hair stops above the ear on purpose.** The first version ran the
 * line all the way down both sides to the mass's bottom tips and closed `back`
 * on the mass's whole reversed chain, which meant the front fill covered
 * everything the mass covered. Nothing was left for an ear to be seen in: the
 * ear reads at the chibi and all but vanishes at the adult, and the fix is not
 * to float the ear over the hair but to stop the hair filling the place the
 * canon keeps for it.
 *
 * Both ends sit on the mass's own outline, at the temple points the trace
 * already has, so the stroke still never stops in mid-air.
 *
 * The fringe itself is **not traced yet**. These are the overlapping wedge locks
 * the short cut settled on, tips dipping toward the brow and notches rising
 * about a third of the way back, which is what reads as hair lying over hair
 * rather than as a row of teeth. Tracing it is the next step and wants its own
 * measurement: the canon's fringe boundary is hair against skin, so it can be
 * read off the reference the way the silhouette was.
 */
export function cropHairlineShape(fall: number): Hairline {
  const [, edge] = cropOutline(fall);
  const [templeL, templeR, ] = cropIndices(fall);
  const leftTemple = at(edge, templeL)[1];
  const rightTemple = at(edge, templeR)[1];
  const [lx, ly] = CROP_FRINGE_START;
  const [rx, ry] = at(CROP_FRINGE, -1)[1];
  const line: Segment[] = [
    // out to the temple, past where the forehead ends and the trace with it
    [[(leftTemple[0] + lx) / 2, ly - 0.10], [lx, ly]],
    ...CROP_FRINGE,
    [[(rightTemple[0] + rx) / 2, ry - 0.10], rightTemple],
  ];
  // Back over the crown, taken off the mass's own points and pulled in a
  // fraction of a radius so it is inside the silhouette at every bearing.
  //
  // This was three hand-picked quadratics for a round and it leaked: written as
  // flat multiples of the scale they sat at a constant radius while the traced
  // crown does not, so between two tips the fill ran outside the outline and
  // painted a smooth gold arc past the spikes. The lesson is the one task 59
  // already paid for on the long cut, that an edge stated twice drifts. Nothing
  // here restates the crown.
  const crown = reverse(at(edge, templeL)[1], pySlice(edge, templeL + 1, templeR + 1))[1];
  const k = 1.0 - CROP_FILL_INSET;
  const back: Segment[] = crown.map(([c, e]): Segment => [[c[0] * k, c[1] * k], [e[0] * k, e[1] * k]]);
  // The last end has to be the temple itself, not the pulled-in copy of it, so
  // the fill closes exactly where the fringe's stroke started.
  back[back.length - 1] = [at(back, -1)[0], leftTemple];
  return [leftTemple, line, back];
}

/**
 * Where the crop fades to its tip tone: the fringe's own edge, lifted.
 *
 * The same traced chain the fringe is drawn from, moved up by `_CROP_TONE_LIFT`
 * and extended out to the mass on both sides. That is the cheap way to get what
 * the canon has, and it works for a reason worth stating: a *uniform* lift over
 * a boundary whose blades end at different depths leaves every blade pale from a
 * fixed distance above its own tip, so the pale sits in the tips and the gold at
 * the roots without any of it being stated per lock.
 *
 * What it does not reproduce is that the canon varies how far the pale climbs
 * from lock to lock. This gives them all the same depth. The bar here is the
 * spirit of an edge per lock rather than the canon's own, and one list used
 * twice is worth more than a second list that can drift from the first.
 *
 * It replaces a single wave at a fixed height, which could only ever say "pale
 * below this line" and read as a white liner under a gold cap.
 */
export function cropTipEdge(fall: number): Chain[] {
  const v = fall / CROP_BASE_TIP;
  const lift = CROP_TONE_LIFT;
  const edge = 1.35 * v;
  const floor = fall + 1.5;
  const [sx, sy] = CROP_FRINGE_START;
  const [ex, ey] = at(CROP_FRINGE, -1)[1];
  return [
    [
      [-edge, sy - lift],
      [
        [[(-edge + sx) / 2, sy - lift], [sx, sy - lift]],
        ...CROP_FRINGE.map(([c, e]): Segment => [[c[0], c[1] - lift], [e[0], e[1] - lift]]),
        [[(ex + edge) / 2, ey - lift], [edge, ey - lift]],
        [[edge, floor * 0.6], [edge, floor]],
        [[0.0, floor], [-edge, floor]],
      ],
    ],
  ];
}

/**
 * Lines dividing the crown into locks, each aimed at a notch of the fringe.
 *
 * Without them the crown is one field of hair colour, which is what makes a cut
 * read as an object the colour of hair rather than as hair. They scale with the
 * mass, since they live on it.
 */
export function cropStrands(fall: number): Chain[] {
  const v = fall / CROP_BASE_TIP;
  const out: [Point, Segment[]][] = [];
  for (const [x, y] of CROP_NOTCHES) {
    // Up from a notch of the traced fringe, leaning the way the lock sweeps.
    // One line where two locks meet is what reads as overlap rather than as a
    // gap, which is the thing the canon does and a plain zigzag does not.
    const top: Point = [x + CROP_SWEEP, y - CROP_STRAND_RUN];
    out.push([[x, y], [[[(x + top[0]) / 2 + CROP_SWEEP * 0.5, (y + top[1]) / 2], top]]]);
  }
  // Two long ones over the crown as well, or the top of the head is one field of
  // hair colour and the cut reads as an object rather than as hair.
  for (const [x0, y0, x1, y1] of [
    [-0.62, -0.72, -1.00, -0.24],
    [0.70, -0.70, 1.04, -0.22],
  ] as const) {
    out.push([
      [x0 * v, y0 * v],
      [[[((x0 + x1) / 2) * v, ((y0 + y1) / 2) * v], [x1 * v, y1 * v]]],
    ]);
  }
  return out;
}

// ---------------------------------------------------------------------------------------------------------
// Satoshi's tousled crop

/**
 * The right side, temple down to the side lock's point. One piece because
 * the mass draws it and `fall_edge` hands the same points to the front lock,
 * the same agreement `_FALL_*` exists for on the long cut.
 */
export function tousleSide(tip: number): Segment[] {
  return [
    [[1.30, -0.24], [1.26, 0.02]],
    [[1.20, 0.26], [1.12, tip - 0.20]],
    [[1.18, tip + 0.04], [1.02, tip + 0.06]],
  ];
}

export function polar(deg: number, radius: number): Point {
  const a = radians(deg);
  return [radius * pySin(a), -radius * pyCos(a)];
}

export function chain(start: Point, points: readonly Point[]): Segment[] {
  const segments: Segment[] = [];
  let prev = start;
  for (const q of points) {
    segments.push(straight(prev, q));
    prev = q;
  }
  return segments;
}

/**
 * The crop's outer contour: a spiked crown rising to a cowlick right of
 * centre, temple spikes, side locks past the ear, and a ragged nape.
 */
export function tousleMassShape(tip: number): Chain {
  const leftSide = tousleSide(tip).map(([c, e]): Segment => [mirrorPt(c), mirrorPt(e)]);
  const leftTemple: Point = [-TOUSLE_TEMPLE[0], TOUSLE_TEMPLE[1]];
  return [
    leftTemple,
    [
      ...chain(leftTemple, TOUSLE_CROWN.map(([d, r]) => polar(d, r))),
      straight(polar(...at(TOUSLE_CROWN, -1)), TOUSLE_TEMPLE),
      ...tousleSide(tip),
      // The nape, right to left: shorter points than the sides, and the middle
      // of it tucks up behind the skull where the neck covers it anyway.
      [[1.00, tip + 0.10], [0.88, tip + 0.24]],
      [[0.76, tip + 0.02], [0.62, tip + 0.14]],
      [[0.42, tip + 0.28], [0.20, tip + 0.20]],
      [[0.00, tip + 0.32], [-0.20, tip + 0.20]],
      [[-0.42, tip + 0.28], [-0.62, tip + 0.14]],
      [[-0.76, tip + 0.02], [-0.88, tip + 0.24]],
      [[-1.00, tip + 0.10], [-1.10, tip + 0.04]],
      ...reverse(leftTemple, leftSide)[1],
    ],
  ];
}

export function mirrorPt(q: Point): Point {
  return [-q[0], q[1]];
}

/**
 * The side lock's outer edge, its point back up to the temple. Traces the
 * mass's own side exactly, so the two strokes land on each other.
 */
export function tousleFallEdge(tip: number): Chain {
  return reverse(TOUSLE_TEMPLE, tousleSide(tip));
}

/**
 * Up the left side lock, across the fringe, down the right.
 *
 * The fringe is a row of separate pointed locks, not a scalloped edge: the
 * notches rise most of the way back up the forehead, so each lock is a blade
 * with dark either side of it rather than a tooth on a band. That is the single
 * biggest difference between the crop the canon draws and the one this
 * replaces, and it is why the notch list is as deep as it is.
 */
export function tousleHairlineShape(tip: number): Hairline {
  const rightEdge = tousleFallEdge(tip);
  const leftDown = reverse(...mirror(...tousleFallEdge(tip)));
  // Back across the crown inside the mass, so the mass's own outline carries
  // the silhouette and the skull outline never shows through the hair.
  // The radius comes off the crown's own deepest notch rather than being picked.
  // At a picked 1.16 this arc stood outside the silhouette near the temple, where
  // the crown's notches drop to 1.06, and the fill painted past the outline with
  // no stroke on it to show what had happened. A constant radius under a notched
  // crown is the mistake; the notch that decides it has to be the one in the data.
  const [, innerCrown] = arc(pyMinIter(TOUSLE_CROWN.map(([, r]) => r)) - 0.04, CROWN_TO_TEMPLE, -CROWN_TO_TEMPLE, 4);
  const back: Segment[] = [...rightEdge[1], ...innerCrown, ...leftDown[1]];
  const start: Point = at(back, -1)[1];
  const line: Segment[] = [
    // Up the inside of the left side lock to where the fringe starts.
    [[-1.16, tip - 0.14], [-1.10, tip - 0.40]],
    [[-1.04, -0.06], [-0.98, TOUSLE_NOTCHES[0][1]]],
    ...tousleFringeLine(),
    // Down the inside of the right side lock to its point.
    [[1.04, -0.06], [1.10, tip - 0.40]],
    [[1.16, tip - 0.14], rightEdge[0]],
  ];
  return [start, line, back];
}

/**
 * The fringe as quadratics: notch, point, notch, point. Controls sit along
 * each edge rather than off it, so a lock is a blade with a slight bow in it
 * and not a bulge.
 */
export function tousleFringeLine(): Segment[] {
  const segments: Segment[] = [];
  TOUSLE_TIPS.forEach((point, i) => {
    const [left, right] = [TOUSLE_NOTCHES[i] as Point, TOUSLE_NOTCHES[i + 1] as Point];
    segments.push([lerp(left, point, 0.55), point]);
    segments.push([lerp(right, point, 0.55), right]);
  });
  return segments;
}

/**
 * One pale region per lock, which is the whole point of this cut.
 *
 * Each fringe lock gets a wedge covering the last `1 - _HAIR_FADE` of its own
 * length, so the boundary runs along the lock the way the canon's does, and the
 * ratio of the two tones is the shared one rather than this cut's own. The
 * regions overlap freely: a clip path is the union of its children, so they only
 * have to cover the right area between them, not tile it.
 */
export function tousleTipEdge(tip: number): Chain[] {
  const regions: Chain[] = [];
  TOUSLE_TIPS.forEach((point, i) => {
    const [left, right] = [TOUSLE_NOTCHES[i] as Point, TOUSLE_NOTCHES[i + 1] as Point];
    // The top edge drops to each lock's own fade height, but keeps the notch
    // x values rather than following the lock's edges inward. Following them
    // inward is the obvious construction and it is wrong: it gives a wedge
    // the same shape as the lock and half the size, which is narrower than
    // the two outline strokes running down the lock's sides, so the tone is
    // painted and then covered up. Measured on the first attempt, only three
    // locks out of eight showed any of it. Keeping the notch x values makes
    // the region wider than the lock at every height, and a clip only has to
    // cover the area, not match it.
    const a: Point = [left[0], left[1] + (point[1] - left[1]) * (1.0 - HAIR_FADE)];
    const b: Point = [right[0], right[1] + (point[1] - right[1]) * (1.0 - HAIR_FADE)];
    // Past the point rather than up to it, for the same reason.
    const far = lerp(lerp(left, right, 0.5), point, 1.35);
    // Controls on the midpoints, so each side of the region is a straight line.
    regions.push([a, [[lerp(a, b, 0.5), b], [lerp(b, far, 0.5), far], [lerp(far, a, 0.5), a]]]);
  });
  // The sides and the nape, which hang the same way as each other and so take
  // one region between them, bounded above by a line sloping out to the temples.
  const floor = tip + 1.5;
  regions.push(
    [
      [-1.60, -0.30],
      [
        [[-1.20, 0.16], [-0.90, 0.24]],
        [[0.00, 0.40], [0.90, 0.24]],
        [[1.20, 0.16], [1.60, -0.30]],
        [[1.60, floor * 0.6], [1.60, floor]],
        [[0.00, floor], [-1.60, floor]],
      ],
    ]
  );
  return regions;
}

/**
 * Lines dividing the crown into locks, each aimed at a notch of the fringe.
 *
 * Aimed at the notches on purpose: a line that dies over the middle of a lock
 * contradicts the lock it is lying on, and a line that runs to the crown itself
 * turns the whole set into spokes, which is what made the old cut an umbrella.
 * They start part way down for that reason and there are fewer of them than
 * there are notches, because the canon draws two or three, not one per lock.
 */
export function tousleStrands(tip: number): Chain[] {
  return [
    [[-0.60, -1.02], [[[-0.86, -0.80], [-0.96, -0.52]]]],
    [[-0.10, -1.08], [[[-0.34, -0.86], [-0.52, -0.66]]]],
    [[0.22, -1.14], [[[0.16, -0.90], [0.02, -0.72]]]],
    [[0.34, -1.06], [[[0.52, -0.86], [0.66, -0.62]]]],
    [[0.80, -1.04], [[[1.02, -0.80], [1.10, -0.50]]]],
    // One down each side lock, following it rather than crossing it.
    [[1.26, -0.30], [[[1.30, 0.10], [1.20, tip - 0.24]]]],
    [[-1.26, -0.30], [[[-1.30, 0.10], [-1.20, tip - 0.24]]]],
  ];
}

// ---------------------------------------------------------------------------------------------------------
// Risa's fringed cut

// END fringed trace
/** A traced chain at `fall` (`_fall_q`). */
export function fringed(chain: Chain, fall: number): Chain {
  const q = fallQ(fall, FRINGED_BASE_TIP);
  const [start, segs] = chain;
  return [q(start), segs.map(([c, e]): Segment => [q(c), q(e)])];
}

export function fringedMass(fall: number): Chain {
  return fringed(FRINGED_MASS, fall);
}

/**
 * The whole front piece is one closed outline, all of it stroked, so the hairline
 * is that outline and there is no separate closing edge.
 */
export function fringedHairline(fall: number): Hairline {
  const [start, line] = fringed(FRINGED_FRONT, fall);
  return [start, line, []];
}

export function fringedFallEdge(fall: number): Chain[] {
  return [];
}

export function fringedTipEdge(fall: number): Chain[] {
  return [fringedMass(fall)];
}

export function fringedStrands(fall: number): Chain[] {
  return FRINGED_STRANDS.map((c) => fringed(c, fall));
}

export function fringedLocks(fall: number): Lock[] {
  const q = fallQ(fall, FRINGED_BASE_TIP);
  return FRINGED_LOCKS.map(([role, pts, w, ln]): Lock => [role, pts.map(q), w, ln]);
}

export function fringedUnderside(fall: number): readonly [Chain, readonly Chain[]] {
  return [fringed(FRINGED_UNDERSIDE, fall), []];
}

export function fringedOpenings(fall: number): Chain[] {
  return FRINGED_OPENINGS.map((c) => fringed(c, fall));
}

export function fringedShade(fall: number): Chain[] {
  return FRINGED_SHADE.map((c) => fringed(c, fall));
}

