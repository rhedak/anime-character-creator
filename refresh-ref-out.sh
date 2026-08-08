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
# The layout, and what each directory is for:
#
#   ref-out/<name>.svg|png           the chibi, every character, transparent
#   ref-out/on-white/<name>.png      the same, on white, for the README only
#   ref-out/real/<name>.svg|png      the realistic build, deferred, a short list
#
# The files at the top are the art itself and are transparent, which is what
# makes them usable as they are. The copies under on-white/ exist only because
# the README displays them on a page whose colour we do not control: OUTLINE is
# #0d0d0d, GitHub's dark theme is #0d1117, and a transparent figure on that loses
# its entire outer contour, which is the hard-edged look the project is for.
# Interior line work survives either way, since it sits on filled shapes. Same
# drawing, one paint behind it, and nothing outside the README should reach for
# the on-white copies.
#
# real/ is a deferral, not an archive. The owner's call on 2026-08-08 was that
# the tall figures do not work well enough to publish and the chibi is where the
# project is, so they moved out of the top level and lost their on-white copies,
# which existed only to be displayed. `presets.REALISTIC_REFS` is the short list
# that still gets one; every other character is chibi-only here. Nothing about
# the realistic *build* changed, and `--build realistic` still works on anything.
#
# Characters come from `presets.PRESETS`, the realistic short list from
# `presets.REALISTIC_REFS` and builds from `skeleton.BUILDS`, all read out of the
# installed package, so adding a character here is adding it there. Nothing about
# the names below is baked in.
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

# Where a build's renders go, relative to ref-out/, as a directory prefix. The
# default build sits at the top level with a bare character name, which is what
# the committed files and the README's links use; the realistic build goes under
# real/, which is the deferral described above.
#
# A build with no entry here is a hard error rather than a guess. These paths are
# committed and linked from the README, so inventing one silently would leave a
# link pointing at nothing, and skipping one silently would leave a character
# half-refreshed, which is the exact failure this script exists to prevent.
prefix_for() {
    case "$1" in
        chibi) printf '' ;;
        realistic) printf 'real/' ;;
        *) return 1 ;;
    esac
}

# Whether a build's renders get an on-white copy. Only the builds the README
# displays do, because that is the only thing on-white is for.
displayed() {
    [ "$1" = chibi ]
}

# The whole-page compositions, each with a `<name>.sh` that renders it. They are
# not characters, so they sit outside the loops below, but they *contain*
# characters, which means they go stale on any shape change rather than only on
# their own, and the sheet goes stale on a new character too. That is why they
# are refreshed here rather than by hand when somebody remembers.
pages="cover sheet"
npages=$(set -- $pages; echo $#)

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
realistic=$(listing presets REALISTIC_REFS) || { echo "could not read REALISTIC_REFS; is the package installed?  uv sync" >&2; exit 1; }

for build in $builds; do
    if ! prefix_for "$build" >/dev/null; then
        echo "build '$build' has no ref-out/ prefix in $(basename "$0"); add one" >&2
        exit 1
    fi
done

# Every name on the short list has to be a character, or a typo there silently
# drops a realistic render instead of failing.
for preset in $realistic; do
    case " $presets " in
        *" $preset "*) ;;
        *) echo "REALISTIC_REFS names '$preset', which is not in PRESETS" >&2; exit 1 ;;
    esac
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
#
# `rel_of` is a path relative to ref-out/ and may contain a slash, so every
# directory it names has to exist in the staging area before a render lands in it.
preset_of=()
build_of=()
rel_of=()
for preset in $presets; do
    for build in $builds; do
        # The chibi is published for everyone; the realistic build only for the
        # short list. A character not on it simply has no tall render, which is
        # the deferral rather than a gap.
        if [ "$build" != chibi ]; then
            case " $realistic " in
                *" $preset "*) ;;
                *) continue ;;
            esac
        fi
        preset_of+=("$preset")
        build_of+=("$build")
        rel_of+=("$(prefix_for "$build")${preset}")
    done
done
# `if` rather than `displayed x && mkdir ...`: under `set -e` a trailing `&&`
# whose left side is false makes the whole loop body fail, and the body's status
# is the loop's, so the script would exit the moment it met a build with no
# on-white copy. That is the one build this change adds.
for build in $builds; do
    mkdir -p "$stage/$(prefix_for "$build")"
    if displayed "$build"; then
        mkdir -p "$stage/on-white/$(prefix_for "$build")"
    fi
