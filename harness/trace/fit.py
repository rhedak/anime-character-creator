"""Fit a small chain of quadratics to the canon's measured hair contour.

Two steps that were being done by eye and should not be. Marks are the local
extrema of the radius profile with a prominence floor, so a tip is a tip and not
a wobble. Control points are then least-squares fitted to the measured points
between each pair of marks, which is exact for a quadratic: with the endpoints
pinned there is one free control and the error is linear in it.

Placing the control at the mid-bearing at the mean radius, which is the obvious
thing and what the first pass did, bulges every edge outside the chord. On a
contour made of straight lock edges that is wrong everywhere at once.
"""
import math, sys
sys.path.insert(0, "out/trace")
import numpy as np
from PIL import Image
from trace import REF, REF_CX, REF_CY, REF_R

_a = np.asarray(Image.open(REF).convert("RGB")).astype(int)
INK = _a.sum(2) < 700


def radius_at(deg, rmax=2.0, step=0.002):
    th = math.radians(deg)
    last, r = None, 0.30
    while r < rmax:
        x = int(round(REF_CX + math.sin(th) * REF_R * r))
        y = int(round(REF_CY - math.cos(th) * REF_R * r))
        if 0 <= y < INK.shape[0] and 0 <= x < INK.shape[1] and INK[y, x]:
            last = r
        r += step
    return last


def polar(deg, r):
    a = math.radians(deg)
    return (math.sin(a) * r, -math.cos(a) * r)


def profile(lo=-142, hi=143, step=1):
    out = []
    for d in range(lo, hi, step):
        r = radius_at(d)
        if r is not None and r < 1.7:
            out.append((float(d), r))
    return out


def marks(prof, tol=0.030):
    """Simplify the contour to a handful of points, Douglas-Peucker in xy.

    The first attempt thinned by repeatedly dropping the shallowest adjacent
    pair of extrema, and that quietly eats real locks: once a pair of
    near-equal-radius wiggles goes, a genuine tip and the notch two places away
    become neighbours with a small step between them and are dropped next. It
    lost the whole sawtooth down the character's left side while looking like it
    was working. Douglas-Peucker keeps whatever is far from the chord, which is
    exactly what a tip is, and has no opinion about alternation.
    """
    pts = [polar(d, r) for d, r in prof]

    def simplify(lo, hi):
        if hi - lo < 2:
            return [lo]
        ax, ay = pts[lo]
        bx, by = pts[hi]
        dx, dy = bx - ax, by - ay
        n = math.hypot(dx, dy) or 1e-9
        worst, at = -1.0, lo
        for i in range(lo + 1, hi):
            px, py = pts[i]
            dist = abs(dx * (ay - py) - (ax - px) * dy) / n
            if dist > worst:
                worst, at = dist, i
        if worst <= tol:
            return [lo]
        return simplify(lo, at) + simplify(at, hi)

    keep = simplify(0, len(pts) - 1) + [len(pts) - 1]
    return [prof[i] for i in keep]


def fit_chain(prof, mk):
    """Least-squares control point per segment, endpoints pinned to the marks."""
    by_deg = {d: r for d, r in prof}
    start = polar(*mk[0])
    segs = []
    for (d0, r0), (d1, r1) in zip(mk, mk[1:]):
        p0, p2 = polar(d0, r0), polar(d1, r1)
        lo, hi = (d0, d1) if d0 < d1 else (d1, d0)
        pts = [(d, by_deg[d]) for d in range(int(lo) + 1, int(hi)) if d in by_deg]
        num = np.zeros(2)
        den = 0.0
        for d, r in pts:
            t = (d - d0) / (d1 - d0)
            w = 2 * (1 - t) * t
            q = np.array(polar(d, r))
            res = q - (1 - t) ** 2 * np.array(p0) - t**2 * np.array(p2)
            num += w * res
            den += w * w
        c = (num / den) if den > 1e-9 else (np.array(p0) + np.array(p2)) / 2
        segs.append(((float(c[0]), float(c[1])), p2))
    return start, segs
