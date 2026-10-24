// The adult woman's long-sleeved shirt (`collar_cut` "shirt" on a tunic): the school shirt of ref/risa-adult/06-blouse-bikini.png (docs/risa-adult-plan.md).
//
// The torso and the sleeves are not traced. The lesson of docs/risa-plan.md is to trace nothing below the chin off a reference whose body is not ours, so they are built from this body's own
// tables (the shoulder, the arm's two edges, the torso's side) with an ease, and so cover the body whatever its proportions. What the reference gives, because the body cannot, is traced
// (body-adult-shirt-data.ts): the collar, the hem with the V of its shirttails, the two lines of the button band and the buttons. The cuffs are a line across each sleeve.
//
// One closed outline in one flat colour: the neck's top, down the left sleeve's outer edge to the cuff, up its inner edge to the armpit, down the torso's side to the hem, along the hem to the
// other side, and up again. It is drawn in the legs' layer when tucked (the skirt then covers its lower part) and its sleeves are drawn again over the skirt, in front of it as the arms are.

import { OUTLINE, outlineW, strokeW } from "./character.ts";
import { colorStr } from "./body-parts-legs.ts";
import { ARM_INNER, ARM_OUTER, LEG_OUTER, SHOULDER_OUTER, TORSO_SIDE } from "./body-adult-data.ts";
import { ARM_OVER_HOOKS, DEFAULT_TAPER, adultNeck, RIB_KNOTS, adultBustLine, at, place, quad, smooth, type Knots, type Pt } from "./body-adult-parts.ts";
import { FOOT_D_CUT } from "./body-adult-foot-data.ts";
import { RIBBON_BACK, RIBBON_KNOT, RIBBON_LOOP, RIBBON_SLIT, RIBBON_TAIL, SHIRT_BUTTONS, SHIRT_COLLAR, SHIRT_HEM, SHIRT_NECK, SHIRT_PLACKET, SHIRT_STAND, SHIRT_STAND_BUTTON } from "./body-adult-shirt-data.ts";
import { adultArmPoses, raisedSides } from "./body-adult-pose.ts";
import { adultPosedSleeve } from "./body-adult-pose-arm.ts";
import { shade } from "./colorutil.ts";
import type { CharacterParams } from "./params.ts";
import { fmt1, fmt2 } from "./pynum.ts";
import { spacedDepths } from "./body-adult-build.ts";
import type { Skeleton } from "./skeleton.ts";

const SIDE: Knots = [...TORSO_SIDE, ...LEG_OUTER.filter(([d]) => d <= FOOT_D_CUT)];

/** How much roomier the shirt is than the body it covers, in head heights: over the shoulder, along the sleeve's outer edge, along its inner edge, and along the torso's side. */
const EASE_FREE = { shoulder: 0.02, outer: 0.035, inner: 0.025, torso: 0.02 } as const;
/** Under a blazer the shirt is the least roomier than the arm it covers, so its sleeve stays inside the blazer's (which cannot be narrower than the arm). */
const EASE_UNDER = { shoulder: 0.008, outer: 0.008, inner: 0.008, torso: 0.015 } as const;
type Ease = { readonly shoulder: number; readonly outer: number; readonly inner: number; readonly torso: number };
/** Whether a blazer is worn over the shirt (the same test as `wearsBlazer` in body-adult-blazer.ts, which imports this module). */
const underBlazer = (p: CharacterParams): boolean => p.outfit.coat_color !== null && p.outfit.coat_cut === "blazer";
/** How far a posed arm's shirt sleeve stands off the arm, in canvas units: the ease the shirt is cut with, the closer one under a blazer. */
export const shirtSleeveEase = (sk: Skeleton, p: CharacterParams): number => {
  const E = underBlazer(p) ? EASE_UNDER : EASE_FREE;
  return ((E.outer + E.inner) / 2) * 2 * sk.head_r;
};
const easeOf = (p: CharacterParams): Ease => (underBlazer(p) ? EASE_UNDER : EASE_FREE);
/** Where the cuff ends (the traced hand takes over at `HAND_D_CUT`, 2.0) and how tall the cuff's band is, in head heights. */
const CUFF_END = 2.0;
/** Where the blazer worn over the shirt ends its sleeve (head heights); the shirt's cuff shows below it. */
export const BLAZER_SLEEVE_END = 1.86;
const CUFF_BAND = 0.19;
/** Where the sleeve's inner edge meets the torso's side: the armpit, in head heights below the chin (the body's arm table begins at 1.1). */
const ARMPIT = 1.1;

