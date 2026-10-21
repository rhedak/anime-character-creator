// The adult woman's school blazer (`coat_cut` "blazer" on a coat): the navy single-breasted blazer of ref/risa-adult/05-blazer.png (docs/risa-adult-plan.md).
//
// As for the shirt, the torso and the sleeves are not traced: each front panel is one closed outline built from this body's own tables (the shoulder, the arm's two edges, the torso's side) with a roomier
// ease, so it covers the body whatever its proportions, and sleeves down to just above the shirt's cuffs. What the flat reference gives, because the body cannot, is traced (body-adult-blazer-data.ts):
// the V of the opening, the collar, its notch and the lapel, the front edge and its flared hem, the flap and welt pockets, the dart lines and the buttons. The left panel is the right's mirror.
//
// Two panels meet at the front edge, each with its own outline; the lapel is lines on the panel (it is the same cloth, one flat colour). Drawn over the shirt, the ribbon and the skirt's top, and its
// sleeves are drawn again over the skirt, in front of the shirt's, as the arms are.

import { OUTLINE, outlineW, strokeW } from "./character.ts";
import { colorStr } from "./body-parts-legs.ts";
import { ARM_INNER, ARM_OUTER, LEG_OUTER, SHOULDER_OUTER, TORSO_SIDE } from "./body-adult-data.ts";
import { ARM_OVER_HOOKS, at, place, smooth, type Knots, type Pt } from "./body-adult-parts.ts";
import {
  BLAZER_BUTTONHOLE,
  BLAZER_BUTTON_DEPTHS,
  BLAZER_BUTTON_R,
  BLAZER_COLLAR,
  BLAZER_DART,
  BLAZER_FLAP,
  BLAZER_FLAP_LINE,
  BLAZER_FRONT,
  BLAZER_HEM,
  BLAZER_LAPEL_FOLD,
  BLAZER_LAPEL_TOP,
  BLAZER_NOTCH,
  BLAZER_V_EDGE,
  BLAZER_WELT,
} from "./body-adult-blazer-data.ts";
import { FOOT_D_CUT } from "./body-adult-foot-data.ts";
import { adultArmPoses, raisedSides } from "./body-adult-pose.ts";
import { adultPosedSleeve } from "./body-adult-pose-arm.ts";
import { BLAZER_SLEEVE_END, shirtSleevesOver, torsoWithoutRaisedSleeves, wearsShirt } from "./body-adult-shirt.ts";
import { shade, tint } from "./colorutil.ts";
import type { CharacterParams } from "./params.ts";
import { fmt1, fmt2 } from "./pynum.ts";
import type { Skeleton } from "./skeleton.ts";

const SIDE: Knots = [...TORSO_SIDE, ...LEG_OUTER.filter(([d]) => d <= FOOT_D_CUT)];

/**
 * How much roomier the blazer is than the body, in head heights: over the shoulder, along the sleeve's outer edge, along its inner edge and along the torso's side. These are the least that covers the body
 * and the shirt under it: the blazer cannot be narrower than the arms it covers (the body's arms are drawn under it and would show beside a narrower sleeve, as would the shirt's), so its width is the body's,
 * not the reference's (docs/risa-adult-plan.md, the blazer's outline check). The shirt eases less under a blazer (`shirtEase` in body-adult-shirt.ts) so that its sleeve does not show outside this one.
 */
const EASE = { shoulder: 0.02, outer: 0.018, inner: 0.015, torso: 0.03 } as const;
/** Where the sleeve ends: above the shirt's cuff (which runs to 2.0), so the cuff shows. */
const SLEEVE_END = BLAZER_SLEEVE_END;
/** Where the hem is, and where the sleeve's inner edge meets the torso's side (the armpit). */
const HEM_D = 1.95;
const ARMPIT = 1.1;
/** The buttons' x, in head heights from the centre line (the viewer's left of it, where the closure is). */
const BUTTON_X = -0.02;

const ease = (t: number): number => {
  const u = Math.min(1, Math.max(0, t));
  return u * u * (3 - 2 * u);
};

export const wearsBlazer = (p: CharacterParams): boolean => p.outfit.coat_color !== null && p.outfit.coat_cut === "blazer";

