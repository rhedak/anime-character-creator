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
export const EYE_AT: Record<number, Pt> = { 1: [0.336, 0.28], [-1]: [0.307, 0.305] };

/** The lid band's top edge, inner corner to the wing's tip. */
const LID_TOP: Pt[] = [[-31, -11], [-23, -23], [-9, -31], [8, -32], [22, -28], [34, -19], [41, -13]];
/** The lid band's lower edge, which is also the aperture's top, from the wing's tip back to the inner corner. */
const LID_BOTTOM: Pt[] = [[41, -13], [35, -12], [27, -17], [14, -21], [0, -23], [-12, -21], [-23, -15], [-31, -11]];
/** The aperture's lower edge, from the outer corner round to the inner corner (the white's soft lower outline). */
const LOWER: Pt[] = [[41, -13], [37, -7], [30, 2], [20, 11], [6, 18], [-8, 19], [-20, 15], [-28, 6], [-31, -4], [-31, -11]];
const IRIS: { c: Pt; rx: number; ry: number } = { c: [-1, 0], rx: 18, ry: 23 };
const PUPIL: { c: Pt; rx: number; ry: number } = { c: [-4, 1], rx: 6, ry: 10 };
const HILITE: { c: Pt; r: number } = { c: [-8, -14], r: 6.5 };
const GLINT: { c: Pt; r: number } = { c: [7, 8], r: 2 };

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

/** One eye. `side` is +1 for the viewer's right. `h` is the skeleton with the head where it hangs. */
function oneEye(h: Skeleton, p: CharacterParams, side: number, id: string): string {
  const k = h.head_r / PX_PER_R;
  const [ex, ey] = EYE_AT[side] as Pt;
  const cx = h.head_cx + side * ex * h.head_r;
  const cy = h.head_cy + ey * h.head_r;
  const at = ([x, y]: Pt): Pt => [cx + side * x * k, cy + y * k];
  const path = (pts: readonly Pt[]): string => {
    const a = pts.map(at);
    return `M ${fmt1((a[0] as Pt)[0])} ${fmt1((a[0] as Pt)[1])} ${smooth(a)}`;
  };
  const apertureD = `${path(LID_BOTTOM)}${smooth([...LOWER].reverse().map(at))}Z`;
  const iris = p.eye_color;
  const ink = outlineW(strokeW(h));
  const clip = `<clipPath id="${id}"><path d="${apertureD}" /></clipPath>`;
  const ic = at(IRIS.c);
  const irisTop = shade(iris, 0.55);
  const parts = [
    clip,
    // the white
    `<path d="${apertureD}" fill="#ffffff" />`,
    `<g clip-path="url(#${id})">`,
    // the iris: the lower amber, with the upper third in a darker tone, as the reference's lid shades it
    ellipse(ic, IRIS.rx * k, IRIS.ry * k, iris, ""),
    `<path d="M ${fmt1(ic[0] - IRIS.rx * k)} ${fmt1(ic[1] - 0.05 * IRIS.ry * k)} A ${fmt1(IRIS.rx * k)} ${fmt1(IRIS.ry * k)} 0 0 1 ${fmt1(ic[0] + IRIS.rx * k)} ${fmt1(ic[1] - 0.05 * IRIS.ry * k)} Z" fill="${irisTop}" />`,
    ellipse(at(PUPIL.c), PUPIL.rx * k, PUPIL.ry * k, shade(iris, 0.18)),
    `<ellipse cx="${fmt1(ic[0])}" cy="${fmt1(ic[1])}" rx="${fmt1(IRIS.rx * k)}" ry="${fmt1(IRIS.ry * k)}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(ink * 0.7)}" />`,
    `<circle cx="${fmt1(at(HILITE.c)[0])}" cy="${fmt1(at(HILITE.c)[1])}" r="${fmt1(HILITE.r * k)}" fill="#ffffff" />`,
    `<circle cx="${fmt1(at(GLINT.c)[0])}" cy="${fmt1(at(GLINT.c)[1])}" r="${fmt1(GLINT.r * k)}" fill="#ffffff" opacity="0.85" />`,
    `</g>`,
    // the soft outline round the lower half of the aperture: thin, and a dark brown, not the hard black of the lid
    `<path d="${path(LOWER)}" fill="none" stroke="${shade(p.skin_tone, 0.42)}" stroke-width="${fmt2(ink * 0.55)}" stroke-linecap="round" />`,
    // the lid: a thick black band, tapering to a wing at the outer corner
    `<path d="${path(LID_TOP)}${smooth(LID_BOTTOM.map(at))}Z" fill="${OUTLINE}" />`,
  ];
  return parts.join("");
}

/** Both eyes. */
export function adultEyes(sk: Skeleton, p: CharacterParams): string {
  return oneEye(sk, p, -1, "adult-eye-l") + oneEye(sk, p, 1, "adult-eye-r");
}
