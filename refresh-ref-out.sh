#!/usr/bin/env bash
# Re-render every named character into ref-out/.
#
# ref-out/ is the only generated output under version control, and the README
# displays it. It is meant to be the *current* state of the named characters
# rather than a snapshot of a past one, so run this in the same change as any
# shape edit; miss it and the README shows art the code no longer produces.
#
#   ./refresh-ref-out.sh          re-render, report which files moved
#   ./refresh-ref-out.sh --check  compare only, write nothing, exit 1 if stale
#
# Each character is rendered twice. The files at the top of ref-out/ are the art
# itself and are transparent, which is what makes them usable as they are. The
# copies under ref-out/on-white/ exist only because the README displays them on
# a page whose colour we do not control: OUTLINE is #0d0d0d, GitHub's dark theme
# is #0d1117, and a transparent figure on that loses its entire outer contour,
# which is the hard-edged look the project is for. Interior line work survives
# either way, since it sits on filled shapes. Same drawing, one paint behind it,
# and nothing outside the README should reach for the on-white copies.
#
# Characters come from `presets.PRESETS` and builds from `skeleton.BUILDS`, read
# out of the installed package, so adding a character here is adding it there.
# Nothing about the pair of names below is baked in.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
py="$root/.venv/bin/python"
if [ ! -x "$py" ]; then
    echo "no .venv here; create one with:  uv sync" >&2
    exit 1
fi

check_only=false
case "${1-}" in
    --check) check_only=true ;;
    "") ;;
    *) echo "usage: $(basename "$0") [--check]" >&2; exit 2 ;;
esac

# Filename suffix per named build. The default build takes the bare character
# name, which is what the committed files and the README's links already use.
#
# A build with no entry here is a hard error rather than a guess. These filenames
# are committed and linked from the README, so inventing one silently would leave
# a link pointing at nothing, and skipping one silently would leave a character
# half-refreshed, which is the exact failure this script exists to prevent.
suffix_for() {
    case "$1" in
        chibi) printf '' ;;
        realistic) printf '_real' ;;
        *) return 1 ;;
    esac
}

# Two command substitutions rather than one call read line by line: bash
# implements here-strings and here-documents by writing a temp file, so anything
# using `<<<` breaks wherever TMPDIR is not writable. Command substitution uses a
# pipe and needs nothing on disk.
listing() {
    MOD="anime_character_creator.$1" NAME="$2" "$py" -c '
import importlib, os
mod = importlib.import_module(os.environ["MOD"])
print(" ".join(sorted(getattr(mod, os.environ["NAME"]))))
' 2>/dev/null || return 1
}
presets=$(listing presets PRESETS) || { echo "could not read PRESETS; is the package installed?  uv sync" >&2; exit 1; }
builds=$(listing skeleton BUILDS) || { echo "could not read BUILDS; is the package installed?  uv sync" >&2; exit 1; }

for build in $builds; do
    if ! suffix_for "$build" >/dev/null; then
        echo "build '$build' has no filename suffix in $(basename "$0"); add one" >&2
        exit 1
    fi
done

# Render into a staging directory and only copy over ref-out/ once every file has
# come out. The CLI's PNG export is best effort: it warns and carries on if
# cairo is missing, so rendering straight into ref-out/ could refresh the SVGs and
# leave the PNGs the README actually displays untouched and stale. Staging also
# makes the change report unambiguous, since an unchanged file and a file that was
# never written are otherwise the same bytes.
#
# Under out/ rather than the system temp directory, so the script needs nothing
# outside the project and does not care how TMPDIR is set or sandboxed. out/ is
# already ignored.
stage="$root/out/.refresh-stage"
rm -rf "$stage"
mkdir -p "$stage"
trap 'rm -rf "$stage"' EXIT

# Parallel arrays rather than colon-packed strings, which would need `<<<` to take
# apart again. Bash 3.2, which is what macOS ships as /bin/bash, has no
# associative arrays.
preset_of=()
build_of=()
stem_of=()
for preset in $presets; do
    for build in $builds; do
        preset_of+=("$preset")
        build_of+=("$build")
        stem_of+=("${preset}$(suffix_for "$build")")
    done
done
count=${#stem_of[@]}

i=0
while [ "$i" -lt "$count" ]; do
    stem=${stem_of[$i]}
    "$root/render.sh" --out "$stage/$stem" --preset "${preset_of[$i]}" --build "${build_of[$i]}" >/dev/null
    # The README's copy. Rendered rather than composited afterwards, so it goes
    # through exactly the same path as the art and cannot drift from it.
    "$root/render.sh" --out "$stage/on-white/$stem" --preset "${preset_of[$i]}" \
        --build "${build_of[$i]}" --background white >/dev/null
    for ext in svg png; do
        if [ ! -s "$stage/$stem.$ext" ]; then
            echo "render produced no $stem.$ext, leaving ref-out/ alone" >&2
            if [ "$ext" = png ]; then
                echo "  PNG export needs the system cairo library: brew install cairo" >&2
            fi
            exit 1
        fi
    done
    if [ ! -s "$stage/on-white/$stem.png" ]; then
        echo "render produced no on-white/$stem.png, leaving ref-out/ alone" >&2
        exit 1
    fi
    i=$((i + 1))
done

changed=0
i=0
while [ "$i" -lt "$count" ]; do
    stem=${stem_of[$i]}
    i=$((i + 1))
    # The SVG decides. It is deterministic text, where a PNG can differ in bytes
    # for reasons that are not the drawing.
    #
    # Its absence does not, though: an on-white copy that was never written, or
    # deleted, leaves a broken image in the README while the drawing itself is
    # perfectly current, so the SVG comparison alone would call that clean.
    if cmp -s "$stage/$stem.svg" "$root/ref-out/$stem.svg" &&
        [ -s "$root/ref-out/on-white/$stem.png" ]; then
        echo "  unchanged  $stem"
        continue
    fi
    changed=$((changed + 1))
    if $check_only; then
        echo "  STALE      $stem"
    else
        echo "  updated    $stem"
    fi
done

if $check_only; then
    if [ "$changed" -gt 0 ]; then
        echo "$changed of $count in ref-out/ do not match the code; run $(basename "$0")" >&2
        exit 1
    fi
    echo "ref-out/ matches the code"
    exit 0
fi

mkdir -p "$root/ref-out/on-white"
i=0
while [ "$i" -lt "$count" ]; do
    stem=${stem_of[$i]}
    cp "$stage/$stem.svg" "$stage/$stem.png" "$root/ref-out/"
    cp "$stage/on-white/$stem.png" "$root/ref-out/on-white/"
    i=$((i + 1))
done
echo "wrote $count characters to ref-out/, $changed changed"
