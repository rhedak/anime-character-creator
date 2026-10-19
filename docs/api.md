# API reference

What the TypeScript package exposes, what each value means, and the shape of a typical call. The package is
`ts/src/` (version 0.4.0, the source of truth since the port; `ts/README.md` is the map). The frozen Python
package (deleted from the tree on 2026-10-19; the tag `python-final` keeps it) had the same surface under snake_case names, given in parentheses below. For how the drawing
itself is put together, see [architecture.md](architecture.md); for how to run the command lines, see the README.

There is no index file. Each name is imported from the module that defines it, with the `.ts` extension
(Node 22.18 or newer runs the files as they are):

```ts
import { renderCharacter } from "./ts/src/render.ts";                    // render_character
import { characterParams, outfit, faceStyle, replace } from "./ts/src/model.ts";
import type { CharacterParams, Outfit, FaceStyle, Expression } from "./ts/src/params.ts";
import { PRESETS, NEUTRAL_BASES, EXPRESSIONS, ROSTERS } from "./ts/src/presets.ts";
import { buildSkeleton, buildSkeletonWith, BUILDS, type Skeleton } from "./ts/src/skeleton.ts";
import { skeletonFor, BODY_TYPES } from "./ts/src/body.ts";
import { HAIRSTYLES, type Hairstyle } from "./ts/src/core-head.ts";
import { shade } from "./ts/src/colorutil.ts";
```

