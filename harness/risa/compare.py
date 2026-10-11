"""Risa's reference against our render, at one head scale (`docs/risa-plan.md`, M2).

Calibrated the way `landmarks.py` is (centre (630, CY), R = 165 px per head
radius), our render is scaled so that its head radius is R and its head centre
lands on the reference's, then drawn beside the reference and blended over it.
Both on white. A body that matches shows the figure's edges landing on each
other in the blend; a body that does not shows two ghosts.

The body is the preset's own (`character.BODY_TYPES["tall_slender"]`, which was
fitted with this script). To try a number without touching `src/`, register a
profile under another name in `BODY_TYPES` here and put `body=` on the replace.

    ./harness/run.sh harness/risa/compare.py            # the whole figure
    ./harness/run.sh harness/risa/compare.py legs       # a crop
"""

import io
import sys

from dataclasses import replace

import cairosvg
import numpy as np
from PIL import Image

from anime_character_creator.character import (
    _SLENDER_HEAD_SCALE,
    BODY_TYPES,
    render_character,
    skeleton_for,
)
from anime_character_creator.presets import RISA

BASE = "ref-local/mio"
R = 165.0
CX = 630.0
CHIN = 399
CY = CHIN - 1.02 * R

CROPS = {
    "full": None,
    "upper": (330, 30, 930, 760),
    "head": (330, 30, 930, 560),
    "torso": (400, 380, 860, 960),
    "legs": (400, 820, 860, 1540),
}


def reference():
    im = Image.open(f"{BASE}/mio.png").convert("RGBA")
    bg = Image.new("RGBA", im.size, "white")
    bg.alpha_composite(im)
    return bg.convert("RGB")


def ours(p, size, r=R):
    """Our render with its head radius at `r` px and its head centre at the
    reference's, which sits `1.02 r` above her chin whatever `r` is."""
    sk = skeleton_for(p)
    f = r / sk.head_r
    cy = CHIN - 1.02 * r
    png = cairosvg.svg2png(bytestring=render_character(p, sk=sk).encode(), scale=f)
    fig = Image.open(io.BytesIO(png)).convert("RGBA")
    page = Image.new("RGBA", size, "white")
    page.alpha_composite(fig, (int(round(CX - sk.head_cx * f)), int(round(cy - sk.head_cy * f))))
    return page.convert("RGB")


def sheet(p, crop="full", out="out/risa/m2_compare.png"):
    ref = reference()
    mine = ours(p, ref.size, r=R * _SLENDER_HEAD_SCALE)
    box = CROPS[crop]
    if box:
        ref, mine = ref.crop(box), mine.crop(box)
    blend = Image.blend(ref, mine, 0.5)
    w, h = ref.size
    s = Image.new("RGB", (w * 3, h), "white")
    for i, im in enumerate((ref, mine, blend)):
        s.paste(im, (w * i, 0))
    s.save(out)
    print(f"wrote {out} ({s.size[0]} x {s.size[1]})")


def head_variants(scales=(1.0, 0.91, 0.85), crop="upper", out="out/risa/m2_heads.png"):
    # Always on the measured profile at the calibrated radius, whatever scale the
    # preset's own body carries, so the variants stay comparable.
    """The head-size decision: the same body in pixels under a head `s` times the
    calibrated one (`BodyProfile.head_scaled`), reference first, then each as a
    50% blend over the reference."""
    ref = reference()
    box = CROPS[crop]
    panels = [ref.crop(box)]
    for s in scales:
        measured = BODY_TYPES["tall_slender"].head_scaled(1 / _SLENDER_HEAD_SCALE)
        BODY_TYPES[f"tall_slender_{s}"] = measured.head_scaled(s)
        p = replace(RISA, body=f"tall_slender_{s}")
        mine = ours(p, ref.size, r=R * s)
        panels.append(Image.blend(ref, mine, 0.5).crop(box))
    w, h = panels[0].size
    sheet_im = Image.new("RGB", (w * len(panels), h), "white")
    for i, im in enumerate(panels):
        sheet_im.paste(im, (w * i, 0))
    sheet_im.save(out)
    print(f"wrote {out} ({sheet_im.size[0]} x {sheet_im.size[1]}), scales {scales}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "heads":
        head_variants()
        sys.exit()
    crop = sys.argv[1] if len(sys.argv) > 1 else "full"
    sheet(RISA, crop, f"out/risa/m2_{crop}.png")
