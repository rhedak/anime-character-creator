# Detail status

The record for `detail-plan.md`. Procedure: `detail-strategy.md`.

## RESUME

D0 and D1 done (2026-09-27; D1 approved), and the second eye style
retired. D2 done, with `FaceStyle.lash` (the men at 0.4). D3 done: one
Age slider (`CharacterParams.face_age`, 0 to 2), the cast's ages applied,
the moustache under the nose; the chin and the crease deferred. Next: D4,
the body at height (a study first). Earlier D3 notes: which presets state an
age (a lineup and a whole-figure before/after, `harness/detail/age_lineup.py`
and `age_before_after.py`; the owner: "mostly good"); and the nose against
the beard (fixed, below).
The owner does not want `../valley_of_mist` regenerated for now: work
through the plan. The baseline is
`harness/detail/baseline.py` (writes `out/detail/`); the height range is
`harness/tall_chibi/height_range.py`; the inventories are in
`docs/detail-inventory/`. The plan is committed at 7b8a2f7.

## Scoreboard

| step | state |
|---|---|
| D0 inventory and baseline | done |
| D1 line weights | done |
| D2 eyes | done |
| D3 face maturity | done |
| D4 body at height | D4a, D4b, the knee done; D4c superseded; D4d H0 with the owner |
| D5 hair | not started |
| D6 garment line work | not started |

## Findings, newest first

### D4d H0: the reference's hands calibrated (2026-09-27)

