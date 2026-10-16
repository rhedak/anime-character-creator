"""The soft finish on a list of presets, without and with the clumps, side by side.

    ./harness/run.sh harness/soft_hair/cast.py satoko linnea kyoko
    ./harness/run.sh harness/soft_hair/cast.py --cut long_traced          every preset on that cut
    ./harness/run.sh harness/soft_hair/cast.py --cut long_traced --face   the head zoomed instead

Writes `out/soft/cast-<tag>.png`: a row per preset, left the soft finish with the clumps taken out of
the cut, right as the package draws it. For looking while authoring a cut, not for judging.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
from dataclasses import replace
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw

sys.path.insert(0, "src")
from anime_character_creator import HAIRSTYLES, PRESETS, render_character  # noqa: E402

VIEWS = {"app": ("55 0 290 330", (352, 400)), "face": ("120 5 160 170", (400, 425))}
GROUND = "#2b1a55"


def draw(name: str, view: str, locks: bool) -> Image.Image:
    p = replace(PRESETS[name], finish="soft")
    style = HAIRSTYLES[p.hairstyle]
    if not locks:
        HAIRSTYLES[p.hairstyle] = replace(style, locks=None)
    try:
        svg = render_character(p)
    finally:
        HAIRSTYLES[p.hairstyle] = style
    box, (w, h) = VIEWS[view]
    svg = re.sub(r'viewBox="[^"]+"', f'viewBox="{box}"', svg, count=1)
    svg = re.sub(r'width="400" height="\d+"', f'width="{w}" height="{h}"', svg, count=1)
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), background_color=GROUND))).convert("RGB")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("presets", nargs="*", choices=[[], *sorted(PRESETS)][1:] or None)
    ap.add_argument("--cut", help="every preset on this hairstyle")
    ap.add_argument("--face", action="store_true")
    ap.add_argument("--out", default="out/soft")
    args = ap.parse_args()
    names = list(args.presets)
    if args.cut:
        names += [n for n in sorted(PRESETS) if PRESETS[n].hairstyle == args.cut]
    view = "face" if args.face else "app"
    w, h = VIEWS[view][1]
    cols = 2
    per_row = 2 if view == "app" else 1  # presets per row of the sheet
    rows = -(-len(names) // per_row)
    sheet = Image.new("RGB", (per_row * (cols * w + 10) + 0, rows * (h + 6)), "white")
    for i, name in enumerate(names):
        x0 = (i % per_row) * (cols * w + 10)
        y = (i // per_row) * (h + 6)
        sheet.paste(draw(name, view, False), (x0, y))
        sheet.paste(draw(name, view, True), (x0 + w, y))
        ImageDraw.Draw(sheet).text((x0 + 8, y + 6), name, fill="white")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    tag = args.cut or "-".join(names)
    sheet.save(out / f"cast-{tag}{'-face' if args.face else ''}.png")
    print("wrote", out / f"cast-{tag}{'-face' if args.face else ''}.png")


if __name__ == "__main__":
    main()
