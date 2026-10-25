# Risa polish: closing the gap to her reference

Started 2026-10-24 at the owner's request. Risa is on the adult woman's body in her school uniform (`docs/risa-adult-plan.md`, released in 0.6.0). She reads close to
`ref/risa-adult/`, but there are gaps: a body that is too broad, and a polish the flat style and the soft finish do not reach. This plan is the campaign to close them, one
stage at a time, each measured against the reference before the owner judges it by eye. The references are guides: a number that differs is a lead, and the pick is by eye.

## Owner's decisions (2026-10-24)

1. **The bikini image (`00`) is canon for her body's proportions.** The uniform images (`01` to `07`) draw her about 6% narrower and with legs 20 to 25% shorter below the knee
   when registered by the irises. That is Grok's drift between edits, not her body, and is not a target.
2. **A new field for the body's proportions is acceptable**, though it moves the recorded fixtures of every character: only Risa's drawing may change, every other character's
   (Franzi is the only other adult woman) stays byte-identical.
3. **Below mid-thigh, where `00` shows nothing,** Risa gets Franzi's knees, calves and lengths, her own thighs tapering into them.
4. **Line work** may go in the flat finish or the soft one: an experiment, both are acceptable.
5. **Shading stays after the base.** The soft finish may grow to shading and more polish, but only once the body, the uniform, the hair's drape, the lines and the eyes are
   right (stages 1 to 7); stage 8 is an option then, not a commitment now.

## The gap analysis (2026-10-24)

Our render and the reference on the bikini's grid (head height 352 px, the chin and the centre line matched, `compare_head.py`'s mapping), made by
`harness/risa_adult/gap_strips.py` (strips in `out/gap/`) and `harness/risa_adult/gap_widths.py` (the numbers).

**Measured, against `00`** (the body is the skin and bikini pixels, the hair left out; rows in head heights H below the chin):

| where | rows | ours against the reference |
|---|---|---|
| outer extent, arm to arm | 0.4 to 2.4 | 6 to 9% wider |
| the torso just under the bust | 1.0 to 1.2 | 13 to 15% wider (269 against 234 px at 1.0) |
| the waist | 1.4 to 1.6 | the same (255 to 319 against 258 to 318) |
| each arm | 1.0 to 1.6 | the same or a little thinner (63 to 70 against 65 to 75 px) |
| each thigh | 2.5 to 3.0 | 15 to 21% wider (175 against 149 px at 2.6) |
| the briefs' top, the crotch | | 0.06 H and 0.10 H lower (`body_landmarks.py`: rows 1041 and 1226 against 1019 and 1189) |

So the body is not uniformly broad: the thighs, the ribcage under the bust and the torso's length are off. The bikini image ends at mid-thigh, so below about 3.1 H there is no
canon.

**Corrected by stage 1's gate (2026-10-24):** this first pass counted skin and bikini pixels by colour, which left out our heavy black outline (about 6 px a run on this
grid) and kept the reference's thin one, so it under-measured ours. The arms are not the right size: the gate, which measures both silhouettes to the ink's outer edge, finds
the forearms 17 to 27% thick and the thighs 24 to 30% wide. Its numbers (stage 1, below) replace the table above.

**Seen, not measured:**

- **The hair's drape.** In the uniform images, locks fall in front of both shoulders and down onto the blazer; ours all hang behind the body, so the blazer's shoulders show as
  one square block. This is probably a large part of why she reads broad in the uniform (an inference, to be checked by stage 4's render).
- **Line work.** Our outline is a heavy black stroke, about three times the reference's, and the hair's strand lines are ink black. The reference draws thin lines in a dark
  tone of what they bound (dark red in the hair, brown on the skin).
- **The hair.** The reference has a sheen band across the crown, lit strands and a brighter crimson (its median `#7b232d`; the preset's `#6b1f2a` is the owner's pick, a prior
  decision). Her cut has no soft-finish clumps (`locks: []`, `ts/src/body-adult-cuts.ts`), so the soft finish adds nothing to her hair.
- **The eyes.** The reference's iris has several tones (a yellow lower half), large catchlights and a heavier upper lash; the two eyes differ (already listed as not done in
  `docs/risa-adult-plan.md`, "Eyelids, first pass").
- **Shading.** The reference has cel shadows on the skin (under the chin, under the bust, the knees, the inner thighs) and on the cloth (the blazer's folds and lapels, a strip
  beside each pleat). We draw none: flat is the house style, and the soft finish covers only the iris, the blush, the fringe's shadow and the hair clumps.
- **Hands and knees.** The reference's fingers are separate and relaxed and its knees and calves are shaped; ours are simpler.

## Invariants

- **Franzi and every other character stay byte-identical** at every stage. A new control defaults to Franzi's drawing; a new piece defaults to nothing.
- **Risa's own goldens move on purpose**, stage by stage, with the owner's say: `ref-out/risa.*` through `./refresh-ref-out.sh`, the recorded fixtures that hold her through a
  `harness/ts_port/golden-updates-*/` updater with a README, as `golden-updates-risa-adult/` did.
- **Flat stays the house style.** Shading planes are only ever inside `finish = "soft"`, and widening the soft finish to skin and cloth is the owner's decision (stage 8), judged by
  blind pairs as `docs/soft-hair-plan.md` describes.
