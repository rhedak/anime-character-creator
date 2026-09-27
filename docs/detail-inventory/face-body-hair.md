# D0 inventory: face, hands, limbs, widths-at-height, hair

All line refs against `src/anime_character_creator/character.py` (10028
lines) and `skeleton.py` (408 lines) unless noted. File: `character.py`
unless stated otherwise.

## 1. Face

- `_head_shape` (8472-8501): the jaw/face outline. Its own path, not the
  head circle: `_head_pt` (8321-8340) walks a unit circle profile and, below
  `_JAW_START_Y`, narrows x by `jaw_pull=0.20*build` and drops y by
  `chin_drop=0.05*build`, both eased by `_JAW_EASE`. At `build=0` (pure
  chibi) this is exactly a circle; taper only appears as `sk.build` rises.
  Reads: `sk.build` only (no anchors beyond `head_cx/cy/r`, no `FaceStyle`
  fields).
- `_head` (8705-8740): fills/strokes `_head_shape`, splits stroke weight at
  the chin (full weight silhouette, 0.6x under the chin). Reads
  `p.skin_tone`, `sk.head_r/cx/cy`.
- Eyes: `_eye_shape` (8779-8815) builds the aperture (shared by both
  styles) from `f.eye_width`, `f.eye_openness`, `f.eye_lower_lid`,
  `f.eye_tilt`, `f.eye_corner`, and the shared constant `_EYE_ASPECT=1.28`
  (8759). `_eye_realistic` (8818-8879, every preset's default): white
  aperture, 3-tone iris (rim/base/pupil via `shade()`), 2 highlight
  circles; reads `f.iris_size`, `p.eye_color`, `pupil_ratio` (computed in
  `_face` from `_PUPIL_REALISTIC_GROW*sk.build`, 8776/9193). `_eye_anime`
  (8898-8977, no preset uses it): same aperture, different interior - one
  dark iris body + 2 offset glow highlights (`f.eye_glow` gates them, one
  fixed highlight never gated), no separate pupil ring; `pupil_ratio` param
  accepted and ignored (8916). `_eye_closed` (8991-9008) draws one lash
  line instead, used when `f.eyes_closed`.
- Eye size/placement (the D3-relevant numbers): all computed in
  `_eye_placement` (9040-9155), the single source `_face` and `_glasses`
  both call. `eye_y = cy + r*0.16` (9145, fixed, does not move with
  build - a D3 lever). `eye_dx = r*0.46*(1-0.27*sk.build)` (9146,
  moves inward with build already). `eye_r = r*0.26*(1-0.12*sk.build)*f.eye_size`
  (9154). `f.eye_openness`, `f.eye_lower_lid`, `f.eye_width`, `f.eye_corner`
  are each rescaled by `sk.build` inside this function (9073-9127) before
  being handed to the eye-drawing functions - so a maturity slider wanting
  "smaller, lower eyes" most naturally adds its own terms alongside these
  `sk.build` ones, in the same function.
- Brows: drawn inline in `_face` (9196-9207), a `<line>` per side. Reads
  `f.brow_tilt`, `f.brow_weight`, `brow_color = shade(p.hair_color, 0.45)`,
  position pinned to `eye_y - eye_r*1.30`.
- Mouth: drawn inline in `_face` (9215-9221), one quadratic. `mouth_y = cy
  + r*(_MOUTH_Y + _MOUTH_REALISTIC_DROP*sk.build)` (9215; constants at
  4997, 5024). `mouth_half` reads `f.mouth_width`,
  `_MOUTH_REALISTIC_WIDEN` (5007). Curve reads `f.mouth_curve`.
- Nose: **none**. No `_nose` function, no nose reference anywhere in
  `_face` or `_head`; confirmed by grep. D3's "nose tick" is wholly new.
- Blush: inline in `_face` (9223-9233), gated by `f.blush`, color/opacity
  from `_blush(p.skin_tone)` (9171-9180, skin-tone-aware, blends toward a
  darker rose on dark skin).
- Glasses: `_glasses` (5286-5335), gated by `f.face.glasses` (i.e.
  `FaceStyle.glasses`). Fully derives its rim geometry from
  `_eye_placement`'s return values (`eye_dx/eye_y/eye_r` + the same
  `f.eye_width`/`_EYE_ASPECT`/`eye_openness`/`eye_lower_lid` the eye itself
  uses) - so any D2/D3 change to `_eye_shape`'s geometry is inherited by
  glasses for free with no separate edit needed, per the function's own
  docstring history of the opposite going wrong.
