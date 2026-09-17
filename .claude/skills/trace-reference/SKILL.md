---
name: trace-reference
description: Convert an AI-generated reference image's silhouette into hand-portable quadratic-curve coordinates for a new or revised part in character.py (a hairstyle, a hat, a prop, a garment edge). Use whenever a new part needs to match a reference image's shape closely, not just its general idea; this is the same method the long_traced/long_traced_real hairstyles, Satoko's hair and Katherina's witch hat were built with. Do NOT use this to import, composite, or otherwise ship pixels from the reference itself.
---

# Trace-reference

Turns "make this part look like that reference image" into portable numbers,
by measuring the reference's silhouette in code and fitting a small
quadratic-curve chain to it, the same units and the same curve primitive
`character.py` already draws with. The output is Python source (a `Point`
and a list of `Segment`s per shape) that lives in `character.py` like every
other part. Nothing that goes into `character.py` is, or contains, a pixel
from the reference.

## Where this rule actually sits, stated once so it doesn't drift again

**`CLAUDE.md`'s "no scraping or importing external art assets" means don't
ship the reference's pixels.** It does not mean don't look at the
reference, and it does not mean don't measure it with code. This project's
own long-cut hairstyles (`long_traced`, `long_traced_real`), Satoko's hair
and Katherina's witch hat were built exactly this way: an AI-generated or
drawn reference, measured, fitted, and ported as editable numbers.
`harness/trace/` (the hair) and `harness/trace_hat/` (the hat) are the
records of that work; this skill and `trace_lib.py` are the generalized
pipeline, so the next part doesn't re-derive it from scratch.

What's actually forbidden, concretely:

- Embedding the reference image, or a crop of it, as a layer in the
  rendered output (no `<image>` SVG element pointing at it, no raster
  compositing).
- Running the reference through an image model to "clean it up into" the
  shape code (an upscaler, a vectorizer, anything generative). The
  vectorization here is `trace_lib.py`'s deterministic pixel labelling +
  curve fit, not a model call.
- Treating the reference's texture (shading, gradients, line weight) as
  something to reproduce. Only the silhouette and flat region colours
  transfer; `CLAUDE.md`'s flat-color hard-edge rule still applies.

What's fine, and is this skill's whole method: looking at the reference
repeatedly, measuring where its ink actually is with ordinary pixel code,
and porting the fitted curves into the part function, checked by rendering
and comparing.

## What went wrong before, so it isn't repeated

The witch hat took three passes. The first two did not look traced and did
not fit her head, and every cause is a rule below:

1. **Hand-measured landmarks instead of a traced contour.** An automated
   radial scan on the composite picked up hair and the staff instead of the
   hat, so the pass fell back to ~15 points read off a pixel grid. Fifteen
   points joined by guessed curves is a drawing *inspired by* the
   reference, not a trace. Walk the real contour (Step 3).
2. **A calibration nobody cross-checked.** Eye-to-chin alone, with an
   assumed eye position the chibi skeleton doesn't have: 18% off in scale
   and 45 px off-centre. A single vertical run cannot disagree with itself
   (Step 2).
3. **The trace rescaled to fit the canvas**, by a different factor per
   axis, which made it small and squat (Step 2, last rule).
4. **Checked only on the reference's black background**, which hid a gap
   between the brim and our narrower hair (Step 6).
5. **Measurement delegated with a landmark list.** The delegate built what
   it was given faithfully; the error was upstream. Keep calibration,
   contour extraction and the overlay check with whoever owns the result;
   they're cheap in tokens and they're where the judgment is. Delegating
   the port of already-fitted chains is fine.

## The pipeline

`trace_lib.py`, beside this file, has the reusable pieces (numpy, Pillow,
scipy, all dev dependencies). Run from the repo root with `uv run python`,
with the cairo path set if you'll render:

```bash
export DYLD_FALLBACK_LIBRARY_PATH="${DYLD_FALLBACK_LIBRARY_PATH:-}:/opt/homebrew/lib:/usr/local/lib"
```

Put the pass's scripts in `harness/<part>/` (calibrate, segment, trace,
emit, compare), writing intermediate images to the ignored `out/<part>/`.
They are the record of what was measured and how, the same reason
`harness/trace/` is kept.

### Step 1: pick the reference

**Trace off the full-figure composite when placement matters**, which for
anything worn or held it does: the composite is the only image where the
part's size and position relative to the head are defined.

**An AI tool's "layer export" is not a pixel crop of the composite.** The
grok `layer-*.png` files are regenerated variants: the hat layer's brim
ends and bow differ visibly from the hat in `katherina_grok.jpg`, and a
two-point correspondence between them gave x and y scales of 1.45 and 1.03,
which no crop can produce. Use a layer to see a part's shape where the
composite hides it (behind hair, off the edge), not as the source of
coordinates, unless you've checked with three or more well-separated points
that it really is the same geometry.

