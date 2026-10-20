// A raised arm of the adult woman (docs/franzi-expressions-plan.md, steps 3 and 4).
//
// The body outline leaves the arm out on a raised side (adultBodyPath's `without`) and this draws it on its own: the hanging arm, built from the same knot tables as the outline's (the
// shoulder's outer edge, `ARM_OUTER` and `ARM_INNER`) with the traced open palm or fist at the wrist, turned as one piece about the shoulder by the angle the companion sends. Turning it
// is a `rotate` on a group, so the widths and the stroke weights come through unchanged and the arm is exactly the hanging arm, raised. The viewer's-right arm is the mirror image, turned
// the other way.
//
// Two layers, because the garments go between them: the skin (the arm's fill and its outline, in the `_torso` slot, under the garments) and the hand's interior (nails, creases, lines, in
// the `_arms` slot, over them). The arm's top is a straight chord across the shoulder's tip, filled but not stroked, with the pivot at its middle, so it turns in place and the body's own outline
// (which runs under it, in to the armpit) is hidden by the arm's fill. Only the arm's own edges are stroked: the outer edge, the hand, the inner edge.

import { OUTLINE, outlineW, strokeW } from "./character.ts";
import { ARM_INNER, ARM_OUTER, SHOULDER_OUTER } from "./body-adult-data.ts";
import { HAND_D_CUT, HAND_STROKE_K } from "./body-adult-hand-data.ts";
import { HAND_FIST_OUTLINE, HAND_OPEN_OUTLINE } from "./body-adult-hand-poses-data.ts";
import { HAND_FIST_CAVITY, HAND_FIST_FINGERS, HAND_FIST_NAILS, HAND_OPEN_LINES, HAND_OPEN_LINE_WIDTHS } from "./body-adult-hand-poses-lines-data.ts";
import { adultArms, adultTorso, at, place, quad, smooth, taperedStrand, type Knots, type Pt } from "./body-adult-parts.ts";
import { RAISED_SHOULDER_D, adultArmPoses, type ArmPose } from "./body-adult-pose.ts";
import { colorStr } from "./body-parts-legs.ts";
import { tint } from "./colorutil.ts";
import type { CharacterParams } from "./params.ts";
import { fmt1, fmt2 } from "./pynum.ts";
import type { Skeleton } from "./skeleton.ts";
import type { Chain } from "./tables.ts";

/** Where the raised arm begins, in head heights below the chin: the shoulder's tip, from where it turns. */
const D_TOP = RAISED_SHOULDER_D;
/** The arm's width there and where the knot tables take over (1.1), in head heights: the arm above the tables' range thickens linearly between them. */
const WIDTH_TOP = 0.15;
const D_TABLES = 1.1;
/** The taper of the stroke from the arm's weight to the hand's, as in `adultBodyStroke`: over this many head heights below the wrist, in this many bands. */
const TAPER = 0.32;
const BANDS = 8;

const OUTER: Knots = [[D_TOP, at(SHOULDER_OUTER, D_TOP)], ...SHOULDER_OUTER.filter(([d]) => d > D_TOP + 1e-6), ...ARM_OUTER.filter(([d]) => d <= HAND_D_CUT + 1e-6)];
const INNER_BELOW: Knots = ARM_INNER.filter(([d]) => d <= HAND_D_CUT + 1e-6);
/** The inner edge above the tables: the outer edge less the width, which grows from `WIDTH_TOP` to the tables' own width at `D_TABLES`. */
const INNER_ABOVE: Knots = (() => {
  const first = INNER_BELOW[0] as readonly [number, number];
  const widthAt = at(OUTER, first[0]) - first[1];
  return [D_TOP, 0.6, 0.8, 0.95, first[0]].map((d): readonly [number, number] => [d, at(OUTER, d) - (WIDTH_TOP + ((widthAt - WIDTH_TOP) * (d - D_TOP)) / (first[0] - D_TOP))]);
})();
const INNER: Knots = [...INNER_ABOVE.filter(([d]) => d < D_TABLES - 1e-6), ...INNER_BELOW];

const pixelFrame = { head_cx: 0, head_cy: 0, head_r: 1 } as Skeleton; // taperedStrand reads a chain in head radii; this frame makes it read pixels

