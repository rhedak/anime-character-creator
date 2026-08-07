import math, sys
sys.path.insert(0, "src")
from collections import Counter
from dataclasses import replace
import cairosvg
import numpy as np
from PIL import Image
from anime_character_creator import character as C
from anime_character_creator.presets import PRESETS
from anime_character_creator.skeleton import BUILDS, build_skeleton

p = replace(PRESETS["satoshi"], hairstyle="short_crop")
sk = build_skeleton(heads=BUILDS["realistic"], frame=p.frame)
S = 4
cairosvg.svg2png(bytestring=C.render_character(p, sk).encode(), write_to="out/trace/_p.png",
                 output_width=int(sk.canvas_w*S), output_height=int(sk.canvas_h*S))
a = np.asarray(Image.open("out/trace/_p.png").convert("RGB"))
cx, cy, r = sk.head_cx*S, sk.head_cy*S, sk.head_r*S
fall = C._hair_fall(sk, p)
start, edge = C._crop_outline(fall)
pts, prev = [], start
for ctrl, end in edge:
    for i in range(1, 13):
        t = i/12
        pts.append(((1-t)**2*prev[0]+2*(1-t)*t*ctrl[0]+t**2*end[0],
                    (1-t)**2*prev[1]+2*(1-t)*t*ctrl[1]+t**2*end[1]))
    prev = end
bad = []
for x, y in pts:
    n = math.hypot(x, y)
    ix, iy = x*(1 - 0.06/n), y*(1 - 0.06/n)
    px, py = int(cx + ix*r), int(cy + iy*r)
    col = tuple(int(v) for v in a[py, px])
    if sum(col) > 700:
        bad.append((round(math.degrees(math.atan2(x, -y))), col))
print(f"{len(bad)} of {len(pts)} samples 0.06 r inside the outline are near-white")
print("bearings:", sorted({b for b, _ in bad}))
print("colours:", Counter(c for _, c in bad).most_common(3))
print("hair", p.hair_color, " tips", p.hair_tip_color)