/** Whether this character wears the school shirt on the adult body: a tunic with the shirt collar. */
export const wearsShirt = (p: CharacterParams): boolean => p.outfit.tunic_color !== null && p.outfit.collar_cut === "shirt";

const tableFrom = (tab: Knots, from: number, to: number): [number, number][] => {
  const out: [number, number][] = [];
  for (const [d, v] of tab) if (d >= from - 1e-9 && d <= to + 1e-9) out.push([d, v]);
  return out;
};

/** The shirt's pieces as paths and point lists, for one skeleton. */
function geometry(sk: Skeleton, EASE: Ease) {
  const { cx, y, w } = place(sk);
  const P = (s: number, v: number, d: number): Pt => [cx + s * w(d, v), y(d, v)];
  const outerKnots = (): [number, number][] => [
    [0.2, 0.2],
    [0.25, 0.4],
    ...tableFrom(SHOULDER_OUTER, 0.3, 0.9).map(([d, v]): [number, number] => [d, v + EASE.shoulder]),
    ...tableFrom(ARM_OUTER, 1.1, CUFF_END).map(([d, v]): [number, number] => [d, v + EASE.outer]),
  ];
  const outer = (s: number): Pt[] => outerKnots().map(([d, v]) => P(s, v, d));
  const inner = (s: number): Pt[] => tableFrom(ARM_INNER, ARMPIT, CUFF_END).map(([d, v]) => P(s, v - EASE.inner, d));
  // The hem's two ends are the torso's side at their depth (the reference's torso is narrower there than this body's, so the traced ends would stop short of the side and leave a notch).
  const hemD = (SHIRT_HEM[0] as Pt)[1];
  const hemDR = (SHIRT_HEM[SHIRT_HEM.length - 1] as Pt)[1];
  // The reference's corners are rounded where the side runs into the hem; the traced points just inside the corner are a flat step, which against this body's wider side is a ledge, so the
  // points within 0.005 H of an end's depth, past the end itself, are left out and the side runs into the curve.
  const traced = SHIRT_HEM.filter(([, d], i) => i === 0 || i === SHIRT_HEM.length - 1 || (Math.abs(d - hemD) > 0.005 && Math.abs(d - hemDR) > 0.005));
  const hem = traced.map(([v, d], i): Pt => {
    if (i === 0) return P(-1, at(SIDE, d) + EASE.torso, d);
    if (i === traced.length - 1) return P(1, at(SIDE, d) + EASE.torso, d);
    return P(1, v, d);
  });
  const torso = (s: number, to: number): Pt[] => {
    const pts: Pt[] = [];
    for (let d = ARMPIT; d < to - 0.05; d += 0.1) pts.push(P(s, at(SIDE, d) + EASE.torso, d));
    pts.push(P(s, at(SIDE, to - 0.05) + EASE.torso, to - 0.05));
    return pts;
  };
  // the shirt's neckline is the collar's inner edge, the opening the neck shows through, from the viewer's right top, down to the V at the stand, and up the left
  const neckline = SHIRT_NECK.map(([v, d]) => P(1, v, d));
  return { P, outer, inner, hem, hemD, hemDR, torso, neckline, cx, y, w };
}

/**
 * The shirt's body as a shape in `attrs`, cut as the drawing cuts it where an arm is raised (the clip under `id`): for a mask of what the shirt covers (the front locks' outline,
 * body-adult-front-locks.ts). "" when it is not worn.
 */
export function shirtCover(sk: Skeleton, p: CharacterParams, attrs: string, id: string): string {
  if (!wearsShirt(p)) return "";
  const E = underBlazer(p) ? EASE_UNDER : EASE_FREE;
  const body = `<path d="${outline(sk, E)}" ${attrs} />`;
  const raisedSigns = adultArmPoses(p).map((r) => r.sign);
  if (raisedSigns.length === 0) return body;
  return `<clipPath id="${id}"><polygon points="${torsoWithoutRaisedSleeves(sk, raisedSigns, (s) => armholeKnots(s, E), (dd) => at(SIDE, dd) + E.torso)}" /></clipPath><g clip-path="url(#${id})">${body}</g>`;
}

