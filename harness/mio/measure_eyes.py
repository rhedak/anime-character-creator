"""Her eyes, measured (`docs/mio-plan.md`, M9 variant): where the two eye layers sit in the
composite, and for each eye the aperture, the iris and the white, and the gap between them.

    ./harness/run.sh harness/mio/measure_eyes.py
"""

import numpy as np
from common import CX, CY, R, RGB
from PIL import Image

BASE = "ref-local/mio"
comp = np.asarray(Image.open(f"{BASE}/mio.png").convert("RGBA")).astype(int)


def find(name):
    seg = np.asarray(Image.open(f"{BASE}/segments/large-black-eyes/{name}").convert("RGBA")).astype(int)
    h, w = seg.shape[:2]
    opaque = seg[:, :, 3] > 200
    best = (1e18, None)
    # The eyes sit in the face, rows 250 to 340: search that band.
    for oy in range(255, 345 - h):
        for ox in range(500, 760 - w):
            diff = np.abs(comp[oy : oy + h, ox : ox + w, :3] - seg[:, :, :3])[opaque].mean()
            if diff < best[0]:
                best = (diff, (ox, oy))
    return seg, best


for name in ("large-black-eyes-1.png", "large-black-eyes-2.png"):
    seg, (diff, (ox, oy)) = find(name)
    print(name, seg.shape[:2], "offset", (ox, oy), "mean diff", round(diff, 2))

# --- classify and look ----------------------------------------------------------------
for name, off in (("large-black-eyes-1.png", (518, 255)), ("large-black-eyes-2.png", (663, 257))):
    seg = np.asarray(Image.open(f"{BASE}/segments/large-black-eyes/{name}").convert("RGBA")).astype(int)
    op = seg[:, :, 3] > 128
    s = seg[:, :, :3].sum(2)
    cls = np.zeros(seg.shape[:2] + (3,), np.uint8) + 120
    cls[~op] = (200, 230, 200)
    cls[op & (s > 650)] = (255, 255, 255)
    cls[op & (s <= 650) & (s > 200)] = (140, 140, 140)
    cls[op & (s <= 200)] = (0, 0, 0)
    Image.fromarray(cls).resize((seg.shape[1] * 8, seg.shape[0] * 8), Image.NEAREST).save(
        f"out/mio/eye_cls_{name[-5]}.png"
    )
