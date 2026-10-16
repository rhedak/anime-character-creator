// The body's lower half: the legs (bare in one seat with a pair of briefs, or in trousers), the boots and bare feet, the leg cuts
// (a traced sock or shoe on one leg), and the skirts (the plain skirt, the underskirt and the hakama). Port of the `parts-body`
// module of character.py (see `harness/ts_port/modules.json`); the upper half is in `body-parts.ts`. Names are the Python ones in
// camelCase and every expression keeps Python's evaluation order. Numbers reach the text only through the `fmt*` kernel functions.

import { BOOT_CUTS, KNEE_SOCK_CUT, SKIRT_CUTS } from "./body-parts-tables.ts";
import { skeletonFor } from "./body.ts";
import { OUTLINE, interiorW, outlineW, quadPoint, strokeW } from "./character.ts";
import { shade } from "./colorutil.ts";
import {
  beltBand,
  bodyKnots,
  drawCut,
  garmentPlacement,
  interp,
  legGapAndTop,
  limbBuild,
  maxOf,
  minOf,
  quadSplit,
  skirtHalfW,
  skirtHemY,
} from "./core-limbs.ts";
import type { GarmentCut } from "./core-limbs-tables.ts";
import { characterParams } from "./model.ts";
import type { CharacterParams } from "./params.ts";
import { PyError, fmt1, fmt2, pyDiv, pyMax, pyMin, truthy } from "./pynum.ts";
import type { Skeleton } from "./skeleton.ts";
import type { Point } from "./tables.ts";
import { pyValueRepr } from "./pyvalue.ts";

/**
 * `f"{color}"` of a colour field: a string as it is, anything else (None, an int, a list from a link) as Python's `str` spells it.
 * A colour that is only interpolated (never shaded) is not checked by Python, so it reaches the text.
 */
export const colorStr = (v: unknown): string => (typeof v === "string" ? v : pyValueRepr(v));

export const SOCK_CLIP_ID = "leg-above-sock";

/** `table[name]`: a name that is not a cut is Python's `KeyError`, a list is an unhashable key. */
function cutNamed(table: Readonly<Record<string, GarmentCut>>, name: unknown): GarmentCut {
  if (Array.isArray(name)) throw new PyError("TypeError", "unhashable type: 'list'");
  if (typeof name !== "string" || !Object.hasOwn(table, name)) throw new PyError("KeyError", pyValueRepr(name));
  return table[name] as GarmentCut;
}

// How far the limbs' taper reaches at most: `core-limbs`' `_TAPER_MAX`, which `body.ts` keeps private, so repeated here.
const TAPER_MAX = 0.5;

// ---------------------------------------------------------------------------------------------------------
// A traced cut worn on one leg

// How far outside `_leg_gap_and_top`'s centre line a leg is actually drawn, measured
// where a sock starts, in head radii: the knee's bulge and the inside edge running
// off toward the crotch put the visible leg there, and a sock set on the gap itself
// sat 7 px in from it on Risa, where the reference's sock and leg share one centre
// (`docs/risa-plan.md`, M3). It is also where her reference's feet stand.
export const LEG_CUT_OUT = 0.05;

/**
 * Map a per-leg cut onto the wearer's leg on `side` (-1 left, +1 right).
 *
 * The cut's x is from its leg's centre line, in head radii on `ref_body`: it is
 * scaled by how much thicker this wearer's leg is than that body's and set down
 * where the leg hangs, `gap` pixels out from the figure's centre line, mirrored
 * for the left. Heights move piecewise between the two bodies' landmarks like
 * any cut's, so a sock top traced under the knee lands under this body's.
 */
export function legPlacement(sk: Skeleton, ref_body: string, side: number, gap: number): (pt: Point) => Point {
  const ref = skeletonFor(characterParams({ body: ref_body }));
  const [refYs] = bodyKnots(ref);
  const [ys] = bodyKnots(sk);
  const across = pyDiv(pyDiv(sk.leg_half_w, sk.head_r), pyDiv(ref.leg_half_w, ref.head_r));
  const centre = pyDiv(gap, sk.head_r) + LEG_CUT_OUT;

  return (pt: Point): Point => [side * (centre + pt[0] * across), interp(pt[1], refYs, ys)];
}

/**
 * The highest point of a `per_leg` cut once placed, in pixels: where a sock's
 * top edge is, so the bare leg can stop there.
 */
export function legCutTopY(sk: Skeleton, cut: GarmentCut): number {
  const xf = legPlacement(sk, cut.ref_body, 1, 0.0);
  const ys: number[] = [];
  for (const [start, segs] of cut.fills) {
    for (const pt of [start, ...segs.flatMap((seg) => [...seg])]) ys.push(xf(pt)[1]);
  }
  return sk.head_cy + minOf(ys) * sk.head_r;
}

/** One leg's share of a `per_leg` cut: `gap` is where that leg's centre line hangs, from `_leg_gap_and_top`. */
export function drawLegCut(sk: Skeleton, cut: GarmentCut, fill: string, gap: number, side: number): string {
  return drawCut(sk, cut, fill, 1.0, legPlacement(sk, cut.ref_body, side, gap));
}

// ---------------------------------------------------------------------------------------------------------
// The skirt

/**
 * Where a skirt's side stops running straight and starts turning under into
 * its hem. Measured up from the hem in body units rather than as a fraction of
 * the panel's own height, so two panels sharing a hem turn under together: a
 * shadow band that rounded over a different span than the panel it sits on
 * poked out past its side, which is how this got its own function.
 */
export function skirtCornerY(sk: Skeleton, hem_y: number): number {
  return hem_y - (sk.ankle_y - sk.hip_y) * 0.07;
}

/**
 * An A-line skirt panel. Widths default to the flare the skeleton implies,
 * but a layer underneath can pass its own: an underskirt that kept flaring past
 * the hem above it would stick out sideways as a shelf rather than hanging.
 *
 * `scallop` waves the flat run of the hem into that many peaks (0 keeps the
 * single straight line every caller but `_underskirt` still wants), each pair
 * joined by one shallow dip of `scallop_dip`, rather than the underskirt
 * stating its own hem shape: the peaks land exactly on the two points the
 * corner curves already return to, so a scalloped call and a flat one close
 * on the same silhouette everywhere else.
 */
