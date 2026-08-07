#!/usr/bin/env bash
# Run one measurement script with the two things every one of them needs.
#
#     ./harness/run.sh harness/trace/see.py
#
# The two preconditions, both of which used to be footguns:
#
#   cairo. `cairosvg` finds the system library through this variable and it has
#   to be set before the process starts, so exporting it inside Python is too
#   late. `render.sh` does the same thing for the same reason.
#
#   The output directory. These scripts write their images into `out/`, which
#   is ignored and therefore absent on a fresh clone and after any cleanup.
#   Only `variants/export_variants.py` creates its own directory, so the rest
#   would die on `FileNotFoundError` at the first `save()`. Rather than edit
#   fifty scripts, several of which are kept as records of readings that did
#   not work and should not be touched, the directories are made here.
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "usage: ./harness/run.sh harness/<pass>/<script>.py [args...]" >&2
    exit 2
fi

cd "$(dirname "$0")/.."

# Every script does `sys.path.insert(0, "src")` and reads `ref/` by relative
# path, so they only work from the repo root. The `cd` above is what makes the
# runner callable from anywhere.
mkdir -p out/trace out/ear out/ear2 out/trousers out/variants out/head out/scar

export DYLD_FALLBACK_LIBRARY_PATH=":/opt/homebrew/lib"
exec uv run python "$@"
