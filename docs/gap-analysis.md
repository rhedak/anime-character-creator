# Gap analysis: current renders against the canon

A snapshot comparison of the four checked-in renders against the four
reference drawings, taken 2026-08-06 at `c4dc619`. The target style is
`ref/satoko-chibi.jpg` and `ref/satoko-real.jpg`, applied to both
characters, so where the two references disagree Satoko's win (see
"Where the references disagree" below).

The references are guides, not targets. What follows is measurement used
to find what is wrong, not a list of numbers to converge on; the final
call on any of it is by eye.

## Method and units

Each reference was paired with its render, both cropped to the painted
figure and scaled to the same height, then measured and looked at. The
`gap-analysis` skill in `.claude/skills/gap-analysis/` carries the
procedure and the tooling, so a re-run after a shape pass reproduces
these numbers the same way rather than measuring afresh. Strips
regenerate into `out/gap-analysis/`, while each task that acted on a gap
keeps its own `out/NN/` beside it:

| File | What it shows |
| --- | --- |
| `cmp_all.png`, `cmp_satoko.png`, `cmp_satoshi.png` | full figures, ref beside ours, with guide lines every 0.1 H |
| `heads_satoko.png`, `heads_satoshi.png` | the top 42% at 2x |
| `torso_chibi.png`, `torso_real.png` | the garment construction |
| `legs.png` | hem, legs and boots |

**H** is the figure height, ink top to sole. Every position and width
below is a fraction of it, because that is the one normaliser that
measures reliably on a JPEG reference and on our PNG alike. Our own
figures are computed from `build_skeleton` and the hair point data rather
than measured, so those numbers carry no measurement error. Reference
numbers are only quoted where they reproduced independently (identical on
the left and right of a symmetric figure, and physically sensible);
everything else is stated as what the strips show.

## What already matches, and should not be disturbed

- **The vertical landmark stack.** Chin, shoulder, garment hems and ankle
  all land within a few percent at both builds. Satoko's chin sits at
  about 0.46 H in the canon chibi against our 0.445, and at about 0.18 in
  the canon adult against our 0.184. The chibi figure was read off
  `out/gap-analysis/chin_probe.png` rather than inferred from a colour
  scan, which is worth doing for any landmark in this zone: the mouth
  line at 0.38 H and the jaw stroke spanning 0.45 to 0.47 are easy to
  mistake for each other in a column of colour runs. The tunic's lower
  edge is at 0.99 H in both. Nothing about the skeleton's proportions
  along the body needs moving.
- **Hair length.** Satoko's chibi hair ends at about 0.58 H in the canon
  and 0.571 in ours. The long cut is the right length; what is wrong with
  it is its width and its edge (gap 2).
- **The fade height**, from task 55. The gold-to-pale boundary sits at
  0.176 H in the canon adult and 0.171 in ours.
- **The palette.** Sampled as the modal exact colour inside a flat patch
  of each surface, not from a quantised histogram, since a bucket centre
  is only good to eight points a channel and that is the size of the
  whole question here:

  | Surface | Canon | Ours | Delta per channel |
  | --- | --- | --- | --- |
  | tunic, chibi | `#4c6547` | `#4a6845` | +2, -3, +2 |
  | tunic, adult | `#4d6649` | `#4a6845` | +3, -2, +4 |
  | skin, chibi | `#f3d9c2` | `#f6dbc2` | -3, -2, 0 |
  | apron leather | `#6c594b` | `#6f5c4e` | -3, -3, -3 |
  | hair gold | `#e3b448` | `#e6b53c` | -3, -1, +12 |

  Every surface but one is inside four points a channel, which is not
  visible. The exception is the gold: the canon's is a touch less
  saturated, and ours reads marginally more orange. **Taken in task 70**:
  `HAIR` is now the canon's `#e3b448`. It carries to the brows, which
  derive from it through `shade()`, which is the point of deriving them.
- **The garment inventory.** Every layer the canon wears exists as a
  part. What is missing is construction detail inside those layers
  (gap 8), not garments.
- **Total line quantity.** Outline covers 20.5% of the canon chibi figure
  and 22.4% of ours. The amount of line is right; its colour and its
  hierarchy are not (gap 5).

## Where the references disagree

The two chibi references are not the same chibi. Measured at hip level
(0.50 H), the canon Satoko chibi's silhouette is 0.560 H across and the
canon Satoshi chibi's is 0.252 H: his reference is drawn with a
distinctly smaller body under a similar head. Our two chibis are much
closer to each other, which is what a shared skeleton produces and what
the Satoko-anchored style asks for. **So the large width deltas against
the Satoshi chibi reference, up to +70% through his torso, are not gaps.**
Reading them as gaps would mean giving him a separate set of proportions,
which is exactly the thing `CLAUDE.md` forbids.

The same holds for colour: the Satoshi references use tanner skin
(`#d8b8a8`) and a browner gold (`#c8a858`) than the Satoko ones.
`presets.py` deliberately unifies the palette so the two read as related.
That decision stands; the Satoshi references are still the only source
for his hair shape and his trousers, and should be used there only.

## The gaps, in priority order

Priority is by how much of the "not the canon style" impression each one
carries, which is not the same as how hard it is to fix. Gaps 1, 2, 3
and 4 are most of it.

