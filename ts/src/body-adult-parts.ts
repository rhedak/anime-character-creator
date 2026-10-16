// The adult woman's bare-body parts: one fused outline from the neck to the soles with the arms hanging beside it, and
// the underwear that is always worn on it. They replace the chibi's `_torso`, `_legs_and_boots`, `_arms`,
// `_underwear_top` and friends for a body in `ADULT_BODY_TYPES` (render.ts picks the table), and are built from the
// knot tables in body-adult-data.ts (measured off ref/franzi/, in head heights) mapped onto the skeleton's anchors, so
// a different waist, hip or leg width in the profile moves the figure. Docs: docs/adult-body-plan.md.
//
// The arms are part of the one outline for now: a garment that needs the arm in front of it (a sleeve over the
// upper arm is drawn over the body anyway) will split them off at stage 6.

import { OUTLINE, outlineW, strokeW } from "./character.ts";
import { colorStr } from "./body-parts-legs.ts";
import { ADULT_REF } from "./body-adult.ts";
import { ARM_INNER, ARM_OUTER, LEG_INNER, LEG_OUTER, SHOULDER_OUTER, TORSO_SIDE } from "./body-adult-data.ts";
import type { CharacterParams } from "./params.ts";
import { fmt1, fmt2 } from "./pynum.ts";
import type { Skeleton } from "./skeleton.ts";

type Knots = readonly (readonly [number, number])[];

/** Depths (in H below the chin) the profile's anchors sit at in the reference, in the order `anchorYs` returns. */
const REF_DEPTHS = [0.0, 0.28, 1.3, 2.2, 4.7, 5.4];

const anchorYs = (sk: Skeleton): number[] => [
  sk.head_cy + sk.head_r,
  sk.shoulder_y,
  sk.waist_y,
  sk.hip_y,
  sk.ankle_y,
  sk.foot_y,
];

function piecewise(v: number, xs: readonly number[], ys: readonly number[]): number {
  const n = xs.length;
  if (v <= (xs[0] as number)) return (ys[0] as number) + (v - (xs[0] as number)) * (((ys[1] as number) - (ys[0] as number)) / ((xs[1] as number) - (xs[0] as number)));
  for (let i = 0; i < n - 1; i++) {
    const x0 = xs[i] as number;
    const x1 = xs[i + 1] as number;
    if (v <= x1) return (ys[i] as number) + ((v - x0) / (x1 - x0)) * ((ys[i + 1] as number) - (ys[i] as number));
  }
  return (ys[n - 1] as number) + (v - (xs[n - 1] as number)) * (((ys[n - 1] as number) - (ys[n - 2] as number)) / ((xs[n - 1] as number) - (xs[n - 2] as number)));
}

/** A knot table read at depth `d`, linear between knots. */
function at(tab: Knots, d: number): number {
  return piecewise(d, tab.map((k) => k[0]), tab.map((k) => k[1]));
}

interface Place {
  y: (d: number) => number;
  /** Half-width in pixels of a knot value `v` (H) at depth `d`, following the profile's widths. */
  w: (d: number, v: number) => number;
  cx: number;
}

function place(sk: Skeleton): Place {
  const ys = anchorYs(sk);
  const ratio = (now: number, ref: number): number => now / (ref * sk.head_r);
  const rs = ratio(sk.shoulder_half_w, ADULT_REF.shoulder_half_w);
  const rw = ratio(sk.waist_half_w, ADULT_REF.waist_half_w);
  const rh = ratio(sk.hip_half_w, ADULT_REF.hip_half_w);
  const rl = ratio(sk.leg_half_w, ADULT_REF.leg_half_w);
  const ds = [0.0, 0.28, 1.3, 2.2, 2.4, 3.3, 5.4];
  const rr = [rs, rs, rw, rh, rh, rl, rl];
  return {
    cx: sk.head_cx,
    y: (d) => piecewise(d, REF_DEPTHS, ys),
    w: (d, v) => v * 2 * sk.head_r * piecewise(d, ds, rr),
  };
}

type Pt = readonly [number, number];

