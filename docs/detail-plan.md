# Detail plan

Raise the tall chibi's detail level toward the spirit of
`ref-local/katherina_grok_real/`, and make the one build hold up across the
height range: a face that can mature, and a body that stays in proportion
when it stretches. Written 2026-09-27 at the owner's request, after the tall
chibi campaign made the tall chibi the one figure (`tall-chibi-plan.md`).

The record will be `detail-status.md`. The procedure is the one the last
campaigns used (`bust-strategy.md`, `bare-body-strategy.md`): predict before
measuring, one change per measurement, look in the right view, study before
building, only the owner signs off, one-line commits without a trailer.

## Why

A review on 2026-09-27 put Katherina's face next to the reference's at one
head size (`out/review/face_vs_reference.png`) and eight characters at
heights 0.8, 1.0 and 1.3 (`harness/tall_chibi/height_range.py`). The gap is
in how things are drawn more than in how many things there are:

- **Line weight.** Our line is `_stroke_w`, 0.043 head radii, one weight
  everywhere. The reference's outline is about half that, its interior
  lines thinner still; its one heavy line in the face is the upper lash.
- **Eyes.** Ours are closed rings with one outline weight. The reference's
  are open shapes: a heavy upper lash that thickens toward the outer corner
  and ends in a flick, a short thin lower lash, no line under the rest, a
  lid crease, an iris with a dark upper rim. Ours are also larger against
  the face and sit higher.
- **Face shape.** Ours is a circle; the reference narrows to a soft chin
  and has a nose tick.
- **The face does not change with height.** Satoko at 0.8 and at 1.3 has
  the identical face on a longer body, so a tall figure reads as a child's
  head on stretched legs. Most of what reads as grown up in the reference is
  in the face.
- **Widths stay fixed as the body lengthens.** By design of R4b, the stretch
  keeps every width, so at 1.3 the shoulders are no wider than the head and
  the limbs are straight tubes. Hands are mitten fists at every height.
- **Hair** is a flat mass with a few lines; the reference has strand lines
  and bangs parted into locks.

What already holds: line weight follows head size, so it is the same at
every height, and anything added to the head carries to every height free.

## Owner's decisions (2026-09-27)

1. **Face maturity is its own slider**, not derived from height: short
   adults and tall teenagers both exist.
2. **Skin stays fully flat.** The small cel shadows the reference has (under
   the chin, hair on the forehead) are deferred to an optional polish pass,
   not a priority.
3. **Widths may follow height a little.**
4. **The reference's role is scoped to this plan.** The Grok image is the
   benchmark in spirit, judged by eye, never traced and never a pixel
   target. It is one character's reference, so `CLAUDE.md`'s direction
   (references are not a target for new work) stays as it is.

## Invariants

- **Flat colour, hard edges, no shading.** Detail comes from line work and
  shape, never from a second tone across a surface or on skin.
- **Additive knobs default to today.** A new slider (face maturity, the
  width follow-through) at its default leaves every render byte-identical:
  `./refresh-ref-out.sh --check` and `harness/tall_chibi/snapshot.py`
  compared with `cmp`. Steps that deliberately change every figure (line
  weights, eyes, limb taper, hair) say so, and show before and after.
- **Continuous, for later animation.** Every new knob moves shapes
  continuously: no feature that pops in at a threshold (a nose tick grows
  from nothing, and draws nothing, not a round-cap dot, at zero). The head is
  rigid under any future rig, so head detail is safe to add now; garment
  line work on limbs is last because posable limbs would redraw it.
- **Legible at the smallest consumer size.** Every study is judged at full
  size and at the smallest size `../valley_of_mist` renders (its chapter
  inserts and cast sheet), where fine lines can turn to mud.
- **Nothing downstream moves mid-campaign.** `../valley_of_mist` and the
  covers are regenerated only at checkpoints the owner picks.

## The order

### D0. Inventory and baseline (read-only)

- Every stroke weight: `_stroke_w(sk)` has 78 call sites in
  `character.py`, 20 of them with a fraction; each classed as silhouette,
  interior, or feature (lash, brow, mouth).
