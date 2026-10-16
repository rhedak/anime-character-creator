# Releasing the TypeScript port: the checklist

Nothing below has been done. Every step that publishes (a merge to `main`, a tag, a push) waits for the owner's say, as
`CLAUDE.md` requires. The two repos are released separately, creator first, because the companion pins a creator tag.

## Before either release (owner)

1. Open the cross-engine page in **Safari** and **Firefox**: `cd ts && TSC=<a tsc binary> node web-check/stage.mjs --serve`, then
   `http://127.0.0.1:8765/`. All 15 rows green (Chrome 155 already is). Send the red rows if any.
2. Read and approve (or change) `docs/ts-port-claude-md-proposal.md`; the orchestrator then applies it to `CLAUDE.md`.
3. Try the web tool from the staged build: `node web-stage.mjs --serve`, `http://127.0.0.1:8000/`: pick a character, drag a few sliders,
   copy the link, open it in a new tab, download SVG and PNG.
4. Try the companion app from the `ts-port` worktree of the companion with the creator's `ts-port` checkout:
   `CREATOR_SRC=<creator>/ts/src npm start`: no Python needed, she draws, the soft default is there, a look change by chat works.
5. Check on GitHub (the sandbox could not): Settings, Pages: source "GitHub Actions"; whether a non-`main` branch can deploy
   (only matters if a preview from a branch is wanted); the Actions history of the `ref-out` comparison on Linux.

## Creator release (v0.4.0)

1. Tag the last Python-only commit `python-final` (annotated). The tree of `v0.3.0` is that commit's tree: `git tag -a python-final v0.3.0^{}`
   style, or on the merge commit `8318963`; the orchestrator will propose the exact object.
2. Merge `ts-port` into `dev`, then `dev` into `main` only when `cd ts && npm ci && npm run typecheck && npm test`, the three refresh
   `--check` scripts, `uv run pytest` and `uv run ruff check .` pass (the frozen Python must still pass).
3. Version: `ts/package.json` is already 0.4.0 (the owner's number). Update `STATUS.md`'s release line. `pyproject.toml` stays with the Python.
4. Annotated tag `v0.4.0` on the merged commit; push `main` and the tag together (this deploys the web tool to GitHub Pages: the first
   deploy without Pyodide; watch the workflow and open the live page afterwards).
5. Apply the approved `CLAUDE.md` text in the same merge.

## Companion release (v0.8.0), after the creator tag exists

1. In the companion `ts-port` worktree: `package.json` `creator.ref` to `v0.4.0`; the README and `site/pages/getting-started.md` clone commands
   follow (`test/docs.test.ts` pins them to the ref); `version` to 0.8.0 (and the lockfile).
2. `./check.sh --full` with no drift override (the creator checkout next to it at `v0.4.0`).
3. Merge `ts-port` into `dev`, `dev` into `main` when the owner says; annotated tag `v0.8.0`; push `main` and the tag together (the pre-push hook runs
   `check.sh --full`). The pages workflow publishes the docs site and the demo (now without Pyodide): open both afterwards.

## After

* Remove the frozen Python (decision D8): one release later, on the owner's say; then the three file names `CLAUDE.md` still points at
  (`character.py`, `tests/test_consumers_stay_flat.py`, `ADULT_FACE_AGE`) get their one-line edits (see the proposal).
* The queue of changes held back during the freeze: `docs/ts-port-queue.md` (empty so far).
* `cover.py`, `sheet.py`, the full command line, the comic package and the sibling project (D5, D6) stay Python until raised.
