# Adult body status

The record for `adult-body-plan.md`. Newest findings first below the resume section.

## RESUME (for a fresh context)

- Campaign: a separate adult-female body type, about 6.4 heads, SFW. Plan in `adult-body-plan.md`. References in
  `ref/franzi/` (untracked on `dev` so far). Work in the `dev` worktree (`../anime-character-creator-dev`), in `ts/`.
- Rules that bind: no sensitive parts, bare view in `harness/` only, age floor 21 in the render code, every existing
  render byte-identical, no commit unless the owner asks, no trailer, no em dashes or double hyphens in prose.
- Owner agreed (2026-10-17) to the CLAUDE.md amendment at stage 7 (adult build as its own decision: SFW rules, bare
  view in the harness only, age guard in the render code), and that the proper head, hands and feet for Franzi come
  after the body is done (stage 5, traced from the new references).
- Owner signed off (2026-10-17): the body, the chest, the bikini top and the briefs, the eye shape and lid. Head and hair still
  being polished (5e). The hairline pass is done but uncommitted and not yet seen by the owner (see the first finding below).
  Next action: the owner's look at the hairline, then the steps where the lock pieces meet the dome, then 5d (preset) and
  stage 6 (garments). `PLAN.md` at the repo root points here with the order of work.
- Last commit on `dev`: "PLAN.md: pointer to the Franzi and adult-body campaign, where it stands and what is next". Uncommitted:
  `harness/franzi_hair/face_trace.py` and `ts/src/body-adult-head-data.ts` (the hairline pass). Gates green on it (823 TS tests
  with 7 skipped, typecheck, refresh checks, ruff, 1051 Python tests, body gate IoU 0.957). `ref/franzi/` is tracked on `dev`
  now; nothing is on `main`.
- Running the harness in a fresh worktree: `cd ts && npm ci` first (typecheck needs `typescript`); `./harness/run.sh` goes through
  `uv`, which in a sandbox needs `UV_CACHE_DIR` pointed at a writable directory; the hair scripts hard-code a
  `/Users/henrik/...` path to `trace_lib`, so run them with `PYTHONPATH=.claude/skills/trace-reference`; `out/` is ignored, so
  make `out/franzi` and `out/franzi_hair` and run `harness/franzi/measure.py` once (it writes `target.png` that the body gate
  reads). The hair chain is rebuilt with `face_trace.py`, `trace.py`, `pieces.py`, `slivers.py`, `contrast.py` then `strands3.py emit`, `emit.py`,
  in that order; from a clean tree that reproduces the committed data byte for byte.

## Scoreboard

| stage | state | gate numbers | owner |
|---|---|---|---|
| 0 plan, target, measurements | done 2026-10-17 | target seam leg ratio 1.174 | n/a |
| 1 gate harness | done 2026-10-17 | self 1.000 pass; tall_chibi IoU 0.489 fail | n/a |
| 2 profile | done 2026-10-17, G1 green, G2 passed | G0 IoU 0.741 (predicted 0.80 to 0.88: wrong, the hip is not honored); landmark error waist 0.006, hip 0.082, crotch 0.247 H | n/a |
| 3 torso and limbs | G0 pass, G1 green, G2 passed after one fix round (2026-10-17); waiting for checkpoint 1 | IoU 0.940, widths within 3.2%, landmarks within 0.026 H | checkpoint 1 pending |
| 4 bust, underwear | done 2026-10-17: G1 green, G2 round 1 found the bust too weak and a crotch tick, both reworked | G0 unchanged (IoU 0.940); 820 TS tests | none planned |
| 5a head and face | done 2026-10-17: traced head and ears, face tuned | eyes 0.746 r apart (ref 0.75) | |
| 5b hair | done 2026-10-17: `swept_ponytail` traced | silhouette matches the reference's by eye | |
| 5c hands and feet | done 2026-10-17: G2 round 1 fixed (neck gap) | G0 IoU 0.942 | checkpoint 2 pending |
| 5e head and face polish (before the garments) | eyes, brows, lid, crease done 2026-10-17; hairline pass done (uncommitted, owner has not seen it); lock-to-dome steps next | | checkpoint 2b |
| 5d Franzi preset | | | |
| 6 garments | | | checkpoint 3 |
| 7 guard, tests, catalogue, web | | | checkpoint 4 |

## Findings

