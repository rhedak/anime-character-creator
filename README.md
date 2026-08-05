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

Proof of concept: two characters, Satoko and Satoshi, each rendering at
both ends of the build range. Build is a named mode, `--build chibi`
(default) or `--build realistic`, with `--heads` open for anything in
between. Renders are generated, not checked in;
`./render.sh --preset satoko` writes one to `out/`.

Current shape set: head (a circle at chibi scale, narrowing to a jaw as
the build gets taller), face (eyes, brows, mouth, blush, scar), two
hairstyles optionally fading to a second tone at the ends, and a layered
outfit of tunic, undersleeves, belt, apron, skirt, underskirt, trousers
and boots, plus arms, legs and feet. All flat cel-shaded (base color plus
one shadow tone). A garment is worn when its color is set, so characters
differ by which layers they have rather than by bespoke code.

Named characters live in `src/presets.py`, so a character is a
checked-in artifact that gets re-rendered as the shape code improves.

Not yet built: arms are still capsules with circles for hands, which is
the weak point at taller builds; also no pose variety, no second outfit
family, no picker UI. See `STATUS.md`.

## Setup

```bash
uv venv
uv pip install -r requirements.txt
brew install cairo
```

`cairosvg` (for PNG export) needs the system `cairo` library. If it's
missing, generation still writes a valid `.svg`, you just don't get a
`.png`.

## Usage

`render.sh` is the way in. It runs `src/generate.py` under the venv
with the one environment variable PNG export needs, since `cairosvg`
loads `libcairo` through `dlopen`, which on macOS doesn't look in
Homebrew's prefix.

```bash
./render.sh --out out/demo \
  --hair-color "#e8b84b" --eye-color "#4a9c6d" \
  --outfit-color "#4f7a52" --skin-tone "#f2c9a1" --boot-color "#5b4632"

./render.sh --out out/satoko --preset satoko
./render.sh --out out/satoko-tall --preset satoko --build realistic
./render.sh --out out/satoshi --preset satoshi
```

`--preset` starts from a named character in `src/presets.py`; any flag
given alongside it overrides that one value.

Garment flags, one per layer: `--tunic-color` (also spelled
`--outfit-color`), `--undersleeve-color`, `--belt-color`,
`--apron-color`, `--skirt-color`, `--underskirt-color`,
`--trouser-color`, `--boot-color`, plus `--skirt-length` (hip 0 to ankle
1). A layer is worn when it has a color, so these add layers; to take one
away, drop it from the preset, since the command line has no way to say
"none".

Shape flags: `--hairstyle` (`long_blunt` or `short_layered`),
`--hair-length`, `--frame` (shoulder against hip, -1 to 1, only bites at
taller builds).

Expression flags, each neutral at its default: eye shape
(`--eye-size`, `--eye-width`, `--eye-openness`, `--eye-lower-lid`,
`--eye-tilt`, `--eye-corner`, `--iris-size`), plus `--brow-tilt`, `--brow-weight`,
`--mouth-curve`, `--mouth-width`, `--blush`, `--scar-side`.

```bash
./render.sh --out out/grumpy --mouth-curve -0.6 --blush 0 --brow-tilt 0.5
```

Add `--flat` to disable the cel-shading shadow shapes and see the flat
silhouette only. Output is written as both `.svg` (inspect/edit
directly in a browser or Inkscape) and `.png` (if cairosvg works).

## How it works

- `src/skeleton.py`: `Skeleton` dataclass: head center/radius, the
  neck/shoulder/waist/hip/hem/limb widths, and the y-coordinates (neck,
  shoulder, waist, hip, hem, knee, ankle, foot) every shape positions
  itself against. The whole thing derives from `heads`, how many
  head-heights tall the figure stands, which `BUILDS` names as `chibi`
  (2.4) and `realistic` (6.0). Both the widths and where the landmarks
  sit along the body interpolate between the two: a chibi is nearly
  neckless with high hips in a short body, an adult is not. `frame`
  scales shoulder against hip on top of that, and `Skeleton.build` hands
  parts the position along the range so they don't recompute it.
- `src/colorutil.py`: `shade()` derives a darker/more-saturated
  "shadow" tone from a base color, so palettes for cel-shading are
  computed, not hand-picked per shape.
- `src/character.py`: builds each body part as an SVG shape (paths,
  circles, capsule-strokes) positioned from the skeleton, then stacks
  them in z-order into one `<svg>` document. `CharacterParams` holds the
  colors, an `Outfit` of garments, and a `FaceStyle` of expression knobs
  (eye aperture shape, brow tilt/weight, mouth curve/width, blush, cheek
  scar); `render_character()` is the entry point. The eye is an almond
  built from four quadratics, so one set of knobs spans a tall round
  chibi eye and a narrow lidded adult one. `HAIRSTYLES` maps a name to
  the four outlines a haircut needs, which is how a second cut gets added
  without touching the parts that draw hair.
- `src/presets.py`: named characters as `CharacterParams` values,
  `SATOKO` and `SATOSHI`. Reachable from the CLI via `--preset`. The two
  share a palette through module constants, since they are meant to read
  as related.
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
