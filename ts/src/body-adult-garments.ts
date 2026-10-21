// Garments fitted to the adult woman's body. The shared garment code draws from a few skeleton anchors (waist, hip and shoulder
// widths), which on this body gives straight-sided shapes that ignore her bust, waist and hips (docs/franzi-outfits-plan.md). A garment
// here is cut from the body's own edge tables (the knots in body-adult-data.ts, measured off ref/franzi/) instead, a little outside the
// skin, so it follows her shape and moves with the profile. `ADULT_GARMENT_PARTS` replaces the shared parts of the slots it covers when
// the body is in `ADULT_BODY_TYPES` (render.ts); every other body draws as it always did.

import { OUTLINE, outlineW, strokeW } from "./character.ts";
import { colorStr } from "./body-parts-legs.ts";
import { ARM_INNER, ARM_OUTER, LEG_INNER, LEG_OUTER, TORSO_SIDE } from "./body-adult-data.ts";
import { ADULT_BLOUSE, ADULT_BLOUSE_LINES } from "./body-adult-blouse-data.ts";
import { adultArmPoses, raisedSides } from "./body-adult-pose.ts";
import { armAxis, armTurn, armTurnBack } from "./body-adult-pose-arm.ts";
import { ADULT_BODICE, BODICE_BUTTONS, BODICE_BUTTON_R } from "./body-adult-bodice-data.ts";
import { ADULT_BOW } from "./body-adult-bow-data.ts";
import { ADULT_APRON, ADULT_SKIRT } from "./body-adult-skirt-data.ts";
import { adultBlazer, wearsBlazer } from "./body-adult-blazer.ts";
import { adultRibbon, adultShirt, wearsShirt } from "./body-adult-shirt.ts";
import { LOAFER_ASPECT, LOAFER_OUTLINE, LOAFER_SEAM, LOAFER_SLOT, LOAFER_SOLE_EDGE, LOAFER_STRAP_BOT, LOAFER_STRAP_TOP } from "./body-adult-loafer-data.ts";
import { ADULT_PLEATED_BAND, ADULT_PLEATED_FOLDS, ADULT_PLEATED_SKIRT } from "./body-adult-skirt-pleated-data.ts";
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

/** The depth in head heights below the chin where a blouse sleeve ends: its cuff is at about 1.1, and the hem's flare, which is the body's, starts well below. */
const SLEEVE_END = 1.25;
/** The corner of a sleeve's cap that is left without an outline when the arm is raised: above this depth and inside this half-width (head heights), where the cap meets the bodice. */
const CAP_D = 0.42;
const CAP_V = 0.58;
/** The points of the blouse's traced outline between which the sleeve's outer edge runs, from the cuff's outer corner to the cap, which a raised sleeve reflects for its inner edge (indices into the chain's points). */
/** Where the sleeve proper begins, in head heights below the chin: above it the cloth is the cap, which is drawn only over the body. */
const SLEEVE_TOP = 0.3;
/**
 * The outer edge of a raised side's bodice, [v, d] in head heights: the traced edge from the bust's widest point (0.465 at 0.81) down its nip at the waist, which is kept, then on to the sash at
 * the traced waist's width (0.362), without the step and the hem's flare the trace has between (0.354 at 1.09, 0.385 at 1.1), which show as a notch when the arm does not hide them.
 */
const BODICE_FILL: readonly (readonly [number, number])[] = [[0.467, 0.81], [0.454, 0.886], [0.433, 0.943], [0.41, 0.98], [0.39, 1.01], [0.376, 1.1], [0.368, 1.2], [0.364, 1.3], [0.362, 1.36]];
/** The points of the bodice's traced outline that make its outer side, from the waist up to its top (indices into the chain's points). */
const BODICE_SIDE_FROM = 23;
const BODICE_SIDE_TO = 34;
/** From this angle (degrees) a raised sleeve's end is inked as a rim, and how far it bows toward the shoulder, in head heights. */
const RIM_FROM = 105;
const RIM_BOW = 0.05;
const CONTOUR_FROM = 13;
const CONTOUR_TO = 28;

/**
 * The blouse on `tunic_color`: bodice and puff sleeves in one piece, traced from the white-blouse layer of ref 02 (body-adult-blouse-data.ts), with the sweetheart
 * neckline, frilled cuffs and the opening at the hem. Mapped onto the skeleton as the top and the briefs are, so it follows the profile's shoulders, waist and hips.
 * Drawn in the chest layers, over the body and under the hands. A flat garment in one colour; its lines (the neckline's binding, each sleeve's seam, the gather above
 * each cuff, the front opening) are the outline's weight less a third.
 */
