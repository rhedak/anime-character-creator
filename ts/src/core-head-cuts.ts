// The core-head module, part one: the helpers every cut shares (`fall`, `mirror`, `reverse`, `arc`), the long cut, the short
// layered cut, Satoko's traced cut with its clumps, and the parted cut. Port of character.py's hair block from `_fade_y`
// to `_parted_underside`. Generated once by harness/ts_port/gen_core_head.py from the Python (so no coordinate is typed),
// then owned by hand. Function names are the Python ones in camelCase, and every expression keeps Python's evaluation
// order, since a different order rounds differently. The tables are in core-head-tables.ts.

import { PyError, at, pyCos, pyDiv, pyMax, pyMin, pySin, pySlice, pySqrt, radians, truthy } from "./pynum.ts";
import type { Chain, Point, Segment } from "./tables.ts";
import {
  CROP_LOCKS,
  CROWN_R,
  CROWN_TO_TEMPLE,
  FALL_CHEEK_X,
  FALL_FLARE_X,
  FALL_MID_X,
  FALL_TEMPLE_X,
  FALL_TIP_X,
  FALL_WIDE_X,
  HAIR_CHEEK_Y,
  HAIR_CROWN_Y,
  HAIR_FADE,
  HAIR_TIP_LINE,
  LONG_BASE_TIP,
  LONG_CROWN_AT,
  LONG_EDGE,
  LONG_EDGE_START,
  LONG_LINE,
  LONG_LINE_START,
  LONG_LINE_TUCK,
  LONG_LOCKS,
  LONG_LOCKS_FALL,
  LONG_TONE_LIFT,
  type Lock,
  PARTED_APEX_L,
  PARTED_APEX_R,
  PARTED_BASE_TIP,
  PARTED_CROWN_AT,
  PARTED_EDGE,
  PARTED_LINE,
  PARTED_LOCKS,
  PARTED_LOCKS_FALL,
  PARTED_LOCK_L,
  PARTED_LOCK_R,
  PARTED_SEAM_L,
  PARTED_SEAM_LIFT,
  PARTED_SEAM_R,
  PARTED_TIPS_BEHIND,
  PARTED_TIPS_FRONT,
  PARTED_TONE_LIFT,
  PARTED_TONE_WIDEN,
  PARTED_UNDER_L,
  PARTED_UNDER_R,
  SHORT_LOCKS,
} from "./core-head-tables.ts";

/** `min(items)` and `max(items)` over an iterable: first of equal extremes wins, and an empty one raises as Python does. */
export function pyMinIter(items: readonly number[]): number {
  if (items.length === 0) throw new PyError("ValueError", "min() iterable argument is empty");
  return pyMin(items[0] as number, ...items.slice(1));
}
/** See `pyMinIter`. */
export function pyMaxIter(items: readonly number[]): number {
  if (items.length === 0) throw new PyError("ValueError", "max() iterable argument is empty");
  return pyMax(items[0] as number, ...items.slice(1));
}

/** A hairline: its start, the line drawn, and the edge that closes the front's fill back to the start. */
export type Hairline = readonly [Point, readonly Segment[], readonly Segment[]];

// ---------------------------------------------------------------------------------------------------------
// The shared helpers

/**
 * The two-tone boundary for hair running from `top` to `bottom`, both in
 * head radii. Cuts wave their own edge around this line rather than sitting
 * flat on it, since a level boundary reads as a painted band.
 */
export function fadeY(top: number, bottom: number): number {
  return top + HAIR_FADE * (bottom - top);
}

export function fall(f: number, length: number): number {
  return HAIR_CHEEK_Y + f * (length - HAIR_CHEEK_Y);
}

export function mirror(start: Point, segments: readonly Segment[]): Chain {
  const flip = (q: Point): Point => [-q[0], q[1]];
  return [flip(start), segments.map(([c, e]): Segment => [flip(c), flip(e)])];
}

/**
 * Both sides of a symmetric cut's lock edge, right first.
 *
 * Ordered, never a set: `ref-out/` is compared byte for byte, so the order
 * these come out in has to be the order they went in.
 */
export function mirrored(edge: Chain): Chain[] {
  return [edge, mirror(...edge)];
}

/**
 * `_lerp(a, b, f)` of character.py, on two points. skeleton.py has a `_lerp` of its own, on three numbers, and the call
 * recorder (and so `calls.test.ts`, which finds a function by its name alone) keeps both under the name `lerp`; so this one
 * also answers the scalar call, `a + (b - a) * t`, exactly as skeleton.py's does.
 */
export function lerp(a: number, b: number, t: number): number;
export function lerp(a: Point, b: Point, f: number): Point;
export function lerp(a: number | Point, b: number | Point, f: number): number | Point {
  if (typeof a === "number") return a + ((b as number) - a) * f;
  b = b as Point;
  return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f];
}

/**
 * A point scaled by `k` from the head centre. Used by the crop and the
 * long-real traces to blow a measured contour up to house size.
 */
export function scalePoint(pt: Point, k: number): Point {
  return [pt[0] * k, pt[1] * k];
}

/**
 * Walk a quadratic chain backwards. Reversing a quadratic is just
 * swapping its endpoints and keeping the control point, so this is exact
 * and the two directions trace the same pixels.
 */
export function reverse(start: Point, segments: readonly Segment[]): Chain {
  const anchors = [start, ...segments.map(([, end]) => end)];
  const controls = segments.map(([ctrl]) => ctrl);
  const out: Segment[] = [];
  for (let i = controls.length - 1; i >= 0; i--) out.push([controls[i] as Point, anchors[i] as Point]);
  return [at(anchors, -1), out];
}

/**
 * A circular arc about the head centre, as quadratics, in head-radius units.
 * Angles are degrees clockwise from straight up, so 0 is the top of the head.
 *
 * A quadratic follows a circle closely enough at these spans if its control
 * point sits on the bisector at `r / cos(half the segment's angle)`, the same
 * construction `_head_shape` uses. Placing anchors and controls by hand instead
 * is what gives a crown that scallops between them: the wobble is not texture,
 * it is the segments failing to agree on a radius.
 */
export function arc(r: number, fromDeg: number, toDeg: number, segments: number): Chain {
  const pt = (deg: number, radius: number): Point => {
    const a = radians(deg);
    return [radius * pySin(a), -radius * pyCos(a)];
  };

  const step = pyDiv(toDeg - fromDeg, segments);
  const ctrlR = pyDiv(r, pyCos(radians(step / 2)));
  const out: Segment[] = [];
  for (let i = 0; i < segments; i++) out.push([pt(fromDeg + step * (i + 0.5), ctrlR), pt(fromDeg + step * (i + 1), r)]);
  return [pt(fromDeg, r), out];
}

