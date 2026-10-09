# Webcomic status

The record for `plan.md`. Procedure: `../detail-strategy.md`.

## RESUME

**Beat A (six panels) is drawn end to end** (2026-10-09), the first proof of concept:
`valley_of_mist/books/book1_hero_of_the_mist_tragedy/build/comic/ch01.png`, built by
`shell_scripts/build_comic.sh ch01` in `valley_of_mist`. K1 to K7 and K9 are done; **K8
(poses) and turning characters are deliberately left for after this first proof of
concept**, on the owner's word. The stand-ins are listed under "Beat A, first build" below.
Waiting on the owner: **C2** (the look of Kenzo, Dieter and the driver) and **C1** (what
hurts most in the six panels), which decide what comes next: beats B to D, or poses.
All committed in both repos.

## Scoreboard

| step | state |
|---|---|
| C0 the script | confirmed 2026-10-09 |
| K1 figure ids | done: `render_character(..., id_prefix=)`, default unchanged |
| K2 the strip and the panel | done: `comic/layout.py` |
| K3 text | done: `comic/text.py` (copied), `comic/bubbles.py` |
| K4 backdrops | done: generic helpers in `comic/scenery.py`, the places in `valley_of_mist` |
| K5 props | done: `comic/props.py` (tray, mug), `Placement.hand` |
| K6 new characters (driver, Kenzo, Dieter) | drafted, waiting on the owner's look (C2) |
| K7 acting range | done for beat A: an open mouth, startled, exasperated, alert, smile |
| K8 poses, the reflex first | deferred by the owner until after the first proof of concept |
| K9 seen from behind (a silhouette first) | done: `Placement.tone`, a flat one-tone silhouette |
| K10 effects | not started, needed by beat C |
| later: a second strip, the web tool, an angle study | deferred |

## Owner's answers

One line per checkpoint, dated, as the owner answers.

- **Direction, 2026-10-08.** Webcomic first, animation later. "Start with what works
  and then iterate": the cast stays the tall chibi, front-facing, and more angles come
  later by iteration.
- **C0, 2026-10-09.** The scene is `../valley_of_mist` book 1 from chapter 1 on, the
  prologue skipped for now. Format: a vertical scroll strip. Language: English.
  The script itself is not yet confirmed.
- **K2 follow-up, 2026-10-09.** The flip problem (a flipped Satoshi moves his scar), answered
  "ok" to the two options as the first, the one recommended: keep the scar on the same
  cheek of the face when a figure is flipped. Not built; it waits for the first panel that
  flips him (A4).
- **C0, 2026-10-09, confirmed.** The beat order with A as the first slice, the cuts (the
  Brandt boy, the old-new-year paragraph, most of the inner commentary), the beat A text
  as written, and designing the driver, Kenzo and Dieter from the book's descriptions
  with the owner looking at each first. **Condition:** keep them out of the presets the
  web tool exposes, "there's already enough". The tool lists `sorted(PRESETS)`
  (`catalogue.py`), so they go in a separate registry and not in `PRESETS` (K6).
- **Placement, 2026-10-09.** "In principle functionality should be here and application
  in vom." The generic comic engine goes in this repo, the book's script, strips and
  scenery in `valley_of_mist`.
- **Order, 2026-10-09.** Start from the missing capabilities and build them as the
  panels need them, instead of drawing a rough page first. Simplifying the script is
  fine.

## Findings

### The state of the repo at the start, 2026-10-08

Observed by reading, not measured:

- `cover.py` (408 lines) composes a flat backdrop, mist bands, one figure and title
  text as SVG, and its docstring records the owner's decision to keep it simple and not
  compete with painted art. `sheet.py` (305 lines) tiles presets with labels.
- `Expression` carries deltas for the brow and eyelids and the mouth's curve and
  width. Six named ones exist (`presets.py`): stern, grim, hollow, wry, sorrow,
  resolute. None is a happy, surprised or angry face.
- There is no pose system. An arm swing is a rotation of the whole arm group, seen in
  the SVG as a `rotate(...)` group; the head is rigid. `CLAUDE.md` says "poses do not".
- The hands campaign (`hands-plan.md`) added five relaxed hands and a fist on a held
  staff, and nothing else about bodies changed.

**Not verified.** Whether the mouth can draw an open mouth or teeth, which decides
how much of the acting range is parameters and how much is new shape code. The first
study in K7 answers it.

