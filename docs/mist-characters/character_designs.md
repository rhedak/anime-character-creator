# Character Design Reference: AI Generation Prompts

Purpose: lock each major character's appearance once, in enough prompt-ready detail that every future chapter illustration (`chapter_writing_strategy.md` Step 7) stays consistent without re-deriving the design from scratch each time.

**Reference images exist for all twelve characters** in `style-anchors/` (as `.webp`).
The descriptions below were updated after generation to match the approved images exactly (not the other way around): several characters drifted from their original prompt during iteration, and the generated result was judged better than the original written spec, so the spec was brought in line with the image rather than regenerating to match old text.
Discarded iteration passes live in `style-anchors-src/_old/`; source PNGs/JPGs are kept in `style-anchors-src/` and converted to `style-anchors/` via `shell_scripts/convert_to_webp.sh`.

---

## Style and format

**Style** (locked; `anime-style.md` holds the full spec plus an evaluation checklist to use when judging candidates): modern anime style, clean expressive line art, natural adult proportions (about 6.5-7 heads tall), soft cel-shading, muted earthy palette, polished graphic finish rather than painterly.
Not photorealistic, not pixel art (that is the sister game's style, deliberately different from this book's).
Note: character reference images use a plain near-white background; the cover and chapter insert images keep their atmospheric lighting, so this style section applies to character references only.

**Format:** Full-body reference portrait for every character, upright standing, no dynamic action poses or extreme foreshortening, used as the baseline consistency anchor.
No bust/half-body shots.

**Palette registers** (from `chapter_writing_strategy.md`): Okiri characters lean toward soft, muted jade-gray and pale mist tones with diffused light; Wodensreich characters lean toward cooler steel-blue and rust-iron tones with crisper, more mechanical detail.
A character with divided loyalties (Kisaragi) can visually split the difference rather than being purely one or the other.
Shading, lineart, and contrast are the same locked soft-cel anime style for both: the two-culture split is a palette and detail-density distinction, not a lighting or rendering switch.

---

## Shared prompt elements

**Positive (always include):**
```
modern anime style, clean expressive line art, natural adult proportions
(about 6.5-7 heads tall), soft cel-shading, muted earthy palette, polished
graphic finish rather than painterly, full body portrait, standing, plain
near-white background
```

**Negative (always include):**
```
photorealistic, 3D render, photograph, harsh flat cel-shading, pixel art,
watercolor, blurry, low detail, text, watermark, signature
```

---

## Character palette table

| Character | Faction register | Hair | Eyes | Notes |
|---|---|---|---|---|
| Satoko (persona) | Okiri, muted | Blonde at roots (dyed, over naturally black regrowth) fading to white at tips (genuine, undyed) | Pale jade-green | See dual-reference section below |
| Satoshi (persona) | Okiri, muted | Gender swapped version of Satoko for tragic hero; Blonde at roots (dyed, over naturally black regrowth) fading to white at tips (genuine, undyed) | Pale jade-green | See dual-reference section below |
| Kyoko (former self) | Okiri, before the cataclysm | Jet black, kept sleek and neat | Pale jade-green (unchanged) | Same eyes as Satoko: the one feature the disguise doesn't touch |
| Tomohiro (former self) | Okiri, before the cataclysm | Gender swapped version of Kyoko for tragic hero; Jet black, kept sleek and neat | Pale jade-green (unchanged) | Same eyes as Satoko: the one feature the disguise doesn't touch |
| Reinhard von Falkenrath | Wodensreich, cool steel | Light brown/dark blond, short groomed beard | Pale gray-blue | Precise but not severe; a soldier's build under an officer's uniform |
| Tenno | Okiri, faded | graying, once dark | Tired brown/amber | Stooped, uses a cane; patched, ragged clothing, not merely "worn" |
| Lord Haruto Kisaragi | Okiri/Wodensreich mixed | Dark, topknot | Sharp, pale gray-green | Hakama and katana; a small pin as the one Wodensreich tailoring detail |
| Daizen Kurogane | Okiri, house-marked merchant | gray, full beard | Sharp pale blue (corrected in a later session to match the approved reference art; see his full entry below) | Elaborately patterned house robe (his name in Kirimoji), not unornamented as originally written |
| Dr. Keiko Natsume | Okiri, muted | Long, dark brown | Tired amber, fine spectacles | Reads composed/put-together rather than visibly haggard |
| High Priestess Reika Mizuki | Okiri, faith-coded | Long, black, partly bound with an ornate headpiece | Dark, serene | Reads elegant and gentle rather than cold; the dogmatism is beneath the surface, not on it |
| Captain Elara Sturm | Wodensreich, cool steel | Dark auburn, short and choppy | Hazel | Stoic, serious; Donar's Hammers crossed-hammer pins; scar tracing from one eyebrow down her cheek (corrected in a later session to match the approved reference art; see her full entry below) |
| Lieutenant Viktor Grau | Wodensreich, cool steel | Dark, swept back with undercut | Pale gray-blue | Cool, relaxed, coasts on talent; Reinhard's foil for lacking ambition, not for coldness |
| Magus-Sergeant Krista Bastler | Wodensreich, cool steel | Light brown, wavy, pulled back loosely | Pale blue-green | Genki-girl; belt-mounted mana crystals and goggles; devotion expressed as excitement, not solemnity |
| Chiyo | Okiri, muted | Gray-streaked dark hair under practical kerchief | Dark / blue-gray | Innkeeper; firm, managerial presence |

