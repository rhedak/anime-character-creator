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
import { BODY_OUTLINE_ID, RIB_KNOTS, adultArms, adultTorso, at, place, quad, smooth, taperedStrand, withoutFirstSpan, type Knots, type Pt } from "./body-adult-parts.ts";
import { ARM_ELBOW_MIN, RAISED_SHOULDER_D, adultArmPoses, type ArmPose } from "./body-adult-pose.ts";
import { colorStr } from "./body-parts-legs.ts";
import { tint } from "./colorutil.ts";
import type { CharacterParams } from "./params.ts";
import { fmt1, fmt2 } from "./pynum.ts";
import type { Skeleton } from "./skeleton.ts";
import type { Chain } from "./tables.ts";

/** Where the raised arm begins, in head heights below the chin: the shoulder's tip, from where it turns. */
const D_TOP = RAISED_SHOULDER_D;
/**
 * Where the armpit begins, in head heights below the chin: the hanging arm's armpit crease starts here. An arm held close to the body (under `TRIM_BELOW` degrees) strokes its inner edge only from
 * here down, because above it that edge is inside the shoulder and read as a seam through it; a raised arm strokes all of it, being its visible underside.
 */
const D_ARMPIT = 0.5;
const TRIM_BELOW = 30;
/** Over how many degrees past `TRIM_BELOW` the pivot moves from the outer tip back to the middle of the top chord. */
const PIVOT_BLEND = 20;
/** The arm's width there and where the knot tables take over (1.1), in head heights: the arm above the tables' range thickens linearly between them. */
const WIDTH_TOP = 0.15;
const D_TABLES = 1.1;
/** The taper of the stroke from the arm's weight to the hand's, as in `adultBodyStroke`: over this many head heights below the wrist, in this many bands. */
const TAPER = 0.32;
const BANDS = 8;
/** How far the forearm's edge goes on over the upper arm past the crease of a bent arm, in head heights, and the weight of each of its bands as a fraction of the outline's. */
const FOLD_LEN = 0.35;
const FOLD_K = [1, 1, 0.7];

const OUTER: Knots = [[D_TOP, at(SHOULDER_OUTER, D_TOP)], ...SHOULDER_OUTER.filter(([d]) => d > D_TOP + 1e-6), ...ARM_OUTER.filter(([d]) => d <= HAND_D_CUT + 1e-6)];
const INNER_BELOW: Knots = ARM_INNER.filter(([d]) => d <= HAND_D_CUT + 1e-6);
/** The inner edge above the tables: the outer edge less the width, which grows from `WIDTH_TOP` to the tables' own width at `D_TABLES`. */
const INNER_ABOVE: Knots = (() => {
  const first = INNER_BELOW[0] as readonly [number, number];
  const widthAt = at(OUTER, first[0]) - first[1];
  return [D_TOP, D_ARMPIT, 0.6, 0.8, 0.95, first[0]].map((d): readonly [number, number] => [d, at(OUTER, d) - (WIDTH_TOP + ((widthAt - WIDTH_TOP) * (d - D_TOP)) / (first[0] - D_TOP))]);
})();
const INNER: Knots = [...INNER_ABOVE.filter(([d]) => d < D_TABLES - 1e-6), ...INNER_BELOW];

const pixelFrame = { head_cx: 0, head_cy: 0, head_r: 1 } as Skeleton; // taperedStrand reads a chain in head radii; this frame makes it read pixels

