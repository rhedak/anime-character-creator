"""Trace Risa's shirt collar (`docs/risa-plan.md`, M5).

`segments/white-collared-shirt.png` holds four things: the collar's two wings, a
narrow strip of shirt front down the middle, two slivers beside the ribbon, and a
cuff at each wrist. Only the wings are a silhouette question. The strip and the
slivers are what the blazer's lapels and the ribbon happen to leave visible, so
the tunic draws the shirt front and the blazer (M7) decides how much of it shows;
the cuffs belong to the sleeves (M7).

The wings touch at the foot of their V, where the ribbon's knot sits, and are
separate above it, with her neck between them. Their tips already reach to within
a few pixels of the chin, so nothing is carried up: a first pass copied the top row
upward to tuck them behind the jaw, and the top row of a pointed wing is its tip,
one pixel, so that drew a thin spike.

Cut coordinates are head radii on `tall_slender`, x from the collar's own centre
line (`AXIS_X`).

    ./harness/run.sh harness/risa/trace_collar.py
"""

import json
import sys

import numpy as np
from common import CY, R, median_colour, segment
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

sys.path.insert(0, ".claude/skills/trace-reference")
import trace_lib as T  # noqa: E402

# One, not the 2 the rounder shapes take: eroding by the stroke's half cuts a sharp
# tip back along its bisector by much more than 2 px, and the wings are all tips.
HALF = 1
TOL = 0.008

shirt, rgb = segment("white-collared-shirt.png")
lab, n = ndi.label(shirt)
# The collar: the component whose centroid is highest (the front strip and the
# cuffs are all lower).
best = min(range(1, n + 1), key=lambda i: np.nonzero(lab == i)[0].mean() if (lab == i).sum() > 500 else 1e9)
collar = lab == best
ys, xs = np.nonzero(collar)
print(f"collar {int(collar.sum())} px, rows {ys.min()} to {ys.max()}, x {xs.min()} to {xs.max()}")

sil = ndi.binary_erosion(collar, iterations=HALF)
sy, sx = np.nonzero(sil)
AXIS_X = (sx.min() + sx.max()) / 2
print(f"silhouette x {sx.min()} to {sx.max()}, centre {AXIS_X:.1f}, rows {sy.min()} to {sy.max()}")


def to_cut(p):
    return ((p[0] - AXIS_X) / R, (p[1] - CY) / R)


chain = T.fit_closed([to_cut(p) for p in T.boundary(sil)], TOL)
print(f"collar: {len(chain[1])} segments, colour {median_colour(collar, rgb, 4)}")
json.dump({"axis_x": AXIS_X, "collar": chain, "colour": median_colour(collar, rgb, 4)}, open("out/risa/collar_trace.json", "w"))

box = (int(sx.min()) - 20, int(sy.min()) - 20, int(sx.max()) + 21, int(sy.max()) + 30)
S = 4
base = np.where(collar[..., None], rgb, 230).astype("uint8")
img = Image.fromarray(base).crop(box)
img = img.resize((img.width * S, img.height * S), Image.LANCZOS)
d = ImageDraw.Draw(img)
pts = T.sample_chain(chain[0], chain[1], 14)
px = [((AXIS_X + x * R - box[0]) * S, (CY + y * R - box[1]) * S) for x, y in pts]
d.line(px + [px[0]], fill=(255, 0, 80), width=2)
img.save("out/risa/collar_trace.png")
print("wrote out/risa/collar_trace.json and out/risa/collar_trace.png")
