// The garments: the tunic, the coat (plain and traced) and its cutaway, the belt, the collar, the robe front and the small
// pieces worn on the torso (placket, pockets, strap, apron, pouches, crystal harness, shoulder bars, ribbon). Port of the
// `parts-garments` module of character.py (see `harness/ts_port/modules.json`). Names are the Python ones in camelCase and
// every expression keeps Python's evaluation order, since a different order rounds differently. Numbers reach the text only
// through the `fmt*` kernel functions. The traced tables (`COLLAR_CUTS`, `BELT_CUTS`, `RIBBON_CUT`, `HIP_POCKET_CUT`,
// `COAT_BUTTONS`) are in `garments-tables.ts`.
//
// Type notes (the registry in `params.ts` says which a field is): `shoulder_bars` and `shoulder_bars_side` are ints, every other
// number is a float. A wrong-typed number field arrives as a `BadValue` and raises `TypeError` where Python's arithmetic or
// comparison on it would; a flag is tested with `truthy`.

import { OUTLINE, interiorW, outlineW, quadPoint, strokeW } from "./character.ts";
import { shade } from "./colorutil.ts";
import {
  armPivot,
  armSwing,
  beltBand,
  beltLineHalfW,
  bustBulge,
  bustFold,
  bustPanelLine,
  armpitX,
  capTipX,
  coatCut,
  drawCut,
  garmentPlacement,
  legGapAndTop,
  raisedCoatSleeve,
  rib,
  shoulderSlope,
  skirtHalfW,
  skirtHemY,
  sleeveHalfW,
  sleeveHemY,
  sleeveUnderCap,
  torsoAtArmpit,
  tracedCoat,
  SLEEVE_CUT_ID,
} from "./core-limbs.ts";
import { handsAfterCoat } from "./core-limbs-arms.ts";
import type { GarmentCut } from "./core-limbs-tables.ts";
import { BELT_CUTS, COAT_BUTTONS, COLLAR_CUTS, HIP_POCKET_CUT, RIBBON_CUT } from "./garments-tables.ts";
import type { BeltCut } from "./garments-tables.ts";
import type { CharacterParams } from "./params.ts";
import { pyValueRepr } from "./pyvalue.ts";
import {
  PyError,
  at,
  copysign,
  degrees,
  fmt1,
  fmt2,
  pyDiv,
  pyHypot,
  pyMax,
  pyMin,
  pySum,
  pyCos,
  pySin,
  pyStrRepr,
  radians,
  truthy,
} from "./pynum.ts";
import type { Skeleton } from "./skeleton.ts";
import type { Chain, Point, Segment } from "./tables.ts";

/** `str(x)` of a colour field that may hold a wrong-typed value: a string as it is, anything else as Python prints it (`5`, `True`, `['#fff']`). */
const col = (v: unknown): string => (typeof v === "string" ? v : pyValueRepr(v));

/** `TABLE[name]`: a name that is not in the table is Python's `KeyError`, an unhashable one its `TypeError`. */
function tableGet<T>(table: Readonly<Record<string, T>>, name: unknown): T {
  if (Array.isArray(name)) throw new PyError("TypeError", "unhashable type: 'list'");
  if (typeof name !== "string" || !Object.hasOwn(table, name)) {
    throw new PyError("KeyError", name === null || typeof name !== "string" ? "None" : pyStrRepr(name));
  }
  return table[name] as T;
}

// ---------------------------------------------------------------------------------------------------------
// The tunic

/**
 * The torso garment, shoulder to hip, with its own short sleeves.
 *
 * Reads the waist anchor rather than running straight from shoulder to hem,
 * which is what stops a tall build from coming out as a box: a chibi still
 * widens all the way down, an adult takes in and back out.
 *
 * The sleeve is part of this silhouette rather than a shape laid over it. Drawn
 * as its own capsule with its own closed outline it read as a shoulder pad
 * bolted to the chest, because a garment's seam is not a contour. Here the
 * outline runs neck, down the sloped shoulder, out to the sleeve, down its
 * outside, then steps in at the hem and carries on down the torso, so the whole
 * upper body is one continuous edge.
 */