### 2026-10-18, outlines rebuilt from the visible regions (`outline_masks.py`, `outline_trace.py`, `outline_view.py`)

The owner's report: the hair outline clashes with the face and looks odd in places. Looked at the four tiles (each temple, each side of the
jaw) against the reference first. The faults were structural, not a matter of a few numbers: the hair was cut into a dome and two free
pieces by straight lines, each with its own outline and its own stroke clip, so there were steps where they met (about y 215), a flat
ledge at the eye-band cut, hook corners where the cut masks left their edges, an eye-band patch of face skin over the hair with a tick at
each end, and two outlines on every skin/hair edge (the face's and the hair's) that never quite coincided. The face had been mirrored
from its right half, and its eye-band polygon was a rectangle.

Now every visible region is its own mask read from the reference, and each is traced to its real edge: the face (skin, with the eyes,
lashes and brows counted as face since they are not hair; the thin slivers between a curtain and the face's edge line are taken out by an
opening at the temples), the ears, the small skin strips beside the face (under each ear, the temple slivers), and the hair silhouette
(every visible hair pixel plus the skin regions shrunk 4 px, so its edge only ever meets the page, the neck or the shoulder and never
doubles a skin line). Drawn in this order: silhouette with strands clipped to it, strips, ears, then the face over them, then brows and
eyes. `ADULT_HAIR_DOME/LEFT/TAIL`, `ADULT_FACE`, `ADULT_EAR_*` and the temple sliver are no longer used (the data files are left in place).
Chains sit 2 px outside the skin (the drawn black line's centre) and 1 px inside the hair edge (hair has no drawn line).

Found on the way: the jaw's drawn line is about 2 px wide and its anti-aliased edge is warm enough to bridge the face to the neck, so the
face component is labelled on an eroded mask and grown back; a row-wise fill between the skin's outermost pixels cannot reach the strip
left of the outer eye corner and left a rectangular hole round the eye; the segmentation counts the black brows as hair and cut a slit
into the face from the curtain side (closed vertically in the eye rows); the first grow/shrink formula used a linear threshold and moved
the edge the wrong distance (it is a normal-CDF threshold now).

Open: the strips are still a little lumpy (the small blobs at the left outer eye corner and under the right ear); the ponytail's tip and
the right side cut are as before; the silhouette follows the reference's ragged AI-segmentation edge at 1.6 px smoothing, which is
slightly wobbly on the left side of the skull.

### 2026-10-18, the ponytail goes behind the shoulder

The owner asked for the ponytail to be extended so it looks as going behind the shoulders. In the reference its end tapers to a point exactly
where the shoulder's line crosses it (the shoulder's top is at y 506 to 516 under it); ours stopped in a rounded end just above our
shoulder, with a sliver of page between it and the neck, because the hair was drawn over the body and its mask ended there. Two changes:
the hair mask is extended down past the shoulder line and left to the neck (a polygon in `outline_masks.py`, its right edge carrying on
the mask's own taper, x 799 to 790 over rows 490 to 513, then dropping behind the shoulder), and the whole hair silhouette is drawn
behind the body (`adultHairBehind`, the shared `_hair_tail` slot, before the torso) so the shoulder and neck cover the extension. The skin
strips and ears stay over the body (`adultSkinBeside`, the `_ears` slot) and the face goes over them. A first version dropped the right
edge vertically at x 800 and left a small step above the shoulder line; carrying the taper removed it.

Side effect, which matches the reference: the small piece of back hair beside the neck is behind the neck now, not over it. One thing the
reference does that this does not: its hair is in front of the bikini strap where they meet, ours is behind it, as the owner asked
for the shoulder.

### 2026-10-18, hair and face outlines smoothed (`fit_smooth` in `outline_trace.py`)

The owner asked for the hair outline to be smoothed so it looks more natural. Measured first: the silhouette chain was 89 quadratics with a
median length of 15 px, and 81 of its 89 joins turned the line by more than 10 degrees (51 by more than 25), because the edge is that of a
ragged AI segmentation fitted with as few curves as stay within 2 px. Those kinks, not the overall shape, are what read as wobble.

`fit_smooth` takes the mask edge, low-passes it along its length (sigma 7 px for the hair, 5 px for the face), blends the light smoothing
(2 px) back in wherever the heavy one would move the edge more than about 2.5 px (so a narrow lock, the ponytail's wisp and the chin keep
their points), resamples every 7 px and draws it as a quadratic B-spline (the curve through the midpoints of the polygon's sides with each
vertex a control point), whose slope cannot jump at a join. The result stays within 1.9 px of the real edge (hair) and 1.7 px (face). It is
now 278 + 16 curves for the hair and 105 for the face (more curves, each a short smooth one; the data file is 18 KB). The face got it too
because the border where hair meets skin (curtain edges, temples, jaw) is part of how the hair reads, and it had the same kinks. Strips and
ears keep the old fit (few curves, small).

Not changed: the corner where the ponytail's extension polygon meets the mask's left edge (about ref 718, 450) is a real corner in the mask
and shows as a slight angle beside the jaw.

### 2026-10-18, ears traced properly (`outline_masks.py` ears and conchas, `ear_lines.py`)

The ears were plain blobs. Looked at both at 12x against the reference first: the mask kept only the pale outer rim (263 px left, 844 px
right) because it required brightness over 105 like the face does, and missed the shaded inner part (lum 80 to 160) and the fold lines
(lum 13 to 80). Skin and its drawn lines are warm (red minus blue 25 or more; fold lines 38 to 77, shaded part 70 to 95) where hair is
neutral (0 to 7), so the ear mask now uses that hue test with no brightness cut (422 and 1053 px).

An ear is three layers in the reference and in the render now: (1) the skin with its outline (`ADULT_SKIN_EAR_L/R`, fitted with
`fit_smooth`, 2.2 px smoothing and 3.5 px steps so the right ear's pointed lobe survives), stroke at 0.5 of the outline weight since the
reference's ear outline is thin; (2) the shaded inner part, the concha (`ADULT_EAR_CONCHA_L/R`; the right one is two regions, the apex
and the lower part left of the arc), filled with `shade(skin, 0.83, 1.6)`, which is the measured ratio of the reference's shade to its lit
skin, a second tone on a small element as `CLAUDE.md` allows; (3) the fold lines (`ear_lines.py`, `ADULT_EAR_FOLDS_L/R`), traced like the
hair strands, points read off a grid and snapped onto the dark ridge: the right ear's upper fold (86% on a ridge, control 10%), its
arc (42%: it is a tan-to-pale boundary, dark only at the lower end, so the ridge test undersells it) and the left ear's short stroke
(50%, a 5 px mark). Fold weight 0.38 of the outline, tapering at both ends.

The left ear is only partly visible in the reference (the lock covers most of it), so it is traced as the visible region and not
mirrored from the right. Left over: the strips beside the face are still lumpy (the blob under the right ear is the most visible), and
the arc fold is drawn at constant weight where the reference's is thin at the top and heavy at the bottom.

### 2026-10-17, strand lines traced one by one (`strands3.py`, replaces the by-eye `strands.py`)

The owner's read was that the strand lines did not match the reference's at all. Checked: the reference's lines are dark on near-black, so
they cannot be seen on the plain image or on the linear stretch `strands.py` used, and the hand-placed ones ran across the real arcs.
`contrast.py` now writes four views (A linear, B gamma, C local contrast, D both); C has the crispest lines and is the tracing base. In
`strands3.py` each strand is a few points read off a gridded zoom (reference px), snapped along its normal (within 3.5 px) to the darkest
ridge of C, and reported with how much of it lies on a ridge against a control (the same curve shifted 8 px): 27 strands, 60 to 100%
on a ridge against 4 to 38% for the control, most above 80%. A residual map paints every dark ridge no strand covers yet, which is how
missing lines were found. `strands3.py emit` writes `out/franzi_hair/strands.json`; `emit.py` turns it into `ADULT_HAIR_STRANDS`.

What the reference's hair is, once it can be read: a whorl at about (679, 158) with a fan of arcs above it, a stack of nested scallop arcs
wrapping the right side of the crown (five traced), long arcs sweeping left and down the skull, a long sweep line that becomes the
curtain's inner edge and runs on down the white highlight streak of the ponytail, and many fine parallel lines in the ponytail. The lower
left lock has no dark lines at all (smooth, one faint highlight), so strands end near y 310 there; the old single line down it was wrong.

Corrections made on the way, so they are not repeated: the first ridge measure used the plain luminance and called a correctly placed strand
25% on a ridge (the measure moved to the stretched view and got a control); a line placed down the middle of the bright wedge by the right
curtain was not on any line (the thin line is on the wedge's left edge); and highlight streaks dip on both sides in a difference of
Gaussians and read as lines, so the residual map requires the pixel itself to be dark.

Not traced yet (faint, secondary): the fine parallel lines in the lower left of the ponytail beyond two, the thin lines along the left
silhouette beyond three, the outer arcs on the far right below the ear, the curtain's wedge-edge lines. The strand colour and weight in
the render are unchanged (pale tapered lines on near-black hair, so they show); they are lighter than the reference's own lines.

### 2026-10-17, hairline pass (`face_trace.py`; the face chain above the brows)

The hairline is the top edge of the face chain (`ADULT_FACE`), so the pass is a change to how that chain is traced. Compared at
4x with `aligned.py` and its 50% overlay, three things were wrong, each measured before it was changed:

1. **The left forehead was a mirror of the right.** The face was made symmetric from its right half, which put the left
   hairline about 0.05 radii (7 to 9 reference px) too far out; the reference's left curtain falls over the forehead. Above the
   brows the face is now traced as it is.
2. **The shadow the hair casts on the forehead was left out of the skin.** A strip about 8 px wide along both sides, `(214,154,123)`
   against the lit `(252,208,181)`, is 153 from the lit colour and the skin test cuts at 70, so the hairline sat on the strip's inner
   edge. It is skin (red minus blue about 85, hair is 0). Warm light pixels that touch the face are taken in the hairline rows only;
   `face_mask.npy`, which `trace.py` and `pieces.py` read, is unchanged.
3. **The edge was ragged**, stair-steps from the AI image's segmentation. The hairline rows are smoothed (sigma 2.5 px).

Two mistakes on the way, kept so they are not repeated: blending the two masks over the transition rows flipped the whole gap at
once and left a horizontal ledge (the edges are interpolated row by row now); and fitting the whole loop at once kinked the chin,
whose bottom is a pixel sawtooth (below the join the chain is the old symmetric trace's own curve, so cheeks, jaw and chin are
the ones the owner signed off). Measured, new against old: at most 2.0 px (mean 0.4) from the eye band down, 3 to 12 px above it.
The forehead now has the reference's rounded trapezoid instead of a hexagon.

Seen in the same renders and not fixed (candidates for the next pass): the lock pieces and the dome meet in a visible step in
the silhouette at about y 215 on both sides (the pieces are dilated 4 px and their fill is unstroked above the stroke clip, so it
pokes past the dome's outline); a flat ledge on the left lock's inner edge under the eye (the band cut at 0.5 radii); a thin tick
at each temple where the face-band patch's clip starts; the pale temple strip now floats a little off the forehead edge; the
ponytail's tip is a wedge and its right side has a flat cut; the left ear is hidden; the strand lines are traced now (see the entry above).

### 2026-10-17, stage 2: profile (prediction, written before the first run)

Units: head radii below the head centre (chin at 1.0; one H is 2 head radii, so a width in H is a half-width in head
radii). First profile from the stage 0 table, `heads` 6.4: shoulder_y 1.56 (0.28 H below the chin), waist_y 3.6 (1.3 H),
hip_y 5.4 (2.2 H), ankle_y 10.4 (4.7 H), sole 11.8 by construction; shoulder_half_w 1.0, waist_half_w 0.69,
hip_half_w 1.23, arm_half_w 0.14, arm_x 1.14, leg_half_w 0.38, neck_half_w 0.22, wrist_y 6.2, wrist_x 1.5.
Predicted gate: the chibi limb and torso code on these anchors, so landmarks within 0.05 H but IoU about 0.80 to 0.88
and a width failure at the hip and thigh (no hip curve, straight legs): G0 FAIL, which is expected at this stage.

### 2026-10-17, why the lid looked too thick (owner's report)

Measured, not guessed: the lid polygon is 5 to 8 px thick at the middle, the reference's 10 to 12, so the lid was not too
thick. Three other things made it read so: (1) the shared brow bar sat on top of it (replaced by brows traced from the
reference, `brow_trace.py`; the left one runs on behind the falling strand, read from a contrast-stretched view); (2) the traced
face polygon had deep notches round both eyes (the eyes are dark, so not skin), and its full-weight outline ran along each lid,
doubling it (fixed: the face is filled across each row from the brow to below the eyes before tracing, `face_trace.py`); (3) the
pale strip of skin between the two falling strands at the left temple was not in the face trace, so the dome painted black over it
(traced as its own shape, `slivers.py`, drawn over the hair with the brow back on top). Lesson: when something looks too heavy,
measure each layer before blaming the one you drew last.

### 2026-10-17, review tools for head work (reuse them)

Two overlays the owner asked to keep using at every matching step: `aligned.py NAME x0 y0 x1 y1` also writes
`overlay-NAME.png`, a 50% blend of our render over the reference; `harness/franzi_hair/overlay_lines.py` draws our traced
outlines and lines in contrasting colours on the reference. Owner's read of the head (2026-10-17): most of the visible hair
mismatch is the eyes clashing with the reference's (ours are rounder and larger than its almonds) and the hairlines not lining
up; do the eyes next, then redo the hairline from the contrast-stretched view and recheck the hair.

### 2026-10-17, chest polish rounds with the owner (bust contour, armpit, tapered line, straps)

Sequence, so a fresh context knows why the chest looks as it does: the bust contour was traced over ref 04 with the owner
correcting it three times (`harness/franzi/bust_overlay.py`, `bust_fit.py`; the subtle crescent either side of the centre
line was found with an edge filter), the armpit line was made the arm outline's own weight carried up from the gap's tip along
the bust's outer side, the bust line became one filled tapered shape (`adultBustLine`, taper B, top at 0.5 of full weight: a
floor under which the shape breaks up when rasterised, found when the first version went to 6% and showed holes), the top's
hem was widened to the body's side, the straps stopped at the shoulder line (no extension round the neck, the top clipped to
the body outline), and the inner edges now bow toward the centre and meet it at the bottom of the V (no parallel slit).
The harness-only bare chest view (`bare_chest.ts`, variants closed, open, thin, taper-a to c) draws outlines only: no nipples
or other detail. Side-by-side comparisons use `aligned.py` (the body gate's mapping); earlier hand-placed crops were about 0.3
head heights out vertically.

Known gap, to keep in mind for later (owner, 2026-10-17): our detail level is far below the reference's (shading,
collarbone lines, the cleavage crescent, the gathered knot on the top). Expected for a flat style, and the source of some of
the perceived polish gap; not to be closed by adding more lines.

### 2026-10-17, stage 4 redo: the top traced from the reference

Owner at checkpoint 2: the lower piece works, the top does not look good, is far from the reference, does not connect to
the shoulders, and the cups read as odd shapes. Honest cause: the first top and its cup lines were drawn by me, not
traced, and every gate I had (body silhouette, agent reviews of coverage and drawing errors) was blind to the chest, so
I accepted it though the straps visibly stopped short. Owner's rulings in the same exchange: a bare view in the harness is
allowed for control of anatomical shapes (CLAUDE.md: never a web tool option or API control; no nipples or other sensitive
parts, not even in the harness), and the adult body's baseline may be lower than the chibi's, so the triangle halter top
of ref 04 is the always-worn top.

Done: the top is traced from the bikini-top layer (`segments/04-bikini-fullbody/white-bikini-top.png`) with
`harness/franzi/top_trace.py` (mask eroded 3 px for the stroke centre, straps grown 2 px, straps extended up and in to the
neck's edge where the layer stops short, made symmetric by joining the right half to its mirror, smoothed, fitted to 35
quadratics) into `body-adult-top-data.ts` in the body's own units, drawn through `place()`. New gate
`harness/franzi/gate_top.py`: IoU against the same layer through the body gate's mapping, threshold 0.90 fixed before the
run: 0.918. The cup lines of the first version are gone: the bust is read from the cloth's outline alone. A separate bare
chest view was not built: the garment's outline is the trace of the bust as the cloth shows it, and a skin-coloured copy
of it would show nothing more; to be built if the owner wants it.

### 2026-10-17, stage 5c: hands and feet, and the whole-figure review

Feet: a rounded sole (little-toe side highest, big toe lowest) replacing the flat block, with four toe ticks and a
small big-toenail chevron as interior lines. Hands: the silhouette is the reference's own (the arm knots run through
the hand), with two thin lines for the thumb hanging along the inside and where the curled fingers part. Both are in
`adultDetail` (the `_arms` slot). First tries to give the toes as five separate bumps looked like a saw, so toes are
lines inside one rounded sole.

