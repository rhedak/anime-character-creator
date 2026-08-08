# API reference

What the package exposes, what each value means, and the shape of a
typical call. For how the drawing itself is put together, see
[architecture.md](architecture.md); for how to run the CLI, see the
README.

Everything below is importable from the top-level package:

```python
from anime_character_creator import (
    BUILDS, DEFAULT_BUILD, DEFAULT_HEADS, HAIRSTYLES, PRESETS,
    CharacterParams, FaceStyle, Hairstyle, Outfit, Skeleton,
    build_skeleton, render_character, shade,
)
```

A generated HTML version of this surface, straight from the docstrings:

```bash
uv run pdoc anime_character_creator -o out/apidocs   # writes HTML
uv run pdoc anime_character_creator                  # serves it locally
```

It covers what is re-exported above, which is the public API. The
reasoning behind the shapes lives in the private functions of
`character.py`, in docstrings pdoc does not show, so read those in the
source: they are the record of what was tried and why the numbers are
what they are.

## render_character

```python
render_character(p: CharacterParams | None = None,
                 sk: Skeleton | None = None,
                 background: str | None = None) -> str
```

Draws one character and returns the whole SVG document as a string.
Nothing is written to disk and nothing is rasterized. All three arguments
are optional: no params gives the stock character, no skeleton builds one
from `p.heads` and `p.frame`.

`background` is any SVG paint and defaults to none, so the figure comes
out on transparency and composites straight onto a scene. Pass
`background="white"` for an opaque document. One thing to know before
measuring a render: a tool that finds the figure by looking for near-white
background has to flatten the alpha onto white first, or every transparent
pixel reads as black and the whole canvas counts as ink.

```python
svg = render_character(PRESETS["satoko"])
svg = render_character(PRESETS["satoko"], build_skeleton(heads=6.0, frame=-0.3))
Path("out/satoko.svg").write_text(svg)
```

The output is deterministic: same arguments, same bytes. That is what
lets `ref-out/` be compared byte for byte instead of eyeballed, and it is
worth preserving, so avoid anything time- or set-ordering-dependent in
the shape code.

Pass a skeleton whenever the two knobs on `CharacterParams` are not
enough: another canvas size, more headroom for a tall hairstyle, a build
between the named ones.

## CharacterParams

Frozen dataclass, the public description of a character. Make a variant
with `dataclasses.replace`:

```python
from dataclasses import replace
angry_satoko = replace(SATOKO, face=replace(SATOKO.face, brow_tilt=0.8))
```

| Field | Default | Meaning |
| --- | --- | --- |
| `skin_tone` | `#f2c9a1` | Hex colour. |
| `hair_color` | `#e8b84b` | Hex colour. |
| `hair_tip_color` | `None` | Second tone the hair changes to lower down. `None` is single-tone hair. |
| `hair_length` | `0.45` | What the cut's own range means by "long": see `Hairstyle.tip_range` below. |
| `hairstyle` | `"long_blunt"` | A key of `HAIRSTYLES`. |
| `eye_color` | `#4a9c6d` | Hex colour. |
| `outfit` | `Outfit()` | The garments, below. |
| `face` | `FaceStyle()` | The expression, below. |
| `heads` | `2.4` | Head-heights tall. Ignored when a skeleton is passed. |
| `frame` | `0.0` | Shoulder against hip, -1 to 1. Ignored when a skeleton is passed. |
| `shaded` | `True` | `False` drops every shadow shape, leaving flat silhouettes. |

Anything a character needs to differ on belongs here, on `Outfit` or on
`FaceStyle`, with a neutral default. Nothing character-specific belongs
in a part function.

## Outfit

One field per garment. **A garment is worn when its colour is set**, so a
character states only the layers it has and the parts that draw absent
garments return an empty string. There is no "off" switch and no flag per
piece.