// ---------------------------------------------------------------------------------------------------------
// The long cut

/**
 * The mass's outer edge on the right side, tip up to the cheek. Both the
 * mass and the front lock are built from this, so their edges coincide
 * exactly: where the mass shows, the two strokes land on each other, and
 * where the body covers it, the lock's stroke carries the silhouette on.
 */
export function fallEdge(length: number): Chain {
  const y = (f: number): number => fall(f, length);

  return [[FALL_TIP_X, y(1.00)], [
    [[FALL_FLARE_X, y(0.82)], [FALL_WIDE_X, y(0.62)]],
    [[FALL_MID_X, y(0.30)], [FALL_CHEEK_X, HAIR_CHEEK_Y]],
  ]];
}

/**
 * Crown, then falls that flare outward on the way down, ending in
 * pointed locks. This one shape carries the hair's only outer contour.
 *
 * The silhouette is a bell, not a curtain: slimmer where it passes the
 * face (1.16 at the cheek), widest below the shoulders (1.52 at the
 * controls), then tapering back to the tips. Widest at the skull it read
 * as a tall egg next to the canon, which flares every fall outward and
 * keeps the crown low. Chosen from a side-by-side lab over the straight
 * version and a half-bell; the full bell won at both builds.
 *
 * The bottom edge is tips and notches rather than a blunt curve: the canon
 * ends every fall in points. Offsets around the tip line are absolute head
 * radii rather than fractions of the fall, so the points stay the same
 * size on the chibi's short fall as on the adult's long one, the way the
 * short cut's lock ends are sized.
 */
export function hairMassShape(length: number): Chain {
  const y = (f: number): number => fall(f, length);

  const tip = y(1.00);
  return [[-1.02, -0.30], [
    [[-0.86, HAIR_CROWN_Y - 0.06], [0.00, HAIR_CROWN_Y]],
    [[0.86, HAIR_CROWN_Y - 0.06], [1.02, -0.30]],
    [[FALL_TEMPLE_X, 0.20], [FALL_CHEEK_X, HAIR_CHEEK_Y]],
    [[FALL_MID_X, y(0.30)], [FALL_WIDE_X, y(0.62)]],
    [[FALL_FLARE_X, y(0.82)], [FALL_TIP_X, tip]],
    [[1.08, tip + 0.04], [0.92, tip - 0.24]],
    [[0.76, tip - 0.16], [0.60, tip + 0.10]],
    [[0.44, tip + 0.02], [0.30, tip - 0.20]],
    [[0.14, tip - 0.12], [0.00, tip + 0.06]],
    [[-0.14, tip - 0.12], [-0.30, tip - 0.20]],
    [[-0.44, tip + 0.02], [-0.60, tip + 0.10]],
    [[-0.76, tip - 0.16], [-0.92, tip - 0.24]],
    [[-1.08, tip + 0.04], [-FALL_TIP_X, tip]],
    [[-FALL_FLARE_X, y(0.82)], [-FALL_WIDE_X, y(0.62)]],
    [[-FALL_MID_X, y(0.30)], [-FALL_CHEEK_X, HAIR_CHEEK_Y]],
    [[-FALL_TEMPLE_X, 0.20], [-1.02, -0.30]],
  ]];
}

/**
 * Where hair fades to its tip tone. Only the part crossing the two side
 * falls is ever visible, the rest sits behind the head and body. The edge
 * scallops deeply, dipping toward the tips between anchors, so the fade
 * follows the locks the way the canon's does instead of waving gently
 * across them as one line. Closes into a region covering everything below.
 *
 * Both the line and the scallops around it are placed as fractions of the
 * hair's own height rather than of the fall, so the ratio of the two tones
 * and the size of the wave hold at every build. See `_HAIR_FADE`.
 */
export function hairTipEdge(length: number): Chain[] {
  const span = length - HAIR_CROWN_Y;

  // Above the line and below it, by a fraction of that height. Anchors ride
  // high and the controls pull the curve down between them, so each scallop
  // hangs from two points rather than arching over them, and the depths vary
  // a little so the row does not come out as one repeated wave.
  const hi = (d: number): number => fadeY(HAIR_CROWN_Y, length) - span * d;

  const lo = (d: number): number => fadeY(HAIR_CROWN_Y, length) + span * d;

  const floor = length + 1.5;
  // One region, because this cut's locks all hang the same way: a wave across
  // them is already a per-lock boundary, near enough. A cut whose locks point in
  // different directions returns one region each instead.
  return [
    [
      [-1.90, hi(0.045)],
      [
        [[-1.60, lo(0.075)], [-1.24, hi(0.040)]],
        [[-0.98, lo(0.080)], [-0.72, hi(0.050)]],
        [[-0.48, lo(0.070)], [-0.24, hi(0.040)]],
        [[0.00, lo(0.085)], [0.24, hi(0.040)]],
        [[0.48, lo(0.070)], [0.72, hi(0.050)]],
        [[0.98, lo(0.080)], [1.24, hi(0.040)]],
        [[1.60, lo(0.075)], [1.90, hi(0.045)]],
        [[1.90, floor * 0.6], [1.90, floor]],
        [[0.00, floor], [-1.90, floor]],
      ],
    ]
  ];
}

/**
 * The hairline: up one lock in front of the cheek, across the fringe to
 * the parting at the crown, then back down the other side. This is the only
 * line drawn inside the mass, which is what lets front and back hair read as
 * a single object. Both ends land exactly on the mass's own tips, where the
 * silhouette stroke takes over, so the line never stops in mid-air.
 *
 * The second list closes the fringe's fill back to the start. It stays just
 * inside the mass the whole way, so the two fills overlap rather than butt
 * together, and outside the head circle, so the skull outline never shows
 * through the hair.
 */
