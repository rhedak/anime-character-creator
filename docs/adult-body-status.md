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

### 2026-10-18, skin strips traced (`outline_masks.py` strips, `outline_trace.py`)

The strips beside the face were lumpy. Looked at them at 12x: the old rule took any warm piece beside the face, which gave 15 fragments (a
temple sliver in five parts, a cheek strip's top half missing, speckle). There are three real regions in the reference, each cut out in its
own box: the pale sliver at the left temple, the shaded two-lobed region at the left cheek, and the tan strip beside the right ear. Each
is skin-warm and not a line (red minus blue over 40, brightness over 100), the thin dark dividers inside them are closed over, and
anything under 60 px is dropped, so the mask is three regions. Fitted with `fit_smooth` (2 px smoothing, 3 px steps, within 1.3 px of the
edge).

Two things found in the render, not in the masks: the right strip is 7 px wide and the full-weight outline (about 2.5 px each side) filled
it with black, so strips are drawn at 0.4 of the outline weight, as the ears are, since the reference's lines there are thin; and the pale
highlight and dark line between a strip and the face belong to neither the hair nor the strip mask, so the silhouette had a hole and the
page showed through beside the right strip. The silhouette now covers each strip with a 6 px margin. The white gap between the left lock
and the jaw is not a defect: the reference shows page there too.

Not done: the upper part of the left temple sliver (y 237 to 277) is 2 to 4 px wide in the reference, less than one of our outlines, so it is
left out; the lower part (y 277 to 304) is in. The pale highlight beside the face edge at the right strip is not drawn.

### 2026-10-18, the ponytail corner beside the jaw

The slight angle beside the jaw on the ponytail side had three causes, found by overlaying the silhouette chain on the reference at 8x:

1. **The ponytail extension polygon** (added for "goes behind the shoulder") had its left edge straight down at x=700, but the reference's
   hair edge curves in from x 721 at row 462 to x 748 at the shoulder line (row 499). The vertical stuck out beside the jaw. The polygon now
   follows that curve and only drops vertically below the shoulder line, behind the body.
2. **A sliver of page** between the hair edge and our neck: the reference's neck skin runs right up to the hair, ours is narrower there. A
   skin region traced from the reference (`neckfill`, `ADULT_SKIN_NECKFILL`) is drawn behind the hair.
3. **Two black lines side by side**: the hair's outline and the body's own neck outline 8 px to its left, which the reference does not have
   (the hair sits directly on the neck). The hair is drawn again over the body for the rows above the shoulder only (reference rows 405 to 512,
   columns 690 to 746, `adultHairOnNeck`), with the neck fill under it covering the neck line. Below row 499 the shoulder still covers
   the hair, so the ponytail still goes behind it.

What is left: two ticks of about 2 px, visible at 6x only, where that redrawn region's edges cross the outline (under the jaw, and at the
shoulder). Clean at normal size.

### 2026-10-18, feet traced from the close-up (`harness/franzi_feet/`)

The owner's call: the feet (and hands) in the body are placeholders from the full-body reference, where a foot is about 100 px; the close-ups in
`ref/franzi/hands/` are the real references. This is the feet. Pipeline, in order: `locate.py`, `mapping.py`, `outline.py`, `lines.py` (all
`./harness/run.sh harness/franzi_feet/NAME.py`, from the repo root with `UV_CACHE_DIR` and `PYTHONPATH=.claude/skills/trace-reference` as for the
hair); `view.py` draws the traced foot on the close-up for checking.

- **Segments located** (`locate.py`): Grok's cut-outs (ten toes, three lower-leg layers, two feet) are small cropped PNGs, not full-canvas layers,
  so a masked template match finds each in the 1008 x 1792 close-up; all 15 match with RMS 0.00 (they are crops of the same pixels).
- **Mapping** (`mapping.py`): the close-up is 3.5x the body reference's feet and not registered; each foot is fitted to the body's matching foot by
  scale and offset (IoU 0.933 and 0.927, scale 0.288). The two close-up feet are mirror twins (IoU 0.991), so the traced foot is the mean of one
  and the mirror of the other, symmetric like the rest of the body, placed centred on the mean of where the body's feet stand.