Wodensreich supporting mages (Elara Sturm, Viktor Grau, Krista Bastler) are intentionally non-focus characters (`characters.md`); suggested designs are included below, matching Reinhard's uniform base, but none have been generated or approved yet.

---

## Satoko / Kyoko (dual reference) ; Satoshi / Tomohiro (dual reference)

The single most important design in the book: the same person, styled to read as two different ones.
Generate both reference portraits from the same underlying facial structure (same bone structure, same eyes) so a viewer can, in principle, see the resemblance once told to look for it, without either portrait announcing it.

**Shared, unchanging features (both portraits):** pale jade-green eyes, identical facial bone structure and proportions, same build.

### Kyoko (former self, pre-cataclysm)

**Base prompt:** `young woman, early twenties, jet black hair kept sleek and neat, sharp pale jade-green eyes, striking and youthful features, confident composed expression, formal Okiri researcher's robes, dark layered fabric with subtle mist-motif embroidery, an air of brilliant, untested self-assurance`

**Tone:** Confident to the edge of arrogance.
Nothing in her expression has been let down yet.
Bright rather than guarded.

**Reference generation prompt:** A young woman with sleek jet black hair and striking pale jade-green eyes, wearing formal dark Okiri researcher's robes with subtle mist-pattern embroidery, confident composed expression, youthful and unmarked features.
Modern anime style, clean expressive line art, natural adult proportions (about 6.5-7 heads tall), soft cel-shading, muted earthy palette, polished graphic finish rather than painterly, full-body standing pose on a plain near-white background.

### Satoko (present-day persona)

**Base prompt:** `woman, looks several years older than her actual age, hair blonde at the roots fading to pale white at the tips, pale jade-green eyes, one faint burn mark along the left jaw and cheek (not disfiguring, not covering the eye), quiet guarded expression, plain practical inn-keeper's clothing, muted earth tones`

**Tone:** Composed, reserved, deliberately unremarkable.
Nothing in her expression should read as performed for the viewer; she is not aware of being looked at closely.

**Reference generation prompt:** A woman who looks a little older than her actual years, hair blonde at the roots fading to pale white at the tips (the blonde a maintained dye job over naturally black regrowth; the white tips genuine and undyed), pale jade-green eyes, a faint burn mark along her left jaw and cheek, quiet guarded expression, plain practical clothing in muted earth tones.
Modern anime style, clean expressive line art, natural adult proportions (about 6.5-7 heads tall), soft cel-shading, muted earthy palette, polished graphic finish rather than painterly, full-body standing pose on a plain near-white background.

