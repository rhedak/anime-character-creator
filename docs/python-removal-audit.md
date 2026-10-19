# Removing the Python side: audit

Written 2026-10-19 at the owner's request, as a read-only audit before any deletion. Nothing was changed to produce it. The tag `python-final` already marks the last Python-only
commit, so the history is safe whatever is decided here.

## Verdict

Doing it is sound, and it unlocks real things (below). It is not one change but six, and the order matters because the Python currently does five jobs besides drawing, three of which
have no TypeScript replacement. One of the five has a consumer that is not in this repository and has to be asked about first.

## Decisions (owner, 2026-10-19)

1. **Cover and sheets are ported to TypeScript. The comic package is dropped.** The port has to land before the Python is deleted, because the Python `cover.py`/`sheet.py` output is the oracle to compare the port against (the six files in `ref-out/` are the first golden: `cover`, `sheet`, `sheet_satoshi`, SVG and PNG). `ROSTERS` moves with `sheet.py`. Nothing is frozen.
2. **`render.sh`, `cover.sh`, `sheet.sh` and `sheet_satoshi.sh` are dropped**, with the Python. The sibling consumers are checked by the owner in separate sessions; the `python-final` tag keeps the scripts runnable for them.
3. **The 182 harness scripts that import the package are deleted** (they are in the history). The 136 that need only numpy, scipy, pillow and cairosvg stay.

## Progress

- Stage 2 done: `tools/` is a small uv project (cairosvg 2.9.0, pillow 12.3.0, numpy 2.4.6, scipy 1.17.1, and the rest of the cairosvg chain at the versions the root lock had). `refresh-ref-out.sh`, `refresh-bases.sh`, `harness/run.sh` and `probe.sh` use it. `./refresh-ref-out.sh --pixels` reports 0 of 43 PNGs differ, `--check` of bases and catalogue clean. Create it with `uv sync --project tools`.
- Stage 3 done: the live-Python comparisons in `cli.test.ts` and `catalogue.test.ts`, and the three tests that read the Python source for comment parity (`presets`, `supporting`, `catalogue`), are gone; the options tests (finish, highlight strength, background, id prefix) are TypeScript-only now. The committed fixtures are the golden files.
- Found on the way: `--id-prefix` takes the prefix through a replacement template, as the Python did, so a prefix containing a backslash and a digit (`back\1`) is mangled. Harmless for the ids the tools use; not pinned by a test.

## What the Python does today

| job | where | has a TypeScript replacement? |
|---|---|---|
| draws characters (the original) | `src/anime_character_creator/` (20 files, 19.5k lines) | yes, byte-identical, since 0.4.0 |
| the full command line | `generate.py`, `render.sh` | partly: `ts/bin/render.ts` has `--preset`, `--out`, `--background`, `--finish`, `--highlight-strength`, `--id-prefix`, `--metadata`; it says it lacks the colour, garment, face and shape flags, `--expression` and `--flat` on purpose |
| book cover | `cover.py` (430 lines), `cover.sh` | no |
| the cast sheets | `sheet.py` (308 lines), `sheet.sh`, `sheet_satoshi.sh`, `ROSTERS` in `presets.py` | no |
| comic pages | `comic/` (990 lines, 3 test files, `harness/comic/`, `docs/comic/`) | no |
| PNG export | `harness/svg2png.py` (cairosvg), called by `refresh-ref-out.sh` and `refresh-bases.sh` | no, and it does not need the package |
| the oracle for the port | 14 test files, 1051 tests, `harness/ts_port/*.py` generators | not needed after the port, see below |

## What breaks, by area

**Python tests and tooling (all go with the package).** `tests/` (14 files, 1051 tests), `pyproject.toml`, `uv.lock`, `ruff` and `pytest` runs.