export function tunic(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.tunic_color === null) return "";
  const cx = sk.head_cx;
  const [ww, hwInit] = [sk.waist_half_w, sk.hip_half_w];
  let hw = hwInit;
  const [sy, wy] = [sk.shoulder_y, sk.waist_y];
  let hy = sk.hip_y;
  if (truthy(p.outfit.tunic_tucked)) {
    // Tucked in: the hem stops half way into the belt band rather than
    // carrying on to the hip, so the belt covers the join from both sides
    // and the garment below rises to the same line. Drawn to the hip and
    // relying on z-order instead, the tunic would simply paint over the top
    // of the trousers, because it is stacked above them.
    const [beltY, beltH] = beltBand(sk);
    hy = beltY + beltH * 0.5;
    // A shade over the waist's own width, so the short run below the waist
    // reads as cloth gathered into the belt rather than as a taper.
    hw = ww * 1.01;
  }
  // How deep the neckline cuts. A working tunic wears an open V; a garment
  // with a standing collar closes at the throat, so the V shrinks to a seam
  // the collar then covers. Left at 0.8 under a collar, the V's outline pokes
  // out below the collar's lower edge and reads as a second neckline.
  let notch = sk.neck_half_w * (truthy(p.outfit.collar_color) ? 0.28 : 0.8);
  if (p.outfit.collar_color !== null && p.outfit.collar_cut !== null) {
    // A traced collar opens in a V onto the throat; the tunic's own neckline
    // has to sit behind its wings, or its edges show in that V above the
    // collar's back band.
    notch = sk.head_r * 0.19;
  }
  if (p.outfit.neckline_notch !== null) {
    notch = sk.head_r * p.outfit.neckline_notch;
  }
  let sleeveW = sleeveHalfW(sk);
  // A coat worn over the tunic hides its short sleeve at the shoulder. The
  // coat's own shoulder reaches `_sleeve_half_w(sk) * 0.92` (see `_coat`) and
  // its top edge starts below the tunic sleeve's tip, so at full width the
  // tunic sleeve pokes a wedge out past the coat and above the arm drawn last.
  // It is invisible when the tunic and coat tones are close (every coat preset
  // to date) and obvious when they contrast. Pull the sleeve in under the
  // coat's shoulder so the coat, and the arm below it, cover it completely.
  if (p.outfit.coat_color !== null) {
    sleeveW = sleeveHalfW(sk) * 0.9;
  }
  const cuffY = sleeveHemY(sk);
  // Shoulders slope. A horizontal shoulder line is what made the sleeve look
  // bolted on even once it was the right shape. 0.14 was not enough of it: the
  // canon's shoulder leaves the neck already going down as well as out, and at
  // 0.14 ours held its height across most of the span and then dropped at the
  // end, which is a horizontal cap with a corner on it rather than a slope.
  const slope = shoulderSlope(sk);
  // The torso's own width where the sleeve leaves it. Measured up from the
  // waist, not down from the shoulder: `shoulder_half_w` is the span across the
  // deltoids, so a ribcage derived from it comes out wider than the arm hanging
  // in front of it, and the arm then covers the body's side contour instead of
  // standing clear of it. Both refs show the torso's side and the arm as two
  // separate edges with daylight between them below the armpit.
  const torsoAtCuff = armpitX(sk);
  if (tracedCoat(sk, p)) {
    // Under a traced jacket the tunic's own sleeve cap has nowhere to show but
    // past the jacket's shoulder, where the hair is narrower than the
    // reference's; the traced sleeve starts inside the armhole instead.
    // The plain width, not the bust's armpit: under the jacket it shows
    // nowhere, and the shoulder above it has no reason to move.
    sleeveW = torsoAtArmpit(sk);
  }
  const slanted = sleeveUnderCap(sk, p);
  let tipRound: [Point, Point] = [
    [0.0, 0.0],
    [0.0, 0.0],
  ];
  if (slanted) {
    sleeveW = capTipX(sk);
    // The tip is a corner with a small round on it, not a point: the shoulder
    // arrives nearly level and the underside leaves down and in, and left
    // sharp the join reads as a spike. The round starts `k` back along each
    // edge, with the tip itself as the control.
    const k = sk.head_r * 0.1;
    const under: Point = [torsoAtCuff - sleeveW, cuffY - (sy + slope)];
    const norm = pyHypot(under[0], under[1]);
    tipRound = [
      [sleeveW - k, sy + slope - k * 0.15],
      [sleeveW + pyDiv(under[0], norm) * k, sy + slope + pyDiv(under[1], norm) * k],
    ];
  }

  // Control points sit at the shoulder's own width and the hip's own width, so
  // the curve leaves each landmark vertically and the taper reads as a body
  // rather than as a cone.
  const hipCtrlY = hy - (hy - wy) * 0.45;

  /** Neck to the outer tip of the sleeve, then down the sleeve's outside. */
  const shoulder = (s: number): string => {
    // The control sits half way out and most of the way down, so the edge
    // leaves the neck descending and arrives at the sleeve's tip nearly
    // horizontal. Putting it far out and barely down, which is what was here,
    // gives the opposite: a flat run and then a corner.
    //
    // From the tip down to the step in toward the arm, one quarter-round Q
    // rather than a bulge-then-fillet chain: the control point sits directly
    // below the tip, at the step's own height, so the curve leaves the tip
    // vertical and arrives at `torso_at_cuff` already moving horizontally.
    // That was tried as three separate curves first (an outward bulge down
    // the sleeve, then a fillet rounding a flat step), and read as a wobble,
    // two bends of opposite sense back to back, once both were in the same
    // short run. One arc reads as a hem; a bulge and a fillet chained
    // together reads as neither.
    if (slanted) {
      const [ax, ay] = tipRound[0];
      const [bx, by] = tipRound[1];
      return (
        `Q ${fmt1(cx + s * sleeveW * 0.5)} ${fmt1(sy + slope * 0.62)} ${fmt1(cx + s * ax)} ${fmt1(ay)} ` +
        `Q ${fmt1(cx + s * sleeveW)} ${fmt1(sy + slope)} ${fmt1(cx + s * bx)} ${fmt1(by)} ` +
        `L ${fmt1(cx + s * torsoAtCuff)} ${fmt1(cuffY)} `
      );
    }
    return (
      `Q ${fmt1(cx + s * sleeveW * 0.5)} ${fmt1(sy + slope * 0.62)} ` +
      `${fmt1(cx + s * sleeveW)} ${fmt1(sy + slope)} ` +
      `Q ${fmt1(cx + s * sleeveW)} ${fmt1(cuffY)} ` +
      `${fmt1(cx + s * torsoAtCuff)} ${fmt1(cuffY)} `
    );
  };

  const down = (s: number): string =>
    // A tunic is worn loose: it hangs from the bust (`_bust_shape`).
    rib(sk, cx, s, true, 0.0, true) + `Q ${fmt1(cx + s * hw)} ${fmt1(hipCtrlY)} ${fmt1(cx + s * hw)} ${fmt1(hy)} `;

  const up = (s: number): string =>
    `Q ${fmt1(cx + s * hw)} ${fmt1(hipCtrlY)} ${fmt1(cx + s * ww)} ${fmt1(wy)} ` + rib(sk, cx, s, false, 0.0, true);

  const stand = truthy(p.outfit.neckline_stand) && p.outfit.collar_color === null && !truthy(p.outfit.neckline_round);
  // The stand collar's measures, from the reference's own: the V opens at the
  // neck's width and runs 0.30 head radii deep, and each tab is about 0.09 wide
  // and stands 0.06 above the shoulder line.
  const nw = sk.neck_half_w;
  const [tabW, tabH] = [sk.head_r * 0.09, sk.head_r * 0.06];
  const vDepth = sk.head_r * 0.3;
  const neckEnd: Point = stand ? [nw + tabW, sy - tabH] : [notch, sy];

  /** The mirror of `shoulder`, cuff back up to the neck. */
  const shoulderUp = (s: number): string => {
    const rise = slanted
      ? `L ${fmt1(cx + s * tipRound[1][0])} ${fmt1(tipRound[1][1])} ` +
        `Q ${fmt1(cx + s * sleeveW)} ${fmt1(sy + slope)} ${fmt1(cx + s * tipRound[0][0])} ${fmt1(tipRound[0][1])} `
      : `Q ${fmt1(cx + s * sleeveW)} ${fmt1(cuffY)} ${fmt1(cx + s * sleeveW)} ${fmt1(sy + slope)} `;
    return (
      rise +
      `Q ${fmt1(cx + s * sleeveW * 0.62)} ${fmt1(sy + slope * 0.3)} ` +
      `${fmt1(cx + s * neckEnd[0])} ${fmt1(neckEnd[1])} `
    );
  };

  // The V is two straight edges meeting at a point. A round neckline is the
  // same two endpoints, `(cx+notch, sy)` and `(cx-notch, sy)`, joined by one
  // curve instead: a control point twice as deep as the V's own point so the
  // curve's midpoint (which a quadratic always pulls back toward the
  // endpoints' height) lands at the same depth the V cuts to, rather than
  // reading shallower for no stated reason.
  let closing = truthy(p.outfit.neckline_round)
    ? `Q ${fmt1(cx)} ${fmt1(sy + notch * 2.0)} ${fmt1(cx - notch)} ${fmt1(sy)} Z`
    : `L ${fmt1(cx)} ${fmt1(sy + notch)} Z`;
  if (stand) {
    // Right tab's top, down its inner side (which lies on the neck's own
    // contour), the V's two edges through its point, and up the left tab.
    closing =
      `L ${fmt1(cx + nw)} ${fmt1(sy - tabH)} L ${fmt1(cx + nw)} ${fmt1(sy)} ` +
      `L ${fmt1(cx)} ${fmt1(sy + vDepth)} L ${fmt1(cx - nw)} ${fmt1(sy)} ` +
      `L ${fmt1(cx - nw)} ${fmt1(sy - tabH)} Z`;
  }
  const d =
    `M ${fmt1(cx - neckEnd[0])} ${fmt1(neckEnd[1])} ` +
    shoulder(-1) +
    down(-1) +
    `L ${fmt1(cx + hw)} ${fmt1(hy)} ` +
    up(1) +
    shoulderUp(1) +
    closing;
  const fill = p.outfit.tunic_color;
  let shape = `<path d="${d}" fill="${col(fill)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)))}" />`;
  if (
    p.outfit.undersleeve_color !== null &&
    p.outfit.collar_color === null &&
    truthy(p.outfit.neckline_trim) &&
    !stand
  ) {
    // The undersleeve shows once more at the neckline: a sliver of its tone
    // trimming the V, which both canon builds wear. Drawn just inside the
    // notch so the tunic's own outline still bounds it. Not under a collar,
    // where there is no V left to trim.
    const notchT = notch * 0.78;
    const trim = truthy(p.outfit.neckline_round)
      ? // Same curve the neckline itself uses, pulled in to the trim's own
        // narrower width rather than traced as a fresh shape, so a round
        // collar's trim agrees with the collar it sits inside of.
        `<path d="M ${fmt1(cx - notchT)} ${fmt1(sy + notch * 0.1)} ` +
        `Q ${fmt1(cx)} ${fmt1(sy + notchT * 2.0)} ${fmt1(cx + notchT)} ${fmt1(sy + notch * 0.1)}` +
        `" fill="none" stroke="${col(p.outfit.undersleeve_color)}" ` +
        `stroke-width="${fmt2(outlineW(strokeW(sk), 0.9))}" />`
      : `<path d="M ${fmt1(cx - notchT)} ${fmt1(sy + notch * 0.1)} L ${fmt1(cx)} ${fmt1(sy + notchT)} ` +
        `L ${fmt1(cx + notchT)} ${fmt1(sy + notch * 0.1)}" fill="none" ` +
        `stroke="${col(p.outfit.undersleeve_color)}" stroke-width="${fmt2(outlineW(strokeW(sk), 0.9))}" />`;
    shape += trim;
  }
  return shape;
}

// ---------------------------------------------------------------------------------------------------------
// The robe front and the open coat

// How much an outer layer answers a bust (`docs/tunic-bust-plan.md`, outer
// layers; the owner's calls, 2026-09-26): an open coat's front edges bow out by
// this share of the tunic's drape, and a robe front carries the tunic's line
// under the breast it covers at this share of its weight.
export const COAT_BUST_BOW = 1.0;
export const ROBE_BUST_LINE = 0.6;

/**
 * A kimono's crossed front: one panel laid over the other, right under left.
 *
 * The tunic underneath keeps the silhouette; this only changes what the front
 * of it says. That is the whole trick at this size, and it is why the robe
 * cluster did not need a garment of its own: a torso is a torso, and what makes
 * one a kimono is the diagonal where the two panels meet.
 *
 * Drawn as one filled panel with a diagonal top edge rather than two panels
 * with a seam. Two would be the honest construction and would put a line down
 * the middle of the chest, which is what a *coat* does; a kimono's visible
 * edge runs from the far shoulder down to the near hip, and only one of them
 * shows because the other is underneath.
 */
export function robeFront(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.robe_color === null) return "";
  const cx = sk.head_cx;
  const color = p.outfit.robe_color;
  const sw = strokeW(sk);
  const [sy, wy] = [sk.shoulder_y, sk.waist_y];
  const [beltY] = beltBand(sk);
  const ww = sk.waist_half_w;
  const neck = sk.neck_half_w * 0.62;
  // The overlapping panel: from the wearer's right shoulder, across the chest,
  // down to the left hip. Its far edge follows the torso, so it cannot show
  // outside the tunic it is laid on.
  const torsoAtShoulder = sleeveHalfW(sk) * 0.8;
  const d =
    `M ${fmt1(cx - neck)} ${fmt1(sy + sk.neck_half_w * 0.45)} ` +
    `L ${fmt1(cx - torsoAtShoulder)} ${fmt1(sy + (wy - sy) * 0.22)} ` +
    `Q ${fmt1(cx - torsoAtShoulder)} ${fmt1(wy)} ${fmt1(cx - ww)} ${fmt1(beltY)} ` +
    `L ${fmt1(cx + ww * 0.72)} ${fmt1(beltY)} ` +
    `Z`;
  // The fold's own edge, drawn as a line rather than left as a fill boundary:
  // panel and tunic can be the same colour on a character who wears one robe,
  // and then the diagonal is the only thing saying anything crossed at all.
  const fold =
    `<path d="M ${fmt1(cx - neck)} ${fmt1(sy + sk.neck_half_w * 0.45)} ` +
    `L ${fmt1(cx + ww * 0.72)} ${fmt1(beltY)}" fill="none" stroke="${OUTLINE}" ` +
    `stroke-width="${fmt2(interiorW(sw, 0.8))}" stroke-linecap="round" />`;
  // Over a bust, the tunic's line under the breast the panel covers, the whole
  // curve, lighter: a robe tied with an obi sits close, and with the line only
  // on the uncovered breast (the tunic's, beside the panel) she read lopsided
  // (`docs/tunic-bust-plan.md`, outer layers; the owner's call, 2026-09-26).
  // Bowing the diagonal over the breast was tried and dropped: it kinked, and
  // smoothed it wobbled.
  const line = bustFold(sk, ROBE_BUST_LINE, [-1]);
  return `<path d="${d}" fill="${col(color)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw, 0.7))}" />${fold}${line}`;
}

// How far the lapel rises to meet the neck, and how far out from it, both as
// multiples of `neck_half_w`. Named because they were found by rendering a grid
// against `ref/keiko.png`, not picked from the geometry: see `harness/coat/lapel.py`.
export const COAT_LAPEL_OUT = 1.7;
export const COAT_LAPEL_UP = 1.8;

