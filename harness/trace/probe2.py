import math, sys
sys.path.insert(0, "src")
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
a = np.asarray(Image.open("out/trace/_p.png").convert("RGB")).astype(int)
cx, cy, r = sk.head_cx*S, sk.head_cy*S, sk.head_r*S
fall = C._hair_fall(sk, p)
poly = []
start, edge = C._crop_mass_shape(fall)
prev = start
poly.append(start)
for ctrl, end in edge:
    for i in range(1, 41):
        t = i/40
        poly.append(((1-t)**2*prev[0]+2*(1-t)*t*ctrl[0]+t**2*end[0],
                     (1-t)**2*prev[1]+2*(1-t)*t*ctrl[1]+t**2*end[1]))
    prev = end

def inside(px, py):
    hit = False
    for (ax, ay), (bx, by) in zip(poly, poly[1:] + poly[:1]):
        if (ay > py) != (by > py) and px < ax + (py-ay)/(by-ay)*(bx-ax):
            hit = not hit
    return hit

# every near-white pixel that is inside the mass and above the head centre
found = []
for py in range(int(cy - 1.6*r), int(cy + 0.2*r), 3):
    for px in range(int(cx - 1.7*r), int(cx + 1.7*r), 3):
        if a[py, px].sum() < 720:
            continue
        u, v = (px - cx)/r, (py - cy)/r
        if inside(u, v):
            found.append((round(u, 2), round(v, 2)))
print(f"{len(found)} near-white samples INSIDE the mass outline")
if found:
    xs = [f[0] for f in found]; ys = [f[1] for f in found]
    print(f"  x {min(xs):+.2f}..{max(xs):+.2f}   y {min(ys):+.2f}..{max(ys):+.2f}")
    print("  e.g.", found[:8])
