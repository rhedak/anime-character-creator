"""Where our adult body's underwear sits against Risa's bikini reference: the top's and the briefs' bounding boxes and the briefs' lower tip.

    ./harness/run.sh harness/risa_adult/body_landmarks.py

Renders Risa (risa.ts) with the underwear in a marker colour, maps it to the reference's pixels (compare_head.py's mapping) and measures the two garments' extent, against the
layers `white-bikini-top` and `white-bikini-bottom` of ref/risa-adult/segments/00-bikini/. A difference here is a difference of body, not of garment.
"""

import json
import subprocess
import sys

import numpy as np
from PIL import Image

meta = json.load(open("out/franzi/al-meta.json"))
H_REF, CX_REF, CHIN_REF = 352.0, 668.2, 434.0
scale = H_REF / (2 * meta["head_r"])
subprocess.run(["node", "harness/risa_adult/risa.ts", "out/risa_adult/lm.svg", json.dumps({"outfit": {"underwear_color": "#ff00ff"}})], check=True, stderr=subprocess.DEVNULL)
subprocess.run([sys.executable, "harness/svg2png.py", "out/risa_adult/lm.svg", "out/risa_adult/lm.png", "--scale", f"{scale:.5f}"], check=True, stdout=subprocess.DEVNULL)
a = np.array(Image.open("out/risa_adult/lm.png").convert("RGB")).astype(int)
mark = np.abs(a - np.array([255, 0, 255])).sum(2) < 30
ox = round((meta["canvas_w"] / 2) * scale - CX_REF)
oy = round(meta["chin_y"] * scale - CHIN_REF)
ys, xs = np.nonzero(mark)
ys, xs = ys - oy, xs - ox
ours = np.zeros((1504, 1312), bool)
ok = (ys >= 0) & (ys < 1504) & (xs >= 0) & (xs < 1312)
ours[ys[ok], xs[ok]] = True


def stat(m, y0, y1):
    m = m.copy()
    m[:y0] = False
    m[y1:] = False
    ys_, xs_ = np.nonzero(m)
    return f"x {xs_.min()}..{xs_.max()} (w {xs_.max() - xs_.min() + 1})  y {ys_.min()}..{ys_.max()} (h {ys_.max() - ys_.min() + 1})"


for name, seg, rows in (("top", "white-bikini-top", (480, 820)), ("briefs", "white-bikini-bottom", (820, 1400))):
    ref = np.array(Image.open(f"ref/risa-adult/segments/00-bikini/{seg}.png"))[..., 3] > 200
    print(f"{name:6s} ref  {stat(ref, *rows)}")
    print(f"{name:6s} ours {stat(ours, *rows)}")
