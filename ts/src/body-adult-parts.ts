// The adult woman's bare-body parts: one fused outline from the neck to the soles with the arms hanging beside it, and
// the underwear that is always worn on it. They replace the chibi's `_torso`, `_legs_and_boots`, `_arms`,
// `_underwear_top` and friends for a body in `ADULT_BODY_TYPES` (render.ts picks the table), and are built from the
// knot tables in body-adult-data.ts (measured off ref/franzi/, in head heights) mapped onto the skeleton's anchors, so
// a different waist, hip or leg width in the profile moves the figure. Docs: docs/adult-body-plan.md.
//
// The arms are part of the one outline for now: a garment that needs the arm in front of it (a sleeve over the
// upper arm is drawn over the body anyway) will split them off at stage 6.

import { OUTLINE, curve, outlineW, strokeW } from "./character.ts";
import { colorStr } from "./body-parts-legs.ts";
import { ADULT_REF } from "./body-adult.ts";
import { ARM_INNER, ARM_OUTER, LEG_INNER, LEG_OUTER, SHOULDER_OUTER, TORSO_SIDE } from "./body-adult-data.ts";
import { ADULT_BREAST } from "./body-adult-bust-data.ts";
import { ADULT_TOP } from "./body-adult-top-data.ts";
import { ADULT_HAIR_STRANDS } from "./body-adult-head-data.ts";
import { FOOT_D_CUT, FOOT_OUTLINE } from "./body-adult-foot-data.ts";
import { HAND_D_CUT, HAND_OUTLINE, HAND_STROKE_K } from "./body-adult-hand-data.ts";
import { HAND_CAVITY, HAND_FINGERS, HAND_GAPS, HAND_LINES, HAND_LINE_WIDTHS, HAND_NAILS, HAND_SHADE, HAND_THUMB, HAND_THUMB_FROM } from "./body-adult-hand-lines-data.ts";
import { FOOT_DIVIDERS, FOOT_DIVIDER_WIDTHS, FOOT_NAILS } from "./body-adult-foot-lines-data.ts";
import { ADULT_EAR_CONCHA_L, ADULT_EAR_CONCHA_R, ADULT_HAIR_SILHOUETTE, ADULT_SKIN_EAR_L, ADULT_SKIN_EAR_R, ADULT_SKIN_FACE, ADULT_SKIN_STRIPS } from "./body-adult-outline-data.ts";
import { ADULT_EAR_FOLDS_L, ADULT_EAR_FOLDS_R, ADULT_EAR_FOLD_WIDTHS_L, ADULT_EAR_FOLD_WIDTHS_R } from "./body-adult-ear-data.ts";
import type { CharacterParams } from "./params.ts";
import { fmt1, fmt2 } from "./pynum.ts";
import { shade, tint } from "./colorutil.ts";
import { adultEyes } from "./body-adult-eyes.ts";
import { ADULT_BROW_L, ADULT_BROW_R } from "./body-adult-brow-data.ts";
import { MOUTH_REALISTIC_DROP, MOUTH_Y, noseDot } from "./face.ts";
import type { PartTable } from "./parts.ts";
import type { Chain } from "./tables.ts";
import { faceBuild, replace as replaceSk, type Skeleton } from "./skeleton.ts";

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

/** The tip of the gap between arm and torso, [x, d] in head heights: where the cup's lower outer corner meets the arm (ref 04). */
const GAP_TIP: Pt = [0.4, 0.955];

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
  // The legs stop at `FOOT_D_CUT`, so the leg tables are cut there; a cut table is a new array, so it is recognised by being one of these.
  const legInnerAbove = LEG_INNER.filter(([dd]) => dd <= FOOT_D_CUT + 1e-6);
  const legOuterAbove = LEG_OUTER.filter(([dd]) => dd <= FOOT_D_CUT + 1e-6);
  // The arms stop at `HAND_D_CUT` in the same way, where the traced hand (body-adult-hand-data.ts) takes over.
  const armInnerAbove = ARM_INNER.filter(([dd]) => dd <= HAND_D_CUT + 1e-6);
  const armOuterAbove = ARM_OUTER.filter(([dd]) => dd <= HAND_D_CUT + 1e-6);
  const inner = (tab: Knots): boolean => tab === ARM_INNER || tab === LEG_INNER || tab === legInnerAbove || tab === armInnerAbove;
  const side = (sign: number, tab: Knots): Pt[] =>
    tab.map(([d, v]) => [cx + sign * (w(d, v) + (inner(tab) ? hs : -hs)), y(d)]);
  const rev = <T,>(a: readonly T[]): T[] => [...a].reverse();
  const out = (sign: number): Pt[] => [
    [cx + sign * sk.neck_half_w, y(0.12)],
    [cx + sign * (w(0.2, 0.2) - hs), y(0.2)],
    [cx + sign * (w(0.25, 0.4) - hs), y(0.25)],
    ...side(sign, SHOULDER_OUTER),
    ...side(sign, armOuterAbove),
  ];
  const tip = (sign: number): Pt => [cx + sign * w(GAP_TIP[1], GAP_TIP[0]), y(GAP_TIP[1])];
  // The cap on the gap: two short quadratics through the tip, a point, so the gap opens from where the arm line ends.
  const capArm = (sign: number): Pt => [cx + sign * (w(1.0, 0.425) + hs * 0.4), y(1.0)];
  const capTor = (sign: number): Pt => [cx + sign * (w(1.0, 0.395) - hs * 0.4), y(1.0)];
  // The legs end at `FOOT_D_CUT`; from there the traced foot (body-adult-foot-data.ts) takes over, round the toes and back to the inner edge.
  const legLine = (sign: number): Pt[] => [...side(sign, TORSO_SIDE), ...side(sign, legOuterAbove)];
  const L = -1;
  const R = 1;
  // A traced chain (the foot, the hand), in the knots' own coordinates [v, d] (head heights): the left side walks outer edge to inner edge, the
  // right one the other way.
  const chainPt = (sign: number, q: Pt): Pt => [cx + sign * w(q[1], q[0]), y(q[1])];
  const walk = (sign: number, [start, segs]: Chain): string => {
    if (sign < 0) return segs.map(([c, e]) => quad(chainPt(sign, c), chainPt(sign, e))).join("");
    const ends: Pt[] = [start, ...segs.map(([, e]) => e)];
    return segs.map(([c], i) => quad(chainPt(sign, c), chainPt(sign, ends[i] as Pt))).reverse().join("");
  };
  const foot = (sign: number): string => walk(sign, FOOT_OUTLINE);
  const hand = (sign: number): string => walk(sign, HAND_OUTLINE);
  const a = out(L);
  const start = a[0] as Pt;
  // Left side down, round the left hand, up the arm's inside, over the armpit, down the torso and leg to the sole.
  let d = `M ${fmt1(start[0])} ${fmt1(start[1])} `;
  d += smooth(a);
  d += hand(L);
  d += smooth(rev(side(L, armInnerAbove)));
  const leg = legLine(L);
  d += quad(capArm(L), tip(L)) + quad(capTor(L), leg[0] as Pt);
  d += smooth(leg);
  d += foot(L);
  // The inside of the left leg up to the crotch, across, and the same down the right leg.
  d += smooth(rev(side(L, legInnerAbove)));
  d += line([cx, y(2.25)]);
  d += line(side(R, LEG_INNER)[0] as Pt);
  d += smooth(side(R, legInnerAbove));
  d += foot(R);
  d += smooth(rev(legLine(R)));
  d += quad(capTor(R), tip(R)) + quad(capArm(R), side(R, ARM_INNER)[0] as Pt);
  d += smooth(side(R, armInnerAbove));
  d += hand(R);
  d += smooth(rev(out(R)));
  return d + "Z";
}

