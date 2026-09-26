# Tall chibi status

The record for `tall-chibi-plan.md`, newest first.

## RESUME (for a fresh context)

- **Now:** the plan is done but R4c (heights in compositions), deferred at
  the owner's call. The owner signed off the knee and the slider ("all
  values look good") and `../valley_of_mist` is regenerated. The owner picked distribution C and the range
  0.8 to 1.3, asked for the knee planned properly and shown on the bare
  render, and deferred heights in compositions (R4c). Autonomous, per the
  owner; R4's study is the next stop for input.
- **Byte guard for R3:** `./harness/run.sh harness/tall_chibi/snapshot.py
  out/tall_chibi/after`, then `cmp` against `out/tall_chibi/before` (108
  renders, taken at `9e3942a`).
- **Tree:** clean at `2e549d2` when the plan was written.
- **Invariant:** every tall-chibi render byte-identical through R1 to R3
  (`./refresh-ref-out.sh --check`); only R4 may move a figure.
- **Owner sign-off** after each step; commits one line, no trailer.

## Scoreboard

| step | state | acceptance met |
| --- | --- | --- |
| R0 inventory | done, signed off | inventory below, each item classed and stepped |
| R1 remove the choices | done, signed off | `ref-out/` and bases byte-identical; old link test; browser checked |
| R2 retire the realistic outputs | done, not yet reviewed | `ref-out/` chibi, bases, catalogue unchanged; 606 passed |
| R3 delete the dead code | done | snapshot 108/108 byte-identical; 484 passed |
| R4 the height slider | R4a, R4b done, signed off; R4c dropped (the owner: heights do not matter for the story) | 1.0 byte-identical; 483 passed; browser checked |
| R5 docs and the downstream | done | valley_of_mist regenerated |

## Findings, newest first

### Next: the two other covers (2026-09-26, not started)

The owner asked for `../time_slider_katherina`'s and
`../short_stories/stories/everglow_crystals`'s covers updated. Found:
`time_slider_katherina/tools/generate_cover.py` uses only `render_cover` and
needs a rerun, plus a re-render of `style-anchors/katherina.svg/png` (no
metadata in the current one). `short_stories/scripts/build_cover_dual.py`
builds each figure's skeleton with `build_skeleton(heads=BUILDS[build])`,
the retired compressed chibi without a body profile: it should use
`skeleton_for(character)` and drop its `build` field, which changes Gero's
and Linnea's proportions on that cover to the tall chibi's, and its
`right_scale` (Linnea drawn 0.88 of Gero) may want revisiting now that
`height` exists. Both trees were clean; both repos say commit only when
asked, no trailer. Also fixed on the way: `skeleton_for` was not exported
from the package although its docstring imported it.

### R5: `../valley_of_mist` regenerated (2026-09-26)

At the owner's say-so: 52 images, 51 with pixels moved (Satoko 10, Reika
64, the trousered figures and the inserts they stand in up to 29,328), and
Chiyo's reference metadata only (its embedded link now has `height` and no
`heads`; her skirt hides the legs). Only the PNGs committed there: two prose
edits already in that tree (`ch01_kiriguchi.md`, `.thesaurus-ignore`) were
someone else's and were left as found.

### R5: the docs (2026-09-26)

`CLAUDE.md` (the overview, the direction's paragraph on references, the
`skeleton.py` bullet, the gap-analysis bullet), `README.md` (the status, the
note on `ref-out/real/`, the refresh description, the realistic example, the
architecture's skeleton paragraph), `docs/api.md` (`build_skeleton`, a `body`
row in place of `heads`, the `REALISTIC_REFS` section removed), a dated
section in `STATUS.md`, and the three earlier plans' deferred "realistic fix
pass" struck through with a note. History in `STATUS.md` left as it was.

### R4b: the height slider (2026-09-26)

`CharacterParams.height` (1.0), `skeleton.stretched(sk, h, refit)`:
distribution C in head radii (a third of the extra length to the torso,
shoulder to hip; two thirds to the legs, hip to sole), then refitted to the
canvas by a skeleton built at the new height for its canvas geometry alone.
Not applied at exactly 1.0. Catalogue `height` 0.8 to 1.3, a web row, an
`api.md` row.

**First version, wrong:** stretching the profile and rebuilding. The widths a
profile does not measure (the shoulders, the arms) come from the lerp over
`heads`, so a taller figure's shoulders narrowed (0.94 to 0.85 head radii at
1.3); the new test caught it. Stretching the built skeleton keeps every
width.

