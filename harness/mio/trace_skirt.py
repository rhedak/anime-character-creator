"""Trace Mio's pleated skirt (`docs/mio-plan.md`, M4).

`segments/pleated-skirt.png` is a true crop and is the *visible* skirt: seven
box-pleat faces, six fold lines between them, a stepped hem, and for a top edge
the blazer's hem, arced, with a tab where its front comes to a point. Her skirt
runs on up behind the blazer, so the silhouette is carried upward: the two side
edges are extended along their own slope for `EXTEND` px, and the top rows are
filled across (the tab is the blazer, not a hole in the skirt). That part is
inference and hidden by the blazer in every render; it only has to leave no gap.

The folds are line work, not tone (`docs/mio-plan.md`, decision 6): the
reference alternates two skirt tones across the pleats, which is a shading plane
across a garment. The ink inside the eroded hull is six clean strokes; each is
thinned, walked, smoothed and fitted as an open chain, and its ends are carried
on along their own tangent to meet the silhouette.

Cut coordinates are head radii on `tall_slender`, x from the body's centre line
(`AXIS_X`, the silhouette's own centre), y from the head centre.

    ./harness/run.sh harness/mio/trace_skirt.py
"""

import json
import sys

import numpy as np
from common import CY, R, median_colour, segment, thin, walk
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

sys.path.insert(0, ".claude/skills/trace-reference")
import trace_lib as T  # noqa: E402

# The skirt is carried up behind the blazer to the waist, 3.0 head radii of the 165 px
# skull calibration (`BODY_TYPES["tall_slender"].waist_y`), so it never leaves a gap
# above itself where the blazer is open or the figure is drawn without one.
WAIST_PX = 399 - 1.02 * 165 + 3.0 * 165
FILL_ROWS = 34  # rows from the top across which the blazer's tab is filled over
HALF = 2  # half the stroke, 3 px with its edges (measured on the loafer, same art)
TOL_SILHOUETTE = 0.008
TOL_LINE = 0.010

skirt, rgb = segment("pleated-skirt.png")
ys, xs = np.nonzero(skirt)
top, bottom = ys.min(), ys.max()
print(f"skirt rows {top} to {bottom}, x {xs.min()} to {xs.max()}")

# The silhouette: the alpha, eroded to the stroke's centre line.
sil = ndi.binary_erosion(skirt, iterations=HALF)
sy, sx = np.nonzero(sil)
top = sy.min()
EXTEND = int(top - WAIST_PX)

# The side edges' slopes, measured over rows below the tab, where the skirt's own
# edges are clean.
rows = np.arange(top + FILL_ROWS, top + FILL_ROWS + 40)
left = np.array([np.nonzero(sil[y])[0].min() for y in rows], float)
right = np.array([np.nonzero(sil[y])[0].max() for y in rows], float)
ls, li = np.polyfit(rows, left, 1)
rs, ri = np.polyfit(rows, right, 1)

# Carry the silhouette up to the waist and fill the blazer's tab, from those lines.
# Filling a row across from its own extent is not enough: the segment's topmost
# pixel is the tab's tip, one pixel on its own row, so that row has no extent to
# fill and the carried-up part was joined to the skirt through a one-pixel slit,
# which the contour then traced both sides of and drew as a line across the skirt.
for y in range(top - EXTEND, top + FILL_ROWS):
    a, b = int(round(ls * y + li)), int(round(rs * y + ri))
    sil[y, a : b + 1] = True
    row = np.nonzero(sil[y])[0]
    sil[y, row.min() : row.max() + 1] = True
print(f"carried up {EXTEND} px above row {top}: edge slopes {ls:+.3f} and {rs:+.3f} px per row")

sy, sx = np.nonzero(sil)
AXIS_X = (sx.min() + sx.max()) / 2
print(f"silhouette x {sx.min()} to {sx.max()}, centre {AXIS_X:.1f}")


def to_cut(pt):
    return ((pt[0] - AXIS_X) / R, (pt[1] - CY) / R)


pts = [to_cut(p) for p in T.boundary(sil)]
chain = T.fit_closed(pts, TOL_SILHOUETTE)
print(f"silhouette: {len(chain[1])} segments, colour {median_colour(skirt, rgb, 6)}")

# --- the folds -------------------------------------------------------------------
inner = ndi.binary_erosion(skirt, iterations=4)
dark = (rgb.sum(2) <= 150) & inner
dl, dn = ndi.label(dark, structure=np.ones((3, 3)))
lines = []
for i in range(1, dn + 1):
    m = dl == i
    if m.sum() < 60:
        continue
    path = walk(thin(m))
    p = np.asarray(path, float)
    k = 5
    sm = np.stack([np.convolve(np.pad(p[:, c], k // 2, mode="edge"), np.ones(k) / k, mode="valid") for c in (0, 1)], 1)
    # Carry both ends on along their tangent to the silhouette's edge.
    def tangent(a, b):
        d = a - b
        return d / (np.hypot(*d) or 1)

    t0, t1 = tangent(sm[0], sm[6]), tangent(sm[-1], sm[-7])
    # The end nearer the top is carried on up to the waist, so the folds converge
    # there as stitched-down pleats do; the other end only to the hem's edge.
    up0 = sm[0][1] < sm[-1][1]
    ext0 = [sm[0] + t0 * s for s in range(1, (EXTEND + 6) if up0 else 7)][::-1]
    ext1 = [sm[-1] + t1 * s for s in range(1, 7 if up0 else (EXTEND + 6))]
    full = np.array([*ext0, *sm, *ext1])
    cut_pts = [to_cut((x, y)) for x, y in full]
    marks = T.simplify(cut_pts, TOL_LINE)
    c = T.fit_chain(cut_pts, marks)
    lines.append(c)
    print(f"  fold {len(lines)}: {int(m.sum())} px, {len(c[1])} segments, x {cut_pts[0][0]:+.3f} to {cut_pts[-1][0]:+.3f}")
lines.sort(key=lambda c: c[0][0])

json.dump({"axis_x": AXIS_X, "silhouette": chain, "folds": lines, "colour": median_colour(skirt, rgb, 6)}, open("out/mio/skirt_trace.json", "w"))

# --- back over the reference, 3x --------------------------------------------------
box = (int(sx.min()) - 12, int(top) - 50, int(sx.max()) + 13, int(ys.max()) + 14)
S = 3
img = Image.fromarray(rgb.clip(0, 255).astype("uint8")).convert("RGB")
base = np.where(skirt[..., None], rgb, 255).astype("uint8")
img = Image.fromarray(base).crop(box)
img = img.resize((img.width * S, img.height * S), Image.LANCZOS)
d = ImageDraw.Draw(img)


def draw(c, colour, closed=True):
    q = T.sample_chain(c[0], c[1], 14)
    px = [((AXIS_X + x * R - box[0]) * S, (CY + y * R - box[1]) * S) for x, y in q]
    d.line(px + ([px[0]] if closed else []), fill=colour, width=2)


draw(chain, (255, 0, 80))
for c in lines:
    draw(c, (0, 140, 255), closed=False)
img.save("out/mio/skirt_trace.png")
print("wrote out/mio/skirt_trace.json and out/mio/skirt_trace.png")