- **The companion keeps working.** Her poses (`body-adult-pose-arm.ts`) read the same body tables, so every body stage is checked in the hanging pose and the companion's
  gestures (wave, cheer, folded arm), as the poses in the uniform were.
- **Gates after every stage** (G1): `npm run typecheck`, `npm test`, `./refresh-ref-out.sh --check`, `./refresh-catalogue.sh --check`, `./refresh-bases.sh --check`.

## Stages

The body comes first, because everything else sits on it: the garments are built from its tables and the hair's drape lies over its shoulders.

### Stage 1: Risa's target and gate

A silhouette target from `00` (`segments/00-bikini/anime-girl.png` less the hair layer, neck down to mid-thigh) and a gate in the manner of `harness/franzi/gate.py`: IoU,
widths at the landmark rows (shoulder, under-bust, waist, hip, thigh) within 5%, the landmark heights (waist, the briefs' top, the crotch) within 0.05 H. Unlike Franzi's gate
it registers by the head, not chin to sole, because the image ends at mid-thigh. Run on today's Risa first and record the numbers: the prediction is a fail at the under-bust
and the thighs and on the crotch's height, a pass at the waist. No shape changes in this stage.

**Done 2026-10-24.** Three harness scripts, nothing in `ts/src/` changed:

| script | what |
|---|---|
| `harness/risa_adult/target.py` | the target: `00`'s cutout less the hair layer, from the neck's top (0.12 H) down, strand gaps filled (only holes up to 1500 px, so the arm gaps stay open), and an **unknown zone** where the hair layer cannot say whether a strand is in front of the body: above the bikini band, hair inside the body's span (the locks lying in front of both shoulders, from beside the neck down the bust's sides), and below it only the narrow bites a strand makes in an edge. `target-check.png` shows both over the reference |
| `harness/risa_adult/body_outline.ts` | our body alone: `adultBodyPath` filled and inked black, with `risa.ts`'s parameters and overrides, so no hair or detail lies over it (checked: its leg runs at 2.6 to 3.0 H are the full render's to the pixel) |
| `harness/risa_adult/gate.py` | the gate: head-registered (`compare_head.py`'s mapping), ours shifted sideways onto the target's body centre (the reference's body is centred 8 px right of the head's centre line: her head is turned, ours was made straight), the unknown zone counted neither way. IoU at least 0.93; the outer extent and the centre run (the torso, or each leg) within 5% every 0.1 H from 0.3 to 3.0 H; the waist, hip and crotch heights within 0.05 H. Franzi's thresholds. The arms are printed, not gated. `--self` passes (IoU 1.000), `--self --stretch 1.08` fails (IoU 0.834, worst width +8.6%) |

**Today's Risa** (`./harness/run.sh harness/risa_adult/gate.py --verbose`): **FAIL**, IoU **0.821**.

| where | rows (H below the chin) | ours against the target |
|---|---|---|
| outer extent, shoulders to hips | 0.3 to 2.4 | +6 to +11% |
| outer extent, the thighs | 2.5 to 3.0 | +19 to +20% |
| the torso under the bust | 1.0 to 1.2 | +18 to +20% (281 against 236 px at 1.0) |
| the torso at 1.4 | 1.4 | +3% |
| the hips | 1.7 to 2.1 | +5 to +10% |
| the upper arm | 1.2 to 1.5 | +3 to +8% |
| the forearm | 1.6 to 2.0 | +17 to +27% |
| each leg | 2.3 to 3.0 | +12% at the top, growing to +30% at 2.9 |
| the waist's height (target 1.18) | | +0.077 H (lower) |
| the hip's height (target 2.06) | | +0.094 H |
| the crotch's height (target 2.14) | | +0.065 H |

Against the prediction: the under-bust, the thighs and the crotch fail as predicted. The waist's width passes where the two waists meet in width (1.4 H, +3%), but its
height does not: ours narrows lowest at about 1.26 H against the target's 1.18, so the whole torso from the waist down sits 0.07 to 0.09 H low, and the 1.0 to 1.2 H rows
compare our ribcage with her waist. That makes stage 2's work, in order of size: the thighs and the forearms (about a quarter too wide), the ribcage under the bust (a fifth),
the torso's length (the waist, hips and crotch 0.07 to 0.09 H higher), then the outer extent, which should mostly follow from the arms and the ribcage.

### Stage 2: a body that can take Risa's proportions

The adult body's outline is half-width tables by depth (`SHOULDER_OUTER`, `ARM_OUTER`, `ARM_INNER`, `TORSO_SIDE`, `LEG_OUTER`, `LEG_INNER` in `ts/src/body-adult-data.ts`,
and `RIB_KNOTS`), imported as module constants by five modules (`body-adult-parts.ts`, `-shirt.ts`, `-blazer.ts`, `-garments.ts`, `-pose-arm.ts`). The work:

1. The tables come from the character, not the module: one function (`adultTables(sk)`) that returns Franzi's tables unchanged by default, used by all five. A refactor
   with no change of output, proved by the byte-identical checks before anything else moves.
2. A body profile that warps them, separately per region rather than one scale (a single scale would also thin the arms, which are already right): the ribcage under the bust,
   the hips and thighs, how far the arms hang from the torso, and the torso's length (the rows of the briefs and the crotch). The traced chains that sit on the body (the
   briefs `ADULT_BOTTOM`, the top `ADULT_TOP`, the bust, the hands' placement) go through the same map, as `bustWarp` does for the bust.