### 1. Satoshi's crown is a dome with radial strand lines

The canon draws a tousled crop: a cowlick peak just off centre, spikes
flicking out at the temples, a fringe of separate pointed locks, and
sideburn locks running past the ear to jaw level. Every lock is gold at
the root and pale at the tip, so the two tones follow the direction each
lock lies in.

Ours is a plain part-circle with a scalloped fringe row and a ring of
pale teeth around its lower edge, and its strand lines all radiate from a
single point at the crown. At 2x
(`out/gap-analysis/heads_satoshi.png`) it reads as an umbrella, and the
radial lines are what make it read that way.

Measured: the canon crop is widest at 0.422 H at y 0.171, at the temples,
and narrows below that, ending at 0.756 H with the sideburn locks. Ours
is widest at 0.505 H at y 0.301, which is the bottom of the mass, because
the mass is a circle, and it ends at 0.434 H. So the silhouette's widest
point is in the wrong place, not merely the wrong size.

The crown tousle was tried and reverted on the owner's call, and is
parked with "potentially we will revisit this later" and a bar of beating
the plain circle by eye. Nothing here re-opens it; it is listed first
because it is the largest visual gap, and the rest of this entry is what
re-opening it would have to deal with.

The obstacle is structural rather than a matter of coordinates. The hair
contract gives a cut one `tip_edge`, a single region clipped across the
whole mass, which can express a band at a height but cannot express
"pale from here to the tip of each lock". A tousled cut needs the tone
boundary to follow the locks. That is a change to the contract in
`docs/architecture.md`, most likely a per-lock tip region rather than one
band, and it would want `_short_mass_shape`, `_short_tip_edge` and
`_short_strands` reworked together.

Cheaper partial move, if the contract change is not wanted: drop or
shorten the radial strand lines in `_short_strands`. They are carrying a
large part of the umbrella impression on their own, and removing a
feature is a legitimate column in a side-by-side.

**That partial move was taken in task 58**, and it worked: the spokes are
gone and the crop no longer reads as an umbrella. What is left is the dome
itself, which is this gap with nothing else on top of it, so the
side-by-side in `out/58/final.png` is the cleanest look anyone has had
at what re-opening the tousle would actually be worth.

**Re-opened by the owner on 2026-08-07**, and widened: the hair is to be
rebuilt rather than adjusted, Satoko keeping her style and Satoshi taking
his own cut from his reference. That makes this gap and gap 2 one piece
of work, because they share the root cause described above. The contract
change is task 71, Satoko's cut task 72, Satoshi's task 73. Two things the
rebuild must not quietly change: the pale fraction, which is half and half
on the owner's call against a canon of about a tenth down Satoko and a
third down Satoshi, and the flat-colour rule, which is about garment
panels. Hair has always carried two tones, so per-lock tone is not a task
56 violation.

**Traced on 2026-08-07, and the trace found a blocker nobody had named.**
The canon's crop was pulled off both references as a radius-per-bearing
profile in head-radius units and simplified to a **26-segment** quadratic
chain (`out/trace/`, `v3_*.png` are the fits at several levels). It
matches the adult closely. It does not port, and the reason is not the one
that was expected:

| | crown reach | widest | notches |
| --- | --- | --- | --- |
| `ref/satoshi-real.jpg` | 1.30 r | 1.17 r at y −0.47 | 0.94 to 0.99 r |
| `ref/satoshi-chibi.jpg` | 1.68 r | 1.52 r | 1.05 to 1.15 r |
| ours, both builds | 1.28 r | about 1.15 r | on the skull |

**The canon draws a chibi's hair about 29% bigger against its head than
an adult's**, in both reach and width, and our architecture has one
outline per hairstyle in head-radius units, so it cannot say that. Our
cuts sit on the adult's figure at both builds, which means every chibi we
ship is wearing an adult's volume of hair. That is a plausible second
cause of the helmet reading, alongside the tone band, and it was invisible
until both references were measured in the same units.

Consequences if the adult trace is ported as it stands: at the realistic
build it clears our skull by +0.080 r and the ear sits 0.030 r inside it,
which is a fit. At the chibi it sinks 0.044 r *inside* our skull at the
cheek and the ear pokes 0.094 r out past it. Raising the chibi to the
canon's own volume would also need `hair_margin` roughly doubled, from
0.36 to about 0.72, since 1.68 r plus the stroke is well over the current
−1.36 ceiling.

Read as clearance over the skull rather than as radius, the gap is wider
than 29%: the adult's hair stands 0.29 head radii clear of its skull and
the chibi's 0.73, a factor of 2.5. Ours is 0.28 to 0.30 at both builds.

Both calibrations are eye centre to drawn chin, 0.89 r at the adult and
0.84 at the chibi where `chin_drop` is zero. Cross-checks: the adult's
figure height over six heads implies a radius within 4.8% of the fit, and
the chibi's eye half-separation comes to 0.465 r against our house 0.46.
`out/trace/chibi_check.png` shows the r = 1.0 circle landing on the
canon's drawn chibi face, which is the check that matters, since the
whole comparison rests on the two head radii being right.

