"""The soft finish beside the flat one, for judging by eye.

    ./harness/run.sh harness/soft_finish/pairs.py risa katherina --view face

Writes `out/soft/<view>-<preset>.png`, flat on the left and soft on the right, on a
dark ground like the companion app's stage, and `out/soft/<view>-sheet.png` with
every preset named, flat above soft. Views, as a viewBox of the 400 wide canvas:
`full` the figure, `close` the companion's close-up, `face` the head zoomed.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
from dataclasses import replace
from pathlib import Path

import cairosvg
from PIL import Image

sys.path.insert(0, "src")
from anime_character_creator import PRESETS, render_character  # noqa: E402

VIEWS = {  # name: (x, y, w, h, pixels per unit)
    "full": (0, 0, 400, 500, 1.4),
    "close": (55, 0, 290, 330, 2.0),
    "face": (120, 10, 160, 170, 3.4),
}
GROUND = "#2b1a55"


def draw(name: str, finish: str, view: str) -> Image.Image:
    x, y, w, h, scale = VIEWS[view]
    svg = render_character(replace(PRESETS[name], finish=finish))
    svg = re.sub(r'viewBox="[^"]+"', f'viewBox="{x} {y} {w} {h}"', svg, count=1)
    svg = re.sub(
        r'width="400" height="\d+"', f'width="{int(w * scale)}" height="{int(h * scale)}"', svg, count=1
    )
    png = cairosvg.svg2png(bytestring=svg.encode(), background_color=GROUND)
    return Image.open(io.BytesIO(png)).convert("RGB")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("presets", nargs="*", default=["risa"], choices=sorted(PRESETS))
    ap.add_argument("--view", choices=sorted(VIEWS), default="close")
    ap.add_argument("--out", default="out/soft")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows: list[list[Image.Image]] = [[], []]
    for name in args.presets:
        flat, soft = draw(name, "flat", args.view), draw(name, "soft", args.view)
        rows[0].append(flat)
        rows[1].append(soft)
        pair = Image.new("RGB", (flat.width * 2 + 6, flat.height), "white")
        pair.paste(flat, (0, 0))
        pair.paste(soft, (flat.width + 6, 0))
        pair.save(out / f"{args.view}-{name}.png")
    w, h = rows[0][0].size
    sheet = Image.new("RGB", (w * len(args.presets), h * 2))
    for r, row in enumerate(rows):
        for i, im in enumerate(row):
            sheet.paste(im, (i * w, r * h))
    sheet.save(out / f"{args.view}-sheet.png")
    print(f"wrote {out}/{args.view}-sheet.png and one pair per preset")


if __name__ == "__main__":
    main()
