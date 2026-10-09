# Webcomic plan

Take the generator from drawing one character at a time to drawing comic pages:
panels with several characters, acting, speech bubbles and flat backdrops. Written
2026-10-08 at the owner's request, after the hands campaign (`hands-plan.md`). The
long-term vision is webcomics and animations of the cast; this plan is the first half
of it, and animation is deliberately left for after (see "Deferred").

The record is `status.md` in this folder. The procedure is the one the last campaigns
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
- **The panels drive the order.** A capability is built when the first panel that
  needs it is next in line, and not before (see "The order").
- **No commits unless the owner asks.** One line, no trailer.

## Found in the code, 2026-10-09

Read, not guessed.

- **Two figures in one document collide.** Every figure's `<defs>` use fixed ids.
  Satoshi and Chiyo together repeat `hair-front`, `eye-l` and `eye-r`. The trailer in
  `../valley_of_mist` hit this and namespaces each figure's ids itself
  (`valley_of_mist_tools/trailer/figures.py`, `_namespace`); its docstring says two
  figures in one document would clip each other's hair. `sheet.py` and `cover.py` embed
  figures the same way without it. Not yet looked for in a rendered sheet.
- **There are no stable layer ids**, so the "layers keep stable ids" invariant below is
  a promise and not yet true. The only `<g>` elements are two eye clips.
- **The mouth is one quadratic stroke** whose curve `Expression` moves
  (`character.py`, `_face`). Anything that opens it, or a smile with teeth, is new
  shape code and not a parameter.
- **An arm is one rigid rotation about the shoulder**, with a fixed elbow bend built
  into the shape (the elbow at 35% of the way down). A hand at the hip needs the elbow
  as a parameter.
- **The trailer already built generic pieces, in the wrong repo for them.** In
  `valley_of_mist_tools/trailer/`: the per-figure id prefix, a flat one-tone silhouette
  of a figure, a figure placed by feet and height (`place`), text set as outlines with
  HarfBuzz from a bundled OFL font (`measure`, `wrap`, `block_svg`), and the cover's
  mist banks as a backdrop. None of it is specific to the trailer.

## Where it lives: functionality here, application in `valley_of_mist`

The owner's principle, 2026-10-09. **This repo holds what a comic can do; `../valley_of_mist`
holds the comic that is made with it.** It is the same line the covers and the trailer
already follow, and `CLAUDE.md` keeps this repo ignorant of its consumer.

| here (`anime_character_creator`) | in `valley_of_mist` |
|---|---|
| character capabilities: props, poses, expressions, new presets, the id prefix, the silhouette | the script and design doc (`<book>/docs/comic_design.md`) |
| page primitives: `Strip`, `Panel`, `Placement`, cropping | the strips as data (`<book>/comic/*.toml`), like `trailer/timeline.toml` |
| text: wrapping, captions, bubbles with tails, set as outlines | which words go in which bubble |
| flat scenery helpers: a window, a wall, a floor, a mist band | the book's places: the inn, the road, the valley's head |
| effects: a gust line, a flare | where a panel uses one |
| export of a strip to SVG and PNG | `shell_scripts/build_comic.sh` and the output in `<book>/build/comic/` |

The trailer's generic pieces are **copied here first and the trailer switches to them
later**, as a change of its own that must leave its stills byte-identical. Nothing in the
comic waits on that.

**Layout in this repo:**

```
src/anime_character_creator/
  comic/              # page primitives; imports only the package's public API
    layout.py         # Strip, Panel, Placement, cropping
    text.py           # outlines, measure, wrap (copied from the trailer)
    bubbles.py        # captions and speech bubbles with a tail
    scenery.py        # flat shape helpers
    effects.py
    fonts/            # the bundled OFL font, as in the trailer
  poses.py            # imported by character.py, which is 11.7k lines already
  props.py
tests/test_comic_*.py
docs/comic/           # plan.md, status.md
harness/comic/        # studies
```

**Dependencies.** The package has none today (`pyproject.toml`: an SVG document is text),
and PNG export is the optional `png` extra. Text set as outlines needs `uharfbuzz` and
`fonttools`, so they join as a second extra, `comic` (added with K3, and in the `dev` group so the
tests run, as `png` is), and `anime_character_creator.comic`
imports them only when text is set. The rest of the package stays dependency-free.

## Owner checkpoints

As in the hands plan: at each checkpoint I produce the images, say where they are and
exactly what to look at, and stop until the owner answers. Answers are recorded in
`status.md`, dated. Nothing after a checkpoint is built before it is answered.
The owner answers with one of: pick (a letter), reject all (with what is wrong), adjust
(a named change), or defer.

## The order: capabilities, built as the panels need them

**Revised 2026-10-09 at the owner's suggestion, and again the same day for where it lives.** The first version of this plan drew a
rough page with what exists to see what failed. The gap list already says what fails,
so instead: list the capabilities, order them by which panel needs them first, and
build each one when its panel is next, the generic part here and the application in the
book. There is no throwaway composer.

