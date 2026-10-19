# Audit: what the web tool's controls do to Franzi and to the adult body

Done 2026-10-19, read-only: nothing was fixed. Franzi is the first character on the adult body (`adult_female`, `docs/adult-body-plan.md`), and the web tool's controls were written for the tall chibi. This is what they do to her, with a recommendation for each finding.

## How it was checked

- **Every control of the catalogue, on her, in code.** For each body, hairstyle, hand and grip style, finish, range (min, middle, max), switch, colour, skin swatch, every field of every garment slot (worn alone, with the slot it requires, every option), and every face control: one render, on two bases, Franzi in the dirndl and Franzi in her underwear. 460 variants. Each was checked for an exception, malformed XML, `NaN` or `undefined` in the text, an id defined twice, a reference to an id that does not exist, and whether the picture changed at all. The tool is the same drawing code the page runs.
- **The page itself.** 277 interactions through the real controls in the browser (every option of every list, every slider at both ends, every switch on and off): no JavaScript error, and the preview always drew.
- **By eye.** The 97 variants that change her were rendered on contact sheets and looked at, and ten other characters were put on her body.

## What holds up

- **Nothing throws, and no output is malformed**, except the coat (below). No variant produced `NaN`, `undefined` or a dangling reference.
- **Works as it should:** skin tone (the swatches and any colour), hair colour, eye colour, glasses, the familiar, height, the blouse, shorts, skirt, apron and bodice, underwear colour, hat, headscarf, goggles, blindfold, hair clip. The head, hair and face are hers (traced), and take the colours.
- **Other characters on her body** (Satoko, Katherina, Risa and seven more): the colours, the garments (tunic as the blouse, skirt, apron, trousers as shorts) and the hat come through and look like an adult version of the character. See B2.

## Findings

Sizes: small = an hour or less, medium = a few hours, large = a campaign.

### A. A fault, in the output

| # | what | recommendation |
|---|---|---|
| A1 | **Fixed 2026-10-19.** The adult arms are now drawn once, in the pass after the coat (`adultArms` in `body-adult-parts.ts`); the sweep finds no problem. Was: **the coat (every cut) defines the body's ids twice** (`adult-foot-body`, `adult-arm-strip`, `adult-hand-body`...): the shared layers draw the arms twice around the coat, and the adult arms define clip paths. A browser forgives it; it is invalid SVG and a Pages-level thing a consumer's tool may not forgive. | **Fix**, small: draw the adult arms' definitions once (the second draw needs no defs). |

### B. Changing the body

| # | what | recommendation |
|---|---|---|
| B1 | **Fixed 2026-10-19.** On a body that is not an adult one her cut is drawn as `long_center_part` (`hairstyleOf` in `core-head.ts`); the character still says `swept_ponytail`, so switching back gives her own hair again. Was: **Franzi on a chibi body has no hair.** Her cut (`swept_ponytail`) is drawn only by the adult head's parts; the shared hair code gets an empty cut for it. The head is a bald disc. Her blouse, skirt and apron come out chibi-shaped, which is right; the bodice draws nothing. | **Fix**, small: give the cut a fallback for a chibi body (draw as the nearest chibi cut), or switch to one when the body changes. Or hide the cut for chibi bodies in the page. |
| B2 | **Decided 2026-10-19: option (1), kept.** The body's label in the page now says it brings Franzi's head, face and hands (`BODY_LABELS`). Was: **Another character on the adult body gets Franzi's head.** Their hairstyle, hair length, hair tail and every face setting (eyes, brows, mouth) are ignored: the adult head always draws her traced hair (in their colour) and face. Their garments follow. The chibi collar piece (`collar_mock`) draws as a rectangle at the chin, the belt, pouches, crystals, strap, robe, hakama and coat are the chibi's shapes on her, and the staff and the katana float beside her, held by nobody (the adult hands do not take a grip). | **Decide.** The honest options: (1) keep it, it is a "put this person on the adult body" button and the result reads fine; (2) offer the adult body only to characters that have an adult head (a catalogue note, and the page hides it elsewhere); (3) give the adult body heads of its own, a campaign. I'd take (1) now and record the limits in the page's text. |

### C. Controls that do nothing on her (silent no-ops)

On the dirndl base 132 of the 230 variants draw the same picture: her head, hair, hands and feet are traced and fixed, not driven by the chibi's settings.

