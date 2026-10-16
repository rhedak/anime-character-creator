// The limbs' shared geometry: the sleeve and cap, the bust's outline on the torso's side, the traced garment placement and the
// cut drawer, the arm's line, and the legs' and belt's shared measures. Port of the `core-limbs` module of character.py (see
// `harness/ts_port/modules.json`); the hands are in `core-limbs-hands.ts` and the arms in `core-limbs-arms.ts`. Names are the
// Python ones in camelCase and every expression keeps Python's evaluation order. Numbers reach the text only through the
// `fmt*` kernel functions.
//
// Functions that return a placement closure or take a callable (`garmentPlacement`, `sleevePlacement`, `drawCut` with `xf`) have
// no recorded calls.

import { BODY_TYPES, hatHairMargin, limbTaperAt, skeletonFor } from "./body.ts";
import { OUTLINE, curve, interiorW, outlineW, strokeW } from "./character.ts";
import { shade } from "./colorutil.ts";
import { COAT_CUTS, SLEEVE_CUTS } from "./core-limbs-tables.ts";
import type { GarmentCut, SleeveCut } from "./core-limbs-tables.ts";
import { characterParams } from "./model.ts";
import type { CharacterParams } from "./params.ts";
import {
  PyError,
  at,
  fmt0,
  fmt1,
  fmt2,
  pyCos,
  pyDiv,
  pyHypot,
  pyMax,
  pyMin,
  pyPow,
  pySin,
  pySqrt,
  pyStrRepr,
  radians,
  truthy,
} from "./pynum.ts";
import { sha1Hex } from "./sha1.ts";
import { pyValueRepr } from "./pyvalue.ts";
import { BUILDS, applied, armpitY, buildSkeletonWith, bustReach, bustY, defaultHairMargin, replace, stretched } from "./skeleton.ts";
import type { Skeleton } from "./skeleton.ts";
import type { Chain, Point, Segment } from "./tables.ts";

export { COAT_CUTS, SLEEVE_CUTS, garmentCut } from "./core-limbs-tables.ts";
export type { GarmentCut, HandPiece, SleeveCut } from "./core-limbs-tables.ts";
// The recorded calls name a registry object by its Python name, underscore and all: the same objects under those names.
export {
  LAB_COAT_LAPEL_LEFT as _LAB_COAT_LAPEL_LEFT,
  LAB_COAT_LAPEL_RIGHT as _LAB_COAT_LAPEL_RIGHT,
  LAB_COAT_PANEL_LEFT as _LAB_COAT_PANEL_LEFT,
  LAB_COAT_PANEL_RIGHT as _LAB_COAT_PANEL_RIGHT,
} from "./core-limbs-tables.ts";

/** `max(items)` / `min(items)` of a non-empty list; an empty one is Python's `ValueError`. */
export function maxOf(items: readonly number[]): number {
  if (items.length === 0) throw new PyError("ValueError", "max() iterable argument is empty");
  return pyMax(items[0] as number, ...items.slice(1));
}
export function minOf(items: readonly number[]): number {
  if (items.length === 0) throw new PyError("ValueError", "min() iterable argument is empty");
  return pyMin(items[0] as number, ...items.slice(1));
}

/** `COAT_CUTS[name]`: a name that is not a cut is Python's `KeyError`. */
export function coatCut(name: string | null): GarmentCut {
  if (typeof name !== "string" || !Object.hasOwn(COAT_CUTS, name)) {
    throw new PyError("KeyError", name === null || typeof name !== "string" ? "None" : pyStrRepr(name));
  }
  return COAT_CUTS[name] as GarmentCut;
}

// ---------------------------------------------------------------------------------------------------------
// The sleeve and the cap
//
// Garment panels carry no shadow tone at all. The canon draws the tunic, the
// skirt, the apron, the sleeves and the trousers flat and puts their form on the
// outline; a second tone appears only on small elements, a pouch flap or a boot
// cuff or the turn under a hem, where it reads as a thickness rather than as
// light. Ours used to shade a third of the torso, most of the apron and a stripe
// down every limb, which came to 15% of the figure's ink at the taller build and
// was the most artificial thing on it.
//
// Narrowing those planes to edge turns was tried first and rejected by eye: it
// fixed the torso, but a stripe down something as long and thin as a sleeve or a
// trouser leg reads as two-tone at any width. What is left below is line work,
// which is what the canon uses for drape.

/**
 * Where the tunic's short sleeve ends, which is also where the arm starts.
 * Both parts read it, since the sleeve hem and the arm's top edge are the same
 * line and have to land on each other.
 */
export function sleeveHemY(sk: Skeleton): number {
  return armpitY(sk);
}

/**
 * How far out the sleeve reaches.
 *
 * It has to cover the arm, so it is the arm's own outer edge with a little
 * ease, and it can be wider than the anatomical shoulder: at chibi it has to
 * be, because the shoulders there are narrow while the arms are thick, so a
 * sleeve that stopped at `shoulder_half_w` would not reach the limb it is
 * supposed to be on.
 */
export function sleeveHalfW(sk: Skeleton): number {
  return pyMax(sk.shoulder_half_w, sk.arm_x + sk.arm_half_w * 1.1);
}

/**
 * Whether the tunic draws its cap sleeve slanted over the arm.
 *
 * Not under a coat, a traced jacket or a traced sleeve, which draw their own
 * shoulders and armholes and cover the tunic's cap.
 */
export function sleeveUnderCap(sk: Skeleton, p: CharacterParams): boolean {
  return (
    truthy(p.outfit.sleeve_under_cap) &&
    // No cap without the tunic it belongs to: bare, the arm's top followed
    // the cap's slant anyway (`docs/bare-body-plan.md`, step 4c).
    p.outfit.tunic_color !== null &&
    p.outfit.coat_color === null &&
    !tracedCoat(sk, p) &&
    wornSleeve(sk, p) === null
  );
}

/**
 * How far out the slanted cap reaches, from the centre line.
 *
 * A little past the arm's outer edge at its top: the tip overhangs the sleeve
 * by about 0.07 head radii in the reference, and reaching further, which the
 * flat-shelf cap does, reads as a shoulder pad wider than the arm it covers.
 */
export function capTipX(sk: Skeleton): number {
  const [centreTop] = armLine(sk);
  return centreTop + sk.arm_half_w + sk.head_r * 0.07;
}

