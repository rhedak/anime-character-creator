"""Outer layers over a bust (`docs/tunic-bust-plan.md`, outer layers): Kyoko's
open coat and Reika's robe front, the two parametric garments that did not
answer the bust. Variants for the owner to pick from, set through the module's
strength constants (zero draws each as before):

- before;
- the chosen: the coat's front edges bowing out by the tunic's full drape
  (`_bust_bulge`), the robe carrying the tunic's line under the breast it
  covers at 0.6 of its weight (`_bust_fold`).

Each tile is the chest at 4x beside the whole figure at tile size. Writes
`out/bare/outer_layers.png`.
"""

import io
import os

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

NAMES = ("kyoko", "reika")
# (label, coat bow, robe line). The robe's diagonal bow, tried at 0.5 and 1.0
# in the first round, kinked and then wobbled, and was taken out of the code
# (`docs/bare-body-status.md`); the owner asked for the robe's line to be the
# tunic's whole curve, lighter, and it is `_bust_fold` now.
VARIANTS = (
    ("before", 0.0, 0.0),
    ("chosen: coat bow 1.0, robe line 0.6", 1.0, 0.6),
)


def render(name: str, scale: float) -> tuple[Image.Image, c.Skeleton]:
    p = PRESETS[name]
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="#ffffff")
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=scale))).convert("RGB"), sk


def tile(name: str) -> Image.Image:
    big, sk = render(name, 4)
    s, r, cx = 4, sk.head_r * 4, sk.head_cx * 4
    chest = big.crop((int(cx - 1.1 * r), int(sk.shoulder_y * s - 0.1 * r), int(cx + 1.1 * r), int(sk.waist_y * s + 0.4 * r)))
    small, _ = render(name, 1)
    small = small.crop((int(sk.head_cx - 1.7 * sk.head_r), 0, int(sk.head_cx + 1.7 * sk.head_r), small.height))
    out = Image.new("RGB", (chest.width + small.width + 8, max(chest.height, small.height)), (230, 230, 230))
    out.paste(chest, (0, 0))
    out.paste(small, (chest.width + 8, 0))
    return out


def main() -> None:
    os.makedirs("out/bare", exist_ok=True)
    saved = (c._COAT_BUST_BOW, c._ROBE_BUST_LINE)
    rows = []
    try:
        for label, coat, line in VARIANTS:
            c._COAT_BUST_BOW, c._ROBE_BUST_LINE = coat, line
            rows.append((label, [tile(n) for n in NAMES]))
    finally:
        c._COAT_BUST_BOW, c._ROBE_BUST_LINE = saved
    pad, head = 8, 20
    tw = max(t.width for _, ts in rows for t in ts)
    th = max(t.height for _, ts in rows for t in ts)
    sheet = Image.new("RGB", (pad + len(NAMES) * (tw + pad), pad + len(rows) * (th + head + pad)), (200, 200, 200))
    d = ImageDraw.Draw(sheet)
    y = pad
    for label, tiles in rows:
        d.text((pad, y + 4), label + "   (kyoko, reika)", fill=(0, 0, 0))
        x = pad
        for t in tiles:
            sheet.paste(t, (x, y + head))
            x += tw + pad
        y += th + head + pad
    sheet.save("out/bare/outer_layers.png")
    print("out/bare/outer_layers.png", sheet.size)


if __name__ == "__main__":
    main()
