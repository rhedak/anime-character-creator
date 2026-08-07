"""How much room the traced silhouette leaves over our own skull and ear.

The trace is in head-radius units, so it drops straight onto our head. Whether
it *fits* is a different question: our head is wider against its own radius than
the canon's is, which is the open residual under gap 2, and the ear hangs off
that width.
"""
import math, sys
sys.path.insert(0, "out/trace")
sys.path.insert(0, "src")
from fit import fit_chain, marks, polar, profile
from trace import sample
from anime_character_creator import character as C
from anime_character_creator.skeleton import BUILDS, build_skeleton

prof = profile()
ch = fit_chain(prof, marks(prof, 0.090))
pts = sample(*ch, per=20)

def skull_r(deg, build):
    """Our skull's radius along a bearing, by marching out until we leave it."""
    lo, hi = 0.2, 1.6
    for _ in range(40):
        mid = (lo + hi) / 2
        x, y = polar(deg, mid)
        if abs(x) <= C._head_edge_x(y, build):
            lo = mid
        else:
            hi = mid
    return lo

print(f"{'build':10s} {'worst hair-over-skull':>22s} {'at bearing':>11s} {'ear tip r':>10s} {'hair r there':>13s}")
for name in ("chibi", "realistic"):
    sk = build_skeleton(heads=BUILDS[name])
    b = sk.build
    worst, at = 9.9, 0.0
    for x, y in pts:
        deg = math.degrees(math.atan2(x, -y))
        gap = math.hypot(x, y) - skull_r(deg, b)
        if gap < worst:
            worst, at = gap, deg
    # the ear's furthest point from the head centre
    start, segs = C._ear_outer(b)
    ear = sample(start, segs, per=30)
    ex, ey = max(ear, key=lambda q: math.hypot(*q))
    ear_r = math.hypot(ex, ey)
    ear_deg = math.degrees(math.atan2(ex, -ey))
    hair_r = max(math.hypot(*p) for p in pts
                 if abs(math.degrees(math.atan2(p[0], -p[1])) - ear_deg) < 4)
    print(f"{name:10s} {worst:+22.3f} {at:11.0f} {ear_r:10.3f} {hair_r:13.3f}")
