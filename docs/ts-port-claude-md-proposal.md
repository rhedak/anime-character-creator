# Proposed CLAUDE.md for the TypeScript cutover

For the owner to approve. `CLAUDE.md` itself has **not** been edited (it holds the rules, and the rules are the
owner's). Below is the text of the sections that change, written as complete replacements, and a short list of
what changed and why. Everything else in `CLAUDE.md` stays as it is: the opening of "What this project is" (apart from
the one paragraph added below), all of "Hard constraints" (word for word; see the note at the end about the Python
file names it mentions), and the four closing rules of "Working conventions", which are repeated unchanged at the end
of the replacement (the dash rule is only pointed at, so that this page obeys it) so the section can be pasted whole.

## What changed, and why

1. **"What this project is": one paragraph added.** A reader must learn first that the drawing is TypeScript and the
   Python is a frozen reference, or the rest reads wrongly.
2. **"Structure": rewritten.** It described `src/anime_character_creator/*.py` and the Python console script. It now
   describes `ts/src/` by role, `ts/bin/`, the oracle, the kernel and what stays Python (the full CLI, cover, sheet, the
   comic package, PNG export).
3. **"Working conventions": rewritten.** Where a part or a hairstyle goes now; the checks to run (typecheck, node tests,
   the three refresh scripts, and the frozen Python's own pytest and ruff while it is in the tree); the rule for
   changes to the look after the port (the oracle is the frozen Python, so a new part defaults to nothing and new
   realism work stays behind `finish = "soft"`); branches and releases with the version in `ts/package.json`.
4. **Unchanged on purpose:** the hard constraints (style rules, the adult floor, no AI image generation, no NSFW, flat
   colour with the one opt-in soft finish), and the last four bullets (no commit unless asked, no co-author trailer,
   no em dashes or double hyphens in prose, push back once).
5. **Not decided here, for you:** see "Decisions for the owner" at the end.

## Insert after the first paragraph of "What this project is"

```markdown
**The drawing code is TypeScript** (`ts/src/`, version in `ts/package.json`). The Python package in `src/` was the
original and is **frozen** at the tag `python-final`: it is the reference the TypeScript was proved byte-identical
against, it stays in the tree for one more release, and it is not developed. `generate.py` (the full command line),
`cover.py`, `sheet.py`, `sheet_satoshi` and the `comic/` package are still Python and stay out of the port until the
owner raises them. Do not change `src/` or `tests/` except to keep them passing; new work goes in `ts/`.
```

## Replace "Structure" with

````markdown
## Structure

The drawing is a TypeScript package under `ts/` (Node 22.18 or newer runs the `.ts` files directly; `typescript` and
`@types/node` are dev dependencies for the typecheck and the web build). `ts/package.json` holds the version and the
scripts, `docs/` holds the architecture notes and the API reference, and `harness/` holds the one-off scripts that
measured `ref/` (promoted there out of the ignored `out/` so a cleanup cannot take them; run a Python one with
`./harness/run.sh harness/<pass>/<script>.py`; excluded from ruff on purpose, since several are records of readings
that were wrong). `ts/README.md` is the map; the roles:

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
  `--highlight-strength`, `--id-prefix`); `ts/bin/catalogue.ts` writes the catalogue. PNG export is Python:
  `harness/svg2png.py` rasterises an SVG with cairosvg, and the refresh scripts use it.
- `ts/test/`: the tests (`node:test`). Most compare the port with the frozen Python's recorded output (the corpus and
  manifest under `harness/ts_port/`, the committed `ref-out/`), the rest hold the rules the Python suite held.
- `src/anime_character_creator/` (frozen Python): the reference. `generate.py` is still the full command line,
  `cover.py`, `sheet.py` and `comic/` are still how a cover, a sheet and a comic are made, and `./render.sh`,
  `./cover.sh`, `./sheet.sh` run them from the project's `.venv`.
````

## Replace "Working conventions" with

````markdown
## Working conventions

- When adding a new body part or hairstyle variant, follow the existing pattern. A part is a function
  `(sk, p) -> string` in the file of its role, using only `sk.*` anchors and `p.*` params, returning `""` when the
  character does not have it, registered in the domain's `parts-*.ts` under its Python-style name and placed in the
  `slots` list of `render.ts` at the correct z-order (give it a slot number nobody has used). A hairstyle is a
  `Hairstyle` entry in `HAIRSTYLES` (`core-head.ts`) that keeps the five-callable contract in `docs/architecture.md`.
  A new field gets a neutral default in `params.ts` and, if the web tool should offer it, an entry in `catalogue*.ts`.
  `ts/README.md`, "How a part is added", has the steps.
- After changing shape geometry, actually render it (`node ts/bin/render.ts --out out/tmp --preset satoko`, then a PNG
  with `.venv/bin/python harness/svg2png.py out/tmp.svg out/tmp.png`) and view it before calling it done, coordinates
  that look right in the math are routinely wrong visually; this is an iterate-by-looking project.
