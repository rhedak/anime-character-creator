"""Tomohiro's cropped jacket: how long, and which end is widest.

The panel flares from shoulder to hem, which is right for a coat that falls to
the calf and wrong for one cropped at the waist: the widest point ends up on the
shoulder and the thing reads as armour. Both are swept here.
"""

import io
import pathlib
import sys
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw, ImageFont

from anime_character_creator import PRESETS, build_skeleton, render_character
from anime_character_creator.skeleton import BUILDS

OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("out/beard")
OUT.mkdir(parents=True, exist_ok=True)


def render(length):
    p = PRESETS["tomohiro"]
    p = replace(p, outfit=replace(p.outfit, coat_length=length))
    sk = build_skeleton(heads=BUILDS["chibi"], frame=p.frame)
    png = cairosvg.svg2png(bytestring=render_character(p, sk).encode(), output_width=800)
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    im = bg.convert("RGB")
    im.thumbnail((260, 420), Image.LANCZOS)
    return im


canon = Image.open("ref/tomohiro.png").convert("RGB")
canon.thumbnail((260, 420), Image.LANCZOS)
tiles = [("canon", canon)] + [(f"len {v:.2f}", render(v)) for v in (0.30, 0.38, 0.44, 0.50)]
W = sum(t.width for _, t in tiles) + 12 * (len(tiles) + 1)
H = max(t.height for _, t in tiles) + 34
canv = Image.new("RGB", (W, H), (18, 18, 22))
d = ImageDraw.Draw(canv)
f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 17)
x = 12
for label, t in tiles:
    d.text((x, 5), label, font=f, fill=(255, 255, 255))
    canv.paste(t, (x, 28))
    x += t.width + 12
canv.save(OUT / "jacket.png")
print("wrote", OUT / "jacket.png")