export function hairlineShape(length: number): Hairline {
  const y = (f: number): number => fall(f, length);

  const start: Point = [-1.22, y(1.00)];
  const line: Segment[] = [
    [[-1.18, y(0.97)], [-1.08, y(0.85)]],
    [[-0.98, y(0.60)], [-0.90, y(0.28)]],
    [[-0.92, 0.70], [-0.88, 0.35]],
    // The fringe is a high part with two sweeps, not a curtain: the apex
    // sits well up the forehead and the sweeps descend toward the outer eye
    // corners, so a triangle of skin shows. That structure is the canon's
    // and stays. An earlier pass pulled the whole fringe down to the brow
    // line to cure a bare-headed look and was reverted, correctly: the cure
    // is the sweeps, not blanket coverage, and hair can sit high as long as
    // it visibly comes *from* the part and lies across the forehead on its
    // way down. The part is right of centre, where the crown strands
    // radiate from, and the two sweeps are unequal, so the cut reads parted
    // without the silhouette giving up its mirrored point data.
    //
    // What was wrong was the amount, not the idea. Measured down the centre
    // line, the canon's fringe reaches 0.147 of the figure's height and ours
    // reached 0.109, so the apex sat about 0.19 head radii too high and the
    // triangle it opened was half again too tall. The forehead run below is
    // that much lower, blended to nothing at the temples so the side locks
    // do not move, which leaves the part and the exposed wedge intact and
    // only takes back the excess. Lowering it further closes the part and
    // crowds the brows, which is where the reverted pass went wrong.
    [[-0.72, 0.16], [-0.52, -0.18]],
    [[-0.22, -0.31], [0.12, -0.49]],
    [[0.36, -0.31], [0.58, -0.20]],
    [[0.78, 0.10], [0.88, 0.35]],
    [[0.92, 0.70], [0.90, y(0.28)]],
    [[0.98, y(0.60)], [1.08, y(0.85)]],
    [[1.18, y(0.97)], [1.22, y(1.00)]],
  ];
  // Down the fall the fringe's outer edge is the mass's own edge, so the
  // lock can carry the silhouette where the body hides the mass. Above the
  // cheek it tucks inside instead, which is what keeps the temple seamless.
  const [, rightEdge] = fallEdge(length);
  const [, leftDown] = reverse(...mirror(...fallEdge(length)));
  const back: Segment[] = [
    ...rightEdge,
    [[1.05, 0.10], [1.00, -0.30]],
    [[0.84, -1.16], [0.00, -1.10]],
    [[-0.84, -1.16], [-1.00, -0.30]],
    // Meets the mirrored fall edge at the cheek, so this has to be the same
    // x the mass and `_fall_edge` use. Hardcoded here it silently disagreed
    // with them the first time the fall was widened, and the left fall came
    // out with a sliver of mass outside the lock.
    [[-1.05, 0.10], [-FALL_CHEEK_X, HAIR_CHEEK_Y]],
    ...leftDown,
  ];
  return [start, line, back];
}

/**
 * Lines dividing the long cut into locks: sweeps off a parting just right
 * of centre across the crown, a pair down each fall, and short flicks in the
 * fringe. Unlike the short cut's, which radiate from a crown whorl, these
 * fall with the hair: the fall lines run nearly the whole drop, which is
 * what turns the two side curtains into hanging locks.
 */
export function longStrands(length: number): Chain[] {
  const y = (f: number): number => fall(f, length);

  // The outer line down the right fall. Long enough that writing its mirror out
  // as a second row wraps, and a wrapped row no longer reads as the twin of the
  // one above it, so this pair is mirrored rather than spelled twice.
  //
  // These x values ride with `_FALL_CHEEK_X` and its neighbours, 0.10 head radii
  // further out than they were when the fall was narrower. A strand that stays
  // put while the edge moves out ends up outside its own lock, and then it is
  // not a division inside the hair, it is a second boundary a hair's width in
  // from the silhouette: two parallel lines down the fall, which is what the
  // first attempt at widening this produced.
  const outerLock: [Point, Segment[]] = [
    [1.14, 0.10],
    [[[1.42, y(0.28)], [1.38, y(0.58)]], [[1.32, y(0.78)], [1.36, y(0.94)]]],
  ];
  return [
    // Crown sweeps, following the parting right of centre like the fringe's
    // own peak. They start part way down rather than at the crown itself: run
    // all the way up, four lines converging inside a patch a fifth of a head
    // radius across read as spokes off a hub, which is the same thing that
    // made the short cut look like an umbrella. Cut back to the outer half of
    // each sweep they read as the divisions between locks instead, which is
    // what the canon draws, and it draws fewer of them than this.
    [[-0.32, -0.87], [[[-0.53, -0.70], [-0.66, -0.50]]]],
    [[-0.59, -0.73], [[[-0.84, -0.50], [-0.96, -0.24]]]],
    [[0.41, -0.79], [[[0.54, -0.58], [0.62, -0.34]]]],
    [[0.68, -0.63], [[[0.89, -0.37], [1.00, -0.06]]]],
    // One long line down each fall, drifting outward with the bell, and a
    // shorter inner one, so the fall divides into three unequal locks.
    outerLock,
    mirror(...outerLock),
    [[1.04, 0.40], [[[1.18, y(0.30)], [1.15, y(0.55)]]]],
    [[-1.04, 0.40], [[[-1.18, y(0.30)], [-1.15, y(0.55)]]]],
    // Fringe flicks following the sweeps, ending just above the hairline.
    [[0.26, -0.74], [[[0.36, -0.64], [0.42, -0.55]]]],
    [[-0.16, -0.76], [[[-0.32, -0.64], [-0.46, -0.48]]]],
  ];
}

/**
 * `_hairline_shape`, with the fringe parted at the centre instead of swept
 * to one side: two even sweeps off a single peak at x=0, mirrored left and
 * right, in place of the one asymmetric sweep off a part right of centre
 * that cut carries. Everything else, both falls, the crown closure, is
 * that function's own geometry unchanged, since this cut reuses
 * `_hair_mass_shape` and `_fall_edge` outright and has to retrace their
 * seams exactly or the double-line the hair contract warns about (see
 * `_hairline_shape`) shows up here too.
 */
export function centerPartHairlineShape(length: number): Hairline {
  const y = (f: number): number => fall(f, length);

  const start: Point = [-1.22, y(1.00)];
  const line: Segment[] = [
    [[-1.18, y(0.97)], [-1.08, y(0.85)]],
    [[-0.98, y(0.60)], [-0.90, y(0.28)]],
    [[-0.92, 0.70], [-0.88, 0.35]],
    // The part: two even sweeps off one peak at the crown's own centre
    // line. This is the entire visual difference from `_hairline_shape`;
    // everything else in this function is copied from it verbatim.
    [[-0.68, 0.14], [-0.42, -0.14]],
    [[-0.18, -0.36], [0.00, -0.46]],
    [[0.18, -0.36], [0.42, -0.14]],
    [[0.68, 0.14], [0.88, 0.35]],
    [[0.92, 0.70], [0.90, y(0.28)]],
    [[0.98, y(0.60)], [1.08, y(0.85)]],
    [[1.18, y(0.97)], [1.22, y(1.00)]],
  ];
  const [, rightEdge] = fallEdge(length);
  const [, leftDown] = reverse(...mirror(...fallEdge(length)));
  const back: Segment[] = [
    ...rightEdge,
    [[1.05, 0.10], [1.00, -0.30]],
    [[0.84, -1.16], [0.00, -1.10]],
    [[-0.84, -1.16], [-1.00, -0.30]],
    [[-1.05, 0.10], [-FALL_CHEEK_X, HAIR_CHEEK_Y]],
    ...leftDown,
  ];
  return [start, line, back];
}

