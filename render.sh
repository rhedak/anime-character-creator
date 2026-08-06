#!/usr/bin/env bash
# Render a character, with the environment PNG export needs already set.
#
# cairosvg finds libcairo through dlopen, which on macOS does not look in
# Homebrew's prefix, so plain `anime-character-creator` writes the SVG and then
# reports that cairo is unavailable. Setting the fallback path fixes it, and it
# has to be set before the process starts, so it cannot live in the CLI itself.
#
# It runs the package out of the project's own .venv rather than whatever
# `anime-character-creator` is on PATH, so a render always comes from the
# checkout it was started in.
#
# Usage is the CLI's, from anywhere:
#     ./render.sh --out out/satoko --preset satoko
#     ./render.sh --out out/satoko_real --preset satoko --build realistic
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -x "$root/.venv/bin/python" ]; then
    echo "no .venv here; create one with:  uv sync" >&2
    exit 1
fi

export DYLD_FALLBACK_LIBRARY_PATH="${DYLD_FALLBACK_LIBRARY_PATH:-}:/opt/homebrew/lib"
exec "$root/.venv/bin/python" -m anime_character_creator "$@"
