// The adult woman's bare-body parts: one fused outline from the neck to the soles with the arms hanging beside it, and
// the underwear that is always worn on it. They replace the chibi's `_torso`, `_legs_and_boots`, `_arms`,
// `_underwear_top` and friends for a body in `ADULT_BODY_TYPES` (render.ts picks the table), and are built from the
// knot tables in body-adult-data.ts (measured off ref/franzi/, in head heights) mapped onto the skeleton's anchors, so
// a different waist, hip or leg width in the profile moves the figure. Docs: docs/adult-body-plan.md.
//
// The arms are part of the one outline for now: a garment that needs the arm in front of it (a sleeve over the
// upper arm is drawn over the body anyway) will split them off at stage 6.

import { OUTLINE, curve, outlineW, soft, strokeW } from "./character.ts";
import { SOFT_LOCK_STRENGTH_SCALE, hairClip, softLocks } from "./hair.ts";
import { colorStr } from "./body-parts-legs.ts";
import { ADULT_REF } from "./body-adult.ts";
import { ARM_INNER, ARM_OUTER, LEG_INNER, LEG_OUTER, SHOULDER_OUTER, TORSO_SIDE } from "./body-adult-data.ts";
import { ADULT_BREAST } from "./body-adult-bust-data.ts";
import { ADULT_TOP } from "./body-adult-top-data.ts";
import { ADULT_BOTTOM } from "./body-adult-bottom-data.ts";
import { FOOT_D_CUT, FOOT_OUTLINE } from "./body-adult-foot-data.ts";
import { HAND_D_CUT, HAND_OUTLINE, HAND_STROKE_K } from "./body-adult-hand-data.ts";
import { HAND_CAVITY, HAND_FINGERS, HAND_GAPS, HAND_LINES, HAND_LINE_WIDTHS, HAND_NAILS, HAND_SHADE, HAND_THUMB, HAND_THUMB_FROM } from "./body-adult-hand-lines-data.ts";
import { FOOT_DIVIDERS, FOOT_DIVIDER_WIDTHS, FOOT_NAILS } from "./body-adult-foot-lines-data.ts";
import { adultCutOf } from "./body-adult-cuts.ts";
import type { CharacterParams, FaceStyle } from "./params.ts";
import { MOUTH_INSIDE, blush, mouthDepthShare } from "./face.ts";
import { fmt1, fmt2 } from "./pynum.ts";
import { shade, tint } from "./colorutil.ts";
import { adultEyes } from "./body-adult-eyes.ts";
import { RAISED_SHOULDER_D, gripIsFist, raisedSides } from "./body-adult-pose.ts";
import { HAND_FIST_OUTLINE } from "./body-adult-hand-poses-data.ts";
import { HAND_FIST_CAVITY, HAND_FIST_FINGERS, HAND_FIST_NAILS } from "./body-adult-hand-poses-lines-data.ts";
import { ADULT_BROW_L, ADULT_BROW_R } from "./body-adult-brow-data.ts";
import type { PartTable } from "./parts.ts";
import type { Chain } from "./tables.ts";
import { replace as replaceSk, type Skeleton } from "./skeleton.ts";

export type Knots = readonly (readonly [number, number])[];

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
export function at(tab: Knots, d: number): number {
  return piecewise(d, tab.map((k) => k[0]), tab.map((k) => k[1]));
}

export interface Place {
  y: (d: number) => number;
  /** Half-width in pixels of a knot value `v` (H) at depth `d`, following the profile's widths. */
  w: (d: number, v: number) => number;
  cx: number;
}

