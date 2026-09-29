"""Where each of `ref-local/katherina_grok_real/segments/`'s cuts sits in the
composite, and whether it is a pixel-exact cut of it.

The segments are cropped, not full-frame. A brute-force match at a quarter of
the resolution, then at full resolution within four pixels, on a sample of
each cut's opaque pixels. A mean colour difference near zero with no pixel
far off means an exact cut (the hair's: 0.6, none over 20); a larger one means
a regenerated layer, which the trace skill says not to take coordinates from.
Writes `out/trace_hair/segments.json`.
"""

import json

import numpy as np
from PIL import Image

REF = "ref-local/katherina_grok_real/katherina_grok_real.png"
DIR = "ref-local/katherina_grok_real/segments"
NAMES = ("purple-hair", "witch-hat", "black-bat", "dark-blue-dress", "yellow-collar", "wooden-staff", "brown-belt")
OUT = "out/trace_hair/segments.json"


def score(ref, s, ys, xs, ox, oy):
    return np.abs(ref[ys + oy, xs + ox] - s[ys, xs, :3]).sum(1).mean()


def locate(ref, s):
    m = s[..., 3] > 250
    ys, xs = np.nonzero(m)
    pick = np.random.default_rng(0).choice(len(ys), min(3000, len(ys)), replace=False)
    ys, xs = ys[pick], xs[pick]
    H, W = m.shape
    best = None
    for oy in range(0, ref.shape[0] - H, 4):
        for ox in range(0, ref.shape[1] - W, 4):
            d = score(ref, s, ys, xs, ox, oy)
            if best is None or d < best[0]:
                best = (d, ox, oy)
    _, bx, by = best
    for oy in range(max(0, by - 4), min(ref.shape[0] - H, by + 5)):
        for ox in range(max(0, bx - 4), min(ref.shape[1] - W, bx + 5)):
            d = score(ref, s, ys, xs, ox, oy)
            if d < best[0]:
                best = (d, ox, oy)
    _, ox, oy = best
    full = np.abs(ref[oy : oy + H, ox : ox + W] - s[..., :3]).sum(2)[m]
    return ox, oy, float(full.mean()), float((full > 20).mean())


def main() -> None:
    ref = np.asarray(Image.open(REF).convert("RGB")).astype(float)
    out = {}
    for n in NAMES:
        s = np.asarray(Image.open(f"{DIR}/{n}.png").convert("RGBA")).astype(float)
        ox, oy, mean, frac = locate(ref, s)
        out[n] = {"at": [ox, oy], "size": [s.shape[1], s.shape[0]], "mean_diff": round(mean, 2), "frac_over_20": round(frac, 4)}
        print(n, out[n])
    json.dump(out, open(OUT, "w"), indent=1)


if __name__ == "__main__":
    main()