/** A Catmull-Rom curve through `pts`, as cubic segments continuing from the first point (the pen is already there). */
function smooth(pts: readonly Pt[]): string {
  let s = "";
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)] as Pt;
    const p1 = pts[i] as Pt;
    const p2 = pts[i + 1] as Pt;
    const p3 = pts[Math.min(pts.length - 1, i + 2)] as Pt;
    const c1: Pt = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
    const c2: Pt = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
    s += `C ${fmt1(c1[0])} ${fmt1(c1[1])} ${fmt1(c2[0])} ${fmt1(c2[1])} ${fmt1(p2[0])} ${fmt1(p2[1])} `;
  }
  return s;
}

const line = (pt: Pt): string => `L ${fmt1(pt[0])} ${fmt1(pt[1])} `;

/** A quadratic from the pen to `end` through the control point `ctrl`. */
const quad = (ctrl: Pt, end: Pt): string => `Q ${fmt1(ctrl[0])} ${fmt1(ctrl[1])} ${fmt1(end[0])} ${fmt1(end[1])} `;

/** The body's one outline, neck to soles with the arms, as a closed path. */
export function adultBodyPath(sk: Skeleton): string {
  const { cx, y, w } = place(sk);
  // The knots are the ink's outer edge, stroke included, so the path sits half a stroke inside it: an outer edge moves
  // toward the centre line, an inner edge (the arm's inside, the legs' gap) away from it.
  const hs = outlineW(strokeW(sk)) / 2;
  const inner = (tab: Knots): boolean => tab === ARM_INNER || tab === LEG_INNER;
  const side = (sign: number, tab: Knots): Pt[] =>
    tab.map(([d, v]) => [cx + sign * (w(d, v) + (inner(tab) ? hs : -hs)), y(d)]);
  const rev = <T,>(a: readonly T[]): T[] => [...a].reverse();
  const out = (sign: number): Pt[] => [
    [cx + sign * sk.neck_half_w, y(0.12)],
    [cx + sign * (w(0.2, 0.2) - hs), y(0.2)],
    [cx + sign * (w(0.25, 0.4) - hs), y(0.25)],
    ...side(sign, SHOULDER_OUTER),
    ...side(sign, ARM_OUTER),
  ];
  const handTip = (sign: number): Pt => [cx + sign * w(2.6, 0.69), y(2.7) - hs];
  const apex = (sign: number): Pt => [cx + sign * (w(0.88, 0.41) - hs), y(0.88)];
  const legLine = (sign: number): Pt[] => [...side(sign, TORSO_SIDE), ...side(sign, LEG_OUTER)];
  const lastOuter = (sign: number): Pt => [cx + sign * (w(5.3, 0.349) - hs), y(5.4) - hs];
  const lastInner = (sign: number): Pt => [cx + sign * (w(5.3, 0.065) + hs), y(5.4) - hs];
  const L = -1;
  const R = 1;
  const a = out(L);
  const start = a[0] as Pt;
  const hand = (sign: number): string => {
    const tip = handTip(sign);
    const end = side(sign, ARM_INNER).slice(-1)[0] as Pt;
    return `Q ${fmt1(tip[0])} ${fmt1(tip[1])} ${fmt1(end[0])} ${fmt1(end[1])} `;
  };
  // Left side down, round the left hand, up the arm's inside, over the armpit, down the torso and leg to the sole.
  let d = `M ${fmt1(start[0])} ${fmt1(start[1])} `;
  d += smooth(a);
  d += hand(L);
  d += smooth(rev(side(L, ARM_INNER)));
  const leg = legLine(L);
  d += quad(apex(L), leg[0] as Pt);
  d += smooth(leg);
  d += line(lastOuter(L));
  d += line(lastInner(L));
  // The inside of the left leg up to the crotch, across, and the same down the right leg.
  d += smooth(rev(side(L, LEG_INNER)));
  d += line([cx, y(2.25)]);
  d += line(side(R, LEG_INNER)[0] as Pt);
  d += smooth(side(R, LEG_INNER));
  d += line(lastInner(R));
  d += line(lastOuter(R));
  d += smooth(rev(legLine(R)));
  d += quad(apex(R), side(R, ARM_INNER)[0] as Pt);
  d += smooth(side(R, ARM_INNER));
  {
    const tip = handTip(R);
    const end = side(R, ARM_OUTER).slice(-1)[0] as Pt;
    d += `Q ${fmt1(tip[0])} ${fmt1(tip[1])} ${fmt1(end[0])} ${fmt1(end[1])} `;
  }
  d += smooth(rev(out(R)));
  return d + "Z";
}

