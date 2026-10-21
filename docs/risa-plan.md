> **Superseded, 2026-10-21.** Risa is now on the adult woman's body, drawn from the references in `ref/risa-adult/` (`docs/risa-adult-plan.md`). This plan is the record of the tall slender body and the traced chibi garments she wore; the
> pieces are still in the code (`tall_slender`, the traced `blazer`, `pleated`, `loafer` and ribbon cuts, `long_fringed`) and `RISA_TALL_SLENDER` in `ts/src/presets.ts` keeps her old definition for their tests.

# Risa plan

> **Renamed and recoloured, 2026-10-11.** This campaign began as "Mio", traced off a reference
> that turned out to read too much like Akiyama Mio from K-On (a friend pointed it out). The
> owner's answer: the name is **Risa**, the hair is **dark red** (`#6b1f2a`), the blazer is
> **grey** (`#4d5159`) and she wears a **gold bar clip** (`#e8c45a`) at the temple. The shapes
> (hair cut, blazer, ribbon, skirt, face) are still the traced ones; the names, files and
> comments here were changed to Risa throughout, and the steps below keep "Mio" nowhere except
> in the reference's own paths (`ref-local/mio/`, local only, untouched). The colours
> sampled in M0 and M10 are the reference's, and the hair and blazer rows are no longer hers.
> Whether the silhouette (the blunt fringe and the long straight locks) needs to change as
> well is open.

A new preset, Risa: a generic Japanese high school girl in a school uniform,
black hair, green eyes. Written 2026-10-11 at the owner's request, and
rewritten the same day after the first render, when the owner asked for it to
be done properly: her clothes **traced** off the reference, her **body
measured** (the reference has longer legs than our tall chibi), and the work
taken step by step until she is as close to the reference as is feasible.

She is **twenty-one** (raised from 18 on 2026-10-15, with the rest of the cast).
This repository is open source, so the preset is an adult. The `face_age`
0.75 chosen below was an earlier, younger face; the preset is 0.9.

Reference: `ref-local/mio/mio.png` (the full figure) and
`ref-local/mio/segments/` (hair, bangs, eyes, blazer, shirt, ribbon, skirt,
buttons, loafers, and the figure and background layers). The reference is
local only and is not checked in.

Campaign status lives at the top of each step. Nothing here is committed
unless the owner asks.

## Why this is a different kind of job from the rest of the guests

`CLAUDE.md` says the AI-generated references in `ref/` have done their job and
are not a target for new work, and that new characters are designed directly in
`presets.py`. This one is the owner's explicit exception, a character drawn in
"a slightly new style" and wanted close to her reference, so she follows the
campaigns that did take a reference as the target: Katherina's clothes
(`docs/katherina-clothes-plan.md`) and Keiko's (`docs/keiko-clothes-plan.md`),
by tracing, with `.claude/skills/trace-reference/SKILL.md` as the method and
`harness/keiko/` as the template for the scripts.

The standing lesson is **trace nothing below the chin off a reference whose body
is not ours** (`harness/hair_audit/gate.py` checks it for hair). Risa's body is
not ours: her legs are longer. The fix is to make her body ours first. Katherina
could be traced directly because her reference *is* `tall_chibi`, the profile
was measured off it. Risa gets the same treatment, a body profile measured off
her own reference, before anything below the chin is traced. A first look puts
her at about 4 heads against the tall chibi's 3.47, which is a hunch from
eyeballing the image and exactly what M2 measures.

## What the reference shows

| Part | Reference |
| --- | --- |
| Hair | black, very long (about waist length), blunt bangs across the brow, long side locks in front of the shoulders, straight and flat |
| Eyes | large and round, with highlights. **Black in the reference; the owner wants green.** |
| Blazer | navy, notched lapels, three gold buttons, a flap pocket on each hip, long sleeves, a white cuff showing at each wrist |
| Shirt | white, with a small collar under the lapels |
| Ribbon | a blue bow at the throat with two tails hanging over the shirt front |
| Skirt | light blue-grey, box pleats, ends well above the knee |
| Legs | bare thigh, then black knee socks. **Longer than the tall chibi's.** |
| Shoes | brown penny loafers |

## Decisions that shape the work

1. **Age 18 means an adult face.** `face_age` runs from young (low) to old
   (high): Kyoko 0.6, Lindita 0.7, Risa, Katherina and Linnea 0.75, Satoko 0.8,
   most of the adult cast 1.0. She starts at 0.8 and is tuned by eye later (the owner's
   call). The reference draws her younger than that; the age is the owner's.
2. **Trace, do not eyeball (the owner's call, 2026-10-11, replacing this
   plan's first decision to build parametrically).** Every shape that is a
   silhouette question is traced: the blazer, its lapels, the shirt collar, the
   ribbon, the pleated skirt, the sock, the loafer, the hair and bangs. A part
   that is only a colour or a yes/no stays a field.
3. **The body comes first.** A new `BODY_TYPES` profile measured off her
   reference (M2), the way `tall_chibi` was measured off Katherina's. Named for
   the shape, not for her, so anyone can wear it. Every traced cut is mapped
   landmark to landmark (shoulder, waist, hip, hem, knee, ankle), which is what
   keeps a cut wearable if the calibration is a few percent off.
4. **New behaviour is opt-in, and the cast stays byte-identical.** Knee socks,
   the ribbon, hip pockets, the loafers, the pleated skirt, the blazer and the
   new body are new fields, cuts or profiles with neutral defaults. The other 18
   presets render byte-identical. Compare the files with `cmp`, not only the
   snapshot report. A shared garment (`_coat`, `_tunic`, `_belt`, `_skirt`
   serve most of the cast) is never reshaped.
5. **Names stay neutral.** `"blazer"`, `"pleated"`, `knee_sock_color`,
   `ribbon_color`, never `"risa_blazer"`, so anyone can wear them, the way
   `long_traced` is a hairstyle anyone can pick.
6. **Flat colour, hard edges, no shading plane across a garment** (`CLAUDE.md`).
   The reference's pleats alternate two skirt tones. That is a shading plane
   across a garment, so the pleats are drawn as line work, as the cast's skirts
   already are, with a second tone only on small elements.
7. **The base layer rule stands.** With the tunic off she wears underwear like
   everyone else, and no bare render is a web option (`docs/bare-body-plan.md`).
8. **No em dashes, no double hyphens in prose or comments**, per `CLAUDE.md`.
9. **Not done quickly.** One step at a time, each its own predict, measure,
   render, look, record and owner sign-off pass, not a batch edit.

## Order of work, and why this order

The body first, because every traced cut is placed against it. Then back to
front, the order things are drawn in and occlude each other: legs and shoes are
behind the skirt, the skirt behind the shirt, the shirt behind the ribbon, the
ribbon behind the blazer, and the hair and the face over everything. Judging a
garment against a layer that is still wrong is how the Keiko plan lost a
milestone to a collar that read as a block because the coat's opening was
half the width it should be.

## Method, every step

- **Predict before rendering.** Write the number or the look down first, then
  measure. The gap between predicted and measured is the next clue and is
  invisible without the prediction.
- **One variable per measurement.** A single change that makes things worse is a
  hypothesis about coupling, not a verdict on the lever.
- **Calibrate on our own face, cross-checked twice** (face width and the
  vertical run), per the skill. Check every segment is a true pixel crop of the
  composite by offset search before taking coordinates off it. A layer export
  that is a regenerated variant, not a crop, may be used to see a shape but not
  to take coordinates (the witch hat lost two passes to that).
- **Look at it.** Side by side at one head scale, on white and on black, at 4x
  on every junction the step touches. A black page hides gaps against hair, and
  black hair, blazer and socks need checking on black as well as on white.
- **Scripts are records.** Each pass's scripts live in `harness/risa/`
  (`landmarks.py`, `compare.py`, and one trace and emit script per shape, the
  `harness/keiko/` pattern) and write to the ignored `out/risa/`. The emit step
  generates the `character.py` block from the trace, so a retrace is cheap.
- **Green tooling in the same change:** `ruff check`, `ruff format --check`,
  `pytest`; `./refresh-ref-out.sh` reports only Risa's renders (and the sheets
  and `catalogue.json` where relevant) changed.