G2 (sonnet, 75k tokens): neck PASS except a break: the chibi neck's side strokes stopped about 10 px short of the
shoulder outline. Fixed with an adult neck (`adultNeck`) that runs its side lines into the body outline; a faint seam
at the neck base was then fixed by extending the skin rect. Left as noted, not defects of the code: the hair is a flat
cap with no strand lines (the reference has a part and strand flow), a small jog on the left lock's outer edge near the
ear and a stepped ponytail root (both from the trace; a looser fit changed nothing), ears barely visible (the reference's
are mostly hidden too), hand lines float inside the lobe and stop short of the outline, feet slightly blocky.

### 2026-10-17, stage 5a and 5b: head, face and hair

Calibration (trace-reference step 2, `harness/franzi_hair/trace.py`): the body gate's chin-to-sole mapping puts the
reference at 175.7 px per head radius, origin x 660, origin y 270.5 (the drawn chin, 455 px, 1.05 radii below it).
Cross-checked: the reference's eye line comes out at +0.275 radii, ours +0.28. The README's chin estimate (hair top plus
352 px) was 21 px high; the true chin tip is at row 455, which makes the reference's head 370 px (2.1 radii), and the body
gate's 6.4 heads still holds within about 1% of scale.

Finding: the chibi head is a round skull 2.0 radii wide. The reference head is 1.7 radii wide and 2.1 tall, with a
pointed jaw, and its face (the skin) is only 1.15 radii wide at the eyes. No `FaceStyle` knob changes the skull, so the
adult body draws its own head (`adultHead`, `adultEars` in `body-adult-parts.ts`) from traces of the reference's face skin
joined with everything inside the hair, made symmetric from its right half, and of the right ear mirrored. Data:
`body-adult-head-data.ts`, generated by `harness/franzi_hair/` (`face_trace.py`, `trace.py`, `emit.py`; `show.py` draws a
trace over the reference). The eyes then had to come in: `eye_gap` 0.42 and `eye_size` 0.85 put the irises 0.746 radii
apart (reference 0.75, `harness/franzi/eyes.py`); the first guess (0.9, 0.92) put them 1.0 apart, outside the face.