export function skirtPath(
  sk: Skeleton,
  top_y: number,
  hem_y: number,
  top_w: number | null = null,
  hem_w: number | null = null,
  scallop = 0,
  scallop_dip = 0.0,
): string {
  const cx = sk.head_cx;
  const topW = top_w === null ? skirtHalfW(sk, top_y) : top_w;
  const hemW = hem_w === null ? skirtHalfW(sk, hem_y) : hem_w;
  const corner = skirtCornerY(sk, hem_y);
  let hemLine: string;
  if (scallop >= 2) {
    const span = hemW * 0.6;
    // `scallop - 1` is at least 1 here.
    const xs: number[] = [];
    for (let i = 0; i < scallop; i++) xs.push(cx - span + (span * 2 * i) / (scallop - 1));
    const dipY = hem_y + scallop_dip * 2;
    // `itertools.pairwise(xs)`
    hemLine = "";
    for (let i = 0; i + 1 < xs.length; i++) {
      const [x0, x1] = [xs[i] as number, xs[i + 1] as number];
      hemLine += `Q ${fmt1((x0 + x1) / 2)} ${fmt1(dipY)} ${fmt1(x1)} ${fmt1(hem_y)} `;
    }
  } else {
    hemLine = `L ${fmt1(cx + hemW * 0.6)} ${fmt1(hem_y)} `;
  }
  return (
    `M ${fmt1(cx - topW)} ${fmt1(top_y)} ` +
    `L ${fmt1(cx - hemW)} ${fmt1(corner)} ` +
    `Q ${fmt1(cx - hemW)} ${fmt1(hem_y)} ${fmt1(cx - hemW * 0.6)} ${fmt1(hem_y)} ` +
    `${hemLine}` +
    `Q ${fmt1(cx + hemW)} ${fmt1(hem_y)} ${fmt1(cx + hemW)} ${fmt1(corner)} ` +
    `L ${fmt1(cx + topW)} ${fmt1(top_y)} ` +
    `Z`
  );
}

// Where the other lower-body layers sit, both stated against the skirt rather
// than measured from the hip on their own: a chibi's skirt is drawn shorter than
// asked for, and layers measured independently collapse onto one hem, where the
// underskirt has to keep showing below the skirt and the apron has to keep
// stopping above it, at every build.
//
// How far the underskirt hangs past the skirt's hem, as a fraction of the
// hip-to-ankle span.
export const UNDERSKIRT_DROP = 0.13;
// The underskirt's hem sags rather than running flat, `ref/satoko-real.jpg`'s
// own line. First guess here was a scallop per pleat, several small dips
// across the hem; rendered against the reference it was visibly wrong, one
// continuous shallow sag between the two side corners, not a row of teeth. Two
// peaks is the whole shape then, the two points the corner curves already
// land on, with one dip between them at `_UNDERSKIRT_SCALLOP_DIP` of the
// hip-to-ankle span. Picked by eye off a render sweep the way
// `_CROP_REAL_EAR_MARGIN` was: 0.018 read as barely there, 0.045 and 0.06
// both sagged deep enough to look heavy against the pleats above it, 0.03
// matched the reference's own depth.
export const UNDERSKIRT_SCALLOP = 2;
export const UNDERSKIRT_SCALLOP_DIP = 0.03;

/** A second skirt, longer than the one over it, so its hem shows as a band of a different tone below the other's. */
export function underskirt(sk: Skeleton, p: CharacterParams): string {
  const color = p.outfit.underskirt_color;
  if (color === null) return "";
  const skirtHem = skirtHemY(sk, p.outfit.skirt_length, p.outfit.skirt_length_chibi);
  const hemY = skirtHem + (sk.ankle_y - sk.hip_y) * UNDERSKIRT_DROP;
  // Hangs straight below the skirt's own hem rather than continuing to flare,
  // and clearly narrower, so it reads as being under the other one. At 0.97 it
  // was the skirt's own width to within a stroke, so the silhouette held the
  // skirt's flare all the way down past the hem, which is where ours ran wide
  // of the canon: theirs has already narrowed toward the legs by then. It is
  // also what made the chibi's dark band under a wide hem read as a tray.
  const hemW = skirtHalfW(sk, skirtHem) * 0.86;
  // The wave only reads as cloth where the band under it is deep enough to
  // hold a pleat line, the same cutoff the pleats below already use: on a
  // chibi the visible strip is a few pixels, and waving a few-pixel line is
  // noise, not a fold.
  const deep = hemY - skirtHem > strokeW(sk) * 4;
  const scallop = deep ? UNDERSKIRT_SCALLOP : 0;
  const dip = (sk.ankle_y - sk.hip_y) * UNDERSKIRT_SCALLOP_DIP;
  const d = skirtPath(sk, sk.waist_y, hemY, null, hemW, scallop, dip);
  const shape = `<path d="${d}" fill="${colorStr(color)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)))}" />`;
  if (!truthy(p.shaded)) return shape;
  // Only the band below the skirt above it is ever visible, so the shading is
  // a single turn under the hem rather than the folds the outer skirt gets. It
  // has to follow the panel's own taper: drawn at the hem's width all the way
  // up, it hangs out past the sides as a shelf, which is exactly what it did.
  // Starting the band exactly where the panel turns under means it is the
  // panel's own hem cap, at the same width, so it cannot overhang.
  const bandY = skirtCornerY(sk, hemY);
  const band = skirtPath(sk, bandY, hemY, hemW, hemW, scallop, dip);
  const parts = [shape, `<path d="${band}" fill="${shade(color)}" opacity="0.7" />`];
  // Pleats, as lines rather than as tone, the same call the outer skirt's folds
  // got: the canon adult's underskirt is a pleated skirt and the vertical fold
  // lines are the whole of what says so. They start at the skirt hem above,
  // since nothing higher is ever seen, and they run to the band, not through it,
  // so the turn under the hem stays one unbroken edge.
  //
  // Only where the band is deep enough to hold them (the same `deep` the wave
  // above is gated on).
  if (deep) {
    const pleatSw = pyMax(1.0, strokeW(sk) * 0.45);
    for (let i = -3; i < 4; i++) {
      const frac = i / 3.5;
      const x0 = sk.head_cx + skirtHalfW(sk, skirtHem) * 0.86 * frac;
      const x1 = sk.head_cx + hemW * frac;
      parts.push(
        `<line x1="${fmt1(x0)}" y1="${fmt1(skirtHem)}" x2="${fmt1(x1)}" y2="${fmt1(bandY)}" ` +
          `stroke="${shade(color)}" stroke-width="${fmt2(interiorW(pleatSw))}" opacity="0.75" />`,
      );
    }
  }
  return parts.join("");
}

/**
 * A wide pleated garment over the legs, from the waist to near the floor.
 *
 * The same A-line panel `_skirt` and `_underskirt` already draw, not a second
 * silhouette invented for this: `_skirt_path`'s flare comes off the
 * skeleton's own hip and hem anchors, and a hakama sharing it is what keeps a
 * lower-body garment skeleton-relative instead of a shape with its own
 * private idea of how wide the hips are.
 *
 * What actually makes it read as a hakama and not a plain skirt is the
 * pleats. `_skirt` draws two folds as a suggestion of drape; a hakama is
 * defined by them, so this draws a comb across the whole panel the way
 * `_underskirt` combs its own hem band, just over the full height instead of
 * a strip at the bottom. Flat colour and thin lines rather than a second
 * tone, the same call every other lower-body garment here makes: a wedge
 * wide enough to see is a plane this figure does not have room for twice.
 *
 * Legs or trousers are drawn first and this paints over the top of them,
 * which is what lets the two coexist without this needing to know whether
 * the legs under it are bare or in trousers, or how long they run: Reika's
 * is close to floor-length over bare legs and Haruto's stops well short of
 * his boots, over trousers that carry the rest of the way down.
 */
