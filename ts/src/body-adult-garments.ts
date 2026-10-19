// Garments fitted to the adult woman's body. The shared garment code draws from a few skeleton anchors (waist, hip and shoulder
// widths), which on this body gives straight-sided shapes that ignore her bust, waist and hips (docs/franzi-outfits-plan.md). A garment
// here is cut from the body's own edge tables (the knots in body-adult-data.ts, measured off ref/franzi/) instead, a little outside the
// skin, so it follows her shape and moves with the profile. `ADULT_GARMENT_PARTS` replaces the shared parts of the slots it covers when
// the body is in `ADULT_BODY_TYPES` (render.ts); every other body draws as it always did.

import { OUTLINE, outlineW, strokeW } from "./character.ts";
import { colorStr } from "./body-parts-legs.ts";
import { LEG_INNER, LEG_OUTER, TORSO_SIDE } from "./body-adult-data.ts";
import { ADULT_BLOUSE, ADULT_BLOUSE_LINES } from "./body-adult-blouse-data.ts";
import { ADULT_BODICE, BODICE_BUTTONS, BODICE_BUTTON_R } from "./body-adult-bodice-data.ts";
import { ADULT_BOW } from "./body-adult-bow-data.ts";
import { ADULT_APRON, ADULT_SKIRT } from "./body-adult-skirt-data.ts";
import { FOOT_D_CUT, FOOT_OUTLINE } from "./body-adult-foot-data.ts";
import { DEFAULT_TAPER, adultBriefs, adultBustLine, at, inkAttrs, place, quad, smooth, type Knots, type Pt } from "./body-adult-parts.ts";
import { shade, tint } from "./colorutil.ts";
import { strap } from "./garments.ts";
import type { CharacterParams } from "./params.ts";
import { fmt1, fmt2, truthy } from "./pynum.ts";
import type { Skeleton } from "./skeleton.ts";
import type { Chain } from "./tables.ts";

/** The body's outer edge from the waist to the foot: the torso side, then the leg's outer edge (the tables meet at 2.2 and 2.3). */
const SIDE: Knots = [...TORSO_SIDE, ...LEG_OUTER.filter(([d]) => d <= FOOT_D_CUT)];
const LEG_IN: Knots = LEG_INNER.filter(([d]) => d <= FOOT_D_CUT);

const ease = (t: number): number => {
  const u = Math.min(1, Math.max(0, t));
  return u * u * (3 - 2 * u);
};

/** The shorts' measurements, in head heights below the chin (read off ref 02 and 03, `beige-shorts` and `white-shorts`; docs/franzi-outfits-plan.md). */
const SHORTS = {
  /** Above the briefs' waistband (1.713), so the briefs do not show over the top. */
  top: 1.68,
  /** Mid-thigh: ref 02's hem is at 2.46 and ref 03's at 2.38. */
  hem: 2.42,
  /** Where the legs part: the crotch seam, an arc over the slot. */
  crotch: 2.3,
  /** How far outside the skin's edge the cloth stands at the waist and at the hem (ref 02 and 03 stand 0.00 to 0.06 out). */
  outTop: 0.006,
  outHem: 0.04,
  /** The cloth reaches into the gap between the thighs: the skin's inner edge is 0.045 out and the shorts' legs stand about 0.03 apart (ref 02), so each edge is this far in, no nearer than `slot`. */
  overSlot: 0.03,
  slot: 0.012,
  /** The waistband's depth, and the hem's turned-up cuff. */
  band: 0.035,
  cuff: 0.04,
} as const;

/**
 * Shorts on `trouser_color`: the cloth cut from the body's side and leg tables, waist to mid-thigh, a seam down the front and the
 * waistband and cuff lines. A flat garment in one colour; the lines are the outline's weight less a third.
 */