- The `gap-analysis` skill is retired with the realistic build it measured (moved to `harness/gap_analysis_skill/` as a
  record on 2026-09-26; its standing result is `docs/gap-analysis.md`). Chibi work and new characters are judged by eye
  against the design intent.
- Keep the tooling green in the same change. In `ts/`: `npm run typecheck` and `npm test`. At the root:
  `./refresh-ref-out.sh --check`, `./refresh-catalogue.sh --check` and `./refresh-bases.sh --check` (and `--pixels`
  when a change moves the SVG text and no visible pixel). While the frozen Python is in the tree, also
  `uv run ruff check .` and `uv run pytest`, which must keep passing (do not edit `src/` or `tests/` to make a new
  TypeScript behaviour pass). A stale `ref-out/` after a deliberate shape change means running `./refresh-ref-out.sh`,
  not editing the expectation.
- **The oracle is the frozen Python.** The corpus manifest, the recorded calls and `ref-out/` say what the Python
  drew, so a change that moves a byte of an existing character's output makes the TypeScript tests fail on purpose.
  Do not edit the manifest, the recorded fixtures or `ref-out/` to make a failure pass without the owner's say. A new
  part, option or character should default to nothing (a `null` field, a part that returns `""`), so every existing
  document stays byte-identical. New realism work stays behind `finish = "soft"` (flat is the house style and does
  not move), and is judged by blind pairs as `docs/soft-hair-plan.md` describes. The Python tests that guard the
  soft finish's consumers (`tests/test_consumers_stay_flat.py`) have TypeScript counterparts in `ts/test/rules-*.test.ts`.
- Test color parametrization by rendering at least one palette very different from the defaults, confirms `shade()`
  derivations still look right outside the default hue range, not just coincidentally right for blonde/green.
- Branches and releases: `main` is released code and `dev` is where work happens. Commit to `dev`, and merge into
  `main` only when the owner says to release and the typecheck, the TypeScript tests and the refresh checks pass (and
  `ruff` and `pytest` while the Python is in the tree). Never push `main` or a tag unasked. Every push to `main` is a
  release with a new version: the last commit on `dev` raises `version` in `ts/package.json` (minor for a feature or a
  new look, patch for a fix; the project is 0.x; `pyproject.toml` is frozen with the Python), then the merged commit on
  `main` gets an annotated `vX.Y.Z` tag, pushed together with `main`. The companion app pins these tags, so a tag must
  never be moved or deleted once pushed. The tag `python-final` marks the last Python-only commit and is likewise
  never moved.
- Pushes to any branch but `main`, and pull requests, run `.github/workflows/ts-check.yml` (typecheck and the
  TypeScript tests, no deploy). A push to `main` runs `pages.yml`, which also runs the frozen Python's tests and the
  refresh checks and then deploys the web tool to GitHub Pages.
- The owner's app imports this checkout by path (`../anime-character-creator`), so leave that checkout on `main`.
  Work on `dev` in a second worktree (`git worktree add ../anime-character-creator-dev dev`, then `uv sync` and
  `cd ts && npm ci` in it) and point the companion at it to see a change run. (The companion reads the Python until its
  own port to the TypeScript; its docs say which.)
- do NOT commit unless asked
- even if you commit do not write a "co-authored" trailer
- <keep the existing bullet about em dashes, double hyphens and similar pause-substitutes exactly as it is; it is not
  repeated here so that this page itself obeys it>
- If you disagree (you don't think they add value) with any instructions given, push back once and ask for confirmation
````

## A note on the hard constraints

They are kept exactly. Three of them name Python files or tests that still exist and still mean what they say
(`character.py`, `tests/test_consumers_stay_flat.py`, `ADULT_FACE_AGE` in `character.py`), because the Python is
frozen, not removed. When the Python is removed (decision D8), those names need a one-line edit each to point at
`ts/src/model.ts`, `ts/src/character.ts` and `ts/test/rules-finish.test.ts`; I have not made it, so that nothing in
that section moves before you say.

## Decisions for the owner

* **The oracle after the first deliberate look change.** Python's manifest cannot be regenerated by the TypeScript
  (it records what the Python drew). Options: (a) keep every new thing default-off so the oracle never moves, and
  retire it with the Python (the rule proposed above); (b) when a change is approved, rebuild the TypeScript's own
  manifest from the TypeScript and keep the Python one as `python-final`'s record. I propose (a) now and (b) only
  when a signed change needs it.
* **The package name** in `ts/package.json` is still `anime-character-creator-ts`; it is private, so it only shows in
  the lockfile. Rename at cutover if you want it to read `anime-character-creator`.
* **The tracing tools** (`.claude/skills/trace-reference`, `harness/hair_parted/emit.py`) emit Python source into
  `character.py`. A new traced shape needs an emitter for TypeScript tables, or the skill is retired. The text of the
  skill is not changed by this proposal.
