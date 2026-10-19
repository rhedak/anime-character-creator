"""Strand lines for Franzi's hair, drawn by eye over the reference's hair layer and shown for correction.

    ./harness/run.sh harness/franzi_hair/strands.py

The black hair in the composite hides its strand lines, so they are read from the layer with its dark range stretched
(out/franzi_hair/hair-highlights.png): a whorl at the parting, strands fanning from it over the skull, the two curtains of hair
either side of the face, the ponytail. Points are in that image's coordinates (2x, crop origin (480, 60) of the reference
canvas). Writes out/franzi_hair/strands-overlay.png and, with --emit, out/franzi_hair/strands.json (head radii).
"""

import json
import sys

import numpy as np
from PIL import Image, ImageDraw

OX, OY, S = 660.0, 270.5, 175.7
# open chains, each from the whorl or the hairline outward
STRANDS = [
    # the whorl at the parting, strands sweeping left over the skull
    [(415, 98), (340, 84), (265, 104), (200, 152), (142, 232), (102, 332), (76, 432)],
    [(410, 106), (330, 114), (256, 150), (190, 216), (146, 300), (122, 400)],
    [(405, 112), (300, 150), (230, 216), (186, 300), (150, 420)],
    # ... and right
    [(420, 104), (492, 120), (552, 170), (597, 242), (613, 332), (611, 430)],
    [(426, 116), (512, 150), (566, 216), (592, 292)],
    [(440, 126), (520, 182), (562, 252), (572, 330)],
    # the long left lock and its inner edge
    [(255, 262), (196, 332), (162, 440), (152, 560), (166, 680), (200, 820)],
    [(292, 236), (236, 306), (202, 420), (192, 520)],
    # the right curtain
    [(502, 252), (550, 330), (580, 430), (586, 540), (572, 620), (592, 682)],
    # the ponytail
    [(562, 652), (522, 722), (502, 802), (522, 880)],
    [(612, 664), (592, 742), (572, 832), (592, 892)],
    [(652, 722), (662, 792), (676, 852)],
]


def catmull(pts, n=10):
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * ((2 * p[i][j]) + (-p[i - 1][j] + p[i + 1][j]) * t + (2 * p[i - 1][j] - 5 * p[i][j] + 4 * p[i + 1][j] - p[i + 2][j]) * t**2 + (-p[i - 1][j] + 3 * p[i][j] - 3 * p[i + 1][j] + p[i + 2][j]) * t**3) for j in (0, 1)))
    out.append(tuple(pts[-1]))
    return out


def to_r(z):
    return ((480 + z[0] / 2 - OX) / S, (60 + z[1] / 2 - OY) / S)


if __name__ == "__main__":
    # on the contrast-stretched hair, where the strand lines can be seen
    arr = np.array(Image.open("ref/franzi/04-bikini-fullbody.png").convert("RGBA")).astype(float)
    img = Image.fromarray((np.clip((arr[..., :3].mean(2) - 8) / 100, 0, 1) * 255).astype(np.uint8)).convert("RGB").crop((480, 60, 880, 560)).resize((800, 1000), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    for s in STRANDS:
        d.line(catmull(s), fill=(255, 60, 60), width=3)
    img.save("out/franzi_hair/strands-overlay.png")
    if "--emit" in sys.argv:
        json.dump([[list(to_r(p)) for p in catmull(s, 6)] for s in STRANDS], open("out/franzi_hair/strands.json", "w"))
    print("wrote out/franzi_hair/strands-overlay.png")