**The loop, per capability.** (1) Name the panel that needs it and what that panel must
show. (2) A short study if the answer is not obvious (what the face can already say,
what a bent elbow costs). (3) Build the smallest thing that draws the panel. (4) The
defaults stay byte-identical: `./refresh-ref-out.sh --check`, `ruff`, `pytest`.
(5) Draw the panel and look at it at panel size. (6) Record what it cost.

**The script comes first, and may be cut.** `../valley_of_mist/books/book1_hero_of_the_mist_tragedy/docs/comic_design.md`
is the source of the needs. The owner has said simplifying it is fine, so a capability that turns out
dear is a reason to change a panel, and that is raised with the owner, not patched
around.

### The capabilities, in build order

Cheapest and most reused first; each names the beat A panel that forces it.

| # | capability | first needed by | what it is |
|---|---|---|---|
| K1 | **Figure ids per figure** | A4, a second figure in one panel | `render_character` takes an id prefix; the default prefix is empty, so every existing render is unchanged. Copied from the trailer's `_namespace`. Then give each body part's `<g>` a stable id with the same prefix, which the invariant promises and an animation will need. Check a rendered sheet for the collision first (a control). |
| K2 | **The strip and the panel** | A1, the first panel at all | `comic/layout.py`: a strip is a list of panels; a panel is a frame, a backdrop and placed figures (position, scale, flip, order), clipped to its frame so a figure can be cropped. Placement is the trailer's `place` and the cover's `_figure`, generalised. Export to SVG and PNG. |
| K3 | **Text** | A1 (a caption), A3 (a bubble) | `comic/text.py`: the trailer's outline text (HarfBuzz, bundled font, `measure`, `wrap`) copied over, then what it lacks: caption boxes and speech bubbles with a tail that points at the speaker. Behind the optional `comic` extra. |
| K4 | **Backdrops** | A1, A2 | Generic flat-shape helpers here (`comic/scenery.py`: window, wall, floor, the mist band from `cover.mist_band`); the places themselves (the inn's common room, the mist wall at the head of the valley) are drawn in `valley_of_mist` from those. No gradients. |
| K5 | **Props** | A4 (a tray), A5 (a mug) | A held-object mechanism: a prop is a shape and a grip point, and a hand takes it. The staff is the one prop that exists and is the model. Tray, mug, cloth. |
| K6 | **New characters** | A5, A6 (the driver); beats B, D (Kenzo, Dieter) | Presets designed from the book's descriptions, and the owner looks at each before a page uses it. Older male faces may need `face_age` and wrinkle features that the roster does not have; a study first. |
| K7 | **Acting range** | A6 (a startled face), A3 (a tired, tally-keeping look) | A study of what the face can already say, then the mouth shapes it cannot (open, a smile) and new `Expression` deltas. **C: every new expression on three presets at panel size and at full size.** |
| K8 | **A pose: the reflex** | A5 | Joint angles on the skeleton: the elbow as a parameter, a head tilt, a lean, a lowered stance. A pose is a set of those, a small registry, and continuous so that it tweens later. The reflex is the first pose, a study decides how little it takes. **C: a pose sheet.** |
| K9 | **Seen from behind, or not** | A1 | A solid one-tone silhouette of the figure against the night window, which needs no back view. The trailer already has one (`figures.py`), copied here as a render option. Only if a panel wants more than a silhouette does a true back view get studied. |
| K10 | **Effects** | beat C (the gust, the scar's heat) | Drawn marks that are not characters: a thin cold line across the room, a small flare. Built when beat C is next. |

Why this order: K1 to K3 are needed by every panel and have nothing to do with taste, so
they come first and can be checked without the owner. K4 to K6 then make A1 to A4 drawable
with the faces that already exist, which gives the owner the first look early. K7 to K9
are the three gaps predicted to hurt most (the reflex and the startled face), done after
the owner has seen the rest and can say which of them matters most.

### Checkpoints

- **C0, the script.** Open: the owner confirms or changes that script (`comic_design.md` in the book's `docs/`).
- **C1, the first panels.** After K1 to K5: A1 to A4 drawn with the existing faces. The
  owner says what hurts most, which may reorder K6 to K9.
- **C2, the new characters** (K6): the driver, and later Kenzo and Dieter, each on its own.
- **C3, the faces** (K7) and **C4, the pose** (K8), as in the loop above.
- **C5, beat A**, all six panels, at reading size. Then beats B to D follow the same loop,
  with a capability added only if one of their panels needs it.

## Deferred

- **A second strip, the web tool, and a study in angles.** After beat A, as the first
  version of this plan ordered them: a different scene to test consistency, a form on top
  of the strip's parameters object, and one character in three-quarter and profile to
  learn what an angle costs and whether a flip of the front view does most of the work.
- **Animation.** The same renderer, with a timeline that tweens parameters and joint
  angles frame by frame, and an export to video or a GIF. K1's ids and K8's continuous
  poses are what it needs. A separate plan.
- **The full cast at every angle.** Only after the angle study says what it costs.
- **Detailed painted-style backdrops.** Ruled out by the cover decision, not deferred.
- **Garment line work (D6).** After K8; sleeves would otherwise have to redo it. See
  `detail-plan.md`.
