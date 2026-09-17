---
name: trace-reference
description: Convert an AI-generated reference image's silhouette into hand-portable quadratic-curve coordinates for a new or revised part in character.py (a hairstyle, a hat, a prop, a garment edge). Use whenever a new part needs to match a reference image's shape closely, not just its general idea; this is the same method the long_traced/long_traced_real hairstyles and Satoko's hair were built with. Do NOT use this to import, composite, or otherwise ship pixels from the reference itself.
---

# Trace-reference

Turns "make this part look like that reference image" into portable numbers,
by measuring the reference's silhouette in code and hand-fitting a small
quadratic-curve chain to it, the same units and the same curve primitive
`character.py` already draws with. The output is Python source (a `Point`
and a list of `Segment`s) to paste into a `_part_name()` function. Nothing
that goes into `character.py` is, or contains, a pixel from the reference.

## Where this rule actually sits, stated once so it doesn't drift again

**`CLAUDE.md`'s "no scraping or importing external art assets" means don't
ship the reference's pixels.** It does not mean don't look at the
reference, and it does not mean don't measure it with code. This project's
own long-cut hairstyles (`long_traced`, `long_traced_real`) and Satoko's
hair were built exactly this way: an AI-generated or drawn reference,
measured, fitted, and ported as hand-editable numbers that live in
`character.py` same as every other part. `harness/trace/` is the existing
record of that work; this skill generalizes its pipeline (which hardcoded
one reference file and one calibration) so the next part doesn't
re-derive it from scratch.

What's actually forbidden, concretely:

- Embedding the reference image, or a crop of it, as a layer in the
  rendered output (no `<image>` SVG element pointing at it, no raster
  compositing).
- Running the reference through an image model to "clean it up into" the
  shape code (an upscaler, a vectorizer, anything generative). The
  vectorization here is `trace_lib.py`'s deterministic pixel-threshold +
  curve-fit, not a model call.
- Treating the reference's texture (shading, gradients, line weight) as
  something to reproduce. Only the silhouette transfers; `CLAUDE.md`'s
  flat-color hard-edge rule still applies to what gets drawn.

What's fine, and is this skill's whole method: looking at the reference
repeatedly, measuring where its ink actually is with ordinary pixel
thresholding, and hand-authoring (or delegating with a precise brief) the
resulting curve into the part function, checked by rendering and comparing.

## The pipeline

`trace_lib.py`, beside this file, has the reusable pieces. Run it with
`uv run python`, from the repo root (matches `harness/run.sh`'s own
convention), with `DYLD_FALLBACK_LIBRARY_PATH` set if you'll render:

```bash
export DYLD_FALLBACK_LIBRARY_PATH="${DYLD_FALLBACK_LIBRARY_PATH:-}:/opt/homebrew/lib:/usr/local/lib"
```

### Step 1: pick the reference and check what kind of ink it has

An exported layer PNG with real alpha transparency (common for an
AI-tool's "layer export") thresholds cleanly on alpha; a flat JPG or a
PNG on a solid page has no usable alpha and needs the RGB-brightness
fallback instead. `trace_lib.load_ink()` picks automatically by checking
whether the alpha channel actually varies; sanity-check its `.sum()`
against the image's total pixel count before trusting it (a number near 0
or near everything means the wrong channel got read).

### Step 2: calibrate a coordinate system on the reference