- Scar: `_scar` (9023-9037), two short lines on one cheek, gated by
  `f.scar_side` (nonzero -> discontinuous appearance, by design - it is a
  scar, not a slider).

## 2. FaceStyle and Expression

`FaceStyle` (47-114), all fields/defaults: `eye_size=1.0`, `eye_width=0.88`,
`eye_openness=1.0`, `eye_lower_lid=1.0`, `eye_tilt=0.10`, `eye_corner=0.35`,
`iris_size=0.72`, `eye_style="realistic"`, `eye_glow=1.0`, `brow_tilt=0.0`,
`brow_weight=1.0`, `mouth_curve=1.0`, `mouth_width=1.0`, `blush=1.0`,
`glasses=False`, `eyes_closed=False`, `scar_side=0`.

Discontinuous switches: `eyes_closed` (bool, 106) swaps the entire eye draw
call from `EYESTYLES[...]` to `_eye_closed`, a shape discontinuity by
design (a blink, not a mood). `scar_side` (0/-1/1, 114) is presence/absence,
also deliberate. `eye_style` (string key into `EYESTYLES`, 82) swaps the
whole iris construction, a discontinuity if ever driven by a continuous
slider (it currently isn't - it's a discrete preset/catalogue choice).
No other field has an `if x > 0.01`-style threshold; everything else
(`eye_glow`, `blush`, `iris_size`, etc.) scales continuously to 0.

`Expression` (117-159): delta-only dataclass, every field `None` by default
= "leave alone". Fields: `brow_tilt`, `brow_weight`, `eye_openness`,
`eye_lower_lid`, `mouth_curve`, `mouth_width` (141-150). `EXPRESSIONS` dict
in `presets.py` (1261-1287): `stern` (brow_tilt=0.55, mouth_curve=-0.25),
`grim` (brow_tilt=0.75, mouth_curve=-0.45, mouth_width=0.62), `hollow`
(eye_openness=0.66, brow_tilt=0.30, mouth_curve=-0.20), `wry`
(eye_openness=0.66, brow_tilt=0.30, mouth_curve=0.45), `sorrow`
(brow_tilt=-0.40, mouth_curve=-0.30, eye_openness=0.82), `resolute`
(brow_tilt=0.50, mouth_curve=0.0, eye_openness=1.0, mouth_width=0.80). No
expression touches `eye_width`/`eye_corner`/`iris_size` by design (those
are identity, not mood) - a D3 face-maturity slider is squarely in that
"identity" bucket too and should stay off `Expression`.

## 3. `_eye_anime` reachability

Differs from `_eye_realistic`: no separate pupil ring; iris is one dark
flat body (`shade(eye_color, 0.42)`) plus two off-centre flat highlight
circles gated by `f.eye_glow`, plus one ungated highlight (8898-8977).
Ignores its `pupil_ratio` argument entirely (accepted only because
`EYESTYLES` callers pass it positionally to every style, 8916-8919).

Reachable from:
- No preset (`presets.py` grep: no `eye_style=` anywhere).
- `catalogue.py` (39, 570-578): `FACE_EYE_STYLE` is a `SelectField` built
  directly from `EYESTYLES.keys()`, so it is exposed as a real dropdown
  option in the web tool/catalogue whenever a new `EYESTYLES` entry is
  added - no separate list to update.
