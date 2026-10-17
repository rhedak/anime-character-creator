// The adult woman's eyes, drawn from measurements of ref/franzi/ rather than by the shared eye code, whose round chibi eye
// could not take the reference's shape: a thick black upper lid that tapers to a wing at the outer corner, a soft thin line
// round the rest of the aperture, white with a rounder iris that the lid covers the top of, a pupil and two highlights.
//
// The shapes are in pixels of ref 04 relative to the iris centre, read off an 8x grid of each eye (harness/franzi_hair, the
// grid in out/franzi/eyeR-grid.png), and drawn for the viewer's right eye, then mirrored. 175.7 reference px are one head
// radius (the calibration of harness/franzi_hair/trace.py). Flat colour, hard-edged, as the rest of the figure.

import { OUTLINE, outlineW, strokeW } from "./character.ts";
import { shade } from "./colorutil.ts";
import type { CharacterParams } from "./params.ts";
import { fmt1, fmt2 } from "./pynum.ts";
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
const lidBand = (): Pt[] => [...arc(GREEN, WING, LID_END_OUT, TOP_VIA), ...arc(CYAN, LID_END_IN, CYAN_OUT, TOP_VIA)];
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
const LASH_1: Pt[] = [[-16.5, -20.7], [-20.6, -17.6], [-23, -12.3], [-23.7, -8.9]];
const LASH_2: Pt[] = [[-14, -16.4], [-19, -12], [-22.7, -9.2]];

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

/** One eye. `side` is +1 for the viewer's right. `h` is the skeleton with the head where it hangs. */
function oneEye(h: Skeleton, p: CharacterParams, side: number, id: string): string {
  const k = h.head_r / PX_PER_R;
  const at = placer(h, side);
  const poly = (pts: readonly Pt[], close: boolean): string => {
    const a = pts.map(at);
    return `M ${fmt1((a[0] as Pt)[0])} ${fmt1((a[0] as Pt)[1])} ` + a.slice(1).map(([x, y]) => `L ${fmt1(x)} ${fmt1(y)} `).join("") + (close ? "Z" : "");
  };
  const apertureD = poly(apertureOutline(), true);
  const iris = p.eye_color;
  const ink = outlineW(strokeW(h));
  const clip = `<clipPath id="${id}"><path d="${apertureD}" /></clipPath>`;
  const ic = at(IRIS.c);
  const irisTop = shade(iris, 0.55);
  const parts = [
    clip,
    `<path d="${apertureD}" fill="#ffffff" />`,
    `<g clip-path="url(#${id})">`,
    ellipse(ic, IRIS.rx * k, IRIS.ry * k, iris, ""),
    `<path d="M ${fmt1(ic[0] - IRIS.rx * k)} ${fmt1(ic[1] - 0.05 * IRIS.ry * k)} A ${fmt1(IRIS.rx * k)} ${fmt1(IRIS.ry * k)} 0 0 1 ${fmt1(ic[0] + IRIS.rx * k)} ${fmt1(ic[1] - 0.05 * IRIS.ry * k)} Z" fill="${irisTop}" />`,
    ellipse(at(PUPIL.c), PUPIL.rx * k, PUPIL.ry * k, shade(iris, 0.18)),
    `<ellipse cx="${fmt1(ic[0])}" cy="${fmt1(ic[1])}" rx="${fmt1(IRIS.rx * k)}" ry="${fmt1(IRIS.ry * k)}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(ink * 0.7)}" />`,
    `<circle cx="${fmt1(at(HILITE.c)[0])}" cy="${fmt1(at(HILITE.c)[1])}" r="${fmt1(HILITE.r * k)}" fill="#ffffff" />`,
    `<circle cx="${fmt1(at(GLINT.c)[0])}" cy="${fmt1(at(GLINT.c)[1])}" r="${fmt1(GLINT.r * k)}" fill="#ffffff" opacity="0.85" />`,
    `</g>`,
    // the outline round the lower half of the aperture: the same black as the lid, thinner, from where the lid ends
    varStroke(lowerLine().map(at), ink * 0.66, 0.55, ink * 0.16, OUTLINE),
    // the thin line on along the top of the white, growing out of the lid and tapering to a point
    taperedStroke(lidTail().map(at), ink * 0.9, OUTLINE),
    // the crease line above the lid, and the lash flicks at its inner end
    leafStroke(sampleSmooth(CREASE).map(at), 2.8 * k, shade(p.skin_tone, 0.5)),
    taperedStroke(sampleSmooth(LASH_1).map(at), 3.2 * k, OUTLINE),
    taperedStroke(sampleSmooth(LASH_2).map(at), 2.4 * k, OUTLINE),
    // the lid: a thick black band between the two arcs, tapering to a wing at the outer corner
    `<path d="${poly(lidBand(), true)}" fill="${OUTLINE}" />`,
  ];
  return parts.join("");
}

/** Both eyes. */
export function adultEyes(sk: Skeleton, p: CharacterParams): string {
  return oneEye(sk, p, -1, "adult-eye-l") + oneEye(sk, p, 1, "adult-eye-r");
}

/** The aperture and lid outlines in canvas units, for the harness's overlay on the reference (harness/franzi/eye_outline.ts). */
export function adultEyeOutlines(h: Skeleton): { side: number; aperture: Pt[]; lid: Pt[]; crease: Pt[]; lash1: Pt[]; lash2: Pt[] }[] {
  return [-1, 1].map((side) => {
    const at = placer(h, side);
    return { side, aperture: apertureOutline().map(at), lid: lidBand().map(at), crease: sampleSmooth(CREASE).map(at), lash1: sampleSmooth(LASH_1).map(at), lash2: sampleSmooth(LASH_2).map(at) };
  });
}