export function adultShorts(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.trouser_color === null) return "";
  const { cx, y, w } = place(sk);
  const ink = outlineW(strokeW(sk));
  const fine = ink * 0.67;
  const flare = (d: number): number => SHORTS.outTop + (SHORTS.outHem - SHORTS.outTop) * ease((d - SHORTS.top) / (SHORTS.hem - SHORTS.top));
  // Depths down each side, dense enough for a smooth curve over the knots' own spacing.
  const dsOuter: number[] = [];
  for (let d = SHORTS.top; d < SHORTS.hem - 1e-9; d += 0.06) dsOuter.push(d);
  dsOuter.push(SHORTS.hem);
  const dsInner: number[] = [];
  for (let d = SHORTS.crotch; d < SHORTS.hem - 1e-9; d += 0.04) dsInner.push(d);
  dsInner.push(SHORTS.hem);
  const outer = (s: number, d: number): Pt => [cx + s * w(d, at(SIDE, d) + flare(d)), y(d)];
  const inner = (s: number, d: number): Pt => [cx + s * w(d, Math.max(SHORTS.slot, at(LEG_IN, Math.max(d, LEG_IN[0]![0])) - SHORTS.overSlot)), y(d)];
  const waistDip = 0.018 * sk.head_r * 2;
  // A hem is seen from a little above, so it sags toward the middle of each leg.
  const hemDip = 0.012 * sk.head_r * 2;
  const hemTo = (from: Pt, to: Pt): string => quad([(from[0] + to[0]) / 2, (from[1] + to[1]) / 2 + hemDip], to);
  const L = -1;
  const R = 1;
  const a = dsOuter.map((d) => outer(L, d));
  const start = a[0] as Pt;
  const crotchTop: Pt = [cx, y(SHORTS.crotch - 0.05)];
  const il = dsInner.map((d) => inner(L, d)).reverse();
  const ir = dsInner.map((d) => inner(R, d));
  const ar = dsOuter.map((d) => outer(R, d)).reverse();
  let d = `M ${fmt1(start[0])} ${fmt1(start[1])} `;
  d += smooth(a);
  d += hemTo(a[a.length - 1] as Pt, il[0] as Pt); // the left hem
  d += smooth(il);
  d += quad(crotchTop, ir[0] as Pt); // over the slot between the legs
  d += smooth(ir);
  d += hemTo(ir[ir.length - 1] as Pt, ar[0] as Pt); // the right hem
  d += smooth(ar);
  d += quad([cx, (start[1] + waistDip)], start); // the waist, dipping a little toward the front
  d += "Z";
  const fill = colorStr(p.outfit.trouser_color);
  const lineAttrs = `fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(fine)}" stroke-linecap="round"`;
  const bandY = SHORTS.top + SHORTS.band;
  const bandL = outer(L, bandY);
  const bandR = outer(R, bandY);
  const seam = `<path d="M ${fmt1(cx)} ${fmt1(y(bandY) + waistDip * 0.45)} L ${fmt1(cx)} ${fmt1(crotchTop[1] + 3)}" ${lineAttrs} />`;
  const band = `<path d="M ${fmt1(bandL[0])} ${fmt1(bandL[1])} ${quad([cx, y(bandY) + waistDip * 0.9], bandR)}" ${lineAttrs} />`;
  const cuffY = SHORTS.hem - SHORTS.cuff;
  const cuff = [L, R]
    .map((s) => {
      const o = outer(s, cuffY);
      const i = inner(s, cuffY);
      return `<path d="M ${fmt1(o[0])} ${fmt1(o[1])} ${hemTo(o, i)}" ${lineAttrs} />`;
    })
    .join("");
  return `<path d="${d}" ${inkAttrs(sk, fill)} />${band}${seam}${cuff}`;
}

/**
 * The blouse on `tunic_color`: bodice and puff sleeves in one piece, traced from the white-blouse layer of ref 02 (body-adult-blouse-data.ts), with the sweetheart
 * neckline, frilled cuffs and the opening at the hem. Mapped onto the skeleton as the top and the briefs are, so it follows the profile's shoulders, waist and hips.
 * Drawn in the chest layers, over the body and under the hands. A flat garment in one colour; its lines (the neckline's binding, each sleeve's seam, the gather above
 * each cuff, the front opening) are the outline's weight less a third.
 */