Check what kind of ink the image has. A layer PNG with real alpha
thresholds cleanly on alpha (`trace_lib.load_ink()` picks automatically).
A flat JPG on a *light* page thresholds on brightness. A composite on a
*black* page, which is every grok reference, has outline and background in
the same colour: no threshold separates them, so use Step 3's component
labelling.

### Step 2: calibrate a coordinate system on the reference

Every part in `character.py` is drawn in head-radius units, origin at
`sk.head_cx, sk.head_cy`. The calibration is `(origin_x, origin_y,
px_per_head_radius)` on the reference.

**Calibrate off our own rendered face, measured, not off assumed skeleton
constants.** The hat's working calibration (`harness/trace_hat/calib.py`):

1. Render the character without the part (`dataclasses.replace` the field
   to `None`) at a known scale, and measure its face in head radii
   straight off the skeleton: the skin component's widest row and its
   half-widths, and the chin (lowest skin row). Measure the hair's width at
   a few heights too, which tells you where our hair and the reference's
   will differ.
2. Measure the same features on the reference in pixels (the face is the
   largest skin-coloured component; its widest row and lowest row).
3. Solve the scale **twice, independently**: once from face width, once
   from the vertical run between widest row and chin. The hat's came out
   173.8 and 173.5 px per head radius. Agreement within a few percent is
   what says the calibration is right. If they disagree, the proportions
   genuinely differ and one scale is a compromise to choose by looking.
4. Origin x from the face's centre (mean of the widest row's edges and the
   chin's x), origin y from chin pixel row minus chin head-radius times
   scale. Sanity-check one more feature (the eyes) lands where ours are.

`trace_lib.calibrate_two_points` (two features at known head-radius
heights, eye and chin) is the older method from `harness/trace/`. Only use
it if you've measured both heights on our render rather than assumed them,
and still cross-check against face width.

**A standalone accessory with no companion full-figure reference** has
nothing to calibrate against. Pick two features on it and decide where they
sit in head radii (e.g., "the brim's front rim crosses the centre line at
the top of the skull, -1.0"). That's legitimate, it just encodes a
placement decision instead of a measurement; say so in the part's comment.

**Never rescale the traced result to fit the canvas.** If the part stands
above the canvas's headroom (the hat's crown reaches -2.64 head radii;
chibi headroom was -1.75), give the skeleton room instead:
`build_skeleton(min_hair_margin=...)`, supplied by a function next to the
part (`hat_hair_margin(p)`, which bounds the curve by its control points,
since a quadratic never leaves its control triangle, plus half a stroke).
The figure stands smaller on the same canvas. Then pass it at every call
site that builds a skeleton *for a character*: `render_character`'s
default, `cover.py`, and the `ref-out` snapshot test. `sheet.py` is left
alone on purpose, since a cast sheet holds every member at one body scale.
Check the part's widest reach against the canvas width too; the bigger
margin shrinks `head_r`, which is usually what makes a wide brim fit.

### Step 3: measure the contour

**Default: label fill components and walk their boundaries.** This is what
worked on the hat, and it's the only method that handles black outlines on
a black page and shapes that aren't single-valued in angle or x (a brim
seen from below, a curl that doubles back, a crescent of underside).

1. `lab, _ = scipy.ndimage.label(rgb.sum(2) > 60)`. Each fill region
   between outlines is now its own component. Print every component above
   ~150 px that starts in the part's area, with its bbox and mean colour
   (`harness/trace_hat/seg.py`); it's a quick map of which regions exist
   (the hat had crown, band, three bow pieces, brim top and two underside
   patches, all separate).
2. Pick components by seed pixel (`lab == lab[y, x]`), and `assert` that
   seeds meant to be different pieces really are different components.
3. Measure the reference's outline width: walk a column from one
   component to the next and count the gap (the hat's was 5 px, ~6 with
   antialiasing).
4. For each shape you'll draw: union its components, close by a few
   pixels to bridge interior outlines (`dilate` then `erode`, then
   `binary_fill_holes`), then **grow by half the outline width** so the
   boundary lands on the stroke's centre line, where this code draws its
   own stroke. Adjacent shapes grown this way share their boundary exactly.
5. `trace_lib.boundary(mask)` walks the outer contour in order;
   convert to head radii with the calibration.

Shape decomposition follows drawing order, not the reference's regions one
to one. Draw a base shape that covers the whole part (so no join between
pieces can let a gap show), then the pieces on top with their own
outlines. The hat: brim-plus-everything-above as one base, crown over it,
band, bow pieces, creases.

