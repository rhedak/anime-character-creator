"""Trace the fringe off the owner's isolated crop.

`ref/satoshi-chibi-fringe.png` is the canon's fringe cut out of the chibi
reference, and it settles what five readings off the full drawing could not.
Not because of its alpha, which is a coarse outer selection with the gaps
between blades left as opaque white, but because of what it leaves *out*: there
are no brows and no eyes in it. On the full drawing the deepest ink in a column
is the brow, which is why reading the drawn line failed there. Here the deepest
ink in a column can only be the blade that made it.

The crop is located back in the reference by template match rather than by
eyeballing an offset, so the calibration is the reference's own.
"""

from __future__ import annotations

import sys

sys.path.insert(0, "out/trace")

import numpy as np
from PIL import Image

CROP = "ref/satoshi-chibi-fringe.png"
REF = "ref/satoshi-chibi.jpg"
# Same fit as everywhere else: eye centre to drawn chin, 0.84 head radii at a
# build with no chin drop. Confirmed independently by the eye half-separation
# coming to 0.465 r against our house 0.46.
CX, EYE_Y, CHIN_Y = 434.0, 380.0, 528.0
R = (CHIN_Y - EYE_Y) / 0.84
CY = EYE_Y - 0.16 * R

_crop = np.asarray(Image.open(CROP).convert("RGBA")).astype(int)
_ref = np.asarray(Image.open(REF).convert("RGB")).astype(int)
ALPHA = _crop[:, :, 3] > 128
# The blade's own outline. Nothing else in this crop is dark.
INK = (_crop[:, :, :3].sum(2) < 220) & ALPHA


def locate(x0=180, x1=310, y0=150, y1=300):
    """Where the crop sits in the reference, by least squared difference."""
    h, w = ALPHA.shape
    # a solid block of the crop, away from its edges, to match on
    ys, xs = np.where(ALPHA)
    my = int(np.median(ys))
    patch = _crop[my - 12 : my + 12, 40 : 40 + 120, :3]
    mask = ALPHA[my - 12 : my + 12, 40 : 40 + 120]
    best, at = None, None
    for oy in range(y0, y1):
        for ox in range(x0, x1):
            win = _ref[oy + my - 12 : oy + my + 12, ox + 40 : ox + 160]
            if win.shape[:2] != patch.shape[:2]:
                continue
            err = float((((win - patch) ** 2).sum(2) * mask).sum() / max(1, mask.sum()))
            if best is None or err < best:
                best, at = err, (ox, oy)
    return at, best, (h, w)


def profile(offset):
    """The blades' lower edge, per column, in head radii."""
    ox, oy = offset
    out = []
    for x in range(INK.shape[1]):
        col = np.where(INK[:, x])[0]
        if len(col) == 0:
            continue
        u = (ox + x - CX) / R
        v = (oy + int(col.max()) - CY) / R
        out.append((round(u, 4), v))
    return out


if __name__ == "__main__":
    from PIL import ImageDraw

    at, err, shape = locate()
    print(f"crop {shape[1]}x{shape[0]} placed at {at}, mean squared error {err:.0f}")
    prof = profile(at)
    ys = [v for _, v in prof]
    print(f"{len(prof)} columns; x {prof[0][0]:+.3f}..{prof[-1][0]:+.3f}; "
          f"y {min(ys):+.3f}..{max(ys):+.3f}")
    BOX, Z = (180, 120, 700, 460), 2
    im = Image.open(REF).convert("RGB").crop(BOX)
    im = im.resize((im.width * Z, im.height * Z), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    pts = [((CX + u * R - BOX[0]) * Z, (CY + v * R - BOX[1]) * Z) for u, v in prof]
    d.line(pts, fill=(255, 0, 255), width=3)
    im.save("out/trace/fringe3_check.png")
    print("wrote out/trace/fringe3_check.png")