/**
 * An outer layer hanging open, as two panels with the body between them.
 *
 * Two panels rather than one shape with a hole in it, which is what makes it
 * read as *open*: each has its own outline, and the gap between them shows
 * whatever is worn underneath. A single silhouette with a slit drawn on it is
 * a coat that is done up, however the slit is coloured.
 *
 * One garment covers Tomohiro's cropped jacket, Keiko's lab coat and Kyoko's
 * long coat, because those three differ only in where the hem lands, which is
 * `coat_length`. Building three would have meant three sets of the same
 * mistakes.
 *
 * The panels flare on the way down, following the skirt's own flare so a coat
 * and a skirt worn together do not disagree about which way cloth hangs, and
 * they leave the arms alone: sleeves are the undersleeve's job, and a coat
 * sleeve drawn here would land underneath the arm that is drawn after it.
 *
 * Each panel's top used to run in one line straight from the throat to the
 * shoulder point, which never touches the neck at all: that line sits at or
 * below the shoulder height the whole way, so the strip of shoulder next to the
 * neck was bare skin on both sides and the two panels read as separate wedges
 * resting on the chest rather than one garment worn from the shoulders down.
 * The lapel point added between them is what a collar is drawn as everywhere
 * else in this file, cloth hugging the side of the neck, and it is what says
 * the two panels are the same coat rather than two.
 */
export function coat(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.coat_color === null) return "";
  if (tracedCoat(sk, p)) {
    return ""; // drawn over the arms, by `_traced_coat_and_belt`
  }
  const cx = sk.head_cx;
  const color = p.outfit.coat_color;
  const sw = strokeW(sk);
  const sy = sk.shoulder_y;
  const hemY = sy + (sk.ankle_y - sy) * pyMax(0.0, pyMin(1.0, p.outfit.coat_length));
  const shoulderW = sleeveHalfW(sk) * 0.92;
  // The opening: narrow at the throat, wider at the hem, which is how an
  // unfastened coat hangs. Level edges read as a zip left undone.
  const gapTop = sk.neck_half_w * 0.55;
  const gapHem = sk.waist_half_w * 0.52;
  // Follows the skirt's flare where there is one to follow, so the two hems
  // agree; on a character with no skirt it is the same widening a coat does.
  const outHem = pyMax(sk.hip_half_w * 1.06, skirtHalfW(sk, hemY) * 0.94);
  const waistY = sk.waist_y;
  const throatY = sy + sk.neck_half_w * 0.5;
  const lapelX = sk.neck_half_w * COAT_LAPEL_OUT;
  const lapelY = sy - sk.neck_half_w * COAT_LAPEL_UP;
  const shoulderY = sy + (waistY - sy) * 0.16;
  const parts: string[] = [];
  const panels: string[] = [];
  for (const s of [-1, 1]) {
    // The front edge, hem to throat. Over a bust it bows out, pushed aside
    // by the breast, following the tunic's own drape (`_bust_bulge`) scaled
    // down, since an outer layer shows the bust by where its edges fall and
    // does not draw a fold under it (`docs/tunic-bust-plan.md`, outer
    // layers).
    let front: string;
    if (COAT_BUST_BOW > 0 && sk.bust > 0) {
      const steps = 24;
      let acc = "";
      for (let k = 1; k <= steps; k++) {
        const [x, y] = quadPoint([gapHem, hemY], [gapTop * 1.35, waistY], [gapTop, throatY], k / steps); // `steps` is the constant 24
        acc += `L ${fmt1(cx + s * (x + COAT_BUST_BOW * bustBulge(sk, y)))} ${fmt1(y)} `;
      }
      front = acc;
    } else {
      front = `Q ${fmt1(cx + s * gapTop * 1.35)} ${fmt1(waistY)} ` + `${fmt1(cx + s * gapTop)} ${fmt1(throatY)} `;
    }
    const d =
      `M ${fmt1(cx + s * gapTop)} ${fmt1(throatY)} ` +
      `L ${fmt1(cx + s * lapelX)} ${fmt1(lapelY)} ` +
      `L ${fmt1(cx + s * shoulderW)} ${fmt1(shoulderY)} ` +
      `Q ${fmt1(cx + s * shoulderW * 1.02)} ${fmt1(waistY)} ` +
      `${fmt1(cx + s * outHem)} ${fmt1(hemY)} ` +
      `L ${fmt1(cx + s * gapHem)} ${fmt1(hemY)} ` +
      front +
      "Z";
    parts.push(`<path d="${d}" fill="${col(color)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw))}" />`);
    panels.push(d);
  }
  parts.push(bustPanelLine(sk, panels));
  return parts.join("");
}

// ---------------------------------------------------------------------------------------------------------
// The traced coat, its raised-sleeve cutaway and the belt over it

// How far a raised arm's base runs back into the body past the shoulder joint, in head radii: `RAISED_ARM_INTO_BODY`, in core-limbs.
// How far inside a raised arm's upper edge the shoulder is cut, as a share of the arm's half width.
export const SHOULDER_OVERLAP = 0.4;

/** The part of a quadratic chain (whose height only increases) down to height `y`. */
export function chainUntilY(chain: Chain, y: number): Chain {
  const [start, segs] = chain;
  const out: Segment[] = [];
  let p0: Point = start;
  for (const [c, e] of segs) {
    if (e[1] <= y) {
      out.push([c, e]);
      p0 = e;
      continue;
    }
    // split this segment where it reaches `y`: solve the quadratic's height for t by bisection
    let lo = 0.0;
    let hi = 1.0;
    for (let i = 0; i < 40; i++) {
      const t = (lo + hi) / 2;
      if ((1 - t) * (1 - t) * p0[1] + 2 * t * (1 - t) * c[1] + t * t * e[1] < y) lo = t;
      else hi = t;
    }
    const t = lo;
    const ctrl: Point = [p0[0] + (c[0] - p0[0]) * t, p0[1] + (c[1] - p0[1]) * t];
    const end: Point = [
      (1 - t) * (1 - t) * p0[0] + 2 * t * (1 - t) * c[0] + t * t * e[0],
      (1 - t) * (1 - t) * p0[1] + 2 * t * (1 - t) * c[1] + t * t * e[1],
    ];
    out.push([ctrl, end]);
    break;
  }
  return [start, out];
}

/** The same quadratic chain walked from its far end back to its start. */
export function reversedChain(chain: Chain): Chain {
  const [start, segs] = chain;
  const ends: Point[] = [start, ...segs.map(([, e]) => e)];
  const out: Segment[] = [];
  for (let i = segs.length - 1; i >= 0; i--) out.push([(segs[i] as Segment)[0], ends[i] as Point]);
  return [at(ends, -1), out];
}

// How far outside its traced line the torso's edge is drawn once the sleeve is gone, in head radii:
// the shirt under the coat is a little wider than the coat's torso line, and showed as a white sliver.
export const SLEEVE_CUT_OUT = 0.1;

/**
 * What a raised arm does to a coat whose sleeves are part of its silhouette: a clip
 * path that keeps everything of the coat but that arm's sleeve, and the line that edges
 * the torso there instead.
 *
 * What goes is the strip beside the torso below the arm's own upper edge, which is where the
 * arm takes over: the shoulder above that line stays as the coat's, so the shoulder runs
 * into the arm's upper edge, and the arm's body, drawn under the coat, shows where the
 * sleeve strip was. The strip's inner side is the cut's own side line, moved out a little
 * (`_SLEEVE_CUT_OUT`). The torso's edge line starts at the armpit, where the arm's lower edge
 * meets the torso. Returns `(defs, edge lines)`, or empty strings when no arm is out.
 */