**TypeScript tests.** They do not need Python to pass. Two groups compare against a live Python run and skip without a `.venv`:
- `ts/test/cli.test.ts`: renders every preset with `render.sh` and compares the SVG with the TS command line. Those comparisons have to be deleted; the TS-only tests in the file stay.
- `ts/test/catalogue.test.ts`: one test runs `harness/ts_port/gen_catalogue_expected.py`. Its fallback path is hard-coded to one machine (`/Users/hanssen.henrik/.../.venv/bin/python`), a latent bug whatever is decided.

Everything else reads committed fixtures (`ts/fixtures/`, `harness/ts_port/corpus` and `manifest`, `ref-out/`, 18 MB in all). Those become the golden files and stop being "the oracle".
The generators that made them (`harness/ts_port/gen_*.py`, `cases.py`, `manifest.py`) die with the package. One TS source file is generated from Python: `ts/src/props-tables.ts` (by `gen_props.py`); it becomes hand-maintained.

**CI.** `.github/workflows/pages.yml` runs `uv sync`, `uv run pytest`, installs `libcairo2` and runs the three refresh checks. `ts-check.yml` is TypeScript only and is unaffected. The refresh checks still need cairosvg for PNGs (see below).

**PNG export.** `refresh-ref-out.sh` and `refresh-bases.sh` need a Python with cairosvg (and cairo). They do not need the package. So a small Python environment must stay: cairosvg, pillow, numpy, scipy. Today these come from `[dependency-groups] dev` in `pyproject.toml`, which also installs the package. This has to be separated before `pyproject.toml` can go.

**Cover, sheets, comic.** `refresh-ref-out.sh` renders `cover`, `sheet` and `sheet_satoshi` (SVG and PNG, six checked-in files) through `cover.sh` and `sheet.sh`, and `--check` fails if they are stale. The README displays them. They are built on the Python drawing code (`character.py`), so deleting `src/` stops them being regenerable. Options: port to TypeScript, freeze the six files as committed art (and drop them from `--check`), or drop the feature. The comic package has no checked-in output but is documented and tested.

**The sibling consumer.** `CLAUDE.md` says that since 2026-08-10 a sibling project consumes this repo's output through `render.sh`, `cover.sh` and `sheet.sh`, with chapter-scanning on its side and `sheet.py --members` added for it. Its details are kept in an untracked `local/` folder that does not exist in this worktree. This is the one consumer I cannot assess. **It needs the owner's answer before anything is deleted.**

**The companion app (`anime_ai_companion`).** Not affected at run time: its `CLAUDE.md` says no Python is needed, and it draws with the creator's TypeScript (`CREATOR_SRC`, default `../anime-character-creator/ts/src`). It pins creator tags (README: `v0.4.0`, `AGENTS.md`: `v0.3.0`, which is already out of date), and its CI checks the creator out. What does break: `python/make_sample_pack.py` (imports `anime_character_creator` from `../anime-character-creator/src`), and `test/doctor.test.ts` still has a case for the older `src` layout. A release without Python must be a new tag; the pinned older tags keep working.

**Harness scripts.** 318 Python files; 182 import the package (`ts_port` 28, `trace` 23, `detail` 21, `bare` 11, `soft_hair` 9, `trace_hands` 8, `bust` 8, `risa` 7, and a tail of smaller folders). The other 136 need only numpy, scipy, pillow and cairosvg. All of the current Franzi work (`harness/franzi`, `franzi_hair`, `franzi_feet`, `franzi_hands`) and the `trace-reference` skill's `trace_lib.py` are in the second group: none imports the package (checked), and `aligned.py`, `eyes.py` and `eyes_measure.py` only call `harness/svg2png.py`, so they need the PNG toolchain of stage 2 and nothing else. The 182 are mostly records of earlier measurements.

