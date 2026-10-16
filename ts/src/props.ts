// The props and headgear: the headscarf, the witch's hat, the staff, the katana and the bat familiar. Port of the
// `parts-props` domain of character.py (`hat_underside` lives in character.ts). The traced coordinates are in
// `props-tables.ts`, generated from the Python by `harness/ts_port/gen_props.py`.

import { OUTLINE, curve, interiorW, outlineW, strokeW } from "./character.ts";
import { shade } from "./colorutil.ts";
import { hairEdgeX } from "./core-head.ts";
import { fistGrips, mittenPlacement, tracedPlacement } from "./core-limbs-hands.ts";
import { armLine, armPivot, beltBand, handLength } from "./core-limbs.ts";
import type { CharacterParams } from "./params.ts";
import {
  HAND_FIST_CHANNEL,
  HAT_BAND,
  HAT_BUCKLE,
  HAT_CREASES,
  HAT_CROWN,
  KATANA_BRASS,
  KATANA_DIAMOND,
  KATANA_DIAMONDS,
  KATANA_FUCHI,
  KATANA_GUARD_HALF_V,
  KATANA_HIP_X,
  KATANA_HIP_Y,
  KATANA_KASHIRA,
  KATANA_KOJIRI,
  KATANA_MAX_TILT,
  KATANA_REF_BELT,
  KATANA_REF_GROUND,
  KATANA_RING_BROWN,
  KATANA_RING_DARK,
  KATANA_SAYA,
  KATANA_STOUT,
  KATANA_STRETCH_FROM,
  KATANA_STRETCH_TO,
  KATANA_TILT,
  KATANA_TIP_U,
  KATANA_TRACED_LENGTH,
  KATANA_TSUBA,
  KATANA_TSUKA,
  KOU_BODY,
  KOU_CENTRE_CHIBI,
  KOU_CENTRE_REAL,
  KOU_CHIBI_BUILD,
  KOU_EYES,
  KOU_LINES,
  KOU_PUPIL,
  KOU_SPAN_CHIBI,
  KOU_SPAN_REAL,
  KOU_WINGS,
  KOU_WING_CELLS,
  SCARF_CLEAR,
  SCARF_EDGE_Y,
  STAFF_CRYSTAL,
  STAFF_FACETS_DARK,
  STAFF_FACETS_LIGHT,
  STAFF_GRIP,
  STAFF_STRANDS,
  STAFF_TIP,
  STAFF_TOP_Y,
  STAFF_WOOD,
} from "./props-tables.ts";
import { pyValueRepr } from "./pyvalue.ts";
import { argMax, fmt1, fmt2, pyAcos, pyCos, pyDiv, pyHypot, pyMax, pyMin, pySin, pySum, radians, truthy } from "./pynum.ts";
import type { Skeleton } from "./skeleton.ts";
import type { Chain, Point, Segment } from "./tables.ts";
import { HAT_BRIM } from "./tables.ts";

/**
 * `f"{x}"` of a colour field. A link or a model's request can put an int, a bool or a list in a colour field, and Python
 * writes what `str()` makes of it into the attribute (`fill="5"`, `fill="['#fff']"`), where a function that parses the
 * colour (`shade`) would raise instead. A string is itself.
 */
const pyStr = (v: unknown): string => (typeof v === "string" ? v : pyValueRepr(v));

/** Every point of a chain, in the order Python's `[start, *(q for seg in segs for q in seg)]` lists them. */
function chainPoints(chain: Chain): Point[] {
  const pts: Point[] = [chain[0]];
  for (const seg of chain[1]) for (const q of seg) pts.push(q);
  return pts;
}

/** A chain with `f` applied to every point. */
function mapChain(chain: Chain, f: (q: Point) => Point): Chain {
  return [f(chain[0]), chain[1].map(([c, e]): Segment => [f(c), f(e)])];
}

// ---------------------------------------------------------------------------------------------------------
// The headscarf

