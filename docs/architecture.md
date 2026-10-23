# Architecture

How the generator is put together, for someone changing it. The public
surface is in [api.md](api.md), the current state of the art and what is
weak in `../STATUS.md`, and the rules a change has to respect in
`../CLAUDE.md`. The drawing code is TypeScript (`../ts/src/`, how to work in it is
`../ts/README.md`); the Python it was ported from, byte for
byte, is deleted from the tree (the tag `python-final` keeps it). Names below are the TypeScript ones, camelCase, with the Python name where it helps a reader
who knows the old code (`_hair_mass` is `hairMass`); the parts registry keeps the Python names, since
that is how `render.ts` calls them.

## The whole pipeline

```
CharacterParams ─┐
                 ├─► renderCharacter ─► [ part(sk, p) -> string, ... ] ─► one <svg> string
Skeleton ────────┘      (render.ts, z-order)
```

There is no scene graph, no canvas object and no state. Each part is a
function that takes the skeleton and the params and returns a
string of SVG elements, `renderCharacter` concatenates them back to
front, and the result is text. That is the whole design, and it is what
makes the output deterministic and comparable byte for byte.

Two consequences worth knowing before changing anything:

- **A part draws nothing by returning `""`.** That is how absent garments
  work. No flags, no conditionals in the stack.
- **Ordering in the `slots` list of `render.ts` (`layers` in the Python) is the z-order.** Legs go under the
  skirts so a hem covers the thigh; arms go over every garment so nothing
  can clip a hand. Moving a part in that list is a visual change.
- **The ear's depth says something about how a cut is built.** It sits
  over the head and under `_hair_front`, which is the canon's own
  arrangement: back hair passes behind the ear, front locks over it.
  Whether the ear then *reads* is the cut's business, not the ear's, and
  the two things a cut has to get right are easy to miss.
  - **Leave the ear somewhere to be seen.** A hairline whose fill covers
    everything the mass covers leaves no gap, and the ear all but
    vanishes. That was a real bug in `short_crop` for a round.
    Its fringe runs temple to temple and stops there now, which is why
    its ear reads at both builds.
  - **Put the side locks in front, or make the mass clear the ear.** A
    cut whose side locks live only in the mass cannot cover an ear,
    because the mass is behind the head and the ear is on it.
    `long_blunt` and `short_layered` are both like that, so a hint of ear
    shows at Satoko's temples until her cut is re-authored. `short_crop`
    is the one that gets this right today.

## Modules

The package is `ts/src/`, by role (the same table is in `../ts/README.md`):