interface ArmGeometry {
  /**
   * The arm's own edges (outer edge, hand, inner edge) as an open path. It is stroked as it is, and filled as it is too: a fill closes an open path with a straight line from its end to its
   * start, which is the arm's top chord, so the arm's long outline is written once.
   */
  readonly edge: string;
  /** `rotate(...)` turning the hanging arm about the shoulder. */
  readonly turn: string;
  /** Maps a [v, d] knot point to the hanging arm's canvas position. */
  readonly px: (q: Pt) => Pt;
  readonly id: string;
}

function armGeometry(sk: Skeleton, pose: ArmPose): ArmGeometry {
  const { cx, y, w } = place(sk);
  const hs = outlineW(strokeW(sk)) / 2;
  const sign = pose.sign;
  const rev = <T,>(a: readonly T[]): T[] => [...a].reverse();
  // the outer edge is the ink's edge less half a stroke toward the centre line, the inner edge half a stroke away from it, as in the body outline
  const outer = OUTER.map(([d, v]): Pt => [cx + sign * (w(d, v) - hs), y(d)]);
  const inner = INNER.map(([d, v]): Pt => [cx + sign * (w(d, v) + hs), y(d)]);
  const px = (q: Pt): Pt => [cx + sign * w(q[1], q[0]), y(q[1])];
  const chain = pose.hand === "fist" ? HAND_FIST_OUTLINE : HAND_OPEN_OUTLINE;
  const [start, segs] = chain;
  const walk = (): string => {
    if (sign < 0) return segs.map(([c, e]) => quad(px(c), px(e))).join("");
    const ends: Pt[] = [start, ...segs.map(([, e]) => e)];
    return segs.map(([c], i) => quad(px(c), px(ends[i] as Pt))).reverse().join("");
  };
  const o0 = outer[0] as Pt;
  const i0 = inner[0] as Pt;
  const edge = `M ${fmt1(o0[0])} ${fmt1(o0[1])} ` + smooth(outer) + walk() + smooth(rev(inner));
  // the top is the straight chord a fill closes the path with, from the inner end back to the outer end: filled, not stroked, and the pivot is its middle, so it turns in place and stays in
  // the shoulder (a half circle over the top, tried first, swung out of the torso at the armpit for some angles and left a nub of skin with no outline)
  const pivot: Pt = [(o0[0] + i0[0]) / 2, (o0[1] + i0[1]) / 2];
  // the viewer's-left arm turns clockwise on the page (outward, then up), the viewer's-right one the other way
  const turn = `rotate(${fmt2(-sign * pose.angle)} ${fmt1(pivot[0])} ${fmt1(pivot[1])})`;
  return { edge, turn, px, id: `adult-pose-${sign < 0 ? "l" : "r"}` };
}

/** Clip paths by band across the wrist: above it, the taper's bands, and the hand below. Rectangles in the hanging arm's frame, which the group's turn carries with it. */
function strokeBands(sk: Skeleton, id: string): { clips: string; strokes: (width: number) => string[]; hand: string } {
  const { y } = place(sk);
  const big = Math.max(sk.canvas_w, sk.canvas_h) * 2;
  const rect = (y0: number, y1: number): string => `<rect x="${fmt1(-big)}" y="${fmt1(y0)}" width="${fmt1(3 * big)}" height="${fmt1(y1 - y0)}" />`;
  const top = y(HAND_D_CUT);
  const end = y(HAND_D_CUT + TAPER);
  const lap = 0.4;
  let clips = `<clipPath id="${id}-arm">${rect(-big, top)}</clipPath>`;
  for (let i = 0; i < BANDS; i++) clips += `<clipPath id="${id}-t${i}">${rect(top + ((end - top) * i) / BANDS - lap, top + ((end - top) * (i + 1)) / BANDS)}</clipPath>`;
  clips += `<clipPath id="${id}-hand">${rect(end - lap, big)}</clipPath>`;
  const strokes = (width: number): string[] => {
    const attrs = (wid: number, clip: string): string => `fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(wid)}" stroke-linejoin="round" clip-path="url(#${clip})"`;
    const out = [`<use href="#${id}-edge" ${attrs(width, `${id}-arm`)} />`];
    for (let i = 0; i < BANDS; i++) out.push(`<use href="#${id}-edge" ${attrs(width * (1 - (1 - HAND_STROKE_K) * ((i + 1) / BANDS)), `${id}-t${i}`)} />`);
    out.push(`<use href="#${id}-edge" ${attrs(width * HAND_STROKE_K, `${id}-hand`)} />`);
    return out;
  };
  return { clips, strokes, hand: `<use href="#${id}-edge" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(width0(sk) * HAND_STROKE_K)}" stroke-linejoin="round" clip-path="url(#${id}-hand)" />` };
}

