"""G0 for the bikini top: how well our top covers the bikini-top layer of ref 04.

    ./harness/run.sh harness/franzi/gate_top.py        # renders adult_female first

The render's top is the underwear-coloured region above the waist, grown by the stroke's half width so it is measured at the
ink's outer edge like the reference layer. Both are brought to one grid by the body gate's mapping (chin and sole rows, the
centre line). Pass: IoU at least 0.90 over the chest box. Fixed in docs/adult-body-plan.md terms before tuning (stage 4 redo).
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

OUT = Path("out/franzi")
IOU_MIN = 0.90
T_CHIN, CX_T, H = 434.0, 668.2, 352.0
svg = OUT / "adult_female-underwear.svg"
subprocess.run(["node", "harness/franzi/underwear.ts", "adult_female", str(svg)], check=True)
subprocess.run([sys.executable, "harness/svg2png.py", str(svg), str(svg.with_suffix(".png")), "--scale", "2"], check=True)
meta = json.loads(svg.with_suffix(".json").read_text())
im = np.array(Image.open(svg.with_suffix(".png")).convert("RGBA"))
alpha = im[..., 3] > 128
r_sole = int(np.where(alpha.any(1))[0].max())
r_chin = meta["chin_y"] * 2
tm = np.array(Image.open(OUT / "target.png").convert("L")) > 128
t_sole = int(np.where(tm.any(1))[0].max())
s = (t_sole - T_CHIN) / (r_sole - r_chin)  # reference px per render px

under = np.abs(im[..., :3].astype(int) - [0xE8, 0xE4, 0xDC]).sum(2) < 12
yy = np.mgrid[0 : im.shape[0], 0 : im.shape[1]][0]
under &= (yy < r_chin + 1.3 * H / s) & alpha
render = ndimage.binary_dilation(under, iterations=3)
# resample the render mask onto the reference grid: x_t = CX_T + (x_r - 400) * s, y_t = T_CHIN + (y_r - r_chin) * s
grid = np.zeros((2440, 1312), bool)
ys, xs = np.nonzero(render)
xt = np.round(CX_T + (xs - 400) * s).astype(int)
yt = np.round(T_CHIN + (ys - r_chin) * s).astype(int)
for dy in (0, 1):
    for dx in (0, 1):
        grid[np.clip(yt + dy, 0, 2439), np.clip(xt + dx, 0, 1311)] = True
grid = ndimage.binary_closing(grid, iterations=2)
seg = np.array(Image.open("ref/franzi/segments/04-bikini-fullbody/white-bikini-top.png"))[..., 3] > 128
# the reference layer stops short of the neck where the strap goes behind it: compare from the same row down
box = np.zeros_like(seg)
box[int(T_CHIN + 0.2 * H) : int(T_CHIN + 1.15 * H)] = True
a, b = grid & box, seg & box
iou = (a & b).sum() / (a | b).sum()
print(f"top IoU {iou:.3f} (min {IOU_MIN})  {'ok' if iou >= IOU_MIN else 'FAIL'}   ours {int(a.sum())} px, reference {int(b.sum())} px")
ov = np.full(seg.shape + (3,), 255, np.uint8)
ov[b & ~a] = (40, 90, 230)
ov[a & ~b] = (230, 50, 50)
ov[a & b] = (70, 40, 90)
Image.fromarray(ov).crop((440, 440, 900, 840)).resize((920, 800)).save(OUT / "top-overlay.png")
sys.exit(0 if iou >= IOU_MIN else 1)