/**
 * Division lines for the centre-part cut: mirrored sweeps off the part
 * in place of `_long_strands`' off-centre crown sweeps and fringe flicks.
 * The fall-dividing lines (`outer_lock` and the shorter inner pair) are
 * `_long_strands`' own, unchanged, since both cuts share the same fall.
 */
export function centerPartStrands(length: number): Chain[] {
  const y = (f: number): number => fall(f, length);

  const outerLock: [Point, Segment[]] = [
    [1.14, 0.10],
    [[[1.42, y(0.28)], [1.38, y(0.58)]], [[1.32, y(0.78)], [1.36, y(0.94)]]],
  ];
  const sweepOuter: [Point, Segment[]] = [
    [-0.30, -0.86],
    [[[-0.54, -0.68], [-0.72, -0.44]]],
  ];
  const sweepInner: [Point, Segment[]] = [
    [-0.12, -0.82],
    [[[-0.28, -0.62], [-0.40, -0.40]]],
  ];
  const flick: [Point, Segment[]] = [
    [-0.14, -0.60],
    [[[-0.26, -0.48], [-0.36, -0.32]]],
  ];
  return [
    sweepOuter,
    mirror(...sweepOuter),
    sweepInner,
    mirror(...sweepInner),
    outerLock,
    mirror(...outerLock),
    [[1.04, 0.40], [[[1.18, y(0.30)], [1.15, y(0.55)]]]],
    [[-1.04, 0.40], [[[-1.18, y(0.30)], [-1.15, y(0.55)]]]],
    flick,
    mirror(...flick),
  ];
}

// ---------------------------------------------------------------------------------------------------------
// The short layered cut

/**
 * A short layered cut: the skull, side locks coming down in front of the
 * ears to ragged points, and the nape tucked up behind the jaw.
 *
 * Its points are placed straight off `tip` instead of going through `_fall`,
 * which measures a long fall down from the cheek line and so cannot describe
 * hair that ends above the chin at all.
 *
 * The silhouette is a crop, not a bob: the bulk ends around ear level,
 * hugging the skull at 1.26 past the cheek, and what reaches lower is only
 * ragged tips, a side spike flicking down and out, a second tip below it,
 * and a nape flick that shows beside the neck. It used to fall in two long
 * side locks framing the face to below the cheeks, which is a girl's bob in
 * miniature; every satoshi ref ends the bulk at the ear. The centre of the
 * rim tucks behind the skull, so only the outer tips are ever visible, and
 * more of the nape shows at taller builds as the jaw narrows off it.
 *
 * The crown is one circular arc, kept deliberately clean. Hand-placed
 * points once scalloped it, and a later attempt at additive cowlick flicks
 * (bumps rising off the arc, tried 2026-08-06) read as wobble too and was
 * reverted on the owner's call; the tousle may be revisited, but any
 * version of it has to beat the plain circle by eye first. The hair reads
 * as locks through the strands, the fringe and the rim, so the crown does
 * not have to carry any of it.
 */
export function shortMassShape(tip: number): Chain {
  const [leftTemple, crown] = arc(CROWN_R, -CROWN_TO_TEMPLE, CROWN_TO_TEMPLE, 4);
  return [leftTemple, [
    ...crown,
    [[1.30, -0.10], [1.26, 0.08]],
    [[1.34, tip - 0.34], [1.31, tip - 0.08]],
    [[1.16, tip - 0.28], [1.05, tip - 0.04]],
    [[1.02, tip + 0.02], [0.97, tip + 0.20]],
    [[0.88, tip - 0.04], [0.78, tip + 0.10]],
    [[0.68, tip + 0.16], [0.54, tip + 0.44]],
    [[0.30, tip + 0.16], [0.00, tip + 0.22]],
    [[-0.30, tip + 0.16], [-0.54, tip + 0.44]],
    [[-0.68, tip + 0.16], [-0.78, tip + 0.10]],
    [[-0.88, tip - 0.04], [-0.97, tip + 0.20]],
    [[-1.02, tip + 0.02], [-1.05, tip - 0.04]],
    [[-1.16, tip - 0.28], [-1.31, tip - 0.08]],
    [[-1.34, tip - 0.34], [-1.26, 0.08]],
    [[-1.30, -0.10], leftTemple],
  ]];
}

/**
 * The side lock's outer edge, tip up to the temple. Traces the mass's own
 * outer edge in reverse, exactly, for the same reason `_fall_edge` does, which
 * is why it has to end on the same temple point the crown arc starts from.
 */
export function shortFallEdge(tip: number): Chain {
  const [, crown] = arc(CROWN_R, -CROWN_TO_TEMPLE, CROWN_TO_TEMPLE, 4);
  const rightTemple = at(crown, -1)[1];
  return [[0.97, tip + 0.20], [
    [[1.02, tip + 0.02], [1.05, tip - 0.04]],
    [[1.16, tip - 0.28], [1.31, tip - 0.08]],
    [[1.34, tip - 0.34], [1.26, 0.08]],
    [[1.30, -0.10], rightTemple],
  ]];
}

/**
 * Where the crop fades to its tip tone: a wave about the line half way
 * down the cut, so the sideburns, the rim tips, the nape and the lower part
 * of the fringe are all pale and the crown stays in the base colour. This is
 * what the canon shows, and it is the same ratio the long cut carries.
 *
 * The wave is deep enough to cross the fringe's lock tips rather than run
 * level over them: a straight line there reads as a band painted across the
 * head, and the fringe is the one place on this cut where the boundary is
 * seen against a wide field of hair rather than down a narrow lock.
 *
 * The offsets are absolute head radii rather than fractions of the height,
 * which the long cut needs: this cut's `tip` comes from a `tip_range`, so it
 * sits at the same depth whatever the build, and the whole silhouette with it.
 *
 * Earlier passes put this band far lower, at a third of the way up from the
 * tips. A per-spike boundary hugging each tip was tried before that and lost
 * the two-tone look almost entirely.
 */
