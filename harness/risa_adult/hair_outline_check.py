"""Our hair's outline drawn over the reference, and nothing else of ours: a check of the hair's shape.

    ./harness/run.sh harness/risa_adult/hair_outline_check.py

Renders Risa (harness/risa_adult/risa.ts) with the hair in a marker colour, rasterises it at the reference's scale, maps it to the reference's pixels the way compare_head.py does
(head height 352 px, centre line 668.2, chin 434), takes the visible hair (the marker and its darker strand tone) and draws the boundary of that region over the reference: the outer
edge and every inner edge (the hairline, the locks beside the face, where the body covers it). Cyan, 2 px. Writes out/risa_adult/hair-outline-full.png (the whole figure) and
hair-outline-head.png (the head at 2x).
"""

import json
import subprocess
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

meta = json.load(open("out/franzi/al-meta.json"))
H_REF, CX_REF, CHIN_REF = 352.0, 668.2, 434.0
scale = H_REF / (2 * meta["head_r"])
subprocess.run(["node", "harness/risa_adult/risa.ts", "out/risa_adult/hairmark.svg", json.dumps({"hair_color": "#ff00ff"})], check=True, stderr=subprocess.DEVNULL)
subprocess.run([sys.executable, "harness/svg2png.py", "out/risa_adult/hairmark.svg", "out/risa_adult/hairmark.png", "--scale", f"{scale:.5f}"], check=True, stdout=subprocess.DEVNULL)
a = np.array(Image.open("out/risa_adult/hairmark.png").convert("RGB")).astype(int)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
mark = (r > g + 40) & (b > g + 40)  # magenta and its darker strand tone; the skin (r high, b low), the bikini and the black ink are not
ox = round((meta["canvas_w"] / 2) * scale - CX_REF)
oy = round(meta["chin_y"] * scale - CHIN_REF)
H, W = 1504, 1312
hair = np.zeros((H, W), bool)
ys, xs = np.nonzero(mark)
ys, xs = ys - oy, xs - ox
ok = (ys >= 0) & (ys < H) & (xs >= 0) & (xs < W)
hair[ys[ok], xs[ok]] = True
hair = ndimage.binary_closing(hair, iterations=2)  # the strand lines' ink and the outline's stroke are not the edge
edge = hair & ~ndimage.binary_erosion(hair, iterations=1)
edge = ndimage.binary_dilation(edge, iterations=1)
ref = np.array(Image.open("ref/risa-adult/00-bikini.png").convert("RGB"))
out = ref.copy()
out[edge] = (0, 255, 255)
im = Image.fromarray(out)
im.crop((340, 40, 1030, 1100)).save("out/risa_adult/hair-outline-full.png")
head = im.crop((440, 50, 900, 560))
head.resize((head.width * 2, head.height * 2), Image.LANCZOS).save("out/risa_adult/hair-outline-head.png")
# the same, with the reference's own hair mask boundary in yellow for where the two differ
m = np.load("out/risa_adult/outline_masks.npz")["hair"]
ref_edge = ndimage.binary_dilation(m & ~ndimage.binary_erosion(m, iterations=1), iterations=1)
both = ref.copy()
both[ref_edge] = (255, 255, 0)
both[edge] = (0, 255, 255)
Image.fromarray(both).crop((340, 40, 1030, 1100)).save("out/risa_adult/hair-outline-both.png")
inter = (hair & m).sum()
print("hair px ours", int(hair.sum()), "ref", int(m.sum()), "IoU", round(inter / (hair | m).sum(), 3))

# where the two differ, and why: the head above the chin (no body in front), and below it the reference's hair that our body covers
nonwhite = np.zeros((H, W), bool)
nw = (a.sum(2) < 740)
nonwhite[ys[ok], xs[ok]] = False
full_nw = np.zeros((H, W), bool)
yy, xx = np.nonzero(nw)
yy, xx = yy - oy, xx - ox
k = (yy >= 0) & (yy < H) & (xx >= 0) & (xx < W)
full_nw[yy[k], xx[k]] = True
ours_body = full_nw & ~hair
head = np.zeros((H, W), bool)
head[:440] = True
hi = (hair & m & head).sum() / ((hair | m) & head).sum()
print("head rows (y < 440): hair IoU", round(float(hi), 3), " ours", int((hair & head).sum()), "ref", int((m & head).sum()))
low = ~head
missing = m & ~hair & low
print("below the chin: ref hair we do not show", int(missing.sum()), "px, of which under our body", int((missing & ours_body).sum()), "(", round(100 * (missing & ours_body).sum() / max(1, missing.sum())), "% )")
