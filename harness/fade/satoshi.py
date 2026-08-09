"""Does the shared clamp move Satoshi, once his own lift is back at 0.26?

`_HAIR_FADE` is shared between the two cuts. Satoko wants it at 0.72 and Satoshi
is being put back to how he was, so the question is whether the clamp is doing
anything to him at all: if it is not, one number can stay shared, and if it is,
the fade has to become per-cut.
"""

import io
import pathlib
import sys

import cairosvg
from PIL import Image, ImageDraw, ImageFont

from anime_character_creator import PRESETS, build_skeleton, render_character
from anime_character_creator import character as C
from anime_character_creator.skeleton import BUILDS

OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("out/fade")
OUT.mkdir(parents=True, exist_ok=True)


def head(fade, lift):
    C._HAIR_FADE = fade
    C._CROP_TONE_LIFT = lift
    p = PRESETS["satoshi"]
    sk = build_skeleton(heads=BUILDS["chibi"], frame=p.frame)
    png = cairosvg.svg2png(bytestring=render_character(p, sk).encode(), output_width=800)
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    im = bg.convert("RGB")
    w, h = im.size
    im = im.crop((int(w * 0.10), int(h * 0.04), int(w * 0.90), int(h * 0.50)))
    return im.resize((320, int(320 * im.height / im.width)), Image.LANCZOS)


canon = Image.open("ref/satoshi.png").convert("RGB")
w, h = canon.size
c = canon.crop((int(w * 0.26), int(h * 0.02), int(w * 0.74), int(h * 0.34)))
tiles = [
    ("canon", c.resize((320, int(320 * c.height / c.width)), Image.LANCZOS)),
    ("was: fade .50 lift .26", head(0.50, 0.26)),
    ("now: fade .72 lift .14", head(0.72, 0.14)),
    ("revert lift only", head(0.72, 0.26)),
]
W = sum(t.width for _, t in tiles) + 12 * (len(tiles) + 1)
H = max(t.height for _, t in tiles) + 34
canv = Image.new("RGB", (W, H), (18, 18, 22))
d = ImageDraw.Draw(canv)
f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 16)
x = 12
for label, t in tiles:
    d.text((x, 5), label, font=f, fill=(255, 255, 255))
    canv.paste(t, (x, 28))
    x += t.width + 12
canv.save(OUT / "satoshi.png")
print("wrote", OUT / "satoshi.png")
