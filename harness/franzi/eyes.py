"""Where Franzi's irises sit, in head radii from the head centre, beside the reference's.

    ./harness/run.sh harness/franzi/eyes.py [OVERRIDES_JSON]

The reference (ref 04, brown-eyes segments, the calibration of harness/franzi_hair/trace.py): the iris centres sit at
x = -0.38 and +0.37 radii, y = +0.28 (eye distance 0.75). Prints ours from the amber pixels of a render at the same scale.
"""

import json
import subprocess
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

over = sys.argv[1] if len(sys.argv) > 1 else "{}"
subprocess.run(["node", "harness/franzi/franzi.ts", "out/franzi/eyes.svg", over], check=True)
subprocess.run([sys.executable, "harness/svg2png.py", "out/franzi/eyes.svg", "out/franzi/eyes.png", "--scale", "4"], check=True)
a = np.array(Image.open("out/franzi/eyes.png").convert("RGBA"))
rgb = a[..., :3].astype(int)
amber = (rgb[..., 0] > 140) & (rgb[..., 1] > 90) & (rgb[..., 1] < 190) & (rgb[..., 2] < 100) & (a[..., 3] > 128)
amber[480:] = False
amber[:150] = False
lab, n = ndimage.label(amber)
sizes = ndimage.sum(amber, lab, range(1, n + 1))
idx = np.argsort(sizes)[-2:] + 1
cs = sorted((ndimage.center_of_mass(lab == i) for i in idx), key=lambda c: c[1])
r = 35.8967 * 4
cx, cy = 200 * 4, 61.4192 * 4
print("ours   x", [round((c[1] - cx) / r, 3) for c in cs], "y", [round((c[0] - cy) / r, 3) for c in cs], "distance", round((cs[1][1] - cs[0][1]) / r, 3))
print("ref    x [-0.38, 0.37] y [0.28, 0.28] distance 0.75")