export function place(sk: Skeleton): Place {
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

export type Pt = readonly [number, number];

/** Where the gap between the legs starts, in head heights below the chin: under the briefs' gusset (which ends at 2.262), so its top edge is hidden by it and the gusset's lower edge is the only line across the slot. */
const GAP_TOP = 2.2;

/** The tip of the gap between arm and torso, [x, d] in head heights: where the cup's lower outer corner meets the arm (ref 04). */
const GAP_TIP: Pt = [0.4, 0.955];

/**
 * The ribs, [v, d] in head heights: where the outline of a side without its arm runs from the armpit down to the gap's tip. Below the armpit it follows the bikini top's outer edge, a little outside
 * it (the cup bulges to 0.452 at 0.78), so the breast's side is skin and is not cut off where the hanging arm used to be (the top is clipped to this outline).
 */
export const RIB_KNOTS: readonly Pt[] = [[0.455, 0.5], [0.45, 0.62], [0.462, 0.74], [0.458, 0.82], [0.432, 0.9]];

/** A Catmull-Rom curve through `pts`, as cubic segments continuing from the first point (the pen is already there). */
export function smooth(pts: readonly Pt[]): string {
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

/** A `smooth` path less its last or its first span: what is left is the curve as if the span were there, which a raised arm's edge and the shoulder it leaves share the direction of. */
export const withoutLastSpan = (s: string): string => s.slice(0, s.lastIndexOf("C "));
export const withoutFirstSpan = (s: string): string => s.slice(s.indexOf("C ", 1));

const line = (pt: Pt): string => `L ${fmt1(pt[0])} ${fmt1(pt[1])} `;

/** A quadratic from the pen to `end` through the control point `ctrl`. */
export const quad = (ctrl: Pt, end: Pt): string => `Q ${fmt1(ctrl[0])} ${fmt1(ctrl[1])} ${fmt1(end[0])} ${fmt1(end[1])} `;

/**
 * The body outline is defined once per drawing, in `<defs>`, and everything else refers to it with `<use>`: its fill, the clip paths of the toenails, the hands and the foot, and the stroke bands
 * of `adultBodyStroke`. It is a 46 KB path, and when each of those carried its own copy there were 48 of them in the file (2.3 MB for one figure; 180 KB with one). `adultSkin` writes the
 * definition, before anything refers to it, so a part that uses `adultBodyRef` or `adultBodyClip` needs `adultSkin` (the torso) drawn in the same document.
 */
export const BODY_OUTLINE_ID = "adult-body-outline";
export const adultBodyDef = (sk: Skeleton, without: readonly number[] = [], hand: Chain = HAND_OUTLINE): string => `<defs><path id="${BODY_OUTLINE_ID}" d="${adultBodyPath(sk, without, hand)}" /></defs>`;
/** A reference to the body outline with the given presentation attributes (fill, stroke, clip-path). */
export const adultBodyRef = (attrs: string): string => `<use href="#${BODY_OUTLINE_ID}" ${attrs} />`;
/** A clip path of the body outline, by id. */
export const adultBodyClip = (id: string): string => `<clipPath id="${id}"><use href="#${BODY_OUTLINE_ID}" /></clipPath>`;

/**
 * The body's one outline, neck to soles with the arms, as a closed path. `without` lists the sides (-1 the viewer's left, +1 the right) whose arm is left out, because it is raised and drawn
 * on its own (body-adult-pose-arm.ts): on such a side the outline runs from the top of the shoulder in to the armpit and down the torso, under the cap of the raised arm. The default, no
 * side left out, is the same path as always.
 */
export function adultBodyPath(sk: Skeleton, without: readonly number[] = [], handChain: Chain = HAND_OUTLINE): string {
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
  // A side without its arm: the shoulder stops at the shoulder's tip, where the raised arm's cap begins (`RAISED_SHOULDER_D`), and the outline goes in to the armpit and down the ribs to the gap's tip.
  const shoulderAbove: Knots = [...SHOULDER_OUTER.filter(([dd]) => dd < RAISED_SHOULDER_D), [RAISED_SHOULDER_D, at(SHOULDER_OUTER, RAISED_SHOULDER_D)]];
  const shoulderNext = (sign: number): Pt => side(sign, [SHOULDER_OUTER.find(([dd]) => dd > RAISED_SHOULDER_D + 1e-6) as readonly [number, number]])[0] as Pt;
  const out = (sign: number): Pt[] => [
    [cx + sign * sk.neck_half_w, y(0.12)],
    [cx + sign * (w(0.2, 0.2) - hs), y(0.2)],
    [cx + sign * (w(0.25, 0.4) - hs), y(0.25)],
    ...(without.includes(sign) ? side(sign, shoulderAbove) : [...side(sign, SHOULDER_OUTER), ...side(sign, armOuterAbove)]),
  ];
  const ribs = (sign: number): Pt[] => RIB_KNOTS.map(([v, dd]): Pt => [cx + sign * (w(dd, v) - hs), y(dd)]);
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
  const hand = (sign: number): string => walk(sign, handChain);
  const a = out(L);
  const start = a[0] as Pt;
  // Left side down, round the left hand, up the arm's inside, over the armpit, down the torso and leg to the sole.
  let d = `M ${fmt1(start[0])} ${fmt1(start[1])} `;
  // on a side without its arm the shoulder's last span is given the knot beyond the tip, then dropped, so the line leaves the tip in the direction the raised arm's edge takes up there
  d += without.includes(L) ? withoutLastSpan(smooth([...a, shoulderNext(L)])) : smooth(a);
  const leg = legLine(L);
  if (without.includes(L)) {
    d += smooth([a[a.length - 1] as Pt, ...ribs(L), tip(L)]);
    d += quad(capTor(L), leg[0] as Pt);
  } else {
    d += hand(L);
    d += smooth(rev(side(L, armInnerAbove)));
    d += quad(capArm(L), tip(L)) + quad(capTor(L), leg[0] as Pt);
  }
  d += smooth(leg);
  d += foot(L);
  // The inside of the left leg up to the crotch, across, and the same down the right leg.
  d += smooth(rev(side(L, legInnerAbove)));
  // The gap between the legs has a flat top under the briefs' gusset, its sides running straight up behind it, as in the reference (a slot about 0.09 H wide). It
  // was two lines meeting in a point at 2.25 H, crossing the gusset's lower edge into an X over a pentagon of page, which read as anatomical (the owner).
  const gapL = side(L, legInnerAbove)[0] as Pt;
  const gapR = side(R, LEG_INNER)[0] as Pt;
  d += line([gapL[0], y(GAP_TOP)]);
  d += line([gapR[0], y(GAP_TOP)]);
  d += line(gapR);
  d += smooth(side(R, legInnerAbove));
  d += foot(R);
  d += smooth(rev(legLine(R)));
  if (without.includes(R)) {
    const shoulder = out(R);
    d += quad(capTor(R), tip(R));
    d += smooth([tip(R), ...rev(ribs(R)), shoulder[shoulder.length - 1] as Pt]);
  } else {
    d += quad(capTor(R), tip(R)) + quad(capArm(R), side(R, ARM_INNER)[0] as Pt);
    d += smooth(side(R, armInnerAbove));
    d += hand(R);
  }
  d += without.includes(R) ? withoutFirstSpan(smooth([shoulderNext(R), ...rev(out(R))])) : smooth(rev(out(R)));
  return d + "Z";
}

export function inkAttrs(sk: Skeleton, fill: string): string {
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
  return adultSkin(sk, p) + mid + `<g clip-path="url(#adult-bust-mid)">${adultBustLine(sk, DEFAULT_TAPER, shade(p.skin_tone, 0.78, 1.6), 0.8)}</g>` + `${adultBodyClip("adult-body-clip")}<g clip-path="url(#adult-body-clip)">${adultBand(sk, p)}</g>`;
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
  const raised = raisedSides(p);
  const crease = [1, -1]
    .filter((sign) => !raised.includes(sign))
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
  return adultBodyDef(sk, raised, gripIsFist(p) ? HAND_FIST_OUTLINE : HAND_OUTLINE) + adultBodyRef(`fill="${colorStr(p.skin_tone)}"`) + adultBodyStroke(sk) + crease;
}

/** The hand zones' geometry: each hand's piece between two depths, from the arm's outer side to an inner edge that follows the thigh. */
function handPieces(sk: Skeleton) {
  const { cx, y, w } = place(sk);
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
  return { piece, poly, px, vIn, dAt, rect, OUT };
}

/** A clip path of both hands from the wrist down (the zone `adultBodyStroke` strokes), so a hand can be drawn over a garment that passes in front of it. */
export function adultHandZoneClip(sk: Skeleton, id: string): string {
  const { piece } = handPieces(sk);
  return `<clipPath id="${id}">${piece(-1, HAND_D_CUT, 2.9)}${piece(1, HAND_D_CUT, 2.9)}</clipPath>`;
}

/**
 * The body outline's stroke. The hands are stroked thinner than the rest (`HAND_STROKE_K` of the weight): a finger on the close-up is about as wide
 * as a full-weight stroke, which hid the thumb's edge and the finger tips. The stroke is the same path drawn in clipped pieces: full weight
 * everywhere but the hand columns below the wrist, a taper over twenty bands to the hand weight, from `HAND_D_CUT` down. The hand's own chain is inset by the hand weight's half stroke (harness/franzi_hands/outline.py).
 */
export function adultBodyStroke(sk: Skeleton, only: "all" | "hands" = "all", idPrefix = "adult-stroke"): string {
  const { cx, y, w } = place(sk);
  const full = outlineW(strokeW(sk));
  const stroke = (width: number, clip: string): string => adultBodyRef(`fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(width)}" stroke-linejoin="round" clip-path="url(#${clip})"`);
  const top = y(HAND_D_CUT);
  const bottom = y(2.9);
  const big = sk.canvas_w;
  const bigH = sk.canvas_h;
  const { piece, poly, px, vIn, dAt, rect, OUT } = handPieces(sk);
  const xl = Math.min(cx - w(2.3, OUT), cx + w(2.3, OUT));
  const xr = Math.max(cx - w(2.3, OUT), cx + w(2.3, OUT));
  // the rest: everything but the hand zones. Above the wrist and below the hands, the whole width; between, the outside of each arm and the middle.
  const dsAll = dAt(HAND_D_CUT, 2.9);
  const middle = poly([...dsAll.map((d) => px(-1, d, vIn(d))), ...[...dsAll].reverse().map((d) => px(1, d, vIn(d)))]);
  const rest = `<clipPath id="${idPrefix}-rest">${rect(0, 0, big, top)}${rect(0, top, xl, bottom)}${rect(xr, top, big, bottom)}${middle}${rect(0, bottom, big, bigH)}</clipPath>`;
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
    hands += band(`${idPrefix}-t${i}`, i === 0 ? d0 : d0 - lap, d1);
    strokes += stroke(full * k, `${idPrefix}-t${i}`);
  }
  hands += band(`${idPrefix}-hand`, taperEnd - lap, 2.9);
  strokes += stroke(full * HAND_STROKE_K, `${idPrefix}-hand`);
  return (only === "all" ? rest + stroke(full, `${idPrefix}-rest`) : "") + hands + strokes;
}

/**
 * How far one unit of the `bust` knob scales the adult bust. On the adult woman `bust` is an offset from her traced bust (Franzi's), not an amount from nothing as on the
 * chibi: 0, the default, is the traced one and draws exactly what it always did, below 0 a smaller bust (-0.5 is 0.75 of it) and above 0 a larger one.
 */
export const ADULT_BUST_SPAN = 0.5;

/** The scale the `bust` knob asks of the adult bust: 1 at the default. */
export const adultBustScale = (bust: number): number => 1 + bust * ADULT_BUST_SPAN;

/** Where the scaling of the bust starts to bite and where it is full, in head heights below the chin: above them the straps and the neck are the garment's, not the breast's. */
const BUST_RAMP_FROM = 0.3;
const BUST_RAMP_TO = 0.5;
/** The depth the bust's height is scaled about, just above the top of the breasts (0.485). */
const BUST_TOP = 0.45;

/**
 * A point of the bust's traced outlines ([x, d] in head heights: x from the centre line, d below the chin) moved for the bust knob `s` (`adultBustScale`): x scales about the centre line,
 * so the cleavage's V stays where it is, and the depth about the top of the breasts, so a smaller bust is shorter and its lower edge rises (measured on Risa's reference, whose
 * bikini top is 0.87 of Franzi's wide and sits shorter). The ramp over the neck and straps keeps them from following. `s` of 1 returns the point as it is.
 */
export function bustWarp(q: Pt, s: number): Pt {
  if (s === 1) return q;
  const t = Math.min(1, Math.max(0, (q[1] - BUST_RAMP_FROM) / (BUST_RAMP_TO - BUST_RAMP_FROM)));
  const g = t * t * (3 - 2 * t);
  return [q[0] * (1 + (s - 1) * g), q[1] <= BUST_TOP ? q[1] : BUST_TOP + (q[1] - BUST_TOP) * (1 + (s - 1) * g)];
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
    const scale = adultBustScale(sk.bust);
    const add = (q0: Pt): void => {
      const q = bustWarp(q0, scale);
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
      const scale = adultBustScale(sk.bust);
      const map = (q0: Pt): Pt => {
        const q = bustWarp(q0, scale);
        return [cx + sign * w(q[1], -q[0]), y(q[1])];
      };
      const s0 = map(start);
      const d = `M ${fmt1(s0[0])} ${fmt1(s0[1])} ` + segs.map(([c, e]) => quad(map(c), map(e))).join("") + "Z";
      return `<path d="${d}" fill="none" stroke="${OUTLINE}" stroke-width="${sw}" stroke-linejoin="round" />`;
    })
    .join("");
}

