// The hands: the traced open hand and the constructed fist (built at import time from the ported shape code), the cuff
// opening a hand comes out of, the placements, and the mitten family of styles. Port of the hand code of character.py,
// `core-limbs` module (see `harness/ts_port/modules.json`). Functions that return a placement closure or take a callable
// (`tracedPlacement`, `mittenPlacement`, `mittenPath`, `handNotched`, `handStroked`, `handCurled`) have no recorded calls; the
// styles are exercised through `hand`.

import { OUTLINE, interiorW, outlineW, quadPoint, strokeW } from "./character.ts";
import { armLine, handLength, limbBuild, maxOf, minOf, sleevePlacement, wornSleeve } from "./core-limbs.ts";
import { cosRounded, powRounded, sinRounded } from "./core-limbs-pow.ts";
import { HAND_FIST_INTO, HAND_RELAXED, HAND_RELAXED_INTO } from "./core-limbs-tables.ts";
import type { HandPiece } from "./core-limbs-tables.ts";
import type { CharacterParams } from "./params.ts";
import { PyError, at, copysign, fmt1, fmt2, pyCos, pyDiv, pyMax, pyModInt, pySin, pySlice, pySum, radians } from "./pynum.ts";
import type { Skeleton } from "./skeleton.ts";
import type { Chain, Point, Segment } from "./tables.ts";

// ---------------------------------------------------------------------------------------------------------
// The hands
//
// The traced hands (`HAND_RELAXED`, in `core-limbs-tables.ts`) are two hands traced off the reference
// (`harness/trace_hands/`): her left hand hanging (`relaxed`, the viewer's right) and her right hand round the staff
// (`grip`, the viewer's left). Each is its pieces in drawing order, every piece its outline, its holes (the page
// showing through) and its interior lines, grown to the stroke's centre line. Points are relative to the wrist's
// centre where the skin meets the cuff, in the picture's own axes (x right, y down), in units of the hand's length.

// The grip is constructed, not traced (`docs/hands-plan.md`, H4). The hand traced off
// the realistic reference read as a skinny thumb and angular rolls on a chibi's arm;
// the canon's own staff hand (`ref/katherina/katherina_grok.jpg`) is a chunky fist:
// four short rounded finger rolls stacked on the pole side with three crease strokes,
// and a big rounded back of the hand with the thumb folded into it. This draws that,
// in the hand frame the traced grip used (origin at the wrist's centre, x in hand
// lengths with the fingers toward -x, y down), so the placement, the cuff fit and the
// staff channel work as they did.

/**
 * A smooth closed chain through a rough polygon: the quadratic B-spline whose
 * control points are `pts`, its anchors the midpoints of the polygon's edges.
 */