function inkAttrs(sk: Skeleton, fill: string): string {
  return `fill="${fill}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)))}" stroke-linejoin="round"`;
}

/** The figure's skin: the whole body outline in one piece. */
export function adultTorso(sk: Skeleton, p: CharacterParams): string {
  // The bikini top is drawn here, not in the chest layers, so the neck (the next layer) covers where its straps go behind it.
  // The bust's tapered line goes on the skin and under the top, so only what the top leaves uncovered shows: the inner edges
  // in the V and the lighter upper edge above the cups, as in the reference.
  // The top is clipped to the body's outline, so its straps end at the shoulder line where they pass behind the neck.
  // The bust's tapered ring is for what the top leaves uncovered (the V and the arcs above the cups), so it is clipped to the middle of the chest: out at
  // the sides it lay just beyond the top's own outer edge and drew a second line beside it (the owner's double outline).
  const { cx, w } = place(sk);
  const mid = `<clipPath id="adult-bust-mid"><rect x="${fmt1(cx - w(0.6, 0.33))}" y="0" width="${fmt1(2 * w(0.6, 0.33))}" height="${fmt1(sk.canvas_h)}" /></clipPath>`;
  return adultSkin(sk, p) + mid + `<g clip-path="url(#adult-bust-mid)">${adultBustLine(sk, DEFAULT_TAPER, shade(p.skin_tone, 0.78, 1.6), 0.8)}</g>` + `<clipPath id="adult-body-clip"><path d="${adultBodyPath(sk)}" /></clipPath><g clip-path="url(#adult-body-clip)">${adultBand(sk, p)}</g>`;
}

/**
 * The body outline alone, in skin colour, with the armpit creases: where the arm meets the chest the reference draws a line,
 * from the top of the armpit (about half a head height below the chin, level with the top of the bust) down the arm's inner
 * edge to the tip of the gap between arm and torso, which opens only at a head height. Without it the armpits seemed to sit
 * far lower than the bust (the silhouette's gap starts there, the armpit does not). Read off ref 04 (the arm's inner contour,
 * 0.48 to 1.0 H, x about 0.45 H from the centre line).
 */
export function adultSkin(sk: Skeleton, p: CharacterParams): string {
  const { cx, y, w } = place(sk);
  // The same weight as the arm's own outline: it is that outline carried up to the armpit, not a lighter interior line.
  const sw = fmt2(outlineW(strokeW(sk)));
  const crease = [1, -1]
    .map((sign) => {
      const P = (v: number, d: number): Pt => [cx + sign * w(d, v), y(d)];
      // The arm's inner edge from the top of the armpit down: along the bust's outer side (widest about 0.455 H out at 0.8 H),
      // then in to the gap's tip (GAP_TIP). Read off ref 04 (the contour at 5x, row by row).
      // The line stops where it meets the bikini top's edge, which carries on from there: below that point the two ran 0.015 H apart (the top's
      // outer edge is at 0.432 H at 0.7 H down, this line at 0.447), each at full weight, and drew as one heavy band with a thin gap (the owner's
      // double outline). In the reference the armpit line is hidden behind the cup's edge there. The first rows follow it as before; the last point
      // is on the top's edge (0.412 H at 0.65 H down), so the two join in a Y.
      const pts = [P(0.455, 0.48), P(0.454, 0.6), P(0.4125, 0.652)];
      return `<path d="M ${fmt1((pts[0] as Pt)[0])} ${fmt1((pts[0] as Pt)[1])} ${smooth(pts)}" fill="none" stroke="${OUTLINE}" stroke-width="${sw}" stroke-linecap="round" stroke-linejoin="round" />`;
    })
    .join("");
  return `<path d="${adultBodyPath(sk)}" fill="${colorStr(p.skin_tone)}" />` + adultBodyStroke(sk) + crease;
}

