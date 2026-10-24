"""The front locks of docs/risa-polish-plan.md, stage 4: the hair that falls in front of Risa's shoulders onto the uniform, traced from 01-school-uniform.

    ./harness/run.sh harness/risa_adult/locks_trace.py      # then: node harness/risa_adult/locks_data.ts

01 is registered on the irises (registration.py). The locks are the pixels of its `red-hair` layer that lie inside the uniform's span on their row (between the blazer's or the shirt's
outermost pixels, below the neck): hair in front of the cloth. Each of the larger pieces is read row by row, every 0.01 H, as its leftmost and rightmost pixel, smoothed, and becomes a
lock: its outline the one edge down to the tip and the other back up. The mask's top is only where the uniform's span begins, so each lock is carried up from there to `TOP_D` along its
edges' own direction, into the hair beside the neck (the head is drawn over what reaches the jaw). Two strand lines run inside each lock, at a third and at two thirds of its width.

Positions go onto our body's grid as the other cuts traced from 01 do: 1.06 across about the reference body's centre and 1.03 down about the chin, its drift against the bikini image our
body matches (the plan's decision 1). Written in head heights, [v, d] (v signed, the viewer's left negative; d below the chin), as they are drawn on the slender build, to
out/risa_adult/locks.json; locks_data.ts inverts the build's warp so the data is in the body's knot space. Also writes out/risa_adult/locks-check.png, the traced outlines over 01.
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, "harness/risa_adult")
from registration import Registration  # noqa: E402

OUT = Path("out/risa_adult")
OUT.mkdir(parents=True, exist_ok=True)
H, CHIN, CX = 352.0, 434.0, 668.2
W, HT = 1312, 1504
SX, SY = 1.06, 1.03  # 01's drift against the bikini image, across and down
TOP_D = 0.04  # where each lock is carried up to, in head heights below the chin
STEP = 0.01
MIN_PX = 500  # a piece of hair over the cloth at least this big is a lock
START_BY = 0.3  # and it starts at the shoulder, by this depth (H below the chin): a strand that starts lower, over the chest, has no top to hang from and is left out

reg = Registration("ref/risa-adult/01-school-uniform.png")
layer = lambda n: np.array(reg.register(Image.open(f"ref/risa-adult/segments/01-school-uniform/{n}.png").convert("RGBA"), size=(W, HT)))[..., 3] > 127
hair, cloth = layer("red-hair"), layer("school-blazer") | layer("white-collared-shirt")
first = np.where(cloth.any(1), cloth.argmax(1), W)[:, None]
last = np.where(cloth.any(1), W - 1 - cloth[:, ::-1].argmax(1), -1)[:, None]
cols = np.arange(W)[None, :]
front = hair & (cols > first) & (cols < last)
front[: int(CHIN + 0.15 * H)] = False
front = ndimage.binary_opening(front, structure=np.ones((3, 3)))

# the reference body's centre line: the middle of the blazer's span where it hangs clear of the arms' hair
rows = range(int(CHIN + 0.9 * H), int(CHIN + 1.4 * H))
cb = float(np.mean([(first[r, 0] + last[r, 0]) / 2 for r in rows if cloth[r].any()]))
to_ours = lambda x, y: ((x - cb) / H * SX, (y - CHIN) / H * SY)

lab, n = ndimage.label(front)
sizes = ndimage.sum(front, lab, range(1, n + 1))
locks = []
for k in [i + 1 for i in np.argsort(sizes)[::-1] if sizes[i] >= MIN_PX]:
    m = lab == k
    ys = np.nonzero(m.any(1))[0]
    y0, y1 = int(ys.min()), int(ys.max())
    if (y0 - CHIN) / H > START_BY:
        print(f"left out: a piece of {int(sizes[k - 1])} px starting at {(y0 - CHIN) / H:.2f} H")
        continue
    left, right, ds = [], [], []
    for d in np.arange((y0 - CHIN) / H, (y1 - CHIN) / H, STEP):
        r0, r1 = int(CHIN + d * H), int(CHIN + (d + STEP) * H)
        band = m[r0 : r1 + 1].any(0)
        xs = np.nonzero(band)[0]
        if len(xs) == 0:
            continue
        left.append(xs.min())
        right.append(xs.max() + 1)
        ds.append(d + STEP / 2)
    left, right = ndimage.uniform_filter1d(np.array(left, float), 5), ndimage.uniform_filter1d(np.array(right, float), 5)
    ys_px = CHIN + np.array(ds) * H
    # carried up to TOP_D along each edge's direction over its first 0.1 H
    j = max(2, int(0.1 / STEP))
    up = np.arange(TOP_D, ds[0], STEP)
    yy = CHIN + up * H
    sl = lambda e: (e[j] - e[0]) / (ys_px[j] - ys_px[0])
    left = np.concatenate([left[0] + sl(left) * (yy - ys_px[0]), left])
    right = np.concatenate([right[0] + sl(right) * (yy - ys_px[0]), right])
    ys_px = np.concatenate([yy, ys_px])
    tip = ((left[-1] + right[-1]) / 2, ys_px[-1] + 0.01 * H)
    outline = [to_ours(x, y) for x, y in zip(left, ys_px)] + [to_ours(*tip)] + [to_ours(x, y) for x, y in zip(right[::-1], ys_px[::-1])]
    strands = []
    for f in (1 / 3, 2 / 3):
        n_ = int(len(ys_px) * 0.85)
        strands.append([to_ours(left[i] + f * (right[i] - left[i]), ys_px[i]) for i in range(2, n_)])
    locks.append({"outline": outline, "strands": strands, "px": int(sizes[k - 1])})
    print(f"lock {len(locks)}: {int(sizes[k - 1])} px, {(y0 - CHIN) / H:.2f} to {(y1 - CHIN) / H:.2f} H below the chin, {len(outline)} outline points")

locks.sort(key=lambda l: np.mean([q[0] for q in l["outline"]]))  # the viewer's left first
json.dump({"centre": cb, "locks": [{"outline": l["outline"], "strands": l["strands"]} for l in locks]}, open(OUT / "locks.json", "w"))

im = reg.register(Image.open("ref/risa-adult/01-school-uniform.png").convert("RGB"), size=(W, HT))
d = ImageDraw.Draw(im)
back = lambda v, dd: (cb + v / SX * H, CHIN + dd / SY * H)
for l in locks:
    d.line([back(*q) for q in l["outline"]] + [back(*l["outline"][0])], fill=(255, 255, 0), width=2)
    for s in l["strands"]:
        d.line([back(*q) for q in s], fill=(0, 255, 255), width=1)
im.crop((420, 420, 940, 1000)).save(OUT / "locks-check.png")
print(f"reference body centre {cb:.1f}; wrote {OUT / 'locks.json'} ({len(locks)} locks)")