/**
 * Height of the cap's slanted underside at `x_off` from the centre line.
 *
 * The line from the cap's tip to the armpit, where the torso's side leaves
 * it. Shared by the tunic's outline and the arm's top edge, so the two
 * strokes land on each other and read as one line.
 */
export function capUndersideY(sk: Skeleton, x_off: number, tip_y: number): number {
  const cuffY = sleeveHemY(sk);
  const torsoAtCuff = armpitX(sk);
  const tipX = capTipX(sk);
  const t = pyDiv(tipX - x_off, tipX - torsoAtCuff);
  return tip_y + (cuffY - tip_y) * pyMax(0.0, pyMin(1.0, t));
}

export function capTipY(sk: Skeleton): number {
  return sk.shoulder_y + shoulderSlope(sk);
}

/**
 * How far the shoulder line drops from the neck to its outer tip. The body's
 * and every garment's shoulder share it; see `_tunic` for why it is this much.
 */
export function shoulderSlope(sk: Skeleton): number {
  return (sk.waist_y - sk.shoulder_y) * 0.24;
}

/**
 * The torso's half-width where the arm leaves it, measured up from the waist
 * rather than down from the shoulder; see `_tunic` for why.
 */
export function torsoAtArmpit(sk: Skeleton): number {
  return sk.waist_half_w + (sk.shoulder_half_w - sk.waist_half_w) * 0.12;
}

// ---------------------------------------------------------------------------------------------------------
// The bust on the torso's side

// How far a bust moves the armpit out, in reaches. The sleeve's underside and
// the bust's outline meet at the armpit; left at the plain torso's width, the
// bust swung out from it straight away and the two met in a V, which read as a
// gap cut between the shoulder and the bust (the owner, 2026-09-25). Carried out
// with the bust, the sleeve lands on the bust's upper slope and the outline runs
// on from one into the other, as the breast runs up into the armpit.
export const BUST_ARMPIT_FILL = 0.7;

/**
 * Where the sleeve's underside meets the torso's side: the plain torso's
 * width at the armpit, carried out by a bust. Every part meeting there reads
 * it (the tunic's sleeve, the arm's top edge, the body's shoulder, the bust's
 * outline), so none can open a sliver against another. Exactly
 * `_torso_at_armpit` without a bust.
 */
export function armpitX(sk: Skeleton, inset = 0.0): number {
  return torsoAtArmpit(sk) - inset + BUST_ARMPIT_FILL * bustReach(sk);
}

/**
 * The armpit-to-waist curve's control height: low enough that the side
 * leaves the armpit vertically and curves in to the waist, rather than being
 * pulled out toward the shoulder's own width on the way.
 */
export function ribCtrlY(sk: Skeleton): number {
  const cuffY = sleeveHemY(sk);
  return cuffY + (sk.waist_y - cuffY) * 0.55;
}

// How far below the bust's fullest point its under-bust tuck lands, in multiples
// of its reach: a larger bust is taller as well as fuller. A first guess, for
// the sweep to settle (`docs/bust-plan.md`, step 1).
export const BUST_DROP = 2.0;

/**
 * The height of the fold under the bust: `_BUST_DROP` reaches below its
 * fullest point, and never lower than three quarters of the way to the waist.
 * The body's outline returns to its side there, and the line under the bust
 * is drawn from it; both read this, so reshaping the body's return cannot
 * move the line (`docs/bust-plan.md`, step 3c).
 */
export function underBustY(sk: Skeleton, peak_y: number): number {
  return pyMin(peak_y + bustReach(sk) * BUST_DROP, sk.waist_y - (sk.waist_y - peak_y) * 0.25);
}

/**
 * The parameter where a quadratic whose height only increases crosses `y`,
 * kept inside the run so a height near either end still splits it.
 */
export function quadCrossing(p0: Point, p1: Point, p2: Point, y: number): number {
  const qa = p0[1] - 2 * p1[1] + p2[1];
  const qb = 2 * (p1[1] - p0[1]);
  const qc = p0[1] - y;
  const u = Math.abs(qa) < 1e-9 ? pyDiv(-qc, qb) : pyDiv(-qb + pySqrt(qb * qb - 4 * qa * qc), 2 * qa);
  return pyMin(0.95, pyMax(0.05, u));
}

/**
 * Split a quadratic at `u` (de Casteljau): the first half's control, the
 * point on the curve, and the second half's control.
 */
export function quadSplit(p0: Point, p1: Point, p2: Point, u: number): [Point, Point, Point] {
  const a: Point = [p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u];
  const b: Point = [p1[0] + (p2[0] - p1[0]) * u, p1[1] + (p2[1] - p1[1]) * u];
  return [a, [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u], b];
}

/**
 * The torso's side from the armpit to the waist on side `s`, as path
 * commands continuing from wherever the path is, down or back up.
 *
 * The body and the garments over it draw this one run, so a bust on the body
 * is a bust on the tunic without either keeping its own copy. Without a bust it
 * is one quadratic from the torso's width at the armpit down to the waist. With
 * one it runs down the plain curve to where the bust starts, swells out to the
 * fullest point, which is that curve's own point at `bust_y` moved out by
 * `bust_reach`, comes back in to an under-bust point on the curve, arriving
 * on the diagonal, which is the tuck a bust reads by, and follows the curve's
 * own remainder to the waist (`_bust_shape`). The under-bust point sits `_BUST_DROP` reaches below the fullest
 * point, so as the reach goes to zero the middle piece shrinks to nothing and
 * the other two become the original curve: the bust grows out of this torso
 * rather than jumping to a width of its own (`docs/bust-plan.md`, step 1).
 *
 * At `bust = 0` the single curve is emitted unchanged, character for
 * character, rather than a two-segment form that happens to trace the same
 * path. Splitting a quadratic at a point on it reproduces the curve exactly in
 * geometry and not in the numbers written down, and `ref-out/` compares the
 * numbers: every one of the seventeen presets would have come out "changed"
 * for no visible reason.
 *
 * `inset` pulls the whole run in, for the body under a garment (`_torso`).
 * `drape` is for a loose garment, which hangs from the fullest point rather
 * than following the body back in under it (`_bust_shape`).
 */
