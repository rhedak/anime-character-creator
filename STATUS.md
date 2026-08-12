# Status

Snapshot of where the generator is and what comes next. Working notes,
not user documentation: see `README.md` for how to run it,
`docs/architecture.md` for how the drawing code fits together,
`docs/api.md` for the public surface, `docs/gap-analysis.md` for a
measured comparison of the current renders against the canon, and
`CLAUDE.md` for the rules that govern changes.

Last updated: 2026-08-08, at `0652e73` "focus on chibis", plus two
uncommitted canon passes: the first for language (stroke scaling, canon
eyes, long-cut locks, pouches and buckle, boot toes and laces, mitten
hands, realistic polish, off-centre parting; tasks 35-43), the second
for shape (high-part fringe with visible forehead, eyes lower and
apart with brows on the lash line, bell hair silhouette, chibi arms
clear of the tunic with canon-sized hands; tasks 44-47), plus a
user-caught limb-width swap (chibi legs now wider than arms, task 48),
plus the Satoshi hair pass (bob to shaggy crop: ear-level bulk, spiked
rim, roughened fringe, fade rebalanced; crown cowlick flicks were tried
and reverted on the owner's call, and were re-opened on 2026-08-07 as
part of the hair rebuild below; tasks 49-54), plus the fade move (both cuts now change tone half way
down the hair, at every build, off one shared `_HAIR_FADE`; task 55).
Per-task snapshots used to sit in `out/35` through `out/73`, one
directory per task. **They were deleted on 2026-08-07**, 128MB of
renders in an ignored directory, so they were never on a fresh clone
anyway and the findings they supported are written up here and in
`docs/gap-analysis.md`. What was kept is the code that measured them:
the harnesses moved to `harness/`, which has its own index. Citations
below of the form `out/NN/...` name images that no longer exist; they
are left in place because knowing which task drew a picture still tells
you what was being compared. Where a surviving script regenerates one,
the script is named instead.

On top of that, one change that touches no shape: the code is now a
proper package (`src/anime_character_creator/`, `pyproject.toml`, uv,
ruff, a smoke test suite, `docs/`). Every render came out byte for byte
identical, which is what `./refresh-ref-out.sh --check` was there to
prove.

Then the gap analysis (`docs/gap-analysis.md`, with the `gap-analysis`
skill that carries its procedure and tooling), and the first pass off its
ranked list. **Task 56, the garment shadows are gone.** The owner's call
was to drop them rather than narrow them, so `CLAUDE.md`'s flat-colour
rule now says a second tone is for small elements and never a plane
across a panel. Shadow-tone area fell from 5.9% of the chibi's ink to
0.9%, and from 15.3% to 3.1% at the taller build. **Task 57, the long
cut's fringe sits 0.19 head radii lower**, which is the excess the
analysis found rather than the brow-line coverage an earlier pass tried
and reverted: the high part and the visible wedge of forehead stay, and
the centre line now lands at 0.146 of figure height against the canon's
0.147. Satoshi's crop was already right there and was left alone.
**Task 58, the crown strand lines no longer converge**: every one of them
used to start at the crown, so four lines on the long cut and six on the
short one left the same small patch, and on the short cut's part-circle
mass that read as a beach umbrella. Each starts part way along its own
path now. What is left of the umbrella is the dome, which is the parked
crown tousle and nothing else. **Task 59, the long fall stands 0.10 head
radii further off the skull** at the temple and the cheek, so it holds a
width past the face instead of pinching at the jaw and bulging below it.
The bell stays, since the canon flares below the face too. That edge
turned out to be defined in four places with nothing tying them together,
and the first three now read shared `_FALL_*` constants. **Task 60, the
eye aperture is a wide almond** rather than a near-circle: one shared
`_EYE_ASPECT` puts its width on the canon's, 0.1158 of figure height
against 0.1111, and `eye_width` goes on meaning one character's deviation
from the house eye. Spacing turned out to need nothing once that landed:
centre to centre we were already within 4%, and the gap only looked wrong
because the apertures were narrow. **Task 61, `OUTLINE` is near black**,
`#0d0d0d` rather than `#2b2b2b`: the canon piles 17% of its ink into the
0-9 value bucket where ours sat at 40-49, same amount of line but softer,
and the figure read hazier for it. The line-hierarchy half of that gap was
looked at again afterwards and needed nothing. **Task 62, the adult skull
is 10% narrower and tapers less**, `_SKULL_NARROW`, `_JAW_START_Y` and
`_JAW_EASE`, with `jaw_pull` going down rather than up. The analysis had
this backwards and the measurement caught it: the head already tapered,
and read at depths above its *drawn* chin the jaw was already within 3%
to 9% of the canon. It read round because the whole upper face was wide,
and no taper takes width out of a cheek without taking more out of the
jaw. Narrowing the skull and easing the taper holds the jaw within 2% to
8% and takes 12% off the widest point. The cheek itself is not checkable
against the canon, whose hair lies over the temples where ours stands
off, so that half was picked on the strips. The chibi is unchanged to the
eye.

**Tasks 63, 64 and 70** then took gap 8's two sharpest items and the
palette's one open one. The arm is 0.86 of the sleeve's width rather than
0.99, so a garment hangs over a thinner limb instead of the two reading
as one plank, and its top edge still sits on `_sleeve_hem_y`, so the hem
line and the top of the limb stay one line. `_wrist_cuff` closes the
undersleeve, in the second tone, drawn only where there is an
undersleeve. The shoulder's slope went from 0.14 of the shoulder-to-waist
drop to 0.24, with its control moved half way out and most of the way
down, so the edge leaves the neck descending rather than holding its
height and then turning a corner. And `HAIR` is the canon's `#e3b448`,
which carries to the brows through `shade()`.

**Tasks 65 to 69** finished gap 8's construction detail and gap 9. The
apron is narrower with the pouches flanking it rather than sitting on its
corners, and hangs a share of the skirt's own drop instead of a fixed lift
off its hem, which is what had collapsed it to a band across a chibi's
hips; the belt gained the knotted tie the canon hangs down the apron's
front, and a keeper beside the buckle. The underskirt is pleated with
lines and hangs at 0.86 of the skirt's hem width rather than 0.97, which
with `hem_half_w` coming in to 1.02 at chibi took the hem rows from 13%
to 20% wide of the canon to within 7%. The trousers are one closed path
starting inside the belt band, with the legs parting at a crotch a
quarter of the way to the floor and `_trouser_seams` drawing the fly and
hip pockets over it; `Outfit.tunic_tucked` ends the tunic at the belt to
meet them, which is how both references wear it. The boot
has a cuff band, a tongue under the laces and eyelets where they turn.
The hand has two finger strokes above build 0.5.

One analysis claim turned out to be wrong and was reverted inside task
68: the boot is not 17% to 27% narrow of the canon, it is a third
*wider*. The silhouette agreed only because the canon stands its feet
further apart, and outer edge to outer edge is stance plus boot.

**Task 71 changed the hair contract**, the piece both hair gaps were
waiting on: `tip_edge` is a list of closed regions clipping to their
union, so a cut can give every lock its own tone boundary instead of
running one level line across the whole head. Every render came out byte
for byte identical, which is what that refactor should do. A ceiling test
came with it, solving each quadratic for its own extremum, so a crown
that would be sliced flat against the canvas edge now fails loudly
instead of shipping; the slack today is 16px on the long cut's chibi and
2px on the short cut's adult.

**Task 73, Satoshi's tousled crop, is authored but parked.** It renders
as `short_tousled`, passes everything, and nothing points at it, so no
render regressed. Five rounds in it does not beat the plain circle by
eye, which is the owner's standing bar. What works is the spike-chain
crown, straight lines between alternating tip and notch marks, which is
the right language: a silhouette of tips and notches has no circle left
in it to spoil, where a bump added onto an arc is the wobble that got the
first attempt reverted. What does not is the fringe. The canon's locks
*overlap*, so there is one line between neighbours; ours is a single
zigzag boundary whose every notch is two strokes converging into a black
wedge, and it reads as a saw. Fixing that means drawing the front locks
as their own shapes over the fringe fill, which the contract has no slot
for yet. Two smaller faults behind that one: the cowlick reads as an
artifact stuck on the crown rather than as a blade, and the pale reaches
the fringe in only two or three thin runs where the canon has one per
lock. Progress renders are in `out/73/`, canon at 5x in
`out/73/ref_head.png`.

One measurement from those rounds is worth keeping whatever happens to
the cut: the canon crop is widest 54% of the way down the hair's own
height, at the temples, while the shipped `short_layered` is widest at
89% down, which is the bottom of its mass, because that mass is a circle.
That single number is most of why one reads as a haircut and the other as
a dome.

**The figure has ears** (the owner's call, 2026-08-07, as the first step
of the hair rebuild). They exist on their own merits, a head with no ear
reads as unfinished at the tall build, but the reason they came first is
that they are a *landmark*: a side lock's length and flare were being
chosen against nothing at all, which is a large part of why Satoshi's
crop took five rounds without settling.

Placement is measured, not assumed, and the assumption was wrong. The
life-drawing rule of brow to nose put the ear 0.16 head radii too high.
`ref/satoshi-real.jpg` is the one reference that draws the ear plainly,
with the hair hanging around it rather than over it, and it puts the ear
at 0.03 to 0.49 head radii, top level with the top of the eye aperture
rather than the brow, widest 59% of the way down. The fit is eye centre
to drawn chin, 0.89 head radii apart in our own construction and
unambiguous ink in the reference. Eye to mouth was tried first and is
unusable: the canon's mouth sits lower against its head than ours does,
and the two pairs disagree about the head's radius by 38%.

The ear's own width is the one canon number that would not transfer. The
canon ear is 0.263 head radii wide and sticks out past a cheek sitting at
0.632, for a total silhouette of 0.895; our bare skull is already at 0.81
at the adult and 0.94 at the chibi, so matching the total is arithmetically
impossible and matching the width would have given an elf. Our head being
wide against the canon's is the open residual under gap 2. The ear takes
0.17, chosen by eye off the sheets `harness/ear/lab.py` draws.

Two pieces of machinery came with it. `_head_pt` is now the single
definition of the skull's profile, with `_head_shape` walking it and a
new `_head_edge_x` sampling it, so a part welded to the head follows the
jaw taper for free instead of re-deriving it; that extraction was proved
byte-neutral before the ear went on top of it. And a test asserts the
ear's contour never dips inside the skull, which is the failure a future
taper change would otherwise cause silently.

It has no build-dependent size. A child's ear really is larger against
its skull than an adult's, and that was in for a round as a shrink on the
build, but the span is measured off the *adult* reference, so the shrink
made the one build the number came from the one build that did not
reproduce it. It is gone rather than inverted.

**The outline itself is now traced** (the owner's call, 2026-08-07: the
shape is still a bit off, align it, and here is a crop). Two quadratics
out to a widest point and back was the right idea and the wrong curve.
The canon's rim leaves the top attach far faster than one control can,
holds its width through the middle of the ear rather than peaking, and
comes back in along the lobe; four segments carry that, which is the
finest the line weight supports. The inner fold is traced with it, one
stroke shaped like a question mark.

