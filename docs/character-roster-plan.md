# Character roster plan

Plan for taking the cast from two named characters to fourteen, and for
producing a reference sheet of our own that answers
`ref/character_sheet_satoshi.png`. Written 2026-08-08 at `e3ea295`.

## What the references are, and what they are not

`ref/` gained sixteen files on 2026-08-08: two twelve-slot contact
sheets and fourteen individual figures. **They are AI-generated
references for the character designs, not for the style.** What we take
from them is who these people are: what they wear, how they carry
themselves, what the silhouette has to say about them at a glance. What
we do not take is how they are drawn. Every one of them is soft-shaded,
gradient-lit and painterly, which is the opposite of the flat
hard-edged look this generator exists to produce (see `CLAUDE.md`,
"Hard constraints").

This distinction does real work below. Half of what the references use
to say "this person is sixty" is brushwork that cannot survive being
redrawn as flat vector shapes at chibi scale, so that information has to
be re-expressed rather than copied. Same with fabric weight, embroidery
and beard texture.

The standing rule from `docs/gap-analysis.md` applies here too: the
references are guides, not targets. Measure to find what is wrong, then
choose by eye.

## Where the designs actually come from

`docs/mist-characters/character_designs.md` is the authority, not `ref/`.
It states hair, eyes, garments, scars and bearing per character, and it
records which of those were themselves revised to match an approved
image. Where it and a reference image disagree, it says which one wins
and usually the image does.

Two cautions about using it here.

**It is a prompt document for a different pipeline.** Its style section
locks "natural adult proportions (about 6.5-7 heads tall), soft
cel-shading, polished graphic finish". None of that transfers. This
generator draws flat, hard-edged shapes at 2.4 heads, and `CLAUDE.md`
forbids the shading it asks for and the image generation it exists to
drive. **Take the design facts from it and none of its style.**

**It does not describe our renders, so drift in a reference is not a
target.** The measurement below is the case in point.

### The rule the iris measurement implies

Sampled inside the iris of each reference:

| Reference | Iris | Specified |
| --- | --- | --- |
| `ref/satoshi.png` | `#5a6654` | pale jade-green |
| `ref/satoko.png` | `#5a6c54` | pale jade-green |
| `ref/tomohiro.png` | `#303636` | pale jade-green, "unchanged" |
| `ref/kyoko.png` | `#303036` | pale jade-green, "unchanged" |

The first two are green. The second two are grey. The design document
names the eyes as "the one feature the disguise doesn't touch", so the
drift landed exactly on the feature that carries the resemblance, which
is what the owner meant on 2026-08-08 by "that is AI drift not design
intent".

So: **design facts come from the document, resemblance comes from
construction.** A generator that derives one preset from another cannot
drift, because there is only one value to drift. That is a thing this
project can do that the reference pipeline cannot, and it is worth
building around rather than treating as a convenience.

## The cast

Two **rosters**, not two casts. The sheets share ten members and swap one
slot each: `character_sheet_satoshi.png` carries Satoshi and Tomohiro,
`character_sheet_parent.png` carries Satoko and Kyoko. Fourteen personas,
but **eleven people**: Satoko, Satoshi, Kyoko and Tomohiro are all the
same person.

That last part is the book's central design and it is worth stating
plainly, because it changes what building them costs. Kyoko is who she
was before the cataclysm. Satoko is the persona she wears now: a
maintained blonde dye over black regrowth, a burn along the left jaw and
cheek, plain innkeeper's clothes in place of a researcher's, and a
guarded expression in place of a confident one. Satoshi and Tomohiro are
the same two states of the same person read male. Bone structure, build
and eyes are shared across all four by design.

Which means Kyoko and Tomohiro are not two of the twelve new characters.
They are three fields on two presets we already ship.

The sheets label with full names while our preset keys are short, so a
sheet needs a display name per character rather than reusing the key.

