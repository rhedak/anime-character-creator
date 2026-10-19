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

**The drawing code is TypeScript** (`ts/src/`, version in `ts/package.json`). The Python package in `src/` was the
original and is **frozen** at the tag `python-final`: it is the reference the TypeScript was proved byte-identical
against. It is still in the tree (`src/`, `tests/`, `pyproject.toml`) only until it is deleted in the next release
(`docs/python-removal-audit.md`); it is not developed, not run in CI and not to be edited. The cover and the sheets
are TypeScript now (`ts/bin/cover.ts`, `ts/bin/sheet.ts`), the comic is dropped, and the shell scripts that wrapped the
Python are gone. New work goes in `ts/`.

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

Since 2026-08-10 a sibling project has consumed this repo's output through the shell scripts
(`render.sh`, `cover.sh`, `sheet.sh`), which were removed on 2026-10-19 with the Python; the tag `python-final` still
has them, and the owner checks the consumers in their own sessions. This repo has no knowledge of that consumer;
`ts/bin/sheet.ts --members` keeps the one generic hook it added, a plain preset-name list. Details of the
consumers are kept in `local/`.

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
  **One opt-in exception, 2026-10-16:** `CharacterParams.finish = "soft"` adds
  gradients and tinted lines (a graded iris, a soft blush, the fringe's
  shadow, lines in a dark tone of what they bound, thinner strokes) and, on the
  cuts that describe them (`Hairstyle.locks`), tone clumps laid inside the
  hair's own silhouette: shadow and lit steps with one faint highlight each,
  scaled by `highlight_strength`. It is for a caller that sets the figure
  beside painted art. It is off by default, never used by the presets, the
  covers, the sheets or `ref-out/` (`tests/test_consumers_stay_flat.py` pins
  that), offered in the web tool as a "Finish" choice that starts on flat, and
  it moves no shape. `"flat"` stays the house style and every rule above still
  holds for it. Gradients only, no blur: cairosvg has none. Anything further in
  the soft finish needs the owner's say, judged by blind pairs, and its record
  is `docs/soft-hair-plan.md` and `docs/soft-hair-status.md`.

## Structure

The drawing is a TypeScript package under `ts/` (Node 22.18 or newer runs the `.ts` files directly; `typescript` and
`@types/node` are dev dependencies for the typecheck and the web build). `ts/package.json` holds the version and the
scripts, `docs/` holds the architecture notes and the API reference, and `harness/` holds the one-off scripts that
measured `ref/` (promoted there out of the ignored `out/` so a cleanup cannot take them; run a Python one with
`./harness/run.sh harness/<pass>/<script>.py`, which uses the small Python project in `tools/` (cairosvg, pillow, numpy
and scipy, no package of ours; `uv sync --project tools` once). A script that imports the original package needs the
`python-final` tag. They are records, several of readings that were wrong, and are not linted). `ts/README.md` is the map; the roles:

- `ts/src/skeleton.ts`, `body.ts`: proportion anchors (`Skeleton`, `buildSkeleton`) and a character's skeleton
  (`BODY_TYPES`, `skeletonFor`; `height` stretches it). Change here to adjust overall proportions. A part that needs a
  measurement below the neck should read an anchor, not multiply `head_r` by a number that only happens to work on a
  chibi.
- `ts/src/colorutil.ts`: `shade()` derives shadow tones from a base color. Use this rather than hand-picking a second
  color per part.
- `ts/src/params.ts`, `model.ts`: the field registry (`CharacterParams`, `Outfit`, `FaceStyle`, `Expression`, with
  defaults and type tags) and the constructors, `replace` and `validateFinish`. `CharacterParams` is the public
  color/style interface. Anything a character needs to differ on belongs here with a neutral default, never hardcoded
  into a part function. The generator has to stay general, not become one character's renderer.
- `ts/src/presets.ts`: named characters as `CharacterParams` values (`SATOKO`). Add a character here, not as a pile of
  CLI flags.
- `ts/src/character.ts`, `core-head*.ts`, `core-limbs*.ts`: the shared vocabulary (stroke widths, `curve`, the document
  wrapper, the post-steps), the hair system (`Hairstyle`, `HAIRSTYLES`) and the limbs.
- `ts/src/hair.ts`, `face.ts`, `face-wear.ts`, `body-parts*.ts`, `garments.ts`, `props.ts`: one function per body part,
  each returning an SVG snippet string. `parts.ts` and `parts-*.ts` register them by name; `render.ts`
  (`renderCharacter`) stacks them in z-order.
- `ts/src/pynum.ts` and the other `py*.ts`: the kernel. Every Python behaviour JavaScript lacks (float formatting,
  `round`, `sum`, `hypot`, slices, `json.dumps`, `colorsys`, `re.sub` templates) lives here, and nothing else in `src/`
  may call `toFixed`, `Math.round`, `Math.hypot`, a bare `sort`, or format a float by hand: a number reaches the SVG
  text only through `fmt0` to `fmt3` or `pyRepr`. Keep arithmetic exactly as written; floating point is not
  associative.
- `ts/src/urlstate.ts`, `attribution.ts`, `catalogue*.ts`, `web-bridge.ts`: character links, the `<metadata>` block,
  what the web tool offers, and its four calls.
