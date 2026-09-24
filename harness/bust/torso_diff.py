"""What a change to the body layer moved, painted red: before, after and the
changed pixels, cropped to the change, per preset and build.

Before is the figure with `_torso` switched off. Pass preset names; the
smallest change is the one to read first (`docs/bust-strategy.md`).

    ./harness/run.sh harness/bust/torso_diff.py kyoko satoko

Writes `out/bust/torso_diff.png`.
"""

import io
import sys
import cairosvg
import numpy as np
from PIL import Image, ImageDraw
from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS
S = 3
def png(p, sk):
    return np.array(Image.open(io.BytesIO(cairosvg.svg2png(bytestring=c.render_character(p, sk, background="#ffffff").encode(), scale=S))).convert("RGB"))
tiles = []
real = c._torso
for name, build in [(n, b) for n in sys.argv[1:] for b in ("chibi", "realistic")]:
    p = PRESETS[name]
    sk = c.skeleton_for(p, c.BUILDS[build])
    after = png(p, sk)
    c._torso = lambda sk, p: ""
    before = png(p, sk)
    c._torso = real
    diff = np.any(before != after, axis=-1)
    ys, xs = np.nonzero(diff)
    if not len(xs):
        continue
    x0, x1, y0, y1 = xs.min() - 30, xs.max() + 30, ys.min() - 30, ys.max() + 30
    mark = after.copy(); mark[diff] = (255, 0, 0)
    row = [Image.fromarray(a[max(0,y0):y1, max(0,x0):x1]) for a in (before, after, mark)]
    w = sum(r.width for r in row) + 20; h = row[0].height + 16
    t = Image.new("RGB", (w, h), (220, 220, 220)); d = ImageDraw.Draw(t); d.text((3, 2), f"{name} {build}: before / after / changed in red", fill=(0,0,0))
    x = 0
    for r in row:
        t.paste(r, (x, 16)); x += r.width + 10
    tiles.append(t)
W = max(t.width for t in tiles); H = sum(t.height + 8 for t in tiles)
sheet = Image.new("RGB", (W, H), (200, 200, 200)); y = 0
for t in tiles:
    sheet.paste(t, (0, y)); y += t.height + 8
sheet.save("out/bust/torso_diff.png"); print(sheet.size)
