"""Her height against ours at one head scale (`docs/risa-plan.md`, M10): the top of the hair and
the sole, on her composite and on our render placed on it.

    ./harness/run.sh harness/risa/height_check.py
"""

import numpy as np
from compare import R, _SLENDER_HEAD_SCALE, ours, reference

from anime_character_creator.presets import RISA

ref = np.asarray(reference()).astype(int)
mine = np.asarray(ours(RISA, reference().size, r=R * _SLENDER_HEAD_SCALE)).astype(int)


def extent(a):
    ink = (a.sum(2) < 720)
    ys, xs = np.nonzero(ink)
    return ys.min(), ys.max(), xs.min(), xs.max()


for name, a in (("hers", ref), ("ours", mine)):
    top, bottom, left, right = extent(a)
    print(f"{name}: hair top {top}, sole {bottom}, height {bottom - top} px, x {left}..{right}")
