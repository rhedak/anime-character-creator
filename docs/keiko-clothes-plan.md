# Keiko clothes plan

Porting Keiko's lab coat and the clothes under it off her new design
reference, `ref-local/keiko-tall-chibi/` (`keiko-tall-chibi.png`, the full
composite, plus its `segments/`), by tracing, the method the hat, the staff,
Katherina's clothes and Satoshi's katana were built with
(`.claude/skills/trace-reference/SKILL.md`). Written 2026-09-21 at the owner's
request.

Scope is the clothes only: the lab coat, the dress under it, the belt and the
sleeve cuffs. Hair, face, glasses and boots are not in this campaign, and
neither is her body height (see "The number that is not settled"). Each
milestone is its own render/iterate/sign-off pass, not a batch edit.

Campaign status lives at the top of each milestone.

## What is wrong now, measured and looked at

Reference measurements are in head radii on the calibration below, y down from
the head centre, x as signed half-widths. Ours is `out/keiko.png` at
`07617fb`, on her current body (`tall_chibi_long_torso`, since she sets no
`body`).

| Area | Reference | Ours |
| --- | --- | --- |
| Coat front, upper | a notched lapel: the collar tip starts at 0.79, widens to a stepped notch at y 1.24, x ±0.40 to ±0.43, with the two lapel faces meeting in a V | one "lapel point" vertex per panel (`_COAT_LAPEL_OUT`, `_COAT_LAPEL_UP`), no collar band, no notch |
| Coat front, the opening | never closes: 0.580 wide at the throat, narrowing to a 0.45 plateau from y 2.0 to the belt, then widening steadily to 0.687 by y 4.75. A gentle waist pinch, not a close | narrow and nearly vertical, and the dark strip it shows is about half the reference's width |
| Coat below the belt | the panel alone flares from 0.845 at y 3.80 to 1.169 at 4.80, about 38% | flares only to match a worn skirt (`out_hem`) |
| Coat hem | y 4.97, each panel curving to a rounded point (half-width falls to 0.924 in the last 0.07) rather than a flat cut | a flat cut at `coat_length`, and shorter |
| Coat sleeve | continuous from the shoulder to the wrist, ending at y 3.70 | reads as a detached rectangle starting at hip height, the coat covering the upper arm above it. The same defect Katherina's campaign recorded as "the arm tube emerging mid-torso" |
| Throat | a charcoal mock collar closes it: top at 0.856, half-width a constant 0.276 down to 1.05, no flare | a bare skin V from the chin down to the coat's opening (verified at 3x zoom, not inferred) |
| Dress | reads as one piece: one interior seam, at the collar, none at the waist. Half-width 0.214 at the belt, 0.276 at y 3.80, 0.327 at 4.80, a straight flare; hem a flat cut at **4.868**, just above the coat's own 4.97, with bare leg skin from 4.890 | `tunic_color` plus `skirt_color`, two near but not equal tones, not tucked |
| Belt | white `#ececec`, worn **over** the coat, band y 2.518 to 2.806 (centre 2.662), 0.220 thick, crossing to x ±0.64; a buckle 0.299 by 0.220 centred on x +0.015, a `#8c8478` frame around a dark interior 0.214 by 0.180; and **two** keeper loops at x ±0.43 to ±0.52, each 0.085 to 0.090 wide and 0.28 tall, standing proud of the band | dark `#33332f`, under the coat, visible only in the gap; one keeper; buckle proportional to the band, not parametrized |
| Sleeve | a thin cuff line at y 3.63, sitting 0.01 to 0.02 above the sleeve's end, with the wrist at 3.65 | a filled grey `undersleeve_color` band (`_wrist_cuff`) |
| Hip pockets | none | none either. What reads as pockets in our render is the sleeve tops drawn over the coat panels; no pocket code exists for the coat |

Sampled flat colours, eroded medians: coat `#eeeeee`, its outline `#0e0e0e`,
dress `#373833`, belt `#ececec`, buckle frame `#8c8478` (a warm brass, not a
neutral grey) around a near-black interior. Ours today: coat `#eceded`, tunic
`#3f3f3a`, skirt `#3a3a35`, belt `#33332f`.

All three garment segments are true pixel crops of the composite, checked by
offset search. The crop's top-left corner in the composite, as (x, y):
`white-lab-coat.png` at (398, 530) with mean RGB difference 0.012,
`dark-gray-dress.png` at (564, 540) at 0.015,
`belt-with-buckle.png` at (509, 839) at 0.097. This is not the grok
regenerated-variant case, so coordinates may be taken off the segments
directly. That check is a standing requirement, not a formality: the witch hat
lost two passes to a layer export that was a different geometry.