Hair: `swept_ponytail`, one shape drawn over the head: a mass (the hair joined with the head, closed across the face
opening by the jaw) and a front piece (the hairline, then the mass's own segments over the top and down the ponytail), so
the silhouette is shared exactly and nothing doubles. It is a TypeScript-only cut in `EXTRA_HAIRSTYLES`
(`core-head.ts`), which `hairstyleFor` also reads; `HAIRSTYLES` and the catalogue are untouched. No strand lines or
tip colour yet. Judged by eye against the reference (`out/franzi/head-h4.png`): the same character in house style. Not yet
reviewed by an agent.

### 2026-10-17, stage 4: underwear and bust

The always-worn underwear is now a scoop-necked sports top with straps (from the base of the neck to under the bust,
following the torso in at the hem) with two thin curved lines under the cups, and high-cut briefs with a waistband
that dips a little at the centre. The bust is read from the garment alone: no skin detail, no nipple, nothing that is
not a flat garment edge, seam or outline. `ts/test/adult-body.test.ts` pins that the top and briefs are drawn for any
outfit setting, that the chibi's navel and bust lines are absent, that the anchors are in order at 6.4 heads, and that
the adult type stays out of `BODY_TYPES` and the presets.

DECISION AHEAD (stage 4 swimsuit/bikini and stage 6 garments): a selectable swimsuit, bikini, dirndl or blouse needs a
parameter on `Outfit` or `CharacterParams`. Both are field registries mirrored by the Python-oracle tests, so a new
field breaks them unless those tests are taught about TypeScript-only fields. Options: (a) a TypeScript-only extension
mechanism in the registries, with the mirrored tests exempting it, which needs the owner's say because it edits test
expectations; (b) keep adult garments as named outfits in a TypeScript-only table applied by the preset, with no new
field (the preset holds the whole look, the web tool offers it later); (c) reuse existing fields only. I lean to (b)
for Franzi's dirndl and to decide the web tool's controls at stage 7. Asked of the owner when stage 6 starts.

G2 round 1 (sonnet): coverage and anatomy PASS (nothing beyond a flat garment edge, seam or outline), symmetry PASS,
armpit tips PASS, edges against the outline PASS. Defects: the bust read weakly (two small U lines in a boxy top) and a
small crotch tick on the briefs. Reworked: each cup is now a longer curve from the neckline round the inside, under and
out to the armhole, and the briefs' bottom is one smooth curve through the crotch. Judged by eye afterwards (not
re-reviewed by an agent); the owner sees it at checkpoint 2.