export function adultBlouse(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.tunic_color === null) return "";
  const { cx, y, w } = place(sk);
  const map = (q: Pt): Pt => [cx + w(q[1], q[0]), y(q[1])];
  const [start, segs] = ADULT_BLOUSE;
  const s0 = map(start);
  const d = `M ${fmt1(s0[0])} ${fmt1(s0[1])} ` + segs.map(([c, e]) => quad(map(c), map(e))).join("") + "Z";
  const lineAttrs = `fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)) * 0.67)}" stroke-linecap="round" stroke-linejoin="round"`;
  // A left-hand polyline [v, d] on the viewer's left (sign -1) and the right (sign 1).
  const side = (line: readonly (readonly [number, number])[], sign: number): Pt[] => line.map(([v, dd]) => [cx + sign * w(dd, v), y(dd)] as Pt);
  const open = (pts: Pt[]): string => `<path d="M ${fmt1((pts[0] as Pt)[0])} ${fmt1((pts[0] as Pt)[1])} ${smooth(pts)}" ${lineAttrs} />`;
  const both = (line: readonly (readonly [number, number])[]): string => open(side(line, -1)) + open(side(line, 1));
  // The binding runs from one strap's top, along the neckline, round the point and up the other strap: one curve.
  const bind = [...side(ADULT_BLOUSE_LINES.binding, -1), ...side(ADULT_BLOUSE_LINES.binding, 1).reverse().slice(1)];
  const [o0, o1] = ADULT_BLOUSE_LINES.opening;
  const opening = `<path d="M ${fmt1(cx)} ${fmt1(y(o0))} L ${fmt1(cx)} ${fmt1(y(o1))}" ${lineAttrs} />`;
  // The lines are clipped to the cloth, so a seam read off the reference that starts a pixel above the sleeve's cap does not poke out of it.
  const clip = `<clipPath id="adult-blouse-clip"><path d="${d}" /></clipPath>`;
  // The breasts' shapes over the cloth, as on the bikini top: a darker tone of the cloth at a light weight, under the other lines. It shows where the cut follows
  // the bust and where it does not.
  const bust = adultBustLine(sk, DEFAULT_TAPER, shade(colorStr(p.outfit.tunic_color), 0.8, 1.0), 0.7);
  const lines = bust + open(bind) + both(ADULT_BLOUSE_LINES.seam) + both(ADULT_BLOUSE_LINES.gather) + opening;
  return `<path d="${d}" ${inkAttrs(sk, colorStr(p.outfit.tunic_color))} />${clip}<g clip-path="url(#adult-blouse-clip)">${lines}</g>`;
}

/** A closed traced chain in [x, d] about the garment's centre line, as a path mapped onto the skeleton. */
function chainPath(sk: Skeleton, [start, segs]: Chain): string {
  const { cx, y, w } = place(sk);
  const map = (q: Pt): Pt => [cx + w(q[1], q[0]), y(q[1])];
  const s0 = map(start);
  return `M ${fmt1(s0[0])} ${fmt1(s0[1])} ` + segs.map(([c, e]) => quad(map(c), map(e))).join("") + "Z";
}

/**
 * The dirndl's skirt on `skirt_color`: the green flare from the waist to a hem 2.97 H below the chin, traced from ref 00 (body-adult-skirt-data.ts), one flat colour. It
 * hangs from under the apron's sash (or the bodice) and covers the briefs and the shorts. Drawn where the chibi skirt is, behind the chest layers; the arms are drawn
 * again over it (`adultArmsOver`), as in the reference they hang in front of it.
 */
export function adultSkirt(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.skirt_color === null) return "";
  return `<path d="${chainPath(sk, ADULT_SKIRT)}" ${inkAttrs(sk, colorStr(p.outfit.skirt_color))} />`;
}

/**
 * The apron on `apron_color`: the red apron of ref 00, narrower and shorter than the skirt so a band of it shows round the hem, with its sash at the waist. One flat
 * colour; the sash's lower edge is a line, and the bow with its two tails hangs from the sash's right side.
 */
