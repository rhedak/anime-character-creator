"""Map the staff's fill components and colours in the reference."""

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

REF = "/Users/henrik/git/time_slider_katherina/style-anchors/katherina_grok/katherina_grok.jpg"
OUT = "out/trace_staff"
rgb = np.asarray(Image.open(REF).convert("RGB")).astype(int)
H, W = rgb.shape[:2]
s = rgb.sum(2)
r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]

# sample colours along the staff
for name, (x, y) in {
    "wood_upper": (300, 700),
    "wood_lower": (400, 1300),
    "wood_prong": (215, 500),
    "crystal_hi": (262, 470),
    "crystal_mid": (275, 520),
    "glow": (225, 470),
    "fist": (345, 930),
    "sleeve": (400, 930),
    "bg": (100, 1000),
}.items():
    print(name, (x, y), rgb[y, x], s[y, x])

# horizontal profile across the shaft at a few heights
for y in (650, 800, 1100, 1300, 1450):
    row = s[y, 150:560]
    ink = np.nonzero(row > 60)[0]
    print("row", y, "non-dark x", (ink[:1] + 150).tolist(), (ink[-1:] + 150).tolist(), "n", len(ink))

lab, n = ndi.label(s > 60)
objs = ndi.find_objects(lab)
rows = []
for i, sl in enumerate(objs, start=1):
    ys, xs = sl
    if xs.start > 520 or xs.stop < 140 or ys.stop < 290:
        continue
    area = int((lab[sl] == i).sum())
    if area < 60:
        continue
    col = np.median(rgb[lab == i], axis=0).astype(int)
    rows.append((i, area, xs.start, ys.start, xs.stop, ys.stop, tuple(col.tolist())))
for row in sorted(rows, key=lambda t: -t[1])[:40]:
    print(row)
np.save(f"{OUT}/lab.npy", lab)
