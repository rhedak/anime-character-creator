"""Trace the canon's fringe: the boundary where hair gives way to forehead.

Measurable for the same reason the silhouette was, and by a different means. The
silhouette is ink against the white page; this is hair against skin, and neither
warmth nor lightness settles it alone. Measured off the reference: the forehead
sits in a remarkably tight band, red minus blue of +54 to +58, where the gold
runs +100 to +123 and the pale tips +5 to +48. So warmth alone confuses skin with
the pale tips, and lightness alone confuses it with them too. Both together
separate all three cleanly, and the gold falls out on either test.

A first pass guessed +35 to +110 for skin and swallowed the whole gold crown,
which drew a boundary wandering across the top of the head. The numbers are
cheap to take and the guess was not close.
"""

from __future__ import annotations

import math
import sys

sys.path.insert(0, "out/trace")

import numpy as np
from PIL import Image
from trace import REF, REF_CX, REF_CY, REF_R

_a = np.asarray(Image.open(REF).convert("RGB")).astype(int)
_WARM = _a[:, :, 0] - _a[:, :, 2]
_SUM = _a.sum(2)
# Loose enough to hold the whole forehead together through JPEG ringing, which is
# all it has to do: the region is grown from a seed, so a stray pixel that also
# passes is only included if it is *connected* to the forehead. That is the whole
# reason this works where four per-column rules did not.
_SKINISH = (_WARM >= 22) & (_WARM <= 85) & (_SUM >= 470) & (_SUM <= 700)


def _forehead():
    """The forehead as one connected region, grown from a seed between the brows.

    The seed sits at 0.12 head radii above the head centre, low on the forehead.
    Higher up the centre column is inside the fringe rather than under it, which
    the check here catches rather than growing a region out of the hair.

    Its top edge is the fringe. Nothing simpler works on this reference. Colour
    cannot separate hair from skin, because skin beside a drawn line rings to sum
    520-622 at red minus blue +8 to +56 and overlaps the pale tips on both axes.
    Ink cannot either, because a brow is ink too and every column finds the brow
    before it finds the fringe. Asking instead which pixels are *joined to the
    forehead* sidesteps both: a brow is a hole inside the region, a gap between
    two locks is a channel leading out of it, and neither is on the top edge.

    Eight-connected, not four. The gaps between the canon's fringe blades are
    deep and only a pixel or two across at their narrowest, and a four-connected
    fill cannot get into them: it stops at the mouth of each gap and the top edge
    comes out smooth, reading the fringe as a soft curve where it is really a row
    of points.
    """
    from collections import deque

    h, w = _SKINISH.shape
    seen = np.zeros_like(_SKINISH)
    sx, sy = int(round(REF_CX)), int(round(REF_CY - 0.12 * REF_R))
    if not _SKINISH[sy, sx]:
        raise SystemExit("seed is not on skin; move it")
    q = deque([(sx, sy)])
    seen[sy, sx] = True
    top: dict[int, int] = {}
    while q:
        x, y = q.popleft()
        if y < top.get(x, 10**9):
            top[x] = y
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, -1), (1, 1), (-1, 1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and _SKINISH[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                q.append((nx, ny))
    return top


_TOP: dict[int, int] | None = None


def fringe_at(u: float):
    """Where the fringe's edge sits on this column, in head radii."""
    global _TOP
    if _TOP is None:
        _TOP = _forehead()
    y = _TOP.get(int(round(REF_CX + u * REF_R)))
    return None if y is None else (y - REF_CY) / REF_R


def profile(lo=-0.80, hi=0.81, step=0.01):
    out = []
    u = lo
    while u < hi:
        v = fringe_at(u)
        if v is not None:
            out.append((round(u, 4), v))
        u += step
    return out


if __name__ == "__main__":
    from PIL import ImageDraw

    prof = profile()
    print(f"{len(prof)} columns carry a fringe boundary")
    print(f"  x {prof[0][0]:+.2f} to {prof[-1][0]:+.2f}")
    ys = [v for _, v in prof]
    print(f"  lowest tip y {max(ys):+.3f}   highest notch y {min(ys):+.3f}")
    BOX, Z = (250, 20, 630, 320), 3
    im = Image.open(REF).convert("RGB").crop(BOX)
    im = im.resize((im.width * Z, im.height * Z), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    pts = [((REF_CX + u * REF_R - BOX[0]) * Z, (REF_CY + v * REF_R - BOX[1]) * Z) for u, v in prof]
    d.line(pts, fill=(255, 0, 255), width=3)
    im.save("out/trace/fringe_check.png")
    print("wrote out/trace/fringe_check.png")


def simplify(pts, tol):
    """Douglas-Peucker on the measured boundary, same as the silhouette got."""

    def walk(lo, hi):
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
        return [lo] if worst <= tol else walk(lo, at) + walk(at, hi)

    return walk(0, len(pts) - 1) + [len(pts) - 1]


def fit(pts, keep):
    """Least-squares control point per span, endpoints pinned.

    Two things that the silhouette's fit got away with and this data does not.
    The parameter runs on chord length rather than on the index of the sample,
    because a lock's edge is nearly vertical and dozens of samples pile up at
    almost the same x; indexed, they drag the control sideways and the curve
    leaves the data. And the control is clamped into the span's own bounding box,
    which is not a fudge: a quadratic never leaves the convex hull of its three
    points, so a control inside the box keeps the whole curve inside it.

    Without those, 12 of 26 controls came out beyond the measured range, one of
    them 0.36 head radii below the deepest point ever measured, and the fitted
    fringe hung spikes down into the eye that the canon does not draw.
    """
    segs = []
    for a, b in zip(keep, keep[1:]):
        p0, p2 = pts[a], pts[b]
        run = [0.0]
        for i in range(a + 1, b + 1):
            run.append(run[-1] + math.dist(pts[i - 1], pts[i]))
        total = run[-1] or 1.0
        num = np.zeros(2)
        den = 0.0
        for i in range(a + 1, b):
            t = run[i - a] / total
            w = 2 * (1 - t) * t
            res = np.array(pts[i]) - (1 - t) ** 2 * np.array(p0) - t**2 * np.array(p2)
            num += w * res
            den += w * w
        c = (num / den) if den > 1e-9 else (np.array(p0) + np.array(p2)) / 2
        xs = [q[0] for q in pts[a : b + 1]]
        ys = [q[1] for q in pts[a : b + 1]]
        segs.append(
            (
                (min(max(float(c[0]), min(xs)), max(xs)), min(max(float(c[1]), min(ys)), max(ys))),
                p2,
            )
        )
    return pts[keep[0]], segs
