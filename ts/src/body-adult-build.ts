// A build of the adult woman's body: how a character's body differs from the traced one (Franzi's, body-adult-data.ts), as a warp of the knot space that `place`
// (body-adult-parts.ts) applies before it maps a knot onto the skeleton. Everything drawn on the body goes through `place`, so the outline, the underwear, the garments, the hands
// and the posed arms follow one warp. Docs: docs/risa-polish-plan.md, stage 2.
//
// A knot is [v, d]: a half-width v and a depth d below the chin, both in head heights (H). The warp moves d (the torso closes up between two depths, and everything below
// moves up rigidly, so the legs keep their lengths; the arm closes up by its own amount, so a shorter torso need not take the hands up with it) and, row by row, v: a
// piecewise-linear map through the traced body's own edges at that depth, the centre line, the torso's side (below the crotch, each leg's inner and outer edges), the arm's inner
// edge and its outer edge, each moved by a factor of the build. Points between edges follow linearly, so a garment's ease or a traced chain keeps its place relative to the edges
// it lies between, and points beyond the arm move with it. A point's depth moves by the torso's amount up to the torso's side and by the arm's from the arm's inner edge out,
// blended across the gap between them, so `place`'s `y` takes the point's half-width as well; a point placed without one moves with the torso.

import { ARM_INNER, ARM_OUTER, LEG_INNER, LEG_OUTER, SHOULDER_OUTER, TORSO_SIDE } from "./body-adult-data.ts";

type Knots = readonly (readonly [number, number])[];

export interface AdultBuild {
  /** How much higher, in H, everything at and below `shorten_to` sits: the rows from `shorten_from` to `shorten_to` close up by that much. Traced depths. */
  readonly shorten: number;
  readonly shorten_from: number;
  readonly shorten_to: number;
  /** The arm's own shortening over the same rows, H: how much higher the hand sits. */
  readonly arm_shorten: number;
  /** [d, factor] by traced depth: the torso's half-width (about the centre line), and below the crotch each leg's width (about its inner edge, so the gap between the legs stays). */
  readonly body: Knots;
  /** [d, factor]: the gap between the arm and the torso. */
  readonly gap: Knots;
  /** [d, factor]: the gap between the legs (each leg's inner edge, about the centre line; the leg's width is `body`'s). */
  readonly leg_gap: Knots;
  /** [d, factor]: the arm's width (its outer edge less its inner one), and the hand's. */
  readonly arm: Knots;
}

/**
 * The builds a character can pick (`body_build`), by name. None is the traced body. Fitted by harness/risa_adult/gate.py against the bikini image of ref/risa-adult/, which is
 * canon for her proportions (docs/risa-polish-plan.md, decision 1); below mid-thigh, where it shows nothing, the legs taper back into the traced knees (decision 3).
 */
export const ADULT_BUILDS: Readonly<Record<string, AdultBuild>> = {
  slender: {
    shorten: 0.08,
    shorten_from: 0.95,
    shorten_to: 1.26,
    arm_shorten: 0.045,
    body: [[0.9, 1.0], [1.0, 0.85], [1.26, 0.86], [1.5, 0.9], [2.2, 0.9], [2.3, 0.89], [2.7, 0.84], [3.0, 0.8], [3.5, 1.0]],
    gap: [[0.0, 1.0]],
    leg_gap: [[2.3, 1.0], [2.5, 1.3], [2.7, 1.4], [2.9, 1.5], [3.0, 1.6], [3.5, 1.0]],
    arm: [[0.3, 0.75], [0.9, 0.78], [1.0, 0.83], [1.3, 0.9], [1.5, 0.95], [1.7, 0.9], [2.0, 0.86]],
  },
};

/** A knot table read at `d`: linear between knots, held beyond the first and the last. */
function held(tab: Knots, d: number): number {
  const first = tab[0] as readonly [number, number];
  if (d <= first[0]) return first[1];
  for (let i = 1; i < tab.length; i++) {
    const [d1, v1] = tab[i] as readonly [number, number];
    if (d <= d1) {
      const [d0, v0] = tab[i - 1] as readonly [number, number];
      return v0 + ((d - d0) / (d1 - d0)) * (v1 - v0);
    }
  }
  return (tab[tab.length - 1] as readonly [number, number])[1];
}

/** Where the torso's side is for the warp: above the armpit, a line just inside the arm's inner edge (the ribs under it); from 1.1 the traced side; below the hips the leg's outer edge. */
const SIDE: Knots = [[0.9, 0.435], ...TORSO_SIDE, ...LEG_OUTER.filter(([d]) => d > 2.25)];
/** The arm's outer edge: the shoulder's, then the arm's. */
const OUTER: Knots = [...SHOULDER_OUTER, ...ARM_OUTER];
/** Where the legs part: the pivot of a leg's width moves from the centre line to its inner edge over these depths. */
const LEGS_FROM = 2.15;
const LEGS_TO = 2.3;

/** The traced body's torso side, the arm's inner edge and its outer edge at the traced depth `d`, in increasing order. */
function edges(d: number): [number, number, number] {
  const side = held(SIDE, d);
  const inner = Math.max(held(ARM_INNER, d), side + 1e-6);
  return [side, inner, Math.max(held(OUTER, d), inner + 1e-6)];
}

/**
 * The traced depth `d` of a point at half-width `v`, moved by the build's shortening: the torso's up to the torso's side, the arm's from the arm's inner edge out, blended across
 * the gap. Without `v`, the torso's.
 */
export function warpDepth(b: AdultBuild, d: number, v?: number): number {
  if (d <= b.shorten_from) return d;
  let by = b.shorten;
  if (v !== undefined) {
    const [side, inner] = edges(d);
    const t = Math.max(0, Math.min(1, (Math.abs(v) - side) / (inner - side)));
    by = b.shorten + t * (b.arm_shorten - b.shorten);
  }
  if (d >= b.shorten_to) return d - by;
  return d - (by * (d - b.shorten_from)) / (b.shorten_to - b.shorten_from);
}

/** The traced half-width `v` at the traced depth `d`, moved by the build (the sign is kept: a negative `v` is mirrored). */
export function warpHalf(b: AdultBuild, d: number, v: number): number {
  const a = Math.abs(v);
  const [side, inner, outer] = edges(d);
  const t = Math.max(0, Math.min(1, (d - LEGS_FROM) / (LEGS_TO - LEGS_FROM)));
  const pivot = t * held(LEG_INNER, d);
  const pivot2 = pivot * held(b.leg_gap, d);
  const side2 = pivot2 + held(b.body, d) * (side - pivot);
  const inner2 = side2 + held(b.gap, d) * (inner - side);
  const outer2 = inner2 + held(b.arm, d) * (outer - inner);
  const xs = pivot > 0 ? [0, pivot, side, inner, outer] : [0, side, inner, outer];
  const ys = pivot > 0 ? [0, pivot2, side2, inner2, outer2] : [0, side2, inner2, outer2];
  let r = a - outer + outer2;
  for (let i = 1; i < xs.length; i++) {
    if (a <= (xs[i] as number)) {
      const x0 = xs[i - 1] as number;
      const y0 = ys[i - 1] as number;
      r = y0 + ((a - x0) / ((xs[i] as number) - x0)) * ((ys[i] as number) - y0);
      break;
    }
  }
  return v < 0 ? -r : r;
}