/**
 * The body outline's stroke. The hands are stroked thinner than the rest (`HAND_STROKE_K` of the weight): a finger on the close-up is about as wide
 * as a full-weight stroke, which hid the thumb's edge and the finger tips. The stroke is the same path drawn in clipped pieces: full weight
 * everywhere but the hand columns below the wrist, a taper over twenty bands to the hand weight, from `HAND_D_CUT` down. The hand's own chain is inset by the hand weight's half stroke (harness/franzi_hands/outline.py).
 */
export function adultBodyStroke(sk: Skeleton, only: "all" | "hands" = "all"): string {
  const { cx, y, w } = place(sk);
  const path = adultBodyPath(sk);
  const full = outlineW(strokeW(sk));
  const stroke = (width: number, clip: string): string => `<path d="${path}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(width)}" stroke-linejoin="round" clip-path="url(#${clip})" />`;
  const top = y(HAND_D_CUT);
  const bottom = y(2.9);
  const big = sk.canvas_w;
  const bigH = sk.canvas_h;
  // The hand zone: from the arm's outer side in to an inner edge that follows the thigh (the lowest fingertip reaches 0.60 H from the centre line, past
  // the straight 0.635 H edge this had at first, which cut the tip off and drew it at full weight with a vertical edge: the owner's barb), clear of the
  // thigh's own stroke (its outer edge is 0.611 H at 2.3, 0.583 at 2.5, 0.561 at 2.6; the stroke reaches 0.008 H beyond that).
  const V_IN: readonly (readonly [number, number])[] = [[HAND_D_CUT, 0.635], [2.3, 0.625], [2.4, 0.612], [2.5, 0.598], [2.6, 0.595], [2.9, 0.595]];
  const vIn = (d: number): number => {
    for (let i = 0; i < V_IN.length - 1; i++) {
      const [d0, v0] = V_IN[i] as readonly [number, number];
      const [d1, v1] = V_IN[i + 1] as readonly [number, number];
      if (d <= d1) return v0 + ((v1 - v0) * (d - d0)) / (d1 - d0);
    }
    return (V_IN[V_IN.length - 1] as readonly [number, number])[1];
  };
  const dAt = (d0: number, d1: number): number[] => [d0, ...V_IN.map(([d]) => d).filter((d) => d > d0 && d < d1), d1];
  const poly = (pts: readonly Pt[]): string => `<polygon points="${pts.map((q) => `${fmt1(q[0])},${fmt1(q[1])}`).join(" ")}" />`;
  const px = (sign: number, d: number, v: number): Pt => [cx + sign * w(d, v), y(d)];
  const rect = (x0: number, y0: number, x1: number, y1: number): string => `<rect x="${fmt1(x0)}" y="${fmt1(y0)}" width="${fmt1(x1 - x0)}" height="${fmt1(y1 - y0)}" />`;
  const OUT = 1.0;
  // one hand's piece between depths d0 and d1: outer side straight, inner side along vIn
  const piece = (sign: number, d0: number, d1: number): string => {
    const ds = dAt(d0, d1);
    return poly([...ds.map((d) => px(sign, d, OUT)), ...[...ds].reverse().map((d) => px(sign, d, vIn(d)))]);
  };
  const xl = Math.min(cx - w(2.3, OUT), cx + w(2.3, OUT));
  const xr = Math.max(cx - w(2.3, OUT), cx + w(2.3, OUT));
  // the rest: everything but the hand zones. Above the wrist and below the hands, the whole width; between, the outside of each arm and the middle.
  const dsAll = dAt(HAND_D_CUT, 2.9);
  const middle = poly([...dsAll.map((d) => px(-1, d, vIn(d))), ...[...dsAll].reverse().map((d) => px(1, d, vIn(d)))]);
  const rest = `<clipPath id="adult-stroke-rest">${rect(0, 0, big, top)}${rect(0, top, xl, bottom)}${rect(xr, top, big, bottom)}${middle}${rect(0, bottom, big, bigH)}</clipPath>`;
  // The stroke tapers from the full weight to the hand weight over N bands from the wrist down (a single step showed as a jump at the wrist's outer
  // edge), each band reaching a little up into the one above, which is thicker, so no hairline of the page shows where they meet.
  const taperEnd = HAND_D_CUT + 0.32;
  const N = 20;
  const lap = 0.008;
  const band = (id: string, d0: number, d1: number): string => `<clipPath id="${id}">${piece(-1, d0, d1)}${piece(1, d0, d1)}</clipPath>`;
  let hands = "";
  let strokes = "";
  for (let i = 0; i < N; i++) {
    const d0 = HAND_D_CUT + ((taperEnd - HAND_D_CUT) * i) / N;
    const d1 = HAND_D_CUT + ((taperEnd - HAND_D_CUT) * (i + 1)) / N;
    const k = 1 - (1 - HAND_STROKE_K) * ((i + 1) / N);
    hands += band(`adult-stroke-t${i}`, i === 0 ? d0 : d0 - lap, d1);
    strokes += stroke(full * k, `adult-stroke-t${i}`);
  }
  hands += band("adult-stroke-hand", taperEnd - lap, 2.9);
  strokes += stroke(full * HAND_STROKE_K, "adult-stroke-hand");
  return (only === "all" ? rest + stroke(full, "adult-stroke-rest") : "") + hands + strokes;
}