| Display name | Key | Rosters | Same person as | File |
| --- | --- | --- | --- | --- |
| Satoshi | `satoshi` | child | Satoko, Kyoko, Tomohiro | `ref/satoshi.png` |
| Satoko | `satoko` | parent | Satoshi, Kyoko, Tomohiro | `ref/satoko.png` |
| Kyoko | `kyoko` | parent | Satoko before | `ref/kyoko.png` |
| Tomohiro | `tomohiro` | child | Satoshi before | `ref/tomohiro.png` |
| Chiyo | `chiyo` | both | | `ref/chiyo.png` |
| Daizen Kurogane | `daizen` | both | | `ref/daizen.png` |
| Elara Sturm | `elara` | both | | `ref/elara.png` |
| Haruto Kisaragi | `haruto` | both | | `ref/haruto.png` |
| Keiko Natsume | `keiko` | both | | `ref/keiko.png` |
| Krista Bastler | `krista` | both | | `ref/krista.png` |
| Reika Mizuki | `reika` | both | | `ref/reika.png` |
| Reinhard von Falkenrath | `reinhard` | both | | `ref/reinhard.png` |
| Tenno Amatsuki | `tenno` | both | | `ref/tenno.png` |
| Viktor Grau | `viktor` | both | | `ref/victor.png` |

The sheet spells him "Viktor Grau" and the file is `victor.png`. The
sheet is the character, so the key is `viktor`.
`character_designs.md` already flags the spelling and keeps the
filename, so we do the same rather than renaming a checked-in reference.

`ref/satoshi 2.png` and `ref/satoko 2.png` were accidental additions and
were deleted on 2026-08-08. `ref/satoshi.png` and `ref/satoko.png` remain
the canon, which also settles what `docs/gap-analysis.md` measures
against.

## What the references demand that we do not have

Read character by character this is fourteen problems. Read by
machinery it is about six, because the cast reuses its own costume.

## What "first draft" means, per cluster

Written before any garment code, on purpose. Every one of these designs has
more detail in its reference than a tile can hold, and the failure mode of
working through a cast is that character three absorbs the budget character
ten needed. So each cluster gets a **minimum recognisable list**: the features
that carry identity at the size a character is actually seen, and nothing
else. Anything below the line is not forbidden, it is just not what "first
draft" means, and adding it before every character exists is the mistake.

The test for the line is the one the cover's expression pass established: does
it survive being shrunk to a tile? A brow moves under 1% of a face. A rank tab
is four pixels.

| Cluster | In the first draft | Below the line |
| --- | --- | --- |
| **Uniform** | standing collar, chest pocket pair, centre placket, waist belt, tall boot shaft, cross-body strap | rank tabs, shoulder boards, cuff piping, hip pockets, order-specific collar pins |
| **Robe** | crossed front, wide hanging sleeve, obi at the waist | embroidery, the checked panels, sword furniture, layered inner collars |
| **Open coat** | the open front over a visible inner layer, at the right length | pocket detail, lapel shape, the pattern woven into Kyoko's |
| **Head** | beard, glasses, ponytail, topknot | goggles, kanzashi, hairpins, headscarf pattern |
| **Everyone** | hair colour and mass, eye colour, skin, silhouette, age | anything at all that needs a second tone to read |

Two of those are worth stating as rules rather than rows. **A pattern is below
the line everywhere**: Daizen's checked cuffs and Kyoko's woven coat are both
texture, both invisible at tile size, and both would need machinery that
nothing else in the cast uses. And **a prop is not a garment**: Tenno's cane and
Daizen's chest change how those two read, and they are still deferred, because a
prop is the one thing on this list that can be added later without touching
anything already built.

### Garments

`Outfit` has eleven fields today: tunic, boots, undersleeve, belt,
apron, skirt, underskirt, trousers, pouch, skirt length, tucked. Grouped
by what they would need on top of that:

| Cluster | Characters | Missing machinery |
| --- | --- | --- |
| **Military uniform** | Elara, Krista, Reinhard, Tenno, Viktor | standing collar, chest pocket pair, hip pocket pair, button placket, shoulder boards, cross-body strap, tall boot shaft, cuff piping |
| **Robe and wide sleeve** | Haruto, Daizen, Reika | crossed front, wide hanging sleeve, obi sash, hakama, open outer robe |
| **Open coat** | Kyoko, Tomohiro, Keiko | an outer layer that hangs open over an inner one, in three lengths |
| **Near what we have** | Chiyo | bib apron rather than waist apron, headscarf |