### 2026-10-17, stage 4 start: the armpits

Owner's observation (checkpoint 1): the armpits look odd, visible as red patches in the overlay. Cause, measured:
the target's arm gap opens at 1.0 H below the chin, and my rounded cap (control point at 1.0) peaked at about 1.05 and
the stroke filled the gap's tip to about 1.08. Fix: the cap's control point at 0.88 so the tip peaks at about 0.99, and
the chest band's sides follow the torso in below the armpit, so its corners stay clear of the gap. Result in the
overlay: the left gap matches the target; what red remains on the right gap is the target's own asymmetry (its right
gap is 0.04 to 0.07 H wide at the top, the left 0.01 to 0.04, and the render is exactly symmetric by design).
Gate numbers unchanged (IoU 0.941). Not done: an armpit crease line above the gap tip; to be judged at the next
checkpoint, since the reference draws one.

Harness: `gate.py BODY --silhouette` renders the body outline in skin colour with no underwear at all (no detail of any
kind), for comparing the plain shape with the target; harness only, as the owner allowed.

### 2026-10-17, stage 3: torso and limbs (interim)

Deviation from the plan, stated plainly: no prediction was written before the first stage 3 run, and the whole outline
was built in one step instead of one anchor or curve at a time. Reason: the chibi torso code cannot be tuned toward
the target (it caps the hip at the leg width, so `hip_half_w` is ignored, the stage 2 finding), so patching it
anchor by anchor would not converge. The adult body therefore draws its own parts.

