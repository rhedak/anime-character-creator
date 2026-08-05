#!/usr/bin/env bash
# Render a character, with the environment PNG export needs already set.
#
# cairosvg finds libcairo through dlopen, which on macOS does not look in
# Homebrew's prefix, so a plain `python generate.py` writes the SVG and then
# reports that cairo is unavailable. Setting the fallback path fixes it, and it
# has to be set before the process starts, so it cannot live in generate.py.
#
# Usage is generate.py's, from anywhere:
#     ./render.sh --out out/satoko --preset satoko
#     ./render.sh --out out/satoko_real --preset satoko --build realistic
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -x "$root/.venv/bin/python" ]; then
    echo "no .venv here; create one with:  uv venv && uv pip install -r requirements.txt" >&2
    exit 1
fi

export DYLD_FALLBACK_LIBRARY_PATH="${DYLD_FALLBACK_LIBRARY_PATH:-}:/opt/homebrew/lib"
exec "$root/.venv/bin/python" "$root/src/generate.py" "$@"