Texture in the reference, on the record as deliberately not ported, per
`CLAUDE.md`'s flat-colour rule: antialiased edge blending, a soft cheek blush
with no second flat tone, and stroke-width variation in the hair line work.
The reference is otherwise already flat, one tone per region.

## Calibration, and the number that is not settled

**Calibration used: head centre (625.5, 394.0), 177.5 px per head radius**
(`harness/keiko/landmarks.py`, which re-derives it every run). That
is this repo's own accepted method, the widest row of face skin taken as the
head's diameter, the same one
`harness/body/satoshi_tall_chibi_landmarks.py` used for Satoshi's tall chibi
and the same one its docstring flags as an estimate rather than a trace-grade
calibration.

Two alternatives were tried and rejected, recorded so they are not tried
again:

- **The equator-to-chin vertical run** gives 136.5 px per head radius, 23%
  lower. It is contaminated: the skin component continues below the jaw into
  the neck and stops where a collar cuts it, so the "chin" it finds is a
  garment edge. On Satoshi's katana composite the same measurement returns a
  run of 182 px against Keiko's 111, which is the contamination, not a
  proportion difference.
- **A least-squares circle fit to the visible jaw arc**, which should measure
  the skull directly, returns R = 141.8 on Satoshi's composite against his
  known-good 171.5, a 17% error. The jaw in this style is not a circular arc;
  it tapers to a point. Centre x came out right (625.8 against 626.0), so the
  method locates the centre line and nothing else.

The widest row is a plateau 35 rows deep, so the single argmax row slid by
0.06 head radii with the colour tolerance. The harness takes the plateau's
median row instead, which is why the centre reads 394 here and 401 in K0's
first pass.

**The number that is not settled, and is out of this campaign's scope:** at
177.5 px per head radius the reference's sole sits 6.36 head radii below the
head centre, so it stands **3.68 heads**, against the **3.245** our
`tall_chibi_long_torso` computes. The reference figure is about 13% more
elongated than the body we draw her on. If the true radius is nearer 186 the
figure is 3.51 heads and the gap nearly closes, which is why this is flagged
rather than acted on. It is a body question, the owner asked for clothes, and
the traced-cut machinery maps landmark to landmark (shoulder, waist, hip, hem,
ankle) rather than by absolute head radii, so it re-anchors to whatever body
Keiko ends up on. Every absolute number in this document rides on 177.5 and is
good to about 5% for garment work; any conclusion about her height is not.

## The decision this campaign rests on: reuse the traced-cut machinery

Katherina's campaign (`katherina-clothes-plan.md`) already built exactly what
this needs, and this campaign adds entries to it rather than new machinery:
`COAT_CUTS`, `COLLAR_CUTS`, `BELT_CUTS`, `SLEEVE_CUTS` are string-keyed
registries, each holding one entry today (hers), selected per character by an
`Outfit` field, with `None` drawing the shared parametric garment exactly as
now. `_traced_coat` returning true makes `_coat` return "" for that character
and nothing else.

That matters here because the blast radius of touching the shared garments is
large and the reward is zero: `_coat` serves gero, kyoko, tomohiro and keiko;
`_belt`/`_belt_drawn` serve **all 17 presets**; `_tunic` serves all 17;
`_skirt` serves katherina, satoko, chiyo, keiko and reika. A traced cut
touches only its wearer.

So: **Keiko's coat, collar and belt become named cuts; the shared parametric
garments are not reshaped.** Cuts are registered under neutral names
(`"lab_coat"`, not `"keiko_coat"`) so any character can wear them, the way
`long_traced` is a hairstyle anyone can pick.

Two consequences to accept up front:

1. `_wears_cuts` gates every cut to `sk.build < 0.5`, the chibi range. At
   `--build realistic` Keiko falls back to the parametric coat and will not
   match the reference, exactly as Katherina does today. Deferred, K7.
2. Two tests name Keiko and will have to move with the change, deliberately:
   `test_the_coats_lapel_actually_reaches_the_neck`
   (`tests/test_smoke.py:1422`, parametrized over keiko, kyoko, tomohiro) and
   `test_a_belt_worn_with_an_open_coat_is_drawn_under_it` (`:592`,
   parametrized over keiko, kyoko, gero, tomohiro). Both keep their other
   presets; Keiko leaves them and gains her own.

## Milestones, and why this order

