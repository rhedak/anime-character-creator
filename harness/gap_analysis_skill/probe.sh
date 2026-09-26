#!/usr/bin/env bash
# Run probe.py against the project's own .venv, from anywhere.
#
# A wrapper rather than a documented `python path/to/probe.py` for two reasons.
# The measurement needs Pillow, which the system python here does not have, so
# the interpreter has to be the project's; and holding the invocation in a shell
# variable, the obvious alternative, silently fails under zsh, which does not
# word-split an unquoted variable the way bash does. Same reasoning as
# `render.sh` at the project root.
#
# Usage is probe.py's:
#     .claude/skills/gap-analysis/probe.sh --help
#     .claude/skills/gap-analysis/probe.sh skeleton
#     .claude/skills/gap-analysis/probe.sh profile ref/satoko-chibi.jpg ref-out/satoko.png
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/../../.." && pwd)"

if [ ! -x "$root/.venv/bin/python" ]; then
    echo "no .venv here; create one with:  uv sync" >&2
    exit 1
fi

# Run from the repo root, because that is what the `ref/`, `ref-out/` and
# `out/NN/` paths in SKILL.md are relative to. The consequence: **every relative
# path in the arguments resolves against the repo root, not against wherever the
# caller stood.** Called from elsewhere, pass absolute paths, which work
# unchanged.
cd "$root"
exec "$root/.venv/bin/python" "$here/probe.py" "$@"
