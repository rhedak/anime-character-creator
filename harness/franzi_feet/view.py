"""Draw the traced foot on the close-up, to check it against the reference.

    ./harness/run.sh harness/franzi_feet/view.py [X0 Y0 X1 Y1] [ZOOM]

Box in close-up px (default: the whole foot, ankle to toes). Left: the close-up with a 50 px grid. Right: the same with the foot outline
drawn as the band the render's stroke covers (2 half-strokes wide, centred on the chain, which is inset by one half stroke from the skin
edge, so the band's outer edge should lie on the skin's edge), the toe dividers in red and the nails in blue (when traced). Reads
out/franzi_feet/foot.json (outline.py) and out/franzi_feet/lines.json (lines.py) if present. Writes out/franzi/foot-view.png.
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, ".claude/skills/trace-reference")
import trace_lib as tl  # noqa: E402

OUT = Path("out/franzi_feet")
H, CX, CHIN = 352.0, 668.2, 434.0
HS_H = 0.008
F = json.load(open(OUT / "foot.json"))
s, dx, dy = F["s"], F["dx"], F["dy"]
args = sys.argv[1:]
box = tuple(map(int, args[:4])) if len(args) >= 4 else (120, 260, 540, 1520)
Z = int(args[4]) if len(args) > 4 else (int(args[0]) if len(args) == 1 else 2)
if len(args) == 1:
    box, Z = (120, 260, 540, 1520), int(args[0])


def to_cc(v, d):
    return ((CX - v * H - dx) / s, (CHIN + d * H - dy) / s)


im = Image.open("ref/franzi/hands/feet-front.png").convert("RGBA")
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
    for kind, col in (("dividers", (230, 0, 0, 255)), ("nails", (0, 90, 255, 255))):
        for ch in L.get(kind, []):
            st, sg = ch
            q = tl.sample_chain(tuple(st), [(tuple(c), tuple(e)) for c, e in sg], 8)
            dd.line([px(to_cc(v, d)) for v, d in q], fill=col, width=2)
sheet = Image.new("RGB", (base.width * 2 + 16, base.height), "white")
sheet.paste(grid, (0, 0))
sheet.paste(drawn, (base.width + 16, 0))
sheet.save("out/franzi/foot-view.png")
print("wrote out/franzi/foot-view.png", sheet.size)