| Field | Default | Notes |
| --- | --- | --- |
| `tunic_color` | `#4f7a52` | Always worn. |
| `boot_color` | `#5b4632` | Always worn. |
| `undersleeve_color` | `None` | Long sleeve under the tunic's short one. `None` leaves the arm bare. |
| `belt_color` | `None` | A belt with no apron over it also draws a buckle. |
| `apron_color` | `None` | Front panel hanging from the belt, over the skirt. |
| `skirt_color` | `#4f7a52` | `None` for a character in trousers. |
| `underskirt_color` | `None` | Longer skirt beneath the first, its hem showing below. |
| `trouser_color` | `None` | Fills the legs, which are otherwise bare skin. |
| `pouch_color` | `None` | A pouch on each hip. Needs a belt to hang from. |
| `skirt_length` | `None` | Hem, hip `0` to ankle `1`. `None` uses the skeleton's hem anchor. |
| `tunic_tucked` | `False` | Tunic ends inside the belt band instead of hanging to the hip, and trousers rise to meet it. |

## FaceStyle

Expression knobs, each neutral at its default, so a character states only
what it differs on. The eye is one almond aperture built from four
quadratics, and these deform it; there is no second eye shape to choose.

| Field | Default | Meaning |
| --- | --- | --- |
| `eye_size` | `1.0` | Scales the whole aperture. |
| `eye_width` | `0.88` | Width against height. Below 1 is a tall eye, above 1 a long narrow one. |
| `eye_openness` | `1.0` | How high the upper lid rides. The iris keeps its size and gets cropped, which is what reads as lidded rather than small-eyed. |
| `eye_lower_lid` | `1.0` | How far the lower lid drops. Below 1 flattens the underside. |
| `eye_tilt` | `0.10` | Raises the outer corner above the inner one. |
| `eye_corner` | `0.35` | `0` a rounded oval, `1` all four corners pulled to points. |
| `iris_size` | `0.72` | Iris against the aperture's smaller half-axis. Below 1 leaves sclera all round. |
| `brow_tilt` | `0.0` | Positive drops the inner ends (stern), negative raises them (worried). |
| `brow_weight` | `1.0` | Brow stroke against the figure's own line weight. |
| `mouth_curve` | `1.0` | `1` the stock smile, `0` flat, negative a frown. |
| `mouth_width` | `1.0` | |
| `blush` | `1.0` | `0` removes the cheek patches. |
| `scar_side` | `0` | `-1` left cheek, `1` right, `0` none. |

## Skeleton and build_skeleton

```python
build_skeleton(canvas_w=400, canvas_h=500, heads=2.4, frame=0.0,
               hair_margin=0.36, bottom_margin=0.03) -> Skeleton
```

Every proportion the shapes position themselves against, derived from one
number: `heads`, how many head-heights tall the figure stands. `BUILDS`
names the two ends, `chibi` (2.4, the default) and `realistic` (6.0), and
anything in between is a number.

The returned frozen `Skeleton` carries the canvas size, `heads`, the
head centre and radius, the y of every landmark from neck to foot, the
half-widths at neck, shoulder, waist, hip, hem, arm and leg, where the
arms hang (`arm_x`), and `build`.

`build` is the useful one for shape code: `0.0` at a 2-head chibi, `1.0`
at 6 heads and up, so a part that has to deform along the range reads it
rather than recomputing it from `heads`.

The two margins are room, not proportion: `hair_margin` is headroom above
the skull in head radii (a hairstyle that reaches higher than the current
`0.36` allows needs this raised with it, nothing derives it from the
shapes), and `bottom_margin` is the gap under the feet as a fraction of
canvas height.

## HAIRSTYLES and Hairstyle

`HAIRSTYLES` maps a name to a `Hairstyle`. Ships with `long_blunt`,
`short_layered`, `short_tousled` and `short_crop`; `DEFAULT_HAIRSTYLE`
names the first.

A `Hairstyle` is the four outlines a haircut needs, which have to agree
with each other, plus an optional fifth:

