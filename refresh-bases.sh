#!/usr/bin/env bash
# Re-render the two neutral bases into ref-out/bases/.
#
# The web gallery wants instant-paint art for "Female base" and "Male base"
# the same way it gets it for free from ref-out/<name>.svg for the cast, per
# docs/web-gui-plan.md's "a character is on screen immediately". But
# NEUTRAL_BASES is deliberately not in PRESETS (see presets.py: "that dict is
# the fourteen named characters and nothing else"), so these do not belong at
# ref-out/'s top level, where refresh-ref-out.sh and the README's row-per-
# character test both read PRESETS. bases/ is its own small subdirectory so
# neither of those has to learn about a base, and this script is the one
# place that knows the two exist.
#
# The SVGs come from the TypeScript package (`ts/bin/render.ts`, which reads NEUTRAL_BASES in
# `ts/src/presets.ts`); each PNG is made from its SVG by cairosvg in Python
# (`harness/svg2png.py`), as the Python CLI made it.
#
#   ./refresh-bases.sh          re-render, report which files moved
#   ./refresh-bases.sh --check  compare only, write nothing, exit 1 if stale
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
py="$root/tools/.venv/bin/python"
if [ ! -x "$py" ]; then
    echo "no tools/.venv here; create one with:  uv sync --project tools" >&2
    exit 1
fi
if ! command -v node >/dev/null 2>&1; then
    echo "no node on PATH; the drawing is TypeScript and needs Node 22.18 or newer" >&2
    exit 1
fi
render_ts="$root/ts/bin/render.ts"

check_only=false
case "${1-}" in
    --check) check_only=true ;;
    "") ;;
    *) echo "usage: $(basename "$0") [--check]" >&2; exit 2 ;;
esac

export DYLD_FALLBACK_LIBRARY_PATH="${DYLD_FALLBACK_LIBRARY_PATH:-}:/opt/homebrew/lib:/usr/local/lib"

stage="$root/out/.bases-stage"
rm -rf "$stage"
mkdir -p "$stage"
trap 'rm -rf "$stage"' EXIT

# --no-metadata: the library's own default, which is what ref-out/bases/ has always held.
names=$(node "$render_ts" --list-bases) || { echo "could not read NEUTRAL_BASES from ts/bin/render.ts; is Node 22.18 or newer installed?" >&2; exit 1; }
png_args=()
for name in $names; do
    node "$render_ts" --out "$stage/$name" --preset "$name" --no-metadata >/dev/null
    png_args+=("$stage/$name.svg" "$stage/$name.png")
done
"$py" "$root/harness/svg2png.py" "${png_args[@]}" || { echo "render failed; is cairo installed?  brew install cairo" >&2; exit 1; }

out="$root/ref-out/bases"
mkdir -p "$out"

changed=0
for name in $names; do
    if [ -f "$out/$name.svg" ] && cmp -s "$stage/$name.svg" "$out/$name.svg"; then
        echo "  unchanged  $name"
    else
        changed=$((changed + 1))
        if $check_only; then
            echo "  STALE      $name"
        else
            cp "$stage/$name.svg" "$stage/$name.png" "$out/"
            echo "  updated    $name"
        fi
    fi
done

if $check_only; then
    if [ "$changed" -gt 0 ]; then
        echo "$changed base(s) in ref-out/bases/ do not match the code; run $(basename "$0")" >&2
        exit 1
    fi
    echo "ref-out/bases/ matches the code"
    exit 0
fi

echo "wrote ref-out/bases/, $changed changed"