interface ArmGeometry {
  /**
   * The arm without its hand, closed: the outer edge, across the wrist, the whole inner edge and, by the fill's closing chord, the shoulder's top. The skin is this and the hand's own path filled (a
   * fill closes an open path with a straight line from its end to its start, which for the hand is the wrist), so the hand's long outline is written once.
   */
  readonly fill: string;
  /** The `transform` of the group the arm is drawn in: the turn of the arm about the shoulder (and, when it is bent, of the forearm about the elbow). */
  readonly turn: string;
  /** The turn of the upper arm alone, about the shoulder: what a sleeve on the upper arm is carried by. */
  readonly upperTurn: string;
  /** Maps a [v, d] knot point to the hanging arm's canvas position (in the forearm's own frame, where the hand is). */
  readonly px: (q: Pt) => Pt;
  /** The shoulder joint, in canvas units: the middle of the arm's top chord, which the turn leaves where it is. */
  readonly pivot: Pt;
  readonly id: string;
  /** The three open paths the arm is stroked by: the outer edge down to the wrist, the hand, and the inner edge back up (from the armpit, for an arm held close to the body). */
  readonly pieces: { readonly armA: string; readonly hand: string; readonly armB: string; readonly fold: readonly string[] };
}

/** The depth, in head heights below the chin, of the elbow joint: the middle of the arm between the shoulder's tip and the wrist, at a knot of both edge tables. */
const ELBOW_D = 1.3;

/** Points sampled to each span of an arm edge when one is cut or crossed. */
const N = 3;

/** Points along the Catmull-Rom curve through `pts`, `n` to each span, the knots included (the curve `smooth` draws). */
function catmull(pts: readonly Pt[], n: number): Pt[] {
  const out: Pt[] = [pts[0] as Pt];
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)] as Pt;
    const p1 = pts[i] as Pt;
    const p2 = pts[i + 1] as Pt;
    const p3 = pts[Math.min(pts.length - 1, i + 2)] as Pt;
    for (let k = 1; k <= n; k++) {
      const t = k / n;
      const f = (a: number, b: number, c: number, d: number): number => 0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t * t * t);
      out.push([f(p0[0], p1[0], p2[0], p3[0]), f(p0[1], p1[1], p2[1], p3[1])]);
    }
  }
  return out;
}

/** `q` turned by `deg` degrees about `c`, clockwise on the page (SVG's `rotate`). */
function turned(q: Pt, c: Pt, deg: number): Pt {
  const a = (deg * Math.PI) / 180;
  const [dx, dy] = [q[0] - c[0], q[1] - c[1]];
  return [c[0] + dx * Math.cos(a) - dy * Math.sin(a), c[1] + dx * Math.sin(a) + dy * Math.cos(a)];
}

/** Where segment a-b crosses segment c-d, or null. */
function crossing(a: Pt, b: Pt, c: Pt, d: Pt): Pt | null {
  const [r0, r1] = [b[0] - a[0], b[1] - a[1]];
  const [s0, s1] = [d[0] - c[0], d[1] - c[1]];
  const den = r0 * s1 - r1 * s0;
  if (Math.abs(den) < 1e-12) return null;
  const t = ((c[0] - a[0]) * s1 - (c[1] - a[1]) * s0) / den;
  const u = ((c[0] - a[0]) * r1 - (c[1] - a[1]) * r0) / den;
  return t >= 0 && t <= 1 && u >= 0 && u <= 1 ? [a[0] + t * r0, a[1] + t * r1] : null;
}

/**
 * Where the forearm's edge, cut at the crease of a bent arm, goes on: it lies over the upper arm as the fold between the two (the reference draws it). The edge past the crease, `FOLD_LEN` head
 * heights of it (`rest` runs from the crease back toward the elbow), as one open path per band, each band stroked thinner than the last (`FOLD_K`), so the line fades out into the skin.
 */
function foldLines(x: Pt, rest: readonly Pt[], length: number): string[] {
  const pts: Pt[] = [x, ...rest];
  const cut: Pt[] = [x];
  let run = 0;
  for (let i = 1; i < pts.length && run < length; i++) {
    const a = pts[i - 1] as Pt;
    const b = pts[i] as Pt;
    const d = Math.hypot(b[0] - a[0], b[1] - a[1]);
    const t = d > 0 ? Math.min(1, (length - run) / d) : 1;
    cut.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]);
    run += d;
  }
  if (cut.length < 2) return [];
  const per = Math.ceil((cut.length - 1) / FOLD_K.length);
  const out: string[] = [];
  for (let i = 0; i < FOLD_K.length; i++) {
    const part = cut.slice(i * per, Math.min(cut.length, (i + 1) * per + 1));
    if (part.length >= 2) out.push(`M ${fmt1((part[0] as Pt)[0])} ${fmt1((part[0] as Pt)[1])} ` + smooth(part));
  }
  return out;
}

