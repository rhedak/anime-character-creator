"""Colour fixtures for `ts/test/colorutil.test.ts`: every colour the presets use, plus edge and random colours,
run through every function of colorutil.py with several arguments. Writes `ts/fixtures/colors.json`.

    PY harness/ts_port/colors.py
"""

from __future__ import annotations

import dataclasses
import json
import random
import struct
from pathlib import Path

import _bootstrap  # noqa: F401

from anime_character_creator import NEUTRAL_BASES, PRESETS  # noqa: E402
from anime_character_creator import colorutil as cu  # noqa: E402

_bootstrap.assert_package_location()
OUT = Path(__file__).resolve().parents[2] / "ts" / "fixtures" / "colors.json"


def hexes_in(obj: object, found: set[str]) -> None:
    if isinstance(obj, dict):
        for v in obj.values():
            hexes_in(v, found)
    elif isinstance(obj, str) and obj.startswith("#") and len(obj) == 7:
        found.add(obj)


def main() -> None:
    found: set[str] = set()
    for p in [*PRESETS.values(), *NEUTRAL_BASES.values()]:
        hexes_in(dataclasses.asdict(p), found)
    colours = sorted(found)
    rng = random.Random(7)
    colours += ["#000000", "#ffffff", "#808080", "#ff0000", "#00ff00", "#0000ff", "#fe00ff", "#fffa00", "#FFAA00", "##ff0000", "ff8800"]
    colours += ["#%02x%02x%02x" % (rng.randrange(256), rng.randrange(256), rng.randrange(256)) for _ in range(1500)]
    # pinkish and magenta colours are where colorsys' negative hue modulo bites
    colours += ["#%02x%02x%02x" % (255, rng.randrange(0, 80), rng.randrange(150, 256)) for _ in range(300)]
    bad = ["#abc", "#12", "", "#gg0000", "#12345"]
    rows = []
    for c in [*colours, *bad]:
        row: dict = {"c": c}
        calls = {
            "shade": lambda c=c: cu.shade(c),
            "shade62": lambda c=c: cu.shade(c, 0.62),
            "shade_b13": lambda c=c: cu.shade(c, 0.87, saturation_boost=1.3),
            "tint": lambda c=c: cu.tint(c),
            "tint25": lambda c=c: cu.tint(c, 0.25),
            "lit06": lambda c=c: cu.lit_tone(c, 0.06),
            "lit12": lambda c=c: cu.lit_tone(c, 0.12),
            "lit38": lambda c=c: cu.lit_tone(c, 0.38),
            "lit_big": lambda c=c: cu.lit_tone(c, 0.9),
            "rise": lambda c=c: cu.highlight_rise(c),
            "soft_g05": lambda c=c: cu.soft_shadow_tone(c, 0.5),
            "soft_g1": lambda c=c: cu.soft_shadow_tone(c, 1.0),
            "soft_g2": lambda c=c: cu.soft_shadow_tone(c, 2.0),
        }
        for k, fn in calls.items():
            try:
                v = fn()
                row[k] = v if isinstance(v, str) else "f:" + struct.pack(">d", v).hex()
            except Exception as e:
                row[k] = {"err": type(e).__name__}
        rows.append(row)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rows, separators=(",", ":")))
    print(OUT, OUT.stat().st_size, len(rows), "colours")


if __name__ == "__main__":
    main()
