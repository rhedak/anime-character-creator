"""Trace Risa's knee sock and loafer (`docs/risa-plan.md`, M3).

Both are traced for the **right** leg (the viewer's right) in the cut frame, head
radii on `tall_slender`, with x measured from that leg's own centre line, the
sock's. A cut drawn per leg (`GarmentCut.per_leg`) mirrors it for the left, and
standing on a leg's centre line rather than at fixed x is what keeps the sock on
the leg whatever the profile's hip width does to the spacing.

The sock is the one component of the dark leg colour below the skirt, grown by
half the outline width so its boundary is the stroke's centre line, and run on
down under the shoe, since the reference hides its lower end there. The loafer is
the segment's own alpha, eroded by half the outline width for the same reason
(the segment includes the outline's outer edge). Its interior is line work: the
ink inside the eroded hull, thinned, walked and fitted as open chains, and the
sole band, the one region of a second tone, as a fill.

Writes `out/risa/feet_trace.json` and `out/risa/feet_trace.png`, the chains drawn
back over the reference at 3x. Always look at that before emitting.

    ./harness/run.sh harness/risa/trace_feet.py
"""

import json
import sys

import numpy as np
from common import (
    CX,
    CY,
    R,
    RGB,
    median_colour,
    segment,
    thin,
    walk,
)
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

sys.path.insert(0, ".claude/skills/trace-reference")
import trace_lib as T  # noqa: E402

TOL_SILHOUETTE = 0.010
TOL_LINE = 0.012

figure, _ = segment("anime-girl.png")

# --- the outline's width, measured, not assumed ----------------------------------
shoe, shoe_rgb = segment("brown-loafers/brown-loafers-2.png")
ys, xs = np.nonzero(shoe)
mid = (ys.min() + ys.max()) // 2
row = np.nonzero(shoe[mid])[0]
ink = (shoe_rgb[mid].sum(1) <= 60) & shoe[mid]
run = 0
for x in range(row.min(), row.max()):
    if ink[x]:
        run += 1
    elif run:
        break
# The black run counts only the darkest pixels; the stroke's antialiased edge adds
# about one on each side, which the overlay showed (the first fit rode the fill's
# edge, not the stroke's centre). So the stroke is the run plus two.
OUTLINE_W = run + 2
HALF = int(round(OUTLINE_W / 2))
print(
    f"outline: {run} px of solid ink at the loafer's mid row, {OUTLINE_W} with its edges, half {HALF}"
)


def to_leg(pt, centre_px):
    """Pixels to the cut frame: x from the leg's centre line, y from the head centre."""
    return ((pt[0] - centre_px) / R, (pt[1] - CY) / R)


# --- the sock ---------------------------------------------------------------------
sock_seed = RGB[1300, 580]
sock = (np.abs(RGB - sock_seed).sum(2) <= 40) & figure
sock[:1100] = False
sock[1380:] = False  # the shoe's top is at 1388; below that the sock is hidden
lab, n = ndi.label(sock)
parts = [(lab == i) for i in range(1, n + 1) if (lab == i).sum() > 300]
right = max(parts, key=lambda m: np.nonzero(m)[1].mean())
sy, sx = np.nonzero(right)
top = sy.min()
centre_px = float(
    np.mean(
        [
            (np.nonzero(right[y])[0].min() + np.nonzero(right[y])[0].max()) / 2
            for y in range(top, top + 12)
        ]
    )
)
print(
    f"sock colour {tuple(sock_seed)}, right sock rows {top} to {sy.max()}, centre x {centre_px:.1f} ({(centre_px - CX) / R:+.3f} from the head's centre line)"
)

# Run it on down under the shoe, which hides the reference's lower end, straight
# down from its last visible row (a tail along the shoe's collar is what the
# colour mask finds if it is allowed further).
bottom = sy.max()
for y in range(bottom + 1, bottom + 41):
    xs_b = np.nonzero(right[bottom])[0]
    right[y, xs_b.min() : xs_b.max() + 1] = True
right = ndi.binary_dilation(right, iterations=HALF)
sock_pts = [to_leg(p, centre_px) for p in T.boundary(right)]
sock_chain = T.fit_closed(sock_pts, TOL_SILHOUETTE)
print(
    f"sock: {len(sock_chain[1])} segments, colour {median_colour(right & ndi.binary_erosion(right, iterations=4))}"
)

