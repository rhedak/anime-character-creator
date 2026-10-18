"""Trace the bikini top of ref 04 (the segment layer white-bikini-top.png) into a chain for ts/src/body-adult-top-data.ts.

    ./harness/run.sh harness/franzi/top_trace.py

Coordinates are the body's own: depth d in head heights below the chin (row 434 of the reference canvas is d = 0, a head
height is 352 px) and x in head heights from the body's centre line (column 668.2), so `place()` in body-adult-parts.ts maps
them onto the skeleton exactly as it does the body outline. The mask is eroded 3 px so the traced line sits on the centre
of our stroke, and the straps are left as the reference ends them, at the shoulder line (the drawing clips the top to the body's outline). Made symmetric from the right half. Writes out/franzi/top.json and ts/src/body-adult-top-data.ts and prints the extents.
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, "/Users/henrik/git/anime-character-creator/.claude/skills/trace-reference")
import trace_lib as tl  # noqa: E402

OUT = Path("out/franzi")
CX, CHIN, H = 668.2, 434.0, 352.0
mask = np.array(Image.open("ref/franzi/segments/04-bikini-fullbody/white-bikini-top.png"))[..., 3] > 128
img = Image.fromarray((mask * 255).astype(np.uint8))
dr = ImageDraw.Draw(img)
ys, xs = np.where(mask)
top_rows = ys < ys.min() + 6
# No extension of the straps: in the reference they end where they reach the shoulder line at the neck's base and pass behind the
# neck, so the traced tips are kept as they are and the drawing clips the top to the body's outline (ts/src/body-adult-parts.ts).
mask = np.array(img) > 128
mask = ndimage.binary_erosion(ndimage.binary_fill_holes(mask), iterations=3)
# the straps come out too thin once the stroke takes its share: grow what lies above the cups back by 2 px
yy = np.mgrid[0 : mask.shape[0], 0 : mask.shape[1]][0]
straps = mask & (yy < CHIN + 0.5 * H)
mask = mask | ndimage.binary_dilation(straps, iterations=2)
np.save(OUT / "top_mask.npy", mask)
# Symmetric: the right half of the mask (columns right of the centre) joined to its mirror image.
c = int(round(CX))
sym = np.zeros_like(mask)
right = mask[:, c:]
sym[:, c:] = right
sym[:, c - right.shape[1] + 1 : c + 1] |= right[:, ::-1]
# the mask's edge is jagged: smooth it before fitting. A lower threshold than 0.5 keeps the convex corners (the cups' lower outer
# corners) from being rounded off by the blur: at 3.0 and 0.5 the hem came out 0.04 H narrower than the reference's.
sym = ndimage.gaussian_filter(sym.astype(float), 2.5) > 0.42
# The owner's note: the top's lower edge must be as wide as the body there, as in the reference, where the hem runs out to the
# arm line. The layer's own lower corners are rounded and a little narrow, so reach the hem out to the body's side (0.405 H)
# over its last tenth of a head height, easing in so no corner appears.
for y in range(int(CHIN + 0.86 * H), int(CHIN + 1.0 * H)):
    row = np.where(sym[y])[0]
    if len(row) == 0:
        continue
    t = min(1.0, max(0.0, ((y - CHIN) / H - 0.86) / 0.12))
    reach = int(round(0.03 * H * t * t * (3 - 2 * t)))
    lo, hi = row.min(), row.max()
    target_lo, target_hi = int(round(CX - 0.405 * H)), int(round(CX + 0.405 * H))
    sym[y, max(target_lo, lo - reach) : lo] = True
    sym[y, hi + 1 : min(target_hi, hi + reach) + 1] = True
pts = [((x - CX) / H, (y - CHIN) / H) for x, y in tl.boundary(sym)]  # (x in H, d in H)
# The V where the cups meet. The reference's edges are straight lines (half-gap 0.237 H at 0.585 H down, falling 0.68 H per H to 0.040 H at 0.875 H) and
# end in a short flat base (0.07 H wide, at 0.885 H down) with sharp corners. The mask is blurred before tracing and the fit rounds the corner, which gave a
# smooth round bottom (the owner: "a badly curved line" where the reference has a \_/). The points of the V below 0.69 H are replaced here by that geometry,
# so the fit sees two straight edges and a flat base.
V_TOP_D, V_BASE_D, V_BASE_HALF, V_SLOPE = 0.69, 0.885, 0.036, 0.68
inside = [i for i, (x, d) in enumerate(pts) if V_TOP_D < d < 0.905 and abs(x) < 0.17]
assert inside and inside == list(range(inside[0], inside[-1] + 1)), "the V's points are not one run of the boundary"
first, last = pts[inside[0]], pts[inside[-1]]
half_top = lambda d: V_BASE_HALF + V_SLOPE * (V_BASE_D - d) * 0.97  # the edge's half-gap at depth d
row = []
for d in np.linspace(V_TOP_D, V_BASE_D - 0.004, 24):
    row.append((half_top(d), d))
v_left = [(-x, d) for x, d in row]            # down the left edge (x negative)
v_right = [(x, d) for x, d in reversed(row)]  # up the right edge
base = [(-V_BASE_HALF, V_BASE_D), (V_BASE_HALF, V_BASE_D)]
path = v_left + base + v_right
if first[0] > 0:  # the boundary walks the right side first
    path = path[::-1]
pts = pts[: inside[0]] + path + pts[inside[-1] + 1 :]
start, segs = tl.fit_closed(pts, 0.004)
full = pts
xs_ = [p[0] for p in full]; ds_ = [p[1] for p in full]
print("top extent x", round(min(xs_), 3), round(max(xs_), 3), "d", round(min(ds_), 3), round(max(ds_), 3), "segments", len(segs))
json.dump({"top": (start, segs)}, open(OUT / "top.json", "w"), default=lambda o: list(o))


def pt(p):
    return f"[{p[0]:.4f}, {p[1]:.4f}]"


body = ", ".join(f"[{pt(c)}, {pt(e)}]" for c, e in segs)
Path("ts/src/body-adult-top-data.ts").write_text(
    "// Generated by harness/franzi/top_trace.py from the bikini-top layer of ref 04. Do not edit by hand.\n"
    "// Points are [x, d]: x in head heights from the body's centre line, d in head heights below the chin; the outline is\n"
    "// symmetric. The shape is the bust as the cloth shows it, with the two halter straps running up to the sides of the neck.\n\n"
    'import type { Chain } from "./tables.ts";\n\n'
    f"export const ADULT_TOP: Chain = [{pt(start)}, [{body}]];\n"
)
print("wrote ts/src/body-adult-top-data.ts")
