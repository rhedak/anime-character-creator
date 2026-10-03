"""Hair-trace audit, test 1 as a picture: every source at one head radius.

Each image is scaled so its head radius is `PX` pixels and placed so its head
centre is at the same point, on the calibration the harness already uses for
it (D0's for `katherina_grok_real`, `register.py`'s on top of it for the
hair-only reference, the witch hat's for `katherina_grok`). Ours is rendered
without hair, bat or staff, with `long_traced`'s mass drawn behind it in grey.
Horizontal rules every head radius from the head centre; vertical rules at
x = +-1 (the skull) and +-2.

Written to `out/hair_audit/lineup.png`.

    ./harness/run.sh harness/hair_audit/lineup.py
"""

import io
import json
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/hair_audit"
PX = 60
BOX = (-3.0, -2.2, 3.0, 6.0)  # head radii: left, top, right, bottom
REAL = ("ref-local/katherina_grok_real/katherina_grok_real.png", (636.0, 290.0, 88.7))
CHIBI = ("ref-local/katherina_grok/katherina_grok.jpg", (650.0, 481.0, 173.7))
HAIR_ONLY = "ref-local/katherina_hair/hair_with_human_shape.png"
HAIR_FULL = "ref-local/katherina_hair/hair_only.png"


def tile(img: Image.Image, cal) -> Image.Image:
    ox, oy, s = cal
    k = PX / s
    img = img.convert("RGB").resize((round(img.width * k), round(img.height * k)), Image.LANCZOS)
    W, H = round((BOX[2] - BOX[0]) * PX), round((BOX[3] - BOX[1]) * PX)
    out = Image.new("RGB", (W, H), (0, 0, 0))
    # Head centre to (-BOX[0], -BOX[1]) * PX.
    out.paste(img, (round(-BOX[0] * PX - ox * k), round(-BOX[1] * PX - oy * k)))
    return out


def hair_only_cal():
    reg = json.load(open("out/hair_only/register.json"))
    sc, (dx, dy) = reg["scale"], reg["offset"]
    ox, oy, s = REAL[1]
    # In the hair-only image's own pixels: head centre and px per head radius.
    return ((ox - dx) / sc, (oy - dy) / sc, s / sc)


def ours(height: float) -> Image.Image:
    p = PRESETS["katherina"]
    p = replace(p, height=height, familiar_color=None, hair_tail=0.0, outfit=replace(p.outfit, hat_color=None, staff_color=None))
    sk = c.skeleton_for(p)
    orig = (c._hair_mass, c._hair_front)

    def grey_mass(sk, p):
        d = c._curve(sk.head_cx, sk.head_cy, sk.head_r, *c.HAIRSTYLES[p.hairstyle].mass(c._hair_fall(sk, p)))
        return f'<path d="{d}" fill="#6a6a6a" stroke="#0d0d0d" stroke-width="3" />'

    c._hair_mass, c._hair_front = grey_mass, lambda sk, p: ""
    try:
        svg = c.render_character(p, sk, background="black")
    finally:
        c._hair_mass, c._hair_front = orig
    png = cairosvg.svg2png(bytestring=svg.encode())
    return tile(Image.open(io.BytesIO(png)), (sk.head_cx, sk.head_cy, sk.head_r))


def rules(im: Image.Image, label: str) -> Image.Image:
    d = ImageDraw.Draw(im)
    W, H = im.size
    for yr in range(-2, 7):
        y = (yr - BOX[1]) * PX
        d.line([(0, y), (W, y)], fill=(90, 90, 90) if yr else (200, 200, 0), width=1)
        d.text((2, y - 11), f"{yr}", fill=(255, 255, 0))
    for xr in (-2, -1, 1, 2):
        x = (xr - BOX[0]) * PX
        d.line([(x, 0), (x, H)], fill=(0, 160, 220) if abs(xr) == 1 else (0, 90, 140), width=1)
    d.text((4, H - 16), label, fill=(255, 255, 255))
    return im


def main() -> None:
    tiles = [
        rules(tile(Image.open(REAL[0]), REAL[1]), "katherina_grok_real (realistic)"),
        rules(tile(Image.open(HAIR_FULL), hair_only_cal()), "hair_only (registered)"),
        rules(tile(Image.open(HAIR_ONLY), hair_only_cal()), "hair_with_human_shape"),
        rules(tile(Image.open(CHIBI[0]), CHIBI[1]), "katherina_grok (tall chibi ref)"),
        rules(ours(1.0), "ours h1.0 (preset), long_traced grey"),
        rules(ours(1.3), "ours h1.3"),
    ]
    W, H = tiles[0].size
    sheet = Image.new("RGB", (W * len(tiles) + 8 * (len(tiles) - 1), H), (128, 128, 128))
    for i, t in enumerate(tiles):
        sheet.paste(t, (i * (W + 8), 0))
    sheet.save(f"{OUT}/lineup.png")
    print(f"{OUT}/lineup.png {sheet.size}")


if __name__ == "__main__":
    main()
