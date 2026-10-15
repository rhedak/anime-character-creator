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

Fourteen named characters plus a few guests from
other projects (`presets.py`), each a first draft, all
drawn as the tall chibi (big head, short body), front-facing: the one
figure since 2026-09-26, when the realistic build and the old compressed
chibi were retired (`docs/tall-chibi-plan.md`); `height` stretches it for a
younger or a taller character. Multiple hairstyles and a full
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
polish on what exists. The one place they still earned their keep,
closing measured gaps in the realistic build, went with that build on
2026-09-26; they are not consulted any more (`docs/gap-analysis.md` and
`harness/gap_analysis_skill/` stay as records). The exceptions are the
owner's, one part at a time: Katherina's hands (D4d, closed 2026-10-08: the
mitten stays the default, `hand_style`/`grip_style` are the options) and the
`long_parted` hair (D5, a reference regenerated on the tall-chibi body for it,
`docs/detail-status.md`). The lesson of the second: trace nothing below the
chin off a reference whose body is not ours; `harness/hair_audit/gate.py`
checks that first.

Since 2026-08-10 a sibling project consumes this repo's output directly
(`render.sh`/`cover.sh`/`sheet.sh`). This repo has no knowledge of that
consumer; `sheet.py --members` is the one generic hook it added, and it stays a
plain preset-name list. Details of the consumers are kept in `local/`.

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
- **The body is drawn bare only in a base layer.** With the tunic off a
  figure wears underwear (`Outfit.underwear_color`, always worn; the top
  always drawn with a bust), and no anatomical detail is drawn. A fully bare
  figure exists only as a harness view for proportion work
  (`harness/bare/mannequin.py`), adults only, never a web tool option; no
  bare render of a preset whose age is not an adult's
  (the owner's decision, `docs/bare-body-plan.md`).
- **Every preset is an adult, twenty-one or older** (`ADULT_FACE_AGE`). This
  repository is open source, and the age of majority differs by country;
  twenty-one is the highest of the common ones. The tests, the web tool's age
  slider and the bare-body harness enforce the floor. **Consumers must never
  render a character under twenty-one nude.** No story ages, story names or
  sister-repo details go in tracked files: they live in the untracked `local/`
  folder (`local/cover_faces.json` holds the younger face a published cover
  used, which `cover.py` reads when present).
- **No NSFW or anatomical content, until there is a proper adult body.** The
  only figure is the tall chibi, and explicit material on it would read as
  childlike whatever `face_age` says, so the age floor alone is not enough.
  Underwear, swimwear, sleepwear and similar clothing are fine: flat garments
  that cover the body like the ones that exist. A garment must never show more
  of the body than the always-worn underwear does, and these options stay on
  figures at or above `ADULT_FACE_AGE`. Do not add anatomical detail, a nude
  option, or any control that exposes the bare view (`harness/bare/` stays a
  harness). If a real adult build is ever drawn, revisit this as its own
  decision, with the guard in the render code (an adult-proportioned skeleton
  and a face at the floor) rather than in a form field, and put the content in a
  separate package, not in this repository. Requests for it are declined.
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
  `BUILDS` names the chibi, the one build; every character's skeleton
  is its body profile (`BODY_TYPES`) laid over it (`skeleton_for`), and
  `height` stretches that (`stretched`). A part that needs a measurement below the neck
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
- The `gap-analysis` skill is retired with the realistic build it
  measured (moved to `harness/gap_analysis_skill/` as a record on
  2026-09-26; its standing result is `docs/gap-analysis.md`). Chibi work
  and new characters are judged by eye against the design intent.
- Keep the tooling green in the same change: `uv run ruff check .`,
  `uv run ruff format .`, `uv run pytest`. The test suite is a smoke
  check, it renders every preset and compares `ref-out/`, so a failure
  there after a deliberate shape change means running
  `./refresh-ref-out.sh`, not editing the expectation.
- Test color parametrization by rendering at least one palette very
  different from the defaults, confirms `shade()` derivations still
  look right outside the default hue range, not just coincidentally
  right for blonde/green.
- Branches and releases: `main` is released code and `dev` is where work happens. Commit to `dev`, and merge
  into `main` only when the owner says to release and `ruff` and `pytest` pass. Never push `main` or a tag
  unasked. Every push to `main` is a release with a new version: the last commit on `dev` raises `version`
  in `pyproject.toml` (minor for a feature or a new look, patch for a fix; the project is 0.x), then the
  merged commit on `main` gets an annotated `vX.Y.Z` tag, pushed together with `main`. The companion app
  pins these tags, so a tag must never be moved or deleted once pushed.
- The owner's app imports this checkout by path (`../anime-character-creator`), so leave that checkout on
  `main`. Work on `dev` in a second worktree (`git worktree add ../anime-character-creator-dev dev`, then
  `uv sync` in it) and point the companion at it with `CREATOR_SRC=<worktree>/src` to see a change run.
- do NOT commit unless asked
- even if you commit do not write a "co-authored" trailer
- no em dashes "—" (U+2014), double hyphens "--", or similar pause-substitutes in prose / comments;
  hyphens are fine for compound words, prefixes, and ranges, but in running text prefer a period, comma, 
  or restructured sentence instead
- If you disagree (you don't think they add value) with any instructions given, push back once and ask for confirmation