**Five characters come out of one garment.** The uniform is remarkably
consistent across its five wearers: standing collar with rank tabs, two
flapped chest pockets, two flapped hip pockets, a centre button
placket, a waist belt, trousers into tall boots. Tenno wears the same
cut in khaki instead of blue-grey and without the cross-body strap.
Elara and Krista hang glowing blue crystals off the belt, which is a
world element rather than a personal one and probably wants to be its
own field.

### A hem that does not hold its reading across builds

Found while looking at the four renders on 2026-08-08, pre-existing and
not acted on. Satoko's `skirt_length=0.70` is measured hip to ankle, and
that fraction reads correctly at the realistic build, where the skirt and
the underskirt reach the boots. At chibi it leaves a band of bare leg
between the underskirt's hem and the boot tops. Kyoko inherits it,
because she inherits the outfit.

It matters more now than it did: a twelve-tile sheet is judged at chibi,
and every character with a skirt will be measured the same way. Worth
settling before Chiyo (task 9), who wears two skirts and a bib apron, and
before Reika (task 25), whose outer robe trails. The likely fix is that a
hem needs the same treatment `Hairstyle.volume` gave the hair: a length
that means the same thing at both ends of the build range rather than the
same fraction.

**Half of it was a missing outline, and that half is fixed** (2026-08-08).
The bare leg was a filled path with no stroke, on the reasoning recorded
in `_legs_and_boots` that a hem covers its top. The top, yes; the rest of
it, no, so the chibi carried two untouched skin-coloured shapes in a
drawing whose whole idea is hard edges. It now takes the same outline at
the same 0.85 weight the bare arm already had. What is left of this gap
is the length itself, which is task 20.

The open coat cluster is three lengths of one idea: Tomohiro's jacket is
cropped at the waist, Keiko's lab coat falls below the knee, Kyoko's
coat falls to mid-calf. If the layer takes a length the way `skirt`
does, it is one garment rather than three. Tomohiro and Kyoko also both
wear a navy inner tunic under a wide dark sash, which is a second reason
to look at them together.

### Hair

Nine of the twelve new heads need a cut that is not a variant of the
five we have (`long_blunt`, `short_layered`, `long_traced`,
`short_crop`, `short_tousled`):

- **topknot** with shaved or tight sides: Daizen, Haruto
- **high ponytail**: Krista
- **very long straight, centre-parted, past the waist**: Reika
- **swept back, short, no fringe**: Reinhard, Tenno, Viktor
- **long straight with a centre part, at the shoulder**: Keiko, Kyoko

Tomohiro's shaggy dark cut is the one that plausibly lands on existing
`short_tousled` machinery with different parameters, and Chiyo's hair is
mostly hidden under a scarf, which makes those two the cheapest heads in
the cast as well as the cheapest bodies.

A topknot and a ponytail are both the same new idea: hair that leaves
the skull silhouette and comes back, which no current cut does. Both
also need to sit behind the head at the crown, so they are a z-order
question as much as a shape one.

### Age

**This is the gap nobody has named, and it should be settled before it
gets copied five ways.** The cast spans roughly teens to seventies.
Chiyo, Daizen, Tenno, Keiko and Reika all read visibly older than
Satoshi and Satoko. `FaceStyle` has no age lever at all.

In the references age is carried by crow's feet, jowls, beard texture
and skin mottling, all of which is the style half we discard, and none
of which survives a chibi head anyway. So age has to be re-expressed as
something flat and skeleton-relative. The candidates, cheapest first:

1. **Eye aperture.** A smaller, less open eye with a lower iris ratio
   reads older at any size. `eye_size`, `eye_openness` and `iris_size`
   already exist, so this costs nothing but a decision about what the
   numbers mean.
2. **Brow weight and position.** Heavier and lower reads older.
   `brow_weight` exists.
3. **Hair desaturation.** Grey and white at the temples. `hair_color`
   and `hair_tip_color` exist but the tip tone runs the wrong way for
   this: it is for the ends of a lock, and grey comes in at the root.
4. **Hairline.** A receded hairline is Tenno's single strongest age
   signal and there is no field for it.
5. **A `heads` nudge.** An older figure at a slightly taller build
   inside the chibi range. This is the expensive option and probably
   fights the sheet, which wants one build across the grid.