/** The shirt's outline: a single closed path. */
function outline(sk: Skeleton, E: Ease): string {
  const g = geometry(sk, E);
  const L = -1;
  const R = 1;
  const f = (q: Pt): string => `${fmt1(q[0])} ${fmt1(q[1])}`;
  const down = (pts: Pt[]): string => `L ${f(pts[0] as Pt)} ${smooth(pts)}`;
  const up = (pts: Pt[]): string => down([...pts].reverse());
  const outerL = g.outer(L);
  const outerR = g.outer(R);
  const innerL = g.inner(L); // from the armpit down to the cuff
  const innerR = g.inner(R);
  const tl = g.torso(L, g.hemD);
  const tr = g.torso(R, g.hemDR);
  let d = `M ${f(g.neckline[g.neckline.length - 1] as Pt)} ${down(outerL)} `;
  d += `L ${f(innerL[innerL.length - 1] as Pt)} ${up(innerL)} `; // the cuff's end, then up the inner edge to the armpit
  d += `${down(tl)} `;
  d += g.hem.map((q) => `L ${f(q)} `).join("");
  d += `${up(tr)} `;
  d += `${down(innerR)} L ${f(outerR[outerR.length - 1] as Pt)} ${up(outerR)} ${g.neckline.map((q) => `L ${f(q)} `).join("")}Z`;
  return d;
}

/** One sleeve's own region, the outer edge down, the cuff's end, the inner edge up: for drawing the sleeve again over the skirt. */
function sleeve(sk: Skeleton, s: number, E: Ease): string {
  const g = geometry(sk, E);
  const o = g.outer(s).filter((q) => q[1] >= g.y(ARMPIT - 0.05, 1.0));
  const i = g.inner(s);
  const f = (q: Pt): string => `${fmt1(q[0])} ${fmt1(q[1])}`;
  return `M ${f(o[0] as Pt)} ${smooth(o)} L ${f(i[i.length - 1] as Pt)} ${smooth([...i].reverse())} Z`;
}

/**
 * The armhole: the arm's inner edge carried on up past the armpit to the shoulder, so the sleeve reads as an arm and not as a flap. It follows the body's own crease where the arm meets the
 * chest (`RIB_KNOTS`, the same line the skin draws, 0.43 to 0.46 H out from the centre line), from the sleeve's inner edge at the armpit up to the shoulder's top.
 */
const armholeKnots = (_s: number, E: Ease): [number, number][] => [[0.55, 0.3], [0.5, 0.4], ...(RIB_KNOTS as readonly Pt[]).map(([v, d]): [number, number] => [v, d]), [0.42, 1.0], [at(ARM_INNER, ARMPIT) - E.inner, ARMPIT]];
/** The armhole's ink on a raised side, where the torso is cut (the sleeve that covered the cut has gone with the arm). */
const armholeInk = (sk: Skeleton, s: number, line: string, E: Ease): string => armhole(sk, s, line, E);
function armhole(sk: Skeleton, s: number, line: string, E: Ease): string {
  const g = geometry(sk, E);
  const knots = armholeKnots(s, E);
  const pts = knots.map(([v, d]) => g.P(s, v, d));
  return `<path d="M ${fmt1((pts[0] as Pt)[0])} ${fmt1((pts[0] as Pt)[1])} ${smooth(pts)}" ${line} />`;
}

/** The cuff's line across a sleeve, at the top of its band. */
function cuffLine(sk: Skeleton, s: number, line: string, E: Ease): string {
  const g = geometry(sk, E);
  const d = CUFF_END - CUFF_BAND;
  const a = g.P(s, at(ARM_OUTER, d) + E.outer, d);
  const b = g.P(s, at(ARM_INNER, d) - E.inner, d);
  return `<path d="M ${fmt1(a[0])} ${fmt1(a[1])} L ${fmt1(b[0])} ${fmt1(b[1])}" ${line} />`;
}

/**
 * The bow at the collar (`ribbon_color`), traced from the blue ribbon of ref/risa-adult/06-blouse-bikini.png (body-adult-shirt-data.ts): a band each side that tucks up behind the collar, the two
 * tails over the button band, the two loops with their slits and the knot over them all. One flat colour with a thin ink outline; the slits show the cloth. Drawn between the shirt's body and its
 * collar (the collar's wings lie over the bands), or on its own where the figure wears no shirt. Nothing without a colour.
 */
