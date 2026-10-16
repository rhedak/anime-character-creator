"""Emit parts-garments' coordinate tables as TypeScript literals, so coordinates are never typed by hand.

    PY harness/ts_port/gen_garments_tables.py            writes ts/src/garments-tables.ts

A first draft that is then owned by hand: once it is in `ts/src/`, edit it there. Running this again overwrites the file, so it
refuses unless `--force` is given.
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

import _bootstrap  # noqa: F401

import anime_character_creator.character as ch  # noqa: E402

_bootstrap.assert_package_location()

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ts" / "src" / "garments-tables.ts"


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
        "// Generated once by harness/ts_port/gen_garments_tables.py from the Python tables, then owned by hand.",
        "// The traced collar, belt, ribbon and hip pocket cuts and the coat's buttons: coordinates in head radii, as the trace tools wrote them.",
        "",
        'import { garmentCut } from "./core-limbs-tables.ts";',
        'import type { GarmentCut } from "./core-limbs-tables.ts";',
        "",
        "/** A traced belt: the strap and its keeper in the belt's colour, then the buckle's frame in the hardware tone and the strap seen through it (`BeltCut`). */",
        "export interface BeltCut {",
        "  readonly strap: GarmentCut;",
        "  readonly frame: GarmentCut;",
        "  readonly through: GarmentCut;",
        "}",
        "",
        "/** Traced collar cuts, drawn by `_collar` when `Outfit.collar_cut` names one (`COLLAR_CUTS`). */",
        "export const COLLAR_CUTS: Readonly<Record<string, GarmentCut>> = {",
    ]
    for key, cut in ch.COLLAR_CUTS.items():
        lines.append(f"  {key}: {cut_literal(cut)},")
    lines += [
        "};",
        "",
        "/** Traced belt cuts, drawn by `_belt_drawn` when `Outfit.belt_cut` names one (`BELT_CUTS`). */",
        "export const BELT_CUTS: Readonly<Record<string, BeltCut>> = {",
    ]
    for key, cut in ch.BELT_CUTS.items():
        lines.append(f"  {key}: {{")
        for name in ("strap", "frame", "through"):
            lines.append(f"    {name}: {cut_literal(getattr(cut, name))},")
        lines.append("  },")
    lines += [
        "};",
        "",
        "/** Risa's ribbon: five overlapping pieces drawn in the order they are tied (`RIBBON_CUT`). */",
        f"export const RIBBON_CUT: GarmentCut = {cut_literal(ch.RIBBON_CUT)};",
        "",
        "/** A flapped hip pocket, one flap a side: the right one traced, the left its mirror (`HIP_POCKET_CUT`). */",
        f"export const HIP_POCKET_CUT: GarmentCut = {cut_literal(ch.HIP_POCKET_CUT)};",
        "",
        "/** The blazer's buttons, as (x, y, radius) in head radii on `tall_slender`: a line of three down the front (`_COAT_BUTTONS`). */",
        f"export const COAT_BUTTONS: readonly (readonly [number, number, number])[] = {lit(ch._COAT_BUTTONS)};",
        "",
    ]
    OUT.write_text("\n".join(lines))
    print("wrote", OUT, OUT.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