3. Fit Risa's profile to the target until the gate of stage 1 passes, then judge by eye.

The profile is a new field (decision 2), neutral by default so Franzi draws as before; the recorded fixtures of every character take the field's default through an updater
in `harness/ts_port/golden-updates-*/`, as the elbow fields did. Below mid-thigh the legs are Franzi's (decision 3).

**Done 2026-10-24.** What was built differs from the sketch above in one way: the tables were not moved into the character. Everything on the body already goes through one
function, `place` (`body-adult-parts.ts`), which maps a knot [v, d] (head heights) to pixels, so the build is a **warp of the knot space inside `place`**, and the five modules keep
importing their tables as before.

* **`ts/src/body-adult-build.ts`**: `AdultBuild` and `ADULT_BUILDS` (one, `slender`). Vertically, the rows from 0.95 to 1.26 H close up by `shorten` (0.08 H), so the waist, the hips
  and the legs move up rigidly (the legs keep their lengths); the arm closes up by its own `arm_shorten` (0.045 H), so the hands do not rise with the hips. Horizontally, row by row, a
  piecewise-linear map through the traced body's own edges at that depth (the centre line, the torso's side or, below the crotch, each leg's inner and outer edge, the arm's inner and
  outer edge), each moved by a table by depth: `body` (a factor: the torso, and each leg's width about its inner edge), `leg_gap` (a factor: between the legs), and the arm's
  two edges by shifts of their own, `arm_in` and `arm_out` (in H). Points between edges follow linearly, so a garment's ease or a traced chain keeps its place; points beyond
  the arm move with it. Every table is read with an eased step between knots, and the shortening's ramp is eased too, so no shift turns a corner.
* **`place`'s `y` takes the point's half-width** (`y(d, v)`): a point moves with the torso up to the torso's side and with the arm from the arm's inner edge out, blended across the
  gap. The 47 point constructions that pair `w(d, v)` with `y(d)` pass `v` (mechanically: right by construction); the clip rows and bands of the hands and the sleeves take the arm's.
  The hand zones of `adultBodyStroke` put every corner on the hand's rows, since a corner on the torso's rows opened a seam (a white tick on each thigh's outline, seen and fixed).
* **The field** `body_build` (after `body`, null), read by `skeletonFor`, which lays the build on the skeleton as an optional `adult_build` key, absent without one, so a skeleton
  without a build is key for key the one the recorded calls hold. Every other body ignores the field; an unknown name is a KeyError. Not offered in the web tool.
  `harness/ts_port/golden-updates-build/README.md` records the field's fixture update (no drawing moved), `golden-updates-risa-build/README.md` Risa's switch.
* **`RISA`** sets `body_build: "slender"`. `ts/test/adult-build.test.ts` pins the rest: no key without a build, the chibi unchanged by the field, the KeyError, a neutral build moves
  no knot, no build folds the outline, and Risa's torso rises more than her hands.

**The gate**, with the build: **PASS**, IoU **0.941** (0.821 before), worst width **+3.5%** (the outer extent at 0.6 H, the shoulders), landmarks waist **-0.006**, hip
**+0.017**, crotch **-0.017** H. Every torso and leg row is within 2.4%, the outer extent within 3.5%. The arms (not gated) are within 5% from 1.1 to 2.0 H, but +12 to +13% at
1.0 H, where the armpit's cap meets the arm. Measured fingertips 2.51 H in the reference, 2.55 traced, 2.47 with the torso's shortening alone, now as the reference's within a
few px. Franzi and every other render are byte-identical (`ref-out/`, `refresh-bases.sh --check`); typecheck and 980 tests pass (7 skipped).

**The arms, fixed after the first commit (owner, 2026-10-24: "the arms have become quite messy").** The first build moved the arm by the torso's factor (its inner edge followed
the torso's side, through a gap factor of 1) and a width factor (`arm`: 0.78 at the shoulder, 0.95 at the elbow, 0.86 at the wrist). Hanging, that read as the silhouette; raised
or held out, the arm showed it: a kink on the upper arm (the torso's factor drops from 1.0 to 0.85 just under the armpit, which the arm's inner edge followed) and a bulge at the
elbow (the width factor rising and falling). Checked by rendering the same poses traced and slender side by side (`out/gap/pose_pairs.png`): the traced arms were smooth, so the
build was the cause, not the poses. The arm now moves by its own two slowly changing edge shifts, read with eased steps, and the raised (160 and 130 degrees), held-out (90),
waved and bent arms draw as smooth as the traced ones (`out/gap/pose_fix_*.png`, `arm_zoom.png`, `uniform_pose_fix.png`).

**Seen by eye** (`out/gap/slender_bikini.png`, `slender_uniform.png`, `poses.png`): the blazer, the waist, the hips and the thighs read close to the reference; the uniform follows
the body with no change of its own (stage 3 still checks it piece by piece); the raised and folded arms draw clean; the hands are a little narrower (the outer edge's shift is larger than the inner's), their
traced lines unchanged. Open for the owner's eye: the inner edge of the thigh bends a little above the knee, where the wider gap between the legs returns to Franzi's, and from the
knee down the legs are Franzi's (decision 3), which reads straight against her slimmer thighs.

### Stage 3: refit the uniform on the new body

The shirt's torso and sleeves and the blazer are built from the tables and should follow; what is traced is placed by landmarks and needs a check: the pleated skirt's
silhouette and hem (`body-adult-skirt-pleated-data.ts`, through `registration.py`'s `to_body`), the shirt's hem and collar, the blazer's pockets and darts (fractions of the
half-width, so they follow), the socks and the loafers. `blazer_outline_check.py` against `01`; the width the blazer should reach is the new body's plus its ease, not the
drifted `01`'s. Then the poses.

**Done 2026-10-24.** `harness/risa_adult/uniform_check.py` draws the preset with and without the blazer, on the traced body and on the slender build, beside `01` and `02`
registered by the irises, region by region (`out/risa_adult/uniform-{blazer,shirt}-{collar,torso,skirt,cuffs,legs}.png`), and counts the skin a garment should cover.

* **Coverage:** no skin shows under the garments. In the torso's middle none on either body; across the whole width the slender build shows about 700 px more (1,831 against
  1,134), all in the rows 1.95 to 2.05 H and at least 0.6 H from the centre line: the wrists below the cuffs, which sit higher with the arm's own shortening.
* **The collar, the ribbon and the shirt's top** are above the rows the build moves (0.95 H) and are unchanged.
* **The blazer** follows the body: narrower, fitted at the waist, its hem higher, the pockets and darts in place (they are fractions of the half-width). **The buttons were the one
  fault:** at traced depths 1.00, 1.23 and 1.48 H they straddle the rows the build closes up, so the gaps went from 0.23 and 0.25 H to 0.16 and 0.24 H (the top two bunched). The
  shirt's five buttons wobbled the same way. `spacedDepths` (`body-adult-build.ts`) now places a row of details so its first and last land where the warp puts them and those
  between keep their traced proportions; the blazer's and the shirt's buttons use it, and without a build it returns the depths unchanged (`adult-build.test.ts` pins both).
* **The blazer's armhole seam** (owner, 2026-10-24: the blazer read as too wide on the upper body, running on over the arms where `01` does not; the owner drew the line the front
  panel should end on). The seam existed (`armhole`, `body-adult-blazer.ts`) but was drawn in a dark tone of the navy at half weight and did not read, so the front panel and the
  sleeve were one block. It is now inked at the lapel lines' weight, and its middle moved in to the owner's line (traced knots 0.56 and 0.52 at 0.6 and 0.9 H, now 0.53 and
  0.475; on the bikini grid it measured 0.535 and 0.49 H from the centre line against the drawn 0.51 and 0.464). The silhouette itself was not narrowed: against `01` it is 2.5%
  wider at row 560, 5% at 620, 2% at 700, equal at 780 and narrower below (`blazer_outline_check.py`), and at 620 its right edge is the reference's (881 against 884) while the left
  sticks out 24 px, because the reference's body is centred about 8 px right of her head's centre line and ours on it. In `01` the front locks of hair also cover the tops of the
  sleeves, which stage 4 adds.