| group | no-ops | recommendation |
|---|---|---|
| **Face** | 35 of 37: every eye shape, lash, iris, lid, mouth and brow-length setting; only the glasses and `brows_over_hair` change her | Hide or grey out on an adult body. Medium, once there is a way to say which controls an adult body ignores (below). |
| **Age** | the age slider does nothing (her face is fixed) | Same; or drive her face's age by blending two traces (large). |
| **Hair** | the eight other hairstyles, `hair_length`, `hair_tip_color` | Hide the list while she is on the adult body: only her cut exists. Or trace more cuts for her (large, one per cut). |
| **Hands** | all five hand styles and both grips | Hide on the adult body. The plan already lists the other adult hand poses as later work. |
| **Finish** | `soft` changes nothing (no gradients on her parts) and `highlight_strength` with it | Hide on the adult body, or make the soft finish apply to her (large). |
| **Bust, chest** | do nothing: her bust is traced | Hide, or drive her bust (medium, and a thing to decide with the owner). |
| **Garment options** | tunic neckline, sleeve and tuck options, skirt cut and length, belt cut and scale, collar cut, boot shaft and cut: chibi cuts she does not have | Hide the ones the adult versions do not read. |
| **Garments that draw nothing** | ~~boots, knee socks~~ (done), undersleeve, wristband, shoulder bars (a coat is needed), pouch and crystals without a belt | Hidden by `body_ignores` (below), except what needs a parent. |

The mechanism for all of this is one thing: **the catalogue has no way to say "this control does not apply to this body"**. A `bodies` list per control (absent means all) read by `web/app.js` would let the page hide or grey the controls she ignores and keep them for the chibi. Medium; it adds a field to `catalogue.json` and to the golden.

### D. Things that move, with an odd result

| # | what | recommendation |
|---|---|---|
| D1 | **`hair_tail` above 0 draws a stray dark shape** on top of her head (the chibi's ponytail root, over a head that has its own). | Fix with C: hide `hair_tail` on the adult body, or draw nothing for it there. Small. |
| D2 | **`hair_knot` draws a chibi bun** on top of her traced hair. | Same, small. |
| D3 | **`waist_shift` and `height` move the body and the garments, not the traced head and hands in step.** A waist shift of 1.5 breaks the blouse's neckline against the bodice; at 0.8 or 1.3 height the figure holds. | Limit `waist_shift` for her (hide, or a narrow range); leave height. Small. |
| D4 | **Fixed 2026-10-19** (belt, pouches, crystals, coat, robe with hanging sleeves, hakama and collar are adult garments now, `docs/franzi-outfits-plan.md` step 6; the strap and shoulder bars are still the chibi's shapes). Was: **The chibi belt, pouch, crystals, strap, robe, hakama and coat** are drawn from the chibi's anchors on her torso: a belt at her navel, a robe that is a parallelogram, a coat that is a long vest. | Leave until each is wanted as an adult garment (plan step 6: coat, robe, belt). Not breakage, unfinished. |
| D5 | **The staff and the katana hang in the air** (no hand holds them). | Leave; goes with the adult hand poses. |

### E. Not an issue

The page's list of hand styles shows chibi names ("Mitten (chibi)") for her. That is C, not a fault of its own.

## Done 2026-10-19

- A1 and B1 (above).
- **Knee socks and boots** (the missing garments of C): drawn for the adult body from the legs' tables and the traced foot (`adultKneeSocks`, `adultBoots`), on `knee_sock_color`, `boot_color`, `boot_shaft` and `boot_cut`; the toes and nails are not drawn under a boot. They left the ignore list.
- **D4 and B2:** see their rows above. The garments are by eye, with no reference to compare, so they are a first pass the owner should judge on the figure.
- **C and D1 to D3:** the catalogue has a new key, `body_ignores`: for each body, the fields the page hides. For the adult woman it lists the 49 fields that drawing her showed to change nothing visible (found by `ts/test/ignored-fields.ts`, printed by `node harness/franzi/ignored_fields.ts`) and the three that draw something wrong on her (`hair_tail`, `hair_knot`, `waist_shift`). The page (`applyBodyIgnores` in `web/app.js`) hides those rows, a garment whose fields are all ignored, and a section left empty, and shows them again when the body is changed back: on Franzi the page shows 66 of the 121 fields and no Hair section. The list is pinned by a test against what is drawn, so it cannot drift. Not hidden, by the drawing's own answer: the finish (it thins her strokes), glasses, `brows_over_hair`, and the chibi garments of D4 and D5.

## Suggested order, if the owner wants fixes

1. A1 (the coat's double ids): small, a real fault.
2. B1 (her hair on a chibi body): small, and what the owner met first.
3. The `bodies` field in the catalogue and the page reading it (C, D1 to D3): medium, and it removes most of the "options that break her" in one stroke.
4. Boots and knee socks for the adult body (plan step 5), then the coat, robe and belt as adult garments (step 6): both done.
5. B2 (heads for other characters on the adult body) and the soft finish for her: large, only if wanted.

## Reproducing

`harness/franzi/audit_sweep.ts` is the sweep (every control of `ref-out/catalogue.json` applied to Franzi, each result checked, the changed ones written out as SVG); run it with `mkdir -p $TMPDIR/audit && node harness/franzi/audit_sweep.ts`. The in-page pass was a short script that set every option of every select, both ends of every slider and every switch through the real controls and counted JavaScript errors. If the owner wants the sweep as a test, the "nothing throws, nothing malformed" part is a few lines; the coat's double ids (A1) would be its first failure.