Back to front, the order things are drawn in and the order they occlude each
other: the dress is behind everything, the coat frames it, the belt sits over
the coat, the cuff is a detail on the sleeve. Doing the coat first would mean
judging its opening against a throat that is still wrong.

### K0. Groundwork (no visible change)

**Status: done, 2026-09-21.** `harness/keiko/landmarks.py` re-derives the
calibration and prints every number the table above quotes;
`harness/keiko/compare.py` writes `out/keiko/compare.png`, the whole figure
and the coat front at 2x, each side cropped to the same head-radius window on
its own calibration, on white. No `src/` change, no snapshot change.

What K0 changed in the measurements it inherited, recorded rather than
silently corrected:

- **Retracted: "the coat's fronts close to a 0.05 gap at the waist."** That
  reading came from inside the belt's rows. The crops are occlusion-cut, so
  the belt is missing out of the coat crop, and the one row at the cut's edge
  leaves a residue that measures as a tiny gap; at 0.011 head radii further
  down it jumps to 0.468. Measured clear of the belt, the opening never
  closes at all: 0.580 at the throat, a 0.45 plateau from y 2.0 to the belt,
  then widening to 0.687 by 4.75. The scope this closes: the coat's opening.
  K2's spec changed with it.
- **Retracted: "flares about 80%, 0.65 at the belt to 1.16 near the hem."**
  The 0.65 was the belt's own extent standing in for the coat, which the belt
  does not span. The panel's own edge is only measurable below the sleeve's
  end at y 3.70, and there it runs 0.845 at 3.80 to 1.169 at 4.80, about 38%.
- **Confirmed**, within the calibration's own slop: shoulder y 1.420 at
  half-width 0.941; coat top 0.794; dress collar top 0.856 at a constant
  0.276; belt band 2.518 to 2.806, 0.220 thick; two keepers 0.085 to 0.090
  wide standing 0.28 tall; colours `#eeeeee`, `#373833`, `#ececec`, `#8c8478`.
- **The segments are true pixel crops**, at mean RGB differences of 0.012,
  0.015 and 0.097. The offsets in K0's first pass were reported as (y, x) and
  read as (x, y), which is why they first appeared not to match at all.
- **Question 5 answered.** The dress hem is a flat cut at y 4.868 with bare
  leg skin from 4.890, so it ends just **above** the coat's 4.97 rather than
  running longer. No leg crop was needed; the dress crop's own bottom rows
  are the hem.
- **Seen in the comparison, not in the numbers:** our coat's sleeve reads as a
  detached rectangle starting at hip height, with the coat covering the upper
  arm above it. K2 has to draw a sleeve continuous from the shoulder.