- **Outline** (`outline.py` to `ts/src/body-adult-foot-data.ts`, `FOOT_OUTLINE`): in the body knots' own coordinates [v, d] (head heights), inset
  by the render's half stroke like the leg knots. The legs stop at `FOOT_D_CUT` (4.40 head heights below the chin) and the foot takes over,
  blended from the leg knots over 4.40 to 4.85 so there is no step. Narrow slits between toes (under 22 close-up px) are closed, since followed
  as outline they drew as teeth (the first version did); the open gap beside the big toe stays as a notch. The old placeholder sole is gone.
- **Dividers** (`lines.py`, `FOOT_DIVIDERS`, with `FOOT_DIVIDER_WIDTHS`): the shadow line between each pair of toes, from the midline of the gap
  between the two toe segments, snapped to the darkest pixel, thickness measured across it (thin at the base, heavy at the notch), drawn as tapered
  strokes. The pair beside the big toe (7/5) has an open slit, so it snaps only above the slit and runs on down the middle of it to the notch,
  drawn thin. (A first version judged "page" by brightness and read transparent pixels, which are black, as shadow; it is judged by alpha now.)
- **Nails** (`FOOT_NAILS`): rim found by casting rays from a centre read off the grid and taking the darkest point near the guessed ring; big toe's
  search is held near the ring (it leaked into the shadow wedge beside it and drew a point). Drawn as a thin ring with a lighter skin fill, clipped
  to the body outline with the outline's stroke redrawn over it below the ankle, because the stroke (about 10 close-up px a side) is wider than the
  gap between a little toe's nail and its edge.

**A bug of mine, found by the gate:** the body path decides which way to inset a knot table by `tab === LEG_INNER`; my cut copy of the table failed
that test, so the inner leg edge was inset the wrong way (leg 8 px wider at 60% of chin-to-sole, gate failing on width). The cut tables are
recognised by reference now.

