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

A study first: what stretches (the legs, the torso, both, in what share),
over what range, and how the canvas and head size answer so a taller figure
still fits. The owner picks from a sweep; then `CharacterParams.height`
(1.0 the tall chibi as it is), the web slider, the tests, and every part
looked at across the range (garments, hems, coats, the bare body, bust,
feet). **Acceptance:** default height byte-identical; the range signed off.

### R5. Docs and the downstream

`CLAUDE.md` (its "Direction" and the realistic references), `README.md`,
`STATUS.md`, `docs/api.md`, the plans that mention the realistic fix pass;
`../valley_of_mist` checked by pixels and regenerated only if anything moved.

## What goes away

The deferred "realistic build's own fix pass" in the bust, bare body and
tunic bust plans; the `real/` renders; the traced cuts' build gate.
