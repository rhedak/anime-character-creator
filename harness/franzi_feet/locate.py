"""Find where each of Grok's cut-out segments of the feet close-up sits in the close-up (masked template match).

    ./harness/run.sh harness/franzi_feet/locate.py

`ref/franzi/hands/segments/feet-front/` holds the ten toes and the lower legs as small cropped PNGs, not full-canvas layers like the
full-body segments, so their offsets into `ref/franzi/hands/feet-front.png` (1008 x 1792, the source pixel grid) have to be found. Each
segment is slid over the close-up and scored by the mean squared colour difference over its own opaque pixels (a masked SSD done with
FFT convolutions), and the best offset is kept. A segment is accepted when the score is near zero (the cut-out is a crop of the same
pixels). Writes out/franzi_feet/offsets.json: {name: [x, y, score]} and out/franzi_feet/layers.npz with every segment as a full-canvas
boolean mask, `toe_1`..`toe_10`, `lower_1`..`lower_3`, `left_foot`, `right_foot`.
"""

import glob
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.signal import fftconvolve

OUT = Path("out/franzi_feet")
OUT.mkdir(parents=True, exist_ok=True)
BASE = "ref/franzi/hands/segments/feet-front/"
img = np.array(Image.open("ref/franzi/hands/feet-front.png").convert("RGBA")).astype(float)
# match on colour where the close-up is opaque; the segments were cut from the same pixels
I = img[..., :3]
H, W = I.shape[:2]


def locate(path):
    seg = np.array(Image.open(path).convert("RGBA")).astype(float)
    m = (seg[..., 3] > 200).astype(float)
    T = seg[..., :3]
    th, tw = m.shape
    npx = m.sum()
    # score(y, x) = sum m * (I - T)^2 over the template window, via correlation (flip the template for fftconvolve)
    s_ii = sum(fftconvolve(I[..., c] ** 2, m[::-1, ::-1], mode="valid") for c in range(3))
    s_it = sum(fftconvolve(I[..., c], (m * T[..., c])[::-1, ::-1], mode="valid") for c in range(3))
    s_tt = float((m[..., None] * T**2).sum())
    score = (s_ii - 2 * s_it + s_tt) / (3 * npx)
    y, x = np.unravel_index(int(np.argmin(score)), score.shape)
    return int(x), int(y), float(score[y, x]), m > 0


layers, offsets = {}, {}
names = [("left_foot", BASE + "left-foot.png"), ("right_foot", BASE + "right-foot.png")]
names += [(f"lower_{i}", BASE + f"lower-legs/lower-legs-{i}.png") for i in (1, 2, 3)]
names += [(f"toe_{i}", BASE + f"toes/toes-{i}.png") for i in range(1, 11)]
for name, path in names:
    x, y, score, mask = locate(path)
    full = np.zeros((H, W), bool)
    h, w = mask.shape
    full[y : y + h, x : x + w] = mask
    layers[name] = full
    offsets[name] = [x, y, round(score, 2)]
    ys, xs = np.nonzero(full)
    print(f"{name:11s} at x {x:4d} y {y:4d}  rms {score ** 0.5:6.2f}  bbox x {xs.min()}..{xs.max()}  y {ys.min()}..{ys.max()}")
json.dump(offsets, open(OUT / "offsets.json", "w"))
np.savez_compressed(OUT / "layers.npz", **layers)
