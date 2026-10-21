// The hair domain's parts: the hair layers (defs, mass, front, tail, knot, tie, clip), the brows drawn over the hair, the
// tip and two-tone code, and the soft finish's clump drawing. Port of character.py's `_soft_locks_on`, `_soft_lines`, the hair
// block from `_hair_tip_tone` to `_hair_underside`, `_hair_tail`, `_tail_tie`, `_hair_tie`, the clips, `_hair_knot`,
// `_brows_over_hair`, `_soft_brow_shadow`, and the clump block from `_lock_line` to `_hair_front`. The cuts, `_hair_fall`
// and `_hair_edge_x` are core-head's and are imported. Every expression keeps Python's evaluation order.

import { OUTLINE, curve, interiorW, outlineW, soft, strokeW } from "./character.ts";
import { highlightRise, hexToRgb01, litTone, rgbToHsv, shade, softShadowTone } from "./colorutil.ts";
import { type Hairstyle, type Lock, brow, eyePlacement, hairEdgeX, hairFall, hairstyleOf, headPaths } from "./core-head.ts";
import type { CharacterParams } from "./params.ts";
import { PyInt } from "./pyjson.ts";
import { PyError, deepEqual, fmt1, fmt2, pyCos, pyDiv, pyHypot, pyMax, pyMin, pyPow, pyReplace, pyRepr, pyRound, pySin, pySqrt, pySum, radians, roundTo, sorted, truthy } from "./pynum.ts";
import { PyFloat, numberOf, pyTypeName, pyValueRepr } from "./pyvalue.ts";
import type { Skeleton } from "./skeleton.ts";
import type { Chain, Point } from "./tables.ts";

// ---------------------------------------------------------------------------------------------------------
// Where the soft finish touches the hair

/**
 * `str(v)` for a value that sits in a bare f-string slot: a colour field holds a str unless a link or a request put something else
 * there, and Python then writes its `str()` (`5`, `True`, `['#fff']`) where a str would be written as it is.
 */
const pyStr = (v: unknown): string => (typeof v === "string" ? v : pyValueRepr(v));

/** `a == b` for two colour fields: by value, and `True == 1 == 1.0` as in Python, which `===` is not. */
function pyEqual(a: unknown, b: unknown): boolean {
  const [x, y] = [numberOf(a), numberOf(b)];
  if (x !== undefined && y !== undefined) return x === y;
  return deepEqual(a, b);
}

/** Lines in the hair take a dark tone of the hair itself, not the black outline. */
export const SOFT_HAIR_LINE_VALUE = 0.30;

/** Whether the soft finish draws `style`'s clumps for `p`: the finish is soft, the cut has clumps, and the strength is not zero. */
export function softLocksOn(p: CharacterParams, style: Hairstyle): boolean {
  return style.locks !== null && soft(p) && p.highlight_strength > 0;
}

/** `svg` with the black outline colour swapped for `tone` on its strokes. */
export function softLines(svg: string, tone: string): string {
  return pyReplace(svg, `stroke="${OUTLINE}"`, `stroke="${tone}"`);
}

// ---------------------------------------------------------------------------------------------------------
// The hair layers

// Hair is described in two zones. Above the cheek line it is pinned to the
// skull, so those points are literal head-radius units. Below it the shape is
// a fall whose points are given as a fraction of the way to the tips, so
// `hair_length` restyles the whole thing without touching the crown, and the
// hair keeps its relationship to the body when proportions change.
export const HAIR_TIP_CLIP_ID = "hair-tips";
export const HAIR_FRONT_CLIP_ID = "hair-front";
export const HAIR_MASS_CLIP_ID = "hair-mass";
export const HAIR_UNDERSIDE_CLIP_ID = "hair-underside";
// How far a lock's line runs on past its tip (`Hairstyle.tip_lines`), in head
// radii: the parted cut's reference carries it 0.09 to 0.16 past where its
// colour stops, on the front locks, the one place it shows against its page.
export const HAIR_TIP_LINE = 0.12;
// A cut's underside tone (`Hairstyle.underside`) against its hair colour, as
// `shade`'s value factor: the parted cut's reference measures 0.6, and 0.65 is
// the owner's value from 2026-09-29.
export const HAIR_UNDERSIDE_VALUE = 0.65;

/** The tone the hair fades into, or None when the hair is single-tone. */
export function hairTipTone(p: CharacterParams): string | null {
  if (p.hair_tip_color === null || pyEqual(p.hair_tip_color, p.hair_color)) return null;
  return p.hair_tip_color;
}

/** A hair layer, its lines in the hair's own dark tone when the finish is soft. */
export function hairLines(svg: string, p: CharacterParams): string {
  if (!soft(p)) return svg;
  return softLines(svg, shade(p.hair_color, SOFT_HAIR_LINE_VALUE));
}

