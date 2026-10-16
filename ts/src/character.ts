// The drawing. Port of character.py, in progress: this is the spike's slice (three layers, the post-steps and the
// document wrapper). Function names are the Python ones in camelCase, and every expression keeps Python's
// evaluation order, since a different order rounds differently. Numbers reach the text only through the
// `fmt*` kernel functions.

import { shade } from "./colorutil.ts";
import type { CharacterParams } from "./params.ts";
import { fmt0, fmt1, fmt2, pyCos, pyFloat, pyMin, pyPow, pySin, radians, truthy } from "./pynum.ts";
import { pySub } from "./pyre.ts";
import { replace, type Skeleton } from "./skeleton.ts";
import type { Chain, Point, Segment } from "./tables.ts";
import { HAT_UNDERSIDE } from "./tables.ts";

export const OUTLINE = "#0d0d0d";
const OUTLINE_SCALE = 0.75;
const INTERIOR_SCALE = 0.55;
const SOFT_LINE_SCALE = 0.66;

export const FINISHES = ["flat", "soft"] as const;

/** Whether `p` asks for the soft finish. `renderCharacter` has already validated it. */
export const soft = (p: CharacterParams): boolean => p.finish === "soft";

/** Silhouette stroke weight for this figure: a fraction of the figure, not of the canvas. */
export function strokeW(sk: Skeleton): number {
  return sk.head_r * (0.041 + 0.017 * sk.build);
}

/** The drawn weight of an outline at `k` of the weight `sw`. */
export const outlineW = (sw: number, k = 1.0): number => sw * k * OUTLINE_SCALE;

/** The drawn weight of an interior line at `k` of the weight `sw`. */
export const interiorW = (sw: number, k = 1.0): number => sw * k * INTERIOR_SCALE;

/** Every line's `stroke-width` in `svg` scaled by `SOFT_LINE_SCALE`. */
export function softStrokeWidths(svg: string): string {
  return svg.replace(/<[a-zA-Z][^>]*>/g, (tag) =>
    tag.replace(/stroke-width="([0-9.]+)"/g, (_m, w: string) => `stroke-width="${fmt2(pyFloat(w) * SOFT_LINE_SCALE)}"`),
  );
}

/** Every id defined in `body`, and every reference to one, under `prefix`. */
export function namespaceIds(body: string, prefix: string): string {
  // Python's \b is Unicode-aware; this is its start-of-word test for the `i` of `id=`.
  body = pySub(/(?<![\p{L}\p{N}_])id="([^"]+)"/gu, `id="${prefix}-\\1"`, body);
  body = pySub(/url\(#([^)]+)\)/g, `url(#${prefix}-\\1)`, body);
  return pySub(/href="#([^"]+)"/g, `href="#${prefix}-\\1"`, body);
}

// ---------------------------------------------------------------------------------------------------------
// Curves in head-radius units

/** Map a point given in head-radius units (origin = head center) to absolute canvas coordinates. */
export function headUnits(cx: number, cy: number, r: number, pt: Point): string {
  return `${fmt1(cx + pt[0] * r)} ${fmt1(cy + pt[1] * r)}`;
}

/** Build a path 'd' from a start point plus quadratic segments, all in head-radius units. */
export function curve(cx: number, cy: number, r: number, start: Point, segments: readonly Segment[], close = true): string {
  const d = [`M ${headUnits(cx, cy, r, start)}`];
  for (const [ctrl, end] of segments) {
    d.push(`Q ${headUnits(cx, cy, r, ctrl)} ${headUnits(cx, cy, r, end)}`);
  }
  if (close) d.push("Z");
  return d.join(" ");
}

/** The point at parameter `u` on the quadratic `p0`, `p1`, `p2`. (`(1 - u) ** 2` is written as a product: exact, as C's `pow(x, 2.0)` is.) */
export function quadPoint(p0: Point, p1: Point, p2: Point, u: number): Point {
  const a = (1 - u) * (1 - u);
  const b = 2 * (1 - u) * u;
  const c = u * u;
  return [a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1]];
}

// ---------------------------------------------------------------------------------------------------------
// The head's outline

const HEAD_SEGMENTS = 8;
/** How much width the whole skull loses by the adult end, as a fraction. */
const SKULL_NARROW = 0.1;
/** Where the jaw taper begins, in head radii, negative being above the head centre. */
const JAW_START_Y = -0.25;
/** How the taper eases from there to the chin. */
const JAW_EASE = 1.4;