| Name (Python name) | Module |
| --- | --- |
| `renderCharacter`, `renderStages` (`render_character`) | `render.ts` |
| `characterParams`, `outfit`, `faceStyle`, `expression` (the dataclass constructors), `replace` (`dataclasses.replace`), `validateFinish`, `agedFace`, `expressionOn`, `expressionAppliedTo` (`Expression.on`, `.applied_to`), `FINISHES`, `ADULT_FACE_AGE` | `model.ts` |
| `CharacterParams`, `Outfit`, `FaceStyle`, `Expression` (interfaces), the field registries (`CHARACTERPARAMS_FIELDS` and the rest) | `params.ts` |
| `PRESETS`, `NEUTRAL_BASES`, `EXPRESSIONS`, `ROSTERS`, the named characters (`SATOKO`, ...), `aged` | `presets.ts` |
| `SUPPORTING`, `DISPLAY_NAMES` | `supporting.ts` |
| `Skeleton`, `buildSkeleton`, `buildSkeletonWith`, `BUILDS`, `DEFAULT_BUILD` (`build_skeleton`) | `skeleton.ts` |
| `skeletonFor`, `BODY_TYPES` (`skeleton_for`) | `body.ts` |
| `HAIRSTYLES`, `Hairstyle` | `core-head.ts` |
| `shade`, `tint`, `hexToRgb01`, `rgb01ToHex` (`hex_to_rgb01`, `rgb01_to_hex`) | `colorutil.ts` |
| `encodeParams`, `decodeParams`, `characterUrl`, `paramsToDict`, `paramsFromDict` (`encode_params`, ...) | `urlstate.ts` |
| `metadataBlock` (`metadata_block`) | `attribution.ts` |
| `buildCatalogue`, `toJson` (`build_catalogue`, `to_json`) | `catalogue.ts` |
| `render`, `stateForStart`, `encode`, `decode` | `web-bridge.ts` (the web tool's four calls) |
| `PyError`, the kernel | `pynum.ts` |

Parameter keys stay snake_case (`hair_color`, `highlight_strength`) because they are the wire format of
links, JSON and the catalogue. Functions are camelCase of the Python names (`_hair_fall` is `hairFall`); a
module-level table keeps its name.

The Python docstrings, in the frozen `character.py`, and the JSDoc on the TypeScript beside them are the
record of what was tried and why the numbers are what they are.

## renderCharacter

```ts
renderCharacter(p?: CharacterParams | null,
                sk?: Skeleton | null,
                background: unknown = null,
                metadata: unknown = false,
                id_prefix: unknown = ""): string
```

(`render_character`.) Draws one character and returns the whole SVG document as a string. Nothing is written
to disk and nothing is rasterized. Every argument is optional: no params gives the stock character, no
skeleton builds one with `skeletonFor(p)`. The arguments are in Python's order; `renderCharacterWith(p,
{ sk, background, metadata, id_prefix })` takes them by name.

`background` is any SVG paint and defaults to none (`null`), so the figure comes out on transparency and
composites straight onto a scene. Pass `"white"` for an opaque document. One thing to know before
measuring a render: a tool that finds the figure by looking for near-white
background has to flatten the alpha onto white first, or every transparent
pixel reads as black and the whole canvas counts as ink.

`metadata` embeds the `<metadata>` block: the tool, the licence, the novel and a link that reproduces the
character (`attribution.ts`). It is off in the library, which is what keeps `ref-out/` byte-for-byte
comparable, and on in the web tool's downloads and in the command line by default.

`id_prefix` puts every id the drawing defines, and every reference to one,
under a prefix (`hair-front` becomes `f1-hair-front`). Empty is the document
as it always was. Give each figure its own when several share one SVG, or a
viewer resolves a repeated id to a single definition and they clip each
other's hair.

```ts
const svg = renderCharacter(PRESETS["satoko"]);
const tall = renderCharacter(PRESETS["satoko"], buildSkeletonWith({ heads: 6.0, frame: -0.3 }));
writeFileSync("out/satoko.svg", svg);
```

The output is deterministic: same arguments, same bytes. That is what
lets `ref-out/` be compared byte for byte instead of eyeballed, and it is
worth preserving, so avoid anything time- or set-ordering-dependent in
the shape code.

Pass a skeleton whenever the two knobs on `CharacterParams` are not
enough: another canvas size, more headroom for a tall hairstyle, a build
between the named ones.

**Errors.** Where the Python raises, so does this, with a `PyError` whose `pyType` is the Python exception class
(`ValueError`, `TypeError`, `ZeroDivisionError`, `KeyError`, ...) and whose message is the port's own
(`docs/ts-port-errors.md` lists where it differs from CPython's). A character from a link can carry a string in a
number field; it is kept and raises `TypeError` at the first arithmetic on it, as in Python, and a field the
drawing never reads never complains.

**Ints and floats.** JavaScript has one number type; the field registry (`params.ts`) says which fields are
ints (`scar_side`, for one) and decides how a number is spelt when a character is written to JSON or a link
(`1.0` against `1`).

## The soft finish

`CharacterParams.finish` is `"flat"` (the default, the house style, and the
only finish the presets and `ref-out/` use; the web tool offers it as a "Finish"
choice that starts on flat, and a link carries it) or `"soft"`, an opt-in experiment for a caller that
wants the figure beside painted art:

```ts
const svg = renderCharacter(replace(PRESETS["risa"]!, { finish: "soft" }));
```

`node ts/bin/render.ts --preset risa --finish soft` is the same from the command line.
Soft adds gradients and tinted lines and moves no shape: the fringe's shadow
on the forehead, a graded iris with light bouncing up into it, a soft blush,
outlines in a dark tone of the hair or skin they bound, and every line 0.66 of
its weight. A cut that describes its clumps (`Hairstyle.locks`: `long_fringed`,
`long_traced`, `long_parted`, `short_layered` and `short_crop`) also gets shadow
and lit tone clumps over the hair, each lit one with a faint highlight, inside
the hair's own silhouette. Gradients only, no blur, so the cairosvg PNGs match
what a browser draws. An unknown finish raises `ValueError` (`validateFinish`). `FINISHES` lists
the two.

`highlight_strength` scales the clumps, 0 to 2, soft only (the flat finish
ignores it and a bad value is refused only for soft). 0 draws none, 1 is the
default, and 2 is the strength they were first drawn at, a bit strong on pale
hair. `--highlight-strength` sets it on the command line.

## CharacterParams

A frozen interface (`params.ts`; a frozen dataclass in the Python), the public description of a character.
`characterParams({...})` fills the defaults and refuses a name that is not a field. Make a variant with
`replace` (`dataclasses.replace`):

```ts
import { replace } from "./ts/src/model.ts";
import { SATOKO } from "./ts/src/presets.ts";
const angrySatoko = replace(SATOKO, { face: replace(SATOKO.face, { brow_tilt: 0.8 }) });
```

The three tables below are unchanged by the port: the same fields, the same names, the same defaults. A
`None` is `null` in TypeScript.

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
| `body` | `"tall_chibi_long_torso"` | The body profile, from `BODY_TYPES`: `tall_chibi` (Katherina's, measured), the long torso, or `tall_slender` (Risa's, about 4.4 heads, with a narrow neck and arm and its own wrist anchors). |
| `frame` | `0.0` | Shoulder against hip, -1 to 1. Ignored when a skeleton is passed. |
| `bust` | `0.0` | How much bust the figure carries, 0 to 1; 0 draws the figure as it was before the bust existed. Ignored when a skeleton is passed: build it with `buildSkeleton` (`bust`). See `docs/bust-plan.md`. |
| `height` | `1.0` | How tall the figure stands against its head, 0.8 to 1.3 in the web tool: below the shoulder line the figure is this many times as long, two thirds of the difference in the legs. See `docs/tall-chibi-plan.md`, R4b. |
| `chest` | `0.0` | Chest definition shown bare, 0 to 1: two soft arcs under the pectorals, drawn only with the tunic off and no bust. See `docs/bare-body-plan.md`, step 6. |
| `waist_shift` | `0.0` | Moves the waist and hip lines together, in head radii: negative up, positive down. Ignored when a skeleton is passed. |
| `shaded` | `True` | `False` drops every shadow shape, leaving flat silhouettes. |
| `finish` | `"flat"` | `"flat"` or `"soft"`, see "The soft finish" above. |
| `highlight_strength` | `1.0` | How strong the soft finish's hair clumps are, 0 to 2. Soft only. |
| `right_arm_out`, `left_arm_out` | `0.0` | Swings that whole arm out from the body about the shoulder, in degrees, positive away from the body. `right_arm_out` is the character's own right arm, which is the viewer's left. Past 90 degrees the arm rises above the shoulder: about 115 to 140 reads as hands raised. The elbow does not bend. |
| `hand_style` | `"mitten"` | The relaxed hand, one of `HAND_STYLES`: `mitten` (the default), `notched`, `stroked`, `curled`, `traced`. Every preset wears the mitten. See `docs/hands-status.md`. |
| `grip_style` | `"mitten"` | The hand that holds a staff, one of `GRIP_STYLES`: `mitten` (the default) or `fist`, the canon's rounded fist kept level against the arm's swing. |

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
| `tunic_color` | `#4f7a52` | `None` takes the tunic off, with its placket, chest pockets and long sleeve, and the body shows. See `docs/bare-body-plan.md`. |
| `boot_color` | `#5b4632` | `None` draws bare feet. |
| `knee_sock_color` | `None` | A knee sock over the leg, under the boot. Risa's. |
| `ribbon_color` | `None` | A traced bow at the throat, over the collar and under the coat. |
| `hip_pocket_color` | `None` | A flap pocket on each hip, over the coat. Needs a traced coat. |
| `coat_button_color` | `None` | The coat's buttons, a line of three. Needs a traced coat. |
| `neckline_notch` | `None` | How deep the tunic's V is, in head radii. `None` keeps each case's own depth. |
| `underwear_color` | `#e8e4dc` | The base layer, always worn: underpants under every bare leg, and a top with the tunic off. |
| `underwear_top` | `False` | The top is drawn with the tunic off whenever there is a bust; this adds one without. |
| `undersleeve_color` | `None` | Long sleeve under the tunic's short one. `None` leaves the arm bare. |
| `belt_color` | `None` | A belt with no apron over it also draws a buckle. |
| `apron_color` | `None` | Front panel over the skirt. A belt over it covers its top edge; without one the adult woman's apron has its own sash. |
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
| `brow_length` | `1.0` | How long each brow runs, against the eye's width. |
| `brows_over_hair` | `False` | Draws the brows over the fringe instead of under it. |
| `eye_gap` | `None` | The gap between the eyes as a share of an eye's half-width. `None` keeps the cast's median. |
| `iris_inset` | `0.0` | How far each iris sits toward the nose, by a share of the room it has. `1` is against the inner corner. |
| `iris_aspect` | `1.0` | The iris's height against its width. Above 1 is a tall oval that fills a tall aperture. |
| `lid_shadow` | `0.0` | A greyer band of shadow along the upper lid on the white, as a share of the eye's height. |
| `nose_dot` | `False` | The nose as one dot, in place of the two ticks. |
| `mouth_drop` | `0.0` | The mouth lower in the face, in head radii. |
| `mouth_curve` | `1.0` | `1` the stock smile, `0` flat, negative a frown. |
| `mouth_width` | `1.0` | |
| `blush` | `1.0` | `0` removes the cheek patches. |
| `eyes_closed` | `False` | Both eyes shut, each drawn as one lash line across the open aperture's own corners. A moment (a blink), not a mood, so it is not on `Expression`. |
| `scar_side` | `0` | `-1` left cheek, `1` right, `0` none. |