/** One point on a breast's edge: canvas position and where it lies in head heights (|x| from the centre line, d below the chin). */
export interface EdgePoint {
  readonly pos: Pt;
  readonly x: number;
  readonly d: number;
}

/** Each breast's edge sampled as a polyline (viewer's left, then right), `per` points per quadratic. For the harness's variants. */
export function adultBreastPoints(sk: Skeleton, per = 10): EdgePoint[][] {
  const { cx, y, w } = place(sk);
  const [start, segs] = ADULT_BREAST;
  return [1, -1].map((sign) => {
    const out: EdgePoint[] = [];
    let p0: Pt = start;
    const add = (q: Pt): void => {
      out.push({ pos: [cx + sign * w(q[1], -q[0]), y(q[1])], x: -q[0], d: q[1] });
    };
    add(p0);
    for (const [c, e] of segs) {
      for (let i = 1; i <= per; i++) {
        const t = i / per;
        add([(1 - t) * (1 - t) * p0[0] + 2 * (1 - t) * t * c[0] + t * t * e[0], (1 - t) * (1 - t) * p0[1] + 2 * (1 - t) * t * c[1] + t * t * e[1]]);
      }
      p0 = e;
    }
    return out;
  });
}

/** How the tapered bust line's weight falls from the underside to the top: `from` is the depth where it has reached nothing much, `to` where it is full. */
export interface Taper {
  readonly from: number;
  readonly to: number;
  readonly power: number;
  /** The weight at the top as a share of the full weight. A fraction of a pixel breaks up when rasterised, so never near zero. */
  readonly floor?: number;
}

export const DEFAULT_TAPER: Taper = { from: 0.5, to: 0.95, power: 1.0, floor: 0.5 };

/**
 * Each breast's edge as ONE filled shape of varying width: full weight on the underside and the lower inner edge, easing
 * down along both sides to a hairline at the top. A hard-edged flat shape, not a colour gradient, in the way the hair's tapered
 * tip lines are. The width follows depth alone (smoothstep from `taper.from` to `taper.to`, raised to `taper.power`), so
 * what the bikini top covers hides the heavy part and the inner edges, seen in the V, thin as they rise. The ends are the
 * same hairline, so the ring closes without a visible join.
 */
export function adultBustLine(sk: Skeleton, taper: Taper = DEFAULT_TAPER, color: string = OUTLINE, weight = 0.9): string {
  const full = outlineW(strokeW(sk), weight);
  const rings: string[] = [];
  for (const side of adultBreastPoints(sk, 12)) {
    const n = side.length - 1; // the chain closes on its first point
    const pts = side.slice(0, n);
    const width = pts.map((q) => {
      const t = Math.min(1, Math.max(0, (q.d - taper.from) / (taper.to - taper.from)));
      const smooth01 = t * t * (3 - 2 * t);
      const floor = taper.floor ?? 0.5;
      return full * (floor + (1 - floor) * Math.pow(smooth01, taper.power));
    });
    const outer: Pt[] = [];
    const inner: Pt[] = [];
    for (let i = 0; i < n; i++) {
      const a = (pts[(i + n - 1) % n] as EdgePoint).pos;
      const b = (pts[(i + 1) % n] as EdgePoint).pos;
      const tx = b[0] - a[0];
      const ty = b[1] - a[1];
      const len = Math.hypot(tx, ty) || 1;
      const nx = -ty / len;
      const ny = tx / len;
      const q = (pts[i] as EdgePoint).pos;
      const h = (width[i] as number) / 2;
      outer.push([q[0] + nx * h, q[1] + ny * h]);
      inner.push([q[0] - nx * h, q[1] - ny * h]);
    }
    const poly = (a: readonly Pt[]): string => `M ${fmt1((a[0] as Pt)[0])} ${fmt1((a[0] as Pt)[1])} ` + a.slice(1).map(line).join("") + "Z";
    rings.push(`<path d="${poly(outer)} ${poly(inner)}" fill="${color}" fill-rule="evenodd" />`);
  }
  return rings.join("");
}

/**
 * The two breasts' edges as outlines, traced from ref 04 and agreed with the owner (body-adult-bust-data.ts). For the
 * harness's bare chest view only (harness/franzi/bare_chest.ts): nothing in the figure's own render draws them, and the
 * bikini top covers where they lie. An outline and nothing inside it: no nipples, no other detail, ever.
 */
export function adultBreastOutlines(sk: Skeleton): string {
  const { cx, y, w } = place(sk);
  const [start, segs] = ADULT_BREAST;
  const sw = fmt2(outlineW(strokeW(sk), 0.7));
  return [1, -1]
    .map((sign) => {
      const map = (q: Pt): Pt => [cx + sign * w(q[1], -q[0]), y(q[1])];
      const s0 = map(start);
      const d = `M ${fmt1(s0[0])} ${fmt1(s0[1])} ` + segs.map(([c, e]) => quad(map(c), map(e))).join("") + "Z";
      return `<path d="${d}" fill="none" stroke="${OUTLINE}" stroke-width="${sw}" stroke-linejoin="round" />`;
    })
    .join("");
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
  d += quad([cx, y(crotch + 0.05)], inn(1));
  d += quad(ctrlR, lastR);
  d += smooth([...right].reverse());
  // The waistband dips a little at the centre rather than running dead straight.
  d += quad([cx, y(top + 0.07)], first);
  return `<path d="${d}Z" ${inkAttrs(sk, colorStr(p.outfit.underwear_color))} />`;
}