- `web/app.js`: does not reference `eye_style` directly but imports
  `render_character`/`CharacterParams` generically, so any catalogue field
  reaches it through the generic form-binding path (not confirmed by name
  grep, but the catalogue is the web tool's field source).
- Tests: `tests/test_catalogue.py:72-81` asserts `FACE_SELECTS` eye_style
  options == `set(EYESTYLES)` exactly; `tests/test_smoke.py:60-62`
  parametrizes a render-smoke test over every `EYESTYLES` name x every
  build.
- `src/anime_character_creator/__init__.py` (23, 43): re-exports
  `EYESTYLES` as public API.

Retiring it would NOT be cheap in the "just delete the function" sense:
it is wired into the catalogue (would need the select field removed or
special-cased to one option), the public `__init__.py` export, and two
tests that iterate `EYESTYLES` generically. It would be mechanically
straightforward (all three touch points key off the same dict), but it is
not a dead/unreferenced function - it is a live, tested, catalogue-exposed
knob with zero preset adoption, not orphaned code.

## 4. Hands

Only one hand shape exists: `_hand` (7339-7371), a single filled mitten
path with the thumb as one bump on the inner edge (`x(-hw*1.12)` etc,
7363), no separate fingers, no crease. Docstring (7346-7349) states this
explicitly: "Still no fingers... at this size separate digits read as
noise." No fist/gripping/open variants in `character.py`; a held prop
(staff `_staff`, 6572; katana `_katana`, 7010) is drawn as its own object
placed at `_hand_centre` (6142-6155) and laid over/behind the same one
hand shape, not a different hand shape. `tip = hw*(1.0-0.32*sk.build)`
(7352) is the only build-dependent taper inside the hand itself; no
`height`-dependent term (only `sk.build`, which `stretched()` never
touches, see Q6). No finger-hint lines anywhere (grep for "finger" in
character.py: only in comments/docstrings, e.g. 7347, no drawn geometry).

`_hand_length` (6117-6121): `sk.arm_half_w*(1.35+1.10*sk.build)`.
`_hand_centre` (6142-6155): computes the swung hand's centre in head
radii, reading `_arm_line`, `_arm_pivot`, `p.right_arm_out`/`left_arm_out`.

## 5. Limbs

Arms: `_arms` (7061-7260) draws sleeve-hem-to-hand. Already tapers by
build only: `w_top = sk.arm_half_w`, `w_elbow = sk.arm_half_w*(1-0.15*
sk.build)`, `w_wrist = sk.arm_half_w*(1-0.34*sk.build)` (7118-7120,
comment at 7116 says "Tapers on the build, the way the leg does"). Outline
built as one closed quad-curve path (7157-7169) reading `centre_top`,
`centre_elbow`, `centre_wrist` from `_arm_line` (6097-6114) and the above
widths; bare skin or sleeve-colored per `Outfit` fields
(`sleeve_long`, `undersleeve_color`, `coat_sleeves`, `coat_color`,
sleeve cut via `_worn_sleeve`/`SLEEVE_CUTS`). No `height`/stretch term at
all - only `sk.build`.

Legs: `_legs_and_boots` (7403-7440), taper comment at 7404-7415 explicit
about matching a reference ratio (thigh 1.26x, knee 1.03x, calf 1.01x,
ankle 0.85x leg_half_w, adjusted by `taper = sk.build`, 7416,
7423-7427). Trousers (`_trousers`, 7560) or bare seat (`_bare_seat`, 7634)
consume the same `w_top/w_knee/w_calf/w_ankle`. Boots (`_boot`, 7759) and
bare feet (`_bare_foot`, 7708) are drawn at the ankle width, so foot size
already rides whatever the ankle width is - reaches Q6/Q7 (widths).
Skirts (`_skirt`, 5959, `_skirt_half_w`, 5667) are independent of leg
width (they hang off `hip_half_w`/`hem_half_w`, not leg taper), so a skirt
covers whatever the legs do underneath.

So: both arms and legs already taper along their own length (build-only,
not height), contradicting the plan text's "straight tubes" a little -
the missing piece per the plan (D4b) is knee/ankle/wrist narrowing that
also responds to **height**, since today only `sk.build` (face/limb
"build", pinned per-figure regardless of `height`) drives it, and
`stretched()` explicitly holds every width fixed (Q6).

## 6. Widths at height (`skeleton.py`)

`_KEEP_WS` (208-217): `neck_half_w`, `shoulder_half_w`, `waist_half_w`,
`hip_half_w`, `hem_half_w`, `arm_half_w`, `arm_x`, `leg_half_w` - every
width field on `Skeleton` except none are omitted (this is the full width
set; there is no width field left out of `_KEEP_WS`).

`stretched()` (220-260): for each name in `_KEEP_WS`, `changes[name] =
getattr(sk, name) / sk.head_r * fit.head_r` (258-259) - i.e. holds the
width **proportional to head_r**, not literally fixed in pixels, but
completely insensitive to `h` (the height multiplier) itself: at any `h`,
every width is exactly what it was at `h=1` scaled only by the new
head_r. `_STRETCH_YS` (206) and `_KEEP_YS` (207) are the only fields that
respond to `h`.

Skeleton width fields (35-79): `neck_half_w`, `shoulder_half_w`,
`waist_half_w`, `hip_half_w`, `hem_half_w`, `arm_half_w`, `arm_x`,
`leg_half_w` - exactly `_KEEP_WS`'s list, confirming it is exhaustive.

Other things that read these widths (so a D4a width-follow-through reaches
them transitively via `sk.*_half_w`/`arm_half_w`/`leg_half_w`, without
further edits): `_hand_length`/`_hand` (read `sk.arm_half_w`, 6117/7350),
`_bare_foot`/`_boot` (read the ankle width passed in from
`_legs_and_boots`, itself off `sk.leg_half_w`), `_belt_line_half_w`/`_belt`
(7885, off `waist_half_w`/`hip_half_w`), `_skirt_half_w` (5667, off
`hip_half_w`/`hem_half_w`), `_torso`/`_tunic`/`_bust_shape` (off
`shoulder_half_w`/`waist_half_w`/`hip_half_w`). Head width (`head_r`)
itself is never in `_KEEP_WS` and is not touched by `stretched()` at all -
`stretched()`'s `fit = refit(...)` (252) rebuilds a fresh skeleton at a
new `heads` count purely for canvas geometry, and every landmark/width is
then overwritten from `sk`, so head size only changes via `heads`/`build`,
never via the height slider - i.e. "the same head on a longer body" (the
plan's own diagnosis) is exactly what the code does today, confirmed at
the source.

## 7. Hair: strand lines per hairstyle

All six styles already have a `strands` callable (`Hairstyle.strands`,
2189); none is `None`. Drawn last, over fill and hairline
(`_hair_front`, comment at 9273, loop 9276-9277+).

| hairstyle | strands fn | line | count | parameterisation |
|---|---|---|---|---|
| long_blunt | `_long_strands` (847-893) | 2229-2232 | 10 chains (4 crown sweeps, 1 outer-fall pair (mirrored), 1 inner-fall pair, 2 fringe flicks) | hardcoded head-radii coords; fall-line y's use `_fall(f, length)` so they scale with `hair_length`, crown/fringe coords are fixed |
| short_layered | `_short_strands` (1135-1166) | 2233-2243 | 8 chains (6 crown, 2 sideburn) | mostly hardcoded; the 2 sideburn lines end at `tip-0.28` (parameterised by `tip`) |
| long_center_part | `_center_part_strands` (939-975) | 2244-2252 | 10 chains (2 mirrored sweep pairs = 4, outer-fall pair =2, inner-fall pair=2, flick pair=2) | same `_fall(f,length)` pattern as long_blunt; reuses long_blunt's own `outer_lock` unchanged (943) |
| long_traced (Katherina's) | `_long_traced_strands` (1387-1405) | 2253-2263 | 4 chains (2 fixed crown sweeps + 1 mirrored fall-line pair) | fall-line pair scales by `v = fall/_LONG_BASE_TIP`; sweeps fixed. Fewest strands of the six - the plan's pick to "set the pattern" is also numerically the sparsest today |
| short_crop | `_crop_strands` (1865-1889) | 2264-2274 | `len(_CROP_NOTCHES)` (8) notch-aimed lines + 2 long crown lines = 10 | notch lines from `_CROP_NOTCHES` (fixed list); the 2 crown lines scale by `v = fall/_CROP_BASE_TIP` |
| short_tousled | `_tousle_strands` (2134-2152) | 2275-2282 | 7 chains (5 crown, 2 side-lock, mirrored pair) | crown fixed; side-lock pair ends at `tip-0.24` |

All are open quadratic chains in head-radii space, drawn as thin strokes
(fraction of `_stroke_w`) inside the mass fill - no separate "bangs
parted into locks" structure beyond what these lines already imply; the
plan's D5 ask (bangs parted into locks, more strand lines) is additive on
top of an existing, working strand mechanism per style, not a new
mechanism.

## Not found in this repo (out of scope / external)

Q0's "smallest render sizes `../valley_of_mist` uses" lives in the sibling
`../valley_of_mist` repo (`render.sh`/`sheet.sh` consumers), not in this
one; not inventoried here since this task was scoped to
`anime-character-creator`.