/** One point on the skull's profile, in head radii, clockwise from the crown. */
export function headPt(deg: number, radius: number, build: number): Point {
  const narrow = 1.0 - SKULL_NARROW * build;
  const jawPull = 0.2 * build;
  const chinDrop = 0.05 * build;
  const th = radians(deg);
  let x = pySin(th) * radius * narrow;
  let y = -pyCos(th) * radius;
  if (y > JAW_START_Y) {
    // 0 where the taper starts, 1 at the chin.
    const lean = pyMin(1.0, (y - JAW_START_Y) / (1.0 - JAW_START_Y));
    x *= 1.0 - jawPull * pyPow(lean, JAW_EASE);
    y *= 1.0 + chinDrop * lean;
  }
  return [x, y];
}

/** The skull: a circle at the chibi end, a narrower jawed oval at the adult end. */
export function headShape(build: number): Chain {
  // Control-point radius that makes a quadratic chain trace a unit circle.
  const k = 1 / pyCos(Math.PI / HEAD_SEGMENTS);
  const step = 360 / HEAD_SEGMENTS;
  const anchors: Point[] = [];
  const controls: Point[] = [];
  for (let i = 0; i < HEAD_SEGMENTS; i++) anchors.push(headPt(i * step, 1.0, build));
  for (let i = 0; i < HEAD_SEGMENTS; i++) controls.push(headPt((i + 0.5) * step, k, build));
  const segments: Segment[] = [];
  for (let i = 0; i < HEAD_SEGMENTS; i++) segments.push([controls[i] as Point, anchors[(i + 1) % HEAD_SEGMENTS] as Point]);
  return [anchors[0] as Point, segments];
}

// ---------------------------------------------------------------------------------------------------------
// The neck

const CHIN_SHADOW_CLIP_ID = "chin-shadow";
const CHIN_SHADOW_DROP = 0.16;
const CHIN_SHADOW_VALUE = 0.88;

/** The band of shadow under the jaw, clipped to the neck's skin `neck`. */
export function chinShadow(sk: Skeleton, p: CharacterParams, neck: string): string {
  const faceBuild = sk.build + sk.face_maturity * (1.0 - sk.build);
  const [start, segments] = headShape(faceBuild);
  const d = curve(sk.head_cx, sk.head_cy + CHIN_SHADOW_DROP * sk.head_r, sk.head_r, start, segments);
  const tone = shade(p.skin_tone, CHIN_SHADOW_VALUE);
  return `<clipPath id="${CHIN_SHADOW_CLIP_ID}">${neck}</clipPath><path d="${d}" fill="${tone}" clip-path="url(#${CHIN_SHADOW_CLIP_ID})" />`;
}

/** How far below the chin a bare throat may run, in head radii. */
const BARE_NECK_BELOW_CHIN = 0.16;

/** How far above the measured shoulder a bare neck meets the body, or 0. */
export function bareNeckLift(sk: Skeleton): number {
  const below = sk.shoulder_y - (sk.head_cy + sk.head_r);
  const cap = sk.head_r * BARE_NECK_BELOW_CHIN;
  if (below <= cap) return 0.0;
  return below - cap;
}

/** `sk` with the bare shoulder raised, when a coat is not covering it. */
export function bareShoulderSk(sk: Skeleton, p: CharacterParams): Skeleton {
  if (p.outfit.tunic_color !== null || p.outfit.coat_color !== null) return sk;
  const lift = bareNeckLift(sk);
  if (lift <= 0.0) return sk;
  return replace(sk, { shoulder_y: sk.shoulder_y - lift });
}

const BODY_INSET = 1.5;

/** How far inside the tunic's outline the body is drawn: `BODY_INSET` strokes under a tunic, none without one. */
export function bodyInset(sk: Skeleton, p: CharacterParams): number {
  return p.outfit.tunic_color === null ? 0.0 : strokeW(sk) * BODY_INSET;
}

export function neck(sk: Skeleton, p: CharacterParams): string {
  // Plain skin, not a shadow tone.
  const w = sk.neck_half_w * 2;
  const x = sk.head_cx - w / 2;
  // Runs past the shoulder line so the tunic's V notch, drawn over it, opens onto skin.
  const body = bareShoulderSk(sk, p);
  const meet = body.shoulder_y;
  const h = meet - sk.neck_y + sk.neck_half_w * 1.1;
  const rx = w * 0.35;
  const parts = [
    `<rect x="${fmt1(x)}" y="${fmt1(sk.neck_y)}" width="${fmt1(w)}" height="${fmt1(h)}" rx="${fmt1(rx)}" fill="${p.skin_tone}" />`,
  ];
  if (truthy(p.face.chin_shadow)) {
    parts.push(
      chinShadow(
        sk,
        p,
        `<rect x="${fmt1(x)}" y="${fmt1(sk.neck_y)}" width="${fmt1(w)}" height="${fmt1(h)}" rx="${fmt1(rx)}" />`,
      ),
    );
  }
  // The throat's own contour: silhouette between the jaw and the shoulder, so full weight.
  const end = meet + 2 * bodyInset(sk, p);
  for (const side of [-1, 1]) {
    const nx = sk.head_cx + side * sk.neck_half_w;
    parts.push(
      `<line x1="${fmt1(nx)}" y1="${fmt1(sk.neck_y)}" x2="${fmt1(nx)}" y2="${fmt1(end)}" ` +
        `stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)))}" />`,
    );
  }
  return parts.join("");
}