export function rib(sk: Skeleton, cx: number, s: number, descending: boolean, inset = 0.0, drape = false): string {
  const torsoAtCuff = torsoAtArmpit(sk) - inset;
  const cuffY = sleeveHemY(sk);
  const ribCtrl = ribCtrlY(sk);
  const ww = sk.waist_half_w - inset;
  const wy = sk.waist_y;
  const bust = bustShape(sk, inset, drape);
  if (bust === null) {
    return truthy(descending)
      ? `Q ${fmt1(cx + s * torsoAtCuff)} ${fmt1(ribCtrl)} ${fmt1(cx + s * ww)} ${fmt1(wy)} `
      : `Q ${fmt1(cx + s * torsoAtCuff)} ${fmt1(ribCtrl)} ` + `${fmt1(cx + s * torsoAtCuff)} ${fmt1(cuffY)} `;
  }

  const q = (ctrl: Point, end: Point): string =>
    `Q ${fmt1(cx + s * ctrl[0])} ${fmt1(ctrl[1])} ${fmt1(cx + s * end[0])} ${fmt1(end[1])} `;

  const pieces = bust.pieces();
  if (truthy(descending)) return pieces.map(([, c, e]) => q(c, e)).join("");
  return [...pieces]
    .reverse()
    .map(([st, c]) => q(c, st))
    .join("");
}

/** The outline as `(start, control, end)` triples, armpit first (`_Bust.pieces`). Works on any object with the two fields. */
export function bustPieces(b: { readonly armpit: Point; readonly outline: readonly (readonly [Point, Point])[] }): [Point, Point, Point][] {
  const starts: Point[] = [b.armpit, ...b.outline.slice(0, -1).map(([, e]) => e)];
  // `zip(..., strict=True)`
  if (starts.length !== b.outline.length) {
    throw new PyError("ValueError", `zip() argument 2 is ${starts.length < b.outline.length ? "longer" : "shorter"} than argument 1`);
  }
  return starts.map((st, i) => {
    const [c, e] = b.outline[i] as readonly [Point, Point];
    return [st, c, e] as [Point, Point, Point];
  });
}

/**
 * The bust's outline on one side, as offsets from the centre line.
 *
 * `outline` is the whole run from `armpit` down to the waist as quadratic
 * pieces, each its control and its end point; `peak` is the fullest point on
 * it. Its first `lobe_pieces` pieces run off the plain curve and the last of
 * them ends back on it, and `plain_up` is the plain curve's control from that
 * end back up to the armpit: together they bound the lobe a bust adds to the
 * torso (`_bust_over_arms`).
 */
export class Bust {
  readonly armpit: Point;
  readonly outline: readonly (readonly [Point, Point])[];
  readonly peak: Point;
  readonly lobe_pieces: number;
  readonly plain_up: Point;

  constructor(armpit: Point, outline: readonly (readonly [Point, Point])[], peak: Point, lobe_pieces: number, plain_up: Point) {
    this.armpit = armpit;
    this.outline = outline;
    this.peak = peak;
    this.lobe_pieces = lobe_pieces;
    this.plain_up = plain_up;
  }

  /** The outline as `(start, control, end)` triples, armpit first. */
  pieces(): [Point, Point, Point][] {
    return bustPieces(this);
  }
}

/**
 * The bust on `_rib`'s curve, or None without one; see `_rib`.
 *
 * `drape` is for a loose garment over the bust rather than the body under it.
 * The body comes back in below the fullest point to the under-bust tuck; cloth
 * does not follow it there, it hangs from the fullest point and is taken in
 * only at the waist (the anatomy review in `docs/bust-plan.md`, step 9b). So
 * a draped side is the plain curve split at the bust with the fullest point
 * and both controls either side of it moved out by the reach: smooth at the
 * fullest point, back on the plain curve at the waist, and the plain curve
 * itself as the reach goes to zero.
 */
export function bustShape(sk: Skeleton, inset = 0.0, drape = false): Bust | null {
  const reach = bustReach(sk);
  if (reach <= 0) return null;
  const torsoAtCuff = torsoAtArmpit(sk) - inset;
  const cuffY = sleeveHemY(sk);
  const ribCtrl = ribCtrlY(sk);
  const ww = sk.waist_half_w - inset;
  const wy = sk.waist_y;
  const ribCurve: [Point, Point, Point] = [
    [torsoAtCuff, cuffY],
    [torsoAtCuff, ribCtrl],
    [ww, wy],
  ];
  const [above0, peak0, fall] = quadSplit(...ribCurve, quadCrossing(...ribCurve, bustY(sk)));
  let above: Point = [above0[0] + reach, above0[1]];
  const peak: Point = [peak0[0] + reach, peak0[1]];
  if (truthy(drape)) {
    // From the armpit to the fullest point on the bare breast's curve, the
    // one `_bare_breast_spine` draws, arriving vertical at the widest point:
    // so the tunic's side and the bare outline agree
    // (`docs/tunic-bust-plan.md`, T3). It was the plain curve moved out by
    // the reach, which left the armpit at the torso's angle and dented above
    // the fullest point. Blended in up to a bust of 0.2, the smallest the
    // cast carries, so a tiny bust still moves the outline a tiny amount.
    const armpit: Point = [armpitX(sk, inset), cuffY];
    const bareCtrl: Point = [peak[0], armpit[1] + (peak[1] - armpit[1]) * 0.5];
    const blend = pyMin(1.0, sk.bust / 0.2); // the divisor is the constant 0.2
    above = [above[0] + (bareCtrl[0] - above[0]) * blend, above[1] + (bareCtrl[1] - above[1]) * blend];
    return new Bust(
      armpit,
      [
        [above, peak],
        [[fall[0] + reach, fall[1]], [ww, wy]],
      ],
      peak,
      2,
      ribCurve[1],
    );
  }
  const underY = underBustY(sk, peak[1]);
  const [plainUp, under, below] = quadSplit(...ribCurve, quadCrossing(...ribCurve, underY));
  // The bust swells straight from the armpit. Starting it lower, below an
  // upper chest, was tried for step 9a and put back: at the chibi there are
  // 0.28 head radii between the armpit and the fullest point and the extra turn
  // pinched into a hook, and at the adult build it read as a knob and is under
  // the arm anyway until that build's own fix pass (`docs/bust-status.md`).
  const lean = pyDiv(peak[0] - above[0], peak[1] - above[1]);
  // Leaves the fullest point along the swell's own tangent, so the join is
  // smooth, and arrives at the under-bust point on the diagonal: the control
  // is where that tangent meets a 45 degree line up and out from the
  // under-bust point. Arriving level made a right-angled shelf against the
  // torso's near-vertical side, which showed as a step below the arm.
  // Back into the torso's side as an S of two quadratics, each control on its
  // end's own tangent a third of the drop along it, meeting midway between the
  // controls: smooth at the fullest point, smooth into the side, no crease.
  // It first arrived at the under-bust point on the diagonal (a control where
  // the fullest point's tangent met a 45 degree line from it), which creased
  // into the side; on the bare body the bust read as a knob stuck on
  // (`docs/bust-plan.md`, step 3c). Arriving level before that made a shelf.
  const drop = under[1] - peak[1];
  const leanUnder = pyDiv(below[0] - under[0], below[1] - under[1]);
  const c1: Point = [peak[0] + lean * drop * 0.35, peak[1] + drop * 0.35];
  const c2: Point = [under[0] - leanUnder * drop * 0.35, under[1] - drop * 0.35];
  const mid: Point = [(c1[0] + c2[0]) / 2, (c1[1] + c2[1]) / 2];
  return new Bust(
    [armpitX(sk, inset), cuffY],
    [
      [above, peak],
      [c1, mid],
      [c2, under],
      [below, [ww, wy]],
    ],
    peak,
    3,
    plainUp,
  );
}

