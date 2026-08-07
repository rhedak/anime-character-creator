# Pitfalls

Every entry here produced a wrong number in an earlier run of this
analysis. They are listed with what the wrong output looked like, so the
symptom is recognisable, and with what fixed it. Read before writing any
new measuring code: four measurement passes were thrown away learning
these, and `probe.py` exists so they do not have to be learned again.

## Chained landmark inference poisons everything downstream

**The mistake.** Deriving `shoulder_y` from a colour scan, then taking
`face_width` as the widest skin row above it, then normalising every ratio
by that width.

**What it looked like.** `face width / H = 0.001` for one figure and
`0.159` for another whose face fills half the frame. The same reference
measured 410px one pass and 477px the next, from the same image, because
the primitive underneath was unstable.

**Why.** One stray speckle that passes the colour tolerance moves the
derived landmark, and everything built on it moves with it. Tightening the
tolerance moves the artifacts around rather than removing them.

**The fix.** Normalise by figure height and nothing else. The figure's
bounding box needs no colour classification at all, because the outline
surrounds everything, so it is the one primitive that cannot drift. Each
measurement then answers one question directly from pixels, with no
intermediate landmark.

## Measuring our own output instead of computing it

**The mistake.** Counting pixels in `ref-out/*.png` to find our own
proportions.

**Why it is worse than useless.** It adds error to a number the code
already knows exactly, and a measured number does not tell you which
constant produced it. `build_skeleton` has every anchor, and the hair
callables can be evaluated for their point data.

**The fix.** `probe.py skeleton`. Measure the reference, compute ours.

**One exception.** Widths that come out of a curve rather than an anchor,
such as how wide the hair actually paints, are worth measuring on our own
render too, because the control points of a Bezier lie outside the curve
and using them overstates the width. Measure both sides the same way when
you do.

## An anchor is not always where the ink is

**The mistake.** Aligning our figure to a reference on `Skeleton.chin_y`,
which is `head_cy + head_r`, when `_head_shape` draws the chin at
`(1 + chin_drop) * head_r`. At the realistic build that is 0.004 H lower
than the anchor.

**Why it bites.** Every comparison that reads "at a matched depth above
the chin" is then read 0.004 H too high on our side, which on a face is
several percent of width. In task 62 that was the entire size of the
claim being made, and it flipped the conclusion: the corrected numbers
said the jaw was already close and the whole head was too wide, which is
the opposite change.

**The fix.** Compute the anchor, then check what the shape does to it
before comparing. A part that offsets, drops or extends past an anchor
has to be read at the offset value. Where a landmark is drawn rather than
anchored, find it the same way on both sides, by reading `rows` down
until the run goes to zero, and beware that on this figure the face and
the neck are the same colour, so the span does not vanish at the chin, it
becomes the neck.

## Quantised histograms cannot settle a palette question

**The mistake.** Reading dominant colours from a histogram bucketed at 16
and reporting the bucket centres as the palette.

**What it looked like.** Canon green `#486848` against ours `#4a6845`,
quoted as near-identical. Both were bucket centres, each good to only
eight points a channel, which is the same size as the differences worth
arguing about.

**The fix.** `probe.py sample` counts exact colours inside a box. Put the
box in a flat patch away from any outline or shadow. The real answer for
that green turned out to be within four points a channel, so the
conclusion held, but it was luck rather than evidence.

## Pale hair and light skin are the same colour to a tolerance test

**What it looked like.** A hair-span measurement reporting hair reaching
the bottom of the figure, and the hair's widest row landing at the hips.

**Why.** Pale hair `#eaead8` and light skin `#f5d8c4` differ by less than
the tolerance any JPEG measurement needs, so a tolerance ball around
either one swallows the other, and the arms and hands then count as hair.

**The fix.** Nearest-colour assignment rather than a tolerance ball: a
pixel counts only if it is closer to a wanted colour than to any
competitor. That is what `rows --against` is for. On our own flat output a
tight tolerance is enough, since the colours are exact.