export function hakama(sk: Skeleton, p: CharacterParams): string {
  const color = p.outfit.hakama_color;
  if (color === null) return "";
  const sw = strokeW(sk);
  const topY = sk.waist_y;
  const hemY = skirtHemY(sk, p.outfit.hakama_length, p.outfit.hakama_length_chibi);
  const d = skirtPath(sk, topY, hemY);
  const shape = `<path d="${d}" fill="${colorStr(color)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw))}" />`;
  if (!truthy(p.shaded)) return shape;
  // Pleats run to the corner where the panel turns under, not through it, so
  // the turn stays one unbroken edge the way `_underskirt`'s does.
  const corner = skirtCornerY(sk, hemY);
  if (corner - topY <= sw * 4) return shape;
  const pleatSw = pyMax(1.0, sw * 0.4);
  const parts = [shape];
  for (let i = -3; i < 4; i++) {
    const frac = i / 3.5;
    const x0 = sk.head_cx + skirtHalfW(sk, topY) * frac;
    const x1 = sk.head_cx + skirtHalfW(sk, corner) * frac;
    parts.push(
      `<line x1="${fmt1(x0)}" y1="${fmt1(topY)}" x2="${fmt1(x1)}" y2="${fmt1(corner)}" ` +
        `stroke="${shade(color)}" stroke-width="${fmt2(interiorW(pleatSw))}" opacity="0.75" />`,
    );
  }
  return parts.join("");
}

/** The skirt: a traced cut from `SKIRT_CUTS`, or the shared A-line panel with two folds. */
export function skirt(sk: Skeleton, p: CharacterParams): string {
  const color = p.outfit.skirt_color;
  if (color === null) return "";
  if (p.outfit.skirt_cut !== null) return drawCut(sk, cutNamed(SKIRT_CUTS, p.outfit.skirt_cut), color);
  const hemY = skirtHemY(sk, p.outfit.skirt_length, p.outfit.skirt_length_chibi);
  // Starts above the hip so the tunic drawn over it has something to overlap
  // and the waistband never opens onto skin.
  const topY = sk.waist_y;
  const d = skirtPath(sk, topY, hemY);
  const shape = `<path d="${d}" fill="${colorStr(color)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)))}" />`;
  if (!truthy(p.shaded)) return shape;
  // Two folds, as thin lines rather than the shadow wedges they used to be. The
  // canon suggests this garment's drape with a line: a wedge wide enough to see
  // was a third plane on a figure that already had two, and on the chibi, where
  // the skirt below the apron is only a band, it filled it.
  const folds: string[] = [];
  for (const [s, frac] of [
    [-1, 0.52],
    [1, 0.3],
  ] as const) {
    const x0 = sk.head_cx + s * skirtHalfW(sk, topY) * frac;
    const x1 = sk.head_cx + s * skirtHalfW(sk, hemY) * (frac + 0.06);
    folds.push(
      `<line x1="${fmt1(x0)}" y1="${fmt1(topY + (hemY - topY) * 0.3)}" ` +
        `x2="${fmt1(x1)}" y2="${fmt1(hemY)}" stroke="${shade(color)}" ` +
        `stroke-width="${fmt2(interiorW(pyMax(1.0, strokeW(sk) * 0.45)))}" opacity="0.7" />`,
    );
  }
  return shape + folds.join("");
}

// ---------------------------------------------------------------------------------------------------------
// The legs and boots

export function legsAndBoots(sk: Skeleton, p: CharacterParams): string {
  // The taper belongs in the thigh, and nearly nowhere else. Measured off
  // ref/satoshi.png, the trouser leg is 1.42 leg-half-widths at the thigh, 1.03
  // at the knee, 1.01 through the calf and 0.85 at the ankle: it fills out under
  // the hip, then runs close to straight. This used to run 1.55 down to 0.55, a
  // two-to-one cone that read as fat thighs on stick shins, and the fix was
  // widening the shin rather than thinning the thigh. A plain untapered tube,
  // tried against this, beat the cone and lost to it.
  //
  // The thigh ships at 1.26 rather than the measured 1.42, by preference: the
  // reference's leg is photographed on a hip wider than this skeleton's, so the
  // full measurement came out heavy on it. The knee, calf and ankle are the
  // measured values.
  const taper = limbBuild(sk);
  // Trousers are the outermost garment on the leg, so unlike bare skin they
  // need their own outline, they start at the belt rather than under a hem, and
  // they carry more thigh: a shin-width tube running up to the hip reads as a
  // stilt once there is no skirt covering the top of it.
  const trouserColor = p.outfit.trouser_color;
  const [gap, wTop] = legGapAndTop(sk, truthy(trouserColor));
  const wKnee = sk.leg_half_w * (1.0 + 0.03 * taper);
  // Held, not bulged: the reference measures 72, 71, 71 pixels from knee through
  // calf before it takes in at the ankle.
  const wCalf = sk.leg_half_w * (1.0 + 0.01 * taper);
  const wAnkle = sk.leg_half_w * (0.92 - 0.07 * taper);
  let parts: string[];
  if (truthy(trouserColor)) {
    parts = [trousers(sk, p, trouserColor as string, gap, wTop, wKnee, wCalf, wAnkle)];
  } else {
    // One seat, not two tubes with a gap between them: see `_bare_seat`. What
    // used to be here drew each leg as its own closed path starting a few
    // pixels above the skirt's hem, which left the hip and the top of the
    // inner thigh as untouched canvas the instant nothing covered them, a
    // skirt shorter than default, both garments off entirely, and read as
    // the figure's legs not being attached to its body.
    parts = [bareSeat(sk, p, gap, wTop, wKnee, wCalf, wAnkle)];
  }
  // A knee sock goes over the leg and under the shoe, which in the reference
  // comes down over its lower end. The leg above it stops at its top edge: the
  // sock is narrower than our leg and a tube running on down inside it showed
  // as skin along both its sides.
  if (truthy(p.outfit.knee_sock_color) && !truthy(trouserColor)) {
    const stop = legCutTopY(sk, KNEE_SOCK_CUT) + sk.head_r * 0.04;
    parts = [
      `<clipPath id="${SOCK_CLIP_ID}"><rect x="0" y="0" width="${fmt1(sk.canvas_w)}" ` +
        `height="${fmt1(stop)}" /></clipPath><g clip-path="url(#${SOCK_CLIP_ID})">${parts[0]}</g>`,
    ];
  }
  if (truthy(p.outfit.knee_sock_color)) {
    for (const side of [-1, 1]) parts.push(drawLegCut(sk, KNEE_SOCK_CUT, p.outfit.knee_sock_color as string, gap, side));
  }
  // A bare foot on a bare leg takes the leg's slimmer ankle; a boot, or a foot
  // under trousers, keeps the width it had.
  const bare = !truthy(trouserColor) && p.outfit.boot_color === null;
  const footW = bare ? bareAnkle(sk, wKnee, wAnkle) : wAnkle;
  for (const side of [-1, 1]) parts.push(boot(sk, p, sk.head_cx + side * gap, footW, side));
  return parts.join("");
}