**Docs and rules.** `CLAUDE.md`, `README.md`, `ts/README.md`, `AGENTS.md` and about eight files under `docs/` describe the Python as the frozen reference and the oracle. `CLAUDE.md` has rules that only exist because of it: do not edit `src/` or `tests/`; existing characters must stay byte-identical; the manifest, recorded calls and `ref-out/` are not to be edited; new fields default to nothing; the adult additions live in `EXTRA_*` tables and `ADULT_PRESETS` to keep clear of the mirrored tests. These all need rewriting.

## What it unlocks

- Franzi can join `PRESETS` and with it the catalogue, the web tool, `ref-out/` and the command line (today she is in `ADULT_PRESETS` for exactly this reason).
- The `EXTRA_HAIRSTYLES` and `ADULT_BODY_TYPES` side tables can be folded into the main ones.
- "Existing characters stay byte-identical" can be replaced by golden fixtures that the owner updates on purpose, which is what it effectively is.
- One language and one toolchain; CI without `uv sync` and the Python suite.

## Staged order

Each stage is its own commit (or few), green on its own, and only the last one deletes anything.

1. **Decide** (owner; done, see Decisions above). (a) What happens to cover, sheets and comic: port, freeze the six files, or drop. (b) Who is the sibling consumer, and does it need `render.sh`, `cover.sh`, `sheet.sh` after the next release. (c) Whether the 182 historical harness scripts are kept as records (needing the `python-final` tag to run) or removed.
2. **Separate the PNG toolchain.** A small Python project (or `uv run --with`) holding cairosvg, pillow, numpy and scipy, not the package; point the two refresh scripts and the harness runner at it. `pyproject.toml` keeps working meanwhile. Nothing deleted.
3. **Cut the TypeScript tests loose from live Python.** Delete the Python comparisons in `cli.test.ts` and `catalogue.test.ts` (fix the hard-coded path while there); keep the committed fixtures as golden. Gate: `npm test` without a `.venv`.
4. **Handle cover, sheets and comic** as decided in stage 1. If frozen: take the three pages out of `refresh-ref-out.sh` and its `--check`, keep the six files, and say in the README that they are not regenerated. If ported: that is its own project.
5. **CI and docs.** Remove `uv sync`, `pytest` and `ruff` from `pages.yml`; keep cairo and the PNG tool; rewrite `CLAUDE.md`, `README.md`, `ts/README.md`, `AGENTS.md` and the `docs/` files that call the Python the oracle. Update or remove the companion's `python/make_sample_pack.py` and its `doctor` case, and its pinned tag.
6. **Delete.** With `git rm` (recoverable from history and from `python-final`): `src/`, `tests/`, `pyproject.toml` and `uv.lock` if stage 2 moved the tools, `generate.py`'s shell wrappers (`render.sh`, `cover.sh`, `sheet.sh`, `sheet_satoshi.sh`), `harness/ts_port` generators, and the harness scripts decided in stage 1. Raise the version (0.5.0, since a Python consumer breaks), tag, and let the owner say when to push `main`.
7. **Then Franzi into `PRESETS`** (stage 7 of the adult-body plan): catalogue entry, `ref-out/` render, README table row, command line; and fold the `EXTRA_*` tables in.

## Risks

- Pinned tags: the companion and any sibling consumer pin tags; the release that removes Python must be a new tag, and no existing tag may be moved (the rule in `CLAUDE.md`).
- The refresh checks compare PNG bytes made by cairosvg; they must keep running on the same cairo as CI, which stage 2 must not disturb.
- The six cover and sheet files will go stale the day a character changes, if frozen. That is a documentation cost, not a test cost, once they are out of `--check`.
- The 182 harness scripts that import the package stop running; they are records, but several are cited in `docs/`, which then points at scripts that need the tag.

## What I did not check

The sibling consumer (nothing of it is in this checkout); whether `local/` exists in the main checkout `../anime-character-creator`. (An earlier draft of this audit listed `aligned.py`, `eyes.py` and `eyes_measure.py` as importers of the package; that was a misread of a search, and is corrected above.)