/**
 * A cloth tied over the crown, with a knot at the side.
 *
 * Over the hair and over the fringe, because a scarf covers what it is tied
 * over; the hair below its edge still shows, which is what stops it reading as
 * a swim cap.
 *
 * It is the single strongest signal Chiyo's reference carries, and none of the
 * levers `aged()` has could reach it: age there is the aperture and the brow,
 * and a working woman's headscarf is neither. Worth having as a garment rather
 * than as part of a hairstyle, since it is a thing put on and taken off and
 * anyone could wear one.
 *
 * The edge sits low at the sides and dips at the brow, which is how a scarf
 * tied at the back sits. Level across, it reads as a headband.
 */
export function headscarf(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.headscarf_color === null) return "";
  const cx = sk.head_cx;
  const cy = sk.head_cy;
  const r = sk.head_r;
  const color = p.outfit.headscarf_color;
  const sw = strokeW(sk);
  const edgeY = SCARF_EDGE_Y;
  // **The hair's width, not the skull's.** This part already knew the rule and
  // applied it in one axis only: `crown` below clears the cut rather than the
  // bone, and this line took the bone. On a long cut that is a fifth of a head
  // radius of hair standing outside the cloth tied over it, so the two outlines
  // cross and the cap reads as a shape painted on the hair rather than as
  // something put on. The owner's report on 2026-08-09.
  //
  // The height this is read at barely matters, which is worth knowing before
  // anyone moves `edge_y`: across the whole band from -0.36 to -0.16 the cut's
  // silhouette runs 1.217 to 1.248, because the falls are near vertical where
  // they pass the temple. The skull over the same band moves twice as far.
  const xEdge = hairEdgeX(edgeY, sk, p) * SCARF_CLEAR;
  // It has to clear the hair, not the skull, or it is buried the way the first
  // topknot was. The cuts top out near -1.28 head radii, and a scarf tied over
  // one sits on it rather than replacing it.
  const crown = -1.33;
  // An elliptical arc, not a chain of quadratics. Two attempts at this with
  // quadratics came out square-topped, because a quadratic whose control shares
  // its endpoint's height runs flat into that endpoint, and every arrangement
  // of two or four of them that fixes the top breaks the sides. An arc states
  // the dome directly and cannot be flat anywhere.
  const rx = xEdge * r;
  const ry = (edgeY - crown) * r;
  const leftX = cx - rx;
  const rightX = cx + rx;
  const edgePy = cy + edgeY * r;
  const d =
    `M ${fmt1(leftX)} ${fmt1(edgePy)} ` +
    `A ${fmt1(rx)} ${fmt1(ry)} 0 0 1 ${fmt1(rightX)} ${fmt1(edgePy)} ` +
    // The brow edge, dipping toward the face in the middle. A straight run
    // between the two temples is a headband.
    `Q ${fmt1(cx)} ${fmt1(cy + (edgeY + 0.3) * r)} ${fmt1(leftX)} ${fmt1(edgePy)} Z`;
  // The knot, off to one side where a scarf is tied. Two small lobes, because
  // one is a bump and two is a knot.
  const kx = cx + xEdge * r * 0.94;
  const ky = cy - r * 0.52;
  const lobe = r * 0.17;
  const lobes: readonly Point[] = [
    [0.55, -0.5],
    [0.95, 0.6],
  ];
  const knot = lobes
    .map(
      ([dx, dy]) =>
        `<ellipse cx="${fmt1(kx + dx * lobe)}" cy="${fmt1(ky + dy * lobe)}" rx="${fmt1(lobe)}" ` +
        `ry="${fmt1(lobe * 0.82)}" fill="${pyStr(color)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw))}" />`,
    )
    .join("");
  return `<path d="${d}" fill="${pyStr(color)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw))}" />${knot}`;
}

// ---------------------------------------------------------------------------------------------------------
// The witch's hat

/**
 * A pointed witch's hat's near side: brim, crown, band and bow, over everything.
 *
 * Over the hair mass and the fringe both, the way the headscarf sits over
 * them: a hat is put on, not grown, and it covers what it is put over. It
 * does not size itself off `_hair_edge_x` the way the headscarf does: its
 * shape is the reference's (see the comment above `_HAT_UNDERSIDE`), and the
 * brim is wide enough that every haircut's crown is under it. The far side
 * of the brim is `_hat_underside`, at the back of the figure.
 *
 * Back to front: the brim's top surface with the whole hat above it in the
 * hat colour, the crown over that, the band and its bow in the band colour,
 * and the creases last, as line work.
 */