Two things fell out of doing it. **A retraction**: this said no reference
showed a chibi ear, both cuts covering it. `ref/satoshi-chibi.jpg` draws
the viewer-right one clear of the hair, which is where the owner's crop
came from, and it puts the chibi's ear at 0.024 to 0.614 head radii
against the adult's 0.03 to 0.49, about 30% taller against the skull,
the way anatomy says. The span shipped is still the adult's: turning that
into a build-riding one is a placement change and the ask was shape. And
**a check that came out right**: stand-out over height is 0.361 in the
canon chibi against 0.370 in what we already had, so `_EAR_OUT` at 0.17,
picked by eye, needed nothing. Harness in `harness/ear2/`.

**Satoshi's crop is traced** (the owner's method, 2026-08-07: outline the
canon's hair, then apply the shape to our head). The harness is
`out/trace/`. Curves are authored in head-radius units, the same system
the shape code uses, so porting is dropping numbers in rather than
fighting a transform; the calibration is checked by drawing our own head
outline back onto the reference before anything is traced on it.

Two methods were tried and the first was wrong. Picking tips and notches
by eye off a polar grid and putting each control point at the mid-bearing
at the mean radius bulges every edge outside the chord, which on a contour
made of straight lock edges is wrong everywhere at once. What works is
measuring the contour as a radius per bearing, simplifying it with
Douglas-Peucker, and least-squares fitting each control point, which is
exact for a quadratic with its endpoints pinned. An extrema-thinning pass
was tried in between and silently ate the whole sawtooth down one side,
because dropping the shallowest pair leaves a real tip adjacent to a
notch of similar radius, which then goes too.

**How fine to simplify is decided by the line weight, not by taste.** The
overlays are a thin line over a magnified reference, which flatters
detail; `_stroke_w` is figure-relative, so a feature shorter than about
two stroke widths has the strokes either side of it overlapping and no
amount of rendering bigger rescues it. Counting the fit's edges that fall
under two strokes gives a clean cliff: 50 segments has 11 to 15 of them,
32 has 4 to 6, and 26 has none at either build. **26 is the level**, being
the finest that draws. `harness/trace/weights.py` draws the same trace at three
levels at the real weight, and `harness/trace/detail.py` is the count.

**The trace matches the adult and does not port to the chibi, and the
reason is a gap nobody had named.** The canon draws a chibi's hair about
29% bigger against its head than an adult's, in reach and in width alike;
ours is one outline in head-radius units at both builds, tuned to the
adult. So every chibi we ship wears an adult's volume of hair. The
numbers, the calibration and its cross-checks are in
`docs/gap-analysis.md` under gap 1.

**The owner chose to let the volume ride the build (2026-08-07), and it
is in.** `short_crop` is registered and carries the traced outline, and
`Hairstyle` has a `volume` field, a pair of multipliers on `tip_range`'s
answer for the chibi and adult ends, defaulting to None so the two older
cuts are byte for byte unchanged. `build_skeleton`'s `hair_margin` now
rides the build too, 0.75 at the chibi end and 0.36 at the adult, since a
chibi crown at canon volume reaches 1.69 head radii and the old ceiling
was 1.36. The adult renders are byte-identical; the two chibis are 7%
smaller in frame, which is what the headroom costs and is the price of
the change. `out/trace/margin_effect.png` is the before and after.

**`short_crop` is Satoshi's cut** (the owner's call, 2026-08-07, after
seeing both builds). It replaces `short_layered`, which stays in
`HAIRSTYLES` as a style anyone can ask for and is now referenced by no
preset. `hair_length` 0.65 is unchanged and is the neutral value here:
the cut's `tip_range` is set so that 0.65 *is* the size it was traced at.

Promoting it does more than improve one render. Unreferenced, a cut is
only ever exercised on default `CharacterParams`; pointed at a preset it
comes under the `ref-out/` byte check and the four-render smoke test, at
both builds and on Satoshi's own frame and palette. Checked outside the
blonde range too, near-black on plum, teal on cream and a single-tone red
(`harness/trace/loud.py`).

**What is shipped is one quarter of a cut, and the other three quarters
are visibly borrowed.** `harness/trace/see.py` draws the canon, the traced
crop and what ships today, side by side.

**The fringe is traced off the owner's own crop, after five readings off
the full drawing failed.** Each failed differently and each was caught by
eye against the reference's outline rather than by a number; all five are
written up in `harness/trace/fringe.py` and `fringe2.py` so the next attempt
does not repeat them. The reason none of them worked is worth stating as
a limit rather than as five near-misses: **on this JPEG the canon's pale
tips sit colorimetrically between its gold and its skin**, the forehead
at sum 589-601 and red minus blue +45 to +57, skin beside a drawn line
ringing to 520-622 at +8 to +56, the gold-to-pale band at about +40 and
650. No threshold puts all three on the right side of it.

`ref/satoshi-chibi-fringe.png` settles it, and not for the reason it
looks like. Its alpha is a coarse outer selection with the gaps between
blades left opaque, so that is not the signal. What matters is what the
crop leaves *out*: no brows and no eyes. On the full drawing the deepest
ink in a column is the brow, which is why reading the drawn line came out
along the eyebrows; in the crop the deepest ink can only be the blade
that made it. The crop is placed back in the reference by template match
rather than an eyeballed offset and matches to a mean squared error of 1,
so the calibration is the reference's own.

The result is 16 segments with five lock tips, and it draws: the fringe
reads as pointed blades at both builds rather than as a scalloped band or
a comb of needles. **A claim made from one of the failed readings is
retracted**: it said the canon's fringe was a deep zigzag of needle-tipped
locks, 17 of 22 sides in solid ink, and that drawing it needed a contract
slot for overlapping locks. The two reverts that claim caused were right
on the evidence available; the evidence was wrong.

**Satoko's cut is traced and built as `long_traced`, and nothing points
at it yet.** Both boundaries come off `ref/satoko-chibi-hair.png`, and
the signal is the owner's correction: **trace the drawn black outline,
not the crop's alpha.** The alpha is a rough selection, some of the page
opaque and the face opening a staircase; the ink is the artist's own line
and is exact where the selection is not. Reading ink works on a crop of
hair alone and fails on a whole face, because brows and eyes are the only
other dark things on one. Here the furthest ink along a bearing is the
mass and the nearest is the hairline. The crop places back into the
reference at a mean squared error of 1, and her eye half-separation
cross-checks the calibration at 0.459 head radii against our house 0.46.

Eighteen segments for the mass and eight for the hairline, both the finest
levels with no edge under two stroke widths. **Satoko now wears it.** It renders fuller and rounder than `long_blunt`,
its parting reads, and the pale follows the falls instead of cutting a
level line across them; `harness/trace/satoko_see.py` puts both builds
beside their references. The gain is smaller than Satoshi's was, which is
expected: her `long_blunt` bell was tuned by eye in task 59 and was
already close to the traced outline (`harness/trace/satoko_port.py` overlays
them).

**The line down the inside of each fall was missing** (the owner spotted
it and painted it in). It is the line that says the hair hangs in front
of the shoulder rather than behind it, and its absence was a limitation of
how the boundary was read: a radial sweep from the head centre cannot
describe that stretch, because below the cheek a fall runs almost straight
down and a whole fall's worth of it falls between two bearings. Scanning
rows there instead gives it, and the two readings agree where they meet,
both being the same drawn line. `back` now closes on the mass's own
contour, so the front hair covers exactly the band between the hairline
and the silhouette, which is what hair is.

Three faults were found by looking, and all three were mine rather than the
trace's. The tone region left a gold wedge poking into the pale at the
foot of each fall, because it was built from only those segments lying
below the head centre, which is not a contiguous run; it now lifts the
whole contour and clamps it at the half-and-half line, so the pale follows
the tips and never climbs over the crown. And **a long cut was given a
head-relative `tip_range`**, which froze her hair at one length in head
radii, so at the adult build it rode up her back into a short white
curtain. That is precisely what the body-relative branch of `_hair_fall`
exists for. `_long_scaled` now stretches only what lies below
`_HAIR_CHEEK_Y` and leaves the crown alone, which is the split the hair
contract has always documented, and the cut measures its length against
the body again. The hairline gets the same treatment, since its lower half
rides the falls and its upper half sits on a face that does not grow.

The containment test earned its keep twice more here, on 0.010 head radii
of fill outside the outline: once from a connector bowed off the line
between two points of the silhouette, and once where a fall's inner and
outer edges converge at its tip and the fit put the inner one a hair
outside. Neither would have shown as a misplaced line, only as colour in
the wrong place.

**The tone boundary follows the blades now** (the owner's call,
2026-08-07), and this is the state the chibi is locked at. `_crop_tip_edge`
was a single wave at a fixed height, which could only say "pale below this
line" and read as a white liner under a gold cap. It is the fringe's own
traced chain lifted by `_CROP_TONE_LIFT` and extended out to the mass on
both sides.

The cheap trick is worth understanding rather than just using: a
**uniform** lift over a boundary whose blades end at different depths
leaves every blade pale from a fixed distance above its own tip. So the
pale lands in the tips and the gold at the roots without anything being
stated per lock, and one traced list does two jobs instead of two lists
that can drift apart. What it gives up is that the canon varies how far
the pale climbs from lock to lock; here they all get the same depth. The
bar was the spirit of an edge per lock, not the canon's own.

This does *not* use `tip_edge`'s list of regions, which task 71 added for
exactly this and which nothing has needed yet. Per-lock regions remain the
way to vary the depth per lock if that ever matters.

**The chibis are locked in** (the owner's call, 2026-08-07, confirmed
after the tone change above): the chibi crop is where it should be and
further work goes elsewhere. Nothing extra
is needed to hold it, because `ref-out/` already pins all four renders
byte for byte and `test_ref_out_matches_the_code` fails the moment a shape
changes. That is the lock: refreshing it is a deliberate act, so a chibi
cannot drift without someone choosing to let it.

**The realistic build's hair is too compressed, and it is deferred, but
here is the measurement while it is fresh.** The band of hair between the
fringe's highest notch and the crown comes to 1.035 head radii at the
chibi and 0.683 at the adult, while the blades themselves run 0.506 at
both. So the fringe eats half the depth at the chibi and three quarters
of it at the adult, which is the squashed look. The cause is structural
rather than a bad number: **the mass rides the build and the fringe does
not**, so an adult wears a chibi's fringe under an adult's crown. Two ways
out, and the second is the one that just worked here: scale the fringe on
the same `volume` the mass uses, or trace an adult fringe from a crop of
`ref/satoshi-real.jpg` the way the chibi's came from
`ref/satoshi-chibi-fringe.png`.

Two residuals on the trace itself. It is off the *chibi* reference, and our fringe is
fixed rather than scaled by build, so it sits a little higher over the
adult's eyes than the canon puts it. And the tone is still one wave
across the head rather than a region per lock, which is the original
complaint about this character and the next piece of work. `fringe2.py`
turns out to trace the gold-to-pale boundary cleanly, which is exactly
what those per-lock regions will need: the right tool pointed at the wrong
question, kept for the right one.

The rest of the cut that ships is the silhouette. The fringe is
still the short cut's scalloped locks, the tone boundary is still one
wave rather than a region per lock, and the strand lines are still a
regular fan; all three are visibly a different language from the traced
outline and are the next steps in that order. One defect found by looking
and fixed: the hairline's side runs were made-up radii that sat *outside*
the traced contour, putting a stroked line beyond the silhouette that read
as loose ends tangled down the cheek. They come off the trace's own points
now.