# --- the loafer ---------------------------------------------------------------------
sil = ndi.binary_erosion(shoe, iterations=HALF)
shoe_pts = [to_leg(p, centre_px) for p in T.boundary(sil)]
shoe_chain = T.fit_closed(shoe_pts, TOL_SILHOUETTE)
print(f"loafer silhouette: {len(shoe_chain[1])} segments, colour {median_colour(sil, shoe_rgb, 6)}")

inner = ndi.binary_erosion(shoe, iterations=5)
dark = (shoe_rgb.sum(2) <= 90) & inner
dl, dn = ndi.label(dark, structure=np.ones((3, 3)))
lines = []
for i in range(1, dn + 1):
    m = dl == i
    if m.sum() < 25:
        continue
    path = walk(thin(m))
    if len(path) < 8:
        continue
    # Smooth the walk a little (a one-pixel path is stair-stepped), then fit.
    p = np.asarray(path, float)
    k = 5
    sm = np.stack(
        [
            np.convolve(np.pad(p[:, c], k // 2, mode="edge"), np.ones(k) / k, mode="valid")
            for c in (0, 1)
        ],
        1,
    )
    pts = [to_leg((x, y), centre_px) for x, y in sm]
    marks = T.simplify(pts, TOL_LINE)
    chain = T.fit_chain(pts, marks)
    lines.append(chain)
    print(
        f"  line {i}: {m.sum()} px, {len(path)} walked, {len(chain[1])} segments, y {pts[0][1]:+.3f} to {pts[-1][1]:+.3f}"
    )

# The regions between the lines, to find the one that is a second tone.
# Eroded only by 2 here: the sole band is thinner than the ink search's margin.
free = ndi.binary_erosion(shoe, iterations=2) & ~ndi.binary_dilation(
    (shoe_rgb.sum(2) <= 90) & shoe, iterations=1
)
fl, fn = ndi.label(free)
base = median_colour(sil, shoe_rgb, 6)
print(f"regions inside the loafer (base colour {base}):")
regions = []
for i in range(1, fn + 1):
    m = fl == i
    if m.sum() < 150:
        continue
    yy, xx = np.nonzero(m)
    regions.append((i, m, median_colour(m, shoe_rgb, 3), yy.mean()))
    print(
        f"  region {i}: {m.sum()} px, colour {regions[-1][2]}, centroid y {hy_ if (hy_ := (yy.mean() - CY) / R) else 0:+.3f}"
    )

sole = None
if regions:
    i, m, col, _ = max(regions, key=lambda r: r[3])
    grown = ndi.binary_dilation(m, iterations=HALF + 1) & sil
    sole_pts = [to_leg(p, centre_px) for p in T.boundary(grown)]
    sole = T.fit_closed(sole_pts, TOL_SILHOUETTE)
    print(f"sole band: region {i}, colour {col}, {len(sole[1])} segments")

out = {
    "centre_px": centre_px,
    "outline_px": OUTLINE_W,
    "sock": sock_chain,
    "loafer": shoe_chain,
    "loafer_lines": lines,
    "loafer_sole": sole,
    "base_colour": base,
}
json.dump(out, open("out/risa/feet_trace.json", "w"))

# --- draw it back over the reference, 3x ----------------------------------------------
box = (int(centre_px) - 130, 1130, int(centre_px) + 130, 1520)
S = 3
img = Image.fromarray(np.clip(RGB * 1.0, 0, 255).astype("uint8")).crop(box)
img = img.resize((img.width * S, img.height * S), Image.LANCZOS)
d = ImageDraw.Draw(img)


def draw(chain, colour, closed=True, width=2):
    pts = T.sample_chain(chain[0], chain[1], 14)
    px = [((centre_px + x * R - box[0]) * S, (CY + y * R - box[1]) * S) for x, y in pts]
    d.line(px + ([px[0]] if closed else []), fill=colour, width=width)


draw(sock_chain, (255, 0, 80))
draw(shoe_chain, (0, 170, 255))
for ln in lines:
    draw(ln, (255, 200, 0), closed=False)
if sole:
    draw(sole, (0, 220, 120))
img.save("out/risa/feet_trace.png")
print("wrote out/risa/feet_trace.json and out/risa/feet_trace.png")
