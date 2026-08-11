"""Trace Satoshi's realistic-build crop off `ref/satoshi-real.jpg` directly.

Same method `satoko_real.py` in this directory uses and for the same reason:
no isolated hair crop exists for this reference, so the signal is a
connected hair-colour region grown from a seed, not ink, which sidesteps
both eyebrow ink and the tunic's own outline sitting in the same radius
range the crop does. One seed was enough here, unlike Satoko's fall, which
needed one in the pale tips too: the crop's gold-to-pale boundary does not
fully disconnect the two tones the way her fall's fade line does.
"""

from __future__ import annotations

import math
from collections import deque

from PIL import Image

REF = "ref/satoshi-real.jpg"
CX, EYE_Y, CHIN_Y = 445.0, 176.4, 257.5
R = (CHIN_Y - EYE_Y) / 0.84
CY = EYE_Y - 0.16 * R

_im = Image.open(REF).convert("RGB")
W, H = _im.size
_p = _im.load()


def _is_hairish(px: tuple[int, int, int]) -> bool:
    r, g, b = px
    s = r + g + b
    greenish = g > r and g > b + 5
    near_black = s < 90
    return (not greenish) and (not near_black) and s > 250


_SEEDS = [(int(CX), int(CY - 0.7 * R))]


def _region() -> list[list[bool]]:
    seen = [[False] * W for _ in range(H)]
    q: deque[tuple[int, int]] = deque()
    for sx, sy in _SEEDS:
        if not seen[sy][sx]:
            seen[sy][sx] = True
            q.append((sx, sy))
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and not seen[ny][nx] and _is_hairish(_p[nx, ny]):
                seen[ny][nx] = True
                q.append((nx, ny))
    return seen


_MASK: list[list[bool]] | None = None


def mask() -> list[list[bool]]:
    global _MASK
    if _MASK is None:
        _MASK = _region()
    return _MASK


def _ray(deg: float, lo: float = 0.20, hi: float = 1.80, step: float = 0.004) -> list[float]:
    m = mask()
    th = math.radians(deg)
    hits, r = [], lo
    while r < hi:
        x = int(round(CX + math.sin(th) * R * r))
        y = int(round(CY - math.cos(th) * R * r))
        if 0 <= y < H and 0 <= x < W and m[y][x]:
            hits.append(r)
        r += step
    return hits


def outer(lo: int = -170, hi: int = 171) -> list[tuple[float, float]]:
    out = []
    for deg in range(lo, hi):
        hits = _ray(deg)
        if hits:
            out.append((float(deg), hits[-1]))
    return out


def inner(lo: int = -115, hi: int = 116) -> list[tuple[float, float]]:
    out = []
    for deg in range(lo, hi):
        hits = _ray(deg)
        if hits:
            out.append((float(deg), hits[0]))
    return out


def polar(deg: float, r: float) -> tuple[float, float]:
    a = math.radians(deg)
    return (math.sin(a) * r, -math.cos(a) * r)


def inner_tail(
    side: int, top: float, bottom: float = 1.20, step: float = 0.004
) -> list[tuple[float, float]]:
    m = mask()
    out = []
    y = top
    while y < bottom:
        py = int(round(CY + y * R))
        if 0 <= py < H:
            row = [x for x in range(W) if m[py][x]]
            near = [x for x in row if x < CX] if side < 0 else [x for x in row if x > CX]
            if near:
                px = max(near) if side < 0 else min(near)
                out.append(((px - CX) / R, y))
        y += step
    return out


def hairline() -> list[tuple[float, float]]:
    arc = inner()
    pts = [polar(d, r) for d, r in arc]
    left_top, right_top = pts[0][1], pts[-1][1]
    left = inner_tail(-1, left_top)
    right = inner_tail(+1, right_top)
    return [*reversed(left), *pts, *right]


def marks(prof: list[tuple[float, float]], tol: float = 0.030) -> list[tuple[float, float]]:
    pts = [polar(d, r) for d, r in prof]

    def simplify(lo: int, hi: int) -> list[int]:
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


def fit_chain(
    prof: list[tuple[float, float]], mk: list[tuple[float, float]]
) -> tuple[tuple[float, float], list[tuple[tuple[float, float], tuple[float, float]]]]:
    by_deg = {d: r for d, r in prof}
    start = polar(*mk[0])
    segs = []
    for (d0, r0), (d1, r1) in zip(mk, mk[1:]):
        p0, p2 = polar(d0, r0), polar(d1, r1)
        lo, hi = (d0, d1) if d0 < d1 else (d1, d0)
        pts = [(d, by_deg[d]) for d in range(int(lo) + 1, int(hi)) if d in by_deg]
        num = [0.0, 0.0]
        den = 0.0
        for d, r in pts:
            t = (d - d0) / (d1 - d0)
            w = 2 * (1 - t) * t
            qx, qy = polar(d, r)
            resx = qx - (1 - t) ** 2 * p0[0] - t**2 * p2[0]
            resy = qy - (1 - t) ** 2 * p0[1] - t**2 * p2[1]
            num[0] += w * resx
            num[1] += w * resy
            den += w * w
        c = (num[0] / den, num[1] / den) if den > 1e-9 else ((p0[0] + p2[0]) / 2, (p0[1] + p2[1]) / 2)
        segs.append((c, p2))
    return start, segs