export function hat(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.hat_color === null) return "";
  const cx = sk.head_cx;
  const cy = sk.head_cy;
  const r = sk.head_r;
  const color = p.outfit.hat_color;
  const sw = strokeW(sk);

  const shape = (chain: Chain, fill: string): string => {
    const d = curve(cx, cy, r, chain[0], chain[1]);
    return `<path d="${d}" fill="${pyStr(fill)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw))}" />`;
  };

  const parts = [shape(HAT_BRIM, color), shape(HAT_CROWN, color)];
  const bandColor = p.outfit.hat_band_color;
  if (bandColor !== null) {
    parts.push(shape(HAT_BAND, bandColor));
    for (const piece of HAT_BUCKLE) parts.push(shape(piece, bandColor));
  }
  for (const crease of HAT_CREASES) {
    const d = curve(cx, cy, r, crease[0], crease[1], false);
    parts.push(
      `<path d="${d}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(interiorW(sw, 0.8))}" ` + 'stroke-linecap="round" />',
    );
  }
  return parts.join("");
}

// ---------------------------------------------------------------------------------------------------------
// The staff

/** Where the staff runs through the fist, in its own units (`HAND_FIST_CHANNEL`). */
export function gripChannel(): Point {
  return HAND_FIST_CHANNEL;
}

/** The recorded calls name this table by its Python name (`_HAND_FIST_CHANNEL`), so it is exported under it as well. */
export const _HAND_FIST_CHANNEL = HAND_FIST_CHANNEL;

/**
 * The middle of a hand, in head radii, with its arm's swing applied.
 *
 * `s` is the side as `_arms` loops it: -1 the viewer's left. What a held
 * thing is placed by: the palm sits about halfway down the mitten.
 */
export function handCentre(sk: Skeleton, p: CharacterParams, s: number): Point {
  const [, , centreWrist, wristY] = armLine(sk);
  const [px, py] = armPivot(sk, p, s);
  let [hx, hy] = mittenPlacement(sk, p, s, sk.head_cx + s * centreWrist, wristY)(0.0, handLength(sk) * 0.5);
  if (fistGrips(p, s)) {
    // A fist holds the staff in its channel (`_grip_channel`).
    [hx, hy] = tracedPlacement(sk, p, s)(gripChannel());
  }
  const swing = s === -1 ? p.right_arm_out : p.left_arm_out;
  const a = radians(-s * swing);
  const rx = px + (hx - px) * pyCos(a) - (hy - py) * pySin(a);
  const ry = py + (hx - px) * pySin(a) + (hy - py) * pyCos(a);
  return [pyDiv(rx - sk.head_cx, sk.head_r), pyDiv(ry - sk.head_cy, sk.head_r)];
}

/**
 * Map the staff's reference head radii onto this figure's, as a point function.
 *
 * The grip goes to the centre of the hand holding it, and the staff divides
 * there. Above the grip it keeps the reference's shape at one scale, the one
 * that puts the top of the ornament at the reference's own height against the
 * head (`_STAFF_TOP_Y`): at chibi that scale is close to 1, since the chibi's
 * held-out hand sits almost where the reference's does. Below the grip the
 * shaft keeps its lean and its width and is shortened (or lengthened) along its
 * own axis only, so the foot lands on the ground: the reference's figure is
 * about three and a half heads tall and this one's chibi is 2.4, so a staff
 * carried at the reference's scale would stand a head and a half into the
 * floor. Widths across the shaft take the upper scale everywhere, so the
 * shaft does not change thickness at the hand. The shaft below the fist was
 * smoothed before tracing, since that shortening bunches small knots into
 * spikes.
 */
