# ts_port: Python side of the stage oracle for the TypeScript port

Everything here runs the FROZEN Python package from this worktree's `src/` (the scripts
force it first on sys.path and assert `anime_character_creator.__file__` is under it; the
editable install in the venv points elsewhere). Run from the worktree root:

    PY=/Users/hanssen.henrik/git/self-study/anime-character-creator-dev/.venv/bin/python
    export PYTHONPATH=$PWD/src PYTHONDONTWRITEBYTECODE=1

- `_bootstrap.py`  sys.path and package-location guard. Import it first.
- `instrument.py`  AST import hook for `anime_character_creator.character`. Records every
  element of `chest`, `under_arms`, `layers` (named `chest[i]` by position in the list
  literal, starred slots counted but not recorded) plus `body`, `body_soft`, `body_ns`,
  `doc`. `render_stages(params, **kwargs)` returns {skeleton, stages}.
- `cases.py`  builds `corpus/mini.json` (68 cases, full nested params) and rebuilds
  CharacterParams from it. `$PY harness/ts_port/cases.py write|check`
- `manifest.py`  `$PY harness/ts_port/manifest.py build|verify|check-docs|dump`
  and `show CASE_ID STAGE_NAME` (STAGE_NAME may be `skeleton`).
  `build` and `verify` first prove the hooked doc equals the unhooked doc (second
  interpreter, sha256) for every case. `dump` writes out/stages/<case>.json
  (gitignored) with the full stage texts for the TS unit tests.
- `time_layers.py`  `$PY harness/ts_port/time_layers.py [--reps 5]` times the unhooked
  renderer per case and each layer expression alone; writes out/time-python.json.

`manifest/mini.json` and `corpus/mini.json` are committed; `out/` is not. If `verify`
reports a src_sha256 difference, the frozen source changed and the manifest is stale.
The `.gitignore` re-includes `manifest/` because the repo root ignores `MANIFEST`, which
matches that directory on a case-insensitive filesystem.