function armGeometry(sk: Skeleton, pose: ArmPose): ArmGeometry {
  const { cx, y, w } = place(sk);
  const hs = outlineW(strokeW(sk)) / 2;
  const sign = pose.sign;
  const rev = <T,>(a: readonly T[]): T[] => [...a].reverse();
  // the outer edge is the ink's edge less half a stroke toward the centre line, the inner edge half a stroke away from it, as in the body outline
  const outer = OUTER.map(([d, v]): Pt => [cx + sign * (w(d, v) - hs), y(d)]);
  // the knot above the tip, which the body's shoulder line runs through: the outer edge leaves the tip in the direction that line arrives in (see `withoutLastSpan`)
  const above = SHOULDER_OUTER.filter(([d]) => d < D_TOP - 1e-6).at(-1) as readonly [number, number];
  const outerFrom: Pt[] = [[cx + sign * (w(above[0], above[1]) - hs), y(above[0])], ...outer];
  const smoothOuter = withoutFirstSpan(smooth(outerFrom));
  const inner = INNER.map(([d, v]): Pt => [cx + sign * (w(d, v) + hs), y(d)]);
  const px = (q: Pt): Pt => [cx + sign * w(q[1], q[0]), y(q[1])];
  const chain = pose.hand === "fist" ? HAND_FIST_OUTLINE : HAND_OPEN_OUTLINE;
  const [, segs] = chain;
  // The path runs down the outer edge, round the hand and up the inner edge on both sides, and the chain runs outer edge to inner edge, so both sides walk it forward and only `px` mirrors it.
  // (The body outline walks the viewer's-right hand backwards because its path goes down the inner edge there; copying that here drew a jump across the wrist and the hand backwards.)
  const walk = (): string => segs.map(([c, e]) => quad(px(c), px(e))).join("");
  const o0 = outer[0] as Pt;
  const i0 = inner[0] as Pt;
  // the top is the straight chord a fill closes the path with, from the inner end back to the outer end: filled, not stroked, and the pivot is its middle, so it turns in place and stays in
  // the shoulder (a half circle over the top, tried first, swung out of the torso at the armpit for some angles and left a nub of skin with no outline)
  // An arm held close to the body turns about the outer tip instead, so its edge stays joined to the body's shoulder line there (turned about the middle the tip moves a pixel or so and the line
  // steps); by `TRIM_BELOW` + `PIVOT_BLEND` degrees it is the middle again.
  const toTip = Math.max(0, Math.min(1, 1 - (pose.angle - TRIM_BELOW) / PIVOT_BLEND));
  const pivot: Pt = [(o0[0] + i0[0]) / 2 + ((o0[0] - i0[0]) / 2) * toTip, (o0[1] + i0[1]) / 2 + ((o0[1] - i0[1]) / 2) * toTip];
  const id = `adult-pose-${sign < 0 ? "l" : "r"}`;
  // An arm held close to the body strokes its inner edge only from the armpit down, from where the body's own line (shoulder tip, in to the armpit and down the ribs) comes out from under the
  // arm's fill, so the arm's inner line and the body's meet there and the gap between arm and ribs closes at the top. With none found it starts at the armpit's knot.
  const kArmpit = INNER.findIndex(([d]) => Math.abs(d - D_ARMPIT) < 1e-9);
  const trim = pose.angle < TRIM_BELOW;
  const denseIh = catmull(inner, N);
  const armpit = (() => {
    if (!trim) return null;
    const torso = catmull([o0, ...RIB_KNOTS.map(([v, d]): Pt => [cx + sign * (w(d, v) - hs), y(d)])], N);
    const edge = denseIh.map((q) => turned(q, pivot, -sign * pose.angle));
    for (let t = 0; t < torso.length - 1; t++) {
      for (let j = 0; j < edge.length - 1; j++) {
        const x = crossing(torso[t] as Pt, torso[t + 1] as Pt, edge[j] as Pt, edge[j + 1] as Pt);
        if (x !== null) return { j, x: turned(x, pivot, sign * pose.angle) };
      }
    }
    return null;
  })();
  // the viewer's-left arm turns clockwise on the page (outward, then up), the viewer's-right one the other way
  const upperTurn = `rotate(${fmt2(-sign * pose.angle)} ${fmt1(pivot[0])} ${fmt1(pivot[1])})`;
  if (pose.bend < ARM_ELBOW_MIN) {
    const wrist = outer[outer.length - 1] as Pt;
    const last = px((segs[segs.length - 1] as readonly [unknown, Pt])[1]);
    const innerStroke = armpit !== null ? smooth(rev([armpit.x, ...denseIh.slice(armpit.j + 1)])) : smooth(rev(trim ? inner.slice(kArmpit) : inner));
    const pieces = {
      armA: `M ${fmt1(o0[0])} ${fmt1(o0[1])} ` + smoothOuter,
      hand: `M ${fmt1(wrist[0])} ${fmt1(wrist[1])} ` + walk(),
      armB: `M ${fmt1(last[0])} ${fmt1(last[1])} ` + innerStroke,
      fold: [],
    };
    const fill = `M ${fmt1(o0[0])} ${fmt1(o0[1])} ` + smoothOuter + `L ${fmt1(last[0])} ${fmt1(last[1])} ` + smooth(rev(inner));
    return { fill, turn: upperTurn, upperTurn, px, pivot, id, pieces };
  }

  // A bent arm. It is drawn in the forearm's own frame, where the forearm hangs straight and the hand is traced, and the group's transform is the turn about the shoulder after the bend about the
  // elbow, so the forearm, the hand, their details and the stroke bands need nothing else. The upper arm is then the hanging upper arm turned back by the bend about the elbow, and the two are
  // joined into one outline: where the bend closes (the outer edge) the edges cross and are cut at the crossing; where it opens (the inner edge) they are joined by a round elbow.
  const knot = (tab: Knots): number => tab.findIndex(([d]) => Math.abs(d - ELBOW_D) < 1e-9);
  const [ko, ki] = [knot(OUTER), knot(INNER)];
  if (ko < 0 || ki < 0) throw new Error("the arm tables have no knot at the elbow");
  const denseO = catmull(outerFrom, N).slice(N);
  const denseI = catmull(inner, N);
  const elbow: Pt = [((outer[ko] as Pt)[0] + (inner[ki] as Pt)[0]) / 2, ((outer[ko] as Pt)[1] + (inner[ki] as Pt)[1]) / 2];
  const half = Math.hypot((outer[ko] as Pt)[0] - (inner[ki] as Pt)[0], (outer[ko] as Pt)[1] - (inner[ki] as Pt)[1]) / 2;
  const bb = -sign * pose.bend;
  const upperO = denseO.slice(0, ko * N + 1).map((q) => turned(q, elbow, -bb));
  const upperI = denseI.slice(0, ki * N + 1).map((q) => turned(q, elbow, -bb));
  const lowerO = denseO.slice(ko * N);
  const lowerI = denseI.slice(ki * N);
  // the outer edge: cut both where they cross, near the elbow
  const K = 48;
  let hit: { x: Pt; a: number; b: number } | null = null;
  const a0 = Math.max(0, upperO.length - 1 - K);
  for (let a = upperO.length - 2; a >= a0 && !hit; a--) {
    for (let b = 0; b < Math.min(K, lowerO.length - 1); b++) {
      const x = crossing(upperO[a] as Pt, upperO[a + 1] as Pt, lowerO[b] as Pt, lowerO[b + 1] as Pt);
      if (x !== null) {
        hit = { x, a, b };
        break;
      }
    }
  }
  const outerCut = hit === null ? smooth(upperO) + `L ${fmt1((lowerO[0] as Pt)[0])} ${fmt1((lowerO[0] as Pt)[1])} ` + smooth(lowerO) : smooth([...upperO.slice(0, hit.a + 1), hit.x]) + smooth([hit.x, ...lowerO.slice(hit.b + 1)]);
  const wristOuter = lowerO[lowerO.length - 1] as Pt;
  const chainEnd = (segs[segs.length - 1] as readonly [unknown, readonly [number, number]])[1];
  const endPt = px(chainEnd as Pt);
  // the inner edge: down the forearm's inside to the elbow, round it, up the upper arm's inside
  const join = upperI[upperI.length - 1] as Pt;
  const arc = `A ${fmt1(half)} ${fmt1(half)} 0 0 ${-bb > 0 ? 1 : 0} ${fmt1(join[0])} ${fmt1(join[1])} `;
  const innerCut = smooth(rev(lowerI)) + arc + smooth(rev(upperI));
  const upperStroke = armpit !== null && armpit.j < upperI.length - 1 ? [turned(armpit.x, elbow, -bb), ...upperI.slice(armpit.j + 1)] : trim ? upperI.slice(kArmpit * N) : upperI;
  const innerStroke = smooth(rev(lowerI)) + arc + smooth(rev(upperStroke));
  const top = upperO[0] as Pt;
  const fill = `M ${fmt1(top[0])} ${fmt1(top[1])} ` + outerCut + `L ${fmt1(endPt[0])} ${fmt1(endPt[1])} ` + innerCut;
  const pieces = {
    armA: `M ${fmt1(top[0])} ${fmt1(top[1])} ` + outerCut,
    hand: `M ${fmt1(wristOuter[0])} ${fmt1(wristOuter[1])} ` + walk(),
    armB: `M ${fmt1(endPt[0])} ${fmt1(endPt[1])} ` + innerStroke,
    fold: hit === null ? [] : foldLines(hit.x, lowerO.slice(0, hit.b + 1).reverse(), FOLD_LEN * 2 * sk.head_r),
  };
  const turn = `${upperTurn} rotate(${fmt2(bb)} ${fmt1(elbow[0])} ${fmt1(elbow[1])})`;
  return { fill, turn, upperTurn, px, pivot, id, pieces };
}