**Gate** (body, IoU at least 0.93): 0.957, worst width error 4.3% (the toes' outer width at 90% of chin-to-sole; the close-up's forefoot is 5% narrower
than the body reference's rough feet, so the foot is stretched 6% horizontally about its centre line, `XS` in `outline.py`; without it 5.3% fails the 5%
limit). All other gates green. Left: the right foot is the left mirrored, so the two are exact twins (the close-up's are not quite); the nails of
the little toes are largely hidden by the outline at this size, as the stroke is thick against a 4 px toe; the tick-mark placeholder code is gone.

### 2026-10-18, bikini top step 3 of 3: soft breast contours (owner: the reference shows the breasts' shapes softly, trace the ones from the bare render)

The breast outlines from the bare render (`ADULT_BREAST`, drawn by `adultBustLine` as the tapered ring) were already under the top; they showed as a near full-weight black line (0.9 of the
outline weight, `OUTLINE`) in the V and above the cups. In the reference those shapes are soft tonal edges. `adultBustLine` now takes a colour and weight, and the figure draws it in a
darker, more saturated tone of the skin (`shade(skin, 0.78, 1.6)`, a second tone on a thin element, as for the ears' folds) at 0.8 of the outline weight, still clipped to the middle of
the chest (|x| < 0.33 H). The harness's bare chest view keeps the black default. A first try at 0.5 weight was too faint beside the reference's shading.

Left: the two inner edges still converge into one line down the middle of the V and a small triangle at its foot (the owner's earlier ruling was that they meet, no parallel slit, while
the reference has a pale strip about 0.055 H wide that stays open); the soft lines are lines where the reference has tonal shading; the stub of the armpit line next to each cup
ends in a short hook toward the cup (the reference has the line there too, thin).

### 2026-10-18, bikini top step 2 of 3: the V where the cups meet (owner's observation: the reference has a `\_/`, ours a badly curved line)

Measured in the reference's top layer (`white-bikini-top.png`): the V's edges are straight lines (half-gap 0.237 H at 0.585 H down, falling 0.68 H per H to 0.040 H at
0.875 H) ending in a short flat base about 0.07 H wide at 0.885 H down, with sharp corners. Ours matched the edges (to within 0.004 H) but the bottom was a smooth round curve: the
mask is blurred before tracing and the fit (tolerance 0.006) rounds a corner. `top_trace.py` now replaces the V's boundary points below 0.69 H with that geometry
(two straight edges and a flat base) and fits with tolerance 0.004, so the corners stay. The V is now `\_/`. Left for step 3: the bust ring's inner edges converge into one heavy
line down the middle of the V and a small triangle at its foot; the reference has a soft pale strip there, not a line.

### 2026-10-18, bikini top step 1 of 3: the double outlines at the outer edges (owner's observation)

Confirmed at 9x: each outer side of the top showed two thick lines side by side. Two separate causes, found by switching layers off. (1) The armpit crease
(`adultSkin`, full weight, down the arm's inner edge) ran 0.015 H outside the top's own edge from 0.7 H down; the two merged into one heavy band with a thin gap.
It now stops at the top's edge (a Y join at 0.65 H) since in the reference the armpit line is hidden behind the cup there. (2) With the crease gone a heavy
band remained: the bust's tapered ring (`adultBustLine`, meant for the V and the arcs above the cups) lies just beyond the top's outer edge. It is clipped to
|x| < 0.33 H of the centre line, so it only shows in the middle. Each side is one line now. Steps 2 (the V) and 3 (soft breast contours) follow.

### 2026-10-18, hands: the barb and the cut-off fingertip (owner's two circled flaws)

Both were found by switching layers off one at a time at 12x to 24x, and neither was what it first looked like.
1. **The barb at the fingertip.** Not the sharp-tip detector (turned off for the hand anyway), not the silhouette, not any of the hand's interior layers (it stayed with
   all of them off). It was the hand's stroke zone: a rectangle starting 0.635 H from the centre line, which the lowest fingertip (reaching 0.60 H) stuck out of, so the
   tip outside it was drawn at full weight with a vertical edge. The zone's inner edge now follows the thigh (a polygon, `V_IN` in `adultBodyStroke`), taking in the tip
   and staying clear of the thigh's own stroke. `adultBodyStroke` builds its clips from polygons in (depth, half-width) now, which also removed the rectangle seams.
2. **The cut-off fingertip beside the thumb.** The close-up's second curled finger pokes out past the thumb as a tail about 4 px wide on ref 04; the finger outline I
   drew across it and the thumb's own edge made it look like a separate piece of flesh. The silhouette is opened with a disc of radius 20 close-up px
   (`OPEN_R`), which removes that tail and nothing else (every other thin part is under 150 px at that radius), and the finger pieces are trimmed to it. The thumb is drawn
   over the finger outlines below its tip's row (`HAND_THUMB`, `HAND_THUMB_FROM`) so a finger outline no longer runs across it. The close-up's sliver of nail on that finger
   (24 px tall) is skipped: drawn with a stroke it was a black wedge.
Also: the outline is sampled more finely (717 segments, smoothing 4 samples) since a fingertip is a U-turn only a few vertices wide at the coarser setting. Gates green.
Left: a tiny nub (under 1 px) at that fingertip at 18x; two faint hairlines under the thumbnail at 18x.

### 2026-10-18, hands: outline at a third of the weight, tapered at the wrist (owner's option 1 for giving the fingers room)

The owner asked about a larger image; a larger canvas would not help (a vector scales the figure and the stroke together; the stroke is figure-relative), so the
first lever tried was a thinner hand outline. `HAND_K` 0.5 to 0.33 (`harness/franzi_hands/outline.py`, regenerated; `lines.py` reads it for the thumbnail shift).
The step from the full weight to the hand weight showed as a jump at the wrist's outer edge, so the stroke now tapers over twenty bands from the wrist down
(0.32 head heights, `adultBodyStroke`), each band reaching 0.6 up into the one above so no hairline of the page shows between them. At six bands each band's
stroke ended in a small barb on the outer edge (the 'tick' noted earlier, which was these, not a stray line); at twenty it is mostly gone. One small spike on the
thumb's outer edge is left, at about 8x. Gates green, body gate unchanged (IoU 0.944). Not tried yet: a larger hand relative to the body (option 2).

### 2026-10-18, hand outline thinner, smoother, with fingertips (owner's report: the thick outline covered part of the thumb, the fingers had no proper tips)

Cause, measured: a finger on the close-up is 8 to 10 px on ref 04, about as wide as the full-weight stroke (about 5 px), so the stroke covered the thumb's edge
and the fingertips could only be kept by closing the gaps between them into one lobe. Fix: the hands are stroked at half weight (`HAND_STROKE_K` 0.5).
The body stroke is now drawn by `adultBodyStroke` in clipped pieces: full weight everywhere except the hand columns below the wrist, a step to 0.875 of
the full weight over the blend rows (`HAND_D_CUT` to `HAND_D_BLEND`), then the hand weight; the redraw over the hand's fills uses the same function. The hand
chain is inset by the hand weight's half stroke (`HS_HAND`), the gaps between the tips are closed only if narrower than 3.5 px on ref 04 (radius 14 close-up px,
was 60), so the three curled fingers keep separate tips, and the outline is fitted as a smoothed quadratic B-spline (the foot and hair method, 375 short
segments, slope continuous at every join) with a doubled vertex on any sharp convex tip. The thumbnail shift was halved to match. With no closed gaps left
`HAND_GAPS` is empty (the generator now writes an empty list correctly; the first run produced a file that failed the typecheck, which the other gates did not catch).

Left: the body gate's IoU is 0.944 (unchanged); the long lit finger's tip and the two curled ones now read as three tips at 4x; one tick of black about 2 px at
8x on the inner edge near the wrist, not located. Next, as the owner suggested: a larger default hand.

### 2026-10-18, hand fingers separated (owner's report: the fingers were one blob of flesh, like the big toe and its neighbour but worse)

Agreed and measured: the three curled fingers were one flat shaded region (`HAND_SHADE`), the traced lines only ran along its outside, and the gaps
between the fingertips had been closed to keep the outline from drawing heavy lobes, which also removed the separations. Two additions in `lines.py`:
the gaps the outline closed (`outline.py` now saves them as `gaps.npy`) are drawn as dark slits (`HAND_GAPS`, eroded 8 px so they are slits as in the
reference and not the whole closed gap), and the three shaded finger pieces from Grok's cut-outs are each drawn as a closed shape with a thin outline
(`HAND_FINGERS`, 0.4 of the outline weight). The long lit finger's piece is left out: it has a ragged top edge where Grok cut it from the back of the
hand and drew a wiggly line across the hand; its separation from the shaded fingers is the traced `edge` line already. Gates green, body gate unchanged.
Still small: at normal size the fingers are about 3 px each, so they read as three narrow bands, not as full fingers.

### 2026-10-18, the relaxed hand traced from the close-up (`harness/franzi_hands/`)

The owner chose to start with the relaxed hand and to have every hand style as an option eventually (open palm, fist, pointing later). The relaxed
close-up is the same pose as the full-body reference's hanging hand, so it goes on as the hanging hand. Pipeline, in order, all
`./harness/run.sh harness/franzi_hands/NAME.py` as for the feet: `locate.py`, `mapping.py`, `outline.py`, `trace_lines.py view` (to place the
lines), `lines.py`; `view.py` draws the traced outline on the close-up. `composite.py` is the earlier comparison of the four close-ups on the reference.

- **Which hand:** the close-up has its thumb on the left of the image; the viewer's-left hand has the thumb on the inner side, so it is used
  flipped there and as it is on the other (the owner caught the first composite having them the wrong way round). The traced hand is the
  viewer's left (the person's right); the other is its mirror, as the body is.