export function shortTipEdge(tip: number): Chain[] {
  // Half way down what is seen of the crop rather than half way down its
  // silhouette. The nape flick and the inner rim run behind the jaw and the
  // shoulders at every build, so the height the ratio divides ends at the
  // sideburn tips, not at the lowest point of the shape. Even then the line
  // came out just under the fringe and the cut still read as a blonde head
  // with pale sides, so it lifts another 0.07 head radii to cross the
  // fringe's own tips, where the canon has it.
  const mid = fadeY(-CROWN_R, tip + 0.20) - 0.07;
  const floor = tip + 1.5;
  return [
    [
      [-1.90, mid - 0.10],
      [
        [[-1.58, mid + 0.06], [-1.30, mid - 0.04]],
        [[-1.06, mid + 0.10], [-0.86, mid - 0.02]],
        [[-0.55, mid + 0.10], [-0.30, mid]],
        [[0.00, mid + 0.12], [0.30, mid]],
        [[0.55, mid + 0.10], [0.86, mid - 0.02]],
        [[1.06, mid + 0.10], [1.30, mid - 0.04]],
        [[1.58, mid + 0.06], [1.90, mid - 0.10]],
        [[1.90, floor * 0.6], [1.90, floor]],
        [[0.00, floor], [-1.90, floor]],
      ],
    ]
  ];
}

/**
 * The short cut's fringe: up one side lock, across a fringe that stops just
 * above the brows, and down the other. Both ends land on the mass's own tips,
 * same contract as the long style's hairline. The fringe's two halves are not
 * mirror images, which is what gives it a sweep without the asymmetry having to
 * reach the silhouette.
 *
 * Brows sit at about -0.35, so the fringe bottoms out just above them, same
 * line the long style settled on. It used to stop around -0.55, which left the
 * tall bare forehead that had already been fixed on the long cut. The temples
 * come down to eye level too, where the fringe runs into the side locks.
 *
 * The fringe is a row of overlapping wedge locks rather than one arc: tips dip
 * toward the brows and the notches between them rise only about a third as far,
 * so it reads as hair lying over hair. Rising the whole way between tips gives a
 * row of teeth instead, which is worth knowing because it was the first thing
 * tried. The locks lengthen away from the parting, which sits right of centre.
 */
export function shortHairlineShape(tip: number): Hairline {
  const [, rightEdge] = shortFallEdge(tip);
  const [, leftDown] = reverse(...mirror(...shortFallEdge(tip)));
  // Back across the crown on a smaller arc than the mass's, so the mass's own
  // outline carries the silhouette rather than being painted over, and well
  // outside the head circle, so the skull outline never shows through the hair.
  // This edge is only ever a fill boundary, never stroked, so it can start from
  // the outer temple the fall edge left off at without the radius change showing.
  const [, innerCrown] = arc(CROWN_R - 0.10, CROWN_TO_TEMPLE, -CROWN_TO_TEMPLE, 4);
  const back: Segment[] = [...rightEdge, ...innerCrown, ...leftDown];
  // Both ends land on the mass's own lock tips, which is what `back` starts and
  // finishes on, so the hairline never stops in mid-air wherever those move to.
  const start: Point = at(back, -1)[1];
  const line: Segment[] = [
    [[-1.06, tip - 0.02], [-1.02, tip - 0.30]],
    [[-0.98, 0.10], [-0.92, -0.18]],
    // The locks vary in width, depth and direction on purpose: a wide
    // shallow one, a high notch showing a patch of forehead, a deep
    // narrow tip reaching for the brow, a small crossing kink. The old
    // row repeated one wedge and read as a pattern, and a fringe is the
    // one place this style wants its irregularity.
    [[-0.86, -0.46], [-0.70, -0.34]],
    [[-0.58, -0.58], [-0.44, -0.52]],
    [[-0.36, -0.24], [-0.28, -0.14]],
    [[-0.20, -0.44], [-0.06, -0.40]],
    [[0.04, -0.20], [0.14, -0.24]],
    [[0.24, -0.52], [0.40, -0.46]],
    [[0.52, -0.26], [0.62, -0.30]],
    [[0.78, -0.16], [0.94, -0.16]],
    [[0.98, 0.10], [1.02, tip - 0.30]],
    [[1.06, tip - 0.02], [0.97, tip + 0.20]],
  ];
  return [start, line, back];
}

/**
 * Lines dividing the crop into locks: across the crown on the parting's own
 * lines, each dying near a notch of the fringe, plus one line down each
 * sideburn. They no longer reach the parting itself, for the reason below.
 * The sideburns used to carry a second line each, but the crop's
 * side band is too narrow for two: they read as tram lines and were cut.
 *
 * Without these the crown is one unbroken field of hair colour, which is what
 * made the cut read as an object rather than as hair: a render with the strands
 * suppressed and everything else in place still looks like a pot.
 */
export function shortStrands(tip: number): Chain[] {
  // Each crown line starts part way along its own path rather than at the
  // crown. Drawn full length all six left the same patch at the top of the
  // skull, and six lines from one point on a part-circle mass is a beach
  // umbrella: the spokes were doing as much damage as the dome. Trimmed to
  // their outer halves they sit spread across the crown, each still aimed at
  // its notch of the fringe, and read as the seams between locks. Trimming
  // further, or dropping to four lines, empties the crown and the cut goes back
  // to reading as one smooth field.
  //
  // The dome itself is untouched here. That is the parked crown tousle, and
  // what is left after this is exactly the shape of it.
  return [
    [[-0.49, -0.85], [[[-0.67, -0.64], [-0.74, -0.38]]]],
    [[-0.15, -0.77], [[[-0.22, -0.56], [-0.12, -0.44]]]],
    [[0.24, -0.81], [[[0.29, -0.62], [0.36, -0.48]]]],
    [[0.52, -0.81], [[[0.64, -0.61], [0.66, -0.36]]]],
    [[0.74, -0.68], [[[0.95, -0.44], [1.06, -0.18]]]],
    [[-0.70, -0.71], [[[-0.95, -0.47], [-1.06, -0.20]]]],
    [[1.14, -0.44], [[[1.20, 0.04], [1.14, tip - 0.28]]]],
    [[-1.14, -0.44], [[[-1.20, 0.04], [-1.14, tip - 0.28]]]],
  ];
}

// ---------------------------------------------------------------------------------------------------------
// Satoko's traced cut

/**
 * The traced contour with its fall stretched to `fall`, its crown left alone.
 *
 * A long cut does not scale as one piece, and the contract already says so:
 * above the cheek line hair is pinned to the skull, below it the points are a
 * fraction of the way down to the tips. So only y below `_HAIR_CHEEK_Y` is
 * remapped, and x is left as traced, because a fall that hangs further does not
 * also hang wider.
 *
 * Scaling the whole contour was tried and is wrong twice over. It carries the
 * crown up with the tips, which at the adult build puts it past the canvas
 * ceiling; and it needs a head-relative `tip_range` to stay inside that, which
 * stops a long cut lengthening with the body at all. That is the thing the
 * body-relative branch of `_hair_fall` exists for.
 *
 * The realistic build used to switch this to a separate trace off
 * `ref/satoko-real.jpg` (`harness/trace/real/satoko_real.py`; later the
 * `long_traced_real` cut, retired with that build),
 * used only at the exact `fall` it was measured at. The owner's call on
 * 2026-08-12 was to remove that override: once the build slider made every
 * value in between reachable, the chibi contour stretched past where it was
 * ever measured read better than the "correct" adult trace, so this stretch
 * now runs at every `fall`, the realistic build included.
 */
