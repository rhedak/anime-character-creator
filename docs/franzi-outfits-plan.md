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

## Order and progress (2026-10-19)

The method changed from "trace each garment" to "cut each garment from the body's own edge tables, a little outside the skin, then trace only the design details". Measured on the shorts layers of refs 02 and 03: the cloth's outer edge is within 0.00 to 0.06 H of the body's side knots all the way down, so a body-following cut matches the reference. The garments live in `ts/src/body-adult-garments.ts` and replace the shared parts only on an adult body (`ADULT_GARMENT_PARTS`, laid over `ADULT_PARTS` in `render.ts`).

1. Shorts, on `trouser_color`. **Done**: waist to mid-thigh, hem cuff, waistband and front seam; compared with refs 02 and 03 (`REF=02-blouse tools/.venv/bin/python harness/franzi/aligned.py ...`). Full-length trousers are the same cut with a longer hem; they need a `trouser_cut` choice, which the owner has not been asked about yet.
2. Blouse (`tunic_color`). **Done**: traced from ref 02's `white-blouse` layer as one piece (bodice, puff sleeves, sweetheart neckline, frilled cuffs, front opening), mapped onto the skeleton like the top and the briefs (`harness/franzi/blouse_trace.py`, `ts/src/body-adult-blouse-data.ts`). The traced outline is widened, outwards only, to the body's own edge where ref 02's pose is slimmer than ours at the waist and shoulders. Inside lines: the neckline's binding, each sleeve's seam, the gather above each cuff, the front opening. Not drawn: the scallops of the neckline and frills are smoothed, and the blouse's `sleeve_long`, `neckline_*` and collar options are ignored on the adult body. The arm of ref 02 touches the blouse at the waist where ours (from ref 04) stands a little apart, so a sliver of page shows between them, as it does in the bikini render.
3. Skirt and apron (`skirt_color`, `apron_color`). **Done, bow still to do**: the skirt and the apron are the colour masks of ref 00 (green and red; the base has no segment layers), taken as convex hulls because a hand or the bow only dents their visible edge, mirrored about the centre line and traced (`harness/franzi/skirt_trace.py`, `ts/src/body-adult-skirt-data.ts`). The apron has its sash, a line along the sash's lower edge read off the reference. The chibi underskirt is not drawn on her. Because the flare passes the arms, the arms are drawn again over the skirt (`adultArmsOver`), only when a skirt or apron is worn. The sash is its own band, as wide as the blouse at the waist, over the apron's top; the bow and its two tails are drawn from outlines read off the reference (`harness/franzi/bow_trace.py`, `ts/src/body-adult-bow-data.ts`). Worn with a skirt the blouse is tucked in: it is drawn in the skirt's layer, before the skirt. Not yet: the apron's gathers (dark second tone in the reference; flat here) and the skirt's own second tone.
4. Bodice (new `bodice_color`): over the blouse, lacing and buttons traced.
5. Boots and knee socks (`boot_color`, `knee_sock_color`): follow the leg and foot outline.
6. Coat, robe, strap, belt: from the torso cut, once the blouse exists.