One cross-check disagreed and is worth having explained rather than
waved away, because it was 22.8% and the conclusion rests on the radius.
Dividing the chibi reference's figure height by 2.4 heads gives a radius
far off the fit. **The references are not drawn at our named builds.**
Measured skull-top to feet in each reference's own head heights,
`satoshi-real.jpg` is 5.44 heads against our `realistic` 6.0 and
`satoshi-chibi.jpg` is 2.74 against our `chibi` 2.4. Once the real head
count is used the figure-height check reconstructs the fitted radius, so
it confirms rather than contradicts. It also cuts the other way on the
finding: the canon's chibi is *less* deformed than ours and still carries
2.5 times the hair clearance, so the volume is not a side effect of a
squatter figure.

**The fringe is traced, off `ref/satoshi-chibi-fringe.png`.** Five
readings off the full drawing failed first and all five are written up in
`out/trace/fringe.py` and `fringe2.py`, because each failed differently
and each was caught by eye against the reference's own outline rather
than by any number: first skin going down runs on to the pupil between
two locks; deepest hair above a solid run of skin loses a lock that sits
below a gap; deepest hair outright settles on the brow line, finding
bright desaturated skin beside the hairline; deepest ink finds the brow
itself; and growing the forehead as a connected region cannot enter a gap
where two blades seal it with ink.

The reason none of them work is a property of the reference and worth
stating once: **the canon's pale tips sit colorimetrically between its
gold and its skin.** The forehead is sum 589-601 at red minus blue +45 to
+57, skin beside a drawn line rings to 520-622 at +8 to +56, and the
gold-to-pale band runs about +40 at 650. There is no threshold with all
three on the right side.

The owner's crop settles it by leaving the brows and eyes out of frame,
so the deepest ink in a column can only be the blade that made it. It is
placed back in the reference by template match, mean squared error 1, so
the calibration is the reference's own. Sixteen segments and five lock
tips, and it draws at both builds.

**Retracted:** an earlier entry here said the fringe was a deep zigzag of
needle-tipped locks, 17 of 22 sides ending in solid ink with the worst
0.45 head radii, and that drawing it needed overlapping locks the
contract has no slot for. That came from the second failed reading. The
overlapping-lock idea may still be right for other reasons; that
measurement does not support it.

**Residual:** the trace is off the chibi reference and our fringe is fixed
rather than scaled by build, so it sits higher over the adult's eyes than
the canon puts it.

**Correction to a number recorded earlier:** the crop's widest point was
written up as 54% down the hair's own height. Measured off the contour it
has *two* lobes, 1.17 r at 38% down (the temple tuft) and 1.11 r at 65%
(the lock over the ear), with a waist between them. One figure splitting
the difference was hiding the shape.

### 2. Satoko's falls pinch at the jaw and hook inward

**Closed by task 59 on 2026-08-06**, with the fall's outer edge standing
0.10 head radii further off the skull at the temple and the cheek
(`_FALL_TEMPLE_X` 1.12 to 1.22, `_FALL_CHEEK_X` 1.16 to 1.26,
`_FALL_MID_X` 1.30 to 1.36). The bell survives: it was chosen in an
earlier side-by-side over a straight fall and a half-bell, and the canon
does widen below the face too, from 0.054 H beside the cheek to 0.075 at
the neck. Ours was 0.030 rising to 0.091, so the error was a pinch beside
the face rather than the flare below it.

Two things this turned up that are worth having written down:

- **The fall's outer edge was defined in four places** and nothing tied
  them together: the mass, `_fall_edge`, the hairline's closing path, and
  the two strand lines down each fall. Widening the first two produced
  exactly the double line the hair contract warns about, because the
  hairline still met the old cheek and the strands still lay at their old
  radii, so a sliver of mass showed outside the lock with a stroke down
  each side. The first three now read shared `_FALL_*` constants; the
  strands carry a matching offset with a comment saying so. That
  extraction was verified behaviour-neutral before anything moved.
- **Per-run width is the wrong measurement here.** A strand line inside
  the fall splits it, so "one run" is a lock, not the fall, and the canon
  splits in some rows and not others. The candidates were finally chosen
  by eye against the reference (`out/59/try3_look_chibi.png`,
  `try3_look_real.png`), which is what this repo says to do anyway.

**Residual, not closed:** even with the wider fall, our face occupies more
of the head's width than the canon's does, so the hair frames it less. That
is a head-width question rather than a hair question, it shows at both
builds, and it overlaps gap 7. Widening the fall further to compensate
starts to read bulky, which is where 0.16 head radii went.

