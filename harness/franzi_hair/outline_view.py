"""Draw the outline regions' edges on the plain reference, tile by tile, to check them against it.

    ./harness/run.sh harness/franzi_hair/outline_view.py X0 Y0 X1 Y1 [ZOOM] [masks|chains]

Reference canvas pixels. Writes out/franzi/outline-view.png: the plain reference of the box with a 20 px grid on the left, and the same
with the edges drawn on it on the right. Colours: cyan face, magenta ears, lime hair, yellow hair silhouette (all masks), or with
`chains` the fitted chains in out/franzi_hair/outline.json (what the render will use), in the same colours.
"""

import json
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, ".claude/skills/trace-reference")  # the scripts run from the repo root
import trace_lib as tl  # noqa: E402

OX, OY, S = 660.0, 270.5, 175.7
x0, y0, x1, y1 = map(int, sys.argv[1:5])
Z = int(sys.argv[5]) if len(sys.argv) > 5 else 4
mode = sys.argv[6] if len(sys.argv) > 6 else "masks"

im = Image.open("ref/franzi/04-bikini-fullbody.png").convert("RGBA")
bg = Image.new("RGBA", im.size, "white")
bg.alpha_composite(im)
base = bg.convert("RGB").crop((x0, y0, x1, y1))
base = base.resize((base.width * Z, base.height * Z), Image.LANCZOS)
grid, drawn = base.copy(), base.copy()
gd = ImageDraw.Draw(grid)
for x in range((x0 // 20 + 1) * 20, x1, 20):
    gd.line([((x - x0) * Z, 0), ((x - x0) * Z, grid.height)], fill=(70, 120, 255) if x % 100 else (255, 140, 0), width=1)
    gd.text(((x - x0) * Z + 2, 2), str(x), fill=(200, 0, 120))
for y in range((y0 // 20 + 1) * 20, y1, 20):
    gd.line([(0, (y - y0) * Z), (grid.width, (y - y0) * Z)], fill=(70, 120, 255) if y % 100 else (255, 140, 0), width=1)
    gd.text((2, (y - y0) * Z + 2), str(y), fill=(200, 0, 120))

COL = {"face": (0, 200, 255), "ear_l": (255, 0, 200), "ear_r": (255, 0, 200), "hair": (60, 220, 0), "sil": (255, 200, 0), "strips": (255, 90, 0)}
dd = ImageDraw.Draw(drawn)
if mode == "masks":
    m = np.load("out/franzi_hair/outline_masks.npz")
    arr = np.array(drawn)
    for k in ("hair", "sil", "face", "ear_l", "ear_r", "strips"):
        edge = m[k] & ~ndimage.binary_erosion(m[k])
        e = np.array(Image.fromarray(edge[y0:y1, x0:x1].astype(np.uint8) * 255).resize(drawn.size, Image.NEAREST)) > 0
        arr[e] = COL[k]
    drawn = Image.fromarray(arr)
else:
    ch = json.load(open("out/franzi_hair/outline.json"))
    dd = ImageDraw.Draw(drawn)
    for k, chains in ch.items():
        for st, sg in chains:
            pts = tl.sample_chain(tuple(st), [(tuple(c), tuple(e)) for c, e in sg], 12)
            pts = [((OX + p[0] * S - x0) * Z, (OY + p[1] * S - y0) * Z) for p in pts]
            dd.line(pts + [pts[0]], fill=COL.get(k, (255, 0, 0)), width=2)

sheet = Image.new("RGB", (base.width * 2 + 16, base.height), "white")
sheet.paste(grid, (0, 0))
sheet.paste(drawn, (base.width + 16, 0))
sheet.save("out/franzi/outline-view.png")
print("wrote out/franzi/outline-view.png", sheet.size)