| Field | What it is |
| --- | --- |
| `mass` | The silhouette. The only outer contour the hair has. |
| `hairline` | The fringe and side locks drawn in front of the face, as `(start, line, back)`. |
| `fall_edge` | The stretch of the mass's outer edge the front lock retraces, exactly. |
| `tip_edge` | Where the two tones meet, as a list of closed regions covering everything below each. They clip to their union, so a cut can give each lock its own boundary. |
| `strands` | Optional open chains dividing the mass into locks. |
| `tip_range` | What `hair_length` 0 and 1 mean for this cut, as depth below the head centre. `None` measures the body instead, chin to hip. |
| `volume` | How much bigger the cut is at the chibi end than at the adult end, as `(chibi, adult)` multipliers on `tip_range`'s answer. `None` keeps one size against the head at every build. The canon gives a chibi about 1.3 times an adult's hair, so a cut traced off one reference wants this to reach the other. A cut that raises it needs `hair_margin` to have room for it, and the ceiling test says so. |

Each callable takes the tip depth in head radii and returns point data in
head-radius units (origin at the head centre, `1.0` is one head radius).
Adding a cut is adding an entry here; the parts that draw hair do not
change. The agreement rules those five have to keep are in
[architecture.md](architecture.md#adding-a-hairstyle).

## PRESETS

Named characters as `CharacterParams` values: `PRESETS["satoko"]` and
`PRESETS["satoshi"]`, also importable as `SATOKO` and `SATOSHI` from
`anime_character_creator.presets`. They are checked-in artifacts that get
re-rendered as the shape code improves, which is what `ref-out/` holds.

Add a character here rather than as a pile of CLI flags. Both current
presets share a palette through module constants, since they are meant to
read as related.

## EXPRESSIONS and Expression

Named moods: `EXPRESSIONS["hollow"]`, `"stern"`, `"grim"`, `"sorrow"`,
`"resolute"`. Apply one with either method:

```python
face = EXPRESSIONS["hollow"].on(PRESETS["satoshi"].face)      # a FaceStyle
satoshi = EXPRESSIONS["hollow"].applied_to(PRESETS["satoshi"])  # a whole character
```

**An `Expression` is a delta, not a `FaceStyle`, and that is the point.**
A `FaceStyle` mixes what a face *is* (`eye_size`, `eye_width`,
`eye_corner`, `eye_tilt`, `iris_size`) with what it is *doing*
(`brow_tilt`, `eye_openness`, `mouth_curve`). A mood that arrived as a
whole `FaceStyle` would overwrite the first group with stock values and
hand back a different character wearing the right expression, rendering
perfectly the whole time. So every field defaults to `None`, meaning
leave that one alone, and only the named fields are written. `None`
rather than a neutral number because no number means "unchanged": `0.0`
is a real brow tilt.

Only mood fields exist on it. Adding `eye_size` would make it a way for a
character to stop being themselves.

One measured note, from choosing the cover's face: **the brow is the weak
lever.** Brow-only moods shift under 1% of the face whether you look at a
head crop or a thumbnail, while anything touching `eye_openness` shifts
two to three times that, because a brow is a thin stroke and a lid is the
edge of a filled shape. A mood that has to survive being shrunk moves a
lid.

## shade

```python
shade(hex_color: str, value_factor: float = 0.80,
      saturation_boost: float = 1.08) -> str
```

The shadow tone for a base colour: darker and slightly more saturated.
Use it rather than hand-picking a second colour per part, which is what
keeps a palette consistent when someone changes the base. `hex_to_rgb01`
and `rgb01_to_hex` sit alongside it in `colorutil` for the odd conversion.

## CLI

`anime_character_creator.generate.main()` is the console script
`anime-character-creator`, also reachable as
`python -m anime_character_creator`. Its flags are generated from three
tables in that module (`COLOR_ARGS`, `OUTFIT_ARGS`, `FACE_ARGS`), so a new
field on the dataclasses becomes a flag by being named there. See the
README for the flag list.