The proposal is that **age is a preset-level convention rather than a
field**: a documented set of `FaceStyle` values that read old, applied
per character, in the same way `EXPRESSIONS` is a documented set that
reads as a mood. Where that turns out to be insufficient, it names the
one field worth adding, and the first candidate is the hairline.

### Facial hair

Daizen wears a full beard and Reinhard a short one. There is no
representation of facial hair at all. It is one new part function with a
`beard_color` and a length or style, drawn over the chin and under the
mouth line.

### Accessories and props

Per the brief, props are out of scope for the first pass. Two caveats
worth writing down before someone acts on that literally:

- **Load-bearing props.** Tenno's cane and Daizen's chest are part of
  the pose and the silhouette. Without them those two read as standing
  oddly rather than as not carrying anything.
- **Head accessories are not props.** Krista's goggles, Keiko's glasses,
  Chiyo's headscarf and Reika's kanzashi sit on the head and are part of
  what makes each face recognisable at thumbnail size. Glasses in
  particular are cheap and carry Keiko almost single-handed.

### The gate that has to hold

`CLAUDE.md` requires that anything a character differs on lives in
`CharacterParams`, `FaceStyle` or `Outfit` with a neutral default, never
hardcoded into a part function. Twelve characters is exactly where the
pressure to special-case Reika's kanzashi or Daizen's checked cuffs
becomes real. The generator has to stay general.

The practical test for each new feature: could a second character use
this field, and does leaving it unset draw nothing?

## Decisions taken

- **All fourteen land in `ref-out/`.** Confirmed 2026-08-08. The cost is
  smaller than it looks: `./refresh-ref-out.sh --check` runs the current
  four characters plus the cover in 1.8 seconds, so fourteen is about six
  seconds, and the files are flat-colour PNGs.
- **`refresh-ref-out.sh` needs no change to accommodate them.** It reads
  `PRESETS`, `REALISTIC_REFS` and `BUILDS` out of the installed package,
  so adding a preset adds its files.
- **The sheet is a module, not a script.** `sheet.py` alongside
  `cover.py`, with `sheet.sh` alongside `cover.sh`, so it is testable
  and its output is checked in.
- **`ROSTERS` lists only the characters that exist**, and grows as they
  land. The alternative, naming all twelve slots up front, is ten
  `KeyError`s against `PRESETS` on the day it is written, and it would
  make tasks 3 and 4 unbuildable until the cast is finished. See task 5
  for how the full grid gets exercised in the meantime.
- **The chibi is the published build; the realistic renders are
  deferred.** Settled 2026-08-08, and it settles what was written here
  as an open assumption. The tall figures do not work well enough yet,
  so they moved from `ref-out/<name>_real.*` to `ref-out/real/<name>.*`,
  lost their on-white copies (which existed only to be displayed), and
  came off the README. `presets.REALISTIC_REFS` is the short list that
  still gets one: Satoko and Satoshi, the only two whose realistic build
  was ever measured against a reference. The other twelve are chibi-only
  in `ref-out/`.

  Nothing about the realistic *build* changed. `BUILDS` is untouched and
  `--build realistic` still works on any character, so the stated
  direction of edging toward less deformed proportions is unaffected;
  what shrank is the set of committed artifacts.

## Answered since

- **Kyoko and Tomohiro are not a parent and child pair.** They are
  Satoko and Satoshi before, which is a stronger relationship than the
  one guessed at here and makes them the cheapest characters in the cast
  rather than two of the twelve. Built 2026-08-08 as `_before()` in
  `presets.py`, a `replace()` of three fields on each shipped preset.
- **The "2" references were accidental** and are gone. `ref/satoko.png`
  and `ref/satoshi.png` stay the measured canon.

## Open questions

- **Which roster does the checked-in sheet show?** Both is two artifacts
  and two byte-compare corpora. Child-only is one, and the parent sheet
  becomes a flag.
- **Does the sheet reuse the reference's layout** (4x3, dark ground,
  white labels, light card per tile) or state its own? Reusing it makes
  the comparison direct, which is worth something while the cast is
  being built.

## The order, and why it is not "most similar first"