## Skeleton and buildSkeleton

```ts
buildSkeleton(canvas_w = 400, canvas_h = 500, heads = 2.4, frame = 0.0, bust = 0.0,
              hair_margin = null, bottom_margin = 0.03, min_hair_margin = 0.0): Skeleton
buildSkeletonWith({ heads: 6.0, frame: -0.3 })       // the same, by name
```

(`build_skeleton`, with Python's parameters in Python's order; an `undefined` takes the default.) Every
proportion the shapes position themselves against, derived from one
number: `heads`, how many head-heights tall the figure stands. `BUILDS`
names the chibi (2.4), the one build since the realistic build was retired
(`docs/tall-chibi-plan.md`); `buildSkeleton` still takes any `heads`,
since a body profile builds its base skeleton at its own height. A
character's skeleton comes from `skeletonFor(p)` (`skeleton_for`): its `body` profile over
the chibi build, stretched by its `height`.

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

`HAIRSTYLES` (`core-head.ts`) maps a name to a `Hairstyle`. Ships with eight cuts: `long_blunt`,
`long_center_part`, `long_parted`, `long_traced`, `long_fringed`, `short_crop`, `short_layered` and
`short_tousled`.

A `Hairstyle` is the four outlines a haircut needs, which have to agree
with each other, plus an optional fifth:

| Field | What it is |
| --- | --- |
| `mass` | The silhouette. The only outer contour the hair has. |
| `hairline` | The fringe and side locks drawn in front of the face, as `(start, line, back)`. |
| `fall_edge` | The stretch of the mass's outer edge the front lock retraces, exactly. |
| `tip_edge` | Where the two tones meet, as a list of closed regions covering everything below each. They clip to their union, so a cut can give each lock its own boundary. |
| `strands` | Optional open chains dividing the mass into locks. `strand_weight` sets how heavy they are against the outline. |
| `openings` | Optional patches of skin drawn over the front hair, an ear between two locks. |
| `front_shade` | Optional regions of the front hair painted in a second, darker tone. |
| `underside` | Optional darker hair behind, where the mass shows. |
| `locks` | Optional clumps for the soft finish: `(role, centre line, width, length)` tuples in head radii, `role` being `"shadow"` or `"lit"`. `mass_locks` also draws them on the mass behind the head, for a short cut whose crown is the mass. |
| `tip_range` | What `hair_length` 0 and 1 mean for this cut, as depth below the head centre. `None` measures the body instead, chin to hip. |
| `volume` | How much bigger the cut is at the chibi end than at the adult end, as `(chibi, adult)` multipliers on `tip_range`'s answer. `None` keeps one size against the head at every build. The canon gives a chibi about 1.3 times an adult's hair, so a cut traced off one reference wants this to reach the other. A cut that raises it needs `hair_margin` to have room for it, and the ceiling test says so. |

