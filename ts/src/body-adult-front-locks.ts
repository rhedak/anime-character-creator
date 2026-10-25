// Locks of hair that fall in front of the shoulders onto the adult woman's body and whatever she wears (a cut's `frontLocks`, body-adult-cuts.ts): Risa's, traced from the hair over her
// uniform in ref/risa-adult/01-school-uniform.png (docs/risa-polish-plan.md, stage 4). They are in the body's knot space, so `place` puts them on her body as it is built. Drawn in their own
// slot after the garments and the arms and before the collar and the head (render.ts): the cloth lies under them and the face over their tops, which reach up into the hair beside the
// neck. They are drawn over a posed arm's root as over a hanging arm's, so nothing changes between a hanging arm and one held out a little; a forearm in this pose model folds outward,
// the way the arm is raised, so it does not cross them. (A mask that took the posed forearm and hand out of them was tried and dropped: cairosvg reads a mask by its alpha and a browser by its
// luminance, so a mask that hides with black shapes on white hid them in the companion's browser and in no PNG.)

import { OUTLINE, outlineW, strokeW } from "./character.ts";
import { colorStr } from "./body-parts-legs.ts";
import { adultCutOf } from "./body-adult-cuts.ts";
import { adultBodyRef, onHead, place, smooth, taperedStrand, type Pt } from "./body-adult-parts.ts";
import { adultPosedArmCover } from "./body-adult-pose-arm.ts";
import { blazerCover, blazerSleeveEase, wearsBlazer } from "./body-adult-blazer.ts";
import { shirtCover, shirtSleeveEase, wearsShirt } from "./body-adult-shirt.ts";
import { shade } from "./colorutil.ts";
import type { CharacterParams } from "./params.ts";
import { fmt1, fmt2 } from "./pynum.ts";
import type { Skeleton } from "./skeleton.ts";
import type { Chain } from "./tables.ts";

/** Where a lock's own outline starts whatever lies behind it, in head heights below the chin: below the shoulders' tops, clear of the hair beside the neck. */
const OWN_INK_FROM = 0.35;

/** The front locks of `p`'s cut: each one filled in the hair's colour, its strand lines over it and its outline inked down one edge, round the tip and up the other (the top is the hair beside the neck). */
export function adultFrontLocks(sk: Skeleton, p: CharacterParams): string {
  const cut = adultCutOf(p);
  if (cut.frontLocks.length === 0) return "";
  const { cx, y, w } = place(sk);
  const h = onHead(sk);
  const ink = outlineW(strokeW(sk));
  const hair = colorStr(p.hair_color);
  const tone = shade(p.hair_color, cut.strandTone[0], cut.strandTone[1]);
  const f = (q: Pt): string => `${fmt1(q[0])} ${fmt1(q[1])}`;
  const at = ([v, d]: readonly [number, number]): Pt => [cx + w(d, v), y(d, v)];
  // a strand as the head's chains are written (head radii about its centre), straight between its points, so it tapers as the hair's own strands do
  const strand = (pts: readonly Pt[]): Chain => {
    const r = pts.map((q): Pt => [(q[0] - h.head_cx) / h.head_r, (q[1] - h.head_cy) / h.head_r]);
    return [r[0] as Pt, r.slice(1).map((e, i) => [[((r[i] as Pt)[0] + e[0]) / 2, ((r[i] as Pt)[1] + e[1]) / 2], e] as const)];
  };
  const locks = cut.frontLocks
    .map((lock) => {
      const q = lock.outline.map(at);
      const path = `M ${f(q[0] as Pt)} ${smooth(q)}`;
      const strands = lock.strands.map((s) => taperedStrand(h, strand(s.map(at)), outlineW(strokeW(sk), cut.strandWeight), tone)).join("");
      return (
        `<path d="${path}Z" fill="${hair}" stroke="none" />` +
        strands +
        `<g mask="url(#adult-front-locks-ink)"><path d="${path}" fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(ink)}" stroke-linejoin="round" stroke-linecap="round" /></g>`
      );
    })
    .join("");
  // Each lock has its own outline down both sides and round the tip, everywhere below the shoulders (`OWN_INK_FROM`), whatever lies behind it: the cloth, the body, or the long hair where a
  // raised arm's sleeve was. Only at the top, where it comes out of the hair beside the neck, is it inked just where it lies over the body or something worn on it, out to the edge of that ink
  // (the body's outline, the blazer's panels, the shirt's body and the posed arms with their sleeves, each with its own ink), so the line starts at the top of the clothes and the lock runs
  // into the hair above them unlined. (Inked over the body and the clothes alone, a lock lost its line where a raised arm's sleeve had been and it lay on the hair behind the torso; clipped to
  // the body alone, the line stopped short of the blazer's shoulder.) The mask is white shapes on nothing, in its default units, which cairosvg and a browser read alike; a black backdrop, or a
  // region in user space, makes cairosvg ignore it.
  const sleeve = wearsBlazer(p) ? blazerSleeveEase(sk) : wearsShirt(p) ? shirtSleeveEase(sk, p) : 0;
  const white = (k: number): string => `fill="#ffffff" stroke="#ffffff" stroke-width="${fmt2(k)}" stroke-linejoin="round"`;
  const below = `<rect x="${fmt1(-sk.canvas_w)}" y="${fmt1(y(OWN_INK_FROM))}" width="${fmt1(3 * sk.canvas_w)}" height="${fmt1(2 * sk.canvas_h)}" fill="#ffffff" />`;
  const worn =
    below +
    adultBodyRef(white(ink)) +
    blazerCover(sk, p, white(ink)) +
    shirtCover(sk, p, white(ink)) +
    adultPosedArmCover(sk, p, sleeve + ink / 2, ink / 2, "#ffffff");
  return `<mask id="adult-front-locks-ink">${worn}</mask>${locks}`;
}

export const ADULT_LOCK_PARTS = {
  _front_locks: adultFrontLocks,
};