/**
 * Underwear above the waist, always worn: a halter bikini top, traced from the bikini-top layer of ref 04
 * (body-adult-top-data.ts), the two cups and the straps up to the sides of the neck. The bust is read from the cloth's
 * outline alone: a flat garment, with nothing of the body drawn on it and no line on the cups.
 */
export function adultBand(sk: Skeleton, p: CharacterParams): string {
  const d = adultBandPath(sk);
  // The breasts' shapes over the cloth, as the reference's top follows them: the same outlines as the bare render (ADULT_BREAST), in a darker tone of the
  // cloth at a light weight, clipped to the top so none of it lands on skin. Flat colour, a second tone on a thin line (the ears' folds do the same).
  const soft = shade(colorStr(p.outfit.underwear_color), 0.8, 1.0);
  return (
    `<path d="${d}" fill="${colorStr(p.outfit.underwear_color)}" />` +
    `<clipPath id="adult-top-cloth"><path d="${d}" /></clipPath><g clip-path="url(#adult-top-cloth)">${adultBustLine(sk, DEFAULT_TAPER, soft, 0.7)}</g>` +
    // the outline over the soft line: where the top's edge follows the breast's the two share a centreline, and the outline covers the soft one
    `<path d="${d}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)))}" stroke-linejoin="round" />`
  );
}

/** The bikini top's outline path (body-adult-top-data.ts). */
function adultBandPath(sk: Skeleton): string {
  const { cx, y, w } = place(sk);
  const [start, segs] = ADULT_TOP;
  const map = (q: Pt): Pt => [cx + w(q[1], q[0]), y(q[1])];
  const s0 = map(start);
  return `M ${fmt1(s0[0])} ${fmt1(s0[1])} ` + segs.map(([c, e]) => quad(map(c), map(e))).join("") + "Z";
}

/**
 * How far the head hangs below the skeleton's chin line, in head radii. The body is mapped from the reference with its chin row
 * at the skeleton's chin, but the reference's drawn chin is 0.06 head heights below that row (the drawn chin tip is at row 455,
 * not 434) and ours is 0.025 below, so against the body our head sat 0.035 head heights (0.07 radii) too high and the neck
 * looked too long. Found by the aligned comparison (harness/franzi/aligned.py). Every part drawn on the head takes the skeleton
 * through `onHead`.
 */
export const HEAD_DROP = 0.07;

/** The skeleton as the head parts see it: the head centre lowered by `HEAD_DROP` radii, everything else as it was. */
export const onHead = (sk: Skeleton): Skeleton =>
  replaceSk(sk, { head_cy: sk.head_cy + HEAD_DROP * sk.head_r, head_cx: sk.head_cx + HEAD_SHIFT * sk.head_r });

/**
 * The head's centre in the reference is 8.2 px (0.047 head radii) left of the body's centre line, which the traces were
 * calibrated on (origin x 660, the body's 668.2). Without this every traced head shape sat 0.047 radii too far right, which
 * showed as eyes too far apart on one side and hair too wide on the other (found with the eye overlay, 8x).
 */
export const HEAD_SHIFT = -0.0467;

/** The shared parts that draw on the head, which the adult body wraps so they see the lowered head. */
export const HEAD_PARTS = [
  "_hair_defs", "_hair_mass", "_hair_front", "_hair_tail", "_hair_knot", "_hair_tie", "_hair_clip", "_brows_over_hair", "_face",
  "_mask", "_beard", "_glasses", "_goggles_strap", "_goggles", "_blindfold", "_hat_underside", "_hat", "_headscarf",
] as const;

/** `shared` with every head part taking the lowered head. */
export function withLoweredHead(shared: PartTable): PartTable {
  const out: Record<string, ((...a: any[]) => any) | undefined> = {};
  for (const name of HEAD_PARTS) {
    const fn = shared[name];
    if (fn === undefined) continue;
    // The two free pieces of hair go over the face's edge, right after the front hair.
    out[name] =
      name === "_hair_front"
        ? (sk: Skeleton, p: CharacterParams, ...rest: unknown[]) => fn(onHead(sk), p, ...rest)
        : (sk: Skeleton, ...rest: unknown[]) => fn(onHead(sk), ...rest);
  }
  return out;
}

/**
 * The adult head: the visible skin of the face traced from ref/franzi/ (body-adult-outline-data.ts), drawn over the hair
 * silhouette so its edge is the one line between skin and hair: the hairline, the curtains' inner edges and the jaw.
 */
export function adultHead(sk: Skeleton, p: CharacterParams): string {
  const h = onHead(sk);
  const sw = fmt2(outlineW(strokeW(sk)));
  return ADULT_SKIN_FACE.map(([start, segs]) => `<path d="${curve(h.head_cx, h.head_cy, h.head_r, start, segs)}" fill="${colorStr(p.skin_tone)}" stroke="${OUTLINE}" stroke-width="${sw}" stroke-linejoin="round" />`).join("");
}

/**
 * One strand line as a single filled shape that swells from a point, holds its weight and thins to a point again, so a strand
 * starts and ends inside the hair like a pen stroke and never stops abruptly. A flat black shape, hard-edged.
 */