/**
 * Underwear below the waist, always worn: briefs traced from the bikini-bottom layer of ref 04 (body-adult-bottom-data.ts): the waistband curving down to the
 * centre, the wings flaring to the hips and the leg openings running in long diagonals to a flat gusset. A flat garment with nothing of the body drawn on it.
 */
export function adultBriefs(sk: Skeleton, p: CharacterParams): string {
  const { cx, y, w } = place(sk);
  const [start, segs] = ADULT_BOTTOM;
  // The gusset reaches the reference's depth 2.193, but our legs' gap starts lower (2.25: the crotch the owner signed off), which left a band of skin between them.
  // The last stretch (from 2.10) is lengthened so the gusset ends at the top of the gap, under half a stroke short of it, rather than moving the crotch.
  const STRETCH_FROM = 2.1;
  const BOTTOM_REF = 2.193;
  const BOTTOM_NOW = 2.262;
  const dd = (d: number): number => (d <= STRETCH_FROM ? d : STRETCH_FROM + ((d - STRETCH_FROM) * (BOTTOM_NOW - STRETCH_FROM)) / (BOTTOM_REF - STRETCH_FROM));
  // The wings stopped short of the body's outline (the owner): the traced tip is at 0.502 H from the centre at 1.739 H down, the body's side there is 0.522 H less half a
  // stroke. The region of the wings (out from 0.34 H, down to 1.78 H, easing off over 0.10 H) is moved outward by that gap, so the tips end on the thigh's outline.
  const hs = outlineW(strokeW(sk)) / 2;
  const TIP_D = 1.7386;
  const TIP_V = 0.5016;
  const reach = w(TIP_D, at(TORSO_SIDE, TIP_D)) - hs - w(TIP_D, TIP_V);
  const ease = (t: number): number => {
    const u = Math.min(1, Math.max(0, t));
    return u * u * (3 - 2 * u);
  };
  const map = (q: Pt): Pt => {
    const wing = ease((Math.abs(q[0]) - 0.34) / 0.14) * (1 - ease((q[1] - 1.78) / 0.1));
    return [cx + w(q[1], q[0]) + Math.sign(q[0]) * reach * wing, y(dd(q[1]))];
  };
  const s0 = map(start);
  const d = `M ${fmt1(s0[0])} ${fmt1(s0[1])} ` + segs.map(([c, e]) => quad(map(c), map(e))).join("") + "Z";
  return `<path d="${d}" ${inkAttrs(sk, colorStr(p.outfit.underwear_color))} />`;
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
  const scale = adultBustScale(sk.bust);
  const map = (q0: Pt): Pt => {
    const q = bustWarp(q0, scale);
    return [cx + w(q[1], q[0]), y(q[1])];
  };
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
  const cut = adultCutOf(p);
  const sw = fmt2(outlineW(strokeW(sk), cut.faceWeight));
  return cut.face.map(([start, segs]) => `<path d="${curve(h.head_cx, h.head_cy, h.head_r, start, segs)}" fill="${colorStr(p.skin_tone)}" stroke="${OUTLINE}" stroke-width="${sw}" stroke-linejoin="round" />`).join("");
}