export function longScaled(fall: number): Chain {
  const span = LONG_BASE_TIP - HAIR_CHEEK_Y;
  const k = truthy(span) ? pyDiv(fall - HAIR_CHEEK_Y, span) : 1.0;

  const q = (pt: Point): Point => {
    const y = pt[1];
    return y > HAIR_CHEEK_Y ? [pt[0], HAIR_CHEEK_Y + (y - HAIR_CHEEK_Y) * k] : pt;
  };

  return [q(LONG_EDGE_START), LONG_EDGE.map(([c, e]): Segment => [q(c), q(e)])];
}

/**
 * The traced hairline, with the stretch that the falls get and the face does
 * not: above the cheek line it is pinned to the head, below it it rides the
 * fall down.
 */
export function longLine(fall: number): Chain {
  const span = LONG_BASE_TIP - HAIR_CHEEK_Y;
  const k = truthy(span) ? pyDiv(fall - HAIR_CHEEK_Y, span) : 1.0;

  const q = (pt: Point): Point => {
    const y = pt[1];
    return y > HAIR_CHEEK_Y ? [pt[0], HAIR_CHEEK_Y + (y - HAIR_CHEEK_Y) * k] : pt;
  };

  const line: Segment[] = LONG_LINE.map(([c, e]): Segment => [q(c), q(e)]);
  // The two ends are tucked toward the centre. At a fall's bottom tip the inner
  // and outer edges of the hair converge, so the traced hairline's last point
  // and the traced mass's last point are within a stroke of each other, and the
  // fit can put the inner one a hair outside. This keeps the fill inside the
  // silhouette without moving anything a viewer can see.
  const start: Point = [q(LONG_LINE_START)[0] + LONG_LINE_TUCK, q(LONG_LINE_START)[1]];
  const [ctrl, end] = at(line, -1);
  line[line.length - 1] = [ctrl, [end[0] - LONG_LINE_TUCK, end[1]]];
  return [start, line];
}

/** The whole silhouette, closed behind the shoulders where it is never seen. */
export function longTracedMass(fall: number): Chain {
  const [start, edge] = longScaled(fall);
  const end = at(edge, -1)[1];
  return [start, [...edge, [[(end[0] + start[0]) / 2, pyMax(end[1], start[1]) + 0.16], start]]];
}

/**
 * Both sides of the outline, each from its tip up to the crown. Taken out of
 * the mass's own points rather than restated, and given per side rather than
 * mirrored, since nothing here promises the trace is symmetric.
 */
export function longTracedFallEdge(fall: number): Chain[] {
  const [start, edge] = longScaled(fall);
  return [
    reverse(at(edge, LONG_CROWN_AT)[1], pySlice(edge, LONG_CROWN_AT + 1)),
    [start, pySlice(edge, null, LONG_CROWN_AT + 1)],
  ];
}

/**
 * Her parting, and the line down the inside of each fall.
 *
 * That second part is the whole of what a viewer reads as hair lying in front
 * of the shoulder rather than behind it, and the first version of this cut did
 * not have it: the inner boundary was traced by sweeping bearings from the head
 * centre, and below the cheek a fall runs almost straight down, so a whole
 * fall's worth of it fell between two bearings. `out/trace/satoko.py` scans rows
 * there instead and the two readings agree where they meet, both being the same
 * drawn line.
 *
 * `back` closes the fill on the mass's own contour, so the front hair covers
 * exactly the band between the hairline and the silhouette, which is what the
 * hair *is*. The two short connectors across each fall's bottom are the only
 * invented geometry here.
 *
 * Straight chords, not bowed ones and not a radial inset: a control placed off
 * the line between two silhouette points can leave it (that used to put the
 * fill 0.010 head radii outside the outline at a tip), and a radial inset used
 * to pull the fill 0.05-0.10 head radii inside the outline along the falls,
 * leaving an unfilled band between the gold and the stroke that read worst at
 * the tips where the lock is only a few hundredths wide. Chords of the mass
 * stay inside the silhouette on their own, and both mass tips are path ends so
 * the fill reaches the tip of each fall rather than cutting the corner.
 */
export function longTracedHairline(fall: number): Hairline {
  const [start, edge] = longScaled(fall);
  const [hs, hg] = longLine(fall);
  const end = at(hg, -1)[1];
  const [massStart, massBack] = reverse(start, edge);
  // Right tip, full reverse silhouette to the left tip, then back to the
  // hairline. Both tips are endpoints so the tip wedges fill solid.
  const back: Segment[] = [
    [[(end[0] + massStart[0]) / 2, (end[1] + massStart[1]) / 2], massStart],
    ...massBack,
    [[(start[0] + hs[0]) / 2, (start[1] + hs[1]) / 2], hs],
  ];
  return [hs, hg, back];
}

/**
 * Where the falls turn pale: the mass's own edge, lifted, but never above the
 * half-way line.
 *
 * Two rules, and the second is what a long cut needs that a crop does not. The
 * lift is the crop's trick: a uniform lift over an edge whose tips end at
 * different depths leaves every tip pale from a fixed distance above its own
 * point, so the pale follows the hair instead of cutting a level line across it.
 * The clamp then holds the boundary at `_fade_y`'s half-and-half height wherever
 * the lifted edge would climb above it, which is everywhere but the two falls.
 * Without it the lift carries on over the crown and turns the whole head pale.
 *
 * A first version took only the segments lying below the head centre, which is
 * not a contiguous run, and left a gold wedge poking into the pale at the foot
 * of each fall.
 */
export function longTracedTipEdge(fall: number): Chain[] {
  const [start, edge] = longScaled(fall);
  return liftedTipEdge(start, edge, LONG_TONE_LIFT * (fall / LONG_BASE_TIP));
}

/**
 * The tip-toned region under a long cut's mass edge: the edge pushed up by
 * `lift` and held at the fade line, the construction `_long_traced_tip_edge`
 * describes, shared by the traced long cuts.
 */