// ---------------------------------------------------------------------------------------------------------
// The line under the bust, on cloth

export const BREAST_GAP = 0.15;
export const BREAST_DEPTH = 1.25;
export const BREAST_STOP = 170.0;

/**
 * `(xc, rx, yp, ry)`: the breast's ellipse, one side, as offsets from the
 * centre line, or None without a bust. Widest at the fullest point, reaching
 * `bust_reach` past the plain side there; its inner edge `_BREAST_GAP` of the
 * way out from the sternum; dropping the fold's depth times `_BREAST_DEPTH`
 * below. The bare breast is drawn on it (`_bare_breast_spine`) and the
 * tunic's line under the bust follows it (`_bust_lines`), so the two agree
 * (`docs/tunic-bust-plan.md`). `min_ry` floors that drop, for a bare breast
 * whose reach is too small to read; the clothed line passes none.
 */
export function breastEllipse(sk: Skeleton, inset: number, min_ry = 0.0): [number, number, number, number] | null {
  const body = bustShape(sk, inset);
  if (body === null) return null;
  const [xOut, yp] = body.peak;
  const xIn = (xOut - bustReach(sk)) * BREAST_GAP;
  const [xc, rx] = [(xOut + xIn) / 2, (xOut - xIn) / 2];
  return [xc, rx, yp, pyMax((underBustY(sk, yp) - yp) * BREAST_DEPTH, min_ry)];
}

/**
 * The line under the bust on cloth, on the bare breast's own ellipse:
 * the tunic's (`_bust_lines`) at full weight on both sides, and a lighter one
 * on a robe's panel over the breast it covers (`_robe_front`). Empty without
 * a bust.
 */
export function bustFold(sk: Skeleton, weight = 1.0, sides: readonly number[] = [-1, 1]): string {
  const ellipse = breastEllipse(sk, 0.0);
  if (ellipse === null) return "";
  const cx = sk.head_cx;
  const sw = strokeW(sk);
  const heaviest = outlineW(sw * 0.95 * pyMin(1.0, sk.bust / 0.5) * weight); // the divisor is the constant 0.5
  // The bare breast's own ellipse (`_breast_ellipse`), from the tunic's side
  // at the fullest point round the bottom and up the inner side, so a
  // figure's bust reads the same with the tunic on or off
  // (`docs/tunic-bust-plan.md`, T2). It was a shallower ellipse of its own,
  // tuned for cloth before the bare breast existed, and drawn over the tunic
  // the bare outline ran lower and rounder on every woman.
  const [xc, rx, yp, ry] = ellipse;
  const stop = radians(BREAST_STOP);
  const steps = 40;
  const spine: Point[] = [];
  for (let k = 0; k < steps + 1; k++) {
    const th = (stop * k) / steps; // steps is the constant 40
    spine.push([xc + rx * pyCos(th), yp + ry * pySin(th)]);
  }
  const n = spine.length - 1;
  const left: Point[] = [];
  const right: Point[] = [];
  spine.forEach(([x, y], k) => {
    const a0 = spine[pyMax(0, k - 1)] as Point;
    const a1 = spine[pyMin(n, k + 1)] as Point;
    const dx = a1[0] - a0[0];
    const dy = a1[1] - a0[1];
    const h = pyHypot(dx, dy);
    const norm = truthy(h) ? h : 1.0;
    // Tapered at both ends, as a fold in cloth is: the silhouette carries
    // the outer edge, and the line leaves it and fades toward the sternum.
    // n is spine.length - 1 = 40, never zero.
    const half = heaviest * 0.5 * pyPow(pyMin(1.0, k / n / 0.18, (1.0 - k / n) / 0.3), 0.8);
    const nx = (-dy / norm) * half;
    const ny = (dx / norm) * half;
    left.push([x + nx, y + ny]);
    right.push([x - nx, y - ny]);
  });
  const ring = [...left, ...[...right].reverse()];
  const parts: string[] = [];
  for (const s of sides) {
    const d = "M " + ring.map(([x, y]) => `${fmt1(cx + s * x)} ${fmt1(y)}`).join(" L ") + " Z";
    parts.push(`<path d="${d}" fill="${OUTLINE}" stroke="none" />`);
  }
  return parts.join("");
}

export const COAT_BUST_LINE = 0.6;

/**
 * The tunic's line under the bust, lighter, on an open coat's panels only:
 * masked to `panels` (path data), so it is not drawn in the opening, where
 * the garment underneath shows its own, nor on a lapel drawn after it. The
 * owner's two conditions (2026-09-26): never on the lapel, and as subtle as
 * the robe's. Empty without a bust.
 */