/**
 * One strand line as a single filled shape that swells from a point, holds its weight and thins to a point again, so a strand
 * starts and ends inside the hair like a pen stroke and never stops abruptly. A flat black shape, hard-edged.
 */
export function taperedStrand(h: Skeleton, [start, segs]: Chain, weight: number, color: string, widths?: readonly number[], tipEnd = 0.4): string {
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
    let half = (weight / 2) * Math.min(1, t / 0.2, (1 - t) / tipEnd);
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
  const clip = `<clipPath id="adult-hair-clip">${adultCutOf(p).silhouette.map((c) => `<path d="${d(c)}" />`).join("")}</clipPath>`;
  return clip + adultHairShape(sk, p);
}

/** The hair silhouette with its outline and the strand lines over it, clipped to the silhouette (the shared body of the two draws). */
function adultHairShape(sk: Skeleton, p: CharacterParams): string {
  const h = onHead(sk);
  const sw = fmt2(outlineW(strokeW(sk)));
  const d = ([start, segs]: Chain): string => curve(h.head_cx, h.head_cy, h.head_r, start, segs);
  const cut = adultCutOf(p);
  const hair = cut.silhouette.map((c) => `<path d="${d(c)}" fill="${colorStr(p.hair_color)}" stroke="${OUTLINE}" stroke-width="${sw}" stroke-linejoin="round" />`).join("");
  // the soft finish's clumps over the fill, in the hair's tones, clipped to the silhouette, under the strands
  const clumps = soft(p) && p.highlight_strength > 0 && cut.locks.length > 0 ? softLocks(h, colorStr(p.hair_color), cut.locks, p.highlight_strength * SOFT_LOCK_STRENGTH_SCALE, "adult-hair-clip") : "";
  const strands = cut.strands.map((c) => taperedStrand(h, c, outlineW(strokeW(sk), cut.strandWeight), shade(p.hair_color, cut.strandTone[0], cut.strandTone[1]))).join("");
  // the lines that run down to the face's edge: blunt at the end (the share of the length over which it tapers is a twentieth), the face drawn over what passes the edge
  const edgeStrands = cut.edgeStrands.map((c) => taperedStrand(h, c, outlineW(strokeW(sk), cut.edgeStrandWeight), shade(p.hair_color, cut.strandTone[0], cut.strandTone[1]), undefined, 0.05)).join("");
  return hair + clumps + `<g clip-path="url(#adult-hair-clip)">${strands}${edgeStrands}</g>`;
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
  const cut = adultCutOf(p);
  const ear = (e: typeof cut.earL): string => e.skin.map((c) => skin(c, 0.5)).join("") + concha(e.concha) + folds(e.folds, e.foldWidths);
  return cut.strips.map((c) => skin(c, 0.4)).join("") + ear(cut.earL) + ear(cut.earR);
}