**Second residual, measured in task 62 and not addressed:** the fall's
width does not ride the build correctly, and the error changes sign
between the two ends. At the realistic build our hair envelope is 20% to
24% *wider* than the canon through 0.11 to 0.20 of figure height (the
canon's falls sit about 1.05 head radii off centre, ours about 1.33); at
the chibi build the same profile runs 10% to 13% *narrower*. The `_FALL_*`
constants above were chosen at one end, so a re-author has to re-measure
both rather than carry them over, and the fix is likely a build-dependent
width rather than one constant. The other numbers from tasks 57, 58 and 59
(hairline forehead-run height, fade height, length) still stand.

The original finding follows.

The canon's long hair is one curtain: two slabs of near-constant width
hanging straight down past the shoulders, tips flicking slightly outward,
the whole thing sitting behind the arms and forming the widest part of
the figure.

Ours reads as two ribbons pinned behind the ears, with a waist at jaw
level and a bulge lower down, hooking inward at the tips.

Measured, the width of one fall:

| y / H | canon | ours |
| --- | --- | --- |
| 0.28 | 0.057 | 0.049 |
| 0.32 | 0.054 | 0.030 |
| 0.36 | 0.056 | 0.029 |
| 0.45 | 0.043 | 0.091 |

The canon holds one width for the whole drop. Ours halves at 0.32 and
then more than triples by 0.45, which is the hourglass the strips show.
Consistent with that, our whole silhouette is 9% to 14% narrower than the
canon's through the head and hair zone (0.11 H to 0.40 H).

Fix in the fall rows of `_hair_mass_shape` and in `_fall_edge`, which has
to keep retracing the mass exactly.

### 3. The fringe sits too high, so the forehead is bare

**Closed by task 57 on 2026-08-06, with two corrections to the finding
below.**

First, it is not true that the fringe should come down to the brow. That
was tried in an earlier pass and reverted on purpose, and
`_hairline_shape` records why: the high part with two sweeps and a visible
wedge of forehead is the canon's construction, and the cure for a
bare-headed look is the sweeps, not blanket coverage. What was actually
wrong was the amount. Down the centre line the canon's fringe reaches
0.147 H and ours reached 0.109, so the apex sat about 0.19 head radii too
high. The forehead run is now that much lower, blended to nothing at the
temples so the side locks do not move, which leaves the part and the wedge
intact: measured after, our centre line lands at 0.146 against the
canon's 0.147. Candidates at 0.10, 0.19 and 0.28 head radii were rendered
side by side (`out/57/lab_chibi.png`, `lab_real.png`); 0.28 closes the
part and crowds the brows, which is where the reverted pass went wrong.

Second, this was a long-cut change only. The claim below that it affects
both characters was wrong: Satoshi's fringe already lands where the
canon's does, at 0.185 H against 0.178 down the centre line and 0.171
against 0.174 over the eye, so `_short_hairline_shape` was not touched.

**Its other half, the strand lines, closed by task 58.** Both cuts drew
their crown lines from the crown itself, so four lines on the long cut and
six on the short one left the same patch a fifth of a head radius across:
spokes off a hub, and on the short cut's part-circle mass that is a beach
umbrella. Each line now starts part way along its own path, trimmed to its
outer half, so they sit spread across the crown and read as the seams
between locks. Trimming further, or dropping the short cut to four lines,
empties the crown and it goes back to one smooth field
(`out/58/lab_satoshi.png`, `lab_satoko.png`).

The original finding follows.

In every canon drawing the fringe comes down to just above the brow, and
the brows sit partly under hair. It is built as two large swept locks
meeting at an off-centre parting, their edges long smooth curves ending
in points near the temples.

Ours forms an M with a sharp central peak far above the brows, leaving a
tall bare forehead with the brows drawn on open skin. Our strand lines
are long and nearly straight and cross the parting instead of following
the sweep.

This affects both characters at both builds and is the second thing the
eye catches after the hair silhouette. Fix in `_hairline_shape` and
`_short_hairline_shape` (lower the lock tips toward the brow line, which
`_face` puts at `eye_y - eye_r * 1.30`), and shorten the strand chains in
`_long_strands` and `_short_strands`.

### 4. Interior shadow *shapes* read as geometric wedges

**Closed by task 56 on 2026-08-06.** The owner's call was to drop the
garment tones entirely, which is what the canon shows, and `CLAUDE.md`'s
flat-colour rule was reworded to match: a second tone is for small
elements, not for a garment panel. Removed from `_tunic`, `_apron`,
`_arms` and the trouser branch of `_legs_and_boots`; the skirt's two
folds became thin lines rather than wedges. Kept where the canon does use
a second tone: the pouch flaps, the boot cuff and laces, the belt's lower
edge, and the underskirt's hem cap. Shadow-tone area went from 5.9% to
0.9% of the chibi's ink and from 15.3% to 3.1% of the adult's, with
Satoshi at 0.0% at both builds since everything he wears was a panel.

Narrowing the wedges to edge turns was tried first and rejected by eye,
recorded here because the reasoning generalises: it fixed the torso, but a
stripe down something as long and thin as a sleeve or a trouser leg reads
as two-tone whatever its width. Strips are in `out/56/`.

The original finding follows.

The canon does use a second tone, but only on small elements: pouch
flaps, boot cuffs, the sleeve roll. What it never does is put a large
shading plane across a garment. On the tunic, the skirt and the apron
there is no second tone at all, and the form is carried by line work.

Ours paints five shadow shapes per figure, together about 2.7% of the
figure's ink area (Satoko chibi: tunic `#405c3c` 0.72%, undersleeve
`#897e69` 0.81%, skirt `#4b5b43` 0.38%, apron `#635245` 0.35%,
underskirt `#484744` 0.42%). The tunic one is a diagonal running from the
shoulder down across the chest to the hip, and it is the single most
artificial-looking mark on the figure.

So the finding is about the shapes, not about having a shadow tone.
There are two ways to act on it and the second is the owner's call, not
a mechanical fix:

- **Reshape.** Cut the wedges back to narrow turns along an edge, the way
  `_arms` already justifies its own ("wide enough and it stops reading as
  a rounded limb and starts reading as a two-tone plank"). Same reasoning,
  applied to the torso and the skirt. This stays inside the flat plus one
  shadow tone rule.
- **Remove the garment tones entirely**, which is what the canon shows.
  That is a change to a rule `CLAUDE.md` states as a hard constraint,
  "flat color + one shadow tone per surface, hard-edged", so it needs
  confirming rather than assuming. Worth previewing first: `shaded=False`
  already renders a figure with every shadow dropped.

One thing to notice while doing either: the shadows are painted as
`shade(colour)` at `opacity` 0.45 to 0.8, so the tone that lands is a
composite of the shadow and whatever is under it. `CLAUDE.md` asks for
one shadow tone per surface and `docs/architecture.md` says `shade()` is
the one place a shadow tone is decided; in practice the tone depends on
the stacking, and a shadow crossing two surfaces comes out two colours.
The shapes live in `_tunic`, `_skirt`, `_apron`, `_underskirt` and
`_arms`.

### 5. Line colour and hierarchy

**Closed by task 61 on 2026-08-06.** `OUTLINE` is `#0d0d0d` rather than
`#2b2b2b`. The measurement that settled it: bucketing dark pixels by
value, the canon piles 17% of its figure ink into the 0-9 bucket while
ours piled 16% into 40-49. Same quantity of line, softer colour, and the
whole figure read hazier for it. Below value 20 we now sit at 15.9% of ink
against the canon's 17.5%. Not pure black, which is a shade harder than
the canon and gains nothing.

**The hierarchy half was re-examined afterwards and left alone.** The
claim below, that the canon draws a stronger heavy-silhouette to
thin-interior contrast than we do, came from looking at a hazier figure.
With the line black, the existing `_stroke_w` fractions (0.85 for interior
contours, 0.55 for hair strands, 0.45 for the nose, and opacity on the
softest of them) read as the right hierarchy at 4x, so there was nothing
to change. Strips in `out/61/`.

One thing the dark-palette check turned up, inherent rather than a bug: a
garment darker than the outline loses its own interior detail, since the
detail is drawn in a tone derived from the garment. It would have done
that at the old colour too, just less.


The canon outline is effectively black: mean ink value 9 on the Satoko
chibi and 19 on the Satoshi chibi, sampled at `#080808`. Ours is
`#2b2b2b`, mean 47. Alongside that, the canon draws a stronger contrast
between a heavy silhouette and thin interior detail than we do, which is
part of why the canon reads crisper at the same line quantity.

`OUTLINE` is one constant in `character.py` and `_stroke_w` already
scales with the figure, so this is a small change with a whole-figure
effect. Worth testing at 2x before committing: a pure black outline can
tip a flat palette toward harsh.

### 6. The chibi eye is too round

**Closed by task 60 on 2026-08-06.** The aperture's half-width now carries
a shared `_EYE_ASPECT = 1.28`, which lands its width on the canon's: mean
0.1158 of figure height against 0.1111. A shared constant rather than a
bigger `eye_width` per preset, because the roundness belonged to the house
eye rather than to either character, and the two presets differ from each
other on purpose. Candidates at 1.15, 1.28 and 1.40 were rendered side by
side (`out/60/lab_tight_fit.png`); 1.40 matches the canon's aspect exactly
but overshoots its width by a tenth and reads sleepy.

The aspect still comes out at 1.44 against the canon's 1.52, because the
canon's aperture is also about a tenth shorter than ours. That part lives
in `eye_openness` and `eye_lower_lid`, per-character expression values the
owner set deliberately, so it was left rather than tuned to a ratio.

**Spacing needed nothing, which is why it was measured second.** The gap
between apertures now reads 0.0659 H against the canon's 0.0781, so on its
own it looks 16% too close, having looked 20% too far apart before. But
centre to centre we are at 0.1817 against 0.1892, within 4%: the gap
changed because the apertures grew, not because the eyes moved. `eye_dx`
stays at the canon-derived `r * 0.46`. This is the same trap the original
finding below fell into, in the opposite direction.


Measured on Satoko's chibi, where the aperture detector agreed on both
eyes:

| measure | canon | ours |
| --- | --- | --- |
| aperture aspect (w/h) | 1.51 | 1.12 |
| aperture width / H | 0.111 | 0.090 |
| gap between apertures / H | 0.0781 | 0.0935 |

The canon eye is a wide almond and ours is nearly circular. In the canon
the iris touches both lids and leaves sclera only at the inner and outer
corners; ours leaves white above and below, which is what reads as
startled rather than guarded.

The knob is the aperture, not the iris. `presets.py` records that
`iris_size` was raised to 0.72 by eye precisely because a smaller iris in
an open aperture read startled, so shrinking the iris would undo a
decision already taken. Flattening the aperture (`eye_width`, and the lid
geometry in `_eye_shape`) lets the existing iris fill it.

**Spacing is a consequence here, not a separate gap.** The gap between
apertures is 20% wider than the canon's in absolute terms, and most of
that follows from the apertures themselves being 19% narrower while their
centres sit almost right. `eye_dx = r * 0.46` in `_face` is a canon
measurement someone already took deliberately, with its own note about
the eyes having previously crowded the middle, so it deserves the same
treatment as `iris_size`: widen the aperture first, re-measure, and only
then decide whether the spacing needs anything at all.

### 7. The head keeps its chibi shape at the realistic build

The canon adult head is an inverted egg: widest at the temples, cheeks
tapering to a narrow chin with a visible jaw angle. Ours is the same
rounded oval at both builds, nearly as wide at the jaw as at the temples.
Combined with gap 6 this is why the realistic build reads as a chibi head
on an adult body.

Measured: our silhouette is 8% to 18% wider than the canon's through the
head zone (0.02 H to 0.24 H) at the realistic build, for both
characters, while matching well at chibi.

`_head_shape(build)` already takes the build, so this is a shape edit in
one function rather than an architectural change.

**Closed by task 62 on 2026-08-07**, but not the way this entry expected,
and three of its claims were wrong. `_SKULL_NARROW = 0.10`,
`_JAW_START_Y = -0.25` and `_JAW_EASE = 1.4` are new, and `jaw_pull` went
*down*, from `0.30 * build` to `0.20 * build`.

- **The head already tapered.** `jaw_pull = 0.30 * build` was there. The
  shape at the adult build was not a chibi oval, it was a taper that
  began at the cheek line and eased quadratically, which holds full width
  all the way down the cheek and then loses it in the last tenth.
- **The 8% to 18% was not measuring the skull.** Through 0.02 H to 0.24 H
  at the realistic build the silhouette is hair, not head, so that number
  belongs to the residual below. The skull has to be measured separately,
  as the skin span across the face with the hair colours given to
  `rows --against`.
- **The chin is not where `skeleton` says it is.** `Skeleton.chin_y` is
  `head_cy + head_r`, but `_head_shape`'s `chin_drop` pushes the drawn
  chin to `1.05 * head_r`, so ours is at 0.188 H and not the 0.184 H the
  anchor reports. A first pass compared the two figures at depths taken
  from the anchor and so read our face 0.004 H too high, which at these
  sizes is the whole size of the claim. See `PITFALLS.md`.

Measured at depths above each figure's **drawn** chin (canon 0.176 H,
ours 0.188 H), so both are read at the same place on the face:

  | above chin | canon | before | first try | shipped |
  | --- | --- | --- | --- | --- |
  | 0.037 H | 0.095 | 0.104 | 0.087 | 0.094 |
  | 0.027 H | 0.081 | 0.085 | 0.071 | 0.079 |
  | 0.017 H | 0.061 | 0.059 | 0.050 | 0.056 |