export function adultBlouse(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.tunic_color === null) return "";
  if (wearsShirt(p)) return adultShirt(sk, p);
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
  const raised = adultArmPoses(p);
  const L = -1;
  const R = 1;
  if (raised.length === 0) return `<path d="${d}" ${inkAttrs(sk, colorStr(p.outfit.tunic_color))} />${clip}<g clip-path="url(#adult-blouse-clip)">${lines}</g>`;

  // A raised arm takes its sleeve with it. The blouse is one traced piece, so it is split along the seam (the line where the sleeve meets the bodice) into the body and one sleeve per raised
  // arm. The sleeve is the cloth outside the seam, which is carried up above the shoulder and down through the gap between the arm and the ribs; it is turned with the arm, by the same
  // transform. Each piece is the whole blouse clipped to its region, so the outline and the fill are the traced ones, and the seam and the gather above the cuff are drawn on the piece they
  // belong to, whole (a line on the cut would be clipped in half).
  // The body piece is cut along the seam, or along the bodice's outer edge where that is further in: the blouse's armhole allowance beyond the bodice is hidden by the arm when it hangs, and when
  // it is raised it shows as a white strip down the bodice's side (the owner's residual).
  const [bodiceStart, bodiceSegs] = ADULT_BODICE;
  const bodiceSide: [number, number][] = [bodiceStart, ...bodiceSegs.map(([, e]) => e)]
    .slice(BODICE_SIDE_FROM, BODICE_SIDE_TO + 1)
    .map(([x, dd]): [number, number] => [dd, -x])
    .sort((a, b) => a[0] - b[0]);
  const bodiceEdge = (dd: number): number => at(bodiceSide, dd);
  const region = (sign: number): Pt[] =>
    ([[0.42, -0.1], ...ADULT_BLOUSE_LINES.seam, [0.41, SLEEVE_END]] as [number, number][])
      .map(([v, dd]): [number, number] => (dd >= bodiceSide[0]![0] ? [Math.min(v, bodiceEdge(Math.min(dd, bodiceSide[bodiceSide.length - 1]![0]))), dd] : [v, dd]))
      .map(([v, dd]): Pt => [cx + sign * w(dd, v), y(dd)]);
  const far = (sign: number, dd: number): Pt => [cx + sign * w(dd, 1.6), y(dd)];
  const points = (pts: Pt[]): string => pts.map((q) => `${fmt1(q[0])},${fmt1(q[1])}`).join(" ");
  const raisedSigns = raised.map((r) => r.sign);
  // the body piece is everything but the sleeves: below the sleeve's end the whole width, so the hem's flare, which reaches farther out than the seam, stays with the body
  const leftEdge = raisedSigns.includes(L) ? [...region(L), far(L, SLEEVE_END), far(L, 2.0)]: [far(L, -0.1), far(L, 2.0)];
  const rightEdge = raisedSigns.includes(R) ? [far(R, 2.0), far(R, SLEEVE_END), ...[...region(R)].reverse()] : [far(R, 2.0), far(R, -0.1)];
  const fill = inkAttrs(sk, colorStr(p.outfit.tunic_color));
  const shape = `<defs><path id="adult-blouse-shape" d="${d}" /></defs><clipPath id="adult-blouse-clip"><use href="#adult-blouse-shape" /></clipPath>`;
  const cloth = `<use href="#adult-blouse-shape" ${fill} />`;
  const hanging = [L, R].filter((s) => !raisedSigns.includes(s));
  const bodyLines = bust + open(bind) + hanging.map((s) => open(side(ADULT_BLOUSE_LINES.seam, s)) + open(side(ADULT_BLOUSE_LINES.gather, s))).join("") + opening;
  const body =
    `<clipPath id="adult-blouse-body"><polygon points="${points([...leftEdge, ...rightEdge])}" /></clipPath>` +
    `<g clip-path="url(#adult-blouse-body)">${cloth}<g clip-path="url(#adult-blouse-clip)">${bodyLines}</g></g>` +
    `<g clip-path="url(#adult-blouse-clip)">${raisedSigns.map((s) => open(side(ADULT_BLOUSE_LINES.seam, s))).join("")}</g>`;
  // The sleeve's cap (its top, at the shoulder) ends up beside the bodice when the arm is raised, and the outline along the cap's edge, which was the shoulder's edge, then reads as a hard cut
  // where the cloth should run into the bodice. So the sleeve piece is the cloth with no outline there: its fill is clipped to the sleeve's region and its outline to the same region less the
  // cap's corner (above `CAP_D`, inside `CAP_V`), which leaves the outline along the outer edge, the cuff and the underside.
  const clothEdge = `<use href="#adult-blouse-shape" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)))}" stroke-linejoin="round" />`;
  const clothFill = `<use href="#adult-blouse-shape" fill="${colorStr(p.outfit.tunic_color)}" stroke="none" />`;
  // A raised arm's sleeve is a bag round the whole upper arm, as in the packs, but the trace has the sleeve of a hanging arm: its outer edge is the puff and its inner edge the seam, a straight line
  // that is the bodice's armhole. So the sleeve's inner edge is the outer edge reflected across the upper arm's centre line, or the seam where that is further out (at the cuff and the cap),
  // inked, and the seam line is not drawn on the sleeve (the bodice keeps it).
  const [chainStart, chainSegs] = ADULT_BLOUSE;
  const chainPts: Pt[] = [chainStart, ...chainSegs.map(([, e]) => e)];
  const contour = (() => {
    const out: Pt[] = [];
    for (let i = CONTOUR_FROM; i < CONTOUR_TO; i++) {
      const a = chainPts[i] as Pt;
      const [c, e] = chainSegs[i] as [Pt, Pt];
      for (let k = i === CONTOUR_FROM ? 0 : 1; k <= 4; k++) {
        const t = k / 4;
        const f = (a0: number, c0: number, e0: number): number => (1 - t) * (1 - t) * a0 + 2 * (1 - t) * t * c0 + t * t * e0;
        out.push([-f(a[0], c[0], e[0]), f(a[1], c[1], e[1])]); // [v, d], v the distance from the centre line
      }
    }
    return out.reverse(); // from the shoulder down
  })();
  const seamV = (dd: number): number => {
    const sm = ADULT_BLOUSE_LINES.seam;
    return at(sm.map(([v, d0]) => [d0, v] as const), dd);
  };
  const inner = contour.filter(([, dd]) => dd >= CAP_D).map(([v, dd]): [number, number] => [Math.min(2 * armAxis(dd) - v, seamV(dd)), dd]);
  const innerEdge = (sign: number): Pt[] => inner.map(([v, dd]): Pt => [cx + sign * w(dd, v), y(dd)]);
  // the sleeve's inner edge goes on up the seam above `CAP_D`, to `SLEEVE_TOP`, so its outline reaches the body
  const seamTop = ADULT_BLOUSE_LINES.seam.filter(([, dd]) => dd < CAP_D) as unknown as [number, number][];
  const upSeam: [number, number][] = [[seamV(SLEEVE_TOP), SLEEVE_TOP], ...seamTop.filter(([, dd]) => dd > SLEEVE_TOP)];
  const innerFull = (sign: number): Pt[] => [...upSeam.map(([v, dd]): Pt => [cx + sign * w(dd, v), y(dd)]), ...innerEdge(sign)];
  const seamEnd = ADULT_BLOUSE_LINES.seam.filter(([, dd]) => dd > (inner[inner.length - 1] as [number, number])[1]) as unknown as [number, number][];
  const sleeves = raised
    .map((r) => {
      const tag = r.sign < 0 ? "l" : "r";
      const outer = [far(r.sign, SLEEVE_END), far(r.sign, -0.1)];
      const m = (q: [number, number]): Pt => [cx + r.sign * w(q[1], q[0]), y(q[1])];
      const sleeveRegion = [...innerFull(r.sign), ...seamEnd.map(m), m([0.41, SLEEVE_END])];
      // the cap (the cloth above the sleeve proper, over the shoulder) swings with the arm and can end up beyond the body; it is drawn only where it lies over the body's silhouette
      const capRegion = [m([0.42, -0.1]), ...seamTop.filter(([, dd]) => dd < SLEEVE_TOP).map(m), m([seamV(SLEEVE_TOP), SLEEVE_TOP]), far(r.sign, SLEEVE_TOP), far(r.sign, -0.1)];
      const edgeRegion = [m([CAP_V, -0.1]), m([CAP_V, CAP_D]), m([0.43, CAP_D]), ...innerEdge(r.sign), ...seamEnd.map(m), m([0.41, SLEEVE_END])];
      const edge = innerFull(r.sign);
      // Raised far enough, the sleeve's end (where the cloth passes to the cap, across the arm at `SLEEVE_TOP`) lies beside the body, not in the shoulder's cloth, and is inked: a short curve bowed toward
      // the shoulder, from the inner edge's end to the outer edge's, so the sleeve ends in a rim against the body.
      const rimFrom = edge[0] as Pt;
      const rimTo = m([(contour[0] as [number, number])[0], (contour[0] as [number, number])[1]]);
      const rimBow = RIM_BOW * 2 * sk.head_r;
      const rim =
        r.angle >= RIM_FROM
          ? `<path d="M ${fmt1(rimFrom[0])} ${fmt1(rimFrom[1])} Q ${fmt1((rimFrom[0] + rimTo[0]) / 2)} ${fmt1((rimFrom[1] + rimTo[1]) / 2 - rimBow)} ${fmt1(rimTo[0])} ${fmt1(rimTo[1])}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)))}" stroke-linecap="round" />`
          : "";
      const inkLine = `<path d="M ${fmt1((edge[0] as Pt)[0])} ${fmt1((edge[0] as Pt)[1])} ${smooth(edge)}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)))}" stroke-linecap="round" stroke-linejoin="round" />`;
      return (
        `<clipPath id="adult-blouse-sleeve-${tag}"><polygon points="${points([...sleeveRegion, far(r.sign, SLEEVE_END), far(r.sign, SLEEVE_TOP)])}" /></clipPath>` +
        `<clipPath id="adult-blouse-cap-${tag}"><polygon points="${points(capRegion)}" /></clipPath>` +
        `<clipPath id="adult-blouse-cap-body-${tag}"><use href="#adult-body-outline" transform="${armTurnBack(sk, r)}" /></clipPath>` +
        `<clipPath id="adult-blouse-sleeve-edge-${tag}"><polygon points="${points([...edgeRegion, ...outer])}" /></clipPath>` +
        `<g transform="${armTurn(sk, r)}"><g clip-path="url(#adult-blouse-sleeve-${tag})">${clothFill}</g><g clip-path="url(#adult-blouse-cap-${tag})"><g clip-path="url(#adult-blouse-cap-body-${tag})">${clothFill}</g></g><g clip-path="url(#adult-blouse-sleeve-edge-${tag})">${clothEdge}</g>${inkLine}${rim}` +
        `<g clip-path="url(#adult-blouse-clip)">${open(side(ADULT_BLOUSE_LINES.gather, r.sign))}</g></g>`
      );
    })
    .join("");
  return shape + body + sleeves;
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
  if (p.outfit.skirt_cut === "pleated") return adultPleatedSkirt(sk, colorStr(p.outfit.skirt_color));
  return `<path d="${chainPath(sk, ADULT_SKIRT)}" ${inkAttrs(sk, colorStr(p.outfit.skirt_color))} />`;
}