/** The hair clip, where the cut puts it (the shared placement beside the hair's edge for a cut that does not say). */
export function adultHairClip(sk: Skeleton, p: CharacterParams): string {
  return hairClip(onHead(sk), p, adultCutOf(p).clip);
}

/** What is drawn over the face: the fringe where a cut has one of its own, the brows and the eyes. (The hair is behind it now, in `adultHairBack`.) */
export function adultHairFront(sk: Skeleton, p: CharacterParams): string {
  const h = onHead(sk);
  const cut = adultCutOf(p);
  const fringe = cut.fringe;
  let locks = "";
  if (fringe !== null) {
    const d = ([start, segs]: Chain): string => curve(h.head_cx, h.head_cy, h.head_r, start, segs);
    const tone = shade(p.hair_color, cut.strandTone[0], cut.strandTone[1]);
    // The fringe's hair is a shape of its own over the skin, so it covers the strand lines drawn behind the face: the lines are drawn again over it, clipped to it, and the
    // lines that run on past its edge as thin dark lines (the locks' tips) are drawn whole, over the skin.
    const inside = cut.strands.map((c) => taperedStrand(h, c, outlineW(strokeW(sk), cut.strandWeight), tone)).join("");
    const edge = cut.edgeStrands.map((c) => taperedStrand(h, c, outlineW(strokeW(sk), cut.edgeStrandWeight), tone, undefined, 0.05)).join("");
    locks =
      `<clipPath id="adult-fringe-clip">${fringe.hair.map((c) => `<path d="${d(c)}" />`).join("")}</clipPath>` +
      fringe.hair.map((c) => `<path d="${d(c)}" fill="${colorStr(p.hair_color)}" />`).join("") +
      `<g clip-path="url(#adult-fringe-clip)">${inside}</g>` +
      edge +
      fringe.lines.map((c, i) => taperedStrand(h, c, 0, OUTLINE, fringe.widths[i])).join("");
  }
  return locks + adultBrows(h, p) + adultEyes(h, p);
}

/** How far `brow_tilt` 1 turns a brow, in degrees (the chibi's drops the inner end by 0.28 of an eye radius per unit; this is the same idea on a traced brow). */
const BROW_TILT_DEGREES = 9;

/**
 * A traced brow turned about its middle for `FaceStyle.brow_tilt`: positive drops the inner end (stern) and raises the outer, negative the reverse. 0 returns the traced points
 * untouched, so her default drawing keeps its bytes.
 */
function tiltBrow(poly: readonly (readonly [number, number])[], tilt: number): readonly (readonly [number, number])[] {
  if (tilt === 0) return poly;
  const n = poly.length;
  const mx = poly.reduce((a, q) => a + q[0], 0) / n;
  const my = poly.reduce((a, q) => a + q[1], 0) / n;
  const outward = mx < 0 ? -1 : 1; // the left brow's outer end is at negative x
  const phi = (-outward * tilt * BROW_TILT_DEGREES * Math.PI) / 180;
  const [c, sn] = [Math.cos(phi), Math.sin(phi)];
  return poly.map(([x, y]): [number, number] => [mx + (x - mx) * c - (y - my) * sn, my + (x - mx) * sn + (y - my) * c]);
}

/** A traced brow line turned about the middle of its points for `brow_tilt`, as `tiltBrow` turns a filled brow; 0 returns it untouched. */
function tiltChain([start, segs]: Chain, tilt: number): Chain {
  if (tilt === 0) return [start, segs];
  const all: Pt[] = [start, ...segs.flatMap(([c, e]) => [c, e])];
  const turned = tiltBrow(all, tilt);
  return [turned[0] as Pt, segs.map((_, i) => [turned[1 + 2 * i] as Pt, turned[2 + 2 * i] as Pt] as [Pt, Pt])];
}

/** The brows: two filled, tapering shapes traced from the reference, thick at the outer end and thin toward the nose. */
function adultBrows(h: Skeleton, p: CharacterParams): string {
  const lines = adultCutOf(p).brows;
  if (lines !== null) {
    const color = shade(p.hair_color, lines.tone[0], lines.tone[1]);
    return lines.lines.map((c, i) => taperedStrand(h, tiltChain(c, p.face.brow_tilt), 0, color, lines.widths[i])).join("");
  }
  return [ADULT_BROW_L, ADULT_BROW_R]
    .map((traced) => {
      const poly = tiltBrow(traced, p.face.brow_tilt);
      const pts = poly.map(([x, y]): Pt => [h.head_cx + x * h.head_r, h.head_cy + y * h.head_r]);
      return `<path d="M ${fmt1((pts[0] as Pt)[0])} ${fmt1((pts[0] as Pt)[1])} ${pts.slice(1).map(line).join("")}Z" fill="${OUTLINE}" stroke="${OUTLINE}" stroke-width="0.3" stroke-linejoin="round" />`;
    })
    .join("");
}

