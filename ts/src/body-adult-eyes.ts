// The adult woman's eyes, drawn from measurements of ref/franzi/ rather than by the shared eye code, whose round chibi eye
// could not take the reference's shape: a thick black upper lid that tapers to a wing at the outer corner, a soft thin line
// round the rest of the aperture, white with a rounder iris that the lid covers the top of, a pupil and two highlights.
//
// The shapes are in pixels of ref 04 relative to the iris centre, read off an 8x grid of each eye (harness/franzi_hair, the
// grid in out/franzi/eyeR-grid.png), and drawn for the viewer's right eye, then mirrored. 175.7 reference px are one head
// radius (the calibration of harness/franzi_hair/trace.py). Flat colour, hard-edged, as the rest of the figure.

import { OUTLINE, outlineW, soft, strokeW } from "./character.ts";
import { LID_L } from "./body-adult-lid-data.ts";
import { shade, tint } from "./colorutil.ts";
import type { CharacterParams } from "./params.ts";
import { fmt1, fmt2, truthy } from "./pynum.ts";
import type { Skeleton } from "./skeleton.ts";

type Pt = readonly [number, number];

const PX_PER_R = 175.7;
/** The iris centre, in head radii from the head centre: how far out each eye sits and how far down. The two differ (the head turns a little in the reference), read per eye from its 8x grid. */


// The eye is two circular arcs and a flat base (the owner's marks on the reference's left eye, fitted: harness/franzi/eye_arcs_owner.py).
// Eye frame: pixels of ref 04, x positive OUTWARD (away from the nose), y down, origin at the iris centre; drawn for either side by
// `place`. The lid's upper edge is the circle GREEN, its lower edge the circle CYAN, the two nearly concentric, and GREEN goes on
// down the open (inner) side as the aperture's edge. The lower outline runs from the wing's tip in a short straight line to a flat
// base.
const GREEN = { c: [9.4, 0.3] as Pt, r: 31.6 };
const CYAN = { c: [4.1, 3.2] as Pt, r: 27.6 };
/** The wing's tip, where the lid's upper edge meets the lower outline. */
const WING: Pt = [43.5, -6.25];
/** Where the lid's lower edge ends on the outer side, on its way down to the base. */
const CYAN_OUT: Pt = [28.25, 9.4];
/**
 * Where the lid band ends on the inner side: the point where the two circles cross, so the band tapers to a point there rather
 * than ending in a blunt stub (the arcs end at different radii if they stop at a point that is on neither circle).
 */
const JOIN: Pt = (() => {
  const dx = CYAN.c[0] - GREEN.c[0];
  const dy = CYAN.c[1] - GREEN.c[1];
  const d = Math.hypot(dx, dy);
  const a = (GREEN.r * GREEN.r - CYAN.r * CYAN.r + d * d) / (2 * d);
  const h = Math.sqrt(GREEN.r * GREEN.r - a * a);
  const mx = GREEN.c[0] + (a * dx) / d;
  const my = GREEN.c[1] + (a * dy) / d;
  const p1: Pt = [mx + (h * dy) / d, my - (h * dx) / d];
  const p2: Pt = [mx - (h * dy) / d, my + (h * dx) / d];
  return p1[0] < p2[0] ? p1 : p2; // the inner one (x outward-positive, so the smaller x)
})();
/** The base's points, outer to inner, and where green meets it on the inner side. */
// Two straight lines (the owner's pink marks on the left eye): outer end, a low point, and green's lower end on the inner side.
const BASE: Pt[] = [[21.25, 16.25], [11.25, 20.75]];
const GREEN_LOW: Pt = [-16.5, 18.25];
const IRIS: { c: Pt; rx: number; ry: number } = { c: [0, 0], rx: 17, ry: 20.5 };
const PUPIL: { c: Pt; rx: number; ry: number } = { c: [-1.5, 0], rx: 6.5, ry: 10 };
const HILITE: { c: Pt; r: number } = { c: [9, -14], r: 5.5 };
const GLINT: { c: Pt; r: number } = { c: [-6, 7], r: 2.2 };

