// Garments fitted to the adult woman's body. The shared garment code draws from a few skeleton anchors (waist, hip and shoulder
// widths), which on this body gives straight-sided shapes that ignore her bust, waist and hips (docs/franzi-outfits-plan.md). A garment
// here is cut from the body's own edge tables (the knots in body-adult-data.ts, measured off ref/franzi/) instead, a little outside the
// skin, so it follows her shape and moves with the profile. `ADULT_GARMENT_PARTS` replaces the shared parts of the slots it covers when
// the body is in `ADULT_BODY_TYPES` (render.ts); every other body draws as it always did.

import { OUTLINE, outlineW, strokeW } from "./character.ts";
import { colorStr } from "./body-parts-legs.ts";
import { LEG_INNER, LEG_OUTER, TORSO_SIDE } from "./body-adult-data.ts";
import { ADULT_BLOUSE, ADULT_BLOUSE_LINES } from "./body-adult-blouse-data.ts";
import { ADULT_BOW } from "./body-adult-bow-data.ts";
import { ADULT_APRON, ADULT_SKIRT } from "./body-adult-skirt-data.ts";
import { FOOT_D_CUT } from "./body-adult-foot-data.ts";
import { DEFAULT_TAPER, adultBriefs, adultBustLine, at, inkAttrs, place, quad, smooth, type Knots, type Pt } from "./body-adult-parts.ts";
import { shade } from "./colorutil.ts";
import type { CharacterParams } from "./params.ts";
import { fmt1, fmt2 } from "./pynum.ts";
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

/** The legs' slot on an adult body: the briefs (always worn), then what is worn over them. */
export function adultLegsAndGarments(sk: Skeleton, p: CharacterParams): string {
  return adultBriefs(sk, p) + adultShorts(sk, p);
}

/** The adult body's garment parts, laid over `ADULT_PARTS` by render.ts. */
/** The chibi's underskirt is drawn from its own anchors and has no adult version yet, so it is not drawn on an adult body. */
const none = (): string => "";

/**
 * Worn with a skirt, the blouse is tucked in, so it is drawn with the skirt, in the skirt's own layer and before it, and not in the chest layers, which come after the skirt and would
 * lay the blouse's hem over it (it showed as white strips along the apron's edge, the owner). The skirt then covers the blouse from the waist down. Without a skirt the blouse is in the
 * chest layers as usual, over the shorts.
 */
const tuckedBlouse = (sk: Skeleton, p: CharacterParams): string => (p.outfit.skirt_color === null ? "" : adultBlouse(sk, p));
const looseBlouse = (sk: Skeleton, p: CharacterParams): string => (p.outfit.skirt_color === null ? adultBlouse(sk, p) : "");

export const ADULT_GARMENT_PARTS = {
  _legs_and_boots: adultLegsAndGarments,
  _tunic: looseBlouse,
  _skirt: (sk: Skeleton, p: CharacterParams): string => tuckedBlouse(sk, p) + adultSkirt(sk, p),
  _underskirt: none,
  _apron: adultApron,
};
