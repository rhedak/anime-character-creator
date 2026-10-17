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
import { ADULT_EAR_L, ADULT_EAR_R, ADULT_HEAD } from "./body-adult-head-data.ts";
import type { CharacterParams } from "./params.ts";
import { fmt1, fmt2 } from "./pynum.ts";
import type { PartTable } from "./parts.ts";
import { replace as replaceSk, type Skeleton } from "./skeleton.ts";

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
  const tip = (sign: number): Pt => [cx + sign * w(GAP_TIP[1], GAP_TIP[0]), y(GAP_TIP[1])];
  // The cap on the gap: two short quadratics through the tip, a point, so the gap opens from where the arm line ends.
  const capArm = (sign: number): Pt => [cx + sign * (w(1.0, 0.425) + hs * 0.4), y(1.0)];
  const capTor = (sign: number): Pt => [cx + sign * (w(1.0, 0.395) - hs * 0.4), y(1.0)];
  const legLine = (sign: number): Pt[] => [...side(sign, TORSO_SIDE), ...side(sign, LEG_OUTER)];
  const lastOuter = (sign: number): Pt => [cx + sign * (w(5.3, 0.349) - hs), y(5.4) - hs];
  const lastInner = (sign: number): Pt => [cx + sign * (w(5.3, 0.065) + hs), y(5.4) - hs];
  const L = -1;
  const R = 1;
  // The sole as one rounded curve, the little toe's side highest and the big toe lowest; the toes themselves are lines
  // inside it (`adultDetail`). Walked from the outer edge to the big toe on the left foot and back on the right.
  const sole = (sign: number): Pt[] => {
    const xo = cx + sign * (w(5.3, 0.349) - hs);
    const xi = cx + sign * (w(5.3, 0.065) + hs);
    const yBase = y(5.4) - hs;
    const hH = 2 * sk.head_r;
    const at = (t: number, rise: number): Pt => [xo + (xi - xo) * t, yBase - rise * hH];
    return [at(0, 0.05), at(0.1, 0.03), at(0.35, 0.016), at(0.7, 0.004), at(0.93, 0.0), at(1, 0.03)];
  };
  const toes = (sign: number): string => {
    const pts = sole(sign);
    const run = sign < 0 ? pts : [...pts].reverse();
    return line(run[0] as Pt) + smooth(run);
  };
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
  d += quad(capArm(L), tip(L)) + quad(capTor(L), leg[0] as Pt);
  d += smooth(leg);
  d += toes(L);
  // The inside of the left leg up to the crotch, across, and the same down the right leg.
  d += smooth(rev(side(L, LEG_INNER)));
  d += line([cx, y(2.25)]);
  d += line(side(R, LEG_INNER)[0] as Pt);
  d += smooth(side(R, LEG_INNER));
  d += toes(R);
  d += smooth(rev(legLine(R)));
  d += quad(capTor(R), tip(R)) + quad(capArm(R), side(R, ARM_INNER)[0] as Pt);
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
  // The bikini top is drawn here, not in the chest layers, so the neck (the next layer) covers where its straps go behind it.
  // The bust's tapered line goes on the skin and under the top, so only what the top leaves uncovered shows: the inner edges
  // in the V and the lighter upper edge above the cups, as in the reference.
  // The top is clipped to the body's outline, so its straps end at the shoulder line where they pass behind the neck.
  return adultSkin(sk, p) + adultBustLine(sk) + `<clipPath id="adult-body-clip"><path d="${adultBodyPath(sk)}" /></clipPath><g clip-path="url(#adult-body-clip)">${adultBand(sk, p)}</g>`;
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
      const pts = [P(0.455, 0.48), P(0.454, 0.6), P(0.447, 0.7), P(0.455, 0.81), P(0.446, 0.87), P(0.418, 0.92), P(GAP_TIP[0], GAP_TIP[1])];
      return `<path d="M ${fmt1((pts[0] as Pt)[0])} ${fmt1((pts[0] as Pt)[1])} ${smooth(pts)}" fill="none" stroke="${OUTLINE}" stroke-width="${sw}" stroke-linecap="round" stroke-linejoin="round" />`;
    })
    .join("");
  return `<path d="${adultBodyPath(sk)}" ${inkAttrs(sk, colorStr(p.skin_tone))} />` + crease;
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
export function adultBustLine(sk: Skeleton, taper: Taper = DEFAULT_TAPER): string {
  const full = outlineW(strokeW(sk), 0.9);
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
    rings.push(`<path d="${poly(outer)} ${poly(inner)}" fill="${OUTLINE}" fill-rule="evenodd" />`);
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
  const { cx, y, w } = place(sk);
  const [start, segs] = ADULT_TOP;
  const map = (q: Pt): Pt => [cx + w(q[1], q[0]), y(q[1])];
  const s0 = map(start);
  const d = `M ${fmt1(s0[0])} ${fmt1(s0[1])} ` + segs.map(([c, e]) => quad(map(c), map(e))).join("") + "Z";
  return `<path d="${d}" ${inkAttrs(sk, colorStr(p.outfit.underwear_color))} />`;
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
export const onHead = (sk: Skeleton): Skeleton => replaceSk(sk, { head_cy: sk.head_cy + HEAD_DROP * sk.head_r });

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
    if (fn !== undefined) out[name] = (sk: Skeleton, ...rest: unknown[]) => fn(onHead(sk), ...rest);
  }
  return out;
}