export function adultRibbon(sk: Skeleton, p: CharacterParams): string {
  const color = p.outfit.ribbon_color;
  if (color === null || p.outfit.tunic_color === null) return "";
  const g = geometry(sk, easeOf(p));
  const ink = outlineW(strokeW(sk));
  const fill = colorStr(color);
  const cloth = colorStr(p.outfit.tunic_color);
  const piece = (pts: readonly Pt[]): string => {
    const q = pts.map(([v, d]) => g.P(1, v, d));
    return `<path d="M ${fmt1((q[0] as Pt)[0])} ${fmt1((q[0] as Pt)[1])} ${q.slice(1).map((r) => `L ${fmt1(r[0])} ${fmt1(r[1])} `).join("")}Z" fill="${fill}" stroke="${shade(color, 0.3, 1.0)}" stroke-width="${fmt2(ink * 0.4)}" stroke-linejoin="round" />`; // the reference edges the bow in a thin dark tone of its blue, not in ink
  };
  const slit = (pts: readonly Pt[]): string => {
    const q = pts.map(([v, d]) => g.P(1, v, d));
    return `<path d="M ${fmt1((q[0] as Pt)[0])} ${fmt1((q[0] as Pt)[1])} ${q.slice(1).map((r) => `L ${fmt1(r[0])} ${fmt1(r[1])} `).join("")}Z" fill="${cloth}" />`;
  };
  return (
    RIBBON_BACK.map(piece).join("") +
    RIBBON_TAIL.map(piece).join("") +
    RIBBON_LOOP.map(piece).join("") +
    RIBBON_SLIT.map(slit).join("") +
    piece(RIBBON_KNOT)
  );
}

/** The ribbon's back bands lie under the collar and the rest over it, so the whole bow goes before the collar here and the collar's wings are drawn over its bands. */
const adultRibbonBehindCollar = (sk: Skeleton, p: CharacterParams): string => adultRibbon(sk, p);

/**
 * The part of a garment's torso that stays when an arm is raised: everything but the sleeve on the raised sides, cut along the armhole (the arm's root, from the shoulder's top down the body's crease to the armpit)
 * and down the torso's side. A side whose arm hangs is left whole. `armholeKnots(side)` are the armhole's knots [v, d]; `sideV(d)` the torso side's v at depth d. A polygon, for a clip path.
 */
/** How far down the shoulder's cap stays with the torso when the sleeve leaves with a raised arm, in head heights below the chin (the arm's top is at 0.4). */
const CAP_D = 0.5;
/** Where the cap's lower edge leaves the shoulder's outline: it runs from there in to the armhole at `CAP_D`, a short slant (the sleeve head's seam, inked) instead of a flat ledge. */
const CAP_TOP = 0.34;

export function torsoWithoutRaisedSleeves(sk: Skeleton, raised: readonly number[], armholeKnots: (side: number) => readonly (readonly [number, number])[], sideV: (d: number) => number): string {
  const g = geometry(sk, EASE_FREE);
  const L = -1;
  const R = 1;
  const top = -0.6;
  const bottom = 2.4;
  const sideDs: number[] = [];
  for (let d = ARMPIT; d <= bottom + 1e-9; d += 0.15) sideDs.push(d);
  const down = (s: number): Pt[] => {
    if (!raised.includes(s)) return [g.P(s, 3, top), g.P(s, 3, bottom)];
    // The shoulder's cap (everything outside the armhole down to CAP_D) stays with the torso, so the cloth runs over the shoulder to the arm's root; below it the cut follows the armhole.
    const k = armholeKnots(s).filter(([, d]) => d > CAP_D);
    return [g.P(s, 1.0, top), g.P(s, 1.0, CAP_TOP), g.P(s, (k[0] as readonly [number, number])[0], CAP_D), ...k.map(([v, d]) => g.P(s, v, d)), ...sideDs.map((d) => g.P(s, sideV(d), d))];
  };
  const left = down(L);
  const right = down(R).reverse();
  return [...left, ...right].map((q) => `${fmt1(q[0])},${fmt1(q[1])}`).join(" ");
}

