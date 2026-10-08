# Webcomic plan

Take the generator from drawing one character at a time to drawing comic pages:
panels with several characters, acting, speech bubbles and flat backdrops. Written
2026-10-08 at the owner's request, after the hands campaign (`hands-plan.md`). The
long-term vision is webcomics and animations of the cast; this plan is the first half
of it, and animation is deliberately left for after (see "Deferred").

The record will be `webcomic-status.md`. The procedure is the one the last campaigns
used (`detail-strategy.md`, `hands-plan.md`): predict before measuring, one change per
measurement, study before building, only the owner signs off, one-line commits without
a trailer.

## Why, and the owner's decisions (2026-10-08)

1. **Webcomic first, animation later.** A still page needs poses and a scene layer;
   animation adds a timeline and rig on top of those, so the page is the cheaper
   first target and builds the parts animation needs anyway.
2. **Start with what we have, and iterate.** The cast stays the tall chibi, drawn
   front-facing. More angles come later, one study at a time, once pages show what
   they cost and what they buy. Not designed up front.
3. **Inherited, not new:** the style stays simple and flat. The cover work settled
   that backgrounds do not try to beat painted art on its own ground
   (`src/anime_character_creator/cover.py`, the owner's call of 2026-08-08), and
   `CLAUDE.md` keeps flat colour and hard edges. Backdrops here are flat shapes.

## What exists, and what a page needs

Seen in the repo on 2026-10-08, not built for this:

| a comic page needs | what exists |
|---|---|
| characters, consistent across panels | 19 presets, every one the same tall chibi; `render_character` is a pure function of the parameters |
| faces that act | `Expression` deltas (brow, eyelids, mouth curve and width); six named ones, all serious: stern, grim, hollow, wry, sorrow, resolute |
| bodies that act | none. `CLAUDE.md`: "poses do not" exist. An arm swing is one rotation of the whole arm (`right_arm_out`, `left_arm_out`); the head is rigid |
| hands that hold and gesture | the hands options (`hands-plan.md`): five relaxed hands, a fist on a held staff |
| several characters in one picture | `sheet.py` tiles presets with labels; `cover.py` places one figure on a backdrop |
| backdrops | `cover.py`: a flat backdrop and mist bands, authored shapes, no gradients |
| text | `cover.py` title text; `sheet.py` labels; no wrapping, no bubbles |
| panels and a page | none |
| other angles | none. Front-facing only |

So the work is, in the order the page forces it: acting range, poses, then the scene
layer. The first step is not to build any of that, but to draw a page with what exists
and see what hurts.

## Invariants

- **Render stays a pure function of the parameters.** A panel is a list of placed
  characters, a backdrop and text; the same input gives the same bytes.
- **Defaults stay byte-identical.** Every new knob at its default leaves every
  existing render unchanged: `./refresh-ref-out.sh --check`, and
  `harness/tall_chibi/snapshot.py` compared with `cmp`.
- **Skeleton-relative, continuous, flat.** Poses move joints continuously, so they
  tween for the animation later, and nothing pops in at a threshold.
- **Layers keep stable ids.** Every body part is its own SVG group with an id that does
  not change between renders, so a later timeline or a recolour can address it.
- **Legible at panel size.** A figure is judged at the size it appears in a panel, as
  the roster plan's face rule says, not at full size.
- **No AI image generation, ever** (`CLAUDE.md`), including for backdrops.
- **The slice drives the order.** After the first page the list below is re-ordered by
  what that page showed.
- **No commits unless the owner asks.** One line, no trailer.

## Owner checkpoints

As in the hands plan: at each checkpoint I produce the images, say where they are and
exactly what to look at, and stop until the owner answers. Answers are recorded in
`webcomic-status.md`, dated. Nothing after a checkpoint is built before it is answered.
The owner answers with one of: pick (a letter), reject all (with what is wrong), adjust
(a named change), or defer.

## The order

### W0. The slice (the owner decides, nothing built)

The page everything is judged against. I write a page script from the owner's choice
of scene, and a gap list: for each panel, what the page needs and which of the table's
rows covers it.

- **C0, owner checkpoint: the page.** The owner chooses:
  - **The scene**, from the novel or another story: who is in it, what happens, the
    dialogue. Four to six panels.
  - **The format**: a single page, or a vertical-scroll strip; the page's shape; the
    reading direction.
  - **The language** the text is in.
  I turn it into a panel-by-panel script and the gap list. The owner confirms or
  changes the script before any drawing.

### W1. The page, with what exists

A throwaway page composer under `harness/webcomic/`, not in `src/`: panels, flat
backdrops, placed characters, expressions and arm swings that already exist, and plain
speech bubbles. It is meant to look rough. Its job is to show the gaps.

- Prediction, written first: the first page fails mostly on **acting** (the six
  expressions are all serious, and a still page needs a laugh, a surprise, an
  embarrassment) and on **bodies** (every figure stands in the same pose with one
  swung arm), and not on layout or bubbles.
- **C1, owner checkpoint: page v0.** The owner looks at the page at reading size and
  says what hurts most. That answer re-orders everything below.

### The provisional order after W1

Reordered at C1 by what the page showed. The expected shape:

**W2. Acting range.** Expressions beyond the six: happy, surprised, angry, embarrassed,
laughing, crying, as `Expression` deltas, and whatever the mouth needs to carry them
(an open mouth, teeth) if it cannot yet. A study of what the face can already say comes
first. **C2:** every expression on three presets at panel size and at full size; the
owner picks which are right.

**W3. Poses.** Joints: shoulder, elbow, hip, knee, and the head turning and tilting. A
pose is a set of joint angles on the skeleton; poses are a small registry (standing,
pointing, waving, arms crossed, hands on hips, sitting, a mid-step walk), each judged at
panel size. Hands that hold things (a cup, a book, a sword) come with it. This is also
the elbow the detail plan deferred, and it comes before D6, the garment line work, which
sleeves would otherwise have to redo (`detail-plan.md`). **C3:** a pose sheet on three
presets; the owner picks and rejects poses.

**W4. The scene layer, in `src/`.** What W1's throwaway taught: panel layout, character
placement (position, scale, flip, order), flat backdrops from authored shapes, speech
bubbles with wrapped text, captions and sound effects, a page's export to SVG and PNG.
Built on `cover.py` and `sheet.py`, not beside them. **C4:** page v1, the same script
redone properly.

**W5. A second page.** A different scene with different characters, to find out whether
characters stay consistent from panel to panel and what the first page's choices cost.
**C5:** both pages side by side.

**W6. The web tool.** Compose a page in the browser (a later step; W4's page is a
parameters object, so it is a form on top).

**W7. A study in angles, not a build.** One character in three-quarter and in profile,
to learn what an angle costs in this renderer, and whether a flip of the front view does
most of the work in a chibi comic. **C7:** the owner decides to build it, to stay with
front and flip, or to wait.

## Deferred

- **Animation.** The same renderer, with a timeline that tweens parameters and joint
  angles frame by frame, and an export to video or a GIF. It is cheap to try once poses
  and the face's acting range exist. A separate plan.
- **The full cast at every angle.** Only after W7 says what it costs.
- **Detailed painted-style backdrops.** Ruled out by the cover decision, not deferred.
- **Garment line work (D6).** After W3; see above.