export function bsplineClosed(pts: readonly Point[]): Chain {
  const n = pts.length;
  const mid: Point[] = [];
  for (let i = 0; i < n; i++) {
    const a = pts[i] as Point;
    const b = pts[pyModInt(i + 1, n)] as Point;
    mid.push([(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]);
  }
  const segs: Segment[] = [];
  for (let i = 0; i < n; i++) segs.push([pts[pyModInt(i + 1, n)] as Point, mid[pyModInt(i + 1, n)] as Point]);
  return [at(mid, 0), segs];
}

/**
 * `n` points round a rounded rectangle of half-sizes `a` and `b`: exponent `e` is 2
 * for an ellipse and squarer above it.
 */
export function roundedBox(cx: number, cy: number, a: number, b: number, e: number, n = 16): Point[] {
  const pts: Point[] = [];
  for (let i = 0; i < n; i++) {
    const t = pyDiv(2 * Math.PI * i, n);
    const [ct, st] = [cosRounded(t), sinRounded(t)];
    pts.push([
      // `**` here is `powRounded` and not the kernel's `pyPow`: see `core-limbs-pow.ts`.
      cx + a * copysign(powRounded(Math.abs(ct), pyDiv(2, e)), ct),
      cy + b * copysign(powRounded(Math.abs(st), pyDiv(2, e)), st),
    ]);
  }
  return pts;
}

/**
 * The fist's two pieces in drawing order: the finger block with its three creases,
 * then the back of the hand (last, which `_grip_channel` reads) with the thumb's
 * crease. Rounded shapes from a few numbers, so a change is one number.
 */
export function fist(): HandPiece[] {
  const block = bsplineClosed(roundedBox(-0.67, 0.03, 0.33, 0.39, 3.4));
  const creases: Chain[] = [-0.165, 0.03, 0.225].map((y): Chain => [[-0.99, y], [[[-0.82, y + 0.015], [-0.6, y]]]]);
  const back = bsplineClosed(roundedBox(-0.3, 0.0, 0.4, 0.46, 2.7));
  const thumb: Chain[] = [[[-0.52, -0.3], [[[-0.6, -0.02], [-0.4, 0.14]]]]];
  return [
    [block, [], creases],
    [back, [], thumb],
  ];
}

export const HAND_FIST: readonly HandPiece[] = fist();

// (end of the traced hands)

// The open hand's length, head radii. The reference's hand is an adult's, about the
// face's length; at 0.50 on our wrist it hung to mid-thigh and read as thin. 0.36
// brings its box to the mitten's height; `_HAND_OPEN_STRETCH` then gives it the
// mitten's width (a per-axis scale, on purpose: the target is a chibi's proportions,
// not the reference's). The fist, built here, is 0.50, the size the canon's matches.
export const HAND_OPEN_LENGTH = 0.36;
export const HAND_OPEN_STRETCH = 2.0;
export const HAND_FIST_LENGTH = 0.5;
// How far a traced hand's wrist sits under its cuff, head radii: the hand is drawn
// under its arm, so the cuff's edge lies over the wrist.
export const HAND_CUFF_TUCK = 0.04;
// The open hand's first stretch, its wrist, in hand lengths down from the wrist
// line: over it the hand widens from its traced width to `_HAND_WRIST_FILL` of the
// cuff's opening, so it fills the sleeve or runs on from a bare forearm.
export const HAND_WRIST_STRETCH = 0.3;
export const HAND_WRIST_FILL = 1.1;
// The share of the arm's swing the fist turns back against it, so the finger rolls stay
// level as the canon's do (`_HAND_FIST_UPRIGHT`, owned with the staff: the same 0.85).
export const HAND_FIST_UPRIGHT = 0.85;

/** Points along a fitted chain. */
export function chainPoints(ch: Chain, per = 8): Point[] {
  const [start, segs] = ch;
  const pts: Point[] = [start];
  let p0 = start;
  for (const [c1, p2] of segs) {
    for (let k = 1; k < per + 1; k++) pts.push(quadPoint(p0, c1, p2, pyDiv(k, per)));
    p0 = p2;
  }
  return pts;
}

/**
 * The traced open hand's outline with its wrist end squared off. The trace followed
 * the reference's forearm meeting the hand at an angle, so the top edge is bevelled on
 * the left and its stroke corners drew as ticks below a cuff or on a bare arm. Every
 * point above `y_cut` goes; each side is carried straight up from its own point to a
 * flat top at `top`.
 */
export function squareWrist(chain: Chain, top = -0.033, y_cut = 0.06): Chain {
  const pts = pySlice(chainPoints(chain, 4), null, -1); // closed: the last point is the first
  const n = pts.length;
  const inside = new Set<number>();
  pts.forEach(([, y], i) => {
    if (y < y_cut) inside.add(i);
  });
  let firstOut: number | null = null;
  for (let i = 0; i < n; i++) {
    if (!inside.has(i) && inside.has(pyModInt(i - 1, n))) {
      firstOut = i;
      break;
    }
  }
  if (firstOut === null) throw new PyError("StopIteration", "");
  const keep = [...pts.slice(firstOut), ...pts.slice(0, firstOut)].filter((q) => q[1] >= y_cut);
  const a = at(keep, 0);
  const b = at(keep, -1);
  const ring: Point[] = [...keep, [b[0], top], [a[0], top]];
  const nxt = [...ring.slice(1), ...ring.slice(0, 1)];
  return [
    at(ring, 0),
    ring.map((p, i): Segment => {
      const q = nxt[i] as Point;
      return [[(p[0] + q[0]) / 2, (p[1] + q[1]) / 2], q];
    }),
  ];
}

// The open hand: the traced relaxed hand's outline alone, squared at the wrist. Its two
// fingertip slivers and its interior lines are left out: they overlapped into one dark
// knot at the fingertips at this size (`docs/hands-status.md`, W3).
export const HAND_OPEN: readonly HandPiece[] = [[squareWrist((HAND_RELAXED[0] as HandPiece)[0]), [], []]];
/** The same table under its Python name, which is how the recorded calls refer to it. */
export const _HAND_OPEN = HAND_OPEN;

/** The traced hand's half-width at its wrist line, in hand lengths. */
export function tracedWristHalf(pieces: readonly HandPiece[]): number {
  const top = chainPoints((pieces[0] as HandPiece)[0])
    .filter(([, y]) => y < 0.03)
    .map(([x]) => x);
  return (maxOf(top) - minOf(top)) / 2;
}

/** The relaxed hand's style, with the old "grip" read as the mitten it meant. */
export function handPose(p: CharacterParams): string {
  return p.hand_style === "grip" ? "mitten" : p.hand_style;
}

/**
 * Whether the hand on `side` is a fist round a held staff: the character's own right
 * hand (the viewer's left), with a staff, in a fist grip.
 */
export function fistGrips(p: CharacterParams, side: number): boolean {
  return side === -1 && p.outfit.staff_color !== null && (p.grip_style === "fist" || p.hand_style === "grip");
}

/**
 * Whether the hand on `side` is drawn by `_traced_hand`, under its arm, rather than as
 * one of the mitten's family over it.
 */
export function handTraced(p: CharacterParams, side: number): boolean {
  return fistGrips(p, side) || handPose(p) === "traced";
}

/** The centroid of `pts` and the unit direction of their longest spread. */
export function principal(pts: readonly Point[]): [Point, Point] {
  const n = pts.length;
  const mx = pyDiv(pySum(pts.map(([x]) => x)), n);
  const my = pyDiv(pySum(pts.map(([, y]) => y)), n);
  const sxx = pySum(pts.map(([x]) => (x - mx) * (x - mx)));
  const syy = pySum(pts.map(([, y]) => (y - my) * (y - my)));
  const sxy = pySum(pts.map(([x, y]) => (x - mx) * (y - my)));
  const a = 0.5 * Math.atan2(2 * sxy, sxx - syy);
  return [
    [mx, my],
    [pyCos(a), pySin(a)],
  ];
}

/**
 * `(centre, half_width, out)` of the sleeve's opening a hand comes out of, in
 * the arm's own unswung frame (the frame the hand is drawn in); `out` the unit
 * normal pointing out of the sleeve. On a traced sleeve it is the cuff band's
 * side further along the forearm, a line fitted through it; on a drawn sleeve
 * or a bare arm, the wrist line.
 */
export function cuffOpening(sk: Skeleton, p: CharacterParams, side: number): [Point, number, Point] {
  const [centreTop, , centreWrist, wristY] = armLine(sk);
  const cut = wornSleeve(sk, p);
  if (cut === null) {
    const w = sk.arm_half_w * (1.0 - 0.34 * limbBuild(sk));
    return [[sk.head_cx + side * centreWrist, wristY], w, [0.0, 1.0]];
  }
  const centreElbow = centreTop + (centreWrist - centreTop) * 0.35;
  const [fx, fy] = [side * (centreWrist - centreElbow), wristY - sk.waist_y];
  const place = sleevePlacement(sk, cut, side);
  const pts: Point[] = chainPoints(cut.cuff, 16)
    .map((q) => place(q))
    .map(([x, y]): Point => [sk.head_cx + x * sk.head_r, sk.head_cy + y * sk.head_r]);
  const [[cx, cy], [ax, ay]] = principal(pts);
  let [mx, my] = [-ay, ax];
  if (mx * fx + my * fy < 0) [mx, my] = [-mx, -my];
  const far = pts.filter(([x, y]) => (x - cx) * mx + (y - cy) * my > 0);
  const [[fcx, fcy], [ex, ey]] = principal(far);
  const t = far.map(([x, y]) => (x - fcx) * ex + (y - fcy) * ey);
  const mid: Point = [fcx + (ex * (maxOf(t) + minOf(t))) / 2, fcy + (ey * (maxOf(t) + minOf(t))) / 2];
  let [ox, oy] = [-ey, ex];
  if (ox * fx + oy * fy < 0) [ox, oy] = [-ox, -oy];
  return [mid, (maxOf(t) - minOf(t)) / 2, [ox, oy]];
}

/**
 * Maps a traced hand's point onto the figure, in its arm's unswung frame: the
 * hand turned so its traced wrist lies along the cuff's opening, facing out of
 * it, its wrist's centre on the opening's, tucked under the cuff (the owner,
 * 2026-09-27, `harness/trace_hands/cuff_fit.py`); the open hand's wrist
 * widened to the opening. Mirrored per side: the open hand was traced on the
 * viewer's right, the grip on the left.
 */
export function tracedPlacement(sk: Skeleton, p: CharacterParams, side: number): (q: Point) => Point {
  const grip = fistGrips(p, side);
  const mirror = grip ? side === 1 : side === -1;
  let [ix, iy] = grip ? HAND_FIST_INTO : HAND_RELAXED_INTO;
  if (mirror) ix = -ix;
  const [[mx, my], half, [ox, oy]] = cuffOpening(sk, p, side);
  let theta = Math.atan2(oy, ox) - Math.atan2(iy, ix);
  if (grip) {
    // Turn the fist back against the arm's swing so its rolls stay level.
    const swing = side === -1 ? p.right_arm_out : p.left_arm_out;
    theta += radians(HAND_FIST_UPRIGHT * swing);
  }
  const [cos, sin] = [pyCos(theta), pySin(theta)];
  const k = (grip ? HAND_FIST_LENGTH : HAND_OPEN_LENGTH) * sk.head_r;
  const stretch = grip ? 1.0 : HAND_OPEN_STRETCH;
  const widen = grip ? 1.0 : pyDiv(HAND_WRIST_FILL * half, tracedWristHalf(HAND_OPEN) * stretch * k);
  const [bx, by] = [mx - ox * HAND_CUFF_TUCK * sk.head_r, my - oy * HAND_CUFF_TUCK * sk.head_r];

  return (q: Point): Point => {
    let [x, y] = q;
    if (!grip && y < HAND_WRIST_STRETCH) {
      const t = 1.0 - pyDiv(pyMax(0.0, y), HAND_WRIST_STRETCH);
      x *= 1.0 + (widen - 1.0) * t * t;
    }
    x = (mirror ? -x : x) * stretch * k;
    y *= k;
    return [bx + x * cos - y * sin, by + x * sin + y * cos];
  };
}

/**
 * A drawn hand on `side`: the fist when this is the hand holding a staff in a
 * fist grip, the open hand otherwise, fitted to its cuff (`_traced_placement`).
 */
export function tracedHand(sk: Skeleton, p: CharacterParams, side: number): string {
  const grip = fistGrips(p, side);
  const place = tracedPlacement(sk, p, side);
  const sw = strokeW(sk);

  const pt = (q: Point): string => {
    const [x, y] = place(q);
    return `${fmt2(x)} ${fmt2(y)}`;
  };

  const path = (ch: Chain, closed: boolean): string => {
    const [start, segs] = ch;
    const d = `M ${pt(start)} ` + segs.map(([c1, e]) => `Q ${pt(c1)} ${pt(e)}`).join(" ");
    return closed ? d + " Z" : d;
  };

  const parts: string[] = [];
  for (const [outline, holes, lines] of grip ? HAND_FIST : HAND_OPEN) {
    const d = [outline, ...holes].map((c) => path(c, true)).join(" ");
    parts.push(
      `<path d="${d}" fill="${p.skin_tone}" fill-rule="evenodd" stroke="${OUTLINE}" ` +
        `stroke-width="${fmt2(outlineW(sw, 0.85))}" stroke-linejoin="round" />`,
    );
    for (const ln of lines) {
      parts.push(
        `<path d="${path(ln, false)}" fill="none" stroke="${OUTLINE}" ` +
          `stroke-width="${fmt2(interiorW(sw, 0.8))}" stroke-linecap="round" />`,
      );
    }
  }
  return parts.join("");
}

/**
 * Maps a mitten's `(offset, down)` onto the figure, in its arm's unswung
 * frame: `offset` across the wrist (the right hand's, mirrored per side),
 * `down` along the hand from its wrist line. Hanging straight down from the
 * wrist on a drawn sleeve or a bare arm; on a traced sleeve, turned so its
 * wrist line lies on the cuff's opening, centred on it and facing out of it
 * (`_cuff_opening`), the way `_traced_placement` fits a traced hand. The
 * mitten is drawn over its cuff, so its top edge sits on the cuff's edge
 * rather than tucked under it (the owner, 2026-09-27).
 */
export function mittenPlacement(sk: Skeleton, p: CharacterParams, side: number, cx: number, wrist_y: number): (offset: number, down: number) => Point {
  if (wornSleeve(sk, p) === null) return (offset, down) => [cx + side * offset, wrist_y + down];
  const [[mx, my], , [ox, oy]] = cuffOpening(sk, p, side);

  return (offset: number, down: number): Point => {
    const x = side * offset;
    return [mx + x * oy + down * ox, my - x * ox + down * oy];
  };
}

/**
 * A hand hanging at the side, thumb on the inner edge: the mitten unless
 * `hand_style` says otherwise.
 *
 * The canon's chibi hand is a mitten with one visible thumb, which is what
 * separates a hand from the featureless stub this used to be. Still no
 * fingers by default: the canon suggests them with a crease at most, and at
 * this size separate digits read as noise rather than as a hand. The other
 * styles (`HAND_STYLES`) are the owner's options, kept side by side.
 */
export function hand(sk: Skeleton, p: CharacterParams, cx: number, wrist_y: number, w_wrist: number, side: number): string {
  if (handTraced(p, side)) return tracedHand(sk, p, side);
  const hw = w_wrist * 1.02;
  const length = handLength(sk);
  const tip = hw * (1.0 - 0.32 * sk.build);
  const place = mittenPlacement(sk, p, side, cx, wrist_y);

  /** Offsets are for the right hand, thumb toward -x; the left mirrors. `down` is how far along the hand from its wrist line. */
  const pt = (offset: number, down: number): string => {
    const [x, y] = place(offset, down);
    return `${fmt1(x)} ${fmt1(y)}`;
  };

  const style = handPose(p);
  const sw = strokeW(sk);
  if (typeof style === "string" && Object.hasOwn(HAND_BUILDERS, style)) {
    return (HAND_BUILDERS[style] as HandBuilder)(p, sw, hw, length, tip, pt);
  }
  const d = mittenPath(hw, length, tip, pt);
  const parts = [`<path d="${d}" fill="${p.skin_tone}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw, 0.85))}" />`];
  return parts.join("");
}

/** The mitten's outline, in the hand's own frame (`pt(offset, down)`). */
export function mittenPath(hw: number, length: number, tip: number, pt: (offset: number, down: number) => string): string {
  return (
    `M ${pt(hw, 0.0)} ` +
    `Q ${pt(hw * 1.14, length * 0.55)} ${pt(tip * 0.74, length)} ` +
    `Q ${pt(0.0, length * 1.16)} ${pt(-tip * 0.7, length * 0.97)} ` +
    `Q ${pt(-hw * 1.02, length * 0.8)} ${pt(-hw * 0.86, length * 0.6)} ` +
    `Q ${pt(-hw * 1.32, length * 0.5)} ${pt(-hw * 1.12, length * 0.28)} ` +
    `Q ${pt(-hw * 0.98, length * 0.16)} ${pt(-hw, 0.0)} ` +
    `Z`
  );
}

export function handShape(p: CharacterParams, sw: number, d: string): string {
  return (
    `<path d="${d}" fill="${p.skin_tone}" stroke="${OUTLINE}" ` +
    `stroke-width="${fmt2(outlineW(sw, 0.85))}" stroke-linejoin="round" />`
  );
}

export function handStroke(sw: number, d: string): string {
  return (
    `<path d="${d}" fill="none" stroke="${OUTLINE}" ` +
    `stroke-width="${fmt2(interiorW(sw, 0.8))}" stroke-linecap="round" />`
  );
}

type Pt = (offset: number, down: number) => string;
type HandBuilder = (p: CharacterParams, sw: number, hw: number, length: number, tip: number, pt: Pt) => string;

/**
 * The mitten with its tip cut into three fingers, the middle the longest. Each notch
 * is a V about two outline widths across, so it reads as a notch and not a hairline.
 * The thumb side is the mitten's own.
 */
export function handNotched(p: CharacterParams, sw: number, hw: number, length: number, tip: number, pt: Pt): string {
  const d =
    `M ${pt(hw, 0.0)} ` +
    `Q ${pt(hw * 1.14, length * 0.55)} ${pt(tip * 0.74, length * 0.9)} ` +
    `Q ${pt(tip * 0.62, length * 1.1)} ${pt(tip * 0.34, length * 1.01)} ` +
    `L ${pt(tip * 0.27, length * 0.84)} ` +
    `L ${pt(tip * 0.2, length * 1.03)} ` +
    `Q ${pt(tip * 0.02, length * 1.2)} ${pt(-tip * 0.14, length * 1.04)} ` +
    `L ${pt(-tip * 0.2, length * 0.86)} ` +
    `L ${pt(-tip * 0.27, length * 1.01)} ` +
    `Q ${pt(-tip * 0.48, length * 1.12)} ${pt(-tip * 0.7, length * 0.96)} ` +
    `Q ${pt(-hw * 1.02, length * 0.8)} ${pt(-hw * 0.86, length * 0.6)} ` +
    `Q ${pt(-hw * 1.32, length * 0.5)} ${pt(-hw * 1.12, length * 0.28)} ` +
    `Q ${pt(-hw * 0.98, length * 0.16)} ${pt(-hw, 0.0)} ` +
    `Z`;
  return handShape(p, sw, d);
}

/** The mitten's silhouette exactly, with two finger strokes rising from the tip. */
export function handStroked(p: CharacterParams, sw: number, hw: number, length: number, tip: number, pt: Pt): string {
  const parts = [handShape(p, sw, mittenPath(hw, length, tip, pt))];
  for (const [x, dx] of [
    [tip * 0.27, 0.03],
    [-tip * 0.2, -0.03],
  ] as const) {
    parts.push(
      handStroke(
        sw,
        `M ${pt(x, length * 1.02)} Q ${pt(x * 1.04 + dx * hw, length * 0.85)} ${pt(x, length * 0.66)}`,
      ),
    );
  }
  return parts.join("");
}

/**
 * A half-closed hand: the mitten's silhouette (so it joins and fits as the mitten
 * does), the thumb's crease running down the front and two parallel curled-finger
 * arcs across the lower body. A first version with a closed thumb shape of its own
 * read as a ring at the cuff and crowded the fingers, so the thumb stays the
 * mitten's bump.
 */
export function handCurled(p: CharacterParams, sw: number, hw: number, length: number, tip: number, pt: Pt): string {
  const parts = [handShape(p, sw, mittenPath(hw, length, tip, pt))];
  parts.push(
    handStroke(
      sw,
      `M ${pt(-hw * 0.62, length * 0.36)} Q ${pt(-hw * 0.5, length * 0.46)} ${pt(-hw * 0.3, length * 0.5)}`,
    ),
  );
  for (const x of [tip * 0.4, -tip * 0.04]) {
    parts.push(
      handStroke(
        sw,
        `M ${pt(x + hw * 0.08, length * 0.62)} Q ${pt(x - hw * 0.08, length * 0.8)} ${pt(x, length * 1.0)}`,
      ),
    );
  }
  return parts.join("");
}

export const HAND_BUILDERS: Readonly<Record<string, HandBuilder>> = {
  notched: handNotched,
  stroked: handStroked,
  curled: handCurled,
};