/**
 * The pleated skirt (`skirt_cut` "pleated"): the flare with its slanted hem, traced from the uniform of ref/risa-adult/ (body-adult-skirt-pleated-data.ts, docs/risa-adult-plan.md),
 * one flat colour, the pleats as thin fold lines in a dark tone of it from the waistband's lower edge to the hem, and that edge as one continuous line across (its top shifted down by the band's depth) (the darker strip beside each fold in the reference is left out). Its top is
 * hidden under whatever is worn over it.
 */
function adultPleatedSkirt(sk: Skeleton, color: string): string {
  const { cx, y, w } = place(sk);
  // The skirt is traced on Risa's reference, whose hips are narrower than this body's (the briefs 339 px wide against 355 in our render), so the traced edge can fall inside the body's own
  // side and leave skin and the briefs' wing showing beside it. Wherever it does, the whole skirt is widened there: a point moves out by the shortfall of the edge at its depth, in
  // proportion to how near it is to that edge (so the top's curve and the folds keep their shape and the edge reaches the body's outer edge, the knots being the ink's outer edge, so
  // the skirt's centre line goes on them and its stroke covers the body's). It eases off between 2.0 and 2.3 H below the chin, where the thigh is wider than the skirt's flare.
  const inkHalf = outlineW(strokeW(sk)) / 2; // half a stroke of margin, so the skirt's line covers the body's
  const map = (q: Pt): Pt => {
    const edge = skirtEdgeAt(q[1], Math.sign(q[0]));
    const shortfall = edge === null ? 0 : Math.max(0, w(q[1], at(SIDE, q[1])) + inkHalf - Math.abs(w(q[1], edge)));
    const over = 1 - ease((q[1] - 2.0) / 0.3);
    const near = edge === null ? 0 : Math.min(1, Math.abs(q[0]) / edge);
    return [cx + w(q[1], q[0]) + Math.sign(q[0]) * over * shortfall * near, y(q[1])];
  };
  const [start, segs] = ADULT_PLEATED_SKIRT;
  const s0 = map(start);
  const outline = `M ${fmt1(s0[0])} ${fmt1(s0[1])} ` + segs.map(([c, e]) => quad(map(c), map(e))).join("") + "Z";
  const open = ([a, rest]: Chain): string => {
    const p0 = map(a);
    return `<path d="M ${fmt1(p0[0])} ${fmt1(p0[1])} ${rest.map(([c, e]) => quad(map(c), map(e))).join("")}" fill="none" stroke="${shade(color, 0.42, 1.0)}" stroke-width="${fmt2(outlineW(strokeW(sk), 0.5))}" stroke-linecap="round" />`;
  };
  return `<path d="${outline}" ${inkAttrs(sk, color)} />${[...ADULT_PLEATED_FOLDS, ADULT_PLEATED_BAND].map(open).join("")}`;
}