export function liftedTipEdge(start: Point, edge: readonly Segment[], lift: number): Chain[] {
  const top = pyMinIter(edge.map(([, e]) => e[1]));
  const bottom = pyMaxIter(edge.map(([, e]) => e[1]));
  const fade = fadeY(top, bottom);
  const floor = bottom + 1.0;
  const wide = pyMaxIter(edge.map(([, e]) => Math.abs(e[0]))) + 0.25;

  // The contour, sampled and pushed up, then held at the fade line.
  const pts: Point[] = [];
  let prev = start;
  for (const [ctrl, end] of edge) {
    for (let i = 1; i < 7; i++) {
      const t = i / 6;
      // `x ** 2` is `x * x` here (the kernel's rule for an integer exponent).
      const x = (1 - t) * (1 - t) * prev[0] + 2 * (1 - t) * t * ctrl[0] + t * t * end[0];
      const y = (1 - t) * (1 - t) * prev[1] + 2 * (1 - t) * t * ctrl[1] + t * t * end[1];
      pts.push([x, pyMax(y - lift, fade)]);
    }
    prev = end;
  }

  const chain: Segment[] = [];
  let here: Point = [-wide, fade];
  const ring: Point[] = [...pts, [wide, fade], [wide, floor], [-wide, floor], [-wide, fade]];
  for (const q of ring) {
    chain.push([[(here[0] + q[0]) / 2, (here[1] + q[1]) / 2], q]);
    here = q;
  }
  return [[[-wide, fade], chain]];
}

// ---------------------------------------------------------------------------------------------------------
// The clumps the soft finish lays over the cuts (`Hairstyle.locks`)

/**
 * Clumps authored at a tip depth of `authored_fall`, drawn at `fall`: only y below the cheek
 * line is remapped, x as authored, the way `_long_scaled` stretches the contour.
 */
export function restretchLocks(locks: readonly Lock[], authoredFall: number, fall: number): Lock[] {
  const k = pyDiv(fall - HAIR_CHEEK_Y, authoredFall - HAIR_CHEEK_Y);

  const q = (pt: Point): Point => {
    const y = pt[1];
    return y > HAIR_CHEEK_Y ? [pt[0], HAIR_CHEEK_Y + (y - HAIR_CHEEK_Y) * k] : pt;
  };

  return locks.map(([role, pts, w, ln]): Lock => [role, pts.map(q), w, ln]);
}

export function longTracedLocks(fall: number): Lock[] {
  return restretchLocks(LONG_LOCKS, LONG_LOCKS_FALL, fall);
}

export function shortLocks(fall: number): Lock[] {
  return [...SHORT_LOCKS];
}

export function cropLocks(fall: number): Lock[] {
  return [...CROP_LOCKS];
}

export function partedLocks(fall: number): Lock[] {
  return restretchLocks(PARTED_LOCKS, PARTED_LOCKS_FALL, fall);
}

/**
 * The two sweep lines the canon draws off the parting, and one down each
 * fall. They scale with the mass, since they live on it.
 */
export function longTracedStrands(fall: number): Chain[] {
  const v = fall / LONG_BASE_TIP;
  const out: Chain[] = [];
  for (const [x0, y0, cx0, cy0, x1, y1] of [
    [-0.30, -0.72, -0.62, -0.42, -0.86, -0.05],
    [0.34, -0.74, 0.66, -0.44, 0.90, -0.08],
  ] as const) {
    out.push([[x0, y0], [[[cx0, cy0], [x1, y1]]]]);
  }
  for (const side of [-1, 1]) {
    out.push([
      [side * 1.02 * v, 0.10 * v],
      [[[side * 1.10 * v, 0.70 * v], [side * 1.06 * v, 1.30 * v]]],
    ]);
  }
  return out;
}

// ---------------------------------------------------------------------------------------------------------
// The parted cut

/**
 * A traced point at `fall`, for a cut traced to end at `base_tip`. Above the cheek line pinned to the skull, as on
 * every long cut, and x as traced. Below it the vertical scale ramps
 * smoothly, from its strongest at the cheek line to its lightest at the
 * tips, rather than one linear squash (`_long_scaled`'s rule).
 *
 * That squash flattened the tips into hooks curling outward on a short fall
 * (Linnea's 1.89 is 0.56 of the trace, Chiyo's 1.36 is 0.31), where long
 * straight sides take the same squash unharmed. Holding the tips' last head
 * radius rigid was tried next and made it worse elsewhere: the run above them
 * had to take the whole change, collapsed to a sixth of itself on Linnea, and
 * the silhouette stepped out to the tips' width as a shelf. So the tips keep
 * the square root of the overall scale (`k`), the cheek line takes what is
 * left (`2k` less that, never under a fifth of `k`), and the scale in between
 * is linear in depth, so the tips land on `fall` exactly and nothing kinks. A
 * longer fall than the trace's stretches the run above the tips and leaves
 * the tips as traced. At the traced length it is the identity.
 */
export function fallQ(fall: number, baseTip: number): (pt: Point) => Point {
  const span = baseTip - HAIR_CHEEK_Y;
  const k = pyDiv(fall - HAIR_CHEEK_Y, span);
  const kz = pyMin(1.0, pySqrt(k), 1.8 * k);
  const km = 2 * k - kz;

  const q = (pt: Point): Point => {
    const [x, y] = pt;
    const u = y - HAIR_CHEEK_Y;
    if (u <= 0) return pt;
    if (u <= span) return [x, HAIR_CHEEK_Y + km * u + pyDiv((kz - km) * u * u, 2 * span)];
    return [x, HAIR_CHEEK_Y + k * span + kz * (u - span)];
  };

  return q;
}

/** `_fall_q` for the parted cut. */
export function partedQ(fall: number): (pt: Point) => Point {
  return fallQ(fall, PARTED_BASE_TIP);
}

/** A traced chain at `fall` (`_parted_q`). */
export function parted(chain: Chain, fall: number): Chain {
  const q = partedQ(fall);
  const [start, segs] = chain;
  return [q(start), segs.map(([c, e]): Segment => [q(c), q(e)])];
}

/** A chain's `i`th anchor: 0 its start, `i + 1` the end of segment `i`. */
export function anchor(chain: Chain, i: number): Point {
  return i === 0 ? chain[0] : at(chain[1], i - 1)[1];
}

/** The run of `chain` from anchor `a` to anchor `b`, `a < b`. */
export function subChain(chain: Chain, a: number, b: number): Chain {
  return [anchor(chain, a), pySlice(chain[1], a, b)];
}

// character.py defines `_straight` twice (a bisecting-control one at line 1990 and this one, further down): Python binds the
// later one before any call, so only this one is ported.
/**
 * A quadratic that is a straight line, so the anchors either side of it stay
 * corners. Tips have to be corners: a control point off the line rounds the
 * point over and the lock stops reading as a lock.
 */