export function hairDefs(sk: Skeleton, p: CharacterParams): string {
  const style = hairstyleOf(p);
  const fall = hairFall(sk, p);
  const clips: string[] = [];
  if (hairTipTone(p) !== null) {
    // Several regions clip to their union, which is what lets a cut give each
    // lock its own tone boundary instead of running one line across them all.
    const regions = style
      .tip_edge(fall)
      .map(([start, segments]) => `<path d="${curve(sk.head_cx, sk.head_cy, sk.head_r, start, segments)}" />`)
      .join("");
    clips.push(`<clipPath id="${HAIR_TIP_CLIP_ID}">${regions}</clipPath>`);
  }
  if (style.strands !== null || style.front_shade !== null || softLocksOn(p, style)) {
    // Strands are open chains, so nothing stops one running out past the
    // silhouette; clipping them to the shape they divide means a strand can be
    // drawn long enough to reach its lock's tip without having to end exactly on
    // the outline.
    const [start, line, back] = style.hairline(fall);
    const d = curve(sk.head_cx, sk.head_cy, sk.head_r, start, [...line, ...back]);
    clips.push(`<clipPath id="${HAIR_FRONT_CLIP_ID}"><path d="${d}" /></clipPath>`);
  }
  if (style.underside !== null) {
    const [region] = style.underside(fall);
    const d = curve(sk.head_cx, sk.head_cy, sk.head_r, region[0], region[1]);
    clips.push(`<clipPath id="${HAIR_UNDERSIDE_CLIP_ID}"><path d="${d}" /></clipPath>`);
  }
  if (style.mass_locks && softLocksOn(p, style)) {
    const [start, segments] = style.mass(fall);
    const d = curve(sk.head_cx, sk.head_cy, sk.head_r, start, segments);
    clips.push(`<clipPath id="${HAIR_MASS_CLIP_ID}"><path d="${d}" /></clipPath>`);
  }
  return clips.length > 0 ? `<defs>${clips.join("")}</defs>` : "";
}

/**
 * Fill a hair shape, then repaint its lower part in the tip tone. Fill
 * and outline are separate draws so the second fill can't cover the inner
 * half of the outline stroke.
 */
export function twoToneHair(d: string, p: CharacterParams): string[] {
  const parts = [`<path d="${d}" fill="${pyStr(p.hair_color)}" />`];
  const tips = hairTipTone(p);
  if (tips !== null) {
    parts.push(`<path d="${d}" fill="${pyStr(tips)}" clip-path="url(#${HAIR_TIP_CLIP_ID})" />`);
  }
  return parts;
}

export function hairMass(sk: Skeleton, p: CharacterParams): string {
  const style = hairstyleOf(p);
  const fall = hairFall(sk, p);
  const [start, segments] = style.mass(fall);
  const d = curve(sk.head_cx, sk.head_cy, sk.head_r, start, segments);
  const parts = twoToneHair(d, p);
  if (style.underside !== null) {
    parts.push(hairUnderside(sk, p, d, style.underside(fall)[1]));
  }
  if (style.mass_locks && softLocksOn(p, style)) {
    parts.push(...softLockLayers(sk, p, style, fall, d, HAIR_MASS_CLIP_ID));
  }
  parts.push(
    `<path d="${d}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)))}" ` +
      `stroke-linecap="round" stroke-linejoin="round" />`,
  );
  if (style.tip_lines !== null) {
    parts.push(hairTipLines(sk, style.tip_lines(fall)[0]));
  }
  return parts.join("");
}

/**
 * A tapered line from each apex to its end: as wide as the hair's outline at
 * the apex, so the outline's round join runs into it, and to a point at the
 * end, its sides drawn slightly in so it reads as a pen line thinning out.
 */
export function hairTipLines(sk: Skeleton, tips: readonly (readonly [Point, Point])[]): string {
  const [cx, cy, r] = [sk.head_cx, sk.head_cy, sk.head_r];
  const half = outlineW(strokeW(sk)) / 2;
  const parts: string[] = [];
  for (const [[ax, ay], [ex, ey]] of tips) {
    const a: Point = [cx + ax * r, cy + ay * r];
    const e: Point = [cx + ex * r, cy + ey * r];
    const length = pyHypot(e[0] - a[0], e[1] - a[1]);
    if (length === 0) continue;
    // `length` is not zero here (the `continue` above), so the division cannot raise.
    const [ux, uy] = [(e[0] - a[0]) / length, (e[1] - a[1]) / length];
    const [nx, ny] = [-uy, ux];
    const mid: Point = [a[0] + (e[0] - a[0]) * 0.45, a[1] + (e[1] - a[1]) * 0.45];
    const pts: Point[] = [
      [a[0] + nx * half, a[1] + ny * half],
      [mid[0] + nx * half * 0.36, mid[1] + ny * half * 0.36],
      e,
      [mid[0] - nx * half * 0.36, mid[1] - ny * half * 0.36],
      [a[0] - nx * half, a[1] - ny * half],
    ];
    const [p0, c1, p1, c2, p2] = pts as [Point, Point, Point, Point, Point];
    const xy = (q: Point): string => `${fmt1(q[0])} ${fmt1(q[1])}`;
    parts.push(`<path d="M ${xy(p0)} Q ${xy(c1)} ${xy(p1)} Q ${xy(c2)} ${xy(p2)} Z" fill="${OUTLINE}" />`);
  }
  return parts.join("");
}

/**
 * The mass `d` again in the underside tone, inside the cut's underside
 * region (`_hair_defs`), and the lines bounding that region where it shows.
 * A two-tone head of hair takes the underside of its tip tone at the tips.
 */
export function hairUnderside(sk: Skeleton, p: CharacterParams, d: string, lines: readonly Chain[]): string {
  const parts = [`<g clip-path="url(#${HAIR_UNDERSIDE_CLIP_ID})">`];
  parts.push(`<path d="${d}" fill="${shade(p.hair_color, HAIR_UNDERSIDE_VALUE)}" />`);
  const tips = hairTipTone(p);
  if (tips !== null) {
    const tone = shade(tips, HAIR_UNDERSIDE_VALUE);
    parts.push(`<path d="${d}" fill="${tone}" clip-path="url(#${HAIR_TIP_CLIP_ID})" />`);
  }
  parts.push("</g>");
  const w = outlineW(strokeW(sk));
  for (const chain of lines) {
    const lineD = curve(sk.head_cx, sk.head_cy, sk.head_r, chain[0], chain[1], false);
    parts.push(
      `<path d="${lineD}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(w)}" ` +
        `stroke-linecap="round" stroke-linejoin="round" />`,
    );
  }
  return parts.join("");
}