/** The traced skirt's half-width in head heights at a depth on one side (-1 the viewer's left; the traced skirt is not centred on the body, as the reference's is not): the widest point of its outline within 0.012 H of it (the outline flares by 0.4 H of width per H of depth, so a wider window reads the edge as wider than it is there), null where the outline has none. */
let pleatedEdge: readonly (readonly [number, number])[] | null = null;
function skirtEdgeAt(d: number, side: number): number | null {
  if (pleatedEdge === null) {
    const out: [number, number][] = [];
    let p0: Pt = ADULT_PLEATED_SKIRT[0];
    for (const [c, e] of ADULT_PLEATED_SKIRT[1]) {
      for (let i = 1; i <= 16; i++) {
        const t = i / 16;
        out.push([(1 - t) * (1 - t) * p0[1] + 2 * (1 - t) * t * c[1] + t * t * e[1], (1 - t) * (1 - t) * p0[0] + 2 * (1 - t) * t * c[0] + t * t * e[0]]);
      }
      p0 = e;
    }
    pleatedEdge = out;
  }
  let best: number | null = null;
  for (const [dd, xs] of pleatedEdge) {
    const x = side * xs; // the half-width on this side, negative where the outline is on the other
    if (Math.abs(dd - d) <= 0.012 && x > 0 && (best === null || x > best)) best = x;
  }
  return best;
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
export function adultBodiceCloth(sk: Skeleton, color: string, hem: number | null = null, filled: readonly number[] = []): string {
  const { cx, y, w } = place(sk);
  const ink = outlineW(strokeW(sk));
  const d = chainPath(sk, ADULT_BODICE);
  // On a side whose arm is raised the bodice's nip at the waist (a step, then the hem flare) is not hidden by the arm and reads as a notch; the pack's bodice runs straight down there. That side is
  // filled out: bodice colour from the bust's widest point down to the cut, bounded by a gentle curve, which is inked, over the bodice's own outline.
  const fillOut = filled
    .map((sign) => {
      const P = ([v, dd]: readonly [number, number]): Pt => [cx + sign * w(dd, v), y(dd)];
      const edge = BODICE_FILL.map(P);
      const inner = [P([0.3, BODICE_FILL[BODICE_FILL.length - 1]![1]]), P([0.3, BODICE_FILL[0]![1]])];
      const head = (q: Pt): string => `${fmt1(q[0])} ${fmt1(q[1])}`;
      return (
        `<path d="M ${head(edge[0] as Pt)} ${smooth(edge)}L ${head(inner[0] as Pt)} L ${head(inner[1] as Pt)} Z" fill="${colorStr(color)}" stroke="none" />` +
        `<path d="M ${head(edge[0] as Pt)} ${smooth(edge)}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(ink)}" stroke-linecap="round" stroke-linejoin="round" />`
      );
    })
    .join("");
  const body = `<path d="${d}" ${inkAttrs(sk, colorStr(color))} />${fillOut}`;
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
 * A blouse is tucked in when the outfit says so (`tunic_tucked`), or a skirt, hakama or a bodice is worn (a bodice ends above the blouse's hem) (the skirt is drawn before the chest layers, so an untucked blouse would lay its hem over it and show as
 * white strips along the apron's edge, the owner). A tucked blouse is drawn in the legs' layer, after the briefs and before the shorts or the skirt, which then cover its lower part; an untucked
 * one is in the chest layers, over everything below the waist (as in ref 02, the blouse over the shorts).
 */
const tucked = (p: CharacterParams): boolean => p.outfit.tunic_color !== null && (truthy(p.outfit.tunic_tucked) || p.outfit.skirt_color !== null || p.outfit.bodice_color !== null || p.outfit.hakama_color !== null);

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
  const ds = depths(SOCK_TOP, FOOT_D_CUT, 0.1);
  const leg = (sign: number): string => {
    // The sock's ink edge lies on the leg's own (the knots are the leg's outer ink edge, and its path sits half a stroke inside them), a fifth of a pixel proud of it (about one pixel of the 1312-wide reference grid) so the skin's line is covered: the path
    // is half a stroke inside the knots on the outer side and half a stroke outside them on the inner, as the body's is. (It stood `m` off the knots, so with its own stroke it overhung by about six pixels a side.)
    const hs = ink / 2;
    const outer = ds.map((d) => [cx + sign * (w(d, at(LEG_OUTER, d)) - hs + 0.2), y(d)] as Pt);
    const inner = ds.map((d) => [cx + sign * (w(d, Math.max(0.02, at(LEG_IN, d))) + hs - 0.2), y(d)] as Pt).reverse();
    const first = outer[0] as Pt;
    // With loafers the sock is the school's (the references' 02 and 03): its top edge dips at the front in one curve (0.07 H deep, as in the references), there is no band line, and its lower end is open
    // (it goes into the shoe), so only its two sides and its top edge are inked.
    const school = p.outfit.boot_cut === "loafer";
    const innerTop = inner[inner.length - 1] as Pt;
    const sag = 0.07 * 2 * sk.head_r;
    const closing = school ? `Q ${fmt1((first[0] + innerTop[0]) / 2)} ${fmt1(first[1] + 2 * sag)} ${fmt1(first[0])} ${fmt1(first[1])} ` : "";
    // The school sock goes on down into the shoe (whose opening shows it), and its lower sides are the reference's: in 08 (the legs close-up) the sock narrows to about 0.62 of the shoe's width where it
    // enters it and runs straight down inside the counters. So from 4.0 H, where the leg's own edges are, down to the shoe's top the edges ease (smoothstep) from the leg's to that width about the shoe's
    // centre, then run on to a third of the way into the shoe, where they are hidden. (They used to follow the foot's outline, which stepped at the ankle where the leg's tables end and was wider than the
    // shoe's counters.)
    let outerS: Pt[] = outer;
    let innerTD: Pt[] = [...inner].reverse(); // top to bottom
    if (school && p.outfit.boot_color !== null) {
      const fit = loaferFit(shoeFoot(sk, sign));
      const yA = y(4.0);
      const yEnd = y(FOOT_D_CUT);
      const yCut = fit.top + 0.3 * fit.length;
      const legX = (yy: number, outerSide: boolean): number => {
        const d = Math.min(FOOT_D_CUT, Math.max(4.0, 4.0 + ((yy - yA) / (yEnd - yA)) * (FOOT_D_CUT - 4.0)));
        return outerSide ? cx + sign * (w(d, at(LEG_OUTER, d)) - hs + 0.2) : cx + sign * (w(d, Math.max(0.02, at(LEG_IN, d))) + hs - 0.2);
      };
      const tOuter = fit.xc + sign * 0.33 * fit.width;
      const tInner = fit.xc - sign * 0.33 * fit.width;
      const rows: number[] = [];
      for (let i = 0; i <= 12; i++) rows.push(yA + ((yCut - yA) * i) / 12);
      const low = (outerSide: boolean): Pt[] =>
        rows.map((yy): Pt => {
          const t = Math.min(1, Math.max(0, (yy - yA) / (fit.top - yA)));
          const k = t * t * (3 - 2 * t);
          const target = outerSide ? tOuter : tInner;
          return [legX(yy, outerSide) * (1 - k) + target * k, yy];
        });
      outerS = [...outer.filter((q) => q[1] < yA - 1e-6), ...low(true)];
      innerTD = [...innerTD.filter((q) => q[1] < yA - 1e-6), ...low(false)];
    }
    const innerLast = innerTD[innerTD.length - 1] as Pt;
    const innerUp = [...innerTD].reverse();
    const path = `M ${fmt1(first[0])} ${fmt1(first[1])} ${smooth(outerS)}L ${fmt1(innerLast[0])} ${fmt1(innerLast[1])} ${smooth(innerUp)}${closing}Z`;
    const schoolInk = school
      ? `<path d="M ${fmt1(first[0])} ${fmt1(first[1])} ${smooth(outerS)}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(ink)}" stroke-linejoin="round" stroke-linecap="round" />` +
        `<path d="M ${fmt1(innerLast[0])} ${fmt1(innerLast[1])} ${smooth(innerUp)}${closing}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(ink)}" stroke-linejoin="round" stroke-linecap="round" />`
      : "";
    const bandD = SOCK_TOP + 0.05;
    const a: Pt = [cx + sign * (w(bandD, at(LEG_OUTER, bandD)) - hs + 0.2), y(bandD)];
    const b: Pt = [cx + sign * (w(bandD, Math.max(0.02, at(LEG_IN, bandD))) + hs - 0.2), y(bandD)];
    const band = `<path d="M ${fmt1(a[0])} ${fmt1(a[1])} L ${fmt1(b[0])} ${fmt1(b[1])}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(ink * 0.67)}" stroke-linecap="round" />`;
    if (school) return `<path d="${path}" fill="${colorStr(p.outfit.knee_sock_color as string)}" />${schoolInk}`;
    return `<path d="${path}" ${inkAttrs(sk, colorStr(p.outfit.knee_sock_color as string))} />${band}`;
  };
  return leg(-1) + leg(1);
}

/**
 * Boots on `boot_color`: each foot and the leg above it, out to the knee as `boot_shaft` says (0 an ankle boot, 1 to the knee), cut from the leg's tables and the traced foot's outline, a
 * little off the skin, with a thicker sole. `boot_cut` "loafer" is a low shoe, the foot alone. A flat garment in one colour; its cuff is a line. The foot's toes and nails are not drawn
 * under it (body-adult-parts.ts, `adultDetail`).
 */
/** The shoe's last for one foot: the foot outline's convex hull in the chain's order (outer edge, toes, inner edge), smoothed and stood off the skin's ink edge, as the boots draw it. */
function shoeFoot(sk: Skeleton, sign: number): Pt[] {
  const { cx, y, w } = place(sk);
  const ink = outlineW(strokeW(sk));
  const unit = 2 * sk.head_r;
  const off = ink / 2 + 0.014 * unit;
  const sole = 0.012 * unit;
  const P = (v: number, d: number): Pt => [cx + sign * w(d, v), y(d)];
  const chain = smoothed(densify(hullInOrder(sampleChain(FOOT_OUTLINE, 5).map(([v, d]) => P(v, d))), 3), 4);
  return chain.map((q, i) => {
    const a = chain[Math.max(0, i - 1)] as Pt;
    const b = chain[Math.min(chain.length - 1, i + 1)] as Pt;
    const tx = b[0] - a[0];
    const ty = b[1] - a[1];
    const len = Math.hypot(tx, ty) || 1;
    const nx = (sign * ty) / len;
    const ny = (-sign * tx) / len;
    const k = off + (ny > 0.5 ? sole * ny : 0);
    return [q[0] + nx * k, q[1] + ny * k] as Pt;
  });
}

/**
 * The school loafer, traced from the legs close-up of ref/risa-adult/08-legs-closeup.png (body-adult-loafer-data.ts) in its own coordinates and fitted to this body's foot, not placed by registration:
 * Grok drew the legs of the uniform images much shorter than the body's, so the shoe is the reference's shape (a length of 1.6 widths) as wide as the foot, its toe at the foot's toe, and the foot's
 * instep above it is the sock's (`schoolSockLength`), which shows through the notch in the shoe's top. The shoe is one silhouette with that notch, a darker sole band, the strap with its slot, and the seam
 * round the oval below it. The right shoe is the left's mirror.
 */
interface LoaferFit {
  readonly xc: number;
  readonly width: number;
  readonly top: number;
  readonly length: number;
}

function loaferFit(foot: readonly Pt[]): LoaferFit {
  const xs = foot.map((q) => q[0]);
  const ys = foot.map((q) => q[1]);
  const width = (Math.max(...xs) - Math.min(...xs)) * 1.05;
  const length = width * LOAFER_ASPECT;
  const bottom = Math.max(...ys) + 0.012 * (Math.max(...ys) - Math.min(...ys));
  return { xc: (Math.max(...xs) + Math.min(...xs)) / 2, width, top: bottom - length, length };
}

/** The shoe's silhouette and the lines on it for the foot `foot`, `sign` -1 the viewer's left (the traced shoe) and 1 its mirror. */
function loaferShoe(sk: Skeleton, p: CharacterParams, sign: number, foot: readonly Pt[]): string {
  const fit = loaferFit(foot);
  const ink = outlineW(strokeW(sk));
  const brown = colorStr(p.outfit.boot_color as string);
  const at2 = ([u, t]: readonly [number, number]): Pt => [fit.xc + (sign < 0 ? u : -u) * fit.width, fit.top + t * fit.length];
  const chainD = ([start, segs]: Chain): string => {
    const s0 = at2(start);
    return `M ${fmt1(s0[0])} ${fmt1(s0[1])} ${segs.map(([c, e]) => quad(at2(c), at2(e))).join("")}Z`;
  };
  const poly = (pts: readonly (readonly [number, number])[], close = false): string => {
    const q = pts.map(at2);
    return `M ${fmt1((q[0] as Pt)[0])} ${fmt1((q[0] as Pt)[1])} ${smooth(q)}${close ? "Z" : ""}`;
  };
  const id = `adult-loafer-clip-${sign < 0 ? "l" : "r"}`;
  const outline = chainD(LOAFER_OUTLINE);
  const dark = shade(brown, 0.55, 1.0);
  const fine = `fill="none" stroke="${shade(brown, 0.4, 1.0)}" stroke-width="${fmt2(ink * 0.5)}" stroke-linecap="round" stroke-linejoin="round"`;
  const strap = `${poly(LOAFER_STRAP_TOP)} L ${fmt1(at2(LOAFER_STRAP_BOT[LOAFER_STRAP_BOT.length - 1] as readonly [number, number])[0])} ${fmt1(at2(LOAFER_STRAP_BOT[LOAFER_STRAP_BOT.length - 1] as readonly [number, number])[1])} ${smooth([...LOAFER_STRAP_BOT].reverse().map(at2))}Z`;
  const inside =
    `<path d="${poly(LOAFER_SOLE_EDGE)} L ${fmt1(at2([0.6, 1.2])[0])} ${fmt1(at2([0.6, 1.2])[1])} L ${fmt1(at2([-0.6, 1.2])[0])} ${fmt1(at2([-0.6, 1.2])[1])} Z" fill="${dark}" />` +
    `<path d="${poly(LOAFER_SEAM)}" ${fine} />` +
    `<path d="${strap}" fill="${tint(brown, 0.08)}" stroke="${OUTLINE}" stroke-width="${fmt2(ink * 0.55)}" stroke-linejoin="round" />` +
    `<path d="${poly(LOAFER_SLOT, true)}" fill="${shade(brown, 0.3, 1.0)}" />`;
  return (
    `<clipPath id="${id}"><path d="${outline}" /></clipPath>` +
    `<path d="${outline}" fill="${brown}" />` +
    `<g clip-path="url(#${id})">${inside}</g>` +
    `<path d="${outline}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(ink)}" stroke-linejoin="round" />`
  );
}

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
    const foot = shoeFoot(sk, sign);
    // the foot's offset ends are on the leg's offset edges at the ankle cut; the shoe's own top edge is straight across
    const run: Pt[] = [...outer, ...foot, ...inner];
    const first = run[0] as Pt;
    const path = `M ${fmt1(first[0])} ${fmt1(first[1])} ${smooth(run)}Z`;
    const cuffD = top + 0.045;
    const cuff = loafer
      ? ""
      : `<path d="M ${fmt1(P(at(LEG_OUTER, cuffD) + mLeg, cuffD)[0])} ${fmt1(y(cuffD))} L ${fmt1(P(Math.max(0.02, at(LEG_IN, cuffD) - mLeg), cuffD)[0])} ${fmt1(y(cuffD))}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(ink * 0.67)}" stroke-linecap="round" />`;
    if (loafer) return loaferShoe(sk, p, sign, foot);
    return `<path d="${path}" ${inkAttrs(sk, colorStr(p.outfit.boot_color as string))} />${cuff}`;
  };
  return boot(-1) + boot(1);
}

