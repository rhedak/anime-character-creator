"""Pull the canon's hair silhouette off the reference as a radius-per-bearing
profile, in head-radius units. Reading it off a polar grid by eye is possible
but it is the tips and notches that matter and they are a few pixels wide."""
import math, sys
sys.path.insert(0, "out/trace")
import numpy as np
from PIL import Image
from trace import REF, REF_CX, REF_CY, REF_R

a = np.asarray(Image.open(REF).convert("RGB")).astype(int)
ink = a.sum(2) < 700          # figure vs the white page

def radius_at(deg, rmax=2.0, step=0.002):
    """Furthest ink along this bearing, marching outward from the head centre."""
    th = math.radians(deg)
    last = None
    r = 0.30
    while r < rmax:
        x = int(round(REF_CX + math.sin(th) * REF_R * r))
        y = int(round(REF_CY - math.cos(th) * REF_R * r))
        if 0 <= y < ink.shape[0] and 0 <= x < ink.shape[1] and ink[y, x]:
            last = r
        r += step
    return last

prof = [(d, radius_at(d)) for d in range(-150, 151, 2)]
print("bearing  radius (head radii), + is the character's left")
for d, r in prof:
    if r is None:
        continue
    bar = "#" * int((r - 0.8) * 40) if r > 0.8 else ""
    print(f"{d:5d}   {r:.3f}  {bar}")