export function sleeveCutaway(sk: Skeleton, p: CharacterParams): [string, string] {
  const sides = [-1, 1].filter((s) => raisedCoatSleeve(p, s));
  if (sides.length === 0) return ["", ""];
  const cut = coatCut(p.outfit.coat_cut);
  if (cut.arm_lines === null || cut.sleeve_hem_y === null) throw new PyError("AssertionError", "");
  const [cx, cy, r] = [sk.head_cx, sk.head_cy, sk.head_r];
  const xf = garmentPlacement(sk, cut.ref_body);

  /** A point of the cut in pixels, moved out from the centre line by `_SLEEVE_CUT_OUT`. */
  const px = (pt: Point): Point => {
    const [x, y] = xf(pt);
    return [cx + (x + copysign(SLEEVE_CUT_OUT, x)) * r, cy + y * r];
  };

  const below = cy + xf([0.0, cut.sleeve_hem_y + 0.4])[1] * r;

  const curveOf = (chain: Chain): string =>
    chain[1].map(([c, e]) => `Q ${fmt1(px(c)[0])} ${fmt1(px(c)[1])} ${fmt1(px(e)[0])} ${fmt1(px(e)[1])}`).join(" ");

  const atPt = (pt: Point): string => `${fmt1(pt[0])} ${fmt1(pt[1])}`;

  /** Where the line from `origin` along `along` crosses the vertical `x`. */
  const across = (origin: Point, along: Point, x: number): Point => {
    const t = Math.abs(along[0]) > 1e-6 ? pyDiv(x - origin[0], along[0]) : 0.0;
    return [x, origin[1] + t * along[1]];
  };

  // The whole canvas as one rectangle, and each arm's sleeve strip as a hole in it: wound the
  // other way, under the clip path's own non-zero rule (`clip-rule` is not honoured everywhere).
  const far = 8.0 * r;
  let path = `M ${atPt([cx - far, cy - far])} L ${atPt([cx + far, cy - far])} L ${atPt([cx + far, cy + far])} L ${atPt([cx - far, cy + far])} Z `;
  const edges: string[] = [];
  for (const s of sides) {
    let chain = (cut.lines[(cut.arm_lines as readonly [number, number])[s === -1 ? 0 : 1] as number]) as Chain;
    // The strip ends level with the coat's own hem at the corner, not on the sleeve's lobe below.
    if (cut.hem_corners === null) throw new PyError("TypeError", "'NoneType' object is not subscriptable");
    const hemRef = cut.hem_corners[s === -1 ? 0 : 1];
    chain = chainUntilY(chain, hemRef[1]);
    const [hemX, hemY] = [xf(hemRef)[0] * r + cx, xf(hemRef)[1] * r + cy];
    const [first, last] = [px(chain[0]), px((at(chain[1], -1) as Segment)[1])];
    const pivot = armPivot(sk, p, s);
    const turn = radians(-s * armSwing(p, s));
    const along: Point = [-pySin(turn), pyCos(turn)]; // from the shoulder toward the hand
    const wide: Point = [pyCos(turn), pySin(turn)]; // across the arm
    const down = wide[1] > 0 ? 1.0 : -1.0; // which way along `wide` is the lower edge
    const w = sk.arm_half_w;
    const lower: Point = [pivot[0] + down * w * wide[0], pivot[1] + down * w * wide[1]];
    // The line the shoulder stops on lies a little inside the arm's upper edge, so the arm's
    // own outline, which curves a little off a straight line, leaves no sliver under it.
    const inset = SHOULDER_OVERLAP * w - w;
    const upper: Point = [pivot[0] + down * inset * wide[0], pivot[1] + down * inset * wide[1]];
    const meetUpper = across(upper, along, first[0]);
    // Along the arm's upper edge, well clear of the body; and back round the outside.
    const k = 5.0 * r;
    const out: Point = [upper[0] + k * along[0], upper[1] + k * along[1]];
    const corner: Point = [cx + s * 5.0 * r, out[1]];
    // the strip's outline, for which way round it goes: it has to run against the rectangle's
    const loop: Point[] = [out, corner, [corner[0], below], [hemX, below], [hemX, hemY], last, first, meetUpper];
    const next: Point[] = [...loop.slice(1), loop[0] as Point];
    // `zip(loop, next, strict=True)`: the two lists have the same length by construction.
    const area = pySum(loop.map((a, i) => a[0] * (next[i] as Point)[1] - (next[i] as Point)[0] * a[1]));
    let hole: string;
    if (area > 0) {
      hole =
        `M ${atPt(out)} L ${atPt(meetUpper)} L ${atPt(first)} ${curveOf(chain)} L ${atPt([hemX, hemY])} ` +
        `L ${atPt([hemX, below])} L ${atPt([corner[0], below])} L ${atPt(corner)} Z `;
    } else {
      hole =
        `M ${atPt(out)} L ${atPt(corner)} L ${atPt([corner[0], below])} L ${atPt([hemX, below])} ` +
        `L ${atPt([hemX, hemY])} L ${atPt(last)} ${curveOf(reversedChain(chain))} L ${atPt(first)} L ${atPt(meetUpper)} Z `;
    }
    path += hole;
    const armpit = across(lower, along, first[0]);
    edges.push(`M ${atPt(armpit)} L ${atPt(first)} ${curveOf(chain)} L ${atPt([hemX, hemY])}`);
  }
  const weight = interiorW(strokeW(sk), cut.line_weight);
  const lines = edges
    .map((d) => `<path d="${d}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(weight)}" stroke-linecap="round" />`)
    .join("");
  return [`<defs><clipPath id="${SLEEVE_CUT_ID}"><path d="${path}" /></clipPath></defs>`, lines];
}

/** The coat cut's side lines that a raised arm replaces (`_sleeve_cutaway` draws its own edge). */
export function cutawaySideLines(p: CharacterParams): Set<number> {
  if (p.outfit.coat_color === null || p.outfit.coat_cut === null) return new Set();
  const cut = coatCut(p.outfit.coat_cut);
  if (cut.arm_lines === null) return new Set();
  const out = new Set<number>();
  for (const s of [-1, 1]) if (raisedCoatSleeve(p, s)) out.add(cut.arm_lines[s === -1 ? 0 : 1]);
  return out;
}

/**
 * A traced jacket, on whichever side of the arms its cut asks for, and the
 * belt over it.
 *
 * The shared coat goes under the arms, the order every other character is
 * drawn in. Katherina's jacket goes over them, because its armholes are what
 * covers the top of a sleeve: her reference hides that top under the hair,
 * and a body whose hair is narrower would show it standing out of the
 * shoulder. Keiko's lab coat goes under, because her sleeve is a piece in its
 * own right and has to lie over the body with its own outline. The cut says
 * which (`GarmentCut.over_arms`), so the order rides on the garment and never
 * changes globally.
 *
 * The belt is worn over the jacket either way, and always after the arms, so
 * an arm cannot cut across it.
 */
export function tracedCoatAndBelt(sk: Skeleton, p: CharacterParams, after_arms = true): string {
  if (!tracedCoat(sk, p)) return "";
  const cut = coatCut(p.outfit.coat_cut);
  if (cut.over_arms !== after_arms) return "";
  // The belt travels with the jacket it is worn over, so a coat drawn under
  // the arms takes its belt under them too: the arm's outline is then what
  // ends the band, which is what a belt passing round a body looks like.
  const [defs, edges] = sleeveCutaway(sk, p);
  return (
    defs +
    drawCut(sk, cut, p.outfit.coat_color as string, 1.0, null, truthy(defs) ? SLEEVE_CUT_ID : null, cutawaySideLines(p)) +
    edges +
    hipPockets(sk, p) +
    coatButtons(sk, p) +
    beltDrawn(sk, p)
  );
}

/**
 * A flapped pocket on each hip, a traced cut (`HIP_POCKET_CUT`), over the coat it
 * is sewn on and in the colour `hip_pocket_color`. Nothing without a colour.
 */
export function hipPockets(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.hip_pocket_color === null) return "";
  return drawCut(sk, HIP_POCKET_CUT, p.outfit.hip_pocket_color);
}

/**
 * The coat's buttons: discs down the front (`_COAT_BUTTONS`), each with a thin
 * ring, in `coat_button_color`. Nothing without a colour.
 */
export function coatButtons(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.coat_button_color === null) return "";
  const xf = garmentPlacement(sk, "tall_slender");
  const sw = strokeW(sk);
  const out: string[] = [];
  for (const [x, y, r] of COAT_BUTTONS) {
    const [px, py] = xf([x, y]);
    out.push(
      `<circle cx="${fmt1(sk.head_cx + px * sk.head_r)}" cy="${fmt1(sk.head_cy + py * sk.head_r)}" ` +
        `r="${fmt1(r * sk.head_r)}" fill="${col(p.outfit.coat_button_color)}" stroke="${OUTLINE}" ` +
        `stroke-width="${fmt2(interiorW(sw, 0.5))}" />`,
    );
  }
  return out.join("");
}

/**
 * How far out from the centre line a placed cut's fills reach at height
 * `y`, both in pixels: the outermost crossing of that row by any fill's
 * outline, or None if no fill crosses it.
 */
export function cutHalfWAt(sk: Skeleton, cut: GarmentCut, y: number): number | null {
  const [cx, cy, r] = [sk.head_cx, sk.head_cy, sk.head_r];
  const xf = garmentPlacement(sk, cut.ref_body);
  let reach: number | null = null;
  for (const [start, segs] of cut.fills) {
    let p0 = xf(start);
    for (const [c, e] of segs) {
      const [p1, p2] = [xf(c), xf(e)];
      let prev: Point | null = null;
      for (let i = 0; i < 25; i++) {
        const t = i / 24;
        let pt: Point = [
          (1 - t) * (1 - t) * p0[0] + 2 * t * (1 - t) * p1[0] + t * t * p2[0],
          (1 - t) * (1 - t) * p0[1] + 2 * t * (1 - t) * p1[1] + t * t * p2[1],
        ];
        pt = [cx + pt[0] * r, cy + pt[1] * r];
        if (prev !== null && (prev[1] - y) * (pt[1] - y) <= 0 && prev[1] !== pt[1]) {
          const k = pyDiv(y - prev[1], pt[1] - prev[1]);
          const w = Math.abs(prev[0] + (pt[0] - prev[0]) * k - cx);
          reach = reach === null ? w : pyMax(reach, w);
        }
        prev = pt;
      }
      p0 = p2;
    }
  }
  return reach;
}

// ---------------------------------------------------------------------------------------------------------
// The collar, the ribbon, the placket, the pockets and the strap

/**
 * A mock neck: the collar takes the neck's own silhouette.
 *
 * Knitwear pulled up the throat has no opening and stands no wider than what
 * it covers, so this is one band at the neck's width from the top of the neck
 * down past the tunic's neckline, and no notch. The standing band `_collar`
 * draws is the other thing, a uniform's collar spreading toward the
 * shoulders; drawn at 1.70 neck half-widths on a mock neck it reads as a
 * yoke.
 *
 * It has to reach below the tunic's V or a sliver of throat shows under it.
 * `_tunic` cuts that V to `neck_half_w * 0.28` below the shoulder line
 * whenever a collar is worn, so the band clears the V's point by a stroke
 * width rather than stopping on the shoulder line where the cloth's own
 * seam would sit.
 */