What was built: `ts/src/body-adult-parts.ts` draws one fused outline (neck, shoulders, arms, torso, legs, soles) plus
always-worn underwear (a chest band, briefs), replacing `_torso`, `_legs_and_boots`, `_arms`, `_underwear_top` and the
chibi bust lines for a body in `ADULT_BODY_TYPES` (`render.ts` picks the table; nothing existing changes). The shape
comes from knot tables in `ts/src/body-adult-data.ts`, generated by `harness/franzi/outline.py` from the fused target
(edges symmetrised, smoothed 1/4, 1/2, 1/4) and mapped onto the skeleton anchors, so a different waist, hip or leg
width in the profile moves the figure. The path sits half a stroke inside the measured ink edge, since the knots are
the outer edge of the ink.

Gate: IoU 0.940 (min 0.93), widest width error 3.2%, landmarks within 0.026 H: G0 PASS. Two changes to the gate itself
while getting there, neither a threshold: (1) alignment moved from a detected shoulder line to the chin row (known
exactly for both silhouettes), because the shoulder detector put the render's line 0.13 H higher than the target's;
(2) the waist and hip landmarks are the middle of the plateau within 1.5% of the extremum, because on a smooth outline
an argmin lands anywhere on a flat bottom. The first run before the stroke inset gave IoU 0.933 with widths 1 to 3%
too wide and the ankle 13% wide.

