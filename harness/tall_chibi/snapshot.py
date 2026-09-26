"""A broad byte snapshot of the tall chibi, for R3 of `docs/tall-chibi-plan.md`.

`ref-out/` holds only the presets as they are dressed, too narrow a guard for
deleting code. This renders, as SVG text, every preset in four states
(dressed, tunic off, every optional garment off, barefoot), and on the default
character every hairstyle, eye style, expression, body type, traced cut, and a
bust sweep, the belt line both ways, and an arm out. Two runs are compared file
by file with `cmp`; any difference is a leak.

    ./harness/run.sh harness/tall_chibi/snapshot.py out/tall_chibi/before

The compressed chibi (`body=None`) is left out on purpose: R3 retires it.
"""

import dataclasses
import os
import sys
from dataclasses import replace

from anime_character_creator import EYESTYLES
from anime_character_creator import character as c
from anime_character_creator.presets import EXPRESSIONS, NEUTRAL_BASES, PRESETS

KEEP = ("boot_color", "underwear_color")
OPTIONAL = [f.name for f in dataclasses.fields(c.Outfit) if f.name.endswith("_color") and f.name not in KEEP]


def cases() -> dict[str, c.CharacterParams]:
    out: dict[str, c.CharacterParams] = {}
    for name, p in {**PRESETS, **{f"base_{k}": v for k, v in NEUTRAL_BASES.items()}}.items():
        out[f"{name}.dressed"] = p
        out[f"{name}.tunic_off"] = replace(p, outfit=replace(p.outfit, tunic_color=None))
        out[f"{name}.all_off"] = replace(p, outfit=replace(p.outfit, **dict.fromkeys(OPTIONAL)))
        out[f"{name}.barefoot"] = replace(p, outfit=replace(p.outfit, boot_color=None, **dict.fromkeys(OPTIONAL)))
    base = c.CharacterParams()
    for h in sorted(c.HAIRSTYLES):
        out[f"hair.{h}"] = replace(base, hairstyle=h)
    for e in sorted(EYESTYLES):
        out[f"eyes.{e}"] = replace(base, face=replace(base.face, eye_style=e))
    for x in sorted(EXPRESSIONS):
        out[f"expr.{x}"] = EXPRESSIONS[x].applied_to(base)
    for b in sorted(c.BODY_TYPES):
        out[f"body.{b}"] = replace(base, body=b)
    for field, table in (
        ("coat_cut", c.COAT_CUTS),
        ("skirt_cut", c.SKIRT_CUTS),
        ("sleeve_cut", c.SLEEVE_CUTS),
        ("belt_cut", c.BELT_CUTS),
        ("collar_cut", c.COLLAR_CUTS),
    ):
        for cut in sorted(table):
            extra = {"coat_color": "#445566"} if field == "coat_cut" else {}
            extra |= {"belt_color": "#332211"} if field == "belt_cut" else {}
            extra |= {"collar_color": "#998877"} if field == "collar_cut" else {}
            out[f"cut.{field}.{cut}"] = replace(base, outfit=replace(base.outfit, **{field: cut}, **extra))
    for v in (0.01, 0.3, 1.0):
        out[f"bust.{v}"] = replace(base, bust=v)
    for v in (-0.8, 1.2):
        out[f"waist.{v}"] = replace(base, waist_shift=v)
    out["arm.out"] = replace(base, right_arm_out=0.6, left_arm_out=0.3)
    out["coat.parametric"] = replace(base, bust=0.6, outfit=replace(base.outfit, coat_color="#556677"))
    out["robe"] = replace(base, bust=0.6, outfit=replace(base.outfit, robe_color="#aaaaaa"))
    return out


def main() -> None:
    dest = sys.argv[1]
    os.makedirs(dest, exist_ok=True)
    n = 0
    for name, p in cases().items():
        with open(os.path.join(dest, f"{name}.svg"), "w") as f:
            f.write(c.render_character(p))
        n += 1
    print(f"{n} renders to {dest}")


if __name__ == "__main__":
    main()