/** The cheeks' flush, in reference pixels (ref 04, the face's calibration): centre, radii and a turn in degrees, below and outside each eye. Judged by eye against the AI pack's shy picture. */
const ADULT_CHEEKS: readonly { c: Pt; rx: number; ry: number; turn: number }[] = [
  { c: [608, 361], rx: 25, ry: 10, turn: -8 },
  { c: [715, 358], rx: 25, ry: 10, turn: 8 },
];

/** The traced mouth line, in reference pixels (ref 04, the face's calibration), left to right, and its width at each point. */
const MOUTH_POINTS: readonly Pt[] = [[645.5, 399.3], [648, 400.2], [651, 401.2], [654.5, 402.1], [658, 402.8], [662, 403.2], [665, 403.4], [668, 403.3], [671, 403], [674, 402.4], [677, 401.4], [680, 400.2], [683, 398.8], [685.5, 397.4], [687.5, 395.8]];
/** The traced line made symmetric about the middle of its ends: the left half is kept and mirrored for the right, so neither corner sits higher (the traced right corner is 3.5 px higher). */
export const SYMMETRIC_MOUTH_POINTS: readonly Pt[] = (() => {
  const mid = (((MOUTH_POINTS[0] as Pt)[0]) + (MOUTH_POINTS[MOUTH_POINTS.length - 1] as Pt)[0]) / 2;
  const left = MOUTH_POINTS.filter((q) => q[0] < mid);
  return [...left, ...[...left].reverse().map((q): Pt => [2 * mid - q[0], q[1]])];
})();
const MOUTH_WIDTHS: readonly number[] = [1.5, 1.8, 1.9, 1.9, 1.7, 1.5, 1.4, 1.5, 1.7, 1.9, 2.0, 1.9, 1.5, 1.1, 0.7];
const SYMMETRIC_MOUTH_WIDTHS: readonly number[] = (() => {
  const left = MOUTH_WIDTHS.slice(0, SYMMETRIC_MOUTH_POINTS.length / 2);
  return [...left, ...[...left].reverse()];
})();
/** The open mouth's greatest drop below the line, in widths of the mouth, at `mouth_open` 1 (the chibi's is 1.0, which on this narrow mouth read as a gape). */
const ADULT_MOUTH_DEPTH = 0.5;

/**
 * The mouth line as `mouth_curve` and `mouth_width` ask (their defaults, 1, are the traced line, returned as it is so that her default drawing stays byte for byte what it was):
 * the curve scales how far each point sits from the straight line between the two ends (so 0 is straight and below 0 turns the corners down), then the width scales the whole
 * line about its middle.
 */
function adultMouthPoints(f: FaceStyle, symmetric = false): readonly Pt[] {
  const traced = symmetric ? SYMMETRIC_MOUTH_POINTS : MOUTH_POINTS;
  if (f.mouth_curve === 1 && f.mouth_width === 1) return traced;
  const a = traced[0] as Pt;
  const z = traced[traced.length - 1] as Pt;
  const mid = (a[0] + z[0]) / 2;
  return traced.map(([x, y]): Pt => {
    const chord = a[1] + ((z[1] - a[1]) * (x - a[0])) / (z[0] - a[0]);
    return [mid + (x - mid) * f.mouth_width, chord + (y - chord) * f.mouth_curve];
  });
}

/**
 * The adult face: brows from the shared code, eyes from the traced shape (body-adult-eyes.ts), the nose dot and the mouth. The
 * shared face code is not used because its eye is the chibi's round one.
 */