export function adultApron(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.apron_color === null) return "";
  const { cx, y, w } = place(sk);
  const d = chainPath(sk, ADULT_APRON);
  // The sash: a band over the waist from the apron's top to its lower edge, as wide as the blouse at that depth (the owner: it has to reach the blouse's outline on both sides), so it
  // covers the blouse's side where the apron, narrower there, would leave a strip of it. Its sides follow the blouse's half-width (0.368 H at the top, 0.365 at 1.30, 0.378 at 1.345,
  // measured on the traced blouse); its top is the apron's own (a little lower at the middle); its lower edge is read off the reference (the darkest pixel of each column below the
  // sash), sagging toward the middle.
  const side: [number, number][] = [[0.368, 1.276], [0.365, 1.3], [0.378, 1.345]];
  const lower: [number, number][] = [[0.378, 1.345], [0.318, 1.372], [0.233, 1.403], [0.148, 1.418], [0.05, 1.423], [0, 1.424]];
  const P = (sign: number, [v, dd]: [number, number]): Pt => [cx + sign * w(dd, v), y(dd)];
  const topL = P(-1, side[0] as [number, number]);
  const topR = P(1, side[0] as [number, number]);
  const sashPath =
    `M ${fmt1(topL[0])} ${fmt1(topL[1])} ` +
    `Q ${fmt1(cx)} ${fmt1(topL[1] + 2 * (y(1.2983) - topL[1]))} ${fmt1(topR[0])} ${fmt1(topR[1])} ` +
    smooth(side.map((q) => P(1, q))) +
    smooth([...lower.map((q) => P(1, q)), ...lower.slice(0, -1).reverse().map((q) => P(-1, q))]) +
    smooth([...side].reverse().map((q) => P(-1, q))) +
    "Z";
  // The bow: two tails, two loops and the knot over them, in the apron's own colour, told apart by their outlines (the shapes are body-adult-bow-data.ts's, read off ref 00).
  const fill = colorStr(p.outfit.apron_color);
  const mapPt = (q: readonly [number, number]): Pt => [cx + w(q[1], q[0]), y(q[1])];
  const bow = Object.values(ADULT_BOW)
    .map((runs) => {
      const first = mapPt(runs[0]![0]!);
      const path = `M ${fmt1(first[0])} ${fmt1(first[1])} ` + runs.map((run) => smooth(run.map(mapPt))).join("") + "Z";
      return `<path d="${path}" fill="${fill}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)) * 0.8)}" stroke-linejoin="round" />`;
    })
    .join("");
  return `<path d="${d}" ${inkAttrs(sk, fill)} /><path id="adult-apron-sash" d="${sashPath}" ${inkAttrs(sk, fill)} />${bow}`;
}

/**
 * The dirndl's bodice, traced from the corset layer of ref 03 (body-adult-bodice-data.ts): straps, the scooped neckline that shows the blouse, sides that nip in at the waist and a hem
 * with a notch at the front, with the lacing (a ribbon from each button to the next row's button on the other side, and one across the top) and the sixteen gold buttons, two columns
 * of eight. One flat colour; the laces are a darker tone of it, the buttons gold with a small lighter highlight (small elements, so a second tone is allowed).
 *
 * `hem` is the depth, in head heights below the chin, where the bodice is cut off when something lies over its lower part (the sash at 1.34, a skirt's top at 1.315); null draws the
 * whole bodice, down to the hips as in the reference. `adultBodice` draws it from `Outfit.bodice_color`.
 */