// ---- belt, pouches, crystals, coat and robe, cut from the torso's tables

/** Where the belt sits: the top of the band, in head heights below the chin (her waist is the narrowest part of the torso, 1.3), and the height of one unit of `belt_scale`. */
const BELT = { top: 1.26, unit: 0.075 } as const;

/** A closed path through `pts`, smooth, as the garments' tables give them. */
const closed = (pts: readonly Pt[]): string => `M ${fmt1((pts[0] as Pt)[0])} ${fmt1((pts[0] as Pt)[1])} ${smooth(pts)}Z`;

/** The band's depths from `d0` to `d1`, every `step`, and `d1`. */
const dsBand = (d0: number, d1: number, step = 0.03): number[] => depths(d0, d1, step);

/** The belt's top and bottom depths at its height `scale` (1 is a belt, 3 an obi). */
const beltBand = (scale: number): [number, number] => [BELT.top, BELT.top + BELT.unit * Math.max(0.5, scale)];

/**
 * A belt on `belt_color`: a band round the waist cut from the torso's side table, a shade outside the skin, its top and bottom edges dipping a little toward the front, with a
 * buckle (a frame and a plate). `belt_scale` is its height. Over a coat it is drawn after the coat (`adultCoat`), so the coat is cinched by it.
 */
export function adultBeltBand(sk: Skeleton, p: CharacterParams): string {
  const color = p.outfit.belt_color;
  if (color === null) return "";
  const { cx, y, w } = place(sk);
  const ink = outlineW(strokeW(sk));
  const [d0, d1] = beltBand(Number(p.outfit.belt_scale));
  const out = (s: number, d: number): Pt => [cx + s * w(d, at(SIDE, d) + 0.014), y(d)];
  const dip = 0.012 * 2 * sk.head_r;
  const ds = dsBand(d0, d1);
  const left = ds.map((d) => out(-1, d));
  const right = ds.map((d) => out(1, d));
  const path =
    `M ${fmt1((left[0] as Pt)[0])} ${fmt1((left[0] as Pt)[1])} ` +
    quad([cx, (left[0] as Pt)[1] + 2 * dip], right[0] as Pt) +
    smooth(right) +
    quad([cx, (right[right.length - 1] as Pt)[1] + 2 * dip], left[left.length - 1] as Pt) +
    smooth([...left].reverse()) +
    "Z";
  const mid = y((d0 + d1) / 2) + dip;
  const h = y(d1) - y(d0);
  const bw = Math.max(h * 1.5, 0.075 * 2 * sk.head_r);
  const bh = h * 0.78;
  const plate = `<rect x="${fmt1(cx - bw / 2)}" y="${fmt1(mid - bh / 2)}" width="${fmt1(bw)}" height="${fmt1(bh)}" rx="${fmt1(bh * 0.18)}" fill="#8a8578" stroke="${OUTLINE}" stroke-width="${fmt2(ink * 0.67)}" />`;
  const inner = `<rect x="${fmt1(cx - bw * 0.3)}" y="${fmt1(mid - bh * 0.28)}" width="${fmt1(bw * 0.6)}" height="${fmt1(bh * 0.56)}" rx="${fmt1(bh * 0.1)}" fill="${shade(colorStr(color), 0.6, 1.0)}" stroke="${OUTLINE}" stroke-width="${fmt2(ink * 0.45)}" />`;
  return `<path d="${path}" ${inkAttrs(sk, colorStr(color))} />${plate}${inner}`;
}

