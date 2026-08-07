"""The line the canon draws inside the ear, traced the same way as the rim.

Connectivity does not separate it: the fold runs into the rim at the top, so the
whole ear is one piece of ink. What does separate it is position along a row.
Scanning in from the outside, a row crosses the rim, then skin, then the fold,
then skin again, so the fold is the second run of ink from the right and its
middle is the stroke's own line.

Rows where there is no second run are where the fold has ended, and they are
dropped rather than filled in: a fold that ran the ear's whole height would
close into a second outline and read as a hole rather than as a turn of rim.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("eartrace", HERE / "trace.py")
T = importlib.util.module_from_spec(spec)
sys.modules["eartrace"] = T
spec.loader.exec_module(T)


def runs(row: list[bool]) -> list[tuple[int, int]]:
    out, start = [], None
    for x, on in enumerate(row):
        if on and start is None:
            start = x
        elif not on and start is not None:
            out.append((start, x - 1))
            start = None
    if start is not None:
        out.append((start, len(row) - 1))
    return out


ink, ox, oy, W, H = T.masks()
sil = T.filled(ink, W, H)
rows = [y for y in range(H) if any(sil[y])]
y0, y1 = rows[0], rows[-1]


def span(y: int) -> tuple[int, int]:
    xs = [x for x in range(W) if sil[y][x]]
    return xs[0], xs[-1]


top = (span(y0)[1], y0)
bot = (span(y1)[1], y1)
widest = max(span(y)[1] - (top[0] + (bot[0] - top[0]) * (y - y0) / (y1 - y0)) for y in range(y0, y1 + 1))

pts = []
for y in range(y0, y1 + 1):
    r = runs(ink[y])
    if len(r) < 2:
        continue
    a, b = r[-2]
    mid = (a + b) / 2
    f = (y - y0) / (y1 - y0)
    chord_x = top[0] + (bot[0] - top[0]) * f
    pts.append((f, (mid - chord_x) / widest))

print(f"fold traced on {len(pts)} of {y1 - y0 + 1} rows, "
      f"y {pts[0][0]:.2f}..{pts[-1][0]:.2f} of the ear's height")
for tol in (0.010, 0.020, 0.035, 0.060, 0.090):
    keep = T.simplify(pts, tol)
    print(f"  tol {tol:.3f} -> {len(keep) - 1} segments")

TOL = 0.035
start, segs = T.fit(pts, T.simplify(pts, TOL))
print("\n_EAR_FOLD_START = (%.3f, %.3f)" % start)
print("_EAR_FOLD = [")
for c, e in segs:
    print("    ((%.3f, %.3f), (%.3f, %.3f))," % (c[0], c[1], e[0], e[1]))
print("]")

box = (ox - 30, oy - 30, ox + W + 30, oy + H + 30)
z = 6
im = Image.open(T.SHEET).convert("RGB").crop(box)
im = im.resize((im.width * z, im.height * z), Image.LANCZOS)
d = ImageDraw.Draw(im)


def place(f: float, o: float) -> tuple[float, float]:
    x = top[0] + (bot[0] - top[0]) * f + o * widest
    y = y0 + (y1 - y0) * f
    return ((ox + x - box[0]) * z, (oy + y - box[1]) * z)


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
d.line(walk, fill=(0, 200, 255), width=3)
im.save(HERE / "fold.png")
print("\nwrote out/ear2/fold.png")