### Code reading, 2026-10-09

The trailer in `../valley_of_mist` has already built the id prefix, a silhouette, a
placement, outline text and mist backdrops (`plan.md`). 
Seen in `character.py` and `cover.py`; the experiments are still to do. Two figures in
one document repeat the ids `hair-front`, `eye-l` and `eye-r` (checked on satoshi and
chiyo), and there are no stable layer ids. The mouth is a single quadratic stroke. An
arm is one rigid rotation with a fixed elbow. **Not verified:** that the repeated ids
change how a sheet draws, which K1's control answers.

### K1, 2026-10-09

**Control, predicted first:** that two figures in one document would draw the first one
wrongly. **Not held in the form predicted.** A positive control with two different clip
paths under one id confirms cairosvg resolves a repeated id to the **last** definition
(the first rectangle took the later, larger clip). But on four pairs of real figures
(satoshi and chiyo both ways, katherina and gero, daizen and keiko) the first figure
came out pixel-identical to the same figure alone, with duplicated ids and namespaced
alike. The definitions do differ between characters (the hair-front clip's markup
differs); the clipped content evidently does not reach the edge of either clip. Browsers
resolve a repeated id to the **first** definition and were not tested, so a web tool or
an SVG viewed in a browser may still show it. The trailer's author reports the clash.

**Built:** `render_character(..., id_prefix="")`. Every defined id, every `url(#x)` and
every `href="#x"` in the body gains the prefix. Empty is byte-identical to before: the
suite's `ref-out/` comparison passes unchanged. Two tests: the default is unchanged, and
with a prefix every id and reference is prefixed and removing the prefix gives the plain
document back. `ruff` clean, 626 passed, 1 skipped.

**Not done:** stable ids on the body-part groups, which the plan's invariant promises
and an animation will need. The figure has two `<g>` elements today. That is the next
step of K1's second half and is left until a panel or the animation asks for it.

### K2, 2026-10-09

**Built:** `anime_character_creator.comic` (`layout.py`): `Placement` (character, x, feet,
height, flip), `Panel` (frame, backdrop, figures, overlay, border), `Strip` (panels
stacked, margin, gutter, paper), `render_panel`, `render_strip`, `write_strip` (SVG, and
PNG when cairosvg is there). A figure stands on `feet_y` and is sized by its whole canvas,
as the cover does; a panel clips its contents, so a figure can be cropped by the frame.
Each figure takes its own id prefix (K1) and each panel its own clip id. The package
itself does not import `comic`. Eight tests (determinism, no id defined twice on a page,
every reference defined, flip, clipping, strip height, an oversized panel refused, an
empty strip); `ruff` clean, 634 passed, 1 skipped. The look, `harness/comic/k2_check.py`
-> `out/comic/k2.png`: two figures facing each other, a cropped close-up, a narrow centred
panel with a figure at its edge. All three draw as intended.

**Found: a flip mirrors the character's asymmetries.** Satoshi's sword moved to the other
hip in the test strip, and his scar moves to the other cheek, which breaks the one fixed
fact about his face. Two ways out, both small and not built: set `scar_side` opposite on a
flipped figure so the scar stays on the same cheek of the face (the book says the left jaw,
`presets.py`), or avoid flipping Satoshi and turn the other speaker. The same applies to
hair partings and a held staff. To be decided when a panel flips him, which beat A's
two-shots will (A4 to A6).

**Left out on purpose:** reading direction and page numbers (a strip has neither), a
sound-effect layer (K10), a panel's own palette (the backdrop is the caller's).

### K3, 2026-10-09