Each callable takes the tip depth in head radii and returns point data in
head-radius units (origin at the head centre, `1.0` is one head radius).
Adding a cut is adding an entry here; the parts that draw hair do not
change. The agreement rules those five have to keep are in
[architecture.md](architecture.md#adding-a-hairstyle).

## PRESETS

Named characters as `CharacterParams` values: `PRESETS["satoko"]`,
`"satoshi"`, `"kyoko"` and `"tomohiro"` among twenty, also importable as `SATOKO`,
`SATOSHI`, `KYOKO` and `TOMOHIRO` from `ts/src/presets.ts`. `NEUTRAL_BASES` holds the two bases the
web gallery paints first, and `ROSTERS` the named groups the sheets use.
They are checked-in artifacts that get re-rendered as the shape code
improves, which is what `ref-out/` holds. Every preset is twenty-one or
older.

Add a character here (`presets.ts`) rather than as a pile of CLI flags. The four share a
palette through module constants, since they are meant to read as
related.

**Kyoko and Tomohiro are derived, not written.** They are Satoko and
Satoshi before the dye and the burn, so they come out of a `_before()`
helper (`before`) that is a `replace()` of three fields (`hair_color`,
`hair_tip_color`, `scar_side`) rather than a second set of numbers. The
same reasoning as `Expression` below: the shared face is a property the
story depends on, and a copy holds it only until somebody tunes an eye on
one of the four. Derive a character from another whenever they are
supposed to stay the same underneath.

## EXPRESSIONS and Expression

Named moods: `EXPRESSIONS["hollow"]`, `"stern"`, `"grim"`, `"sorrow"`,
`"resolute"`, and more. Apply one with either function (from `model.ts`):

```ts
const face = expressionOn(EXPRESSIONS["hollow"]!, PRESETS["satoshi"]!.face);        // a FaceStyle (Expression.on)
const satoshi = expressionAppliedTo(EXPRESSIONS["hollow"]!, PRESETS["satoshi"]!);   // a whole character (applied_to)
```

**An `Expression` is a delta, not a `FaceStyle`, and that is the point.**
A `FaceStyle` mixes what a face *is* (`eye_size`, `eye_width`,
`eye_corner`, `eye_tilt`, `iris_size`) with what it is *doing*
(`brow_tilt`, `eye_openness`, `mouth_curve`). A mood that arrived as a
whole `FaceStyle` would overwrite the first group with stock values and
hand back a different character wearing the right expression, rendering
perfectly the whole time. So every field defaults to `null`, meaning
leave that one alone, and only the named fields are written. `null`
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

```ts
shade(hexColor: string, valueFactor = 0.80, saturationBoost = 1.08): string
```

The shadow tone for a base colour: darker and slightly more saturated.
Use it rather than hand-picking a second colour per part, which is what
keeps a palette consistent when someone changes the base. `hexToRgb01`
and `rgb01ToHex` sit alongside it in `colorutil.ts` for the odd conversion; the module also has `tint`,
`litTone` and `softShadowTone`, which the soft finish uses. The colour maths includes a hand-written `colorsys`,
so a derived tone is the same hex digit for digit as Python's.

## Links and the catalogue

`encodeParams(p)` writes a character as the value of a `?c=` link (sorted-key compact JSON, urlsafe base64, no
padding), `decodeParams` reads one back and raises `ValueError` on anything that is not one of this project's
links, and `characterUrl(p, baseUrl)` is the whole URL. These are byte-compatible with the Python's, because the
metadata block embeds such a link. `buildCatalogue()` and `toJson()` give what the web tool may show (its
colours, ranges, garments and starting points); `toJson()` is `ref-out/catalogue.json` byte for byte.

## CLI

`ts/bin/render.ts` is the SVG command line: `--out BASE`, `--preset NAME` (a preset or a neutral base),
`--finish`, `--highlight-strength`, `--background`, `--id-prefix`, `--metadata` and `--no-metadata`, `--list`.
Its SVG equals what the Python CLI wrote for the same arguments. `ts/bin/catalogue.ts [PATH]` writes the catalogue,
`ts/bin/cover.ts` the book cover and `ts/bin/sheet.ts` the cast sheets (`--members`, `--roster`). See the README for examples.

The Python's full command line (a flag for every colour, garment and face knob, `--expression`, `--flat` and the
PNG) is gone with it; its flags were generated from three tables in `generate.py` (`COLOR_ARGS`, `OUTFIT_ARGS`,
`FACE_ARGS`, in the tag `python-final`). The TypeScript has no such flags: build the variant with `replace` and
call `renderCharacter`. PNG is `harness/svg2png.py`, which rasterises an SVG file with cairosvg.