Which says the jaw was **already about right**, within 3% to 9%. The
first try, a stronger taper starting above the cheek line, looked better
on the strips and measured worse, pulling the jaw 8% to 18% *under* the
canon. The head did not read round because the jaw was wide. It read
round because the whole upper face was, and a taper cannot take width out
of the cheek without taking more out of the jaw. So the fix is the other
way round: narrow the whole adult skull by 10% and taper it *less*, which
leaves the jaw within 2% to 8% and takes 12% off the widest point.

The cheek half cannot be checked against the canon at all, because their
hair lies over the temples and ours stands off them, so what is visible
there is a hair difference wearing a face's clothes. That half was judged
on the strips (`out/62/round2_satoko.png`, `round2_satoshi.png`), where a
narrower skull with straighter sides is clearly the canon's face and the
first try was still a wide face with a point on it. This is the "measure
to find out what is wrong, then choose by eye" rule doing real work: the
measurement redirected the change and the eye picked it.

The chibi loses about 1% of head width, since `build` is 0.1 at 2.4 heads
rather than 0. That is *away* from the canon, whose chibi head is wider
than ours rather than narrower, so it is a regression in principle. It is
also invisible: against the committed original the two are
indistinguishable (`out/62/chibi_check3.png`).

**Residual, and it is gap 2's, not this one's.** The hair envelope at the
realistic build is 20% to 24% wider than the canon's through 0.11 H to
0.20 H, where the silhouette is Satoko's falls. Measured in head radii,
the canon's falls sit about 1.05 radii off the head centre at that
height and ours about 1.33. At the chibi build the same profile runs the
other way, ours 10% to 13% *narrower* than the canon's. So the fall width
is not one number that is wrong, it is a number that does not ride the
build correctly, and task 59's values should not be carried into the hair
rebuild without re-measuring at both ends. Recorded on task 72.

### 8. Garment construction detail the canon draws and we do not

Individually small, collectively a lot of the "finished drawing" quality.
From `out/gap-analysis/torso_chibi.png`, `torso_real.png` and `legs.png`:

- **Sleeve over limb.** The canon's short sleeve ends in a curved hem and
  the undersleeve below it is visibly *narrower*, so a garment hangs over
  a thinner arm. `_arms` deliberately makes the arm the sleeve's own
  width (`out_top = _sleeve_half_w(sk) * 0.99`) to avoid a step at the
  hem, and the result reads as one continuous plank from shoulder to
  wrist. The canon wants that step; it is what says "sleeve".
  **Closed by task 63**: the arm is now 0.86 of the sleeve's width rather
  than 0.99, and its top edge still sits on `_sleeve_hem_y`, so the hem
  line and the top of the limb stay one line and the narrower arm leaves
  the outer stretch of it showing either side (`out/63/sleeve.png`,
  `full.png`). The curved hem in the same bullet was NOT done: curving it
  means the arm's top edge either stops coinciding with it, which
  double-lines, or has to be an exact sub-curve of it, and arms draw over
  every garment so it cannot simply hide behind the tunic. Worth doing
  with a quadratic-splitting helper, not worth faking.