The stated heuristic is easy to hard, starting with the characters
closest to what exists. That is right for the first two and stops being
right after them, because the cast's cost is concentrated in shared
machinery rather than spread across individuals. Ordering purely by
per-character similarity would build the uniform on the fifth character
and then not use it four more times.

So: the two cheapest characters first, because they prove the pipeline
and the sheet with almost no new shape code. Then order by how many
characters each new piece of machinery unlocks.

The sheet comes before any of them. It is buildable today with the two
presets we have, and it is the artifact every later step is judged
against. Built last, it would be the thing that finally reveals that
twelve characters were each tuned in isolation and do not sit together.

One rule applies throughout, and it comes from choosing the cover's
expression on 2026-08-08: **a face is judged at the size it will be
seen.** That measurement found a brow-only change shifts under 1% of the
face while anything touching the lid shifts two to three times as much,
which is why the choice was made on thumbnails rather than head crops. A
twelve-tile sheet renders every character small. So every character task
below is done when the character reads **in its tile**, not when it reads
at full size, and a face that is only distinguishable at full size is not
finished. Leaving that check to the end would mean tuning twelve faces
twice.

The other rule is the one the phases below already follow and Phase 1
originally did not: **machinery gets its own task, before its first
wearer.** A garment three characters share, hidden inside the first
character who happens to wear it, is a garment the second wearer has to
go back and generalise.

## Where it got to, 2026-08-08

**Every character in the cast has a first-draft chibi.** Fourteen presets,
all on `ref-out/sheet.svg`, all in the README, all byte-compared. What was
built to get there, in the order it was built:

1. **`sheet.py`**, the cast on one page. Built first as a batching tool as
   much as a deliverable: a character is judged in its tile, and rendering a
   whole cluster and reading one sheet is the only way to look at this cast
   often enough.
2. **A stub pass**: all ten remaining characters at once, with the colouring
   and frame their designs call for and the closest garments then available.
   That put a full sheet on screen before any new garment existed, which is
   what surfaced the blush default and the hair-length problem below while
   they were still cheap.
3. **`aged()`**, the age vocabulary.
4. **The uniform**, five `Outfit` fields, five characters.
5. **The beard** and **the spectacles**.
6. **The open coat**, one garment at three lengths, three characters.
7. **The robe**: crossed front, hanging sleeve, obi.

### What the stub pass caught, which is the argument for doing one

- **`FaceStyle.blush` defaults to 1.0**, which is the generator's cute
  default and wrong for most of this cast. Ten characters arrived with pink
  cheeks, including both men in their sixties. Every preset now states one.
- **`short_crop` is not a short cut.** Its `tip_range` spans 0.800 to 0.911,
  so `hair_length` barely moves it, and its `volume` is 1.30 at the chibi
  end. Five men came out with shoulder-length shaggy hair. `short_layered`
  at a low length is the tight cut, and it took all five with no new
  geometry: what looked like "nine new hairstyles" in the plan was mostly a
  wrong base.
- **`short_tousled` leaves a notch** in its silhouette that reads as damage
  once shrunk to a tile. Elara moved off it.

8. **The ponytail and the topknot**, as two composable parts rather than
   `Hairstyle` entries. That is what made them cheap enough to build at all:
   a `Hairstyle` is five callables that have to agree with each other and
   with the ceiling test, while `hair_tail` and `hair_knot` compose with any
   cut, so one small shape each gave Krista her ponytail and Haruto and
   Daizen their topknots without touching the five existing cuts.

   Both were invisible on the first attempt, in opposite directions. The
   tail was drawn inside the hair mass, which measures 1.34 to 1.39 head
   radii wide, so a shape at 0.42 was behind a filled silhouette and drew
   nothing. The knot was drawn *behind* the mass, where a cut leaves under a
   tenth of a radius of daylight above itself, and then between the mass and
   the fringe, where the fringe covers the crown. It ends up last of all the
   hair, poking through.

## The one-by-one pass, 2026-08-09

Every character looked at beside its own reference rather than on the sheet.
Two findings were worth more than the rest, and both were **systemic**: one
part or one rule failing the same way on several characters at once, which is
the kind of thing a per-character review finds and a sheet does not.