export function bustPanelLine(sk: Skeleton, panels: readonly string[]): string {
  const line = bustFold(sk, COAT_BUST_LINE);
  if (!line) return "";
  const maskD = panels.join(" ");
  const maskId = "coat-bust-" + sha1Hex(maskD + line).slice(0, 10);
  return (
    `<defs><mask id="${maskId}" maskUnits="userSpaceOnUse" x="0" y="0" ` +
    `width="${fmt0(sk.canvas_w)}" height="${fmt0(sk.canvas_h)}">` +
    panels.map((pd) => `<path d="${pd}" fill="white" />`).join("") +
    `</mask></defs><g mask="url(#${maskId})">${line}</g>`
  );
}

/**
 * The x where a quadratic whose height only increases crosses `y`, or None
 * if it does not.
 */
export function quadXAt(p0: Point, p1: Point, p2: Point, y: number): number | null {
  if (!(p0[1] <= y && y <= p2[1])) return null;
  const qa = p0[1] - 2 * p1[1] + p2[1];
  const qb = 2 * (p1[1] - p0[1]);
  const qc = p0[1] - y;
  let u = Math.abs(qa) < 1e-9 ? pyDiv(-qc, qb) : pyDiv(-qb + pySqrt(qb * qb - 4 * qa * qc), 2 * qa);
  u = pyMin(1.0, pyMax(0.0, u));
  return (1 - u) * (1 - u) * p0[0] + 2 * u * (1 - u) * p1[0] + u * u * p2[0];
}

/**
 * How far a loose garment over the bust stands out from the torso's plain
 * side at height `y`: the traced cuts are all worn loose (`_bust_shape`).
 */
export function bustBulge(sk: Skeleton, y: number): number {
  const b = bustShape(sk, 0.0, true);
  if (b === null) return 0.0;
  let out: number | null = null;
  for (const piece of b.pieces()) {
    out = quadXAt(piece[0], piece[1], piece[2], y);
    if (out !== null) break;
  }
  if (out === null) return 0.0;
  const armpit: Point = [torsoAtArmpit(sk), b.armpit[1]];
  const plain = quadXAt(armpit, [armpit[0], ribCtrlY(sk)], (at(b.outline, -1) as readonly [Point, Point])[1], y);
  return plain !== null ? pyMax(0.0, out - plain) : 0.0;
}

// ---------------------------------------------------------------------------------------------------------
// The skeleton a character stands on

/**
 * The skeleton `p`'s body profile lays over the chibi build, before `waist_shift`. (`body.ts` keeps a private copy it calls from
 * `skeletonFor`; this one is exported so the recorded calls of `_skeleton_at` can be replayed.)
 */
export function skeletonAt(p: CharacterParams): Skeleton {
  const heads = BUILDS.chibi as number;
  let margin = hatHairMargin(p);
  const profile = BODY_TYPES[p.body];
  if (profile === undefined) throw new PyError("KeyError", pyValueRepr(p.body));
  // The hair (and everything else on the head) always draws at the
  // chibi build under a profile, since `BodyProfile.applied` pins
  // `sk.build` back to it below, so it needs the chibi build's own
  // headroom rather than whatever `profile.heads`'s taller figure gets
  // by default. Without this floor a hat-less hairstyle clips flat
  // against the canvas top on a profile taller than chibi (found on
  // Satoshi's `short_crop` under `tall_chibi`,
  // `docs/satoshi-tall-chibi-plan.md` T1); a hat's own floor already
  // covers it for whoever wears one, so this only widens the floor,
  // never narrows it.
  margin = pyMax(margin, defaultHairMargin(heads));
  let sk = buildSkeletonWith({ heads: profile.heads, frame: p.frame, bust: p.bust, min_hair_margin: margin });
  // The chibi's build, computed rather than written as 0.1: every figure's
  // `sk.build` is this value, (2.4 - 2.0) / 4.0 in floating point, and
  // the parts' lerps are evaluated at it exactly.
  const chibi = buildSkeletonWith({ heads, frame: p.frame, bust: p.bust }).build;
  sk = applied(profile, sk, chibi);
  // Not stretched at all at 1.0, rather than stretched by one: the identity in
  // floating point is not exact, and the tall chibi as it is must not move.
  if (p.height !== 1.0) {
    sk = stretched(sk, p.height, (h) => buildSkeletonWith({ heads: h, frame: p.frame, bust: p.bust, min_hair_margin: margin }));
  }
  if (p.face_age > 0.0) sk = replace(sk, { face_maturity: pyMin(1.0, p.face_age) });
  return replace(sk, { limb_taper: limbTaperAt(p.height) });
}

// ---------------------------------------------------------------------------------------------------------
// The traced garment's placement

export const GARMENT_REF_BODY = "tall_chibi";
// The bust, as knots at fixed fractions of the armpit-to-waist run.
export const BUST_KNOTS: readonly number[] = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6];

/**
 * A skeleton's landmark heights and half-widths, in head radii.
 *
 * What a traced garment hangs from: the chin (the neck's width), shoulder,
 * the bust's run, waist, hip and hem, then the ankle and sole below. The knee is left out
 * on purpose: it sits below the hem on a tall body and above it on the
 * shared chibi, and knots have to keep one order on every body.
 */
export function bodyKnots(sk: Skeleton): [number[], number[]] {
  const r = sk.head_r;
  const [sy, wy] = [pyDiv(sk.shoulder_y - sk.head_cy, r), pyDiv(sk.waist_y - sk.head_cy, r)];
  const [sw, ww] = [pyDiv(sk.shoulder_half_w, r), pyDiv(sk.waist_half_w, r)];
  // The bust, as knots at fixed fractions of the armpit-to-waist run, each as
  // wide as the straight shoulder-to-waist line plus what the body's bust adds
  // at that height. At the same fractions on every body, and adding nothing
  // without a bust, they lie on the line the other knots already draw, so they
  // move no cut until a wearer has one; with one, a traced jacket bulges in the
  // bust's own shape rather than to a point (`docs/bust-plan.md`, step 6).
  const armpit = sleeveHemY(sk);
  const waist = sk.waist_y;
  const bustYs: number[] = [];
  const bustWs: number[] = [];
  for (const frac of BUST_KNOTS) {
    const y = armpit + (waist - armpit) * frac;
    const ky = pyDiv(y - sk.head_cy, r);
    bustYs.push(ky);
    bustWs.push(sw + pyDiv((ww - sw) * (ky - sy), wy - sy) + pyDiv(bustBulge(sk, y), r));
  }
  const ys = [
    1.0,
    sy,
    ...bustYs,
    wy,
    pyDiv(sk.hip_y - sk.head_cy, sk.head_r),
    pyDiv(sk.hem_y - sk.head_cy, sk.head_r),
    pyDiv(sk.ankle_y - sk.head_cy, sk.head_r),
    pyDiv(sk.foot_y - sk.head_cy, sk.head_r),
  ];
  const ws = [
    pyDiv(sk.neck_half_w, sk.head_r),
    sw,
    ...bustWs,
    ww,
    pyDiv(sk.hip_half_w, sk.head_r),
    pyDiv(sk.hem_half_w, sk.head_r),
    pyDiv(sk.hem_half_w, sk.head_r),
    pyDiv(sk.hem_half_w, sk.head_r),
  ];
  return [ys, ws];
}