| Files | What lives there |
| --- | --- |
| `skeleton.ts`, `body.ts` | `Skeleton` and `buildSkeleton`: every proportion anchor, all derived from `heads`; `BODY_TYPES` and `skeletonFor`, a character's skeleton. Change proportions here, not in a part. |
| `colorutil.ts` | `shade()` and hex conversion, with `colorsys`. The one place a shadow tone is decided. |
| `params.ts`, `model.ts`, `plain.ts` | The field registry (`CharacterParams`, `Outfit`, `FaceStyle`, `Expression`, with defaults and type tags), the constructors and `replace`, and the reading of a wrong-typed value from a link. |
| `character.ts`, `core-head*.ts`, `core-limbs*.ts` | The shared vocabulary: stroke widths, `curve`, the document wrapper and the post-steps; the hair system (`Hairstyle`, `HAIRSTYLES`, the cuts, the head's paths); sleeves, arms, hands and the traced garment cuts. |
| `hair.ts`, `face.ts`, `face-wear.ts`, `body-parts*.ts`, `garments.ts`, `props.ts` | The parts, one function per body part. |
| `parts.ts`, `parts-*.ts`, `render.ts` | The registry of parts by name, and `renderCharacter`, which stacks them. |
| `*-tables.ts` | Traced coordinates, generated from the Python once and owned by hand. |
| `presets.ts`, `supporting.ts` | Named characters as `CharacterParams` values, the neutral bases, the moods, the rosters. |
| `urlstate.ts`, `attribution.ts`, `catalogue*.ts`, `web-bridge.ts` | Links, the `<metadata>` block, what the web tool offers, and the web tool's four calls. |
| `pynum.ts`, `pyjson*.ts`, `pycodecs.ts`, `pyre.ts`, `pyvalue.ts`, `sha1.ts` | The kernel: every Python behaviour JavaScript lacks, which keeps the bytes equal. |
| `../ts/bin/render.ts`, `../ts/bin/catalogue.ts` | The command lines, with `../ts/bin/cover.ts` and `../ts/bin/sheet.ts` for the cover and the cast sheets. |

The parts share a large vocabulary (`curve`, `arc`, `mirror`, `strokeW`, the hair constants). The
Python kept it in one 14,000-line `character.py` on purpose; the port split it by role into files of roughly
500 to 1,500 lines, with the shared helpers in `character.ts` and `core-*.ts` that the part files import.

Arithmetic is kept exactly as the Python wrote it: floating point is not associative, so a part is not
simplified, reordered or folded, and every number reaches the text through the kernel's formatters
(`fmt1`, `fmt2`, and so on), never `toFixed`. `../ts/README.md` has the rules.

## Two coordinate systems

Everything below the neck is in **canvas pixels**, taken from skeleton
anchors: `sk.hip_y`, `sk.shoulder_half_w`, and so on. Nothing is a
literal pixel value. A part that needs a measurement should read an
anchor, or a fraction of one, rather than multiplying `head_r` by a
number that only happens to work on a chibi.

The head, face and hair are in **head-radius units**: origin at the head
centre, `1.0` is one head radius, y positive downward. `_head_units`
maps a point into canvas coordinates and `_curve` builds a whole path
from `(start, [(control, end), ...])` point data. Shapes are kept as
point data rather than as format strings so a silhouette can be reshaped
without rewriting SVG.

Hair splits that further, because a haircut has two halves that behave
differently:

- **Above the cheek line** (`_HAIR_CHEEK_Y = 0.72`) hair is pinned to the
  skull, so points are literal head-radius units.
- **Below it** the hair is a *fall*, and points are a fraction of the way
  down to the tips (`_fall(f, length)`). That is what lets `hair_length`
  restyle a cut without touching its crown, and what keeps a long cut in
  the same relationship to the body when the build changes.

## The skull profile, and the ear on it

`headPt(deg, radius, build)` (`_head_pt`) is the single definition of where the
skull's edge is. `headShape` walks it to lay the outline down, and
`headEdgeX(y, build)` samples it to answer "how far off centre is the
head at this height", which is what a part welded to the head needs. It
samples rather than inverting because the jaw taper moves a point in
both axes at once, so there is no closed form; the point of routing both
through one function is that the ear cannot drift off the head when the
taper is retuned, and there is a test that says so.

The ear is placed by `earSpan(build)` and drawn by `earOuter(build)`,
both in head-radius units on the right side, mirrored per side. Its
span, `_EAR_TOP_Y` to `_EAR_BOT_Y`, is measured off the canon rather than
taken from anatomy: the life-drawing rule of brow to nose put it 0.16
head radii too high. **A hairstyle should read that span rather than
guess where the side of the head is**, which is the reason it is stated
as named constants at all.

## The build parameter

`buildSkeletonWith({ heads: N })` computes `build`: `0.0` at a 2-head chibi,
`1.0` at 6 heads and up. Every width and every landmark position
interpolates along it, and any part that has to deform along the range
reads `sk.build` rather than recomputing it from `heads`. Examples in
the code: the boot's toe grows with it, the eye shrinks and lids slightly
with it, the nose line appears only above `0.5`.

`frame` (shoulder against hip) rides on `build`, so it bites at the tall
builds and all but vanishes at a chibi, where the head swamps the torso
anyway.

## Style rules the code enforces

- **Flat colour, hard-edged, and no shading plane across a garment.** No
  gradients, no blur. Where a second tone does appear it comes from
  `shade()`, never hand-picked, so a palette change carries.
  `shade()`'s output belongs on small elements, a pouch flap, a boot
  cuff, the turn under a hem, where it reads as thickness. A garment
  panel stays one flat colour: the tunic, skirt, apron, sleeve and
  trouser shadows were all deleted in task 56 because a plane across a
  panel reads as painted on rather than as light, and a stripe down
  anything as long and thin as a limb reads as two-tone at any width.
  Drape on the skirt is a line, not a tone.
- **One outline colour** (`OUTLINE`) for every line on the figure.
- **Line weight is figure-relative.** `_stroke_w(sk)` is the silhouette
  weight, measured off the canon at about 0.017 of head width at chibi
  and 0.023 at the tall build. Every other line is a fraction of it
  (0.85 for interior contours, 0.55 for hair strands, 1.6 for the upper
  lash, and so on), so the whole figure re-weights together.

## The hair contract

Hair is the one part with an internal contract, because it is drawn as
several pieces that have to look like one. A `Hairstyle` is five
callables, each taking the tip depth in head radii:

1. `mass` carries the **entire outer contour**. No other piece adds
   silhouette.
2. `fall_edge` is the stretch of that contour the front lock retraces
   **exactly**. Where the mass shows, the two strokes land on each other;
   where the body hides the mass, the lock carries the silhouette on. If
   these two disagree by a pixel it reads as a double line.
3. `hairline` is the only line drawn *inside* the mass. Its two ends have
   to land on the mass's own lock tips, or the fringe stops in mid-air.
4. `tip_edge` is where the two tones meet, as a **list of closed
   regions**. A clip path is the union of its children, so one region per
   lock composes with no other machinery, and a cut whose locks all hang
   the same way can still return a single region. None of them is ever
   stroked, so the lower half of each can be anywhere convenient
   (`floor`).

   A list rather than one region because one region can only say "pale
   below this height", while the canon says "pale from here to the tip of
   *this lock*", which is a different boundary per lock and cannot be one
   curve unless the locks happen to line up. Two things this is not: it
   is not a shading plane, so the flat-colour rule is untouched, that
   rule is about garment panels and hair has carried two tones since the
   start; and it is not a licence to move the *amount* of pale, which is
   `_HAIR_FADE` and is the owner's call. Keep it a list, never a set or a
   dict's values, or `ref-out/` stops comparing byte for byte.
5. `strands` are open chains dividing the mass into locks, clipped to the
   front fill. Without them a cut reads as an object the colour of hair
   rather than as hair.

Two constants tie the tones and the headroom down:

- `_HAIR_FADE` is where the two tones meet, as a fraction of the hair's
  own height from crown to lowest tips, shared by both cuts. It is a
  fraction of the whole silhouette rather than of the fall on purpose:
  the fall lengthens with the body while the crown stays on the skull, so
  a fall fraction lands at a different height per build and colours the
  same character two ways.
- **No hair ink may reach above `-(1 + hair_margin)` head radii**, and
  the outer half of the stroke counts as ink. Nothing in the shape code
  derives that bound, so a taller crown comes out silently sliced flat
  against the canvas edge, which is how both chibis shipped once. A cut
  that needs more headroom raises `hair_margin` with it.
  `test_hair_stays_under_the_canvas_ceiling` is what makes the failure
  loud: it solves each quadratic for its own extremum, since the topmost
  anchor understates a crown that peaks between two anchors and the
  topmost control point overstates every crown. The slack today is 16px
  on the long cut's chibi and 2px on the short cut's adult, so a spiked
  crown will need the margin raised, not trimmed to fit.

## Adding things

**A body part.** Write `fooBar(sk, p): string` using only `sk.*`
anchors and `p.*` params, return `""` when the character does not have
it, export it from the domain's `parts-*.ts` table as `_foo_bar`, and add it to the `slots` list in
`render.ts` at the right depth, with a slot number nobody has used (the number is its stage name in the
oracle). `../ts/README.md`, "How a part is added", has the steps.

**A garment.** Add a colour field to `Outfit` in `params.ts` defaulting to `null`, draw
it in a part that returns `""` when the field is `null`, and name the
field in `catalogue-tables.ts` if the web tool should offer it.

<a id="adding-a-hairstyle"></a>
**A hairstyle.** Write the five callables above, keeping the contract,
and add a `Hairstyle` to `HAIRSTYLES` in `core-head.ts`. Nothing that draws hair changes.
Give it a `tip_range` if the cut ends on the head rather than on the
body: a cut ending above the chin cannot be described in chin-to-hip
units at all.

**A character.** Add a `characterParams({...})` to `presets.ts` and re-render
`ref-out/`. Anything the character needs to differ on goes on
`CharacterParams`, `Outfit` or `FaceStyle` with a neutral default. A
value hardcoded into a part function for one character is the one thing
that turns the generator into that character's renderer.

**A command line option.** `ts/bin/render.ts` takes its options from the `parseArgs` call in `main()`; add the
flag there and a case to `ts/test/cli.test.ts`. The Python CLI's flags came from three tables in `generate.py`
(gone with it); the TypeScript one is deliberately small.

## Working loop

Shape work is iterate-by-looking. The coordinates that are right in the
arithmetic are routinely wrong on screen, and most of the fixes in this
repo came from looking rather than from reasoning.

```bash
node ts/bin/render.ts --out out/tmp --preset satoko   # then view out/tmp.svg, or make a PNG:
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib:/usr/local/lib   # macOS: lets cairosvg find Homebrew's cairo
tools/.venv/bin/python harness/svg2png.py out/tmp.svg out/tmp.png
./refresh-ref-out.sh                                  # same change as any shape edit
(cd ts && npm run typecheck && npm test)              # types, then the oracle and the rules
```

Render candidates **side by side** rather than one at a time: build the variants as `replace`d characters, or as
scratch copies of `ts/` with one function changed (an ES module's exports cannot be patched from outside, as
the Python's could), render three or four variants into one strip, and pick by eye. Include the reference and the
current state as columns. Suppressing a feature entirely is a legitimate
column: a render with the hair strands turned off is what proved they
were carrying the difference.

A script just imports the modules by path (the package has no build step), and `replace` swaps a field:

```ts
import { replace } from "./ts/src/model.ts";
import { PRESETS } from "./ts/src/presets.ts";
import { renderCharacter } from "./ts/src/render.ts";

const variant = (k: number) =>
  renderCharacter(replace(PRESETS["satoko"]!, { hair_length: k }));
```

The shape tables are typed read-only, so a script that wants to try another cut edge works on a scratch copy of
`ts/` or edits the entry in `core-head*.ts`, rather than patching the shared `HAIRSTYLES` as the Python could.

When a comparison shows no difference at all, check that the variant was
actually applied before concluding the knob does not matter.

For the other half of the loop, comparing what comes out against the
reference art, there is tooling: the retired `gap-analysis` skill
(`harness/gap_analysis_skill/`, kept as a record, Python). `probe.py` there builds the normalised
strips and takes the measurements, its `PITFALLS.md` records how naive
pixel measurement went wrong here, and `gap-analysis.md` beside this file
is the current result.

## Things that are easy to break

- **Determinism.** Same params, same bytes. Anything that iterates a set,
  reads a clock or hashes an object breaks `ref-out/` comparison and the
  test that guards it. In TypeScript, an object with integer-like keys iterates in a different order than
  in the Python; use a `Map`.
- **Number spelling.** A number printed with `toFixed`, a template string or `Math.round` instead of the
  kernel's formatters rounds ties differently from Python's and moves a digit. Nothing outside `pynum.ts` does it.
- **`ref-out/` going stale.** It is committed, and the README displays
  its `on-white/` copies, which are the same drawings with a white card
  behind them for a page whose background colour is not ours to set.
  Refresh it in the same change as any shape edit; `--check` and the test
  suites both catch a miss, and `--check` counts a missing card as stale
  too, since that breaks the README while the art itself is current.
- **The hair ceiling**, above.
- **Coordinate tables that wrap.** The shape data is rows, one lock per
  row, often a mirrored pair. A row long enough for the formatter to wrap
  stops reading as the twin of the row beside it. Shorten it, or build
  the pair with `mirror` the way `longStrands` does.