**Predicted and measured:** at 1.0 the 107 snapshot renders byte-identical
to the commit before (taken properly by stashing: a first comparison was
against a snapshot taken after the edit, and proved nothing); 483 passed;
across 0.8 to 1.3 (`harness/tall_chibi/height_range.py`,
`out/tall_chibi/height_range.png`: Satoko, Satoshi, Krista, Keiko, Kyoko,
Reika, Katherina, Krista in the base layer) hems, aprons, the hakama, both
coats, the traced lab coat and jacket, the katana, boots, bust and bare body
all follow, and no figure is clipped by its canvas at either end. Satoshi's
ink touches his canvas edge at every height, 1.0 included: already so, not
the stretch. Browser: the slider is in the Build section, and at 1.3 Krista
renders taller and the link carries `height`.

### R4a K1: the real knee (2026-09-26)

The owner picked 0.5. The profile's landmark is renamed for what it is,
`boot_y` (`Skeleton`, `BodyProfile`, the `tall_chibi` profile's 3.39), and
the boot's default shaft still measures off it. `Skeleton.knee_y` is the real
knee, half way from the hip to the ankle, set in `BodyProfile.applied` and
left alone by the belt line (the waist-shift test holds the knees and soles
still). `_real_knee_y` removed, its readers on `sk.knee_y`, which is the same
value; `_crotch_y` one rule, dressed or bare; the trousers' crotch reads the
real knee too.

**Predicted:** every boot byte-identical; the legs move where they show,
most on trousers, little under skirts. **Measured:** all 68 boots (17
characters, dressed and tunic-off, both feet) found character for character
in the renders from before; `--pixels`: trousers 6,200 to 7,500 pixels at 2x
(the thigh taper and the inseam), skirts 10 (Satoko), 64 (Reika), 676
(Keiko), the cover, the sheets and both bases. Before and after:
`out/tall_chibi/k1_cast.png` (on trousers the inseam now runs to a narrow
pointed arch and the thighs converge a little; skirts and coats unchanged to
the eye). 480 passed; `ref-out/` refreshed. `../valley_of_mist` now stale,
regenerated at R5 on the owner's say-so.

### R4a K0: the knee study (2026-09-26)

`harness/tall_chibi/knee_study.py`: the legs' knee moved to a fraction of
hip to ankle for the legs only, the boots kept on the old landmark (they do
not move in any row). Krista and Gero bare (underwear stubbed, the knee
marked), Satoshi and Tenno in trousers, Satoko in a skirt.

**Now:** the knee line sits at the hip; the legs are straight columns, and
the bare crotch shows a small double bump, the inseam rising and dipping on
its way up (the inseam's control points at the landmark). **At 0.45, 0.5,
0.55:** the crotch is a clean arch and the legs taper gently from thigh to
knee; the trousers' inseam changes a little; under a skirt nothing visible
moves. The three candidates differ subtly. **Recommendation: 0.5**, the rule
`_real_knee_y` already gives the underpants, the bare crotch and the tall
boot shaft, so every part would read one knee.

### R4: the height study (2026-09-26)

`harness/tall_chibi/height_study.py`: a height `h` keeps the head, the
shoulders and every width, and moves the profile's landmarks below the
shoulder so the shoulder-to-foot run is `h` times as long; `heads` follows
from the new foot (`2 * heads - 1`), and `build_skeleton` fits it to the
canvas, so on its own canvas a taller figure has a smaller head. Three
distributions of the extra length: **A** evenly, **B** legs only, **C** two
thirds to the legs; at 0.8, 0.9, 1.0, 1.15, 1.3 on Satoko and Satoshi, drawn
at one head size with the feet aligned.

The mechanics hold: hems, the apron, trousers, boots, the katana and the
hair's body-relative length all follow. A at 0.8 is squat (the torso
compresses too) and at 1.3 long-waisted; B reads young at 0.8 and lanky at
1.3, all legs; C reads young at 0.8 and adult at 1.3 without either extreme.

**Open for the owner:** the distribution (recommended C), the range
(recommended 0.8 to 1.3), the knee (the stretch scales the long-torso
profile's knee landmark, which sits above the hip; recommended a real knee
as part of R4, a small visible change to every leg's curve, mostly under the
tunic), and whether sheets, covers and the book's inserts draw figures at one
head size so heights show (they now fit each figure to its tile, which would
hide a height difference).

### R3c: `long_traced_real` (2026-09-26)

The owner's call: removed, the realistic build's own cut. Its trace
(`_LONG_REAL_*`, the `_long_real_*` functions, 170 lines), its `HAIRSTYLES`
entry and its catalogue label. `urlstate` maps an old link's
`long_traced_real` to `long_traced`, the chibi cut it was split from, so the
link still renders. **Measured:** 107 of the snapshot's 108 renders
byte-identical, the one gone being that hairstyle's; 480 passed (the
hairstyle parametrizations one fewer); `ref-out/` matches; the catalogue
refreshed.

