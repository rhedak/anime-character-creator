"""The lower body, canon against ours, at both builds and matched in height.

Normalised on the belt-to-floor span rather than on the whole figure, because
that is the part being judged: matching total height would size the tile by the
hair, which stands differently at each build and would leave the two trouser
legs at different scales.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "src")

from PIL import Image, ImageDraw  # noqa: E402

from anime_character_creator import character as C  # noqa: E402
from anime_character_creator.presets import PRESETS  # noqa: E402
from anime_character_creator.skeleton import BUILDS, build_skeleton  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def ours(build: str) -> tuple[int, int]:
    """Our own belt bottom and floor, from the skeleton rather than measured.

    Pasting the rows in was tried and went stale the first time the shape moved:
    they came off a scratch render that no longer exists, and the tile silently
    cropped the hips off, which is the part the change is about. The PNG is
    exported at twice the SVG canvas, hence the doubling.
    """
    p = PRESETS["satoshi"]
    sk = build_skeleton(heads=BUILDS[build], frame=p.frame)
    belt_y, belt_h = C._belt_band(sk)
    return round((belt_y + belt_h) * 2), round(sk.foot_y * 2)


# (label, file, belt bottom y, floor y). The canon's two are measured, by
# `measure.py`; ours come off the skeleton.
SHOTS = [
    ("canon chibi", "ref/satoshi-chibi.jpg", 792, 1141),
    ("ours chibi", "ref-out/satoshi.png", *ours("chibi")),
    ("canon adult", "ref/satoshi.png", 530, 1117),
    ("ours adult", "ref-out/satoshi_real.png", *ours("realistic")),
]

H = 460
tiles = []
for label, name, belt, floor in SHOTS:
    im = Image.open(ROOT / name).convert("RGB")
    w, _ = im.size
    span = floor - belt
    # A margin of a fifth of the span above the belt, so the tunic's hem and the
    # belt itself are both in frame: half the point is where the two garments
    # meet.
    top = round(belt - span * 0.22)
    # Width taken as a multiple of that same span, so every tile ends up the
    # same aspect and one height normalises all four. A fraction of the canvas
    # does not: the canon's sheets and ours frame the figure differently, and at
    # the chibi it cropped the hips off, which is the part being looked at.
    keep = round(span * 1.5)
    crop = im.crop(((w - keep) // 2, top, (w + keep) // 2, floor + round(span * 0.04)))
    k = H / crop.height
    tiles.append((label, crop.resize((round(crop.width * k), H), Image.LANCZOS)))

pad, bar = 10, 22
W = sum(t.width for _, t in tiles) + pad * (len(tiles) + 1)
sheet = Image.new("RGB", (W, H + bar + pad * 2), "white")
d = ImageDraw.Draw(sheet)
x = pad
for label, t in tiles:
    sheet.paste(t, (x, pad + bar))
    d.text((x + 4, pad + 4), label, fill="black")
    x += t.width + pad
sheet.save(ROOT / "out/trousers/see.png")
print("wrote out/trousers/see.png", sheet.size)