export function adultBodiceCloth(sk: Skeleton, color: string, hem: number | null = null): string {
  const { cx, y, w } = place(sk);
  const ink = outlineW(strokeW(sk));
  const d = chainPath(sk, ADULT_BODICE);
  const body = `<path d="${d}" ${inkAttrs(sk, colorStr(color))} />`;
  const clip = `<clipPath id="adult-bodice-clip"><path d="${d}" /></clipPath>`;
  // The lacing, over the bodice: crossing ribbons, each a dark outline under a band of the lace tone.
  const lace = shade(colorStr(color), 0.62, 1.0);
  const btn = (side: number, i: number): Pt => [cx + side * w((BODICE_BUTTONS[i] as readonly [number, number])[1], (BODICE_BUTTONS[i] as readonly [number, number])[0]), y((BODICE_BUTTONS[i] as readonly [number, number])[1])];
  const ribbonW = 0.017 * 2 * sk.head_r;
  const ribbon = (a: Pt, b: Pt): string =>
    `<path d="M ${fmt1(a[0])} ${fmt1(a[1])} L ${fmt1(b[0])} ${fmt1(b[1])}" stroke="${OUTLINE}" stroke-width="${fmt2(ribbonW + ink * 0.55)}" stroke-linecap="round" fill="none" />` +
    `<path d="M ${fmt1(a[0])} ${fmt1(a[1])} L ${fmt1(b[0])} ${fmt1(b[1])}" stroke="${lace}" stroke-width="${fmt2(ribbonW)}" stroke-linecap="round" fill="none" />`;
  let ribbons = ribbon(btn(-1, 0), btn(1, 0));
  for (let i = 0; i < BODICE_BUTTONS.length - 1; i++) ribbons += ribbon(btn(-1, i), btn(1, i + 1)) + ribbon(btn(1, i), btn(-1, i + 1));
  const r = BODICE_BUTTON_R * 2 * sk.head_r;
  const gold = "#dfae45";
  let buttons = "";
  for (let i = 0; i < BODICE_BUTTONS.length; i++) {
    for (const s of [-1, 1]) {
      const c = btn(s, i);
      buttons += `<circle cx="${fmt1(c[0])}" cy="${fmt1(c[1])}" r="${fmt1(r)}" fill="${gold}" stroke="${OUTLINE}" stroke-width="${fmt2(ink * 0.5)}" />`;
      buttons += `<circle cx="${fmt1(c[0] - r * 0.28)}" cy="${fmt1(c[1] - r * 0.28)}" r="${fmt1(r * 0.3)}" fill="${tint(gold, 0.55)}" />`;
    }
  }
  const inside = `${clip}<g clip-path="url(#adult-bodice-clip)">${ribbons}${buttons}</g>`;
  if (hem === null) return body + inside;
  // Cut where something lies over the lower part: the outline stops there and a line closes the bottom edge.
  const cutY = y(hem);
  const cut = `<clipPath id="adult-bodice-cut"><rect x="0" y="0" width="${fmt1(sk.canvas_w)}" height="${fmt1(cutY)}" /></clipPath>`;
  const edge = `<g clip-path="url(#adult-bodice-clip)"><path d="M 0 ${fmt1(cutY)} H ${fmt1(sk.canvas_w)}" stroke="${OUTLINE}" stroke-width="${fmt2(ink)}" fill="none" /></g>`;
  return `${cut}<g clip-path="url(#adult-bodice-cut)">${body}${inside}</g>${edge}`;
}

/**
 * A blouse is tucked in when the outfit says so (`tunic_tucked`), or a skirt or a bodice is worn (a bodice ends above the blouse's hem) (the skirt is drawn before the chest layers, so an untucked blouse would lay its hem over it and show as
 * white strips along the apron's edge, the owner). A tucked blouse is drawn in the legs' layer, after the briefs and before the shorts or the skirt, which then cover its lower part; an untucked
 * one is in the chest layers, over everything below the waist (as in ref 02, the blouse over the shorts).
 */
const tucked = (p: CharacterParams): boolean => p.outfit.tunic_color !== null && (truthy(p.outfit.tunic_tucked) || p.outfit.skirt_color !== null || p.outfit.bodice_color !== null);

// ---- socks and boots, cut from the leg's and the foot's own tables

/** A traced chain of quadratics as points, `per` to a segment. */
function sampleChain([start, segs]: Chain, per: number): Pt[] {
  const out: Pt[] = [start as Pt];
  let p0 = start as Pt;
  for (const [c, e] of segs) {
    for (let i = 1; i <= per; i++) {
      const t = i / per;
      out.push([(1 - t) * (1 - t) * p0[0] + 2 * (1 - t) * t * c[0] + t * t * e[0], (1 - t) * (1 - t) * p0[1] + 2 * (1 - t) * t * c[1] + t * t * e[1]]);
    }
    p0 = e as Pt;
  }
  return out;
}

/** The points of an open chain that lie on its convex hull, in the chain's order (the straight line that would close it is not part of the result). */
function hullInOrder(pts: readonly Pt[]): Pt[] {
  const cross = (o: Pt, a: Pt, b: Pt): number => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const idx = pts.map((_, i) => i).sort((i, j) => (pts[i] as Pt)[0] - (pts[j] as Pt)[0] || (pts[i] as Pt)[1] - (pts[j] as Pt)[1]);
  const half = (order: number[]): number[] => {
    const h: number[] = [];
    for (const i of order) {
      while (h.length >= 2 && cross(pts[h[h.length - 2] as number] as Pt, pts[h[h.length - 1] as number] as Pt, pts[i] as Pt) <= 0) h.pop();
      h.push(i);
    }
    return h;
  };
  const lower = half(idx);
  const upper = half([...idx].reverse());
  const onHull = new Set([...lower, ...upper]);
  return pts.filter((_, i) => onHull.has(i));
}