// ---------------------------------------------------------------------------------------------------------
// The tail, its band, the clip and the knot

/**
 * A gathered tail hanging behind the head.
 *
 * Drawn *behind* the hair mass and the head, so it emerges from the silhouette
 * rather than sitting on the face. That is the whole reason this is a part and
 * not a `Hairstyle`: a cut owns the outline around the skull, and a tail is by
 * definition outside it.
 *
 * Narrow where it is bound and swelling below, because a bundle of hair does
 * that, and because a constant-width strip reads as a ribbon.
 */
export function hairTail(sk: Skeleton, p: CharacterParams): string {
  if (p.hair_tail <= 0.0) return "";
  const [cx, r] = [sk.head_cx, sk.head_r];
  const color = p.hair_color;
  const sw = strokeW(sk);
  const [tieX, tieY] = tailTie(sk);
  const length = (sk.hip_y - sk.shoulder_y) * pyMax(0.0, pyMin(1.0, p.hair_tail));
  const tipY = tieY + r * 0.45 + length;
  // Off to one side, and **outside the cut**. Measured on the shipped
  // hairstyles, the mass spans about 1.34 to 1.39 head radii either way, so a
  // tail drawn anywhere inside that is behind a filled shape wider than it is
  // and simply does not exist. The first attempt put the belly at 0.42 and drew
  // nothing at all. It has to swing clear of the hair before it falls.
  // Both edges sit **outside the hair**, not just the outer one. The cut spans
  // about 1.39 head radii and the torso is drawn over this as well, so a tail
  // whose inner edge is at 1.02 has its whole body hidden behind one or the
  // other and shows as a sliver. Starting the near edge past the cut is what
  // makes it a bundle beside the head rather than a rim behind it.
  const belly = r * 1.88;
  const near = r * 1.42;
  // Pinched at the tie and swelling below it, which is what a bundle of hair
  // gathered in a band does, and what a strip of constant width does not: the
  // first version ran the same width the whole way and read as one side of the
  // haircut being longer than the other.
  const d =
    `M ${fmt1(tieX)} ${fmt1(tieY)} ` +
    `Q ${fmt1(cx + belly)} ${fmt1(tieY + (tipY - tieY) * 0.3)} ` +
    `${fmt1(cx + belly * 0.84)} ${fmt1(tipY)} ` +
    `Q ${fmt1(cx + near * 0.86)} ${fmt1(tipY - (tipY - tieY) * 0.18)} ` +
    `${fmt1(cx + near * 0.52)} ${fmt1(tieY + (tipY - tieY) * 0.3)} ` +
    `Z`;
  return `<path d="${d}" fill="${pyStr(color)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw))}" />`;
}

/**
 * Where a ponytail is bound, in canvas coordinates.
 *
 * Shared between the tail and the band that binds it, because the two only
 * read as one object while they agree, and they are drawn in different layers:
 * the tail goes behind the hair and the band in front of it.
 *
 * High and back, level with the top of the ear rather than at the nape. That
 * height is most of what tells a ponytail from hair simply hanging down, and
 * the first version tied it at 0.30 head radii below centre, which is low
 * enough that the tail left the head beside the ear and read as a long side
 * lock.
 *
 * Pulled out from 0.62 head radii above centre to 0.46, and right from 0.62
 * to 0.78, once Krista also carried goggles: the two were tuned without
 * knowledge of each other and the tie used to land inside the goggle strap's
 * own footprint, close enough that the strap only painted over its centre
 * and left the tie's own outline poking out past the right lens. Moved along
 * the same high-and-back direction rather than picked to dodge the strap, so
 * a character with the tail and no goggles is unaffected in anything that
 * would show at this size.
 */
export function tailTie(sk: Skeleton): [number, number] {
  return [sk.head_cx + sk.head_r * 0.78, sk.head_cy - sk.head_r * 0.46];
}

/**
 * The band a ponytail is gathered in, drawn over the hair.
 *
 * Over, like the knot and unlike the tail, and for the same reason: the cut is
 * a filled shape wider than the skull, so anything behind it is gone. Without
 * this the tail emerges from the silhouette with nothing to say it was bound,
 * and a bundle of hair that is not visibly tied is just more hair.
 */
export function hairTie(sk: Skeleton, p: CharacterParams): string {
  if (p.hair_tail <= 0.0) return "";
  const [x, y] = tailTie(sk);
  const r = sk.head_r;
  const sw = strokeW(sk);
  const [w, h] = [r * 0.2, r * 0.13];
  return (
    `<ellipse cx="${fmt1(x)}" cy="${fmt1(y)}" rx="${fmt1(w)}" ry="${fmt1(h)}" ` +
    `fill="${pyStr(p.hair_color)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw))}" />` +
    `<path d="M ${fmt1(x - w * 0.72)} ${fmt1(y - h * 0.3)} ` +
    `L ${fmt1(x + w * 0.72)} ${fmt1(y - h * 0.3)}" fill="none" stroke="${OUTLINE}" ` +
    `stroke-width="${fmt2(interiorW(sw, 0.7))}" stroke-linecap="round" />`
  );
}