- **The owner signs off before the next step starts.**

## Steps

### M0. Groundwork

**Status: done, 2026-10-11.**

- [x] Read the segments and sample the flat colours.
- [x] Render a throwaway to see which existing fields already do the job.
- [x] Compare the existing hairstyles against the hair and bangs segments.
- [x] Record the findings here before changing `src/`.

Findings, sampled as the dominant flat colour of each segment's eroded interior
(a 6-level quantised histogram, so good to about a step per channel, not the
modal-exact grade the Satoko palette used; M10 refines them):

| Part | Sampled |
| --- | --- |
| Hair | `#27272d` |
| Blazer | `#1b2739` |
| Skirt | `#818da5` |
| Ribbon | `#457b99` |
| Shirt | `#f9f9f9` |
| Loafers | `#453327` |
| Gold buttons | `#bd9957` |
| Skin | about `#f9dbc3` (the figure layer; ours stays `#f6dbc2`, Satoko's) |

What the existing fields do against the reference, rendered at `out/tmp/risa/`:

- **Hair.** `long_blunt` is the closest of `long_blunt`, `long_center_part`,
  `long_parted` and `long_traced`: flat and straight, ears covered. None of them
  has blunt bangs straight across the brow. Every one sweeps the fringe into a
  point or a part.
- **Blazer.** The shared coat with `coat_sleeves=True` gives navy sleeves and a
  coat that reads as a blazer from a distance, but it has only a small lapel
  point. `coat_cut="lab_coat"` has a notched lapel, but it ignores `coat_length`
  and runs to the knee. `open_jacket` is Katherina's and bares the shoulders.
- **Shirt, collar, buttons.** `collar_color` and `placket_color` read right as a
  white standing collar and a gold line of buttons, but the reference has three
  separate buttons and a notched collar that opens, not a closed band.
- **Skirt.** The shared skirt is a smooth bell with two fold lines and **no
  pleats**.
- **Feet.** `boot_color` gives a lace-up ankle boot, nothing like a loafer, and
  there is no sock.
- **A preset needs more than a `PRESETS` entry:** a `DISPLAY_NAMES` entry and a
  `ROSTERS` entry, or the smoke tests fail.

### M1. The first preset, existing fields only

**Status: first pass done, 2026-10-11, and now a placeholder.** `RISA` in
`presets.py`, registered last in `PRESETS` so nobody else's sheet order moves,
with `DISPLAY_NAMES["risa"] = "Risa"` and `ROSTERS["risa"] = ("risa",)`. `face_age`
0.8, `long_blunt` at `hair_length` 0.9, the shared coat with navy sleeves at
`coat_length` 0.55, a white tunic and collar, a gold placket, the grey skirt at
`skirt_length` 0.35, black boots. Rendered at `out/tmp/risa_preset.png`, beside
the reference at `out/tmp/risa_compare.png`.

It exists as a baseline to improve on. Each later step replaces a piece of it
with a traced one, and the fields it uses stand in until then.

Tests: 828 pass. Three fail on purpose and wait for M11: the `ref-out/`
snapshot, the `catalogue.json` match and the README table row. `ruff` is green.

### M2. Calibration, the crop check, and the body

The step that decides whether everything after it works.

**Status: done pending the owner's sign-off, 2026-10-11.** Findings and what
was built are in "M2 findings" below the checklist.

- [x] **Crop check.** Find which segments are true pixel crops of `mio.png` (the reference composite, whose file name is the reference's own) by
      offset search (mean RGB difference at the best offset), and which are
      regenerated variants. Record the offset of each true crop. Expect the
      figure layer (`anime-girl.png`) to be a crop and some layer exports not
      to be, as the grok layers were.
- [x] **Calibration.** `harness/risa/landmarks.py` re-derives it every run:
      head centre and px per head radius from our own rendered face against the
      reference's, solved twice (face width, vertical run) and cross-checked on
      the eyes. Record both numbers and the gap, and reject the contaminated
      method the Keiko plan documents (equator to chin, which runs into the
      neck and the collar).
- [x] **Landmarks, in head radii, y down from the head centre:** shoulder,
      waist, hip, skirt hem, knee, ankle, sole, and the half-widths at each, the
      arm's and the leg's. Print them all so the numbers have a runnable source.
- [x] **Predict, then fit.** Write down the predicted height in heads, then
      measure it. Add `BODY_TYPES["<name>"]` (a neutral name for a longer-legged
      tall chibi) and its `BODY_LABELS` entry, and check the shape that decides
      it: where the knee falls under a short skirt and how far the boot or sock
      shaft reaches (`boot_y`, `ankle_y`).
- [x] **A head-size decision.** `tall_chibi_long_torso` scales the head 1.1 over
      the measured profile, the owner's pick. Decide, by looking, whether her
      head ratio is the reference's or the cast's.
- [x] Render her on the new body with the M1 clothes and compare beside the
      reference on white, at one head scale, whole figure and legs.

Acceptance: both calibration numbers agree to a few percent; the landmark table
reproduces from the harness; her body sits on the reference's at the shoulder,
waist, hip, knee and sole to a stated tolerance; every other preset byte
identical. **This is the owner's first sign-off**: her proportions are the one
thing that is hard to change once the clothes are traced to them.

#### M2 findings

**Every segment is a true pixel crop** (`harness/risa/crops.py`, a masked
sum-of-squares search over every offset), at RMS differences of 0.03 to 0.44 per
channel for thirteen of fourteen and 4.67 for the hair layer (a layer composited
under other layers at its edges). Better than Keiko's. Coordinates may be taken
straight off any segment. The offsets, as (x, y) of the crop's top-left corner in
the composite: figure (416, 47), blazer (440, 410), shirt (447, 401), skirt (475,
836), ribbon (593, 435), loafers (531, 1388) and (650, 1388), bangs (511, 101),
long hair (417, 47), eyes (518, 255) and (663, 257), buttons (611, 766), (612,
613) and (612, 690). The composite is transparent, not white.

**The calibration is a compromise, and the compromise is the finding.** Her head
is not our head. Measured in our own head radii, four features give four scales:

| Feature | Her pixels | Ours in head radii | Px per radius |
| --- | --- | --- | --- |
| Ear tip to ear tip | 299 | 1.76 | 170 |
| Hair top to chin | 352 | 2.19 | 161 |
| Visible face width | 226 | 1.60 | 141 |
| Eye line to chin | 108 | 0.84 | 128 |

The first two measure the skull and agree within 5%. The last two measure the
face and disagree with them by 15 to 25%, because her face is a wide, short one
against ours: her ears sit about 0.5 head radii above her chin, ours about 1.0.
Keiko's calibration used the widest row of skin as the head's diameter, which
cannot be used here since her side locks cover the cheeks. The method that works:
the skull sets the body's scale, **R = 165 px per head radius**, head centre at
the chin minus 1.02 R (our chin stands 1.02 below our centre). This is an
estimate good to about 4%.

**She stands 4.36 heads on that radius, against the tall chibi's 3.47.** That is
not "slightly longer legs": the shoulder is where ours is (1.40), the torso is
longer (the wrist at 3.9), and the legs run 3.8 head radii from the hip to the
sole where the default tall chibi's run 2.3. The landmark table, `landmarks.py`,
in head radii from the head centre: shoulder 1.40 at 0.80 across, blazer hem
3.87, wrist 3.90, fingertips 4.35, skirt hem 4.43 (widest 0.93), sock top 5.675,
sole 7.72, thigh 0.27 wide at the top running to 0.21 at the calf, legs centred
0.39 either side. Waist and hip are not measured (a blazer and a skirt cover
them) and are placed by the tall chibi's own proportion.

**The head-size decision, taken by looking** (`compare.py heads`, three head
sizes blended over the reference): at the full 165 px our face is about 17% wider
than hers and the eyes sit far apart; at 0.85 of it the face width lands on hers,
which is also what the visible-face-width estimate gives on its own (141 px).
The face is what reads, so the head is made to suit it: the profile carries a
head scale of 0.85 (`_SLENDER_HEAD_SCALE`), the way `tall_chibi_long_torso`
carries 1.1. Her figure then stands 4.96 heads in that smaller radius.

**Built:** `BODY_TYPES["tall_slender"]` in `character.py` with its label in
`catalogue.py`, `RISA.body = "tall_slender"`, and the placeholder skirt and
blazer lengths re-derived for her body (`skirt_length` 0.168, `coat_length`
0.437). Measured against the reference on the same pixels (`compare.py`, and a
leg-run comparison): the figure's sole within 0.05 head radii (8 px), the sock
top and the knee on hers in the blend, the thigh and the calf within 0.03 of her
widths, the legs 0.06 closer to the centre line at the thigh top than hers.
`ref-out` check: only Risa's files differ; every other character is byte-identical.
Tests: 828 pass, and the same three expected failures wait for M11.

**Known and left, each for its own step:**

- The leg spacing at the thigh top wants `hip_half_w` near 1.2 (it is 1.0): at
  1.2 the placeholder shared skirt, which follows the hip width, flares into
  wings. Revisit once the skirt is a traced cut (M4), which does not read it.
- **Our hair is smaller than hers**, 0.28 head radii lower at the crown with her
  head scale at 0.85: her hair stands up to 0.28 radii clear of her skull. M8.
- Our face has no jaw like hers: our chin is a V, hers a rounded U. The face
  fields reach part of it (M9); a head-shape option may be needed.
- **Cuts are drawn in head radii of a reference body.** `_GARMENT_REF_BODY` is
  `"tall_chibi"`, so a traced cut is mapped from that body onto the wearer's.
  Risa's cuts are traced off her own body, so the mapping needs `tall_slender` (or
  a per-cut reference body) as its reference. That is a small change to
  `_garment_placement` and belongs at the start of M3, before the first cut.

### M3. Legs, knee socks and loafers

**Status: done pending the owner's sign-off, 2026-10-11.** What was built and
found is in "M3 findings" below the checklist.

- [x] `Outfit.knee_sock_color` (default `None`, draws nothing): trace the sock's
      silhouette (its top edge, the slight taper at the calf and the ankle)
      from the figure crop, mapped by landmark to the new body. Drawn over the
      bare leg and under the shoe. Check first whether `boot_shaft` plus a boot
      colour is close enough to avoid a new field; it probably is not, since a
      sock is not a boot and has no cuff.
- [x] The loafer: trace `segments/brown-loafers/` (two crops of one shoe, check
      which is true) as a low shoe. Probably a new opt-in shoe variant beside
      the ankle boot, since the ankle boot's silhouette is the wrong shape for a
      loafer. Include the strap and the opening as line work.
- [x] Look at the legs full body, on white and on black (black socks on a black
      page vanish: check the outline holds them).
- [x] Catalogue entries and a test that the other presets draw neither.

Acceptance: bare thigh, black sock, brown loafer, at figure size and at 4x on
the knee, the sock top and the ankle; the other 18 byte-identical.

#### M3 findings

**The cuts needed to learn about bodies first.** A traced cut is drawn in head
radii of a reference body, `_GARMENT_REF_BODY`, which was fixed at the tall
chibi. `GarmentCut` now carries `ref_body` (default the tall chibi, so every
older cut is untouched, held by a test), `_garment_placement` takes it, and a
test holds that a cut is the identity on the body it was traced on. Risa's cuts
are traced on `tall_slender`.

**A cut for a limb.** `GarmentCut.per_leg` marks a cut whose coordinates are the
right leg's, with x from that leg's own centre line, drawn once per leg and
mirrored for the left (`_leg_placement`, `_draw_leg_cut`). A sock or a shoe
therefore goes where the leg hangs and not at a fixed x, so the leg spacing
(deferred to M4) cannot pull a sock off its leg. `GarmentCut.shades` gives a
fill its own tone (the loafer's sole), as `shade()`'s value factor on the cut's
colour.

**Traced, by `harness/risa/trace_feet.py`, emitted by `emit_feet.py`:**

- `KNEE_SOCK_CUT`: one sock, 17 segments, the leg-coloured component below the
  skirt grown to the stroke's centre line. The reference hides its lower end under
  the shoe, so it is run straight on down under it; a first pass that let the
  colour mask follow the sock into the shoe's collar grew a spike along the shoe.
- `BOOT_CUTS["loafer"]`: the silhouette (18 segments), a sole band as a second
  tone (0.78 of the leather, the reference's #332921 over #433228), and four
  lines: the saddle's upper seam, the penny slit, the toe-cap loop (the saddle's
  lower edge, the sides and the U, one closed ring) and the sole line.
- The outline width has to be measured with its antialiased edge: the solid ink
  run was 1 px and the stroke is 3, and a trace grown by 1 rode the fill's edge
  and not the stroke's centre. The first overlay showed it.
- The toe-cap loop is a closed ring, so the line walker (`common.walk`) now closes
  rings, which it did not.

**Two things the render found and the numbers had not:**

- The bare leg is wider than the sock and ran on down inside it, showing as skin
  along both sides. The leg is now clipped at the sock's top edge when a sock is
  worn (`leg-above-sock`).
- Our sock sat 7 px in from our own leg where the reference's sock and leg share a
  centre and a width (72 and 74 px). The leg is not drawn on `_leg_gap_and_top`'s
  centre line: the knee's bulge and the inside edge running off toward the crotch
  put it 0.05 head radii further out. `_LEG_CUT_OUT` carries that, and it also
  puts her feet where the reference's are. Measured after: leg 535 to 605 px, sock
  535 to 606.

**Measured against the reference** (`step.py`-style leg and sock runs, at the sock
top): the reference's leg 531 to 603 and sock 530 to 604; ours 535 to 605 and 535
to 606. Her legs still stand 4 to 9 px nearer the centre line than the
reference's, which is the hip-width item below.

Looked at: the legs against the reference on white at figure size and at 3x on the
sock top and the shoe; both on white and on black (the sock's fill separates from
black and the loafer's seams read). The sock's slight bend at the lower calf is
the reference's own.

**New fields and registry:** `Outfit.knee_sock_color`, `Outfit.boot_cut`,
`BOOT_CUTS`; the catalogue slots `KNEE_SOCK` and the `boot_cut` select on the
boots slot (renamed "Boots (and shoes)"), each with its label and the registry
assert. `refresh-ref-out.sh --check` says only Risa is stale: every other
character is byte-identical. Tests: 835 pass, plus the same three expected
failures for M11; seven new tests hold the reference body, the older cuts'
default, that only Risa wears either, the mirror and the placement, the leg clip
and the sole's tone.

**Still open for M4:** the legs' spacing at the thigh top (about 4 to 9 px
closer than hers, `hip_half_w` 1.0 against about 1.2) waits for the traced skirt,
which does not read the hip width. The shared skirt on the placeholder is a bell
and hides the thigh tops.


### M4. The pleated skirt

**Status: done pending the owner's sign-off, 2026-10-11.** Findings below the
checklist.

- [x] Trace the skirt's silhouette off `segments/pleated-skirt.png` (check the
      crop first) as `SKIRT_CUTS["pleated"]`, landmarks mapped: waistband,
      the hem's edge, which is a zigzag of pleat folds and not a smooth curve.
- [x] The pleat folds are **line work**, not tone planes (decision 6): trace
      the interior fold lines the way the skill's interior-stroke case does
      (erode the hull, take the dark pixels, fit open chains), keeping their
      count and spacing from the reference.
- [x] Hem about at mid-thigh, checked against the sock top and the blazer hem.
- [x] Check it from the front only; no pose exists.

Acceptance: pleats read at figure size; `SKIRT_CUTS` has a label and the
assert; no other skirt wearer changes (`cmp` Satoko, Chiyo, Keiko, Reika).

#### M4 findings

**`SKIRT_CUTS["pleated"]`**, traced by `harness/risa/trace_skirt.py` and emitted by
`emit_skirt.py`: one silhouette (24 segments, carrying the stepped hem, each pleat's
bottom edge a slanted straight line) and six fold lines (one to two segments
each), the stroke's centre line throughout. The segment is the visible skirt, so
its top edge is the blazer's hem arc with a tab where the blazer's front comes to
a point. Her skirt continues up behind the blazer, so the silhouette is carried up
to her waist (120 px, 3.0 head radii on the skull calibration) along its own side
slopes and the top rows filled across the tab; that is inference, hidden by the
blazer, and it has to leave no gap above the skirt wherever the blazer is open (a
first pass carried it up only 36 px and left a band of the placeholder underwear
showing between the tunic and the skirt). The fold lines are the six clean ink
components inside the eroded hull, thinned and fitted, their ends carried on along
their tangent to meet the outline, and the upper ends on up to the waist so they
converge there as stitched-down pleats do.

**A stray line, found by the owner, and what it was.** A first emit drew a thick
horizontal line across the skirt, mid-way. It was a bug in the trace and nothing
meant to show where the blazer goes: the segment's topmost pixel is the blazer
tab's tip, one pixel on its own row, so "fill the top rows across from each row's
own extent" filled nothing there and the carried-up part was joined to the visible
skirt through a one-pixel slit. The contour walked down both sides of the slit and
drew it as a line, with a spike to the centre and back. It is now filled from the
side edges' fitted slopes, which has no such row, and a check that the silhouette
has no long near-horizontal segment other than its top edge. That silhouette fell
from 32 segments to 24 as well. The one horizontal that remains is the skirt's top
edge at her waist, where it meets the shirt: a waistband the open placeholder
blazer shows, which the traced blazer (M7) will cover.

**Folds are line work, not tone.** The reference alternates two skirt tones
across the pleats, which is a shading plane across a garment (decision 6). The
skirt is one colour, held by a test (one fill, six `fill="none"` strokes). Its
other tone, a darker band along the top and a skin shadow on the thigh under the
hem, is texture and not ported.

**The underwear showed.** Her hem sits above where the placeholder underwear
ends, which no other character's does, and the white showed as a strip under it
where the reference has bare thigh. `_underpants` now takes a `hem_cap` and
`_bare_seat` passes `_skirt_bottom_y` (a cut's own lowest point, or the
parametric hem), so underwear is never drawn below a worn skirt's hem. It changes
no other character: `refresh-ref-out.sh --check` shows only Risa.

**The leg spacing is closed.** With the skirt a cut, `hip_half_w` could go to 1.2
without the placeholder flaring into wings. Measured at five heights against the
reference's skin and sock runs, her legs are now within 1 to 7 px on the left and
within 7 to 13 px on the right at the thigh and 4 to 8 at the sock; the reference
is itself asymmetric about its own centre by a few pixels (its legs stand 62 px
left and 69 px right of 630), ours about 62 and 61. Near enough: about 0.03 head
radii.

**Left, by design:** the thigh's taper (the reference's tapers from 0.27 to 0.21
across the thigh, ours is straight) is the shared leg shape, not the skirt's.

