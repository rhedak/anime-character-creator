# Anime Character Creator

A 2D anime-style character creator that **draws characters
programmatically** from parametric vector shapes (SVG), rather than
compositing pre-made art. A small skeleton of proportion anchors
(head size, shoulder width, hip width, etc.) drives every shape,
hair, face, clothes, limbs, so style stays consistent by construction
instead of by curating matching assets. No AI image generation is
involved anywhere in the pipeline.

Animation is out of scope. Backgrounds and text overlays are a
possible later addition (they'd slot in as extra SVG layers).

## Status

Proof of concept: a front-facing character renders end-to-end from
`src/character.py`, fully parametrized by skin/hair/eye/outfit/boot
color. Build is a named mode, `--build chibi` (default) or
`--build realistic`, with `--heads` open for anything in between. See
`out/` for
example renders. Current shape set: head, face (eyes, brows, mouth,
blush), shoulder-length hair (optionally fading to a second tone at
the ends), dress-style outfit, arms, legs, boots; all flat cel-shaded
(base color + one shadow tone).

Named characters live in `src/presets.py`, so a character is a
checked-in artifact that gets re-rendered as the shape code improves.

Not yet built: layered outfits (the single dress shape is the weak
point at taller builds, where a torso has room for real garment
layers), alternate hairstyles/poses, a picker UI.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`cairosvg` (for PNG export) needs the system `cairo` library. On
macOS: `brew install cairo`. If it's missing, generation still writes
a valid `.svg`, you just don't get a `.png`.

## Usage

```bash
cd src
python generate.py --out ../out/demo \
  --hair-color "#e8b84b" --eye-color "#4a9c6d" \
  --outfit-color "#4f7a52" --skin-tone "#f2c9a1" --boot-color "#5b4632"

python generate.py --out ../out/satoko --preset satoko
python generate.py --out ../out/satoko-tall --preset satoko --build realistic
```

`--preset` starts from a named character in `src/presets.py`; any flag
given alongside it overrides that one value. Besides colors there are
expression flags, each neutral at its default: eye shape
(`--eye-size`, `--eye-width`, `--eye-openness`, `--eye-lower-lid`,
`--eye-tilt`, `--eye-corner`, `--iris-size`), plus `--brow-tilt`, `--brow-weight`,
`--mouth-curve`, `--mouth-width`, `--blush`, `--scar-side`.

```bash
python generate.py --out ../out/grumpy --mouth-curve -0.6 --blush 0 --brow-tilt 0.5
```

Add `--flat` to disable the cel-shading shadow shapes and see the flat
silhouette only. Output is written as both `.svg` (inspect/edit
directly in a browser or Inkscape) and `.png` (if cairosvg works).

## How it works

- `src/skeleton.py`: `Skeleton` dataclass: head center/radius, the
  neck/shoulder/hip/hem/limb widths, and the y-coordinates (neck,
  shoulder, waist, hip, hem, knee, ankle, foot) every shape positions
  itself against. The whole thing derives from `heads`, how many
  head-heights tall the figure stands, which `BUILDS` names as `chibi`
  (2.4) and `realistic` (7.0). Both the widths and where the landmarks
  sit along the body interpolate between the two: a chibi is nearly
  neckless with high hips in a short body, an adult is not.
- `src/colorutil.py`: `shade()` derives a darker/more-saturated
  "shadow" tone from a base color, so palettes for cel-shading are
  computed, not hand-picked per shape.
- `src/character.py`: builds each body part as an SVG shape (paths,
  circles, capsule-strokes) positioned from the skeleton, then stacks
  them in z-order into one `<svg>` document. `CharacterParams` holds
  the color inputs plus a `FaceStyle` of expression knobs (eye
  aperture shape, brow tilt/weight, mouth curve/width, blush, cheek
  scar); `render_character()` is the entry point. The eye is an almond
  built from four quadratics, so one set of knobs spans a tall round
  chibi eye and a narrow lidded adult one.
- `src/presets.py`: named characters as `CharacterParams` values, e.g.
  `SATOKO`. Reachable from the CLI via `--preset`.
- `src/generate.py`: CLI: renders one character to SVG, rasterizes to
  PNG via `cairosvg` if available.

## Design principles

- **No pre-drawn art, no scraping.** Every pixel comes from shapes
  this code defines. This sidesteps licensing entirely and is what
  keeps every character on-model.
- **Skeleton-relative, not hardcoded coordinates.** Every shape is a
  function of `head_r` and the anchor y-values, not fixed pixels, so
  adjusting proportions (e.g. moving away from chibi later) doesn't
  require touching every shape.
- **Flat color + one shadow tone per surface**, hard-edged (no
  gradients), matches the target cel-shaded anime look and is cheap
  to render.
- **Iterate on shape, not variety, first.** Get one hairstyle/outfit
  looking right before adding a second, a shape template with wrong
  proportions is wrong for every character generated from it.