- **Cuffs.** Satoshi's canon undersleeves are rolled at the forearm with
  a thicker cuff and two roll lines, leaving bare forearm below. Satoko's
  end in a wrist cuff. Ours run to the wrist with no cuff at either build.
  **Settled on 2026-08-07, and drawn in task 63** as `_wrist_cuff`, in
  the second tone and only where there is an undersleeve, since a cuff on
  a bare arm is a bracelet: the plain wrist cuff is in, since it is on
  Satoko's own references, and the rolled forearm cuff stays out, since
  the roll is Satoshi's and his references drive his haircut and nothing
  else about his design. STATUS.md previously ruled out cuffs wholesale
  and now names the roll instead.
- **Shoulder slope.** The canon shoulder runs down and out from the neck.
  Ours is a nearly horizontal cap with a square outer corner, most
  visible on Satoshi at the realistic build. **Closed by task 64**: the
  slope went from 0.14 of the shoulder-to-waist drop to 0.24, and the
  control point moved from far out and barely down to half way out and
  most of the way down, so the edge now leaves the neck descending
  instead of holding its height and then turning a corner
  (`out/64/shoulder.png`).
- **Apron.** The canon apron hangs *below* a belt, and the pouches hang
  at the hips off the belt. Ours is a rectangle with a hard top edge and
  the pouches sit on its upper corners, so at chibi the whole assembly
  reads as a satchel across the hips rather than an apron. The canon
  adult also has a knotted belt tie hanging down the apron's front, which
  we have nothing for. **Closed by task 65**: the panel is 0.74 of the
  waist half-width rather than 0.90, the pouches moved out to flank it
  instead of sitting on its corners, and the tie is drawn, a knot with two
  unequal tails. The apron's drop is now a share of the skirt's own drop
  rather than a fixed lift off its hem, which is what had collapsed it to
  a band across a chibi's hips: the old lift was measured hip to ankle,
  most of a chibi's whole body.
- **Belt.** The canon buckle is a frame with a pin, with a keeper and
  stitching along the strap. Ours is a hollow square. **Task 65** added
  the keeper. A square alone is a shape; a square with a strap running
  through a loop beside it is a fastening. Stitching along the strap is
  still missing.
- **Underskirt.** The canon adult's is a pleated skirt with vertical fold
  lines and a scalloped hem. Ours is a flat band, and at chibi its heavy
  dark rim under a wide hem reads as a tray. **Closed by task 66** for
  the pleats, drawn as lines, and for the tray, which was the band's own
  width: it hung at 0.97 of the skirt's hem width, so the silhouette kept
  the skirt's flare all the way past the hem, and it is 0.86 now. The
  scalloped hem is not done.
- **Trousers.** The canon has pocket seams, a fly seam, hip shaping and a
  taper to the ankle. Ours are two rectangles with background visible
  between them up to the hip. **Task 67** joined them with a wedge drawn
  behind the two legs, so only the V between them showed, and added the
  fly and the hip pockets. **That wedge was not enough and is gone**: it
  hung below the tunic's hem as a flap between two legs that still had a
  slot of canvas running up between them, and it was the most obviously
  wrong thing on Satoshi's lower body. Both references were measured
  properly for the rebuild, off the silhouette rather than the garment's
  colour, since the canon shades the cloth and the chibi is a JPEG:
  - **The tunic is tucked in.** Its green ends 23px *above* the belt's
    lower edge on both sheets, so the belt is the boundary between the
    two garments. Ours hung a band of tunic below its own belt and
    started the trousers at the hip, well below it.
  - **The trousers are one garment with a notch, not two tubes.** The
    silhouette below the belt is a single run until roughly a quarter of
    the way to the floor, 0.28 on the chibi and 0.23 on the adult, where
    background first appears between the legs; from there the slot opens
    smoothly to about a third of the garment's width by the boot. So the
    inseam above the crotch is a drawn line on solid cloth, and below it
    it is the two edges of the notch.
  - **The garment swells 8% from the belt to its widest**, 110.5px to
    119.5px on the chibi, which is what `hip_half_w / waist_half_w`
    already is at that build. **Measured but not drawn**: see the row
    below. The outer edges run straight instead.
  Rebuilt as one closed path in `_trousers`, top edge inside the belt
  band, straight down the outer edges, across each cuff and up the inner
  edges to meet at the crotch. `Outfit.tunic_tucked` shortens the tunic
  to meet it. `_trouser_seams` still draws the fly and the pockets.