Tests: 837 pass, plus the same three expected failures for M11; two new tests
hold the skirt's shape (one fill, six folds, her body) and the underwear cap.


### M5. The shirt and its collar

**Status: done pending the owner's sign-off, 2026-10-11.** Findings below the
checklist.

- [x] Trace the collar off `segments/white-collared-shirt.png`
      (`COLLAR_CUTS["shirt"]`, a neutral name): two points sitting over the
      lapels, opening at the throat, not the closed band `_collar` draws.
- [x] Decide whether the shirt body is the shared tunic (probably, in white) or
      needs a cut, by comparing the front, the cuffs and the hem under the
      skirt. The cuffs show white at the wrist; `undersleeve_color` may do.
- [x] Skin shows in the V of the collar above the ribbon: check the neck.

Acceptance: the collar reads as a real shirt collar at 4x, on white and black,
beside the ribbon's place (not yet drawn); only Risa's render changes.

#### M5 findings

**What the shirt segment holds.** The collar's two wings (one component, touching
at the foot of their V where the ribbon's knot sits), a narrow strip of shirt front
down the middle, two slivers beside the ribbon, and a cuff at each wrist. Only the
wings are a silhouette question: the strip and the slivers are what the lapels and
the ribbon leave visible, so the tunic draws the shirt front and the blazer (M7)
decides how much shows; the cuffs go with the sleeves (M7).

