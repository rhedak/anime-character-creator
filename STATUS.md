# Status

Snapshot of where the generator is and what comes next. Working notes,
not user documentation: see `README.md` for how to run it,
`docs/architecture.md` for how the drawing code fits together,
`docs/api.md` for the public surface, `docs/gap-analysis.md` for a
measured comparison of the current renders against the canon, and
`CLAUDE.md` for the rules that govern changes.

Last updated: 2026-08-06, at `21850a5` "add new references", plus two
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

`ref-out/` holds those four as checked-in `.png` and `.svg`, and the
README displays them. It is the only generated output in version control,
and it is the current state of the named characters rather than a
snapshot of some past one, so **refresh it in the same change that alters
a shape.** Miss it and the README shows art the code no longer produces:

```bash
./refresh-ref-out.sh          # re-render, report which characters moved
./refresh-ref-out.sh --check  # compare only, write nothing, exit 1 if stale
```

Anything else goes to `out/`, which is ignored, and which was emptied on
2026-08-07: 128MB of per-task snapshots, with the scripts that measured
them promoted to `harness/` first.

`ref-out/on-white/` holds the same four on a white card. They exist for
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