- `ts/bin/render.ts`: the SVG command line (`--preset`, `--out`, `--background`, `--no-metadata`, `--finish`,
  `--highlight-strength`, `--id-prefix`); `ts/bin/catalogue.ts` writes the catalogue; `ts/bin/cover.ts` and `ts/bin/sheet.ts` write the cover and the cast sheets.
  PNG export is Python in `tools/`: `harness/svg2png.py` rasterises an SVG with cairosvg, and the refresh scripts use it.
- `ts/test/`: the tests (`node:test`). Most compare the drawing with golden files recorded from the Python
  before it was frozen (the corpus and manifest under `harness/ts_port/` and `ts/fixtures/`, the committed `ref-out/`),
  the rest hold the rules the Python suite held. Nothing runs the Python to compare: the golden files are plain files,
  and a deliberate change to them is the owner's call.
- `src/anime_character_creator/` (frozen Python, deleted in the next release): the reference the golden files were
  recorded from. Nothing wraps or runs it any more.

## Working conventions

- When adding a new body part or hairstyle variant, follow the existing pattern. A part is a function
  `(sk, p) -> string` in the file of its role, using only `sk.*` anchors and `p.*` params, returning `""` when the
  character does not have it, registered in the domain's `parts-*.ts` under its Python-style name and placed in the
  `slots` list of `render.ts` at the correct z-order (give it a slot number nobody has used). A hairstyle is a
  `Hairstyle` entry in `HAIRSTYLES` (`core-head.ts`) that keeps the five-callable contract in `docs/architecture.md`.
  A new field gets a neutral default in `params.ts` and, if the web tool should offer it, an entry in `catalogue*.ts`.
  `ts/README.md`, "How a part is added", has the steps.
- After changing shape geometry, actually render it (`node ts/bin/render.ts --out out/tmp --preset satoko`, then a PNG
  with `tools/.venv/bin/python harness/svg2png.py out/tmp.svg out/tmp.png`) and view it before calling it done, coordinates
  that look right in the math are routinely wrong visually; this is an iterate-by-looking project.
- The `gap-analysis` skill is retired with the realistic build it measured (moved to `harness/gap_analysis_skill/` as a
  record on 2026-09-26; its standing result is `docs/gap-analysis.md`). Chibi work and new characters are judged by eye
  against the design intent.
- Keep the tooling green in the same change. In `ts/`: `npm run typecheck` and `npm test`. At the root:
  `./refresh-ref-out.sh --check`, `./refresh-catalogue.sh --check` and `./refresh-bases.sh --check` (and `--pixels`
  when a change moves the SVG text and no visible pixel). The Python in the tree is frozen and not run: do not edit
  `src/` or `tests/`. A stale `ref-out/` after a deliberate shape change means running `./refresh-ref-out.sh`, not
  editing the expectation.
- **The oracle is the recorded Python output.** The corpus manifest, the recorded calls and `ref-out/` say what the
  Python drew, so a change that moves a byte of an existing character's output makes the TypeScript tests fail on purpose.
  Do not edit the manifest, the recorded fixtures or `ref-out/` to make a failure pass without the owner's say. A new
  part, option or character should default to nothing (a `null` field, a part that returns `""`), so every existing
  document stays byte-identical. New realism work stays behind `finish = "soft"` (flat is the house style and does
  not move), and is judged by blind pairs as `docs/soft-hair-plan.md` describes. The soft finish's consumers
  (the presets, the covers, the sheets, `ref-out/`) are pinned flat by `ts/test/rules-*.test.ts`.
- Test color parametrization by rendering at least one palette very different from the defaults, confirms `shade()`
  derivations still look right outside the default hue range, not just coincidentally right for blonde/green.
- Branches and releases: `main` is released code and `dev` is where work happens. Commit to `dev`, and merge into
  `main` only when the owner says to release and the typecheck, the TypeScript tests and the refresh checks pass. Never push `main` or a tag unasked. Every push to `main` is a
  release with a new version: the last commit on `dev` raises `version` in `ts/package.json` (minor for a feature or a
  new look, patch for a fix; the project is 0.x; the root `pyproject.toml` is frozen with the Python and goes with it), then the merged commit on
  `main` gets an annotated `vX.Y.Z` tag, pushed together with `main`. The companion app pins these tags, so a tag must
  never be moved or deleted once pushed. The tag `python-final` marks the last Python-only commit and is likewise
  never moved.
- Pushes to any branch but `main`, and pull requests, run `.github/workflows/ts-check.yml` (typecheck and the
  TypeScript tests, no deploy). A push to `main` runs `pages.yml`, which also runs the refresh checks (they need cairo and
  `uv sync --project tools`) and then deploys the web tool to GitHub Pages.
- The owner's app imports this checkout by path (`../anime-character-creator`), so leave that checkout on `main`.
  Work on `dev` in a second worktree (`git worktree add ../anime-character-creator-dev dev`, then
  `uv sync --project tools` and `cd ts && npm ci` in it) and point the companion at it to see a change run. (The
  companion draws with this repo's TypeScript; its docs say which tag it pins.)
- do NOT commit unless asked
- even if you commit do not write a "co-authored" trailer
- no em dashes "—" (U+2014), double hyphens "--", or similar pause-substitutes in prose / comments;
  hyphens are fine for compound words, prefixes, and ranges, but in running text prefer a period, comma, 
  or restructured sentence instead
- If you disagree (you don't think they add value) with any instructions given, push back once and ask for confirmation