**`COLLAR_CUTS["shirt"]`**, traced by `harness/risa/trace_collar.py`, emitted by
`emit_collar.py`: the two wings as one outline of 24 segments, open above the
crossing so her neck shows between them, which the closed standing band
`_collar` draws without a cut cannot do. Her chin and the wing tips already
meet, so nothing is carried up; a first pass copied the top row upward to tuck the
wings behind the jaw and the top row of a pointed wing is its one-pixel tip, so
that drew a spike. The erosion to the stroke's centre is one pixel here and not
two: these are all sharp tips, which a wider erosion cuts back along their bisector.

**`Outfit.neckline_notch`**, a new opt-in depth for the tunic's V, in head radii
(`None` keeps every case as it was; only Risa sets it, 0.04). A traced collar sets
the V to 0.19, built for Katherina's, and on Risa it bottomed out below the point
where her wings cross, leaving a diamond of skin under them where the reference has
white shirt. Under the wings the V is now a seam. It is in the catalogue as a
range on the tunic slot.

**Checked:** the calibration holds at the throat: her chin and ours both at row 399
and the face's columns 516 to 745 against the reference's 516 to 742. The wings
sit on the reference's in the blend.

**Left for M6 and M7:** the wings crossing reads as an X without the ribbon's knot
over it, and the skin between the crossing and the tunic's top edge will be covered
by the ribbon; the reference's neck has a darker shadow tone under the chin
(texture, not ported). Tests: 842 pass; `refresh-ref-out.sh` changed only Risa's
render.


### M6. The ribbon

**Status: done pending the owner's sign-off, 2026-10-11.** Findings below the
checklist.

- [x] `Outfit.ribbon_color` (default `None`, draws nothing): trace the bow and
      its two tails off `segments/blue-ribbon.png` as fills with interior
      line work, a small unoccluded shape, which is what tracing is for. Mapped
      to the collar's landmarks so it lands at the throat.
- [x] Draw order: over the shirt and collar, under the blazer's lapels.
- [x] Catalogue entry, and a test that the other presets draw no ribbon.

