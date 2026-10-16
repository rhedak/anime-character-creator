"""Emit Python data tables as TypeScript literals, so coordinates are never typed by hand.

    PY harness/ts_port/gen_tables.py            writes ts/src/tables.ts

The output is a first draft that is then owned by hand: once a table is in `ts/src/`, edit it there. Running this
again overwrites the file, so it refuses unless `--force` is given. Add a table by naming it in TABLES.
"""

from __future__ import annotations

import sys
from pathlib import Path

import _bootstrap  # noqa: F401

_bootstrap.assert_package_location() if False else None

import anime_character_creator.character as ch  # noqa: E402

_bootstrap.assert_package_location()

OUT = Path(__file__).resolve().parents[2] / "ts" / "src" / "tables.ts"

# name in TS, python attribute, TS type, one line of why
TABLES = [
    ("HAT_UNDERSIDE", "_HAT_UNDERSIDE", "Chain", "The brim's underside, drawn behind the hair."),
    ("HAT_BRIM", "_HAT_BRIM", "Chain", "The brim's top surface with the crown, band and bow."),
]


def lit(v: object) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        r = repr(v)
        return r[:-2] if r.endswith(".0") else r
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if v is None:
        return "null"
    if isinstance(v, (tuple, list)):
        return "[" + ", ".join(lit(x) for x in v) + "]"
    raise TypeError(type(v))


def main() -> None:
    if OUT.exists() and "--force" not in sys.argv:
        raise SystemExit(f"{OUT} exists and is hand-owned now; pass --force to overwrite")
    lines = [
        "// Generated once by harness/ts_port/gen_tables.py from the Python tables, then owned by hand.",
        "",
        "export type Point = readonly [number, number];",
        "export type Segment = readonly [Point, Point];",
        "export type Chain = readonly [Point, readonly Segment[]];",
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