export function adultFace(sk: Skeleton, p: CharacterParams): string {
  const h = onHead(sk);
  // Traced from ref 04 (harness: the pixel maps in docs/adult-body-status.md), in reference pixels and drawn through the head calibration of the eyes (origin (660, 270.5), 175.7 px
  // per head radius). The shared face (a dot for the nose, one symmetric arc for the mouth, placed by the chibi's proportions) read as a smile that was off: the reference's mouth is
  // two thin strokes with a gap between them, 42 px wide and about 9 px higher than ours was, uneven (the right half rises further), and its nose is a pale oval with a short
  // dark tick at its lower right, not a dot.
  const k = h.head_r / 175.7;
  const ref = (q: Pt): Pt => [h.head_cx + (q[0] - 660) * k, h.head_cy + (q[1] - 270.5) * k];
  const line = shade(p.skin_tone, 0.28, 1.4);
  const stroke = (pts: readonly Pt[], widths: readonly number[]): string => {
    // a polyline as a chain of straight quadratics, in head radii for taperedStrand; widths in reference px
    const r = pts.map(([x, y]): Pt => [(x - 660) / 175.7, (y - 270.5) / 175.7]);
    const segs = r.slice(1).map((e, i) => [[((r[i] as Pt)[0] + e[0]) / 2, ((r[i] as Pt)[1] + e[1]) / 2] as Pt, e] as [Pt, Pt]);
    return taperedStrand(h, [r[0] as Pt, segs], 0, line, widths.map((v) => v / 175.7));
  };
  const parts: string[] = [];
  // the flush: `blush` above its default of 1 (her neutral face carries 1 and draws none, as the reference does; the chibi's mild blush at 1 is not hers). Two flat tint ellipses on the
  // cheeks, in the chibi's blush colour for this skin, their opacity growing with how far above 1 the value is (1.5 is the chibi's own opacity, 2 twice it, never past solid).
  if (p.face.blush > 1) {
    const [tint0, opacity] = blush(p.skin_tone);
    const alpha = Math.min(1, opacity * 2 * (p.face.blush - 1));
    // A cut with its own cheeks (Risa's) has the blush clipped to the face's own skin (its traced edge), so a blush near the cheek never runs over the hair or the outline; Franzi's is as it was.
    const clipped = adultCutOf(p).cheeks !== null;
    if (clipped) {
      const faceClip = adultCutOf(p).face.map(([start, segs]) => `<path d="${curve(h.head_cx, h.head_cy, h.head_r, start, segs)}" />`).join("");
      parts.push(`<clipPath id="adult-cheek-clip">${faceClip}</clipPath><g clip-path="url(#adult-cheek-clip)">`);
    }
    for (const cheek of adultCutOf(p).cheeks ?? ADULT_CHEEKS) {
      const c = ref(cheek.c);
      parts.push(`<ellipse cx="${fmt1(c[0])}" cy="${fmt1(c[1])}" rx="${fmt1(cheek.rx * k)}" ry="${fmt1(cheek.ry * k)}" transform="rotate(${cheek.turn} ${fmt1(c[0])} ${fmt1(c[1])})" fill="${tint0}" opacity="${fmt2(alpha)}" />`);
    }
    if (clipped) parts.push(`</g>`);
  }
  // the nose: the pale oval highlight, a lighter tone of the skin, then the dark tick
  const at = adultCutOf(p).featuresAt;
  const nose = (q: Pt): Pt => [q[0] + at.nose[0], q[1] + at.nose[1]];
  const c = ref(nose([657, 360.5]));
  parts.push(`<ellipse cx="${fmt1(c[0])}" cy="${fmt1(c[1])}" rx="${fmt1(3.1 * k)}" ry="${fmt1(5.8 * k)}" transform="rotate(4 ${fmt1(c[0])} ${fmt1(c[1])})" fill="${tint(p.skin_tone, 0.62)}" />`);
  parts.push(stroke([nose([660.6, 366.2]), nose([661.8, 368.8]), nose([663, 372.2])], [1.8, 2.4, 1.2]));
  // the mouth: one continuous line. The reference draws it as two strokes with a small gap at the low point (x about 665), which the owner called a flaw of the reference, so the
  // two are joined there along the curve (the low point is flat for a few px) with the line a little thinner across the join; thickest toward the outer ends, thin at both tips.
  // `mouth_curve`, `mouth_width` and `mouth_open` move it (adultMouthPoints); at their defaults the points are the traced ones, untouched.
  const upper = adultMouthPoints(p.face, adultCutOf(p).symmetricMouth).map((q): Pt => [q[0] + at.mouth[0], q[1] + at.mouth[1]]);
  const open = p.face.mouth_open;
  if (open > 0) {
    // Open: the traced line is the upper lip and a second curve below it closes the shape, filled with the one flat dark red the chibi's open mouth uses, no teeth or tongue.
    const first = upper[0] as Pt;
    const last = upper[upper.length - 1] as Pt;
    const across = last[0] - first[0];
    const drop = across * ADULT_MOUTH_DEPTH * mouthDepthShare(open);
    const lower = upper.map(([x, y]): Pt => [x, y + drop * Math.max(0, Math.sin((Math.PI * (x - first[0])) / across)) ** 0.65]);
    const px = (q: Pt): string => `${fmt1(ref(q)[0])} ${fmt1(ref(q)[1])}`;
    parts.push(`<path d="M ${px(upper[0] as Pt)} ${upper.slice(1).map((q) => `L ${px(q)} `).join("")}${[...lower].reverse().map((q) => `L ${px(q)} `).join("")}Z" fill="${MOUTH_INSIDE}" />`);
    parts.push(stroke(lower, lower.map((_, i) => (i === 0 || i === lower.length - 1 ? 0.6 : 1.3))));
  }
  parts.push(stroke(upper, adultCutOf(p).symmetricMouth ? SYMMETRIC_MOUTH_WIDTHS : MOUTH_WIDTHS));
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
  const raised = raisedSides(p);
  for (const sign of [-1, 1].filter((s) => !raised.includes(s))) {
    const px = (q: Pt): Pt => [cx + sign * w(q[1], q[0]), y(q[1])];
    const inPx = ([start, segs]: Chain): Chain => [px(start), segs.map(([c, e]) => [px(c), px(e)] as [Pt, Pt])];
    const closed = (ch: Chain, attrs: string): string => {
      const [start, segs] = inPx(ch);
      return `<path d="M ${fmt1(start[0])} ${fmt1(start[1])} ` + segs.map(([c, e]) => quad(c, e)).join("") + `Z" ${attrs} />`;
    };
    if (gripIsFist(p)) {
      // The fist, where `grip_style` asks for one: the traced fist's outline is in the body outline (adultBodyPath) and its cavity, finger separations and nails are drawn here, in the same frame.
      // The fist goes in front of what hangs over it, the skirt and the apron: its curled fingers reach farther in than the hand zone (which follows the thigh, and which the relaxed hand fits
      // inside), so the garments covered them and cut them off flat. It is drawn again here, its traced outline filled with skin (closed with a straight chord across the wrist, where the arm's
      // own skin carries on) and edged at the hand's weight, on top of the body's fill and of the thigh's outline where the fingers overlap it.
      const [fistStart, fistSegs] = inPx(HAND_FIST_OUTLINE);
      const fistPath = `M ${fmt1(fistStart[0])} ${fmt1(fistStart[1])} ` + fistSegs.map(([c, e]) => quad(c, e)).join("");
      parts.push(`<path d="${fistPath}Z" fill="${colorStr(p.skin_tone)}" />`);
      parts.push(`<path d="${fistPath}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)) * HAND_STROKE_K)}" stroke-linejoin="round" />`);
      const fistInk = HAND_FIST_CAVITY.map((c) => closed(c, `fill="${OUTLINE}"`)).join("") + HAND_FIST_FINGERS.map((c) => closed(c, `fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk), 0.4))}" stroke-linejoin="round"`)).join("");
      parts.push(`<g clip-path="url(#adult-hand-body)">${fistInk}</g>`);
      parts.push(...HAND_FIST_NAILS.map((c) => closed(c, `fill="${tint(p.skin_tone, 0.28)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk), 0.3))}" stroke-linejoin="round"`)));
      continue;
    }
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
  const stroke = adultBodyStroke(sk, "hands", "adult-hand-stroke");
  const clip = adultBodyClip("adult-hand-body");
  // The hands' skin again, first: a garment drawn before this layer (the shorts) passes behind the hand, so the hand's skin goes over it, and its lines and
  // outline below are then on skin and not on cloth.
  const skin = adultHandZoneClip(sk, "adult-hand-zone") + adultBodyRef(`fill="${colorStr(p.skin_tone)}" clip-path="url(#adult-hand-zone)"`);
  return clip + skin + parts.join("") + stroke;
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
    if (p.outfit.boot_color === null) FOOT_DIVIDERS.forEach((c, i) => out.push(taperedStrand(pixelFrame, inPx(c), 0, OUTLINE, (FOOT_DIVIDER_WIDTHS[i] as readonly number[]).map((v) => v * sk.head_r))));
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
        `${adultBodyClip("adult-foot-body")}<clipPath id="adult-foot-rows">${frame}</clipPath>` +
        `<g clip-path="url(#adult-foot-body)">NAILS</g>` +
        adultBodyRef(`fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)))}" stroke-linejoin="round" clip-path="url(#adult-foot-rows)"`);
    }
    nailsHere.push(nailPaths);
  }
  // A boot covers the foot: its toes, nails and the outline stroke redrawn below the ankle are not drawn then, or they would show through the leather.
  const bare = p.outfit.boot_color === null;
  return out.join("") + (bare ? footClip.replace("NAILS", nailsHere.join("")) : "") + adultArmsOver(sk, p) + adultHandsDetail(sk, p);
}