Every part in `character.py` is drawn in head-radius units, origin at
`sk.head_cx, sk.head_cy`. A reference of a whole figure calibrates off two
points with a known head-radius position (`trace_lib.calibrate_two_points`,
same as `harness/trace/trace.py`'s `REF_EYE_Y`/`REF_CHIN_Y`): eye-center
and drawn-chin are the two this project has used, at 0.16 and ~1.0-1.05
head radii depending on the build, since both are unambiguous ink on
almost any reference.

**A reference of a standalone accessory (a hat by itself, a prop by
itself) has no head to calibrate against.** Two options, in order of
preference:

1. Calibrate against a companion reference that has the same accessory
   *on* a head (the full-figure grok reference, not just the exported
   layer), then carry the scale over to the isolated layer if it's
   pixel-identical geometry cropped out of the same source (check this:
   compare the accessory's own width in both images at the same zoom
   before trusting it).
2. Pick two features on the accessory itself with a *design* decision
   about where they should sit in head-radius units (e.g., "the brim's
   underside should clear the hair the way the headscarf's edge does,
   at `_SCARF_EDGE_Y`-ish height") and calibrate to that instead of to a
   measured reference. This is a legitimate calibration, it just encodes
   a placement decision instead of reading one off a photo; say so in the
   part function's docstring so a future reader knows which kind it is.

**Check a calibration by making two independent measurements agree.**
The witch hat's first two passes calibrated off an eye-to-chin run alone,
assumed an eye position this skeleton does not have, and came out 18% off
in scale and 45 px off-centre; nothing flagged it because a single
vertical run cannot disagree with itself. What caught it: render our own
character (without the part), measure its face in head radii (widest row,
half-widths, chin), measure the same features on the reference, and solve
the scale separately from the width and from the height. If the two
scales agree within a few percent, the calibration is right; if they do
not, the proportions differ and a single scale is a compromise to decide
on by looking.

**Never rescale the traced result to fit the canvas.** If a part stands
above the canvas's headroom, give the skeleton more room
(`build_skeleton(min_hair_margin=...)`, as `hat_hair_margin` does) so the
figure stands smaller instead. Shrinking the part to fit throws away the
trace; per-axis shrinking is how the hat's second pass came out squat.

### Step 3: measure the silhouette

**For a reference with black outlines, label the fills, not the ink.**
A composite on a black page (the grok references) has outline and
background in the same colour, so no threshold isolates one object's
silhouette, and a radial scan picks up whatever sits outermost. Label
connected components of the non-outline fill instead (`scipy.ndimage.label`
on `rgb.sum(2) > 60`): each fill region between outlines becomes its own
component, pick the ones belonging to the part by seed pixel, union them,
close the outline-width gaps between them, and grow the result by half
the reference's outline width so the boundary lands on the stroke's
centre line. Then walk it with `boundary()` and fit with `fit_closed()`,
one chain per region (a hat's crown, band and brim are separate shapes
drawn in order, each with its own outline). Ink left inside a region's
filled hull (creases, folds) can be taken as open strokes: label it, order
its pixels along their main axis, fit a two-segment chain.

**Parts that wrap around the head need two layers.** A brim, a collar, a
scarf: its far side is behind the hair and its near side in front. Trace
them as separate regions and draw the far side first in the layer list.
Otherwise, wherever our hair is narrower than the reference's, the page
shows through between them.



Two scan shapes, pick whichever matches how the part is actually
arranged:

- **`radial_profile`**: furthest ink per bearing from one center point.
  Right for anything roughly centered on an anchor: hair around the
  skull, a crown around its own apex.
- **`column_profile`**: topmost or bottommost ink per horizontal
  position. Right for anything with a left-to-right reading and no single
  natural center: a brim's upper edge, a hem, a shaft.

Sanity-check the raw measurement before fitting anything: plot the
profile back over the reference (draw the sampled points as a polyline on
a copy of the image, the same check `harness/trace/check.py` does) and
look at whether it actually rides the silhouette's edge. A measurement
that's off by a consistent amount usually means the calibration is wrong,
not the scan.

### Step 4: simplify and fit

`trace_lib.simplify()` (Douglas-Peucker) picks a handful of marks from the
raw scan; `tol` around 0.03-0.07 head radii is where this project has
started, then adjusted by looking at the result. `trace_lib.fit_chain()`
least-squares fits one quadratic control point per segment between
consecutive marks, endpoints pinned exactly to the marks. Do not hand-pick
the control point at the segment's midpoint; `fit.py`'s own history
records that this bulges every edge outside the true contour.

### Step 5: emit and port

`trace_lib.emit_chain()` prints `Point`/`Segment` Python literals. Paste
them into a new or existing `_part_name()` function in `character.py`,
following the existing per-part convention (skeleton-relative anchors,
`OUTLINE`/`shade()` for stroke and shadow, appended to `layers` at the
correct z-order in `render_character()`).

### Step 6: check on our own figure, not just on the reference

A curve that matches the reference's own proportions can still look wrong
on this generator's skeleton, which has different ratios (chibi head-to-
body, a different jaw, different hair mass). Render the character
(`render.sh --preset <name>`) and look at it beside the reference, the
same `on_ref`/`on_ours`/`strip` comparison `harness/trace/trace.py`
already builds. Iterate the fitted numbers by looking, not by re-running
the fit tighter; the fit's job was getting a reasonable first draft onto
the page, not producing a final answer no one checks.

## When NOT to use this

A part that's a placement/color decision, not a silhouette question
(picking a hat *color*, deciding *whether* a garment has long sleeves)
doesn't need tracing at all, just a value in `CharacterParams`/`Outfit`.
Reach for this skill specifically when a reference's *shape* is the thing
being matched and eyeballing coordinates by hand would take many render-
edit-look cycles to converge on it.