Acceptance: the bow reads at figure size and at 4x, tails over the shirt front,
lapels crossing the tails the way the reference does; byte-identical elsewhere.

#### M6 findings

**`RIBBON_CUT`**, traced by `harness/risa/trace_ribbon.py`, emitted by
`emit_ribbon.py`, with `Outfit.ribbon_color` (opt-in, `None` draws nothing) and a
`RIBBON` slot in the catalogue. The bow is five overlapping pieces drawn in the
order it is tied, the tails, then the loops over their tops, then the knot over
both: each a region of the reference's blue between its black outlines, grown by
half the stroke to the stroke's centre line, 72 segments in all.

**A first pass traced it the other way and it failed.** One silhouette, plus the
network of fold lines inside it as open strokes. The network is thick and
branching, and splitting it at its junctions left eight fragments of 6 to 21 pixels
that did not describe a fold. Building it as the skill says, in drawing order, makes
the outlines the folds and needs no interior line work at all; the same lesson as
the skirt's. The branch splitter (`common.branches`) stays in the harness unused.

**Holes in a cut.** The loops' slits are white in the reference with the shirt
behind them, so a cut can now carry `holes`, `(index into fills, shape)` pairs,
drawn as extra subpaths of that fill under the even-odd rule: whatever is under the
bow shows through, the white tunic on Risa and anything else on another wearer.
Painting them white would have been right only on a white shirt.

**The line weight.** At the figure's own stroke the slits filled in solid black,
since they are narrower than the line, and the bow came out bulky. The reference
draws the ribbon in about half the weight of its silhouette, so the bow is drawn
at `_RIBBON_LINE = 0.55` of it, through `_draw_cut`'s existing `weight` for small
hardware.

**Placement.** It is traced about the collar's centre line so the bow and the wings
it is tied under share an axis, and is drawn right after the collar, over it and
before the head. The blazer's lapels (M7) will have to cross its edges; the
reference has them beside the loops and not over them.

**Left:** the highlight tick on the left tail and the bow's lighter blue strokes are
texture and not ported. The crossing of the collar's wings still shows above the
knot as a small X. Tests: 845 pass; `refresh-ref-out.sh` changed only Risa's render
(and `catalogue.json`).


### M7. The blazer

The largest piece, so it is last of the garments, and the one with the most to
get wrong.

**Status: done pending the owner's sign-off, 2026-10-11.** Findings below the
checklist.

- [x] Trace `COAT_CUTS["blazer"]` off `segments/school-blazer.png` (crop check
      first): the notched lapels, the front opening and its taper, the hem, and
      the sleeves.
- [x] **The decision point from the Keiko plan, taken on the data.** Keiko's
      panels were built from the measured profile and only the lapel traced,
      because the crop was occlusion-cut and the shoulder sat under the hair.
      Risa's hair covers her shoulders the same way. Trace both and look; fall
      back to the profile-built panel plus a traced lapel if the shoulder and
      the arm come out as stair-steps. Record which, and why, in this file.
