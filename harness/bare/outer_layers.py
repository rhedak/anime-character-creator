"""Outer layers over a bust (`docs/tunic-bust-plan.md`, outer layers): Kyoko's
open coat and Reika's robe front, the two parametric garments that did not
answer the bust. Variants for the owner to pick from, set through the module's
strength constants (zero draws each as before):

- now;
- bow 0.5: the coat's front edges and the robe's diagonal bow out by half the
  tunic's drape (`_bust_bulge`), the robe's side following the drape;
- bow 1.0: the same at the tunic's full drape;
- bow 0.5 and a faint line (robe only): a 0.6-stroke line under the breast
  the panel covers, its outer half.

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
VARIANTS = (
    ("now", 0.0, 0.0, 0.0),
    ("bow 0.5", 0.5, 0.5, 0.0),
    ("bow 1.0", 1.0, 1.0, 0.0),
    ("bow 0.5, faint line on the robe", 0.5, 0.5, 0.6),
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
    saved = (c._COAT_BUST_BOW, c._ROBE_BUST_BOW, c._ROBE_BUST_LINE)
    rows = []
    try:
        for label, coat, robe, line in VARIANTS:
            c._COAT_BUST_BOW, c._ROBE_BUST_BOW, c._ROBE_BUST_LINE = coat, robe, line
            rows.append((label, [tile(n) for n in NAMES]))
    finally:
        c._COAT_BUST_BOW, c._ROBE_BUST_BOW, c._ROBE_BUST_LINE = saved
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