Caveat on what G0 proves: the knots were measured from the same target, so a pass shows the pipeline reproduces the
measurement (the stroke inset, the anchor mapping, the curve fit), not that the target is right. G0 guards against
drift from here on; whether the figure is good is the owner's eye at checkpoint 1.

G1 green after the change: typecheck, 816 TypeScript tests, three refresh checks, ruff, 1051 Python tests.

G2 (two sonnet reviews, read-only, about 70k tokens each). Round 1 found: a spike where the thigh gap ran up through the
briefs, boxer-like briefs, a hooked step at the armpit, a chest band narrower than the torso, a squarish shoulder.
Fixed: briefs are now a high-cut brief closed across the crotch, the armpit slit has a rounded top, the band is
wider, the early shoulder slope is lower. Round 2: all five FIXED or PARTLY (the upper arm is still a near-vertical
wall, a little boxy); no stroke gaps or fill leaks; outline exactly symmetric about the centre.
Left for later, all cosmetic or owned by stage 4 and 5: the band and briefs get redrawn at stage 4 (straight waistband,
band corners touching the slit cap, small ticks at the band's top corners); the thigh gap is an open sliver about
10 to 12 px wide where the references show the thighs almost touching, and the inner knee has a small wobble (both from
the measured inner edge of the legs); feet are placeholder blocks that sit a few px below the target's toes; hands
are placeholder lobes (5c); the head and hair are the old chibi code (5a, 5b).

### 2026-10-17, stage 2: result

Profile in `ts/src/body-adult.ts` (a TypeScript-only table that `skeletonFor` consults after `BODY_TYPES`; adding it to
`BODY_TYPES` broke 10 tests and the catalogue sync, which mirror the frozen Python, so it stays out). G1 green: 816
TypeScript tests, three refresh checks, nothing existing moved. Gate: IoU 0.741, a miss against the predicted 0.80 to
0.88, because the chibi torso code does not honor `hip_half_w`.

G2 (sonnet, read-only): anchors in order and consistent (H 71.8 px at canvas 400 x 500, shoulder 0.280 H, waist 1.300,
hip 2.200, knee 3.450 derived, ankle 4.700, sole 5.400); widths positive; scale 6.43 H on the reference against 6.4;
margin about 3% above and below. Defects, all for stage 3:
- the rendered hip is 0.99 H wide, not 1.23 (profile honored at the waist, neck, arm and wrist but not the hip);
- the leg split starts at 2.54 H below the chin, the target's at 2.3 H (crotch too low);
- the arms reach 1.13 H at the shoulder against about 1.28 (they only reach `arm_x` at the wrist);
- hands are small stubs and start about 0.3 H low (`wrist_y` 6.2 had no measured source; the reference hand starts at
  about 2.2 to 2.3 H);
- the knee is derived at 3.45 H (midpoint of hip and ankle) against about 3.6 measured, which is ambiguous in the
  measurements (width minimum at 3.6, outer minimum at 3.3);
- the hip number 1.23 is the mean of refs 1 and 3 only (ref 4 gives 1.16); the stage 0 note "widest at 2.2 H" is a lower
  bound, since row 2.3 is already below the crotch.
Leftover chibi-lerp anchors: `hem_y`, `boot_y`, `hem_half_w`, unused by underwear.

### 2026-10-17, stage 1: the gate

`harness/franzi/underwear.ts` renders a body type's underwear-only figure (no tunic, skirt or boots, short hair) with a
skeleton sidecar; `harness/franzi/gate.py BODY` rasterises it and compares the neck-down silhouette with
`out/franzi/target.png`, both measured by the same landmark rules (shoulder line, waist, hip, crotch) and brought to a
common scale (shoulder line to sole). Run `./harness/run.sh harness/franzi/gate.py tall_chibi` or `--self`.

Controls: the target against itself passes (IoU 1.000, all errors 0). The tall chibi fails loudly (IoU 0.489, worst
width error 110 to 155%, landmark errors 0.23 to 0.44 H), so the gate can tell a wrong body from a right one.

G1 baseline on `dev` at 3f26cf5 plus the harness files: typecheck clean, 816 TypeScript tests pass (8 skipped), the
three refresh checks match, ruff clean, 1051 Python tests pass. Nothing under `ts/src` has changed.

Known weakness: the shoulder-line detector is a width jump over the neck, so a render with a very wide neck or
sloping shoulders may place the line a few rows off. Stage 2 will show whether that matters.

### 2026-10-17, stage 0: measurements

Row widths in head heights (H) below the chin, read from the silhouettes by `harness/franzi/measure.py`:

- Waist (torso only, narrowest at 1.3 H): ref 1 0.69, ref 3 0.71, ref 4 0.68.
- Hips (widest at about 2.2 H): ref 1 1.23, ref 3 1.24, ref 4 1.16.
- Crotch 2.25 to 2.3 H. Knee about 3.6 H, calf about 3.8 H, ankle about 4.7 H, sole 5.4 H, so 6.4 heads in all.
- Ref 4 thighs are 17% narrower than ref 1 at the mid-thigh crop; the fused target widens them and eases back over one
  head height. A 3 px step remains on the outer thigh edge at the seam.
- Not measurable from silhouettes: the bust line (arms merge with the torso above the waist).
