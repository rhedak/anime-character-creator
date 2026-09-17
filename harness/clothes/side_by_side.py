"""Reference beside our render, same head scale: `side_by_side.py <out.png> [x0 x1 y0 y1 px]`."""

import io
import sys

import cairosvg
from PIL import Image

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

REF = "../time_slider_katherina/style-anchors/katherina_grok/katherina_grok.jpg"
OX, OY, SC = 650.0, 481.0, 173.7
out = sys.argv[1]
X0, X1, Y0, Y1, PX = (float(v) for v in (sys.argv[2:7] if len(sys.argv) > 6 else (-2.2, 2.2, 0.3, 4.8, 110)))
bg = sys.argv[7] if len(sys.argv) > 7 else "black"


def crop(im, ox, oy, s):
    w, h = im.size
    big = Image.new("RGB", (w * 3, h * 3), bg)
    big.paste(im, (w, h))
    box = (w + ox + X0 * s, h + oy + Y0 * s, w + ox + X1 * s, h + oy + Y1 * s)
    return big.crop(tuple(round(v) for v in box)).resize((round((X1 - X0) * PX), round((Y1 - Y0) * PX)))


p = PRESETS["katherina"]
sk = c.skeleton_for(p)
svg = c.render_character(p, sk, background=bg)
im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=6))).convert("RGB")
k = im.width / sk.canvas_w
a = crop(Image.open(REF).convert("RGB"), OX, OY, SC)
b = crop(im, sk.head_cx * k, sk.head_cy * k, sk.head_r * k)
sheet = Image.new("RGB", (a.width * 2 + 10, a.height), "white")
sheet.paste(a, (0, 0))
sheet.paste(b, (a.width + 10, 0))
sheet.save(out)