export function mockCollar(sk: Skeleton, _p: CharacterParams, color: string, sw: number): string {
  const [cx, sy] = [sk.head_cx, sk.shoulder_y];
  // Just outside the neck, so the band's outline sits beside the neck's
  // rather than on top of it.
  // Tapered, not parallel-sided: the reference's band runs 0.276 head radii
  // across at the top and 0.256 at its seam. That 7% is also what keeps its
  // lower corners inside the coat's opening, which narrows from the throat
  // down; parallel sides poked out over the lapels and put the step back.
  const [half, halfLow] = [sk.neck_half_w * 1.03, sk.neck_half_w * 0.95];
  const chin = sk.head_cy + sk.head_r;
  // The top edge sags in the middle, under the jaw, instead of running flat
  // across the throat: measured on the reference at 0.868 head radii at the
  // band's outer edges against 0.907 at the centre line, a sag of 0.039, with
  // a sliver of neck skin above it. Drawn flat and above the chin it was
  // simply covered by the head, so no skin showed and the band read as a
  // square block sitting under the face (the owner's review, P2). The control
  // point is placed so the curve's own midpoint lands on the sag, since a
  // quadratic reaches only a quarter of the way to its control.
  const top = chin + sk.head_r * 0.015;
  const sag = chin + sk.head_r * 0.075;
  const ctrl = top + (sag - top) * 2.0;
  const bottom = sy + sk.neck_half_w * 0.28 + sw;
  const lip = `M ${fmt1(cx - half)} ${fmt1(top)} Q ${fmt1(cx)} ${fmt1(ctrl)} ${fmt1(cx + half)} ${fmt1(top)}`;
  return (
    // The fill and the edges are separate so the seam at the bottom can be
    // line work rather than an outline: the dress below the band is the same
    // cloth in the same colour, and a full-weight edge across it was the
    // other half of what read as a block.
    `<path d="${lip} L ${fmt1(cx + halfLow)} ${fmt1(bottom)} L ${fmt1(cx - halfLow)} ${fmt1(bottom)} Z" ` +
    `fill="${col(color)}" stroke="none" />` +
    `<path d="M ${fmt1(cx - halfLow)} ${fmt1(bottom)} L ${fmt1(cx - half)} ${fmt1(top)} ` +
    `Q ${fmt1(cx)} ${fmt1(ctrl)} ${fmt1(cx + half)} ${fmt1(top)} L ${fmt1(cx + halfLow)} ${fmt1(bottom)}" ` +
    `fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw))}" stroke-linejoin="round" />` +
    `<line x1="${fmt1(cx - halfLow)}" y1="${fmt1(bottom)}" x2="${fmt1(cx + halfLow)}" y2="${fmt1(bottom)}" ` +
    `stroke="${OUTLINE}" stroke-width="${fmt2(interiorW(sw, 0.7))}" stroke-linecap="round" />`
  );
}

/**
 * A standing collar closing at the throat, over the tunic's open V.
 *
 * The tunic's neckline is a V that shows the undersleeve's tone at its edge,
 * which is right for a working tunic and wrong for a uniform, where the
 * garment closes at the neck. Rather than give the tunic a second neckline
 * shape, this covers the V with a band: the silhouette underneath is
 * unchanged, and a collar is a separate piece of cloth on the reference too.
 *
 * Two shapes, not one. The band around the neck reads as a collar only once
 * something says which way it faces, so the front carries a shallow notch
 * where the two halves meet, which is the same trick the V was doing.
 */
export function collar(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.collar_color === null) return ""; // Python: `return None or ""`
  if (p.outfit.collar_cut !== null) {
    return drawCut(sk, tableGet(COLLAR_CUTS, p.outfit.collar_cut), p.outfit.collar_color);
  }
  const [cx, sy] = [sk.head_cx, sk.shoulder_y];
  const color = p.outfit.collar_color;
  const sw = strokeW(sk);
  if (truthy(p.outfit.collar_mock)) {
    return mockCollar(sk, p, color, sw);
  }
  // Off the neck, not off the shoulder: a collar wraps a throat, and reading
  // the shoulder here would widen it into a yoke as the frame gets broader.
  const half = sk.neck_half_w * 1.7;
  const h = sk.neck_half_w * 1.75;
  // Sits high, most of it above the shoulder line. A collar drawn down onto
  // the chest reads as a bib; what says "closed at the throat" is cloth
  // standing up the neck, and at tile size the part below the shoulder is
  // indistinguishable from the tunic it is the same colour as anyway.
  const top = sy - h * 0.8;
  const d =
    `M ${fmt1(cx - half)} ${fmt1(top)} L ${fmt1(cx + half)} ${fmt1(top)} ` +
    `L ${fmt1(cx + half * 0.86)} ${fmt1(top + h)} L ${fmt1(cx - half * 0.86)} ${fmt1(top + h)} Z`;
  const notch = h * 0.55;
  return (
    `<path d="${d}" fill="${col(color)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw))}" />` +
    `<path d="M ${fmt1(cx)} ${fmt1(top)} L ${fmt1(cx)} ${fmt1(top + notch)}" fill="none" ` +
    `stroke="${OUTLINE}" stroke-width="${fmt2(interiorW(sw, 0.7))}" />`
  );
}

// The ribbon's outline against the figure's: the reference draws it in a line about
// half the weight it draws the figure's silhouette in.
export const RIBBON_LINE = 0.55;

/**
 * A bow tied at the throat, over the collar's wings and the shirt front: a
 * traced cut (`RIBBON_CUT`), in `ribbon_color`. Nothing without a colour.
 */
export function ribbon(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.ribbon_color === null) return "";
  // Thinner than the figure's line: the bow is small, and its slits are narrower
  // than the full stroke, which filled them in.
  return drawCut(sk, RIBBON_CUT, p.outfit.ribbon_color, RIBBON_LINE);
}

/**
 * A line of buttons down the centre front, collar to belt.
 *
 * The one piece of uniform trim that is pure line work, and the one that does
 * most of the work: a plain coloured torso reads as a jersey, and a seam down
 * the middle of it reads as a coat that fastens. The buttons are dots on that
 * seam rather than drawn discs, because at tile size a disc with an outline is
 * a smudge and a dot is a button.
 */
export function placket(sk: Skeleton, p: CharacterParams): string {
  // Sewn on the tunic, so it goes when the tunic does.
  if (p.outfit.placket_color === null || p.outfit.tunic_color === null) return "";
  const cx = sk.head_cx;
  const color = p.outfit.placket_color;
  const sw = strokeW(sk);
  const top = sk.shoulder_y + sk.neck_half_w * 0.9;
  const [beltY] = beltBand(sk);
  const bottom = beltY;
  // Slightly off centre, the way a real placket is: the flap that carries the
  // buttons laps over the other side rather than meeting it edge to edge. A
  // dead-centre line reads as a fold in the cloth instead.
  const x = cx + sk.waist_half_w * 0.13;
  const parts = [
    `<path d="M ${fmt1(x)} ${fmt1(top)} L ${fmt1(x)} ${fmt1(bottom)}" fill="none" ` +
      `stroke="${col(color)}" stroke-width="${fmt2(interiorW(sw, 0.7))}" stroke-linecap="round" />`,
  ];
  // Four, which is what fits between a collar and a belt without the row
  // reading as a zip. They ride the line rather than sitting beside it.
  const n = 4;
  for (let i = 0; i < n; i++) {
    const by = top + ((bottom - top) * (i + 0.5)) / n; // `n` is the constant 4
    parts.push(`<circle cx="${fmt1(x)}" cy="${fmt1(by)}" r="${fmt1(sw * 0.62)}" fill="${col(color)}" />`);
  }
  return parts.join("");
}

/**
 * A flapped pocket on each breast.
 *
 * Drawn as a flap alone rather than a pocket with a flap over it. The pocket's
 * own outline is a rectangle behind the flap and is invisible at every size
 * this is looked at, so all it would add is two more lines to thicken the
 * shape; what says "military tunic" is the horizontal flap with a stitch under
 * it.
 */
export function chestPockets(sk: Skeleton, p: CharacterParams): string {
  // Sewn on the tunic, like the placket.
  if (p.outfit.chest_pocket_color === null || p.outfit.tunic_color === null) return "";
  const cx = sk.head_cx;
  const color = p.outfit.chest_pocket_color;
  const sw = strokeW(sk);
  // Between the armpit and the waist, and inside the torso's own width at that
  // height, so a pocket cannot ride out over the side contour on a broad frame.
  const top = sleeveHemY(sk) + (sk.waist_y - sleeveHemY(sk)) * 0.28;
  const w = sk.waist_half_w * 0.38;
  const h = sk.waist_half_w * 0.3;
  const off = sk.waist_half_w * 0.5;
  const parts: string[] = [];
  for (const s of [-1, 1]) {
    const px = cx + s * off;
    parts.push(
      // The flap takes the second tone, which is the pouch-flap and
      // boot-cuff case the flat-colour rule leaves open: a turn of cloth
      // reading as thickness on a small element, not a plane across a
      // panel. Without it the flap is the tunic's own colour and all that
      // survives being shrunk is a faint rectangle of outline.
      `<rect x="${fmt1(px - w / 2)}" y="${fmt1(top)}" width="${fmt1(w)}" height="${fmt1(h)}" ` +
        `rx="${fmt1(h * 0.22)}" fill="${shade(color)}" stroke="${OUTLINE}" ` +
        `stroke-width="${fmt2(outlineW(sw, 0.7))}" />`,
    );
  }
  return parts.join("");
}

/**
 * A strap over the right shoulder and across to the opposite hip.
 *
 * Every uniformed character in the references wears one the same way round, so
 * the direction is fixed rather than a field: it is part of the uniform, not
 * something a character chooses. Tenno is the one who goes without, and he does
 * that by leaving the colour unset.
 *
 * Drawn over the tunic and under the arms. Over the arms it would cross a hand
 * at the wrist, and under the tunic it would not exist.
 */
export function strap(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.strap_color === null) return "";
  const cx = sk.head_cx;
  const color = p.outfit.strap_color;
  const sw = strokeW(sk);
  const topX = cx + sk.shoulder_half_w * 0.52;
  const topY = sk.shoulder_y + (sk.waist_y - sk.shoulder_y) * 0.1;
  const [beltY] = beltBand(sk);
  const botX = cx - sk.waist_half_w * 0.72;
  const w = sk.neck_half_w * 0.42;
  // A band with two parallel edges rather than a thick line, so it takes an
  // outline like every other garment and does not read as a drawn stroke.
  const [dx, dy] = [botX - topX, beltY - topY];
  const length = pyHypot(dx, dy);
  const [nx, ny] = [pyDiv(-dy, length) * w, pyDiv(dx, length) * w];
  const d =
    `M ${fmt1(topX + nx)} ${fmt1(topY + ny)} L ${fmt1(botX + nx)} ${fmt1(beltY + ny)} ` +
    `L ${fmt1(botX - nx)} ${fmt1(beltY - ny)} L ${fmt1(topX - nx)} ${fmt1(topY - ny)} Z`;
  return `<path d="${d}" fill="${col(color)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw, 0.8))}" />`;
}