/**
 * The adult head: the skin of the face traced from ref/franzi/ (body-adult-head-data.ts), narrower than the chibi's round
 * skull, with the jaw coming down to a point at the chin. The hair drawn over it hides the skull's top and sides.
 */
export function adultHead(sk: Skeleton, p: CharacterParams): string {
  const [start, segs] = ADULT_HEAD;
  const h = onHead(sk);
  const d = curve(h.head_cx, h.head_cy, h.head_r, start, segs);
  return `<path d="${d}" fill="${colorStr(p.skin_tone)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)))}" stroke-linejoin="round" />`;
}

/** The ears, drawn before the head so the face covers their inner edge. */
export function adultEars(sk: Skeleton, p: CharacterParams): string {
  return [ADULT_EAR_L, ADULT_EAR_R]
    .map(([start, segs]) => `<path d="${curve(onHead(sk).head_cx, onHead(sk).head_cy, sk.head_r, start, segs)}" fill="${colorStr(p.skin_tone)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk), 0.8))}" stroke-linejoin="round" />`)
    .join("");
}

/**
 * Thin interior lines on the hands and feet, over the body: a thumb and a finger line on each hand, the toe divisions and
 * the big toenail on each foot. Interior strokes, not outlines, so lighter than the outline.
 */
export function adultDetail(sk: Skeleton, p: CharacterParams): string {
  void p;
  const { cx, y, w } = place(sk);
  const sw = outlineW(strokeW(sk), 0.55);
  const stroke = (pts: Pt[]): string => `<path d="M ${fmt1((pts[0] as Pt)[0])} ${fmt1((pts[0] as Pt)[1])} ${smooth(pts)}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(sw)}" stroke-linecap="round" stroke-linejoin="round" />`;
  const out: string[] = [];
  for (const sign of [-1, 1]) {
    const P = (v: number, d: number): Pt => [cx + sign * w(d, v), y(d)];
    // Hand: the thumb hanging along the inside of the hand, and where the curled fingers part from it.
    out.push(stroke([P(0.715, 2.2), P(0.705, 2.32), P(0.715, 2.44), P(0.7, 2.52)]));
    out.push(stroke([P(0.785, 2.34), P(0.775, 2.45), P(0.745, 2.55)]));
    // Foot: four short lines marking the toes, and the big toenail.
    const xo = w(5.3, 0.349);
    const xi = w(5.3, 0.065);
    const hH = 2 * sk.head_r;
    for (const t of [0.14, 0.3, 0.46, 0.66]) {
      const x = cx + sign * (xo + (xi - xo) * t);
      const yb = y(5.4) - hH * (0.05 - 0.046 * t);
      out.push(stroke([[x, yb - 0.04 * hH], [x + sign * 0.002 * hH, yb - 0.004 * hH]]));
    }
    const nx = cx + sign * (xo + (xi - xo) * 0.85);
    const ny = y(5.4) - 0.045 * hH;
    out.push(stroke([[nx - 0.03 * hH, ny - 0.01 * hH], [nx, ny + 0.012 * hH], [nx + 0.03 * hH, ny - 0.01 * hH]]));
  }
  return out.join("");
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
  _ears: adultEars,
};
