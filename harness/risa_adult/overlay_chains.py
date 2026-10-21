"""The fitted chains (out/risa_adult/outline.json) drawn over the reference, to see how well the traced edges follow it.

    PYTHONPATH=.claude/skills/trace-reference ./harness/run.sh harness/risa_adult/overlay_chains.py x0 y0 x1 y1 [ZOOM] [REF]

cyan the face's edge, lime the hair silhouette's. Calibration as outline_trace.py (origin 660, 270.5, 175.7 px per head radius).
Writes out/risa_adult/chains-view.png.
"""

import json
import sys

from PIL import Image, ImageDraw

import trace_lib as tl

OX, OY, S = 660.0, 270.5, 175.7
x0, y0, x1, y1 = map(int, sys.argv[1:5])
Z = int(sys.argv[5]) if len(sys.argv) > 5 else 3
ref = sys.argv[6] if len(sys.argv) > 6 else "ref/risa-adult/00-bikini.png"
res = json.load(open("out/risa_adult/outline.json"))
img = Image.open(ref).convert("RGB").crop((x0, y0, x1, y1)).resize(((x1 - x0) * Z, (y1 - y0) * Z), Image.LANCZOS)
d = ImageDraw.Draw(img)
for key, col in (("face", (0, 255, 255)), ("sil", (0, 255, 0))):
    for st, sg in res[key]:
        pts = tl.sample_chain(tuple(st), [(tuple(c), tuple(e)) for c, e in sg], 12)
        px = [((OX + p[0] * S - x0) * Z, (OY + p[1] * S - y0) * Z) for p in pts]
        d.line(px + [px[0]], fill=col, width=max(1, Z // 2))
img.save("out/risa_adult/chains-view.png")
print(img.size)