/** The blazer's half-width at a depth, in head heights: the chest's, nipped at the waist, flaring toward the hem. */
function halfWidth(d: number): number {
  const chest: Knots = [[0.5, 0.43], [0.81, 0.467], [1.0, 0.41]];
  const base = d < 1.0 ? at(chest, d) : at(SIDE, Math.max(d, 1.1)) + (d < 1.1 ? (1.1 - d) * 0.3 : 0);
  return base + EASE.torso + 0.03 * ease((d - 1.3) / 0.65);
}

function geometry(sk: Skeleton) {
  const { cx, y, w } = place(sk);
  const P = (s: number, v: number, d: number): Pt => [cx + s * w(d, v), y(d)];
  const tableFrom = (tab: Knots, from: number, to: number): [number, number][] => tab.filter(([d]) => d >= from - 1e-9 && d <= to + 1e-9) as [number, number][];
  const outerKnots = (): [number, number][] => [
    [0.12, 0.26],
    [0.22, 0.42],
    ...tableFrom(SHOULDER_OUTER, 0.3, 0.9).map(([d, v]): [number, number] => [d, v + EASE.shoulder]),
    ...tableFrom(ARM_OUTER, 1.1, SLEEVE_END).map(([d, v]): [number, number] => [d, v + EASE.outer]),
    [SLEEVE_END, at(ARM_OUTER, SLEEVE_END) + EASE.outer],
  ];
  const innerKnots = (): [number, number][] => [...tableFrom(ARM_INNER, ARMPIT, SLEEVE_END), [SLEEVE_END, at(ARM_INNER, SLEEVE_END)]].map(([d, v]): [number, number] => [d, v - EASE.inner]);
  const outer = (s: number): Pt[] => outerKnots().map(([d, v]) => P(s, v, d));
  const inner = (s: number): Pt[] => innerKnots().map(([d, v]) => P(s, v, d));
  return { P, outer, inner, cx, y, w };
}

/**
 * Where the blazer's V opening and its collar start at the neck, in head heights: level with the shirt's collar (whose top corner is at 0.165 H across and 0.05 H down) and not beyond it. The flat
 * blazer's own corner (0.189 H across, 0.057 H down) put the blazer's tips above and outside the shirt's collar.
 */
const V_TOP: Pt = [0.172, 0.11];
const vEdgePts: readonly Pt[] = [V_TOP, ...BLAZER_V_EDGE.slice(1)];
const collarPts: readonly Pt[] = [V_TOP, ...BLAZER_COLLAR.slice(1)];

/** One front panel's closed outline: the V's top, over the shoulder, down the sleeve, up its inner edge, down the torso's side, along the hem, up the front edge and the V's edge. */
function panel(sk: Skeleton, s: number): string {
  const g = geometry(sk);
  const f = (q: Pt): string => `${fmt1(q[0])} ${fmt1(q[1])}`;
  const run = (pts: Pt[]): string => (pts.length === 0 ? "" : `L ${f(pts[0] as Pt)} ${smooth(pts)}`);
  const top = g.P(s, V_TOP[0], V_TOP[1]);
  const outer = g.outer(s);
  const inner = g.inner(s);
  // the torso's side starts where the sleeve's inner edge ends (the armpit) and eases out to the blazer's half-width, so there is no hook where the two meet
  const vArmpit = at(ARM_INNER, ARMPIT) - EASE.inner;
  const side: Pt[] = [];
  for (let d = ARMPIT; d < HEM_D - 0.1; d += 0.1) side.push(g.P(s, vArmpit + (halfWidth(d) - vArmpit) * ease((d - ARMPIT) / 0.3), d));
  const hem = BLAZER_HEM.map(([nx, d]): Pt => g.P(s, nx * halfWidth(d), d)); // front corner out to the side
  const sideCorner = hem[hem.length - 1] as Pt;
  // from the closure down to the front corner: the closure is on the centre line, both panels' straight front edges lie on it (their strokes merge), and only the flare leaves it
  const front = BLAZER_FRONT.map(([v, d]): Pt => g.P(s, Math.max(0, v - (BLAZER_FRONT[0] as Pt)[0]), d));
  const vEdge = vEdgePts.map(([v, d]): Pt => g.P(s, v, d));
  return (
    `M ${f(top)} ${run(outer)} ` +
    `${run([...inner].reverse())} ` +
    `${run(side)} L ${f(sideCorner)} ` +
    `${run([...hem].reverse())} ` +
    `${run([...front].reverse())} ` +
    `${run([...vEdge].reverse())} Z`
  );
}