// Where the legs part, measured hip to knee. Both canon sheets put the crotch at
// very nearly a quarter of belt-to-floor, 0.28 on the chibi and 0.23 on the
// adult, which lands within a percent of the body's height of this one fraction
// at both builds, so it does not need to ride the build.
//
// Those two numbers are where *background* first shows between the legs, which
// is a stroke-width below the point the two edges actually meet: until the notch
// is wider than the two strokes facing each other across it, it paints solid. So
// ours reads a little lower than the canon's at the same fraction, ours being the
// heavier line. Correcting for it would move the crotch by well under a percent
// of the figure's height, and the render is right by eye, so it is left alone.
export const CROTCH_AT = 0.28;
// With the pelvis bare, how far below the hip the legs may part, in head radii.
// The fraction above is right on the cast, whose thigh is short. On a leg as
// long as Risa's it lands half a head down and the briefs become a panel over
// the thigh. The cast's own drop is 0.27 and Katherina's 0.36, so 0.38 holds
// them and only reins in the longer leg. Dressed, the fraction stays, so a
// skirt's thigh does not move.
export const BARE_PELVIS = 0.38;

/**
 * Where the legs part: `_CROTCH_AT` of the way from the hip to the knee,
 * the real one (`Skeleton.knee_y`, `docs/tall-chibi-plan.md`, R4a). Bare it
 * read a real knee from step 4d of `bare-body-plan.md`; clothed it read the
 * boot landmark, above the hip on the long-torso profile, until the knee was
 * made real for everyone.
 */
export function crotchY(sk: Skeleton, p: CharacterParams): number {
  let y = sk.hip_y + (sk.knee_y - sk.hip_y) * CROTCH_AT;
  if (p.outfit.tunic_color === null && p.outfit.skirt_color === null && p.outfit.trouser_color === null) {
    y = pyMin(y, sk.hip_y + sk.head_r * BARE_PELVIS);
  }
  return y;
}

/**
 * Where a garment covering both legs as one seat starts: inside the belt
 * band when the tunic is tucked, the hip otherwise. Shared by `_trousers` and
 * `_bare_seat` so a tucked tunic with no trousers still has something under
 * it rather than a gap the width of the belt.
 */
export function legTuckTopY(sk: Skeleton, p: CharacterParams): number {
  const [beltY, beltH] = beltBand(sk);
  return truthy(p.outfit.tunic_tucked) ? beltY + beltH * 0.5 : sk.hip_y;
}

/**
 * A seat with a notch cut out of it, not two tubes: one closed silhouette
 * from the waist to both ankles, meeting at `crotch_y` and parting below it.
 *
 * The canon draws no gap between the legs above the crotch and no seam across
 * the top of the thigh either. Measured on both Satoshi sheets, the silhouette
 * below the belt is a single run until roughly a quarter of the way to the
 * floor, where background first appears between the legs, and from there the
 * slot opens smoothly to about a third of the garment's width by the boot.
 *
 * Shared by `_trousers` and `_bare_seat`, which differ only in fill, outline
 * weight and whether a seam gets drawn on top: the crotch itself is the one
 * thing that must never draw two different ways depending on what the legs
 * are wearing.
 */
export function seatNotchD(
  sk: Skeleton,
  cx: number,
  gap: number,
  top_y: number,
  crotch_y: number,
  w_top: number,
  w_knee: number,
  w_calf: number,
  w_ankle: number,
  knee = 0.0,
): string {
  const calfY = sk.knee_y + (sk.ankle_y - sk.knee_y) * 0.35;
  // The two outer edges run straight, at the leg's own width, from the belt all
  // the way to the ankle: the only taper in them is the leg's own 1.10 thigh to
  // 0.92 ankle, which is a couple of degrees off vertical.
  //
  // Flaring them out to `hip_half_w` at the hip was tried first, on the
  // reasoning that the garment should carry the body's width through the belt.
  // It does not work here, and the owner's call on it was to put the straight
  // line back. Our chibi's leg is 0.24 of its belt's half-width where the
  // canon's is 0.39 (`docs/gap-analysis.md`), so a hip drawn at full width has
  // to shed 40% of it before the knee, and no distribution of that hides it:
  // low it becomes a saddlebag on each side, high it becomes a wedge with the
  // leg thick at the hip and thin at the boot. A straight column is what the
  // canon draws at both builds anyway. The cost is that the belt is wider than
  // the trousers under it, and that is a leg-width gap, not a trouser one.
  const kneeCtrlY = sk.knee_y - (sk.knee_y - top_y) * 0.3;
  if (knee > 0.0) {
    return kneeNotchD(sk, cx, gap, top_y, crotch_y, w_top, w_knee, w_calf, w_ankle, knee, calfY, kneeCtrlY);
  }

  /** Belt to ankle down one side, on the leg's own contour throughout. */
  const outerDown = (s: number): string =>
    `Q ${fmt1(cx + s * (gap + w_top))} ${fmt1(kneeCtrlY)} ` +
    `${fmt1(cx + s * (gap + w_knee))} ${fmt1(sk.knee_y)} ` +
    `Q ${fmt1(cx + s * (gap + w_calf))} ${fmt1(calfY)} ` +
    `${fmt1(cx + s * (gap + w_ankle))} ${fmt1(sk.ankle_y)} `;

  /** One ankle's inside up to the crotch, which is the inseam. */
  const innerUp = (s: number): string =>
    `L ${fmt1(cx + s * (gap - w_ankle))} ${fmt1(sk.ankle_y)} ` +
    `Q ${fmt1(cx + s * (gap - w_top))} ${fmt1(sk.knee_y)} ${fmt1(cx)} ${fmt1(crotch_y)} `;

  const innerDown = (s: number): string =>
    `Q ${fmt1(cx + s * (gap - w_top))} ${fmt1(sk.knee_y)} ` +
    `${fmt1(cx + s * (gap - w_ankle))} ${fmt1(sk.ankle_y)} ` +
    `L ${fmt1(cx + s * (gap + w_ankle))} ${fmt1(sk.ankle_y)} `;

  const outerUp = (s: number): string =>
    `Q ${fmt1(cx + s * (gap + w_calf))} ${fmt1(calfY)} ` +
    `${fmt1(cx + s * (gap + w_knee))} ${fmt1(sk.knee_y)} ` +
    `Q ${fmt1(cx + s * (gap + w_top))} ${fmt1(kneeCtrlY)} ` +
    `${fmt1(cx + s * (gap + w_top))} ${fmt1(top_y)} `;

  const wWaist = gap + w_top;
  return (
    `M ${fmt1(cx - wWaist)} ${fmt1(top_y)} L ${fmt1(cx + wWaist)} ${fmt1(top_y)} ` +
    outerDown(1) +
    innerUp(1) +
    innerDown(-1) +
    outerUp(-1) +
    "Z"
  );
}