`harness/keiko/` holds the pass's scripts, the way `harness/katana/` and
`harness/clothes/` hold theirs: a `landmarks.py` that re-derives the
calibration and prints every measurement in this document so the numbers have
a runnable source, and a `compare.py` that crops the reference and our render
to the same head-radius window from each one's own calibration and writes
`out/keiko/compare.png` (the katana pass's `compare.py` is the template).

Acceptance: the harness reproduces the table above, and the comparison image
exists for every later milestone to be judged in. No `src/` change, no
snapshot change.

### K1. The dress and the closed throat

Cheapest thing first, and it may need no new shape code at all:
`collar_color` plus `_collar` already draws a standing band that closes at the
throat, which is what a mock neck is. Try the fields before writing anything:
`collar_color` at the dress tone, `tunic_tucked=True`, and one colour for
tunic and skirt.

- Target: collar top 0.856, half-width a constant 0.276 with no flare down to
  y 1.05. Dress half-width 0.214 at the belt, 0.254 at y 3.40, 0.276 at 3.80,
  0.307 at 4.40, 0.327 at 4.80, a straight flare, and a flat hem at 4.868.
- Predict before rendering: how far `_collar`'s band top lands from 0.856.
  Write the number down, then measure it.
- Only if the band cannot be made to sit right does this become
  `COLLAR_CUTS["mock"]`, traced off `segments/dark-gray-dress.png`'s collar,
  whose one interior seam is the band's lower edge.
- The hem sits just above the coat's, so `skirt_length_chibi` has to place it
  against the coat rather than against the legs, and K2 may move it again.

Acceptance: the throat reads as cloth, not skin, at 4x zoom, on white and on
black; `skirt_length_chibi` still lands the hem where the reference's does.

### K2. The coat: `COAT_CUTS["lab_coat"]`

The campaign's main shape. Traced off `segments/white-lab-coat.png`, which is
a verified crop, as one `GarmentCut` beside `"open_jacket"`.

- The silhouette: coat top 0.794, shoulder y 1.420 at half-width 0.941; the
  opening 0.580 wide at the throat, a 0.45 plateau from y 2.0 to the belt,
  0.490 at 3.0, 0.603 at 4.0, 0.687 at 4.75; the panel's own edge 0.845 at
  y 3.80 growing to 1.169 at 4.80; each panel curving to a rounded point at
  4.97, its half-width falling to 0.924 over the last 0.07, rather than a flat
  cut.
- **The opening is a gentle pinch, not a close.** Ours widens monotonically
  from throat to hem (`gap_top` under `gap_hem`); the reference narrows to the
  belt and then widens. Getting that one reversal right is most of what makes
  the front read as tailored.
- The sleeve is continuous from the shoulder to its end at y 3.70, and ours is
  not (K0's comparison). The cut has to carry the sleeve, not leave the arm to
  emerge from a hem partway down the torso. `SLEEVE_CUTS` is where that lives.
- The lapel: the collar tip starts at 0.79 and widens to the notch at y 1.24,
  x ±0.40 to ±0.43. The notch sits about 60% of the way in from the shoulder
  edge toward the front opening, and it is **interior line work, not
  silhouette**: the outer edge of the panel runs past it unbroken. Trace it as
  the skill's interior-stroke case (erode the hull, take the dark pixels
  inside, fit an open chain), not as part of the closed contour.
- The reference has **no separate collar band** behind the lapel: what reads
  as the collar is the lapel's own pointed tip, with the dress's mock collar
  showing between the two tips. So no new collar-band field is wanted here,
  and K1's dress collar is what fills that space.
- Sleeve widths below the elbow in the measurement pass are an outer envelope
  that includes the forearm, not a clean panel width. Re-measure any sleeve
  number against the segment, where the sleeve is a separate shape.

Acceptance: region overlap and mean contour distance against the reference,
predicted before it is rendered and recorded with the commit. Looked at on
white and on black, 4x at the notch, the waist pinch and the hem corner.
`test_the_coats_lapel_actually_reaches_the_neck` keeps kyoko and tomohiro.

### K3. The belt, over the coat

`BELT_CUTS["lab"]` beside `"buckled"`, and the z-order decision from
Katherina's C5 applies unchanged: **the order depends on the cut, never
globally.** `render_character`'s layer list hardcodes belt-under-coat whenever
`coat_color` is set, deliberately (drawn over the shared panels it "stopped
short of the arms and read as a patch"); the traced path already draws its
belt after its jacket in `_traced_coat_and_belt`, which is the seam this cut
rides on.

- Band y 2.518 to 2.806, centre 2.662, thickness 0.220, crossing to x ±0.64,
  so it covers the coat's front and a little of the side panels but stops well
  inside the shoulder envelope at ±0.94.
- Buckle 0.299 wide by 0.220 tall centred on x +0.015, a `#8c8478` frame
  around a dark interior 0.214 by 0.180. `_belt_drawn` already draws a frame,
  an inset and a pin line, so this is a colour and proportion question, not
  new shape.
- **Two** keeper loops, spanning x -0.515 to -0.431 and +0.465 to +0.544,
  0.085 to 0.090 wide and 0.28 tall, so they stand proud of the 0.220 band
  by about a third of its height. `_belt_drawn` draws one today; the second
  is the only genuinely new shape here, and it must be opt-in, since that
  function serves all 17 presets.

Acceptance: the belt reads as worn over the coat at 4x, with no patch effect
at the arms, which is the failure that put it under the coat in the first
place. Every other preset's belt renders byte-identical: `cmp` the files, not
just the snapshot report.

### K4. The sleeve cuff line

Replace the filled grey band with a thin stroke at y 3.63, just above the
sleeve's end, the wrist at 3.65, sleeve half-width about 0.24. These are the
one set of numbers K0 did not re-derive (the harness measures the coat's
sleeve end at 3.70, which is consistent but not the same measurement), so
K4 re-measures the cuff off the segment before drawing it. There is no
stroke-only cuff anywhere in the file today; the reusable primitive is the
placket's centre line (`_placket`, a `fill="none"` path at about 0.7 of the
stroke width), not a function to call. A rolled cuff with roll lines was
considered for Satoshi in 2026-08 and deliberately not implemented, so this
lands as a new variant behind a field, with `undersleeve_color` unchanged for
everyone else.

The reference also shows a second line higher up the sleeve, at y 3.48. That
is a fold crease, texture under the flat-colour rule, and is not ported.

### K5. Colours

Move the preset to the sampled values one milestone at a time, as Katherina's
campaign did, rather than in one jump: coat `#eeeeee`, dress `#373833`, belt
`#ececec`, buckle frame `#8c8478` over a near-black interior. Ours are
already close on the coat and the dress; the belt is the real change, from
`#33332f` to near white, and it only makes sense once K3 has put the belt
where it can be seen.

### K6. Integration

In this order, each checked before the next: the catalogue entry for every new
cut (`COAT_CUT_LABELS` and its `assert set(...) == set(COAT_CUTS)`, the same
for the collar, belt and sleeve label maps, plus the slot's `selects`), the
web GUI restaged and looked at, the cast sheet, then the cover.

`ref-out/keiko.svg` and `keiko.png` refresh at the end of each milestone, and
`refresh-ref-out.sh` must report **only Keiko changed**, plus `catalogue.json`
where a cut was exposed. Anything else changing is a blast-radius escape and
stops the milestone.

`../valley_of_mist` checks in Keiko's reference sheet and her chapter inserts
and regenerates them from this repo. That regeneration is a separate,
explicit step at the owner's request, in that repo, after the campaign is
signed off here. Nothing in this campaign touches it.

### K7. Deferred

- **The realistic build.** Cuts are chibi-only, so `--build realistic` keeps
  the parametric coat and the bare throat. Same scope decision as Katherina's
  campaign, and the same open item as the realistic-build sword placement.
- **Her height.** 3.67 heads measured against 3.245 rendered, see above. A
  body question, not a clothes one.
- **Hair, face, glasses, boots.** Not called wrong, not in scope.

## Acceptance, every milestone

- The K0 harness: per-region overlap and mean contour distance against the
  reference, **predicted before rendering**, recorded in the milestone's
  status with the commit it was taken at. The gap between predicted and
  measured is the next clue and is invisible without the prediction.
- Looked at: side by side at one head scale, on white and on black, and at 4x
  zoom on every junction the milestone touches.
- One variable per measurement. A single change that makes things worse is a
  hypothesis about coupling, not a verdict on the lever.
- `uv run ruff check .`, `ruff format --check .`, `pytest` green, in the same
  change; `refresh-ref-out.sh` reports only Keiko's renders changed.
- The owner's sign-off before the next milestone starts.

## Risks

- **The calibration is an estimate**, the same grade as Satoshi's tall-chibi
  landmarks. Every absolute head-radius number moves with it. Landmark-to-
  landmark mapping is what keeps the cuts wearable if it turns out to be off.
- **Draw order is shared.** Belt over coat is right for this cut and wrong for
  the four presets whose belts sit under an open coat. The order has to depend
  on the cut. This is a repeat of a risk Katherina's campaign already named,
  which is why it is worth naming again.
- **`_belt_drawn` serves all 17 presets.** The second keeper and the buckle
  tones are opt-in or they are a 17-preset change.
- **The hair hides the shoulders and the upper sleeves** in the reference, as
  it did for Katherina. Shape there comes from the segment, which here is a
  verified crop, so this risk is smaller than it was, but the occluded region
  is still inference.
- **Scope creep into a garment rewrite.** Parametric garments stay the default
  for the cast; this campaign adds cuts beside them.
- **Scope creep into her body.** The 13% height difference is real and is not
  this campaign's to fix.

## Owner's decisions (2026-09-21)

1. **Traced cuts**, not changes to the shared `_coat`.
2. **Colours move to the reference's samples**, one milestone at a time.
3. **Her height stays as it is.** The 13% difference is recorded and not acted
   on.
4. **The realistic build keeps the shared garments.** The owner's words: it is
   a different beast.
5. **Measure the dress hem** on a leg crop rather than accepting coat-level.

The questions as asked, kept for the record:

## Questions for the owner, with recommendations

1. **Traced cuts or changes to the shared `_coat`?** Recommended: traced cuts.
   Zero blast radius on gero, kyoko and tomohiro, and the registry already
   exists.
2. **Colours to the reference's samples?** Recommended: yes, one milestone at
   a time, the belt last because it only reads once it is over the coat.
3. **Her height, 3.67 measured against 3.245 rendered?** Recommended: out of
   scope, recorded in K7. Clothes first, and the cut mapping absorbs it.
4. **The realistic build?** Recommended: keep the shared garments there for
   now, matching Katherina's scope.
5. **The dress hem below the coat**, which the composite could not settle:
   measure it on a leg crop in K0, or accept coat-level. Recommended: measure
   it, it is one crop.