const width0 = (sk: Skeleton): number => outlineW(strokeW(sk));

/** The `transform` that turns a hanging arm, and whatever hangs from it, into the raised one: a garment's sleeve is turned with it. */
export const armTurn = (sk: Skeleton, pose: ArmPose): string => armGeometry(sk, pose).turn;

/** The raised arms' skin, in the `_torso` slot: each arm's fill and outline turned about its shoulder. */
export function adultPosedArmSkin(sk: Skeleton, p: CharacterParams): string {
  return adultArmPoses(p)
    .map((pose) => {
      const g = armGeometry(sk, pose);
      const bands = strokeBands(sk, g.id);
      return (
        `<g transform="${g.turn}"><defs><path id="${g.id}-edge" d="${g.edge}" /></defs>` +
        `<use href="#${g.id}-edge" fill="${colorStr(p.skin_tone)}" stroke="none" />${bands.clips}${bands.strokes(width0(sk)).join("")}</g>`
      );
    })
    .join("");
}

/** The hand's interior, turned with the arm: the open palm's lines, or the fist's cavity, finger separations and nails, clipped to the arm and the hand's outline drawn again over them. */
export function adultPosedArmDetail(sk: Skeleton, p: CharacterParams): string {
  return adultArmPoses(p)
    .map((pose) => {
      const g = armGeometry(sk, pose);
      const bands = strokeBands(sk, g.id);
      const inPx = ([start, segs]: Chain): Chain => [g.px(start), segs.map(([c, e]) => [g.px(c), g.px(e)] as [Pt, Pt])];
      const closed = (ch: Chain, attrs: string): string => {
        const [start, segs] = inPx(ch);
        return `<path d="M ${fmt1(start[0])} ${fmt1(start[1])} ` + segs.map(([c, e]) => quad(c, e)).join("") + `Z" ${attrs} />`;
      };
      const inkW = (k: number): string => fmt2(outlineW(strokeW(sk), k));
      const parts: string[] = [];
      if (pose.hand === "open") {
        HAND_OPEN_LINES.forEach((c, i) => parts.push(taperedStrand(pixelFrame, inPx(c), 0, OUTLINE, (HAND_OPEN_LINE_WIDTHS[i] as readonly number[]).map((v) => v * sk.head_r))));
      } else {
        for (const c of HAND_FIST_CAVITY) parts.push(closed(c, `fill="${OUTLINE}"`));
        for (const c of HAND_FIST_FINGERS) parts.push(closed(c, `fill="none" stroke="${OUTLINE}" stroke-width="${inkW(0.4)}" stroke-linejoin="round"`));
        for (const c of HAND_FIST_NAILS) parts.push(closed(c, `fill="${tint(p.skin_tone, 0.28)}" stroke="${OUTLINE}" stroke-width="${inkW(0.3)}" stroke-linejoin="round"`));
      }
      return (
        `<g transform="${g.turn}"><clipPath id="${g.id}-in"><use href="#${g.id}-edge" /></clipPath><g clip-path="url(#${g.id}-in)">${parts.join("")}</g>` +
        // the skin's edge is the hand's edge, so the details covered half of its stroke: drawn again over them at the hand's weight
        `${bands.hand}</g>`
      );
    })
    .join("");
}

/** The adult torso layer with the raised arms' skin after it. */
export const adultTorsoPosed = (sk: Skeleton, p: CharacterParams): string => adultTorso(sk, p) + adultPosedArmSkin(sk, p);

/** The adult hands' layer with the raised arms' hand interior after it (called with `false` for the arms' first pass under a coat, it draws nothing, as `adultArms` does). */
export const adultArmsPosed = (sk: Skeleton, p: CharacterParams, only: boolean | null = null): string => adultArms(sk, p, only) + (only === false ? "" : adultPosedArmDetail(sk, p));

/** The parts that draw a raised arm, laid over `ADULT_PARTS` by render.ts. */
export const ADULT_POSE_PARTS = {
  _torso: adultTorsoPosed,
  _arms: adultArmsPosed,
};