`harness/trace_hands/calib.py`: each hand's wrist is where its skin meets the
cuff, fitted as a line in a box read off the gridded close-ups (the sleeve
and the dress are the same navy, so "skin touching navy" alone ran down the
relaxed hand's whole side), the hand closed over its own interior lines
before labelling (the trace skill's step 3; the grip's finger rolls had cut
it into pieces). Measured (the reference's head radius about 84 px):

| | wrist | length | length / wrist |
|---|---|---|---|
| relaxed | 36 px, 0.43 head radii | 98 px, 1.17 | 2.72 |
| grip | 26 px (foreshortened) | 68 px, 0.81 | 2.63 |
| our mitten | 0.39 head radii | 0.31 | 0.79 |

The wrists nearly agree against the head; the reference's hands are more
than three times as long as the mitten, an adult's hand about the face's
length. So a uniform scale cannot fit both the wrist and a chibi's hand.
`harness/trace_hands/size_mock.py` pastes the reference's relaxed hand onto
Krista (a harness preview, nothing ships) at three sizes: **A**, by the wrist,
about 1.06 head radii, reaches mid-thigh, too big; **B**, 0.65 head radii,
reads as a real hand on this body at 1.0 and 1.3; **C**, 0.45, reads spindly,
its wrist far narrower than the sleeve. At B the traced wrist is narrower than
our arm's: the cuff hides it on a sleeve, a bare arm needs the join handled
(the arm tapering into it, or the hand's top widened to the arm). With the
owner.

### D4c: the hands, research and a study (2026-09-27)

The owner asked for proper research first. A Sonnet delegate (59k tokens)
read drawing tutorials and style guides: `docs/detail-inventory/hands-research.md`
(sources listed there). What is sourced: chibi and distant figures keep the
thumb and drop creases and nails first; a hand is a finger mass plus a thumb;
a grip is stacked curves, one per finger, down the pole, the thumb the anchor;
knuckles are interior lines at the joints, not notches in the outline. The
delegate's level recommendations for our sizes are its own inference and were
treated as a hypothesis.

`harness/detail/hand_study.py` draws levels over today's mitten as interior
lines, for the relaxed hand and Katherina's hand on the staff (drawn over the
staff already), at 4x and at the smallest insert size. Seen: **level 1** (a
thumb crease) makes the thumb its own part on both hands, cleanly; the grip's
**stacked finger rolls** (levels 1 to 3) read as fingers round the staff;
level 2's two finger lines at the tips of the relaxed hand read as a paw, the
failure the research warned of; **level 3** (a fold where the fingers curl
under, one separation below it) reads as a loose fist. At the insert size
every level shows the same silhouette: nothing turns to mud, the lines just
fade. With the owner.

### D4: the bare leg's knee built (2026-09-27)

The owner's pick, "realistic, with height": `_knee_notch_d` draws the bare
leg with the knee in by `_KNEE_IN` (0.10), the calf's control `_CALF_CTRL`
(1.15) out from the narrowed knee and the bare ankle to `_BARE_ANKLE` (0.70)
of it, the bare foot taking that ankle (`_bare_ankle`); its strength follows
the limb taper (`_knee_strength`: none at 0.8, full from 1.3). The trousers and
the boots are untouched. Continuous: the leg's inside, one curve without a
knee, is split at the knee's height (`_quad_u_at`, a bisection;
`_quad_crossing`'s closed form hit a math domain error on one figure) into the
same curve in two halves, and its points blend toward the knee's.

**Measured:** at 1.3 pixel-identical to the study's realistic row; across
height 0.8 no element moves by more than 0.25 px (a test), the extra
anti-aliased pixels there being rounding in the arms, not a jump (the leg's
path changes structure only); trousered renders byte-identical, the bare-legged
ones changed (`ref-out/`: Satoko, Katherina, Keiko, Reika, Chiyo, the sheets
and the female base). 545 passed, 1 skipped.

### D4: a knee on the bare leg, the study (2026-09-27)

`harness/detail/knee_study.py` draws the bare leg (only: the trousers keep
their measured, nearly straight run) with a knee: in at the knee, the inside
split there into two curves, the crotch as it was. The owner asked whether
the ratios are realistic; measured off the render (knee = 1; a real leg front
on: upper thigh 1.4 to 1.6, calf about 1, ankle about 0.6):

| | upper thigh | mid-thigh | calf | ankle |
|---|---|---|---|---|
| today, no knee | 1.15 | 1.08 | 0.98 | 0.85 |
| firm (knee in 0.10, calf swell 0.08) | 1.35 | 1.15 | 1.12 | 1.00 |
| realistic (knee in 0.10, calf 1.03, ankle 0.70), full | 1.35 | 1.15 | 1.04 | 0.76 |

The firm knee only narrowed the knee, leaving the calf and ankle heavy. The
realistic row narrows the bare ankle too, and the bare foot with it (it is
sized off the ankle); the boots keep today's width. The ankle measures 0.76
against its 0.70 target because the outline adds a fixed width. With the
height (as the limb taper): none at 0.8, light at 1.0 (calf 1.01, ankle
0.87), full at 1.3. With the owner.

### The two other covers regenerated (2026-09-27)

At the owner's request, after the eye and spacing fixes:
`../short_stories` 3c496e7 (the Everglow cover, `scripts/build_cover_dual.py`)
and `../time_slider_katherina` 617b37d (the cover by `tools/generate_cover.py`,
the reference by `render.sh --preset katherina --no-metadata`, as it was made
before). Both covers byte-identical to the rebuilds the owner reviewed.
`../valley_of_mist` not regenerated (the owner: not for now).

### D3 follow-up: the eyes' spacing follows their size (2026-09-27)

The owner: on the rebuilt Everglow cover Gero's eyes still read much farther
apart than Linnea's. Measured: their centres were nearly as far apart (0.85
and 0.88 head radii, `eye_dx` held at 0.46 whatever the eye's size) but his
eyes are smaller, so the gap between them was 0.56 of an eye's width against
her 0.36 (Tenno 0.58, Krista 0.30). `harness/detail/eye_spacing_study.py`
(the gap following the eye's width at k 0, 0.5, 1; the target the cast's
median 0.44, not the default face's 0.58, which sat at Gero's end); at k 1
the eye's corner crossed the face's edge at the sliders' tops. The owner's
pick: k 1 with a limit. `_eye_placement` now puts the eye's centre at `w * (1
+ _EYE_GAP)` from the face's centre, `w` the eye's half-width, but never
nearer the face's edge than `_EYE_CORNER_CLEAR` (0.05) at its corner; the
lash's upper edge is kept inside too (`_eye_lash`).

**A bug, and a retraction.** The flick cap of the previous entry (e504eb0)
never worked: inside `_eye` the lower lash's sample count was also called
`reach` and shadowed the parameter, so every flick was cut to nothing (the
cap read 8 px against a real 28). The face-edge test passed, since it
computed its own reach. e504eb0's `ref-out/` and the two covers rebuilt to
scratch then had flickless eyes. Fixed (the local renamed `lower_n`); a new
test reads the lash off the rendered face (the flick past the corner, inside
the face) and fails on all three of its presets with the shadow put back.

**Measured:** `ref-out/` (all 20) and the bases refreshed, the cast's faces
checked by eye; 544 passed, 1 skipped. Both covers rebuilt to scratch again
(`out/review/covers_before_after.png`).

### D3 follow-up: the eye and the age, one story at a time (2026-09-27)

The owner, on a rebuilt Everglow cover: Gero (face age 1.55) and Linnea (0,
though she is fifteen) looked inconsistent; eye sizes should not differ this
dramatically within one story; scaling them is fine but as its own choice.
Measured: the eye's area fell to 0.87 at age 0.4, 0.70 at 1, 0.46 at 2.
`harness/detail/eye_age_study.py` (now, light, none); the owner's pick
**light**: `_MATURE_EYE_SHARE` 0.5 to 0.2, `aged_face`'s eye terms at a
third. The area is now 0.95 at 0.4, 0.87 at 1, 0.76 at 2; how big a
character's eyes are is `FaceStyle.eye_size`'s (the web tool's Eye size).
Ages set: Linnea 0.4 (fifteen), Katherina 0.35 (fourteen at the start of her
story, the owner).

**The eye inside the face.** On the study's "none" row the eyes reached and
ran over the face's edge, which read as creepy (the owner). Measured with
"light": the eye's outer corner stays 0.06 head radii inside the face even at
the top of the web tool's eye size and width, but the lash's flick crossed by
up to 0.036 there, and by 0.009 on Krista at her own settings. `_eye_lash`
now shortens the flick (never lengthens it) so its tip stays `_EYE_EDGE_CLEAR`
(0.03) inside the face's edge at the eye's height; a test holds the corner
0.04 inside and the lash inside, for every preset at face ages 0, 1 and 2, at
its own settings and the sliders' tops.

**Measured:** `ref-out/` (all 20) and the bases refreshed; 541 passed, 1
skipped. The Everglow and Time Slider Katherina covers rebuilt to scratch
(`out/review/covers_before_after.png`), not yet written to their repos.

### D4b: the limbs taper with the height (2026-09-27)

The owner's calls over three rounds: the hands follow the wrists; the taper
grows with the height instead of being one amount for all (the point of it,
explained to the owner: a straight tube of an arm is the chibi's, fine on a
short young figure and a pipe on a tall grown one); and, seeing the full
taper leave a tall figure's upper arm 1.5 times its wrist once D4a had
widened the arm, half of it at most. Now `Skeleton.limb_taper =
_limb_taper_at(height)`: 0 at 0.8, `_TAPER_MAX` 0.5 from 1.3, linear between,
0.2 at 1.0 where every preset stands (about 7% narrower at the wrist, the
hands with it). `_limb_build` reads it for `_arms` and `_legs_and_boots`.

**Measured:** all 20 `ref-out/` renders and both bases changed (every figure
stands at 1.0); at 4x the wrists, cuffs, sleeves and hands join cleanly on
six presets, Katherina's grip on the staff included. A test of the mapping.
The web tool restaged. 490 passed, 1 skipped. The three study scripts are
records now (the `_LIMB_TAPER` they patch is gone).

**Open:** the bare leg has no knee (the adult taper was measured on
trousers); a knee is a new shape, a separate study if the owner wants one.

### D4b: the limb taper, the study (2026-09-27)

The retired adult build's limb taper is still in `_arms` (the elbow 15% and
the wrist 34% in) and `_legs_and_boots` (the ankle to 0.85), riding the build.
`_LIMB_TAPER` (0, byte-identical: checked, 0 of 105 renders differ) sets how
far along it the limbs are drawn, through `_limb_build`.
`harness/detail/taper_study.py`: taper 0, 0.5 and 1, on Krista's base layer,
Satoshi, Keiko and Satoko at heights 1.0 and 1.3. Seen:

- **The arms** read better tapered: at 1 the forearm narrows to a wrist.
- **The hands** take the wrist's width (`_hand`: `w_wrist * 1.02`), so at 1
  they shrink with it and read small; kept at today's size they overhang the
  narrower wrist like a mitten stuck on; **half way** between reads as a
  hand a little wider than its wrist.
- **The legs barely change**: the adult taper was measured on trousers
  (`ref/satoshi.png`), nearly straight below the thigh, so a bare leg stays
  a tube with no knee.

**Recommendation:** taper 1 with the hands half way. The bare leg's knee is
a separate question for the owner.

### D4a: the widths follow the height (2026-09-27)

The owner's pick, k = 0.6: `stretched` scales the body's widths (shoulders,
waist, hips, hem, arms and where they hang, legs) by `1 + _WIDTH_FOLLOW *
(h - 1)`, the neck kept. **Predicted:** every preset byte-identical (all at
height 1.0, where the stretch is not applied). **Measured:** 0 of 105
snapshot renders differ from the committed tree's (taken with `git stash`;
an older snapshot, from before the ages, gave a false 60); the height test
restated (the widths grow by the rule, the neck does not); the web tool
restaged. 489 passed, 1 skipped.

### D4a: the widths at height, the study (2026-09-27)

`harness/detail/width_study.py` scales the body's widths after the height
stretch by `1 + k * (height - 1)` (shoulders, waist, hips, hem, arms and
where they hang, legs; not the neck), k 0, 0.3 and 0.6, on seven characters
and Krista's base layer at 0.8, 1.0 and 1.3. At 1.0 nothing moves (the
stretch is not applied there), and no preset uses another height, so this
changes the slider, not the cast. Seen: the traced coat and jacket, the long
coat, the robe and the skirts all follow; only Satoshi's hair reaches the
canvas edge, as before. At 1.3, k 0.3 is still a little lanky, k 0.6 reads
as an adult build, and it is the skirts and the hakama that grow widest.
With the owner.

### D3: the cast's ages applied (2026-09-27)

The owner approved the lineup ("mostly good", the nose and beard then
fixed). Applied: Katherina and Linnea 0 (unchanged); Kyoko and Tomohiro 0.6;
Satoko, Satoshi and Viktor 0.8; Krista, Elara, Keiko, Reika, Haruto and
Reinhard 1.0; Gero 1.55; Chiyo, Daizen and Tenno 2.0. The male and female
bases stay at 0.

**One correction to the proposal:** Kyoko is Satoko's earlier self
(`_before`), as Tomohiro is Satoshi's, and the proposal had her older (1.0)
than Satoko (0.5). Now the pair mirrors Satoshi and Tomohiro: `_before` takes
the earlier self's face age, 0.6 for both.

**The aged four** no longer bake `aged()` into their face: their plain face at
`face_age = 1 + years`. **Measured:** each renders SVG-identical to the old
baked face at age 1 (Gero's 1.55 included), so the web tool no longer ages
them twice. `presets.aged` stays as a helper with no preset caller.
`ref-out/` refreshed (18 changed: every preset but Katherina and Linnea, and
the sheets); two tests that assumed age 0 now read the mouth's real height
and set Satoko's baseline to 0. 489 passed, 1 skipped. `../valley_of_mist`
not regenerated (the owner's call: not for now).

### D3: one moustache rule at every face age (2026-09-27)

The owner: the chibi's beard has always sat a bit high; match it to the
grown face's. `harness/detail/beard_height.py` put the moustache's top at
today's 0.36 head radii, at 0.40, and at the grown face's rule applied at age
0 too (under the nose's line, about 0.43); the owner picked the one rule. Now
`tash_y = _nose_y(sk) + _BEARD_NOSE_GAP` at every face age, nose drawn or
not; `_BEARD_TASH_Y` and the settling blend (`_BEARD_NOSE_ONSET`) are gone.
The band of hair over the lip comes out the same on the chibi face and the
grown one (about 0.087 head radii, some 2.7 times the drawn outline), and
still reads at the smallest insert size.

**Predicted:** only the three bearded men change, in all four states each.
**Measured:** exactly those 12 of 105 snapshot renders; `ref-out/` refreshed
(5 changed: Gero, Daizen, Reinhard and the two sheets); the moustache test
restated against the rule and the drawn outline, at face ages 0 and 1. 489
passed, 1 skipped.

### D3: the moustache ends under the nose (2026-09-27)

The moustache's outer corner now drops with the mouth
(`_MOUTH_REALISTIC_DROP` times the face build's growth), and its top edge
moves to `_BEARD_NOSE_GAP` (0.05 head radii) under the nose's lowest point
(`_nose_y`, shared with `_nose`), settled by face maturity
`_BEARD_NOSE_ONSET` (0.25) while the nose is still faint, so it never
jumps. **Predicted:** byte-identical at face age 0 (both terms zero), the
nose clear of the moustache from 0.25 up. **Measured:** all 105 snapshot
renders identical; `harness/detail/beard_nose.py` (Gero at 0 to 1, and
Gero, Daizen and Reinhard at their proposed ages) shows the nose above the
moustache everywhere and no jump. The cost: on a grown face nose and mouth
are closer, so the moustache's band over the lip is thinner than the
chibi's; it still reads as a moustache. 487 passed, 1 skipped.

### D3: the nose inside the beard (2026-09-27)

The owner, on the whole-figure before/after: mostly good, but the nose
collides with the beard. A beard ends between the nose and the mouth, it does
not grow around the nose. Cause: `_BEARD_TASH_Y` holds the moustache's top at
0.36 head radii, which is `_NOSE_Y` itself, and the nose and mouth drop with
the face build (`_MOUTH_REALISTIC_DROP`, to about 0.54 for the nose at face
age 1) while the moustache does not. Added to the plan under D3.

### D3: one Age slider (2026-09-27)

The owner's calls on the prototypes: **as built**, no longer chin and no
crease; the chin deferred and not touched. And, from a user's side, child to
adult to old is one slider: `CharacterParams.face_age`, 0 to 2, replaces
`face_maturity`. 0 to 1 is maturity (`Skeleton.face_maturity = min(1,
face_age)`); 1 to 2 applies `aged_face` at render time (in
`_eye_placement`, the one place that reads the fields it scales).
`presets.aged` keeps its name and now calls `character.aged_face`, the
numbers in one place. Web tool: "Age (child, adult, old)", 0 to 2, beside
the height.

**Measured:** all 105 snapshot renders identical to before the rename; a
test that `face_age = 1 + years` renders the same as `aged(face, years)` at
1; checked in the browser (the slider there, the face older at 1.5, the link
carrying `face_age`). 487 passed, 1 skipped.

**Not yet:** Chiyo, Daizen, Tenno and Gero still bake `aged()` into their
face at age 0; moved onto `face_age` they would also take the grown face.
The web tool ages them twice if a visitor slides their age up. That is the
presets step, with the owner.

### D3: the face maturity mechanism (2026-09-27)

`CharacterParams.face_maturity` (0 to 1, default 0) is carried on the
skeleton (`Skeleton.face_maturity`), which exposes `face_build = build +
maturity * (1 - build)`. Everything welded to the skull reads it instead of
`build`: the head's outline (`_head_pt` through `_head_shape`), the hair's
inner edge, the ears, the beard, the glasses' arms, the mouth. That reaches
the retired adult build's face terms, which were still in the code, running
at the chibi's pinned build. Maturity's own terms: the eyes lower
(`_MATURE_EYE_DROP` 0.06) and a nose growing in (`_nose`: the retired adult
build's two marks, measured off `ref/satoko-real.jpg`, their length, weight
and spacing scaled by maturity, so it never pops; nothing drawn at 0). The
hair's volume and the familiar's size stay on the figure's own build.

**The study** (`harness/detail/maturity_study.py`): 0.5 read as a teen or a
young adult; with height 1.3 it is the first figure that reads grown rather
than a child's head on a long body. At 1 the adult build's eye change
(openness down 40%, width down 21%) left an adult squinting, where the
reference keeps a large, open eye. The sweep in steps of 0.1 moves without
a jump. **The owner's calls:** the eye takes half of that change
(`_MATURE_EYE_SHARE`, through `_eye_build`), the skull and mouth all of
theirs; `aged()` stays a separate mechanism, but a user sees one continuous
slider (child to adult to old), so the two become one "Age" slider, 0 to 1
maturity and 1 to 2 `aged()`; the chin and the crease as prototypes first.

**Ears under long hair.** From maturity 0.4 the ear showed under all three
long cuts: their side locks were fitted to the chibi skull and meet the face
at maturity 0; a narrower face opens a gap between lock and jaw (measured:
0 to 2 px of ear at 0, 94 to 225 px at 1). `Hairstyle.covers_ears` on the
three long cuts, and `_ears` draws nothing under them. At maturity 0 that
removes the hidden ear's six paths from every long-haired render (checked:
with the flag off every snapshot render is byte-identical to before, and
each changed render lost exactly six paths and gained none); the 2 px
sliver it leaked on `long_traced` is gone with it.

**Measured:** at maturity 0 the eye share leaves every render
byte-identical (the flag-off check above); `ref-out/` refreshed (10
changed: the eight long-haired presets and the two sheets); 485 passed, 1
skipped.

### D3: the chin and crease prototypes (2026-09-27)

`harness/detail/maturity_proto.py` patches `_head_pt` (the chin's drop
plus `extra * maturity`) and `_eye` (a crease over the outer half of the lid,
its weight growing with maturity). Seen: **+0.10** gives a longer, adult
lower face, and Gero's beard follows it; **+0.20** reaches the reference's
chin but the chin starts to cover the collar and the tunic's V, so the neck
reads short; **the crease** reads like the reference's lid line and is
light at 0.5. With the owner.

### D2: the men's lash (2026-09-27)

The owner's call: `FaceStyle.lash` (default 1.0) scales the lash's outer
thickness above the inner one and the flick's length; `presets.MAN_LASH =
0.4` on every man (Satoshi, Tomohiro through him, Daizen, Haruto, Reinhard,
Tenno, Viktor, Gero) and the male base. A web tool slider, "Lash (soft to
winged)", 0 to 1. **Predicted:** only the nine male figures change, in all
four snapshot states each. **Measured:** exactly those 36 of 105 snapshot
renders changed, the rest byte-identical; by eye, a firm upper line and no
wing on all of them. 482 passed, 1 skipped.

**For D3:** `presets.aged(face, years)` already reads a face older by
walking the eye's size, width and openness down and the brows' weight up
(Chiyo, Daizen, Tenno at the full amount). Face maturity overlaps it; D3's
study has to decide whether maturity replaces `aged`, builds on it, or is
kept apart from it (maturity as adult against child, `aged` as old against
adult).

### D2: the eye built (2026-09-27)

`_eye` draws variant D: the aperture filled white and unstroked; the
iris's top in a darker band (`_IRIS_BAND_CUT`, `_IRIS_BAND_SHADE`); a faint
lower edge (`_interior_w(sw, 0.8)`); a short lower lash over the outer half
of the lower lid's outer curve; the upper lash as a filled band
(`_eye_lash`: `_LASH_INNER` 0.05 to `_LASH_OUTER` 0.24 eye radii, the
flick `_LASH_FLICK` 0.40 at `_LASH_FLICK_ANGLE` 28 degrees). The aperture's
four quadratics now come from one place, `_eye_quads`, which `_eye_shape`
and the lash both read.

**Predicted:** pixel-identical to the study's D; every render changed only
inside the eyes. **Measured:** zero differing pixels against the study's
candidate on all five study cases; all 105 snapshot cases changed, none
outside a box of the eyes (`eye_y - 1.6 r` to `eye_y + 1.4 r`, eye radii).
One test read the iris band's arc radii as a point (`A 11.78 11.78`) and
now skips arc radii. `ref-out/` and the bases refreshed; 479 passed, 1
skipped.

**Seen:**

- The glasses sit cleanly over the lash; the closed eye is unchanged (a
  thinner line than the open lash: a blink would jump, which matters only
  for animation; noted for it).
- **On the men the flick reads as winged eyeliner**: Satoshi, Daizen and
  Tenno have narrow, sharp-cornered eyes and the wing dominates them.
  `harness/detail/lash_men.py` scales the lash's outer thickness and the
  flick: at 0.6 the wing is small, at 0.3 gone and the upper line still
  firm. **Owner question:** a `FaceStyle.lash` knob (default 1.0, the women
  as now), the men at about 0.4?

### D2: the eye study (2026-09-27, at 2736cb6)

`harness/detail/eye_study.py` stands candidates in for `_eye`, keeping the
aperture and the iris and changing the lining: A today; B a filled lash
along the lid (thin inner, thick outer, a flick past the corner), a short
lower lash at the outer corner, the lower edge unlined, the iris's top in a
darker flat band (`shade(eye_color, 0.68)`); C B plus a faint lower edge
(`_interior_w(sw, 0.8)`); D C with a heavier lash (0.24 eye radii at the
outer end, against 0.16) and a longer flick; E C plus a crease over the
outer half. On Katherina (amber), Krista (teal), red eyes on dark skin, and
Katherina "hollow" and "sorrow"; and at the smallest insert size.

**Seen:**

- **B fails**: without a lower line the white under the iris bleeds into
  pale skin, worst with the lids lowered. The reference gets away with it on
  a face drawn at a larger scale with a shaded lid; we cannot. C, D and E
  keep the faint line.
- **The iris band reads** on all three palettes, the red one included.
- **D is closest in spirit** to the reference: the lash reads as the one
  heavy line in the face, as there, and the flick shows. At the insert size
  it still reads as a darker lash line.
- **E's crease crowds our brows**, which sit at `eye_y - 1.30 * eye_r`, and
  at the insert size crease and brow merge into a double brow. A crease
  belongs with higher brows, which face maturity (D3) may bring.

**Recommendation: D, without the crease** (the crease revisited in D3).

### D1: the line weights built (2026-09-27)

The owner's pick: outlines at 0.75 of the old weight, interior lines at
0.55. `_stroke_w` keeps the old weight, since 18 places size geometry off
it; the drawn weight goes through `_outline_w` and `_interior_w`
(`_OUTLINE_SCALE`, `_INTERIOR_SCALE`), all 100 drawn sites classed by hand:

- **By meaning, not by the study's value rule.** An outline is a part's
  edge at whatever fraction it was drawn (the hands, cuffs, pouches, belt
  pieces, strap, robe front, the eyes' aperture and the brows); an interior
  line divides or decorates inside a part. So those edges come out 0.75 of
  their old weight where the study showed 0.55.
- **Kept**: the bust mask's widening stroke and the goggles' rim (a band
  sized off the lens).
- **Filled lines** (the bust fold, the bare breasts' line, the male chest
  lines) take the outline scale in their width: they meet the body's
  outline and have to match it there.
- **Every geometry use of the weight is untouched**, including the offsets
  that tuck a fill under a line (the bust over the arms, the arm's joint
  cap, the bare foot's ankle patch, the belt).
- Drawn weights print to two decimals now, not one, which cost up to 8% on
  the thinnest lines.

**Predicted:** with `stroke-width` stripped every SVG identical but the
three filled lines; the stroke ratios at 0.55 and 0.75, and 1 on the kept
sites. **Measured** (`harness/detail/d1_check.py` over two snapshot runs):
the only geometry changes are those filled lines and the coat-bust masks
whose content-hashed ids hold the bust line; ratios 0.53 to 0.56 and 0.72
to 0.77 (the old values' one-decimal rounding), 1.00 on 29 strokes. By eye
(`harness/detail/d1_look.py`): the whole figure lightens evenly; at 4x the
bust over the arm, the base layer, the belt, the hand and the bare foot show
no gap or overhang. `ref-out/` and the bases refreshed; 479 passed, 1
skipped.

**Seen, not caused by D1:** a short grey vertical mark at the bottom of
Keiko's coat-at-the-arm zoom, before and after alike. Left for D6.

### D1: the line-weight study (2026-09-27, at 9079ad7)

`harness/detail/line_weight.py` rescales only the drawn `stroke-width`
attributes (geometry untouched, as the change will be), silhouette strokes
(within 5% of `_stroke_w` or above) and interior strokes separately, on
Satoko, Krista, Keiko (a white coat on a light card, the worst case) and
Katherina. Variants (outline, interior): (1.0, 1.0) today, (0.75, 0.75),
(0.6, 0.6), (0.75, 0.55), (0.6, 0.4).

**Predicted:** (0.6, 0.4) closest to the reference at full size; at the
smallest size, 1x, the 0.6 outline goes faint.

**Measured, by looking:**

- Full size: (0.6, 0.4) reads closest to the reference, as predicted.
- Smallest size, 1x (`line_weight_small_zoom.png`): every variant's
  silhouette still reads, since the flat fills carry it; the prediction
  was wrong there. What fades is the interior: at 0.4, Keiko's lapels and
  glasses frame and the hair strands go near-invisible grey. At 0.55 they
  hold.
- **The reference's own weight**, measured on its chin line (a dark run of
  2 to 3 px across columns 610 to 665) at the calibrated 83.9 px per head
  radius: about 0.030 head radii, 0.70 of ours. Its finger lines measure
  the same.

**Recommendation: (0.75, 0.55).** It is within 7% of the reference's
measured line, and the interior survives the smallest view. (0.6, 0.4)
looks lighter still at full size but loses the interior in the chapter
inserts.

### The second eye style retired (2026-09-27)

`_eye_anime`, its `eye_glow` knob, the `eye_style` field and the
`EYESTYLES` registry are gone; `_eye_realistic` is now `_eye`, the one eye
D2 redraws. The web tool's eye style select went with the catalogue entry;
an old link carrying `eye_style` or `eye_glow` loads with the one eye
(`urlstate`, tested). **Predicted:** every render byte-identical, since no
preset used the style; the suite at 483 minus the 6 eye-style tests plus 2
old-link tests. **Measured:** `harness/tall_chibi/snapshot.py`, 105 renders
`cmp`-identical to the committed tree's (its two `eyes.*` cases dropped);
`./refresh-ref-out.sh --check` matches; 479 passed, 1 skipped.

### D0: the line-weight inventory (2026-09-27)

Full list: `docs/detail-inventory/strokes.md` (a Sonnet delegate's read,
109k tokens; its UNSURE classes are marked there). 105 `stroke-width` sites
plus 18 places the weight is used as geometry:

| class | sites | multipliers of `_stroke_w` |
|---|---|---|
| silhouette | 53 | 1.0 on 37; 0.7 to 0.9 on the rest |
| interior | 44 | 0.4 to 0.7 mostly; 1.0 on 2 |
| feature (eyes, brows, mouth, glasses) | 11 | eyes 0.85 (`_EYE_OUTLINE_W`); brows from `FaceStyle.brow_weight` |
| geometry, not ink | 18 | offsets, radii, thresholds, clamps |

What it means for D1, checked by reading:

- **Interior lines are already split off by a factor** almost everywhere, so
  "lighter silhouette" and "lighter interior" are two separate levers: the
  base in `_stroke_w`, and the interior factors.
- **The weight doubles as geometry in 18 places**, and not all of it should
  follow a lighter line. Offsets that cover or meet a drawn stroke (the bust
  over the arms, the arm joint cap's half stroke, the bare foot's ankle
  patch, the body inset under a garment) should follow the ink. Sizes and
  thresholds should not: the navel's size, the placket button's radius, the
  underskirt's and hakama's pleats (drawn only when wider than four
  strokes), the crystal spacing, the staff's and familiar's canvas clamps.
  D1 therefore gives the ink its own weight and keeps the current value for
  the geometry that must not move, site by site.
- **`hat_hair_margin`** allows for the stroke with a literal 0.06 head
  radii, not `_stroke_w`. A lighter line leaves it generous, which is
  harmless and keeps the canvas; leave it.
- **Existing lighter silhouettes**: the robe front (0.7), several at 0.85.
  A lighter base would make them lighter still; D1's study checks they
  still read.
- **Not tracking the weight**: the goggles' lens rim (from `lens_r`) and the
  staff crystal's outline (full weight on a small shape).

**The owner's answers (2026-09-27):** retire `_eye_anime`; commit as each
step lands with the usual one-liners.

### D0: the baseline (2026-09-27, at 7b8a2f7)

**Calibration** (`out/detail/calibration.txt`). Our face (Katherina, the
hat off, the skin component): widest visible row at 0.446 head radii below
the head centre, half-width 0.852, chin at 0.987. The reference's face
component: widest row y 330, x 564 to 707, chin y 399.

- Scale from face width: 83.9 px per head radius; the reference's head
  centre at (636, 293).
- Scale from the widest row to the chin: 127.7. They disagree by 52%, by
  design: at one face width the reference's chin is at 1.26 head radii
  against our 0.99, a longer lower face ending in a point. That is D3's
  direction (a chin that drops and narrows), not a calibration fault.
- The review's by-eye crop (88 px) was 5% off; the calibrated sheet is
  `out/detail/face_vs_reference.png`.

**The smallest view** (`out/detail/smallest.png`). `../valley_of_mist`'s
chapter inserts are `sheet.sh` sheets, up to four columns, 2576 px wide;
its reader (`.chapter-end`, `max-width: 40rem`) shows them about 600 CSS px
wide, a scale of 0.233. A tile scales the figure by `0.86 * 400 /
canvas_h`, so the head radius there is about 21 px at 1x (Satoko 21.6,
Katherina 20.3; the review's "13 px" was a guess) and today's line (0.0427
head radii) about 0.9 CSS px, 1.8 device px on a 2x screen. Halving it
leaves about 0.45 CSS px at 1x: D1's lighter weights must be judged at this
size first.

### D0: the face, body and hair inventory (2026-09-27)

Full list: `docs/detail-inventory/face-body-hair.md` (a Sonnet delegate's
read, 131k tokens); the load-bearing lines, checked by reading:

- **The realistic lerp is still in place, running at the pinned build.**
  `_head_pt` (the skull: `_SKULL_NARROW * build`, `jaw_pull = 0.20 * build`,
  `chin_drop = 0.05 * build`), `_eye_placement` (`eye_dx` and the eye's size,
  openness, width and corner scale with `sk.build`; `eye_y = cy + 0.16 r` has
  no build term), `_arms` (elbow and wrist taper by `0.15` and `0.34 *
  build`), `_legs_and_boots` (`taper = sk.build`). With `sk.build` pinned at
  0.1 each runs at a tenth. **D3 and D4b can drive these terms** from face
  maturity and height instead of drawing new shapes, keeping today's value
  at the default so the default stays byte-identical. The realistic values
  they lerp toward were measured off `ref/satoko-real.jpg`; D3's study
  decides how far along each the slider goes.
- **No nose exists anywhere**: D3's nose tick is new.
- **One hand shape**, `_hand`, a mitten with a thumb bump ("still no
  fingers"); props sit over it at `_hand_centre`.
- **`_KEEP_WS` holds all eight width fields** and `stretched()` rescales
  them with `head_r` only; D4a's follow-through goes there, and the hands,
  feet, belt, skirt and torso all read those fields, so they follow free.
- **Every hairstyle already draws strands** (open quadratic chains as thin
  strokes); `long_traced` has the fewest (4), `short_crop` the most (10).
- **`_eye_anime`**: no preset uses it, but the catalogue's eye style option
  lists it and two tests iterate `EYESTYLES`; retiring it is three small
  touches. An owner question for D2.
- **Discontinuities**: `eyes_closed`, `scar_side`, `eye_style` switch by
  design; no stray thresholds in the face.
