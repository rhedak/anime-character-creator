"""D3 of `docs/detail-plan.md`: the chibi's moustache, lowered toward the grown
face's. The owner: the chibi beard has always sat a bit high.

At face age 0 the moustache's top edge is `_BEARD_TASH_Y` (0.36 head radii
below the head's centre, where a nose would be). On a grown face it sits
`_BEARD_NOSE_GAP` under the nose (`_nose_y`). Variants at age 0: today's 0.36;
0.40; and the grown face's rule applied at age 0 too (`_nose_y + gap`, about
0.43), which would make it one rule at every age. The three bearded men, faces
at 3x, and each at the smallest insert size (head radius 21 px) beside it.
Writes `out/detail/beard_height.png`.
"""

import io
import os

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/detail"
ORIG = c._BEARD_TASH_Y


def crop(p, scale, box):
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="#ffffff")
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=scale))).convert("RGB")
    r, cx, cy = sk.head_r * scale, sk.head_cx * scale, sk.head_cy * scale
    return im.crop((int(cx + box[0] * r), int(cy + box[1] * r), int(cx + box[2] * r), int(cy + box[3] * r)))


def main():
    os.makedirs(OUT, exist_ok=True)
    sk0 = c.skeleton_for(PRESETS["gero"])
    unified = c._nose_y(sk0) + c._BEARD_NOSE_GAP
    variants = (("today 0.36", ORIG), ("0.40", 0.40), (f"one rule {unified:.3f}", unified))
    rows = []
    try:
        for label, y in variants:
            c._BEARD_TASH_Y = y
            row = []
            for n in ("gero", "daizen", "reinhard"):
                big = crop(PRESETS[n], 3, (-1.0, -0.3, 1.0, 1.4))
                sk = c.skeleton_for(PRESETS[n])
                k = 21.0 / sk.head_r
                small = crop(PRESETS[n], k * 4, (-1.3, -1.3, 1.3, 1.6))
                small = small.resize((small.width // 4, small.height // 4), Image.LANCZOS)
                small = small.resize((small.width * 3, small.height * 3), Image.NEAREST)
                tile = Image.new("RGB", (big.width + small.width + 4, max(big.height, small.height)), (255, 255, 255))
                tile.paste(big, (0, 0))
                tile.paste(small, (big.width + 4, 0))
                ImageDraw.Draw(tile).text((3, 3), f"{n}: {label}", fill=(200, 0, 0))
                row.append(tile)
            rows.append(row)
    finally:
        c._BEARD_TASH_Y = ORIG
    tw = max(t.width for r in rows for t in r)
    th = max(t.height for r in rows for t in r)
    sheet = Image.new("RGB", (3 * (tw + 4), len(rows) * (th + 4)), (190, 190, 190))
    for j, r in enumerate(rows):
        for i, t in enumerate(r):
            sheet.paste(t, (i * (tw + 4), j * (th + 4)))
    sheet.save(f"{OUT}/beard_height.png")
    print(f"{OUT}/beard_height.png", sheet.size, "unified", round(unified, 3))


if __name__ == "__main__":
    main()