// How far down the apron hangs, as a share of the skirt's own drop from the
// apron's top edge to the skirt's hem. A share rather than a fixed lift off that
// hem, which is what the apron used to take: measured hip to ankle, the lift was
// most of a chibi's whole body and left a band across its hips.
export const APRON_DROP = 0.74;

/**
 * A front panel hanging from the belt over the skirt. Narrow enough to leave
 * the hands clear on both sides, which is what fixes its width more than the
 * reference does.
 */
export function apron(sk: Skeleton, p: CharacterParams): string {
  const color = p.outfit.apron_color;
  if (color === null) return "";
  const cx = sk.head_cx;
  // Starts above the waist so the belt drawn over it covers the top edge.
  // A fraction of the skirt's own drop rather than a fixed lift off its hem.
  // The lift was measured from the hip to the ankle, which is most of a chibi's
  // whole body, so on a chibi it ate nearly the entire panel and left a band
  // across the hips where the canon hangs an apron down the skirt. Stated as a
  // share of the skirt the apron hangs over, one number holds at both builds.
  const topY = sk.waist_y - (sk.hip_y - sk.waist_y) * 0.4;
  let botY = topY + (skirtHemY(sk, p.outfit.skirt_length, p.outfit.skirt_length_chibi) - topY) * APRON_DROP;
  // Narrower than the waist by a quarter rather than a tenth. At 0.90 the panel
  // reached the hips, so the pouches hanging there landed on its top corners and
  // the belt, apron and pouches read as one satchel strapped across the body,
  // which is what the canon chibi does not do: there the apron is a panel hung
  // in the middle with the pouches flanking it, and the gap between them is what
  // tells the three pieces apart. The pouches move outboard to match.
  const topW = beltLineHalfW(sk) * 0.74;
  // No longer than it is wide. On the shared chibi the apron is a short wide
  // panel (about twice as wide as it is tall) and this never binds; on a body
  // with a long drop to the skirt hem it hung to the hem as a tall strip
  // that read as a bag, so it stops where it would stop being an apron.
  botY = pyMin(botY, topY + 2 * topW);
  // Flares only a little. Following the skirt's own flare down to a hem this
  // low turns the panel into a cone that swallows the garment under it, and the
  // reference's apron is a straight-hanging panel.
  const botW = pyMin(topW * 1.12, skirtHalfW(sk, botY) * 0.7);
  const r = botW * 0.14;
  const d =
    `M ${fmt1(cx - topW)} ${fmt1(topY)} ` +
    `L ${fmt1(cx - botW)} ${fmt1(botY - r)} ` +
    `Q ${fmt1(cx - botW)} ${fmt1(botY)} ${fmt1(cx - botW + r)} ${fmt1(botY)} ` +
    `L ${fmt1(cx + botW - r)} ${fmt1(botY)} ` +
    `Q ${fmt1(cx + botW)} ${fmt1(botY)} ${fmt1(cx + botW)} ${fmt1(botY - r)} ` +
    `L ${fmt1(cx + topW)} ${fmt1(topY)} ` +
    `Z`;
  return `<path d="${d}" fill="${col(color)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)))}" />`;
}

/**
 * A shoulder board with rank bars, on the coat's shoulder.
 *
 * The board lies along the coat's own shoulder line, between the lapel point
 * and the shoulder point (the two `_coat` draws its panel through), tilted to
 * that slope, a darker tone of the coat with the bars across it, perpendicular
 * to its length the way a board's bars run. Drawn after the arms and the coat,
 * so nothing covers it, and before the collar and the head, which are over the
 * neck either way. Nothing without a plain coat: the formula is the coat's.
 */
export function shoulderBars(sk: Skeleton, p: CharacterParams): string {
  const color = p.outfit.shoulder_bars_color;
  if (color === null || p.outfit.coat_color === null || tracedCoat(sk, p)) return "";
  if (p.outfit.shoulder_bars < 1) return "";
  const side = p.outfit.shoulder_bars_side;
  const [cx, r] = [sk.head_cx, sk.head_r];
  const sw = strokeW(sk);
  const sy = sk.shoulder_y;
  const shoulderW = sleeveHalfW(sk) * 0.92;
  const lapelX = sk.neck_half_w * COAT_LAPEL_OUT;
  const lapelY = sy - sk.neck_half_w * COAT_LAPEL_UP;
  const shoulderY = sy + (sk.waist_y - sy) * 0.16;
  const [dx, dy] = [shoulderW - lapelX, shoulderY - lapelY];
  const length = pyHypot(dx, dy);
  const angle = degrees(Math.atan2(dy, dx));
  // Centred on the outer part of the slope, a little proud of the cloth it sits on.
  const t = 0.62;
  const [halfL, halfW] = [length * 0.34, r * 0.115];
  // Pushed in from the line by about its own half width, along the slope's normal
  // toward the body, so it lies on the cloth and not along its outline.
  const [nx, ny] = [pyDiv(-dy, length), pyDiv(dx, length)];
  const bx = cx + side * (lapelX + dx * t + nx * halfW * 1.1);
  const by = lapelY + dy * t + ny * halfW * 1.1;
  const n = pyMin(4, p.outfit.shoulder_bars);
  // `range(n)` needs an int: a fractional count is Python's `TypeError`. (A whole float such as `3.0` reaches here as `3`, which
  // Python also rejects; the parameter registry's int/float marker is gone by now. See `docs/ts-port-errors-garments.md`.)
  if (!Number.isInteger(n)) throw new PyError("TypeError", "'float' object cannot be interpreted as an integer");
  const barW = halfL * 2 * 0.13;
  const span = halfL * 1.3;
  const bars: string[] = [];
  for (let i = 0; i < n; i++) {
    // `n - 1` is not zero where it divides (`n > 1`).
    const off = n > 1 ? (span * i) / (n - 1) : span / 2;
    bars.push(
      `<rect x="${fmt1(-span / 2 + off - barW / 2)}" ` +
        `y="${fmt1(-halfW)}" width="${fmt1(barW)}" height="${fmt1(halfW * 2)}" fill="${col(color)}" />`,
    );
  }
  const board =
    `<rect x="${fmt1(-halfL)}" y="${fmt1(-halfW)}" width="${fmt1(halfL * 2)}" height="${fmt1(halfW * 2)}" ` +
    `rx="${fmt1(halfW * 0.3)}" fill="${shade(p.outfit.coat_color)}" stroke="${OUTLINE}" ` +
    `stroke-width="${fmt2(outlineW(sw, 0.85))}" stroke-linejoin="round" />`;
  return `<g transform="translate(${fmt1(bx)} ${fmt1(by)}) rotate(${fmt2(side * angle)})">${board}${bars.join("")}</g>`;
}

// ---------------------------------------------------------------------------------------------------------
// The belt, the pouches and the crystal harness

/**
 * A band at the waist. On a front view this is what actually makes a waist
 * read, since the arms hang over the silhouette's own taper and hide it.
 */
export function belt(sk: Skeleton, p: CharacterParams): string {
  if (tracedCoat(sk, p)) {
    return ""; // drawn over the traced jacket, by `_traced_coat_and_belt`
  }
  return beltDrawn(sk, p);
}