/** Piecewise-linear `ys` over ascending `xs`; past either end, offset one-for-one. */
export function interp(v: number, xs: readonly number[], ys: readonly number[]): number {
  if (v <= at(xs, 0)) return at(ys, 0) + (v - at(xs, 0));
  if (v >= at(xs, -1)) return at(ys, -1) + (v - at(xs, -1));
  for (let i = 0; i < xs.length - 1; i++) {
    if (v <= at(xs, i + 1)) {
      const t = pyDiv(v - at(xs, i), at(xs, i + 1) - at(xs, i));
      return at(ys, i) + t * (at(ys, i + 1) - at(ys, i));
    }
  }
  return at(ys, -1);
}

export function interpFlat(v: number, xs: readonly number[], ys: readonly number[]): number {
  if (v <= at(xs, 0)) return at(ys, 0);
  if (v >= at(xs, -1)) return at(ys, -1);
  return interp(v, xs, ys);
}

/**
 * Map a traced garment's head radii onto `sk`'s body, as a point function.
 *
 * Heights move piecewise between the two bodies' landmarks (`_body_knots`),
 * so a hem traced at the reference's hem lands on this body's hem whatever
 * lies between. Across, each point scales by this body's half-width over
 * the reference's at the same landmark-relative height, so a collar keeps
 * to the neck and a skirt to the hips. Above the chin nothing is scaled: that
 * is the head, which every body shares at one size. The identity on
 * `_GARMENT_REF_BODY` is the test that this is right, not an approximation.
 */
export function garmentPlacement(sk: Skeleton, ref_body: string = GARMENT_REF_BODY): (pt: Point) => Point {
  const [refYs, refWs] = bodyKnots(skeletonFor(characterParams({ body: ref_body })));
  const [ys, ws] = bodyKnots(sk);

  return (pt: Point): Point => {
    const [x, y] = pt;
    if (y <= 1.0) return [pyDiv(x * (ws[0] as number), refWs[0] as number), y];
    const scale = pyDiv(interpFlat(y, refYs, ws), interpFlat(y, refYs, refWs));
    return [x * scale, interp(y, refYs, ys)];
  };
}

// ---------------------------------------------------------------------------------------------------------
// The raised arm and the coat's sleeve

/** How far the arm on side `s` (-1 the viewer's left) is swung out, in degrees. */
export function armSwing(p: CharacterParams, s: number): number {
  return s === -1 ? p.right_arm_out : p.left_arm_out;
}

/**
 * Whether the arm on side `s` is out and the coat's sleeve is part of its silhouette,
 * so the sleeve has to be drawn on the arm and left out of the coat.
 */
export function raisedCoatSleeve(p: CharacterParams, s: number): boolean {
  if (p.outfit.coat_color === null || p.outfit.coat_cut === null) return false;
  return coatCut(p.outfit.coat_cut).arm_lines !== null && armSwing(p, s) !== 0.0;
}

/**
 * Where a raised arm whose coat sleeve is part of the coat's silhouette turns: the shoulder,
 * as `(offset from the centre line, y)` in pixels, on the arm's own line extended up to it.
 * The arm is then as long as the real one, from the shoulder; the sleeve hem it hangs from at
 * rest is far below that.
 */
export function raisedShoulder(sk: Skeleton, p: CharacterParams, s: number): [number, number] | null {
  if (!raisedCoatSleeve(p, s)) return null;
  const cut = coatCut(p.outfit.coat_cut);
  if (cut.shoulder_y === null) throw new PyError("AssertionError", "");
  const y = sk.head_cy + garmentPlacement(sk, cut.ref_body)([0.0, cut.shoulder_y])[1] * sk.head_r;
  const [centreTop, topY, centreWrist, wristY] = armLine(sk);
  return [centreTop + pyDiv(centreWrist - centreTop, wristY - topY) * (y - topY), y];
}

export const SLEEVE_CUT_ID = "sleeve-cutaway";

export const RAISED_ARM_INTO_BODY = 0.5;

export function tracedCoat(_sk: Skeleton, p: CharacterParams): boolean {
  return p.outfit.coat_color !== null && p.outfit.coat_cut !== null;
}

// ---------------------------------------------------------------------------------------------------------
// Drawing a traced cut

/**
 * `weight` scales the outline, for small hardware whose own parts are
 * thinner than the figure's line (a buckle's frame). `xf` replaces the
 * placement, for a cut that is not hung off the torso (`_draw_leg_cut`).
 * `fills_clip` is the id of a clip path for the fills, not the lines; `skip_lines` are the
 * indexes of lines left out.
 */
