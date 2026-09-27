"""D1 of `docs/detail-plan.md`: the line-weight change, before and after.

Reads two `harness/tall_chibi/snapshot.py` runs and writes to `out/detail/`:

- `d1_before_after.png`: four presets dressed, whole figure, before above
  after;
- `d1_joins.png`: 4x zooms on the places where a fill is tucked under a line
  by an offset that still reads the old weight (the arm's joint cap, the bust
  over the arms, the belt, the bare foot's ankle patch, the base layer's top),
  before beside after, to show no gap or overhang opened when the line
  thinned.

    ./harness/run.sh harness/detail/d1_look.py out/detail/d1_before out/detail/d1_after
"""

import io
import sys

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/detail"
FIGURES = ("satoko", "krista", "keiko", "satoshi")
# (snapshot case, preset, what, box in head radii about (head_cx, anchor y))
JOINS = (
    ("krista.dressed", "krista", "shoulder, bust over arm", "shoulder_y", (-2.0, 0.0, -0.4, 1.4)),
    ("krista.tunic_off", "krista", "base layer: bust, arm", "shoulder_y", (-2.0, 0.0, -0.4, 1.4)),
    ("krista.dressed", "krista", "belt and hand", "waist_y", (-1.4, -0.4, 0.2, 0.8)),
    ("satoshi.dressed", "satoshi", "belt, trousers", "waist_y", (-1.2, -0.4, 0.4, 0.8)),
    ("krista.barefoot", "krista", "bare foot", "ankle_y", (-0.8, -0.4, 0.1, 0.5)),
    ("keiko.dressed", "keiko", "coat at the arm", "shoulder_y", (-1.4, -0.2, 0.0, 1.2)),
)


def png(path: str, scale: float) -> Image.Image:
    svg = open(path).read()
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=scale))).convert("RGBA")
    white = Image.new("RGBA", im.size, (255, 255, 255, 255))
    return Image.alpha_composite(white, im).convert("RGB")


def tag(im: Image.Image, text: str) -> Image.Image:
    ImageDraw.Draw(im).text((3, 3), text, fill=(200, 0, 0))
    return im


def main() -> None:
    before, after = sys.argv[1], sys.argv[2]
    rows = []
    for d, label in ((before, "before"), (after, "after")):
        rows.append([tag(png(f"{d}/{n}.dressed.svg", 1.2), f"{n} {label}") for n in FIGURES])
    w, h = rows[0][0].size
    sheet = Image.new("RGB", (len(FIGURES) * (w + 4), 2 * (h + 4)), (200, 200, 200))
    for j, r in enumerate(rows):
        for i, t in enumerate(r):
            sheet.paste(t, (i * (w + 4), j * (h + 4)))
    sheet.save(f"{OUT}/d1_before_after.png")

    tiles = []
    K = 4
    for case, preset, what, anchor, (x0, y0, x1, y1) in JOINS:
        p = PRESETS[preset]
        sk = c.skeleton_for(p)
        r, cx, ay = sk.head_r * K, sk.head_cx * K, getattr(sk, anchor) * K
        box = (int(cx + x0 * r), int(ay + y0 * r), int(cx + x1 * r), int(ay + y1 * r))
        pair = [tag(png(f"{d}/{case}.svg", K).crop(box), f"{what} {lab}") for d, lab in ((before, "before"), (after, "after"))]
        both = Image.new("RGB", (pair[0].width * 2 + 4, pair[0].height), (200, 200, 200))
        both.paste(pair[0], (0, 0))
        both.paste(pair[1], (pair[0].width + 4, 0))
        tiles.append(both)
    tw = max(t.width for t in tiles)
    th = max(t.height for t in tiles)
    cols = 2
    sheet = Image.new("RGB", (cols * (tw + 6), ((len(tiles) + 1) // cols) * (th + 6)), (160, 160, 160))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * (tw + 6), (i // cols) * (th + 6)))
    sheet.save(f"{OUT}/d1_joins.png")
    print(f"{OUT}/d1_before_after.png {OUT}/d1_joins.png")


if __name__ == "__main__":
    main()