function taperedStrand(h: Skeleton, [start, segs]: Chain, weight: number, color: string, widths?: readonly number[]): string {
  const pts: Pt[] = [];
  let p0: Pt = start;
  for (const [c, e] of segs) {
    for (let i = 0; i < 6; i++) {
      const t = i / 6;
      pts.push([(1 - t) * (1 - t) * p0[0] + 2 * (1 - t) * t * c[0] + t * t * e[0], (1 - t) * (1 - t) * p0[1] + 2 * (1 - t) * t * c[1] + t * t * e[1]]);
    }
    p0 = e;
  }
  pts.push(p0);
  const n = pts.length;
  const abs = (q: Pt): Pt => [h.head_cx + q[0] * h.head_r, h.head_cy + q[1] * h.head_r];
  const P = pts.map(abs);
  const left: Pt[] = [];
  const right: Pt[] = [];
  for (let i = 0; i < n; i++) {
    const a = P[Math.max(0, i - 1)] as Pt;
    const b = P[Math.min(n - 1, i + 1)] as Pt;
    const len = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
    const nx = -(b[1] - a[1]) / len;
    const ny = (b[0] - a[0]) / len;
    const t = i / (n - 1);
    let half = (weight / 2) * Math.min(1, t / 0.2, (1 - t) / 0.4);
    if (widths) {
      // measured thickness (head radii) interpolated along the line; the ends still close to a point
      const x = t * (widths.length - 1);
      const k = Math.min(widths.length - 2, Math.floor(x));
      const w = (widths[k] as number) * (1 - (x - k)) + (widths[k + 1] as number) * (x - k);
      half = ((w * h.head_r) / 2) * Math.min(1, t / 0.08, (1 - t) / 0.08);
    }
    const q = P[i] as Pt;
    left.push([q[0] + nx * half, q[1] + ny * half]);
    right.push([q[0] - nx * half, q[1] - ny * half]);
  }
  const poly = [...left, ...right.reverse()];
  return `<path d="M ${fmt1((poly[0] as Pt)[0])} ${fmt1((poly[0] as Pt)[1])} ${poly.slice(1).map(line).join("")}Z" fill="${color}" />`;
}

/**
 * Franzi's hair, drawn behind the whole body (the `_hair_tail` slot, before the torso). One silhouette, the visible hair plus the
 * face, ears and strips shrunk a few pixels (harness/franzi_hair/outline_masks.py), so its edge only ever meets the page, the neck
 * or the shoulder and never doubles a line the skin regions draw, with the strand lines over it, clipped to it. The ponytail runs on
 * past the shoulder line, so the shoulder covers its end and it reads as going behind the shoulder. It replaces the earlier dome, two
 * free pieces and the eye-band patch, whose straight cuts and separate outlines left steps, ledges and doubled lines.
 */
export function adultHairBehind(sk: Skeleton, p: CharacterParams): string {
  const h = onHead(sk);
  const d = ([start, segs]: Chain): string => curve(h.head_cx, h.head_cy, h.head_r, start, segs);
  const clip = `<clipPath id="adult-hair-clip">${ADULT_HAIR_SILHOUETTE.map((c) => `<path d="${d(c)}" />`).join("")}</clipPath>`;
  return clip + adultHairShape(sk, p);
}

/** The hair silhouette with its outline and the strand lines over it, clipped to the silhouette (the shared body of the two draws). */
function adultHairShape(sk: Skeleton, p: CharacterParams): string {
  const h = onHead(sk);
  const sw = fmt2(outlineW(strokeW(sk)));
  const d = ([start, segs]: Chain): string => curve(h.head_cx, h.head_cy, h.head_r, start, segs);
  const hair = ADULT_HAIR_SILHOUETTE.map((c) => `<path d="${d(c)}" fill="${colorStr(p.hair_color)}" stroke="${OUTLINE}" stroke-width="${sw}" stroke-linejoin="round" />`).join("");
  const strands = ADULT_HAIR_STRANDS.map((c) => taperedStrand(h, c, outlineW(strokeW(sk), 0.5), shade(p.hair_color, 2.6, 0.9))).join("");
  return hair + `<g clip-path="url(#adult-hair-clip)">${strands}</g>`;
}

/**
 * The skin beside the face and the ears, each its own traced region, drawn over the body and the hair (the `_ears` slot, after the
 * torso): the strips of neck and temple that show between a curtain and the cheek (7 to 18 px wide in the reference, so drawn with a thin
 * outline as the reference does, or the line would fill them), and the two ears. An ear is three things as in the
 * reference: the skin with its outline, the shaded inner part (the concha, a second tone of the skin on a small element), and the dark
 * fold lines, each tapering to a point at both ends. The face goes over all of it.
 */
export function adultSkinBeside(sk: Skeleton, p: CharacterParams): string {
  const h = onHead(sk);
  const d = ([start, segs]: Chain): string => curve(h.head_cx, h.head_cy, h.head_r, start, segs);
  const skin = (c: Chain, weight: number): string => `<path d="${d(c)}" fill="${colorStr(p.skin_tone)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk), weight))}" stroke-linejoin="round" />`;
  const inner = shade(p.skin_tone, 0.83, 1.6);
  const concha = (cs: readonly Chain[]): string => cs.map((c) => `<path d="${d(c)}" fill="${inner}" />`).join("");
  const folds = (cs: readonly Chain[], ws: readonly (readonly number[])[]): string => cs.map((c, i) => taperedStrand(h, c, outlineW(strokeW(sk), 0.38), OUTLINE, ws[i])).join("");
  return (
    ADULT_SKIN_STRIPS.map((c) => skin(c, 0.4)).join("") +
    ADULT_SKIN_EAR_L.map((c) => skin(c, 0.5)).join("") +
    concha(ADULT_EAR_CONCHA_L) +
    folds(ADULT_EAR_FOLDS_L, ADULT_EAR_FOLD_WIDTHS_L) +
    ADULT_SKIN_EAR_R.map((c) => skin(c, 0.5)).join("") +
    concha(ADULT_EAR_CONCHA_R) +
    folds(ADULT_EAR_FOLDS_R, ADULT_EAR_FOLD_WIDTHS_R)
  );
}

