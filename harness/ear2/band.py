"""Where the fold's band sits inside the ear, derived rather than picked.

The trace fixes the fold's shape; what it cannot fix is where that shape lands
across an ear narrower than the canon's. Three candidate bands were rendered
first and the three chibi tiles were not distinguishable at any useful zoom, so
choosing among them by eye would have been a coin flip. The constraint is real
though, and there are only two sides to it: the fold has to clear the skull,
which bulges out past the attach chord everywhere between the two attach points,
and it has to stay inside the rim. So this widens the band until one of those
clearances falls under a crease's own stroke width, then centres it in whatever
slack is left, at whichever build is tighter.

Also prints the attach chord's tilt, which `_ear_place` assumes is near enough
vertical to measure the stand-out straight along x.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, "src")

from anime_character_creator import character as C  # noqa: E402
from anime_character_creator.skeleton import BUILDS, build_skeleton  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def walk(start, segs, per=40):
    pts = [start]
    prev = start
    for c, e in segs:
        for i in range(1, per + 1):
            t = i / per
            pts.append(
                (
                    (1 - t) ** 2 * prev[0] + 2 * (1 - t) * t * c[0] + t**2 * e[0],
                    (1 - t) ** 2 * prev[1] + 2 * (1 - t) * t * c[1] + t**2 * e[1],
                )
            )
        prev = e
    return pts


FOLD = walk(C._EAR_FOLD_START, C._EAR_FOLD)
RIM = walk(C._EAR_ARC_START, C._EAR_ARC)


def rim_out(along: float) -> float:
    """The rim's own stand-out at a height, by interpolating the traced arc."""
    best = 0.0
    for i in range(len(RIM) - 1):
        a, b = RIM[i], RIM[i + 1]
        lo, hi = sorted((a[0], b[0]))
        if lo <= along <= hi and hi > lo:
            t = (along - a[0]) / (b[0] - a[0])
            best = max(best, a[1] + (b[1] - a[1]) * t)
    return best


print("build   chord tilt   crease width   feasible band")
for name in ("chibi", "realistic"):
    sk = build_skeleton(heads=BUILDS[name])
    (tx, ty), (bx, by) = C._ear_span(sk.build)
    tilt = math.degrees(math.atan2(abs(bx - tx), by - ty))
    # A crease's stroke, in head radii, then as a share of the stand-out.
    crease = C._stroke_w(sk) * 0.55 / sk.head_r
    m = crease / C._EAR_OUT

    def limits(along: float, sk=sk, tx=tx, ty=ty, bx=bx, by=by) -> tuple[float, float]:
        y = ty + (by - ty) * along
        chord_x = tx + (bx - tx) * along
        skull = (C._head_edge_x(y, sk.build) - chord_x) / C._EAR_OUT
        return skull, rim_out(along)

    lo_need = max(limits(a)[0] for a, _ in FOLD)  # innermost the fold may sit
    hi_need = min(limits(a)[1] for a, u in FOLD if u > 0.9)
    print(
        f"{name:9s} {tilt:5.1f} deg   {m:.3f} of out   "
        f"skull {lo_need:+.3f}  rim {hi_need:.3f}  margin {m:.3f}"
    )

# A fold point at height `a` and depth `u` lands at IN + u * SPAN, and has to
# sit between the skull and the rim at that height with a crease's width to
# spare. Two inequalities per point per build, linear in IN and SPAN, so the
# widest band is the largest SPAN that still leaves an IN satisfying all of
# them. Small enough to settle by sweeping SPAN and reading off the interval.
BOUNDS = []
for name in ("chibi", "realistic"):
    sk = build_skeleton(heads=BUILDS[name])
    (tx, ty), (bx, by) = C._ear_span(sk.build)
    m = C._stroke_w(sk) * 0.55 / sk.head_r / C._EAR_OUT
    for along, u in FOLD:
        y = ty + (by - ty) * along
        chord_x = tx + (bx - tx) * along
        skull = (C._head_edge_x(y, sk.build) - chord_x) / C._EAR_OUT
        BOUNDS.append((u, skull + m, rim_out(along) - m))


def interval(span: float) -> tuple[float, float]:
    lo = max(b - u * span for u, b, _ in BOUNDS)
    hi = min(t - u * span for u, _, t in BOUNDS)
    return lo, hi


best = 0.0
for i in range(1, 201):
    s = i / 200
    lo, hi = interval(s)
    if lo <= hi:
        best = s
lo, hi = interval(best)
print(f"\nwidest feasible span {best:.3f}, with the inner edge free in {lo:.3f}..{hi:.3f}")
print(f"_EAR_FOLD_IN = {(lo + hi) / 2:.2f}\n_EAR_FOLD_SPAN = {best:.2f}")
