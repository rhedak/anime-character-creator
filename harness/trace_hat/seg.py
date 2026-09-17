"""Label the reference's non-outline regions around the hat, report them."""

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

REF = "/Users/henrik/git/time_slider_katherina/style-anchors/katherina_grok/katherina_grok.jpg"
OUT = "out/trace_hat"

rgb = np.asarray(Image.open(REF).convert("RGB")).astype(int)
H, W = rgb.shape[:2]
s = rgb.sum(2)
for thr in (40, 60, 80):
    fill = s > thr
    lab, n = ndi.label(fill)
    print("thr", thr, "components", n)

thr = 60
fill = s > thr
lab, n = ndi.label(fill)
objs = ndi.find_objects(lab)
rows = []
for i, sl in enumerate(objs, start=1):
    ys, xs = sl
    if ys.start > 560:  # only things that begin above the eyes' bottom
        continue
    area = int((lab[sl] == i).sum())
    if area < 150:
        continue
    col = rgb[lab == i].mean(0).round().astype(int)
    rows.append((i, area, xs.start, ys.start, xs.stop, ys.stop, tuple(col)))
for r in sorted(rows, key=lambda r: -r[1])[:30]:
    print(r)
np.save(f"{OUT}/lab.npy", lab)