/** The path definitions of an arm, for the `<defs>` of its group: its fill and the pieces it is stroked by. */
const armDefs = (g: ArmGeometry): string => `<path id="${g.id}-fill" d="${g.fill}" /><path id="${g.id}-arm-a" d="${g.pieces.armA}" /><path id="${g.id}-arm-b" d="${g.pieces.armB}" /><path id="${g.id}-hand-edge" d="${g.pieces.hand}" />${g.pieces.fold.map((d, i) => `<path id="${g.id}-fold-${i}" d="${d}" />`).join("")}`;

/** The skin: the arm without its hand and the hand, each filled (the hand's closing chord is the wrist). `attrs` are the presentation attributes of both. */
const skinUses = (g: ArmGeometry, attrs: string, transform = ""): string => `<use href="#${g.id}-fill" ${attrs}${transform} /><use href="#${g.id}-hand-edge" ${attrs}${transform} />`;

/**
 * Clip paths by band across the wrist, and the strokes: the two arm pieces are stroked whole in the arm's weight and the hand path is banded, tapering over `TAPER` below the wrist to the hand's weight
 * (the clips are rectangles in the arm's frame, which the group's transform carries with it).
 */
function strokeBands(sk: Skeleton, g: ArmGeometry): { clips: string; strokes: (width: number) => string[]; hand: string } {
  const id = g.id;
  const handId = `${id}-hand-edge`;
  const { y } = place(sk);
  const big = Math.max(sk.canvas_w, sk.canvas_h) * 2;
  const rect = (y0: number, y1: number): string => `<rect x="${fmt1(-big)}" y="${fmt1(y0)}" width="${fmt1(3 * big)}" height="${fmt1(y1 - y0)}" />`;
  const top = y(HAND_D_CUT);
  const end = y(HAND_D_CUT + TAPER);
  const lap = 0.4;
  let clips = "";
  for (let i = 0; i < BANDS; i++) clips += `<clipPath id="${id}-t${i}">${rect(top + ((end - top) * i) / BANDS - lap, top + ((end - top) * (i + 1)) / BANDS)}</clipPath>`;
  clips += `<clipPath id="${id}-hand">${rect(end - lap, big)}</clipPath>`;
  const strokes = (width: number): string[] => {
    const attrs = (wid: number, clip: string | null): string => `fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(wid)}" stroke-linejoin="round"${clip === null ? "" : ` clip-path="url(#${clip})"`}`;
    const out = [`<use href="#${id}-arm-a" ${attrs(width, null)} stroke-linecap="round" />`, `<use href="#${id}-arm-b" ${attrs(width, null)} stroke-linecap="round" />`];
    g.pieces.fold.forEach((_, i) => out.push(`<use href="#${id}-fold-${i}" ${attrs(width * (FOLD_K[i] as number), null)} stroke-linecap="round" />`));
    for (let i = 0; i < BANDS; i++) out.push(`<use href="#${handId}" ${attrs(width * (1 - (1 - HAND_STROKE_K) * ((i + 1) / BANDS)), `${id}-t${i}`)} />`);
    out.push(`<use href="#${handId}" ${attrs(width * HAND_STROKE_K, `${id}-hand`)} />`);
    return out;
  };
  return { clips, strokes, hand: `<use href="#${handId}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(width0(sk) * HAND_STROKE_K)}" stroke-linejoin="round" clip-path="url(#${id}-hand)" />` };
}

