#!/usr/bin/env bash
# Render the cast as a labelled grid, with the environment PNG export needs set.
#
# Same wrapper, same reason, as render.sh and cover.sh: cairosvg finds libcairo
# through dlopen, which on macOS does not look in Homebrew's prefix, and the
# variable has to be set before the process starts so it cannot live in the CLI.
#
# The sheet is how a *cast* gets judged. Whether these people look like they come
# from one world is a question about the set, which no single render asks, and a
# tile is also the size a character is actually looked at.
#
#     ./sheet.sh
#     ./sheet.sh --out out/sheet/wide --columns 5
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -x "$root/.venv/bin/python" ]; then
    echo "no .venv here; create one with:  uv sync" >&2
    exit 1
fi

# Both prefixes, since Homebrew lives at /opt/homebrew on Apple Silicon and
# /usr/local on Intel, and the two do not agree on which machine wrote this.
export DYLD_FALLBACK_LIBRARY_PATH="${DYLD_FALLBACK_LIBRARY_PATH:-}:/opt/homebrew/lib:/usr/local/lib"
exec "$root/.venv/bin/python" -m anime_character_creator.sheet "$@"