## A colour run does not tell you what it is

**What it looked like.** A centre-column scan read as chin at 0.474 H when
the run at 0.38 H was the mouth and the jaw stroke was at 0.45 to 0.47.
Both readings were self-consistent; the wrong one was picked because it
"made more sense".

**Why it matters.** That number anchored the claim that the vertical
proportions already match, which is the claim most likely to stop a future
pass moving something that was right.

**The fix.** Crop the band at 3x with guides and look. Any landmark that
is going to appear in the report gets confirmed by eye. If it cannot be
confirmed, quote it to one significant figure.

## Blob detectors find highlights and gaps, not just eyes

**What it looked like.** The enclosed-white detector returning apertures
of 119x79px on one reference, correct, and 13x70px on another, which was a
gap between hair strands, and 41x38px on a third, which was a highlight
dot.

**The tell.** On a symmetric figure the left and right come out the same
size when it worked, and differ when it did not. `probe.py eyes` prints
that check. When it says the two disagree, the numbers are worthless: crop
the head and read it by eye instead.

## Our shadows are composites, so `shade()` is not the tone on screen

**What it looked like.** Counting pixels equal to `shade(tunic_colour)`
found almost none, on a figure with obvious shadow wedges.

**Why.** The shadows are painted as `shade(colour)` at `opacity` between
0.45 and 0.8, so the pixel that lands is a blend of the shadow and
whatever is beneath it. The tunic shadow renders as `#405c3c`, not as
`shade("#4a6845")` which is `#395335`.

**The fix.** Read the exact colours out of the render and identify the
composites, then count those. Worth knowing for its own sake as well: it
means the shadow tone depends on the stacking, so a shadow crossing two
surfaces comes out two colours.

## The references disagree with each other

**What it looked like.** Our Satoshi chibi measuring up to 70% wider
through the torso than his reference, which reads as a catastrophic gap.

**Why.** The two chibi references are not the same chibi. At hip level the
canon Satoko chibi is 0.560 H across and the canon Satoshi chibi 0.252 H.
Our two are close to each other, which is what a shared skeleton produces
and what the Satoko-anchored style asks for. Chasing his reference would
mean giving him separate proportions, which `CLAUDE.md` forbids.

**The fix.** Check whether a delta is explained by the references
themselves before reporting it. The same applies to colour: his references
use tanner skin and browner gold, and `presets.py` deliberately unifies
the palette.

## A ratio can inflate a gap that has one cause

**What it looked like.** Eye spacing reported as 46% too wide, measured in
aperture widths, alongside apertures that were themselves 19% too narrow.
In absolute terms the spacing was 20% off, and most of that followed from
the apertures.

**The fix.** When two measurements share a cause, report the absolute
figure and say which one is upstream. Fix the upstream one, re-measure,
and only then decide whether the other needs anything. Otherwise the same
gap gets counted twice and gets corrected twice.

## The shell here is zsh, which does not word-split a variable

**What it looked like.** `P=".venv/bin/python .../probe.py"` and then
`$P strip ...`, giving `no such file or directory: .venv/bin/python
.../probe.py` on every line. The same script had just worked when typed
out in full.

**Why.** bash splits an unquoted variable on whitespace and so treats that
as an interpreter plus a script; zsh does not, and looks for a single
executable whose name contains a space. It bites a loop over commands held
in a variable the same way (`for c in "eyes x" "column y"; do $S $c`).

**The fix.** `probe.sh` is a real executable, so a variable holding its
path works in either shell. Put paths in variables, not commands.

## Ruff covers `.claude/` too

New tooling here is linted and formatted along with `src/`. Two things
recur: unpacking a value you do not use (prefix it with an underscore, or
return less from the helper), and closures over loop variables, which is
what the `B023` here was. Extract the loop body into a function taking
parameters rather than adding a `noqa`. Compact numeric tables that the
formatter wants to explode into one-value-per-line can be wrapped in
`# fmt: off` and `# fmt: on`.