/** A polyline with a point at least every `step` pixels. */
function densify(pts: readonly Pt[], step: number): Pt[] {
  const out: Pt[] = [pts[0] as Pt];
  for (let i = 1; i < pts.length; i++) {
    const a = pts[i - 1] as Pt;
    const b = pts[i] as Pt;
    const n = Math.max(1, Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) / step));
    for (let k = 1; k <= n; k++) out.push([a[0] + ((b[0] - a[0]) * k) / n, a[1] + ((b[1] - a[1]) * k) / n]);
  }
  return out;
}

/** A moving average over `half` points each side, the two ends kept where they are. */
function smoothed(pts: readonly Pt[], half: number): Pt[] {
  return pts.map((q, i) => {
    if (i === 0 || i === pts.length - 1) return q;
    const r = Math.min(half, i, pts.length - 1 - i);
    let x = 0;
    let yy = 0;
    for (let k = -r; k <= r; k++) {
      x += (pts[i + k] as Pt)[0];
      yy += (pts[i + k] as Pt)[1];
    }
    return [x / (2 * r + 1), yy / (2 * r + 1)] as Pt;
  });
}

/** The leg's depths from `d0` to `d1`, every `step`, and `d1` itself. */
const depths = (d0: number, d1: number, step = 0.1): number[] => {
  const out: number[] = [];
  for (let d = d0; d < d1 - 1e-9; d += step) out.push(d);
  out.push(d1);
  return out;
};

/** Where the knee-high sock begins (just under the knee) and the ankle boot's top, and how far a full boot shaft climbs (the knee), in head heights below the chin. */
const SOCK_TOP = 3.62;
const ANKLE_BOOT_TOP = 4.18;
const SHAFT_TOP = 3.55;

/**
 * Knee socks on `knee_sock_color`: a tube over each leg from just under the knee to the ankle, where the foot begins, standing a little off the skin, with a band at the top.
 * The legs' tables give both edges, so it follows her calf. A flat garment in one colour. Drawn over the legs; the foot below it stays bare unless boots are worn.
 */
export function adultKneeSocks(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.knee_sock_color === null) return "";
  const { cx, y, w } = place(sk);
  const ink = outlineW(strokeW(sk));
  const m = 0.012;
  const ds = depths(SOCK_TOP, FOOT_D_CUT, 0.1);
  const leg = (sign: number): string => {
    const outer = ds.map((d) => [cx + sign * w(d, at(LEG_OUTER, d) + m), y(d)] as Pt);
    const inner = ds.map((d) => [cx + sign * w(d, Math.max(0.02, at(LEG_IN, d) - m)), y(d)] as Pt).reverse();
    const first = outer[0] as Pt;
    const path = `M ${fmt1(first[0])} ${fmt1(first[1])} ${smooth(outer)}L ${fmt1((inner[0] as Pt)[0])} ${fmt1((inner[0] as Pt)[1])} ${smooth(inner)}Z`;
    const bandD = SOCK_TOP + 0.05;
    const a: Pt = [cx + sign * w(bandD, at(LEG_OUTER, bandD) + m), y(bandD)];
    const b: Pt = [cx + sign * w(bandD, Math.max(0.02, at(LEG_IN, bandD) - m)), y(bandD)];
    const band = `<path d="M ${fmt1(a[0])} ${fmt1(a[1])} L ${fmt1(b[0])} ${fmt1(b[1])}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(ink * 0.67)}" stroke-linecap="round" />`;
    return `<path d="${path}" ${inkAttrs(sk, colorStr(p.outfit.knee_sock_color as string))} />${band}`;
  };
  return leg(-1) + leg(1);
}

/**
 * Boots on `boot_color`: each foot and the leg above it, out to the knee as `boot_shaft` says (0 an ankle boot, 1 to the knee), cut from the leg's tables and the traced foot's outline, a
 * little off the skin, with a thicker sole. `boot_cut` "loafer" is a low shoe, the foot alone. A flat garment in one colour; its cuff is a line. The foot's toes and nails are not drawn
 * under it (body-adult-parts.ts, `adultDetail`).
 */