- **Segments located** (`locate.py`): the hand, the thumb, five finger pieces and four nails, all exact (RMS 0.00).
- **Mapping** (`mapping.py`): IoU 0.836 against the reference's hand (scale 0.1265, wrist 7 rows low). Lower than the feet's 0.93: the reference's
  curled fingers sweep inward and the close-up's hang almost straight down, so the traced hand is the close-up's, not the reference's.
- **Outline** (`outline.py`, `ts/src/body-adult-hand-data.ts`, `HAND_OUTLINE`): the close-up's alpha with its holes filled, inset by the render's
  half stroke, in the body's knot coordinates, taking over from the arm's knots at `HAND_D_CUT` (2.00; the close-up starts at 1.99) with a blend to 2.16.
  The first blend to 2.30 dragged the outer edge outside the skin, because the arm's knots widen into the reference's outer corner there (found with
  `view.py`). The fingertips are 8 to 10 px wide on ref 04, narrower than a stroke, so the gaps between them are closed (radius 60 close-up px) and
  the tips are one lobe; the shaded fingers show the rest. Smaller radii (20, 34) left a zigzag of heavy lobes.
- **Interior** (`lines.py`, `body-adult-hand-lines-data.ts`): the curled fingers in shadow as a second tone (`shade(skin, 0.83, 1.6)`, lightness 140 to 196
  against lit skin's 205 to 220, below row 780); the dark wedge between the thumb and the fingers, which is transparent in the close-up, so a hole in
  the silhouette, drawn as a dark shape; the nails from Grok's cut-outs (the thumbnail shifted and shrunk so the inset outline does not cover it); and
  three contour lines placed by points read off a grid and snapped to the dark ridge (99, 97 and 93% on a ridge, control 2%), tapered by measured
  thickness. An automatic line finder caught only fragments and was dropped. The shade and the cavity are clipped to the body outline and the outline's
  stroke is drawn again over them in each hand's columns and rows (their edge is the skin's edge, so they covered half of the stroke), as for the toenails.