const width0 = (sk: Skeleton): number => outlineW(strokeW(sk));

/** The `transform` that turns the upper arm, and whatever hangs from it (a blouse's sleeve), into the raised one; the forearm of a bent arm is turned further by the elbow. */
export const armTurn = (sk: Skeleton, pose: ArmPose): string => armGeometry(sk, pose).upperTurn;

/** The raised arms' skin, in the `_torso` slot: each arm's fill and outline turned about its shoulder. */
export function adultPosedArmSkin(sk: Skeleton, p: CharacterParams): string {
  return adultArmPoses(p)
    .map((pose) => {
      const g = armGeometry(sk, pose);
      const bands = strokeBands(sk, g);
      return (
        `<g transform="${g.turn}"><defs>${armDefs(g)}</defs>` +
        `${skinUses(g, `fill="${colorStr(p.skin_tone)}" stroke="none"`)}${bands.clips}${bands.strokes(width0(sk)).join("")}</g>`
      );
    })
    .join("");
}

/** The hand's interior, turned with the arm: the open palm's lines, or the fist's cavity, finger separations and nails, clipped to the arm and the hand's outline drawn again over them. */
export function adultPosedArmDetail(sk: Skeleton, p: CharacterParams): string {
  return adultArmPoses(p)
    .map((pose) => {
      const g = armGeometry(sk, pose);
      const bands = strokeBands(sk, g);
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
        // the hand in front of what hangs over it (a skirt, an apron): its skin again, below the wrist, before its interior
        `<g transform="${g.turn}"><use href="#${g.id}-hand-edge" fill="${colorStr(p.skin_tone)}" stroke="none" clip-path="url(#${g.id}-hand)" />` +
        `<clipPath id="${g.id}-in"><use href="#${g.id}-fill" /><use href="#${g.id}-hand-edge" /></clipPath><g clip-path="url(#${g.id}-in)">${parts.join("")}</g>` +
        // the skin's edge is the hand's edge, so the details covered half of its stroke: drawn again over them at the hand's weight
        `${bands.hand}</g>`
      );
    })
    .join("");
}