- [x] The sleeve runs from the shoulder to the wrist and ends in the white cuff
      (a thin cuff line, or the shirt's cuff showing). Re-measure sleeve widths
      against the segment, not the composite.
- [x] Buttons: three separate gold buttons, not the cast's line of dots. Trace
      their positions off `segments/gold-buttons/`, probably a new
      `Outfit.button_color` with a count, or the existing placket given a
      spacing option. Check `_placket` first.
- [x] `Outfit.hip_pocket_color` (default `None`): a flapped pocket on each
      hip, as the reference has (the owner's call, 2026-10-11).
- [x] Draw order, hands and arms: the reference's order is sleeve, then coat,
      then hand. Decide, per the cut, the way the Keiko plan's P5 did, and keep
      it a property of the cut, never global.
- [x] Watch the bust (`bust=0.3` now): an open front bows out over it
      (`_COAT_BUST_BOW`); check the blazer's front edge against the reference.

Acceptance: region overlap and mean contour distance against the reference,
predicted before it is rendered; looked at on white and on black, 4x at the
lapel notch, the front opening, the pocket flaps, the hem and the cuff. The
other presets that wear a coat (gero, kyoko, tomohiro, keiko, katherina) are
byte-identical.

#### M7 findings

**The decision point: the whole garment is traced, sleeves and all.** The crop's
gaps are two strips beside the torso, each bounded by visible cloth on both sides
(the sleeve's outer edge, the torso's edge) and closed below by the armpit, with
only a short shoulder line open above. Her hair hides them, but they are inside the
garment's outline, so filling them is inference over one flat cloth with no seam to
place, which is a different problem from Keiko's, where panel and sleeve were traced
as separate pieces and the join left stair-steps. The shoulder runs on in a straight
line from where it is last seen (the torso at 535, 448 and 725, 450 in her composite)
to each sleeve's tip, and `trace_blazer.py` fills the strips row by row. The result is
one silhouette of 43 segments. The profile-built fallback was not needed. A first pass
quietly did not fill the strips at all (a loop bound that broke on the rows above the
sleeves' tips), which drew the torso alone with the sleeves hanging off it as 114
ragged segments; the overlay showed it, the numbers had not.

**The neck opening is read off the composite and smoothed.** The segment's own edge
there is the shirt layer's cut and ragged. `trace_blazer.py` walks in from each side
over navy and ink and stops at the first bright pixel (the ribbon's outline masked
out, since it is dark too and the walk would carry on through it), then moves the walls
to the stroke's centre line and smooths each below the collar wings to a plain slope,
which is what a lapel's inner edge is. Above, where the wings hide it, the walls run
straight up. The lapels' V tip lands on her shirt's tip.

**Lapels and lines come from the regions the ink cuts the garment into.** Labelling
the navy inside the silhouette with the ink as a barrier gives the two lapel facings,
the two fronts, the two lower sleeves and the two pocket flaps as clean regions;
growing each by half the stroke puts its boundary on the stroke's centre line. The
lapels are fills over the garment (their notches come out as corners), the front line
and the two side lines are the gap between the regions they part, and the pocket flap
is a region of its own. That replaced a first attempt at thinning the ink and
splitting it at its junctions, which broke every notch into fragments. A barrier across
each sleeve at the armpit stands in for the hidden seam while labelling, since above it
the filled strips make sleeve and torso one cloth.

**New behaviour, all opt-in.** `GarmentCut.line_weight` (default 0.7, the blazer's 1.0:
its lapel and front lines are as heavy as its edge in the reference), `Outfit.hip_pocket_color`
with `HIP_POCKET_CUT` (the traced right flap and its mirror), `Outfit.coat_button_color`
with `_COAT_BUTTONS` (three discs with a thin ring, since the reference's are separate
gold buttons and not the tunic's dotted placket), and the catalogue entries for the three
(`COAT_CUT_LABELS["blazer"]` and two slots that require a coat). Pockets and buttons are
drawn with a traced coat, after it, on whichever side of the arms the cut goes, and are
placed by the body's landmarks, so they work with any traced coat on any body.

**The arm under it is the shirt's.** The cut is the whole garment, so it is drawn over the
arms (`over_arms`, the default) and the hands come out after it. The arm tube is the long
white sleeve of the tunic (`sleeve_long`), hidden under the blazer's own sleeve, and the
white cuff is that tube showing past the blazer's end, with the tube's own outline for the
cuff's line. A first render drew `_wrist_cuff`'s band there, a second tone of white that
read as grey; it is skipped under a traced coat, which owns its sleeve.

**The arm had to move to meet the sleeve.** Her wrist stood 0.13 head radii too low and
0.14 too far in, and the tube, 0.224 across at its top and 0.202 at the wrist, was wider
than the blazer's sleeve end (0.165) and showed as a white edge along the whole outer
side. Two changes, both on her body profile and neither touching another body:
`BodyProfile.wrist_y` and `wrist_x`, new opt-in anchors (default `None`, which keeps the
arm line's formula from the hip and the arm's width) set to the shirt cuff's bottom, 3.947
down and 0.999 out on the skull's radius; and `arm_half_w` from 0.19 to 0.145, which
brings the tube to 0.17 at the top and 0.122 at the wrist and her hands to the reference's
size. `stretched` carries the anchors with the height, held by a test.

**Measured against the reference** (`harness/risa/blazer_overlap.py`, navy against navy on
the same pixels at one head scale): overlap 0.843 and a mean outline distance of 0.040
head radii (5.6 px) below the armpit, 0.771 and 0.039 over the whole garment. No
prediction was written down before this reading, which the method asks for, so these are
a reading and not the test of one. The picture (`out/risa/m7_overlap.png`) shows where the
rest goes: a thin red edge along the outline, hers navy where ours is ink, since our
stroke is a little heavier than hers; our hair counted as navy on the shoulders, since
the two darks are within the colour tolerance; and the sleeve ends, where ours sit a few
pixels inside. No systematic offset.

Looked at on white and on black, whole figure, 3x on the lapels and the cuff, and with
two other palettes (a cream blazer over a red skirt, and the same cut on Satoko, whose
body differs). The notches, the front line, the pocket flaps, the buttons and the hem
read; the blazer separates from her black hair by its outline on black.

**Left, each for its own step:**

- Her hair covers the shoulders in the reference and ours is narrower, so our inferred
  shoulder line shows where hers hides (M8).
- The darker strip along the inside of each sleeve, and the shadow tone on the lapels'
  inner edge, are texture and not ported (decision 6).
- The hands are still the shared mitten; the reference draws fingers. Not in this plan's
  scope unless the owner asks.
- Her neck's colour: the reference's visible neck is a warm, darker skin tone under the
  chin (about #d9a589 against the face's #f6dbc2). `FaceStyle.chin_shadow` was tried and
  came out a dull grey-tan, since `shade()` darkens without warming, so it is off and the
  neck stays flat skin (the owner's rule on the throat, `_neck`). Open for M9 or M10.

**The neck, after the owner looked at the side-by-side** (`harness/risa/side_by_side.py`
writes hers, ours and the blend). Three differences were real and are fixed:

- *Width.* Ours was 0.40 head radii a half, the chibi's neck; hers is 0.151 on the skull's
  radius (25 px). `BodyProfile.neck_half_w` is a new opt-in anchor, set only on
  `tall_slender`, carried through `head_scaled` and `applied`; `stretched` already keeps the
  neck's width. A test holds that only that body sets it.
- *The double line beside the collar.* The opening's walls were read at the white's edge
  and sat three or four pixels outside the wing's own outline, so the two strokes read as
  one heavy, doubled line. Above row 470 the wall now lies on the wing's outline
  (`collar_trace.json`), so the two coincide.
- *Skin round the ribbon's knot.* The tunic starts at the shoulder line, 27 px below where
  the wings cross, and the neck's skin showed in the gap. `COLLAR_CUTS["shirt"]` has a
  first fill, the shirt front under the crossing, drawn under the wings. A thin white
  sliver with the fill's outline still shows round the knot's top.

The knot also sits about 4 px lower than hers (M6, not moved).

Tests: 852 pass, `ruff` green; `refresh-ref-out.sh --check` and `refresh-catalogue.sh`
changed only Risa's render and the catalogue, every other character byte-identical. Seven
new tests hold the cut's shape, the two opt-in parts and that only Risa wears them, the
shirt's arm without a band, the wrist anchors (set only on her body) and their stretch.

### M8. The hair and the bangs

**Status: done pending the owner's sign-off, 2026-10-11.** Findings below the
checklist.

- [x] Run `harness/hair_audit/gate.py` first. Not applicable: it checks a hair
      reference against `katherina_grok`'s body, to keep a hair traced off a
      reference whose body is not ours. Her reference is the body `tall_slender`
      was measured off (M2), so nothing below the chin is taken from a foreign body.
- [x] Trace the fringe, the long mass and the side locks, **and the lines in the hair**
      (`harness/risa/trace_hair.py`, `emit_hair.py`), as the new cut `long_fringed`.
- [x] The ears, the crown and the hairline against the face, at 4x.
- [x] Check it clears the arms and the blazer: the front is drawn over the blazer, the
      way hers lies in front of her shoulders.

Acceptance: the fringe is blunt, the locks hang straight in front of the shoulders and
every other preset's hair is byte-identical (`refresh-ref-out.sh --check`).

#### M8 findings

**The hair is the composite's, not the layers'.** `segments/long-black-hair.png` and
`bangs.png` are flat fills with only some of her line work: they hold the silhouette and
the fringe's lines but not the darker strips and the lines between them, which only the
composite has (the owner's reminder, mid-step, that her blacks come in shades). So the
outline comes from the two layers together and everything inside it from the composite,
read two ways: a **thin dark line** is a black-hat of the luminance (dark runs narrower
than seven pixels, whatever tone they lie in), and the **darker hair** is the second tone
(21, 22, 24) against the main fill (39, 40, 44), a wide region once the lines are opened
away. A plain ink threshold found a third of the lines, because many are thin and grey.

**What `long_fringed` is** (a `Hairstyle`, body-relative like `long_traced`, `covers_ears`):

- *The front piece*: both layers as one U-shaped silhouette, the fringe, the face
  opening and the two curtains of locks, as one closed outline (143 segments), all of it
  stroked. Her outer outline lies just outside the layer's mask and the opening's inside
  it, so the outer ink is added before the whole is eroded by half the stroke.
- *The mass behind*: the same silhouette with the gap between the two curtains closed
  below the chin, where the blazer hides it. Not the whole row's span: the daylight
  between a curtain's outer lock and its inner one has to stay open (a first pass
  filled it and left a flat ledge between the tips).
- *The strands* (`_FRINGED_STRANDS`, 28): the lines that part the hair into locks, open
  chains, found by thinning, pruning spurs (`common.prune`, which Zhang-Suen's rough
  edges need) and cutting at junctions. Her thin lines are grey along their length and
  black only in places, so they are found by hysteresis: every line-like pixel that
  touches a strong one. Left out: blotches (the streaks in the flaps), near-horizontal
  marks at the fringe's foot (her eyebrows showing through it, the face's), strokes lying
  along the outline (half of one is clipped away and it reads as dashes) and short
  fragments below the fringe. They are drawn at `Hairstyle.strand_weight` 0.8 of the
  outline, where the default is 0.55, since her lines are bold.
- *The flaps and the hair behind the neck belong to the mass.* A first pass traced them
  as part of the front, and the hair met the blazer in a doubled line with a wedge of
  mass between (the owner's circle on the neck and shoulders). In the reference the
  flap is hair behind the blazer, whose outline is the one line there. So the front is
  cut along the curtain's inner edge, which runs straight on past where the flaps hang,
  and the flaps and everything between the curtains below the ear are the mass's, in
  the second tone (`Hairstyle.underside`, `_FRINGED_UNDERSIDE`), under the blazer.
- *The darker hair* (`Hairstyle.front_shade`, `_FRINGED_SHADE`, 2 regions: the outer strips): her strips down
  the outer side of each curtain and the flaps beside the neck, painted in
  `_HAIR_UNDERSIDE_VALUE` of the hair colour, clipped to the front. The flat-colour
  rule allows a second tone on hair that lies behind (`underside`, the same call).
- *The openings* (`Hairstyle.openings`, two): patches of skin drawn over the hair, her
  ears peeping out between the locks. They are the layer's holes, ringed by ink, and are
  drawn skin-filled rather than cut, since our own ear sits elsewhere on a wider face.
  A third, a small skin gap in her fringe, is left out: it read as a scratch.
- *The contour is rounded along its length* (a Gaussian of 2.5 px on the coordinates)
  before it is fitted, since a mask's edge is a staircase and her edges are long curves.
  That took the fringe's opening from a jagged line to her V parting.
- `_fall_q` is `_parted_q` with the traced tip depth as a parameter; the parted cut calls
  it, so it draws as before. Her `hair_length` is 0.716, which puts the tips at the traced
  3.441 head radii and makes the stretch the identity.

**Palette check:** red hair on dark skin, blond hair, and black on black. The second tone
derives well on all three.

**Left:**

- The lock tips are blunter and about 15 px shorter than hers: her tapers are under four
  pixels wide for the last stretch, which the erosion to the stroke's centre removes, and
  our outline is heavier than hers.
- The strokes are constant in width; hers taper.
- The flaps' streaks and the noisy temple patches are not ported.
- The fringe's tabs are narrow under our heavier stroke, so the notches between them read
  as thin spikes.
- The hair covers less of our shoulders than hers where the blazer's inferred shoulder
  line shows (M7's open item), now hidden under the front hair.

**A sliver beside each sleeve (found by the owner on the dark red hair).** Along each outer lock
a thin strip of the hair behind showed between the blazer's sleeve and the lock's inner edge, with
two outlines a few pixels apart and a hooked top. Her blazer, traced with the hair over the
sleeve, stops 3 to 7 px short of her outer locks (`blazer_sil.npy`'s edge against the layer's),
so ours had a gap she does not. The black hair had hidden it. The hair is now taken out to the
sleeve's edge in rows 455 to 700 (`GAP_ROWS`, at most `GAP_MAX` 14 px), on both sides, and the
filled strip is in the darker tone of the strip beside it: the two outlines are one, and the
dark strip meets the sleeve as hers does.

Tests: 859 pass, `ruff` green, `refresh-ref-out.sh --check` shows only Risa and the
catalogue changed. Her eyebrows over the fringe are M9's: the face is drawn under the hair, and
hers are drawn over it.

### M9. The face

**Status: done pending the owner's sign-off, 2026-10-11.** Findings below the
checklist.

- [x] Compare the eyes against `segments/large-black-eyes/`, tune `FaceStyle`, trace only if
      the fields cannot reach the shape. They reach it: no tracing.
- [x] Green eyes that hold against black hair and a dark lash line.
- [x] Brows, mouth, blush: calm and neutral, a short mouth low in the face, a tiny nose mark.
- [x] `face_age` by eye, from 0.75 to 0.85: **0.75**, the low end, for the rounder jaw.

Acceptance: a calm, neutral, clearly young-adult face that reads beside the reference at one
head scale.

#### M9 findings

**Method.** `harness/risa/face_compare.py` lays her face and variants of ours side by side at one
head scale (`BOX` is the face, 3x) and takes each variant as a dict of `FaceStyle` fields and
`CharacterParams` fields, so a sweep is a list of dicts. Several rounds, each changing a few
fields, picked by eye against the blend and not by a number.

**What her eyes are against ours: measured, then solved.** The two eye layers
(`segments/large-black-eyes/`) are true crops of the composite, at (518, 255) and (663, 257), so
the eye can be read in her own pixels (`harness/risa/measure_eyes.py`, `eye_metrics.py`). Each
aperture is 63.5 wide and 66.5 tall, so a tall oval, nearly round, where ours was 1.43 wide for
each unit of height. Her iris is 48.5 wide, 76% of the aperture, **as tall as the aperture**
(an oval about 1.37 tall for its width, clipped by the lids), set **against the inner
corner**: the white shows on the outer side only, a crescent 15 px at its widest. The two
apertures' centres are 137 px apart, a gap of 75 px between the eyes, about one eye (1.16 of the
aperture's width).

A first pass by eye (a sweep of `eye_size`, `eye_width`, `iris_size`...) had the iris at 60 px,
1.25 times hers, and read as filled only because it was clipped by a small aperture. Solving for
her numbers, `eye_metrics.py` against `RISA.face`: `eye_size` 1.009, `eye_width` 0.729,
`iris_size` 0.978, `eye_gap` 1.157, the lids even (`eye_openness` and `eye_lower_lid` 1.0),
`eye_corner` 0.2 for the round oval and `lash` 1.2. That was a variant the owner asked for, and it is the one in
the preset now. The first pass's values are in the commit before it, `6023132`.

**Why the matched eye read cold, and what fixed it** (the owner: hers reads friendly, ours
creepy). The numbers matched and the feeling did not. Looked at 6x beside hers:

- *Bare white all round a bright iris.* Hers has a heavy upper lid that comes down over the top
  of the iris, a grey lid shadow along the top of the white, and a dark, quiet iris. Ours had the
  whole iris showing under a thin lash, a stark white crescent and a bright saturated green:
  a stare. So the lid comes down (`eye_openness` 0.9 with `eye_size` and `eye_width` re-solved
  to keep her aperture, `iris_aspect` 1.5), the lash is as heavy as hers (`lash` 1.6, about
  12 px at its thickest), the white takes a lid shadow (`lid_shadow` 0.15, a second tone on a small
  element) and the green is deeper (`#3c7a50`; the owner's green, not the first pass's `#4f9a5e`).
- *A face with nothing in it.* A flat mouth, two ticks for a nose, flat brows close over the lid.
  Hers has one dot of a nose, a short mouth that turns up a little and brows with air under them.
  So `nose_dot`, `mouth_curve` 0.6 at `mouth_width` 0.5 and `brow_tilt` -0.15.

Two more opt-in fields for that: `lid_shadow` (0, a greyer band along the upper lid on the white)
and `nose_dot` (False, one small dot where the ticks would be). The eye's measurements are
unchanged by the lid (`eye_metrics.py` still reads her 63.5 by 66.5, an iris 48.5 and a centre
distance of 137), because the solve was repeated with the lid at 0.9.

**Seven new opt-in `FaceStyle` fields**, since no existing one reached them (every other face
renders as before, `refresh-ref-out.sh --check`):

- `eye_gap` (None keeps `_EYE_GAP`): the gap between the eyes as a share of an eye's half-width.
  A narrow eye keeps its gap proportionate to itself, which put her tall pair too close;
  hers is 1.157.
- `iris_inset` (0.0) and `iris_aspect` (1.0): the iris against the inner corner, by a share of
  the room it has, and a tall oval iris. `gaze` sends both eyes the same way and cannot do the
  first; a circle cannot fill a tall aperture without growing too wide for it.
- `mouth_drop` (0.0): the mouth lower in the face, in head radii. Hers is 0.06 lower and about
  two thirds as wide (`mouth_width` 0.45).
- `brows_over_hair` (False) and `brow_length` (1.0): her brows are drawn through the fringe, as
  short arcs. The brow is now `_brow`, and `_brows_over_hair` draws it after the front hair
  when asked; the stock face draws them where it always did. Hers are arcs and ours are
  straight lines.

**`face_age` 0.75.** The age moves the jaw and little else: at 0.5 the jaw is rounder and
wider, nearer hers, and at 0.85 it narrows to a V. The owner's range is 0.75 to 0.85, so the
low end, which is the rounder jaw. `out/risa/face_age_strip.png` shows 0.50, 0.65, 0.75 and 0.85
for the owner's call on going lower.

**Left:**

- Her jaw and chin are wider and rounder than any of ours: the skull's shape is the build's and
  not a `FaceStyle` field (`_head_shape`), and the head's width was already matched at one
  scale in M2. Only a lower `face_age` brings it nearer, and the owner set the range.
- Her iris is grey with a lighter lower half, a softer look than our flat band and a darker
  rim; the highlight pair is at the same places.
- The eyes' lash wing droops down and out at hers and flicks up at ours.
- The web tool's ranges (`FACE_RANGES`) do not reach these values (`eye_width` 0.85 to 1.10,
  `iris_size` 0.60 to 0.80). Risa is not a web starting point until M11 decides whether to widen
  them.

Tests: 863 pass, `ruff` green, `refresh-ref-out.sh --check` shows only Risa's render changed.

### M10. Colours and finish

**Status: done pending the owner's sign-off, 2026-10-11.** Findings below the checklist.

- [x] Move every colour to a modal-exact sample, one layer at a time.
- [x] A palette very different from the defaults (red hair, brown eyes, a cream blazer), and
      black on black on white and on black.
- [x] `height` by eye: the default 1.0 stays.

#### M10 findings

**Colours** (`harness/risa/colours.py`). Her fills carry a faint mottle, so the exact mode of a
fill is a weak statistic (the hair's is 18% of its pixels, the ribbon's 1%) and the per-channel
median of the eroded interior is the steadier read; the two agree to within one or two steps. The
first pass (M0) had been a 6-level histogram, good to a step per channel, and every colour was
within three of the new reading. Moved one layer at a time, each step rendered and the pixels it
changed counted (`out/risa/apply_colours.py`, not kept: it is the commit's diff), each landing only in
its own layer, by no more than 3 a channel except the buttons (7):

| Layer | Was | Now |
| --- | --- | --- |
| Hair | `#27272d` | `#27282b` (then `#6b1f2a`, see the note at the top) |
| Blazer, hip pockets | `#1b2739` | `#1c2838` |
| Skirt | `#818da5` | `#808ea7` |
| Ribbon | `#467b99` | `#467a98` |
| Shirt (tunic, cuffs, collar) | `#f9f9f9` | `#f8f8f8` |
| Loafers | `#453327` | `#433228` |
| Gold buttons | `#bd9957` | `#ba975e`, the mean of her three buttons' medians |
| Knee socks | `#262729` | unchanged: the mode, and 50% of the fill |

**Not moved: the skin.** Hers samples at `#fbd9c0`, pinker than ours; the owner's M0 call was
to keep Satoko's `#f6dbc2`, and it stands. Her eyes are green, the owner's, and were set in M9.

**A palette far from the defaults.** Red hair, brown eyes, a lighter skin, a cream blazer with
pockets to match, a deep red skirt, a green bow, white socks and black loafers
(`out/risa/m10_palettes.png`). The second tone on the hair, the lid shadow and the outline all
derive and read; nothing is hard-coded to her dark palette.

**Black on black.** Hair, blazer and socks on white and on a black page: the hair's fill is a
visible step lighter than the black, the blazer is blue against it and the outline separates the
socks from the legs and the loafers. Nothing merges.

**Height.** `harness/risa/height_check.py` places her and ours at one head scale: hair top at
45 and 46, sole at 1515 and 1506, the width of the hair 416 to 853 on both. Ours is 10 px shorter in
1470, 0.7%, which `height` 1.007 would close; not worth leaving the default for. It stays 1.0.

Tests: 863 pass, `ruff` green, `refresh-ref-out.sh --check` shows only Risa's render changed.

### M11. Integration

**Status: done pending the owner's sign-off, 2026-10-11.** Findings below the checklist.

- [x] `catalogue.py`: every new field has its control and label; each registry's assert holds.
- [x] `catalogue.json`, `ref-out/risa.*` refreshed; `refresh-ref-out.sh` reports only Risa, the
      two cast sheets and `catalogue.json` changed (the sheets: see below).
- [x] README (the Risa row and the hairstyle list), `docs/api.md` (the new `Outfit`, `FaceStyle`
      and `Hairstyle` fields and the `tall_slender` body). `CLAUDE.md` and the README say
      "fourteen named characters plus guests", which is still true: she is a guest.
- [x] The cast sheet at tile size, Risa beside Satoko, Keiko and Katherina.
- [x] The web tool restaged (`web-stage.sh`) and looked at in a browser.
- [x] `ruff check`, `ruff format --check`, `pytest` green.

#### M11 findings

**A latent bug the cast sheet surfaced.** At tile size Risa's irises were gone: white discs for eyes.
`sheet.py` pasted every figure into one SVG without namespacing its ids, and the eye's clip path is
`eye-l` in every figure, so a viewer clipped Risa's iris to another figure's aperture. Until her, every
character's eye sat in nearly the same place, so the wrong clip happened to fit. `render_character`
already had an `id_prefix` for this (the comic uses it); the sheet now gives each tile its own
(`id_prefix=preset`), and a test holds that every id on a sheet carries a preset's name. The two
committed cast sheets changed for that, in their ids only.

**The web tool.** Her tile loads her; her values sit inside every slider, because the catalogue's
ranges were widened to cover her (the rule there is the min and max across the presets, plus a
margin): `eye_size`, `eye_width`, `eye_tilt`, `eye_corner`, `iris_size`, `lash` and `mouth_width`
reach further, and six new sliders (`eye_gap`, `iris_inset`, `iris_aspect`, `lid_shadow`,
`mouth_drop`, `brow_length`) and two switches (`nose_dot`, `brows_over_hair`) were added.
Driven in the page: each control is there at her value, moving them redraws the preview (the
iris, the spacing and the mouth), and the console has no errors.

Tests: 864 pass, `ruff` green.

## Risks

- **The reference body is not ours, and the reference is AI-generated.** A new
  body profile is a measurement of one picture, so it can encode that picture's
  quirks. Mitigation: landmark-to-landmark mapping, two independent calibrations,
  and the owner's sign-off on proportions before any cut depends on them.
- **Occluded regions.** Her hair hides the shoulders and the upper sleeves, the
  skirt hides the thigh tops, the hands hide the sleeve ends. Shape there is
  inference. Where the Keiko plan hit this it built from the measured profile
  and traced only what was unoccluded.
- **Segments that are not crops.** An AI layer export may be a regenerated
  variant, not a crop. Offset search before using any coordinate.
- **Age and the reference disagree.** It reads younger than 18. The owner's age
  wins and `face_age` is tuned, not the reference copied.
- **Shared garments serve many presets.** New behaviour is a new field, a new
  named cut or a new profile, never a reshaped shared garment.
- **Black on black.** Hair, blazer and socks are all very dark: outline and
  `shade()` tones have to keep them apart, checked on black as well as white.
- **Scope creep.** No poses, no new skeleton, no realistic build (retired).
  Nothing here touches the consumer repo.

## Owner's decisions (2026-10-11)

1. **`face_age` is judged by eye.** Start at 0.75 to 0.85.
2. **The hip pocket flaps get a new field.** Opt-in, default draws nothing.
3. **Default height for now**, revisited by eye at the end (M10). Her longer legs
   come from her own body profile (M2), not from `height`.
4. **Display name is just "Risa".** (Her entry in `DISPLAY_NAMES` is still
   needed: the label is "Risa" and the entry is its only home.)
5. **Trace her clothes properly, and measure her body, step by step, as close to
   the reference as is feasible, not quickly.** This replaces the first plan's
   "parametric first, trace only small shapes".
6. **Order is the plan's.** The owner left it open; this file's order stands
   (body, legs, skirt, shirt, ribbon, blazer, hair, face).
