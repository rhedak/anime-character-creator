"""Trace Satoko's chibi hair off the owner's isolated crop.

**The signal is the drawn black outline, not the alpha.** The crop's alpha is a
rough selection: parts of the page came through opaque, and the face opening's
edge is a staircase that does not follow her parting. The ink inside the crop is
the artist's own line and is exact wherever the selection is not.

Reading ink works here and did not on Satoshi's full drawing for one reason: a
crop of the hair alone has no brows and no eyes in it, and those are the only
other dark things on a face. So the furthest ink along a bearing is the mass's
outer edge and the nearest is the hairline, with nothing in between that could
be mistaken for either.

The two interior sweep lines are brown rather than black and fall well outside
the threshold, so they do not register as either boundary.
"""

from __future__ import annotations

import math
import sys

sys.path.insert(0, "out/trace")

import numpy as np
from PIL import Image

CROP = "ref/satoko-chibi-hair.png"
REF = "ref/satoko-chibi.jpg"
# Same fit as everywhere else: eye centre to drawn chin, 0.84 head radii at a
# build with no chin drop. Cross-checks on the eye half-separation, which comes
# to 0.459 r against our house 0.46.
CX, EYE_Y, CHIN_Y = 445.0, 362.0, 545.0
R = (CHIN_Y - EYE_Y) / 0.84
CY = EYE_Y - 0.16 * R

_crop = np.asarray(Image.open(CROP).convert("RGBA")).astype(int)
_ref = np.asarray(Image.open(REF).convert("RGB")).astype(int)
ALPHA = _crop[:, :, 3] > 128
# The drawn line. Tight enough that the brown sweep lines inside the hair, which
# run about 400 on the channel sum, are nowhere near it.
INK = (_crop[:, :, :3].sum(2) < 220) & ALPHA


def locate(x0=120, x1=260, y0=40, y1=180):
    """Where the crop sits in the reference, by least squared difference."""
    ys, xs = np.where(ALPHA)
    my, mx = int(np.median(ys)), int(xs.min()) + 30
    patch = _crop[my - 14 : my + 14, mx : mx + 90, :3]
    mask = ALPHA[my - 14 : my + 14, mx : mx + 90]
    best, at = None, None
    for oy in range(y0, y1):
        for ox in range(x0, x1):
            win = _ref[oy + my - 14 : oy + my + 14, ox + mx : ox + mx + 90]
            if win.shape[:2] != patch.shape[:2]:
                continue
            err = float((((win - patch) ** 2).sum(2) * mask).sum() / max(1, mask.sum()))
            if best is None or err < best:
                best, at = err, (ox, oy)
    return at, best


def _ink_at(ox, oy):
    """The crop's ink placed into reference coordinates."""
    full = np.zeros(_ref.shape[:2], dtype=bool)
    h, w = INK.shape
    full[oy : oy + h, ox : ox + w] = INK
    return full


def _ray(m, deg, lo=0.30, hi=2.30, step=0.002):
    """Every radius along a bearing where the ray is on ink, in head radii."""
    th = math.radians(deg)
    hits, r = [], lo
    while r < hi:
        x = int(round(CX + math.sin(th) * R * r))
        y = int(round(CY - math.cos(th) * R * r))
        if 0 <= y < m.shape[0] and 0 <= x < m.shape[1] and m[y, x]:
            hits.append(r)
        r += step
    return hits


def outer(offset, lo=-170, hi=171):
    """The mass's outer edge: the furthest ink along each bearing."""
    m = _ink_at(*offset)
    out = []
    for deg in range(lo, hi):
        hits = _ray(m, deg)
        if hits:
            out.append((float(deg), hits[-1]))
    return out


def inner(offset, lo=-115, hi=116):
    """The hairline: the nearest ink along each bearing, going out from the head
    centre. The centre sits inside the face opening at every bearing this covers,
    so the first line it meets is the one the hair is drawn against."""
    m = _ink_at(*offset)
    out = []
    for deg in range(lo, hi):
        hits = _ray(m, deg)
        if hits:
            out.append((float(deg), hits[0]))
    return out


def inner_tail(offset, side, top, bottom=1.70, step=0.004):
    """The inner edge of one fall below the cheek, as x per y.

    A radial sweep from the head centre cannot describe this stretch: it runs
    almost straight down, so a whole fall's worth of it falls between two
    bearings. Scanning rows instead is the natural parameterisation, and where
    the two meet they agree, because both are reading the same drawn line.
    """
    m = _ink_at(*offset)
    out = []
    y = top
    while y < bottom:
        py = int(round(CY + y * R))
        if 0 <= py < m.shape[0]:
            row = np.where(m[py])[0]
            cxp = CX
            near = row[row < cxp] if side < 0 else row[row > cxp]
            if len(near):
                px = near.max() if side < 0 else near.min()
                out.append(((px - CX) / R, y))
        y += step
    return out


def hairline(offset):
    """The whole inner boundary: up one fall, over the parting, down the other."""
    arc = inner(offset)
    pts = [(math.sin(math.radians(d)) * r, -math.cos(math.radians(d)) * r) for d, r in arc]
    left_top, right_top = pts[0][1], pts[-1][1]
    left = inner_tail(offset, -1, left_top)
    right = inner_tail(offset, +1, right_top)
    return [*reversed(left), *pts, *right]


if __name__ == "__main__":
    from PIL import ImageDraw

    at, err = locate()
    print(f"crop {ALPHA.shape[1]}x{ALPHA.shape[0]} placed at {at}, mean squared error {err:.0f}")
    o, i = outer(at), inner(at)
    print(f"outer: {len(o)} bearings, radius {min(r for _, r in o):.3f}..{max(r for _, r in o):.3f}")
    print(f"inner arc: {len(i)} bearings")
    hl = hairline(at)
    print(f"hairline: {len(hl)} points, y {min(y for _, y in hl):+.3f}..{max(y for _, y in hl):+.3f}")
    BOX, Z = (120, 40, 780, 700), 2
    im = Image.open(REF).convert("RGB").crop(BOX)
    im = im.resize((im.width * Z, im.height * Z), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    mass = [((CX + math.sin(math.radians(dg)) * R * r - BOX[0]) * Z,
             (CY - math.cos(math.radians(dg)) * R * r - BOX[1]) * Z) for dg, r in o]
    d.line(mass, fill=(255, 0, 255), width=3)
    hl = [((CX + x * R - BOX[0]) * Z, (CY + y * R - BOX[1]) * Z) for x, y in hairline(at)]
    d.line(hl, fill=(0, 190, 255), width=3)
    im.save("out/trace/satoko_check.png")
    print("wrote out/trace/satoko_check.png  magenta = mass, cyan = hairline")
