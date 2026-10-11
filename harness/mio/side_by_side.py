"""Hers and ours side by side, with a half-and-half blend (`docs/mio-plan.md`).

Left her composite, middle our render, right the two blended. Both are on white at the
same head scale and the same head centre (`compare.py`), so a difference of placement
shows as a double line in the blend.

    ./harness/run.sh harness/mio/side_by_side.py [crop ...]     # crops: see compare.CROPS
"""

import sys

from compare import CROPS, R, _SLENDER_HEAD_SCALE, ours, reference
from PIL import Image, ImageDraw

from anime_character_creator.presets import MIO


def run(crop, out):
    ref = reference()
    mine = ours(MIO, ref.size, r=R * _SLENDER_HEAD_SCALE)
    box = CROPS[crop]
    if box:
        ref, mine = ref.crop(box), mine.crop(box)
    w, h = ref.size
    top = 36
    s = Image.new("RGB", (w * 3, h + top), "white")
    for i, (label, im) in enumerate(
        (("reference", ref), ("ours", mine), ("blend", Image.blend(ref, mine, 0.5)))
    ):
        s.paste(im, (w * i, top))
        ImageDraw.Draw(s).text((w * i + 8, 10), label, fill="black")
    s.save(out)
    print(f"wrote {out} ({s.size[0]} x {s.size[1]})")


for crop in sys.argv[1:] or ["upper", "torso"]:
    run(crop, f"out/mio/side_{crop}.png")