* **The upper body widened outward above the bust** (owner, 2026-10-24, after the seam: "it reads as if the upper body stretches outward rather than inward above the bust", and the
  breasts as larger). Measured, the blazer's outer width bulged at the deltoid: 405, 427, 423, 424 at rows 560, 620, 700, 780 against `01`'s steadily widening 395, 406, 415, 424.
  The body had the same bulge against the canon: from 0.3 to 0.8 H the target's outer extent is 380, 400, 405, 405, ours was 379, 407, 417, 419 (within the gate's 5% row by row,
  but widening about 60% more between the shoulder and 0.6 H, then holding). `arm_out` now takes the shoulder's outer edge in by more at the deltoid (-0.062 H at 0.55) than at
  its top (-0.038 at 0.3): the body's outer extent is within 0.5% of the target on every row from 0.3 to 0.9 H, the blazer widens downward as `01`'s does (403, 413, 413, 418, 434
  against 395, 406, 415, 424, 446), the gate passes as before (IoU 0.941, worst +3.0%, the torso at 1.0 H), and the raised, held-out and bent arms draw as before. Not changed: the
  bust, which measures as the reference's (283 px wide against 277, its lower edge at 761 against 762); that it reads larger is the flat colour (the reference shades the cups and the
  blazer's front toward the sides), which is stage 8's, and the front locks over the shoulders (stage 4). A smaller `bust` would be a choice by eye, the owner's.
