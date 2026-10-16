"""Highlight strength on pale and vivid hair, for picking a default by eye.

    ./harness/run.sh harness/soft_hair/strength.py --seed 61

Writes `out/soft/strength-<seed>/sheet-app.png` and `sheet-zoom.png`: Risa in five hair colours (rows),
each at five strengths (columns A to E), the letter-to-strength mapping drawn once and the same on every
row so the answers compare across colours, and `key.json` (not to be opened before choosing).
"""

from __future__ import annotations

import argparse
import io
import json
import random
import re
import sys
from dataclasses import replace
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw

sys.path.insert(0, "src")
from anime_character_creator import PRESETS, render_character  # noqa: E402

COLOURS = {"blonde": "#e8b84b", "pink": "#e56a9c", "orange": "#b5602b", "light brown": "#a9763f", "red": None}
STRENGTHS = [1.0, 0.75, 0.5, 0.25, 0.0]
VIEWS = {"app": ("55 0 290 330", (352, 400)), "zoom": ("120 5 160 170", (336, 357))}


def draw(hair: str | None, strength: float, view: str) -> Image.Image:
    p = replace(PRESETS["risa"], finish="soft", highlight_strength=strength)
    if hair:
        p = replace(p, hair_color=hair)
    box, (w, h) = VIEWS[view]
    svg = render_character(p)
    svg = re.sub(r'viewBox="[^"]+"', f'viewBox="{box}"', svg, count=1)
    svg = re.sub(r'width="400" height="\d+"', f'width="{w}" height="{h}"', svg, count=1)
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), background_color="#2b1a55"))).convert("RGB")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--seed", type=int, default=61)
    ap.add_argument("--out", default="out/soft")
    args = ap.parse_args()
    order = STRENGTHS[:]
    random.Random(f"strength-{args.seed}").shuffle(order)
    out = Path(args.out) / f"strength-{args.seed}"
    out.mkdir(parents=True, exist_ok=True)
    for view in VIEWS:
        w, h = VIEWS[view][1]
        img = Image.new("RGB", (len(order) * (w + 6) - 6, len(COLOURS) * (h + 6) - 6), "white")
        for r, hair in enumerate(COLOURS.values()):
            for c, s in enumerate(order):
                x, y = c * (w + 6), r * (h + 6)
                img.paste(draw(hair, s, view), (x, y))
                if r == 0:
                    ImageDraw.Draw(img).text((x + 8, y + 6), "ABCDE"[c], fill="white")
            ImageDraw.Draw(img).text((8, r * (h + 6) + 20), str(r + 1), fill="white")
        img.save(out / f"sheet-{view}.png")
    (out / "key.json").write_text(
        json.dumps({"columns": {"ABCDE"[i]: s for i, s in enumerate(order)}, "rows": {str(i + 1): n for i, n in enumerate(COLOURS)}}, indent=1)
    )
    print("wrote", out)


if __name__ == "__main__":
    main()
