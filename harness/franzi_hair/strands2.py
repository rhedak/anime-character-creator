"""Trace the strand lines of Franzi's hair from the contrast-shifted hair layer (not by eye).

    ./harness/run.sh harness/franzi_hair/strands2.py

The hair layer's dark range is stretched; a line is a thin ridge darker than its surroundings (difference of Gaussians). The ridge
mask inside the eroded hair is split into connected pieces, each thinned by taking, along its main direction, the median
position of its pixels in short bins (the trace-reference method for interior lines), and kept when long enough. Chains are in
head radii; out/franzi_hair/strands2.png shows them over the stretched hair; out/franzi_hair/strands.json feeds emit.py.
"""

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

OUT = Path("out/franzi_hair")
OX, OY, S = 660.0, 270.5, 175.7
a = np.array(Image.open("ref/franzi/04-bikini-fullbody.png").convert("RGBA")).astype(float)
hair = ndimage.binary_fill_holes(np.array(Image.open("ref/franzi/segments/04-bikini-fullbody/black-hair.png"))[..., 3] > 128)
lum = a[..., :3].mean(2)
inner = ndimage.binary_erosion(hair, iterations=6)
hp = ndimage.gaussian_filter(lum, 1.1) - ndimage.gaussian_filter(lum, 4.5)
ridge = (hp < -6.5) & inner
ridge = ndimage.binary_opening(ridge, structure=np.ones((2, 2)))
lab, n = ndimage.label(ridge, structure=np.ones((3, 3)))
chains = []
for i in range(1, n + 1):
    ys, xs = np.nonzero(lab == i)
    if len(xs) < 45:
        continue
    pts = np.stack([xs, ys], 1).astype(float)
    c = pts.mean(0)
    u, sv, vt = np.linalg.svd(pts - c, full_matrices=False)
    if sv[0] < 4 * max(sv[1], 1e-6) or sv[0] / np.sqrt(len(xs)) < 3:  # not elongated: a blob
        continue
    t = (pts - c) @ vt[0]
    order = np.argsort(t)
    nb = max(4, int((t.max() - t.min()) / 7))
    edges = np.linspace(t.min(), t.max(), nb + 1)
    line = []
    for b in range(nb):
        sel = (t >= edges[b]) & (t <= edges[b + 1])
        if sel.sum():
            line.append(tuple(np.median(pts[sel], 0)))
    if len(line) >= 4:
        chains.append(line)
print("strand lines", len(chains))
img = Image.fromarray((np.clip((lum - 8) / 100, 0, 1) * 255).astype(np.uint8)).convert("RGB").crop((480, 60, 880, 560)).resize((800, 1000), Image.LANCZOS)
d = ImageDraw.Draw(img)
for k, ln in enumerate(chains):
    z = [((x - 480) * 2, (y - 60) * 2) for x, y in ln]
    d.line(z, fill=(255, 60, 60), width=2)
img.save(OUT / "strands2.png")
json.dump([[[(x - OX) / S, (y - OY) / S] for x, y in ln] for ln in chains], open(OUT / "strands2-raw.json", "w"))