// Where a hair clip sits, in head radii from the head's centre: about where the
// side tail's band was (`_tail_tie`), just under a hat's brim, so it shows with
// the hat on.
export const HAIR_CLIP_AT: readonly [number, number] = [0.78, -0.4];
// How far inside the silhouette the clip's centre stays: half the widest clip
// and a little hair beyond it. The long blunt cuts are only 1.0 head radii wide
// at that height, against 1.2 to 1.3 for the rest, and at 0.78 a crescent stuck
// out past their outline.
export const HAIR_CLIP_INSET = 0.27;
// The tilt of a long clip, degrees clockwise from level: along the lock it is
// pinned to, which falls steeply from the parting toward the temple.
export const HAIR_CLIP_TILT = 62.0;

/** A plain bar clip: a rounded bar, with a line along it for the fold. */
export function clipBar(r: number, line: number, fold: number, color: string): string {
  const [length, w] = [r * 0.45, r * 0.11];
  return (
    `<rect x="${fmt2(-length / 2)}" y="${fmt2(-w / 2)}" width="${fmt2(length)}" height="${fmt2(w)}" ` +
    `rx="${fmt2(w / 2)}" fill="${pyStr(color)}" stroke="${OUTLINE}" stroke-width="${fmt2(line)}" />` +
    `<path d="M ${fmt2(-length * 0.36)} 0 L ${fmt2(length * 0.36)} 0" stroke="${OUTLINE}" ` +
    `stroke-width="${fmt2(fold)}" stroke-linecap="round" />`
  );
}

/**
 * A bracket clip: a gold frame open on one side, two parallel bars joined by a short one, the way a flat barrette lies on the temple. The bars run along the clip's own x axis
 * (it is drawn outline first, a wider dark stroke under the gold one, so the frame is outlined whole without a fill).
 */
export function clipBracket(r: number, line: number, _fold: number, color: string): string {
  const [w, h, t] = [r * 0.16, r * 0.12, r * 0.04];
  const d = `M ${fmt2(w / 2)} ${fmt2(-h / 2)} L ${fmt2(-w / 2)} ${fmt2(-h / 2)} L ${fmt2(-w / 2)} ${fmt2(h / 2)} L ${fmt2(w / 2)} ${fmt2(h / 2)}`;
  return (
    `<path d="${d}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(t + line)}" stroke-linejoin="round" stroke-linecap="round" />` +
    `<path d="${d}" fill="none" stroke="${pyStr(color)}" stroke-width="${fmt2(t)}" stroke-linejoin="round" stroke-linecap="round" />`
  );
}

/** Two thin pins crossed in an X. */
export function clipCrossed(r: number, line: number, _fold: number, color: string): string {
  const [length, w] = [r * 0.45, r * 0.075];
  // `rotate({a})` prints an int: -24 and 24.
  return [-24, 24]
    .map(
      (a) =>
        `<rect x="${fmt2(-length / 2)}" y="${fmt2(-w / 2)}" width="${fmt2(length)}" height="${fmt2(w)}" ` +
        `rx="${fmt2(w / 2)}" fill="${pyStr(color)}" stroke="${OUTLINE}" stroke-width="${fmt2(line)}" ` +
        `transform="rotate(${String(a)})" />`,
    )
    .join("");
}

/** A snap clip: a long narrow triangle with a slot along it. */
export function clipSnap(r: number, line: number, fold: number, color: string): string {
  const [length, w] = [r * 0.48, r * 0.15];
  return (
    `<path d="M ${fmt2(-length / 2)} ${fmt2(-w / 2)} L ${fmt2(length / 2)} 0 L ${fmt2(-length / 2)} ${fmt2(w / 2)} Z" ` +
    `fill="${pyStr(color)}" stroke="${OUTLINE}" stroke-width="${fmt2(line)}" stroke-linejoin="round" />` +
    `<path d="M ${fmt2(-length * 0.36)} 0 L ${fmt2(length * 0.12)} 0" stroke="${OUTLINE}" ` +
    `stroke-width="${fmt2(fold)}" stroke-linecap="round" />`
  );
}

/**
 * A crescent moon: the outer disc less a smaller one shifted toward its
 * opening, as one path between the two circles' crossings.
 */
export function clipCrescent(r: number, line: number, _fold: number, color: string): string {
  const [big, small, off] = [r * 0.195, r * 0.158, r * 0.098];
  // `off` is zero only for a zero head radius, which Python reports as `ZeroDivisionError`.
  const x = pyDiv(big * big - small * small + off * off, 2 * off);
  const y = pySqrt(big * big - x * x);
  const d =
    `M ${fmt2(x)} ${fmt2(-y)} A ${fmt2(big)} ${fmt2(big)} 0 1 0 ${fmt2(x)} ${fmt2(y)} ` +
    `A ${fmt2(small)} ${fmt2(small)} 0 0 1 ${fmt2(x)} ${fmt2(-y)} Z`;
  return `<path d="${d}" fill="${pyStr(color)}" stroke="${OUTLINE}" stroke-width="${fmt2(line)}" stroke-linejoin="round" />`;
}

