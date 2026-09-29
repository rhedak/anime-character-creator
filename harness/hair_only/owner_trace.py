"""The owner's own trace of the reference's front lock and back hair (2026-09-29).

The owner drew, on a screenshot of `katherina_grok_real`, the front lock in
red (one strand on each side, from near the top of the head down to the chest,
its two edges) and the darker back hair behind the neck in cyan. This reads
those marks out of the screenshot and puts them in the reference's own pixels
by registering the screenshot to the reference (a scale and a shift, found by
correlating gradient images), so they can be measured in head radii.

Writes `out/hair_only/owner_trace.json` (the registration, the red and cyan
marks in the reference's pixels) and `out/hair_only/owner_trace.png` (the
marks over the reference, to check they land where the owner drew them).
"""

import json

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.signal import fftconvolve

SHOT = "/Users/henrik/Desktop/Screenshot 2026-09-29 at 23.30.38.png"
REF = "ref-local/katherina_grok_real/katherina_grok_real.png"
OUT = "out/hair_only"


def marks(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    red = (r > 190) & (g < 100) & (b < 100)
    cyan = (b > 170) & (g > 130) & (r < 130)
    return red, cyan


def grad(gray):
    gx, gy = ndi.sobel(gray, axis=1), ndi.sobel(gray, axis=0)
    return np.hypot(gx, gy)


def ncc_peak(big, small):
    """Best zero-mean normalised cross-correlation of `small` inside `big`."""
    s = small - small.mean()
    n = np.sqrt((s**2).sum())
    win = np.ones_like(small)
    num = fftconvolve(big, s[::-1, ::-1], mode="valid")
    sq = fftconvolve(big**2, win[::-1, ::-1], mode="valid")
    sm = fftconvolve(big, win[::-1, ::-1], mode="valid")
    var = np.maximum(sq - sm**2 / small.size, 1e-9)
    score = num / (np.sqrt(var) * n)
    y, x = np.unravel_index(np.argmax(score), score.shape)
    return float(score[y, x]), int(x), int(y)


def main() -> None:
    shot = Image.open(SHOT).convert("RGB")
    a = np.asarray(shot).astype(float)
    red, cyan = marks(a)
    ann = ndi.binary_dilation(red | cyan, iterations=3)
    gray = a @ np.array([0.299, 0.587, 0.114])
    # The marks are not in the reference: each takes its nearest unmarked
    # pixel's value before the two are correlated.
    near = ndi.distance_transform_edt(ann, return_distances=False, return_indices=True)
    gray = gray[near[0], near[1]]

    ref = Image.open(REF).convert("RGB")
    rg = np.asarray(ref).astype(float) @ np.array([0.299, 0.587, 0.114])
    G = grad(rg)
    best = (-1, None)
    for s in np.arange(1.6, 3.4, 0.1):
        w, h = int(shot.width / s), int(shot.height / s)
        t = grad(np.asarray(Image.fromarray(np.uint8(gray)).resize((w, h), Image.LANCZOS)).astype(float))
        if w >= G.shape[1] or h >= G.shape[0]:
            continue
        sc, x, y = ncc_peak(G, t)
        if sc > best[0]:
            best = (sc, (s, x, y))
    print("coarse", best)
    s0 = best[1][0]
    for s in np.arange(s0 - 0.1, s0 + 0.1, 0.01):
        w, h = int(round(shot.width / s)), int(round(shot.height / s))
        t = grad(np.asarray(Image.fromarray(np.uint8(gray)).resize((w, h), Image.LANCZOS)).astype(float))
        sc, x, y = ncc_peak(G, t)
        if sc > best[0]:
            best = (sc, (s, x, y))
    score, (s, x, y) = best
    print(f"registration: shot pixel / {s:.3f} + ({x}, {y}) in the reference, score {score:.3f}")

    def to_ref(mask):
        ys, xs = np.nonzero(mask)
        return [[float(px / s + x), float(py / s + y)] for px, py in zip(xs, ys)]

    json.dump(
        {"scale": float(s), "offset": [x, y], "score": score, "red": to_ref(red), "cyan": to_ref(cyan)},
        open(f"{OUT}/owner_trace.json", "w"),
    )
    # Check: the marks over the reference.
    view = np.asarray(ref).copy()
    for key, col in (("red", (255, 40, 40)), ("cyan", (40, 220, 255))):
        for px, py in json.load(open(f"{OUT}/owner_trace.json"))[key]:
            view[int(py), int(px)] = col
    x0, y0 = x, y
    Image.fromarray(view).crop((x0, y0, x0 + int(shot.width / s), y0 + int(shot.height / s))).resize((shot.width, shot.height)).save(f"{OUT}/owner_trace.png")
    print(f"{OUT}/owner_trace.png")


if __name__ == "__main__":
    main()