/** An open run of traced points mapped onto the body for one side. */
function line(sk: Skeleton, s: number, pts: readonly Pt[], style: string, wide = false): string {
  const g = geometry(sk);
  const q = pts.map(([v, d]): Pt => g.P(s, wide ? v * halfWidth(d) : v, d));
  return `<path d="M ${fmt1((q[0] as Pt)[0])} ${fmt1((q[0] as Pt)[1])} ${smooth(q)}" ${style} />`;
}

function polygon(sk: Skeleton, s: number, pts: readonly Pt[], style: string): string {
  const g = geometry(sk);
  const q = pts.map(([v, d]): Pt => g.P(s, v * halfWidth(d), d));
  return `<path d="M ${fmt1((q[0] as Pt)[0])} ${fmt1((q[0] as Pt)[1])} ${q.slice(1).map((r) => `L ${fmt1(r[0])} ${fmt1(r[1])} `).join("")}Z" ${style} />`;
}

/** The sleeve's seam: a smooth curve from the shoulder's end down to the armpit, a little inside the sleeve's outer edge and ending on its inner edge. (The body's own underarm crease, which the shirt follows, is wavy; on the blazer it read as bubbles.) */
function armhole(sk: Skeleton, s: number, style: string): string {
  const g = geometry(sk);
  const knots: [number, number][] = [[0.3, 0.6], [0.6, 0.56], [0.9, 0.52], [1.1, at(ARM_INNER, ARMPIT) - EASE.inner]];
  const q = knots.map(([d, v]) => g.P(s, v, d));
  return `<path d="M ${fmt1((q[0] as Pt)[0])} ${fmt1((q[0] as Pt)[1])} ${smooth(q)}" ${style} />`;
}

export function adultBlazer(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.coat_color === null) return "";
  const g = geometry(sk);
  const ink = outlineW(strokeW(sk));
  const cloth = colorStr(p.outfit.coat_color);
  const fine = `fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(ink * 0.55)}" stroke-linecap="round" stroke-linejoin="round"`;
  const seam = `fill="none" stroke="${shade(cloth, 0.45, 1.0)}" stroke-width="${fmt2(ink * 0.5)}" stroke-linecap="round" stroke-linejoin="round"`;
  const L = -1;
  const R = 1;
  const panels = [L, R].map((s) => `<path d="${panel(sk, s)}" fill="${cloth}" stroke="${OUTLINE}" stroke-width="${fmt2(ink)}" stroke-linejoin="round" />`).join("");
  // the lapel: the collar's outer edge, the notch, the lapel's top edge and its fold, each side
  const lapel = [L, R].map((s) => line(sk, s, collarPts, fine) + line(sk, s, BLAZER_NOTCH, fine) + line(sk, s, BLAZER_LAPEL_TOP, fine) + line(sk, s, BLAZER_LAPEL_FOLD, fine)).join("");
  const raised = adultArmPoses(p);
  const raisedSigns = raised.map((r) => r.sign);
  const details =
    [L, R].map((s) => polygon(sk, s, BLAZER_FLAP, `fill="${cloth}" stroke="${OUTLINE}" stroke-width="${fmt2(ink * 0.55)}" stroke-linejoin="round"`) + line(sk, s, BLAZER_FLAP_LINE, seam, true) + line(sk, s, BLAZER_DART, seam, true) + (raisedSigns.includes(s) ? "" : armhole(sk, s, seam))).join("") +
    polygon(sk, R, BLAZER_WELT, `fill="${cloth}" stroke="${OUTLINE}" stroke-width="${fmt2(ink * 0.55)}" stroke-linejoin="round"`);
  // the buttons: gold, a ring in a dark tone of it and a pale highlight, each with its buttonhole's slit to the left
  const gold = p.outfit.coat_button_color === null ? "#ba975e" : colorStr(p.outfit.coat_button_color);
  const r = BLAZER_BUTTON_R * 2 * sk.head_r;
  const buttons = BLAZER_BUTTON_DEPTHS.map((d) => {
    const c = g.P(1, BUTTON_X, d);
    const a = g.P(1, BUTTON_X - BLAZER_BUTTON_R - BLAZER_BUTTONHOLE, d);
    const b = g.P(1, BUTTON_X - BLAZER_BUTTON_R, d);
    return (
      `<path d="M ${fmt1(a[0])} ${fmt1(a[1])} L ${fmt1(b[0])} ${fmt1(b[1])}" ${seam} />` +
      `<circle cx="${fmt1(c[0])}" cy="${fmt1(c[1])}" r="${fmt2(r)}" fill="${gold}" stroke="${shade(gold, 0.55, 1.0)}" stroke-width="${fmt2(ink * 0.5)}" />` +
      `<circle cx="${fmt1(c[0] - r * 0.25)}" cy="${fmt1(c[1] - r * 0.3)}" r="${fmt2(r * 0.38)}" fill="${tint(gold, 0.45)}" />`
    );
  }).join("");
  // The pockets and the dart lines go under the lapel's lines (the fold runs over the welt where they meet), the buttons over everything.
  const torso = panels + details + lapel + buttons;
  if (raised.length === 0) return torso;
  // A raised arm takes its sleeve with it: the torso is cut along the armhole (the shoulder's cap stays), and the sleeve is the posed arm's own silhouette grown by the blazer's ease, drawn after in the arm's
  // turned frame, ending above the shirt's cuff so that shows. The shirt's own sleeve is drawn before, under it.
  const sleeveEase = ((EASE.outer + EASE.inner) / 2) * 2 * sk.head_r;
  const sleeves = raised.map((r) => adultPosedSleeve(sk, r, { cloth, ease: sleeveEase, endD: SLEEVE_END, tag: "blazer", cutMargin: 1.2 })).join("");
  const knots = (): [number, number][] => [[0.62, 0.45], [0.6, 0.6], [0.56, 0.9], [at(ARM_INNER, ARMPIT) - EASE.inner, ARMPIT]].map(([v, d]) => [v as number, d as number] as [number, number]);
  const cut = torsoWithoutRaisedSleeves(sk, raisedSigns, knots, (dd) => halfWidth(dd));
  return `<clipPath id="adult-blazer-torso"><polygon points="${cut}" /></clipPath><g clip-path="url(#adult-blazer-torso)">${torso}</g>${sleeves}`;
}

