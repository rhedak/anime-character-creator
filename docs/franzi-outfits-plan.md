# Franzi's outfits: what the generator does with her today, and how to trace the new ones

Written 2026-10-19 after putting Franzi into a local copy of the web tool (`node web-stage.mjs --adult`) and rendering her in every garment slot the generator offers (24 cases; the contact sheets were in the scratchpad, not committed). This is stage 6 of `docs/adult-body-plan.md` made concrete.

## What the existing garments do on her

The garment code draws from the chibi's anchors, so on the adult body:

| garment | result | verdict |
|---|---|---|
| bikini top and briefs (always worn) | traced, signed off | fine |
| hair clip, headscarf, hat | sit on the head correctly | fine as they are |
| tunic (plain, long sleeve, collar, ribbon) | a kite-shaped sack from shoulders to upper thigh: no arms, no bust, no waist | wrong; needs an adult blouse |
| skirt (a-line, pleated, column) and hakama | start at the waist and hang straight; the column is a strip; pleated is narrower than her hips | a-line is passable; the rest need adult cuts |
| underskirt, belt, apron | the chibi's belt pouch and apron box on the waist | wrong |
| coat (blazer, open jacket) | a sleeveless vest, hem at the hips | passable as a vest, wrong as a coat |
| robe, strap | a floating parallelogram; a strap across the bust | wrong |
| boots, knee socks, trousers, undersleeve, wristband | **nothing is drawn** (her feet stay bare, legs bare) | missing, not wrong |

Nothing crashed (no render failed in 24 cases). Her ids stay unique and the SVG stays small.

## What the references give us

All on the shared 1312 x 2440 canvas, so they overlay the body exactly (`ref/franzi/README.md`). Segment layers exist for 01 to 04; the base (00) has none.

| ref | outfit | segment layers | traced from it |
|---|---|---|---|
| 02 blouse | white puff-sleeve blouse, scalloped square neckline, plain short underlayer | `white-blouse`, `beige-shorts` | blouse, shorts |
| 03 bodice | white blouse, green laced bodice with gold buttons, no apron, short underlayer | `green-corset`, `lace-up-front/`, `gold-buttons/`, `puffed-sleeves/`, `white-blouse`, `white-shorts` | bodice, lacing, buttons, sleeves |
| 00 dirndl | blouse, bodice, red apron, head to mid-thigh | none | apron and skirt, from the image by colour (red is separable) |
| 01 swimsuit | plain white one-piece | `white-one-piece-swimsuit` | one-piece |

## Order of work, one garment at a time

Each step is the bikini-top routine: segment mask, boundary, `fit_closed`, ridge-snapped interior lines, flat colour with `shade()` only on small elements, checked against the overlay at 50% before the next.

1. **Shorts** (02 `beige-shorts`, 03 `white-shorts`): simplest, below the hip, shares the bikini bottom's inset and leg-opening rules. Also settles how a garment that covers the briefs hides them.
2. **Blouse** (02): neckline, puff sleeves over the arms (the sleeves are the hard part: they cross the arm outline, which the body path owns), hem.
3. **Bodice** (03): the corset shape over the blouse, lacing, 16 buttons as small circles.
4. **Apron and skirt** (00): the dirndl's lower half. Needs the colour-based mask first.
5. **One-piece** (01): lowest priority; the bikini already covers the swimwear case.

Checkpoint 3 of the adult plan is steps 1 to 4 together: the dirndl and one casual outfit (blouse and shorts), shown beside refs 00 and 02.

## How they become selectable

The point of the generator test was this: the existing controls should keep working. Proposal: on an adult body, the slots the generator already offers draw the adult version, so no catalogue change is needed.

- `tunic_color` draws the blouse (`sleeve_cut`, `neckline_*` map to the blouse's cut where they have a meaning, and are ignored where they do not).
- `skirt_color` with `a_line` draws the dirndl skirt; `apron_color` the apron; a new slot `bodice_color` for the bodice (the one catalogue addition, TypeScript-only like the adult body).
- A new `shorts_color` slot (or `trouser_color` with a short cut) for the underlayer.
- The slots with no adult version yet stay as they are now (drawn from the chibi's anchors, wrong but harmless), and the adult catalogue hides or marks them.
- Named outfits (dirndl, blouse and shorts) are presets in `ADULT_PRESETS`, so they show up as starting points beside Franzi.

The render route is the one `adultBriefs` already uses: `render.ts` swaps the garment parts for the adult body's own (`...ADULT_PARTS`), so the shared garment code is not touched.

## Open items, for the owner

1. Is "adult slots under the existing controls" the right way, or should adult outfits be their own list of named outfits only?
2. The missing garments (boots, knee socks, trousers, undersleeve, wristband, which draw nothing on her): trace them too, or hide them in the adult catalogue? Boots and knee socks look like the first ones worth having after the dirndl.
3. Whether the shared `catalogue.json` and `ref-out/` offer her at all before the Python is gone: today she is only in the local preview (`web-stage.mjs --adult`); after the Python removal she moves into `PRESETS` (stage 7 of the removal audit) and the preview flag goes.
