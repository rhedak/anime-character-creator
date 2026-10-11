"""Trace Risa's ribbon (`docs/risa-plan.md`, M6).

`segments/blue-ribbon.png` is a true crop and the whole bow. Drawn the way an
illustrator would build it, as five overlapping pieces, so that their outlines are
the fold lines and no interior line work has to be traced at all (the skill's
"shape decomposition follows drawing order"): the **two tails** first, hanging
apart; the **two loops** over their tops, each a rounded teardrop whose bottom
crosses a tail; the **knot** last, over both loops. A first pass traced the
silhouette and the fold network as strokes instead, and the network, thick and
branching, came out as fragments.

Each piece is a region of the bow's blue between its black outlines, grown by half
the stroke so its boundary is the stroke's centre line, where the neighbouring
pieces' boundaries meet. The two **slits** inside the loops are white in the
reference, with the shirt behind them: holes in the loops' fills, so whatever is
under the bow shows through. The one-pixel highlight tick on the left tail is
texture and is left out.

Cut coordinates are head radii on `tall_slender`, x from the collar's centre line
(`AXIS_X`, so the bow and the wings it is tied under share one axis).

    ./harness/run.sh harness/risa/trace_ribbon.py
"""

import json
import sys

import numpy as np
from common import CY, R, median_colour, segment
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

sys.path.insert(0, ".claude/skills/trace-reference")
import trace_lib as T  # noqa: E402

AXIS_X = 630.5  # the collar's centre line (`trace_collar.py`)
GROW = 2  # half the stroke
TOL = 0.008

m, rgb = segment("blue-ribbon.png")
total = rgb.sum(2)
blue = ndi.binary_opening((total > 230) & (total <= 560) & m, iterations=1)
lab, n = ndi.label(blue)
regions = []
for i in range(1, n + 1):
    c = lab == i
    if c.sum() < 100:
        continue
    ys, xs = np.nonzero(c)
    regions.append({"mask": c, "size": int(c.sum()), "y0": ys.min(), "y1": ys.max(), "x": xs.mean()})
assert len(regions) == 5, f"expected knot, two loops and two tails, found {len(regions)} pieces"

knot = min(regions, key=lambda r: r["size"])
tails = sorted((r for r in regions if r["y1"] >= 550), key=lambda r: r["x"])
loops = sorted((r for r in regions if r is not knot and all(r is not t for t in tails)), key=lambda r: r["x"])
assert len(tails) == 2 and len(loops) == 2
# Drawing order: the tails, then the loops over them, then the knot over both.
pieces = [("tail left", tails[0]), ("tail right", tails[1]), ("loop left", loops[0]), ("loop right", loops[1]), ("knot", knot)]


def to_cut(p):
    return ((p[0] - AXIS_X) / R, (p[1] - CY) / R)


fills = []
for name, r in pieces:
    grown = ndi.binary_dilation(r["mask"], iterations=GROW)
    chain = T.fit_closed([to_cut(p) for p in T.boundary(grown)], TOL)
    fills.append(chain)
    print(f"{name}: {r['size']} px, {len(chain[1])} segments, colour {median_colour(r['mask'], rgb, 2)}")

# The slits: white pixels, grown to the centre of their black ring.
light = (total > 560) & m
ll, ln = ndi.label(light)
holes = []
for i in range(1, ln + 1):
    c = ll == i
    if c.sum() < 15:
        continue
    ys, xs = np.nonzero(c)
    # Which loop it is in: the loop whose box holds it.
    for k, (name, r) in enumerate(pieces):
        if name.startswith("loop") and r["y0"] <= ys.min() and ys.max() <= r["y1"] and abs(xs.mean() - r["x"]) < 25:
            chain = T.fit_closed([to_cut(p) for p in T.boundary(ndi.binary_dilation(c, iterations=2))], 0.006)
            holes.append((k, chain))
            print(f"slit in {name}: {int(c.sum())} px, {len(chain[1])} segments")
            break

json.dump({"axis_x": AXIS_X, "fills": fills, "holes": holes, "colour": median_colour(m & blue, rgb, 2)}, open("out/risa/ribbon_trace.json", "w"))

ys, xs = np.nonzero(m)
box = (int(xs.min()) - 10, int(ys.min()) - 10, int(xs.max()) + 11, int(ys.max()) + 11)
S = 5
img = Image.fromarray(np.where(m[..., None], rgb, 225).astype("uint8")).crop(box)
img = img.resize((img.width * S, img.height * S), Image.LANCZOS)
d = ImageDraw.Draw(img)
cols = [(255, 0, 80), (255, 140, 0), (0, 170, 255), (0, 200, 90), (200, 0, 255)]
for chain, col in zip(fills, cols):
    q = T.sample_chain(chain[0], chain[1], 14)
    px = [((AXIS_X + x * R - box[0]) * S, (CY + y * R - box[1]) * S) for x, y in q]
    d.line([*px, px[0]], fill=col, width=2)
for _, chain in holes:
    q = T.sample_chain(chain[0], chain[1], 14)
    px = [((AXIS_X + x * R - box[0]) * S, (CY + y * R - box[1]) * S) for x, y in q]
    d.line([*px, px[0]], fill=(255, 255, 0), width=2)
img.save("out/risa/ribbon_trace.png")
print("wrote out/risa/ribbon_trace.json and out/risa/ribbon_trace.png")
