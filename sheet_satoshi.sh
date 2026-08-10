#!/usr/bin/env bash
# The other cast sheet: `ROSTERS["satoshi"]`, Satoshi's persona rather than
# Satoko's, so Tomohiro stays and Satoko and Kyoko drop. Same page, same
# `sheet.py`, just the other roster; see its comment in presets.py for why the
# split exists. This wrapper exists so `refresh-ref-out.sh` has a `<name>.sh`
# to call the way it does for `sheet` and `cover`.
#
#     ./sheet_satoshi.sh
#     ./sheet_satoshi.sh --out out/sheet_satoshi/wide --columns 5
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -x "$root/.venv/bin/python" ]; then
    echo "no .venv here; create one with:  uv sync" >&2
    exit 1
fi

# Both prefixes, since Homebrew lives at /opt/homebrew on Apple Silicon and
# /usr/local on Intel, and the two do not agree on which machine wrote this.
export DYLD_FALLBACK_LIBRARY_PATH="${DYLD_FALLBACK_LIBRARY_PATH:-}:/opt/homebrew/lib:/usr/local/lib"
exec "$root/.venv/bin/python" -m anime_character_creator.sheet --roster satoshi \
    --out out/sheet_satoshi/sheet_satoshi "$@"