/** A five-pointed star. */
export function clipStar(r: number, line: number, _fold: number, color: string): string {
  const pts: string[] = [];
  for (let i = 0; i < 10; i++) {
    // `i % 2` of a non-negative int; `-90 + i * 36` is an int.
    const k = i % 2 === 0 ? 0.195 : 0.083;
    pts.push(`${fmt2(k * r * pyCos(radians(-90 + i * 36)))},${fmt2(k * r * pySin(radians(-90 + i * 36)))}`);
  }
  return (
    `<polygon points="${pts.join(" ")}" fill="${pyStr(color)}" stroke="${OUTLINE}" stroke-width="${fmt2(line)}" ` +
    `stroke-linejoin="round" />`
  );
}

export type ClipShape = (r: number, line: number, fold: number, color: string) => string;

// The shapes a hair clip comes in (`harness/hair_clip/sheet.py` has them side by
// side), each drawn about its own centre, and the tilt it takes: a long clip
// lies along the lock (`None`), while a moon or a star reads the right way up
// and only leans a little. At the insert size (head radius 21 px) the crescent
// and the bar read best, the star as a dot and the crossed pins hardly at all.
/** A null-prototype object, so that a name like `constructor` is a missing clip, not an inherited one. */
export const HAIR_CLIPS: Readonly<Record<string, readonly [ClipShape, number | null]>> = Object.assign(
  Object.create(null) as Record<string, readonly [ClipShape, number | null]>,
  {
    bar: [clipBar, null],
    bracket: [clipBracket, -21.5],
    crescent: [clipCrescent, -15.0],
    crossed: [clipCrossed, null],
    snap: [clipSnap, null],
    star: [clipStar, -10.0],
  },
);

/** `HAIR_CLIPS[name]`: a name that is not a clip raises `KeyError`, an unhashable one `TypeError`, as the dictionary does. */
function hairClipFor(name: unknown): readonly [ClipShape, number | null] {
  if (typeof name === "string") {
    const entry = HAIR_CLIPS[name];
    if (entry !== undefined) return entry;
  } else if (Array.isArray(name) || name instanceof Map || (typeof name === "object" && name !== null && !(name instanceof PyInt) && !(name instanceof PyFloat))) {
    throw new PyError("TypeError", `unhashable type: '${pyTypeName(name)}'`);
  }
  throw new PyError("KeyError", pyValueRepr(name));
}

/**
 * A clip worn in the hair, over the hair and the fringe, under anything
 * worn on the head: goggles' strap, a scarf or a hat's brim covers it.
 */
export function hairClip(sk: Skeleton, p: CharacterParams, at: readonly [number, number] | null = null): string {
  const color = p.outfit.hair_clip_color;
  if (color === null) return "";
  const [shape, tilt] = hairClipFor(p.outfit.hair_clip);
  const r = sk.head_r;
  const sw = strokeW(sk);
  // `at`: where a cut that knows its own hair (the adult woman's, body-adult-cuts.ts) puts the clip, in head radii about the head's centre, instead of beside the hair's edge.
  const atY = at === null ? HAIR_CLIP_AT[1] : at[1];
  const atX = at === null ? pyMin(HAIR_CLIP_AT[0], hairEdgeX(atY, sk, p) - HAIR_CLIP_INSET) : at[0];
  const [x, y] = [sk.head_cx + atX * r, sk.head_cy + atY * r];
  const angle = tilt === null ? HAIR_CLIP_TILT : tilt;
  const body = shape(r, outlineW(sw), interiorW(sw, 0.7), color);
  return `<g transform="translate(${fmt1(x)} ${fmt1(y)}) rotate(${fmt1(angle)})">${body}</g>`;
}

/**
 * A knot gathered on the crown.
 *
 * **Over** the hair mass, not behind it, which is the opposite of the tail and
 * the only thing that works. A cut carries its own volume: the shipped ones top
 * out around -1.25 to -1.28 head radii while `build_skeleton`'s hair margin
 * puts the ceiling at -1.36, so there is under a tenth of a radius of daylight
 * above a cut for a knot to poke through. Drawn behind, it is invisible; drawn
 * over, it reads as what it is, hair gathered on top of hair, and it cannot
 * clip the canvas because it never has to reach above the cut to be seen.
 */
export function hairKnot(sk: Skeleton, p: CharacterParams): string {
  if (!truthy(p.hair_knot)) return "";
  const [cx, cy, r] = [sk.head_cx, sk.head_cy, sk.head_r];
  const sw = strokeW(sk);
  const [rx, ry] = [r * 0.24, r * 0.19];
  // Poking above the cut rather than sitting inside it. The shipped cuts top
  // out around -1.25 to -1.28 head radii and the canvas ceiling is -1.36, so
  // this rides at -1.13 and paints to about -1.34 once the stroke's outer half
  // is counted, which is what the ceiling counts. Buried at -1.02 it was a
  // same-coloured ellipse on same-coloured hair, which is nothing at all; at
  // -1.15 it cleared the hair and went 0.001 past the margin, which the test
  // caught and the eye did not.
  const cyk = cy - r * 1.13;
  // A band under it. One line, and it is the difference between a knot and a
  // lump: hair gathered has to look tied.
  const bandW = rx * 0.85;
  return (
    `<ellipse cx="${fmt1(cx)}" cy="${fmt1(cyk)}" rx="${fmt1(rx)}" ry="${fmt1(ry)}" ` +
    `fill="${pyStr(p.hair_color)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw))}" />` +
    `<path d="M ${fmt1(cx - bandW)} ${fmt1(cyk + ry * 0.86)} ` +
    `L ${fmt1(cx + bandW)} ${fmt1(cyk + ry * 0.86)}" fill="none" stroke="${OUTLINE}" ` +
    `stroke-width="${fmt2(interiorW(sw, 0.7))}" stroke-linecap="round" />`
  );
}

