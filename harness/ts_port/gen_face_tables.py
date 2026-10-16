"""Emit the parts-face coordinate tables (the ear's traced rim and fold) as TypeScript literals.

    PY harness/ts_port/gen_face_tables.py            writes ts/src/face-tables.ts

A first draft that is then owned by hand, so it refuses to overwrite unless `--force` is given.
"""

from __future__ import annotations

import sys
from pathlib import Path

import _bootstrap  # noqa: F401
import anime_character_creator.character as ch  # noqa: E402
from gen_tables import lit  # noqa: E402

_bootstrap.assert_package_location()

OUT = Path(__file__).resolve().parents[2] / "ts" / "src" / "face-tables.ts"

TABLES = [
    ("EAR_ARC_START", "_EAR_ARC_START", "Point", "The ear's rim, in the ear's own frame: where it leaves the top attach."),
    ("EAR_ARC", "_EAR_ARC", "readonly Segment[]", "The ear's rim: four quadratics, top attach to bottom attach."),
    ("EAR_FOLD_START", "_EAR_FOLD_START", "Point", "The antihelix's start, in the ear's own frame."),
    ("EAR_FOLD", "_EAR_FOLD", "readonly Segment[]", "The antihelix, one question-mark stroke."),
]


def main() -> None:
    if OUT.exists() and "--force" not in sys.argv:
        raise SystemExit(f"{OUT} exists and is hand-owned now; pass --force to overwrite")
    lines = [
        "// Generated once by harness/ts_port/gen_face_tables.py from the Python tables, then owned by hand.",
        "",
        'import type { Point, Segment } from "./tables.ts";',
        "",
    ]
    for ts_name, attr, ty, why in TABLES:
        lines.append(f"/** {why} */")
        lines.append(f"export const {ts_name}: {ty} = {lit(getattr(ch, attr))};")
        lines.append("")
    OUT.write_text("\n".join(lines))
    print("wrote", OUT, OUT.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