def xy_simplify(pts: list[tuple[float, float]], tol: float) -> list[int]:
    def walk(lo: int, hi: int) -> list[int]:
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


def xy_fit(
    pts: list[tuple[float, float]], keep: list[int]
) -> tuple[tuple[float, float], list[tuple[tuple[float, float], tuple[float, float]]]]:
    segs = []
    for a, b in zip(keep, keep[1:]):
        p0, p2 = pts[a], pts[b]
        run = [0.0]
        for i in range(a + 1, b + 1):
            run.append(run[-1] + math.dist(pts[i - 1], pts[i]))
        total = run[-1] or 1.0
        num = [0.0, 0.0]
        den = 0.0
        for i in range(a + 1, b):
            t = run[i - a] / total
            w = 2 * (1 - t) * t
            resx = pts[i][0] - (1 - t) ** 2 * p0[0] - t**2 * p2[0]
            resy = pts[i][1] - (1 - t) ** 2 * p0[1] - t**2 * p2[1]
            num[0] += w * resx
            num[1] += w * resy
            den += w * w
        cx, cy = (num[0] / den, num[1] / den) if den > 1e-9 else ((p0[0] + p2[0]) / 2, (p0[1] + p2[1]) / 2)
        xs = [q[0] for q in pts[a : b + 1]]
        ys = [q[1] for q in pts[a : b + 1]]
        cx = min(max(cx, min(xs)), max(xs))
        cy = min(max(cy, min(ys)), max(ys))
        segs.append(((cx, cy), p2))
    return pts[keep[0]], segs


if __name__ == "__main__":
    from PIL import ImageDraw

    o = outer()
    hl = hairline()
    print(f"outer: {len(o)} bearings, radius {min(r for _, r in o):.3f}..{max(r for _, r in o):.3f}")
    print(f"hairline: {len(hl)} points, y {min(y for _, y in hl):+.3f}..{max(y for _, y in hl):+.3f}")

    BOX, Z = (250, 0, 640, 500), 2
    im = _im.crop(BOX)
    im = im.resize((im.width * Z, im.height * Z), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    mass_pts = [
        ((CX + math.sin(math.radians(dg)) * R * r - BOX[0]) * Z, (CY - math.cos(math.radians(dg)) * R * r - BOX[1]) * Z)
        for dg, r in o
    ]
    d.line(mass_pts, fill=(255, 0, 255), width=3)
    hl_pts = [((CX + x * R - BOX[0]) * Z, (CY + y * R - BOX[1]) * Z) for x, y in hl]
    d.line(hl_pts, fill=(0, 190, 255), width=3)
    im.save("harness/trace/real/satoshi_real_check.png")
    print("wrote harness/trace/real/satoshi_real_check.png")

    for tol in (0.020, 0.035, 0.055):
        start, segs = fit_chain(o, marks(o, tol))
        print(f"mass fit tol {tol}: {len(segs)} segments")
    for tol in (0.010, 0.018, 0.030):
        keep = xy_simplify(hl, tol)
        _, hg = xy_fit(hl, keep)
        print(f"hairline fit tol {tol}: {len(hg)} segments")

    print("\n--- emit (mass tol 0.030, hairline tol 0.018) ---\n")
    start, segs = fit_chain(o, marks(o, 0.030))
    print(f"_CROP_REAL_START: Point = ({start[0]:.3f}, {start[1]:.3f})")
    print("_CROP_REAL_EDGE: list[Segment] = [")
    for (cx, cy), (ex, ey) in segs:
        print(f"    (({cx:6.3f}, {cy:6.3f}), ({ex:6.3f}, {ey:6.3f})),")
    print("]")
    print(f"# {len(segs)} segments")

    keep = xy_simplify(hl, 0.018)
    hs, hg = xy_fit(hl, keep)
    print(f"\n_CROP_REAL_LINE_START: Point = ({hs[0]:.3f}, {hs[1]:.3f})")
    print("_CROP_REAL_LINE: list[Segment] = [")
    for (cx, cy), (ex, ey) in hg:
        print(f"    (({cx:6.3f}, {cy:6.3f}), ({ex:6.3f}, {ey:6.3f})),")
    print("]")
    print(f"# {len(hg)} segments")