Closing it was cheaper than it first looked and the first estimate here
said so wrongly. It does **not** need a contract change: the shape
callables already receive one float from `_hair_fall`, which already has
the skeleton and today ignores it for any cut with a `tip_range`, so a
skull-pinned cut can express its radii off that float and have it ride
`sk.build`. What it does need is `hair_margin`, since 1.68 head radii
plus the stroke is well past the current −1.36 ceiling. Raising it
globally shrinks every figure on the canvas, 6.5% at the chibi and 2.8%
at the adult, so it should ride the build too and leave the adult alone.
That is still a change to every chibi render's scale, which is why it is
the owner's call rather than something to decide while tracing.

**The outline did not match the fill on the upper left, and the outline
was the broken half** (the owner spotted it, 2026-08-07). `_hair_front`
drew the lock edge and *its mirror*, one chain reflected, which is a
hidden assumption that every cut is symmetric. It was silent for as long
as every cut was. The traced crop is not, so its right-hand edge was
stamped onto its left where the mass is a different shape, and drew a row
of black barbs standing off the silhouette with white between them and
the hair. `fall_edge` is a list now, one chain per side, and a symmetric
cut says so by handing back both through `_mirrored`. That is the same
move `tip_edge` made in task 71, and for the same reason: what looked
like one thing the framework could derive was really a statement only the
cut can make.

The mass's own stroke also picked up round joins on the way past. It is
not what caused the barbs, but SVG defaults a join to `miter` with a limit
of four, so a sharp enough corner shoots a spike up to four stroke widths
past the point it is drawing, and this is the first cut whose locks meet
at real points.

**The hair fill was also escaping its own outline, and there is a test for
it now** (the owner spotted it, 2026-08-07). The traced crop's closing edge
was three hand-picked quadratics written as flat multiples of the scale,
so it sat at a constant radius while the traced crown does not, and
between two tips the gold painted outside the spikes as a smooth arc. The
closing edge comes off the mass's own points now, pulled in a fixed
fraction, so nothing restates the crown. That is the lesson task 59
already paid for on the long cut: an edge stated twice drifts.

`test_the_front_hair_adds_no_silhouette` is the check that was missing,
and it is worth having because this failure is *silent*. The closing edge
is a fill boundary and never carries a stroke, so when it strays there is
no line out of place, just hair colour where there should be none. It
found two more leaks in the parked `short_tousled` immediately: its fringe
ended on a hand-written point that missed the mass's own lock tip by
0.011 head radii, and its inner crown arc stood at a picked 1.16 under a
crown whose notches drop to 1.06. Both now read the data rather than
restating it.

Getting the test to say something true took three attempts and the first
two both cried wolf, which is recorded in its docstring: comparing radii
at a shared bearing breaks near a lock tip where the radius moves fast
against the bearing, shrinking each point toward the head centre breaks at
a tip too because the inward direction there is along the lock, and a
coarsely sampled mass reports points on its own outline as outside it by
the chord sagitta. What works is point-in-polygon against a densely
sampled mass, with a hair's breadth of tolerance for the stretches that
retrace it exactly.

**The ear is now at the canon's depth**, over the back hair and under
`_head` (the owner asked, 2026-08-07). It went in over the head first and
moved under it later the same day, once the traced outline made the
difference legible: the canon runs one unbroken heavy line down the side
of the face with the ear behind it, and over the head our rim ran into
that outline and joined it, so the two read as a single silhouette that
bulges rather than as an ear behind a face. `out/ear2/depth.png` is the
canon and both depths side by side. Everything below about *reaching*
that depth stands; only which side of `_head` it lands on changed.

What had been blocking it turned out to be two separate things, and only
one of them was about the ear.

The first was a bug in the traced crop's own hairline: its `line` ran
down both sides to the mass's bottom tips and its `back` closed on the
mass's whole reversed chain, so the front fill covered everything the
mass covered and left the ear nowhere to be seen. It reads at the chibi
and all but vanishes at the adult. Floating the ear over the hair would
have hidden that rather than fixed it; the fringe runs temple to temple
and stops there now, and the ear reads at both builds.

The second is real and stands: a cut whose side locks live only in the
mass cannot cover an ear, because the mass is drawn behind the head and
the ear is in front of it. `long_blunt` and `short_layered` are both like that, so
a hint of ear shows at their temples, 91 to 561 px per render. Both are
slated for re-authoring and this is one more thing the re-author has to
answer. `harness/ear/wedge.py` measures it and `harness/trace/eardepth.py` draws the
three depths compared under the traced crop.

The paragraph below is what this said before that change, kept because
the reasoning still holds for any cut that has not been re-authored.

And **the ear was not, at first, at the depth the canon draws it.** It ships under
`_hair_mass`, which hides it completely: all four renders are byte for
byte what they were before the ear existed, so the README's art is
untouched. The canon's depth is over the head and under the front locks,
and at that depth both cuts fill the temple solidly enough that what
appears is a wedge of ear through the hair's inner edge rather than an
ear, 90 to 630 px of it per render. That is the coupling the owner
diagnosed, measured rather than argued: the hair owns the ear's space.
`harness/ear/wedge.py` reproduces it, and draws the picture.
**Moving `_ears` out from under `_hair_mass` is one line and belongs in
the hair rebuild**, once a cut leaves the ear room. (It landed just
*before* `_head` rather than just after, for the reason at the top of
this section.)

## Where it stands

All four PoC targets render: Satoko and Satoshi, each at `chibi` and
`realistic`. Every shape is computed from the `Skeleton`, nothing is
composited from pre-made art, and no AI image generation is involved.

Two more characters landed on 2026-08-08, and they are the same two
people: Kyoko is Satoko before the dye and the burn, Tomohiro is Satoshi
the same way, each a `replace()` of three fields on the preset it comes
from rather than a second set of numbers. The derivation is the point,
not a shortcut, since a copied face agrees on the day it is written and
drifts the first time somebody tunes an eye. See
`docs/character-roster-plan.md`, which also holds the plan for the ten
remaining characters in the cast.

The same day, **the realistic renders were deferred**: the tall figures
do not work well enough to publish, so the chibi is now the build this
project ships. They moved to `ref-out/real/`, lost their on-white copies
and came off the README, and only `presets.REALISTIC_REFS` (Satoko and
Satoshi, the two ever measured against a reference) still gets one. The
`realistic` build itself is untouched and works on any character.

`ref-out/` holds the chibis as checked-in `.png` and `.svg`, and the
README displays them. It is the only generated output in version control,
and it is the current state of the named characters rather than a
snapshot of some past one, so **refresh it in the same change that alters
a shape.** Miss it and the README shows art the code no longer produces:

```bash
./refresh-ref-out.sh          # re-render, report which characters moved
./refresh-ref-out.sh --check  # compare only, write nothing, exit 1 if stale
```

`ref-out/cover.svg` and its PNG are the fifth checked-in render: the book
cover from `cover.py`, a flat backdrop with mist banks, one character and
the title over it. It is refreshed by the same script, which matters more
than it looks, since the cover embeds a character and so goes stale on
**any** shape change rather than only on its own.

Anything else goes to `out/`, which is ignored, and which was emptied on
2026-08-07: 128MB of per-task snapshots, with the scripts that measured
them promoted to `harness/` first.

`ref-out/on-white/` holds the same chibis on a white card. They exist for
the README and for nothing else: the page's background colour is not
ours to set, `OUTLINE` is `#0d0d0d`, and a dark theme is around
`#0d1117`, so a transparent figure there loses its entire outer contour
and keeps only the interior line work, which sits on filled shapes. They
are rendered through the same path with `--background white` rather than
composited afterwards, so they cannot drift from the art. Their absence
counts as stale in `--check`, since a missing card leaves a broken image
in the README while the drawing itself is perfectly current, and the SVG
comparison alone would call that clean.

**Those four render on transparency** as of 2026-08-07, the owner's call:
a character gets composited onto a scene, so a white rectangle behind it
was never part of the drawing, only something a caller then had to
remove. `render_character` takes `background`, defaulting to none, and
the CLI takes `--background white` for the old opaque document. The
`fill="white"` still in each `.svg` is the sclera of an eye, which is why
the test walks the elements rather than searching the text.

That change has one consequence that would otherwise bite silently, and
it is the same shape as every other measurement trap here. Anything that
finds the figure by looking for near-white background has to flatten the
alpha onto white on load; a plain `convert("RGB")` throws the alpha away
and leaves the background **black**, so the whole canvas counts as ink
and the numbers come out wrong rather than the run failing.
`probe.py`'s loader and `harness/trousers/measure.py` both do the
flattening now, and both were checked against the transparent renders.

What is parametrized:

- **Build.** `BUILDS` names `chibi` (2.4 head-heights, the default) and
  `realistic` (6.0). `--heads N` reaches anything in between. Both
  widths and where the landmarks sit along the body interpolate, so a
  chibi comes out nearly neckless with high hips and an adult does not.
  `Skeleton.build` exposes where along that range a figure sits, so
  parts that deform with the build read it instead of recomputing it.
- **Frame.** `frame` scales shoulder against hip, -1 narrow-shouldered
  and wide-hipped through +1 the other way. It rides on the build, so it
  bites at `realistic` and all but vanishes at `chibi`, where the head
  swamps the torso anyway.
- **Where the legs hang.** At the taller builds the outer edge of the
  thigh lands on `hip_half_w`, which is what the tunic's hem is drawn to,
  so the body's side carries straight on down into the leg rather than the
  trousers overhanging it. That falls out of the frame for free: a
  narrow-hipped figure's legs come in, a wider-hipped one's go out. It
  also happens to land the crotch gap where `ref/satoshi.png` has it, each
  inner edge about 0.09 head radii off centre. A chibi keeps its legs
  tucked in close instead, since its hips are nearly as wide as an adult's
  in head radii while its legs are notably thinner. Legs always run wider
  than arms, though: the chibi shipped inverted (arms 1.3x the legs) until
  it was pointed at, and the canon chibis measure the same arm-to-leg
  ratio as the adult, about 0.7.
- **Garments.** `Outfit` carries one field per piece: tunic,
  undersleeve, belt, apron, skirt, underskirt, trousers, pouches,
  boots, plus a `skirt_length`. A garment is worn when its color is
  set, so a character states only the layers it has. Satoko wears all
  but the trousers, Satoshi swaps skirt, apron and pouches for
  trousers. A belt without an apron over it shows a buckle; pouches
  hang from the belt band, tucked inboard at chibi where the arms
  would otherwise hide them.
- **Hair.** `HAIRSTYLES` names `long_blunt` and `short_layered`, each a
  set of four outlines that agree with each other, plus an optional fifth
  giving the strands that divide the mass into locks. Two-tone with a
  waved fade boundary, placed by `_HAIR_FADE` as a fraction of the hair's
  own height rather than of the fall: the fall lengthens with the body
  while the crown stays on the skull, so one fall fraction used to come
  out at a different height per build and coloured the same character
  differently at each. It is 0.5 now, half blonde over half white, and
  moving the fade is moving that one number. The short cut measures its
  half against the hair the eye sees, since its nape and inner rim sit
  behind the jaw at every build. `hair_length` spans whatever range the cut
  defines: the long one measures the body, chin to hip, so it survives a
  change of build; the short one measures the head, a tight crop at 0 to
  a shaggy ear-length cut at 1, because the body-relative range cannot
  express hair ending above the chin at all.