/**
 * Trousers as one garment: a seat with a notch cut out of it, not two tubes.
 *
 * What was here before was a wedge drawn behind two separately stroked tubes,
 * and the wedge's lower V hung below the tunic's hem between two legs that had
 * a slot of canvas running all the way up between them: it read as a flap
 * hanging off the belt rather than as the seat of a garment. `_seat_notch_d`
 * is the fix, shared with the bare-skin case in `_bare_seat` below.
 *
 * Starts inside the belt band when the tunic is tucked, which is the other
 * half of the same fix. The trousers used to begin at the hip, a good part of
 * the way down from the belt, with the tunic covering the difference, so the
 * tunic hung in a band below its own belt and the trousers appeared to start
 * at the tunic's hem. Both references tuck the tunic in and start the trousers
 * at the belt. Untucked they still begin at the hip, since a tunic hanging to
 * the hip is over them either way and a waist drawn under it could only ever
 * show through some later change to the garment above.
 */
export function trousers(
  sk: Skeleton,
  p: CharacterParams,
  color: string,
  gap: number,
  w_top: number,
  w_knee: number,
  w_calf: number,
  w_ankle: number,
): string {
  const cx = sk.head_cx;
  const topY = legTuckTopY(sk, p);
  const crotch = sk.hip_y + (sk.knee_y - sk.hip_y) * CROTCH_AT;
  const d = seatNotchD(sk, cx, gap, topY, crotch, w_top, w_knee, w_calf, w_ankle);
  // Rounded joins, because the inseam meets itself at a point at the crotch and
  // SVG's default miter shoots a spike off any sharp corner. `_hair_mass` hit
  // the same thing at a lock's tip.
  return (
    `<path d="${d}" fill="${colorStr(color)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)))}" ` +
    `stroke-linejoin="round" />` +
    trouserSeams(sk, p, color, gap, w_top, topY, crotch)
  );
}

// A fixed placeholder, not a character trait: nobody's design in
// the local character notes specifies underwear, so there is
// nothing for a per-character field to hold, the way there is for a tunic or a
// skirt. A plain neutral cotton tone, the way OUTLINE is a plain neutral line
// regardless of what it outlines.

/**
 * The lowest point of the skirt the figure wears, in pixels, or None without
 * one: a traced cut's own hem, otherwise the parametric skirt's.
 */
export function skirtBottomY(sk: Skeleton, p: CharacterParams): number | null {
  if (p.outfit.skirt_color === null) return null;
  if (p.outfit.skirt_cut === null) return skirtHemY(sk, p.outfit.skirt_length, p.outfit.skirt_length_chibi);
  const cut = cutNamed(SKIRT_CUTS, p.outfit.skirt_cut);
  const xf = garmentPlacement(sk, cut.ref_body);
  const ys: number[] = [];
  for (const [start, segs] of cut.fills) {
    for (const pt of [start, ...segs.map(([, end]) => end)]) ys.push(xf(pt)[1]);
  }
  return sk.head_cy + maxOf(ys) * sk.head_r;
}

/**
 * A modesty layer over the top of `_bare_seat`, not full-length: it never
 * reaches the point the legs part, so it needs no notch of its own and is
 * just a plain block with a shallow curved hem, the way a brief is cut higher
 * than trousers rather than a shorter copy of them.
 */
export function underpants(
  sk: Skeleton,
  color: string,
  gap: number,
  top_y: number,
  crotch_y: number,
  w_top: number,
  hem_cap: number | null = null,
): string {
  const cx = sk.head_cx;
  // Off the real knee: on the long-torso profile the landmark is above the
  // hip, and the hem came out above the top, the underpants gone entirely on
  // every untucked figure (`docs/bare-body-status.md`, steps 1 and 3).
  // Capped in head radii: the same fraction of Risa's thigh ran the hem into
  // a panel. 0.22 is past Katherina's 0.206, the longest brief that still
  // reads as one, so the cast is unchanged.
  const drop = pyMin((sk.knee_y - crotch_y) * 0.22, sk.head_r * 0.22);
  let hemY = crotch_y + drop;
  // Never below a skirt's hem: a short skirt, Risa's, ends above where this does,
  // and the thigh under it is bare skin in her reference.
  if (hem_cap !== null) hemY = pyMin(hemY, hem_cap - sk.head_r * 0.05);
  const wWaist = gap + w_top;
  // A little narrower at the hem than the waist, which is what a hem gathered
  // by elastic looks like rather than a straight-sided box.
  const wHem = wWaist * 0.82;
  const dip = (hemY - top_y) * 0.1;
  const d =
    `M ${fmt1(cx - wWaist)} ${fmt1(top_y)} L ${fmt1(cx + wWaist)} ${fmt1(top_y)} ` +
    `L ${fmt1(cx + wHem)} ${fmt1(hemY - dip)} ` +
    `Q ${fmt1(cx)} ${fmt1(hemY)} ${fmt1(cx - wHem)} ${fmt1(hemY - dip)} Z`;
  return (
    `<path d="${d}" fill="${colorStr(color)}" stroke="${OUTLINE}" ` +
    `stroke-width="${fmt2(outlineW(strokeW(sk), 0.85))}" stroke-linejoin="round" />`
  );
}

// The bare leg's knee (`docs/detail-plan.md`, D4; the owner's pick, 2026-09-27,
// from `harness/detail/knee_study.py`). A tube of a leg is the chibi's; a real
// one, front on, is about as wide at the calf as at the knee and six or seven
// tenths of it at the ankle. At full strength the knee comes in by `_KNEE_IN`
// of the leg, the calf's control sits `_CALF_CTRL` out from the narrowed knee
// (the curve peaking about 1.03 of it) and the bare ankle, the bare foot with
// it, goes to `_BARE_ANKLE` of the knee. Measured off the render: calf 1.04 and
// ankle 0.76 of the knee (the outline adds to both). It follows the limb taper,
// none at height 0.8 and full from 1.3, so a short figure keeps the chibi's
// leg. The trousers keep their own, measured run and the boots their width.
export const KNEE_IN = 0.1;
export const CALF_CTRL = 1.15;
export const BARE_ANKLE = 0.7;

/** How much of the bare leg's knee a figure is drawn with, 0 to 1. */
export function kneeStrength(sk: Skeleton): number {
  // `_TAPER_MAX` is a constant 0.5, so the division cannot be by zero.
  return pyMin(1.0, sk.limb_taper / TAPER_MAX);
}

/** The bare ankle's half-width at this figure's knee strength. */
export function bareAnkle(sk: Skeleton, w_knee: number, w_ankle: number): number {
  const k = kneeStrength(sk);
  return w_ankle + (w_knee * (1.0 - KNEE_IN * k) * BARE_ANKLE - w_ankle) * k;
}