**Satoko's two-tone boundary was level, and at the wrong height.** The canon
keeps her blonde past the jaw and turns her pale over the last third of each
fall; ours switched in a dead level line at eyebrow height, so she read as a
white-haired woman in a blonde cap. The machinery was already right, and its own
docstring names this failure: `Hairstyle.tip_edge` says a boundary that runs
level "can only say pale below this height". `_HAIR_FADE` went 0.50 to 0.72.
**The 0.50 was a recorded owner decision**, so this reverses one; it is one
number to put back.

**Satoshi was changed the same way and the owner reversed it the same day.**
`_CROP_TONE_LIFT` went 0.26 to 0.14 to match `ref/satoshi.png`, which shows gold
nearly to the tips; at 0.14 the white on his fringe is barely noticeable, and
the owner's call is that the wider split reads better. It is back at 0.26 and
that value is now **canon rather than an approximation of the reference**, which
is worth stating plainly because the next person measuring against `ref/` will
find the same discrepancy and reach for the same fix.

The two turned out to be cleanly independent, which is what let his be put back
without moving her: sweeping `_HAIR_FADE` across its whole range leaves his
fringe byte-identical, because his lifted edge already sits below the level line
and so wins, and she is untouched by the lift and set entirely by the clamp. His
`ref-out/satoshi.svg` is byte-identical to what it was before the pass.

This is the clearest case yet of the standing rule from `docs/gap-analysis.md`:
the references are guides, not targets. A measured gap is a reason to look, not
a reason to close it.

**An outer layer needs a tone gap or it does not exist.** Measured across the
six characters who wear a coat or a robe: Keiko 174 luminance apart and reading
instantly, Tomohiro 19 and Reika 14 reading fine, Kyoko 5 and Haruto 8
invisible, and Daizen's robe *byte-identical* to his tunic, so the fold line had
been doing all the work alone. Both garments are built entirely around a
boundary and neither states its own silhouette, so both vanish completely when
what is under them matches, and they vanish while rendering perfectly. Now
guarded by a test at a gap of 12.

The other five were per-character and are recorded on their tasks: the beard
needed **sideburns** before it stopped reading as a scarf, the ponytail needed a
visible **tie** and both its edges outside the hair mass, Tomohiro's jacket
needed length, and Chiyo needed the headscarf that `aged()` could never have
reached.

### The sideburns, later the same day

The owner's read on the beard the pass had just landed: the outer lines of the
sideburns should track the shape of the face rather than use straight lines.
They were straight for a reason worth naming, because it will come up again on
any part welded to the head. **Each edge was a single quadratic** from the top
of the strip to the bottom. A quadratic can be told where to bulge but it cannot
be made to agree with a curve it does not share points with, so both edges left
their ends at a plausible distance from the skull and chorded across everything
in between: the outer one fell to 0.78 of the skull's half width at mid-span
while both of its ends sat above 0.87.

The fix is to stop approximating the contour and sample it. `_face_track` walks
`_head_edge_x`, the same function the skull's own outline is drawn from, and
returns a polyline held at a given share of the way out and a given width
further in. Two knobs rather than one, because a share alone gives a band that
thins as the jaw draws in and a width alone gives one that ignores the taper.

Looking at it also turned up a second fault, and it was the one doing the
damage: **the strip was widest at the top and converged to a point at the jaw**,
0.31 head radii down to 0.06. Two edges that converge make a triangle, which is
why it read as a cut-out or a chinstrap rather than as hair. `ref/reinhard.png`
has the strip narrow down the front of the ear, spreading only where it meets
the beard, so the taper is now inverted: 0.08 at the top, 0.17 at the join.

`_BEARD_SIDE_INSET` moved 0.87 to 0.93 as a consequence. Its old value was tuned
when there were no sideburns at all and the mass had to be kept off the cheek by
width alone; the top edge's dive past the mouth does that now, so what 0.87
bought was no longer a cheek but a band of skin between the strip and the hair
above it, and a sideburn that does not reach the hair is a strap. 0.98 was tried
and brings back the original hood.

`harness/beard/sideburn.py` keeps the old two-quadratic version alongside the new
one so the change can be judged as a single before-and-after, at head size and at
tile size together, which is the only way this part has ever been judged safely.