/** The brows, drawn after the front hair, for a face that asks for it. */
export function browsOverHair(sk: Skeleton, p: CharacterParams): string {
  if (!truthy(eyePlacement(sk, p)[3].brows_over_hair)) return "";
  return [-1, 1].map((side) => brow(sk, p, side)).join("");
}

// ---------------------------------------------------------------------------------------------------------
// The soft finish: the fringe's shadow and the clumps

// How far the fringe's shadow falls on the forehead, in head radii, and how dark.
export const SOFT_BROW_SHADOW_DROP = 0.09;
export const SOFT_BROW_SHADOW_VALUE = 0.8;
export const SOFT_BROW_SHADOW_OPACITY = 0.55;

/** The fringe's shadow on the face, drawn under the hair. */
export function softBrowShadow(sk: Skeleton, p: CharacterParams, fillD: string): string {
  const faceFill = headPaths(sk)[0];
  return (
    `<defs><clipPath id="soft-face-clip"><path d="${faceFill}" /></clipPath></defs>` +
    `<g clip-path="url(#soft-face-clip)"><path d="${fillD}" ` +
    // A bare `{_SOFT_BROW_SHADOW_OPACITY}` of a float is its repr.
    `fill="${shade(p.skin_tone, SOFT_BROW_SHADOW_VALUE)}" opacity="${pyRepr(SOFT_BROW_SHADOW_OPACITY)}" ` +
    `transform="translate(0 ${fmt2(SOFT_BROW_SHADOW_DROP * sk.head_r)})" /></g>`
  );
}

// The soft finish's clumps (`Hairstyle.locks`): shadow clumps and lit clumps in solid tone steps of
// the hair colour, a soft separation along each shadow clump's dark edge and one faint highlight
// in each lit clump, all inside the hair's own silhouette so no contour moves. Tuned by eye over
// three rounds of the owner's blind pairs (2026-10-16, `docs/soft-hair-status.md`): the tones keep
// the hair's saturation (a tint toward white read as frosting on dark red), the highlights stay
// faint, and the clumps sit on the cut's own strand dashes, which are drawn over them.
export const SOFT_LOCK_LIGHT: readonly [number, number] = [-0.55, -0.83]; // toward the light: up and to the left
// `highlight_strength` 1 is this share of the strength the clumps were first drawn and judged at.
export const SOFT_LOCK_STRENGTH_SCALE = 0.5;
// A tip colour at least this pale and this grey stays clean: no clumps in it. A shadow clump that
// crosses from the hair's own colour into a white tip came out as a grey oval that read as a stain
// (Satoshi, found by the break-it review of the cuts added after Gate 1), and a lit step cannot
// rise on white anyway. The tip repaint still covers the hair-colour clumps under it.
export const SOFT_LOCK_PALE_TIP_SATURATION = 0.15;
export const SOFT_LOCK_PALE_TIP_VALUE = 0.85;
export const SOFT_LOCK_MID_RISE = 0.12; // a lit clump's body, as a share of `highlight_rise`
export const SOFT_LOCK_HIGH_RISE = 0.38; // its highlight
export const SOFT_LOCK_SEP_VALUE = 0.74;
export const SOFT_LOCK_SEP_OPACITY = 0.6;
export const SOFT_LOCK_POINTS = 9; // points kept per side of a clump's outline before it is drawn as curves

