"""Emit parts-body's coordinate tables as TypeScript literals, so coordinates are never typed by hand.

    PY harness/ts_port/gen_body_tables.py            writes ts/src/body-parts-tables.ts

The output is a first draft that is then owned by hand: once it is in `ts/src/`, edit it there. Running this again
overwrites the file, so it refuses unless `--force` is given. The tables are the ones `character.py` builds at import:
`_LAB_DRESS_COLUMN`, `KNEE_SOCK_CUT`, `BOOT_CUTS`, and `SKIRT_CUTS` (which Python fills in two places: the literal at
line 6254 and `SKIRT_CUTS["pleated"]` further down).
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

import _bootstrap  # noqa: F401

import anime_character_creator.character as ch  # noqa: E402

_bootstrap.assert_package_location()

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ts" / "src" / "body-parts-tables.ts"

COLUMN = ch._LAB_DRESS_COLUMN


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
    if v is COLUMN:
        return "LAB_DRESS_COLUMN"
    if isinstance(v, (tuple, list)):
        return "[" + ", ".join(lit(x) for x in v) + "]"
    raise TypeError(type(v))


def cut_literal(cut: object) -> str:
    parts = []
    for f in dataclasses.fields(cut):  # type: ignore[arg-type]
        value = getattr(cut, f.name)
        if f.default is not dataclasses.MISSING and value == f.default:
            continue
        parts.append(f"{f.name}: {lit(value)}")
    return "garmentCut({ " + ", ".join(parts) + " })"


def main() -> None:
    if OUT.exists() and "--force" not in sys.argv:
        raise SystemExit(f"{OUT} exists and is hand-owned now; pass --force to overwrite")
    lines = [
        "// Generated once by harness/ts_port/gen_body_tables.py from the Python tables, then owned by hand.",
        "// The traced skirt, sock and foot cuts the body's lower half draws: coordinates in head radii, as the trace tools wrote them.",
        "",
        'import { garmentCut } from "./core-limbs-tables.ts";',
        'import type { GarmentCut } from "./core-limbs-tables.ts";',
        'import type { Chain } from "./tables.ts";',
        "",
    ]
    lines.append("/** Keiko's dress below the belt: a narrow column, not a skirt that flares (`_LAB_DRESS_COLUMN`). */")
    lines.append(f"export const LAB_DRESS_COLUMN: Chain = {chain_lit(COLUMN)};")
    lines.append("")
    lines.append("/** The traced skirt cuts by name (`SKIRT_CUTS`): what an `Outfit.skirt_cut` names. Python adds `pleated` further down the file. */")
    lines.append("export const SKIRT_CUTS: Readonly<Record<string, GarmentCut>> = {")
    for key, cut in ch.SKIRT_CUTS.items():
        lines.append(f"  {key}: {cut_literal(cut)},")
    lines.append("};")
    lines.append("")
    lines.append("/** Risa's knee sock, traced (`KNEE_SOCK_CUT`). */")
    lines.append(f"export const KNEE_SOCK_CUT: GarmentCut = {cut_literal(ch.KNEE_SOCK_CUT)};")
    lines.append("")
    lines.append("/** The traced feet by name (`BOOT_CUTS`): what an `Outfit.boot_cut` names. */")
    lines.append("export const BOOT_CUTS: Readonly<Record<string, GarmentCut>> = {")
    for key, cut in ch.BOOT_CUTS.items():
        lines.append(f"  {key}: {cut_literal(cut)},")
    lines.append("};")
    lines.append("")
    OUT.write_text("\n".join(lines))
    print("wrote", OUT, OUT.stat().st_size, "bytes")


def chain_lit(chain: object) -> str:
    """The column itself, written out in full (inside `lit` its identity stands for the name)."""
    start, segs = chain  # type: ignore[misc]
    return "[" + lit(start) + ", " + lit(segs) + "]"


if __name__ == "__main__":
    main()
