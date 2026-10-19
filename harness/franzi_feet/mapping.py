"""Fit the feet close-up onto the full-body reference (ref 04), foot by foot.

    ./harness/run.sh harness/franzi_feet/mapping.py

The close-up (1008 x 1792, ref/franzi/hands/feet-front.png) is about 3.5 times larger than the feet in the full-body reference (a foot is
about 100 px wide there) and is not registered to it, and its two feet stand closer together than the body's. Each foot is therefore
fitted on its own to the body's matching foot, over the rows from just above the ankle to the sole (rows 2050 to 2335 of ref 04): scale
s, and the offsets (dx, dy), chosen to maximise the overlap (intersection over union) of the two silhouettes. The body's feet are rough
(an AI image, 100 px tall), so the fit is judged by the number it reaches and by how it looks, and the ankle row and the sole row are
reported too, since those are what the body's legs and the sole of the body outline have to meet.

Writes out/franzi_feet/mapping.json: {"A": {...}, "B": {...}} (A is the foot on the viewer's left, which is the right_foot segment).
"""

import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

OUT = Path("out/franzi_feet")
c = np.array(Image.open("ref/franzi/hands/feet-front.png").convert("RGBA"))[..., 3] > 128
f = np.array(Image.open("ref/franzi/04-bikini-fullbody.png").convert("RGBA"))[..., 3] > 128
Y0, Y1 = 2050, 2336

# the body's feet: the legs below the knee, left and right of the centre line (668.2)
f_left, f_right = f.copy(), f.copy()
f_left[:, 668:] = False
f_right[:, :669] = False
# the close-up's feet: foot A on the viewer's left (x under 530), foot B on the right (x over 540)
c_a, c_b = c.copy(), c.copy()
c_a[:, 530:] = False
c_b[:, :540] = False


def place(mask, s, dx, dy):
    """The close-up mask scaled by s about the origin, then shifted by (dx, dy), on the full-body canvas, as a float field."""
    m = ndimage.affine_transform(mask.astype(float), [1 / s, 1 / s], offset=[-dy / s, -dx / s], output_shape=f.shape, order=1)
    return m


def iou(a, b):
    a, b = a[Y0:Y1] > 0.5, b[Y0:Y1] > 0.5
    return float((a & b).sum() / max(1, (a | b).sum()))


res = {}
for name, cm, fm in (("A", c_a, f_left), ("B", c_b, f_right)):
    best = (0, None)
    ys, xs = np.nonzero(fm[Y0:Y1])
    target_cx = xs.mean()
    cys, cxs = np.nonzero(cm[560:1500])
    for s in np.arange(0.250, 0.340, 0.004):
        # centre the close-up foot's centroid (ankle to toes rows) on the body foot's centroid, then refine
        mcx = cxs.mean() * s
        for dx in np.arange(target_cx - mcx - 8, target_cx - mcx + 8, 1.0):
            for dy in np.arange(2329 - 1499 * s - 8, 2329 - 1499 * s + 8, 1.0):
                v = iou(place(cm, s, dx, dy), fm)
                if v > best[0]:
                    best = (v, (float(s), float(dx), float(dy)))
    # refine
    v0, (s0, dx0, dy0) = best
    for s in np.arange(s0 - 0.004, s0 + 0.0041, 0.001):
        for dx in np.arange(dx0 - 2, dx0 + 2.01, 0.5):
            for dy in np.arange(dy0 - 2, dy0 + 2.01, 0.5):
                v = iou(place(cm, s, dx, dy), fm)
                if v > best[0]:
                    best = (v, (float(s), float(dx), float(dy)))
    v, (s, dx, dy) = best
    pm = place(cm, s, dx, dy) > 0.5
    rows = np.nonzero(pm.any(1))[0]
    res[name] = {"iou": round(v, 4), "s": round(s, 4), "dx": round(dx, 2), "dy": round(dy, 2), "bottom": int(rows.max())}
    print(name, res[name])
json.dump(res, open(OUT / "mapping.json", "w"))