- **Headroom.** `hair_margin` is the space above the skull, measured in
  head radii rather than as a fraction of the canvas, because that is
  what it measures. As a canvas fraction it was generous at a tall build
  and too small at a chibi, where the head is a third of the figure, so
  both chibis used to come out with the top of their hair sliced flat
  against the canvas edge.
- **Head.** Eight quadratics tracing a circle at the chibi end and
  narrowing to a jaw and chin as the build gets taller. The short cut's
  crown is a circular arc off the same construction, a shell 0.28 head radii
  thick over it.
- **Colors.** Skin, hair, hair tips, eyes, and every garment above.
- **Face.** `FaceStyle` carries the eye aperture (size, width,
  openness, lower lid, tilt, corner sharpness, iris size), brow tilt
  and weight, mouth curve and width, blush, and a cheek scar. Every
  default is neutral, so a character states only what it differs on.
- **Characters.** `presets.py` holds `SATOKO` and `SATOSHI`, sharing a
  palette through module constants because the two are meant to read as
  related.

Every knob above has a CLI flag, and flags override a preset one value
at a time.

## Style canon

`ref/satoko-chibi.jpg` and `ref/satoko-real.jpg` are the style canon:
the target drawing language at each end of the build range, chosen
2026-08-06. They were made by feeding the original references and our
renders to an image model and tuning toward the owner's vision, so they
are guides in spirit as much as letter; visual appeal still beats exact
match.

The satoshi pair (`ref/satoshi-chibi.jpg`, `ref/satoshi-real.jpg`) is
identity-only. It fixes his haircut, trousers and the lower-body garment
detail the satoko refs barely show (belt buckle, simple trouser lines),
but its drawing style is explicitly not the target: the per-lock
highlight sweeps, ears, articulated fingers and skin shading there do
not carry over. Render his features in the satoko language. The older
`ref/satoko.png` and `ref/satoshi.png` stay identity sources, and the
`ref/girl-chibi.png` that used to set the chibi detail bar is gone from
`ref/`; the canon supersedes it and sets a higher bar.

What the canon language is, concretely:

- Bold uniform outline that scales with the figure: measured about
  0.017 of head width at chibi and 0.023 at real. Thick silhouette over
  thinner interior lines.
- Big open rounded eyes at chibi: heavy top lash line, iris rim tone,
  pupil, two highlights. Expression lives in brows and mouth, not in
  lowered lids. Smaller and slightly lidded at real.
- Hair as wedge locks with pointed tips and interior strands, falls
  sitting in front of the shoulders, the tip fade following the locks
  rather than waving smoothly across them. *Where* that fade sits is
  ours rather than the canon's: the canon changes tone about seven
  tenths of the way down Satoko's hair and about a third of the way
  down Satoshi's, and both are half and half here, on the owner's call.
- Flat fills, hard edges, and **no shading plane on a garment at all**:
  measured in task 56, the canon's tunic, skirt, apron, sleeves and
  trousers carry no second tone anywhere, and form is on the outline and
  on line work. A second tone appears only on small elements, a pouch
  flap, a boot cuff, the turn under a hem. Ears hidden under hair on
  Satoko, though the satoshi pair does draw them. Mitten-grade hands with
  a thumb notch at chibi.
- Garment accents survive chibification: pouches with flap and button,
  a buckled belt band, boot cross-laces, a plain wrist cuff on the
  undersleeve. (The *rolled* forearm cuff appears only in the satoshi
  pair, whose style is not the target, so it stays out. The plain wrist
  cuff is on Satoko's own references and is in, the owner's call on
  2026-08-07, which also settled that Satoshi's references drive his
  haircut and nothing else about his design.)

## What is weak right now

The bar is how it looks, not how closely it matches `ref/`. Those images are
guides: they are drawn on a different figure, in `ref/satoshi.png`'s case on a
wider hip and in a slightly turned pose, so numbers lifted off them come out
heavy or splayed even when the arithmetic is right. Measure to find *what* is
wrong, then choose by eye, and note in a comment where a shipped number departs
from a measured one. A difference from a reference is not a defect on its own,
so each entry below says whether it actually looks wrong or is only a
measurement gap.

- **The waist is wider than the reference's, relative to the shoulder.**
  *Measurement gap only, does not read as wrong.* The forearm-to-waist gap
  is about 4px where `ref/satoshi.png` has 21px, but the arms hanging close
  to the body looks fine, and narrowing `waist_half_w` is a skeleton change
  touching both characters and both builds. Not worth doing on the
  measurement alone.
- **Hair silhouettes are mirrored point data, and stay that way.**
  Both cuts part off-centre in the fringe, divide into locks through
  strands and end in points, which carries the asymmetry the canon
  shows. Crown cowlick flicks (silhouette-level asymmetry) were tried
  on the short cut and reverted: they read as wobble, not tousle. If
  that is revisited, the bar is beating the plain circle by eye.
- **The realistic leg length is settled: it matches the canon.** The old
  short-legged judgment was made against `ref/satoshi.png` and does not
  survive the canon: measured, the canon's leg split sits at 0.565 of
  figure height against our 0.528, so ours are if anything the longer,
  and side by side at equal height the two figures agree. `hip_y` and
  `knee_y` stay where they are.
- **No pose variety, one outfit family.** Deliberately deferred.
- **Satoshi at chibi reads as a boy only through hair and trousers.**
  That is by design, since a shoulder-to-hip ratio is invisible at 2.4
  heads, but it does mean the two chibis are closer to each other than
  the two realistic builds are.

## Acceptance criteria

Four targets: Satoko and Satoshi, each at `chibi` and `realistic`. The
tables below are the definition of done. Style comes from the canon
(`ref/satoko-chibi.jpg`, `ref/satoko-real.jpg`); identity comes from
`ref/satoko.png` and `ref/satoshi.png`, plus the satoshi pair for his
haircut and lower body.

### How much detail each build carries

The canon sets the chibi bar, and it is higher than the old
`ref/girl-chibi.png` one: pouches with a flap and button, a buckled
belt band and boot cross-laces all survive chibification there, each
drawn as a few flat shapes. A chibi still reads through silhouette and
color banding first; these are accents on top of that, not texture.

Still out of scope at chibi: articulated fingers (a mitten with a thumb
notch is the bar), ears, skirt pleats, sleeve wrinkles, the apron's
hanging strap. At realistic the canon adds pleats on the underskirt, a
nose line, a visible neck and collar, and hinted fingers; the fingers
are optional, hand detail is explicitly deprioritized.

### Satoko

Ranked by identity carried per pixel.

| Feature | State |
| --- | --- |
| Blonde fading to white ends | done, half and half by height at both builds |
| Shoulder-length blunt hair | done |
| Guarded expression: level brows, no smile (carried by brows and mouth) | done |
| Canon eye: open rounded aperture, heavy top lash, iris rim and pupil | done |
| Cheek scar | done |
| Muted green / leather palette | done |
| Outfit color banding: green tunic, brown belt and apron, green skirt, dark underskirt | done |
| Tan long undersleeves under short green sleeves | done |
| Waist that reads: belt at the waist anchor, tunic taking in above it | done |
| Hair that reads as locks: pointed tips, strands, per-lock fade | done |
| Pouches with flap and button on the belt band | done |
| Ankle boots with a shaft rather than a brown block | done |
| Boot toe and cross-laces | done |
| Side-swept parting | done, fringe and crown strands part right of centre |

### Satoshi

Same palette and same tunic as Satoko, by design: they are meant to read
as related, so what carries his identity is hair and lower body.