/**
 * The parameter where the quadratic `p0`, `p1`, `p2` comes nearest height
 * `y`, found by bisection on its height, which runs one way from `p0` to `p2`
 * here; `_quad_crossing`'s closed form fails when the control's height is not
 * between the ends'.
 */
export function quadUAt(p0: Point, p1: Point, p2: Point, y: number): number {
  let lo = 0.0;
  let hi = 1.0;
  const rising = p2[1] >= p0[1];
  for (let i = 0; i < 40; i++) {
    const u = (lo + hi) / 2;
    const h = quadPoint(p0, p1, p2, u)[1];
    if ((h < y) === rising) lo = u;
    else hi = u;
  }
  return (lo + hi) / 2;
}

/**
 * `_seat_notch_d` with a knee at strength `k`. Continuous in `k`: the leg's
 * inside, one curve from the crotch to the ankle without a knee, is split at
 * the knee's height into the same curve in two halves, and each of its points
 * moves toward the knee's by `k`; the outside's knee, calf and ankle blend the
 * same way from the widths passed in.
 */
export function kneeNotchD(
  sk: Skeleton,
  cx: number,
  gap: number,
  top_y: number,
  crotch_y: number,
  w_top: number,
  w_knee: number,
  w_calf: number,
  w_ankle: number,
  k: number,
  calf_y: number,
  knee_ctrl_y: number,
): string {
  const wkFull = w_knee * (1.0 - KNEE_IN);
  const wk = w_knee * (1.0 - KNEE_IN * k);
  const wc = w_calf + (wk * CALF_CTRL - w_calf) * k;
  const wa = bareAnkle(sk, w_knee, w_ankle);

  const lerp = (a: Point, b: Point): Point => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k];

  const crotch: Point = [0.0, crotch_y];
  const ctrl: Point = [gap - w_top, sk.knee_y];
  const ankle: Point = [gap - w_ankle, sk.ankle_y];
  const [a, mid, b] = quadSplit(crotch, ctrl, ankle, quadUAt(crotch, ctrl, ankle, sk.knee_y));
  const thighInY = crotch_y + (sk.knee_y - crotch_y) * 0.5;
  const c1 = lerp(a, [gap - w_top, thighInY]);
  const m = lerp(mid, [gap - wkFull, sk.knee_y]);
  const c2 = lerp(b, [gap - wkFull * CALF_CTRL, calf_y]);
  const ankleIn: Point = [gap - wa, sk.ankle_y];

  const pt = (s: number, q: Point): string => `${fmt1(cx + s * q[0])} ${fmt1(q[1])}`;

  const outerDown = (s: number): string =>
    `Q ${fmt1(cx + s * (gap + w_top))} ${fmt1(knee_ctrl_y)} ${fmt1(cx + s * (gap + wk))} ${fmt1(sk.knee_y)} ` +
    `Q ${fmt1(cx + s * (gap + wc))} ${fmt1(calf_y)} ${fmt1(cx + s * (gap + wa))} ${fmt1(sk.ankle_y)} `;

  const innerUp = (s: number): string =>
    `L ${pt(s, ankleIn)} Q ${pt(s, c2)} ${pt(s, m)} Q ${pt(s, c1)} ${fmt1(cx)} ${fmt1(crotch_y)} `;

  const innerDown = (s: number): string =>
    `Q ${pt(s, c1)} ${pt(s, m)} Q ${pt(s, c2)} ${pt(s, ankleIn)} ` + `L ${fmt1(cx + s * (gap + wa))} ${fmt1(sk.ankle_y)} `;

  const outerUp = (s: number): string =>
    `Q ${fmt1(cx + s * (gap + wc))} ${fmt1(calf_y)} ${fmt1(cx + s * (gap + wk))} ${fmt1(sk.knee_y)} ` +
    `Q ${fmt1(cx + s * (gap + w_top))} ${fmt1(knee_ctrl_y)} ${fmt1(cx + s * (gap + w_top))} ${fmt1(top_y)} `;

  const wWaist = gap + w_top;
  return (
    `M ${fmt1(cx - wWaist)} ${fmt1(top_y)} L ${fmt1(cx + wWaist)} ${fmt1(top_y)} ` +
    outerDown(1) +
    innerUp(1) +
    innerDown(-1) +
    outerUp(-1) +
    "Z"
  );
}

/**
 * Bare legs, as one silhouette rather than two separate tubes with a gap
 * between them, the same fix `_trousers` got and for the same reason: two
 * independent shapes leave a slot of background between them, which used to
 * run all the way up to the hip the moment nothing else covered it, skirt and
 * trousers both off, or a skirt shorter than default. A placeholder pair of
 * underpants rides on top, so the figure reads as dressed rather than as a
 * body with a hole cut in the middle of it.
 */
export function bareSeat(
  sk: Skeleton,
  p: CharacterParams,
  gap: number,
  w_top: number,
  w_knee: number,
  w_calf: number,
  w_ankle: number,
): string {
  const cx = sk.head_cx;
  // With the tunic off there is no tuck to start inside, and the seat, and
  // the underpants on it, start at the hip for everyone: tucked presets came
  // out in shorts up to the belt line and untucked ones in briefs.
  const topY = p.outfit.tunic_color === null ? sk.hip_y : legTuckTopY(sk, p);
  // The underpants start a third of the way up to the waist from there: at
  // the hip itself they were a thin strip, and the torso's notch where the
  // legs part showed above them on the long-torso profile, whose crotch sits
  // above the hip (`docs/bare-body-status.md`, step 3). Capped like the hem,
  // so a long waist-to-hip does not hike them into a high panel. 0.22 is past
  // Katherina's 0.200.
  const rise = pyMin((sk.hip_y - sk.waist_y) * 0.35, sk.head_r * 0.22);
  const briefY = p.outfit.tunic_color === null ? topY - rise : topY;
  const crotch = crotchY(sk, p);
  const d = seatNotchD(sk, cx, gap, topY, crotch, w_top, w_knee, w_calf, w_ankle, kneeStrength(sk));
  // No tone down the leg, same as the old two-tube version: a stripe down a
  // leg reads the way one down a sleeve does, one flat surface with an outline
  // doing the work instead.
  return (
    `<path d="${d}" fill="${colorStr(p.skin_tone)}" stroke="${OUTLINE}" ` +
    `stroke-width="${fmt2(outlineW(strokeW(sk), 0.85))}" stroke-linejoin="round" />` +
    underpants(sk, p.outfit.underwear_color, gap, briefY, crotch, w_top, skirtBottomY(sk, p))
  );
}

/**
 * The fly and the two hip pocket seams.
 *
 * Lines rather than tone, the same call the skirt's folds and the underskirt's
 * pleats got. The fly ends on the crotch rather than at a fraction of the way
 * to the knee: it is the seam that runs down to where the legs part, so it has
 * to move when the crotch does.
 */