export function staffPlacement(sk: Skeleton, p: CharacterParams): (pt: Point) => Point {
  const [hx, hy] = handCentre(sk, p, -1);
  const [gx, gy] = STAFF_GRIP;
  const [tx, ty] = STAFF_TIP;
  // The grip and the tip are distinct constants, so `length` and the divisors below are never zero.
  const length = pyHypot(tx - gx, ty - gy);
  const ax = (tx - gx) / length;
  const ay = (ty - gy) / length;
  const kUp = (hy - STAFF_TOP_Y) / (gy - STAFF_TOP_Y);
  const ground = pyDiv(sk.foot_y - sk.head_cy, sk.head_r);
  const kLow = (ground - hy) / (ty - gy);

  const placed = (pt: Point): Point => {
    const dx = pt[0] - gx;
    const dy = pt[1] - gy;
    let along = dx * ax + dy * ay;
    let across = -dx * ay + dy * ax;
    const k = along <= 0 ? kUp : kLow;
    along *= k;
    across *= kUp;
    return [hx + along * ax - across * ay, hy + along * ay + across * ax];
  };

  // The ornament reaches out past the hand, and a hat's headroom narrows the
  // canvas in head radii, so at chibi its outer prong lands on the canvas edge.
  // Slide the whole staff inward by exactly what keeps its outline on the page
  // (the chain's controls bound the curve), and by nothing when it already fits.
  const xs = chainPoints(STAFF_WOOD).map((q) => placed(q)[0]);
  const reach = pyMin(xs[0] as number, ...xs.slice(1));
  const edge = pyDiv(-sk.canvas_w / 2 + strokeW(sk), sk.head_r);
  const shift = pyMax(0.0, edge - reach);

  return (pt: Point): Point => {
    const [x, y] = placed(pt);
    return [x + shift, y];
  };
}

/**
 * A wizard's staff held in the character's own right hand (the viewer's left).
 *
 * Drawn before the arms, so the hand closes over the shaft and the sleeve
 * passes in front of it, and after the hair and every garment, so the staff is
 * in front of the body it is held beside. Back to front: the wooden silhouette,
 * its strands, then the crystal: mid tone, dark and light faces, and its
 * outline last so the faces stay inside it.
 */
export function staff(sk: Skeleton, p: CharacterParams): string {
  const wood = p.outfit.staff_color;
  if (wood === null) return "";
  const cx = sk.head_cx;
  const cy = sk.head_cy;
  const r = sk.head_r;
  const sw = strokeW(sk);
  const xf = staffPlacement(sk, p);

  const d = (chain: Chain): string => {
    const [start, segs] = chain;
    return curve(cx, cy, r, xf(start), segs.map(([c, e]): Segment => [xf(c), xf(e)]));
  };

  const parts: string[] = [`<path d="${d(STAFF_WOOD)}" fill="${pyStr(wood)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw))}" />`];
  for (const strand of STAFF_STRANDS) {
    parts.push(
      `<path d="${d(strand)}" fill="${pyStr(wood)}" stroke="${OUTLINE}" stroke-width="${fmt2(interiorW(sw, 0.6))}" ` + 'stroke-linejoin="round" />',
    );
  }
  const crystal = p.outfit.staff_crystal_color;
  if (crystal !== null) {
    parts.push(`<path d="${d(STAFF_CRYSTAL)}" fill="${pyStr(crystal)}" />`);
    const dark = shade(crystal, 0.88, 1.1);
    const light = shade(crystal, 1.03, 0.54);
    for (const face of STAFF_FACETS_DARK) parts.push(`<path d="${d(face)}" fill="${dark}" />`);
    for (const face of STAFF_FACETS_LIGHT) parts.push(`<path d="${d(face)}" fill="${light}" />`);
    parts.push(`<path d="${d(STAFF_CRYSTAL)}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw))}" />`);
  }
  return parts.join("");
}

// (end of the traced staff)

// ---------------------------------------------------------------------------------------------------------
// The katana

/**
 * How much the plain scabbard grows for a sword `length` times as long, so
 * the whole sword is `length` times the traced one.
 */
export function katanaStretchFactor(length: number): number {
  // The divisor is the constant 2.215 - 0.375, never zero.
  return 1.0 + ((length - 1.0) * KATANA_TRACED_LENGTH) / (KATANA_STRETCH_TO - KATANA_STRETCH_FROM);
}