| Feature | State |
| --- | --- |
| Short shaggy crop: bulk at the ear, spiked rim, nape showing | done |
| Hair that reads as locks rather than as one mass | done |
| Blonde fading to white ends | done, the pale tone crossing the fringe as the canon has it |
| Dark trousers instead of skirt and apron | done |
| Trouser leg that fills out at the thigh then runs near straight | done |
| Legs hanging under the hip, not overhanging the body's side | done |
| Green tunic, tan undersleeves, brown belt, brown boots (shared with Satoko) | done |
| Level brows, no smile | done |
| Canon eye construction (same geometry as Satoko's, his own knobs) | done |
| Belt buckle | done |
| Boot toe and cross-laces | done |
| Slimmer frame: broader shoulder over narrower hip | done, realistic only |
| Faint cheek mark | not started, and the canon satoshi pair shows none, so decide first whether it survives |
| Off-centre parting in the silhouette, not only in the fringe | settled: fringe and strands carry it; crown flicks tried and reverted |

The frame row is realistic-only on purpose. At 2.4 heads a shoulder to
hip ratio is invisible, so a chibi Satoshi has to read as a boy on hair
and trousers alone. If that turns out not to be enough, the answer is
more contrast in those two, not skeleton work.

## Next steps

`docs/gap-analysis.md` (2026-08-06) measures all four renders against
the canon and ranks what is left by how much of the style gap each
item carries. It supersedes the ranking below, which it absorbs as its
gap 8 (garment construction) and items 3 and 4 here. Its item 2, the
palette resample, all but closes on that measurement: sampled exactly
rather than from a quantised histogram, the canon's green, skin and
leather come within four points a channel of ours, which is not
visible. The one surface with anything left in it is the hair gold,
where the canon is slightly less saturated.

**The hair is the largest remaining item, and it is being rebuilt rather
than adjusted** (the owner's call, 2026-08-07). Both hair gaps have one
root: a cut is drawn as a mass carrying the silhouette, one horizontal
tone band cutting across it, and strand lines on top as decoration, while
the canon draws a bundle of locks with the tone running along each lock's
own direction. That is why Satoshi reads as an umbrella and Satoko as a
gold helmet with a white liner. So the contract changes first, to per-lock
tip regions, then Satoko's cut is re-authored on it to the silhouette
already measured, and Satoshi gets a genuinely new tousled crop from his
own reference. The pale fraction is not part of this: half and half stays,
only the boundary's shape changes.

The two canon passes of 2026-08-06 cleared the previous list; leg
length closed as already matching the canon, and the chibi arms now
hang clear of the tunic. What remains, ranked:

1. **Realistic garment details the canon shows.** The belt with buckle
   and hanging strap sits *over* the apron in `ref/satoko-real.jpg`, but
   our no-buckle-under-apron rule (right at chibi) also erases it at the
   taller build; the underskirt wants pleats there; and the short sleeve
   wants a visible cap hem instead of blending into the tunic's
   shoulder.
2. **Palette resample from the canon.** Their green and skin run a
   touch brighter and warmer; ours were sampled from the older refs.
   One-time, low effort.
3. **Satoshi's faint cheek mark, or its removal.** The old identity refs
   suggest one; the canon satoshi pair shows none. Decide first, then it
   is one `FaceStyle` value either way.
4. **Then variety.** More hairstyles and a second outfit family. The
   hairstyle registry and `Outfit` are both built to take them now.

## Direction, 2026-08-10

The ranking under "Next steps" above is from 2026-08-06 and is largely
overtaken by what happened after it: the hair rebuild, the shadow
removal, the fringe and strand fixes, and the roster growing from two
characters to fourteen with a full `Outfit` system behind them. Items 2
and 3 there closed; item 4, variety, is done in the sense that the
registries exist, not in the sense that they are populated with much
past what the fourteen presets use.

The owner's call, recorded here rather than only in conversation: the
AI-generated references in `ref/` did the job they were brought in for,
establishing the style and the initial fourteen-character roster, and
are not a target for what comes next. Effort now goes to:

1. **More GUI customization.** The `web/` page exposes a limited slice
   of what `Outfit`/`FaceStyle`/the hairstyle registry can already do;
   widen that, and add new hair/garment/prop options to the registries
   themselves where the fourteen presets don't yet exercise something a
   character might want.
2. **A bigger roster.** New characters, including ones from other games
   or stories the owner has written, designed directly as
   `CharacterParams` in `presets.py` the way the current fourteen are.
   These have no AI reference and are not measured against one; the
   design intent (written or described) is the only source of truth.
3. **Polish.** Refinement passes on what exists, judged by eye against
   the established style rather than against `ref/`.

**The one exception is the realistic build**, item 1 above the fold
("Realistic garment details") and the deferred hair-compression finding
earlier in this file: both are known, already-measured gaps against
`ref/satoko-real.jpg`/`ref/satoshi-real.jpg`, and closing them is still
in scope for the `gap-analysis` skill. Nothing else is benchmarked
against `ref/` going forward; see `CLAUDE.md`, "Direction," and
`docs/gap-analysis.md`'s scope note.

Some ideas for the three items above, not yet decided on:

- **Customization:** props (a held item, a weapon, glasses variants
  beyond the current on/off), a second outfit family (the roster plan
  already names candidates), independent recoloring of parts that
  currently share a color field, a "randomize" button on the web page
  constrained to combinations that are known to render cleanly.
- **Roster:** new characters as `CharacterParams` in `presets.py`, same
  pattern as the current fourteen, designed from written/described
  intent rather than a reference image; reuse the `Hairstyle`/`Outfit`
  registries as the menu of what's expressible before adding a one-off
  field. An explicit non-`valley_of_mist` preset namespace/roster entry
  once a second setting has more than one or two characters, so
  `sheet.py --members` and the web catalogue don't have to assume one
  cast.
- **Polish:** a second pass at palette consistency across all fourteen
  now that more of them exist side by side, expression coverage per
  character (not every preset has been checked against every named
  `Expression`), and closing whatever `docs/character-roster-plan.md`
  still lists as below the first-draft line per character.

**Order, decided 2026-08-10: the realistic build goes first**, ahead of
all three items above. The chibi build works and is locked in; the
realistic build does not, so customization/roster/polish effort would
be spent on a build that is known to be off. See the next section.

## Realistic build, 2026-08-10

All fourteen presets rendered at `--build realistic` (`out/realistic-review/`,
not committed, regenerate with `./render.sh --out out/realistic-review/<name>_real
--preset <name> --build realistic --background white` per preset) and
compared: each against its own chibi (`ref-out/`), and Satoko and
Satoshi additionally against `ref/satoko-real.jpg` and
`ref/satoshi-real.jpg`, which is the guide for the look the realistic
build is after. Strips built with the `gap-analysis` skill's `probe.sh`.
The four items below were worked in this order; results, not just
findings, since three of the four turned out different once actually
investigated rather than eyeballed.

1. **Fixed: the eye aperture was never getting the build-based lidding
   it was supposed to.** `_eye_placement` (character.py:4725) computed a
   build-adjusted `FaceStyle` (smaller `eye_openness`/`eye_lower_lid` at
   higher `sk.build`) and returned it, but `_eye()` (character.py:4660)
   read `p.face` fresh instead of taking that adjusted value, so every
   eye ever drawn used the raw, un-lidded preset numbers regardless of
   build; only the brow line, which read the adjustment correctly in
   `_face()`, ever reflected it. This is why every realistic-build face
   read too round and open next to `ref/satoko-real.jpg` and
   `ref/satoshi-real.jpg`: the constants tuning it were always inert.
   Fixed by passing the adjusted `FaceStyle` through, and while there,
   measured the two references directly (pixel grid by eye, since the
   automated `eyes` probe finds the iris highlight dot on this art
   rather than the aperture, a new addition to `PITFALLS.md`-worthy
   failure modes) and retuned the reduction from `0.20`/`0.10` to
   `0.40`/`0.20` to land on the reference's roughly 2.2:1 aperture
   aspect ratio against the chibi's 1.4:1. Confirmed the chibi is
   unaffected in any visible way (`sk.build` is 0.1 there, not exactly
   0, so this does move the chibi's eyes by sub-pixel amounts;
   `ref-out/` was refreshed to absorb it, see `cmp_satoko_guide2.png`
   for the before/after against the same chibi crop). Every preset's
   realistic build reads noticeably more mature after this one wiring
   fix than any of the other three items below would have delivered.
2. **Investigated, not fixed: hair volume compression at the realistic
   build needs either a geometry refactor or a new trace, not a
   constant.** The first attempt (scale the crop's fringe depth by the
   same `v` that scales its crown) was wrong: `_CROP_BASE_TIP` is
   calibrated so `v` is already ~1.0 at the realistic build (that is
   the trace's own reference scale) and only inflates at the chibi end,
   so scaling the fringe by `v` left the realistic build unchanged and
   made the chibi's fringe measurably deeper — caught by
   `test_ref_out_matches_the_code` failing on `satoshi`/`tomohiro`
   after the edit, and reverted. The real fix needs the crown's
   available headroom decoupled from the outline's single scale factor
   (which also controls tip depth), or a fringe traced directly off
   `ref/satoshi-real.jpg` the way the chibi one came from
   `ref/satoshi-chibi-fringe.png`. Both are real pieces of work, not
   available in this pass; the measurement stands (crown-to-hairline
   band 1.035 head radii at chibi, 0.683 at realistic, fringe blade
   length fixed at 0.506 either way) and is the starting point for
   whoever picks this up.
3. **Investigated, mostly not a bug.** Haruto's hakama appearing to
   swallow his legs entirely was a false alarm: `hakama_color`
   (`#2b2b26`) and `trouser_color` (`#2b2b27`) are one hex digit apart
   by design (the preset's own comment says so), so the actual gap
   between hem and boot is there at both builds, just invisible because
   the two garments read as one fabric. Reika's case is real and
   confirmed numerically (`_skirt_hem_y` vs. the boot's `top_y`): the
   hem clears the boot at chibi (435.9 vs. 457.8) and runs into it at
   realistic (454.9 vs. 435.0), with zero leg showing at the realistic
   build (`out/realistic-review/hakama_recheck.png`). But
   `hakama_length=0.95` is deliberately near-floor-length, and a real
   floor-length garment on adult proportions plausibly does drape onto
   the shoe with no gap. Whether that reads as intended or as a
   collision is a look call, not a bug with an obvious fix, so it needs
   the owner's eye on `hakama_recheck.png` rather than a guessed rule
   like "always clear the boot by X."
4. **Investigated and closed: not a regression.** The impression that
   Daizen and Reinhard's beards merge into their collars at the
   realistic build did not hold up numerically: beard-bottom against
   `shoulder_y` for Daizen actually clears by more at the realistic
   build (~4px above the shoulder line) than at chibi (~10px past it,
   already overlapping), because `beard_length` is a fixed head-radii
   drop while the neck itself gets visibly longer at taller builds. The
   "merged" read was the small scale of the head-only crop making the
   sideburn-to-collar transition hard to parse, not a build-dependent
   defect; `_face_track`/`_jaw_track` already carry the beard's edge
   correctly at both builds. Found and fixed a real but unrelated stale
   comment along the way: `CharacterParams.beard_length`'s docstring
   claimed Reinhard wears 0.15 and Daizen 0.45; the actual preset
   values are 0.07 and 0.17.
5. **The uniformed and coated cast hold up well, unchanged.** Tenno,
   Viktor, Reinhard's uniform, Elara and Krista's crystal rig, Keiko's
   lab coat, and Kyoko/Tomohiro's coat-over-tunic all still scale
   cleanly to the realistic build.
6. **Fixed: the belt buckle now shows at the realistic build with an
   apron on.** The old rule in `_belt` (character.py:3948) suppressed
   the buckle outright whenever an apron was worn, on the reasoning
   that the apron covers it, true of `ref/satoko-chibi.jpg` but not of
   `ref/satoko-real.jpg`, which shows the buckle sitting clear above
   the apron with the strap's tail running down over the panel. Gated
   the buckle on `sk.build > 0.5` (the same cut the chibi-only nose
   already uses) rather than dropping the rule, so it still hides at
   chibi and shows at realistic, together with the existing tie. First
   attempt at this broke the tie for every obi-wearing, apron-less
   character (Daizen, Haruto, Reika) by tying the tie's presence to
   "has an apron" instead of "buckle isn't carrying the belt alone";
   caught by `test_ref_out_matches_the_code` failing on all three, and
   by the tail's own drop distance quietly changing for everyone else
   once the two branches shared a variable that meant different things
   in each (`knot_h*0.7` for where a drawn knot's own box ends is not
   `knot_h` for where the tail's drop is measured from). Both caught
   before landing; `ref-out/` now differs only where it should,
   `real/satoko` and `real/chiyo` (the two apron-wearing presets),
   confirmed by `./refresh-ref-out.sh --check` coming back clean
   everywhere else.
7. **Already done, contrary to what item 6 in "Next steps" above still
   claimed.** Checked underskirt pleats and the sleeve's cap edge
   against `ref/satoko-real.jpg` directly rather than trusting that
   older note: both are already drawn (pleats: task 66; the sleeve's
   cap already carries a distinct pointed edge, not a plain blend into
   the shoulder). The pleat count and spacing read close to the
   reference; the underskirt's hem is a smooth curve where the
   reference scallops between pleats, and the sleeve's cap is more
   ornate (a pointed zigzag) than the reference's plain rounded one.
   Both are minor stylistic gaps, not the "missing entirely" gap the
   old note described, and neither seemed worth a change without the
   owner's call on which look is wanted.

Net for this pass: two real, confirmed fixes shipped (item 1, eye
lidding, and item 6, the belt buckle, both gated on `sk.build` so the
chibi is untouched); one item that needs more scoping than a session
affords (item 2, the crop fringe); two items that looked like bugs
from a screenshot and were not, once measured (items 3's Haruto half
and 4); one still genuinely open and owner-facing (item 3's Reika
half); and one correction to a stale "still open" claim (item 7).
Suggested next step, if continuing here: item 2's fringe work, since
it is the remaining shared-code lever; otherwise this list is spent
and the direction section above (customization/roster/polish) is next.
(Item 2 is done, 2026-08-11: see the section below.)

## Realistic build, 2026-08-11

Item 2 above got the trace it needed: `rhedak/real_builds` (`93463eb`)
adds a real, direct trace of both `ref/satoko-real.jpg` and
`ref/satoshi-real.jpg` (`harness/trace/real/satoko_real.py`,
`satoshi_real.py`), used at the exact `fall` value each was measured
at instead of stretching the chibi contour past where it was ever
measured to go. Compared the new renders against `main` and against
both references with the `gap-analysis` skill's `probe.sh`.

A code review of that commit before this comparison found and fixed
three real defects that shipped alongside the trace, none of them
visible from a glance at the golden PNGs:

1. **Fixed: Satoko's pale-tip lift used a chibi-relative scale factor
   against a contour that no longer scales that way.** `_long_scaled`
   switches to the fixed real trace at Satoko/Kyoko's `fall`, but
   `_long_traced_tip_edge` still multiplied its lift by `fall /
   _LONG_BASE_TIP`, a factor that only means something against the
   chibi contour's own stretch. Added `_LONG_REAL_TONE_LIFT`, a
   separate constant for the real branch. Picked by rendering a sweep
   (0, 0.3, 0.62, 1.06, 1.6, 2.4) rather than by formula: every
   nonzero value poked a small gold wedge through the pale at the foot
   of one fall or the other, a six-samples-per-segment threshold
   artifact against the fade clamp rather than something that moves
   smoothly with the constant, and 0 was the only value clear of it on
   either side.
2. **Fixed: Satoshi's realistic crown painted a few antialiased pixels
   into row 0 of the canvas.** `_CROP_REAL_SCALE`'s comment compared
   the crown's apex only against the full `hair_margin` ceiling, not
   against the ceiling minus the outline stroke's own outer half that
   `hair_margin`'s own comment says it has to clear. `1.03` cleared
   the wrong number. `1.005` clears the real one, confirmed by reading
   the exported PNG's own top row back rather than trusting the
   arithmetic alone, since antialiasing bleeds the stroke a pixel or
   so past its analytic centre.
3. **Fixed: the real trace's dispatch had no build or identity guard.**
   Both `_long_scaled` and `_crop_outline` switch to the measured trace
   on a bare `abs(fall - target) < tolerance` check. At 0.05, Krista's
   own `fall` (a different `hair_length` on the same `long_traced` cut)
   drifted into Satoko's window at some `--heads` values away from
   6.0, silently swapping in Satoko's hair. Tightened
   `_LONG_REAL_TOL` to 0.001, tight enough to still catch Satoko/Kyoko
   at exactly `--build realistic` and to shrink Krista's (and Keiko's)
   accidental windows to a few thousandths of a head, well past
   anything typed by hand.

Two related questions went to the owner rather than being decided in
code: **left as-is**, `BASE_MALE`'s `hair_length=0.65` matching
Satoshi's exactly, and so inheriting his measured trace at the
realistic build, the same sharing Kyoko and Tomohiro already do on
purpose; and **left open, undecided by design**, the fact that the fix
only covers `--heads` at (almost exactly) 6.0, so a taller custom
build still falls through to the pre-fix chibi-scaled crown and its
crossing lines. Extending the real trace's own tips further for taller
builds was the alternative on the table; the owner's call was to
tighten the match instead and leave taller builds a documented gap
rather than invent geometry no reference measures.

Against the references, with the review fixes in: Satoko's crown no
longer crosses itself and now follows a natural, photo-close parting;
Satoshi's crown-to-fringe headroom is now the measured proportion
instead of the reused chibi one. The comparison also turned up a real
bug in the trace itself, since fixed:

**Fixed: Satoshi's realistic hair stopped above both ears instead of
framing the head down to the jaw.** First read as strand lines
crossing the ear silhouette, a rendering-layer problem; it was not.
`ref/satoshi-real.jpg` draws a sideburn tuft below each ear as a few
small pointed locks with no hair-coloured pixels joining them to the
crown mass, so `harness/trace/real/satoshi_real.py`'s single seed near
the crown never reached them (checked directly: a fresh flood fill
from a pixel inside either tuft gives a blob a few hundred pixels
wide, nothing like the ~14000-pixel main mass). The resulting
silhouette stopped at the ear on both sides, worse framing than the
chibi-scaled shape it replaced, which happened to reach nearly to the
jaw already (0.86 head radii on the side against the real trace's own
0.36) and read fine (the owner's own check: "our chibi satoshi already
has hair properly framing his face"). Four more seeds, two per side
since each side's tuft is itself two separate blobs, fixed the trace
at the source; `_CROP_REAL_EDGE` grew from 23 segments to 42 and now
reaches the jaw on both sides, `_CROP_REAL_TEMPLE_L/R` and
`_CROP_REAL_CROWN_AT` moved to the same anatomical points at their new
indices.

That alone still read as too weak once rendered: most of both tufts
landed *behind* `_head`'s own skull shape, which is drawn over the hair
and paints right over whatever falls inside its edge. Checked directly
against `_head_edge_x` rather than assumed: several of the tuft's own
points sit inside the skull's edge, not outside it, and several more
clear it by only a few hundredths of a head radius, thin enough to read
as a broken scribble rather than visible hair. This is the same problem
`_EAR_OUT` already exists to solve for the ear, and it got the same
fix: `_CROP_REAL_SIDEBURN_PUSH` pushes each tuft's own points further
out from the head centre, x only, so the traced shape clears the skull
instead of mostly hiding behind it. Scoped to exactly the new segments
(edge indices 0-7 left, 32-41 right); the already-fine trace in between
is untouched.

Owner's eye caught a second round: even with that push, the hair and the
ear still visibly fought each other right at the ear. Pushing the tuft
out had moved a few of its points from inside the ear's own outline,
correctly leaving it visible, to level with it instead, and separately,
a few points from the *original* trace (not the new tuft, the
pre-existing zigzag right above the ear noted as a "minor blemish" and
left alone the first time) sit in that same strip on their own, push or
no push. Both are one problem: `_ears` only draws the sliver standing
clear of the skull, from the skull's own edge out to `_EAR_OUT`, within
`_EAR_TOP_Y` to `_EAR_BOT_Y`, and several of the mass's points, at
exactly that height, land inside that same narrow strip, so the hair's
outline and the ear's outline were drawing into the same few pixels
regardless of the push. `_crop_real_point` now retreats any such point
to the skull's own edge (`_head_edge_x`, computed directly, hardcoded at
the realistic build's own `1.0` since this trace never runs at any
other), ceding the strip to the ear the same way the fringe already
cedes it higher up. Points at ear height but already clear of that
strip are left alone. Confirmed by rendering both sides at 5-6x: the ear
now shows a visible sliver of its own rim on the side that had none
before, and the tangle is markedly reduced, though not perfectly clean,
the raw zigzag's sharp turns still add some density even where they no
longer overlap the ear outline. Good enough to stop chasing by hand;
further cleanup here is re-trace territory (a coarser or re-seeded pass
specifically over the ear-height band), not another point-by-point
patch.

**That retreat was the wrong read of the reference, per the owner.**
`ref/satoshi-real.jpg` does not leave the ear in a clean skin-only
window; the hair runs on past it, behind it, and the ear sits in front
of that, poking out of a continuous mass rather than out of a gap in
one. Retreating the mass to the skull's edge at ear height fixed the
tangle by removing the hair that should have been there instead of by
fixing how it met the ear. `_crop_real_point` now pushes *out* at ear
height instead of back in, past the ear's own outer edge with a margin
(`_CROP_REAL_EAR_MARGIN = 0.1`, picked by rendering 0 to 0.2 and reading
the results the same way `_CROP_REAL_SIDEBURN_PUSH` was) so the ear's
own fill fully covers the seam between them rather than the two outlines
meeting at it. Confirmed at 4x on both sides and at full figure size:
hair now runs continuously behind the ear the way the reference does,
the ear still reads as its own shape in front of it, and the earlier
"clean gap" version's thin-at-the-ear look is gone.

**One side of that push left a real hole, caught by the owner on
Satoshi's own left ear specifically.** Pushing to the floor only exactly
within `_EAR_TOP_Y`/`_EAR_BOT_Y` left a sharp step at the boundary
wherever the last point outside it was not already close to the floor:
on that side
the last unpushed point stood at 0.886, the first pushed one right after
it at 1.072, and that single segment's curve folded back on itself
rather than bulging smoothly, a self-crossing path rather than a
rounding error, and left a small triangle of bare canvas exactly at the
fold, easy to miss at a glance since it sits inside the hair mass rather
than on its outer silhouette. The other side had no visible hole only
because its own last unpushed point happened to already sit close to the
floor, not because the underlying logic was any safer there.
`_CROP_REAL_EAR_BUFFER` extends the floor a little above and below the
ear's own height, so the point that used to make the jump gets pushed
too and the step disappears on both sides; picked as the smallest buffer
that rendered with no such hole on either side, checked at 4x.

What is still open, ranked:

1. **Checked, kept as-is: `_LONG_REAL_SCALE=1.2`.** At a tight 3x head
   crop it reads wider than `ref/satoko-real.jpg`'s closer silhouette;
   rendered 1.0/1.1/1.2 side by side at full figure height to check
   whether that held up away from the zoom, and at that scale, the
   scale a viewer actually sees this at, the three barely differ and
   1.2 does not read as wrong. The 3x crop was overstating a subtle
   effect. No change.
2. **Garment details against `ref/`** (this file's "Next steps" item 1,
   `docs/gap-analysis.md` gap 8, unchanged by this pass): Satoshi's
   sleeves are plain to the wrist where the reference rolls a
   three-quarter cuff; Satoko's skirt is flat where the reference
   tiers. Lower priority under the 2026-08-10 direction call, which
   points most effort at customization/roster/polish rather than more
   reference-chasing.
3. **Reika's hakama still meets her boot with no leg showing** (item 3
   above, unchanged, still the owner's call).

Net for this pass: item 2 from 2026-08-10 is done, four real defects
in the commit that did it are fixed (three in the code review, one in
the reference comparison that followed), two questions the code review
raised went to the owner rather than being guessed at, and Satoshi's
realistic build now properly frames his head the way the chibi build
already did. Suggested order: item 1 above is a cheap side-quest;
items 2 and 3 stay where the 2026-08-10 direction call put them.

Items 2 and 3 above were picked back up the same day, on the owner's
go-ahead. One of the two halves of item 2 turned out not to be work at
all.

**Retracted rather than built: Satoshi's rolled sleeve cuff.** Gap 8
names it, but this file's own "Style canon" section already settled
the question on 2026-08-07: the rolled forearm cuff "appears only in
the satoshi pair, whose style is not the target, so it stays out," the
same call that keeps his references to his haircut, trousers and belt
buckle and nothing else about his design. Gap 8 either predates that
call or missed it. Drawing the cuff would mean reopening a decision
already on the record rather than closing a gap, so it is not built;
this half of item 2 is struck rather than done.

**Satoko's skirt tiering, built, and the first reading of the
reference was wrong.** The first attempt scalloped the underskirt's
hem into a small dip under each pleat, several teeth across the whole
width. Rendered against `ref/satoko-real.jpg` rather than trusted by
eye off the crop alone, that was visibly the wrong shape: the
reference's hem is one continuous shallow sag between its two rounded
corners, not a row of scallops, the fabric dipping once in the middle
the way a hem actually settles under its own weight. `_skirt_path`
grew a `scallop`/`scallop_dip` pair (0 keeps every existing caller's
flat line, unchanged silhouette everywhere but `_underskirt`), and
`_underskirt` calls it with two peaks, the same two points the
existing corner curves already land on, and one dip between them.
Depth is `_UNDERSKIRT_SCALLOP_DIP`, picked off a render sweep the same
way `_CROP_REAL_EAR_MARGIN` was: 0.018 of the hip-to-ankle span barely
read as a fold, 0.045 and 0.06 sagged deep enough to look heavy under
the pleat lines above it, 0.03 matched the reference's own depth.
Gated on the same `hem_y - skirt_hem > stroke*4` check the pleat lines
already use, so it only shows where the band is deep enough to hold a
wave and the chibi, where that band is a few-pixel sliver, is
untouched: `./refresh-ref-out.sh --check` came back changed only for
`real/satoko`, the one skirt-wearing preset the byte check tracks.
Checked directly on Chiyo (also skirt-plus-underskirt) at the
realistic build too, since nothing pins her render byte for byte;
reads the same. Keiko's skirt shares the code path but is worn under a
full-length coat that hides it at every build, so there was nothing to
check by eye there.

**Reika's hakama, checked and kept as-is.** Rendered at the realistic
build and read at 3x zoom right at the hem-to-boot boundary, the exact
test this file's own note called for: a collision would cross the two
outlines mid-shape and leave a notch or an X, and this does not, the
hem's own rounded corner simply runs down to the boot's own top edge
in one unbroken line, both boots reading as tucked under the hem
rather than fought with it. That is drape, not a defect, so
`hakama_length` is untouched; the earlier finding (hem meets boot with
zero leg showing) stands as a description, not as a bug report.

Net for this second pass: item 2 splits into one retraction (the
Satoshi cuff, contradicted by a standing call rather than open) and
one real fix (Satoko's underskirt hem), and item 3 closes as checked,
kept as-is, the same shape as item 1's scale check. Nothing here
touches the chibi: `./refresh-ref-out.sh --check` differs only in
`real/satoko`.

**All fourteen now have a realistic render checked in, the owner's
call the same day.** `presets.REALISTIC_REFS` was a short list of two,
Satoko and Satoshi, the only pair ever measured against a reference;
it is `tuple(PRESETS)` now, so a new preset gets a `ref-out/real/`
render the same way it already gets a chibi one, with no second list
to remember. `./refresh-ref-out.sh` wrote the twelve new files
(`daizen`, `elara`, `haruto`, `keiko`, `krista`, `kyoko`, `reika`,
`reinhard`, `tenno`, `tomohiro`, `viktor`, and `chiyo`); Satoko and
Satoshi's own `real/` renders were untouched, since nothing about their
shapes changed here. Looked at each of the twelve by eye rather than
just trusting the smoke test: nothing broken, no clipped canvas edge,
no crossed outline. This is a publishing change, not a judgment: the
other twelve have not been measured against anything, `ref/` has no
realistic-build reference for any of them, and the README keeps showing
the chibi only. Updated everywhere else this tuple was described as a
short list: `refresh-ref-out.sh`'s own comments, `README.md`,
`docs/api.md`, `docs/web-gui-plan.md`, and a follow-up note in
`docs/character-roster-plan.md`'s decision log rather than rewriting
its 2026-08-08 entry.

**Asked to trace `ref/satoshi-real.jpg`'s eye and match ours to it,
which turned into gap 10 of `docs/gap-analysis.md` and stopped there,
per that skill's own "analysis, not a shape pass" rule.** First pass
computed our own aperture from `_eye_placement`'s formula and got an
aspect of 2.17, matching the 2.2 the 2026-08-10 eye-lidding fix quotes
for both references, and concluded there was no gap. The owner asked
for Satoko to be measured the same way before deciding anything, which
is what turned up the actual finding: measured on both references with
a consistent ink-to-ink convention (not the path centreline, which
undercounts the stroke), Satoshi's aperture is 1.4 and Satoko's 1.6, not
2.2 on either. Height alone matches both references within noise, so
the 2026-08-10 fix's shipped height numbers hold up; width is 60% to
90% too wide on both characters and visibly so on a matched-scale strip
crop (`out/eyecheck2/`, not checked in), which is what the too-round
look actually traces to, not the height. The undersized-looking iris
follows from that: `iris_r`'s governing term is the aperture height,
correctly sized, competing against a width term that is not, so it
comes out sized for a narrower eye than the one drawn around it.
Nothing here touches `iris_size` (0.72, gap 6's deliberate call) or the
chibi (`_EYE_ASPECT`, `eye_dx`, both unchanged and rechecked).

**Decided and shipped the same day: match `ref/satoko-real.jpg`, "as I
like them the most."** `_eye_placement` grew a build-gated `eye_width`
reduction alongside the existing height one, and two wrong values
shipped before the right one, both from the same mistake: measuring ink
on a render instead of computing the path.

Solving the ratios directly by matching our ink width to the
reference's ink width does not work: a stroke bulges past a sharp
corner by roughly its own width no matter how narrow the underlying
path is, so past some point the number being matched is the stroke, not
the aperture, and a reduction near 0.99 renders as a black sliver with
no almond left. A render sweep chosen by eye against that same
ink-corrupted signal, in a tight one-eye crop, landed on 0.50 instead,
and that shipped first. **The owner caught it**: overlaid full-face
against the reference, it looked worse, not better, and reading the
emitted SVG path directly showed why: the aperture at 0.50 comes out
10.1 x 10.1, aspect 1.0, rounder than the ungated value it replaced, not
flatter. A crop tight enough to fill the frame with one eye made a
uniformly-shrunk circle look like a narrowed almond; only the full-face
comparison the owner asked for showed it wasn't.

`_eye_shape`'s aperture is closed-form, so there was never a need to
measure ink. Solving `2w / (top + bot) = 1.6` (Satoko's own measured
aspect, `top + bot` the height, already confirmed close and untouched)
for the reduction gives 0.21, confirmed by reading the path's own bounds
(16.1 x 10.1, aspect 1.59) rather than a raster, and by the same
full-face overlay this time holding up. Checked by eye across all
fourteen presets' realistic renders after landing on 0.21, plus both
neutral web-gallery bases: no clipping, no pinched corners, no collision
with Keiko's glasses. Confirmed sub-pixel at chibi either way
(`sk.build = 0.1`, not 0, same situation the height reduction already
lives with). Satoshi's own reference wants narrower still (1.4 against
Satoko's 1.6) and stands as a named residual against his own photo, on
the owner's steer toward Satoko specifically rather than an average of
the two; not a second knob. `./refresh-ref-out.sh` and
`./refresh-bases.sh` both had to run, since `eye_width` reaches the two
neutral web-gallery bases the same way it reaches every preset; ruff and
`pytest -q` (346 passed) are green after.

**Also the owner's call the same day: the upper and lower half-circles
of the eye outline now carry the same weight.** `_eye()` used to redraw
the upper lid heavier than the rest of the aperture, `sw * 1.6` over
`sw * 0.85`, the canon's own heavy-lash-line convention (see gap 6's
notes on it). Both are now `sw * _EYE_OUTLINE_W` (0.85), a new module
constant rather than two call sites repeating the same literal, at both
builds since neither read is build-gated. Checked at chibi and
realistic on Satoko directly and across the rest of the roster on the
chibi strip: reads as one even line around the aperture rather than a
thick brow-like arc over a thinner rim. `./refresh-ref-out.sh` and
`./refresh-bases.sh` both ran again; ruff and `pytest -q` green.

**Asked next to match `out/real/satoko.png`'s mouth and nose to
`ref/satoko-real.jpg`, done the same day.** Applied the lesson from the
eye-width mistake immediately rather than after a wrong first shot: read
both features off the reference at the same head-radius scale the eye
fixes validated, from the emitted path/formula rather than off a raster,
and checked full-face before touching anything.

The mouth's *position* needed nothing: the first pass forgot to subtract
the reference photo's own top margin before dividing by figure height
(the exact `PITFALLS.md` mistake this file already had written down),
which made `mouth_y` and the nose's `nose_y` look 15-20% too high on the
face. Redone with the figure's actual ink top (36px, giving H = 1112,
matching the tool's own number), both landed within 2% of the
reference, already correct, unchanged.

Width was real. The mouth measured about 0.334 head radii across on the
reference against our own 0.18 (`0.12 * mouth_width * 2` at Satoko's
0.75), a 1.86x gap. `_MOUTH_REALISTIC_WIDEN = 0.85` widens it at higher
`sk.build` the same way the eye's width reduction narrows the aperture,
landing at 1.85x at full realistic build and left alone at chibi
(`0.12 * mouth_width` is a per-character value already, never measured
against a reference at chibi, which stays locked in). Checked the chibi
delta directly rather than assumed: 2px wider on a ~1000px canvas,
smaller than the eye fix's own accepted sub-pixel move.

The nose was a different construction, not just a size gap. The old
single stroke, "leaning off to one side," turned out not to be a
simplification of the canon's nose so much as half of a different one:
`ref/satoko-real.jpg` draws a nostril shadow as two short mirrored
marks, each angling down from an outer point near the brow line to an
inner point just short of centre, close to touching but not quite.
Rebuilt as two strokes instead of one, measured off the reference the
same way (outer end 0.094 r from centre, inner end 0.028 r, 0.033 r
drop). Both changes are shared across every preset, since neither the
mouth stroke nor the nose was ever per-character beyond `mouth_width`
and both are already build-gated (the nose only drew past `sk.build >
0.5` to begin with); checked Daizen and Reinhard's moustaches, which
cover this part of the face entirely and read unchanged, and the rest
of the roster on a realistic-build strip: no collision, no clipping.
`./refresh-ref-out.sh` and `./refresh-bases.sh` both ran; ruff and
`pytest -q` (346 passed) green.

**Followed immediately by: the owner's eye caught that position still
needed work, after this file had just called it close.** The mouth's
position had been read as already correct via mouth_y as a fraction of
figure height H, which turned out to be the wrong normalisation for a
facial feature: H includes hair and body, and this reference's hair
height as a fraction of H does not match ours, so a mouth that lands at
the right H-fraction can still sit wrong relative to the skull actually
drawn under it. Re-derived as a fraction of the eye-to-chin span
instead, using only landmarks read off the same image on each side (no
cross-image scale assumption): that framing needed a chin position, and
the chin did not have one stable reading to give it, tried three times.
The jaw's outline on this reference is open at the bottom centre, skin
tone running straight into the neck with no line between them, and each
attempt to find a "chin" instead found something else: the collar's own
V-neck (a true taper to a single pixel, the tell this file's own
`PITFALLS.md` already names), then a point 27px lower down the neck
past where the jaw actually ends. Abandoned the arithmetic and picked
both `_MOUTH_REALISTIC_DROP` and `_NOSE_REALISTIC_DROP` (0.18 each, same
value so their already-correct spacing from each other does not change)
by a render sweep against the reference at matched scale instead,
`_face()` call-site additions again, `_MOUTH_Y` and the nose's own
`0.36` untouched.

That surfaced a real collision the width and shape changes had not: the
beard's own mouth-hole ellipse (`_beard`, skin-toned, cut into the fur to
show the lip) reads `_MOUTH_Y` directly, so once the actual mouth stroke
moved out from under it at the realistic build, Daizen and Reinhard
rendered with a stray dark line inside the fur below an empty hole.
Fixed by moving the hole's own `cy` by the same `_MOUTH_REALISTIC_DROP`;
its width already cleared the mouth's realistic-build widening without
needing the same treatment. Caught by rendering and looking directly at
the mouth region on both bearded presets, not by the smoke tests, which
have no assertion that would have caught two shapes drifting apart like
this. Confirmed the chibi move is small (3px on a ~970px canvas, the
nose untouched there since it never draws below `sk.build > 0.5`),
re-checked the full roster on a wider strip after the beard fix, and
`./refresh-ref-out.sh` / `./refresh-bases.sh` / ruff / `pytest -q` (346
passed) all green again.

**Asked for a gap analysis of the eyes specifically, which became gap
11, then asked to act on all three of its findings the same day: "the
reference's eyes look warm and sharp, ours look dead and boring."**
Landed as three build-gated changes, each picked by render sweep
against `ref/satoko-real.jpg` rather than solved from a ratio alone,
gap 10's own lesson.

1. **Eye spacing.** `eye_dx` (`r * 0.46`, gap 6's own chibi canon
   measurement, never build-gated) now carries `* (1.0 - 0.27 *
   sk.build)`, landing on Satoko's measured eye_dx-to-aperture-width
   ratio. Reopens gap 6's chibi call the same way gap 10's width fix
   reopened the aspect reading; the owner's explicit go-ahead this time
   covered it directly.
2. **Corner sharpness.** `eye_corner` doubles at full build
   (`* (1.0 + 1.0 * sk.build)`), landing Satoko's 0.45 at 0.90; past
   about 1.0 in the sweep it read as a point rather than a corner.
   Satoshi's own reference is rounder than hers, so his doubled value
   overshoots his own photo a little, the same anchored-to-Satoko
   tradeoff as the width fix, not a new one.
3. **Pupil size.** `_eye()` grew a `pupil_ratio` parameter (default
   0.40, the old literal, so every other caller is unaffected) and
   `_face` passes `0.40 + _PUPIL_REALISTIC_GROW * sk.build`,
   `_PUPIL_REALISTIC_GROW = 0.10`. This one is global, not
   per-character, the one place in this pass where a fix touches every
   preset's eye construction rather than riding a value that was
   already per-character or already build-local.

All three checked full-face against both references, not just tight
eye crops (gap 10's other lesson), and across the whole roster at the
realistic build: no collision with Keiko's glasses, Daizen's or
Reinhard's beards, or either scar mark. Chibi confirmed sub-pixel for
all three. `./refresh-ref-out.sh` and `./refresh-bases.sh` both ran;
ruff and `pytest -q` (346 passed) green.

**Then asked, the same day, to break from the reference on purpose:
slightly bigger eyes.** Not a gap-analysis item, since there is no
reference number to chase when the owner's own taste is the target.
`eye_r`'s realistic-build shrink went from 0.22 to 0.12 (`r * 0.26 * (1.0
- 0.12 * sk.build) * f.eye_size`, was `0.22`), picked by render sweep
(0.22 down to 0.00) for "slightly larger" without the two eyes crowding
each other or the brow. Checked the same way as everything else in this
pass: full-face against both references (still visibly close to them,
just a size step past what either draws), the whole roster for
collisions, chibi delta under half a pixel. `./refresh-ref-out.sh` and
`./refresh-bases.sh` ran; ruff and `pytest -q` (346 passed) green.

## Web tool: realistic build and mouth width, 2026-08-12

Proposed after the eye/mouth/nose passes above: let the web tool select
the realistic build (chibi stays the default), expose eye/nose/mouth
there, and, as a later item, more eye styles. Agreed with the shape of
it, flagged one interaction to check before shipping, and one piece
(nose) that turned out not to be exposable yet at all.

**Shipped:** `catalogue.py` grew a `BUILD` select (`heads`, "Chibi" /
"Realistic", chibi default) and `mouth_width` joined `FACE_RANGES`.
Reopens the 2026-08-10 "chibi only" call on purpose, recorded as a
reopening rather than a rewrite in `docs/web-gui-plan.md`: the call
stands as an accurate record of why realistic was off, and the passes
since then are what changed. No bridge change was needed. `heads` was
already a `CharacterParams` field the state object round-trips
end to end regardless of whether any control ever wrote to it, so the
web layer's own "learns no geometry" rule holds without a single new
line in the Python bridge.

**The interaction flagged before starting turned out fine, checked
rather than assumed.** `eye_corner`'s committed range (0.30-0.65)
becomes an effective 0.60-1.30 once `_eye_placement` doubles it at the
realistic build. Rendered it directly rather than lowering the ceiling
on the strength of the arithmetic alone, gap 10's own lesson: 0.65
renders a sharp but intact corner at the realistic build, not a
self-intersecting one, and the "malformed combinations are the
visitor's own responsibility" call in `docs/web-gui-plan.md` already
covers a corner sharper than either reference draws. Checked the other
four ranges' own extremes at the realistic build the same way while at
it, since none of them had been rendered at that build before either;
all clean. Left the range alone.

**Nose is not "expose it," it is "there is nothing to expose yet."**
Unlike eye and mouth, nose carries no `FaceStyle` field at all: it is
fixed shape logic with no per-character variation. Left as its own
follow-up rather than folded in here, since it means designing a
parameter first, not just adding a line to `FACE_RANGES`.

**Tested end to end**, not just reviewed: staged the site with
`web-stage.sh`, served it locally, and drove a real headless Chrome
against it with Playwright (installed ad hoc via `uv run --with
playwright`, not added to the project's own dependencies). Confirmed
the build select offers exactly "Chibi"/"Realistic", picking Satoko
then switching to Realistic changes the rendered SVG, the mouth-width
slider appears and renders at its catalogue maximum together with
Realistic, and picking a different starting point resets Build back to
chibi. No console or page errors. `docs/web-gui-plan.md`'s own
"machine has no browser and no route to the Pyodide CDN" caveat did not
hold on this machine; recorded there rather than left stale.

`ruff`, `ruff format`, `pytest -q` (350 passed, 4 new: `BUILD`'s field
check, its options matching `BUILDS` exactly, and one render test per
option), and `./refresh-catalogue.sh --check` all green.
`./refresh-ref-out.sh --check` and `./refresh-bases.sh --check` also
green and untouched, correctly: nothing here changed `character.py`.

Eye styles (anime vs. realistic as discrete, swappable constructions)
stayed a later item, as agreed going in: the natural template is an
`EYESTYLES` registry mirroring `HAIRSTYLES`'s existing pattern, a
different shape of change from tuning ranges on the eye construction
that exists now, and bigger than this pass.

## Eye styles: `EYESTYLES` and the anime construction, 2026-08-12

The "later" item above, the same day. Asked to design a "classical
anime" eye style off `ref-local/anime-chibi.png`, prototyped it by
monkeypatching `_eye` in a throwaway script rather than editing
`character.py` directly (this project's own render-and-look rule, kept
even for a design pass with nothing committed yet), iterated against
the reference until it read right, then asked to make it real.

**The reference's construction turned out to be a different shape, not
a retuning of the existing one.** No separate pupil: the iris reads as
one dark body. The "glossy" look is two flat, off-centre highlights
standing in for a reflection, not `_eye_realistic`'s concentric rings:
a warm crescent low in the iris and a cooler, larger one toward the
temple, mirrored by `side` the same way everything else in this file
already mirrors. Rounded corners and a big, nearly aperture-filling
iris are not new geometry either, just `FaceStyle` numbers the
realistic construction never gets set to (`eye_corner=0`,
`iris_size≈0.90`, generous `eye_openness`/`eye_lower_lid`). The
aperture itself, `_eye_shape`, is unchanged and shared by both styles.

**Shipped as `EYESTYLES`, a plain `dict[str, Callable]` keyed the way
`HAIRSTYLES` keys hairstyles**, since an eye, unlike a haircut, is one
callable rather than several that have to agree with each other; no
wrapper dataclass earns its keep here. `_eye` renamed to
`_eye_realistic`; `_eye_anime` is the new one. `FaceStyle` grew
`eye_style: str = "realistic"` (so every existing preset's own
`ref-out/` stays byte-identical, confirmed by `refresh-ref-out.sh
--check` after) and `eye_glow: float = 1.0`.

**`eye_glow` is the control the owner asked for, in the same
conversation that saw the design**: "make the inner glow... smaller or
turn it off entirely." Multiplies the radius of `_eye_anime`'s two
secondary highlights only, not the one main highlight, whose own
comment says turning *that* off would read as unlit rather than merely
less glossy. At 0 the two glow circles have zero radius, which draws
nothing, a clean off rather than a special case. Confirmed by render
sweep (0.0 / 0.5 / 1.0): 0.0 leaves one flat highlight on a dark iris,
noticeably less "sparkly," exactly the ask; 1.0 matches the traced
reference.

Checked: `eye_style="anime"` on Satoko, Satoshi, Krista (goggles) and
Keiko (glasses) through the real code path, not the prototype's
monkeypatch, no collision. `eye_style="anime"` composes sensibly even
without the round-tuned `FaceStyle` numbers, confirming the style only
changes what is inside the aperture, never the aperture itself. No
preset's own `eye_style` was changed from the "realistic" default;
this is additive only. `ruff`, `ruff format`, and `pytest -q` (361
passed, 11 new: both styles at both builds, every preset's own
`eye_style` still "realistic", and the glow sweep at both builds) all
green. `./refresh-ref-out.sh --check`, `./refresh-bases.sh --check` and
`./refresh-catalogue.sh --check` all green and untouched.

**Left for later, not asked for yet:** exposing `eye_style`/`eye_glow`
in the web tool's catalogue (same shape of decision as `mouth_width`
joining `FACE_RANGES` above, not done automatically here since nobody
asked); any preset actually switching to the anime style; the
reference's eyelash-tuft and eyelid-crease details, which `_eye_anime`
does not attempt.

## Conventions worth remembering

- Render and *look* at the PNG before calling a shape change done.
  Coordinates that are right in the math are routinely wrong visually;
  most of the fixes so far came from looking, not from reasoning.
- Render candidates side by side rather than one at a time. Monkeypatch
  the shape functions from a throwaway script so several profiles can be
  compared in one image without editing the source per guess, then write
  the winner in. Suppressing a feature entirely is part of the set: a
  render with the hair strands turned off is what proved they were
  carrying the difference, and the untapered leg is what proved the old
  taper was worse than no taper at all.
- When a comparison shows no difference, check that the variant was
  actually applied before concluding the knob does not matter. One
  strand-weight comparison here was five copies of the same image,
  because the substitution it relied on never matched.
- Re-render `ref-out/` in the same change as any shape edit. It is
  committed and the README shows it, so it is the one piece of output that
  goes stale visibly and silently. `./refresh-ref-out.sh` does it, and
  `--check` detects a stale state without writing anything.
- Anything meant to read as a smooth curve should be generated, not
  hand-placed. `_arc` traces a circle about the head centre by putting each
  control point on the bisector at `r / cos(half the segment angle)`, the
  same construction `_head_shape` uses. Hand-placed anchors and controls
  scallop instead: the crown peaked between its anchors and dipped at them,
  and that wobble reads as a defect rather than as texture. The hair reads
  as locks through the strands and the fringe, which is where the
  irregularity belongs.
- Check both builds after touching anything below the neck. Several
  rules that were correct at 4 heads broke the chibi (arm placement in
  particular), which is why `arm_x` is a skeleton anchor and not a
  formula in `character.py`.
- Check a palette far from the defaults after touching `shade()`
  derivations.
- Leave the tooling green: `uv run ruff check .`, `uv run ruff format .`,
  `uv run pytest`. The tests are a smoke check (imports, every preset at
  every build, `ref-out/` freshness), not a judge of whether a shape
  looks right, which is still decided by eye.