/** One sleeve as a fill (the outer edge down to the cuff, the cuff's end, the inner edge back up) and its two edges and the cuff's end as open lines, so no line is drawn across the top where it is clipped. */
function sleeve(sk: Skeleton, s: number): { fill: string; edges: string } {
  const g = geometry(sk);
  const o = g.outer(s).filter((q) => q[1] >= g.y(ARMPIT - 0.05));
  const i = g.inner(s);
  const f = (q: Pt): string => `${fmt1(q[0])} ${fmt1(q[1])}`;
  const edges = `M ${f(o[0] as Pt)} ${smooth(o)} L ${f(i[i.length - 1] as Pt)} ${smooth([...i].reverse())}`;
  return { fill: `${edges} Z`, edges };
}

/** The sleeves drawn again over the skirt: the shirt's first (its cuffs show below the blazer's), then the blazer's. null when this character does not wear the blazer. */
function blazerSleevesOver(sk: Skeleton, p: CharacterParams): string | null {
  if (!wearsBlazer(p)) return null;
  const hanging = [-1, 1].filter((s) => !raisedSides(p).includes(s));
  if (hanging.length === 0) return "";
  const g = geometry(sk);
  const ink = outlineW(strokeW(sk));
  const cloth = colorStr(p.outfit.coat_color as string);
  const top = g.y(ARMPIT + 0.05);
  const clip = `<clipPath id="adult-blazer-sleeves-over"><rect x="0" y="${fmt1(top)}" width="${fmt1(sk.canvas_w)}" height="${fmt1(sk.canvas_h)}" /></clipPath>`;
  const pieces = hanging
    .map((s) => {
      const sl = sleeve(sk, s);
      return `<path d="${sl.fill}" fill="${cloth}" /><path d="${sl.edges}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(ink)}" stroke-linejoin="round" stroke-linecap="round" />`;
    })
    .join("");
  return (wearsShirt(p) ? (shirtSleevesOver(sk, p, SLEEVE_END - 0.06) ?? "") : "") + `${clip}<g clip-path="url(#adult-blazer-sleeves-over)">${pieces}</g>`;
}

ARM_OVER_HOOKS.unshift(blazerSleevesOver);
