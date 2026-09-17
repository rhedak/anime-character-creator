"""Trace the witch hat's regions off the full reference, in head radii.

Calibration (measured this pass, calib.py): our face widest half-width and
chin against the reference's give 173.7 px per head radius on both axes,
head centre at (650, 481) in katherina_grok.jpg.
"""

import json
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

sys.path.insert(0, "/Users/henrik/git/anime-character-creator/.claude/skills/trace-reference")
import trace_lib as tl  # noqa: E402

REF = "/Users/henrik/git/time_slider_katherina/style-anchors/katherina_grok/katherina_grok.jpg"
OUT = "out/trace_hat"
OX, OY, SCALE = 650.0, 481.0, 173.7
HALF_STROKE = 3

rgb = np.asarray(Image.open(REF).convert("RGB")).astype(int)
lab, _ = ndi.label(rgb.sum(2) > 60)


def comp_at(x, y):
    v = lab[y, x]
    assert v, (x, y)
    return lab == v


crown = comp_at(640, 120)
band = comp_at(600, 245)
brim_top = comp_at(700, 300)
under_l = comp_at(380, 360)
under_r = comp_at(960, 450)
buckle = [comp_at(775, 270), comp_at(803, 283), comp_at(826, 295)]
assert not (buckle[0] & buckle[1]).any()

disk = ndi.generate_binary_structure(2, 1)


def grow(m, n):
    return ndi.binary_dilation(m, structure=disk, iterations=n)


def close(m, n):
    return ndi.binary_fill_holes(ndi.binary_erosion(grow(m, n), structure=disk, iterations=n))


everything = crown | band | brim_top | under_l | under_r | buckle[0] | buckle[1] | buckle[2]
front = crown | band | brim_top | buckle[0] | buckle[1] | buckle[2]


def hull(m):
    """Filled convex hull of a mask, by half-plane tests on its hull vertices."""
    from scipy.spatial import ConvexHull

    ys, xs = np.nonzero(m)
    pts = np.column_stack([xs, ys])
    h = ConvexHull(pts)
    yy, xx = np.mgrid[0 : m.shape[0], 0 : m.shape[1]]
    inside = np.ones(m.shape, bool)
    for a, b, c in h.equations:
        inside &= a * xx + b * yy + c <= 0.5
    return inside


regions = {
    # The underside, drawn behind the hair: the whole silhouette plus the hull
    # of the two visible underside patches, which carries the brim's hidden
    # back rim across behind the head, so wherever our hair is narrower than
    # the reference's the underside shows instead of the page.
    "back": grow(close(everything | hull(under_l | under_r), 8), HALF_STROKE),
    # The brim's top surface with the crown, band and bow: the front layer.
    "brim": grow(close(front, 8), HALF_STROKE),
    "crown": grow(close(crown, 2), HALF_STROKE),
    "band": grow(close(band, 2), HALF_STROKE),
    "buckle0": grow(close(buckle[0], 2), HALF_STROKE),
    "buckle1": grow(close(buckle[1], 2), HALF_STROKE),
    "buckle2": grow(close(buckle[2], 2), HALF_STROKE),
}

TOL = {"back": 0.018, "brim": 0.018, "crown": 0.018, "band": 0.015}
result = {}
over = Image.open(REF).convert("RGB")
over = Image.fromarray(np.clip(np.asarray(over).astype(float) * 3.5, 0, 255).astype("uint8"))
d = ImageDraw.Draw(over)
colors = ["#00ff66", "#ff3355", "#33aaff", "#ffee00", "#ff00ff", "#00ffff", "#ffffff", "#ff8800"]
for (name, m), col in zip(regions.items(), colors, strict=False):
    pts_px = tl.boundary(m)
    pts = [((x - OX) / SCALE, (y - OY) / SCALE) for x, y in pts_px]
    start, segs = tl.fit_closed(pts, TOL.get(name, 0.012))
    result[name] = {"start": start, "segs": segs, "n_raw": len(pts)}
    # draw the fitted chain back on the reference
    poly = tl.sample_chain(start, segs, 12)
    d.line([(OX + x * SCALE, OY + y * SCALE) for x, y in poly], fill=col, width=2)
    print(name, "raw", len(pts), "segments", len(segs))
over.crop((250, 0, 1100, 700)).save(f"{OUT}/trace_overlay.png")
json.dump(result, open(f"{OUT}/hat_trace.json", "w"), indent=1)


# Interior crease strokes: ink inside the crown's filled hull that is not part
# of its boundary outline.
hull = ndi.binary_fill_holes(close(crown, 12))
inner = ndi.binary_erosion(hull, structure=disk, iterations=7)
ink = (rgb.sum(2) <= 60) & inner
clab, cn = ndi.label(ink, structure=np.ones((3, 3)))
creases = []
for i in range(1, cn + 1):
    ys, xs = np.nonzero(clab == i)
    if len(xs) < 25:
        continue
    pts = np.column_stack([xs, ys]).astype(float)
    mu = pts.mean(0)
    u = np.linalg.svd(pts - mu, full_matrices=False)[2][0]
    t = (pts - mu) @ u
    order = np.argsort(t)
    # centre line: average the stroke's pixels in bins along its main axis
    bins = np.array_split(order, 6)
    cl = [pts[b].mean(0) for b in bins if len(b)]
    a, b = pts[order[0]], pts[order[-1]]
    cl = [a, *cl, b]
    hr = [((x - OX) / SCALE, (y - OY) / SCALE) for x, y in cl]
    start, segs = tl.fit_chain(hr, [0, len(hr) // 2, len(hr) - 1])
    creases.append({"start": start, "segs": segs, "px": len(xs)})
    print("crease", len(xs), "px", [round(v, 3) for v in start], segs)
    d.line([(OX + x * SCALE, OY + y * SCALE) for x, y in tl.sample_chain(start, segs)], fill="#ff0000", width=2)
result["creases"] = creases
over.crop((600, 60, 900, 260)).resize((600, 400)).save(f"{OUT}/crease_overlay.png")
json.dump(result, open(f"{OUT}/hat_trace.json", "w"), indent=1)
