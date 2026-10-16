#!/usr/bin/env bash
# Assemble the deployable site into out/web-stage/, flat. A thin wrapper: the work is
# done by web-stage.mjs, which compiles the TypeScript package with tsc and copies the
# page and ref-out/ beside it (see the comment there for why the layout is flat).
#
#   ./web-stage.sh            stage into out/web-stage/
#   ./web-stage.sh --serve    stage, then serve it on http://127.0.0.1:8000
#
# Needs Node 22.18 or newer and `npm install` (or `npm ci`) once in ts/, which puts tsc at
# ts/node_modules/.bin/tsc; set TSC to another tsc binary to skip that.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec node "$root/web-stage.mjs" "$@"