export function beltDrawn(sk: Skeleton, p: CharacterParams): string {
  const color = p.outfit.belt_color;
  if (color === null) return "";
  if (p.outfit.belt_cut !== null) {
    const cut: BeltCut = tableGet(BELT_CUTS, p.outfit.belt_cut);
    return drawCut(sk, cut.strap, color) + drawCut(sk, cut.frame, "#8a8578", 0.55) + drawCut(sk, cut.through, color, 0.55);
  }
  const cx = sk.head_cx;
  // Wraps over the tunic, so it is a shade wider than the body at the waist.
  let halfW = sk.waist_half_w * 1.03;
  if (p.outfit.belt_scale > 1.6) {
    halfW = beltLineHalfW(sk) * 1.03;
  }
  if (p.outfit.trouser_color !== null) {
    // Wide enough to cover the trousers' top corners. On the shared chibi the
    // belt is wider than the legs it sits over and this never binds; on a body
    // with a narrow waist the trousers hang wider than the belt, and their
    // square corners stood out under its rounded ends as a small step.
    const [gap, wTop] = legGapAndTop(sk, true);
    halfW = pyMax(halfW, gap + wTop + strokeW(sk) * 0.5);
  }
  // A belt worn over a coat has further to go than one worn over a waist: it
  // reaches the coat's own front edge. Keiko's stopped at 0.679 head radii
  // where her coat's panel is 0.784, so it read as a short bar floating in the
  // middle of the coat (the owner's review, P6).
  halfW *= p.outfit.belt_reach;
  const [y, h] = beltBand(sk, p.outfit.belt_scale);
  if (handsAfterCoat(sk, p)) {
    // Over a coat worn over the arms, the band runs to the coat's own edge
    // at its height and stops half a stroke inside it, so the edge's outline
    // stays whole and reads as the sleeve passing over the belt, the way the
    // arm's outline ended it while the arms were drawn over the coat. The
    // reach does not apply: shorter, the band floats in the middle of the
    // coat (the owner's review, P6); longer, it is drawn over the sleeve
    // (`docs/bust-plan.md`, step 5b).
    const edge = cutHalfWAt(sk, coatCut(p.outfit.coat_cut), y + h / 2);
    if (edge !== null) {
      halfW = edge - strokeW(sk) / 2;
    }
  }
  let parts: string[];
  if (truthy(p.outfit.belt_keeper_pair)) {
    // No end caps. A belt goes *around* a body, so its ends have nothing to
    // show: capped and rounded they read as the two ends of a strap laid on
    // the front, and here they sat right on top of the arm's own outline
    // (the owner, 2026-09-21). Drawn instead as a fill with only its top and
    // bottom edges stroked, running out past the arm's inner edge so those
    // two lines end on the arm's outline and the band reads as continuing
    // behind it. Square, not rounded, since the corners are never seen.
    parts = [
      `<rect x="${fmt1(cx - halfW)}" y="${fmt1(y)}" width="${fmt1(halfW * 2)}" height="${fmt1(h)}" ` +
        `fill="${col(color)}" stroke="none" />`,
    ];
    for (const edge of [y, y + h]) {
      parts.push(
        `<line x1="${fmt1(cx - halfW)}" y1="${fmt1(edge)}" x2="${fmt1(cx + halfW)}" y2="${fmt1(edge)}" ` +
          `stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)))}" />`,
      );
    }
  } else {
    parts = [
      `<rect x="${fmt1(cx - halfW)}" y="${fmt1(y)}" width="${fmt1(halfW * 2)}" height="${fmt1(h)}" ` +
        `rx="${fmt1(h * 0.18)}" fill="${col(color)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)))}" />`,
    ];
  }
  // Not on a dress belt. This band is meant to read as the strap's own
  // thickness, which it does on the dark leather the rest of the cast wears
  // and does not on a pale one: on Keiko's white belt it read as a grey
  // stripe down the lower half, a two-tone plank rather than a belt (the
  // owner, 2026-09-21). `CLAUDE.md`'s rule is that a garment carries no
  // shading plane and a second tone is for small elements where it reads as
  // thickness, so where it stops doing that it goes.
  if (truthy(p.shaded) && !truthy(p.outfit.belt_keeper_pair)) {
    parts.push(
      `<rect x="${fmt1(cx - halfW)}" y="${fmt1(y + h * 0.62)}" width="${fmt1(halfW * 2)}" height="${fmt1(h * 0.38)}" ` +
        `rx="${fmt1(h * 0.18)}" fill="${shade(color)}" opacity="0.8" />`,
    );
  }
  // A buckle, but not on a sash. An obi is the same band three times as deep
  // and it is *tied*, not fastened, so a metal buckle on one is the single
  // detail that would say "belt" loudest on the three characters the depth is
  // there to dress. The cut-off sits between a wide belt and a narrow sash.
  const obi = p.outfit.belt_scale > 1.6;
  // An apron hides it: `ref/satoko-chibi.jpg`'s apron sits high enough to
  // cover it. (The retired realistic build showed it above the apron, as
  // `ref/satoko-real.jpg` does.)
  const showBuckle = p.outfit.apron_color === null && !obi;
  // Whenever the buckle is not carrying the belt on its own: an obi (never
  // gets a buckle) or an apron at any build below where the buckle joins it,
  // same as before this build split existed. With both an apron and the
  // buckle showing, the tie stays too, since that is the realistic build's
  // own reference.
  const showTie = !showBuckle || p.outfit.apron_color !== null;
  let tieTop = y + h * 0.55;
  if (showBuckle) {
    // Metal is a fixed neutral tone: it is not anyone's palette.
    const sw = strokeW(sk);
    const [bw, bh] = [h * 1.5, h * 1.08];
    const [bx, by] = [cx - bw / 2, y + (h - bh) / 2];
    const inset = h * 0.26;
    parts.push(
      `<rect x="${fmt1(bx)}" y="${fmt1(by)}" width="${fmt1(bw)}" height="${fmt1(bh)}" rx="${fmt1(bh * 0.22)}" ` +
        `fill="#8a8578" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw, 0.85))}" />`,
    );
    // The buckle's opening shows the cloth behind the belt. On a dark belt a
    // shade of its own colour says that well enough, but on a pale one it
    // says nothing: Keiko's white belt lost its buckle to a light grey
    // square, where the reference's reads near-black because her charcoal
    // dress is what is behind it. So a dress belt takes the garment's tone.
    const opening =
      truthy(p.outfit.belt_keeper_pair) && p.outfit.tunic_color !== null ? shade(p.outfit.tunic_color, 0.9) : shade(color, 0.7);
    parts.push(
      `<rect x="${fmt1(bx + inset)}" y="${fmt1(by + inset)}" width="${fmt1(bw - inset * 2)}" ` +
        `height="${fmt1(bh - inset * 2)}" rx="${fmt1(bh * 0.1)}" fill="${opening}" />`,
    );
    parts.push(
      `<line x1="${fmt1(cx)}" y1="${fmt1(by)}" x2="${fmt1(cx)}" y2="${fmt1(by + bh * 0.55)}" ` +
        `stroke="${OUTLINE}" stroke-width="${fmt2(interiorW(sw, 0.5))}" stroke-linecap="round" />`,
    );
    // The keeper, the loop that holds the strap's loose end down past the
    // buckle. One small band, and it is most of what tells a buckle from the
    // hollow square this used to read as: a square alone is a shape, a square
    // with a strap running through a loop beside it is a fastening.
    // A dress belt carries one either side of the buckle instead, set well
    // out from it and standing proud of the band: Keiko's reference has
    // them 0.085 wide and 0.28 tall against a 0.220 band, their inner edges
    // about 1.36 band-heights out from the buckle's own edge
    // (`harness/keiko/landmarks.py`). Off by default, because
    // `_belt_drawn` dresses all seventeen presets.
    if (truthy(p.outfit.belt_keeper_pair)) {
      const [kw, kh] = [h * 0.39, h * 1.27];
      const ky = y + (h - kh) / 2;
      for (const s of [-1, 1]) {
        const kx = cx + s * (bw / 2 + h * 1.36) - kw / 2;
        parts.push(
          `<rect x="${fmt1(kx)}" y="${fmt1(ky)}" width="${fmt1(kw)}" height="${fmt1(kh)}" ` +
            `rx="${fmt1(kw * 0.3)}" fill="${col(color)}" ` +
            `stroke="${OUTLINE}" stroke-width="${fmt2(interiorW(sw, 0.55))}" />`,
        );
      }
    } else {
      const kw = h * 0.22;
      parts.push(
        `<rect x="${fmt1(bx + bw + h * 0.3)}" y="${fmt1(y + h * 0.08)}" width="${fmt1(kw)}" ` +
          `height="${fmt1(h * 0.84)}" rx="${fmt1(kw * 0.3)}" fill="${shade(color, 0.7)}" ` +
          `stroke="${OUTLINE}" stroke-width="${fmt2(interiorW(sw, 0.55))}" />`,
      );
    }
    // The tail continues from the buckle's own bottom edge when both show,
    // so the strap reads as one piece running through the buckle rather
    // than two unrelated ornaments stacked on the belt.
    tieTop = by + bh;
  }
  if (showTie) {
    // The strap's knotted end hanging down the apron's front, the one
    // thing on the assembly that says the panel hangs *from* the belt
    // rather than being a pocket sewn across it. Skips its own knot box
    // when the buckle is also showing, since the buckle already anchors
    // the strap and a second knot directly under it doubles up.
    const sw = strokeW(sk);
    const tieW = h * 0.3;
    const knotH = h * 0.55;
    const knotY = tieTop;
    if (!showBuckle) {
      parts.push(
        `<rect x="${fmt1(cx - h * 0.42)}" y="${fmt1(knotY)}" width="${fmt1(h * 0.84)}" ` +
          `height="${fmt1(knotH)}" rx="${fmt1(knotH * 0.35)}" fill="${shade(color, 0.86)}" ` +
          `stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw, 0.7))}" />`,
      );
    }
    // Two different heights off the same knot, not one: the top edge sits
    // inside where the knot box would be (or right at the buckle's own
    // edge when there is no box), and the drop is measured from a full
    // knot_h down, past where the box would end.
    const tailStart = !showBuckle ? knotY + knotH * 0.7 : knotY;
    const tailBase = !showBuckle ? knotY + knotH : knotY;
    for (const [s, drop] of [
      [-1, 0.62],
      [1, 0.48],
    ] as const) {
      // Two ends of unequal length, because a knot with two equal tails
      // reads as a ribbon.
      const x0 = cx + s * h * 0.2;
      parts.push(
        `<path d="M ${fmt1(x0 - tieW / 2)} ${fmt1(tailStart)} ` +
          `L ${fmt1(x0 + tieW / 2)} ${fmt1(tailStart)} ` +
          `L ${fmt1(x0 + s * h * 0.1 + tieW / 2)} ${fmt1(tailBase + (sk.hip_y - sk.waist_y) * drop)} ` +
          `L ${fmt1(x0 + s * h * 0.1 - tieW / 2)} ${fmt1(tailBase + (sk.hip_y - sk.waist_y) * drop)} ` +
          `Z" fill="${shade(color, 0.86)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw, 0.7))}" />`,
      );
    }
  }
  return parts.join("");
}

/**
 * A pouch on each hip, hanging from the belt band over whatever sits
 * under it. Body, flap and button are three flat tones off one color, the
 * same recipe as everything else. Drawn after the belt and apron so it
 * hangs in front of both, and before the arms so a hand can hang over it,
 * which is exactly how the canon stacks them.
 */
export function pouches(sk: Skeleton, p: CharacterParams): string {
  const color = p.outfit.pouch_color;
  if (color === null || p.outfit.belt_color === null) return "";
  const cx = sk.head_cx;
  const sw = strokeW(sk);
  const [beltY, beltH] = beltBand(sk);
  // Sized off the head, not the band: the chibi's band is a sliver while its
  // canon pouch is nearly half a head radius, so a band-relative pouch
  // vanishes exactly where the canon makes it loudest.
  const h = sk.head_r * (0.3 + 0.16 * sk.build);
  const w = h * 0.95;
  const top = beltY + beltH * 0.55;
  const r = w * 0.18;
  // How far out the pouches hang. They flank the apron rather than sitting on
  // its corners: the canon chibi leaves a gap of skirt between panel and pouch,
  // and that gap is what tells belt, apron and pouch apart instead of letting
  // them read as one satchel across the hips. Still short of the band's ends,
  // because a chibi's arms are thick and hang over them, which is what the
  // earlier inboard value was really guarding against.
  const xFrac = 0.68 + 0.08 * sk.build;
  const parts: string[] = [];
  for (const side of [-1, 1]) {
    const x = cx + side * beltLineHalfW(sk) * xFrac - w / 2;
    parts.push(
      `<rect x="${fmt1(x)}" y="${fmt1(top)}" width="${fmt1(w)}" height="${fmt1(h)}" rx="${fmt1(r)}" ` +
        `fill="${col(color)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw, 0.85))}" />`,
    );
    const flapH = h * 0.44;
    parts.push(
      `<rect x="${fmt1(x)}" y="${fmt1(top)}" width="${fmt1(w)}" height="${fmt1(flapH)}" rx="${fmt1(r)}" ` +
        `fill="${shade(color, 0.82)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw, 0.85))}" />`,
    );
    parts.push(
      `<circle cx="${fmt1(x + w / 2)}" cy="${fmt1(top + flapH)}" r="${fmt1(w * 0.1)}" ` + `fill="${shade(color, 0.5)}" />`,
    );
  }
  return parts.join("");
}

