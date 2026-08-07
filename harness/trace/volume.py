"""Is the chibi's extra hair one scale factor, or does it vary around the head?

If the ratio between the two canon contours is roughly flat, the whole
build-dependence is one number and the cut stays a single traced shape.
"""
import math, sys
sys.path.insert(0, "out/trace")
import numpy as np
from PIL import Image
from trace import REF, REF_CX, REF_CY, REF_R

CHIBI = ("ref/satoshi-chibi.jpg", 434.0, 352.0, 176.2)
ADULT = (REF, REF_CX, REF_CY, REF_R)


def profile_of(path, cx, cy, r, lo=-130, hi=131):
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    ink = a.sum(2) < 700
    out = {}
    for deg in range(lo, hi):
        th = math.radians(deg)
        last, rad = None, 0.30
        while rad < 2.1:
            x = int(round(cx + math.sin(th) * r * rad))
            y = int(round(cy - math.cos(th) * r * rad))
            if 0 <= y < ink.shape[0] and 0 <= x < ink.shape[1] and ink[y, x]:
                last = rad
            rad += 0.002
        if last is not None and last < 1.9:
            out[deg] = last
    return out


ad = profile_of(*ADULT)
ch = profile_of(*CHIBI)
both = sorted(set(ad) & set(ch))
ratios = [ch[d] / ad[d] for d in both]
print(f"{len(both)} shared bearings")
print(f"ratio chibi/adult: mean {np.mean(ratios):.3f}  median {np.median(ratios):.3f} "
      f" sd {np.std(ratios):.3f}  min {min(ratios):.3f}  max {max(ratios):.3f}")
print("\nby sector:")
for lo, hi, label in ((-130, -60, "lower right"), (-60, -20, "upper right"),
                      (-20, 20, "crown"), (20, 60, "upper left"), (60, 130, "lower left")):
    seg = [ch[d] / ad[d] for d in both if lo <= d < hi]
    if seg:
        print(f"  {label:12s} {np.mean(seg):.3f}  (sd {np.std(seg):.3f})")