export function adultShirt(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.tunic_color === null) return "";
  const E = easeOf(p);
  const g = geometry(sk, E);
  const ink = outlineW(strokeW(sk));
  const cloth = colorStr(p.outfit.tunic_color);
  const line = `fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(ink * 0.67)}" stroke-linecap="round" stroke-linejoin="round"`;
  // The details inside the cloth (the button band, the buttons, the cuffs) are thin pale lines in the reference, not ink: a darker tone of the cloth at a light weight, as the blouse's bust lines are.
  const soft = `fill="none" stroke="${shade(cloth, 0.62, 1.0)}" stroke-width="${fmt2(ink * 0.5)}" stroke-linecap="round" stroke-linejoin="round"`;
  const d = outline(sk, E);
  const poly = (pts: readonly Pt[], close = false): string => `M ${fmt1((pts[0] as Pt)[0])} ${fmt1((pts[0] as Pt)[1])} ${pts.slice(1).map((q) => `L ${fmt1(q[0])} ${fmt1(q[1])} `).join("")}${close ? "Z" : ""}`;
  const map = (pts: readonly Pt[]): Pt[] => pts.map(([v, dd]) => g.P(1, v, dd));
  const clip = `<clipPath id="adult-shirt-clip"><path d="${d}" /></clipPath>`;
  const placket = SHIRT_PLACKET.map((ln) => `<path d="${poly(map(ln))}" ${soft} />`).join("");
  const button = (v: number, dd: number, r: number): string => {
    const c = g.P(1, v, dd);
    const rr = r * 2 * sk.head_r;
    return `<circle cx="${fmt1(c[0])}" cy="${fmt1(c[1])}" r="${fmt2(rr)}" ${soft} /><circle cx="${fmt1(c[0])}" cy="${fmt1(c[1])}" r="${fmt2(rr * 0.4)}" fill="${shade(cloth, 0.85, 1.0)}" />`;
  };
  // under a build the buttons keep their spacing (spacedDepths): the warp alone would close up the ones in the rows it shortens
  const buttonDs = spacedDepths(sk.adult_build, SHIRT_BUTTONS.map(([, dd]) => dd));
  const buttons = SHIRT_BUTTONS.map(([v, , r], i) => button(v, buttonDs[i] as number, r)).join("");
  const raised = adultArmPoses(p);
  const raisedSigns = raised.map((r) => r.sign);
  const cuffs = [-1, 1].filter((s) => !raisedSigns.includes(s)).map((s) => cuffLine(sk, s, soft, E)).join("");
  const armholes = [-1, 1].filter((s) => !raisedSigns.includes(s)).map((s) => armhole(sk, s, line, E)).join(""); // a raised side's armhole is the torso's cut edge and is not inked
  // The breasts' shapes as a soft outline over the cloth: the contour the skin and the top draw, in a darker tone of the cloth at a light weight, under the other lines.
  const bust = adultBustLine(sk, DEFAULT_TAPER, shade(cloth, 0.84, 1.0), 0.55);
  // the button band lies over the breasts' inner edges: a strip of the cloth over them, as wide as the band, so their outline stops at its edges
  const bandTop = g.P(1, 0, 0.3);
  const bandBottom = g.P(1, 0, 1.75);
  const bandHalf = Math.abs(g.P(1, (SHIRT_PLACKET[1] as readonly Pt[])[0]![0], 0.3)[0] - g.cx);
  const bandMask = `<rect x="${fmt1(g.cx - bandHalf)}" y="${fmt1(bandTop[1])}" width="${fmt1(2 * bandHalf)}" height="${fmt1(bandBottom[1] - bandTop[1])}" fill="${cloth}" />`;
  // The collar: one closed outline over the shirt, with the two sides of its stand and the stand's button.
  const collar = `<path d="${poly(map(SHIRT_COLLAR), true)}" fill="${cloth}" stroke="${OUTLINE}" stroke-width="${fmt2(ink)}" stroke-linejoin="round" />`;
  const stand = SHIRT_STAND.map((ln) => `<path d="${poly(map(ln))}" ${soft} />`).join("") + button(...SHIRT_STAND_BUTTON);
  // The neck is drawn again over the collar, but only inside the collar's opening (the neckline and straight up from its two ends): there the collar's top corners would otherwise lie over the neck
  // instead of behind it. Anywhere else the neck is not redrawn, so nothing of the collar is hidden.
  const nl = g.neckline.map((q): Pt => [q[0], q[1] - ink * 0.55]); // up by half the collar's stroke, so the clip stops at the stroke's inner edge and does not cut across it
  const top = g.y(-0.6);
  const opening = [...nl, [(nl[nl.length - 1] as Pt)[0], top], [(nl[0] as Pt)[0], top]] as Pt[];
  const neckOver = `<clipPath id="adult-shirt-neck-opening"><polygon points="${opening.map((q) => `${fmt1(q[0])},${fmt1(q[1])}`).join(" ")}" /></clipPath><g clip-path="url(#adult-shirt-neck-opening)">${adultNeck(sk, p)}</g>`;
  const bodyShape =
    `<path d="${d}" fill="${cloth}" stroke="${OUTLINE}" stroke-width="${fmt2(ink)}" stroke-linejoin="round" />` + `${clip}<g clip-path="url(#adult-shirt-clip)">${bust}${bandMask}${placket}${cuffs}${armholes}</g>`;
  // A raised arm takes its sleeve with it: the body is cut along the armhole and the sleeve is the posed arm's own silhouette grown by the sleeve's ease, drawn after, in the arm's turned frame.
  const sleeveEase = shirtSleeveEase(sk, p);
  const sleeves = raised
    .map((r) => adultPosedSleeve(sk, r, { cloth, ease: sleeveEase, endD: CUFF_END, tag: "shirt", cutMargin: 3, extra: () => cuffLine(sk, r.sign, soft, E) }))
    .join("");
  const knotsOf = (s: number): readonly (readonly [number, number])[] => armholeKnots(s, E);
  const body =
    raised.length === 0
      ? bodyShape
      : `<clipPath id="adult-shirt-torso"><polygon points="${torsoWithoutRaisedSleeves(sk, raisedSigns, knotsOf, (dd) => at(SIDE, dd) + E.torso)}" /></clipPath><g clip-path="url(#adult-shirt-torso)">${bodyShape}</g>` +
        // the sleeve head's seam: the slanted edge the cap is cut along, inked, inside the shirt's outline
        `<g clip-path="url(#adult-shirt-clip)">${raised.map((r) => `<path d="M ${fmt1(g.P(r.sign, 1.0, CAP_TOP)[0])} ${fmt1(g.P(r.sign, 1.0, CAP_TOP)[1])} L ${fmt1(g.P(r.sign, (armholeKnots(r.sign, E).find(([, d]) => d > CAP_D) as [number, number])[0], CAP_D)[0])} ${fmt1(g.y(CAP_D))}" ${line} />`).join("")}</g>` +
        sleeves;
  return (
    body +
    buttons +
    adultRibbonBehindCollar(sk, p) +
    collar +
    stand +
    // The collar goes behind the neck at its top corners: the neck is drawn again over it (it is drawn before the legs' layer the shirt is in, so it would otherwise lie under the collar).
    neckOver
  );
}