// Where each crystal sits along the belt, as a fraction of `waist_half_w`
// either side of centre, outer to inner. Kept inboard of the pouch's own
// 0.68-0.76 span (`_pouches`) so a character wearing both does not stack a
// gem on a flap: nothing in the cast does yet, but the rig and a pouch are
// both belt-mounted kit and there is no reason a future character couldn't
// wear both.
export const CRYSTAL_X_FRACS: readonly [number, number, number, number] = [-0.6, -0.28, 0.28, 0.6];

/**
 * How big the four crystals are and where they hang: `(scale, offsets)`, the
 * scale on their usual size and the offsets from the centre line, outer to
 * inner.
 *
 * `_CRYSTAL_X_FRACS` of the waist, which is what they were fitted to: two
 * either side with the buckle showing between the middle pair. On a body with a
 * narrow waist and a deeper belt that closes up: the belt is 1.16 head radii
 * wide against the chibi's 1.84, but the buckle is sized off the belt's depth,
 * which is larger there, so the middle pair landed on the buckle and hid it.
 * There the middle pair stand clear of it (its half-width, a crystal's, and a
 * gap), the outer pair a crystal and a gap beyond them, and if that does not fit
 * inside the belt, with the outer strap, the crystals shrink until it does. On
 * the shared chibi all of it is slack, so scale and fractions are the old ones,
 * and the realistic build keeps them.
 */
export function crystalLayout(sk: Skeleton, belt_h: number): [number, [number, number, number, number]] {
  const h0 = sk.head_r * (0.3 + 0.12 * sk.build);
  const w0 = h0 * 0.58;
  const half = sk.waist_half_w;
  let inner = -CRYSTAL_X_FRACS[1] * half;
  let outer = CRYSTAL_X_FRACS[3] * half;
  // Half a stroke apart, which is how the chibi's straps sit: touching.
  const gap = strokeW(sk) * 0.5;
  const beltHalf = half * 1.03;
  const buckleHalf = (belt_h * 1.5) / 2;
  // buckle + inner crystal half + gap, then a crystal and a gap, then the
  // outer strap's half (1.22 of a crystal's width) inside the belt's end.
  const scale = pyMin(1.0, pyDiv(beltHalf - buckleHalf - 2 * gap, 2.11 * w0));
  const w = w0 * scale;
  inner = pyMax(inner, buckleHalf + w / 2 + gap);
  outer = pyMax(outer, inner + w + gap);
  return [scale, [-outer, -inner, inner, outer]];
}

/**
 * Up to four mana crystals clipped along the belt band, two a side.
 *
 * Flat kite-shaped gems, no glow: a crystal is dangerous to grip
 * bare-handed (a file in the consumer repo, "Donarsblut"), which is
 * what the rig is about, not a light source, and a glow at chibi scale
 * reads as clutter before it reads as danger anyway. The shape, the flat
 * color and the loop clipping it to the belt are what say "crystal", the
 * same way a flat rectangle with a flap says "pouch". Drawn after the belt
 * and pouches, in front of both, so the rig reads as riding over the band.
 */
export function crystalHarness(sk: Skeleton, p: CharacterParams): string {
  const colors = [p.outfit.crystal_color_1, p.outfit.crystal_color_2, p.outfit.crystal_color_3, p.outfit.crystal_color_4];
  if (p.outfit.belt_color === null || colors.every((c) => c === null)) return "";
  const cx = sk.head_cx;
  const sw = strokeW(sk);
  const [beltY, beltH] = beltBand(sk, p.outfit.belt_scale);
  const bandCy = beltY + beltH * 0.5;
  // A little taller than the pouch's own head-relative size: a gem this
  // small still has to read as faceted rather than as a dot.
  const [scale, offsets] = crystalLayout(sk, beltH);
  const h = sk.head_r * (0.3 + 0.12 * sk.build) * scale;
  const w = h * 0.58;
  const parts: string[] = [];
  // `zip(offsets, colors, strict=True)`: four and four.
  offsets.forEach((offset, i) => {
    const color = colors[i] as string | null;
    if (color === null) return;
    const gx = cx + offset;
    const top: Point = [gx, bandCy - h / 2];
    const right: Point = [gx + w / 2, bandCy - h * 0.08];
    const bottom: Point = [gx, bandCy + h / 2];
    const left: Point = [gx - w / 2, bandCy - h * 0.08];
    const d =
      `M ${fmt1(top[0])} ${fmt1(top[1])} ` +
      `L ${fmt1(right[0])} ${fmt1(right[1])} ` +
      `L ${fmt1(bottom[0])} ${fmt1(bottom[1])} ` +
      `L ${fmt1(left[0])} ${fmt1(left[1])} Z`;
    parts.push(`<path d="${d}" fill="${col(color)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw, 0.8))}" />`);
    // One facet line, top point to bottom point: the cheap cue that reads
    // as a cut stone rather than a bead, without a second fill or a
    // gradient.
    parts.push(
      `<line x1="${fmt1(top[0])}" y1="${fmt1(top[1])}" x2="${fmt1(bottom[0])}" y2="${fmt1(bottom[1])}" ` +
        `stroke="${shade(color, 0.6)}" stroke-width="${fmt2(interiorW(sw, 0.5))}" />`,
    );
    // The loop clipping it to the belt: a short stroke standing in for a
    // leather keeper, the same idea as the buckle's own keeper in `_belt`.
    parts.push(
      `<line x1="${fmt1(gx)}" y1="${fmt1(bandCy - h * 0.6)}" x2="${fmt1(gx)}" y2="${fmt1(top[1])}" ` +
        `stroke="${OUTLINE}" stroke-width="${fmt2(interiorW(sw, 0.6))}" stroke-linecap="round" />`,
    );
    // A leather strap wrapping the gem at its widest point, holding it to
    // the belt rather than leaving it looking merely balanced there.
    // Belt-colored so it reads as the same rig, not a second accessory.
    const strapH = h * 0.24;
    const strapW = w * 1.22;
    const strapY = bandCy - h * 0.08 - strapH / 2;
    parts.push(
      `<rect x="${fmt1(gx - strapW / 2)}" y="${fmt1(strapY)}" width="${fmt1(strapW)}" ` +
        `height="${fmt1(strapH)}" fill="${col(p.outfit.belt_color)}" ` +
        `stroke="${OUTLINE}" stroke-width="${fmt2(interiorW(sw, 0.6))}" />`,
    );
  });
  if (truthy(p.outfit.crystal_tongs)) {
    // A small crossed-tongs silhouette hanging below the outer right
    // gem, on the thigh rather than beside it: further out at belt
    // height sits behind the arm, the same room problem the pouches
    // solve by hanging low instead of wide. Standard Crystal Conclave
    // kit for a stock nobody grips bare-handed. Fixed neutral metal
    // tone, like the belt buckle: not anyone's palette.
    const tx = cx + offsets[3];
    const ty = bandCy + h * 1.05;
    const arm = h * 0.75;
    parts.push(
      `<line x1="${fmt1(tx - arm * 0.22)}" y1="${fmt1(ty - arm * 0.55)}" ` +
        `x2="${fmt1(tx + arm * 0.28)}" y2="${fmt1(ty + arm * 0.55)}" ` +
        `stroke="#8a8578" stroke-width="${fmt2(interiorW(sw, 0.7))}" stroke-linecap="round" />`,
    );
    parts.push(
      `<line x1="${fmt1(tx + arm * 0.22)}" y1="${fmt1(ty - arm * 0.55)}" ` +
        `x2="${fmt1(tx - arm * 0.28)}" y2="${fmt1(ty + arm * 0.55)}" ` +
        `stroke="#8a8578" stroke-width="${fmt2(interiorW(sw, 0.7))}" stroke-linecap="round" />`,
    );
    parts.push(`<circle cx="${fmt1(tx)}" cy="${fmt1(ty)}" r="${fmt1(sw * 0.6)}" fill="#6b665c" />`);
  }
  return parts.join("");
}

// The recorded calls name a constant by its Python name, underscore and all: the same values under those names.
export {
  APRON_DROP as _APRON_DROP,
  COAT_BUST_BOW as _COAT_BUST_BOW,
  COAT_LAPEL_OUT as _COAT_LAPEL_OUT,
  COAT_LAPEL_UP as _COAT_LAPEL_UP,
  CRYSTAL_X_FRACS as _CRYSTAL_X_FRACS,
  RIBBON_LINE as _RIBBON_LINE,
  ROBE_BUST_LINE as _ROBE_BUST_LINE,
  SHOULDER_OVERLAP as _SHOULDER_OVERLAP,
  SLEEVE_CUT_OUT as _SLEEVE_CUT_OUT,
};
export { BELT_CUTS, COAT_BUTTONS, COAT_BUTTONS as _COAT_BUTTONS, COLLAR_CUTS, HIP_POCKET_CUT, RIBBON_CUT } from "./garments-tables.ts";
export type { BeltCut } from "./garments-tables.ts";
