"""Trace Satoko's realistic-build hair off `ref/satoko-real.jpg` directly.

Unlike the chibi trace (`../satoko.py`), there is no isolated hair crop for
this reference, so the signal here is a **connected hair-colour region**
grown from a seed in the gold crown, not ink. That sidesteps both hazards an
ink sweep would hit on the full drawing: eyebrows are ink too, and the body's
own outline sits within the same radius range the hair fall does, so a
"furthest ink" sweep risks jumping from the hair's edge to the tunic's.
Colour cannot confuse either, since neither eyebrow nor tunic is close to
gold or to the hair's pale tip tone, and the region is grown rather than
thresholded pixel by pixel so it cannot leak across the black outline that
already separates hair from whatever is next to it.

Two seeds, not one: the gold crown and a pale tip on each fall. The two-tone
fade boundary the shipped chibi trace also has is itself a drawn line, thin
enough to be a barrier the fill will not cross, so the gold region and the
pale region are two connected components that meet only through the ink
between them. Seeding both sides once each is cheaper than trying to make the
mask bridge a line it should not bridge.
"""

from __future__ import annotations

import math
from collections import deque

from PIL import Image

REF = "ref/satoko-real.jpg"
# Eye centre to drawn chin, 0.84 head radii at a build with no chin drop, the
# same fit every other trace in this directory uses. EYE_Y is the centroid of
# a saturated-green colour match on the iris, not eyeballed: the `eyes` probe
# tool finds only the highlight dot on this art (a known failure recorded in
# `.claude/skills/gap-analysis/PITFALLS.md`), and reading ink at centre column
# is unreliable this high up the face, so colour is the only clean signal.
# CHIN_Y is the midpoint of the dark run where the jaw's own outline crosses
# the centre column, found the same way `_belt` gap analysis needed a chin
# line: scan brightness at cx, band the search to miss the mouth and the
# collar's own V.
CX, EYE_Y, CHIN_Y = 439.0, 156.9, 235.5
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


_SEEDS = [(int(CX), int(CY - 0.7 * R)), (354, 226), (523, 226)]


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


def _ray(deg: float, lo: float = 0.20, hi: float = 2.20, step: float = 0.004) -> list[float]:
    """Every radius along a bearing where the ray is inside the hair region."""
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
    """The mass's outer edge: the furthest point in the region along each
    bearing, same convention as `../satoko.py`'s chibi trace."""
    out = []
    for deg in range(lo, hi):
        hits = _ray(deg)
        if hits:
            out.append((float(deg), hits[-1]))
    return out


def inner(lo: int = -115, hi: int = 116) -> list[tuple[float, float]]:
    """The hairline: the nearest point in the region along each bearing,
    going out from the head centre. Only meaningful on the front arc, where
    the ray starts inside the face rather than inside the hair itself."""
    out = []
    for deg in range(lo, hi):
        hits = _ray(deg)
        if hits:
            out.append((float(deg), hits[0]))
    return out


def inner_tail(
    side: int, top: float, bottom: float = 1.60, step: float = 0.004
) -> list[tuple[float, float]]:
    """The inner edge of one fall below the cheek, as x per y, same technique
    `../satoko.py` uses: a radial sweep cannot describe a stretch that runs
    almost straight down, so this scans rows instead. `side` is -1 for the
    left fall (in image terms, screen-left) and +1 for the right."""
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
    """The whole inner boundary in xy (head-radius units): up one fall, over
    the parting, down the other, matching `../satoko.py`'s `hairline()`."""
    arc = inner()
    pts = [polar(d, r) for d, r in arc]
    left_top, right_top = pts[0][1], pts[-1][1]
    left = inner_tail(-1, left_top)
    right = inner_tail(+1, right_top)
    return [*reversed(left), *pts, *right]


def polar(deg: float, r: float) -> tuple[float, float]:
    a = math.radians(deg)
    return (math.sin(a) * r, -math.cos(a) * r)


def marks(prof: list[tuple[float, float]], tol: float = 0.030) -> list[tuple[float, float]]:
    """Simplify a (degree, radius) profile to a handful of points,
    Douglas-Peucker in xy. Ported from `../fit.py` without numpy, since it is
    not installed in this project's own venv; the harness scripts that import
    it directly need it pip-installed ad hoc first."""
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
    """Least-squares control point per segment, endpoints pinned to the marks."""
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
    """Douglas-Peucker on a plain xy chain, ported from `../fringe.py`'s
    `simplify`, for the hairline: it runs near-vertical down each fall, where
    the degree-indexed `marks` above would bunch dozens of samples at nearly
    the same x and is the wrong parameterisation."""

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
    """Least-squares control point per span, parameterised on chord length
    and clamped into the span's own bounding box, ported from
    `../fringe.py`'s `fit` for the same reason it needed both there."""
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

    BOX, Z = (250, 0, 640, 620), 2
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
    im.save("harness/trace/real/satoko_real_check.png")
    print("wrote harness/trace/real/satoko_real_check.png  magenta = mass, cyan = hairline")

    for tol in (0.020, 0.035, 0.055):
        start, segs = fit_chain(o, marks(o, tol))
        print(f"mass fit tol {tol}: {len(segs)} segments")
    for tol in (0.010, 0.018, 0.030):
        keep = xy_simplify(hl, tol)
        _, hg = xy_fit(hl, keep)
        print(f"hairline fit tol {tol}: {len(hg)} segments")

    # Emit at the tolerances chosen after looking at satoko_real_check.png:
    # a segment count close to the chibi trace's own (18 mass, 8 hairline).
    print("\n--- emit ---\n")
    start, segs = fit_chain(o, marks(o, 0.035))
    print(f"_LONG_REAL_EDGE_START: Point = ({start[0]:.3f}, {start[1]:.3f})")
    print("_LONG_REAL_EDGE: list[Segment] = [")
    for (cx, cy), (ex, ey) in segs:
        print(f"    (({cx:6.3f}, {cy:6.3f}), ({ex:6.3f}, {ey:6.3f})),")
    print("]")

    keep = xy_simplify(hl, 0.018)
    hs, hg = xy_fit(hl, keep)
    print(f"\n_LONG_REAL_LINE_START: Point = ({hs[0]:.3f}, {hs[1]:.3f})")
    print("_LONG_REAL_LINE: list[Segment] = [")
    for (cx, cy), (ex, ey) in hg:
        print(f"    (({cx:6.3f}, {cy:6.3f}), ({ex:6.3f}, {ey:6.3f})),")
    print("]")
