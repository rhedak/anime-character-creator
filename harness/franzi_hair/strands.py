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
    [(410, 100), (480, 108), (540, 140), (590, 205), (608, 300)],
    [(415, 115), (500, 150), (560, 205), (592, 270)],
    [(405, 100), (330, 88), (245, 118), (175, 185), (132, 262)],
    [(398, 115), (305, 122), (232, 172), (182, 245), (152, 330)],
    [(395, 125), (315, 170), (255, 232), (205, 305)],
    [(300, 240), (232, 295), (178, 380), (148, 500), (150, 620)],
    [(255, 305), (195, 405), (152, 520)],
    [(525, 262), (565, 335), (592, 435), (584, 560)],
    [(545, 250), (585, 352), (603, 480), (578, 640)],
    [(595, 615), (562, 705), (545, 800), (552, 860)],
    [(625, 640), (603, 745), (612, 850)],
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
    im = Image.open("ref/franzi/04-bikini-fullbody.png").convert("RGBA")
    bg = Image.new("RGBA", im.size, "white")
    bg.alpha_composite(im)
    img = bg.convert("RGB").crop((480, 60, 880, 560)).resize((800, 1000), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    for s in STRANDS:
        d.line(catmull(s), fill=(255, 60, 60), width=3)
    img.save("out/franzi_hair/strands-overlay.png")
    if "--emit" in sys.argv:
        json.dump([[list(to_r(p)) for p in catmull(s, 6)] for s in STRANDS], open("out/franzi_hair/strands.json", "w"))
    print("wrote out/franzi_hair/strands-overlay.png")