### Still below the line, and deliberately

- **Krista's goggles.** Named in the table above as a first-draft feature and
  still the one thing on that list not built. Chiyo's headscarf, the other
  one, landed on 2026-08-09.
- **The hakama**, which Haruto and Reika both want under their robes.
- **Everything already listed** under "What first draft means": patterns,
  rank tabs, kanzashi, props.

## Tasks

Numbered for reference in commits and in later notes, the way
`docs/gap-analysis.md`'s gaps are. Each is meant to be one change that
leaves the tooling green.

### Phase 0a: Kyoko and Tomohiro (done 2026-08-08)

Ahead of the sheet, which is a reversal of the order first written here.
The sheet came first while Tomohiro looked like an ordinary cheap
character. He is not one: he and Kyoko are three fields on presets that
already ship, which makes them cheaper than the sheet and better inputs
to it, since a four-tile sheet says more than a two-tile one. The sheet
still comes before every expensive character.

- [x] **0. Kyoko and Tomohiro as derived presets.** `_before()` in
      `presets.py`: jet black hair, no tip tone, no scar, everything else
      inherited by `replace()`. Their outfits stay Satoko's and
      Satoshi's for now, because dressing them needs task 7 and the
      point of this task was the face. Also fixed on the way past: the
      `scar_side` comment said "1 the right" while `presets.py` said
      "her left cheek", which are the same side described from opposite
      ends and would have put Elara's scar on the wrong cheek.

### Phase 0: the artifact to iterate against

- [x] **1. `sheet.py`.** A labelled grid of characters on one page, as
      SVG, built from the same skeleton-relative approach as `cover.py`.
      Takes a roster and lays out its members. Display name per tile.
- [x] **2. Display names and rosters.** A display name on
      `CharacterParams` (or a parallel mapping in `presets.py`), and a
      `ROSTERS` mapping so the child and parent sheets are data rather
      than two functions. Each roster lists only the characters that
      exist, so today both are two names long (Satoshi and Tomohiro;
      Satoko and Kyoko) and both grow by one every time a character
      lands.
- [x] **3. `sheet.sh` and `ref-out/sheet.png`.** Mirror `cover.sh`. Add
      the sheet to `refresh-ref-out.sh` and to its `--check` staleness
      test, the way the cover already is.
- [x] **4. Sheet tests.** Renders, stays deterministic, every roster
      member appears exactly once, and the checked-in file matches the
      code.
- [x] **5. Exercise the layout at full width.** A two-tile sheet proves
      nothing about a four by three grid: not the tile aspect, not
      whether long labels like "Reinhard von Falkenrath" collide, not
      whether twelve figures at that size read as one cast. Render twelve
      placeholder tiles from the two presets with varied palettes, look
      at it, and fix the layout then. The checked-in artifact still has
      two tiles; this is a harness script, and `harness/` is where it
      goes. Without it, task 26 lays the grid out a second time and
      Phase 0 bought less than it looks.

### Phase 1: the first two characters, and what they need

- [x] **6. Age vocabulary.** Comes before Chiyo, not out of her: she is
      the first older character, so her face cannot be built until this
      is settled, and settling it inside her task means five more
      characters inherit an undocumented decision. Choose the
      `FaceStyle` values that read old (see "Age" above for the
      candidates), document them in `presets.py` next to `EXPRESSIONS`
      with the reasoning, and check them at tile size.
- [x] **7. Open outer layer.** A garment that hangs open over an inner
      one, with a length the way `skirt_length` works. Three wearers at
      three lengths: Tomohiro cropped at the waist, Keiko below the knee,
      Kyoko at mid-calf. Built once here rather than cropped now and
      generalised at task 19.
- [x] **8. Dress Kyoko and Tomohiro.** They exist and share their
      originals' clothes. Tomohiro's reference is a cropped olive jacket
      over a navy tunic with a wide sash and dark trousers; Kyoko's is
      the same navy tunic and sash under a mid-calf coat, with tall
      boots. Both use task 7's garment, at its two ends. Note the two
      references agree with each other on the inner layer, which is the
      design working rather than a coincidence.
