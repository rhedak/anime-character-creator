#!/usr/bin/env bash
# Assemble the deployable site into out/web-stage/, flat.
#
# web/index.html fetches "ref-out/catalogue.json" and
# "src/anime_character_creator/*.py" as plain relative paths, which only
# resolve correctly if those directories are siblings of index.html at
# whatever root serves the page. They are not siblings in the repository,
# ref-out/ and src/ sit at the top level and web/ is its own directory, on
# purpose: CLAUDE.md keeps the site out of anything that looks like working
# notes, and ref-out/ is shared with the README and the test suite. So this
# script does the one thing that reconciles the two: copy the three into one
# flat directory, which is what both a local test server and the GitHub
# Actions deploy (.github/workflows/pages.yml) serve from, so neither can
# disagree with the other about the layout.
#
#   ./web-stage.sh            stage into out/web-stage/
#   ./web-stage.sh --serve    stage, then serve it on http://localhost:8000
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
stage="$root/out/web-stage"

rm -rf "$stage"
mkdir -p "$stage"
cp "$root"/web/*.html "$root"/web/*.css "$root"/web/*.js "$stage/"
cp -r "$root/ref-out" "$stage/ref-out"
mkdir -p "$stage/src/anime_character_creator"
cp "$root"/src/anime_character_creator/*.py "$stage/src/anime_character_creator/"

echo "staged at $stage"

if [ "${1-}" = "--serve" ]; then
    cd "$stage"
    python3 -m http.server 8000
fi
