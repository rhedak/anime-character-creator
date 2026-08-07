"""Read the fringe's blades the way the owner's manual crop shows them.

Their crop isolates the blades against nothing, which makes the point that the
gaps between blades are deep and narrow and sealed by ink where two blades
meet. The connected-forehead reading cannot enter a sealed gap, so it comes out
smooth. This reads the other way round: the first skin going *down* from inside the
crown, on each column, which does not care whether that skin is joined to the
rest of the forehead.

**It does not find the fringe's edge.** It finds the gold-to-pale boundary,
because the transition band between them runs about +40 on red minus blue at
sum 650 and passes any skin test loose enough to hold the forehead together.
That is a sixth way of missing this edge, and the reason is the same one every
time: on this JPEG the canon's pale tips sit colorimetrically between its gold
and its skin, so no threshold has all three on the right side of it.

Kept because what it does find is worth having. **This is the tone boundary**,
the line the per-lock `tip_edge` regions will need, traced and validated. It is
the right tool pointed at the wrong question.
"""

from __future__ import annotations

import sys

sys.path.insert(0, "out/trace")

import numpy as np
from PIL import Image
from fringe import _SKINISH, REF, REF_CX, REF_CY, REF_R

_a = np.asarray(Image.open(REF).convert("RGB")).astype(int)


def fringe_at(u: float, top: float = -0.62, bottom: float = -0.02, step: float = 0.002,
              need: float = 0.020):
    """First skin below the crown on this column, needing a run to count.

    The run is what rejects a single pale pixel inside a blade. It is short,
    0.02 head radii, because a sealed gap is only a little wider than that and a
    longer requirement would step over the very thing this is for.
    """
    x = int(round(REF_CX + u * REF_R))
    if not 0 <= x < _SKINISH.shape[1]:
        return None
    run, v = 0.0, top
    while v < bottom:
        y = int(round(REF_CY + v * REF_R))
        if 0 <= y < _SKINISH.shape[0] and _SKINISH[y, x]:
            run += step
            if run >= need:
                return v - run + step
        else:
            run = 0.0
        v += step
    return None


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
    ys = [v for _, v in prof]
    print(f"{len(prof)} columns; x {prof[0][0]:+.2f}..{prof[-1][0]:+.2f}; "
          f"y {min(ys):+.3f}..{max(ys):+.3f}")
    BOX, Z = (300, 60, 590, 260), 4
    im = Image.open(REF).convert("RGB").crop(BOX)
    im = im.resize((im.width * Z, im.height * Z), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    pts = [((REF_CX + u * REF_R - BOX[0]) * Z, (REF_CY + v * REF_R - BOX[1]) * Z) for u, v in prof]
    d.line(pts, fill=(255, 0, 255), width=3)
    im.save("out/trace/fringe2_check.png")
    print("wrote out/trace/fringe2_check.png")