- [x] **9. Chiyo.** Bib apron (chest coverage with shoulder straps,
      unlike Satoko's waist apron) over a tan shirt, waist sash, brown
      overskirt, dark underskirt, headscarf. Closest to Satoko's existing
      layer stack; the new pieces are the bib and the scarf.

### Phase 2: the uniform, five characters

- [x] **10. The uniform garment.** Standing collar, chest and hip pocket
      pairs, button placket, shoulder boards, cuff piping, tall boot
      shaft. New `Outfit` fields, all defaulting to off.
- [x] **11. Cross-body strap and belt kit.** The strap as its own field,
      since Tenno lacks it; the belt crystals as another, since only
      Elara and Krista carry them.
- [x] **12. Swept-back short hair.** One cut, three wearers.
- [x] **13. Elara Sturm.** Blue-grey uniform, dark red short cut, gloves.
- [x] **14. Krista Bastler.** Same uniform, high ponytail, goggles on the
      head. The ponytail is a new cut and the first hair that leaves the
      skull silhouette and comes back, which makes it a z-order question
      as much as a shape one. It has one wearer, so it stays in her task.
- [x] **15. Viktor Grau.** Same uniform, black swept-back hair, laced
      boots rather than smooth.
- [x] **16. Facial hair.** One new part drawn over the chin and under the
      mouth line, with a colour and a length, absent by default. Its own
      task because Daizen needs the full-beard end of it at task 24, and
      a beard built inside Reinhard is a beard Daizen has to go back and
      generalise.
- [x] **17. Reinhard von Falkenrath.** Same uniform, blond swept-back
      hair, short beard.
- [x] **18. Tenno Amatsuki.** Khaki uniform, no strap, grey hair and a
      receding hairline, oldest face in the cast and so the first real
      test of task 6. Cane deferred with the other props, and noted as
      load-bearing.

### Phase 3: coats

- [x] **19. Keiko Natsume.** White lab coat over a dark wrap and long
      skirt, long centre-parted hair, glasses. Glasses are a new head
      part, cheap, and carry her almost single-handed at tile size.
- [ ] **20. The chibi hem.** A skirt length that reads the same at both
      builds rather than the same fraction of hip-to-ankle, which is what
      leaves Satoko and Kyoko bare-legged at chibi today (see "A hem that
      does not hold its reading across builds"). Here rather than earlier
      because Keiko's skirt is the third one to want it and the sheet is
      the first thing that shows it off; earlier is fine if Chiyo makes
      it obvious first.

Kyoko's coat used to be this task and has moved to task 8, with the rest
of her. She is Satoko, so she arrived with the first pair.

### Phase 4: robes

- [x] **21. Robe geometry.** Crossed front, wide hanging sleeve, obi
      sash. The largest single piece of new shape work in the plan.
- [ ] **22. Hakama.** Wide pleated lower garment, worn by Haruto and
      Reika both.
- [x] **23. Haruto Kisaragi.** Black kimono and hakama, obi, laced boots,
      topknot. The topknot is a new cut with two wearers, and it stays
      here rather than becoming its own task only because Daizen is the
      very next character to use it.
- [x] **24. Daizen Kurogane.** Open haori over a kimono, obi, full beard,
      grey topknot. The checked cuff panels are a pattern, and a pattern
      on a flat garment needs its own decision.
- [x] **25. Reika Mizuki.** Layered kimono, grey outer robe with a
      trailing hem, teal hakama, very long straight hair, kanzashi.

### Phase 5: closing out

- [ ] **26. Refresh `ref-out/` for the full cast** and update the
      README's table to show the fourteen chibis.
- [ ] **27. Re-run the gap analysis** against the sheet as a whole rather
      than character by character, which is the first point at which
      "do these people look like one cast" is answerable. This is a
      check on the cast, not a substitute for the tile-size check each
      character already passed.
- [ ] **28. Revisit props** with the load-bearing ones first: Tenno's
      cane, Daizen's chest.

Twenty-eight tasks and one already done: five for the sheet, eight for
shared machinery, eleven for the remaining characters, three for closing
out. Kyoko and Tomohiro left the character count entirely, which is what
"they are the same person" buys. The machinery tasks
are the ones worth doing carefully; a character on top of machinery that
already works is mostly a palette and a set of numbers, which is the
shape this generator is supposed to have.
