#!/usr/bin/env bash
# Re-emit ref-out/catalogue.json from the TypeScript package (`ts/bin/catalogue.ts`, which
# writes `toJson()` of `ts/src/catalogue.ts`).
#
# The web tool's controls and its instant first paint both read this file, so
# it is committed the same way the SVGs in ref-out/ are: current on disk
# rather than regenerated only when the page happens to load.
#
#   ./refresh-catalogue.sh          re-emit, report whether it changed
#   ./refresh-catalogue.sh --check  compare only, write nothing, exit 1 if stale
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v node >/dev/null 2>&1; then
    echo "no node on PATH; the catalogue is written by TypeScript and needs Node 22.18 or newer" >&2
    exit 1
fi

check_only=false
case "${1-}" in
    --check) check_only=true ;;
    "") ;;
    *) echo "usage: $(basename "$0") [--check]" >&2; exit 2 ;;
esac

out="$root/ref-out/catalogue.json"
tmp="$root/out/.catalogue-stage.json"
mkdir -p "$root/out"
node "$root/ts/bin/catalogue.ts" "$tmp"

if [ -f "$out" ] && cmp -s "$tmp" "$out"; then
    rm -f "$tmp"
    echo "ref-out/catalogue.json matches the code"
    exit 0
fi

if $check_only; then
    rm -f "$tmp"
    echo "ref-out/catalogue.json does not match the code; run $(basename "$0")" >&2
    exit 1
fi

mv "$tmp" "$out"
echo "wrote ref-out/catalogue.json"