/**
 * The katana's own frame, lengthened: points on the scabbard's stretch grow
 * along the axis, the cap below it moves as one, everything above is unchanged.
 */
export function katanaStretched(length: number): (pt: Point) => Point {
  const f = katanaStretchFactor(length);
  const a = KATANA_STRETCH_FROM;
  const b = KATANA_STRETCH_TO;

  return (pt: Point): Point => {
    const [u, v] = pt;
    if (u <= a) return pt;
    if (u >= b) return [u + (f - 1.0) * (b - a), v];
    return [a + (u - a) * f, v];
  };
}

/**
 * Map the katana's own frame onto this figure, as a point function in head
 * radii.
 *
 * It hangs from the belt on the character's left, the viewer's right, at the
 * reference's tilt. The guard sits where the reference's does against its belt,
 * a share of the belt's half-width across and a stretch below its centre, and the
 * sword is scaled by the figure's height (crown to sole, against the reference's)
 * rather than by the head, so it stays a similar share of the figure whichever
 * body it hangs on (0.46 of the reference figure's height, 0.58 of its belt to
 * sole).
 */
export function katanaPlacement(sk: Skeleton, length = 1.0): (pt: Point) => Point {
  const r = sk.head_r;
  const [beltY, beltH] = beltBand(sk);
  const ground = pyDiv(sk.foot_y - sk.head_cy, r);
  const beltC = pyDiv(beltY + beltH / 2 - sk.head_cy, r);
  // Between the two ways of keeping it in proportion: by the figure's height
  // (crown to sole), which puts our shorter legs' tip below the boot top, and by
  // the belt-to-sole distance, which makes it a short sword; the reference's tip
  // stops well above its boots.
  // (The divisors here are `_KATANA_REF_GROUND + 1.0` and `_KATANA_REF_GROUND - _KATANA_REF_BELT`, constants that are not zero.)
  const byHeight = (ground + 1.0) / (KATANA_REF_GROUND + 1.0);
  const byLeg = (ground - beltC) / (KATANA_REF_GROUND - KATANA_REF_BELT);
  const k = (byHeight + byLeg) / 2;
  const beltHalf = pyDiv(sk.waist_half_w * 1.03, r);
  let ox = KATANA_HIP_X * beltHalf;
  // The reference's arm hangs clear of its hip, so the sword sits in the gap
  // between the two. Ours hangs closer in, and the arm is drawn over the sword,
  // so at the reference's proportion it covers half the guard. Pull the guard in
  // until its outer edge clears the arm's inner edge (at the elbow's height, which
  // is where the belt is) by a stroke.
  const [centreTop, , centreWrist] = armLine(sk);
  const centreElbow = centreTop + (centreWrist - centreTop) * 0.35;
  const armInner = pyDiv(centreElbow - sk.arm_half_w * (1.0 - 0.15 * sk.build), r);
  const guardHalf = KATANA_GUARD_HALF_V * k * KATANA_STOUT;
  ox = pyMin(ox, armInner - guardHalf - pyDiv(strokeW(sk), r));
  const oy = beltC + KATANA_HIP_Y * k;
  let t = radians(KATANA_TILT);
  // A longer sword would put its tip through the floor at the reference's tilt,
  // so it swings further out, about the guard, until the tip stands a stroke
  // above the soles (or as far as `_KATANA_MAX_TILT` allows, and then it simply
  // ends at the boots).
  const tipU = katanaStretched(length)([KATANA_TIP_U, 0.0])[0];
  const room = pyDiv(ground - 0.05 - oy, k * tipU);
  if (room < pyCos(t)) {
    t = pyMin(radians(KATANA_MAX_TILT), pyAcos(pyMax(-1.0, pyMin(1.0, room))));
  }
  const ax = pySin(t);
  const ay = pyCos(t);

  return (pt: Point): Point => {
    const u = pt[0];
    let v = pt[1];
    v *= KATANA_STOUT;
    return [ox + k * (u * ax - v * ay), oy + k * (u * ay + v * ax)];
  };
}