/** A smooth curve through `points`, sampled. */
export function lockLine(points: readonly Point[], per = 14): Point[] {
  if (points.length === 0) throw new PyError("IndexError", "tuple index out of range");
  const p: Point[] = [points[0] as Point, ...points, points[points.length - 1] as Point];
  const out: Point[] = [];
  for (let i = 1; i < p.length - 2; i++) {
    const [p0, p1, p2, p3] = [p[i - 1] as Point, p[i] as Point, p[i + 1] as Point, p[i + 2] as Point];
    for (let k = 0; k < per; k++) {
      // `per` is positive here (the loop body runs only then).
      const t = k / per;
      const [t2, t3] = [t * t, t * t * t];
      out.push([
        0.5 *
          (2 * p1[0] +
            (-p0[0] + p2[0]) * t +
            (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
            (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
        0.5 *
          (2 * p1[1] +
            (-p0[1] + p2[1]) * t +
            (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
            (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3),
      ]);
    }
  }
  out.push(points[points.length - 1] as Point);
  return out;
}

export function lockNormals(line: readonly Point[]): Point[] {
  const out: Point[] = [];
  for (let i = 0; i < line.length; i++) {
    const a = line[pyMax(0, i - 1)] as Point;
    const b = line[pyMin(line.length - 1, i + 1)] as Point;
    const [dx, dy] = [b[0] - a[0], b[1] - a[1]];
    const h = pyHypot(dx, dy);
    // `math.hypot(dx, dy) or 1.0`
    const n = truthy(h) ? h : 1.0;
    // `n` is never zero here (the `or` above).
    out.push([-dy / n, dx / n]);
  }
  return out;
}

/**
 * +1 where a clump's normal faces the light on the whole, else -1. Chosen once for the whole
 * clump: chosen point by point it flips mid-clump where the line bends past the light.
 */
export function lockSide(_line: readonly Point[], normals: readonly Point[]): number {
  // `sum` starts from the int 0 and every term is a float.
  const total = pySum(normals.map(([nx, ny]) => nx * SOFT_LOCK_LIGHT[0] + ny * SOFT_LOCK_LIGHT[1]), 0);
  return total >= 0 ? 1.0 : -1.0;
}

/** Cubic curves through `points` (Catmull-Rom), as the tail of a path already at the first. */
export function smoothPath(points: readonly (readonly [number, number])[]): string {
  const out: string[] = [];
  const n = points.length;
  for (let i = 0; i < n - 1; i++) {
    const [p0, p1, p2, p3] = [
      points[pyMax(i - 1, 0)] as Point,
      points[i] as Point,
      points[i + 1] as Point,
      points[pyMin(i + 2, n - 1)] as Point,
    ];
    const c1: Point = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
    const c2: Point = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
    out.push(`C ${fmt1(c1[0])} ${fmt1(c1[1])} ${fmt1(c2[0])} ${fmt1(c2[1])} ${fmt1(p2[0])} ${fmt1(p2[1])}`);
  }
  return out.join(" ");
}

/**
 * A tapered shape along a clump's line, nothing at either end and `width` (head radii) at the
 * widest. `offset` shifts it across the line by that share of its local width, positive toward
 * the light.
 */
export function lockShape(
  cx: number,
  cy: number,
  r: number,
  points: readonly Point[],
  width: number,
  t0 = 0.0,
  t1 = 1.0,
  power = 0.75,
  offset = 0.0,
): string {
  if (t1 - t0 < 0.05) return ""; // too short to draw: nothing but its two tapered ends
  const line = lockLine(points);
  const nrm = lockNormals(line);
  const side = lockSide(line, nrm);
  const n = line.length;
  let left: Point[] = [];
  let right: Point[] = [];
  // `zip(line, nrm, strict=True)`: the two lists are the same length by construction.
  for (let i = 0; i < line.length; i++) {
    const [x, y] = line[i] as Point;
    const [nx, ny] = nrm[i] as Point;
    // A single-point line is `n - 1 == 0`: ZeroDivisionError, as in Python.
    const t = pyDiv(i, n - 1);
    if (t < t0 || t > t1) continue;
    const u = pyDiv(t - t0, t1 - t0);
    const w = width * pyPow(pySin(Math.PI * u), power);
    const [mx, my] = [x + nx * side * offset * w, y + ny * side * offset * w];
    left.push([cx + (mx + (nx * w) / 2) * r, cy + (my + (ny * w) / 2) * r]);
    right.push([cx + (mx - (nx * w) / 2) * r, cy + (my - (ny * w) / 2) * r]);
  }
  if (left.length < 3) return "";
  const keepSet = new Set<number>();
  for (let k = 0; k < SOFT_LOCK_POINTS; k++) keepSet.add(pyRound(pyDiv(k * (left.length - 1), SOFT_LOCK_POINTS - 1)));
  const keep = sorted(keepSet);
  left = keep.map((k) => left[k] as Point);
  right = keep.map((k) => right[k] as Point).reverse();
  return `M ${fmt1((left[0] as Point)[0])} ${fmt1((left[0] as Point)[1])} ${smoothPath(left)} ${smoothPath([left[left.length - 1] as Point, ...right])} Z`;
}

/**
 * The soft finish's clumps in the tones of `hair`, as one group clipped to a hair layer
 * (`clip_id`, the front piece by default) and with `tip_clip` to the tip-toned region too.
 * `gain` is the internal strength, 1 the strength the clumps were first drawn and judged at.
 */
export function softLocks(
  sk: Skeleton,
  hair: string,
  locks: readonly Lock[],
  gain: number,
  clipId: string = HAIR_FRONT_CLIP_ID,
  tipClip = false,
): string {
  const [cx, cy, r] = [sk.head_cx, sk.head_cy, sk.head_r];
  const rise = highlightRise(hair) * gain;
  const shadow = softShadowTone(hair, gain);
  const [mid, high] = [litTone(hair, rise * SOFT_LOCK_MID_RISE), litTone(hair, rise * SOFT_LOCK_HIGH_RISE)];
  const sep = shade(hair, SOFT_LOCK_SEP_VALUE);
  const parts: string[] = [];

  const add = (d: string, fill: string, opacity: number | null = null): void => {
    if (truthy(d)) {
      // A bare `{opacity}` of a float is its repr.
      const extra = opacity === null ? "" : ` opacity="${pyRepr(opacity)}"`;
      parts.push(`<path d="${d}" fill="${fill}"${extra} />`);
    }
  };

  for (const [role, points, width, length] of locks) {
    if (role === "shadow") {
      add(lockShape(cx, cy, r, points, width, 0.0, length, 0.55), shadow);
      const sepD = lockShape(cx, cy, r, points, 0.035, 0.1, pyMin(length, 0.9), 0.5, -1.7);
      add(sepD, sep, roundTo(SOFT_LOCK_SEP_OPACITY * gain, 3));
    } else if (role === "lit") {
      add(lockShape(cx, cy, r, points, width, 0.0, length, 0.55), mid);
      const highD = lockShape(cx, cy, r, points, width * 0.3, 0.1, 0.62, 0.8, 0.45);
      add(highD, high);
    } else {
      throw new PyError("ValueError", `a lock's role is shadow or lit, not ${pyValueRepr(role)}`);
    }
  }
  let body = parts.join("");
  if (tipClip) {
    body = `<g clip-path="url(#${HAIR_TIP_CLIP_ID})">${body}</g>`;
  }
  return `<g clip-path="url(#${clipId})">${body}</g>`;
}

/**
 * The soft finish's clumps on one hair layer (`fill_d` its shape, `clip_id` its clip). A
 * two-tone cut gets them twice: in the hair's tones, then, over a repaint of the tip region, in
 * the tip colour's. A cut whose tip region is the whole mass skips the first pass, which the
 * repaint would hide entirely. `after_repaint` is drawn between the repaint and the tip-colour
 * pass, for what the repaint would otherwise cover (the front piece's `front_shade` strips).
 */
export function softLockLayers(
  sk: Skeleton,
  p: CharacterParams,
  style: Hairstyle,
  fall: number,
  fillD: string,
  clipId: string,
  afterRepaintArg: readonly string[] | null = null,
): string[] {
  if (style.locks === null) throw new PyError("AssertionError", "");
  const afterRepaint = truthy(afterRepaintArg) ? (afterRepaintArg as readonly string[]) : [];
  const locks = style.locks(fall);
  const gain = p.highlight_strength * SOFT_LOCK_STRENGTH_SCALE;
  const tips = hairTipTone(p);
  const parts: string[] = [];
  // `!=` on a list of chains against a one-element list: by value, in Python and here.
  if (tips === null || !deepEqual(style.tip_edge(fall), [style.mass(fall)])) {
    parts.push(softLocks(sk, p.hair_color, locks, gain, clipId));
  }
  if (tips !== null) {
    parts.push(`<path d="${fillD}" fill="${pyStr(tips)}" clip-path="url(#${HAIR_TIP_CLIP_ID})" />`);
    parts.push(...afterRepaint);
    const [, tipS, tipV] = rgbToHsv(...hexToRgb01(tips));
    const pale = tipS < SOFT_LOCK_PALE_TIP_SATURATION && tipV > SOFT_LOCK_PALE_TIP_VALUE;
    if (!pale) {
      parts.push(softLocks(sk, tips, locks, gain, clipId, true));
    }
  }
  return parts;
}

export function hairFront(sk: Skeleton, p: CharacterParams): string {
  const [cx, cy, r] = [sk.head_cx, sk.head_cy, sk.head_r];
  const sw = strokeW(sk);

  // Fringe and side locks are one shape in the same flat tone as the mass,
  // drawn without a stroke of its own. The only line added is the hairline,
  // so nothing divides the hair into separate pieces.
  const style = hairstyleOf(p);
  const fall = hairFall(sk, p);
  const [start, line, back] = style.hairline(fall);
  const fillD = curve(cx, cy, r, start, [...line, ...back]);
  const lineD = curve(cx, cy, r, start, line, false);
  let parts = twoToneHair(fillD, p);
  if (soft(p)) {
    parts = [softBrowShadow(sk, p, fillD), ...parts];
  }
  const strips: string[] = [];
  if (style.front_shade !== null) {
    const tone = shade(p.hair_color, HAIR_UNDERSIDE_VALUE);
    for (const region of style.front_shade(fall)) {
      strips.push(`<path d="${curve(cx, cy, r, region[0], region[1])}" fill="${tone}" clip-path="url(#${HAIR_FRONT_CLIP_ID})" />`);
    }
  }
  parts.push(...strips);
  if (softLocksOn(p, style)) {
    // The strips sit under the clumps, with or without a tip colour: a tip repaint would cover
    // them, so they are drawn again between it and the tip-colour clumps.
    parts.push(...softLockLayers(sk, p, style, fall, fillD, HAIR_FRONT_CLIP_ID, strips));
  }
  parts.push(
    `<path d="${lineD}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw))}" ` +
      `stroke-linecap="round" stroke-linejoin="round" />`,
  );
  if (style.openings !== null) {
    for (const chain of style.openings(fall)) {
      parts.push(
        `<path d="${curve(cx, cy, r, chain[0], chain[1])}" fill="${pyStr(p.skin_tone)}" stroke="${OUTLINE}" ` +
          `stroke-width="${fmt2(interiorW(sw))}" stroke-linejoin="round" />`,
      );
    }
  }
  // Outer edge of each lock. Redundant where the mass shows behind the body,
  // since it lands on the mass's own stroke, and the silhouette where it
  // doesn't.
  // A list, one entry per side, rather than one chain mirrored here. Mirroring
  // was a hidden assumption that every cut is symmetric, and it was silent until
  // one was not: the traced crop's right-hand edge got stamped onto its left,
  // where the mass is a different shape, and drew a row of black barbs standing
  // off the silhouette with white between them and the hair. A cut that is
  // symmetric says so by handing back both sides.
  for (const [edgeStart, edgeSegments] of style.fall_edge(fall)) {
    const edgeD = curve(cx, cy, r, edgeStart, edgeSegments, false);
    parts.push(
      `<path d="${edgeD}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw))}" ` +
        `stroke-linecap="round" />`,
    );
  }
  if (style.tip_lines !== null) {
    parts.push(hairTipLines(sk, style.tip_lines(fall)[1]));
  }
  // Interior strands last, so they sit over the fill and the hairline both.
  // Lighter than the silhouette, the same relation the jaw line has to the head
  // outline: these divide one surface, they do not bound it.
  if (style.strands !== null) {
    for (const [sStart, sSegments] of style.strands(fall)) {
      const sD = curve(cx, cy, r, sStart, sSegments, false);
      parts.push(
        `<path d="${sD}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(interiorW(sw, style.strand_weight))}" ` +
          `stroke-linecap="round" clip-path="url(#${HAIR_FRONT_CLIP_ID})" />`,
      );
    }
  }
  return parts.join("");
}