/**
 * The arms from below the sleeve to the wrist, drawn again over what hangs in front of the legs: a skirt that flares past the arm's inner edge would otherwise cover it (the
 * body is one outline drawn first, and garments over it), where in the reference the arms hang in front of the skirt. Only when a skirt, an apron or a hakama is worn; without one nothing
 * lies over the arms there and the arms are not drawn twice. The strip runs from the outside of the arm in to just past its inner edge, from 1.1 H below the chin (under the
 * blouse's cuff) to the wrist, where the hands' own layer takes over.
 */
/**
 * Garments that cover the arm to the wrist (the school shirt's long sleeves) register here to draw their own sleeves, instead of the skin the arms are drawn again with over the skirt.
 * The first that answers (a string, not null) is used. They register themselves when their module is loaded (body-adult-shirt.ts), because the garments import this module.
 */
export const ARM_OVER_HOOKS: ((sk: Skeleton, p: CharacterParams) => string | null)[] = [];

function adultArmsOver(sk: Skeleton, p: CharacterParams): string {
  for (const hook of ARM_OVER_HOOKS) {
    const own = hook(sk, p);
    if (own !== null) return own;
  }
  if (p.outfit.skirt_color === null && p.outfit.apron_color === null && p.outfit.hakama_color === null) return "";
  const { cx, y, w } = place(sk);
  const hs = outlineW(strokeW(sk)) / 2;
  // a robe's hanging sleeves cover the arm down to their hem, so the strip begins below it
  const from = p.outfit.robe_color !== null && Number(p.outfit.sleeve_drop) > 0 ? 0.9 + 1.8 * Math.min(1, Number(p.outfit.sleeve_drop)) : 0;
  const tab = ARM_INNER.filter(([d]) => d <= HAND_D_CUT + 0.02 && d >= from);
  const strip = (sign: number): string => {
    const inner = tab.map(([d, v]) => `${fmt1(cx + sign * (w(d, v) - hs * 1.5))},${fmt1(y(d))}`);
    const outer = [...tab].reverse().map(([d]) => `${fmt1(cx + sign * w(d, 1.0))},${fmt1(y(d))}`);
    return `<polygon points="${[...inner, ...outer].join(" ")}" />`;
  };
  const id = "adult-arm-strip";
  const hanging = [-1, 1].filter((s) => !raisedSides(p).includes(s));
  if (hanging.length === 0) return "";
  return (
    `<clipPath id="${id}">${hanging.map(strip).join("")}</clipPath>` +
    adultBodyRef(`fill="${colorStr(p.skin_tone)}" clip-path="url(#${id})"`) +
    adultBodyRef(`fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)))}" stroke-linejoin="round" clip-path="url(#${id})"`)
  );
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

/**
 * `_arms` is called twice when a coat is worn (render.ts, layers 15 and 18): first with `false` for the arms and then with `true` for the hands, so the hands come out over the coat's sleeves.
 * The adult arms are part of the body outline and only their hands' and feet's detail is drawn here, so the first pass draws nothing and the second all of it. Called with `null` (no coat) it
 * draws all of it once. Drawing it in both passes defined its ids twice.
 */
export function adultArms(sk: Skeleton, p: CharacterParams, only: boolean | null = null): string {
  return only === false ? "" : adultDetail(sk, p);
}

const none = (): string => "";

/** The parts an adult body replaces. Everything else (head, hair, face, garments) is the shared code. */
export const ADULT_PARTS = {
  _torso: adultTorso,
  _legs_and_boots: adultBriefs,
  _arms: adultArms,
  _underwear_top: none,
  _navel: none,
  _chest_lines: none,
  _bust_lines: none,
  _bust_over_arms: none,
  _neck: adultNeck,
  _head: adultHead,
  _hair_front: adultHairFront,
  _hair_clip: adultHairClip,
  _face: adultFace,
  _ears: adultSkinBeside,
  _hair_tail: adultHairBehind,
  _hair_mass: none,
};
