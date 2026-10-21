"""Where our adult eyes sit against Risa's reference: the iris blobs, and the dark lid and lash ink, in reference pixels.

    ./harness/run.sh harness/risa_adult/eye_metrics.py ['{"face":{"eye_size":1.0}}']

Renders Risa (harness/risa_adult/risa.ts) with a pure green iris, rasterises it at the reference's scale and maps it to the reference's pixels the
way compare_head.py does (head height 352 px, centre line 668.2, chin 434), then measures the same things in both images:
  iris   the green blob of each eye: centre, width, height (the lid hides the top of it, in the reference and in ours alike)
  ink    the extent of the dark lid and lash pixels (lightness under 60, not hair-red) in each eye's box: left, right, top, bottom
A number to bring near, not a verdict: the look is judged against the overlay (compare_head.py).
"""

import json
import subprocess
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

over = sys.argv[1] if len(sys.argv) > 1 else "{}"
o = json.loads(over)
o.setdefault("eye_color", "#00ff00")
subprocess.run(["node", "harness/risa_adult/risa.ts", "out/risa_adult/metrics.svg", json.dumps(o)], check=True, stderr=subprocess.DEVNULL)
meta = json.load(open("out/franzi/al-meta.json"))
H_REF, CX_REF, CHIN_REF = 352.0, 668.2, 434.0
scale = H_REF / (2 * meta["head_r"])
subprocess.run([sys.executable, "harness/svg2png.py", "out/risa_adult/metrics.svg", "out/risa_adult/metrics.png", "--scale", f"{scale:.5f}"], check=True)
im = Image.open("out/risa_adult/metrics.png").convert("RGBA")
bg = Image.new("RGBA", im.size, "white")
bg.alpha_composite(im)
ours_full = np.array(bg.convert("RGB")).astype(int)
ox = (meta["canvas_w"] / 2) * scale - CX_REF
oy = meta["chin_y"] * scale - CHIN_REF
W, Hh = 1312, 700
ours = np.full((Hh, W, 3), 255, int)
for y in range(Hh):
    sy = round(oy + y)
    if 0 <= sy < ours_full.shape[0]:
        xs0 = round(ox)
        lo, hi = max(0, -xs0), min(W, ours_full.shape[1] - xs0)
        ours[y, lo:hi] = ours_full[sy, xs0 + lo : xs0 + hi]
ref = np.array(Image.open("ref/risa-adult/00-bikini.png").convert("RGB")).astype(int)[:Hh]

BOXES = {"left": (570, 280, 650, 350), "right": (690, 280, 780, 350)}


def stats(a, name):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    green = (g > r + 8) & (g > b + 8)
    lum = a.mean(2)
    ink = (lum < 60) & ~((r - g) > 25)  # dark but not hair-red
    for side, (x0, y0, x1, y1) in BOXES.items():
        m = np.zeros_like(green)
        m[y0:y1, x0:x1] = green[y0:y1, x0:x1]
        lab, n = ndimage.label(m, structure=np.ones((3, 3)))
        if n:
            sizes = ndimage.sum(m, lab, range(1, n + 1))
            m = lab == (1 + int(np.argmax(sizes)))
        ys, xs = np.nonzero(m)
        k = np.zeros_like(ink)
        k[y0:y1, x0:x1] = ink[y0:y1, x0:x1]
        ky, kx = np.nonzero(k)
        print(f"{name:5s} {side:5s} iris centre ({xs.mean():6.1f}, {ys.mean():6.1f}) w {xs.max() - xs.min() + 1:3d} h {ys.max() - ys.min() + 1:3d} | ink x {kx.min()}..{kx.max()} y {ky.min()}..{ky.max()}")


stats(ref, "ref")
stats(ours, "ours")