/** How far round the shoulder joint the sleeve head's cloth reaches, in head heights: enough to cover the shoulder's top and the upper armpit, which the sleeve's own cloth leaves when it turns away. */
const SLEEVE_HEAD_R = 0.2;

/**
 * The sleeve head: where the blouse's sleeve turns away with the arm, the cloth that covered the shoulder goes with it and leaves bare skin beside the strap, and the sleeve's inner end is a
 * flat cut. So the blouse's colour is laid over the shoulder first: a disc about the joint (which a turn about the joint leaves where it is, so it fits at every angle), clipped to what is
 * skin there, the body without its arm and the arm, so it cannot reach past the silhouette. It goes in the torso layer, under the blouse's body piece, the bodice and the turned sleeve, which
 * hide its inner part, and the outline of the shoulder and of the arm's root is drawn again over it at full weight (the cloth would otherwise cover the inner half of the stroke).
 * Only with a blouse; with none the arm's skin is the shoulder.
 */
export function adultPosedSleeveHead(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.tunic_color === null) return "";
  const { cx, y, w } = place(sk);
  const ink = outlineW(strokeW(sk));
  return adultArmPoses(p)
    .map((pose) => {
      const g = armGeometry(sk, pose);
      const id = `${g.id}-head`;
      const r = SLEEVE_HEAD_R * 2 * sk.head_r;
      // the shoulder's outline over the head: the body outline's stroke in a box about the shoulder, on this side
      const box = [0.3, 0.8].map((v) => cx + pose.sign * w(0.2, v));
      const [bx0, bx1] = [Math.min(...box), Math.max(...box)];
      const bounds = `<clipPath id="${id}-box"><rect x="${fmt1(bx0)}" y="${fmt1(y(0.15))}" width="${fmt1(bx1 - bx0)}" height="${fmt1(y(0.75) - y(0.15))}" /></clipPath>`;
      const bands = strokeBands(sk, g);
      return (
        `<clipPath id="${id}-clip"><use href="#${BODY_OUTLINE_ID}" /><use href="#${g.id}-fill" transform="${g.turn}" /><use href="#${g.id}-hand-edge" transform="${g.turn}" /></clipPath>` +
        `<g clip-path="url(#${id}-clip)"><circle cx="${fmt1(g.pivot[0])}" cy="${fmt1(g.pivot[1])}" r="${fmt1(r)}" fill="${colorStr(p.outfit.tunic_color as string)}" /></g>` +
        bounds +
        `<use href="#${BODY_OUTLINE_ID}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(ink)}" stroke-linejoin="round" clip-path="url(#${id}-box)" />` +
        `<g transform="${g.turn}">${bands.strokes(ink).join("")}</g>`
      );
    })
    .join("");
}

/** The adult torso layer with the raised arms' skin after it, and the blouse's sleeve head over the shoulder. */
export const adultTorsoPosed = (sk: Skeleton, p: CharacterParams): string => adultTorso(sk, p) + adultPosedArmSkin(sk, p) + adultPosedSleeveHead(sk, p);

/** The adult hands' layer with the raised arms' hand interior after it (called with `false` for the arms' first pass under a coat, it draws nothing, as `adultArms` does). */
export const adultArmsPosed = (sk: Skeleton, p: CharacterParams, only: boolean | null = null): string => adultArms(sk, p, only) + (only === false ? "" : adultPosedArmDetail(sk, p));

/** The parts that draw a raised arm, laid over `ADULT_PARTS` by render.ts. */
export const ADULT_POSE_PARTS = {
  _torso: adultTorsoPosed,
  _arms: adultArmsPosed,
};
