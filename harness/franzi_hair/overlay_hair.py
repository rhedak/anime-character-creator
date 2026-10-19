"""Our hair outline and hairlines drawn in high-contrast colours on the reference's head, nothing else added.

    PYTHONPATH=.claude/skills/trace-reference ./harness/run.sh harness/franzi_hair/overlay_hair.py [ZOOM]

Reads the chains the render is built from (out/franzi_hair/pieces.json, face.json, strands.json; run face_trace.py, pieces.py and
strands.py --emit first) and draws them in head radii at the reference's own calibration (trace.py), so there is no resampling.

    cyan     the dome's outline (the hair on the skull)
    lime     the left lock and the right curtain with the ponytail, only where the render strokes them (below the temples; above
             that the dome draws the outline, and the pieces' own box edges are hidden under the hair)
    magenta  the hairline: the face skin's top edge, down both sides to the eye band
    white    the strand lines inside the hair

Writes out/franzi/hair-overlay-reference.png (the reference alone on the left of it for comparison) and prints its size.
"""

import json
import sys

from PIL import Image, ImageDraw

import trace_lib as tl

OX, OY, S = 660.0, 270.5, 175.7
Z = int(sys.argv[1]) if len(sys.argv) > 1 else 3
BOX = (440, 60, 900, 560)
STROKE_FROM_Y = -0.05  # the render strokes the free pieces only below this many radii under the head centre
W = max(2, Z)

pcs = json.load(open("out/franzi_hair/pieces.json"))
strands = json.load(open("out/franzi_hair/strands.json"))
face = json.load(open("out/franzi_hair/face.json"))["face"]

VARIANT = sys.argv[2] if len(sys.argv) > 2 else ""  # A, B or C: a contrast variant of contrast.py as the base instead of the plain reference
if VARIANT:
    bg = Image.open(f"out/franzi/contrast-{VARIANT}.png").convert("RGB")
else:
    im = Image.open("ref/franzi/04-bikini-fullbody.png").convert("RGBA")
    bg = Image.new("RGBA", im.size, "white")
    bg.alpha_composite(im)
    bg = bg.convert("RGB")
base = bg.crop(BOX).resize(((BOX[2] - BOX[0]) * Z, (BOX[3] - BOX[1]) * Z), Image.LANCZOS)
img = base.copy()
d = ImageDraw.Draw(img)


def px(p):
    return ((OX + p[0] * S - BOX[0]) * Z, (OY + p[1] * S - BOX[1]) * Z)


def chain_pts(ch, n=12):
    st, sg = ch
    return tl.sample_chain(tuple(st), [(tuple(c), tuple(e)) for c, e in sg], n)


def runs(pts, keep):
    """Consecutive points that satisfy `keep`, as separate polylines (a closed chain wraps, so join the first and last run)."""
    out, cur = [], []
    for p in pts:
        if keep(p):
            cur.append(p)
        elif cur:
            out.append(cur)
            cur = []
    if cur:
        if out and keep(pts[0]):
            out[0] = cur + out[0]
        else:
            out.append(cur)
    return out


CYAN, LIME, MAGENTA, WHITE = (0, 235, 255), (80, 255, 0), (255, 0, 230), (255, 255, 255)
if VARIANT:  # on a mid-grey base white strands vanish: use a saturated red, which the reference's own black and grey lines cannot be
    WHITE = (255, 20, 20)

dome = chain_pts(pcs["dome"])
d.line([px(p) for p in dome + [dome[0]]], fill=CYAN, width=W)
for key in ("left", "tail"):
    for r in runs(chain_pts(pcs[key]), lambda p: p[1] > STROKE_FROM_Y):
        d.line([px(p) for p in r], fill=LIME, width=W)
# the hairline: the face chain from the eye band on one side over the forehead to the eye band on the other; its jaw is left off
for r in runs(chain_pts(face), lambda p: p[1] < 0.55):
    if len(r) > 3:
        d.line([px(p) for p in r], fill=MAGENTA, width=W + 1)
for ln in strands:
    d.line([px(p) for p in ln], fill=WHITE, width=max(1, Z - 1))

gap = 16
sheet = Image.new("RGB", (base.width * 2 + gap, base.height), "white")
sheet.paste(base, (0, 0))
sheet.paste(img, (base.width + gap, 0))
tag = f"-{VARIANT}" if VARIANT else ""
sheet.save(f"out/franzi/hair-overlay-reference{tag}.png")
img.save(f"out/franzi/hair-overlay-only{tag}.png")
print(f"wrote out/franzi/hair-overlay-reference{tag}.png", sheet.size, f"and hair-overlay-only{tag}.png", img.size)
