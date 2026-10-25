"""Line widths and colours of Risa against her uniform reference (docs/risa-polish-plan.md, stage 5): 01 registered to the bikini grid beside our uniform render on the same grid.

    ./harness/run.sh harness/risa_adult/line_measure.py      # after uniform_check.py, which renders out/risa_adult/uc-slender.png

A line pixel is one much darker than its neighbourhood (below 0.6 of a 17 px median, and dark); its width is twice the distance to the nearest non-line pixel, read on the middle of each
line (the distance transform's ridge). Printed per region: the median width, the line pixels, and the colour of the darkest quarter of them.
"""

import json, sys
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, "harness/risa_adult")
from registration import Registration
H, CX, CHIN = 352.0, 668.2, 434.0
W, HT = 1312, 2300
reg = Registration("ref/risa-adult/01-school-uniform.png")
ref = np.array(reg.register(Image.open("ref/risa-adult/01-school-uniform.png").convert("RGB"), size=(W, HT))).astype(float)
m = json.load(open("out/franzi/al-meta.json")); s = H / (2 * m["head_r"])
ox, oy = round(m["canvas_w"] / 2 * s - CX), round(m["chin_y"] * s - CHIN)
im = Image.open("out/risa_adult/uc-slender.png").convert("RGBA"); bg = Image.new("RGBA", im.size, "white"); bg.alpha_composite(im)
ours = np.array(bg.convert("RGB").crop((ox, oy, ox + W, oy + HT))).astype(float)
REGIONS = {"hair+face": (CHIN - 1.0 * H, CHIN), "torso": (CHIN + 0.2 * H, CHIN + 2.0 * H), "legs": (CHIN + 2.4 * H, min(HT, CHIN + 4.2 * H))}
def lines(a):
    L = a @ np.array([0.299, 0.587, 0.114])
    loc = ndimage.median_filter(L, size=17)
    line = (L < 0.6 * loc) & (L < 140)
    dt = ndimage.distance_transform_edt(line)
    ridge = line & (dt >= ndimage.maximum_filter(dt, size=3))
    return line, dt, ridge, L
for label, a in (("ref", ref), ("ours", ours)):
    line, dt, ridge, L = lines(a)
    for rname, (y0, y1) in REGIONS.items():
        sl = slice(int(y0), int(y1))
        w = 2 * dt[sl][ridge[sl]]
        col = a[sl][line[sl]]
        dark = col[np.argsort(col.sum(1))[: max(1, len(col) // 4)]].mean(0)
        print(f"{label:4s} {rname:9s} line width median {np.median(w):4.1f} px (p25 {np.percentile(w, 25):3.1f}, p75 {np.percentile(w, 75):3.1f})  line px {int(line[sl].sum()):6d}  darkest quarter colour {tuple(int(c) for c in dark)}")