/** A pouch on each hip on `pouch_color`, hanging from the belt: body, flap and button, as the chibi's, sized off the head and set on the hip's side. Needs a belt. */
export function adultPouches(sk: Skeleton, p: CharacterParams): string {
  const color = p.outfit.pouch_color;
  if (color === null || p.outfit.belt_color === null) return "";
  const { cx, y, w } = place(sk);
  const ink = outlineW(strokeW(sk));
  const [, d1] = beltBand(Number(p.outfit.belt_scale));
  const U = 2 * sk.head_r;
  const pw = 0.085 * U;
  const ph = 0.12 * U;
  const top = y(d1) - 0.01 * U;
  const r = pw * 0.18;
  const fill = colorStr(color);
  let out = "";
  for (const side of [-1, 1]) {
    const x = cx + side * w(d1, 0.31) - pw / 2;
    const flap = ph * 0.44;
    out +=
      `<rect x="${fmt1(x)}" y="${fmt1(top)}" width="${fmt1(pw)}" height="${fmt1(ph)}" rx="${fmt1(r)}" fill="${fill}" stroke="${OUTLINE}" stroke-width="${fmt2(ink * 0.85)}" />` +
      `<rect x="${fmt1(x)}" y="${fmt1(top)}" width="${fmt1(pw)}" height="${fmt1(flap)}" rx="${fmt1(r)}" fill="${shade(fill, 0.82, 1.0)}" stroke="${OUTLINE}" stroke-width="${fmt2(ink * 0.85)}" />` +
      `<circle cx="${fmt1(x + pw / 2)}" cy="${fmt1(top + flap)}" r="${fmt1(pw * 0.1)}" fill="${shade(fill, 0.5, 1.0)}" />`;
  }
  return out;
}

/** The four crystals' distances from the centre line, outer to inner, in head heights: two a side with the buckle between the middle pair. */
const CRYSTAL_V: readonly [number, number, number, number] = [-0.215, -0.115, 0.115, 0.215];

/** Up to four faceted gems clipped along the belt, two a side, with the tongs hanging from the outer right one: the chibi's rig on the adult belt. Needs a belt. */
export function adultCrystals(sk: Skeleton, p: CharacterParams): string {
  const colors = [p.outfit.crystal_color_1, p.outfit.crystal_color_2, p.outfit.crystal_color_3, p.outfit.crystal_color_4];
  const beltColor = p.outfit.belt_color;
  if (beltColor === null || colors.every((c) => c === null)) return "";
  const { cx, y } = place(sk);
  const ink = outlineW(strokeW(sk));
  const U = 2 * sk.head_r;
  const [d0, d1] = beltBand(Number(p.outfit.belt_scale));
  const bandCy = (y(d0) + y(d1)) / 2;
  const h = 0.12 * U;
  const gw = h * 0.58;
  let out = "";
  CRYSTAL_V.forEach((v, i) => {
    const color = colors[i] as string | null;
    if (color === null) return;
    const gx = cx + v * U;
    const top: Pt = [gx, bandCy - h / 2];
    const right: Pt = [gx + gw / 2, bandCy - h * 0.08];
    const bottom: Pt = [gx, bandCy + h / 2];
    const left: Pt = [gx - gw / 2, bandCy - h * 0.08];
    const fill = colorStr(color);
    out += `<path d="M ${fmt1(top[0])} ${fmt1(top[1])} L ${fmt1(right[0])} ${fmt1(right[1])} L ${fmt1(bottom[0])} ${fmt1(bottom[1])} L ${fmt1(left[0])} ${fmt1(left[1])} Z" fill="${fill}" stroke="${OUTLINE}" stroke-width="${fmt2(ink * 0.8)}" stroke-linejoin="round" />`;
    out += `<line x1="${fmt1(top[0])}" y1="${fmt1(top[1])}" x2="${fmt1(bottom[0])}" y2="${fmt1(bottom[1])}" stroke="${shade(fill, 0.6, 1.0)}" stroke-width="${fmt2(ink * 0.5)}" />`;
    const strapH = h * 0.24;
    const strapW = gw * 1.22;
    out += `<rect x="${fmt1(gx - strapW / 2)}" y="${fmt1(bandCy - h * 0.08 - strapH / 2)}" width="${fmt1(strapW)}" height="${fmt1(strapH)}" fill="${colorStr(beltColor)}" stroke="${OUTLINE}" stroke-width="${fmt2(ink * 0.6)}" />`;
  });
  if (truthy(p.outfit.crystal_tongs)) {
    const tx = cx + (CRYSTAL_V[3] as number) * U;
    const ty = bandCy + h * 1.05;
    const arm = h * 0.75;
    out +=
      `<line x1="${fmt1(tx - arm * 0.22)}" y1="${fmt1(ty - arm * 0.55)}" x2="${fmt1(tx + arm * 0.28)}" y2="${fmt1(ty + arm * 0.55)}" stroke="#8a8578" stroke-width="${fmt2(ink * 0.7)}" stroke-linecap="round" />` +
      `<line x1="${fmt1(tx + arm * 0.22)}" y1="${fmt1(ty - arm * 0.55)}" x2="${fmt1(tx - arm * 0.28)}" y2="${fmt1(ty + arm * 0.55)}" stroke="#8a8578" stroke-width="${fmt2(ink * 0.7)}" stroke-linecap="round" />` +
      `<circle cx="${fmt1(tx)}" cy="${fmt1(ty)}" r="${fmt1(ink * 0.6)}" fill="#6b665c" />`;
  }
  return out;
}

/** The coat's hem, in head heights below the chin, for `coat_length` (0.2 a vest to just under the bust, 0.85 to the shin). */
const coatHem = (length: number): number => 0.4 + 4.3 * Math.min(0.85, Math.max(0.2, Number(length)));

/** The front edge's distance from the centre line at a depth: close at the throat, pushed aside by the bust, closing toward the hem, widening again as the coat hangs. Each [d, v]. */
const COAT_FRONT: Knots = [[0.5, 0.09], [0.8, 0.14], [1.0, 0.19], [1.2, 0.205], [1.45, 0.16], [1.9, 0.13], [3.0, 0.15], [4.5, 0.17]];

