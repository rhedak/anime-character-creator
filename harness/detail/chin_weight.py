"""The line under the chin: its weight against the face's silhouette.

The owner (2026-09-27): the chin reads as a different weight from the rest of
the face. `_head` draws it at `_interior_w(sw, 0.6)`, which since D1 is 0.44 of
the silhouette's weight (it was 0.60 before D1). Columns: as built (0.44), the
pre-D1 ratio (0.60), 0.8, and full weight (1.0). Rows: Satoshi, Katherina,
Reinhard, Chiyo, at 5x round the jaw, plus the whole heads at 2x. Writes
`out/detail/chin_weight.png`.

The owner picked 0.60 (2026-09-27), now `_outline_w(sw, 0.6)` in `_head`; the
"as built" column shows that from then on.
"""

import io
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

ORIG = c._interior_w
RATIOS = (None, 0.60, 0.8, 1.0)
NAMES = ("satoshi", "katherina", "reinhard", "chiyo")


def main():
    tiles = []
    for name in NAMES:
        p = PRESETS[name]
        row = []
        for ratio in RATIOS:
            if ratio is not None:
                target = c._outline_w(1.0) * ratio

                def iw(sw, k=1.0, _t=target):
                    return sw * _t / 0.6 if k == 0.6 else ORIG(sw, k)

                c._interior_w = iw
            try:
                sk = c.skeleton_for(p)
                svg = c.render_character(p, sk, background="#ffffff")
            finally:
                c._interior_w = ORIG
            big = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=4))).convert("RGB")
            r = sk.head_r * 4
            cx, cy = sk.head_cx * 4, sk.head_cy * 4
            t = big.crop((int(cx - 1.05 * r), int(cy - 0.1 * r), int(cx + 1.05 * r), int(cy + 1.25 * r)))
            ImageDraw.Draw(t).text((4, 4), f"{name} {'as built 0.44' if ratio is None else ratio}", fill=(200, 0, 0))
            row.append(t)
        tiles.append(row)
    w = max(t.width for r in tiles for t in r)
    h = max(t.height for r in tiles for t in r)
    sheet = Image.new("RGB", (len(RATIOS) * (w + 4), len(tiles) * (h + 4)), (190, 190, 190))
    for j, row in enumerate(tiles):
        for i, t in enumerate(row):
            sheet.paste(t, (i * (w + 4), j * (h + 4)))
    sheet.save("out/detail/chin_weight.png")
    print("out/detail/chin_weight.png", sheet.size)


if __name__ == "__main__":
    main()