/** What is drawn over the face: the brows and the eyes. (The hair is behind it now, in `adultHairBack`.) */
export function adultHairFront(sk: Skeleton, p: CharacterParams): string {
  const h = onHead(sk);
  return adultBrows(h) + adultEyes(h, p);
}

/** The brows: two filled, tapering shapes traced from the reference, thick at the outer end and thin toward the nose. */
function adultBrows(h: Skeleton): string {
  return [ADULT_BROW_L, ADULT_BROW_R]
    .map((poly) => {
      const pts = poly.map(([x, y]): Pt => [h.head_cx + x * h.head_r, h.head_cy + y * h.head_r]);
      return `<path d="M ${fmt1((pts[0] as Pt)[0])} ${fmt1((pts[0] as Pt)[1])} ${pts.slice(1).map(line).join("")}Z" fill="${OUTLINE}" stroke="${OUTLINE}" stroke-width="0.3" stroke-linejoin="round" />`;
    })
    .join("");
}

/**
 * The adult face: brows from the shared code, eyes from the traced shape (body-adult-eyes.ts), the nose dot and the mouth. The
 * shared face code is not used because its eye is the chibi's round one.
 */
export function adultFace(sk: Skeleton, p: CharacterParams): string {
  const h = onHead(sk);
  const f = p.face;
  const sw = strokeW(sk);
  const parts: string[] = [];
  parts.push(noseDot(h, sw));
  const mouthY = h.head_cy + h.head_r * (MOUTH_Y + MOUTH_REALISTIC_DROP * faceBuild(sk) + f.mouth_drop);
  const half = h.head_r * 0.12 * f.mouth_width;
  parts.push(`<path d="M ${fmt1(h.head_cx - half)} ${fmt1(mouthY)} Q ${fmt1(h.head_cx)} ${fmt1(mouthY + h.head_r * 0.08 * f.mouth_curve)} ${fmt1(h.head_cx + half)} ${fmt1(mouthY)}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw, 0.62))}" stroke-linecap="round" />`);
  return parts.join("");
}

/**
 * The relaxed hand's interior, traced from the close-up (harness/franzi_hands/): the curled fingers in shadow (a second tone of the skin, on a small
 * element), the dark wedge between them and the thumb, the nails and the contour lines, tapering. The viewer's-right hand is the mirror image. The
 * shade and the cavity are clipped to the body outline and the outline's stroke is drawn again over them in the hands' rows, because their edge is
 * the skin's edge, so they would otherwise cover half of the stroke there (the same as for the toenails).
 */
function adultHandsDetail(sk: Skeleton, p: CharacterParams): string {
  const { cx, y, w } = place(sk);
  const pixelFrame = { head_cx: 0, head_cy: 0, head_r: 1 } as Skeleton; // taperedStrand reads a chain in head radii; this frame makes it read pixels
  const parts: string[] = [];
  for (const sign of [-1, 1]) {
    const px = (q: Pt): Pt => [cx + sign * w(q[1], q[0]), y(q[1])];
    const inPx = ([start, segs]: Chain): Chain => [px(start), segs.map(([c, e]) => [px(c), px(e)] as [Pt, Pt])];
    const closed = (ch: Chain, attrs: string): string => {
      const [start, segs] = inPx(ch);
      return `<path d="M ${fmt1(start[0])} ${fmt1(start[1])} ` + segs.map(([c, e]) => quad(c, e)).join("") + `Z" ${attrs} />`;
    };
    const fills =
      HAND_SHADE.map((c) => closed(c, `fill="${shade(p.skin_tone, 0.83, 1.6)}"`)).join("") +
      HAND_FINGERS.map((c) => closed(c, `fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk), 0.4))}" stroke-linejoin="round"`)).join("") +
      HAND_GAPS.map((c) => closed(c, `fill="${OUTLINE}"`)).join("") +
      HAND_CAVITY.map((c) => closed(c, `fill="${OUTLINE}"`)).join("");
    parts.push(`<g clip-path="url(#adult-hand-body)">${fills}</g>`);
    // the thumb over the finger outlines, from `HAND_THUMB_FROM` down (the rows of its tip): skin, with a thin outline of its own
    const thumbClip = `adult-thumb-rows-${sign < 0 ? "l" : "r"}`;
    parts.push(`<clipPath id="${thumbClip}"><rect x="0" y="${fmt1(y(HAND_THUMB_FROM))}" width="${fmt1(sk.canvas_w)}" height="${fmt1(sk.canvas_h)}" /></clipPath>`);
    parts.push(`<g clip-path="url(#${thumbClip})">` + HAND_THUMB.map((c) => closed(c, `fill="${colorStr(p.skin_tone)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk), 0.4))}" stroke-linejoin="round"`)).join("") + "</g>");
    parts.push(...HAND_NAILS.map((c) => closed(c, `fill="${tint(p.skin_tone, 0.28)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk), 0.3))}" stroke-linejoin="round"`)));
    HAND_LINES.forEach((c, i) => parts.push(taperedStrand(pixelFrame, inPx(c), 0, OUTLINE, (HAND_LINE_WIDTHS[i] as readonly number[]).map((v) => v * sk.head_r))));
  }
  // the outline's stroke over the fills, in each hand's columns and rows, at the hands' weight (their edge is the skin's edge, so they covered half of it)
  const stroke = adultBodyStroke(sk, "hands");
  const clip = `<clipPath id="adult-hand-body"><path d="${adultBodyPath(sk)}" /></clipPath>`;
  return clip + parts.join("") + stroke;
}