export function drawCut(
  sk: Skeleton,
  cut: GarmentCut,
  fill: string,
  weight = 1.0,
  xf: ((pt: Point) => Point) | null = null,
  fills_clip: string | null = null,
  skip_lines: ReadonlySet<number> | null = null,
): string {
  const [cx, cy, r] = [sk.head_cx, sk.head_cy, sk.head_r];
  const sw = strokeW(sk) * weight;
  const place = xf === null ? garmentPlacement(sk, cut.ref_body) : xf;

  const d = (chain: Chain, close = true): string => {
    const [start, segs] = chain;
    return curve(cx, cy, r, place(start), segs.map(([c, e]): Segment => [place(c), place(e)]), close);
  };

  const tone = (i: number): string => {
    const k = i < cut.shades.length ? (cut.shades[i] as number | null) : null;
    return k === null ? fill : shade(fill, k);
  };

  /** One fill, with the cut's holes for it as extra subpaths: under the even-odd rule they are left open. */
  const fillPath = (i: number, shape: Chain): string => {
    const mine = cut.holes.filter(([j]) => j === i).map(([, h]) => h);
    const data = [d(shape), ...mine.map((h) => d(h))].join(" ");
    const rule = mine.length > 0 ? ' fill-rule="evenodd"' : "";
    return `<path d="${data}" fill="${tone(i)}"${rule} ` + `stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw))}" />`;
  };

  let parts = cut.fills.map((shape, i) => fillPath(i, shape));
  if (cut.bust_line_after !== null) {
    const n = cut.bust_line_after;
    const line = bustPanelLine(
      sk,
      cut.fills.slice(0, n).map((shape) => d(shape)),
    );
    parts.splice(n, 0, line);
  }
  if (truthy(fills_clip)) {
    parts = [`<g clip-path="url(#${fills_clip})">`, ...parts, "</g>"];
  }
  cut.lines.forEach((line, i) => {
    if (truthy(skip_lines) && (skip_lines as ReadonlySet<number>).has(i)) return;
    parts.push(
      `<path d="${d(line, false)}" fill="none" stroke="${OUTLINE}" ` +
        `stroke-width="${fmt2(interiorW(sw, cut.line_weight))}" stroke-linecap="round" />`,
    );
  });
  return parts.join("");
}

// ---------------------------------------------------------------------------------------------------------
// The skirt's measures

/**
 * Half-width of an A-line skirt at a given height. The flare angle comes
 * from the skeleton's own hip and hem anchors, so a longer skirt flares
 * further instead of needing a width of its own.
 */
export function skirtHalfW(sk: Skeleton, y: number): number {
  const span = sk.hem_y - sk.hip_y;
  if (span <= 0) return sk.hip_half_w;
  // span is above zero here (or nan, which divides without raising in Python too).
  return sk.hip_half_w + ((sk.hem_half_w - sk.hip_half_w) * (y - sk.hip_y)) / span;
}

/**
 * Where a skirt ends. `length` is measured hip (0) to ankle (1); None takes
 * the skeleton's own hem anchor, which is where a hem sits when nobody asks
 * for anything in particular.
 *
 * A requested length used to be pulled back toward the skeleton's own,
 * shorter hem at low builds, floored at half strength rather than running
 * all the way down to `sk.build` (0.1 at chibi): task #103's report was that
 * at full `sk.build` strength, two lengths as far apart as 0.60 and 0.95 land
 * within four pixels of each other. The floor-at-half compromise, the
 * owner's pick on 2026-08-10, fixed Reika's hakama without going as far as
 * removing the pull-back outright, on the read that doing so would swallow a
 * chibi's short legs and read as a bell with no limbs underneath.
 *
 * That read turned out not to hold once it was rendered rather than assumed.
 * Docs Phase 6 task 32 found a real bare-leg gap the floor-at-half left
 * behind, between the hem and the boot tops, on Satoko and Keiko at their
 * shipped lengths (0.70, 0.82); removing the pull-back entirely closed it
 * with no bell, no swallowed legs, checked across the whole range in
 * `harness/hem/pullback.py`'s own four references (0.60 to 0.95) and at the
 * literal extreme, `skirt_length=1.0`. So there is no hidden pull-back: a
 * requested `length` lands exactly, at every build, the plain reading of
 * "length is measured hip to ankle" the docstring already promised.
 *
 * `length_chibi`, added the same day, is the opt-in way to still want two
 * different lengths at the two ends of the build range: `None` (every
 * character but the four the owner asked to keep their pre-task-32 chibi
 * silhouette) leaves `length` alone at every build. Set, it is what
 * `length` blends *from* at the chibi end, linearly against `sk.build`,
 * the same shape of idea `Hairstyle.volume` already uses for a chibi
 * wearing more hair than an adult on the same head. Unlike the old
 * pull-back, this is a stated choice per character rather than a hidden
 * rule applied to everyone: `skirt_length` still means what it says unless
 * a character's preset opts into a second number.
 */
export function skirtHemY(sk: Skeleton, length: number | null, length_chibi: number | null = null): number {
  if (length === null) return sk.hem_y;
  if (length_chibi !== null) length = length_chibi + (length - length_chibi) * sk.build;
  return sk.hip_y + length * (sk.ankle_y - sk.hip_y);
}

// ---------------------------------------------------------------------------------------------------------
// A traced sleeve and the arm's line

/** A `SleeveCut`'s placement on `sk`'s hanging arm on side `s`, head radii in and out, before any swing. */
export function sleevePlacement(sk: Skeleton, cut: SleeveCut, s: number): (pt: Point) => Point {
  const [, , centreWrist, wristY] = armLine(sk);
  const [px, py] = garmentPlacement(sk)(cut.pivot);
  const [wx, wy] = [pyDiv(centreWrist, sk.head_r), pyDiv(wristY - sk.head_cy, sk.head_r)];
  const [rax, ray] = [cut.wrist[0] - cut.pivot[0], cut.wrist[1] - cut.pivot[1]];
  const refLen = pyHypot(rax, ray);
  const [tax, tay] = [wx - px, wy - py];
  const tgtLen = pyHypot(tax, tay);
  const acrossScale = pyDiv(pyDiv(sk.arm_half_w, sk.head_r), cut.half_w);

  return (pt: Point): Point => {
    const [dx, dy] = [pt[0] - cut.pivot[0], pt[1] - cut.pivot[1]];
    const along = pyDiv(dx * rax + dy * ray, refLen * refLen);
    const across = pyDiv(-dx * ray + dy * rax, refLen) * acrossScale;
    const x = px + along * tax - pyDiv(across * tay, tgtLen);
    const y = py + along * tay + pyDiv(across * tax, tgtLen);
    return [s * x, y];
  };
}

/**
 * `(centre_top, top_y, centre_wrist, wrist_y)` of a hanging arm.
 *
 * The x values are offsets from `sk.head_cx`, outward, for either side; y is
 * absolute. The top is the sleeve hem's centre, which is also the pivot a
 * swung arm turns about.
 */