/** Points along the circle `circ` from `a` to `b`, taking the way round that passes `via`. */
function arc(circ: { c: Pt; r: number }, a: Pt, b: Pt, via: Pt, n = 18): Pt[] {
  const ang = (q: Pt): number => Math.atan2(q[1] - circ.c[1], q[0] - circ.c[0]);
  const a0 = ang(a);
  let a1 = ang(b);
  const av = ang(via);
  const norm = (v: number): number => ((v % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);
  // go counter-clockwise from a to b if via lies on that way, else clockwise
  const ccw = norm(av - a0) < norm(a1 - a0);
  if (ccw) a1 = a0 + norm(a1 - a0);
  else a1 = a0 - norm(a0 - a1);
  const out: Pt[] = [];
  for (let i = 0; i <= n; i++) {
    const t = a0 + ((a1 - a0) * i) / n;
    out.push([circ.c[0] + circ.r * Math.cos(t), circ.c[1] + circ.r * Math.sin(t)]);
  }
  return out;
}

const TOP_VIA: Pt = [0, -40];
/** A point on the upper branch of `circ` at eye-frame x. */
const onTop = (circ: { c: Pt; r: number }, x: number): Pt => [x, circ.c[1] - Math.sqrt(circ.r * circ.r - (x - circ.c[0]) * (x - circ.c[0]))];
/**
 * The black lid ends well before the circles cross (owner's circle on the reference: past this the area is skin): on green at
 * x = -15 and on cyan at x = -9, joined by a short end. The thin line carries on along cyan to the crossing (`lidTail`).
 */
const LID_END_OUT: Pt = onTop(GREEN, -15);
const LID_END_IN: Pt = onTop(CYAN, -9);
/** The lid band: green from the wing's tip over the top to the join, cyan back to where it ends outside, then the wing's lower line. */
/**
 * The lid's lower edge is the cyan circle lowered by 3.4 px (the reference's lid is 10 to 12 px thick at the middle, the band between
 * the owner's two circles 6.9); the aperture keeps the cyan circle itself, and the lid is drawn over the white and the iris top, as
 * the reference's lid covers it.
 */
const CYAN_LID = { c: [CYAN.c[0], CYAN.c[1] + 2.0] as Pt, r: CYAN.r };
/**
 * The lid tapers to a point at the inner end, as the reference's does (measured on its viewer's-left eye, the black run of each column, lightness under 45:
 * 7 to 8 px thick from the middle out to x = 20, 6 px at x = -12, 3 px at -16, 2 px at -20, and gone by -22). It used to stop at x = -15 on its upper arc with a
 * blunt chord to the lower arc at x = -9, a heavy crescent that ended abruptly where the reference's thins out and runs into the lashes. Its upper edge is still the
 * circle GREEN, now to the inner tip at x = -20.5; its lower edge is the upper edge plus the thickness below (x outward-positive, as in the eye frame), joined to the
 * lowered CYAN circle at x = 14.
 */
// The lid is the left eye's, measured in the reference (harness/franzi/lid_measure.py: LID_L, [x, top edge, bottom edge] in the eye frame; the first lid, a pair of circles,
// sat about 3 px high on it), and mirrored for the right eye like everything else of the eye: the lid, the crease, the lashes and the aperture are ONE set drawn for the left
// eye. A version with the right eye's own lid, crease and lashes (measured from its own grid, c2e1915) put pieces of different eyes together: they no longer lined up with
// the aperture, the iris and the highlights that are mirrored from the left, and the right eye looked broken (the owner). The measured edges are used from the tip out to
// x = XB0; from there to XB1 they blend into the circles above, which keep the outer wing (the owner's marks).
const XB0 = 14;
const XB1 = 22;
const smoothstep = (t: number): number => {
  const u = Math.min(1, Math.max(0, t));
  return u * u * (3 - 2 * u);
};
const tableAt = (tab: readonly (readonly [number, number, number])[], x: number, col: 1 | 2): number => {
  const first = tab[0] as readonly [number, number, number];
  const last = tab[tab.length - 1] as readonly [number, number, number];
  if (x <= first[0]) return first[col];
  if (x >= last[0]) return last[col];
  for (let i = 0; i < tab.length - 1; i++) {
    const r0 = tab[i] as readonly [number, number, number];
    const r1 = tab[i + 1] as readonly [number, number, number];
    if (x <= r1[0]) return r0[col] + ((r1[col] - r0[col]) * (x - r0[0])) / (r1[0] - r0[0]);
  }
  return last[col];
};
/** Where the circle arcs are defined: GREEN reaches x = -22.2 and CYAN x = -23.5; the table alone is used past that (its weight is 1 there). */
const circleTop = (circ: { c: Pt; r: number }, x: number): number | null => (x > circ.c[0] - circ.r + 0.3 ? onTop(circ, x)[1] : null);
const lidBand = (): Pt[] => {
  const tab = LID_L;
  const xTip = (tab[0] as readonly [number, number, number])[0];
  const upper: Pt[] = [];
  const lower: Pt[] = [];
  for (let x = XB1; x >= xTip - 1e-9; x -= 1) {
    const wgt = 1 - smoothstep((x - XB0) / (XB1 - XB0));
    const gt = circleTop(GREEN, x);
    const ct = circleTop(CYAN_LID, x);
    upper.push([x, gt === null || wgt >= 1 ? tableAt(tab, x, 1) : gt + (tableAt(tab, x, 1) - gt) * wgt]);
    lower.push([x, ct === null || wgt >= 1 ? tableAt(tab, x, 2) : ct + (tableAt(tab, x, 2) - ct) * wgt]);
  }
  const tipU = upper[upper.length - 1] as Pt;
  const tipL = lower[lower.length - 1] as Pt;
  const tip: Pt = [xTip - 1.5, (tipU[1] + tipL[1]) / 2 + 0.5];
  return [
    ...arc(GREEN, WING, onTop(GREEN, XB1), onTop(GREEN, 32)),
    ...upper.slice(1),
    tip,
    ...[...lower].reverse(),
    ...arc(CYAN_LID, onTop(CYAN_LID, XB1), CYAN_OUT, onTop(CYAN_LID, 26)).slice(1),
  ];
};

/**
 * The lash flicks, from the viewer's-left eye's 16x grid (out/franzi/lash-ref-L.png; eye frame points, widths in ref px), mirrored for the right eye with the rest of the
 * set: the eye's inner tail splits into three flicks fanning down and out from where the lid thins out (the thick one is dark from (623, 309) to (629, 315) on ref 04).
 * The reference's right eye has one long tail and two small flicks on top instead; they are not used, so that the right eye is the mirror of a set that fits together.
 */
const LASHES: readonly { pts: readonly Pt[]; w: number }[] = [
  { pts: [[-15.5, -18.5], [-19, -16], [-21.8, -13], [-23.4, -9.5]], w: 3.0 },
  { pts: [[-17, -20.5], [-20, -18.2], [-22.8, -15.7], [-25, -13.5]], w: 1.8 },
  { pts: [[-15, -21.5], [-17.5, -20.5], [-20.5, -19.2], [-23, -18]], w: 1.3 },
];
/** The thin line along the aperture's top where the black lid has ended, to the crossing of the circles. */
const lidTail = (): Pt[] => arc(CYAN, onTop(CYAN, 2), JOIN, onTop(CYAN, -12), 16);
/** The aperture: the lower outline from the wing's tip round the base, up green's inner side, and back along cyan's lower edge. */
const apertureOutline = (): Pt[] => [
  // Starts at the lid's lower corner, not the wing tip: the chord from the tip to the corner is the lid's own edge, and a white
  // fill bounded by it showed as a hairline beside the black on both eyes.
  CYAN_OUT,
  ...BASE,
  ...arc(GREEN, GREEN_LOW, JOIN, [GREEN.c[0] - GREEN.r, GREEN.c[1]], 10),
  ...arc(CYAN, JOIN, CYAN_OUT, TOP_VIA).slice(1),
];
/** The soft lower outline alone: wing tip, down the short line and along the base, and up green's inner side. */
const lowerLine = (): Pt[] => [[WING[0] + (CYAN_OUT[0] - WING[0]) * 0.7, WING[1] + (CYAN_OUT[1] - WING[1]) * 0.7] as Pt, CYAN_OUT, ...BASE, ...arc(GREEN, GREEN_LOW, JOIN, [GREEN.c[0] - GREEN.r, GREEN.c[1]], 10)];

/** A filled stroke along `pts` that is `w0` wide at the start and tapers to a point at the end (flat black, hard-edged). */
function taperedStroke(pts: readonly Pt[], w0: number, color: string): string {
  const n = pts.length;
  const left: Pt[] = [];
  const right: Pt[] = [];
  for (let i = 0; i < n; i++) {
    const a = pts[Math.max(0, i - 1)] as Pt;
    const b = pts[Math.min(n - 1, i + 1)] as Pt;
    const len = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
    const nx = -(b[1] - a[1]) / len;
    const ny = (b[0] - a[0]) / len;
    const half = (w0 / 2) * (1 - i / (n - 1)) ** 0.8;
    const q = pts[i] as Pt;
    left.push([q[0] + nx * half, q[1] + ny * half]);
    right.push([q[0] - nx * half, q[1] - ny * half]);
  }
  const poly = [...left, ...right.reverse()];
  return `<path d="M ${fmt1((poly[0] as Pt)[0])} ${fmt1((poly[0] as Pt)[1])} ${poly.slice(1).map(([x, y]) => `L ${fmt1(x)} ${fmt1(y)} `).join("")}Z" fill="${color}" />`;
}

/**
 * A filled stroke along `pts` whose width falls with the distance along it: `w` at the start, held until `hold` of the length,
 * then easing to `wEnd` at the end. Flat black, hard-edged; round at the start so it joins what it starts from.
 */
function varStroke(pts: readonly Pt[], w: number, hold: number, wEnd: number, color: string): string {
  const n = pts.length;
  const cum: number[] = [0];
  for (let i = 1; i < n; i++) cum.push((cum[i - 1] as number) + Math.hypot((pts[i] as Pt)[0] - (pts[i - 1] as Pt)[0], (pts[i] as Pt)[1] - (pts[i - 1] as Pt)[1]));
  const total = cum[n - 1] as number;
  const left: Pt[] = [];
  const right: Pt[] = [];
  for (let i = 0; i < n; i++) {
    const a = pts[Math.max(0, i - 1)] as Pt;
    const b = pts[Math.min(n - 1, i + 1)] as Pt;
    const len = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
    const nx = -(b[1] - a[1]) / len;
    const ny = (b[0] - a[0]) / len;
    const t = (cum[i] as number) / total;
    const u = t <= hold ? 0 : (t - hold) / (1 - hold);
    const half = ((w + (wEnd - w) * u * u * (3 - 2 * u)) / 2);
    const q = pts[i] as Pt;
    left.push([q[0] + nx * half, q[1] + ny * half]);
    right.push([q[0] - nx * half, q[1] - ny * half]);
  }
  const poly = [...left, ...right.reverse()];
  const s0 = pts[0] as Pt;
  return `<path d="M ${fmt1((poly[0] as Pt)[0])} ${fmt1((poly[0] as Pt)[1])} ${poly.slice(1).map(([x, y]) => `L ${fmt1(x)} ${fmt1(y)} `).join("")}Z" fill="${color}" /><circle cx="${fmt1(s0[0])}" cy="${fmt1(s0[1])}" r="${fmt2(w / 2)}" fill="${color}" />`;
}

/** `n` points per span along the Catmull-Rom curve through `pts`. */
function sampleSmooth(pts: readonly Pt[], n = 6): Pt[] {
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

/** A filled leaf-shaped stroke along `pts`: a point at each end, widest in the middle. */
function leafStroke(pts: readonly Pt[], w: number, color: string): string {
  const n = pts.length;
  const left: Pt[] = [];
  const right: Pt[] = [];
  for (let i = 0; i < n; i++) {
    const a = pts[Math.max(0, i - 1)] as Pt;
    const b = pts[Math.min(n - 1, i + 1)] as Pt;
    const len = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
    const nx = -(b[1] - a[1]) / len;
    const ny = (b[0] - a[0]) / len;
    const t = i / (n - 1);
    const half = (w / 2) * Math.sin(Math.PI * t) ** 0.7;
    const q = pts[i] as Pt;
    left.push([q[0] + nx * half, q[1] + ny * half]);
    right.push([q[0] - nx * half, q[1] - ny * half]);
  }
  const poly = [...left, ...right.reverse()];
  return `<path d="M ${fmt1((poly[0] as Pt)[0])} ${fmt1((poly[0] as Pt)[1])} ${poly.slice(1).map(([x, y]) => `L ${fmt1(x)} ${fmt1(y)} `).join("")}Z" fill="${color}" />`;
}

// Details read off the reference's left eye (the base eye; the right is its mirror), eye frame as above: the crease line above the
// lid, and two lash flicks that fan down from the lid's inner end. From the 16x grids out/franzi/lashes-L-grid{,2}.png.
const CREASE: Pt[] = [[18, -31.8], [12, -33.3], [6, -34.1], [-4, -33.6], [-11.5, -31.7], [-16.5, -29.2], [-20.3, -25.7], [-21.5, -23]];

/** Catmull-Rom through `pts` as cubic segments, the pen already at the first point. */
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

function ellipse(c: Pt, rx: number, ry: number, fill: string, extra = ""): string {
  return `<ellipse cx="${fmt1(c[0])}" cy="${fmt1(c[1])}" rx="${fmt1(rx)}" ry="${fmt1(ry)}" fill="${fill}"${extra} />`;
}

/** The iris centre of each eye in reference pixels (ref 04), the origin of its frame: read off the 8x grids. */
const IRIS_AT: Record<number, Pt> = { [-1]: [606, 325], 1: [718.5, 321.5] };

/** Reference pixels to canvas, for the head as it hangs: the calibration of harness/franzi_hair/trace.py (origin (660, 270.5)). */
function toCanvas(h: Skeleton, q: Pt): Pt {
  const k = h.head_r / PX_PER_R;
  return [h.head_cx + (q[0] - 660) * k, h.head_cy + (q[1] - 270.5) * k];
}

/** The eye frame's outward-positive points to canvas for `side`. */
function placer(h: Skeleton, side: number): (q: Pt) => Pt {
  const [ix, iy] = IRIS_AT[side] as Pt;
  return ([x, y]) => toCanvas(h, [ix + side * x, iy + y]);
}

/**
 * The shut eye (`FaceStyle.eyes_closed`, a blink): the upper lid has come down over the aperture, so what is drawn is the lid's edge, one black line along where the
 * aperture's lower outline ran, from the inner corner to the wing's tip. It follows the open eye's own points (the base, `CYAN_OUT`, `WING`), so the wing stays where it was and
 * the eye does not jump when it opens. The crease, the white, the iris and the highlights are gone with it; the thick lash flick stays, moved down so that it starts from
 * the line's inner end as it starts from the open lid's (the two thin ones and the lid's tail made a scribble at that scale).
 */
const CLOSED_LINE: Pt[] = [[-21, 9], [-15, 16], [-6, 20], [4, 21.5], BASE[1] as Pt, BASE[0] as Pt, CYAN_OUT, [36, 1.5], WING];
/** How far the lash flicks move down when the eye is shut: from the open lid's inner end to the closed line's. */
const CLOSED_LASH_DROP = 34;

function closedEye(h: Skeleton, side: number): string {
  const k = h.head_r / PX_PER_R;
  const at = placer(h, side);
  const flick = LASHES[0] as { pts: readonly Pt[]; w: number };
  return [
    leafStroke(sampleSmooth(CLOSED_LINE).map(at), 8.5 * k, OUTLINE),
    taperedStroke(sampleSmooth(flick.pts.map(([x, y]): Pt => [x, y + CLOSED_LASH_DROP])).map(at), flick.w * k, OUTLINE),
  ].join("");
}

/**
 * `FaceStyle.eye_openness` lowers the upper lid over the aperture (1 is the traced eye, 0 would shut it): the lid band, the thin line along the top of the white, the aperture's top
 * edge (so no white shows above the lid) and the lash flicks move down together, the crease half as far. The wing tip stays where it is and the inner end moves about half as far as the
 * middle, as a lid closes. `LID_TRAVEL` is how far the lid's lower edge drops across the middle of the eye at 0, about to the closed line; the iris keeps its size and is cropped by the
 * lowered aperture. At 1 nothing moves and the points are returned as they are.
 */
const LID_TRAVEL = 40;
const lidShare = (x: number): number => (x >= 22 ? 1 - smoothstep((x - 22) / (WING[0] - 22)) : x <= -8 ? 0.5 + 0.5 * smoothstep((x + 23) / 15) : 1);
const lidRow = (y: number): number => 1 - smoothstep((y + 8) / 14);
const openness = (f: { eye_openness: number }): number => Math.max(0, Math.min(1.3, f.eye_openness));
/** Where the eyes look (`FaceStyle.gaze`, +1 to the viewer's right), in eye-frame pixels at the full look: both eyes move together, and the aperture crops the iris at the corners. */
const GAZE_TRAVEL = 7;

/** One eye. `side` is +1 for the viewer's right. `h` is the skeleton with the head where it hangs. */
function oneEye(h: Skeleton, p: CharacterParams, side: number, id: string): string {
  if (truthy(p.face.eyes_closed)) return closedEye(h, side);
  const k = h.head_r / PX_PER_R;
  const at = placer(h, side);
  const poly = (pts: readonly Pt[], close: boolean): string => {
    const a = pts.map(at);
    return `M ${fmt1((a[0] as Pt)[0])} ${fmt1((a[0] as Pt)[1])} ` + a.slice(1).map(([x, y]) => `L ${fmt1(x)} ${fmt1(y)} `).join("") + (close ? "Z" : "");
  };
  const open = openness(p.face);
  const lowered = (pts: readonly Pt[], byRow: boolean, share = 1): readonly Pt[] =>
    open === 1 ? pts : pts.map(([x, y]): Pt => [x, y + (1 - open) * LID_TRAVEL * share * lidShare(x) * (byRow ? lidRow(y) : 1)]);
  const lashDrop = open === 1 ? 0 : (1 - open) * LID_TRAVEL * lidShare(-16);
  const look = Math.max(-1, Math.min(1, p.face.gaze));
  const gaze = look === 0 ? "" : `<g transform="translate(${fmt2(look * GAZE_TRAVEL * k)} 0)">`;
  const apertureD = poly(lowered(apertureOutline(), true), true);
  const iris = p.eye_color;
  const ink = outlineW(strokeW(h));
  const clip = `<clipPath id="${id}"><path d="${apertureD}" /></clipPath>`;
  const ic = at(IRIS.c);
  const irisTop = shade(iris, 0.55);
  // The soft finish: the iris darker at the top, where the lid shades it, and lighter at the bottom, with a glow of light coming up into it (the chibi's eye does the same).
  const isSoft = soft(p);
  const gradient = isSoft
    ? `<linearGradient id="${id}-grad" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${shade(iris, 0.62)}" /><stop offset="0.55" stop-color="${iris}" /><stop offset="1" stop-color="${tint(iris, 0.38)}" /></linearGradient>` +
      `<radialGradient id="${id}-glow"><stop offset="0" stop-color="${tint(iris, 0.5)}" stop-opacity="0.6" /><stop offset="1" stop-color="${tint(iris, 0.5)}" stop-opacity="0" /></radialGradient>` +
      `<clipPath id="${id}-iris"><ellipse cx="${fmt1(ic[0])}" cy="${fmt1(ic[1])}" rx="${fmt1(IRIS.rx * k)}" ry="${fmt1(IRIS.ry * k)}" /></clipPath>`
    : "";
  const glow = isSoft
    ? `<ellipse cx="${fmt1(ic[0])}" cy="${fmt1(ic[1] + IRIS.ry * k * 0.5)}" rx="${fmt1(IRIS.rx * k * 0.62)}" ry="${fmt1(IRIS.ry * k * 0.4)}" fill="url(#${id}-glow)" clip-path="url(#${id}-iris)" />`
    : "";
  const parts = [
    clip,
    gradient,
    `<path d="${apertureD}" fill="#ffffff" />`,
    `<g clip-path="url(#${id})">`,
    gaze,
    ellipse(ic, IRIS.rx * k, IRIS.ry * k, isSoft ? `url(#${id}-grad)` : iris, ""),
    `<path d="M ${fmt1(ic[0] - IRIS.rx * k)} ${fmt1(ic[1] - 0.05 * IRIS.ry * k)} A ${fmt1(IRIS.rx * k)} ${fmt1(IRIS.ry * k)} 0 0 1 ${fmt1(ic[0] + IRIS.rx * k)} ${fmt1(ic[1] - 0.05 * IRIS.ry * k)} Z" fill="${irisTop}" />`,
    ellipse(at(PUPIL.c), PUPIL.rx * k, PUPIL.ry * k, shade(iris, 0.18)),
    glow,
    `<ellipse cx="${fmt1(ic[0])}" cy="${fmt1(ic[1])}" rx="${fmt1(IRIS.rx * k)}" ry="${fmt1(IRIS.ry * k)}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(ink * 0.7)}" />`,
    `<circle cx="${fmt1(at(HILITE.c)[0])}" cy="${fmt1(at(HILITE.c)[1])}" r="${fmt1(HILITE.r * k)}" fill="#ffffff" />`,
    `<circle cx="${fmt1(at(GLINT.c)[0])}" cy="${fmt1(at(GLINT.c)[1])}" r="${fmt1(GLINT.r * k)}" fill="#ffffff" opacity="0.85" />`,
    gaze === "" ? "" : `</g>`,
    `</g>`,
    // the outline round the lower half of the aperture: the same black as the lid, thinner, from where the lid ends
    varStroke(lowerLine().map(at), ink * 0.66, 0.55, ink * 0.16, OUTLINE),
    // the thin line on along the top of the white, growing out of the lid and tapering to a point
    taperedStroke(lowered(lidTail(), true).map(at), ink * 0.9, OUTLINE),
    // the crease line above the lid
    leafStroke(lowered(sampleSmooth(CREASE), false, 0.75).map(at), 3.8 * k, shade(p.skin_tone, 0.42)),
    // the lid: a thick black band between the two arcs, tapering to a wing at the outer corner
    `<path d="${poly(lowered(lidBand(), false), true)}" fill="${OUTLINE}" />`,
    // the lash flicks, growing out of the lid's thin inner end and tapering to points
    ...LASHES.map((l) => taperedStroke(sampleSmooth(lashDrop === 0 ? l.pts : l.pts.map(([x, y]): Pt => [x, y + lashDrop])).map(at), l.w * k, OUTLINE)),
  ];
  return parts.join("");
}

/** Both eyes. */
export function adultEyes(sk: Skeleton, p: CharacterParams): string {
  return oneEye(sk, p, -1, "adult-eye-l") + oneEye(sk, p, 1, "adult-eye-r");
}

/** The aperture and lid outlines in canvas units, for the harness's overlay on the reference (harness/franzi/eye_outline.ts). */
export function adultEyeOutlines(h: Skeleton): { side: number; aperture: Pt[]; lid: Pt[]; crease: Pt[]; lashes: Pt[][] }[] {
  return [-1, 1].map((side) => {
    const at = placer(h, side);
    return { side, aperture: apertureOutline().map(at), lid: lidBand().map(at), crease: sampleSmooth(CREASE).map(at), lashes: LASHES.map((l) => sampleSmooth(l.pts).map(at)) };
  });
}