/**
 * Thin interior lines on the hands and feet, over the body: a thumb and a finger line on each hand, the toe divisions and
 * the big toenail on each foot. Interior strokes, not outlines, so lighter than the outline.
 */
export function adultDetail(sk: Skeleton, p: CharacterParams): string {
  const { cx, y, w } = place(sk);
  const sw = outlineW(strokeW(sk), 0.55);
  const stroke = (pts: Pt[]): string => `<path d="M ${fmt1((pts[0] as Pt)[0])} ${fmt1((pts[0] as Pt)[1])} ${smooth(pts)}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(sw)}" stroke-linecap="round" stroke-linejoin="round" />`;
  const out: string[] = [];
  const nailsHere: string[] = [];
  let footClip = "";
  for (const sign of [-1, 1]) {
    const P = (v: number, d: number): Pt => [cx + sign * w(d, v), y(d)];
    // Foot, traced from the close-up (harness/franzi_feet/): the dividers between toes, thin at the base and heavy toward the notch, and the
    // five toenails, each a closed ring with a slightly lighter fill. The chains are in the knots' [v, d] coordinates, mapped like the legs.
    const px = (q: Pt): Pt => [cx + sign * w(q[1], q[0]), y(q[1])];
    const inPx = ([start, segs]: Chain): Chain => [px(start), segs.map(([c, e]) => [px(c), px(e)] as [Pt, Pt])];
    const pixelFrame = { head_cx: 0, head_cy: 0, head_r: 1 } as Skeleton; // taperedStrand reads a chain in head radii; this frame makes it read pixels
    FOOT_DIVIDERS.forEach((c, i) => out.push(taperedStrand(pixelFrame, inPx(c), 0, OUTLINE, (FOOT_DIVIDER_WIDTHS[i] as readonly number[]).map((v) => v * sk.head_r))));
    // The nails are clipped to the body outline and the outline's stroke is drawn again over them below the ankle, because the stroke
    // (about 10 close-up px a side) is wider than the gap between a little toe's nail and the toe's edge, so a nail would spill over it.
    const nailPaths = FOOT_NAILS.map((ring) => {
      const [start, segs] = inPx(ring);
      const d = `M ${fmt1(start[0])} ${fmt1(start[1])} ` + segs.map(([c, e]) => quad(c, e)).join("") + "Z";
      return `<path d="${d}" fill="${tint(p.skin_tone, 0.28)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk), 0.3))}" stroke-linejoin="round" />`;
    }).join("");
    if (sign < 0) {
      const top = y(FOOT_D_CUT);
      const frame = `<rect x="0" y="${fmt1(top)}" width="${fmt1(sk.canvas_w)}" height="${fmt1(sk.canvas_h - top)}" />`;
      footClip =
        `<clipPath id="adult-foot-body"><path d="${adultBodyPath(sk)}" /></clipPath><clipPath id="adult-foot-rows">${frame}</clipPath>` +
        `<g clip-path="url(#adult-foot-body)">NAILS</g>` +
        `<path d="${adultBodyPath(sk)}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)))}" stroke-linejoin="round" clip-path="url(#adult-foot-rows)" />`;
    }
    nailsHere.push(nailPaths);
  }
  return out.join("") + footClip.replace("NAILS", nailsHere.join("")) + adultHandsDetail(sk, p);
}

/**
 * The neck: skin from inside the head down to where the body outline begins, with a line down each side that runs into
 * that outline, so there is no break between the jaw and the shoulder slope (the chibi's neck stops short of it).
 */
export function adultNeck(sk: Skeleton, p: CharacterParams): string {
  const { cx, y } = place(sk);
  const hs = outlineW(strokeW(sk)) / 2;
  const top = sk.head_cy + sk.head_r * 0.8;
  const bottom = y(0.12);
  const nw = sk.neck_half_w;
  const sw = fmt2(outlineW(strokeW(sk)));
  const side = (x: number): string => `<path d="M ${fmt1(x)} ${fmt1(top)} L ${fmt1(x)} ${fmt1(bottom)}" fill="none" stroke="${OUTLINE}" stroke-width="${sw}" stroke-linecap="round" />`;
  return `<rect x="${fmt1(cx - nw)}" y="${fmt1(top)}" width="${fmt1(2 * nw)}" height="${fmt1(bottom - top + 3 * hs)}" fill="${colorStr(p.skin_tone)}" />` + side(cx - nw) + side(cx + nw);
}

const none = (): string => "";

/** The parts an adult body replaces. Everything else (head, hair, face, garments) is the shared code. */
export const ADULT_PARTS = {
  _torso: adultTorso,
  _legs_and_boots: adultBriefs,
  _arms: adultDetail,
  _underwear_top: none,
  _navel: none,
  _chest_lines: none,
  _bust_lines: none,
  _bust_over_arms: none,
  _neck: adultNeck,
  _head: adultHead,
  _hair_front: adultHairFront,
  _face: adultFace,
  _ears: adultSkinBeside,
  _hair_tail: adultHairBehind,
  _hair_mass: none,
};
