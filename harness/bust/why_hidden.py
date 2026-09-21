"""Why the bust sweep looks flat: the arms cover exactly where a bust would be.

Three columns at `bust = 0` and at `bust = 1.0`: the figure as it renders, the
tunic on its own with the arms taken away, and the tunic with the arms laid
back over it at a third opacity so the overlap is visible.

The middle column is the point. The bulge is there, it is just behind the arm
on every character, because `_tunic` draws before `_arms` for all seventeen of
them (`docs/bust-plan.md`, B0's result).

Writes `out/bust/why_hidden.png`.
"""

import io
import os
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

PRESET = "satoko"
SCALE = 3


def sheet(inner: str, sk) -> Image.Image:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{sk.canvas_w:.0f}" '
        f'height="{sk.canvas_h:.0f}" viewBox="0 0 {sk.canvas_w:.0f} {sk.canvas_h:.0f}">'
        f'<rect width="100%" height="100%" fill="#ffffff" />{inner}</svg>'
    )
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=SCALE)))
    return im.convert("RGB")


def crop(im, sk):
    cx, cy, r = sk.head_cx * SCALE, sk.head_cy * SCALE, sk.head_r * SCALE
    return im.crop((int(cx - 1.55 * r), int(cy + 0.75 * r), int(cx + 1.55 * r), int(cy + 2.75 * r)))


def column(bust: float):
    p = replace(PRESETS[PRESET], bust=bust)
    sk = c.skeleton_for(p)
    torso = c._tunic(sk, p)
    arms = c._arms(sk, p)
    return [
        (crop(sheet(torso + arms, sk), sk), f"as rendered, bust {bust}"),
        (crop(sheet(torso, sk), sk), f"arms taken away, bust {bust}"),
        (crop(sheet(torso + f'<g opacity="0.33">{arms}</g>', sk), sk), f"arms at a third, bust {bust}"),
    ]


def main() -> None:
    os.makedirs("out/bust", exist_ok=True)
    rows = [column(0.0), column(1.0)]
    tw, th = rows[0][0][0].size
    pad, head = 12, 26
    sheet_im = Image.new(
        "RGB", (3 * tw + 4 * pad, 2 * (th + head) + 3 * pad), (225, 225, 225)
    )
    d = ImageDraw.Draw(sheet_im)
    for r, row in enumerate(rows):
        y = pad + r * (th + head + pad)
        for i, (tile, label) in enumerate(row):
            x = pad + i * (tw + pad)
            d.text((x + 4, y + 6), label, fill=(0, 0, 0))
            sheet_im.paste(tile, (x, y + head))
    sheet_im.save("out/bust/why_hidden.png")
    print("out/bust/why_hidden.png", sheet_im.size)


main()