/**
 * An open coat on `coat_color`: two panels cut from the torso's tables, hanging from the shoulders (the armhole follows the blouse's sleeve seam, so the arms stay bare or
 * keep their sleeves), the outer edges following her waist and hip and flaring a little toward the hem, the front edges parting round the bust with the breasts' lines
 * showing on the cloth. `coat_length` sets the hem. A flat garment in one colour. The belt is drawn over it.
 */
export function adultCoat(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.coat_color === null) return "";
  if (wearsBlazer(p)) return adultBlazer(sk, p);
  const { cx, y, w } = place(sk);
  const ink = outlineW(strokeW(sk));
  const hem = coatHem(p.outfit.coat_length);
  const color = colorStr(p.outfit.coat_color);
  // the seam's top is the blouse's strap beside the neck; the coat's shoulder starts where the seam meets the shoulder's slope
  const seam = [[0.424, 0.26] as const, ...ADULT_BLOUSE_LINES.seam.filter(([, d]) => d > 0.3 && d <= 1.096)];
  const flare = (d: number): number => 0.014 + 0.06 * ease((d - 1.3) / Math.max(0.5, hem - 1.3));
  const panel = (s: number): string => {
    const P = (v: number, d: number): Pt => [cx + s * w(d, v), y(d)];
    const dsSide: number[] = [];
    for (let d = 1.15; d < hem - 1e-9; d += 0.06) dsSide.push(d);
    dsSide.push(hem);
    const shoulder = seam.map(([v, d]) => P(v, d));
    const side = dsSide.map((d) => P(at(SIDE, d) + flare(d), d));
    const dsFront: number[] = [];
    for (let d = hem; d > 0.5 + 1e-9; d -= 0.08) dsFront.push(d);
    dsFront.push(0.5);
    const front = dsFront.map((d) => P(at(COAT_FRONT, d), d));
    const collar = [P(0.125, 0.32), P(0.165, 0.18), P(0.3, 0.205)];
    const top = shoulder[0] as Pt;
    return (
      `M ${fmt1(top[0])} ${fmt1(top[1])} ` +
      smooth(shoulder) +
      smooth(side) +
      `L ${fmt1((front[0] as Pt)[0])} ${fmt1((front[0] as Pt)[1])} ` +
      smooth(front) +
      collar.map((q) => `L ${fmt1(q[0])} ${fmt1(q[1])} `).join("") +
      "Z"
    );
  };
  const left = panel(-1);
  const right = panel(1);
  const clip = `<clipPath id="adult-coat-clip"><path d="${left}" /><path d="${right}" /></clipPath>`;
  const bust = adultBustLine(sk, DEFAULT_TAPER, shade(color, 0.8, 1.0), 0.7);
  return (
    `<path d="${left}" ${inkAttrs(sk, color)} /><path d="${right}" ${inkAttrs(sk, color)} />${clip}<g clip-path="url(#adult-coat-clip)">${bust}</g>` +
    adultBeltBand(sk, p)
  );
}

/** Where the robe's front ends (just under the belt's band), the depth of the V's tip, and the shoulder's slope from the seam out to the arm. Head heights below the chin. */
const ROBE = { hem: 1.56, tip: 0.82, tipV: 0.04 } as const;
const SHOULDER_SLOPE: Knots = [[0.424, 0.26], [0.5, 0.26], [0.571, 0.27], [0.615, 0.35], [0.634, 0.46]];

/**
 * A robe on `robe_color`, kimono style: the torso's cloth from the shoulders to just under the belt, cut from the side and seam tables, with a V-necked front (the two collars meet at a
 * point a little right of centre) and the fold of the lapel running from that point down to her right hip. With `sleeve_drop` above 0 each arm gets a hanging sleeve: a bag of cloth
 * from the shoulder, the outer edge standing off the arm, the arm coming out of its hem. One flat colour.
 */
export function adultRobe(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.robe_color === null) return "";
  const { cx, y, w } = place(sk);
  const ink = outlineW(strokeW(sk));
  const color = colorStr(p.outfit.robe_color);
  const P = (s: number) => (v: number, d: number): Pt => [cx + s * w(d, v), y(d)];
  const seam = ADULT_BLOUSE_LINES.seam.filter(([, d]) => d > 0.3 && d <= 1.096);
  const sideDs: number[] = [];
  for (let d = 1.15; d < ROBE.hem - 1e-9; d += 0.06) sideDs.push(d);
  sideDs.push(ROBE.hem);
  const sideV = (d: number): number => at(SIDE, d) + 0.016;
  const dip = 0.012 * 2 * sk.head_r;
  const pl = P(-1);
  const pr = P(1);
  // the torso panel, clockwise from the left shoulder: along the shoulders, down the right side, across the hem, up the left side, and the V
  const rightSide = [pr(0.424, 0.26), ...seam.map(([v, d]) => pr(v, d)), ...sideDs.map((d) => pr(sideV(d), d))];
  const leftSide = [...sideDs.map((d) => pl(sideV(d), d)).reverse(), ...seam.map(([v, d]) => pl(v, d)).reverse(), pl(0.424, 0.26)];
  const tip: Pt = [cx + w(ROBE.tip, ROBE.tipV), y(ROBE.tip)];
  const collarR = pr(0.16, 0.17);
  const collarL = pl(0.16, 0.17);
  const hemR = rightSide[rightSide.length - 1] as Pt;
  const hemL = leftSide[0] as Pt;
  const d =
    `M ${fmt1(collarL[0])} ${fmt1(collarL[1])} L ${fmt1(tip[0])} ${fmt1(tip[1])} L ${fmt1(collarR[0])} ${fmt1(collarR[1])} ` +
    `L ${fmt1((rightSide[0] as Pt)[0])} ${fmt1((rightSide[0] as Pt)[1])} ` +
    smooth(rightSide) +
    quad([cx, hemR[1] + 2 * dip], hemL) +
    smooth(leftSide) +
    "Z";
  // the lapel's fold: from the V's tip to the hem at her right hip, lighter than the outline
  const foldEnd = pr(0.3, ROBE.hem - 0.04);
  const fold = `<path d="M ${fmt1(tip[0])} ${fmt1(tip[1])} L ${fmt1(foldEnd[0])} ${fmt1(foldEnd[1])}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(ink * 0.67)}" stroke-linecap="round" />`;
  // hanging sleeves
  const drop = Math.max(0, Math.min(1, Number(p.outfit.sleeve_drop)));
  let sleeves = "";
  if (drop > 0) {
    const hemD = 0.9 + 1.8 * drop;
    const r = 0.05;
    for (const s of [-1, 1]) {
      const Q = P(s);
      const top = SHOULDER_SLOPE.map(([v, dd]) => Q(v, dd));
      // wide enough to cover a blouse's puffs (0.75 out at 0.9 below the chin), then standing off the arm
      const outerV = (dd: number): number => (dd < 0.95 ? 0.634 + 0.15 * ease((dd - 0.4) / 0.55) : Math.max(0.78, at(ARM_OUTER, dd) + 0.09));
      const outerDs: number[] = [];
      for (let dd = 0.55; dd < hemD - r; dd += 0.08) outerDs.push(dd);
      const out = outerDs.map((dd) => Q(outerV(dd), dd));
      const corner = Q(outerV(hemD), hemD);
      const cornerEnd = Q(outerV(hemD) - r, hemD);
      const inner = [...ADULT_BLOUSE_LINES.seam.filter(([, dd]) => dd > 0.5 && dd <= 1.096).map(([v, dd]) => Q(v, dd)), ...outerDs.filter((dd) => dd >= 1.15).map((dd) => Q(at(ARM_INNER, dd) - 0.01, dd))];
      const hemI = Q(at(ARM_INNER, hemD) - 0.01, hemD);
      const path =
        `M ${fmt1((top[0] as Pt)[0])} ${fmt1((top[0] as Pt)[1])} ` +
        smooth(top) +
        smooth(out) +
        quad(corner, cornerEnd) +
        `L ${fmt1(hemI[0])} ${fmt1(hemI[1])} ` +
        smooth([...inner, hemI].reverse()) +
        "Z";
      sleeves += `<path d="${path}" ${inkAttrs(sk, color)} />`;
    }
  }
  return `<path d="${d}" ${inkAttrs(sk, color)} />${fold}${sleeves}`;
}