- The face: `_face`, `_eye_realistic` (every preset uses it), `_eye_anime`
  (no preset uses it: keep, upgrade too, or retire), the brows, the mouth,
  and every `FaceStyle` knob and expression they must keep honouring.
- The hands (`_hand`, `_hand_length`, `_hand_centre`), the limbs'
  outlines, and `_KEEP_WS` in `skeleton.py`, which the height stretch holds.
- The six hairstyles' interior lines.
- The smallest render sizes `../valley_of_mist` uses.
- A baseline sheet in `harness/detail/`: the face comparison with the
  reference calibrated properly (face width and chin measured twice, as the
  trace skill's step 2 does, instead of the review's by-eye crop), and the
  height range sheet.

**Acceptance:** the inventory in the status file, each item with its step.

### D1. Line weights

A study: the silhouette at today's 0.043 and two lighter weights (about
0.032 and 0.025 head radii), each with interior lines at two fractions of
it, on four characters at full size and the smallest consumer size. The
owner picks. Then the change, all figures at once.

**Acceptance:** before and after sheets; `ref-out/` refreshed; the suite
green.

### D2. Eyes

`_eye_realistic` redrawn in the reference's spirit, still flat:

- the upper lash as a filled shape, thickening toward the outer corner,
  with a flick;
- a short thin lower lash at the outer corner, the rest of the lower edge
  unlined;
- a lid crease;
- the iris's upper rim in a darker flat band.

Study first (two or three lash shapes, on warm and cool eye colours, a very
different palette included). Every existing knob and expression keeps
working: `eye_openness`, `eye_lower_lid`, `eyes_closed`, tilt, glow,
glasses.

**Acceptance:** before and after on every preset and every expression; the
knob sweeps still read.

### D3. The face maturity slider

`CharacterParams.face_maturity`, 0 to 1, default 0 (today's face). Toward
1, together:

- the eyes a little smaller and lower;
- the jaw narrowing to a soft chin;
- a nose tick growing in.

Study first: maturity 0, 0.5 and 1 against heights 0.8, 1.0 and 1.3, on a
man and a woman. The owner sets the ranges and then which presets opt in.
Web tool slider, `urlstate`, catalogue.

**Acceptance:** byte-identical at 0; continuous across the range (a sweep
at fine steps with no pops); the owner's sign-off on the grid.

### D4. The body at height

In three parts, each studied first:

- **D4a. Widths follow height a little.** Shoulders, and the limb widths
  with them, scale by `1 + k * (height - 1)` for a small `k` the owner picks
  from a sweep. Touches the R4b stretch rule (`_KEEP_WS`). Byte-identical at
  height 1.0.
- **D4b. Limb taper.** Wrist, knee and ankle narrowing, on bare and clothed
  views (the base layer shows it best). Changes every figure; looks right
  at 1.0 as well.
- **D4c. Finger hints.** A thumb split and one or two creases on the fist
  and the gripping hand, not full articulation.

**Acceptance per part:** before and after at the three heights; the suite
green.

### D5. Hair

Strand lines inside the mass and bangs parted into locks, on one hairstyle
first to set the pattern (`long_traced`, Katherina's, since hers is the
reference), then the other five one at a time.

**Acceptance per hairstyle:** before and after on every preset wearing it,
and under a hat.

### D6. Garment line work

Cuff gathers, seams and folds, one garment at a time. Last, because it
multiplies across cuts, bust and height, and because jointed limbs for
animation would redraw sleeves.

**Acceptance per garment:** before and after across cuts and heights.

### Checkpoints

After D2, after D4 and at the end: regenerate `../valley_of_mist` and the
two covers (`../time_slider_katherina`, `../short_stories`) if the owner
asks, pixel-checked against the previous commit so only the intended
change shows.

## Deferred

- **Small skin shadows** (under the chin, hair on the forehead): an
  optional polish pass after the plan, owner's decision 2.
- **Animation**: a separate plan. Face animation (blink, talking mouth
  shapes, expressions) builds on D2 and D3 and needs no rig; jointed arms
  and legs come before D6's sleeve and trouser detail would be worth
  finishing.
- **Height in compositions**: stays dropped (height differences are not
  important for the stories).
