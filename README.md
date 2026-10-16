# Anime Character Creator

A 2D anime-style character creator that **draws characters
programmatically** from parametric vector shapes (SVG), rather than
compositing pre-made art. A small skeleton of proportion anchors
(head size, shoulder width, hip width, etc.) drives every shape,
hair, face, clothes, limbs, so style stays consistent by construction
instead of by curating matching assets. No AI image generation is
involved when a character is drawn (but see
[How this was made](#how-this-was-made): the code is AI-written, and the
designs began from AI-generated references).

Animation is out of scope. Backgrounds and text overlays are a
possible later addition (they'd slot in as extra SVG layers).

**The drawing code is TypeScript** (`ts/src/`, version 0.4.0). It draws the same bytes the Python
package drew, proved on a corpus of 7,662 characters (see "The TypeScript port" in `STATUS.md`),
and it is what the web tool, the SVG command line and the committed `ref-out/` art come from. The
Python package in `src/` is **frozen** at the tag `python-final`, as the reference the port was
measured against; it stays in the tree for one more release and is not developed. Work on the
drawing happens in `ts/`: see `ts/README.md`.

## Status

Fourteen named characters, plus guests. They are all the tall chibi, the one
figure since 2026-09-26, when the realistic build and the old compressed chibi
were retired; a `height` from 0.8 to 1.3 stretches it for a shorter or a
taller character. Risa is the exception in proportion: she is drawn on her own
longer body, measured off her reference (`docs/risa-plan.md`).

Every preset is **twenty-one or older**. The age of majority differs by
country, and twenty-one is the highest of the common ones, so that is the
floor: `ADULT_FACE_AGE` (`ts/src/model.ts`; `character.py` in the frozen Python),
which the tests, the web tool's age slider and the bare-body harness all read. `face_age` is a drawing setting, not
a number of years, so it is the floor that keeps a figure an adult, not a label.

**A rule for anything that uses this repository: never render a character
under twenty-one nude.** This tool draws the body bare only in a harness view
for proportion work, and only for faces at or above that floor
(`harness/bare/`). A consumer that draws a younger face of its own (the library
renders any `face_age`) must keep the figure clothed.

All are **first drafts**: each carries the colouring, frame and garments
its design calls for, judged at the size a character is actually seen on a
sheet rather than at full height. What is deliberately left off is listed
per cluster in `docs/character-roster-plan.md`, and the two least finished
are Krista and Chiyo, whose references lean hardest on a head accessory.

| Satoko | Satoshi | Kyoko | Tomohiro |
| --- | --- | --- | --- |
| <img src="ref-out/on-white/satoko.png" width="140" alt="Satoko"> | <img src="ref-out/on-white/satoshi.png" width="140" alt="Satoshi"> | <img src="ref-out/on-white/kyoko.png" width="140" alt="Kyoko"> | <img src="ref-out/on-white/tomohiro.png" width="140" alt="Tomohiro"> |

| Chiyo | Daizen | Elara | Haruto |
| --- | --- | --- | --- |
| <img src="ref-out/on-white/chiyo.png" width="140" alt="Chiyo"> | <img src="ref-out/on-white/daizen.png" width="140" alt="Daizen"> | <img src="ref-out/on-white/elara.png" width="140" alt="Elara"> | <img src="ref-out/on-white/haruto.png" width="140" alt="Haruto"> |

| Keiko | Krista | Reika | Reinhard |
| --- | --- | --- | --- |
| <img src="ref-out/on-white/keiko.png" width="140" alt="Keiko"> | <img src="ref-out/on-white/krista.png" width="140" alt="Krista"> | <img src="ref-out/on-white/reika.png" width="140" alt="Reika"> | <img src="ref-out/on-white/reinhard.png" width="140" alt="Reinhard"> |

| Tenno | Viktor | Katherina | Gero |
| --- | --- | --- | --- |
| <img src="ref-out/on-white/tenno.png" width="140" alt="Tenno"> | <img src="ref-out/on-white/viktor.png" width="140" alt="Viktor"> | <img src="ref-out/on-white/katherina.png" width="140" alt="Katherina"> | <img src="ref-out/on-white/gero.png" width="140" alt="Gero"> |

| Linnea | Dritan | Lindita | Risa |
| --- | --- | --- | --- |
| <img src="ref-out/on-white/linnea.png" width="140" alt="Linnea"> | <img src="ref-out/on-white/dritan.png" width="140" alt="Dritan"> | <img src="ref-out/on-white/lindita.png" width="140" alt="Lindita"> | <img src="ref-out/on-white/risa.png" width="140" alt="Risa"> |

There are two finishes. **Flat** is the house style, the default, and what every preset, cover and
sheet uses: flat colour, hard edges, one black line. **Soft** is an opt-in for a figure that has to
sit beside painted art: gradients in the iris and blush, tinted lines, and tone clumps in the hair on
five of the cuts. `highlight_strength` (0 to 2, default 1) sets how strong those are. See "The soft
finish" in `docs/api.md`; the web tool has a Finish choice and a strength slider.

All of them live in `ref-out/` as both `.png` and `.svg`. **They are
transparent**, so a render drops onto a scene as it is.

Under the clothes there is a body. The tunic and the boots are optional
like every other garment, and with the tunic off a figure shows its body in
a plain base layer (underwear that is always worn), with bare feet when the
boots come off too. That is what lets new garments be layered over a real
torso and skin tones be judged on more than a face and two hands; the web
tool offers the toggles and a row of skin tone swatches. See
`docs/bare-body-plan.md`.

They are also only two people. Kyoko is Satoko before the dye and the
burn, and Tomohiro is Satoshi the same way, so each pair is one preset
and a `replace()` of three fields rather than two sets of numbers that
happen to agree. That is deliberate: the resemblance is the point, and a
copied face keeps it only until somebody tunes an eye. See
`docs/character-roster-plan.md`.

The table is the tall chibi, the only figure since 2026-09-26: the
realistic build, which never worked as well, was retired with its
`ref-out/real/` renders (`docs/tall-chibi-plan.md`).

`ref-out/cover.svg` is there too: a book cover composed around one of
them by `cover.py`, which is the same drawing code with a backdrop, mist
and a title stacked over it. That one is opaque, being a page rather than
a figure. Render it with `./cover.sh`.

`ref-out/sheet.svg` is the whole cast on one page, from `sheet.py`. That
is where a cast gets judged rather than a character: whether these people
look like they come from one world is a question about the set. Render it
with `./sheet.sh`.

`ref-out/sheet_satoshi.svg` is the same page with the other of the two
reference rosters: Satoshi's persona rather than Satoko's, so Tomohiro
stays and Satoko and Kyoko drop. Ten of the twelve are the same
characters as `sheet.svg`; `presets.ROSTERS["satoshi"]` is the one place
that says which two swap. Render it with `./sheet_satoshi.sh`.

`sheet.py` also takes `--members name1,name2,...`, an arbitrary subset
overriding `--roster`, a hook for a consumer that generates one character
sheet per chapter, restricted to whoever that chapter names (`render.sh`,
`cover.sh`). This repo stays the generic drawing tool; the consumer owns the chapter-scanning and
publication-specific detail.

The tables above link `ref-out/on-white/`, which is the same characters
drawn on a white background. That exists for this page and nothing else:
the outline is `#0d0d0d` and a dark theme here is about `#0d1117`, so a
transparent figure on it loses its whole outer contour, which is the
hard-edged look the project is for. Reach for the transparent ones for
anything real.

Both sets are the current state of the named characters, so they have to
be refreshed whenever a shape changes, otherwise these tables show art
the code no longer produces:

```bash
./refresh-ref-out.sh          # re-render every named character, report what moved
./refresh-ref-out.sh --check  # compare only, write nothing, exit 1 if stale
```

It renders every character in `PRESETS` and both pages, so adding a character means adding it to
`ts/src/presets.ts` and nothing else. The characters' SVG comes from the TypeScript (`ts/bin/render.ts`), each
PNG is made from that SVG by cairosvg in Python (`harness/svg2png.py`), and the cover and the two sheets are
still drawn by the frozen Python (`cover.sh`, `sheet.sh`). `./refresh-catalogue.sh` and `./refresh-bases.sh`
do the same for `ref-out/catalogue.json` and `ref-out/bases/`, and `./refresh-ref-out.sh --pixels` compares
decoded PNG pixels when a change moves the SVG's text and no visible pixel.
Everything else generated goes to `out/`, which is not checked in.

Current shape set: head (a circle at chibi scale, narrowing to a jaw as
the build gets taller), face (eyes, brows, mouth, blush, scar, spectacles),
a beard, five hairstyles that optionally divide into locks and change to a
second tone over their lower half, and a layered outfit of tunic,
undersleeves, belt, apron, skirt, underskirt, trousers and boots, plus
uniform trim (standing collar, button placket, chest pockets, cross-body
strap, tall boot shaft), an open coat at any length, and robe pieces
(crossed front, hanging sleeve, obi), plus arms, legs and feet. All flat
cel-shaded. A garment is worn when its color is set, so characters differ
by which layers they have rather than by bespoke code.

Named characters live in `ts/src/presets.ts`, so a character is a checked-in
artifact that gets re-rendered as the shape code improves.

Not yet built: no pose variety, no picker UI, and no hair that leaves the
skull silhouette and comes back, which is what a ponytail and a topknot
both need. See `STATUS.md` for what is still weak and
`docs/character-roster-plan.md` for what each character is still waiting
on.

## Setup

```bash
cd ts && npm ci    # typescript and @types/node, for the typecheck and the web build
```

Node 22.18 or newer runs the `.ts` files directly, with no build step, and the drawing has no runtime
dependencies: an SVG document is text. `npm ci` is only for the checks and for compiling the web tool.

PNG export, the cover and the sheets are the frozen Python (`cairosvg` needs the system `cairo` library):

```bash
uv sync            # venv, dependencies, dev tools, and the frozen package (editable)
brew install cairo # for PNG export
```

## Usage

The SVG command line is TypeScript:

```bash
node ts/bin/render.ts --out out/satoko --preset satoko        # writes out/satoko.svg
node ts/bin/render.ts --out out/risa-soft --preset risa --finish soft --highlight-strength 0.7
node ts/bin/render.ts --out out/white --preset satoshi --background white --no-metadata
node ts/bin/render.ts --list                                  # the names --preset takes
```

`--preset` takes any character in `PRESETS` or either neutral base (`female`, `male`). `--finish soft`
draws the soft finish and `--highlight-strength` (0 to 2, default 1, soft only) sets how strong the hair
clumps are. `--background` is any SVG paint; the default is transparent. `--id-prefix` namespaces every id
in the drawing, for a page that holds several figures. Every render embeds a link that reproduces the exact
character in an SVG `<metadata>` block by default (`--no-metadata` for a plain, minimal file); the file is
byte for byte the one the Python CLI writes for the same arguments. It has no colour, garment or face
flags: take a preset and use the library below, or the web tool, for a variant. `node ts/bin/catalogue.ts`
writes the web tool's catalogue JSON.

For a PNG, rasterise the SVG with the same call the Python CLI makes:

```bash
.venv/bin/python harness/svg2png.py out/satoko.svg out/satoko.png    # scale 2, as the CLI does
```

As a library, from TypeScript (Node 22.18 or newer; there is no index file, so import from the module that
has the name, see `docs/api.md`):

```ts
import { writeFileSync } from "node:fs";
import { replace } from "./ts/src/model.ts";
import { PRESETS } from "./ts/src/presets.ts";
import { renderCharacter } from "./ts/src/render.ts";
import { buildSkeletonWith } from "./ts/src/skeleton.ts";

const satoko = PRESETS["satoko"]!;
writeFileSync("out/satoko-mid.svg", renderCharacter(satoko, buildSkeletonWith({ heads: 4.0 })));

// a variant of a named character
const grumpier = replace(satoko, { face: replace(satoko.face, { brow_tilt: 0.6 }) });
```

### The web tool

`web/` is a plain page that draws in the visitor's browser with the TypeScript compiled to ES modules, no
server and no Python. To run it locally:

```bash
cd ts && npm ci && cd ..    # once, for tsc
./web-stage.sh --serve      # same as: node web-stage.mjs --serve; open http://127.0.0.1:8000/
```

`web-stage.mjs` compiles `ts/src` with `tsc` (`ts/tsconfig.web.json`) and copies the page and `ref-out/` beside
it into `out/web-stage/`, the layout the GitHub Pages workflow deploys. Set `TSC` to use another tsc binary.

### The full command line (frozen Python)

The Python CLI has every flag below, and writes the PNG as well. It is frozen, so use it for the options the
TypeScript CLI does not have; for the options both have, the SVG is the same.

`render.sh` is the way in. It runs the CLI from the project's own venv
with the one environment variable PNG export needs, since `cairosvg`
loads `libcairo` through `dlopen`, which on macOS doesn't look in
Homebrew's prefix.

```bash
./render.sh --out out/demo \
  --hair-color "#e8b84b" --eye-color "#4a9c6d" \
  --outfit-color "#4f7a52" --skin-tone "#f2c9a1" --boot-color "#5b4632"

./render.sh --out out/satoko --preset satoko
./render.sh --out out/satoshi --preset satoshi
```

The same CLI is installed as `anime-character-creator` and as
`python -m anime_character_creator`; both skip the cairo environment
`render.sh` sets, so on macOS they write the SVG and report that PNG
export is unavailable.

`--preset` starts from a named character in `presets.py`; any flag given
alongside it overrides that one value.

Garment flags, one per layer: `--tunic-color` (also spelled
`--outfit-color`), `--undersleeve-color`, `--belt-color`,
`--apron-color`, `--skirt-color`, `--underskirt-color`,
`--trouser-color`, `--pouch-color`, `--boot-color`, plus `--skirt-length` (hip 0 to ankle
1). A layer is worn when it has a color, so these add layers; to take one
away, drop it from the preset, since the command line has no way to say
"none".

Shape flags: `--hairstyle` (`long_blunt`, `long_center_part`, `long_parted`,
`long_traced`, `long_fringed`, `short_crop`, `short_layered` or `short_tousled`),
`--hair-length`, `--frame` (shoulder against hip, -1 to 1, only bites at
taller builds).

Expression flags, each neutral at its default: eye shape
(`--eye-size`, `--eye-width`, `--eye-openness`, `--eye-lower-lid`,
`--eye-tilt`, `--eye-corner`, `--iris-size`), plus `--brow-tilt`, `--brow-weight`,
`--mouth-curve`, `--mouth-width`, `--blush`, `--scar-side`.

```bash
./render.sh --out out/grumpy --mouth-curve -0.6 --blush 0 --brow-tilt 0.5
```

`--expression` lays a named mood (`hollow`, `stern`, `grim`, `sorrow`,
`resolute`) over the character's resting face, changing only what the
face is *doing* and leaving what it *is* alone, so the same mood works on
any character. Individual knobs still win over it.

`--finish soft` draws the soft finish (gradients, tinted lines and tone clumps in the
hair) instead of the flat house style, and `--highlight-strength` (0 to 2, default 1,
soft only) sets how strong the hair clumps are:

```bash
./render.sh --out out/risa-soft --preset risa --finish soft --highlight-strength 0.7
```

Add `--flat` to disable the cel-shading shadow shapes and see the flat
silhouette only. Output is written as both `.svg` (inspect/edit
directly in a browser or Inkscape) and `.png` (if cairosvg works).

Every render embeds a link that reproduces the exact character back into
both files, by default: an SVG `<metadata>` block, and a PNG `tEXt` chunk
(keyword `Source`, readable with any tool that reads PNG text, e.g.
Pillow's `Image.open(...).text`) carrying the same link, so a file that
leaves this repo, downloaded, shared, dropped into another project, stays
reconstructable. `sheet.sh` does the same with one link per member and
`cover.sh` with the featured character. Pass `--no-metadata` to skip it and
get a plain, minimal file. (This is a CLI-only default: `render_character()`
and friends default to *off* as a library, which is what keeps `ref-out/`
byte-for-byte comparable; see `attribution.py`.)

**The background is transparent**, so a render drops onto a scene as it
is. Pass `--background white` (or any SVG paint) if you want it filled.

## How it works

The drawing package is `ts/src/`. Longer notes on the machinery are in
[docs/architecture.md](docs/architecture.md), the public surface is written up in [docs/api.md](docs/api.md),
and how to work in the TypeScript (layout, commands, the oracle, adding a part) is in [ts/README.md](ts/README.md).
The names below are the TypeScript files, with the frozen Python module in parentheses.

- `skeleton.ts` (`skeleton.py`): the `Skeleton` interface: head center/radius, the
  neck/shoulder/waist/hip/hem/limb widths, and the y-coordinates (neck,
  shoulder, waist, hip, hem, knee, ankle, foot) every shape positions
  itself against. Every character's comes from `skeletonFor(p)` (`body.ts`): its body profile
  (`BODY_TYPES`, measured tall-chibi proportions) laid over the chibi
  build, stretched by `height` when that is not 1.0.
  `hair_margin` is the headroom above the skull, in head radii, so hair
  has somewhere to go at a build where the head fills a third of the
  frame.
- `colorutil.ts` (`colorutil.py`): `shade()` derives a darker/more-saturated
  "shadow" tone from a base color, so palettes for cel-shading are
  computed, not hand-picked per shape.
- `render.ts`, `character.ts`, `hair.ts`, `face.ts`, `garments.ts`, `props.ts` and the rest (`character.py`):
  build each body part as an SVG shape (paths,
  circles, capsule-strokes) positioned from the skeleton, then stack
  them in z-order into one `<svg>` document. `CharacterParams` (`params.ts`) holds the
  colors, an `Outfit` of garments, and a `FaceStyle` of expression knobs
  (eye aperture shape, brow tilt/weight, mouth curve/width, blush, cheek
  scar); `renderCharacter()` is the entry point. The eye is an almond
  built from four quadratics, so one set of knobs spans a tall round
  chibi eye and a narrow lidded adult one. `HAIRSTYLES` (`core-head.ts`) maps a name to
  the four outlines a haircut needs, plus an optional set of strands
  dividing the mass into locks, which is how a second cut gets added
  without touching the parts that draw hair.
- `pynum.ts` and its neighbours: the kernel, every Python behaviour JavaScript lacks (number
  formatting, `round`, `sum`, `hypot`, slices, `json.dumps`), which is what keeps the output byte-identical.
- `presets.ts` (`presets.py`): named characters as `CharacterParams` values,
  `SATOKO` and `SATOSHI` among twenty. Reachable from the CLI via `--preset`. The two
  share a palette through module constants, since they are meant to read
  as related.
- `bin/render.ts` and `bin/catalogue.ts`: the command lines. (`generate.py` is the frozen Python CLI.)

## Development

```bash
cd ts && npm ci          # once
npm run typecheck        # tsc, strict
npm test                 # the TypeScript tests (node:test, several hundred)
npm run build:web        # compile the package and stage the web tool into ../out/web-stage
cd .. && ./refresh-ref-out.sh --check && ./refresh-catalogue.sh --check && ./refresh-bases.sh --check
uv run pytest            # the frozen Python's suite, which must keep passing until it is removed
uv run ruff check .      # lint the frozen Python (the TypeScript is checked by tsc)
```

The TypeScript tests compare the port with the frozen Python (a corpus of 7,662 characters recorded
from it, the committed `ref-out/`, and a fresh run of the Python CLI where a `.venv` exists), and hold
the rules the Python suite held (ids unique, the silhouette's ceiling, flat stays flat, validation).
They are a guard against a change that moves a byte, not a judge of whether a shape looks right: that
is decided by eye, against the design intent.

`CLAUDE.md` holds the rules a change to this repo has to respect, and
`STATUS.md` is the running state: what is done, what is weak, what is
next.

## How this was made

**This project was built with AI coding agents**, directed by its owner: mostly
**Claude Code** (Anthropic), with some work done with **Cursor** (using Grok models)
and **opencode** (using the free "Big Pickle" model). AI-written code can be
wrong; the repository has a test suite, but treat it as you would any software
you have not read line by line.

- **The drawing** is ordinary code: no image generator runs when a character is
  drawn. But the characters' designs began from AI-generated reference images
  (some made with Grok, kept in `ref/`), which set the style and the first
  roster, and several characters, Katherina and Risa among them, were traced
  from such references.
- **The documentation** was written by Claude Code.
- **Commits** here carry no co-author trailer (this repository's own rule), so
  the history does not show which were AI-written: assume most of the code was.
- The companion app that uses this
  was built the same way and says so in its own README.

## Design principles

- **No pre-drawn art, no scraping.** Every pixel comes from shapes
  this code defines. This sidesteps licensing entirely and is what
  keeps every character on-model.
- **Skeleton-relative, not hardcoded coordinates.** Every shape is a
  function of `head_r` and the anchor y-values, not fixed pixels, so
  adjusting proportions (e.g. moving away from chibi later) doesn't
  require touching every shape.
- **Flat color, hard-edged (no gradients), and no shading plane across
  a garment.** Matches the target cel-shaded anime look and is cheap to
  render. A second tone is for small elements, a pouch flap, a boot
  cuff, the turn under a hem, where it reads as thickness; a tunic,
  skirt or trouser leg stays one flat color and gets its form from the
  outline and the line work.
- **Iterate on shape, not variety, first.** Get one hairstyle/outfit
  looking right before adding a second, a shape template with wrong
  proportions is wrong for every character generated from it.