done
# Two counts, deliberately. `characters` bounds every loop over `rel_of`, and
# `count` is only ever reported. They were one variable until the cover was
# added to the total, which walked the copy loop one index past the end of the
# array.
characters=${#rel_of[@]}
count=$((characters + npages))

i=0
while [ "$i" -lt "$characters" ]; do
    rel=${rel_of[$i]}
    "$root/render.sh" --out "$stage/$rel" --preset "${preset_of[$i]}" --build "${build_of[$i]}" >/dev/null
    for ext in svg png; do
        if [ ! -s "$stage/$rel.$ext" ]; then
            echo "render produced no $rel.$ext, leaving ref-out/ alone" >&2
            if [ "$ext" = png ]; then
                echo "  PNG export needs the system cairo library: brew install cairo" >&2
            fi
            exit 1
        fi
    done
    if displayed "${build_of[$i]}"; then
        # The README's copy. Rendered rather than composited afterwards, so it
        # goes through exactly the same path as the art and cannot drift from it.
        "$root/render.sh" --out "$stage/on-white/$rel" --preset "${preset_of[$i]}" \
            --build "${build_of[$i]}" --background white >/dev/null
        if [ ! -s "$stage/on-white/$rel.png" ]; then
            echo "render produced no on-white/$rel.png, leaving ref-out/ alone" >&2
            exit 1
        fi
    fi
    i=$((i + 1))
done

# The pages. Neither gets an on-white copy, because each paints its own opaque
# ground over the whole canvas and there is no transparency for a card to sit
# behind.
for page in $pages; do
    "$root/$page.sh" --out "$stage/$page" >/dev/null
    for ext in svg png; do
        if [ ! -s "$stage/$page.$ext" ]; then
            echo "render produced no $page.$ext, leaving ref-out/ alone" >&2
            exit 1
        fi
    done
done

changed=0
i=0
while [ "$i" -lt "$characters" ]; do
    rel=${rel_of[$i]}
    build=${build_of[$i]}
    i=$((i + 1))
    # The SVG decides. It is deterministic text, where a PNG can differ in bytes
    # for reasons that are not the drawing.
    #
    # Its absence does not, though: an on-white copy that was never written, or
    # deleted, leaves a broken image in the README while the drawing itself is
    # perfectly current, so the SVG comparison alone would call that clean. Only
    # the displayed builds have one to be missing.
    fresh=false
    if cmp -s "$stage/$rel.svg" "$root/ref-out/$rel.svg"; then
        fresh=true
        if displayed "$build" && [ ! -s "$root/ref-out/on-white/$rel.png" ]; then
            fresh=false
        fi
    fi
    if $fresh; then
        echo "  unchanged  $rel"
        continue
    fi
    changed=$((changed + 1))
    if $check_only; then
        echo "  STALE      $rel"
    else
        echo "  updated    $rel"
    fi
done

# A render that used to be published and is not any more leaves its old file
# behind, where it goes stale invisibly: nothing above looks at files the loop
# does not name. Called out rather than deleted, because ref-out/ is committed
# and a script that removes tracked files without being asked is worse than a
# stale one.
for orphan in "$root"/ref-out/*_real.svg "$root"/ref-out/*_real.png \
    "$root"/ref-out/on-white/*_real.png; do
    [ -e "$orphan" ] || continue
    echo "  ORPHAN     ${orphan#"$root"/ref-out/}  (realistic renders live in real/ now; git rm it)" >&2
    changed=$((changed + 1))
done

# Same rule as a character: the SVG decides, and it is deterministic text.
for page in $pages; do
    if cmp -s "$stage/$page.svg" "$root/ref-out/$page.svg"; then
        echo "  unchanged  $page"
    else
        changed=$((changed + 1))
        if $check_only; then
            echo "  STALE      $page"
        else
            echo "  updated    $page"
        fi
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

for build in $builds; do
    mkdir -p "$root/ref-out/$(prefix_for "$build")"
    if displayed "$build"; then
        mkdir -p "$root/ref-out/on-white/$(prefix_for "$build")"
    fi
done
i=0
while [ "$i" -lt "$characters" ]; do
    rel=${rel_of[$i]}
    cp "$stage/$rel.svg" "$stage/$rel.png" "$root/ref-out/$(dirname "$rel")/"
    if displayed "${build_of[$i]}"; then
        cp "$stage/on-white/$rel.png" "$root/ref-out/on-white/$(dirname "$rel")/"
    fi
    i=$((i + 1))
done
for page in $pages; do
    cp "$stage/$page.svg" "$stage/$page.png" "$root/ref-out/"
done
echo "wrote $count renders to ref-out/, $changed changed"