* **The bust under the blazer, and the lapels** (owner, 2026-10-24, from a one-off overlay of the bust contour over the uniform and of `00`'s bikini top over `01`). The blazer sits
  snugly (its cloth 3 to 4 px outside the body's ink edge on every row from the shoulder to the waist, about the ease), the lapels meet just above the bust's lower edge and the first
  button is just below it, as in `01`. Two faults, both of the flat trace of `05`: **the armhole seam ran about 23 px outside the bust** at its height (the front panel about a fifth
  wider than `01`'s), and **the lapels were about three times too wide** (at 0.5 H the flat lapel ran from 0.11 to 0.39 H, `01`'s from 0.07 to 0.15; its collar reached 0.43 H, the
  worn notch sits at about 0.25 H). The seam now comes in to 0.425 H from 0.7 to 0.9 H, just outside the bust's widest point (0.41 H), so the sleeve is about 0.18 H wide at the bust as
  in `01`. The collar, the notch, the lapel's top edge and its fold are read off `01` (a 3x gridded zoom with the navy's range stretched; notch at 0.19, 0.30, the lapel's tip at
  0.30, 0.485, the fold straight down to the V's point; scaled 1.06 across and 1.03 down for the uniform image's drift) and the breast welt pocket with them (0.235 to 0.40 H across,
  0.56 to 0.62 H down), since the flat blazer's, placed by fractions of the half-width, crossed the seam once it came in. The flat trace's lapel and welt stay in
  `body-adult-blazer-data.ts` as its record, unused. The raised arm's cut has its own knots and is unchanged.

  Then (owner, same day) the seam's curve: through fixed knots it ran straight down the bust's side and bowed out *below* the bust on its way in to the armpit, where in `01` it wraps the
  bust's side. It is now the smooth outer envelope (`smoothMax`, a log-sum-exp with a 0.01 H blend) of three lines, row by row: the line down from the shoulder's end (0.562 H at 0.3 H)
  toward the bust (0.38 H at 0.75 H), the bust's own outer edge (`adultBreastPoints`, its outermost crossing with each row) 0.012 H outside it, and the vertical down to the armpit's
  end. Where the bust bulges out the seam follows it (it widens with a larger `bust`), and it hands over between the lines without a corner. A first try that joined the bust's edge to
  the lines end to end left a kink at 0.68 H and a hook at 0.88 H, which the envelope removes.
* **The garments under a raised arm** (owner, 2026-10-25: "the parts of the blazer that were hidden below the arms are just badly drawn polygons, without an outline"). A raised arm took its
  sleeve with it by clipping the whole blazer, and the shirt under it, along a polygon: the armhole's knots (0.60 to 0.56 H out from the centre line, well outside the ribs at 0.43 to 0.46)
  and then straight chords down the torso's side every 0.15 H. That left a wedge of the sleeve under the arm, its edge a clip with no ink, and the shirt's wedge showed past the blazer as white
  slivers. Now a raised side of the blazer (`panel`) and of the shirt (`outline`) is its own outline, one inked path: down the shoulder's outer edge to where the posed arm begins
  (`RAISED_SHOULDER_D`, 0.4 H), curving in to the torso's breadth from `RAISED_SIDE_FROM` (0.65 H) and down it to the hem. The breadth is one table both garments read (`torsoBreadth`:
  the chest beside the bust, then the torso's side; the blazer's `halfWidth` is it plus its eases, as before). No clip is left, `torsoWithoutRaisedSleeves` is gone, and the lock outline's
  covers (`blazerCover`, `shirtCover`) use the same outlines. A first try left the shoulder at 0.34 H and slanted in to the chest by 0.5 H, which put a peak above a hanging upper arm's
  sleeve (a wave); following the shoulder to the arm's top puts the turn under the sleeve's root. The hanging pose is byte-identical (`ref-out/` unchanged); `adult-raised-garments.test.ts`
  pins that a raised pose has no clip of either garment, that its ids are unique, and that a raised side's panel no longer carries the sleeve while the hanging side's is unchanged.
* **The shirt** follows the narrower ribcage and waist; its tucked hem meets the skirt's waistband as before.
* **The skirt** is narrower and higher, and now sits between the hands much as in `01` and `02` (the hands reach its sides); its traced hem and folds are unchanged in shape.
* **The cuffs, the socks and the loafers** are as before: the cuffs show below the blazer's sleeves, and below the knee the legs are Franzi's (decision 3), so the socks' tops
  and the shoes are unchanged.
* **The poses** were checked with the arm fix of stage 2 (`out/gap/uniform_pose_fix.png`): the blazer's posed sleeves draw as the traced ones do.

The harness base `harness/risa_adult/risa.ts` now carries her build as the preset does, so the gate passes by default and `{"body_build":null}` draws the traced body. The older
measuring scripts of `docs/risa-adult-plan.md` (`bust_metrics.py`, `body_landmarks.py` and the rest) measured the traced body; run again, they measure the slender one.

### Stage 4: the hair in front of the shoulders

Front locks over the shoulders and the chest, traced from `01`'s `red-hair` layer where it covers the blazer (registered, `registration.py`), drawn as a part over the garments,
behind the arms where they cross. Checked on the raised and folded arms, where a lock over a moving arm would read wrong (the likely answer: the locks stay on the chest and the
arm passes in front). The bikini drawing gets the same locks where `00` shows them.

**Done 2026-10-25.**

* **The trace** (`harness/risa_adult/locks_trace.py`, then `locks_data.ts`): in `01` registered by the irises, the hair in front of the uniform is the `red-hair` layer's pixels inside
  the uniform's span on their row (between the blazer's or the shirt's outermost pixels, below the neck; the blazer's own layer has no pixels where hair covers it, so a mask of the cloth
  missed them). Two locks, one each side, from the shoulder beside the collar (0.20 and 0.22 H below the chin) down over the outer chest to a pointed tip (0.88 and 0.92 H); a thin
  third piece from 0.96 to 1.22 H, which starts over the chest and so has no top to hang from, is left out. Each is read row by row every 0.01 H (its left and right edges, smoothed),
  carried up from the cloth's top to 0.04 H along its edges' direction into the hair beside the neck, and given two strand lines at a third and two thirds of its width. Scaled 1.06
  across and 1.03 down as the other `01` reads, then stored in the body's knot space (`locks_data.ts` inverts the slender build's warp by halving), so `place` puts them on whatever
  body is built: `ts/src/body-adult-risa-locks-data.ts`, generated.