- **Gate** (body, IoU at least 0.93): 0.944 (was 0.957 with the feet, before the hands), worst widths 4.3% and 3.2%. All other gates green.

Not done / honest limits: the hand's fingers are far narrower than the stroke, so at this size the three curled fingers read as one shaded lobe with two
thin lines, not three fingers (the toes had the same limit); the nails of the little curled fingers are not drawn (they sit in the closed tips); the
thumb's crease lines and the knuckle wrinkles are left out (under a pixel wide); the thumb is narrower than the full-body reference's. For the
other hand styles later: the same pipeline per close-up, with the data in one file per style and a style name selecting it (the data constants are
`HAND_*` now, named for the one style, and would become a table keyed by style).

### 2026-10-18, feet: the big-toe divider reaches the notch (owner's report: skin joined the big toe to its neighbour)

The divider between the big toe and the next one stopped short of the notch where the outline's two toe lobes meet (its end was set 3 rows past
the narrowest gap between the toe masks, 1432, where the notch is at about 1450), so the stub ended in skin. It now runs 16 rows past, to 1445,
where it meets the outline. Two things measured on the way: the slit between those toes is only 17 close-up px of page at its top (y 1370) and 5
by y 1430, about 5 and 1.5 px on ref 04, narrower than the stroke is wide, so it cannot be drawn as an opening and the divider carries it; and
the shadow lines of the other dividers do start about where ours do (tracked upward on the close-up: the big-toe line is dark above 1340 only to
about 1320), so "all the way" meant to the notch, not up. `CLOSE_R` went from 11 to 5, which changes no pixel that shows (the slit is under 10 px
in the averaged mask) and keeps the setting honest.

### 2026-10-18, the four leftovers (wisp tip, arc fold weight, pale highlight, faint strands)

1. **Ponytail wisp tip, done.** The wisp is a 4 px wide tail running to about y 486; ours ended near y 471 for two reasons. The 1 px shrink
   that puts the stroke's outer edge on the hair edge eats half of a 4 px part, so parts narrower than a disc of radius 2 are now kept
   un-shrunk. And a smoothed edge plus a B-spline through side midpoints blunts any point (it cuts a corner by up to half a vertex spacing),
   so `fit_smooth` now finds the real convex tips (turn over 105 degrees within 7 px each side, convex only: the first version counted
   notches too, and flagged the notch where the lock meets the ear) and puts a doubled vertex on each, which makes the spline reach it.
   Tips kept: the wisp, the left lock's tip, the two ends of the small neck piece. The wisp now ends near y 483.