/**
 * A katana in its scabbard, hung from the belt at the character's left hip.
 *
 * Drawn after every garment and before the arms, so it hangs in front of the
 * tunic and the trousers and the hand at that side closes over it, as in the
 * reference. Back to front: the scabbard, its two rings and the end cap, the
 * guard, the handle and its diamonds, the collar the handle comes out of, and
 * the pommel cap.
 */
export function katana(sk: Skeleton, p: CharacterParams): string {
  const saya = p.outfit.katana_color;
  if (saya === null) return "";
  const cx = sk.head_cx;
  const cy = sk.head_cy;
  const r = sk.head_r;
  const sw = strokeW(sk);
  const place = katanaPlacement(sk, p.outfit.katana_length);
  const grow = katanaStretched(p.outfit.katana_length);

  const xf = (pt: Point): Point => place(grow(pt));

  const fittings = p.outfit.katana_fittings_color;
  const metal = truthy(fittings) ? (fittings as string) : KATANA_BRASS;
  const wrap = shade(saya, 0.86, 0.3);
  const band = shade(saya, 1.35, 1.15);

  const d = (chain: Chain): string => {
    const [start, segs] = chain;
    return curve(cx, cy, r, xf(start), segs.map(([c, e]): Segment => [xf(c), xf(e)]));
  };

  const shape = (chain: Chain, fill: string, weight: number): string =>
    `<path d="${d(chain)}" fill="${pyStr(fill)}" stroke="${OUTLINE}" ` + `stroke-width="${fmt2(outlineW(sw, weight))}" stroke-linejoin="round" />`;

  // Lighter than the figure's own line, in the proportion the reference draws it:
  // its prop is a fine object, and at the figure's full weight the guard and the
  // handle's diamonds fill in.
  const parts = [
    shape(KATANA_SAYA, saya, 0.65),
    shape(KATANA_RING_DARK, saya, 0.4),
    shape(KATANA_RING_BROWN, band, 0.4),
    shape(KATANA_KOJIRI, metal, 0.45),
    shape(KATANA_TSUBA, shade(metal, 0.72), 0.5),
    shape(KATANA_TSUKA, wrap, 0.55),
  ];
  for (const dia of KATANA_DIAMONDS) parts.push(`<path d="${d(dia)}" fill="${KATANA_DIAMOND}" />`);
  parts.push(shape(KATANA_FUCHI, shade(metal, 0.8), 0.45));
  parts.push(shape(KATANA_KASHIRA, metal, 0.45));
  return parts.join("");
}

// (end of the traced katana)

// ---------------------------------------------------------------------------------------------------------
// The bat familiar

/** A chain flipped about its own middle, which turns a frown into a smile. */
export function mirroredY(chain: Chain): Chain {
  const pts = chainPoints(chain);
  const mid = pyDiv(pySum(pts.map((q) => q[1])), pts.length);

  const flip = (q: Point): Point => [q[0], 2 * mid - q[1]];

  return [flip(chain[0]), chain[1].map(([c, e]): Segment => [flip(c), flip(e)])];
}

/**
 * Which of the traced interior lines is the mouth: the lowest of them. Found
 * rather than hardcoded, so a re-trace that reorders them cannot silently flip
 * an ear ridge instead.
 */
const KOU_MOUTH: number = argMax(KOU_LINES.map((line) => pySum(chainPoints(line).map((q) => q[1]))));

/**
 * A small bat familiar in flight, beside the figure's left shoulder.
 *
 * Drawn last of everything: he is beside her rather than worn, so nothing on
 * the figure should cross him. Placed by `_KOU_SPAN`/`_KOU_CENTRE` in head
 * radii, which is all a hovering creature needs: no contact geometry where
 * feet would meet a shoulder, and no dependence on where the hair ends.
 */