* **The cut** carries them (`frontLocks` on `AdultHeadCut`, a `FrontLock` an outline and strands); Franzi's ponytail has none, so her drawing is byte-identical.
* **The part** `_front_locks` (`ts/src/body-adult-front-locks.ts`) in a new slot after the arms, before the collar and the head (render.ts calls it only when the part table has it,
  which only the adult one does, so no other body draws anything there): each lock filled in the hair's colour, its strands in the cut's strand tone and weight (`taperedStrand`), and its
  outline inked only where the lock lies over the body or something worn on it, out to the edge of that ink, so above them the lock runs into the hair beside the neck unlined. The
  outline's mask is white shapes: the body's outline, the blazer's panels (`blazerCover`), the shirt's body (`shirtCover`), each cut as the drawing cuts it for a raised arm, and the
  posed arms with their sleeves (`adultPosedArmCover`, grown by the outermost sleeve's ease, `blazerSleeveEase`, `shirtSleeveEase`), each with its own ink. Seen and fixed on the way:
  inked everywhere, the outline drew two heavy lines up through the hair to the jaw; clipped to the body's outline alone (owner, 2026-10-25), it stopped short of the blazer's
  shoulder (which stands off the body by its ease) and of a raised arm's sleeve.
* **The locks' own outlines** (owner, 2026-10-25, after the raised-arm fix of stage 3: "with arms raised the outline of the front locks disappears"). Masked to the body and the clothes,
  a lock lost its line wherever nothing was worn behind it: under a raised arm the sleeve has gone and the viewer's left lock lay partly over the long hair behind the torso (47 of its 61
  outline points inked, against 55 hanging). Now each lock has its own outline everywhere below the shoulders (`OWN_INK_FROM`, 0.35 H below the chin: a white band in the mask), whatever
  lies behind it, and only its top, where it comes out of the hair beside the neck, is masked to the body and the clothes; 55 of 61 again in both poses, the rest the open top. The hanging
  pose is pixel-identical (only the SVG's mask text changed).
* **cairosvg's masks** (found on the way, tested in isolation): cairosvg reads a mask by its **alpha**, a browser by its luminance, and it ignores a mask given `maskUnits="userSpaceOnUse"`
  with an explicit region. A mask of white shapes on nothing, in its default units, reads alike in both; a black backdrop makes cairosvg let everything through. So the outline's mask is
  white shapes only, and the locks have **no mask for posed arms**: one that hid the posed forearm and hand with black shapes on white would hide them in the companion's browser and in
  no PNG. The locks are drawn over a posed arm's root as over a hanging arm's (so nothing changes between a hanging arm and one held out a little), and in this pose model a bent forearm
  folds outward, the way the arm was raised, never across the locks; the waves' and the cheers' hands stay clear of them in the renders.
* **Seen** (`out/gap/slender_uniform.png`, `slender_bikini.png`, `out/gap/lock_poses.png`, `lock_pose_zoom.png`): in the uniform the locks fall over the blazer's shoulder line and the outer
  chest as in `01`, and the front reads narrower; in the bikini they lie along the bust's sides to the band as in `00`. The reference's locks are fuller, split into more clumps and
  a little longer; ours are one shape with two strands each, a choice for the flat style.
* `ts/test/adult-front-locks.test.ts` pins that only a cut with locks draws them, each outline masked, that a posed arm is in the outline's mask and the mask is white shapes only, that the
  ids stay unique, and that the locks follow the build. Her drawing is now 389 KB (the outline's mask repeats the blazer's panels), inside the adult budget (400 KB) but close to it.

### Stage 5: line work

Thinner lines in a dark tone of what they bound, for Risa: the outline, the hair's silhouette and strands. Her cut already carries its own face stroke (0.45), so per-cut line
settings are the pattern. Flat or soft is an experiment (decision 4): try both and pick by eye.

**Measured and tried, 2026-10-25 (not yet a setting).** `harness/risa_adult/line_measure.py` reads the line work of `01` against our uniform render on the bikini grid: the reference's lines
are about 2 px everywhere (median, the hair and face, the torso, the legs), ours 2 px in the face, 4 on the torso and 6 on the legs and the outline, and we draw 2.2 to 4.3 times the line pixels;
the reference's lines are near-black on the uniform (10, 5, 15) and the legs (6, 3, 2) but dark red on the hair (40, 8, 6), ours neutral black (13, 13, 13) everywhere.
`harness/risa_adult/line_variants.ts` draws the preset five ways as a text pass over the finished SVG (as `softStrokeWidths` is), for the owner to pick by eye: a, flat as it is; b, soft as
it is (strokes 0.66, the fringe's lines tinted, the hair silhouette's outline still black because the adult hair is drawn outside `_hair_lines`); c, flat with strokes 0.6 and the hair's
outline in its strand tone; d, flat 0.45 tinted; e, soft 0.7 tinted. Strips: `out/risa_adult/lines-{head,torso,full,1x}.png`. Seen: c and d read closest to the reference at full size, and
all five stay legible at the native 400 x 500. Not reached by the pass: the hair's strand lines are filled tapered shapes, not strokes, so they keep their weight in every variant and
are much of why the hair reads busy; thinning them is the cut's `strandWeight`.

**Done 2026-10-25: the owner picked c** (flat, lines at 0.6, the hair's outline in its strand tone). It is a field, `line_style` (after `highlight_strength`, null), naming a style of
`LINE_STYLES` (`ts/src/character.ts`); `fine` is c. `renderStages` scales every stroke by the style's `scale` in the same step as the soft finish's (they compose: soft and fine is 0.66 x 0.6),
`adultHairInk` (`body-adult-parts.ts`) draws the hair silhouette's and the front locks' outlines in the cut's strand tone when the style asks, and the hair's tapered strands (the hair's,
the fringe's and the front locks') take the scale too (`lineScale`), which the text pass of the experiment could not reach: the hair's interior reads lighter and finer, closer to the
reference's fine strands (`out/risa_adult/lines-fine-vs-c-*.png`). The fringe's thin edge lines stay as they were. `RISA` sets `line_style: "fine"`; every other character's drawing is
byte-identical. The field's fixture update is `harness/ts_port/golden-updates-line-style/README.md`; `ts/test/line-style.test.ts` pins the rules.

### Stage 6: the hair under the soft finish

Clumps for `long_straight_fringed` (its `locks` list is empty), and a sheen band across the crown, inside the hair's silhouette, scaled by `highlight_strength`. Blind pairs.

**Done 2026-10-25.** The tones of `00`'s hair, read on a grid at the cut's calibration (the hair's luminance smoothed, above 1.28 or below 0.72 of its median): **lit**, a sheen across the crown along
y -0.40 to -0.60 head radii (left, centre and right, dipping at the middle onto the fringe's top), the front locks over the shoulders, the fringe's tips; **shadow**, the hair behind the neck
inside each curtain (y 0.4 to 1.4) and the falls behind the body (y 2.1 to 4.1, outer and inner).

* **The clumps** (`LONG_STRAIGHT_FRINGED_LOCKS`, `body-adult-cuts.ts`): three lit clumps along the sheen's measured centre line, a shadow behind the neck each side, and a shadow down the outer and the
  inner fall each side. The neck's shadows are centred on the face's own edge and then the neck's, so the face covers their inner half and a band shows along it; centred out on the curtain
  first, each showed whole, as a dark oval beside the face.
* **Over the fringe:** the fringe is drawn over the face as its own shape, so it hid the sheen where it dips onto it. `adultHairFront` draws again, clipped to the fringe, the clumps that reach its
  rows (above 0.25 head radii: the three lit ones), not the whole set, which would write the rest twice.
* **The front locks** are in the body's frame, which the head's clumps cannot reach, so `adultFrontLocks` draws a lit clump of its own down each lock's middle (the two strands' midline, 0.6 of
  the lock's width), clipped to the lock.
* **Strength:** the soft finish's lit tones rise only a little on dark red (by design: a tint toward white read as frosting in the 2026-10-16 blind pairs), so the sheen was hard to see. A cut now
  carries `lockGain`, a multiple of the shared strength: Franzi's 1 (her soft drawing is unchanged), Risa's **3**, the owner's pick of 1.6, 3 and 5 (`harness/risa_adult/soft_gain.ts`,
  `out/risa_adult/soft-gain-{head,bikini}.png`): the sheen and the front locks' light read, the shadows stay moderate (at 5 the band beside the face and the lobes beside the waist got heavy).
* **Size:** her soft drawing is about 414 KB (flat 389 KB). The owner raised the adult soft budget from 400 KB to 440 KB (`rules-soft-locks.test.ts`), and expects such raises as detail is added.
* Every flat render is byte-identical (`ref-out/` unchanged: the presets are flat). `ts/test/adult-soft-hair.test.ts` pins that the flat finish draws no clumps, that the soft one draws them behind,
  over the fringe (only those that reach it) and down each front lock with unique ids, and Franzi's gain of 1.

### Stage 7: the eyes

Per-eye lids, wings and lashes traced as the brows were (`harness/risa_adult/brows.py`), the inner corner's flick, and the iris's lower half in a second tone (flat) or graded
(soft). The two eyes may differ in shape while their placement stays the levelled one (`body-adult-cut-level.ts`).

**Done 2026-10-25.** Her eyes were Franzi's measured eye with a few settings; up close (`out/risa_adult/eyes-compare.png`) the differences were a bold black lower outline with hard corners (the
reference's lower lid is thin, soft and broken), an iris with two tones where the reference has three (a dark top band, the colour, a large yellow-green crescent), highlights mirrored from eye to
eye where the reference lights both from the viewer's upper left, and a shorter wing.

* **The trace** (`harness/risa_adult/eye_trace.py`, then `eye_data.ts` into `ts/src/body-adult-risa-eye-data.ts`): in the eye model's frame (reference pixels about the iris centre, x outward, y
  down, at the head's calibration). Her face is drawn straight on purpose (the owner) while the reference's head is tilted 6.3 degrees and a little turned, so each eye is levelled about its
  iris centre, the left mirrored onto the right, and the two averaged as masks on a 0.25 px grid: one frontal eye, drawn mirrored on the straight face, its placement the levelled one. From
  the `green-eyes-1` layer (the whole eye) and the colours under it: the lid is its dark pixels that are not green (the iris's dark top band is dark green and must not count) and not the pupil,
  the opening the rest; the iris's centre, half width and drop; the light crescent's start (7.25 px below the centre); the pupil; the highlight, near-white and unsaturated in the iris's upper
  part, kept in image orientation. Checked on `out/risa_adult/eye-check.png` (each eye with the mean outlines over it).
* **The iris's tones**, measured as shifts from its middle band and given against the preset's eye colour (`#78925a`, the reference's lower half, near the crescent): the middle band at 0.705
  of its value (so the iris's body is darker than the eye colour), the dark top band as before (`shade` 0.55, the measured 0.51), the crescent turned 0.076 toward yellow at 1.11 of its value.
  Filled with the eye colour itself, the body first came out as light as the crescent, which then did not show. The soft finish grades through the same three.
* **The drawing** (`tracedEye`, `body-adult-eyes.ts`, when a cut has an `eyeShape`; `AdultEyeShape` in `body-adult-cuts.ts`): the opening in the white, the iris clipped to it with its three tones
  (the crescent an ellipse whose top is the traced start, clipped to the iris), the pupil, the rim, the highlights (frame x is the side times the image offset, so both stay at the upper left),
  the lower line along the opening's bottom in the lid's ink at the cut's thin `lowerLine`, the crease, and the lid with its wing and lashes as one shape. Opening, gaze, size and tilt go through
  the same frame and lowering as Franzi's eye (checked: `out/risa_adult/eyes-states.png`). The **shut eye** was Franzi's heavy black line, wider than Risa's eye: a traced eye now shuts onto its
  own lower edge, one leaf from the wing's tip along the opening's bottom, in the lid's colour, as thin as the open lid (`out/risa_adult/eyes-closed.png`).
* Franzi's eye is untouched (`eyeShape` null, `ref-out/franzi.*` unchanged); Risa's drawing is 383 KB (her eye has fewer parts than Franzi's). `ts/test/adult-eye-shape.test.ts` pins the cut's
  choice, the iris's tones, the highlights' orientation and the shut eye's colour.

Not done: the inner corner's flick (the reference's is a faint mark, lost in the average), and two eyes of different shapes (the owner keeps the face symmetric).

### Stage 8: cel shading, after the base is right

Hard-edged shadow shapes, one tone each, under `finish = "soft"` only: on the skin (under the chin, under the bust, the knees, the inner thighs) and on the cloth (the blazer's
folds and lapels, the strip beside each pleat, of which the skirt's trace found three of ten). The owner allows the soft finish to grow this way (decision 5), once stages 1 to 7
are done; it is judged by blind pairs, and `CLAUDE.md`'s rule for the soft finish is updated with it.

**Done 2026-10-25, kept by the owner.** `harness/risa_adult/shadow_map.py` marks where the reference shades her, per material (its Grok layers, darker than the material's median):
on the skin a large shadow on the neck under the jaw, a band under the bikini top, thin bands down the torso's sides and the inner thighs, and in the uniform a band on the thighs under the
skirt's hem; on the blazer a band down each panel's outer side widening toward the hem, and a strip beside each lapel's fold; on the skirt a strip beside every pleat and a band along its top
under the blazer's hem.

* **`ts/src/body-adult-cel.ts`**: one tone per material (`shade()` of what they lie on: skin 0.86 with a little more saturation, the navy 0.62, the skirt 0.80) and `castShadow`, a shape moved down
  and filled, for the caller to clip to what it falls on. Most of the reference's shadows are cast ones, so they are the casting shape moved down: the face's skin onto the neck (clipped to it,
  under the face, so only the crescent below the jaw shows), the bikini top onto the ribs, the skirt onto the thighs (clipped to the body, under the skirt), the blazer's panels onto the skirt
  (clipped to the skirt). The rest are bands: `edgeBand` (`body-adult-parts.ts`) along the torso's side and each inner thigh, tapering to nothing at both ends; on the blazer a band inside each
  panel's side from 0.8 H to the hem, 0.025 to 0.075 H wide, and a 0.014 H strip outside each lapel's fold, clipped to the panels (`blazerCel`); on the skirt a 0.022 H strip on the far side of
  each fold line, clipped to the skirt. Everything is under the lines (the pockets, the darts, the folds), so no line moves.
* **Only for a cut that asks** (`celShading` on `AdultHeadCut`, Risa's true, `celOn`): applied to every adult figure in the soft finish, it moved Franzi's soft drawing, which two tests pin
  (`adult-face-baseline` and the soft cost test); the campaign's rule is that only Risa changes.
* The neck is drawn twice in the uniform (the shirt redraws it inside its collar's opening), so its clip took an id suffix (`adultNeck(sk, p, "-over")`).
* Every flat drawing and Franzi's soft one are byte-identical; Risa's soft drawing is 438 KB (the budget 440 KB). `ts/test/adult-cel.test.ts` pins the opt-in, the flat and Franzi's soft drawings
  without shadows, and unique ids.
* **Blind pairs** (`harness/risa_adult/cel_pairs.ts`): the soft finish with and without the shadows, in the uniform, the bikini and a wave, each pair in a random order, the key in
  `out/risa_adult/cel-pairs/key.json`, not opened before the owner judged. **Verdict:** the owner preferred A in all three pairs, and A had the shadows in all three (the owner noted the shadows
  were visible, so the pairs were not blind in effect: a preference, not a blind test). `CLAUDE.md`'s rule for the soft finish now allows the cel shadows on a cut that asks for them.

### Stage 9 (optional): hands and knees

Relaxed fingers and a shaped knee and calf. Lower priority than the rest; the hands are traced data shared with Franzi, so a Risa-only change is a second hand set.

## Open questions for the owner

None at present: the four the first draft listed are decisions 2 to 5 above.