export function straight(a: Point, b: Point): Segment {
  return [lerp(a, b, 0.5), b];
}

/** The whole silhouette, closed behind the body where it is never seen. */
export function partedMass(fall: number): Chain {
  const [start, edge] = parted(PARTED_EDGE, fall);
  const end = at(edge, -1)[1];
  return [start, [...edge, [[(end[0] + start[0]) / 2, pyMax(end[1], start[1]) + 0.16], start]]];
}

/**
 * The face opening and each front lock's inner edge, and the front's
 * closing edge: up the right lock's outer edge to the top of it, the seam out
 * to the silhouette, the mass's own segments over the crown, the left seam,
 * and down the left lock's outer edge to where the line started. The
 * stretch over the crown is the mass's, so the front can never paint past it.
 */
export function partedHairline(fall: number): Hairline {
  const edge = parted(PARTED_EDGE, fall);
  const [start, line] = parted(PARTED_LINE, fall);
  const lockL = parted(PARTED_LOCK_L, fall);
  const [, upRight] = reverse(...parted(PARTED_LOCK_R, fall));
  const [qR, over] = reverse(...subChain(edge, PARTED_SEAM_L + 1, PARTED_SEAM_R + 1));
  const back: Segment[] = [
    ...upRight,
    straight(at(upRight, -1)[1], qR),
    ...over,
    straight(at(over, -1)[1], lockL[0]),
    ...lockL[1],
  ];
  return [start, line, back];
}

/**
 * What the front strokes besides its hairline: each lock's outer edge, and
 * the silhouette from each seam to the crown, which the front's fill covers
 * half of and so draws again.
 */
export function partedFallEdge(fall: number): Chain[] {
  const edge = parted(PARTED_EDGE, fall);
  return [
    parted(PARTED_LOCK_L, fall),
    subChain(edge, PARTED_SEAM_L + 1, PARTED_CROWN_AT + 1),
    subChain(edge, PARTED_CROWN_AT + 1, PARTED_SEAM_R + 1),
    parted(PARTED_LOCK_R, fall),
  ];
}

/**
 * `_lifted_tip_edge` on this cut's silhouette, pushed out sideways by
 * `_PARTED_TONE_WIDEN` first. The outer falls widen downward, so the edge
 * lifted straight up lies inside the silhouette, and a sliver down the
 * outside of each fall kept the top colour (Satoko's pale tips). The region
 * only clips the hair, so running past the silhouette costs nothing.
 */
export function partedTipEdge(fall: number): Chain[] {
  let [start, edge] = parted(PARTED_EDGE, fall);

  const out = (pt: Point): Point => [pt[0] * PARTED_TONE_WIDEN, pt[1]];

  edge = edge.map(([c, e]): Segment => [out(c), out(e)]);
  return liftedTipEdge(out(start), edge, PARTED_TONE_LIFT * (fall / PARTED_BASE_TIP));
}

/**
 * Each tip's line, behind and in front, from its apex `_HAIR_TIP_LINE`
 * along the tip's bisector, both ends stretched with the fall.
 */
export function partedTipLines(fall: number): readonly [readonly (readonly [Point, Point])[], readonly (readonly [Point, Point])[]] {
  const q = partedQ(fall);

  const lines = (tips: readonly (readonly [Point, Point])[]): [Point, Point][] => {
    const out: [Point, Point][] = [];
    for (const [[ax, ay], [dx, dy]] of tips) {
      out.push([q([ax, ay]), q([ax + dx * HAIR_TIP_LINE, ay + dy * HAIR_TIP_LINE])]);
    }
    return out;
  };

  return [lines(PARTED_TIPS_BEHIND), lines(PARTED_TIPS_FRONT)];
}

/**
 * The darker hair behind: a region the mass is painted over in the second
 * tone, and the two lines that bound it where it shows.
 *
 * Each line is an outer fall's inner edge, from where the dark strip is two
 * strokes across down to the fall's tip, led in from one anchor up the lock's
 * edge, so it leaves that line rather than starting beside it: the reference's
 * one line that splits in two. The region runs from those lines up each lock's
 * edge to its top, out along the seam lifted into the front's fill, and is
 * closed far outside the mass, which clips it, so wherever its boundary is not
 * a drawn line it is under the front, the head or the body.
 */
export function partedUnderside(fall: number): readonly [Chain, readonly Chain[]] {
  const edge = parted(PARTED_EDGE, fall);
  const lines: Chain[] = [];
  const sides: [Chain, number][] = [];
  for (const [lock0, apex, under] of [
    [PARTED_LOCK_L, PARTED_APEX_L, PARTED_UNDER_L],
    [PARTED_LOCK_R, PARTED_APEX_R, PARTED_UNDER_R],
  ] as const) {
    const lock = parted(lock0, fall);
    const [uStart, uSegs] = parted(under, fall);
    const merge = anchor(lock, apex);
    lines.push([merge, [straight(merge, uStart), ...uSegs]]);
    sides.push([lock, apex]);
  }
  const [[lockL, apexL], [lockR, apexR]] = sides as [[Chain, number], [Chain, number]];
  const qL = anchor(edge, PARTED_SEAM_L + 1);
  const qR = anchor(edge, PARTED_SEAM_R + 1);
  const [tL, tR] = [lockL[0], lockR[0]];
  const far = pyMaxIter(edge[1].map(([, e]) => Math.abs(e[0]))) + 1.0;
  const top = pyMinIter(edge[1].map(([, e]) => e[1])) - 1.0;
  const floor = fall + 1.0;
  const lift = PARTED_SEAM_LIFT;

  // Down the left line reversed, up the left lock, out and over, down the
  // right lock and line, and round underneath.
  const [downLStart, downL] = reverse(...(lines[0] as Chain));
  const [, upLockL] = reverse(...subChain(lockL, 0, apexL));
  const path: Segment[] = [...downL, ...upLockL];
  for (const q of [
    [tL[0], tL[1] - lift],
    [qL[0] - far, qL[1] - lift],
    [-far, top],
    [far, top],
    [qR[0] + far, qR[1] - lift],
    [tR[0], tR[1] - lift],
    tR,
  ] as Point[]) {
    path.push(straight(at(path, -1)[1], q));
  }
  path.push(...subChain(lockR, 0, apexR)[1]);
  path.push(...(lines[1] as Chain)[1]);
  const end = at(path, -1)[1];
  for (const q of [[end[0], floor], [downLStart[0], floor], downLStart] as Point[]) {
    path.push(straight(at(path, -1)[1], q));
  }
  return [[downLStart, path], lines];
}

