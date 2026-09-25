# Bust status

The record for `bust-plan.md`: what has been measured, predicted and decided,
newest first. The plan says what to do; this says where it stands. The method
lessons live in `bust-strategy.md`.

## RESUME (for a fresh context)

- **Now:** the plan is done. `../valley_of_mist` is regenerated and waits for
  the owner's commit call there. Left: the realistic build's own fix pass.
- **Owner's calls 2026-09-24 (after 5a):** 5a signed off; the realistic build
  needs its own fix pass later, deferred; step 6 then 5b then 4; the fixed
  clip ids get fixed at the appropriate time.
- **Tree:** clean at `e3b65e5` when preparation began.
- **Measure** with `harness/bust/drawn_widths.py` (the drawn ink). Never quote
  a `Skeleton` field as a body measurement.
- **Run harness scripts** with `./harness/run.sh harness/bust/<script>.py`.
- **Check a change that should move no pixel** with
  `./refresh-ref-out.sh --pixels`; `ref-out/bases/` is not covered by it and
  is compared by hand with `compare_pixels.py`.
- **Owner sign-off** is needed after each step before the next.
- **Commits:** one line, repo style, no trailer.

## Scoreboard

| step | state | acceptance met |
| --- | --- | --- |
| B0 sweep harness | done, readings void | harness stands |
| B1 parameter and anchor | done, `bust_half_w` to be replaced | plumbing only |
| 1 reach, not width | done, signed off | continuity and armpit tests green |
| 2 pixel check | done | 0 of 54 on a clean tree; catches a bust |
| 3 body layer | done (3c at the owner's call, 2026-09-25) | clothed cast unmoved but the 3a finding |
| 4 line under the bust | done, signed off | zero case byte-identical; tested |
| 5 bust over the arm | 5a, 5c signed off; 5b reversed | Keiko as before 5b; Katherina's hand fixed |
| 6 traced cuts follow | done, signed off | zero case byte-identical; widening tested |
| 9 fit and drape (added 2026-09-25) | 9a deferred; 9b done, signed off | zero case byte-identical; drape tested |
| 7 cast values | done, applied at the owner's call | cast sheet looked at |
| 8 integration | done; valley_of_mist regenerated, uncommitted there | catalogue test; bridge checked; browser checked |

## Step 1 preparation

### Who reads the anchor (grep at `e3b65e5`)

- `character.py` `_tunic`, the `rib()` closure: the only reader of
  `bust_half_w` and `bust_y` in `src/`.
- `skeleton.py`: `_BUST_ALONG`, `_BUST_REACH`, the two `Skeleton` fields and
  their computation in `build_skeleton`.
- `harness/bust/bare.py` prints `sk.bust_half_w`; `sweep.py`, `why_hidden.py`
  and `drawn_widths.py` set `bust=` only.
- **No test mentions bust.** B1's status said a test asserts
  `build_skeleton(bust=0.0) == build_skeleton()`; it was never written. Step 1
  writes it, along with the continuity test.

### Where the bust sits (measured at `e3b65e5`, head radii below the head centre)

| body | shoulder | armpit (`_sleeve_hem_y`) | `bust_y` | waist |
| --- | --- | --- | --- | --- |
| chibi, long torso (satoko, keiko, satoshi) | 1.118 | 1.788 | 1.905 | 2.713 |
| chibi, `tall_chibi` (katherina) | 1.130 | 1.657 | 1.981 | 2.384 |
| realistic | 1.280 | 2.561 | 2.653 | 4.330 |

`bust_y` is 45% of shoulder to waist, which puts it 13% of the way from the
armpit to the waist on the long-torso chibi and 5% at the realistic build: hard
up under the armpit, where a bulge merges with the sleeve cap. On `tall_chibi`
it is 60% of the way, so one constant lands differently on two chibi bodies.
**Open for step 1:** measure `bust_y` from the armpit. The armpit today is a
garment function (`_sleeve_hem_y`), not an anchor, so either it becomes one or
the bust's height is expressed in a way that does not need it. Decide by
reading `_sleeve_hem_y` first.

### Predictions for step 1, written before any change

With `bust_reach = head_r * lerp(0.10, 0.20, t) * bust` added to the torso
curve's own width at the bust row, chibi half-widths at that row:

| `bust` | 0 | 0.01 | 0.5 | 1.0 |
| --- | --- | --- | --- | --- |
| torso now | 0.583 | 0.950 | 1.013 | 1.080 |
| torso predicted | 0.583 | 0.584 | 0.633 | 0.683 |

Realistic: 1.077 at zero to about 1.277 at 1.0. The arm's ink starts at 0.587
(chibi) and 0.631 (realistic), so **as rendered, the whole bulge is predicted
to be under the arm at both builds for every value above about 0.04.** Step 1
is judged in `why_hidden.py`'s view (arms at a third), and the owner should
expect the rendered sweep to look unchanged.

### Delegation plan

- Step 1's shape, the continuity test and the `bare.py` crop: kept, since the
  shape is the judgment and the rest is a few lines.
- Step 2's pixel check: independent of step 1 and fully specifiable, so it
  can go to a `general-purpose` agent on `sonnet` in a worktree while step 1
  runs, brief in `bust-strategy.md`'s template.
- Nothing is read-only-trace shaped yet; no `Explore` needed.

## Open items outside the steps

- None. (`harness/run.sh`'s cairo path was fixed in `f61c3c1`.)

## Findings, newest first

### 2026-09-25: `../valley_of_mist` regenerated (uncommitted there)

**Owner's call:** regenerate its character references, cover and chapter
images.

**Done** with that repo's own `valley_of_mist_tools.generate_assets`
(`generate-refs`, `generate-covers`, `generate-inserts`, Book 1; Book 2 has no
images yet). 52 files rewritten; the 9 with no pixel changed (the cover,
every male reference, ch26) were restored, leaving 43. Pixels changed: the
women's references 0.1 to 0.6% (the bust), Keiko's 14% (her lab coat campaign,
never regenerated there before); inserts 0.1 to 3% (the women in them), ch13
7.4% and ch25 a new size (1952 to 2904 tall): both now name more characters
(Viktor in ch13; Haruto and Reika in ch25) since the 2026-09-23 consistency
passes edited those chapters after their images were last made. Looked at:
`out/bust/vom_refs.png`, `vom_ch13.png`, `vom_ch25.png`.

Not committed there: its `CLAUDE.md` says not to commit unless asked. Its
trailer imports this package directly and picks the bust up on its next build;
not rebuilt.

### 2026-09-25: step 3c, the bare body where it shows

**Owner's call:** do 3c now, before `../valley_of_mist`, "for good measure".

**Four changes, each pixel-checked on the clothed cast** (the acceptance: no
garment may stop covering the body):
1. **The neck's lines** end where the body's shoulder line meets the neck,
   rather than running down the chest.
2. **The torso runs to the hip** at the bare seat's width, under the seat,
   closing the page that showed between an untucked figure's torso and its
   legs. The white band under a tucked one is `_bare_seat`'s placeholder
   underpants, by design. On the long-torso chibi the crotch sits 1.1 pixels
   above the hip anchor, so a straight edge showed in the notch between the
   legs of every figure (34 pixels each, 16 images): the bottom edge now rises
   into a small V a stroke above the crotch.
3. **The shoulder rounds over the arm** down to the line the arm starts at
   (a quarter round from its tip, the tip itself rounded), instead of cutting
   a slanted sleeve's diagonal and leaving a wedge of page. Its underside lies
   on that line where the arm's top edge covers it, so a bare arm shows one
   line; it first sat an inset above and showed as a double line, and on the
   line throughout it showed in the gap between a flat sleeve's torso and the
   arm (14 images). It steps up an inset only in that gap.
4. **A smooth return under the bust**: the body's outline goes back into the
   side as an S of two tangent-matched quadratics, where the diagonal tuck
   creased and the bust read as a knob (`out/bust/bare_3c.png`, both looked
   at side by side). The line under the bust no longer reads the body's tuck:
   both take the fold's height from `_under_bust_y`, and the line was checked
   identical to before.

**Measured:** the clothed cast moves only at the stand-collar corners accepted
at 3a (five realistic figures, up to 10 pixels at 2x) and one pixel on
Katherina. Bases pixel-identical. Suite: 531 passed, 1 skipped (a new test
that the neck's lines stop at the body and the torso reaches the hip).

**Left, and why:** on the bare body the arms still rise to a point at the
shoulder where their top follows a slanted cap sleeve's underside, which the
tunic's cap covers when worn: that is the arm's garment logic, not the body.
A two-pixel step at each armpit is the inset that keeps the clothed cast
pixel-identical. The realistic build's straight torso stays with that build's
own fix pass.

### 2026-09-25: the gap between the shoulder and the bust

**The owner's report:** an unnatural gap between the bust and the shoulder,
at Satoko 1.0 in the web tool. The crease noted when the bust was raised to
0.15: the sleeve's slanted underside and the bust's outline both met at the
plain torso's armpit, and the bust swung out from it straight away, so the two
met in a V.

**Change.** `_armpit_x`: the armpit carried out by `_BUST_ARMPIT_FILL = 0.7`
reaches, read by everything meeting there (the tunic's sleeve, the slanted
underside the arm's top edge shares, the body's shoulder, the bust's outline
start). The bust's geometry and the traced cuts' bulge keep the plain side, and
a traced coat's hidden tunic sleeve keeps the plain width. Exactly the plain
width without a bust: the men and zero values unchanged.

**A second artifact, found at 12x and fixed:** the over-arm lobe closed back up
to the carried-out armpit, which is past the arm's inner edge, so the top of
that edge was left half covered, a grey smear under the armpit. The lobe now
closes to the plain armpit. A slightly soft cut remains at 12x where the
lobe's top crosses the sleeve's underside stroke; under a pixel at size.

**Looked at** (`out/bust/armpit.png` before and after at 4x: Satoko 1.0 and
0.5, Krista 1.0, Chiyo 0.6; `armpit_zoom.png` at 12x; `female_overview.png`):
the outline runs on from the sleeve into the bust with no V.

The armpit test now checks nothing above the sleeve's tip moves, since the
slanted underside tilts with the bust by design. `ref-out/`: the nine women
and the sheets; bases unchanged. Suite: 529 passed, 1 skipped.

### 2026-09-25: step 8, integration (up to `../valley_of_mist`)

**Change.** `catalogue.BUST`, a plain `RangeField` from 0 to 1 beside the belt
line, in `build_catalogue()` as `"bust"`; `ref-out/catalogue.json` refreshed
(the one entry added). `web/app.js` gives it a slider in the build section,
the same kind of row as `waist_shift`, needing no bridge change. `docs/api.md`
lists the field. A catalogue test that the slider covers every preset's value.

**Checked.** The page's own Python path (`params_from_dict`, then
`render_character`) keeps `bust` through the URL round trip and renders the
bust. The staged site (`./web-stage.sh`) serves the new catalogue entry and
slider on the local server already running on port 8000. Driven in Chrome once
the extension was connected: Krista's page loads the Bust slider at 1 under
"Belt line (up / down)"; set to 0 the preview redraws flat and the shareable
URL carries `"bust":0`; clicked back to the end, the bust and its lines return
and the URL carries `"bust":1`. Sheets, cover and
bases were refreshed at step 7 (the cover did not move).

**Not done:** `../valley_of_mist`, which waits for the owner's explicit say-so.

### 2026-09-25: step 7, the cast's values applied

**Owner's call:** the bust raised to the canon's height and the proposed
values applied.

**Change.** `_BUST_ALONG` 0.30 to 0.15. In `presets.py`: Krista 1.0, Chiyo
0.6, Reika 0.6, Keiko 0.6, Satoko 0.5 (so Kyoko 0.5), Elara 0.4, Linnea 0.3,
Katherina 0.2; every male preset at zero. Two of this plan's tests assumed
Satoko had no bust and now ask for zero explicitly; the profile test passes
the preset's bust to the skeleton it compares with.

**Measured.** `refresh-ref-out.sh`: 20 renders changed, the nine women at
both builds and the two cast sheets; no male preset, not the cover, not the
bases. Suite: 528 passed, 1 skipped.

**Looked at** (`ref-out/sheet.png`, `out/bust/female_overview.png`): the cast
reads together. Satoko, Chiyo and Krista show a clear, restrained bust at
sheet size; Keiko, Reika and Kyoko are subtle under their outer layers; Elara
slight; the men unchanged.

### 2026-09-25: the bust's height, checked on the bare body

**The owner's question:** Krista at 1.0 looked "a bit too low". Measured,
from the shoulder line to the waist: fullest point 59%, fold 71%, against the
canon's nipple line at about 50% and fold at about 62%. Too low by about a
tenth of the torso: `_BUST_ALONG = 0.30` is measured from the "armpit", which
is the sleeve hem, already 42% of the way down.

**Checked without clothes, at the owner's suggestion**
(`harness/bust/bare_proportions.py`, `out/bust/bare_proportions.png`: every
garment off, the arms at a third, canon lines in blue and ours in red; adults
only):

| | fullest | fold |
| --- | --- | --- |
| Krista 1.0 at 0.30 | 59% | 71% |
| Krista 1.0 at 0.20 | 54% | 65% |
| Krista 1.0 at 0.15 | 51% | 62% |
| Satoko 0.5 at 0.15 | 51% | 57% |

At 0.15 Krista's lines lie on the canon's. Recommended; the cost, seen at 5x
only (`height_zoom.png`), is a tighter crease under the armpit.

**Also seen, deferred:** the chibi's arm joins the torso 42% of the way down
(at the sleeve hem), where a real armpit sits a quarter to a third of the
way, so at the canon's height the bust sits right under the arm's top with a
long flat upper chest above it. That is the chibi's construction, not the
bust. The neck's lines running onto the chest and the gap between the torso
and the legs are step 3c's, as before.

### 2026-09-25: step 7, the proposal (not yet applied)

**Owner's calls before it:** step 4's second round signed off. Katherina is
14 (the owner); Linnea is 15 (her preset's own comment).

**Proposal** (`harness/bust/cast_proposal.py`, `out/bust/female_overview.png`,
each female character at the chibi, now against proposed): Krista 1.0 (her
brief asks for "a noticeable bust"), Chiyo 0.6 (late 40s to mid 50s, "strong
capable build"), Reika 0.6, Keiko 0.6, Satoko 0.5 and so Kyoko 0.5 (one
person; `_before` carries the value), Elara 0.4 ("slender strong build").
Katherina and Linnea are children and stay at zero, as do the male presets.
Kept in the harness, not `presets.py`, so `ref-out/` does not move before
the owner approves.

**Looked at:** Krista reads clearly, silhouette and lines through her strap;
Chiyo and Satoko read on their tunics; Reika, Keiko and Kyoko are subtle,
their outer layers covering the chest as agreed at step 4; Elara is a slight
suggestion. Kyoko's parametric coat does not swell with the bust yet, the gap
noted at 9b.

**Revised at the owner's call:** Linnea 0.3 and Katherina 0.2, the rest
unchanged. At tile size both are slight: Linnea's tunic takes a faint curve
and the start of the line, and Katherina's traced jacket swells a little, her
line lying under it.

### 2026-09-25: step 4, second round: the line reaches the side, tapers, and lies under outer layers

**Owner's review of the first round:** the lines mostly work, but should match
the bust's width and could vary in weight; and a lab coat, as the outer layer,
should cover them.

**Change.**
- **Under outer layers.** `_bust_lines` is drawn right after `_tunic`, so a
  coat, robe front or apron bib over the bust covers it; the outer layer's
  own swelling outline is the cue there (steps 6, 9b). On Keiko the line now
  shows only in her coat's opening.
- **Matching the width.** The bottom of the breast as the lower arc of an
  ellipse centred on it: its outer rim on the tunic's draped side at the
  fullest point, its lowest point at the under-bust height under the
  breast's centre, its inner rim reaching toward the sternum as the bust
  grows. The arc runs from a little below the side, where it merges into the
  silhouette, round the bottom and half way up the inner side.
- **Varying the weight.** A filled shape rather than a stroke, thickest in the
  middle and tapering to nothing at both ends; flat and hard-edged.

**Looked at, three shapes** (`out/bust/lines3.png` at 3x and tile size,
`sweep.png`): two quadratics from the side, first lower and flat (ran long,
hooked up at the sternum, read as a smirk), then leaving the side straight
down (the tapered start vanished into the outline and it still read as a
shelf); then the ellipse, which reads as the underside, clearest at 0.75 and
1.0 and legible at tile size from 0.5.

Test rewritten for the filled, tapered shape: reaches the side, stays inside
the torso and below the fullest point, thickens with the bust to 0.5. Suite:
528 passed, 1 skipped; `ref-out/` byte-identical at zero.

### 2026-09-25: step 4, the line under the bust (proposed, for the owner)

**Owner's call before it:** 5c signed off.

**Change.** `_bust_lines`: a short arc under each breast, centred half way
between the sternum and the plain side, just above the body's under-bust
height; its span and dip grow with the bust up to 0.75 and its weight up to
0.5, so it fades in rather than appearing whole. A stroke at 0.6 of the
outline's weight, like the fold lines, never a tone. Drawn last on the chest,
after a traced coat worn under the arms too, so it lies on whatever is worn
on top and comes over the arms inside the bust's mask. Nothing at `bust = 0`;
`ref-out/` byte-identical.

**Looked at, two versions** (`out/bust/lines.png` at 1x and 2x,
`sweep_keiko.png`):
1. A long U from the bust's side toward the sternum: at 1.0 it read as
   under-bust curves, but at 0.25 and 0.5 it ran nearly the torso's width and
   read as a crease across the ribs, since only its weight shrank. Replaced.
2. The short centred arc, the usual convention: reads as a bust from 0.5 at
   2x and at tile size, faint at 0.25 as intended. On Keiko it was first under
   her traced coat (only ticks in the opening showed); moved after that coat,
   it lies on the coat and crosses the lapel into the dress. At the realistic
   build it reads too.

**Not done:** a separation cue at the neckline, which the plan allowed "where
the neckline allows". Left for the owner to ask for.

New test: no line without a bust, two arcs inside the torso and below the
fullest point, weight growing to 0.5. Suite: 528 passed, 1 skipped.

### 2026-09-25: step 5c, the arm in front of the coat and behind the bust

**The owner's call on 5b:** neither order alone; the arm over the coat and the
bust over the arm, which is also what the anatomy says (the coat wraps round
the body behind the hanging arm, and only the bust stands forward of the
arm's inner edge). 5b's coat order is reversed.

**Change.** `lab_coat` back under the arms, which also switches 5b's hand lift
and belt-to-the-edge off for Keiko, since both key on a coat worn over the
arms (Katherina, whose jacket is, keeps her hand fix). `_arms(silhouette=True)`
gives each arm as bare shapes, rotation included, and `_bust_over_arms` clips
the bust's outline to them, so it is drawn only where it lies over an arm: it
leaves the arm's inner edge, crosses the sleeve and joins the edge again. On
the torso side the garment's own outline is already there.

**Measured.** Keiko at `bust = 0` is pixel-identical to her pre-5b render
(`compare_pixels.py` against `47e22f9`), and against that commit `ref-out/`
differs only in Katherina's hand. Satoko's signed-off look is unchanged.

**Looked at** (`out/bust/step5c.png`, before and now at 1.0; `joins.png` at
10x): Keiko's bust now overlaps her sleeve and meets the arm's edge at both
ends, where before 5b its outline floated as a bracket in the white. At 10x
the joins carry a soft grey edge where the outline is cut at the arm's
boundary: under a pixel at normal size, accepted. Her hair still covers the
top of it, so step 4 still matters for her.

Suite: 527 passed, 1 skipped.

### 2026-09-25: step 5b, Keiko's coat over the arms

**Owner's call before it:** 9b's draped tunic signed off in place of 5a's look.

**Done, one variable at a time** (`out/bust/keiko_5b_a.png`, `_b`, `_c`):
1. `lab_coat` back over the arms. The bracket went under the coat's panel,
   whose own edge now swells with the bust (step 6), so **the proposed arm-edge
   anchor for the lobe was not needed** and was not built. Two regressions, as
   predicted: the coat's front edge cut across both hands, and the belt's open
   ends stopped in the middle of the panel.
2. `_arms(hands=...)`: the arms without their hands, and the hands on their
   own, each in its arm's swing; `_hands_after_coat` switches it on for a
   traced coat worn over the arms, and the hands are drawn after that coat.
3. The belt over such a coat runs to the coat's own edge at its height
   (`_cut_half_w_at`, new) and stops half a stroke inside it, so the coat's
   outline ends the band as the arm's used to. `belt_reach` no longer applies
   there: shorter floats mid-coat (P6), longer draws over the sleeve. Keiko's
   plan's P5 and P6 carry the reversal in place.

**Pixel check at `bust = 0`:** Keiko (5625 pixels) and Katherina (477, all at
one hand) and the sheets; nothing else. Katherina's jacket hem used to clip
her hand's edge; the hand is now whole in front of it, which is the right
order for a hand and counted as a fix.

**Looked at** (`out/bust/keiko_5b.png`, before and after, bust 0 and 1.0): at
zero, one clean edge where the armhole line was doubled, the hands over the
coat, the belt ended by the coat's edge. The sleeve reads narrower, since the
coat now covers the arm's inner part out to 0.836 head radii.

**Finding: on Keiko the side outline cannot carry a bust.** Her panel does
swell (edge at the bust row 0.836, 0.869, 0.903 for 0, 0.5, 1.0), but her long
hair hangs over that part of the chest at the chibi, and the swell only shows
below the hair's tips. For her, the line under the bust (step 4) is what will
read, which matters for step 7.

Tests: the belt test rewritten for the new order (arms, coat, belt, hands; the
band's end on the coat's edge), the mock-collar test pointed at the coat's new
place. Suite: 527 passed, 1 skipped. `ref-out/` refreshed (Keiko, Katherina,
sheets); bases unchanged.

### 2026-09-25: step 9b, loose garments hang from the fullest point

**Change.** `_bust_shape(drape=True)`: the plain curve split at the bust with
the fullest point and both controls either side of it moved out by the reach,
so the side is smooth at the fullest point, back on the plain curve at the
waist, and the plain curve itself as the reach goes to zero. This is the shape
step 1a drew and rejected as a barrel ribcage: wrong for the body, right for
cloth. The body (`_torso`) keeps the tuck; the tunic, the over-arm lobe and the
traced cuts' knots (`_bust_bulge`) drape, per the owner's call that fit belongs
to the garment kind. `_Bust` now carries the whole run to the waist and says
how many of its pieces bound the lobe.

**Predicted vs measured** (Satoko, `drawn_widths.py`, new row 30% of the way
from the bust row to the waist): bust row and waist unchanged, as predicted
(0.687, 0.538 at the chibi). The new row, at `bust = 1.0`: 0.568 tucked, 0.668
draped, against a predicted 0.64 to 0.66; the cloth falls more slowly just
below the fullest point than guessed. At 0.01 it moved 0.004, one raster pixel
at that scale. `ref-out/` byte-identical at zero.

**Looked at** (`out/bust/drape.png`, previous commit above, draped below;
`drape_zoom.png` at 5x): Satoko's tunic now reads as cloth over a bust, taken
in at the belt, rather than two round lobes tucked under; at 5x the fall
comes over the arm and meets the side just above the belt, with the existing
daylight between arm and body below it. Katherina's jacket changes slightly.
Keiko's outline now falls toward the belt but still floats inside her coat
(5b). **This changes the look signed off at 5a**, so it is shown to the owner
beside it rather than assumed.

**Not yet following the bust:** the parametric `_coat` (Kyoko) and
`_robe_front` (Reika). Both need to read the body when step 7 gives their
wearers a value. Aprons, straps and plackets sit on the front and are redrawn
over the arm correctly as they are.

New test: the draped side stands clear of the body's tuck and meets it at the
peak and the waist. Suite: 527 passed, 1 skipped.

### 2026-09-25: step 9a, the bust starting below the armpit: tried, not kept

**Owner's calls before it:** step 6 signed off; fit is a property of the
garment kind, not a new knob (for 9b).

**Tried.** The plain side from the armpit down to an onset 35% of the way to
the fullest point, then an S of two tangent-matched quadratics out to it (a
slight hollow where the arm's front fold meets the chest, then the swell).
The fullest point, reach and tuck unchanged, so the bust-row widths were
predicted and measured unchanged (0.579, 0.631, 0.687); `ref-out/` unchanged.

**Looked at, rejected at both builds** (`out/bust/onset.png`,
`onset_real.png`):
- **Chibi:** the chibi has 0.28 head radii between the armpit and the fullest
  point, against 0.53 at the adult build. An upper chest plus a 0.11 swell in
  that height pinched into a hook just below the armpit, at 0.5 as well as
  1.0. A smooth run from one near-vertical line to another set outward has to
  be an S or a corner, so no tuning fixes it. The bust starting at the armpit
  is the chibi's style, which is the anatomy review's own point 4.
- **Adult build:** the S read as a knob, a tight hollow then a small bump, and
  that build's bust is under the arm until its own fix pass anyway.

**Kept:** the refactor it needed. `_Bust` now carries its outline as a chain
of quadratic pieces (`outline`, `pieces()`), which `_rib`, `_bust_over_arms`
and `_bust_bulge` all walk, and which 9b needs. Output identical to the
previous commit on 18 renders (Satoko, Keiko, Katherina; bust 0.25, 0.5, 1.0;
both builds). 9a itself is **deferred to the realistic build's fix pass**.

### 2026-09-25: step 6, traced cuts follow the bust

**Change** (`8e47780`). `_body_knots` gained seven knots at fixed fractions of
the armpit-to-waist run (`_BUST_KNOTS`, 0 to 0.6), each as wide as the
straight shoulder-to-waist line plus the body's own bulge there
(`_bust_bulge`, read off `_bust_shape`). A traced garment then swells in the
bust's shape, not to a point at one knot. At the same fractions on every body
and adding nothing without a bust, they lie on the line the other knots draw:
`ref-out/` byte-identical, and the identity-on-the-traced-body test still
passes.

**Measured.** A traced point 1.0 head radius out at the reference's bust
height, on Katherina: 0.998 flat, 1.072 at `bust = 0.5`, 1.147 at 1.0. More
than the body's own reach (0.11 at 1.0), because placement scales a point by
the knot widths' ratio and this point lies outside the knot line there, so a
garment's side swells a little more than the body under it. New test: a cut
widens at the bust and not at the shoulder or the waist.

**Looked at** (`out/bust/cuts.png`, chest crops at 3x):
- **Katherina** (traced jacket, worn over the arms): the jacket's sides swell
  over the chest and come back in to the waist, smoothly. Works.
- **Keiko** (lab coat, worn under the arms): the bust's outline still sits
  inside her coat's panel like a bracket. Her panel's edge is the armhole
  seam, which is the arm's inner edge, while the over-arm lobe is anchored at
  the torso's side, which lies under her panel. That is 5b's problem, with a
  proposal to the owner: anchor the over-arm lobe at the arm's inner edge
  rather than the torso's side. At the chibi those are within 0.01 of each
  other on a plain tunic, so nothing already signed off would move, and on a
  coat whose panel ends at the sleeve the bust's edge becomes the panel's
  edge bulging over the sleeve, which step 6's knots now make it do.

### 2026-09-24: step 5a, the bust over the arms (taken before step 4)

**Owner's call:** step 3c deferred until a garment exposes the body (no preset
shows any torso today, per the pixel check), and step 5 before step 4, since
the line under the bust is easier to judge once the bust shows.

**Change.** `render_character` builds the chest layers (`_tunic` through
`_crystal_harness`, plus the traced coat worn under the arms) once, draws them
in place, and after `_arms` draws them again inside `_bust_over_arms`: masked
to the lobe a bust adds to the torso (the bust's outline, closed back along
the plain side a stroke inside it), then the outline stroked over the arm.
The katana and staff are left out, being held at the side. `_bust_shape`
holds the bust's points for `_rib` and the lobe alike. Nothing is added at
`bust = 0`; `ref-out/` byte-identical.

**Looked at** (`sweep.py`, 4x zooms):
- **Chibi, plain tunic:** the bust reads, from 0.5 clearly, over both arms,
  tucking back into the side. The notch deferred at step 1 is gone, replaced
  by the under-bust contour as predicted. A small crease at the armpit where
  the sleeve's hem meets the bust.
- **Realistic, tried and rejected.** The arm hangs 0.45 head radii across the
  torso. A lobe to the plain side left a detached strip of chest over the
  arm's middle. Carried in past the arm's inner edge at full depth it hid a
  strip of arm even at a tiny bust, against continuity. Scaled with the bust,
  it floated as a green pad over the arm at 0.25 to 0.75 and read as a ledge
  at 1.0. That is the adult arm's placement, not the bust; the over-arm bust is
  **chibi-range only** (`build < 0.5`, the traced cuts' switch), and at the
  realistic build the bust stays under the arm. Tested.
- **A clip bled.** Clipping applies per layer, so along the soft edge each
  layer under the top one showed through: on Keiko, a grey seam (215 against
  the coat's 238) where her dark dress lies under the white coat. Group opacity
  nearly fixed it (235) but shifts colour; a **mask** composites the chest
  first and leaves no seam (238). Masked, with a user-space region the size of
  the canvas, and an id hashed from the lobe so figures on one sheet cannot
  borrow each other's.
- **Keiko** (coat and traced cut): the bust's outline floats inside the coat
  like a bracket, because her traced coat does not yet bulge with the bust
  (step 6) and her coat and sleeve order is the Keiko-specific part of this
  step (5b). Both wait for the owner.

**Also found, outside this plan:** the eye clips (`eye-l`, `eye-r`) and the
hair clips (`hair-tips`, `hair-front`) use fixed ids, so on a cast sheet every
figure's clip shares one id. It renders because the figures are similar; a
clip that differed per figure would be taken from whichever one the renderer
resolves. Not touched.

Suite: 525 passed, 1 skipped.

### 2026-09-24: step 3b, garments read the body

**Change.** Mostly landed with 3a's refactor (`ba66b6a`): `_tunic` reads the
shared measures and `_rib`, the same ones `_torso` draws. The remaining exact
copies were in the cap sleeve's helpers: `_cap_underside_y` recomputed the
armpit width and `_cap_tip_y` the shoulder drop; both now read
`_torso_at_armpit` and `_shoulder_slope`. `refresh-ref-out.sh --check`:
nothing changed, so not one float moved.

**Scope closed, and what it left.** The robe front (`torso_at_shoulder =
_sleeve_half_w * 0.80`), the coat, the belt (`waist_half_w * 1.03`) and the
apron use their own fractions of the anchors. Those are each garment's own
ease, not copies of the torso line, and putting them on the body would move
pixels, against this step's acceptance. Per the plan they move onto the body
as each is reshaped: the coat and whatever lies over the chest at step 5.

### 2026-09-24: step 3a, the body layer

**Owner's calls before it** (on step 1's sheets): the shape is accepted as a
base; the notch below the arm is deferred to step 5, which turns it into the
visible under-bust contour; steps in the recommended order (3 before 4);
`harness/run.sh` fixed (`f61c3c1`).

**Change.** A byte-identical refactor first (`ba66b6a`): the torso's measures
(`_shoulder_slope`, `_torso_at_armpit`, `_rib_ctrl_y`) and its armpit-to-waist
run with the bust (`_rib`) moved out of `_tunic` into shared module functions.
Then `_torso(sk, p)`: skin, outlined, drawn just before `_neck`, reading no
`Outfit` field (tested). `_BODY_INSET = 1.5` strokes inside the garments.

**Predicted: 0 of 54 PNGs change**, with the slanted cap, a coat and the traced
jacket as the likely exceptions. **Measured, first version: 54 of 54.** Chased
from the smallest (Kyoko's chibi, 6 pixels), three causes, none predicted:

1. The torso's side on the tunic's own curve drew the outline twice, and the
   second pass darkens the first one's antialiased rim along every shared edge.
   A body exactly under a garment can never be pixel-identical; it has to sit
   under the fill. Fixed by the inset.
2. At the realistic build the slanted cap stops short of the arm's outer edge,
   and a shoulder out to the sleeve's width showed past it as a skin crescent.
   Fixed by giving the body the arm's own shoulder: out to the arm's outer edge
   where it leaves the body (`_arm_line`), then down the diagonal to the armpit
   that the arm's top edge follows.
3. The bottom outline showed between the tops of Kyoko's legs.

**Second version: 28 of 54**, two clusters. The nine trouser-wearers at the
chibi showed a skin wedge beside each hip: their trousers are straight columns
at leg width, narrower than `hip_half_w`, which is the owner's standing call in
`_seat_notch_d`, and below a tucked tunic the body is already the legs'
(`_bare_seat`). So the torso now stops in the belt band, where a tucked tunic
ends and the seat starts, at the bare seat's width (both from skeleton-only
functions). The rest were slivers along sloping shoulders, where an inset
measured straight down is less than the same inset square to the line; the
shoulder line is now inset twice as far.

**Third version: 5 of 54**, 5 to 11 pixels each, all at the left stand-collar
tab's corner on the realistic Elara, Krista, Reinhard, Tenno and Viktor: the
tunic left a wedge of page under less than a pixel wide there, and the torso's
outline fills it. **Accepted as a finding**, per the plan's rule, and
arguably cleaner; left side only because of how the tunic's path closes.
`ref-out/` refreshed: the 37 SVGs gain the layer, those 5 PNGs move, no
other PNG does. `ref-out/bases/` (not covered by `--pixels`) refreshed and
compared by hand with `compare_pixels.py`: 0 of 2 differ.

**For step 3c, where the body shows** (`harness/bust/torso.py`, garments off):
the neck's side lines run on down onto the chest; at the chibi a wedge of
page shows between the shoulder tip and the arm; a gap shows between the
torso's end and the legs where nothing covers the seat; the realistic torso
is straight-sided. At `bust = 1.0` the bust shows on the bare body, since
nothing covers the side the sleeve cap used to.

Suite: 524 passed, 1 skipped.

### 2026-09-24: step 2, the pixel check

**Built by a delegate** (`general-purpose`, `sonnet`, in a worktree, 85k
tokens), reviewed and brought in: `./refresh-ref-out.sh --pixels` renders to
the staging area as the other modes do, then `compare_pixels.py` compares every
PNG it would publish (54: chibi, on-white, realistic, three pages) as decoded
RGBA, reporting changed pixels and their box per file. Writes nothing; exits 1
on any pixel change; still prints the SVG byte count, for information.

**Acceptance.** Clean tree: 0 of 54 differ. The delegate's test (a skin colour
changed on Satoko) flagged her PNGs, Kyoko's (derived from her) and the sheet.

**First use, which is also a measurement.** `bust=1.0` set on Satoko for one
run and reverted:

| file | SVG | pixels changed |
| --- | --- | --- |
| `satoko.png` (chibi) | differs | 1113, box (293, 450) to (480, 587) |
| `real/satoko.png` | differs | **0** |
| `kyoko.png`, `real/kyoko.png` | differ | 0 (her coat covers it) |
| `sheet.png` | differs | 602 |

At the realistic build a full bust changes no pixel at all: the arm hides all
of it. At the chibi, 1113 pixels, the notch below the arm. Step 1's
prediction, now counted.

**Also answered by the delegate.** `test_ref_out_matches_the_code`
(`tests/test_smoke.py`) compares SVG text only. A pixel variant in pytest is
feasible (cairosvg and Pillow are in the dev group) but needs the system cairo
library; recommended as a separate test that skips without cairo. Not built;
step 3 is where it would first matter.

### 2026-09-24: step 1c, the shape below the bust

**Change.** The bust is three pieces on `_tunic`'s own rib curve: armpit out to
the fullest point (the curve's point at `bust_y` plus the reach), down and back
in to an under-bust point `_BUST_DROP = 2.0` reaches lower, and the curve's own
remainder to the waist. The tuck arrives on a 45 degree diagonal. New helpers
`_quad_crossing` and `_quad_split` beside `_tunic`.

**Looked at, three versions** (`why_hidden.py`, arms taken away):
1. 1b's shape, reach added on both sides of the split, tapered all the way to
   the waist: a barrel ribcage, not a bust.
2. The tuck arriving level: a bust, but a right-angled shelf against the
   torso's side, which showed as a step just below the arm as rendered.
3. The tuck on the diagonal: a rounded bust coming back into the side. Kept.

**Bug found by looking, fixed, tested.** The first version named the tuck's
lean `slope`, which `_tunic`'s shoulder already reads further down, so every
sleeve tip grew a horn at `bust > 0`. New test
`test_a_bust_changes_nothing_above_the_armpit`, confirmed failing with the
clash put back (3 failed) and passing without it.

**Measured.** Bust-row widths identical to 1b (chibi 0.579, 0.579, 0.631,
0.687; realistic 1.070, 1.070, 1.172, 1.274), as predicted, since the fullest
point is the same point.

**As rendered** (`sweep.py`, whose crop now runs shoulder to waist at every
build; the old fixed window cut the realistic row above the bust): the bust is
under the arm at every value on both builds, as predicted in step 1's
preparation. The only visible trace at the chibi is a small diagonal notch
where the tuck comes back out past the arm's inner edge, from about 0.5 up.
Keiko's traced coat hides all of it. For the owner to judge.

**Zero case.** `refresh-ref-out.sh --check`: nothing changed. Suite: 520
passed, 1 skipped.

### 2026-09-24: step 1b, the bust's height from the armpit

**Change.** `Skeleton.armpit_y` (0.42 of shoulder to waist, the arithmetic
`_sleeve_hem_y` already used, which now reads it) and `bust_y` at
`_BUST_ALONG = 0.30` of armpit to waist, a first guess. Previously 0.45 of
shoulder to waist.

**Predicted vs measured** (torso half-width at the bust row):

| | 0 | 0.01 | 0.5 | 1.0 |
| --- | --- | --- | --- | --- |
| chibi predicted, row 2.066 | 0.580 | 0.581 | 0.635 | 0.690 |
| chibi measured, row 2.065 | 0.579 | 0.579 | 0.631 | 0.687 |
| realistic predicted, row 3.092 | 1.073 | 1.075 | 1.173 | 1.273 |
| realistic measured | 1.070 | 1.070 | 1.172 | 1.274 |

Within 0.004 everywhere: the split now lands about 28% along the curve, no
clamp, and the full reach shows at the row. The arm's ink at the new row still
starts at 0.587 (chibi) and 0.637 (realistic), so as predicted the bulge is
under the arm at every value above about 0.07 (chibi).

**Zero case.** `refresh-ref-out.sh --check`: nothing changed, so moving
`_sleeve_hem_y` onto `armpit_y` changed no float.

### 2026-09-24: step 1a, reach rather than width

**Change.** `Skeleton` stores only the knob, `bust`; `bust_y` and
`bust_reach` are properties derived from the final shoulder, waist and build.
`_tunic` splits its armpit-to-waist quadratic where it crosses `bust_y` and
moves the split point and both neighbouring controls out by the reach, so the
join stays smooth and the halves become the original curve as the reach goes
to zero. At zero it still emits the original single curve.

**Second defect found and fixed with it.** `BodyProfile.applied` and
`waist_shift` replace the shoulder and waist, but the stored `bust_y` and
`bust_half_w` were computed from the unprofiled skeleton, so on every
profiled body the bust sat at a height unrelated to that body's own waist, and
its reach rode the profile's `heads` rather than the chibi build the figure is
pinned to. Derived properties make both impossible.

**Predicted vs measured** (torso half-width at the bust row, head radii,
`drawn_widths.py`):

| | 0 | 0.01 | 0.5 | 1.0 |
| --- | --- | --- | --- | --- |
| chibi predicted | 0.584 | 0.585 | 0.639 | 0.694 |
| chibi measured | 0.583 | 0.583 | 0.624 | 0.668 |
| realistic predicted | 1.077 | 1.079 | 1.177 | 1.277 |
| realistic measured | 1.077 | 1.077 | 1.153 | 1.236 |

Continuity holds. The shortfall at 1.0 (0.026 chibi, 0.041 realistic) is the
bust height: `bust_y` sits so close to the armpit that the crossing lands at
about 5% of the way along the curve, and the split is clamped at 10%, so the
peak lies below the row being measured. That is step 1b's variable, and this
number is the evidence for it.

**Zero case.** `refresh-ref-out.sh --check`: nothing changed. Suite: 513
passed, 1 skipped, before the new tests; the three new tests (skeleton
equality, the bust following a profile and a waist shift, continuity and
monotonic growth) pass.

### 2026-09-24: the first draft read anchors as the figure

Mechanism, measurement and scope in `bust-plan.md`, "What the first draft got
wrong". Taken with `harness/bust/drawn_widths.py` at `504edc3`.