/**
 * Hakama on `hakama_color`: wide trousers from under the belt to `hakama_length` (0 at the hip, 1 at the ankle): the waist's width, flaring over the hips and out to a wide hem, with
 * the pleats' lines fanning from the waist to where the panel turns under. One flat colour. The arms are drawn over it, as over a skirt.
 */
export function adultHakama(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.hakama_color === null) return "";
  const { cx, y, w } = place(sk);
  const color = colorStr(p.outfit.hakama_color);
  const top = 1.4;
  const len = p.outfit.hakama_length;
  const hem = len === null ? 3.0 : 2.2 + (FOOT_D_CUT - 2.2) * Math.min(1, Math.max(0, Number(len)));
  const vTop = at(SIDE, top) + 0.008;
  const vHem = Math.max(at(SIDE, hem) + 0.14, 0.72);
  // the cloth clears the hip, and the curve over it is smoothed so it does not follow every wobble of the body's edge
  const raw = (d: number): number => Math.max(at(SIDE, d) + 0.035, vTop + (vHem - vTop) * Math.pow((d - top) / (hem - top), 0.85));
  const grid: number[] = [];
  for (let d = top; d < hem + 1e-9; d += 0.04) grid.push(d);
  let vs = grid.map(raw);
  for (let pass = 0; pass < 3; pass++) {
    const prev = vs;
    vs = prev.map((_, i) => {
      const near = prev.slice(Math.max(0, i - 4), i + 5);
      return near.reduce((a, b) => a + b, 0) / near.length;
    });
  }
  const edge = (d: number): number => Math.max(at(SIDE, d) + 0.025, at(grid.map((g, i) => [g, vs[i] as number] as const), d));
  const ds: number[] = [];
  for (let d = top; d < hem - 0.08; d += 0.08) ds.push(d);
  const P = (s: number) => (v: number, d: number): Pt => [cx + s * w(d, v), y(d)];
  const right = ds.map((d) => P(1)(edge(d), d));
  const left = ds.map((d) => P(-1)(edge(d), d)).reverse();
  const r = 0.07 * 2 * sk.head_r;
  const sag = 0.012 * 2 * sk.head_r;
  const topL = P(-1)(edge(top), top);
  const hl = P(-1)(edge(hem - 0.08), hem - 0.08);
  const cr = P(1)(edge(hem) + 0.01, hem);
  const cl = P(-1)(edge(hem) + 0.01, hem);
  const path =
    `M ${fmt1(topL[0])} ${fmt1(topL[1])} ` +
    quad([cx, topL[1] + 2 * sag], right[0] as Pt) +
    smooth(right) +
    quad(cr, [cr[0] - r, cr[1]]) +
    quad([cx, cr[1] + 2 * sag], [cl[0] + r, cl[1]]) +
    quad(cl, hl) +
    smooth(left) +
    "Z";
  const pleats = truthy(p.shaded)
    ? [-3, -2, -1, 0, 1, 2, 3]
        .map((i) => {
          const f = i / 3.5;
          const a: Pt = [cx + w(top, vTop) * f, y(top)];
          const bPt: Pt = [cx + w(hem - 0.1, edge(hem - 0.1)) * f, y(hem - 0.1)];
          return `<line x1="${fmt1(a[0])}" y1="${fmt1(a[1])}" x2="${fmt1(bPt[0])}" y2="${fmt1(bPt[1])}" stroke="${shade(color, 0.8, 1.08)}" stroke-width="${fmt2(outlineW(strokeW(sk)) * 0.4)}" opacity="0.75" />`;
        })
        .join("")
    : "";
  return `<path d="${path}" ${inkAttrs(sk, color)} />${pleats}`;
}

/**
 * A collar on `collar_color`: a band round her neck from under the jaw to just below the base of the throat, a little wider at the bottom where the neck meets the shoulders, its top
 * sagging under the chin; a standing collar has a notch at the front where the two halves meet. The traced cuts are the chibi's shapes and are not used.
 */
export function adultCollar(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.collar_color === null || wearsShirt(p)) return ""; // the school shirt has its own collar
  const { cx, y } = place(sk);
  const ink = outlineW(strokeW(sk));
  const nw = sk.neck_half_w;
  const top = y(0.0) + 0.01 * 2 * sk.head_r;
  const sag = y(0.0) + 0.045 * 2 * sk.head_r;
  const bottom = y(0.2);
  const hi = nw * 1.12;
  const lo = nw * 1.3;
  const fill = colorStr(p.outfit.collar_color);
  const d =
    `M ${fmt1(cx - hi)} ${fmt1(top)} Q ${fmt1(cx)} ${fmt1(top + 2 * (sag - top))} ${fmt1(cx + hi)} ${fmt1(top)} ` +
    `L ${fmt1(cx + lo)} ${fmt1(bottom)} L ${fmt1(cx - lo)} ${fmt1(bottom)} Z`;
  const notch = truthy(p.outfit.collar_mock) ? "" : `<path d="M ${fmt1(cx)} ${fmt1(sag)} L ${fmt1(cx)} ${fmt1(bottom)}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(ink * 0.67)}" stroke-linecap="round" />`;
  return `<path d="${d}" ${inkAttrs(sk, fill)} />${notch}`;
}

/** The bodice on `bodice_color`, cut at the sash or the skirt's top when one is worn. */
export function adultBodice(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.bodice_color === null) return "";
  const hem = p.outfit.apron_color !== null ? 1.34 : p.outfit.skirt_color !== null ? 1.315 : null;
  return adultBodiceCloth(sk, p.outfit.bodice_color, hem, raisedSides(p));
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
  _coat: adultCoat,
  _robe_front: adultRobe,
  _collar: adultCollar,
  // the shirt draws its own ribbon under its collar; on any other top the ribbon goes where the shared one does, on its own (the chibi's traced bow would sit wrong on this body)
  _ribbon: (sk: Skeleton, p: CharacterParams): string => (wearsShirt(p) ? "" : adultRibbon(sk, p)),
  _hakama: adultHakama,
  _hanging_sleeves: none,
  // the traced coat cuts are the chibi's shapes: on this body the coat is the one above, whatever `coat_cut` says
  _traced_coat_and_belt: none,
  _belt: (sk: Skeleton, p: CharacterParams): string => (p.outfit.coat_color !== null ? "" : adultBeltBand(sk, p)),
  _pouches: adultPouches,
  _crystal_harness: adultCrystals,
};
