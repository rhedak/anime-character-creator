#!/usr/bin/env bash
# Render a book cover, with the environment PNG export needs already set.
#
# Same wrapper, same reason, as render.sh: cairosvg finds libcairo through
# dlopen, which on macOS does not look in Homebrew's prefix, and the variable
# has to be set before the process starts so it cannot live in the CLI.
#
#     ./cover.sh
#     ./cover.sh --preset satoshi --build realistic --out out/cover/tall
#     ./cover.sh --title "THE HERO" --title "OF THE MIST" --title "TRAGEDY"
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -x "$root/.venv/bin/python" ]; then
    echo "no .venv here; create one with:  uv sync" >&2
    exit 1
fi

export DYLD_FALLBACK_LIBRARY_PATH="${DYLD_FALLBACK_LIBRARY_PATH:-}:/opt/homebrew/lib"
exec "$root/.venv/bin/python" -m anime_character_creator.cover "$@"