function inkAttrs(sk: Skeleton, fill: string): string {
  return `fill="${fill}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)))}" stroke-linejoin="round"`;
}

/** The figure's skin: the whole body outline in one piece. */
export function adultTorso(sk: Skeleton, p: CharacterParams): string {
  return `<path d="${adultBodyPath(sk)}" ${inkAttrs(sk, colorStr(p.skin_tone))} />`;
}

/** Underwear below the waist, always worn: briefs from the hip line to the top of the thigh. */
export function adultBriefs(sk: Skeleton, p: CharacterParams): string {
  const { cx, y, w } = place(sk);
  const hs = outlineW(strokeW(sk)) / 2;
  const top = 1.85;
  const cut = 2.0;
  const crotch = 2.3;
  const out = (sign: number, d: number): Pt => [cx + sign * (w(d, at(TORSO_SIDE, d)) - hs), y(d)];
  const inn = (sign: number): Pt => [cx + sign * (w(crotch, at(LEG_INNER, crotch)) + hs), y(crotch)];
  const ds: number[] = [];
  for (let t = top; t <= cut + 1e-9; t += 0.05) ds.push(t);
  const left = ds.map((t) => out(-1, t));
  const right = ds.map((t) => out(1, t));
  const first = left[0] as Pt;
  const lastL = left[left.length - 1] as Pt;
  const lastR = right[right.length - 1] as Pt;
  // The leg opening leaves the side at the cut line and curves down to the crotch, high at the hip, low at the centre.
  const ctrlL: Pt = [lastL[0] + (inn(-1)[0] - lastL[0]) * 0.55, lastL[1] + (inn(-1)[1] - lastL[1]) * 0.2];
  const ctrlR: Pt = [2 * cx - ctrlL[0], ctrlL[1]];
  let d = `M ${fmt1(first[0])} ${fmt1(first[1])} `;
  d += smooth(left);
  d += quad(ctrlL, inn(-1));
  d += line([cx, y(crotch - 0.02)]);
  d += line(inn(1));
  d += quad(ctrlR, lastR);
  d += smooth([...right].reverse());
  return `<path d="${d}Z" ${inkAttrs(sk, colorStr(p.outfit.underwear_color))} />`;
}

/** Underwear above the waist, always worn: a plain band across the chest. Its shape over a bust is stage 4. */
export function adultBand(sk: Skeleton, p: CharacterParams): string {
  const { cx, y, w } = place(sk);
  const top = 0.82;
  const bottom = 1.14;
  // Full width above the armpit (arm and torso are one there), then following the torso's side in, so the corners
  // stay clear of the arm gap's cap.
  const half = (d: number): number => (d <= 0.95 ? 0.43 : 0.43 + (at(TORSO_SIDE, bottom) - 0.02 - 0.43) * ((d - 0.95) / (bottom - 0.95)));
  const pts = (sign: number): Pt[] => [top, 0.95, 1.05, bottom].map((d) => [cx + sign * w(d, half(d)), y(d)] as Pt);
  const l = pts(-1);
  const r = pts(1);
  const dip = (y(bottom) - y(top)) * 0.12;
  const d =
    `M ${fmt1((l[0] as Pt)[0])} ${fmt1((l[0] as Pt)[1])} ` +
    l.slice(1).map(line).join("") +
    line([cx + 0, y(bottom)]) +
    r.slice().reverse().map(line).join("") +
    `Q ${fmt1(cx)} ${fmt1(y(top) + dip)} ${fmt1((l[0] as Pt)[0])} ${fmt1((l[0] as Pt)[1])} `;
  return `<path d="${d}Z" ${inkAttrs(sk, colorStr(p.outfit.underwear_color))} />`;
}

const none = (): string => "";

/** The parts an adult body replaces. Everything else (head, hair, face, garments) is the shared code. */
export const ADULT_PARTS = {
  _torso: adultTorso,
  _legs_and_boots: adultBriefs,
  _arms: none,
  _underwear_top: adultBand,
  _navel: none,
  _chest_lines: none,
  _bust_lines: none,
  _bust_over_arms: none,
};