export function familiar(sk: Skeleton, p: CharacterParams): string {
  const fur = p.familiar_color;
  if (fur === null) return "";
  const cx = sk.head_cx;
  const cy = sk.head_cy;
  const r = sk.head_r;
  const sw = strokeW(sk);
  // The divisor is the constant 1.0 - 0.1, never zero.
  const t = pyMax(0.0, (sk.build - KOU_CHIBI_BUILD) / (1.0 - KOU_CHIBI_BUILD));
  const span = KOU_SPAN_CHIBI + (KOU_SPAN_REAL - KOU_SPAN_CHIBI) * t;
  const ox = KOU_CENTRE_CHIBI[0] + (KOU_CENTRE_REAL[0] - KOU_CENTRE_CHIBI[0]) * t;
  const oy = KOU_CENTRE_CHIBI[1] + (KOU_CENTRE_REAL[1] - KOU_CENTRE_CHIBI[1]) * t;

  const placed = (pt: Point): Point => [ox + pt[0] * span, oy + pt[1] * span];

  // His far wing tip reaches past where a figure ever does, and a hat's
  // headroom narrows the canvas in head radii, so slide him inward by exactly
  // what keeps him on the page and by nothing when he already fits, the same
  // clamp the staff's ornament gets.
  const xs: number[] = [];
  for (const c of [...KOU_WINGS, KOU_BODY]) {
    xs.push(placed(c[0])[0]);
    for (const seg of c[1]) for (const e of seg) xs.push(placed(e)[0]);
  }
  const reach = pyMax(xs[0] as number, ...xs.slice(1));
  const edge = pyDiv(sk.canvas_w / 2 - strokeW(sk), sk.head_r);
  const shift = pyMin(0.0, edge - reach);

  const xf = (pt: Point): Point => {
    const [x, y] = placed(pt);
    return [x + shift, y];
  };

  const d = (chain: Chain, close = true): string => {
    const [start, segs] = chain;
    return curve(cx, cy, r, xf(start), segs.map(([c, e]): Segment => [xf(c), xf(e)]), close);
  };

  // The wings and the body carry the full outline; the cells inside a wing are
  // drawn lighter, since what they are for is the thin strut lines between
  // them, not a second silhouette.
  const parts: string[] = KOU_WINGS.map(
    (shape) => `<path d="${d(shape)}" fill="${pyStr(fur)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw))}" />`,
  );
  for (const cell of KOU_WING_CELLS) {
    parts.push(
      `<path d="${d(cell)}" fill="${pyStr(fur)}" stroke="${OUTLINE}" stroke-width="${fmt2(interiorW(sw, 0.5))}" ` + 'stroke-linejoin="round" />',
    );
  }
  parts.push(`<path d="${d(KOU_BODY)}" fill="${pyStr(fur)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw))}" />`);
  // Each eye, then its pupil: the same traced shape scaled about its own
  // centre, so the pupil is the eye's form rather than a circle laid on it.
  // A coloured eye needs one; solid amber discs read as goggles at tile size.
  const eyeColor = p.familiar_eye_color;
  for (const eye of KOU_EYES) {
    parts.push(
      `<path d="${d(eye)}" fill="${truthy(eyeColor) ? pyStr(eyeColor) : OUTLINE}" stroke="${OUTLINE}" ` +
        `stroke-width="${fmt2(interiorW(sw, 0.5))}" />`,
    );
    if (eyeColor === null) continue;
    const pts = chainPoints(eye);
    const mx = pyDiv(pySum(pts.map((q) => q[0])), pts.length);
    const my = pyDiv(pySum(pts.map((q) => q[1])), pts.length);

    const shrink = (q: Point): Point => [mx + (q[0] - mx) * KOU_PUPIL, my + (q[1] - my) * KOU_PUPIL];

    const pupil = mapChain(eye, shrink);
    parts.push(`<path d="${d(pupil)}" fill="${OUTLINE}" />`);
  }
  KOU_LINES.forEach((chain, i) => {
    let line = chain;
    if (i === KOU_MOUTH && truthy(p.familiar_smile)) line = mirroredY(line);
    parts.push(
      `<path d="${d(line, false)}" fill="none" stroke="${OUTLINE}" ` +
        `stroke-width="${fmt2(interiorW(sw, 0.7))}" stroke-linecap="round" />`,
    );
  });
  return parts.join("");
}

// (end of the traced familiar)