**Built.** `comic/text.py` is the trailer's `text.py` copied (HarfBuzz shapes the bundled
Gelasio font and each glyph is drawn as a path, so the same bytes come out on any
machine); the trailer is to switch to this copy as a change of its own. `comic/bubbles.py`
is new: `caption_svg` (the narrator's box, wrapped, returns its height) and `bubble_svg`
(an ellipse sized to its wrapped text, with a tail to a target point or without). The tail
is **part of the bubble's outline**, one path: the ellipse's arc the long way round between
two points either side of the line to the target, then out to the tip. A first version laid
a triangle against the ellipse and painted over the join; on a short tail the patch poked out
as a white notch, so it was replaced rather than tuned. `Placement.head()` gives a figure's
head in panel coordinates (mirrored under a flip) for aiming a tail. The `comic` extra
(`uharfbuzz`, `fonttools`) is in `pyproject.toml` and in the `dev` group, so a bare `uv sync`
runs the tests; the font and its licence (`comic/fonts/OFL.txt`) are bundled. Nine tests;
`ruff` clean, 643 passed, 1 skipped.

**The look**, `harness/comic/k3_check.py` -> `out/comic/k3.png`: beat A's real text on a
caption (A2), Chiyo's line (A3) and the two lines of A4. It reads. Two things the look
showed: a bubble needs headroom, and with the target too close to the ellipse no tail is
drawn (a guard, on purpose, so a bubble cannot grow a stump). **Open, taste:** the font is a
serif (Gelasio) in every bubble. Comic lettering is usually a sans or a hand face; a serif
reads as narration. Left alone until the owner says.

**Not built:** thought bubbles, shouted or whispered text, a bubble that is not an ellipse, and
placing bubbles automatically (the caller gives the centre).

### K6, 2026-10-09

**Built:** `supporting.py`, a `SUPPORTING` registry of `kenzo`, `dieter` and `driver`, with
`DISPLAY_NAMES`, kept out of `PRESETS` on the owner's condition. A test checks they render, have
names, and are neither presets nor offered by the web tool (`catalogue._cast_points`,
`_base_points`). Built only from the book's lines (`continuity_reference.md`): Kenzo "weathered the
color of an old oak sill", Dieter "thin, perpetually damp about the collar" in the occupiers' cooler
tones, the driver unnamed and plain. No reference exists and none is traced.

**The look**, `harness/comic/k6_check.py` -> `out/comic/k6.png`, all five at one scale. Kenzo
reads old (the oldest face, a short grey beard, a faded blue tunic); Dieter thin, pale and
resentful in grey-blue; the driver broad and brown. A first draft showed the driver with the
default pink cheeks, wrong on him, so `blush` is 0. **Not checked:** other palettes, as `CLAUDE.md`
asks of colour work. These three are fixed colours with no parametrised derivation of their own.
Waiting on the owner's look before a page uses them (C2).

### K4, K5, K7, K9 and beat A, first build, 2026-10-09

**Built here:** `comic/scenery.py` (rect, planks, window with a clipped view, table, the cover's
mist banks), `Placement.tone` (a one-tone silhouette: every fill and stroke replaced, opacity
dropped), `comic/props.py` (tray, mug), `Placement.hand(side)` (a hand in panel coordinates with
the arm's swing and a flip applied, over `character._hand_centre`), `FaceStyle.mouth_open` (0 is
the shut line, so every existing render is unchanged; the suite's `ref-out/` comparison passes) and
four expressions in `presets.py`: `startled`, `exasperated`, `alert`, `smile`. 730 tests pass.
Two redraws taught something: the open mouth first drew as a pointed wedge that read as a tongue,
so its lower edge became a fuller cubic; and a bubble placed over its speaker's head draws no tail,
so the caller leaves headroom.

**Built in `valley_of_mist`:** `valley_of_mist_tools/comic/` (`places.py`: the common room by day,
the room at night, the mist wall; `ch01.py`: panels A1 to A6; `build.py`) and
`shell_scripts/build_comic.sh`.

**Found while drawing:** Satoshi's preset carries his katana, and the beat is that his hand closes on
nothing at his hip. The chapter's Satoshi is the preset with `katana_color=None`, set in `ch01.py`,
not in the preset.

**Stand-ins, to be replaced by poses (K8) and a turn:**
- **A1:** Satoshi is a flat silhouette facing us, not seen from behind. It reads as a figure against
  the dark room, but it is front-on.
- **A5, the reflex:** an alert face, one arm swung out near the hip, the driver close at his
  shoulder. It does not show weight dropped low or a hand closed on air. **The weakest panel.**
- **A6:** the driver's raised hands are both arms swung out 58 degrees, which reads as a T. It is a
  surrender in the sense of the beat and looks stiff.
- **A4:** the tray handoff is two swung arms and a tray between them, hands under it.
- **Flip:** Chiyo is flipped in A4; Satoshi is never flipped yet, so the scar fix is not built.

**Not done:** C2 and C1 (the owner's look), the ids on body-part groups, beats B to D, and a pass at
the font.