**Parts that wrap around the head need two layers.** A brim, a collar, a
scarf: its far side is behind the hair and its near side in front. Trace a
separate far-side shape and draw it *first* in `render_character`'s layer
list. Our hair is never exactly the reference's, and wherever ours is
narrower, a single front layer leaves the page showing through. For the
hat the far side is the whole silhouette unioned with the convex hull of
the two visible underside patches, which carries the hidden back rim
across behind the head; the head and hair cover everything but the parts
that should show.

**Interior line work** (creases, folds) is ink inside a region's filled
hull that isn't its boundary: erode the hull by more than the outline
width, take `rgb.sum(2) <= 60` inside it, label with 8-connectivity, drop
specks under ~25 px. For each stroke, order its pixels along their main
axis (SVD), average them in ~6 bins for a centre line, fit a two-segment
open chain, and draw it slightly thinner than the outline with round caps.

**Colours**: the median of each component, eroded a few pixels so the
antialiased outline edge doesn't pull it dark. A second tone (the hat's
underside) is a `shade()` of the base colour tuned to land on the sampled
value, not a new field.

**Fallback scans**, for simple cases: `radial_profile` (furthest ink per
bearing from one centre: hair around a skull, on a reference where nothing
else sits at those radii) and `column_profile` (topmost/bottommost ink per
column: a hem, a shaft). Both fail silently on a busy composite: they
return a plausible closed curve made of whatever is outermost. A
suspiciously clean result (a near-perfect circle at `r_max`) means
something else is being included.

**Always draw the result back over the reference and look, zoomed in.**
Brighten the reference (×3.5) so dark fills separate from outline, draw
each fitted chain (`trace_lib.sample_chain`) in its own colour, and crop 2
to 3× around the fine parts (tips, bows, the ends of a brim). A chain that
rides the outline's centre everywhere is done; one that's off by a
constant amount is a calibration or grow-width problem, not a tracing one.

### Step 4: simplify and fit

Closed contours: `trace_lib.fit_closed(points, tol)`, which opens the loop
at its most distant pair and runs Douglas-Peucker plus a least-squares
control point per segment. Tolerances in head radii that worked on the
hat: 0.018 for large shapes (brim, crown: ~30 to 40 segments), 0.015 for
medium (band), 0.012 for small pieces (bow). Open chains:
`simplify()` + `fit_chain()`; 0.03 to 0.07 was the hair's range.

Don't smooth away bumps that are in the reference (the hat's notch where a
crease meets the outline is real). Don't hand-place a control point at a
segment's midpoint; `fit.py`'s history records that it bulges every edge
outside the true contour.

### Step 5: emit and port

Save the fitted chains as JSON, then generate the `character.py` block
from it with a script (`harness/trace_hat/emit_hat.py`): module constants
typed as `Chain = tuple[Point, list[Segment]]`, a comment above them
saying where they were traced from and how calibrated, and the part
functions using `_curve(cx, cy, r, *chain)`. Generating rather than
pasting by hand is what makes a retrace cheap: re-run trace, re-run emit,
re-render. Write these scripts with a file-writing tool, not an unquoted
shell heredoc, which eats backticks and `\n`. Run `ruff format` after.

The part follows the usual per-part conventions: `OUTLINE` stroke at
`_stroke_w(sk)`, colours from `CharacterParams`/`Outfit` fields with
`None` drawing nothing, appended to `layers` at the right z-order.

### Step 6: check on our own figure

**Same window, same scale, side by side.** Crop the reference and our
render to the same head-radius box using each one's own calibration
(`harness/trace_hat/compare.py`) and put them next to each other. This
answers "does it fit her head" directly; a full-figure glance does not.

**Then check what the reference's page hid:**

- Render on transparency composited onto **white**, not only on black. A
  black page hides every gap between the part and our hair.
- Zoom our render at 4× (`cairosvg.svg2png(..., scale=4)`) around every
  junction: part against hair, part against face, tips.
- **Both builds** (chibi and `--build realistic`); the head-to-body ratio
  changes what "fits" looks like.
- **Wherever it's actually used**: a cover or style anchor on its own
  background, previewed to a scratch file before overwriting anything a
  downstream repo has checked in.

Iterate by looking. Retrace (Steps 3 to 5) when the shape is wrong; adjust
layering or colour by hand when it's a composition problem.

**Before calling it done:** `uv run ruff check .`, `ruff format --check .`,
`pytest` (the `ref-out` snapshot test fails for the changed character,
which is expected), `./refresh-ref-out.sh` and confirm its report says only
that character changed, then `./refresh-ref-out.sh --check`.

## When NOT to use this

A part that's a placement/color decision, not a silhouette question
(picking a hat *color*, deciding *whether* a garment has long sleeves)
doesn't need tracing at all, just a value in `CharacterParams`/`Outfit`.
Reach for this skill specifically when a reference's *shape* is the thing
being matched and eyeballing coordinates by hand would take many render-
edit-look cycles to converge on it.
