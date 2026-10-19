"""Our hair outline and strand lines drawn in colour on the reference head. ./harness/run.sh harness/franzi_hair/overlay_lines.py

The chains are in head radii in the reference's own calibration (trace.py), so they are drawn at (660 + x*175.7, 270.5 + y*175.7)
with no resampling. Red: the dome's outline. Blue: the left lock. Green: the right curtain and ponytail. Magenta: strand lines. Orange: the hairline, the face skin's upper edge.
"""

import json
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, "/Users/henrik/git/anime-character-creator/.claude/skills/trace-reference")
import trace_lib as tl

OX, OY, S = 660.0, 270.5, 175.7
Z = 2
BOX = (440, 60, 900, 560)
pcs = json.load(open("out/franzi_hair/pieces.json"))
strands = json.load(open("out/franzi_hair/strands.json"))
im = Image.open("ref/franzi/04-bikini-fullbody.png").convert("RGBA")
bg = Image.new("RGBA", im.size, "white")
bg.alpha_composite(im)
img = bg.convert("RGB").crop(BOX).resize(((BOX[2] - BOX[0]) * Z, (BOX[3] - BOX[1]) * Z), Image.LANCZOS)
d = ImageDraw.Draw(img)


def px(p):
    return ((OX + p[0] * S - BOX[0]) * Z, (OY + p[1] * S - BOX[1]) * Z)


for key, col in (("dome", (230, 0, 0)), ("left", (0, 90, 255)), ("tail", (0, 170, 60))):
    st, sg = pcs[key]
    pts = [px(p) for p in tl.sample_chain(tuple(st), [(tuple(c), tuple(e)) for c, e in sg], 10)]
    d.line(pts + [pts[0]], fill=col, width=3)
for ln in strands:
    d.line([px(p) for p in ln], fill=(255, 0, 220), width=3)
# the hairline: the top edge of the face skin (the face chain, ADULT_FACE), from the left temple over the forehead to the right
face = json.load(open("out/franzi_hair/face.json"))["face"]
fr = tl.sample_chain(tuple(face[0]), [(tuple(c), tuple(e)) for c, e in face[1]], 10)
# the face chain also holds the eye holes (closed over the eyes): keep the forehead arc and the sides, not the eyes
keep = [p for p in fr if p[1] < 0.02 or (abs(p[0]) > 0.58 and p[1] < 0.75)]
for q in keep:
    x, y = px(q)
    d.ellipse((x - 1.5, y - 1.5, x + 1.5, y + 1.5), fill=(255, 150, 0))
img.save("out/franzi/hair-lines-on-reference.png")
print("wrote out/franzi/hair-lines-on-reference.png")