/** The sleeves, drawn again over what hangs in front of them (the skirt), from just below the armpit down; null when this character does not wear the shirt. */
export function shirtSleevesOver(sk: Skeleton, p: CharacterParams, from: number = ARMPIT + 0.05): string | null {
  if (!wearsShirt(p)) return null;
  const E = easeOf(p);
  const g = geometry(sk, E);
  const ink = outlineW(strokeW(sk));
  const cloth = colorStr(p.outfit.tunic_color as string);
  const line = `fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(ink * 0.67)}" stroke-linecap="round" stroke-linejoin="round"`;
  const hanging = [-1, 1].filter((s) => !raisedSides(p).includes(s));
  if (hanging.length === 0) return "";
  const top = g.y(from, 1.0); // the sleeve's row, which moves with the arm under a build
  const clip = `<clipPath id="adult-shirt-sleeves-over"><rect x="0" y="${fmt1(top)}" width="${fmt1(sk.canvas_w)}" height="${fmt1(sk.canvas_h)}" /></clipPath>`;
  const pieces = hanging.map((s) => `<path d="${sleeve(sk, s, E)}" fill="${cloth}" stroke="${OUTLINE}" stroke-width="${fmt2(ink)}" stroke-linejoin="round" />${cuffLine(sk, s, line, E)}`).join("");
  return `${clip}<g clip-path="url(#adult-shirt-sleeves-over)">${pieces}</g>`;
}

ARM_OVER_HOOKS.push(shirtSleevesOver);
void quad;