- **Chibi legs are half the canon's width against the belt.** Found while
  measuring the above and *not* acted on. Against its own belt's
  half-width, the canon chibi's trouser leg is 0.39 and ours is 0.24; the
  pair of legs plus the slot between them spans 1.17 belt-widths in the
  canon and 0.62 in ours. So the canon's chibi wears its trousers as one
  straight column, hips no wider than legs, where ours has to give up
  40% of its width between the hip and the knee. This is `leg_half_w` at
  the chibi end, not anything the trousers can fix, and it is a bigger
  version of the standing "chibi 20% narrow at 0.75 H" row. The
  boot-to-trouser ratio is *not* implicated: 1.41 in the canon and 1.41
  in ours.

  It is also why the trousers do not carry the hip's own width, which the
  first rebuild had them do and which the canon's 8% swell would suggest.
  A hip drawn at `hip_half_w` has to shed 40% of it before the knee, and
  no distribution of that hides it: spend it low and each side grows a
  saddlebag, spend it high and the leg comes out thick at the hip and
  thin at the boot. The owner's call on 2026-08-07 was to put the
  straight line back, which is what the canon draws at both builds
  anyway. The flare is worth revisiting only after `leg_half_w`.
- **Boots.** The canon boot has a cuff, a tongue, eyelets, a heel and a
  sole. Ours is a rounded blob with lace crosses. At the realistic build
  ours is also 17% to 27% narrower than the canon's through the foot.
  **Task 68** turned the cuff from a line into a band, added a tongue
  under the laces and eyelets where they turn, above build 0.4.
  **The width claim is wrong and was reverted.** Measured on the boot's
  own colour rather than on the silhouette, the canon's adult boot is
  0.058 of figure height across and ours 0.076, so ours is a third
  *wider*. The silhouette agreed only because the canon stands its feet
  further apart than we do, and outer edge to outer edge is stance plus
  boot. Widening to chase it took the foot 22% past the canon. The real
  residual is the stance, and a heel is a side-view feature a front view
  can only imply.
- **Hands.** The canon indicates fingers with short strokes. Ours are
  teardrop blobs, and at chibi they sit at the same height as the pouches
  so they merge with them. **Closed by task 69**: two short strokes run
  in from the outer edge above build 0.5, alongside the thumb crease that
  was already there. Not separate digits, which the code had already
  ruled out for reading as noise at this size, and which is also what the
  canon does. The chibi merge went with task 65's pouches moving out.

### 9. Chibi hem too wide, adult hem band too wide

Our chibi silhouette runs 13% to 17% wider than the canon's at 0.80 H to
0.85 H, and the adult 8% to 20% wider at the same rows. In both cases it
is the skirt hem plus the underskirt band. `hem_half_w` lerps to
`head_r * 1.11` at chibi; the canon's flare is gentler and its underskirt
does not extend past the skirt.

**Closed by task 66**, both halves at once, since they are one row of the
silhouette: `hem_half_w` lerps to 1.02 at chibi and the underskirt hangs
at 0.86 of the skirt's hem width rather than 0.97. The chibi went from
+17.6% and +13.3% at 0.80 and 0.85 to +9.5% and -6.9%, the adult from
+19.8% at 0.85 to +6.2%.

Residual, and it is the other direction: at 0.75 H the chibi is 20%
*narrower* than the canon and always was. That row is above the hem, so
it is the skirt's own length and rise rather than its flare, and it did
not move with this.

## Suggested order

1. ~~Gap 4 (reshape the shadow wedges, or ask about dropping the garment
   tones)~~. **Done, task 56**: dropped. Smallest change, immediate
   effect, and it makes everything else easier to judge.
2. ~~Gap 3 (fringe down to the brow)~~. **Done, task 57**: lowered by
   0.19 head radii, long cut only, keeping the part.
3. ~~Gap 2 (Satoko's fall width)~~. **Done, task 59.**
4. ~~Gap 6 (flatten the chibi eye, then re-measure the spacing)~~.
   **Done, task 60**: widened, and the spacing needed nothing.
5. ~~Gap 5 (outline toward black)~~. **Done, task 61**, after 4 so the two
   were judged separately.
6. ~~Gap 7 (adult head taper)~~. **Done, task 62**: the taper now starts
   above the cheek line and runs straighter. What looked like gap 2's
   residual belonging here turned out to be hair, not skull, and went
   back to the hair work.
7. ~~Gap 8 and gap 9~~. **Done, tasks 63 to 69**, with the palette's one
   open item (task 70) alongside. What is left inside gap 8 is named in
   its own bullets: stitching along the belt strap, a scalloped underskirt
   hem, a wider stance, and gap 9's one remaining row, the chibi being
   narrow at 0.75 H.
8. Gap 1, **re-opened by the owner on 2026-08-07** together with a
   rebuild of Satoko's cut. Both hair gaps have the same root: the
   contract gave a cut one horizontal tone band where the canon runs the
   tone along each lock. **The contract is changed, task 71**:
   `tip_edge` is now a list of regions clipping to their union, so a cut
   can give every lock its own boundary, and a ceiling test now makes a
   sliced crown fail loudly instead of shipping. **Satoshi's crop (task
   73) is authored but parked**, five rounds in and not yet past the
   owner's bar of beating the plain circle by eye; it renders as
   `short_tousled`, nothing points at it, and what works and what does
   not is written up in `STATUS.md`. **Satoko's re-authoring has not
   started**, and its acceptance spec is the two residuals under gap 2
   above, not the shipped `_FALL_*` values.

Gap 8's items are independent of each other and can be picked off in any
order, which makes them good filler work between the larger passes.
