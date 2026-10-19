"""Fit the relaxed hand close-up onto the full-body reference's hanging hand (ref 04), the viewer's-left one.

    ./harness/run.sh harness/franzi_hands/mapping.py

The close-up is flipped (its thumb is on the left of the image; the viewer's-left hand has its thumb on the inner side, toward the body, which is
the right of the image), scaled and shifted to overlap the reference hand as well as it can, over the rows from just below the wrist to the
fingertips (rows 1166 to 1345 of ref 04): scale s and offset (dx, dy) chosen to maximise the intersection over union of the two silhouettes.
The reference's hand is 180 px long and rough (an AI image), so the fit is judged by the number and by the picture, and the wrist row and
width are reported since the arm's knots have to meet them. The viewer's-right hand is this one mirrored, as the rest of the body is.

Writes out/franzi_hands/mapping.json: {"s", "dx", "dy", "iou", "wrist_cc"} (wrist_cc: the close-up's wrist row, 250, see composite.py).
"""

import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

OUT = Path("out/franzi_hands")
WRIST_CC = 250  # the close-up is cut mid-forearm and has no narrowing; the wrist is where the hand starts to widen (composite.py)
c = np.array(Image.open("ref/franzi/hands/relaxed.png").convert("RGBA"))[..., 3] > 128
cf = c[:, ::-1]  # flipped
W = c.shape[1]
f = np.array(Image.open("ref/franzi/04-bikini-fullbody.png").convert("RGBA"))[..., 3] > 128
arm = np.zeros_like(f)
arm[1090:1350, :462] = f[1090:1350, :462]
lab, _ = ndimage.label(arm)
arm = lab == lab[1200, 420]
Y0, Y1 = 1166, 1346


def place(mask, s, dx, dy):
    return ndimage.affine_transform(mask.astype(float), [1 / s, 1 / s], offset=[-dy / s, -dx / s], output_shape=f.shape, order=1)


def iou(a, b):
    a, b = a[Y0:Y1] > 0.5, b[Y0:Y1]
    return float((a & b).sum() / max(1, (a | b).sum()))


# wrist centre of the flipped close-up at row WRIST_CC, and of the reference at its wrist row 1158
xs = np.nonzero(cf[WRIST_CC])[0]
wc_cc = (xs.min() + xs.max()) / 2
wc_ref = 416.0
best = (0, None)
for s in np.arange(0.120, 0.152, 0.002):
    for dx in np.arange(wc_ref - wc_cc * s - 6, wc_ref - wc_cc * s + 6.1, 1.0):
        for dy in np.arange(1158 - WRIST_CC * s - 6, 1158 - WRIST_CC * s + 6.1, 1.0):
            v = iou(place(cf, s, dx, dy), arm)
            if v > best[0]:
                best = (v, (float(s), float(dx), float(dy)))
v0, (s0, dx0, dy0) = best
for s in np.arange(s0 - 0.002, s0 + 0.0021, 0.0005):
    for dx in np.arange(dx0 - 1.5, dx0 + 1.51, 0.5):
        for dy in np.arange(dy0 - 1.5, dy0 + 1.51, 0.5):
            v = iou(place(cf, s, dx, dy), arm)
            if v > best[0]:
                best = (v, (float(s), float(dx), float(dy)))
v, (s, dx, dy) = best
pm = place(cf, s, dx, dy) > 0.5
rows = np.nonzero(pm.any(1))[0]
print(f"fit: IoU {v:.4f}  scale {s:.4f}  offset ({dx:.1f}, {dy:.1f})  close-up wrist row {WRIST_CC} lands on row {WRIST_CC * s + dy:.1f} (reference wrist 1158)  fingertip row {rows.max()} (reference 1337)")
json.dump({"s": s, "dx": dx, "dy": dy, "iou": v, "wrist_cc": WRIST_CC, "W": W}, open(OUT / "mapping.json", "w"))