export function trouserSeams(
  sk: Skeleton,
  p: CharacterParams,
  color: string,
  gap: number,
  w_top: number,
  top_y: number,
  crotch_y: number,
): string {
  if (!truthy(p.shaded)) return "";
  const cx = sk.head_cx;
  const drop = crotch_y - top_y;
  const seamSw = pyMax(1.0, strokeW(sk) * 0.45);
  const parts = [
    `<line x1="${fmt1(cx)}" y1="${fmt1(top_y + drop * 0.12)}" x2="${fmt1(cx)}" y2="${fmt1(crotch_y)}" ` +
      `stroke="${shade(color)}" stroke-width="${fmt2(interiorW(seamSw))}" opacity="0.8" />`,
  ];
  for (const s of [-1, 1]) {
    parts.push(
      `<path d="M ${fmt1(cx + s * (gap + w_top * 0.9))} ${fmt1(top_y + drop * 0.16)} ` +
        `Q ${fmt1(cx + s * (gap + w_top * 0.4))} ${fmt1(top_y + drop * 0.46)} ` +
        `${fmt1(cx + s * (gap - w_top * 0.1))} ${fmt1(top_y + drop * 0.86)}" ` +
        `fill="none" stroke="${shade(color)}" stroke-width="${fmt2(interiorW(seamSw))}" opacity="0.8" />`,
    );
  }
  return parts.join("");
}

/**
 * One bare foot, where a boot would be (`docs/bare-body-plan.md`, step 5).
 *
 * The boot's own silhouette with the shaft taken away, since it is the same
 * foot in the same duck stance: down from the ankle to the heel, along the
 * sole, round the toe pointing a little outward, and back up the instep. A
 * little slimmer than the boot, which adds leather, and rounder at the toe.
 * No toes drawn: at the chibi they would be grit, the way the boot's eyelets
 * were.
 *
 * Its fill reaches just over the end of the leg, whose path ends in a
 * stroked edge across the ankle; its outline starts at the ankle, at the
 * leg's own weight, so the leg runs into it. Drawn from above the ankle at
 * full weight, the outline stepped out of the leg's there and read as the
 * top of a sock.
 */
export function bareFoot(sk: Skeleton, p: CharacterParams, cx: number, w_ankle: number, side: number): string {
  const footW = sk.leg_half_w * (2.08 - 0.08 * sk.build) * 0.85;
  const footH = sk.foot_y - sk.ankle_y;
  const instepY = sk.ankle_y + footH * 0.3;
  const heelW = pyMax(footW * 0.42, w_ankle);
  const toeX = heelW + footW * 0.32;
  const r = footW * 0.22;

  /** Offsets are for the right foot, toe toward +x; the left mirrors. */
  const x = (offset: number): number => cx + side * offset;

  const edge =
    `M ${fmt1(x(w_ankle))} ${fmt1(sk.ankle_y)} ` +
    `Q ${fmt1(x(w_ankle * 1.06))} ${fmt1(sk.ankle_y + footH * 0.16)} ${fmt1(x(w_ankle * 1.3))} ${fmt1(sk.ankle_y + footH * 0.26)} ` +
    `Q ${fmt1(x(toeX * 0.96))} ${fmt1(sk.ankle_y + footH * 0.42)} ${fmt1(x(toeX))} ${fmt1(sk.foot_y - r * 1.2)} ` +
    `Q ${fmt1(x(toeX))} ${fmt1(sk.foot_y)} ${fmt1(x(toeX - r))} ${fmt1(sk.foot_y)} ` +
    `L ${fmt1(x(-heelW + r))} ${fmt1(sk.foot_y)} ` +
    `Q ${fmt1(x(-heelW))} ${fmt1(sk.foot_y)} ${fmt1(x(-heelW))} ${fmt1(sk.foot_y - r)} ` +
    `Q ${fmt1(x(-heelW))} ${fmt1(instepY)} ${fmt1(x(-w_ankle))} ${fmt1(sk.ankle_y)} `;
  const sw = strokeW(sk) * 0.85;
  // Up over the leg's end only a little, and inside its side lines, which a
  // full-width strip reaching higher cut through.
  const inner = w_ankle - sw * 0.5;
  const coverY = sk.ankle_y - sw * 1.5;
  const fill =
    `${edge}L ${fmt1(x(-inner))} ${fmt1(sk.ankle_y)} L ${fmt1(x(-inner))} ${fmt1(coverY)} ` +
    `L ${fmt1(x(inner))} ${fmt1(coverY)} L ${fmt1(x(inner))} ${fmt1(sk.ankle_y)} Z`;
  return (
    `<path d="${fill}" fill="${colorStr(p.skin_tone)}" stroke="none" />` +
    `<path d="${edge}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw))}" ` +
    `stroke-linejoin="round" />`
  );
}

/**
 * One boot: a shaft over the ankle, an instep, and a toe pointing a
 * little outward, the pair standing in the canon's slight duck stance. The
 * toe is what stopped this reading as a brown block: a symmetric rounded
 * rectangle has no front, and a foot is mostly front.
 *
 * Cross-laces run down the instep. The canon keeps them at both builds, so
 * the old rule that they do not survive chibification is gone with the old
 * reference that set it. With no boot colour, a bare foot (`_bare_foot`).
 */
