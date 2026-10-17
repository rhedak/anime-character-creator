"""Eye aperture size, ours against the reference, in head radii (the calibration of harness/franzi_hair/trace.py).

    ./harness/run.sh harness/franzi/eyes_measure.py [OVERRIDES_JSON]

The aperture is the eye's dark outline interior: the eye-white and iris pixels together (anything that is not skin or dark line
inside the lash outline), found as the connected region around the iris centre. Prints width, height and the iris size.
"""

import json
import subprocess
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

S_REF, OX, OY = 175.7, 660.0, 270.5
over = sys.argv[1] if len(sys.argv) > 1 else "{}"
subprocess.run(["node", "harness/franzi/franzi.ts", "out/franzi/eyes.svg", over], check=True)
subprocess.run(["node", "harness/franzi/underwear.ts", "adult_female", "out/franzi/al-meta.svg"], check=True)
meta = json.load(open("out/franzi/al-meta.json"))
scale = 4.894
subprocess.run([sys.executable, "harness/svg2png.py", "out/franzi/eyes.svg", "out/franzi/eyes.png", "--scale", str(scale)], check=True)


def region(rgba, cx, cy, skin):
    rgb = rgba[..., :3].astype(int)
    notskin = (np.abs(rgb - skin).sum(2) > 60) & (rgba[..., 3] > 128)
    # grow a little so thin eye-white gaps join the iris, then take the component at the seed
    lab, _ = ndimage.label(ndimage.binary_closing(notskin, iterations=2))
    return lab == lab[int(cy), int(cx)]


def box(m):
    ys, xs = np.where(m)
    return xs.min(), xs.max(), ys.min(), ys.max(), m.sum()


ref = np.array(Image.open("ref/franzi/04-bikini-fullbody.png").convert("RGBA"))
ren = np.array(Image.open("out/franzi/eyes.png").convert("RGBA"))
skin = np.array([0xFF, 0xD0, 0xB5])
out = {}
for name, im, seeds, s in (("reference", ref, [(593.5, 323.5), (725.5, 314.0)], S_REF), ("ours", ren, None, 35.8967 * scale)):
    if seeds is None:
        cx0, cy0 = meta["canvas_w"] / 2 * scale, 61.4192 * scale
        seeds = [(cx0 - 0.38 * s, cy0 + 0.275 * s), (cx0 + 0.37 * s, cy0 + 0.275 * s)]
    for side, (sx, sy) in zip(("left", "right"), seeds):
        x0, x1, y0, y1, n = box(region(im, sx, sy, skin))
        out[(name, side)] = ((x1 - x0) / s, (y1 - y0) / s)
        print(f"{name:9s} {side:5s} eye width {(x1 - x0) / s:.3f} r, height {(y1 - y0) / s:.3f} r  (area {n / s / s:.3f} r^2)")
