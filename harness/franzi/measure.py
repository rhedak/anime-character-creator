"""Row-by-row silhouette widths of the Franzi references, in head heights (H) below the chin.

The first step of the adult-body campaign: read the numbers off the references before any shape is drawn, and write
the fused target (refs 1-3 down to the mid-thigh crop, ref 4 below) that every later gate measures against.

    ./harness/run.sh harness/franzi/measure.py

Writes out/franzi/measurements.json, out/franzi/target.png and prints the width table.
"""

import json
from pathlib import Path

import numpy as np
from PIL import Image

REF = Path("ref/franzi")
OUT = Path("out/franzi")
OUT.mkdir(parents=True, exist_ok=True)
CROP = 1504  # refs 1-3 end here (mid-thigh)
# Head height (top of hair to chin) in px on the common canvas, from ref/franzi/README.md; ref 4 is scaled 1.365.
H = {"01-swimsuit": 352, "03-bodice": 350, "04-bikini-fullbody": 256 * 1.365}


def mask(name):
    return np.array(Image.open(REF / f"{name}.png"))[..., 3] > 128


def runs(row):
    d = np.diff(np.concatenate([[0], row.astype(int), [0]]))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


def profile(m, top, h, step=0.1, lo=0.0, hi=6.4):
    """For each depth d (in H below the chin): body-run left/right/width/centre in H, and the run count."""
    out = []
    for i in range(int(lo / step), int(hi / step) + 1):
        d = i * step
        y = int(round(top + h * (1 + d)))
        if y >= m.shape[0] or not m[y].any():
            break
        r = runs(m[y])
        # With the arms free of the torso the middle run is the body; merged, the single run is body plus arms.
        body = r[len(r) // 2] if len(r) >= 3 else max(r, key=lambda a: a[1] - a[0])
        out.append({"d": round(d, 2), "runs": len(r), "w": round((body[1] - body[0]) / h, 3),
                    "outer": round((r[-1][1] - r[0][0]) / h, 3), "cx": round(((body[0] + body[1]) / 2) / h, 3)})
    return out


result = {}
for name, h in H.items():
    m = mask(name)
    ys = np.where(m.any(1))[0]
    top = ys.min()
    result[name] = {"head_top_px": int(top), "H_px": h, "rows": profile(m, top, h)}

# Fused target: refs 1-3 down to the crop, ref 4 below, ref 4's legs widened to meet ref 1 at the seam.
a, b = mask("01-swimsuit"), mask("04-bikini-fullbody")
target = np.zeros_like(a)
target[:CROP] = a[:CROP]
target[CROP:] = b[CROP:]
# Ref 4's thighs are about 17% narrower than ref 1's at the crop (README caveat). Widen each leg about its own
# centre by the seam ratio, easing to nothing over one head height, so the legs meet at the seam and keep ref 4's
# length, knee and ankle below.
ra, rb = runs(a[CROP - 1]), runs(b[CROP - 1])
seam_ratio = float(np.mean([(x1 - x0) / (y1 - y0) for (x0, x1), (y0, y1) in zip(ra, rb)]))
EASE = H["04-bikini-fullbody"]
for y in range(CROP, target.shape[0]):
    k = max(0.0, 1.0 - (y - CROP) / EASE)
    f = 1.0 + (seam_ratio - 1.0) * k
    if f <= 1.0005 or not b[y].any():
        continue
    target[y] = False
    for x0, x1 in runs(b[y]):
        c, hw = (x0 + x1) / 2, (x1 - x0) / 2 * f
        target[y, int(round(c - hw)) : int(round(c + hw))] = True
Image.fromarray((target * 255).astype(np.uint8)).save(OUT / "target.png")
seam_a = runs(a[CROP - 1])
seam_b = runs(b[CROP - 1])
result["seam"] = {"leg_width_ratio_ref1_over_ref4": round(seam_ratio, 3), "row": CROP - 1, "ref1_runs": [[int(x), int(y)] for x, y in seam_a],
                  "ref4_runs": [[int(x), int(y)] for x, y in seam_b]}
(OUT / "measurements.json").write_text(json.dumps(result, indent=1))

print("depth(H below chin) | ref1 body w, outer | ref3 body w | ref4 body w, outer")
by = {n: {r["d"]: r for r in result[n]["rows"]} for n in H}
for i in range(0, 65):
    d = round(i * 0.1, 2)
    cells = []
    for n in H:
        r = by[n].get(d)
        cells.append(f"{r['w']:.2f} ({r['runs']}r) {r['outer']:.2f}" if r else "   -   ")
    print(f"{d:4.1f} | " + " | ".join(cells))
print("seam", result["seam"])
