"""The length of the fringe's locks: our hair's outline over the reference around the forehead, and the lowest hair row in each column of both.

    ./harness/run.sh harness/risa_adult/fringe_length_check.py [ZOOM]

Renders Risa with the hair in a marker colour (as hair_outline_check.py), maps it to the reference's pixels, and draws the boundary of our visible hair in cyan over the
reference's forehead (x 560 to 780, y 150 to 340), with the reference's own fringe boundary (outline_masks.py's `fringe_hair`) in yellow. Then, for every 6th column in the fringe, the
lowest row of hair, from the top of the box down the first run of hair, in the reference and in ours, and the difference (ours minus the reference, positive is longer).
Writes out/risa_adult/fringe-length.png.
"""

import json
import subprocess
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

zoom = int(sys.argv[1]) if len(sys.argv) > 1 else 5
meta = json.load(open("out/franzi/al-meta.json"))
H_REF, CX_REF, CHIN_REF = 352.0, 668.2, 434.0
scale = H_REF / (2 * meta["head_r"])
subprocess.run(["node", "harness/risa_adult/risa.ts", "out/risa_adult/hairmark.svg", json.dumps({"hair_color": "#ff00ff"})], check=True, stderr=subprocess.DEVNULL)
subprocess.run([sys.executable, "harness/svg2png.py", "out/risa_adult/hairmark.svg", "out/risa_adult/hairmark.png", "--scale", f"{scale:.5f}"], check=True, stdout=subprocess.DEVNULL)
a = np.array(Image.open("out/risa_adult/hairmark.png").convert("RGB")).astype(int)
mark = (a[..., 0] > a[..., 1] + 40) & (a[..., 2] > a[..., 1] + 40)
ox = round((meta["canvas_w"] / 2) * scale - CX_REF)
oy = round(meta["chin_y"] * scale - CHIN_REF)
H, W = 1504, 1312
ours = np.zeros((H, W), bool)
ys, xs = np.nonzero(mark)
ys, xs = ys - oy, xs - ox
ok = (ys >= 0) & (ys < H) & (xs >= 0) & (xs < W)
ours[ys[ok], xs[ok]] = True
ours = ndimage.binary_closing(ours, iterations=1)
ref_m = np.load("out/risa_adult/outline_masks.npz")["fringe_hair"]
refimg = np.array(Image.open("ref/risa-adult/00-bikini.png").convert("RGB"))
box = (560, 150, 780, 340)


def edge(m):
    return ndimage.binary_dilation(m & ~ndimage.binary_erosion(m))


out = refimg.copy()
out[edge(ref_m)] = (255, 255, 0)
out[edge(ours)] = (0, 255, 255)
im = Image.fromarray(out).crop(box)
im.resize((im.width * zoom, im.height * zoom), Image.NEAREST).save("out/risa_adult/fringe-length.png")


def lowest(m, x, y0=176, y1=336):
    col = m[y0:y1, x]
    if not col.any():
        return None
    # the first run of hair from the top of the box down
    ys_ = np.nonzero(col)[0]
    first = ys_[0]
    last = first
    for y in ys_[1:]:
        if y - last > 1:
            break
        last = y
    return y0 + last


print("  x   ref  ours  diff")
diffs = []
for x in range(600, 746, 6):
    r, o = lowest(ref_m, x), lowest(ours, x)
    if r is None or o is None:
        print(f"{x:4d}  {r}  {o}")
        continue
    diffs.append(o - r)
    print(f"{x:4d} {r:4d} {o:5d} {o - r:+5d}")
print("mean diff", round(float(np.mean(diffs)), 1), "mean abs", round(float(np.mean(np.abs(diffs))), 1))
