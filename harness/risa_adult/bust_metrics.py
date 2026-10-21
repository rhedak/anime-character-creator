"""Our bikini top against Risa's reference, at a range of `bust` values.

    ./harness/run.sh harness/risa_adult/bust_metrics.py [BUST ...]

For each value, renders Risa on the adult body (harness/risa_adult/risa.ts) with a marker colour for the top, rasterises it at the reference's scale and maps it to the
reference's pixels (head height 352 px, centre line 668.2, chin 434, as compare_head.py), and measures the top's cups: bounding box and area, against the reference's
`white-bikini-top` layer (its cups and straps, alpha over 200). Only rows from the cups' top down (y 480 to 800) are counted, so the straps' height is the same in both.
A number to bring near; the look is judged on the overlay (compare_head.py).
"""

import json
import subprocess
import sys

import numpy as np
from PIL import Image

values = [float(v) for v in sys.argv[1:]] or [0.0, -0.1, -0.2, -0.26, -0.3]
meta = json.load(open("out/franzi/al-meta.json"))
H_REF, CX_REF, CHIN_REF = 352.0, 668.2, 434.0
scale = H_REF / (2 * meta["head_r"])
MARK = (255, 0, 255)

ref = np.array(Image.open("ref/risa-adult/segments/00-bikini/white-bikini-top.png"))[..., 3] > 200


def box(m, y0=480, y1=800):
    m = m.copy()
    m[:y0] = False
    m[y1:] = False
    ys, xs = np.nonzero(m)
    return f"area {int(m.sum()):6d}  x {xs.min()}..{xs.max()} (w {xs.max() - xs.min() + 1})  y {ys.min()}..{ys.max()} (h {ys.max() - ys.min() + 1})"


print("ref        ", box(ref))
for b in values:
    over = {"bust": b, "outfit": {"underwear_color": "#ff00ff"}}
    subprocess.run(["node", "harness/risa_adult/risa.ts", "out/risa_adult/bust.svg", json.dumps(over)], check=True, stderr=subprocess.DEVNULL)
    subprocess.run([sys.executable, "harness/svg2png.py", "out/risa_adult/bust.svg", "out/risa_adult/bust.png", "--scale", f"{scale:.5f}"], check=True, stdout=subprocess.DEVNULL)
    im = Image.open("out/risa_adult/bust.png").convert("RGB")
    a = np.array(im).astype(int)
    mark = (np.abs(a - np.array(MARK)).sum(2) < 30)
    ox = round((meta["canvas_w"] / 2) * scale - CX_REF)
    oy = round(meta["chin_y"] * scale - CHIN_REF)
    full = np.zeros((1504, 1312), bool)
    ys, xs = np.nonzero(mark)
    ys, xs = ys - oy, xs - ox
    ok = (ys >= 0) & (ys < 1504) & (xs >= 0) & (xs < 1312)
    full[ys[ok], xs[ok]] = True
    print(f"bust {b:+.2f}  ", box(full))
