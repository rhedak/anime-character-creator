# Tall chibi plan

Commit to the tall chibi as the one figure: retire the compressed shared
chibi (`body=None`) and the realistic build, and replace the build slider
with a **height** slider that stretches the tall chibi itself. Written
2026-09-26 at the owner's request, after the bust and bare body campaigns,
which polished the tall chibi and repeatedly had to leave the realistic build
unjudged.

The record is `tall-chibi-status.md`. The procedure is the one the last
campaigns used (`bust-strategy.md`, `bare-body-strategy.md`): predict before
measuring, one change per measurement, look in the right view, only the owner
signs off, one-line commits without a trailer.

## Why

- Every preset draws on a tall-chibi body profile (`tall_chibi` for
  Katherina, `tall_chibi_long_torso` for the rest); `../valley_of_mist` only
  ever renders the chibi.
- The realistic build has its own unfinished fix pass, and the last two
  campaigns deferred or skipped judging it at every step; 59 places in
  `character.py` branch on `sk.build`.
- The build slider does not stretch the tall chibi: a body profile applies
  only at exactly the chibi's 2.4 heads, and off it the figure falls back to
  the shared lerp between the compressed chibi and the realistic one.

## Owner's decisions (2026-09-26)

1. Retire the compressed chibi and the realistic build.
2. **Option 2**: the build slider becomes a height slider that stretches the
   tall chibi (longer legs and torso, the head and the chibi look kept), so
   children and adults can differ in height inside the one style.

## Invariant

**Every tall-chibi render stays byte-identical** through the retirement
(R1 to R3): `./refresh-ref-out.sh --check` on the chibi renders, the bases,
and `../valley_of_mist` by pixel check at the end. Only R4 (the height
slider) may move a figure, and at its default height it must not.

## The order

### R0. Inventory (read-only)

Every reader of the realistic build, the compressed chibi and the build
slider: `BUILDS`, `heads`, `sk.build` and what it gates, `body=None`,
`BODY_TYPES`, `_wears_cuts`, `REALISTIC_REFS`, `ref-out/real/`, the CLI's
`--build`/`--heads`, `cover.py`, `sheet.py`, the web tool, `urlstate`, the
tests, the skills (`gap-analysis`), the docs, and the consumers in
`../valley_of_mist` (`generate_assets.py`, the trailer's `figures.py`). Each
item classed: remove, collapse to the chibi's value, or keep.

**Acceptance:** the inventory in the status file, each item with its step.

### R1. Remove the choices

The web build slider and the "shared chibi" body option, the CLI's
`--build`/`--heads`, the catalogue entries. Old web links carrying `heads`
or `body=None` still load, onto the tall chibi. **Acceptance:** `ref-out/`
byte-identical; the catalogue changes are the only committed-output change;
an old link round-trips; checked in the browser.

### R2. Retire the realistic outputs

`ref-out/real/`, `REALISTIC_REFS`, the tests parametrized over builds, the
`gap-analysis` skill (retired with a note; `docs/gap-analysis.md` kept as a
record). **Acceptance:** chibi `ref-out/` byte-identical; the suite green.

### R3. Delete the dead code

The realistic-only branches in `character.py` and `skeleton.py`, in slices
(the face and eyes, the hair, the garments and cuts, the body and skeleton),
each slice its own commit. `sk.build` collapses to the value the profiles
pin it to where it only lerped toward the realistic build. The harness stays
as the record it is. **Acceptance per slice:** every chibi render
byte-identical, the suite green.

### R4. The height slider

**The owner's calls on the study (2026-09-26):** distribution C (two thirds
of the extra length to the legs, a third to the torso); range 0.8 to 1.3;
the knee planned properly first and shown on the bare render; sheets,
covers and the book's inserts at one head size deferred until the rest is
in place.

#### R4a. A real knee

The profile's `knee_y` is not a knee: it is where the reference's default
boot top lands (`_boot`'s shaft is measured off it), above the hip on
`tall_chibi_long_torso` and well above mid-leg on `tall_chibi`. Read as a
knee by the legs' outline (`_seat_notch_d`, shared by the bare legs and the
trousers: the thigh taper, the calf, the inseam's control points) and the
trousers' crotch; the bare crotch, the underpants and the tall boot shaft
already read `_real_knee_y` (mid-leg where the landmark is above it).

- **K0, study:** where the knee sits (candidates along hip to ankle), drawn on
  the adults' mannequin and the base layer with the knee marked, and
  clothed on figures in trousers and in skirts, before and after. The owner
  picks.
- **K1, the split:** the boot's reference keeps its value under its own name
  (`boot_top_y` or like), so a default boot cannot move; `Skeleton.knee_y`
  becomes the real knee, read by every leg; `_real_knee_y` and the clothed
  and bare crotch rules collapse into one.
- **K2:** the cast looked at, `ref-out/` refreshed (every figure's legs
  move, on purpose); the boots byte-identical within their SVGs.

#### R4b. The stretch

`CharacterParams.height` (1.0 the tall chibi as it is, 0.8 to 1.3), the
profile's landmarks below the shoulder moved by distribution C, the real
knee with them; the web slider; tests; every part looked at across the range
(garments, hems, coats, the bare body, the bust, feet, props, the hair).
**Acceptance:** at 1.0 byte-identical to after R4a; the range signed off.

#### R4c. Heights in compositions (deferred)

Sheets, covers and the book's inserts at one head size with the feet on one
line, so a height shows; until then each figure fills its tile as now.

### R5. Docs and the downstream

`CLAUDE.md` (its "Direction" and the realistic references), `README.md`,
`STATUS.md`, `docs/api.md`, the plans that mention the realistic fix pass;
`../valley_of_mist` checked by pixels and regenerated only if anything moved.

## What goes away

The deferred "realistic build's own fix pass" in the bust, bare body and
tunic bust plans; the `real/` renders; the traced cuts' build gate.