**Revised (later session):** her true hair color is black (matching the Kyoko reference below), not blonde; the blonde is a deliberate, maintained disguise over black roots, not her natural color partially whitened.
This does not change the approved image (`satoko.webp` already shows blonde fading to plain white at the tips, with no re-dyed blonde ends, which matches this correction cleanly), only the in-world explanation of why it looks that way.

**Consistency check when both exist:** place the two reference images side by side.
The resemblance (bone structure, eyes) should be visible once pointed out, but neither portrait should look like an obvious "before/after" pair on its own.
If they look too obviously like the same photo edited, the disguise reads as too thin; if the resemblance isn't visible at all even when told to look, the eventual reveal will feel unearned regardless of what the prose does.
Adjust generation until the balance feels right.

**Kyoko at seventeen (Ch10):** the approved `kyoko.webp` reference shows a hypothetical adult Kyoko at twenty, as if the cataclysm had never happened; it is not what she actually looked like at seventeen and should not be used for facial proportions or age in that flashback.
Ch10 sits only three years before Ch1, so the seventeen-year-old Kyoko should instead be anchored to the `satoko.webp` reference (same underlying bone structure, build, and eyes, aged down three years, softer/less settled features) with the `kyoko.webp` reference used only for hair color/texture and general wardrobe register.
Change enough on top of that shared structure (jet black hair, no burn mark, plain student's clothing, unguarded scorn rather than guarded restraint) that the resemblance to Satoko is not obvious at a glance; see `chapters/ch10_the_prodigy_notes.md` for the full prompt.

---

## Oberst-Researcher Reinhard von Falkenrath

**Base prompt:** `man, composed and precisely groomed, light brown/dark blond hair swept back, short groomed beard, pale gray-blue eyes, faint knowing expression, Wodensreich officer's uniform in slate gray-blue with silver rank tabs, leather shoulder strap and belt, small eagle/iron-cross pin, fastidious bearing`

**Tone:** Relaxed, controlled, never visibly rattled.
Poirot-coded fastidiousness: precise grooming and posture read as characterization, not just costuming.
The beard is part of his settled design (not in the original written spec, kept after generation because it reads well).

**Post-Ch22/24 update: several streaks of white now run through his hair, never fading, distinct from the general design's brown/dark blond base.** Earned on the page in Ch22's duel (a single streak, from forcing a connection through the Spirit/Connection crystal) and joined by a few more, their exact cause never witnessed on the page, sometime during his unexplained interval unconscious near the entity in Ch24.
Deliberately kept short of a full head of white (unlike Kyoko's own acute cataclysm marking): noticeable, permanent, a handful of streaks rather than a wholesale color change.
Carry this into any future appearance of him (a sequel, if the hook in Ch24 is ever followed up).

**Reference generation prompt:** A composed, precisely groomed man with light brown hair swept back and a short groomed beard, pale gray-blue eyes, wearing a slate gray-blue Wodensreich officer's uniform with silver rank tabs, a leather shoulder strap and belt, a faint knowing expression, fastidious bearing.
Modern anime style, clean expressive line art, natural adult proportions (about 6.5-7 heads tall), soft cel-shading, muted earthy palette, polished graphic finish rather than painterly, full-body standing pose on a plain near-white background.
---

## Tenno, former King of Okiri

**Base prompt:** `older man, once-regal bearing now diminished, graying hair that was once dark, tired brown/amber eyes, simple but well mainted traveling clothes stripped of royal regalia, simple leather belt, straight back with a simple walking cane, permanently apologetic expression`

**Tone:** Deflated rather than villainous on the surface, per his design as an intentional red herring (`characters.md`); residual dignity should be visible but suppressed, not gone.

**Reference generation prompt:** An older man with a once-regal bearing now visibly diminished, graying hair, tired brown eyes, simple but well maintained traveling clothes tied with a simple leather belt, no royal regalia, straight backed but uses a simple wooden cane, a permanently apologetic expression with residual royalty.
Modern anime style, clean expressive line art, natural adult proportions (about 6.5-7 heads tall), soft cel-shading, muted earthy palette, polished graphic finish rather than painterly, full-body standing pose on a plain near-white background.

**Pre-cataclysm appearance (Ch6):** Ch6 sits only three years before Ch1's present day, not decades, so this is the same mature, older man as the present-day style anchor, not a young man: same age and facial structure, same tired brown/amber eyes.
The only differences from his present-day appearance are dark hair not yet graying, bound in a formal court knot rather than his present-day plainer style; upright posture, no cane; and full Okiri royal regalia (layered silk in Okiri blue, the crane-and-mist crest worked in silver thread at each shoulder) in place of his ragged present-day traveling clothes.
No permanent apology in his eyes yet.

**Corrected in a later session:** the Ch6 insert image (`images/ch06.webp`) rendered him as a young man in his twenties, which contradicts the three-year gap to Ch1.
The prompt above and the chapter's own image-generation notes (`chapters/ch06_make_it_happen_notes.md`) have been revised to explicitly anchor his age and facial structure to the present-day style anchor; the image should be regenerated against this corrected prompt.

---

## Lord Haruto Kisaragi, Warden of the Eastern Veil

**Base prompt:** `refined nobleman, dark hair in a topknot, sharp pale gray-green eyes, elegant dark Okiri court robes and hakama, a single small pin as the one Wodensreich-influenced tailoring detail, a katana worn at the belt, practiced charming smile, calculating undertone beneath the warmth`

**Tone:** Liked by nearly everyone in a room, trusted by fewer than his manner suggests.
The Wodensreich tailoring detail (the pin) should read as a quiet, consistent visual marker of his divided loyalties, not a costume gimmick.
The katana was not in the original written spec but is now part of his settled design: a nobleman who still carries himself, and arms himself, like a warrior-class Okiri lord.

**Reference generation prompt:** A refined nobleman with dark hair worn in a topknot and sharp pale gray-green eyes, wearing elegant dark Okiri court robes and hakama with one small Wodensreich-influenced pin, a katana at his belt, a practiced charming smile with a calculating undertone.
Modern anime style, clean expressive line art, natural adult proportions (about 6.5-7 heads tall), soft cel-shading, muted earthy palette, polished graphic finish rather than painterly, full-body standing pose on a plain near-white background.

**Pre-cataclysm appearance (Ch14):** Ch14 sits only three years before Ch1's present day, the same gap already established for Ch6 and Ch10, so this is the same man as the present-day style anchor with no appearance changes at all: same topknot, same sharp pale gray-green eyes, same court robes, hakama, pin, and katana.
Only his expression and interior narration differ from how present-day chapters see him from outside; see `chapters/ch14_favors_kept_and_counted_notes.md` for the chapter's insert prompt.

---

## Daizen Kurogane

**Base prompt:** `older self-made merchant, gray hair and full gray beard, sharp pale blue assessing eyes, stern weathered face, elaborately patterned blue-and-red checkered house robe bearing his name/house mark in kanji-style characters (黒金), belt hung with keys and a coin pouch, carries an abacus and ledger scrolls, a locked traveling chest nearby`

**Tone:** Shrewd and severe rather than amused; a self-made man who has earned every part of his visible wealth and wants it seen.
This is a deliberate departure from the original written spec (which called for unornamented, practically-dressed understatement): the generated design reads as a much older, more established, more visibly successful merchant house head, and that version was preferred and kept.
His assessing sharpness survives the change; the "quality over ornament" restraint does not.
**Eye color corrected to match the approved art (later session):** the original written spec and an earlier draft of this prompt called for amber/ gold eyes, but the approved reference image (`style-anchors/daizen.webp`) rendered pale blue eyes instead and was approved as-is; the image is canon, and this document has been updated to match it rather than the other way around. `chapters/ch05_five_names.md` reflects blue eyes accordingly.

**Reference generation prompt:** An older, weathered self-made merchant with gray hair, a full gray beard, and sharp pale blue eyes, wearing an elaborately patterned blue-and-red checkered house robe with his house mark in kanji-style characters, a belt hung with keys and a coin pouch, holding an abacus and ledger scrolls, with a locked iron-bound traveling chest beside him.
Modern anime style, clean expressive line art, natural adult proportions (about 6.5-7 heads tall), soft cel-shading, muted earthy palette, polished graphic finish rather than painterly, full-body standing pose on a plain near-white background.

---

## Dr. Keiko Natsume

**Base prompt:** `woman, former head researcher, long dark brown hair, tired amber eyes behind fine wire spectacles, composed and put-together, white lab coat over dark gray Okiri researcher's robes, holds a ledger/clipboard and pen`

**Tone:** Well-meaning and privately haunted, but the exhaustion does not show on the surface the way the original spec called for.
The generated design reads polished and professional rather than visibly worn down; that version was preferred and kept.
Her guilt and overwork should now be played through behavior and dialogue (restless hands mid-scene, over-explaining, over-apologizing) rather than through visible disrepair, since the settled appearance no longer carries that signal on its own.

**Reference generation prompt:** A composed woman with long dark brown hair and tired amber eyes behind fine wire spectacles, wearing a white lab coat over dark gray Okiri researcher's robes, holding a ledger and pen.
Modern anime style, clean expressive line art, natural adult proportions (about 6.5-7 heads tall), soft cel-shading, muted earthy palette, polished graphic finish rather than painterly, full-body standing pose on a plain near-white background.

**Pre-cataclysm appearance (Ch10):** Ch10 sits only three years before Ch1's present day, not decades, so this is recognizably the same woman as the present-day style anchor, only three years younger, not a markedly more youthful person: same face, build, tired amber eyes, and long dark brown hair.
See `chapters/ch10_the_prodigy_notes.md` for the full prompt.

---

## High Priestess Reika Mizuki

**Base prompt:** `woman, long black hair partly bound with an ornate jeweled headpiece and hairpins, dark serene eyes, gentle composed expression, elegant formal Kiri-no-Miko vestments in gray and white with crane/dragon motifs, teal underskirt, silver necklace with a large pearl/moonstone pendant, holds a folding fan`

**Tone:** Dogmatic and uncompromising underneath, but this no longer reads on the surface as coldness.
The generated design is elegant, gentle, and serene rather than severe or stony, a deliberate departure from the original spec, and it was preferred and kept: her composure now reads as refined grace rather than icy discipline, which makes the eventual reveal of her guilt over the sabotage land as a contrast rather than confirmation of what her appearance already signaled.

**Reference generation prompt:** A woman with long black hair partly bound with an ornate jeweled headpiece, dark serene eyes, a gentle composed expression, wearing elegant formal Kiri-no-Miko vestments in gray and white with crane and dragon motifs and a teal underskirt, a silver necklace with a large pearl pendant, holding a folding fan.
Modern anime style, clean expressive line art, natural adult proportions (about 6.5-7 heads tall), soft cel-shading, muted earthy palette, polished graphic finish rather than painterly, full-body standing pose on a plain near-white background.

---

## Wodensreich supporting mages

Still intentionally non-focus characters (`characters.md`), but all three now have approved reference images (`elara.webp`, `victor.webp` note the filename spelling, `krista.webp`) generated with some deliberate departure from the original suggested designs below; descriptions were updated to match the approved images and the personality direction that came with them, the same policy as the main cast.
All three still share Reinhard's uniform base (slate gray-blue Wodensreich cut, silver rank insignia, leather strap and belt), so the group reads visually as one expedition.

### Captain Elara Sturm, Donar's Hammers

**Base prompt:** `woman, slender strong build, stern serious expression, dark auburn hair cut short and choppy, hazel eyes, a faint scar tracing from one eyebrow down across the cheek, Wodensreich officer's uniform in slate gray-blue with silver captain's insignia and crossed-hammer collar pins, fingerless leather gloves`

**Tone:** Stoic and serious, blunt, physical, impatient with theory.
Donar's Hammers is the strength/industry order, so she reads as muscle-and-machinery discipline next to Reinhard's precision, not as another investigator.
Matches the original design intent closely; no major departure.
**Scar corrected to match the approved art (later session):** the original written spec and an earlier draft of this prompt called for the scar to run "through one eyebrow" only, but the approved reference image (`style-anchors/elara.webp`) shows it continuing down across the cheek toward the jaw, and was approved as-is; the image is canon, and this document has been updated to match it. `chapters/ch06_what_the_crystals_woke.md` reflects the cheek-length scar accordingly.

**Reference generation prompt:** A slender, strong-looking woman with short choppy dark auburn hair, hazel eyes, a faint scar tracing from one eyebrow down across the cheek, and a stern serious expression, wearing a slate gray-blue Wodensreich officer's uniform with silver captain's insignia, crossed-hammer collar pins, and fingerless leather gloves.
Modern anime style, clean expressive line art, natural adult proportions (about 6.5-7 heads tall), soft cel-shading, muted earthy palette, polished graphic finish rather than painterly, full-body standing pose on a plain near-white background.

### Lieutenant Viktor Grau, Woden's Ravens

**Base prompt:** `man, lean, youthful, dark hair swept back with an undercut, pale gray-blue eyes, faint relaxed half-smile, Wodensreich officer's uniform in slate gray-blue with silver lieutenant's insignia, raven and cross collar pins, a leather chest strap echoing Reinhard's own`

**Tone:** Cool and relaxed rather than the cold, humorless foil originally written; visually he reads as an echo of Reinhard (same order, similar uniform detailing, a similar half-smile), which turned out to suit the settled characterization better than a contrast would have: he coasts on natural talent rather than effort, and Reinhard privately criticizes him for lacking ambition, an implicit reminder of what Reinhard might have been without the discipline he actually built his career on.
He still notices things (an intelligence/scrying specialist by role) but can't be bothered to chase what he notices, including, potentially, something off about Satoko.

**Reference generation prompt:** A lean, youthful man with dark hair swept back in an undercut, pale gray-blue eyes, and a faint relaxed half-smile, wearing a slate gray-blue Wodensreich officer's uniform with silver lieutenant's insignia, raven and cross collar pins, and a leather chest strap.
Modern anime style, clean expressive line art, natural adult proportions (about 6.5-7 heads tall), soft cel-shading, muted earthy palette, polished graphic finish rather than painterly, full-body standing pose on a plain near-white background.

### Magus-Sergeant Krista Bastler, Crystal Conclave

**Base prompt:** `slender, attractive woman, genki-girl energy, wavy light brown hair pulled back loosely, goggles pushed up on her forehead, bright pale blue-green eyes, subtle grin, Wodensreich uniform in slate gray-blue worn loosely with a noticeable bust, a belt at her waist holding several glowing Donarsblut mana crystals rather than scattered across the uniform, a star-shaped pin and crossed-pick collar pins`

**Tone:** Bright, excitable, talks fast; a deliberate tonal counterweight to a cast that otherwise skews heavy and controlled, a departure from the original "calm devout" spec that was preferred and kept.
Her devotion to Donarsblut crystals is unchanged underneath, it now expresses as giddy fascination rather than solemnity, which sharpens rather than dilutes her eventual friction with Reika Mizuki (same underlying reverence for sacred power, opposite affect).

**Reference generation prompt:** A slender, attractive woman with genki-girl energy, wavy light brown hair pulled back loosely, goggles pushed up on her forehead, bright pale blue-green eyes, and a subtle grin, wearing a slate gray-blue Wodensreich uniform worn loosely with a noticeable bust, a belt at her waist holding several glowing mana crystals rather than scattered across the uniform, a star-shaped pin and crossed-pick collar pins.
Modern anime style, clean expressive line art, natural adult proportions (about 6.5-7 heads tall), soft cel-shading, muted earthy palette, polished graphic finish rather than painterly, full-body standing pose on a plain near-white background.

## Chiyo, Innkeeper of Kiriguchi

**Base prompt:** `middle-aged woman, late 40s to mid-50s, gray-streaked dark hair scraped back tightly under a practical cloth kerchief, weathered but sharp face, firm mouth, observant eyes, strong capable build, simple practical working clothes with sleeves rolled to the elbows, sturdy brown apron with pockets, muted earth-tone tunic, sensible closed shoes or short boots, upright grounded stance with one hand on hip`

**Tone:** Firm, no-nonsense, and quietly protective.
The woman who keeps the books, the rooms, and the people in line.
Not maternal in a soft sense; managerial and assessing.
She has already buried boys from the first survey party and will not lose another without a fight.

**Reference generation prompt:** A middle-aged woman with gray-streaked dark hair scraped back under a practical cloth kerchief, weathered but sharp features, firm mouth and observant eyes, wearing simple practical working clothes with sleeves rolled to the elbows, a sturdy brown apron with pockets over a muted earth-tone tunic, and sensible short boots, standing upright with one hand on her hip in a calm, assessing expression.
Modern anime style, clean expressive line art, natural adult proportions (about 6.5-7 heads tall), soft cel-shading, muted earthy palette, polished graphic finish rather than painterly, full-body standing pose on a plain near-white background.

---

## Production notes

- **Generate Satoko and Kyoko's references before any other character**; every other design is secondary to getting the book's central visual trick right.
- **Reference roles:** Satoko is the origin (no reference).
  Reinhard takes Satoko as his style reference.
  The other male characters take Reinhard as primary style reference, falling back to Satoko if his image is ever missing (backward compatible with the pre-Reinhard setup); female characters take Satoko.
  The female Wodensreich mages (Elara, Krista) additionally attach a uniform-only secondary reference (`uniform-f.webp`, a female-cut crop of the Wodensreich uniform with no figure in frame); the captions label Satoko as the female figure/style reference and the crop as clothing only, and the main prompt states the split explicitly so the uniform reference cannot leak into the figure. `uniform-m.webp` holds the male-cut crop (not yet wired into any prompt; male uniforms come from the Reinhard primary).
- **Consistency practice:** once a character's reference portrait is approved, use it as a character reference (image-to-image or a reference parameter, depending on the tool) at moderate strength for every subsequent chapter illustration featuring them, the same way the sister project locks a "fullbody reference" first and reuses it.
  Do not regenerate a character's appearance from the base prompt alone for every new chapter; drift will accumulate.
- **Do not invent a physical description for a character in a chapter's image prompt that contradicts this document.** If a chapter draft reveals a detail this document doesn't yet have (a specific hairstyle change, an outfit for a specific scene), add it here rather than letting it live only in one chapter's notes file.
- Approved finals live directly in `style-anchors/` (e.g. `satoko.webp`, `daizen.webp`).
  Source PNGs/JPGs are kept in `style-anchors-src/`; run `shell_scripts/convert_to_webp.sh` to regenerate.
  Discarded iteration passes are kept in `style-anchors-src/_old/` instead, in case an earlier pass is ever worth revisiting.
- **When a generated image drifts from this document's written spec and the drift is an improvement** (as happened with Reinhard, Tenno, Haruto, Daizen, Keiko, and Reika during the first full-cast generation pass), update the spec to match the approved image rather than regenerating to match the old text.
  The image is the source of truth once approved; the prose descriptions above exist to keep future regenerations consistent with it, not the other way around.
- **"Kanji" in the prompts above is a deliberate exception to the `styleguide_en.md` rule against using it.** Kurogane's prompts say "kanji-style characters" because an image-generation tool needs a recognizable real-world term to render the right kind of script; this is tool instruction, not prose.
  In the book's own text (chapter prose, `continuity_reference.md`, any other narrative documentation), the in-universe term is **Kirimoji** (see `styleguide_en.md`'s proper noun table).
  Do not use "kanji" outside of an image-generation prompt string.
