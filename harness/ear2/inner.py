"""The inner strokes on their own, by eroding the silhouette to strip the rim.

Two earlier readings failed. Connectivity does not separate them, because the
fold runs into the rim at the top and the whole ear is one piece of ink. Taking
the second run of ink along each row does not either: the canon draws *two*
inner strokes, an upper crescent and a lower hook, and a row-scan hops between
them and back onto the rim, which comes out as a zigzag that is on none of them.

Eroding works because the rim is the boundary of the shape by definition, so a
few pixels in from the silhouette's edge there is nothing left of it, while a
stroke drawn across the middle survives whole.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("eartrace", HERE / "trace.py")
T = importlib.util.module_from_spec(spec)
sys.modules["eartrace"] = T
spec.loader.exec_module(T)

ERODE = 8

ink, ox, oy, W, H = T.masks()
sil = T.filled(ink, W, H)


def erode(m, k):
    cur = m
    for _ in range(k):
        nxt = [[False] * W for _ in range(H)]
        for y in range(1, H - 1):
            for x in range(1, W - 1):
                if cur[y][x] and cur[y - 1][x] and cur[y + 1][x] and cur[y][x - 1] and cur[y][x + 1]:
                    nxt[y][x] = True
        cur = nxt
    return cur


core = erode(sil, ERODE)
inner = [[ink[y][x] and core[y][x] for x in range(W)] for y in range(H)]


def components(m):
    lab = [[0] * W for _ in range(H)]
    n = 0
    for sy in range(H):
        for sx in range(W):
            if not m[sy][sx] or lab[sy][sx]:
                continue
            n += 1
            stack = [(sx, sy)]
            while stack:
                x, y = stack.pop()
                if lab[y][x] or not m[y][x]:
                    continue
                lab[y][x] = n
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < W and 0 <= ny < H and not lab[ny][nx] and m[ny][nx]:
                            stack.append((nx, ny))
    return lab, n


lab, n = components(inner)
sizes = sorted(
    ((sum(row.count(i) for row in lab), i) for i in range(1, n + 1)), reverse=True
)
print(f"{n} inner strokes after eroding {ERODE}px; sizes {[s for s, _ in sizes[:6]]}")
for s, i in sizes[:4]:
    xs = [x for y in range(H) for x in range(W) if lab[y][x] == i]
    ys = [y for y in range(H) for x in range(W) if lab[y][x] == i]
    print(f"  stroke {s:4d}px  x {min(xs)}..{max(xs)}  y {min(ys)}..{max(ys)}")

z = 6
box = (ox - 10, oy - 10, ox + W + 10, oy + H + 10)
im = Image.open(T.SHEET).convert("RGB").crop(box)
im = im.resize((im.width * z, im.height * z), Image.LANCZOS)
d = ImageDraw.Draw(im)
COLORS = [(255, 0, 255), (0, 200, 255), (255, 190, 0), (0, 255, 120)]
for k, (_, i) in enumerate(sizes[:4]):
    for y in range(H):
        for x in range(W):
            if lab[y][x] == i:
                px, py = (ox + x - box[0]) * z, (oy + y - box[1]) * z
                d.rectangle([px, py, px + z - 1, py + z - 1], fill=COLORS[k])
im.save(HERE / "inner.png")
print("wrote out/ear2/inner.png")


def bfs(seed, pts):
    """Geodesic distance from a pixel, over the stroke only."""
    dist = {seed: 0}
    frontier = [seed]
    while frontier:
        nxt = []
        for x, y in frontier:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = (x + dx, y + dy)
                    if q in pts and q not in dist:
                        dist[q] = dist[(x, y)] + 1
                        nxt.append(q)
        frontier = nxt
    return dist


# The stroke's centreline, ordered. Its far end is found the way a tree's
# diameter is: walk to the furthest pixel from anywhere, then from there. Then
# every pixel at the same geodesic distance is one cross-section of the stroke,
# and its centroid is the line the artist drew.
big = sizes[0][1]
pts = {(x, y) for y in range(H) for x in range(W) if lab[y][x] == big}
a = max(bfs(next(iter(pts)), pts).items(), key=lambda kv: kv[1])[0]
dist = bfs(a, pts)
bins: dict[int, list[tuple[int, int]]] = {}
for q, dd in dist.items():
    bins.setdefault(dd, []).append(q)
line = [
    (sum(q[0] for q in v) / len(v), sum(q[1] for q in v) / len(v))
    for _, v in sorted(bins.items())
]
print(f"\ncentreline: {len(line)} points, {len(pts)}px of stroke")

rows = [y for y in range(H) if any(sil[y])]
y0, y1 = rows[0], rows[-1]


def span(y: int) -> tuple[int, int]:
    xs = [x for x in range(W) if sil[y][x]]
    return xs[0], xs[-1]


top = (span(y0)[1], y0)
bot = (span(y1)[1], y1)
widest = max(
    span(y)[1] - (top[0] + (bot[0] - top[0]) * (y - y0) / (y1 - y0)) for y in range(y0, y1 + 1)
)
norm = []
for x, y in line:
    f = (y - y0) / (y1 - y0)
    norm.append((f, (x - (top[0] + (bot[0] - top[0]) * f)) / widest))
# Run it from the top down, whichever end the walk started at.
if norm[0][0] > norm[-1][0]:
    norm.reverse()

# Same two-stroke-width rule the rim got, against the crease's own weight: it
# is drawn at 0.55 of the outline's, so its floor is lower.
import math  # noqa: E402

HEIGHT_R, WIDE_R = 0.590, 0.213
for tol in (0.010, 0.020, 0.035, 0.060, 0.090):
    keep = T.simplify(norm, tol)
    anch = [(norm[i][0] * HEIGHT_R, norm[i][1] * WIDE_R) for i in keep]
    ch = [math.dist(anch[i], anch[i + 1]) for i in range(len(anch) - 1)]
    print(f"  tol {tol:.3f} -> {len(keep) - 1:2d} segments, shortest {min(ch):.3f} r,"
          f" under two crease widths: {T._thin([c / 0.55 for c in ch])}")
FTOL = 0.090
start, segs = T.fit(norm, T.simplify(norm, FTOL))
# Normalised across the fold's own width as well as its height. The canon's
# fold reaches a third of the ear's stand-out *left* of the attach chord,
# because the canon's ear overlaps the cheek and ours cannot: our chord is the
# skull, and the skull bulges out past it in the middle. So the offsets are
# rescaled to 0..1 across the fold's own extent and the code decides which band
# of the ear that lands in, rather than the trace insisting on a place that is
# not inside our ear at all.
lo = min([start[1]] + [q[1] for seg in segs for q in seg])
hi = max([start[1]] + [q[1] for seg in segs for q in seg])
print(f"\nfold offsets ran {lo:+.3f}..{hi:+.3f} of the ear's stand-out, rescaled to 0..1")


def u(pt):
    return (pt[0], (pt[1] - lo) / (hi - lo))


start = u(start)
segs = [(u(c), u(e)) for c, e in segs]
print("\n_EAR_FOLD_START = (%.3f, %.3f)" % start)
print("_EAR_FOLD = [")
for c, e in segs:
    print("    ((%.3f, %.3f), (%.3f, %.3f))," % (c[0], c[1], e[0], e[1]))
print("]")


def place(f: float, o: float) -> tuple[float, float]:
    x = top[0] + (bot[0] - top[0]) * f + o * widest
    return ((ox + x - box[0]) * z, (oy + y0 + (y1 - y0) * f - box[1]) * z)


walk = [place(*start)]
prev = start
for c, e in segs:
    for i in range(1, 21):
        t = i / 20
        walk.append(
            place(
                (1 - t) ** 2 * prev[0] + 2 * (1 - t) * t * c[0] + t**2 * e[0],
                (1 - t) ** 2 * prev[1] + 2 * (1 - t) * t * c[1] + t**2 * e[1],
            )
        )
    prev = e
d.line(walk, fill=(0, 0, 0), width=3)
im.save(HERE / "inner.png")
print("wrote out/ear2/inner.png with the fitted centreline in black")
