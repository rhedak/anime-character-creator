# CLAUDE.md

Guidance for working in this repo.

## What this project is

A 2D anime character creator that **draws characters programmatically**
as parametric SVG shapes, rather than compositing pre-made art. Used
for the owner's novels/games, so output must not look "AI generated"
and must stay stylistically consistent, which this architecture gets
for free, since every character is built from the same shape code. No
animation. Backgrounds/text overlays may be added later as more SVG
layers.

Fourteen named characters (`presets.py`), each a first draft, all
rendering at the chibi (big head, short body) front-facing build by
default; `--build realistic` (or `--heads` for anything in between)
renders the same character taller. Multiple hairstyles and a full
garment system (`Outfit`) exist; poses do not. See `README.md`'s Status
section and `STATUS.md` for what is current.

**Direction, as of 2026-08-10:** the chibi build is locked in (see
`STATUS.md`) and the AI-generated design references in `ref/` have
done the job they were for, getting the style and the initial roster
established. They are not a target for new work going forward. Effort
now goes to three things: more GUI customization (hair/outfit/prop
options beyond what the fourteen presets already use), a bigger roster
(new characters, including ones from other games/stories, which have
no AI reference at all and are designed directly in `presets.py`), and
polish on what exists. The one place references still earn their keep
is closing known, already-measured gaps in the **realistic** build
(see "Direction" in `STATUS.md` and the `gap-analysis` skill); they are
not consulted for chibi work or for new characters.

Since 2026-08-10, `../valley_of_mist` (the novel this cast is written
for) consumes this repo's output directly: `render.sh`/`cover.sh`/`sheet.sh`
generate its character references, cover, and per-chapter inserts,
replacing an AI image pipeline it used before (see that repo's
`docs/character_designs.md`). This repo has no knowledge of that
consumer; `sheet.py --members` is the one generic hook it added to make
that possible, and it stays a plain preset-name list, not anything
valley_of_mist-specific.

## Hard constraints

- **No AI image generation, ever.** Every shape in `character.py` is
  explicit SVG (paths, circles, capsule-strokes) computed from the
  `Skeleton`. Don't introduce diffusion models, style transfer, ML of
  any kind, that's the opposite of what this project is for.
- **No scraping or importing external art assets.** This was the
  original plan and was explicitly abandoned in favor of drawing
  everything programmatically (see README status). Don't reintroduce
  an asset-pack/raster-compositing architecture without being asked.
- **Shapes are skeleton-relative.** Position/size everything off
  `Skeleton`'s anchor points (`head_r`, `shoulder_y`, `hem_y`, etc.),
  never hardcoded pixel coordinates, that's what lets proportions
  change globally later without rewriting every part.
- **Flat color, hard-edged, and no shading plane across a garment.**
  Matches the target cel-shaded anime look. Don't add gradients/blur,
  they'd break the flat-vector aesthetic that's the whole point. A
  second tone from `shade()` is for small elements, a pouch flap, a
  boot cuff, the turn under a hem, where it reads as thickness; a
  tunic, skirt, apron, sleeve or trouser leg stays one flat color and
  gets its form from the outline and from line work. This was
  originally "one shadow tone per surface", which drew shadow wedges
  covering a third of the torso and most of the apron, up to 15% of
  the figure's ink; the owner's call on 2026-08-06 was to drop them
  (task 56, see `docs/gap-analysis.md`).

## Structure

An installed package under `src/anime_character_creator/`, so the
modules below import each other relatively and the CLI is the
`anime-character-creator` console script. `pyproject.toml` holds the
metadata, the `uv` dependency groups and the `ruff` config; `docs/` holds
the architecture notes and the API reference; `harness/` holds the
one-off scripts that measured `ref/`, promoted there out of the ignored
`out/` so a cleanup cannot take them. Run one with
`./harness/run.sh harness/<pass>/<script>.py`, which handles the cairo
variable and makes the output directory. It is excluded from ruff on
purpose: several of those scripts are records of readings that were
wrong, and reformatting them would be editing the evidence.

- `src/anime_character_creator/skeleton.py`: proportion anchors (`Skeleton` dataclass +
  `build_skeleton()`). Change here to adjust overall proportions.
  Everything derives from `heads`; `BUILDS` names the chibi and
  realistic ends. A part that needs a measurement below the neck
  should read an anchor, not multiply `head_r` by a number that only
  happens to work on a chibi.
- `src/anime_character_creator/colorutil.py`: `shade()` derives shadow tones from a base
  color. Use this rather than hand-picking a second color per part.
- `src/anime_character_creator/presets.py`: named characters as `CharacterParams` values
  (`SATOKO`). Add a character here, not as a pile of CLI flags.
  Anything a character needs to differ on belongs in `CharacterParams`
  / `FaceStyle` with a neutral default, never hardcoded into a part
  function. The generator has to stay general, not become one
  character's renderer.
- `src/anime_character_creator/character.py`: one private `_part_name()` function per body
  part, each returning an SVG snippet string; `render_character()`
  stacks them in z-order. `CharacterParams` is the public color/style
  interface.
- `src/anime_character_creator/generate.py`: CLI entry point, writes `.svg` and (if
  `cairosvg`/system `cairo` available) `.png`.

## Working conventions

- When adding a new body part or hairstyle variant, follow the
  existing pattern: a `_part_name(sk, p) -> str` function using only
  `sk.*` anchors and `p.*` params, appended to the `layers` list in
  `render_character()` at the correct z-order.
- After changing shape geometry, actually render it
  (`./render.sh --out out/tmp --preset satoko`) and view the PNG before
  calling it done, coordinates that look right in the math are
  routinely wrong visually; this is an iterate-by-looking project.
- The `gap-analysis` skill (`.claude/skills/gap-analysis/`) compares a
  render against `ref/`. Its scope is the **realistic build only** now
  that the chibi is locked in and the roster is growing past the
  fourteen the references cover; do not reach for it, or for `ref/`, to
  judge a chibi render or a new character with no reference of its own,
  that is by eye against the design intent instead. When it does apply,
  its `probe.sh` builds the normalized side-by-side strips and takes the
  measurements rather than writing measuring code from scratch, and its
  `PITFALLS.md` records the ways naive pixel measurement gave wrong
  answers here. The standing result is `docs/gap-analysis.md`.
- Keep the tooling green in the same change: `uv run ruff check .`,
  `uv run ruff format .`, `uv run pytest`. The test suite is a smoke
  check, it renders every preset and compares `ref-out/`, so a failure
  there after a deliberate shape change means running
  `./refresh-ref-out.sh`, not editing the expectation.
- Test color parametrization by rendering at least one palette very
  different from the defaults, confirms `shade()` derivations still
  look right outside the default hue range, not just coincidentally
  right for blonde/green.
- do NOT commit unless asked
- even if you commit do not write a "co-authored" trailer
- no em dashes "—" (U+2014), double hyphens "--", or similar pause-substitutes in prose / comments;
  hyphens are fine for compound words, prefixes, and ranges, but in running text prefer a period, comma, 
  or restructured sentence instead
- If you disagree (you don't think they add value) with any instructions given, push back once and ask for confirmation