export function armLine(sk: Skeleton): [number, number, number, number] {
  const outTop = sleeveHalfW(sk) * 0.86;
  const centreTop = outTop - sk.arm_half_w;
  // Arms drift outward on the way down, so daylight opens between forearm and
  // waist. The drift lives in the forearm: the upper arm hangs near vertical
  // and the bend happens at the elbow, which is what the canon's arms do and
  // what a straight slant from shoulder to wrist failed to read as. The
  // chibi keeps a modest drift of its own now: the canon's chibi hands hang
  // beside the skirt, not against it.
  let centreWrist = centreTop + sk.arm_half_w * (0.5 + 0.7 * sk.build);
  let wristY = sk.hip_y + sk.arm_half_w * 0.8;
  // A body profile that measured where the hand begins says so (`BodyProfile.wrist_y`).
  if (sk.wrist_x !== null) centreWrist = sk.wrist_x;
  if (sk.wrist_y !== null) wristY = sk.wrist_y;
  return [centreTop, sleeveHemY(sk), centreWrist, wristY];
}

export function handLength(sk: Skeleton): number {
  // Sized to land the canon's hand, about 0.10 of head width at chibi. The
  // factor absorbs the arm it hangs off: when the chibi arm slimmed from
  // 0.22 to 0.14 head radii this went up to keep the hand itself the same.
  return sk.arm_half_w * (1.35 + 1.1 * sk.build);
}

export function wornSleeve(_sk: Skeleton, p: CharacterParams): SleeveCut | null {
  const named = p.outfit.sleeve_cut;
  const key: unknown = truthy(named) ? named : "";
  // `dict.get` of a list is an unhashable key; any other value is simply not a name.
  if (Array.isArray(key)) throw new PyError("TypeError", "unhashable type: 'list'");
  return typeof key === "string" && Object.hasOwn(SLEEVE_CUTS, key) ? (SLEEVE_CUTS[key] as SleeveCut) : null;
}

/**
 * Where an arm on side `s` turns when swung, in canvas px.
 *
 * The sleeve hem's centre for a plain arm; the placed shoulder joint when a
 * traced sleeve is worn, whose cap is a disc about it.
 */
export function armPivot(sk: Skeleton, p: CharacterParams, s: number): [number, number] {
  const cut = wornSleeve(sk, p);
  if (cut === null) {
    const shoulder = raisedShoulder(sk, p, s);
    if (shoulder !== null) return [sk.head_cx + s * shoulder[0], shoulder[1]];
    const [centreTop, topY] = armLine(sk);
    return [sk.head_cx + s * centreTop, topY];
  }
  const [jx, jy] = sleevePlacement(sk, cut, s)(cut.pivot);
  return [sk.head_cx + jx * sk.head_r, sk.head_cy + jy * sk.head_r];
}

// ---------------------------------------------------------------------------------------------------------
// The legs' and the belt's shared measures

/**
 * `(gap, w_top)`: how far each leg's centre hangs from the centre line, and
 * its half-width at the top. Shared by the legs and by the belt, which has to
 * cover the trousers' top corners.
 *
 * Where the legs hang. At a tall build the outer edge of the thigh lands on
 * the hip, which is what the tunic's own hem is drawn to, so the body's side
 * carries straight on down into the leg instead of the trousers overhanging
 * it. Since the hip rides on `frame`, a narrow-hipped figure's legs come in
 * and a wider-hipped one's go out, which is the frame doing its job.
 *
 * A chibi keeps its legs tucked in close instead: its hips are nearly as wide
 * as an adult's in head radii while its legs are notably thinner, so
 * hanging them off the hip would splay them to the corners of the body.
 *
 * However the legs are covered, the boots go in the same two places, so the
 * gap floor is shared rather than duplicated per branch. The reference leaves
 * each inner edge about 0.09 head radii off centre, which is where the
 * presets land without the floor biting.
 */
export function legGapAndTop(sk: Skeleton, trousers: boolean): [number, number] {
  const taper = sk.build;
  const thigh = truthy(trousers) ? 1.1 + 0.16 * taper : 1.0 + 0.12 * taper;
  const wTop = sk.leg_half_w * thigh;
  const tuck = sk.leg_half_w * 1.45;
  let gap = tuck + (sk.hip_half_w - wTop - tuck) * taper;
  gap = pyMax(gap, wTop + sk.leg_half_w * 0.2);
  return [gap, wTop];
}

/** The build the arms and legs taper at. */
export function limbBuild(sk: Skeleton): number {
  return sk.build + sk.limb_taper * (1.0 - sk.build);
}

/**
 * How wide the body is where the belt-hung pieces (a sash, an apron, the
 * pouches) are sized, as a half-width.
 *
 * The waist on the shared chibi, which barely has one: it is about as wide as
 * the hip, and those pieces were fitted to it. A body with a real waist and
 * wider hips (`tall_chibi`, Katherina's measured slim waist) leaves them sized
 * off a width narrower than the figure they hang on, so a sash comes out a box,
 * an apron a tall strip and the pouches crowd its corners. There they take the
 * width from the hip instead, at the same ratio the chibi has between the two.
 */
export function beltLineHalfW(sk: Skeleton): number {
  return pyMax(sk.waist_half_w, sk.hip_half_w * 0.9);
}

/**
 * Where the belt sits and how deep it is, as (top y, height).
 *
 * Shared rather than computed where it is needed, because three parts depend
 * on it now: the belt draws it, a tucked tunic ends inside it, and trousers
 * start inside it. Two of those only work while all three agree, and the
 * failure is a band of bare canvas at the waist.
 *
 * `scale` is how an obi is drawn: the same band three or four times as deep,
 * growing about its own centre so the waist does not move. Only `_belt` passes
 * it. The tucked tunic and the trousers deliberately keep asking for the plain
 * band, because their join has to land where a belt of any depth covers it, and
 * the unscaled midpoint is inside every scaled band by construction.
 */
export function beltBand(sk: Skeleton, scale = 1.0): [number, number] {
  const base = (sk.hip_y - sk.waist_y) * 0.42;
  let h = base * pyMax(0.2, scale);
  if (scale > 1.6) {
    // A sash is a wide flat band: its depth follows the waist-to-hip distance,
    // which is a sliver on the shared chibi and most of a head radius on a body
    // with a real waist, so on that one it came out a box. Capped by its own
    // width, at the width-to-depth the cast's sashes have on the chibi (4.8 to
    // 6), and never thinner than the plain belt.
    h = pyMax(base, pyMin(h, (2 * beltLineHalfW(sk) * 1.03) / 3.4));
  }
  return [sk.waist_y - h * 0.35, h];
}