2. **Arc fold weight, done.** The reference's thickness along each fold was measured across the snapped line (coverage from skin brightness
   150 toward line darkness 40), clamped to 0.7 to 3.4 px so hair beside a line's end does not inflate it, and stored with the line
   (`ADULT_EAR_FOLD_WIDTHS_*`, head radii, nine points); `taperedStrand` takes an optional width list. The arc is now thin at the top and
   heavy at the lower end, the upper fold heavier at the lock end.
3. **Pale highlight beside the right strip, not drawn.** Measured: the cream wedge is 13 px of data (about 3 by 6 px) in the reference, smaller
   than one of our outlines, so any shape drawn for it would be a guess rather than a trace. A first attempt with a brightness test found 12
   px and one with a saturation test 13, and was removed.
4. **Faint strands, one added.** The residual map (dark ridges no strand covers) was checked tile by tile with all strands drawn: ponytail,
   left skull, right crown. What is left is the edges of the white highlight streaks (they dip dark beside a bright area) and the face
   boundary, not dark lines; the one real gap was a thin line down the ponytail's left side (`pony-6`, 96% on a ridge, control 16%). 28 strands now.

Still visible only at 6x: two ticks of about 2 px at the redrawn hair-over-neck region (see the corner entry).

### 2026-10-18, the hair-strap-shoulder junction on the viewer's right (owner's report: an edge and a gap)

The owner pointed at the spot where the ponytail meets the strap and shoulder: it looked like an edge with a gap. At 14x there were two causes, both mine from the earlier work on the corner:

1. **A squared corner left of the strap.** The ponytail extension polygon closed with a diagonal running down past the strap, so the hair ended in a flat-bottomed corner below the hair edge. In the reference the hair edge runs to a point at the strap top, about (741, 495). The polygon now follows the hair edge to that point, then along the hair's bottom edge to the right, and drops straight down at x 750 behind the body.
2. **A thin black spike pointing left at the strap top.** Bisected by switching the over-neck redraw off: the body's own neck outline sweeps down and into the shoulder line at rows 504 to 507, just below the bottom of the neck fill (row 504), and the exposed tail showed as a spike. The neck fill now reaches row 513 (left of the strap only, x under 744), so it covers that stretch. (The tip detector was tried first as the cause and ruled out: the spike was unchanged with it excluded, the exclusion is kept anyway since that corner is not a lock of hair.)

At normal size both shoulders now read alike. What is left is one pixel of light colour at the strap's top-left corner, visible only at 14x.

### 2026-10-18, the right neck-to-shoulder curve mirrors the left (owner's request)

The body outline is already left/right symmetric (the knot tables are the mean of both sides); what differed was the layering on the right. The
earlier corner fix drew the hair again over the body beside the neck, with a skin fill under it, which hid the body's own neck line and its
curve into the shoulder, so the hair edge stood in for the neck and the shoulder line came out from under the hair at the strap. Mirroring
the left means the opposite: the body's neck line and curve are on top, as on the left, and the hair goes behind them.

Done by dropping `adultHairOnNeck` and the neck fill (`ADULT_SKIN_NECKFILL`, `neckfill` in the harness) and adding hair under the neck to the
mask (a polygon from the neck line, x 716, out to the hair's real edge, rows 425 to 514, in `outline_masks.py`), so the body curve, drawn
over the hair, is the boundary between neck skin and hair. This puts the hair edge a few px nearer the neck than the reference has it (the
reference's hair edge is itself the neck's boundary), which is the trade the owner accepted. The strap-top junction fix from the previous
entry (hair edge to the strap point, no squared corner) stays. Both neck lines now end in the same small joint where the rect's bottom meets
the body curve, 2 px at 8x on both sides.

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