export function adultBoots(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.boot_color === null) return "";
  const { cx, y, w } = place(sk);
  const ink = outlineW(strokeW(sk));
  const hs = ink / 2;
  const unit = 2 * sk.head_r; // one head height in pixels
  const loafer = p.outfit.boot_cut === "loafer";
  const top = loafer ? FOOT_D_CUT : ANKLE_BOOT_TOP + (SHAFT_TOP - ANKLE_BOOT_TOP) * Math.min(1, Math.max(0, Number(p.outfit.boot_shaft)));
  const mLeg = 0.014;
  const off = hs + 0.014 * unit; // off the skin's ink edge
  const sole = 0.012 * unit; // thicker under the toes and the heel
  const boot = (sign: number): string => {
    const P = (v: number, d: number): Pt => [cx + sign * w(d, v), y(d)];
    const ds = depths(top, FOOT_D_CUT, 0.1);
    const outer = loafer ? [] : ds.map((d) => P(at(LEG_OUTER, d) + mLeg, d));
    const inner = loafer ? [] : ds.map((d) => P(Math.max(0.02, at(LEG_IN, d) - mLeg), d)).reverse();
    // A shoe's toe is one smooth curve, not the foot's five toes: the outline's convex hull (in the chain's order), densified and smoothed, is the shoe's last.
    const chain = smoothed(densify(hullInOrder(sampleChain(FOOT_OUTLINE, 5).map(([v, d]) => P(v, d))), 3), 4);
    const foot = chain.map((q, i) => {
      const a = chain[Math.max(0, i - 1)] as Pt;
      const b = chain[Math.min(chain.length - 1, i + 1)] as Pt;
      const tx = b[0] - a[0];
      const ty = b[1] - a[1];
      const len = Math.hypot(tx, ty) || 1;
      const nx = (sign * ty) / len; // outward: the chain runs outer edge, toes, inner edge
      const ny = (-sign * tx) / len;
      const k = off + (ny > 0.5 ? sole * ny : 0);
      return [q[0] + nx * k, q[1] + ny * k] as Pt;
    });
    // the foot's offset ends are on the leg's offset edges at the ankle cut; the shoe's own top edge is straight across
    const run: Pt[] = [...outer, ...foot, ...inner];
    const first = run[0] as Pt;
    const path = `M ${fmt1(first[0])} ${fmt1(first[1])} ${smooth(run)}Z`;
    const cuffD = top + 0.045;
    const cuff = loafer
      ? ""
      : `<path d="M ${fmt1(P(at(LEG_OUTER, cuffD) + mLeg, cuffD)[0])} ${fmt1(y(cuffD))} L ${fmt1(P(Math.max(0.02, at(LEG_IN, cuffD) - mLeg), cuffD)[0])} ${fmt1(y(cuffD))}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(ink * 0.67)}" stroke-linecap="round" />`;
    return `<path d="${path}" ${inkAttrs(sk, colorStr(p.outfit.boot_color as string))} />${cuff}`;
  };
  return boot(-1) + boot(1);
}

/** The bodice on `bodice_color`, cut at the sash or the skirt's top when one is worn. */
export function adultBodice(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.bodice_color === null) return "";
  const hem = p.outfit.apron_color !== null ? 1.34 : p.outfit.skirt_color !== null ? 1.315 : null;
  return adultBodiceCloth(sk, p.outfit.bodice_color, hem);
}

/** The legs' slot on an adult body: the briefs (always worn), a tucked blouse, then what is worn over them. */
export function adultLegsAndGarments(sk: Skeleton, p: CharacterParams): string {
  return adultBriefs(sk, p) + (tucked(p) ? adultBlouse(sk, p) : "") + adultShorts(sk, p) + adultKneeSocks(sk, p) + adultBoots(sk, p);
}

/** The chibi's underskirt is drawn from its own anchors and has no adult version yet, so it is not drawn on an adult body. */
const none = (): string => "";

/** The adult body's garment parts, laid over `ADULT_PARTS` by render.ts. */
export const ADULT_GARMENT_PARTS = {
  _legs_and_boots: adultLegsAndGarments,
  _tunic: (sk: Skeleton, p: CharacterParams): string => (tucked(p) ? "" : adultBlouse(sk, p)),
  _skirt: adultSkirt,
  _underskirt: none,
  // the strap's slot, which comes before the apron's in the chest layers: the bodice, then the cross-body strap of the shared garments
  _strap: (sk: Skeleton, p: CharacterParams): string => adultBodice(sk, p) + strap(sk, p),
  _apron: adultApron,
};
