"""Draw the traced hand on the (flipped) close-up, to check it against the reference.

    ./harness/run.sh harness/franzi_hands/view.py [X0 Y0 X1 Y1] [ZOOM]

Box in flipped close-up px (default: the hand from the wrist down). Left: the flipped close-up with a 50 px grid. Right: the same with the outline
drawn as the band the render's stroke covers (two half strokes wide, centred on the chain, which is inset by one half stroke from the skin's edge,
so the band's outer edge should lie on the skin's edge), the lines in red and the nails in blue when traced (out/franzi_hands/lines.json).
Reads out/franzi_hands/hand.json and mapping.json. Writes out/franzi/hand-view.png.
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, ".claude/skills/trace-reference")
import trace_lib as tl  # noqa: E402

OUT = Path("out/franzi_hands")
H, CX, CHIN = 352.0, 668.2, 434.0
HS_H = 0.008
M = json.load(open(OUT / "mapping.json"))
s, dx, dy = M["s"], M["dx"], M["dy"]
F = json.load(open(OUT / "hand.json"))
args = [a for a in sys.argv[1:]]
if len(args) >= 4:
    box, Z = tuple(map(int, args[:4])), int(args[4]) if len(args) > 4 else 2
else:
    box, Z = (250, 0, 880, 1600), (int(args[0]) if args else 1)


def to_cc(v, d):
    return ((CX - v * H - dx) / s, (CHIN + d * H - dy) / s)


im = Image.open("ref/franzi/hands/relaxed.png").convert("RGBA").transpose(Image.FLIP_LEFT_RIGHT)
bg = Image.new("RGBA", im.size, "white")
bg.alpha_composite(im)
base = bg.convert("RGB").crop(box)
base = base.resize((base.width * Z, base.height * Z), Image.LANCZOS)
grid, drawn = base.copy(), base.copy()
gd, dd = ImageDraw.Draw(grid), ImageDraw.Draw(drawn, "RGBA")
for x in range((box[0] // 50 + 1) * 50, box[2], 50):
    gd.line([((x - box[0]) * Z, 0), ((x - box[0]) * Z, grid.height)], fill=(70, 120, 255), width=1)
    gd.text(((x - box[0]) * Z + 2, 2), str(x), fill=(200, 0, 120))
for y in range((box[1] // 50 + 1) * 50, box[3], 50):
    gd.line([(0, (y - box[1]) * Z), (grid.width, (y - box[1]) * Z)], fill=(70, 120, 255), width=1)
    gd.text((2, (y - box[1]) * Z + 2), str(y), fill=(200, 0, 120))


def px(p):
    return ((p[0] - box[0]) * Z, (p[1] - box[1]) * Z)


start, segs = F["chain"]
pts = tl.sample_chain(tuple(start), [(tuple(c), tuple(e)) for c, e in segs], 10)
line = [px(to_cc(v, d)) for v, d in pts]
band = 2 * HS_H * H / s * Z
dd.line(line, fill=(0, 0, 0, 110), width=max(2, int(band)), joint="curve")
dd.line(line, fill=(255, 0, 160, 255), width=1)
lp = OUT / "lines.json"
if lp.exists():
    L = json.load(open(lp))
    for kind, col in (("lines", (230, 0, 0, 255)), ("nails", (0, 90, 255, 255)), ("cavity", (255, 160, 0, 255))):
        for ch in L.get(kind, []):
            st, sg = ch
            q = tl.sample_chain(tuple(st), [(tuple(c), tuple(e)) for c, e in sg], 8)
            dd.line([px(to_cc(v, d)) for v, d in q], fill=col, width=2)
sheet = Image.new("RGB", (base.width * 2 + 16, base.height), "white")
sheet.paste(grid, (0, 0))
sheet.paste(drawn, (base.width + 16, 0))
sheet.save("out/franzi/hand-view.png")
print("wrote out/franzi/hand-view.png", sheet.size)