// ---------------------------------------------------------------------------------------------------------
// A mask

const MASK_HALF_W = 0.5;
const MASK_TOP = 0.1;
const MASK_H = 0.46;
const MASK_PLEATS = 3;

/** A face mask pulled down under the chin. Drawn before the head: the jaw covers the mask's top edge. */
export function mask(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.mask_color === null) return "";
  const cx = sk.head_cx;
  const cy = sk.head_cy;
  const r = sk.head_r;
  const color = p.outfit.mask_color;
  const sw = strokeW(sk);
  const chinY = cy + r;
  const top = chinY - r * MASK_TOP;
  const bot = top + r * MASK_H;
  const hwTop = r * MASK_HALF_W;
  const hwBot = hwTop * 0.9;
  const crease = shade(color, 0.78);
  const loops = [-1, 1]
    .map(
      (side) =>
        `<path d="M ${fmt1(cx + side * hwTop)} ${fmt1(top + r * 0.04)} ` +
        `Q ${fmt1(cx + side * r * 0.98)} ${fmt1(top + r * 0.1)} ${fmt1(cx + side * r * 0.92)} ${fmt1(cy + r * 0.3)}" ` +
        `fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(interiorW(sw, 0.8))}" stroke-linecap="round" />`,
    )
    .join("");
  const body =
    `<path d="M ${fmt1(cx - hwTop)} ${fmt1(top)} L ${fmt1(cx + hwTop)} ${fmt1(top)} ` +
    `L ${fmt1(cx + hwBot)} ${fmt1(bot - r * 0.06)} Q ${fmt1(cx + hwBot)} ${fmt1(bot)} ${fmt1(cx + hwBot - r * 0.06)} ${fmt1(bot)} ` +
    `L ${fmt1(cx - hwBot + r * 0.06)} ${fmt1(bot)} Q ${fmt1(cx - hwBot)} ${fmt1(bot)} ${fmt1(cx - hwBot)} ${fmt1(bot - r * 0.06)} Z" ` +
    `fill="${color}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw))}" stroke-linejoin="round" />`;
  const pleatLines: string[] = [];
  for (let i = 1; i <= MASK_PLEATS; i++) {
    pleatLines.push(
      `<path d="M ${fmt1(cx - hwTop * (1 - 0.1 * (i / MASK_PLEATS)) + r * 0.05)} ${fmt1(top + ((bot - top) * i) / (MASK_PLEATS + 1))} ` +
        `L ${fmt1(cx + hwTop * (1 - 0.1 * (i / MASK_PLEATS)) - r * 0.05)} ${fmt1(top + ((bot - top) * i) / (MASK_PLEATS + 1))}" ` +
        `fill="none" stroke="${crease}" stroke-width="${fmt2(interiorW(sw, 0.7))}" stroke-linecap="round" />`,
    );
  }
  return loops + body + pleatLines.join("");
}

// ---------------------------------------------------------------------------------------------------------
// A hat's brim, underneath

/** The underside of a hat's brim, behind the hair and everything else. */
export function hatUnderside(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.hat_color === null) return "";
  const [start, segments] = HAT_UNDERSIDE;
  const d = curve(sk.head_cx, sk.head_cy, sk.head_r, start, segments);
  const fill = shade(p.outfit.hat_color, 0.62);
  return `<path d="${d}" fill="${fill}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)))}" />`;
}

// ---------------------------------------------------------------------------------------------------------
// The document

/** The SVG document around `body`, as `render_character` writes it. */
export function documentWrap(sk: Skeleton, body: string, background: string | null = null, metadata = ""): string {
  // Emitted only when asked for, rather than always drawn and sometimes painted over.
  const bg = background ? `  <rect width="100%" height="100%" fill="${background}" />\n` : "";
  const md = metadata ? `  ${metadata}\n` : "";
  return (
    `<svg xmlns="http://www.w3.org/2000/svg" width="${fmt0(sk.canvas_w)}" height="${fmt0(sk.canvas_h)}" ` +
    `viewBox="0 0 ${fmt0(sk.canvas_w)} ${fmt0(sk.canvas_h)}">\n` +
    `${md}${bg}  ${body}\n` +
    `</svg>\n`
  );
}