export function boot(sk: Skeleton, p: CharacterParams, cx: number, w_ankle: number, side: number): string {
  const color = p.outfit.boot_color;
  if (color === null) return bareFoot(sk, p, cx, w_ankle, side);
  if (p.outfit.boot_cut !== null) {
    return drawLegCut(sk, cutNamed(BOOT_CUTS, p.outfit.boot_cut), color, Math.abs(cx - sk.head_cx), side);
  }
  // A foot is a foot: measured off the leg rather than off the ankle, so it
  // keeps its size when the shin's width is retuned. As a multiple of the ankle
  // it doubled the moment the leg stopped tapering to a point. The multiplier
  // was retuned when the chibi leg thickened from 0.15 to 0.22 head radii, so
  // the boot itself, already sized to the canon, came out the same.
  // `docs/gap-analysis.md` had this 17% to 27% narrow of the canon through the
  // foot at the realistic build. It is not: measured on the boot's own colour
  // rather than on the silhouette, the canon's adult boot is 0.058 of figure
  // height across and ours is 0.076, so ours is a third *wider*. The silhouette
  // agreed only because the canon stands its feet further apart than we do, and
  // outer-edge-to-outer-edge is stance plus boot. Widening this to chase that
  // number was tried in task 68 and took the whole foot 22% past the canon.
  const bootW = sk.leg_half_w * (2.08 - 0.08 * sk.build);
  const footH = sk.foot_y - sk.ankle_y;
  // The shaft climbs a third of the way to the knee, so it stays a boot rather
  // than becoming a waders as the shin gets longer at taller builds.
  //
  // `boot_shaft` extends that toward the knee without changing anything else
  // about the boot: the five uniformed characters and Kyoko all wear a tall
  // boot with the trouser tucked into it, which is a different garment from the
  // ankle boot the rest of the cast wears and reads as one at any size. It
  // stops a little short of the knee itself, because a shaft that reaches the
  // joint reads as a legging rather than as a boot pulled on.
  //
  // `sk.boot_y` is where a body profile put the default shaft's reference, its
  // own reference's boot top; the tall shaft aims at the real knee,
  // `sk.knee_y`, which on `tall_chibi_long_torso` is well below that landmark
  // (the landmark is above the hip there: a shaft sent to it came up to the
  // belt). The two were one field until R4a of `docs/tall-chibi-plan.md`.
  const baseTop = sk.ankle_y - (sk.ankle_y - sk.boot_y) * 0.32;
  const kneeY = sk.knee_y;
  const tallTop = sk.ankle_y - (sk.ankle_y - kneeY) * 0.92;
  const topY = baseTop + (tallTop - baseTop) * pyMax(0.0, pyMin(1.0, p.outfit.boot_shaft));
  // Off the ankle it wraps, not off the knee above it, so the shaft cannot come
  // out wider than the leg going into it.
  const shaftW = w_ankle * 1.1;
  const instepY = sk.ankle_y + footH * 0.3;
  // The heel can never come in narrower than the shaft above it, or the boot
  // tucks inward below the ankle, which is what it briefly did at realistic,
  // where the leg is thick against the whole boot.
  const heelW = pyMax(bootW * 0.42, shaftW * 1.02);
  const toeX = heelW + bootW * 0.34;
  const r = bootW * 0.18;

  /** Offsets are for the right boot, toe toward +x; the left mirrors. */
  const x = (offset: number): number => cx + side * offset;

  const d =
    `M ${fmt1(x(-shaftW))} ${fmt1(topY)} ` +
    `L ${fmt1(x(-shaftW))} ${fmt1(sk.ankle_y)} ` +
    `Q ${fmt1(x(-heelW))} ${fmt1(instepY)} ${fmt1(x(-heelW))} ${fmt1(sk.foot_y - r)} ` +
    `Q ${fmt1(x(-heelW))} ${fmt1(sk.foot_y)} ${fmt1(x(-heelW + r))} ${fmt1(sk.foot_y)} ` +
    `L ${fmt1(x(toeX - r))} ${fmt1(sk.foot_y)} ` +
    `Q ${fmt1(x(toeX))} ${fmt1(sk.foot_y)} ${fmt1(x(toeX))} ${fmt1(sk.foot_y - r * 1.2)} ` +
    `Q ${fmt1(x(toeX * 0.96))} ${fmt1(sk.ankle_y + footH * 0.42)} ${fmt1(x(shaftW * 1.3))} ${fmt1(sk.ankle_y + footH * 0.26)} ` +
    `Q ${fmt1(x(shaftW * 1.06))} ${fmt1(sk.ankle_y + footH * 0.16)} ${fmt1(x(shaftW))} ${fmt1(sk.ankle_y)} ` +
    `L ${fmt1(x(shaftW))} ${fmt1(topY)} ` +
    `Z`;
  const parts = [`<path d="${d}" fill="${colorStr(color)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)))}" />`];
  if (!truthy(p.shaded)) return parts.join("");
  const soleH = footH * 0.24;
  parts.push(
    `<path d="M ${fmt1(x(-heelW))} ${fmt1(sk.foot_y - soleH)} L ${fmt1(x(toeX))} ${fmt1(sk.foot_y - soleH)} ` +
      `L ${fmt1(x(toeX))} ${fmt1(sk.foot_y - r)} ` +
      `Q ${fmt1(x(toeX))} ${fmt1(sk.foot_y)} ${fmt1(x(toeX - r))} ${fmt1(sk.foot_y)} ` +
      `L ${fmt1(x(-heelW + r))} ${fmt1(sk.foot_y)} ` +
      `Q ${fmt1(x(-heelW))} ${fmt1(sk.foot_y)} ${fmt1(x(-heelW))} ${fmt1(sk.foot_y - r)} ` +
      `Z" fill="${shade(color, 0.7)}" />`,
  );
  // Turned cuff at the top of the shaft, the one thing that says "boot" rather
  // than "sock". A band now rather than a line: the canon turns the leather over
  // and the depth of the turn is what reads, where a single line reads as a
  // seam. This is the small-element case the flat-colour rule leaves open, a
  // turn of material showing its thickness.
  const cuffH = (sk.ankle_y - topY) * 0.34;
  parts.push(
    `<rect x="${fmt1(cx - shaftW)}" y="${fmt1(topY)}" width="${fmt1(shaftW * 2)}" ` +
      `height="${fmt1(cuffH)}" fill="${shade(color, 0.78)}" stroke="${OUTLINE}" ` +
      `stroke-width="${fmt2(interiorW(strokeW(sk), 0.7))}" />`,
  );
  // The tongue, under the laces and above the instep. Drawn before them so they
  // cross it, which is the only way a tongue reads on a front view.
  const tongueW = shaftW * 0.5;
  parts.push(
    `<path d="M ${fmt1(cx - tongueW)} ${fmt1(topY + cuffH)} L ${fmt1(cx + tongueW)} ${fmt1(topY + cuffH)} ` +
      `Q ${fmt1(cx + tongueW * 0.86)} ${fmt1(instepY + footH * 0.1)} ` +
      `${fmt1(cx)} ${fmt1(instepY + footH * 0.18)} ` +
      `Q ${fmt1(cx - tongueW * 0.86)} ${fmt1(instepY + footH * 0.1)} ${fmt1(cx - tongueW)} ${fmt1(topY + cuffH)} Z" ` +
      `fill="${shade(color, 0.88)}" stroke="${OUTLINE}" stroke-width="${fmt2(interiorW(strokeW(sk), 0.55))}" />`,
  );
  // Cross-laces down the instep, between the cuff and the sole. Dark tone of
  // the boot's own leather, thin: they divide a surface, they do not bound one.
  const laceColor = shade(color, 0.45);
  const laceW = shaftW * 0.52;
  const laceTop = topY + (sk.ankle_y - topY) * 0.45;
  const laceBot = instepY + footH * 0.16;
  const laceSw = pyMax(1.0, strokeW(sk) * 0.4);
  const steps = 3;
  const dy = (laceBot - laceTop) / steps;
  for (let i = 0; i < steps; i++) {
    const y0 = laceTop + i * dy;
    for (const s of [-1, 1]) {
      parts.push(
        `<line x1="${fmt1(cx - s * laceW)}" y1="${fmt1(y0)}" x2="${fmt1(cx + s * laceW)}" y2="${fmt1(y0 + dy)}" ` +
          `stroke="${laceColor}" stroke-width="${fmt2(interiorW(laceSw))}" stroke-linecap="round" />`,
      );
    }
  }
  return parts.join("");
}