### R3b: the build-gated branches (2026-09-26)

Deleted, never true at the pinned build: the hand's crease and finger
strokes, the boot eyelets, `_belt_line_half_w`'s realistic waist, the nose,
and `_NOSE_REALISTIC_DROP` with them. Unwrapped, always true: the apron's
length cap, the crystals' spacing, the sash cap and the belt over trousers
(their `sk.build < 0.5` halves dropped), the buckle rule (`or sk.build >
0.5` dropped), `_bust_over_arms`' gate (`or sk.build >= 0.5`), and **the
eye block, frozen as it renders** (the owner's call), its wrong comment
("`sk.build` gates it to 0 there") corrected: it trims every figure's eye
openness by 4% and the lower lid by 2%. `_wears_cuts` removed and its six
callers' `and _wears_cuts(sk)` dropped. One more always-true gate than the
inventory had (the crystals', found reading the sites). The lerps that read
`sk.build` stay: at the pinned value they give exactly today's numbers, and
rewriting them as literals would risk float differences for nothing.

**Predicted and measured:** the 108 snapshot renders byte-identical, 484
passed, `ref-out/` matches.

### R3a: the skeleton path (2026-09-26)

`_skeleton_at(p)` always lays `p.body`'s profile over the chibi build; its
pinned `sk.build` is still computed by `build_skeleton(heads=2.4).build`
(0.09999999999999998 in floating point, not a literal 0.1, so every lerp
evaluates exactly as before). `skeleton_for(p)` lost its `heads` argument;
`CharacterParams.heads` removed; `body` is a plain `str`; `BUILDS` keeps the
chibi only. `urlstate` still maps an old link's `heads` and `body: null`.

**The byte guard:** `harness/tall_chibi/snapshot.py`, 108 renders (every
preset dressed, tunic off, all off, barefoot; the neutral bases; every
hairstyle, eye style, expression, body type and traced cut; a bust sweep,
the belt line both ways, an arm out, a parametric coat and a robe over a
bust), byte-identical before and after.

**Tests:** a sonnet delegate (184k tokens, over the 100k signal; the next
such brief to be split) moved the failing tests to the new API, deleting no
test and removing only assertions about the realistic build or the
compressed chibi's own numbers (reviewed in its diff). It moved only the six
tests that failed, not every character drawn on the compressed skeleton as
briefed; the orchestrator moved 18 more by pattern. One then failed, and
stays on the shared skeleton with a note: **the legs' path (`_seat_notch_d`)
carries the long-torso profile's knee landmark, which is above the hip, as a
control point**, so tucked the crotch curve rises a little before it dips and
untucked the path's sides reach above its own top. Hidden under the tunic in
every preset; changing it would move every leg's curve, so it goes to R4,
whose height slider needs a real knee anyway. 14 `build_skeleton(heads=...)`
calls stay in the tests: the skeleton-machinery tests and a few on the
default character. 484 passed (606 before, the realistic cases gone).

### R2: the realistic outputs retired (2026-09-26)

`ref-out/real/` removed (34 files); `presets.REALISTIC_REFS` and its export
removed; `refresh-ref-out.sh` renders the one build (`builds=chibi`), drops
the realistic list and its checks, no longer passes `--build`, and reports
anything left under `ref-out/real/` as an orphan. The CLI's `--build` and
`--heads` removed from `generate.py`, and `--build` and the `build` field
from `sheet.py` and `cover.py`, which now call `skeleton_for(character)`: the
character's own `heads` is the same 2.4. The `gap-analysis` skill moved to
`harness/gap_analysis_skill/` as a record (`docs/gap-analysis.md` kept).
Tests: the snapshot set is the chibi only; the leftover check covers
`real/`; the cover test is no longer parametrized; the CLI test asserts the
retired options fail. The tests parametrized over `BUILDS` still run both
builds, since the realistic code exists until R3.

**Predicted:** every chibi render, the cover, the sheets, the bases and the
catalogue unchanged. **Measured:** so (`--check` matches, bases and catalogue
unchanged); 606 passed.

### R1: the choices removed (2026-09-26)

The owner's calls on R0: old links load as the default tall chibi;
`long_traced_real` goes (R3); the eye block is frozen as it renders today
(R3).

Removed: `catalogue.BUILD`, `BuildField`, `_build_json` and the catalogue's
`build` key; the `None` ("Chibi") entry in `bodies`; the web tool's build
slider and snaps, the body select's `""`-to-`null` handling. Old links:
`urlstate.params_from_dict` drops `heads` and a `body` of `None`, so they
load as the default tall chibi. **Moved to R2:** the CLI's `--build` and
`--heads`, since `refresh-ref-out.sh` renders `ref-out/real/` through
`render.sh --build`; they retire with those renders.

**Predicted:** `ref-out/` and the bases byte-identical, the catalogue JSON
the only committed output to change. **Measured:** so; 624 passed. One test
read `heads` back through `decode_params`, which now maps it away; it reads
the link's raw JSON instead, what `main()` resolved. Browser: an old link
(Krista at `heads=6`, `body=null`) loads as the tall chibi, the Build
section shows the body select and the belt, bust and chest sliders, no build
slider.

### R0: the inventory (2026-09-26, at `6c1b275`)

A read-only delegate (sonnet, 79k tokens) over both repositories; the
riskiest claims checked by hand.

**The pin.** On the tall-chibi path `sk.build` is 0.1: `_skeleton_at`
applies a body profile only at `heads == BUILDS["chibi"]` (2.4), and
`BodyProfile.applied` sets `build` to a throwaway unprofiled skeleton's value
at 2.4 heads, `(2.4 - 2.0) / 4.0`. `_KOU_CHIBI_BUILD = 0.1` already relies on
it.

**Classes, with the step that takes each:**

| item | where | class | step |
| --- | --- | --- | --- |
| build slider (`BUILD`, a 2 to 7 heads range with two snaps) | `catalogue.py:460`, `web/app.js` | replaced by height | R1, R4 |
| body select's empty option (the compressed chibi) | `web/app.js:277`, `BODY_LABELS` | remove | R1 |
| `--build` / `--heads` | `generate.py:85,90,134`, `sheet.py:213,267`, `cover.py:215,351`, `render.sh`, `cover.sh` | remove (`--heads` may carry height later) | R1 |
| `urlstate` | generic `asdict` round trip, no clamp | old `heads`/`body=None` mapped onto the tall chibi | R1 |
| `REALISTIC_REFS`, `ref-out/real/` | `presets.py:1229`, `refresh-ref-out.sh:41,118,323` | remove | R2 |
| tests over builds | 21 parametrizations in `test_smoke.py`, 6 in `test_catalogue.py`, realistic asserts at `test_smoke.py:226,228,2037,2170`, `test_catalogue.py:99` (snaps equal `BUILDS`), `test_generate_cli.py:46` | rewrite with the removal they test | R1, R2 |
| `gap-analysis` skill | `.claude/skills/gap-analysis/` | retire; `docs/gap-analysis.md` kept as record | R2 |
| `body=None` branch | `character.py:4110` (`return build_skeleton(...)` unprofiled) | remove | R3 |
| `BUILDS["realistic"]` | `skeleton.py:21`, `character.py:10102`, readers above | remove; `BUILDS` keeps the chibi or becomes a constant | R3 |
| realistic-only branches (never true at 0.1) | `character.py:2908, 7562, 8108, 8130, 8256, 9457, 10013` | delete | R3 |
| always-true halves (`sk.build < 0.5`) | `_wears_cuts` (`4318`, six callers), `6076, 8151, 8185` | drop the half, keep the other operand | R3 |
| lerps evaluated at 0.1 (arm, leg, hat, hair, head shape, mouth, nose, eyes, stroke width at `43`, the moustache at `5335`, and about 25 more) | many | **freeze at their 0.1 value, never delete** | R3 |
| `long_traced_real` | `character.py:2431`, `catalogue.py:534` | no preset uses it; tuned for the realistic build | owner's call, R3 |
| docs | `CLAUDE.md:18,32,95,123`, `docs/api.md:152,218`, `README.md`, `STATUS.md` (a new dated section, history left) | reword | R5 |
| `../valley_of_mist` | `generate_assets.py`, `trailer/figures.py` | no `heads`, `build` or `body` anywhere: nothing to change | R5 (pixel check only) |

**Checked by hand, against the delegate:**

1. **The eye block at `character.py:9301` is live at the chibi.** It is
   gated `if sk.build > 0`, true at 0.1, so every tall chibi's eyes are
   already trimmed by the realistic tuning (openness by 4%, the lower lid by
   2%); its comment ("`sk.build` gates it to 0 there") is wrong. R3 must
   freeze it, not delete it, and correct the comment.
2. **`CLAUDE.md` does need rewording** (the delegate said not): it still
   describes `--build realistic` and the realistic-only `gap-analysis`
   direction.
3. No preset sets `heads` or `long_traced_real`.

**Riskiest for byte-identity:** the lerps (freeze, never delete); the eye
block; `_wears_cuts`' callers (an inlined `and` can change precedence); the
throwaway skeleton in `_skeleton_at` (inline 0.1 only with the invariant
written down).
