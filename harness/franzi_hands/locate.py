"""Find where each of Grok's cut-out segments of the relaxed hand close-up sits in the close-up (masked template match).

    ./harness/run.sh harness/franzi_hands/locate.py

`ref/franzi/hands/segments/relaxed/` holds the hand, the thumb, five finger pieces and four fingernails as small cropped PNGs, not full-canvas
layers, so their offsets into `ref/franzi/hands/relaxed.png` (1008 x 1792, the source pixel grid) are found by sliding each over the close-up and
scoring the mean squared colour difference over its own opaque pixels (a masked SSD with FFT convolutions). Same method as
harness/franzi_feet/locate.py. Writes out/franzi_hands/offsets.json and out/franzi_hands/layers.npz (full-canvas boolean masks: hand, thumb,
finger_1..finger_5, nail_1..nail_4).
"""

import glob
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.signal import fftconvolve

OUT = Path("out/franzi_hands")
OUT.mkdir(parents=True, exist_ok=True)
BASE = "ref/franzi/hands/segments/relaxed/"
img = np.array(Image.open("ref/franzi/hands/relaxed.png").convert("RGBA")).astype(float)
I = img[..., :3]
H, W = I.shape[:2]


def locate(path):
    seg = np.array(Image.open(path).convert("RGBA")).astype(float)
    m = (seg[..., 3] > 200).astype(float)
    T = seg[..., :3]
    npx = m.sum()
    s_ii = sum(fftconvolve(I[..., c] ** 2, m[::-1, ::-1], mode="valid") for c in range(3))
    s_it = sum(fftconvolve(I[..., c], (m * T[..., c])[::-1, ::-1], mode="valid") for c in range(3))
    s_tt = float((m[..., None] * T**2).sum())
    score = np.real((s_ii - 2 * s_it + s_tt) / (3 * npx))
    y, x = np.unravel_index(int(np.argmin(score)), score.shape)
    return int(x), int(y), float(score[y, x]), m > 0


names = [("hand", BASE + "hand.png"), ("thumb", BASE + "thumb.png")]
names += [(f"finger_{i}", BASE + f"fingers/fingers-{i}.png") for i in range(1, 6)]
names += [(f"nail_{i}", BASE + f"fingernails/fingernails-{i}.png") for i in range(1, 5)]
layers, offsets = {}, {}
for name, path in names:
    x, y, score, mask = locate(path)
    full = np.zeros((H, W), bool)
    h, w = mask.shape
    full[y : y + h, x : x + w] = mask
    layers[name] = full
    offsets[name] = [x, y, round(score, 2)]
    ys, xs = np.nonzero(full)
    print(f"{name:9s} at x {x:4d} y {y:4d}  rms {score ** 0.5:6.2f}  bbox x {xs.min()}..{xs.max()}  y {ys.min()}..{ys.max()}")
json.dump(offsets, open(OUT / "offsets.json", "w"))
np.savez_compressed(OUT / "layers.npz", **layers)
